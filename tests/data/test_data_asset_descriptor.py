# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for DataAssetDescriptor frozen dataclass.

Story 21.1 - implement-canonical-evidence-asset-descriptor-and-current-phase-source-matrix.
AC1, AC7, AC12, AC14: Construction, JSON round-trip, validation, frozen immutability.
"""

from __future__ import annotations

import pytest

from reformlab.data.descriptor import DataAssetDescriptor
from reformlab.data.errors import EvidenceAssetError


class TestDataAssetDescriptorConstruction:
    """Tests for DataAssetDescriptor construction with all field combinations.

    Story 21.1 / AC1: Required fields, optional fields with defaults.
    """

    def test_create_with_all_required_fields_only(self) -> None:
        """Given only required fields, when created, then defaults are applied."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test Asset",
            description="Test description",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        assert descriptor.asset_id == "test-asset"
        assert descriptor.name == "Test Asset"
        assert descriptor.description == "Test description"
        assert descriptor.data_class == "structural"
        assert descriptor.origin == "synthetic-public"
        assert descriptor.access_mode == "bundled"
        assert descriptor.trust_status == "exploratory"
        # Verify defaults
        assert descriptor.source_url == ""
        assert descriptor.license == ""
        assert descriptor.version == ""
        assert descriptor.geographic_coverage == ()
        assert descriptor.years == ()
        assert descriptor.intended_use == ""
        assert descriptor.redistribution_allowed is False
        assert descriptor.redistribution_notes == ""
        assert descriptor.update_cadence == ""
        assert descriptor.quality_notes == ""
        assert descriptor.references == ()

    def test_create_with_all_fields(self) -> None:
        """Given all fields, when created, then all fields are accessible."""
        descriptor = DataAssetDescriptor(
            asset_id="reformlab-fr-synthetic-2024",
            name="French Synthetic Population 2024",
            description="100k synthetic households for France",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
            source_url="https://example.com/data",
            license="CC-BY-4.0",
            version="2024",
            geographic_coverage=("FR",),
            years=(2024,),
            intended_use="Demo and testing",
            redistribution_allowed=True,
            redistribution_notes="Free to redistribute",
            update_cadence="annual",
            quality_notes="Not calibrated",
            references=("https://example.com/docs",),
        )
        assert descriptor.asset_id == "reformlab-fr-synthetic-2024"
        assert descriptor.name == "French Synthetic Population 2024"
        assert descriptor.description == "100k synthetic households for France"
        assert descriptor.source_url == "https://example.com/data"
        assert descriptor.license == "CC-BY-4.0"
        assert descriptor.version == "2024"
        assert descriptor.geographic_coverage == ("FR",)
        assert descriptor.years == (2024,)
        assert descriptor.intended_use == "Demo and testing"
        assert descriptor.redistribution_allowed is True
        assert descriptor.redistribution_notes == "Free to redistribute"
        assert descriptor.update_cadence == "annual"
        assert descriptor.quality_notes == "Not calibrated"
        assert descriptor.references == ("https://example.com/docs",)


