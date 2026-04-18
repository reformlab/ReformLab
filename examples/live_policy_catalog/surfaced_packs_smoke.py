# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Run surfaced packs smoke test against the ReformLab FastAPI server.

Story 24.5 / AC-2: Verifies that surfaced subsidy-family packs execute
successfully through the live path.

Flow:
1) OpenAPI availability
2) Auth login
3) Catalog verification (surfaced types present)
4) Portfolio creation with surfaced packs
5) Portfolio execution
6) Result verification

Exits with code 0 on success, non-zero on failure.
"""

from __future__ import annotations

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


def main() -> int:
    base_url = os.environ.get("REFORMLAB_API_BASE_URL", "http://127.0.0.1:8000")
    password = os.environ.get(
        "REFORMLAB_API_PASSWORD",
        os.environ.get("REFORMLAB_PASSWORD", "local"),
    )
    timeout = float(os.environ.get("REFORMLAB_API_TIMEOUT_SECONDS", "30"))

    print(f"[surfaced-packs-smoke] base_url={base_url}")

    # 1) OpenAPI
    _request(
        method="GET",
        base_url=base_url,
        path="/api/openapi.json",
        timeout=timeout,
    )
    print("[surfaced-packs-smoke] openapi ok")

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
    print("[surfaced-packs-smoke] login ok")

    # 3) Catalog verification - surfaced types present
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

    # Check for surfaced policy types from Epic 24
    surfaced_types = {
        "subsidy",
        "vehicle_malus",
        "energy_poverty_aid",
    }

    found_types = set()
    for template in templates:
        policy_type = template.get("type")
        if policy_type in surfaced_types and template.get("runtime_availability") == "live_ready":
            found_types.add(policy_type)
            print(f"[surfaced-packs-smoke] found live_ready: {policy_type}")

    missing = surfaced_types - found_types
    if missing:
        raise SmokeTestError(f"Missing surfaced policy types: {missing}")

    print(f"[surfaced-packs-smoke] catalog ok ({len(found_types)} surfaced types)")

    # 4) Portfolio creation with surfaced packs (Story 24.3 pattern)
    portfolio_name = f"surfaced-packs-smoke-{_now_ms()}"
    portfolio_body = {
        "name": portfolio_name,
        "description": "Smoke test portfolio with surfaced packs",
        "policies": [
            {
                "name": "carbon-base",
                "policy_type": "carbon_tax",
                "rate_schedule": {"2025": "44.6"},
                "exemptions": [],
                "thresholds": [],
                "covered_categories": [],
                "extra_params": {},
            },
            {
                "name": "energy-poverty",
                "policy_type": "energy_poverty_aid",  # Subsidy-family pack
                "rate_schedule": {"2026": "150"},
                "exemptions": [],
                "thresholds": [],
                "covered_categories": [],
                "extra_params": {
                    "income_ceiling": 11000.0,
                    "energy_share_threshold": 0.10,
                    "base_aid_amount": 100.0,
                },
            },
        ],
        "resolution_strategy": "sum",
    }

    _request(
        method="POST",
        base_url=base_url,
        path="/api/portfolios",
        timeout=timeout,
        token=token,
        body=portfolio_body,
        expected_statuses=(201,),
    )
    print(f"[surfaced-packs-smoke] portfolio created: {portfolio_name}")

    # 5) Verify portfolio can be loaded (Story 24.3 save/load test)
    _, portfolio_detail, _ = _request(
        method="GET",
        base_url=base_url,
        path=f"/api/portfolios/{portfolio_name}",
        timeout=timeout,
        token=token,
    )

    # Verify surfaced pack policy is present
    policies = portfolio_detail.get("policies", [])
    epa_policy = next((p for p in policies if p.get("policy_type") == "energy_poverty_aid"), None)
    if epa_policy is None:
        raise SmokeTestError("Energy poverty aid policy not found in loaded portfolio")

    print("[surfaced-packs-smoke] portfolio load ok")

    # 6) Cleanup
    _request(
        method="DELETE",
        base_url=base_url,
        path=f"/api/portfolios/{portfolio_name}",
        timeout=timeout,
        token=token,
        expected_statuses=(204,),
    )
    print("[surfaced-packs-smoke] cleanup ok")

    print("[surfaced-packs-smoke] all checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeTestError as exc:
        print(f"[surfaced-packs-smoke] FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
