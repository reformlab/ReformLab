# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for POST /api/decisions/summary — Story 17.5.

Test classes by AC:
- TestDecisionSummaryValidation: 404/409/422 error cases
- TestDecisionSummarySuccess: valid 1-domain and 2-domain responses
- TestDecisionSummaryFiltering: decile filtering, year detail with/without probabilities
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pyarrow as pa
import pytest
from fastapi.testclient import TestClient

from reformlab.interfaces.api import SimulationResult
from reformlab.orchestrator.panel import PanelOutput
from reformlab.server.dependencies import ResultCache, get_result_cache, get_result_store
from reformlab.server.result_store import ResultMetadata, ResultStore

# ---------------------------------------------------------------------------
# Helpers — panel builders
# ---------------------------------------------------------------------------

_VEHICLE_ALTS = ["keep_current", "buy_petrol", "buy_diesel", "buy_hybrid", "buy_ev", "buy_no_vehicle"]
_HEATING_ALTS = ["keep_current", "gas_boiler", "heat_pump", "electric", "wood_pellet"]


def _make_vehicle_panel(
    n: int = 100,
    years: list[int] | None = None,
    include_probabilities: bool = True,
    include_income: bool = True,
) -> PanelOutput:
    """Create a PanelOutput with vehicle decision columns."""
    if years is None:
        years = [2025]

    all_rows: dict[str, list[Any]] = {
        "household_id": [],
        "year": [],
        "income": [],
        "vehicle_chosen": [],
    }
    if include_probabilities:
        all_rows["vehicle_probabilities"] = []
    all_rows["decision_domains"] = []

    for yr in years:
        for i in range(n):
            all_rows["household_id"].append(i)
            all_rows["year"].append(yr)
            if include_income:
                all_rows["income"].append(10000.0 + i * 1000.0)
            else:
                all_rows["income"].append(None)
            # Mostly keep_current, some buy_ev for higher-income households
            chosen = "buy_ev" if i >= 80 else "keep_current"
            all_rows["vehicle_chosen"].append(chosen)
            if include_probabilities:
                probs = [0.7, 0.05, 0.05, 0.05, 0.1, 0.05] if i < 80 else [0.1, 0.02, 0.02, 0.06, 0.75, 0.05]
                all_rows["vehicle_probabilities"].append(probs)
            all_rows["decision_domains"].append(["vehicle"])

    schema_fields = [
        ("household_id", pa.int64()),
        ("year", pa.int64()),
        ("income", pa.float64()),
        ("vehicle_chosen", pa.string()),
    ]
    if include_probabilities:
        schema_fields.append(("vehicle_probabilities", pa.list_(pa.float64())))
    schema_fields.append(("decision_domains", pa.list_(pa.string())))

    arrays = {}
    for name, dtype in schema_fields:
        if name == "income" and not include_income:
            arrays[name] = pa.array([None] * len(all_rows["household_id"]), type=pa.float64())
        else:
            arrays[name] = pa.array(all_rows[name], type=dtype)

    table = pa.table(arrays)
    metadata = {
        "start_year": min(years),
        "end_year": max(years),
        "decision_domain_alternatives": {"vehicle": _VEHICLE_ALTS},
    }
    return PanelOutput(table=table, metadata=metadata)


def _make_two_domain_panel(n: int = 100) -> PanelOutput:
    """Create a PanelOutput with vehicle AND heating decision columns."""
    incomes = [10000.0 + i * 1000.0 for i in range(n)]
    vehicle_chosen = ["buy_ev" if i >= 80 else "keep_current" for i in range(n)]
    heating_chosen = ["heat_pump" if i >= 70 else "keep_current" for i in range(n)]
    v_ev = [0.1, 0.02, 0.02, 0.06, 0.75, 0.05]
    v_keep = [0.7, 0.05, 0.05, 0.05, 0.1, 0.05]
    vehicle_probs = [v_ev if i >= 80 else v_keep for i in range(n)]
    h_heat = [0.1, 0.05, 0.75, 0.05, 0.05]
    h_keep = [0.8, 0.05, 0.1, 0.02, 0.03]
    heating_probs = [h_heat if i >= 70 else h_keep for i in range(n)]
    decision_domains_list = [["vehicle", "heating"]] * n

    table = pa.table({
        "household_id": pa.array(list(range(n)), type=pa.int64()),
        "year": pa.array([2025] * n, type=pa.int64()),
        "income": pa.array(incomes, type=pa.float64()),
        "vehicle_chosen": pa.array(vehicle_chosen, type=pa.string()),
        "vehicle_probabilities": pa.array(vehicle_probs, type=pa.list_(pa.float64())),
        "heating_chosen": pa.array(heating_chosen, type=pa.string()),
        "heating_probabilities": pa.array(heating_probs, type=pa.list_(pa.float64())),
        "decision_domains": pa.array(decision_domains_list, type=pa.list_(pa.string())),
    })
    metadata = {
        "start_year": 2025,
        "end_year": 2025,
        "decision_domain_alternatives": {
            "vehicle": _VEHICLE_ALTS,
            "heating": _HEATING_ALTS,
        },
    }
    return PanelOutput(table=table, metadata=metadata)


