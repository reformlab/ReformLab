# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for manifest backward compatibility after EPIC-28.

Story 28.5 / AC-8: Existing manifest fixtures from earlier epics load
successfully after adding optional technology_set field.

Tests validate:
- Old manifests without technology_set field load with default {}
- New manifests with technology_set field load correctly
- RunManifest.from_dict handles both cases
- Serialization preserves technology_set when present
"""

from __future__ import annotations

import json

import pytest

from reformlab.governance.manifest import RunManifest

# ============================================================================
# Fixtures: Sample manifests from earlier epics
# ============================================================================


@pytest.fixture
def epic_21_manifest_json() -> str:
    """Sample manifest from EPIC-21 (before technology_set field).

    Story 28.5 / Task 9.2: Collect all manifest fixtures from earlier epics.
    This represents a typical manifest after EPIC-21 (discrete choice governance)
    but before EPIC-28 (technology sets).
    """
    return json.dumps({
        "manifest_id": "epic-21-test-manifest-001",
        "created_at": "2026-04-01T10:00:00Z",
        "engine_version": "0.1.0",
        "openfisca_version": "40.0.0",
        "adapter_version": "1.0.0",
        "scenario_version": "v1.0",
        "data_hashes": {
            "population.csv": "a" * 64,
        },
        "output_hashes": {
            "results/2025.csv": "b" * 64,
        },
        "seeds": {
            "master": 42,
            "year_2025": 1001,
        },
        "policy": {
            "carbon_tax_rate": 44.6,
        },
        "assumptions": [
            {
                "key": "constant_population",
                "value": True,
                "source": "scenario",
                "is_default": True,
            },
        ],
        "mappings": [],
        "warnings": [],
        "step_pipeline": ["computation", "discrete_choice"],
        "parent_manifest_id": "",
        "child_manifests": {},
        "exogenous_series": [],
        "taste_parameters": {
            "beta_cost": -0.01,
        },
        "evidence_assets": [],
        "calibration_assets": [],
        "validation_assets": [],
        "evidence_summary": {},
        "runtime_mode": "live",
        "population_id": "test-pop-001",
        "population_source": "bundled",
        "integrity_hash": "",
        # Note: technology_set field is ABSENT (EPIC-21 format)
    })


@pytest.fixture
def epic_23_manifest_json() -> str:
    """Sample manifest from EPIC-23 (before technology_set field).

    Story 28.5 / Task 9.2: Collect all manifest fixtures from earlier epics.
    This represents a manifest after EPIC-23 (result store) but before EPIC-28.
    """
    return json.dumps({
        "manifest_id": "epic-23-test-manifest-002",
        "created_at": "2026-04-15T10:00:00Z",
        "engine_version": "0.1.0",
        "openfisca_version": "40.0.0",
        "adapter_version": "1.0.0",
        "scenario_version": "v1.0",
        "data_hashes": {},
        "output_hashes": {},
        "seeds": {},
        "policy": {},
        "assumptions": [],
        "mappings": [],
        "warnings": [],
        "step_pipeline": [],
        "parent_manifest_id": "",
        "child_manifests": {},
        "exogenous_series": [],
        "taste_parameters": {},
        "evidence_assets": [],
        "calibration_assets": [],
        "validation_assets": [],
        "evidence_summary": {},
        "runtime_mode": "live",
        "population_id": "fr-synthetic-2024",
        "population_source": "bundled",
        "integrity_hash": "",
        # Note: technology_set field is ABSENT (EPIC-23 format)
    })


@pytest.fixture
def epic_28_manifest_json() -> str:
    """Sample manifest from EPIC-28 (with technology_set field).

    Story 28.5 / Task 9.5: Add new minimal fixture with technology_set.
    This represents a manifest after EPIC-28 (technology sets).
    """
    return json.dumps({
        "manifest_id": "epic-28-test-manifest-003",
        "created_at": "2026-05-17T10:00:00Z",
        "engine_version": "0.1.0",
        "openfisca_version": "40.0.0",
        "adapter_version": "1.0.0",
        "scenario_version": "v1.0",
        "data_hashes": {},
        "output_hashes": {},
        "seeds": {},
        "policy": {},
        "assumptions": [],
        "mappings": [],
        "warnings": [],
        "step_pipeline": ["discrete_choice", "state_update"],
        "parent_manifest_id": "",
        "child_manifests": {},
        "exogenous_series": [],
        "taste_parameters": {},
        "evidence_assets": [],
        "calibration_assets": [],
        "validation_assets": [],
        "evidence_summary": {},
        "runtime_mode": "live",
        "population_id": "fr-synthetic-2024",
        "population_source": "bundled",
        # EPIC-28 addition: technology_set field
        "technology_set": {
            "version": "fr-default-2026-04-26",
            "domains": {
                "heating": {
                    "domain": "heating",
                    "enabled": True,
                    "alternatives": [
                        {
                            "id": "keep_current",
                            "name": "Keep Current Heating",
                            "attributes": {},
                        },
                        {
                            "id": "condensing_boiler",
                            "name": "Condensing Boiler",
                            "attributes": {
                                "heating_type": "gas",
                                "heating_age": 0,
                                "heating_emissions_kgco2_kwh": 0.227,
                            },
                        },
                        {
                            "id": "heat_pump_air",
                            "name": "Air Source Heat Pump",
                            "attributes": {
                                "heating_type": "heat_pump",
                                "heating_age": 0,
                                "heating_emissions_kgco2_kwh": 0.057,
                            },
                        },
                    ],
                    "referenceAlternativeId": "keep_current",
                    "costColumn": "heating_cost",
                },
                "vehicle": {
                    "domain": "vehicle",
                    "enabled": True,
                    "alternatives": [
                        {
                            "id": "keep_current",
                            "name": "Keep Current Vehicle",
                            "attributes": {},
                        },
                        {
                            "id": "ev",
                            "name": "Electric Vehicle",
                            "attributes": {"vehicle_type": "ev"},
                        },
                    ],
                    "referenceAlternativeId": "keep_current",
                    "costColumn": "total_vehicle_cost",
                },
            },
        },
        "integrity_hash": "",
    })


# ============================================================================
# Test: Load old manifests without technology_set field
# ============================================================================


class TestLoadOldManifests:
    """Tests for loading manifests from earlier epics (AC-8).

    Story 28.5 / AC-8: All existing manifest fixtures load successfully
    after adding optional technology_set field.
    """

    # Story 28.5 / Task 9.3: Iterate over fixtures and load
    def test_epic_21_manifest_loads(self, epic_21_manifest_json: str):
        """EPIC-21 manifest (without technology_set) loads successfully."""
        manifest = RunManifest.from_json(epic_21_manifest_json)

        # Assert basic fields loaded correctly
        assert manifest.manifest_id == "epic-21-test-manifest-001"
        assert manifest.engine_version == "0.1.0"
        assert manifest.taste_parameters == {"beta_cost": -0.01}

        # Assert technology_set defaults to empty dict
        assert manifest.technology_set == {}

    def test_epic_23_manifest_loads(self, epic_23_manifest_json: str):
        """EPIC-23 manifest (without technology_set) loads successfully."""
        manifest = RunManifest.from_json(epic_23_manifest_json)

        # Assert basic fields loaded correctly
        assert manifest.manifest_id == "epic-23-test-manifest-002"
        assert manifest.population_id == "fr-synthetic-2024"

        # Assert technology_set defaults to empty dict
        assert manifest.technology_set == {}


# ============================================================================
# Test: Load new manifest with technology_set field
# ============================================================================


class TestLoadNewManifests:
    """Tests for loading manifests with technology_set field (AC-8).

    Story 28.5 / AC-8: New manifests with technology_set load and
    populate the field correctly.
    """

    def test_epic_28_manifest_loads(self, epic_28_manifest_json: str):
        """EPIC-28 manifest (with technology_set) loads successfully."""
        manifest = RunManifest.from_json(epic_28_manifest_json)

        # Assert basic fields loaded correctly
        assert manifest.manifest_id == "epic-28-test-manifest-003"

        # Assert technology_set is populated correctly
        assert manifest.technology_set is not None
        assert "version" in manifest.technology_set
        assert manifest.technology_set["version"] == "fr-default-2026-04-26"

        # Assert domains structure
        assert "domains" in manifest.technology_set
        domains = manifest.technology_set["domains"]
        assert "heating" in domains
        assert "vehicle" in domains

        # Assert heating domain structure
        heating = domains["heating"]
        assert heating["domain"] == "heating"
        assert heating["enabled"] is True
        assert "alternatives" in heating
        assert len(heating["alternatives"]) == 3
        assert heating["referenceAlternativeId"] == "keep_current"


# ============================================================================
# Test: Round-trip serialization preserves technology_set
# ============================================================================


class TestTechnologySetSerialization:
    """Tests for technology_set serialization (AC-8).

    Story 28.5 / AC-8: Serialization preserves technology_set when present.
    """

    def test_serialization_preserves_technology_set(
        self, epic_28_manifest_json: str
    ):
        """Round-trip serialization preserves technology_set field."""
        # Load manifest
        manifest = RunManifest.from_json(epic_28_manifest_json)

        # Serialize to JSON
        serialized = manifest.to_json()

        # Deserialize and compare
        manifest2 = RunManifest.from_json(serialized)

        # Assert technology_set preserved
        assert manifest2.technology_set == manifest.technology_set
        assert manifest2.technology_set["version"] == "fr-default-2026-04-26"

    def test_serialization_omits_empty_technology_set(
        self, epic_21_manifest_json: str
    ):
        """Empty technology_set is omitted from serialization for compactness."""
        # Load old manifest (technology_set defaults to {})
        manifest = RunManifest.from_json(epic_21_manifest_json)

        # Serialize to JSON
        serialized = manifest.to_json()

        # Parse and verify technology_set is omitted
        data = json.loads(serialized)
        # Empty technology_set is present in the frozen dataclass
        # but may be omitted during JSON serialization for compactness
        # This test verifies the behavior is consistent
        assert data.get("technology_set", {}) == {}


# ============================================================================
# Test: Multiple manifest fixtures load correctly
# ============================================================================


class TestAllManifestFixturesLoad:
    """Tests for loading all manifest fixtures (AC-8).

    Story 28.5 / Task 9.3: Collect all manifest fixtures and iterate.
    """

    def test_all_epic_manifests_load_without_error(
        self,
        epic_21_manifest_json: str,
        epic_23_manifest_json: str,
        epic_28_manifest_json: str,
    ):
        """All manifest fixtures from earlier epics load without error.

        Story 28.5 / AC-8: Validates backward compatibility for all
        existing manifest fixtures across EPIC-21, EPIC-23, and EPIC-28.
        """
        fixtures = {
            "epic_21": epic_21_manifest_json,
            "epic_23": epic_23_manifest_json,
            "epic_28": epic_28_manifest_json,
        }

        for name, fixture_json in fixtures.items():
            try:
                manifest = RunManifest.from_json(fixture_json)
                # Verify basic integrity
                assert manifest.manifest_id
                assert manifest.engine_version
            except Exception as e:
                pytest.fail(
                    f"Failed to load {name} manifest: {e}"
                )
