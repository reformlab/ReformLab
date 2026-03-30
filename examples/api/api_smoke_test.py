"""Run a quick end-to-end smoke test against the ReformLab FastAPI server.

Flow:
1) OpenAPI availability
2) Auth login
3) Templates listing (+ optional scenario bootstrap if empty)
4) Baseline + reform runs
5) Indicator + comparison
6) CSV + Parquet export
7) Evidence model verification (Story 21.8 / AC4)
"""

from __future__ import annotations

import copy
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any


class SmokeTestError(RuntimeError):
    """Raised when a smoke test step fails."""


def _now_ms() -> int:
    return int(time.time() * 1000)


def _join_url(base_url: str, path: str) -> str:
    if base_url.endswith("/"):
        base_url = base_url[:-1]
    if not path.startswith("/"):
        path = "/" + path
    return base_url + path


def _request(
    *,
    method: str,
    base_url: str,
    path: str,
    timeout: float,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    expected_statuses: tuple[int, ...] = (200,),
) -> tuple[int, Any, dict[str, str]]:
    url = _join_url(base_url, path)
    headers: dict[str, str] = {"Accept": "application/json"}
    data: bytes | None = None

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url=url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            raw = resp.read()
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read()
        resp_headers = {k.lower(): v for k, v in exc.headers.items()}
    except urllib.error.URLError as exc:
        raise SmokeTestError(f"Network error for {method} {path}: {exc}") from exc

    if status not in expected_statuses:
        text = raw.decode("utf-8", errors="replace")
        raise SmokeTestError(
            f"{method} {path} returned {status}, expected {expected_statuses}. Body: {text}"
        )

    content_type = resp_headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            payload: Any = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise SmokeTestError(f"Invalid JSON response from {method} {path}") from exc
    else:
        payload = raw

    return status, payload, resp_headers


def _bump_rate_schedule(policy: dict[str, Any], increment: float = 10.0) -> dict[str, Any]:
    """Return a policy copy with numeric rate_schedule values increased."""
    reform_policy = copy.deepcopy(policy)
    schedule = reform_policy.get("rate_schedule")
    if isinstance(schedule, dict):
        for key, value in list(schedule.items()):
            if isinstance(value, (int, float)):
                schedule[key] = float(value) + increment
    return reform_policy


