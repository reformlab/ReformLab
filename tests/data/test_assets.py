# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for typed asset dataclasses for each evidence taxonomy data class.

Story 21.3 - implement-typed-structural-exogenous-calibration-and-validation-asset-schemas.
AC1-AC4, AC6, AC9-AC10: Asset type construction, JSON round-trip, validation.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.data.assets import (
    CalibrationAsset,
    ExogenousAsset,
    StructuralAsset,
    ValidationAsset,
    create_calibration_asset,
    create_exogenous_asset,
    create_structural_asset,
    create_validation_asset,
)
from reformlab.data.descriptor import DataAssetDescriptor
from reformlab.data.errors import EvidenceAssetError


class TestStructuralAsset:
    """Tests for StructuralAsset typed contract.

    Story 21.3 / AC1.
    """

    def test_create_with_all_fields(self) -> None:
        """Given all fields, when created, then all fields are accessible."""
        descriptor = DataAssetDescriptor(
            asset_id="test-population",
            name="Test Population",
            description="Test structural asset",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        table = pa.Table.from_pydict({"household_id": [1, 2, 3], "income": [1000, 2000, 3000]})
        asset = StructuralAsset(
            descriptor=descriptor,
            table=table,
            entity_type="household",
            record_count=3,
            primary_key="household_id",
        )
        assert asset.descriptor.data_class == "structural"
        assert asset.record_count == 3
        assert asset.entity_type == "household"
        assert asset.primary_key == "household_id"
        assert asset.table.num_rows == 3

    def test_create_with_relationships(self) -> None:
        """Given relationships tuple, when created, then relationships are accessible."""
        descriptor = DataAssetDescriptor(
            asset_id="test-population",
            name="Test",
            description="Test",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        table = pa.Table.from_pydict({"person_id": [1, 2]})
        asset = StructuralAsset(
            descriptor=descriptor,
            table=table,
            entity_type="person",
            record_count=2,
            relationships=("household",),
        )
        assert asset.relationships == ("household",)

    def test_data_class_mismatch_raises_error(self) -> None:
        """Given descriptor with wrong data_class, when created, then raises."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",  # Wrong!
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        table = pa.Table.from_pydict({"col": [1]})
        with pytest.raises(EvidenceAssetError, match="data_class.*structural"):
            StructuralAsset(
                descriptor=descriptor,
                table=table,
                entity_type="household",
                record_count=1,
            )

    def test_record_count_mismatch_raises_error(self) -> None:
        """Given record_count not matching table, when created, then raises."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        table = pa.Table.from_pydict({"col": [1, 2, 3]})
        with pytest.raises(EvidenceAssetError, match="record_count mismatch"):
            StructuralAsset(
                descriptor=descriptor,
                table=table,
                entity_type="household",
                record_count=5,  # Wrong!
            )

    def test_to_json_serializes_descriptor_and_metadata(self) -> None:
        """Given structural asset, when to_json(), then serializes descriptor and metadata."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test Asset",
            description="Test description",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        table = pa.Table.from_pydict({"id": [1]})
        asset = StructuralAsset(
            descriptor=descriptor,
            table=table,
            entity_type="household",
            record_count=1,
        )
        json_dict = asset.to_json()
        assert json_dict["descriptor"]["asset_id"] == "test-asset"
        assert json_dict["entity_type"] == "household"
        assert json_dict["record_count"] == 1
        # table is NOT serialized
        assert "table" not in json_dict

    def test_from_json_validates_data_class(self) -> None:
        """Given valid JSON, when from_json(), then returns asset with descriptor."""
        json_dict = {
            "descriptor": {
                "asset_id": "test-asset",
                "name": "Test",
                "description": "Test",
                "data_class": "structural",
                "origin": "synthetic-public",
                "access_mode": "bundled",
                "trust_status": "exploratory",
            },
            "entity_type": "household",
            "record_count": 100,
            "relationships": ["person"],
            "primary_key": "household_id",
        }
        asset = StructuralAsset.from_json(json_dict)
        assert asset.descriptor.data_class == "structural"
        assert asset.entity_type == "household"
        assert asset.record_count == 100
        assert asset.relationships == ("person",)
        assert asset.primary_key == "household_id"

    def test_from_json_invalid_data_class_raises_error(self) -> None:
        """Given JSON with wrong data_class, when from_json(), then raises."""
        json_dict = {
            "descriptor": {
                "asset_id": "test-asset",
                "name": "Test",
                "description": "Test",
                "data_class": "exogenous",  # Wrong!
                "origin": "synthetic-public",
                "access_mode": "bundled",
                "trust_status": "exploratory",
            },
            "entity_type": "household",
            "record_count": 100,
        }
        with pytest.raises(EvidenceAssetError, match="data_class.*structural"):
            StructuralAsset.from_json(json_dict)

    def test_json_round_trip_preserves_equality(self) -> None:
        """Given a structural asset, when round-tripped through JSON, then preserves equality."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        table = pa.Table.from_pydict({"household_id": [1, 2]})
        original = StructuralAsset(
            descriptor=descriptor,
            table=table,
            entity_type="household",
            record_count=2,
            relationships=("person",),
            primary_key="household_id",
        )
        json_dict = original.to_json()
        # Note: table is not serialized, so we can't round-trip fully
        # We only test that JSON structure is valid for from_json
        restored = StructuralAsset.from_json(json_dict)
        assert restored.descriptor == original.descriptor
        assert restored.entity_type == original.entity_type
        assert restored.record_count == original.record_count


class TestStructuralAssetFrozen:
    """Tests for StructuralAsset frozen immutability.

    Story 21.3 / AC10.
    """

    def test_frozen_cannot_modify_field(self) -> None:
        """Given a structural asset, when modifying field, then raises AttributeError."""
        descriptor = DataAssetDescriptor(
            asset_id="test",
            name="Test",
            description="Test",
            data_class="structural",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        table = pa.Table.from_pydict({"col": [1]})
        asset = StructuralAsset(
            descriptor=descriptor,
            table=table,
            entity_type="household",
            record_count=1,
        )
        with pytest.raises(AttributeError):
            asset.entity_type = "person"  # type: ignore[misc]


class TestExogenousAsset:
    """Tests for ExogenousAsset typed contract.

    Story 21.3 / AC2.
    """

    def test_create_with_all_fields(self) -> None:
        """Given all fields, when created, then all fields are accessible."""
        descriptor = DataAssetDescriptor(
            asset_id="carbon-tax-rate",
            name="Carbon Tax Rate",
            description="French carbon tax rate over time",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="carbon_tax_eur_per_ton",
            values={2020: 44.6, 2021: 44.6, 2022: 44.6, 2023: 48.5, 2024: 48.5},
            unit="EUR/ton",
            frequency="annual",
            source="French Ministry of Ecology",
            vintage="2024",
            interpolation_method="linear",
            aggregation_method="mean",
        )
        assert asset.descriptor.data_class == "exogenous"
        assert asset.name == "carbon_tax_eur_per_ton"
        assert asset.values[2024] == 48.5
        assert asset.unit == "EUR/ton"
        assert asset.interpolation_method == "linear"

    def test_data_class_mismatch_raises_error(self) -> None:
        """Given descriptor with wrong data_class, when created, then raises."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="structural",  # Wrong!
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        with pytest.raises(EvidenceAssetError, match="data_class.*exogenous"):
            ExogenousAsset(
                descriptor=descriptor,
                name="test",
                values={2020: 100.0},
                unit="%",
            )

    def test_empty_values_raises_error(self) -> None:
        """Given empty values dict, when created, then raises EvidenceAssetError."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        with pytest.raises(EvidenceAssetError, match="values.*non-empty"):
            ExogenousAsset(
                descriptor=descriptor,
                name="test",
                values={},  # Empty!
                unit="%",
            )

    def test_non_integer_year_keys_raises_error(self) -> None:
        """Given non-integer year keys, when created, then raises EvidenceAssetError."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        with pytest.raises(EvidenceAssetError, match="years must be integers"):
            ExogenousAsset(
                descriptor=descriptor,
                name="test",
                values={"2020": 100.0},  # type: ignore[arg-type]
                unit="%",
            )

    def test_nan_values_raises_error(self) -> None:
        """Given NaN value, when created, then raises EvidenceAssetError."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        with pytest.raises(EvidenceAssetError, match="values must be finite"):
            ExogenousAsset(
                descriptor=descriptor,
                name="test",
                values={2020: float("nan")},
                unit="%",
            )

    def test_infinite_values_raises_error(self) -> None:
        """Given infinite value, when created, then raises EvidenceAssetError."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        with pytest.raises(EvidenceAssetError, match="values must be finite"):
            ExogenousAsset(
                descriptor=descriptor,
                name="test",
                values={2020: float("inf")},
                unit="%",
            )

    def test_get_value_exact_year(self) -> None:
        """Given exact year in values, when get_value(), then returns exact value."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test",
            values={2020: 100.0, 2021: 110.0, 2022: 120.0},
            unit="%",
            interpolation_method="linear",
        )
        assert asset.get_value(2020) == 100.0
        assert asset.get_value(2021) == 110.0
        assert asset.get_value(2022) == 120.0

    def test_get_value_interpolates_linear(self) -> None:
        """Given year between values, when get_value() with linear, then interpolates."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test",
            values={2020: 100.0, 2022: 120.0},
            unit="%",
            interpolation_method="linear",
        )
        # Linear interpolation: 100 + (2021-2020)/(2022-2020) * (120-100) = 110
        result = asset.get_value(2021)
        assert result == pytest.approx(110.0)

    def test_get_value_extrapolates_raises_error(self) -> None:
        """Given year outside range, when get_value(), then raises EvidenceAssetError."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test",
            values={2021: 100.0, 2022: 110.0},
            unit="%",
        )
        with pytest.raises(EvidenceAssetError, match=r"year \d+ is out of range"):
            asset.get_value(2020)  # Before min year
        with pytest.raises(EvidenceAssetError, match=r"year \d+ is out of range"):
            asset.get_value(2023)  # After max year

    def test_get_value_step_interpolation(self) -> None:
        """Given step interpolation, when get_value() between years, then returns previous value."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test",
            values={2020: 100.0, 2022: 200.0},
            unit="%",
            interpolation_method="step",
        )
        # Step interpolation: use nearest previous year's value
        assert asset.get_value(2021) == 100.0

    def test_get_value_no_interpolation(self) -> None:
        """Given no interpolation method, when get_value() between years, then raises error."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test",
            values={2020: 100.0, 2022: 200.0},
            unit="%",
            interpolation_method="none",
        )
        with pytest.raises(EvidenceAssetError, match="no data for year"):
            asset.get_value(2021)

    def test_validate_coverage_complete(self) -> None:
        """Given complete coverage, when validate_coverage(), then does not raise."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test",
            values={2020: 100.0, 2021: 110.0, 2022: 120.0},
            unit="%",
        )
        # Should not raise
        asset.validate_coverage(2020, 2022)

    def test_validate_coverage_missing_years_raises_error(self) -> None:
        """Given missing years, when validate_coverage(), then raises EvidenceAssetError."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test",
            values={2020: 100.0, 2022: 120.0},  # Missing 2021
            unit="%",
        )
        with pytest.raises(EvidenceAssetError, match="coverage incomplete.*missing years"):
            asset.validate_coverage(2020, 2022)

    def test_to_json_and_from_json(self) -> None:
        """Given exogenous asset, when round-tripped through JSON, then preserves data."""
        descriptor = DataAssetDescriptor(
            asset_id="carbon-tax",
            name="Carbon Tax",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        original = ExogenousAsset(
            descriptor=descriptor,
            name="carbon_tax_eur_per_ton",
            values={2020: 44.6, 2024: 48.5},
            unit="EUR/ton",
            frequency="annual",
            source="Ministry",
            interpolation_method="step",  # Non-default value to test serialization
        )
        json_dict = original.to_json()
        assert json_dict["values"] == {"2020": 44.6, "2024": 48.5}
        assert json_dict["interpolation_method"] == "step"

        restored = ExogenousAsset.from_json(json_dict)
        assert restored.descriptor == original.descriptor
        assert restored.name == original.name
        assert restored.values == original.values
        assert restored.unit == original.unit
        assert restored.interpolation_method == "step"


class TestExogenousAssetFrozen:
    """Tests for ExogenousAsset frozen immutability.

    Story 21.3 / AC10.
    """

    def test_frozen_cannot_reassign_field(self) -> None:
        """Given an exogenous asset, when reassigning values field, then raises AttributeError."""
        descriptor = DataAssetDescriptor(
            asset_id="test",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test",
            values={2020: 100.0},
            unit="%",
        )
        with pytest.raises(AttributeError):
            asset.values = {2021: 110.0}  # type: ignore[misc]


class TestExogenousAssetValidation:
    """Tests for ExogenousAsset validation edge cases.

    Story 21.3 / AC10.
    """

    def test_validate_coverage_inverted_range_raises_error(self) -> None:
        """Given start_year > end_year, when validate_coverage(), then raises."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ExogenousAsset(
            descriptor=descriptor,
            name="test",
            values={2020: 100.0, 2022: 120.0},
            unit="%",
        )
        with pytest.raises(EvidenceAssetError, match="start_year.*must be <= end_year"):
            asset.validate_coverage(2030, 2020)

    def test_invalid_interpolation_method_raises_error_at_construction(self) -> None:
        """Given invalid interpolation_method, when created, then raises EvidenceAssetError."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="exogenous",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        with pytest.raises(EvidenceAssetError, match="interpolation_method.*invalid"):
            ExogenousAsset(
                descriptor=descriptor,
                name="test",
                values={2020: 100.0},
                unit="%",
                interpolation_method="invalid_method",
            )


class TestFromJsonStrictTypeValidation:
    """Tests for from_json() strict type validation (no coercion).

    Story 21.3 / AC6, AC10.
    """

    def test_exogenous_from_json_rejects_non_string_name(self) -> None:
        """Given non-string name in JSON, when from_json(), then raises EvidenceAssetError."""
        json_dict = {
            "descriptor": {
                "asset_id": "test",
                "name": "Test",
                "description": "Test",
                "data_class": "exogenous",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            },
            "name": 123,  # Not a string!
            "values": {"2020": 100.0},
            "unit": "%",
        }
        with pytest.raises(EvidenceAssetError, match="'name'.*invalid type"):
            ExogenousAsset.from_json(json_dict)

    def test_exogenous_from_json_rejects_non_string_unit(self) -> None:
        """Given non-string unit in JSON, when from_json(), then raises EvidenceAssetError."""
        json_dict = {
            "descriptor": {
                "asset_id": "test",
                "name": "Test",
                "description": "Test",
                "data_class": "exogenous",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            },
            "name": "test",
            "values": {"2020": 100.0},
            "unit": 456,  # Not a string!
        }
        with pytest.raises(EvidenceAssetError, match="'unit'.*invalid type"):
            ExogenousAsset.from_json(json_dict)

    def test_structural_from_json_rejects_non_string_entity_type(self) -> None:
        """Given non-string entity_type in JSON, when from_json(), then raises EvidenceAssetError."""
        json_dict = {
            "descriptor": {
                "asset_id": "test",
                "name": "Test",
                "description": "Test",
                "data_class": "structural",
                "origin": "synthetic-public",
                "access_mode": "bundled",
                "trust_status": "exploratory",
            },
            "entity_type": 123,  # Not a string!
            "record_count": 100,
        }
        with pytest.raises(EvidenceAssetError, match="'entity_type'.*invalid type"):
            StructuralAsset.from_json(json_dict)

    def test_structural_from_json_rejects_non_integer_record_count(self) -> None:
        """Given non-integer record_count in JSON, when from_json(), then raises EvidenceAssetError."""
        json_dict = {
            "descriptor": {
                "asset_id": "test",
                "name": "Test",
                "description": "Test",
                "data_class": "structural",
                "origin": "synthetic-public",
                "access_mode": "bundled",
                "trust_status": "exploratory",
            },
            "entity_type": "household",
            "record_count": "100",  # String, not int!
        }
        with pytest.raises(EvidenceAssetError, match="'record_count'.*invalid type"):
            StructuralAsset.from_json(json_dict)

    def test_calibration_from_json_rejects_non_string_coverage(self) -> None:
        """Given non-string coverage in JSON, when from_json(), then raises EvidenceAssetError."""
        json_dict = {
            "descriptor": {
                "asset_id": "test",
                "name": "Test",
                "description": "Test",
                "data_class": "calibration",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            },
            "target_type": "marginal",
            "coverage": 123,  # Not a string!
        }
        with pytest.raises(EvidenceAssetError, match="'coverage'.*invalid type"):
            CalibrationAsset.from_json(json_dict)

    def test_validation_from_json_rejects_non_boolean_trust_status_upgradable(self) -> None:
        """Given non-boolean trust_status_upgradable, when from_json(), then raises."""
        json_dict = {
            "descriptor": {
                "asset_id": "test",
                "name": "Test",
                "description": "Test",
                "data_class": "validation",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            },
            "validation_type": "marginal_check",
            "benchmark_status": "pending",
            "criteria": {},
            "trust_status_upgradable": "true",  # String, not bool!
        }
        with pytest.raises(EvidenceAssetError, match="'trust_status_upgradable'.*invalid type"):
            ValidationAsset.from_json(json_dict)


class TestCalibrationAsset:
    """Tests for CalibrationAsset typed contract.

    Story 21.3 / AC3.
    """

    def test_create_with_all_fields(self) -> None:
        """Given all fields, when created, then all fields are accessible."""
        descriptor = DataAssetDescriptor(
            asset_id="calibration-income",
            name="Income Distribution Calibration",
            description="French income distribution calibration targets",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = CalibrationAsset(
            descriptor=descriptor,
            target_type="marginal",
            coverage="national",
            source_material=("INSEE Dossier 2024", "Eurostat EU-SILC 2022"),
            margin_of_error=0.05,
            confidence_level=0.95,
            methodology_notes="Calibrated to INSEE decile margins",
        )
        assert asset.descriptor.data_class == "calibration"
        assert asset.target_type == "marginal"
        assert asset.coverage == "national"
        assert asset.source_material == ("INSEE Dossier 2024", "Eurostat EU-SILC 2022")
        assert asset.margin_of_error == 0.05
        assert asset.confidence_level == 0.95

    def test_data_class_mismatch_raises_error(self) -> None:
        """Given descriptor with wrong data_class, when created, then raises."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="structural",  # Wrong!
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        with pytest.raises(EvidenceAssetError, match="data_class.*calibration"):
            CalibrationAsset(
                descriptor=descriptor,
                target_type="marginal",
                coverage="national",
            )

    def test_invalid_target_type_raises_error(self) -> None:
        """Given invalid target_type, when created, then raises EvidenceAssetError."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        with pytest.raises(EvidenceAssetError, match="target_type.*valid CalibrationTargetType"):
            CalibrationAsset(
                descriptor=descriptor,
                target_type="invalid_type",  # type: ignore[arg-type]
                coverage="national",
            )

    def test_all_valid_target_types(self) -> None:
        """Given each valid target_type, when created, then succeeds."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        for target_type in ["marginal", "aggregate_total", "adoption_rate", "transition_rate"]:
            asset = CalibrationAsset(
                descriptor=descriptor,
                target_type=target_type,  # type: ignore[arg-type]
                coverage="national",
            )
            assert asset.target_type == target_type

    def test_to_json_and_from_json(self) -> None:
        """Given calibration asset, when round-tripped through JSON, then preserves data."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        original = CalibrationAsset(
            descriptor=descriptor,
            target_type="aggregate_total",
            coverage="national",
            source_material=("Source A", "Source B"),
            margin_of_error=0.02,
        )
        json_dict = original.to_json()
        assert json_dict["target_type"] == "aggregate_total"
        assert json_dict["source_material"] == ["Source A", "Source B"]

        restored = CalibrationAsset.from_json(json_dict)
        assert restored.descriptor == original.descriptor
        assert restored.target_type == original.target_type
        assert restored.source_material == original.source_material


class TestCalibrationAssetFrozen:
    """Tests for CalibrationAsset frozen immutability.

    Story 21.3 / AC10.
    """

    def test_frozen_cannot_modify_field(self) -> None:
        """Given a calibration asset, when modifying field, then raises AttributeError."""
        descriptor = DataAssetDescriptor(
            asset_id="test",
            name="Test",
            description="Test",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = CalibrationAsset(
            descriptor=descriptor,
            target_type="marginal",
            coverage="national",
        )
        with pytest.raises(AttributeError):
            asset.target_type = "aggregate_total"  # type: ignore[misc]


class TestValidationAsset:
    """Tests for ValidationAsset typed contract.

    Story 21.3 / AC4.
    """

    def test_create_with_all_fields(self) -> None:
        """Given all fields, when created, then all fields are accessible."""
        descriptor = DataAssetDescriptor(
            asset_id="validation-income",
            name="Income Distribution Validation",
            description="French income distribution validation benchmark",
            data_class="validation",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ValidationAsset(
            descriptor=descriptor,
            validation_type="marginal_check",
            benchmark_status="passed",
            criteria={
                "max_relative_error": 0.05,
                "min_deciles": 10,
                "statistical_test": "ks_test",
            },
            last_validated="2024-03-15T10:30:00Z",
            validation_dossier="https://example.com/dossier",
            trust_status_upgradable=True,
        )
        assert asset.descriptor.data_class == "validation"
        assert asset.validation_type == "marginal_check"
        assert asset.benchmark_status == "passed"
        assert asset.criteria["max_relative_error"] == 0.05
        assert asset.last_validated == "2024-03-15T10:30:00Z"

    def test_data_class_mismatch_raises_error(self) -> None:
        """Given descriptor with wrong data_class, when created, then raises."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="structural",  # Wrong!
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
        )
        with pytest.raises(EvidenceAssetError, match="data_class.*validation"):
            ValidationAsset(
                descriptor=descriptor,
                validation_type="marginal_check",
                benchmark_status="pending",
                criteria={},
            )

    def test_invalid_validation_type_raises_error(self) -> None:
        """Given invalid validation_type, when created, then raises EvidenceAssetError."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="validation",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        with pytest.raises(EvidenceAssetError, match="validation_type.*valid ValidationType"):
            ValidationAsset(
                descriptor=descriptor,
                validation_type="invalid_type",  # type: ignore[arg-type]
                benchmark_status="pending",
                criteria={},
            )

    def test_invalid_benchmark_status_raises_error(self) -> None:
        """Given invalid benchmark_status, when created, then raises EvidenceAssetError."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="validation",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        with pytest.raises(EvidenceAssetError, match="benchmark_status.*valid ValidationBenchmarkStatus"):
            ValidationAsset(
                descriptor=descriptor,
                validation_type="marginal_check",
                benchmark_status="invalid_status",  # type: ignore[arg-type]
                criteria={},
            )

    def test_all_valid_validation_types(self) -> None:
        """Given each valid validation_type, when created, then succeeds."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="validation",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        valid_types = [
            "marginal_check",
            "joint_distribution",
            "subgroup_stability",
            "downstream_performance",
        ]
        for validation_type in valid_types:
            asset = ValidationAsset(
                descriptor=descriptor,
                validation_type=validation_type,  # type: ignore[arg-type]
                benchmark_status="pending",
                criteria={},
            )
            assert asset.validation_type == validation_type

    def test_all_valid_benchmark_statuses(self) -> None:
        """Given each valid benchmark_status, when created, then succeeds."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="validation",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        for status in ["passed", "failed", "pending", "not_applicable"]:
            asset = ValidationAsset(
                descriptor=descriptor,
                validation_type="marginal_check",
                benchmark_status=status,  # type: ignore[arg-type]
                criteria={},
            )
            assert asset.benchmark_status == status

    def test_to_json_and_from_json(self) -> None:
        """Given validation asset, when round-tripped through JSON, then preserves data."""
        descriptor = DataAssetDescriptor(
            asset_id="test-asset",
            name="Test",
            description="Test",
            data_class="validation",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        original = ValidationAsset(
            descriptor=descriptor,
            validation_type="joint_distribution",
            benchmark_status="passed",
            criteria={"max_chi_squared": 10.0, "min_p_value": 0.05},
            last_validated="2024-03-15T10:30:00Z",
        )
        json_dict = original.to_json()
        assert json_dict["validation_type"] == "joint_distribution"
        assert json_dict["criteria"]["max_chi_squared"] == 10.0

        restored = ValidationAsset.from_json(json_dict)
        assert restored.descriptor == original.descriptor
        assert restored.validation_type == original.validation_type
        assert restored.criteria == original.criteria


class TestFactoryFunctions:
    """Tests for factory functions.

    Story 21.3 / AC8.
    """

    def test_create_structural_asset(self) -> None:
        """Given descriptor_kwargs and payload, when factory called, then returns StructuralAsset."""
        asset = create_structural_asset(
            # Descriptor fields
            asset_id="test-population",
            name="Test Population",
            description="Test structural asset",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
            # Structural-specific fields
            table=pa.Table.from_pydict({"household_id": [1, 2]}),
            entity_type="household",
            record_count=2,
        )
        assert isinstance(asset, StructuralAsset)
        assert asset.descriptor.asset_id == "test-population"
        assert asset.descriptor.data_class == "structural"
        assert asset.entity_type == "household"

    def test_create_exogenous_asset(self) -> None:
        """Given descriptor_kwargs and payload, when factory called, then returns ExogenousAsset."""
        asset = create_exogenous_asset(
            # Descriptor fields
            asset_id="carbon-tax",
            display_name="Carbon Tax",
            description="Test",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            # Exogenous-specific fields
            series_name="carbon_tax_eur_per_ton",
            values={2020: 44.6, 2024: 48.5},
            unit="EUR/ton",
        )
        assert isinstance(asset, ExogenousAsset)
        assert asset.descriptor.asset_id == "carbon-tax"
        assert asset.descriptor.data_class == "exogenous"
        assert asset.name == "carbon_tax_eur_per_ton"
        assert asset.descriptor.name == "Carbon Tax"

    def test_create_calibration_asset(self) -> None:
        """Given descriptor_kwargs and payload, when factory called, then returns CalibrationAsset."""
        asset = create_calibration_asset(
            # Descriptor fields
            asset_id="calibration-test",
            name="Test Calibration",
            description="Test",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            # Calibration-specific fields
            target_type="marginal",
            coverage="national",
        )
        assert isinstance(asset, CalibrationAsset)
        assert asset.descriptor.asset_id == "calibration-test"
        assert asset.descriptor.data_class == "calibration"
        assert asset.target_type == "marginal"

    def test_create_validation_asset(self) -> None:
        """Given descriptor_kwargs and payload, when factory called, then returns ValidationAsset."""
        asset = create_validation_asset(
            # Descriptor fields
            asset_id="validation-test",
            name="Test Validation",
            description="Test",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
            # Validation-specific fields
            validation_type="marginal_check",
            benchmark_status="pending",
            criteria={},
        )
        assert isinstance(asset, ValidationAsset)
        assert asset.descriptor.asset_id == "validation-test"
        assert asset.descriptor.data_class == "validation"
        assert asset.validation_type == "marginal_check"


# ============================================================================
# Fixtures for valid descriptors
# ============================================================================


@pytest.fixture
def structural_descriptor() -> DataAssetDescriptor:
    """Valid structural descriptor for testing."""
    return DataAssetDescriptor(
        asset_id="test-population",
        name="Test Population",
        description="Test structural asset",
        data_class="structural",
        origin="synthetic-public",
        access_mode="bundled",
        trust_status="exploratory",
    )


@pytest.fixture
def exogenous_descriptor() -> DataAssetDescriptor:
    """Valid exogenous descriptor for testing."""
    return DataAssetDescriptor(
        asset_id="carbon-tax",
        name="Carbon Tax",
        description="French carbon tax rate",
        data_class="exogenous",
        origin="open-official",
        access_mode="fetched",
        trust_status="production-safe",
    )


@pytest.fixture
def calibration_descriptor() -> DataAssetDescriptor:
    """Valid calibration descriptor for testing."""
    return DataAssetDescriptor(
        asset_id="calibration-test",
        name="Test Calibration",
        description="Test calibration asset",
        data_class="calibration",
        origin="open-official",
        access_mode="fetched",
        trust_status="production-safe",
    )


@pytest.fixture
def validation_descriptor() -> DataAssetDescriptor:
    """Valid validation descriptor for testing."""
    return DataAssetDescriptor(
        asset_id="validation-test",
        name="Test Validation",
        description="Test validation asset",
        data_class="validation",
        origin="open-official",
        access_mode="fetched",
        trust_status="production-safe",
    )


# ============================================================================
# Story 21.5 Tests - Calibration/Validation Asset Extensions
# ============================================================================


class TestCalibrationAssetStory21_5:
    """Tests for CalibrationAsset Story 21.5 extensions.

    Story 21.5 / Task 1 - Train/test separation fields.
    """

    def test_new_train_test_separation_fields(self) -> None:
        """Given calibration asset, when created with new fields, then fields are accessible."""
        descriptor = DataAssetDescriptor(
            asset_id="calibration-test",
            name="Test Calibration",
            description="Test calibration with new fields",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = CalibrationAsset(
            descriptor=descriptor,
            target_type="transition_rate",
            coverage="national",
            # Story 21.5 / Task 1: New train/test separation fields
            is_in_sample=True,
            holdout_group="train",
            calibration_method="maximum_likelihood",
            target_years=(2015, 2016, 2017, 2018, 2019, 2020),
        )
        assert asset.is_in_sample is True
        assert asset.holdout_group == "train"
        assert asset.calibration_method == "maximum_likelihood"
        assert asset.target_years == (2015, 2016, 2017, 2018, 2019, 2020)

    def test_holdout_group_validation_accepts_valid_values(self) -> None:
        """Given valid holdout_group values, when created, then succeeds."""
        descriptor = DataAssetDescriptor(
            asset_id="calibration-test",
            name="Test",
            description="Test",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        for holdout_group in ["train", "validation", "test", None]:
            asset = CalibrationAsset(
                descriptor=descriptor,
                target_type="marginal",
                coverage="national",
                holdout_group=holdout_group,  # type: ignore[arg-type]
            )
            assert asset.holdout_group == holdout_group

    def test_invalid_holdout_group_raises_error(self) -> None:
        """Given invalid holdout_group, when created, then raises."""
        descriptor = DataAssetDescriptor(
            asset_id="calibration-test",
            name="Test",
            description="Test",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        with pytest.raises(EvidenceAssetError, match="holdout_group.*valid HoldoutGroup"):
            CalibrationAsset(
                descriptor=descriptor,
                target_type="marginal",
                coverage="national",
                holdout_group="invalid_group",  # type: ignore[arg-type]
            )

    def test_calibration_method_validation(self) -> None:
        """Given each valid calibration_method, when created, then succeeds."""
        descriptor = DataAssetDescriptor(
            asset_id="calibration-test",
            name="Test",
            description="Test",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        for method in ["maximum_likelihood", "method_of_moments", "bayesian"]:
            asset = CalibrationAsset(
                descriptor=descriptor,
                target_type="marginal",
                coverage="national",
                calibration_method=method,  # type: ignore[arg-type]
            )
            assert asset.calibration_method == method

    def test_invalid_calibration_method_raises_error(self) -> None:
        """Given invalid calibration_method, when created, then raises."""
        descriptor = DataAssetDescriptor(
            asset_id="calibration-test",
            name="Test",
            description="Test",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        with pytest.raises(EvidenceAssetError, match="calibration_method.*valid CalibrationMethod"):
            CalibrationAsset(
                descriptor=descriptor,
                target_type="marginal",
                coverage="national",
                calibration_method="invalid_method",  # type: ignore[arg-type]
            )

    def test_to_json_includes_new_fields(self) -> None:
        """Given calibration asset with new fields, when serialized, then includes new fields."""
        descriptor = DataAssetDescriptor(
            asset_id="calibration-test",
            name="Test",
            description="Test",
            data_class="calibration",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = CalibrationAsset(
            descriptor=descriptor,
            target_type="transition_rate",
            coverage="national",
            is_in_sample=False,
            holdout_group="validation",
            calibration_method="bayesian",
            target_years=(2021, 2022),
        )
        json_dict = asset.to_json()
        assert json_dict["is_in_sample"] is False
        assert json_dict["holdout_group"] == "validation"
        assert json_dict["calibration_method"] == "bayesian"
        assert json_dict["target_years"] == [2021, 2022]

    def test_from_json_restores_new_fields(self) -> None:
        """Given JSON with new fields, when deserialized, then restores all fields."""
        json_dict = {
            "descriptor": {
                "asset_id": "calibration-test",
                "name": "Test",
                "description": "Test",
                "data_class": "calibration",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            },
            "target_type": "adoption_rate",
            "coverage": "regional",
            # Story 21.5 / Task 1: New fields
            "is_in_sample": True,
            "holdout_group": "test",
            "calibration_method": "method_of_moments",
            "target_years": [2018, 2019, 2020],
        }
        asset = CalibrationAsset.from_json(json_dict)
        assert asset.is_in_sample is True
        assert asset.holdout_group == "test"
        assert asset.calibration_method == "method_of_moments"
        assert asset.target_years == (2018, 2019, 2020)

    def test_from_json_backward_compatible_without_new_fields(self) -> None:
        """Given JSON without new fields, when deserialized, then uses defaults."""
        json_dict = {
            "descriptor": {
                "asset_id": "calibration-test",
                "name": "Test",
                "description": "Test",
                "data_class": "calibration",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            },
            "target_type": "marginal",
            "coverage": "national",
        }
        asset = CalibrationAsset.from_json(json_dict)
        # Default values for new fields
        assert asset.is_in_sample is True  # Default
        assert asset.holdout_group is None  # Default
        assert asset.calibration_method == "maximum_likelihood"  # Default
        assert asset.target_years == ()  # Default

    def test_from_json_validates_target_years_are_integers(self) -> None:
        """Given target_years with non-integers, when deserialized, then raises."""
        json_dict = {
            "descriptor": {
                "asset_id": "calibration-test",
                "name": "Test",
                "description": "Test",
                "data_class": "calibration",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            },
            "target_type": "marginal",
            "coverage": "national",
            "target_years": [2015, "invalid", 2017],  # Invalid: string in list
        }
        with pytest.raises(EvidenceAssetError, match="target_years.*contains invalid value"):
            CalibrationAsset.from_json(json_dict)


class TestValidationAssetStory21_5:
    """Tests for ValidationAsset Story 21.5 extensions.

    Story 21.5 / Task 1 - Certification fields.
    """

    def test_new_certification_fields(self) -> None:
        """Given validation asset, when created with new fields, then fields are accessible."""
        descriptor = DataAssetDescriptor(
            asset_id="validation-test",
            name="Test Validation",
            description="Test validation with new fields",
            data_class="validation",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ValidationAsset(
            descriptor=descriptor,
            validation_type="marginal_check",
            benchmark_status="passed",
            criteria={"max_relative_error": 0.05},
            # Story 21.5 / Task 1: New certification fields
            certified_at="2026-03-27T15:00:00Z",
            certified_by="analyst@example.com",
            validation_method="holdout",
            holdout_years=(2021, 2022),
        )
        assert asset.certified_at == "2026-03-27T15:00:00Z"
        assert asset.certified_by == "analyst@example.com"
        assert asset.validation_method == "holdout"
        assert asset.holdout_years == (2021, 2022)

    def test_validation_method_validation(self) -> None:
        """Given each valid validation_method, when created, then succeeds."""
        descriptor = DataAssetDescriptor(
            asset_id="validation-test",
            name="Test",
            description="Test",
            data_class="validation",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        for method in ["holdout", "cross_validation", "external", "bootstrap"]:
            asset = ValidationAsset(
                descriptor=descriptor,
                validation_type="marginal_check",
                benchmark_status="passed",
                criteria={},
                validation_method=method,  # type: ignore[arg-type]
            )
            assert asset.validation_method == method

    def test_invalid_validation_method_raises_error(self) -> None:
        """Given invalid validation_method, when created, then raises."""
        descriptor = DataAssetDescriptor(
            asset_id="validation-test",
            name="Test",
            description="Test",
            data_class="validation",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        with pytest.raises(EvidenceAssetError, match="validation_method.*valid ValidationMethod"):
            ValidationAsset(
                descriptor=descriptor,
                validation_type="marginal_check",
                benchmark_status="passed",
                criteria={},
                validation_method="invalid_method",  # type: ignore[arg-type]
            )

    def test_to_json_includes_new_fields(self) -> None:
        """Given validation asset with new fields, when serialized, then includes new fields."""
        descriptor = DataAssetDescriptor(
            asset_id="validation-test",
            name="Test",
            description="Test",
            data_class="validation",
            origin="open-official",
            access_mode="fetched",
            trust_status="production-safe",
        )
        asset = ValidationAsset(
            descriptor=descriptor,
            validation_type="joint_distribution",
            benchmark_status="passed",
            criteria={"chi_squared_p_value": 0.95},
            certified_at="2026-03-27T10:30:00Z",
            certified_by="system",
            validation_method="cross_validation",
            holdout_years=(2020, 2021, 2022),
        )
        json_dict = asset.to_json()
        assert json_dict["certified_at"] == "2026-03-27T10:30:00Z"
        assert json_dict["certified_by"] == "system"
        assert json_dict["validation_method"] == "cross_validation"
        assert json_dict["holdout_years"] == [2020, 2021, 2022]

    def test_from_json_restores_new_fields(self) -> None:
        """Given JSON with new fields, when deserialized, then restores all fields."""
        json_dict = {
            "descriptor": {
                "asset_id": "validation-test",
                "name": "Test",
                "description": "Test",
                "data_class": "validation",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            },
            "validation_type": "subgroup_stability",
            "benchmark_status": "passed",
            "criteria": {"min_subgroup_n": 100},
            # Story 21.5 / Task 1: New certification fields
            "certified_at": "2026-03-27T12:00:00Z",
            "certified_by": "expert@institution.edu",
            "validation_method": "external",
            "holdout_years": [2021],
        }
        asset = ValidationAsset.from_json(json_dict)
        assert asset.certified_at == "2026-03-27T12:00:00Z"
        assert asset.certified_by == "expert@institution.edu"
        assert asset.validation_method == "external"
        assert asset.holdout_years == (2021,)

    def test_from_json_backward_compatible_without_new_fields(self) -> None:
        """Given JSON without new fields, when deserialized, then uses defaults."""
        json_dict = {
            "descriptor": {
                "asset_id": "validation-test",
                "name": "Test",
                "description": "Test",
                "data_class": "validation",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            },
            "validation_type": "marginal_check",
            "benchmark_status": "pending",
            "criteria": {},
        }
        asset = ValidationAsset.from_json(json_dict)
        # Default values for new fields
        assert asset.certified_at is None  # Default
        assert asset.certified_by is None  # Default
        assert asset.validation_method == "holdout"  # Default
        assert asset.holdout_years == ()  # Default

    def test_from_json_validates_holdout_years_are_integers(self) -> None:
        """Given holdout_years with non-integers, when deserialized, then raises."""
        json_dict = {
            "descriptor": {
                "asset_id": "validation-test",
                "name": "Test",
                "description": "Test",
                "data_class": "validation",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            },
            "validation_type": "marginal_check",
            "benchmark_status": "passed",
            "criteria": {},
            "holdout_years": [2021, "invalid", 2022],  # Invalid: string in list
        }
        with pytest.raises(EvidenceAssetError, match="holdout_years.*contains invalid value"):
            ValidationAsset.from_json(json_dict)


class TestAssetLoadFunctionsStory21_5:
    """Tests for asset load functions.

    Story 21.5 / Task 1, Task 5.
    """

    def test_load_calibration_asset_missing_folder_raises_error(self, tmp_path) -> None:
        """Given non-existent asset_id, when loading, then raises EvidenceAssetError."""
        # Temporarily override base path for test
        import reformlab.data.assets as assets_module
        original_path = assets_module._CALIBRATION_ASSETS_BASE_PATH
        assets_module._CALIBRATION_ASSETS_BASE_PATH = tmp_path

        try:
            with pytest.raises(EvidenceAssetError, match="folder does not exist"):
                assets_module.load_calibration_asset("non-existent-asset")
        finally:
            assets_module._CALIBRATION_ASSETS_BASE_PATH = original_path

    def test_load_validation_asset_missing_folder_raises_error(self, tmp_path) -> None:
        """Given non-existent asset_id, when loading, then raises EvidenceAssetError."""
        import reformlab.data.assets as assets_module
        original_path = assets_module._VALIDATION_ASSETS_BASE_PATH
        assets_module._VALIDATION_ASSETS_BASE_PATH = tmp_path

        try:
            with pytest.raises(EvidenceAssetError, match="folder does not exist"):
                assets_module.load_validation_asset("non-existent-asset")
        finally:
            assets_module._VALIDATION_ASSETS_BASE_PATH = original_path

    def test_load_calibration_asset_missing_descriptor_raises_error(self, tmp_path) -> None:
        """Given asset folder without descriptor.json, when loading, then raises."""
        import reformlab.data.assets as assets_module
        original_path = assets_module._CALIBRATION_ASSETS_BASE_PATH
        assets_module._CALIBRATION_ASSETS_BASE_PATH = tmp_path

        try:
            # Create folder but no descriptor.json
            asset_folder = tmp_path / "test-asset"
            asset_folder.mkdir()

            with pytest.raises(EvidenceAssetError, match="missing required file.*descriptor.json"):
                assets_module.load_calibration_asset("test-asset")
        finally:
            assets_module._VALIDATION_ASSETS_BASE_PATH = original_path

    def test_load_calibration_asset_missing_metadata_raises_error(self, tmp_path) -> None:
        """Given asset folder without metadata.json, when loading, then raises."""
        import reformlab.data.assets as assets_module
        original_path = assets_module._CALIBRATION_ASSETS_BASE_PATH
        assets_module._CALIBRATION_ASSETS_BASE_PATH = tmp_path

        try:
            # Create folder with descriptor.json but no metadata.json
            asset_folder = tmp_path / "test-asset"
            asset_folder.mkdir()

            import json
            with (asset_folder / "descriptor.json").open("w") as f:
                json.dump({
                    "asset_id": "test-asset",
                    "name": "Test",
                    "description": "Test",
                    "data_class": "calibration",
                    "origin": "open-official",
                    "access_mode": "fetched",
                    "trust_status": "production-safe",
                }, f)

            with pytest.raises(EvidenceAssetError, match="missing required file.*metadata.json"):
                assets_module.load_calibration_asset("test-asset")
        finally:
            assets_module._CALIBRATION_ASSETS_BASE_PATH = original_path

    def test_load_calibration_asset_success(self, tmp_path) -> None:
        """Given valid asset folder, when loading, then returns CalibrationAsset."""
        import json

        import reformlab.data.assets as assets_module

        original_path = assets_module._CALIBRATION_ASSETS_BASE_PATH
        assets_module._CALIBRATION_ASSETS_BASE_PATH = tmp_path

        try:
            asset_folder = tmp_path / "test-calibration"
            asset_folder.mkdir()

            # Write descriptor.json
            descriptor = {
                "asset_id": "test-calibration",
                "name": "Test Calibration",
                "description": "Test calibration asset",
                "data_class": "calibration",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            }
            with (asset_folder / "descriptor.json").open("w") as f:
                json.dump(descriptor, f)

            # Write metadata.json with Story 21.5 fields
            metadata = {
                "target_type": "transition_rate",
                "coverage": "national",
                "is_in_sample": True,
                "holdout_group": "train",
                "calibration_method": "maximum_likelihood",
                "target_years": [2015, 2016, 2017],
            }
            with (asset_folder / "metadata.json").open("w") as f:
                json.dump(metadata, f)

            asset = assets_module.load_calibration_asset("test-calibration")
            assert asset.descriptor.asset_id == "test-calibration"
            assert asset.target_type == "transition_rate"
            assert asset.is_in_sample is True
            assert asset.holdout_group == "train"
            assert asset.calibration_method == "maximum_likelihood"
            assert asset.target_years == (2015, 2016, 2017)
        finally:
            assets_module._CALIBRATION_ASSETS_BASE_PATH = original_path

    def test_load_validation_asset_success(self, tmp_path) -> None:
        """Given valid asset folder, when loading, then returns ValidationAsset."""
        import json

        import reformlab.data.assets as assets_module

        original_path = assets_module._VALIDATION_ASSETS_BASE_PATH
        assets_module._VALIDATION_ASSETS_BASE_PATH = tmp_path

        try:
            asset_folder = tmp_path / "test-validation"
            asset_folder.mkdir()

            # Write descriptor.json
            descriptor = {
                "asset_id": "test-validation",
                "name": "Test Validation",
                "description": "Test validation asset",
                "data_class": "validation",
                "origin": "open-official",
                "access_mode": "fetched",
                "trust_status": "production-safe",
            }
            with (asset_folder / "descriptor.json").open("w") as f:
                json.dump(descriptor, f)

            # Write metadata.json with Story 21.5 fields
            metadata = {
                "validation_type": "marginal_check",
                "benchmark_status": "passed",
                "criteria": {"max_relative_error": 0.05},
                "certified_at": "2026-03-27T15:00:00Z",
                "certified_by": "analyst@example.com",
                "validation_method": "holdout",
                "holdout_years": [2021, 2022],
            }
            with (asset_folder / "metadata.json").open("w") as f:
                json.dump(metadata, f)

            asset = assets_module.load_validation_asset("test-validation")
            assert asset.descriptor.asset_id == "test-validation"
            assert asset.validation_type == "marginal_check"
            assert asset.certified_at == "2026-03-27T15:00:00Z"
            assert asset.certified_by == "analyst@example.com"
            assert asset.validation_method == "holdout"
            assert asset.holdout_years == (2021, 2022)
        finally:
            assets_module._VALIDATION_ASSETS_BASE_PATH = original_path
