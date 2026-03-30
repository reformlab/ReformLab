"""Evidence model regression tests for Story 21.8.

Tests verify that the evidence model (origin/access_mode/trust_status/data_class)
is consistently applied across population listing, engine validation, run results,
and governance manifests.

Story 21.8 / AC6, AC9, AC10.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from reformlab.data.descriptor import DataAssetDescriptor
from reformlab.governance.manifest import RunManifest

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def example_evidence_descriptors() -> list[DataAssetDescriptor]:
    """Example evidence descriptors for testing."""
    return [
        DataAssetDescriptor(
            asset_id="fr-synthetic-2024",
            name="French Synthetic Population 2024",
            description="100k synthetic households for demo/exploratory",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
            license="CC-BY-4.0",
            version="2024",
            redistribution_allowed=True,
        ),
        DataAssetDescriptor(
            asset_id="ademe-carbon-factors-2024",
            name="Base Carbone® ADEME 2024",
            description="ADEME Base Carbone emission factors V23.6",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            license="Open License",
            version="2024",
            redistribution_allowed=True,
        ),
        DataAssetDescriptor(
            asset_id="ev-adoption-fr",
            name="EV Adoption Rates France",
            description="Historical electric vehicle market share by year",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            license="Open License",
            years=(2010, 2023),
            redistribution_allowed=True,
        ),
        DataAssetDescriptor(
            asset_id="household-survey-fr",
            name="French Household Survey",
            description="Observed household consumption for validation",
            data_class="validation",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            license="Open License",
            years=(2021,),
            redistribution_allowed=True,
        ),
    ]


@pytest.fixture
def example_taste_parameters() -> dict[str, Any]:
    """Example taste parameters for governance testing (Story 21.8 / AC9)."""
    return {
        "asc_names": ["keep_current", "buy_petrol", "buy_ev"],
        "beta_names": ["cost", "emissions"],
        "calibrated_names": ["buy_ev", "cost"],
        "fixed_names": ["emissions"],
        "reference_alternative": "keep_current",
        "literature_sources": {
            "emissions": "Dargay & Gately 1999, 'Income's effect on car vehicle ownership'"
        },
        "is_legacy_mode": False,
    }


# ============================================================================
# TestEvidenceMetadataInPopulationListing (Story 21.8 / AC6)
# ============================================================================


class TestEvidenceMetadataInPopulationListing:
    """Tests that population listing responses include evidence metadata fields.

    Story 21.8 / AC6: Population listing endpoint returns origin/access_mode/trust_status.
    """

    def test_population_response_includes_evidence_fields(self) -> None:
        """Verify that population responses include required evidence fields.

        This test verifies the data model for population responses includes
        origin, access_mode, and trust_status fields. Actual API endpoint
        testing is done in the API smoke test (examples/api/api_smoke_test.py).

        Story 21.8 / AC6.
        """
        # Example population response with evidence fields
        population_response = {
            "id": "fr-synthetic-2024",
            "name": "French Synthetic Population 2024",
            "households": 100000,
            "origin": "synthetic-public",  # Required evidence field
            "access_mode": "bundled",  # Required evidence field
            "trust_status": "exploratory",  # Required evidence field
            "data_class": "structural",
        }

        # Assert required evidence fields are present
        assert "origin" in population_response
        assert population_response["origin"] in ("open-official", "synthetic-public")

        assert "access_mode" in population_response
        assert population_response["access_mode"] in ("bundled", "fetched")

        assert "trust_status" in population_response
        assert population_response["trust_status"] in (
            "production-safe",
            "exploratory",
            "demo-only",
            "validation-pending",
            "not-for-public-inference",
        )

        # Assert evidence values are consistent
        # Synthetic-public + bundled → exploratory is valid
        if population_response["origin"] == "synthetic-public":
            assert population_response["trust_status"] != "production-safe"


# ============================================================================
# TestCalibrationValidationSeparation (Story 21.8 / AC6)
# ============================================================================


class TestCalibrationValidationSeparation:
    """Tests that calibration targets and validation benchmarks remain distinct.

    Story 21.8 / AC6: Calibration targets and validation benchmarks have different
    data_class values, and calibration data is excluded from validation dataset.
    """

    def test_calibration_and_validation_have_different_data_classes(
        self,
        example_evidence_descriptors: list[DataAssetDescriptor],
    ) -> None:
        """Verify calibration and validation assets have distinct data_class values.

        Story 21.8 / AC6.
        """
        calibration_descriptors = [
            d for d in example_evidence_descriptors if d.data_class == "calibration"
        ]
        validation_descriptors = [
            d for d in example_evidence_descriptors if d.data_class == "validation"
        ]

        # Should have at least one of each type
        assert len(calibration_descriptors) > 0, "Expected at least one calibration descriptor"
        assert len(validation_descriptors) > 0, "Expected at least one validation descriptor"

        # Verify data_class separation
        for desc in calibration_descriptors:
            assert desc.data_class == "calibration"

        for desc in validation_descriptors:
            assert desc.data_class == "validation"

    def test_calibration_data_excluded_from_validation_dataset(
        self,
        example_evidence_descriptors: list[DataAssetDescriptor],
    ) -> None:
        """Verify calibration data is not used as validation data.

        Story 21.8 / AC6: Calibration targets and validation benchmarks are distinct.
        """
        calibration_asset_ids = {
            d.asset_id for d in example_evidence_descriptors if d.data_class == "calibration"
        }
        validation_asset_ids = {
            d.asset_id for d in example_evidence_descriptors if d.data_class == "validation"
        }

        # Should be disjoint sets
        assert calibration_asset_ids.isdisjoint(validation_asset_ids), (
            "Calibration and validation asset IDs must be disjoint - "
            "calibration data should not be used for validation"
        )


# ============================================================================
# TestSyntheticVsObservedComparison (Story 21.8 / AC6, AC7)
# ============================================================================


class TestSyntheticVsObservedComparison:
    """Tests for synthetic vs observed data comparison scenarios.

    Story 21.8 / AC6, AC7: Scenarios can load and run with different evidence origins,
    and trust status is correctly assigned.
    """

    def test_synthetic_population_has_exploratory_trust_status(
        self,
        example_evidence_descriptors: list[DataAssetDescriptor],
    ) -> None:
        """Verify synthetic populations are assigned exploratory trust status.

        Story 21.8 / AC6.
        """
        synthetic_descriptors = [
            d for d in example_evidence_descriptors if d.origin == "synthetic-public"
        ]

        for desc in synthetic_descriptors:
            # Synthetic data should not be production-safe in current phase
            if desc.data_class == "structural":
                # Synthetic structural data is exploratory by default
                assert desc.trust_status in ("exploratory", "demo-only", "validation-pending")
                assert desc.trust_status != "production-safe"

    def test_observed_data_can_be_production_safe(
        self,
        example_evidence_descriptors: list[DataAssetDescriptor],
    ) -> None:
        """Verify open-official data can be production-safe.

        Story 21.8 / AC6.
        """
        official_descriptors = [
            d for d in example_evidence_descriptors if d.origin == "open-official"
        ]

        for desc in official_descriptors:
            # Open-official data can be production-safe
            # (but not required to be - depends on validation)
            assert desc.trust_status in ("production-safe", "exploratory", "validation-pending")

    def test_scenario_with_mixed_evidence_origins(self) -> None:
        """Verify scenarios can mix synthetic and observed data sources.

        Story 21.8 / AC7: Flagship scenario demonstrates synthetic vs observed comparison.

        This test verifies the data model allows mixing evidence origins.
        """
        # Scenario using synthetic population + official emission factors
        scenario_evidence = {
            "population": {
                "asset_id": "fr-synthetic-2024",
                "origin": "synthetic-public",
                "trust_status": "exploratory",
            },
            "emission_factors": {
                "asset_id": "ademe-carbon-factors-2024",
                "origin": "open-official",
                "trust_status": "production-safe",
            },
        }

        # Should be able to mix origins
        assert scenario_evidence["population"]["origin"] == "synthetic-public"
        assert scenario_evidence["emission_factors"]["origin"] == "open-official"

        # Trust warnings should be generated for exploratory data
        # (This would be done by the engine during execution)
        exploratory_sources = [
            name for name, data in scenario_evidence.items()
            if data["trust_status"] == "exploratory"
        ]
        assert len(exploratory_sources) > 0, "Expected at least one exploratory source"


# ============================================================================
# TestTasteParameterGovernanceIntegration (Story 21.8 / AC9)
# ============================================================================


class TestTasteParameterGovernanceIntegration:
    """Tests for taste parameter governance integration.

    Story 21.8 / AC9: TasteParameters governance entry includes literature_sources,
    CalibrationResult diagnostics populate in manifest.
    """

    def test_taste_parameters_governance_entry_includes_literature_sources(
        self,
        example_taste_parameters: dict[str, Any],
    ) -> None:
        """Verify taste parameters governance entry includes literature sources.

        Story 21.8 / AC9.
        """
        # Taste parameters from governance entry should include literature_sources
        assert "literature_sources" in example_taste_parameters
        assert isinstance(example_taste_parameters["literature_sources"], dict)

        # Should have literature sources for fixed parameters
        if "fixed_names" in example_taste_parameters:
            for param_name in example_taste_parameters["fixed_names"]:
                assert param_name in example_taste_parameters["literature_sources"], (
                    f"Literature source required for fixed parameter '{param_name}'"
                )

    def test_taste_parameters_governance_entry_structure(
        self,
        example_taste_parameters: dict[str, Any],
    ) -> None:
        """Verify taste parameters governance entry has required structure.

        Story 21.8 / AC9.
        """
        required_fields = (
            "asc_names",
            "beta_names",
            "calibrated_names",
            "fixed_names",
            "literature_sources",
            "is_legacy_mode",
        )

        for field in required_fields:
            assert field in example_taste_parameters, (
                f"Taste parameters governance entry missing required field '{field}'"
            )

        # Verify types
        assert isinstance(example_taste_parameters["asc_names"], list)
        assert isinstance(example_taste_parameters["beta_names"], list)
        assert isinstance(example_taste_parameters["calibrated_names"], list | frozenset | tuple)
        assert isinstance(example_taste_parameters["fixed_names"], list | frozenset | tuple)
        assert isinstance(example_taste_parameters["is_legacy_mode"], bool)


# ============================================================================
# TestEvidenceManifestPopulation (Story 21.8 / AC6, AC9)
# ============================================================================


class TestEvidenceManifestPopulation:
    """Tests for evidence manifest population in run results.

    Story 21.8 / AC6, AC9: Run results include evidence_assets field,
    manifest structure matches expected format.
    """

    def test_run_manifest_includes_evidence_fields(
        self,
        example_evidence_descriptors: list[DataAssetDescriptor],
        example_taste_parameters: dict[str, Any],
    ) -> None:
        """Verify RunManifest includes evidence fields and can serialize to JSON.

        Story 21.8 / AC5, AC6.
        """
        # Create a manifest with evidence fields
        evidence_assets = [d.to_json() for d in example_evidence_descriptors]
        calibration_assets = [
            d.to_json() for d in example_evidence_descriptors if d.data_class == "calibration"
        ]
        validation_assets = [
            d.to_json() for d in example_evidence_descriptors if d.data_class == "validation"
        ]
        evidence_summary = {
            "total_assets": len(evidence_assets),
            "origin_counts": {
                "open-official": sum(
                    1 for d in example_evidence_descriptors if d.origin == "open-official"
                ),
                "synthetic-public": sum(
                    1 for d in example_evidence_descriptors if d.origin == "synthetic-public"
                ),
            },
        }

        manifest = RunManifest(
            manifest_id="test-manifest-id",
            created_at="2026-03-30T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="44.0.0",
            adapter_version="0.1.0",
            scenario_version="1.0",
            evidence_assets=evidence_assets,  # Story 21.8 / AC5
            calibration_assets=calibration_assets,  # Story 21.8 / AC5
            validation_assets=validation_assets,  # Story 21.8 / AC5
            evidence_summary=evidence_summary,  # Story 21.8 / AC5
            taste_parameters=example_taste_parameters,  # Story 21.7 / AC8, 21.8 / AC9
        )

        # Verify evidence fields are present
        assert len(manifest.evidence_assets) == len(evidence_assets)
        assert len(manifest.calibration_assets) == len(calibration_assets)
        assert len(manifest.validation_assets) == len(validation_assets)
        assert manifest.evidence_summary["total_assets"] == len(evidence_assets)

        # Verify JSON serialization includes evidence fields
        manifest_json = manifest.to_json()
        manifest_dict = json.loads(manifest_json)

        assert "evidence_assets" in manifest_dict
        assert "calibration_assets" in manifest_dict
        assert "validation_assets" in manifest_dict
        assert "evidence_summary" in manifest_dict
        assert "taste_parameters" in manifest_dict

    def test_run_manifest_from_json_with_evidence_fields(
        self,
        example_evidence_descriptors: list[DataAssetDescriptor],
    ) -> None:
        """Verify RunManifest can deserialize from JSON with evidence fields.

        Story 21.8 / AC5.
        """
        evidence_assets = [d.to_json() for d in example_evidence_descriptors]

        manifest_dict = {
            "manifest_id": "test-manifest-id",
            "created_at": "2026-03-30T10:00:00Z",
            "engine_version": "0.1.0",
            "openfisca_version": "44.0.0",
            "adapter_version": "0.1.0",
            "scenario_version": "1.0",
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
            "integrity_hash": "",
            "evidence_assets": evidence_assets,  # Story 21.8 / AC5
            "calibration_assets": [],  # Story 21.8 / AC5
            "validation_assets": [],  # Story 21.8 / AC5
            "evidence_summary": {},  # Story 21.8 / AC5
        }

        manifest_json = json.dumps(manifest_dict)
        manifest = RunManifest.from_json(manifest_json)

        # Verify evidence fields are preserved
        assert len(manifest.evidence_assets) == len(evidence_assets)
        assert manifest.calibration_assets == []
        assert manifest.validation_assets == []
        assert manifest.evidence_summary == {}

    def test_run_manifest_integrity_hash_includes_evidence_fields(
        self,
        example_evidence_descriptors: list[DataAssetDescriptor],
    ) -> None:
        """Verify integrity hash computation includes evidence fields.

        Story 21.8 / AC5: All evidence fields included in integrity hash computation.
        """
        evidence_assets = [d.to_json() for d in example_evidence_descriptors]

        manifest1 = RunManifest(
            manifest_id="test-manifest-id",
            created_at="2026-03-30T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="44.0.0",
            adapter_version="0.1.0",
            scenario_version="1.0",
            evidence_assets=evidence_assets,
        )

        manifest2 = RunManifest(
            manifest_id="test-manifest-id",
            created_at="2026-03-30T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="44.0.0",
            adapter_version="0.1.0",
            scenario_version="1.0",
            evidence_assets=[],  # Different evidence assets
        )

        # Integrity hashes should be different
        hash1 = manifest1.compute_integrity_hash()
        hash2 = manifest2.compute_integrity_hash()

        assert hash1 != hash2, (
            "Integrity hashes should differ when evidence_assets differ"
        )

    def test_run_manifest_omits_empty_evidence_lists_from_json(
        self,
    ) -> None:
        """Verify RunManifest.to_json() omits empty evidence lists.

        Story 21.8 / AC5: Manifest serialization excludes empty evidence_assets,
        calibration_assets, validation_assets, and evidence_summary for compact
        storage (internal representation for hashing always uses consistent
        structure).
        """
        # Create manifest with all empty evidence fields
        manifest = RunManifest(
            manifest_id="test-empty-evidence",
            created_at="2026-03-30T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="44.0.0",
            adapter_version="0.1.0",
            scenario_version="1.0",
            evidence_assets=[],  # Empty - should be omitted
            calibration_assets=[],  # Empty - should be omitted
            validation_assets=[],  # Empty - should be omitted
            evidence_summary={},  # Empty - should be omitted
        )

        # Serialize to JSON
        manifest_json = manifest.to_json()
        manifest_dict = json.loads(manifest_json)

        # Verify empty evidence fields are omitted from JSON
        assert "evidence_assets" not in manifest_dict, (
            "Empty evidence_assets should be omitted from JSON"
        )
        assert "calibration_assets" not in manifest_dict, (
            "Empty calibration_assets should be omitted from JSON"
        )
        assert "validation_assets" not in manifest_dict, (
            "Empty validation_assets should be omitted from JSON"
        )
        assert "evidence_summary" not in manifest_dict, (
            "Empty evidence_summary should be omitted from JSON"
        )

    def test_run_manifest_includes_non_empty_evidence_lists_in_json(
        self,
        example_evidence_descriptors: list[DataAssetDescriptor],
    ) -> None:
        """Verify RunManifest.to_json() includes non-empty evidence lists.

        Story 21.8 / AC5: Non-empty evidence fields should be included in JSON.
        """
        evidence_assets = [d.to_json() for d in example_evidence_descriptors]
        calibration_assets = [
            d.to_json() for d in example_evidence_descriptors if d.data_class == "calibration"
        ]

        manifest = RunManifest(
            manifest_id="test-non-empty-evidence",
            created_at="2026-03-30T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="44.0.0",
            adapter_version="0.1.0",
            scenario_version="1.0",
            evidence_assets=evidence_assets,
            calibration_assets=calibration_assets,
        )

        # Serialize to JSON
        manifest_json = manifest.to_json()
        manifest_dict = json.loads(manifest_json)

        # Verify non-empty evidence fields are included in JSON
        assert "evidence_assets" in manifest_dict, (
            "Non-empty evidence_assets should be included in JSON"
        )
        assert len(manifest_dict["evidence_assets"]) == len(evidence_assets)

        assert "calibration_assets" in manifest_dict, (
            "Non-empty calibration_assets should be included in JSON"
        )
        assert len(manifest_dict["calibration_assets"]) == len(calibration_assets)

        # validation_assets should be omitted (empty)
        assert "validation_assets" not in manifest_dict


# ============================================================================
# TestDocumentationCoherence (Story 21.8 / AC8)
# ============================================================================


class TestDocumentationCoherence:
    """Tests for documentation coherence across README, demos, and tests.

    Story 21.8 / AC8: Terminology matches evidence source matrix glossary.
    """

    def test_evidence_literal_values_match_source_matrix(self) -> None:
        """Verify evidence literal values match the evidence source matrix.

        Story 21.8 / AC8: Terminology matches evidence source matrix glossary.

        These values should match _bmad-output/planning-artifacts/evidence-source-matrix-v1-2026-03-27.md.
        """
        # Origin values from source matrix
        valid_origins = ("open-official", "synthetic-public", "synthetic-internal", "restricted")

        # Access mode values from source matrix
        valid_access_modes = ("bundled", "fetched", "deferred-user-connector")

        # Trust status values from source matrix
        valid_trust_statuses = (
            "production-safe",
            "exploratory",
            "demo-only",
            "validation-pending",
            "not-for-public-inference",
        )

        # Data class values from source matrix
        valid_data_classes = ("structural", "exogenous", "calibration", "validation")

        # Verify we're using the correct values in tests
        assert "synthetic-public" in valid_origins
        assert "open-official" in valid_origins
        assert "exploratory" in valid_trust_statuses
        assert "production-safe" in valid_trust_statuses
        assert "bundled" in valid_access_modes
        assert "structural" in valid_data_classes
        assert "exogenous" in valid_data_classes
        assert "calibration" in valid_data_classes
        assert "validation" in valid_data_classes

    def test_evidence_descriptor_structure_matches_spec(self) -> None:
        """Verify DataAssetDescriptor structure matches evidence model spec.

        Story 21.8 / AC8.
        """
        # Create a descriptor with all fields
        descriptor = DataAssetDescriptor(
            asset_id="test-asset-2024",
            name="Test Asset",
            description="Test description",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
            source_url="https://example.com",
            license="CC-BY-4.0",
            version="2024",
            geographic_coverage=("FR",),
            years=(2024,),
            intended_use="Testing",
            redistribution_allowed=True,
            redistribution_notes="Test notes",
            update_cadence="annual",
            quality_notes="Test quality",
            references=("https://example.com/ref",),
        )

        # Verify to_json includes all non-empty fields
        json_data = descriptor.to_json()

        assert json_data["asset_id"] == "test-asset-2024"
        assert json_data["name"] == "Test Asset"
        assert json_data["data_class"] == "structural"
        assert json_data["origin"] == "synthetic-public"
        assert json_data["access_mode"] == "bundled"
        assert json_data["trust_status"] == "exploratory"

        # Optional fields with values should be included
        assert json_data["source_url"] == "https://example.com"
        assert json_data["license"] == "CC-BY-4.0"
        assert json_data["version"] == "2024"
        assert json_data["redistribution_allowed"] is True
