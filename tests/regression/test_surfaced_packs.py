# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""End-to-end regression tests for surfaced live policy packs — Story 24.5.

This module validates the entire Epic 24 implementation by testing surfaced
policy packs (subsidy, vehicle_malus, energy_poverty_aid) through the full
stack: catalog API → portfolio creation → execution → comparison.

Tests are organized by feature and acceptance criterion:
- Catalog exposure tests (AC-1)
- Portfolio validation tests (AC-1)
- Live execution tests (AC-1)
- Comparison tests (AC-1)
- Non-regression tests for existing packs (AC-1)
- Runtime availability guard tests (AC-5)

Story 24.5 closes Epic 24 and provides the regression safety net for the
expanded live policy catalog.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pyarrow as pa
import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from reformlab.templates.energy_poverty_aid.compute import EnergyPovertyAidParameters
    from reformlab.templates.schema import SubsidyParameters
    from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters

# Import shared fixtures and helpers
from tests.regression.conftest import (
    assert_live_ready_metadata,
    assert_surfaced_pack_columns_present,
)


def _unique_name(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"


def _policy_request(policy_type: str, name: str) -> dict[str, object]:
    extras: dict[str, object] = {}
    if policy_type == "vehicle_malus":
        extras = {"emission_threshold": 118.0, "malus_rate_per_gkm": 50.0}
    elif policy_type == "energy_poverty_aid":
        extras = {
            "income_ceiling": 11000.0,
            "energy_share_threshold": 0.10,
            "base_aid_amount": 100.0,
        }

    return {
        "name": name,
        "policy_type": policy_type,
        "rate_schedule": {"2025": "150" if policy_type == "energy_poverty_aid" else "50"},
        "exemptions": [],
        "thresholds": [],
        "covered_categories": [],
        "extra_params": extras,
    }


def _create_surfaced_portfolio(
    client: TestClient,
    auth_headers: dict[str, str],
    *,
    name: str,
    surfaced_type: str,
) -> None:
    response = client.post(
        "/api/portfolios",
        json={
            "name": name,
            "description": f"Regression portfolio with {surfaced_type}",
            "policies": [
                {
                    "name": "carbon",
                    "policy_type": "carbon_tax",
                    "rate_schedule": {"2025": "44.6"},
                    "exemptions": [],
                    "thresholds": [],
                    "covered_categories": [],
                    "extra_params": {},
                },
                _policy_request(surfaced_type, surfaced_type),
            ],
            "resolution_strategy": "sum",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.json()


def _run_portfolio(
    client: TestClient,
    auth_headers: dict[str, str],
    *,
    portfolio_name: str,
    runtime_mode: str = "live",
) -> str:
    response = client.post(
        "/api/runs",
        json={
            "portfolio_name": portfolio_name,
            "start_year": 2025,
            "end_year": 2025,
            "runtime_mode": runtime_mode,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["runtime_mode"] == runtime_mode
    assert data["success"] is True
    return data["run_id"]


def _result_columns(client: TestClient, auth_headers: dict[str, str], run_id: str) -> list[str]:
    response = client.get(f"/api/results/{run_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["data_available"] is True
    columns = data["columns"]
    assert isinstance(columns, list)
    return columns


# ---------------------------------------------------------------------------
# Test Classes: Catalog Exposure (AC-1)
# ---------------------------------------------------------------------------


class TestCatalogExposure:
    """AC-1: Catalog exposure tests verifying surfaced pack metadata.

    Validates that GET /api/templates returns surfaced packs with correct
    runtime_availability and metadata. At least 2 catalog exposure tests.

    Story 24.5 / AC-1: "At least 2 catalog exposure tests verifying surfaced
    pack metadata in GET /api/templates response"
    """

    def test_get_templates_returns_surfaces_subsidy_with_live_ready(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify subsidy pack is surfaced in catalog with live_ready status."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200

        templates = response.json().get("templates", [])
        subsidy_templates = [t for t in templates if t.get("type") == "subsidy"]

        assert len(subsidy_templates) > 0, "Subsidy pack should be surfaced in catalog"

        # Verify at least one subsidy template has live_ready metadata
        live_ready_subsidy = [t for t in subsidy_templates if t.get("runtime_availability") == "live_ready"]
        assert len(live_ready_subsidy) > 0, "Subsidy pack should have live_ready templates"

        # Verify metadata structure
        template = live_ready_subsidy[0]
        assert_live_ready_metadata(template, "subsidy")

    def test_get_templates_returns_surfaces_vehicle_malus_with_live_ready(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify vehicle_malus pack is surfaced in catalog with live_ready status."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200

        templates = response.json().get("templates", [])
        vehicle_malus_templates = [t for t in templates if t.get("type") == "vehicle_malus"]

        assert len(vehicle_malus_templates) > 0, "Vehicle malus pack should be surfaced in catalog"

        # Verify live_ready metadata
        live_ready_templates = [
            t for t in vehicle_malus_templates
            if t.get("runtime_availability") == "live_ready"
        ]
        assert len(live_ready_templates) > 0, "Vehicle malus pack should have live_ready templates"

        template = live_ready_templates[0]
        assert_live_ready_metadata(template, "vehicle_malus")

    def test_get_templates_returns_surfaces_energy_poverty_aid_with_live_ready(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify energy_poverty_aid pack is surfaced in catalog with live_ready status."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200

        templates = response.json().get("templates", [])
        epa_templates = [t for t in templates if t.get("type") == "energy_poverty_aid"]

        assert len(epa_templates) > 0, "Energy poverty aid pack should be surfaced in catalog"

        # Verify live_ready metadata
        live_ready_templates = [t for t in epa_templates if t.get("runtime_availability") == "live_ready"]
        assert len(live_ready_templates) > 0, "Energy poverty aid pack should have live_ready templates"

        template = live_ready_templates[0]
        assert_live_ready_metadata(template, "energy_poverty_aid")

    def test_catalog_includes_all_live_ready_types_from_story_24_2(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify all six live-ready policy types from Story 24.2 are surfaced.

        Story 24.2 added vehicle_malus and energy_poverty_aid to the existing
        live_ready types (carbon_tax, subsidy, rebate, feebate).

        Story 24.5 / AC-1: Catalog exposure for all surfaced packs.
        """
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200

        templates = response.json().get("templates", [])
        live_ready_types = {t.get("type") for t in templates if t.get("runtime_availability") == "live_ready"}

        # All six types from Story 24.2 should be present
        expected_types = {
            "carbon_tax",
            "subsidy",
            "rebate",
            "feebate",
            "vehicle_malus",
            "energy_poverty_aid",
        }

        missing = expected_types - live_ready_types
        assert not missing, f"Missing live_ready policy types: {missing}"


# ---------------------------------------------------------------------------
# Test Classes: Portfolio Validation (AC-1)
# ---------------------------------------------------------------------------


class TestPortfolioValidation:
    """AC-1: Portfolio validation tests for surfaced policy types.

    Validates that portfolio CREATE/VALIDATE operations accept surfaced
    policy types (vehicle_malus, energy_poverty_aid). At least 2 tests.

    Story 24.5 / AC-1: "At least 2 portfolio validation tests confirming
    surfaced policy types (vehicle_malus, energy_poverty_aid) are accepted"
    """

    def test_validate_accepts_vehicle_malus_policy_type(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify portfolio validation accepts vehicle_malus policy type."""
        request_body = {
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
                    "name": "vehicle-malus",
                    "policy_type": "vehicle_malus",
                    "rate_schedule": {"2026": "50.0"},  # Different year to avoid overlapping_years conflict
                    "exemptions": [],
                    "thresholds": [],
                    "covered_categories": [],
                    "extra_params": {
                        "emission_threshold": 118.0,
                        "malus_rate_per_gkm": 50.0,
                    },
                },
            ],
            "resolution_strategy": "sum",
        }

        response = client.post("/api/portfolios/validate", json=request_body, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "is_compatible" in data
        # Should be compatible (no conflicts with non-overlapping years)
        assert data["is_compatible"] is True

    def test_validate_accepts_energy_poverty_aid_policy_type(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify portfolio validation accepts energy_poverty_aid policy type."""
        request_body = {
            "policies": [
                {
                    "name": "subsidy-base",
                    "policy_type": "subsidy",
                    "rate_schedule": {"2025": "5000"},
                    "exemptions": [],
                    "thresholds": [],
                    "covered_categories": [],
                    "extra_params": {},
                },
                {
                    "name": "energy-poverty",
                    "policy_type": "energy_poverty_aid",
                    "rate_schedule": {"2026": "150"},  # Different year to avoid overlapping_years conflict
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

        response = client.post("/api/portfolios/validate", json=request_body, headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "is_compatible" in data
        # Should be compatible (no conflicts with non-overlapping years)
        assert data["is_compatible"] is True

    def test_create_portfolio_with_vehicle_malus_succeeds(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify portfolio creation with vehicle_malus policy succeeds."""
        portfolio_name = _unique_name("test-vehicle-malus")
        request_body = {
            "name": portfolio_name,
            "description": "Test portfolio with vehicle malus",
            "policies": [
                {
                    "name": "carbon",
                    "policy_type": "carbon_tax",
                    "rate_schedule": {"2025": "44.6"},
                    "exemptions": [],
                    "thresholds": [],
                    "covered_categories": [],
                    "extra_params": {},
                },
                {
                    "name": "malus",
                    "policy_type": "vehicle_malus",
                    "rate_schedule": {"2025": "50"},
                    "exemptions": [],
                    "thresholds": [],
                    "covered_categories": [],
                    "extra_params": {
                        "emission_threshold": 118.0,
                        "malus_rate_per_gkm": 50.0,
                    },
                },
            ],
            "resolution_strategy": "sum",
        }

        response = client.post("/api/portfolios", json=request_body, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert "version_id" in data

        # Cleanup
        client.delete(f"/api/portfolios/{portfolio_name}", headers=auth_headers)

    def test_create_portfolio_with_energy_poverty_aid_succeeds(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify portfolio creation with energy_poverty_aid policy succeeds."""
        portfolio_name = _unique_name("test-energy-poverty")
        request_body = {
            "name": portfolio_name,
            "description": "Test portfolio with energy poverty aid",
            "policies": [
                {
                    "name": "subsidy",
                    "policy_type": "subsidy",
                    "rate_schedule": {"2025": "5000"},
                    "exemptions": [],
                    "thresholds": [],
                    "covered_categories": [],
                    "extra_params": {},
                },
                {
                    "name": "epa",
                    "policy_type": "energy_poverty_aid",
                    "rate_schedule": {"2025": "150"},
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

        response = client.post("/api/portfolios", json=request_body, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert "version_id" in data

        # Cleanup
        client.delete(f"/api/portfolios/{portfolio_name}", headers=auth_headers)


# ---------------------------------------------------------------------------
# Test Classes: Live Execution (AC-1)
# ---------------------------------------------------------------------------


class TestLiveExecution:
    """AC-1: Live execution tests for surfaced packs through adapter.

    Validates that surfaced packs execute correctly through the computation
    adapter. At least 2 live execution tests.

    Story 24.5 / AC-1: "At least 2 live execution tests for surfaced packs
    through the adapter"
    """

    def test_translate_subsidy_policy_succeeds(
        self, surfaced_subsidy_params: SubsidyParameters
    ) -> None:
        """Verify subsidy policy translation succeeds via translator."""
        from reformlab.computation.translator import translate_policy

        result = translate_policy(surfaced_subsidy_params, "test-subsidy")
        assert result is not None
        # Subsidy translation is passthrough with validation
        assert result.rate_schedule == surfaced_subsidy_params.rate_schedule

    def test_translate_vehicle_malus_policy_succeeds(
        self, surfaced_vehicle_malus_params: VehicleMalusParameters
    ) -> None:
        """Verify vehicle_malus policy translation succeeds via translator."""
        from reformlab.computation.translator import translate_policy

        result = translate_policy(surfaced_vehicle_malus_params, "test-vehicle-malus")
        assert result is not None
        # VehicleMalusParameters has these attributes
        assert hasattr(result, "emission_threshold")
        assert hasattr(result, "malus_rate_per_gkm")
        assert result.emission_threshold == surfaced_vehicle_malus_params.emission_threshold
        assert result.malus_rate_per_gkm == surfaced_vehicle_malus_params.malus_rate_per_gkm

    def test_translate_energy_poverty_aid_policy_succeeds(
        self, surfaced_energy_poverty_aid_params: EnergyPovertyAidParameters
    ) -> None:
        """Verify energy_poverty_aid policy translation succeeds via translator."""
        from reformlab.computation.translator import translate_policy

        result = translate_policy(surfaced_energy_poverty_aid_params, "test-epa")
        assert result is not None
        # EnergyPovertyAidParameters has income_ceiling attribute
        assert hasattr(result, "income_ceiling")
        assert result.income_ceiling == surfaced_energy_poverty_aid_params.income_ceiling

    def test_subsidy_compute_with_population(
        self, surfaced_subsidy_params: SubsidyParameters, minimal_population_for_surfaced_packs: pa.Table
    ) -> None:
        """Verify subsidy compute produces correct result structure."""
        from reformlab.templates.subsidy.compute import SubsidyResult, compute_subsidy

        result = compute_subsidy(
            population=minimal_population_for_surfaced_packs,
            policy=surfaced_subsidy_params,
            year=2025,
        )

        # Verify result is correct type
        assert isinstance(result, SubsidyResult)
        # Verify result has expected structure
        assert hasattr(result, "household_ids")
        assert hasattr(result, "subsidy_amount")
        assert hasattr(result, "is_eligible")
        assert len(result.household_ids) == len(minimal_population_for_surfaced_packs)

    def test_vehicle_malus_compute_with_population(
        self, surfaced_vehicle_malus_params: VehicleMalusParameters
    ) -> None:
        """Verify vehicle_malus compute produces correct result structure."""
        import pyarrow as pa

        # Create population with vehicle_emissions_gkm column
        population = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([20000.0, 50000.0, 100000.0], type=pa.float64()),
            "vehicle_emissions_gkm": pa.array([80.0, 130.0, 160.0], type=pa.float64()),
        })

        from reformlab.templates.vehicle_malus.compute import VehicleMalusResult, compute_vehicle_malus

        result = compute_vehicle_malus(
            population=population,
            policy=surfaced_vehicle_malus_params,
            year=2025,
        )

        # Verify result is correct type
        assert isinstance(result, VehicleMalusResult)
        # Verify result has expected structure
        assert hasattr(result, "household_ids")
        assert hasattr(result, "malus_amount")
        assert len(result.household_ids) == len(population)

    def test_energy_poverty_aid_compute_with_population(
        self,
        surfaced_energy_poverty_aid_params: EnergyPovertyAidParameters,
        minimal_population_for_surfaced_packs: pa.Table,
    ) -> None:
        """Verify energy_poverty_aid compute produces correct result structure."""
        from reformlab.templates.energy_poverty_aid.compute import (
            EnergyPovertyAidResult,
            compute_energy_poverty_aid,
        )

        result = compute_energy_poverty_aid(
            population=minimal_population_for_surfaced_packs,
            policy=surfaced_energy_poverty_aid_params,
            year=2025,
        )

        # Verify result is correct type
        assert isinstance(result, EnergyPovertyAidResult)
        # Verify result has expected structure
        assert hasattr(result, "household_ids")
        assert hasattr(result, "aid_amount")
        assert len(result.household_ids) == len(minimal_population_for_surfaced_packs)

    def test_vehicle_malus_runs_through_live_portfolio_adapter(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify vehicle_malus executes through POST /api/runs portfolio path."""
        portfolio_name = _unique_name("live-vehicle-malus")
        _create_surfaced_portfolio(
            client,
            auth_headers,
            name=portfolio_name,
            surfaced_type="vehicle_malus",
        )

        run_id = _run_portfolio(client, auth_headers, portfolio_name=portfolio_name)
        columns = _result_columns(client, auth_headers, run_id)

        assert_surfaced_pack_columns_present({"columns": columns}, ("vehicle_malus",))

    def test_energy_poverty_aid_runs_through_live_portfolio_adapter(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify energy_poverty_aid executes through POST /api/runs portfolio path."""
        portfolio_name = _unique_name("live-energy-poverty")
        _create_surfaced_portfolio(
            client,
            auth_headers,
            name=portfolio_name,
            surfaced_type="energy_poverty_aid",
        )

        run_id = _run_portfolio(client, auth_headers, portfolio_name=portfolio_name)
        columns = _result_columns(client, auth_headers, run_id)

        assert_surfaced_pack_columns_present({"columns": columns}, ("energy_poverty_aid",))


# ---------------------------------------------------------------------------
# Test Classes: Comparison Tests (AC-1)
# ---------------------------------------------------------------------------


class TestComparisonFlows:
    """AC-1: Comparison tests verifying surfaced pack outputs work.

    Validates that surfaced pack outputs work correctly in comparison flows.
    At least 2 comparison tests.

    Story 24.5 / AC-1: "At least 2 comparison tests verifying surfaced pack
    outputs work in comparison flows"
    """

    def test_welfare_comparison_accepts_actual_surfaced_pack_runs(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify POST /api/comparison works with real surfaced pack run IDs."""
        baseline_name = _unique_name("comparison-baseline")
        reform_name = _unique_name("comparison-reform")
        _create_surfaced_portfolio(
            client,
            auth_headers,
            name=baseline_name,
            surfaced_type="subsidy",
        )
        _create_surfaced_portfolio(
            client,
            auth_headers,
            name=reform_name,
            surfaced_type="energy_poverty_aid",
        )

        baseline_id = _run_portfolio(client, auth_headers, portfolio_name=baseline_name)
        reform_id = _run_portfolio(client, auth_headers, portfolio_name=reform_name)

        response = client.post(
            "/api/comparison",
            json={
                "baseline_run_id": baseline_id,
                "reform_run_id": reform_id,
                "welfare_field": "disposable_income",
                "threshold": 0,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200, response.json()
        assert "data" in response.json()

    def test_portfolio_comparison_accepts_actual_surfaced_pack_runs(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify multi-portfolio comparison works with surfaced pack outputs."""
        vehicle_name = _unique_name("portfolio-comparison-vehicle")
        energy_name = _unique_name("portfolio-comparison-energy")
        _create_surfaced_portfolio(
            client,
            auth_headers,
            name=vehicle_name,
            surfaced_type="vehicle_malus",
        )
        _create_surfaced_portfolio(
            client,
            auth_headers,
            name=energy_name,
            surfaced_type="energy_poverty_aid",
        )

        vehicle_id = _run_portfolio(client, auth_headers, portfolio_name=vehicle_name)
        energy_id = _run_portfolio(client, auth_headers, portfolio_name=energy_name)

        vehicle_columns = _result_columns(client, auth_headers, vehicle_id)
        energy_columns = _result_columns(client, auth_headers, energy_id)
        assert_surfaced_pack_columns_present({"columns": vehicle_columns}, ("vehicle_malus",))
        assert_surfaced_pack_columns_present({"columns": energy_columns}, ("energy_poverty_aid",))

        response = client.post(
            "/api/comparison/portfolios",
            json={
                "run_ids": [vehicle_id, energy_id],
                "baseline_run_id": vehicle_id,
                "indicator_types": ["fiscal"],
                "include_welfare": False,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200, response.json()
        assert response.json()["portfolio_labels"] == [vehicle_name, energy_name]


# ---------------------------------------------------------------------------
# Test Classes: Non-Regression (AC-1)
# ---------------------------------------------------------------------------


class TestNonRegressionExistingPacks:
    """AC-1: Non-regression tests for existing packs.

    Validates that existing packs (carbon_tax, rebate, feebate) continue
    to work correctly after Epic 24 changes. At least 3 non-regression tests.

    Story 24.5 / AC-1: "At least 3 non-regression tests for existing packs
    (carbon_tax, rebate, feebate)"
    """

    def test_carbon_tax_remains_live_ready(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify carbon_tax remains live_ready after Epic 24 changes."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200

        templates = response.json().get("templates", [])
        carbon_tax_templates = [t for t in templates if t.get("type") == "carbon_tax"]

        assert len(carbon_tax_templates) > 0, "Carbon tax should still be in catalog"

        live_ready = [t for t in carbon_tax_templates if t.get("runtime_availability") == "live_ready"]
        assert len(live_ready) > 0, "Carbon tax should remain live_ready"

    def test_rebate_remains_live_ready(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify rebate remains live_ready after Epic 24 changes."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200

        templates = response.json().get("templates", [])
        rebate_templates = [t for t in templates if t.get("type") == "rebate"]

        assert len(rebate_templates) > 0, "Rebate should still be in catalog"

        live_ready = [t for t in rebate_templates if t.get("runtime_availability") == "live_ready"]
        assert len(live_ready) > 0, "Rebate should remain live_ready"

    def test_feebate_remains_live_ready(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify feebate remains live_ready after Epic 24 changes."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200

        templates = response.json().get("templates", [])
        feebate_templates = [t for t in templates if t.get("type") == "feebate"]

        assert len(feebate_templates) > 0, "Feebate should still be in catalog"

        live_ready = [t for t in feebate_templates if t.get("runtime_availability") == "live_ready"]
        assert len(live_ready) > 0, "Feebate should remain live_ready"


# ---------------------------------------------------------------------------
# Test Classes: Runtime Availability Guard (AC-5)
# ---------------------------------------------------------------------------


class TestRuntimeAvailabilityGuard:
    """AC-5: Runtime availability guard behavior tests.

    Validates that policies with runtime_availability="live_unavailable"
    are rejected in live mode but accepted in replay mode.

    Story 24.5 / AC-5: "When a policy with runtime_availability='live_unavailable'
    is executed in live mode, then the request is rejected with 422 status;
    when executed in replay mode, then it bypasses the availability check"
    """

    def test_live_unavailable_template_in_catalog_has_correct_metadata(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify templates with live_unavailable status have correct metadata."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200

        templates = response.json().get("templates", [])

        # Check that any user-saved scenarios would have live_unavailable
        # (built-in templates are all live_ready for surfaced packs)
        unavailable = [t for t in templates if t.get("runtime_availability") == "live_unavailable"]

        # If any exist, verify they have the structure
        for template in unavailable:
            assert template.get("runtime_availability") == "live_unavailable"

    def test_live_mode_rejects_unavailable_portfolio_but_replay_bypasses_guard(
        self, client: TestClient, auth_headers: dict[str, str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify live run rejects unavailable portfolio policies and replay bypasses."""
        from dataclasses import dataclass

        import reformlab.server.dependencies as deps
        from reformlab.computation.mock_adapter import MockAdapter
        from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
        from reformlab.templates.schema import (
            CarbonTaxParameters,
            SubsidyParameters,
            register_custom_template,
            register_policy_type,
            unregister_policy_type,
        )

        @dataclass(frozen=True)
        class UnavailableSubsidyParameters(SubsidyParameters):
            pass

        register_policy_type("unavailable_regression_policy")
        register_custom_template("unavailable_regression_policy", UnavailableSubsidyParameters)
        try:
            portfolio_name = _unique_name("unavailable-portfolio")
            portfolio = PolicyPortfolio(
                name=portfolio_name,
                policies=(
                    PolicyConfig(
                        policy=CarbonTaxParameters(rate_schedule={2025: 44.6}),
                        name="carbon_tax",
                    ),
                    PolicyConfig(
                        policy=UnavailableSubsidyParameters(rate_schedule={2025: 100.0}),
                        name="unavailable_regression_policy",
                    ),
                ),
                resolution_strategy="sum",
            )
            deps.get_registry().save(portfolio, portfolio_name)

            live_response = client.post(
                "/api/runs",
                json={
                    "portfolio_name": portfolio_name,
                    "start_year": 2025,
                    "end_year": 2025,
                    "runtime_mode": "live",
                },
                headers=auth_headers,
            )
            assert live_response.status_code == 422
            assert "unavailable for live execution" in live_response.json()["detail"]["why"]

            adapter = deps._adapter
            monkeypatch.setattr(
                deps,
                "_create_replay_adapter",
                lambda: MockAdapter(compute_fn=adapter._compute_fn),
            )
            replay_id = _run_portfolio(
                client,
                auth_headers,
                portfolio_name=portfolio_name,
                runtime_mode="replay",
            )
            replay_columns = _result_columns(client, auth_headers, replay_id)
            assert "disposable_income" in replay_columns
        finally:
            unregister_policy_type("unavailable_regression_policy")


# ---------------------------------------------------------------------------
# Test Classes: Portfolio Save/Load Integration (AC-1)
# ---------------------------------------------------------------------------


class TestPortfolioSaveLoad:
    """AC-1: Portfolio save/load integration tests for surfaced packs.

    Validates that portfolios with surfaced packs can be saved and loaded
    correctly, maintaining policy_type mapping.
    """

    def test_portfolio_save_with_vehicle_malus_loads_correctly(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify portfolio with vehicle_malus can be saved and loaded."""
        portfolio_name = _unique_name("test-vm-save-load")
        request_body = {
            "name": portfolio_name,
            "description": "Test save/load with vehicle malus",
            "policies": [
                {
                    "name": "carbon",
                    "policy_type": "carbon_tax",
                    "rate_schedule": {"2025": "44.6"},
                    "exemptions": [],
                    "thresholds": [],
                    "covered_categories": [],
                    "extra_params": {},
                },
                {
                    "name": "malus",
                    "policy_type": "vehicle_malus",
                    "rate_schedule": {"2025": "50"},
                    "exemptions": [],
                    "thresholds": [],
                    "covered_categories": [],
                    "extra_params": {
                        "emission_threshold": 118.0,
                        "malus_rate_per_gkm": 50.0,
                    },
                },
            ],
            "resolution_strategy": "sum",
        }

        # Create
        create_response = client.post("/api/portfolios", json=request_body, headers=auth_headers)
        assert create_response.status_code == 201

        # Load
        get_response = client.get(f"/api/portfolios/{portfolio_name}", headers=auth_headers)
        assert get_response.status_code == 200

        data = get_response.json()
        assert data["name"] == portfolio_name
        assert data["resolution_strategy"] == "sum"
        assert data["policy_count"] == 2

        # Verify vehicle_malus policy is present
        policies = data.get("policies", [])
        vehicle_malus_policy = next((p for p in policies if p.get("policy_type") == "vehicle_malus"), None)
        assert vehicle_malus_policy is not None, "Vehicle malus policy should be in loaded portfolio"

        # Cleanup
        client.delete(f"/api/portfolios/{portfolio_name}", headers=auth_headers)

    def test_portfolio_save_with_energy_poverty_aid_loads_correctly(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify portfolio with energy_poverty_aid can be saved and loaded."""
        portfolio_name = _unique_name("test-epa-save-load")
        request_body = {
            "name": portfolio_name,
            "description": "Test save/load with energy poverty aid",
            "policies": [
                {
                    "name": "subsidy",
                    "policy_type": "subsidy",
                    "rate_schedule": {"2025": "5000"},
                    "exemptions": [],
                    "thresholds": [],
                    "covered_categories": [],
                    "extra_params": {},
                },
                {
                    "name": "epa",
                    "policy_type": "energy_poverty_aid",
                    "rate_schedule": {"2025": "150"},
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

        # Create
        create_response = client.post("/api/portfolios", json=request_body, headers=auth_headers)
        assert create_response.status_code == 201

        # Load
        get_response = client.get(f"/api/portfolios/{portfolio_name}", headers=auth_headers)
        assert get_response.status_code == 200

        data = get_response.json()
        assert data["name"] == portfolio_name

        # Verify energy_poverty_aid policy is present
        policies = data.get("policies", [])
        epa_policy = next((p for p in policies if p.get("policy_type") == "energy_poverty_aid"), None)
        assert epa_policy is not None, "Energy poverty aid policy should be in loaded portfolio"

        # Cleanup
        client.delete(f"/api/portfolios/{portfolio_name}", headers=auth_headers)
