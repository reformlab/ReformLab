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
