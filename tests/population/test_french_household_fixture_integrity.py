# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Semantic integrity checks for French household example source fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from examples.populations import french_household_pipeline as fhp


def test_fixture_loaders_expose_expected_dataset_identity() -> None:
    """Fixture loaders return tables with expected provider/dataset identity."""
    income_loader, income_config = fhp._load_income_source()
    housing_loader, housing_config = fhp._load_housing_source()
    vehicle_loader, vehicle_config = fhp._load_vehicle_source()
    energy_loader, energy_config = fhp._load_energy_source()

    assert income_config.provider == "insee"
    assert income_config.dataset_id == "filosofi_2021_commune"
    pop_income, _ = income_loader.download(income_config)
    assert pop_income.primary_table.num_rows > 0

    assert housing_config.provider == "eurostat"
    assert housing_config.dataset_id == "nrg_d_hhq"
    pop_housing, _ = housing_loader.download(housing_config)
    assert "heating_type" in pop_housing.primary_table.column_names

    assert vehicle_config.provider == "sdes"
    assert vehicle_config.dataset_id == "vehicle_fleet_2023"
    pop_vehicle, _ = vehicle_loader.download(vehicle_config)
    assert "vehicle_type" in pop_vehicle.primary_table.column_names

    assert energy_config.provider == "ademe"
    assert energy_config.dataset_id == "base_carbone_v23"
    pop_energy, _ = energy_loader.download(energy_config)
    assert "carbon_emissions" in pop_energy.primary_table.column_names


@pytest.mark.parametrize(
    ("fixture_name", "original", "replacement", "loader_fn", "expected_fixture_label"),
    [
        (
            "insee_filosofi_2021_fixture.csv",
            ",32000,",
            ",92000,",
            "_load_income_source",
            "insee_filosofi_2021_fixture",
        ),
        (
            "ademe_energy_2023_fixture.csv",
            ",0.227,",
            ",0.027,",
            "_load_energy_source",
            "ademe_energy_2023_fixture",
        ),
    ],
)
def test_semantic_guardrails_reject_mutated_fixture_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    fixture_name: str,
    original: str,
    replacement: str,
    loader_fn: str,
    expected_fixture_label: str,
) -> None:
    """Value-level fixture mutations are rejected before pipeline construction."""
    fixture_dir = tmp_path / "sources"
    shutil.copytree(fhp.FIXTURES_DIR, fixture_dir)

    mutated = fixture_dir / fixture_name
    content = mutated.read_text(encoding="utf-8")
    mutated.write_text(content.replace(original, replacement, 1), encoding="utf-8")

    monkeypatch.setattr(fhp, "FIXTURES_DIR", fixture_dir)
    load = getattr(fhp, loader_fn)

    with pytest.raises(
        ValueError,
        match=rf"semantic integrity check failed for {expected_fixture_label}",
    ):
        load()
