# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Shared fixtures for surfaced pack regression tests — Story 24.5.

This module provides reusable fixtures and helpers for testing surfaced
policy packs (subsidy, vehicle_malus, energy_poverty_aid) that were
added to the live policy catalog in Epic 24.

These fixtures are designed to be reusable for future pack additions,
providing a template pattern for validating new policy types against
the catalog, portfolio, execution, and comparison flows.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from reformlab.templates.energy_poverty_aid.compute import EnergyPovertyAidParameters
    from reformlab.templates.schema import SubsidyParameters
    from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters


# ---------------------------------------------------------------------------
# Surfaced Pack Policy Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def surfaced_subsidy_params() -> SubsidyParameters:
    """Subsidy parameters for surfaced pack testing.

    Returns a SubsidyParameters instance with a simple rate_schedule
    suitable for regression tests. This fixture can be used as a
    template for creating surfaced pack fixtures for future policy types.

    Story 24.5 / AC-1, #4: Provides reusable fixture pattern for
    future pack expansion work.
    """
    from reformlab.templates.schema import SubsidyParameters

    return SubsidyParameters(
        rate_schedule={2025: 5000.0},
    )


@pytest.fixture()
def surfaced_vehicle_malus_params() -> VehicleMalusParameters:
    """Vehicle Malus parameters for surfaced pack testing.

    Returns a VehicleMalusParameters instance with typical French-style
    emissions threshold and malus rate. This fixture demonstrates the
    pattern for surfaced packs with additional parameters beyond
    rate_schedule.

    Story 24.5 / AC-1, #4: Provides reusable fixture pattern for
    future pack expansion work.
    """
    from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters

    return VehicleMalusParameters(
        emission_threshold=118.0,
        malus_rate_per_gkm=50.0,
        rate_schedule={2025: 50.0},
    )


@pytest.fixture()
def surfaced_energy_poverty_aid_params() -> EnergyPovertyAidParameters:
    """Energy Poverty Aid parameters for surfaced pack testing.

    Returns an EnergyPovertyAidParameters instance demonstrating the
    subsidy-family pattern with income ceiling and energy share threshold.

    Story 24.5 / AC-1, #4: Provides reusable fixture pattern for
    future pack expansion work.
    """
    from reformlab.templates.energy_poverty_aid.compute import EnergyPovertyAidParameters

    return EnergyPovertyAidParameters(
        rate_schedule={2025: 150.0},
        income_ceiling=11000.0,
        energy_share_threshold=0.10,
        base_aid_amount=100.0,
    )


# ---------------------------------------------------------------------------
# Population Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def minimal_population_for_surfaced_packs() -> pa.Table:
    """Minimal population table for surfaced pack regression tests.

    Returns a PyArrow table with the minimal required columns for testing
    surfaced packs across subsidy, vehicle_malus, and energy_poverty_aid.

    This fixture is designed to be lightweight (10 households) for fast
    regression test execution while covering the key data requirements:
    - income: Required for subsidy and energy_poverty_aid eligibility
    - vehicle_emissions_gkm: Required for vehicle_malus calculation
    - energy_expenditure: Required for energy_poverty_aid calculation

    Story 24.5 / AC-1, #4: Provides reusable fixture pattern for
    future pack expansion work.
    """
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], type=pa.int64()),
            "income": pa.array(
                [8000.0, 12000.0, 18000.0, 25000.0, 35000.0, 45000.0, 55000.0, 70000.0, 90000.0, 120000.0],
                type=pa.float64(),
            ),
            "vehicle_emissions_gkm": pa.array(
                [100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0, 170.0, 180.0, 200.0],
                type=pa.float64(),
            ),
            "energy_expenditure": pa.array(
                [600.0, 800.0, 500.0, 1000.0, 1500.0, 400.0, 2000.0, 700.0, 5000.0, 720.0],
                type=pa.float64(),
            ),
        }
    )


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def assert_surfaced_pack_columns_present(result: Any, policy_types: tuple[str, ...]) -> None:
    """Assert that surfaced pack columns are present in a result table.

    Validates that the normalized output columns for surfaced policy types
    are present in the result. This helper supports column prefix handling
    for portfolio outputs where columns may be prefixed with policy names.

    Args:
        result: A PyArrow Table or similar tabular result with column_names
        policy_types: Tuple of policy type strings to check (e.g., ("subsidy", "vehicle_malus"))

    Raises:
        AssertionError: If any expected column is not found

    Story 24.5 / AC-1, #4: Provides reusable helper for future pack expansion.
    """
    if hasattr(result, "column_names"):
        column_names = list(result.column_names)
    elif isinstance(result, dict) and isinstance(result.get("columns"), list):
        column_names = [str(column) for column in result["columns"]]
    else:
        column_names = list(result.keys())

    expected_columns = {
        "subsidy": ("subsidy", "subsidy_amount"),
        "vehicle_malus": ("vehicle_malus", "malus_amount"),
        "energy_poverty_aid": ("energy_poverty_aid", "aid_amount"),
    }

    def matches_policy_type(column_name: str, policy_type: str) -> bool:
        candidates = expected_columns.get(policy_type, (policy_type,))
        if column_name in candidates:
            return True

        prefix = f"{policy_type}_"
        if not column_name.startswith(prefix):
            return False

        remainder = column_name[len(prefix):]
        parts = remainder.split("_", 1)
        if parts[0].isdigit() and len(parts) == 2:
            remainder = parts[1]
        return remainder in candidates

    missing = []
    for policy_type in policy_types:
        found = any(matches_policy_type(col, policy_type) for col in column_names)
        if not found:
            missing.append(policy_type)

    assert not missing, f"Missing surfaced pack columns: {missing}. Available columns: {column_names}"