class TestDataAssetDescriptorValidation:
    """Tests for DataAssetDescriptor validation in __post_init__.

    Story 21.1 / AC7, AC14: Validation of required fields, literal values,
    and cross-field combinations.
    """

    def test_empty_required_field_raises_error(self) -> None:
        """Given empty required field, when created, then raises EvidenceAssetError."""
        with pytest.raises(EvidenceAssetError, match="asset_id must be a non-empty string"):
            DataAssetDescriptor(
                asset_id="",  # empty
                name="Test",
                description="Test",
                data_class="structural",
                origin="synthetic-public",
                access_mode="bundled",
                trust_status="exploratory",
            )

    def test_whitespace_only_required_field_raises_error(self) -> None:
        """Given whitespace-only required field, when created, then raises EvidenceAssetError."""
        with pytest.raises(EvidenceAssetError, match="name must be a non-empty string"):
            DataAssetDescriptor(
                asset_id="test",
                name="   ",  # whitespace only
                description="Test",
                data_class="structural",
                origin="synthetic-public",
                access_mode="bundled",
                trust_status="exploratory",
            )

    def test_invalid_origin_literal_raises_error(self) -> None:
        """Given invalid origin value, when created, then raises EvidenceAssetError."""
        with pytest.raises(EvidenceAssetError, match="origin.*is not a valid DataAssetOrigin"):
            DataAssetDescriptor(
                asset_id="test",
                name="Test",
                description="Test",
                data_class="structural",
                origin="invalid-origin",  # type: ignore[arg-type]
                access_mode="bundled",
                trust_status="exploratory",
            )

    def test_invalid_access_mode_literal_raises_error(self) -> None:
        """Given invalid access_mode value, when created, then raises EvidenceAssetError."""
        with pytest.raises(EvidenceAssetError, match="access_mode.*is not a valid DataAssetAccessMode"):
            DataAssetDescriptor(
                asset_id="test",
                name="Test",
                description="Test",
                data_class="structural",
                origin="synthetic-public",
                access_mode="invalid-mode",  # type: ignore[arg-type]
                trust_status="exploratory",
            )

    def test_invalid_trust_status_literal_raises_error(self) -> None:
        """Given invalid trust_status value, when created, then raises EvidenceAssetError."""
        with pytest.raises(EvidenceAssetError, match="trust_status.*is not a valid DataAssetTrustStatus"):
            DataAssetDescriptor(
                asset_id="test",
                name="Test",
                description="Test",
                data_class="structural",
                origin="synthetic-public",
                access_mode="bundled",
                trust_status="invalid-status",  # type: ignore[arg-type]
            )

    def test_invalid_data_class_literal_raises_error(self) -> None:
        """Given invalid data_class value, when created, then raises EvidenceAssetError."""
        with pytest.raises(EvidenceAssetError, match="data_class.*is not a valid DataAssetClass"):
            DataAssetDescriptor(
                asset_id="test",
                name="Test",
                description="Test",
                data_class="invalid-class",  # type: ignore[arg-type]
                origin="synthetic-public",
                access_mode="bundled",
                trust_status="exploratory",
            )

    def test_reserved_origin_synthetic_internal_raises_error(self) -> None:
        """Given synthetic-internal origin, when created, then raises EvidenceAssetError.

        Story 21.1 / AC14: Reserved values raise error in current phase.
        """
        with pytest.raises(
            EvidenceAssetError,
            match="origin.*synthetic-internal.*reserved for future phases",
        ):
            DataAssetDescriptor(
                asset_id="test",
                name="Test",
                description="Test",
                data_class="structural",
                origin="synthetic-internal",  # type: ignore[arg-type]
                access_mode="bundled",
                trust_status="exploratory",
            )

    def test_reserved_origin_restricted_raises_error(self) -> None:
        """Given restricted origin, when created, then raises EvidenceAssetError.

        Story 21.1 / AC14: Reserved values raise error in current phase.
        """
        with pytest.raises(
            EvidenceAssetError,
            match="origin.*restricted.*reserved for future phases",
        ):
            DataAssetDescriptor(
                asset_id="test",
                name="Test",
                description="Test",
                data_class="structural",
                origin="restricted",  # type: ignore[arg-type]
                access_mode="deferred-user-connector",  # type: ignore[arg-type]
                trust_status="exploratory",
            )

    def test_reserved_access_mode_deferred_user_connector_raises_error(self) -> None:
        """Given deferred-user-connector access_mode, when created, then raises EvidenceAssetError.

        Story 21.1 / AC14: Reserved values raise error in current phase.
        """
        with pytest.raises(
            EvidenceAssetError,
            match="access_mode.*deferred-user-connector.*reserved for future phases",
        ):
            DataAssetDescriptor(
                asset_id="test",
                name="Test",
                description="Test",
                data_class="structural",
                origin="open-official",
                access_mode="deferred-user-connector",  # type: ignore[arg-type]
                trust_status="exploratory",
            )

    def test_unsupported_combination_open_official_production_safe_bundled_allowed(self) -> None:
        """Given open-official/bundled/production-safe, when created, then succeeds.

        Story 21.1 / AC14: Current-phase supported combinations table.
        """
        descriptor = DataAssetDescriptor(
            asset_id="test",
            name="Test",
            description="Test",
            data_class="structural",
            origin="open-official",
            access_mode="bundled",
            trust_status="production-safe",
        )
        assert descriptor.origin == "open-official"
        assert descriptor.trust_status == "production-safe"

    def test_unsupported_combination_synthetic_public_production_safe_raises_error(self) -> None:
        """Given synthetic-public/production-safe, when created, then raises EvidenceAssetError.

        Story 21.1 / AC14: synthetic-public cannot be production-safe in current phase.
        """
        with pytest.raises(EvidenceAssetError, match="is not a supported combination"):
            DataAssetDescriptor(
                asset_id="test",
                name="Test",
                description="Test",
                data_class="structural",
                origin="synthetic-public",
                access_mode="bundled",
                trust_status="production-safe",  # not allowed for synthetic-public
            )