def main() -> int:
    base_url = os.environ.get("REFORMLAB_API_BASE_URL", "http://127.0.0.1:8000")
    password = os.environ.get(
        "REFORMLAB_API_PASSWORD",
        os.environ.get("REFORMLAB_PASSWORD", "local"),
    )
    timeout = float(os.environ.get("REFORMLAB_API_TIMEOUT_SECONDS", "30"))

    print(f"[smoke] base_url={base_url}")

    # 1) OpenAPI
    _request(
        method="GET",
        base_url=base_url,
        path="/api/openapi.json",
        timeout=timeout,
    )
    print("[smoke] openapi ok")

    # 2) Login
    _, login_data, _ = _request(
        method="POST",
        base_url=base_url,
        path="/api/auth/login",
        timeout=timeout,
        body={"password": password},
    )
    token = login_data.get("token")
    if not isinstance(token, str) or not token:
        raise SmokeTestError("Login succeeded but no token was returned")
    print("[smoke] login ok")

    # 3) Templates
    _, templates_data, _ = _request(
        method="GET",
        base_url=base_url,
        path="/api/templates",
        timeout=timeout,
        token=token,
    )
    templates = templates_data.get("templates", [])
    if not isinstance(templates, list):
        raise SmokeTestError("Invalid templates payload shape")

    if not templates:
        scenario_name = f"rest-smoke-{_now_ms()}"
        create_body = {
            "name": scenario_name,
            "policy_type": "carbon_tax",
            "policy": {"rate_schedule": {"2025": 44.6, "2026": 55.0, "2027": 65.0}},
            "start_year": 2025,
            "end_year": 2027,
            "description": "Auto-created by API smoke test",
        }
        _request(
            method="POST",
            base_url=base_url,
            path="/api/scenarios",
            timeout=timeout,
            token=token,
            body=create_body,
            expected_statuses=(201,),
        )
        template_id = scenario_name
        default_policy = create_body["policy"]
        print(f"[smoke] no templates found; created scenario '{scenario_name}'")
    else:
        first = templates[0]
        template_id = first.get("id")
        if not isinstance(template_id, str) or not template_id:
            raise SmokeTestError("First template has no usable 'id'")
        _, detail_data, _ = _request(
            method="GET",
            base_url=base_url,
            path=f"/api/templates/{template_id}",
            timeout=timeout,
            token=token,
        )
        default_policy = detail_data.get("default_policy", {})
        if not isinstance(default_policy, dict):
            raise SmokeTestError("Template detail has invalid default_policy")
        print(f"[smoke] using template '{template_id}'")

    baseline_policy = copy.deepcopy(default_policy)
    reform_policy = _bump_rate_schedule(baseline_policy, increment=10.0)

    run_body_baseline = {
        "template_name": template_id,
        "policy": baseline_policy,
        "start_year": 2025,
        "end_year": 2027,
    }
    run_body_reform = {
        "template_name": template_id,
        "policy": reform_policy,
        "start_year": 2025,
        "end_year": 2027,
    }

    # 4) Runs (degrades gracefully when simulation data is unavailable)
    baseline_status, baseline_run_data, _ = _request(
        method="POST",
        base_url=base_url,
        path="/api/runs",
        timeout=timeout,
        token=token,
        body=run_body_baseline,
        expected_statuses=(200, 500),
    )

    degraded_mode = baseline_status == 500
    if degraded_mode:
        required = {"error", "what", "why", "fix", "status_code"}
        if not isinstance(baseline_run_data, dict) or not required.issubset(
            set(baseline_run_data.keys())
        ):
            raise SmokeTestError(
                "Baseline run failed without structured error payload required by API contract"
            )
        print("[smoke] baseline run unavailable in this environment (structured 500 confirmed)")

        _request(
            method="POST",
            base_url=base_url,
            path="/api/runs/memory-check",
            timeout=timeout,
            token=token,
            body={
                "template_name": template_id,
                "policy": baseline_policy,
                "start_year": 2025,
                "end_year": 2027,
            },
        )
        print("[smoke] memory-check ok")

        _request(
            method="POST",
            base_url=base_url,
            path="/api/indicators/invalid_type",
            timeout=timeout,
            token=token,
            body={"run_id": "smoke-missing-run"},
            expected_statuses=(422,),
        )
        print("[smoke] indicator validation path ok (422)")

        _request(
            method="POST",
            base_url=base_url,
            path="/api/comparison",
            timeout=timeout,
            token=token,
            body={
                "baseline_run_id": "missing-baseline",
                "reform_run_id": "missing-reform",
            },
            expected_statuses=(404,),
        )
        print("[smoke] comparison missing-run path ok (404)")

        _request(
            method="POST",
            base_url=base_url,
            path="/api/exports/csv",
            timeout=timeout,
            token=token,
            body={"run_id": "missing-run"},
            expected_statuses=(404,),
        )
        _request(
            method="POST",
            base_url=base_url,
            path="/api/exports/parquet",
            timeout=timeout,
            token=token,
            body={"run_id": "missing-run"},
            expected_statuses=(404,),
        )
        print("[smoke] export missing-run paths ok (404)")
        print("[smoke] checks passed (degraded mode)")
        return 0

    baseline_run_id = baseline_run_data.get("run_id")
    if not isinstance(baseline_run_id, str) or not baseline_run_id:
        raise SmokeTestError("Baseline run did not return run_id")
    print(f"[smoke] baseline run ok ({baseline_run_id})")

    _, reform_run_data, _ = _request(
        method="POST",
        base_url=base_url,
        path="/api/runs",
        timeout=timeout,
        token=token,
        body=run_body_reform,
    )
    reform_run_id = reform_run_data.get("run_id")
    if not isinstance(reform_run_id, str) or not reform_run_id:
        raise SmokeTestError("Reform run did not return run_id")
    print(f"[smoke] reform run ok ({reform_run_id})")

    # 5) Indicators + comparison
    _request(
        method="POST",
        base_url=base_url,
        path="/api/indicators/distributional",
        timeout=timeout,
        token=token,
        body={"run_id": baseline_run_id, "income_field": "income", "by_year": True},
    )
    print("[smoke] distributional indicator ok")

    _request(
        method="POST",
        base_url=base_url,
        path="/api/comparison",
        timeout=timeout,
        token=token,
        body={
            "baseline_run_id": baseline_run_id,
            "reform_run_id": reform_run_id,
            "welfare_field": "disposable_income",
            "threshold": 0,
        },
    )
    print("[smoke] welfare comparison ok")

    # 6) Exports
    _, _, csv_headers = _request(
        method="POST",
        base_url=base_url,
        path="/api/exports/csv",
        timeout=timeout,
        token=token,
        body={"run_id": baseline_run_id},
    )
    if "attachment" not in csv_headers.get("content-disposition", "").lower():
        raise SmokeTestError("CSV export succeeded but did not return attachment headers")
    print("[smoke] csv export ok")

    _, _, parquet_headers = _request(
        method="POST",
        base_url=base_url,
        path="/api/exports/parquet",
        timeout=timeout,
        token=token,
        body={"run_id": baseline_run_id},
    )
    if "attachment" not in parquet_headers.get("content-disposition", "").lower():
        raise SmokeTestError("Parquet export succeeded but did not return attachment headers")
    print("[smoke] parquet export ok")

    # 7) Evidence model verification (Story 21.8 / AC4)
    # Test population listing includes evidence fields
    _, populations_data, _ = _request(
        method="GET",
        base_url=base_url,
        path="/api/populations",
        timeout=timeout,
        token=token,
    )
    populations = populations_data.get("populations", [])
    if not isinstance(populations, list):
        raise SmokeTestError("Invalid populations payload shape")
    # Check that ALL populations include evidence fields (Story 21.8 / AC4)
    for i, pop in enumerate(populations):
        if not isinstance(pop, dict):
            raise SmokeTestError(f"Population entry {i} must be an object")
        # Verify evidence fields are present
        for evidence_field in ("origin", "access_mode", "trust_status"):
            if evidence_field not in pop:
                raise SmokeTestError(
                    f"Population {i} missing evidence field '{evidence_field}'"
                )
    print(f"[smoke] population listing evidence fields ok ({len(populations)} checked)")

    # Test result endpoint includes evidence metadata (if run completed successfully)
    if not degraded_mode:
        _, result_detail_data, _ = _request(
            method="GET",
            base_url=base_url,
            path=f"/api/results/{baseline_run_id}",
            timeout=timeout,
            token=token,
        )
        # Check for evidence_assets field (may be empty list)
        # Note: This field is populated from the manifest when available
        if "evidence_assets" not in result_detail_data:
            raise SmokeTestError(
                "Result detail missing 'evidence_assets' field"
            )
        evidence_assets = result_detail_data.get("evidence_assets", [])
        if not isinstance(evidence_assets, list):
            raise SmokeTestError("evidence_assets must be a list")
        print("[smoke] result evidence metadata ok")

        # Note: AC4 preflight trust-status validation checks and 403 trust-status
        # violation tests are deferred - these require dedicated engine validation
        # endpoints that are not yet implemented. The smoke test verifies evidence
        # fields are present in API responses; full trust-status rule enforcement
        # testing is in tests/regression/test_evidence_model.py.

    print("[smoke] all checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeTestError as exc:
        print(f"[smoke] FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