def assert_live_ready_metadata(template: dict[str, Any], policy_type: str) -> None:
    """Assert that a template has correct live_ready metadata for surfaced packs.

    Validates that surfaced policy types have:
    - runtime_availability = "live_ready"
    - No availability_reason (None)
    - Correct type field (underscore format)

    Args:
        template: Template dictionary from API response
        policy_type: Expected policy type string (e.g., "vehicle_malus")

    Raises:
        AssertionError: If metadata doesn't match live_ready contract

    Story 24.5 / AC-1, #3: Verifies frontend-backend contract consistency.
    """
    assert template.get("runtime_availability") == "live_ready", (
        f"Policy type '{policy_type}' should be live_ready, "
        f"got '{template.get('runtime_availability')}'"
    )
    assert template.get("availability_reason") is None, (
        f"Policy type '{policy_type}' should have no availability_reason when live_ready"
    )
    assert template.get("type") == policy_type, (
        f"Template type mismatch: expected '{policy_type}', got '{template.get('type')}'"
    )


# ---------------------------------------------------------------------------
# API Testing Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _set_test_password(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the shared password env var for all server tests."""
    monkeypatch.setenv("REFORMLAB_PASSWORD", "test-password-123")


def _surfaced_pack_output(population: Any, policy: Any, period: int) -> pa.Table:
    """Return deterministic adapter output with surfaced pack columns."""
    table = population.primary_table
    row_count = table.num_rows or 3
    household_ids = (
        table.column("household_id")
        if table.num_rows and "household_id" in table.column_names
        else pa.array(range(1, row_count + 1), type=pa.int64())
    )
    incomes = (
        table.column("income")
        if table.num_rows and "income" in table.column_names
        else pa.array([20000.0 + i * 1000.0 for i in range(row_count)], type=pa.float64())
    )
    output = {
        "household_id": household_ids,
        "year": pa.array([period] * row_count, type=pa.int64()),
        "income": incomes,
        "disposable_income": pa.array([19000.0 + i * 1000.0 for i in range(row_count)], type=pa.float64()),
        "carbon_tax": pa.array([100.0 + i for i in range(row_count)], type=pa.float64()),
    }

    policy_name = getattr(policy, "name", "")
    if "subsidy" in policy_name:
        output["subsidy_amount"] = pa.array([500.0] * row_count, type=pa.float64())
    elif "vehicle_malus" in policy_name or "malus" in policy_name:
        output["vehicle_malus"] = pa.array([0.0, 600.0, 1200.0][:row_count], type=pa.float64())
    elif "energy_poverty_aid" in policy_name or "energy" in policy_name:
        output["energy_poverty_aid"] = pa.array([150.0] * row_count, type=pa.float64())

    return pa.table(output)


@pytest.fixture()
def tmp_store(tmp_path: Path) -> Any:
    """ResultStore backed by tmp_path."""
    from reformlab.server.result_store import ResultStore

    return ResultStore(base_dir=tmp_path / "results")


@pytest.fixture()
def client(tmp_path: Path, tmp_store: Any, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Create a FastAPI test client with isolated store, registry, and adapter."""
    import reformlab.server.dependencies as deps
    from reformlab.computation.mock_adapter import MockAdapter
    from reformlab.server.dependencies import ResultCache, get_registry, get_result_cache, get_result_store
    from reformlab.templates.registry import ScenarioRegistry

    registry = ScenarioRegistry(registry_path=tmp_path / "registry")
    adapter = MockAdapter(compute_fn=_surfaced_pack_output)

    monkeypatch.setattr(deps, "_adapter", adapter)
    monkeypatch.setattr(deps, "_result_store", tmp_store)
    monkeypatch.setattr(deps, "_result_cache", ResultCache(max_size=20))
    monkeypatch.setattr(deps, "_registry", registry)
    monkeypatch.setenv("REFORMLAB_ENV", "dev")

    from reformlab.server.app import create_app

    app = create_app()
    app.dependency_overrides[get_result_store] = lambda: tmp_store
    app.dependency_overrides[get_result_cache] = lambda: deps._result_cache
    app.dependency_overrides[get_registry] = lambda: registry
    return TestClient(app)


@pytest.fixture()
def auth_token(client: TestClient) -> str:
    """Authenticate and return a valid session token."""
    response = client.post(
        "/api/auth/login",
        json={"password": "test-password-123"},
    )
    assert response.status_code == 200
    token = response.json()["token"]
    assert isinstance(token, str)
    return token


@pytest.fixture()
def auth_headers(auth_token: str) -> dict[str, str]:
    """Return headers with a valid auth token."""
    return {"Authorization": f"Bearer {auth_token}"}
