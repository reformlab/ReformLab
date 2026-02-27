"""Test fixtures for governance tests."""

from __future__ import annotations

import pytest

from reformlab.governance import RunManifest


@pytest.fixture
def minimal_manifest() -> RunManifest:
    """Minimal valid manifest with required fields only."""
    return RunManifest(
        manifest_id="test-manifest-001",
        created_at="2026-02-27T10:00:00Z",
        engine_version="0.1.0",
        openfisca_version="40.0.0",
        adapter_version="1.0.0",
        scenario_version="v1.0",
    )


@pytest.fixture
def full_manifest() -> RunManifest:
    """Complete manifest with all fields populated."""
    return RunManifest(
        manifest_id="test-manifest-full-001",
        created_at="2026-02-27T10:00:00Z",
        engine_version="0.1.0",
        openfisca_version="40.0.0",
        adapter_version="1.0.0",
        scenario_version="v1.0",
        data_hashes={
            "population.csv": "a" * 64,
            "emissions.parquet": "b" * 64,
        },
        output_hashes={
            "results/2025.csv": "c" * 64,
            "results/2026.parquet": "d" * 64,
        },
        seeds={
            "master": 42,
            "year_2025": 1001,
            "year_2026": 1002,
        },
        parameters={
            "carbon_tax_rate": 44.6,
            "rebate_amount": 150.0,
            "simulation_years": [2025, 2026, 2027],
        },
        assumptions=[
            {
                "key": "constant_population",
                "value": True,
                "source": "scenario",
                "is_default": True,
            },
            {
                "key": "linear_price_projection",
                "value": True,
                "source": "scenario",
                "is_default": True,
            },
            {
                "key": "no_behavioral_response",
                "value": True,
                "source": "user",
                "is_default": False,
            },
        ],
        mappings=[
            {
                "openfisca_name": "household_income",
                "project_name": "income",
                "direction": "input",
                "source_file": "/path/to/mappings.yaml",
            },
            {
                "openfisca_name": "carbon_tax_paid",
                "project_name": "tax_paid",
                "direction": "output",
            },
        ],
        warnings=[
            "WARNING: Scenario 'test-scenario' (version 'v1.0') is not marked as "
            "validated in registry metadata."
        ],
        step_pipeline=[
            "compute_baseline",
            "apply_carbon_tax",
            "vintage_transition",
            "state_carry_forward",
        ],
    )