def _make_no_decision_panel(n: int = 100) -> PanelOutput:
    """Create a PanelOutput WITHOUT decision_domain_alternatives in metadata."""
    table = pa.table({
        "household_id": pa.array(list(range(n)), type=pa.int64()),
        "year": pa.array([2025] * n, type=pa.int64()),
        "income": pa.array([10000.0 + i * 500.0 for i in range(n)], type=pa.float64()),
    })
    return PanelOutput(table=table, metadata={"start_year": 2025, "end_year": 2025})


def _make_sim_result(panel: PanelOutput | None = None) -> SimulationResult:
    manifest = MagicMock()
    manifest.manifest_id = "manifest-test"
    return SimulationResult(
        success=True,
        scenario_id="sc-test",
        yearly_states={},
        panel_output=panel,
        manifest=manifest,
        metadata={},
    )


def _make_metadata(run_id: str) -> ResultMetadata:
    return ResultMetadata(
        run_id=run_id,
        timestamp="2026-03-08T00:00:00+00:00",
        run_kind="scenario",
        start_year=2025,
        end_year=2025,
        population_id=None,
        seed=42,
        row_count=100,
        manifest_id="manifest-001",
        scenario_id="sc-001",
        adapter_version="1.0.0",
        started_at="2026-03-08T00:00:00+00:00",
        finished_at="2026-03-08T00:00:05+00:00",
        status="completed",
        template_name="carbon_tax",
        portfolio_name=None,
        policy_type="carbon_tax",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_store(tmp_path: Path) -> ResultStore:
    return ResultStore(base_dir=tmp_path)


@pytest.fixture()
def empty_cache() -> ResultCache:
    return ResultCache(max_size=20)


@pytest.fixture()
def client_with_deps(
    tmp_store: ResultStore,
    empty_cache: ResultCache,
) -> TestClient:
    """TestClient with ResultStore and ResultCache overridden."""
    from reformlab.server.app import create_app

    app = create_app()
    app.dependency_overrides[get_result_store] = lambda: tmp_store
    app.dependency_overrides[get_result_cache] = lambda: empty_cache
    return TestClient(app)


@pytest.fixture()
def auth_headers(client_with_deps: TestClient) -> dict[str, str]:
    response = client_with_deps.post(
        "/api/auth/login",
        json={"password": "test-password-123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def _seed(
    store: ResultStore,
    cache: ResultCache,
    run_id: str,
    panel: PanelOutput | None = None,
    in_cache: bool = True,
) -> None:
    """Add metadata to store and optionally a result to cache."""
    store.save_metadata(run_id, _make_metadata(run_id))
    if in_cache:
        cache.store(run_id, _make_sim_result(panel))


# ---------------------------------------------------------------------------
# AC-1/AC-2/AC-3/AC-4: Validation tests
# ---------------------------------------------------------------------------


class TestDecisionSummaryValidation:
    """Error cases: 404, 409, 422 for various conditions."""

    def test_unknown_run_id_returns_404(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "no-such-run"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["what"] is not None
        assert "why" in detail
        assert "fix" in detail

    def test_evicted_run_returns_409(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        auth_headers: dict[str, str],
    ) -> None:
        # Metadata in store but nothing in cache
        tmp_store.save_metadata("evicted-run", _make_metadata("evicted-run"))
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "evicted-run"},
            headers=auth_headers,
        )
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert "what" in detail
        assert "why" in detail
        assert "fix" in detail

    def test_none_panel_output_returns_409(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed(tmp_store, empty_cache, "run-no-panel", panel=None, in_cache=True)
        # Overwrite with panel=None explicitly
        sim = _make_sim_result(panel=None)
        empty_cache.store("run-no-panel", sim)
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-no-panel"},
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_no_decision_data_returns_422_with_no_decision_data_what(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        """422 when panel has no decision_domain_alternatives metadata key."""
        _seed(tmp_store, empty_cache, "run-nodec", panel=_make_no_decision_panel())
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-nodec"},
            headers=auth_headers,
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["what"] == "NoDecisionData"
        assert "why" in detail
        assert "fix" in detail

    def test_unsupported_group_by_returns_422(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        """422 when group_by is an unsupported value."""
        _seed(tmp_store, empty_cache, "run-badgroupby", panel=_make_vehicle_panel())
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-badgroupby", "group_by": "region"},
            headers=auth_headers,
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "what" in detail
        assert "region" in detail["what"]

    def test_invalid_group_value_non_integer_returns_422(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        """422 when group_value is not a valid integer."""
        _seed(tmp_store, empty_cache, "run-badgv", panel=_make_vehicle_panel())
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-badgv", "group_by": "decile", "group_value": "abc"},
            headers=auth_headers,
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "what" in detail
        assert "abc" in detail["what"]

    def test_invalid_group_value_out_of_range_returns_422(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        """422 when group_value integer is outside 1–10 range."""
        _seed(tmp_store, empty_cache, "run-oor", panel=_make_vehicle_panel())
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-oor", "group_by": "decile", "group_value": "0"},
            headers=auth_headers,
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert "what" in detail

    def test_decile_filter_without_income_column_returns_422(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        """422 with what=NoIncomeData when income column absent and group_by=decile."""
        # Panel has decisions but no income column
        n = 50
        table = pa.table({
            "household_id": pa.array(list(range(n)), type=pa.int64()),
            "year": pa.array([2025] * n, type=pa.int64()),
            "vehicle_chosen": pa.array(["keep_current"] * n, type=pa.string()),
            "decision_domains": pa.array([["vehicle"]] * n, type=pa.list_(pa.string())),
        })
        panel = PanelOutput(
            table=table,
            metadata={
                "start_year": 2025,
                "end_year": 2025,
                "decision_domain_alternatives": {"vehicle": _VEHICLE_ALTS},
            },
        )
        _seed(tmp_store, empty_cache, "run-noincome", panel=panel)
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-noincome", "group_by": "decile", "group_value": "3"},
            headers=auth_headers,
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["what"] == "NoIncomeData"

    def test_error_format_has_what_why_fix(
        self,
        client_with_deps: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "bogus"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}


# ---------------------------------------------------------------------------
# Success tests
# ---------------------------------------------------------------------------


class TestDecisionSummarySuccess:
    """Valid summary responses for 1-domain and 2-domain runs."""

    def test_single_domain_summary_shape(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed(tmp_store, empty_cache, "run-1d", panel=_make_vehicle_panel())
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-1d"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "run-1d"
        assert len(data["domains"]) == 1

        domain = data["domains"][0]
        assert domain["domain_name"] == "vehicle"
        assert domain["alternative_ids"] == _VEHICLE_ALTS
        assert set(domain["alternative_labels"].keys()) == set(_VEHICLE_ALTS)

    def test_single_domain_counts_correct(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        """80 keep_current, 20 buy_ev out of 100 households."""
        _seed(tmp_store, empty_cache, "run-counts", panel=_make_vehicle_panel(n=100))
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-counts"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        outcome = response.json()["domains"][0]["yearly_outcomes"][0]
        assert outcome["year"] == 2025
        assert outcome["total_households"] == 100
        assert outcome["counts"]["keep_current"] == 80
        assert outcome["counts"]["buy_ev"] == 20
        # Percentages
        assert abs(outcome["percentages"]["keep_current"] - 80.0) < 0.01
        assert abs(outcome["percentages"]["buy_ev"] - 20.0) < 0.01

    def test_years_returned_ascending(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        panel = _make_vehicle_panel(years=[2027, 2025, 2026])
        _seed(tmp_store, empty_cache, "run-years", panel=panel)
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-years"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        outcomes = response.json()["domains"][0]["yearly_outcomes"]
        years = [o["year"] for o in outcomes]
        assert years == sorted(years)

    def test_alternatives_follow_metadata_order(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed(tmp_store, empty_cache, "run-order", panel=_make_vehicle_panel())
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-order"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        alt_ids = response.json()["domains"][0]["alternative_ids"]
        assert alt_ids == _VEHICLE_ALTS

    def test_two_domain_summary_shape(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed(tmp_store, empty_cache, "run-2d", panel=_make_two_domain_panel())
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-2d"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        domains = response.json()["domains"]
        assert len(domains) == 2
        domain_names = {d["domain_name"] for d in domains}
        assert domain_names == {"vehicle", "heating"}

    def test_alternative_labels_populated(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed(tmp_store, empty_cache, "run-labels", panel=_make_vehicle_panel())
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-labels"},
            headers=auth_headers,
        )
        labels = response.json()["domains"][0]["alternative_labels"]
        assert labels["buy_ev"] == "Electric (EV)"
        assert labels["keep_current"] == "Keep Current"

    def test_mean_probabilities_null_without_year_param(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        """mean_probabilities should be None when year param is not set."""
        _seed(tmp_store, empty_cache, "run-noprob", panel=_make_vehicle_panel())
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-noprob"},
            headers=auth_headers,
        )
        outcome = response.json()["domains"][0]["yearly_outcomes"][0]
        assert outcome["mean_probabilities"] is None


# ---------------------------------------------------------------------------
# Filtering tests
# ---------------------------------------------------------------------------


class TestDecisionSummaryFiltering:
    """Decile filtering and year detail with/without probabilities."""

    def test_decile_filter_reduces_household_count(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        """Filtering to D1 should return fewer households than All."""
        _seed(tmp_store, empty_cache, "run-decile", panel=_make_vehicle_panel(n=100))
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-decile", "group_by": "decile", "group_value": "1"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        outcome = response.json()["domains"][0]["yearly_outcomes"][0]
        # D1 should have ~10 households (10% of 100)
        assert outcome["total_households"] < 100
        assert outcome["total_households"] > 0

    def test_decile_filter_percentages_sum_to_100(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed(tmp_store, empty_cache, "run-pct", panel=_make_vehicle_panel(n=100))
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-pct", "group_by": "decile", "group_value": "5"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        outcome = response.json()["domains"][0]["yearly_outcomes"][0]
        total_pct = sum(outcome["percentages"].values())
        assert abs(total_pct - 100.0) < 0.01

    def test_year_detail_with_probabilities_populated(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        """When year=2025 and probabilities column present, mean_probabilities is populated."""
        _seed(tmp_store, empty_cache, "run-prob", panel=_make_vehicle_panel(include_probabilities=True))
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-prob", "year": 2025},
            headers=auth_headers,
        )
        assert response.status_code == 200
        outcome = response.json()["domains"][0]["yearly_outcomes"][0]
        assert outcome["year"] == 2025
        probs = outcome["mean_probabilities"]
        assert probs is not None
        assert set(probs.keys()) == set(_VEHICLE_ALTS)
        # All probabilities should be between 0 and 1
        for p in probs.values():
            assert 0.0 <= p <= 1.0

    def test_year_detail_without_probabilities_returns_null_and_warning(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        """When year set but probability column absent, mean_probabilities=None + warning."""
        _seed(
            tmp_store,
            empty_cache,
            "run-noprob2",
            panel=_make_vehicle_panel(include_probabilities=False),
        )
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-noprob2", "year": 2025},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        outcome = data["domains"][0]["yearly_outcomes"][0]
        assert outcome["mean_probabilities"] is None
        # At least one warning about missing probability data
        assert len(data["warnings"]) >= 1
        assert any("Probability data unavailable" in w for w in data["warnings"])

    def test_domain_filter_returns_only_requested_domain(
        self,
        client_with_deps: TestClient,
        tmp_store: ResultStore,
        empty_cache: ResultCache,
        auth_headers: dict[str, str],
    ) -> None:
        _seed(tmp_store, empty_cache, "run-domf", panel=_make_two_domain_panel())
        response = client_with_deps.post(
            "/api/decisions/summary",
            json={"run_id": "run-domf", "domain_name": "vehicle"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        domains = response.json()["domains"]
        assert len(domains) == 1
        assert domains[0]["domain_name"] == "vehicle"