class TestDataAssetDescriptorJsonRoundTrip:
    """Tests for JSON serialization and deserialization.

    Story 21.1 / AC7: to_json() and from_json() with full validation.
    """

    def test_to_json_minimal_descriptor(self) -> None:
        """Given minimal descriptor, when to_json(), then includes only non-default fields."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test Asset",
            description="Test description",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        json_dict = descriptor.to_json()
        assert json_dict == {
            "asset_id": "test-asset",
            "name": "Test Asset",
            "description": "Test description",
            "data_class": "structural",
            "origin": "synthetic-public",
            "access_mode": "bundled",
            "trust_status": "exploratory",
        }
        # Optional fields with defaults are NOT included
        assert "source_url" not in json_dict
        assert "license" not in json_dict
        assert "version" not in json_dict
        assert "geographic_coverage" not in json_dict
        assert "years" not in json_dict
        assert "intended_use" not in json_dict
        assert "redistribution_allowed" not in json_dict

    def test_to_json_full_descriptor(self) -> None:
        """Given full descriptor, when to_json(), then includes all non-empty fields."""
        descriptor = DataAssetDescriptor(
            asset_id="reformlab-fr-synthetic-2024",
            name="French Synthetic Population 2024",
            description="100k synthetic households for France",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
            source_url="https://example.com/data",
            license="CC-BY-4.0",
            version="2024",
            geographic_coverage=("FR",),
            years=(2024,),
            intended_use="Demo",
            redistribution_allowed=True,
            redistribution_notes="Notes",
            update_cadence="annual",
            quality_notes="Quality notes",
            references=("https://example.com/doc1", "https://example.com/doc2"),
        )
        json_dict = descriptor.to_json()
        assert json_dict["asset_id"] == "reformlab-fr-synthetic-2024"
        assert json_dict["source_url"] == "https://example.com/data"
        assert json_dict["license"] == "CC-BY-4.0"
        assert json_dict["version"] == "2024"
        assert json_dict["geographic_coverage"] == ["FR"]
        assert json_dict["years"] == [2024]
        assert json_dict["intended_use"] == "Demo"
        assert json_dict["redistribution_allowed"] is True
        assert json_dict["redistribution_notes"] == "Notes"
        assert json_dict["update_cadence"] == "annual"
        assert json_dict["quality_notes"] == "Quality notes"
        assert json_dict["references"] == ["https://example.com/doc1", "https://example.com/doc2"]

    def test_from_json_minimal_valid(self) -> None:
        """Given minimal valid JSON, when from_json(), then creates descriptor."""
        json_dict = {
            "asset_id": "test-asset",
            "name": "Test Asset",
            "description": "Test description",
            "data_class": "structural",
            "origin": "synthetic-public",
            "access_mode": "bundled",
            "trust_status": "exploratory",
        }
        descriptor = DataAssetDescriptor.from_json(json_dict)
        assert descriptor.asset_id == "test-asset"
        assert descriptor.name == "Test Asset"
        assert descriptor.description == "Test description"
        assert descriptor.data_class == "structural"
        assert descriptor.origin == "synthetic-public"
        assert descriptor.access_mode == "bundled"
        assert descriptor.trust_status == "exploratory"

    def test_from_json_full_valid(self) -> None:
        """Given full valid JSON, when from_json(), then creates descriptor with all fields."""
        json_dict = {
            "asset_id": "test-asset",
            "name": "Test Asset",
            "description": "Test description",
            "data_class": "exogenous",
            "origin": "open-official",
            "access_mode": "fetched",
            "trust_status": "production-safe",
            "source_url": "https://example.com",
            "license": "MIT",
            "version": "1.0",
            "geographic_coverage": ["FR", "DE"],
            "years": [2020, 2021, 2022],
            "intended_use": "Testing",
            "redistribution_allowed": True,
            "redistribution_notes": "Free to share",
            "update_cadence": "quarterly",
            "quality_notes": "High quality",
            "references": ["https://example.com/doc"],
        }
        descriptor = DataAssetDescriptor.from_json(json_dict)
        assert descriptor.asset_id == "test-asset"
        assert descriptor.geographic_coverage == ("FR", "DE")
        assert descriptor.years == (2020, 2021, 2022)
        assert descriptor.redistribution_allowed is True

    def test_from_json_missing_required_field_raises_error(self) -> None:
        """Given JSON missing required field, when from_json(), then raises EvidenceAssetError."""
        json_dict = {
            "asset_id": "test-asset",
            "name": "Test Asset",
            "description": "Test description",
            "data_class": "structural",
            "origin": "synthetic-public",
            # Missing access_mode and trust_status
        }
        with pytest.raises(EvidenceAssetError, match="missing required fields"):
            DataAssetDescriptor.from_json(json_dict)

    def test_from_json_invalid_literal_value_raises_error(self) -> None:
        """Given JSON with invalid literal value, when from_json(), then raises EvidenceAssetError."""
        json_dict = {
            "asset_id": "test-asset",
            "name": "Test Asset",
            "description": "Test description",
            "data_class": "structural",
            "origin": "invalid-origin",  # Invalid literal
            "access_mode": "bundled",
            "trust_status": "exploratory",
        }
        with pytest.raises(EvidenceAssetError, match="origin.*is not a valid DataAssetOrigin"):
            DataAssetDescriptor.from_json(json_dict)

    def test_from_json_invalid_field_type_raises_error(self) -> None:
        """Given JSON with invalid field type, when from_json(), then raises EvidenceAssetError."""
        json_dict = {
            "asset_id": "test-asset",
            "name": "Test Asset",
            "description": "Test description",
            "data_class": "structural",
            "origin": "synthetic-public",
            "access_mode": "bundled",
            "trust_status": "exploratory",
            "years": "not-a-list",  # Invalid type
        }
        with pytest.raises(EvidenceAssetError, match="years.*has invalid type"):
            DataAssetDescriptor.from_json(json_dict)

    def test_from_json_invalid_years_type_raises_error(self) -> None:
        """Given JSON with non-integer years, when from_json(), then raises EvidenceAssetError."""
        json_dict = {
            "asset_id": "test-asset",
            "name": "Test Asset",
            "description": "Test description",
            "data_class": "structural",
            "origin": "synthetic-public",
            "access_mode": "bundled",
            "trust_status": "exploratory",
            "years": [2020, "not-a-number", 2022],  # Mixed types with non-numeric string
        }
        with pytest.raises(EvidenceAssetError, match="years.*non-integer"):
            DataAssetDescriptor.from_json(json_dict)

    def test_from_json_unsupported_combination_raises_error(self) -> None:
        """Given JSON with unsupported combination, when from_json(), then raises EvidenceAssetError."""
        json_dict = {
            "asset_id": "test-asset",
            "name": "Test Asset",
            "description": "Test description",
            "data_class": "structural",
            "origin": "synthetic-public",
            "access_mode": "bundled",
            "trust_status": "production-safe",  # Not allowed for synthetic-public
        }
        with pytest.raises(EvidenceAssetError, match="is not a supported combination"):
            DataAssetDescriptor.from_json(json_dict)

    def test_json_round_trip_preserves_equality(self) -> None:
        """Given a descriptor, when round-tripped through JSON, then preserves equality."""
        original = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test Asset",
            description="Test description",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            source_url="https://example.com",
            license="MIT",
            version="1.0",
            geographic_coverage=("FR",),
            years=(2020, 2021),
            intended_use="Testing",
            redistribution_allowed=True,
        )
        json_dict = original.to_json()
        restored = DataAssetDescriptor.from_json(json_dict)
        assert restored == original


class TestDataAssetDescriptorFrozen:
    """Tests for frozen dataclass immutability.

    Story 21.1 / AC1: Frozen dataclass prevents mutation.
    """

    def test_frozen_cannot_modify_required_field(self) -> None:
        """Given a descriptor, when modifying required field, then raises AttributeError."""
        descriptor = DataAssetDescriptor(
            asset_id="test",
            name="Test",
            description="Test",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        with pytest.raises(AttributeError):
            descriptor.asset_id = "modified"  # type: ignore[misc]

    def test_frozen_cannot_modify_optional_field(self) -> None:
        """Given a descriptor, when modifying optional field, then raises AttributeError."""
        descriptor = DataAssetDescriptor(
            asset_id="test",
            name="Test",
            description="Test",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
            license="MIT",
        )
        with pytest.raises(AttributeError):
            descriptor.license = "Apache-2.0"  # type: ignore[misc]

    def test_frozen_tuple_fields_are_immutable(self) -> None:
        """Given a descriptor, when modifying tuple field, then tuple is immutable."""
        descriptor = DataAssetDescriptor(
            asset_id="test",
            name="Test",
            description="Test",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
            years=(2020, 2021),
        )
        assert descriptor.years == (2020, 2021)
        # Tuple itself is immutable
        with pytest.raises(AttributeError):
            descriptor.years = (2022,)  # type: ignore[misc]


# ============================================================================
# Fixtures for valid descriptors
# ============================================================================


@pytest.fixture
def exploratory_synthetic_descriptor() -> DataAssetDescriptor:
    """Valid exploratory synthetic-public bundled descriptor.

    Story 21.1 / AC1: Example fixture for testing.
    """
    return DataAssetDescriptor(
        asset_id="reformlab-fr-synthetic-2024",
        name="French Synthetic Population 2024",
        description="100k synthetic households for France",
        data_class="structural",
        origin="synthetic-public",
        access_mode="bundled",
        trust_status="exploratory",
        license="CC-BY-4.0",
        version="2024",
        years=(2024,),
        redistribution_allowed=True,
    )


@pytest.fixture
def production_safe_open_official_descriptor() -> DataAssetDescriptor:
    """Valid production-safe open-official fetched descriptor.

    Story 21.1 / AC1: Example fixture for testing.
    """
    return DataAssetDescriptor(
        asset_id="insee-fideli-2021",
        name="Fidéli (Données de cadrage)",
        description="French demographic data sources",
        data_class="structural",
        origin="open-official",
        access_mode="fetched",
        trust_status="production-safe",
        source_url="https://www.insee.fr/fr/statistiques/fichier/4807439",
        license="Open License",
        version="2021",
        years=(2021,),
        redistribution_allowed=True,
    )


@pytest.fixture
def demo_only_descriptor() -> DataAssetDescriptor:
    """Valid demo-only descriptor.

    Story 21.1 / AC1: Example fixture for testing.
    """
    return DataAssetDescriptor(
        asset_id="demo-population",
        name="Demo Population",
        description="Example data for demonstrations",
        data_class="structural",
        origin="synthetic-public",
        access_mode="bundled",
        trust_status="demo-only",
        quality_notes="Not for analysis",
    )
