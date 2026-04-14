# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for result_normalizer module.

Story 23.3: Normalize live OpenFisca results into the stable app-facing output schema

Tests cover:
- NormalizationError structure (AC: 4)
- Renaming known OpenFisca variables (AC: 1)
- Passing through unknown columns (AC: 1)
- Explicit MappingConfig usage (AC: 1)
- Default mapping usage (AC: 1)
- Error on incompatible schema (AC: 4)
- Minimum columns threshold (AC: 1, 4)
- Factory pattern for normalizer (AC: 1)
- Stub for entity table normalization (AC: 1)
- Runtime mode behavior (live vs replay) (AC: 1, 5)
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.computation.mapping import MappingConfig
from reformlab.computation.result_normalizer import (
    _DEFAULT_OUTPUT_MAPPING,
    _MINIMUM_REQUIRED_COLUMNS,
    MAPPING_APPLIED_KEY,
    NORMALIZED_KEY,
    NormalizationError,
    create_live_normalizer,
    normalize_computation_result,
    normalize_entity_tables,
)
from reformlab.computation.types import ComputationResult


class TestNormalizationError:
    """Test NormalizationError exception class (AC: 4)."""

    def test_error_has_what_why_fix(self) -> None:
        """Error detail follows project pattern."""
        exc = NormalizationError(
            what="Output normalization failed",
            why="No recognizable columns",
            fix="Provide valid mapping",
        )
        assert exc.what == "Output normalization failed"
        assert exc.why == "No recognizable columns"
        assert exc.fix == "Provide valid mapping"
        # Error message includes all three parts
        assert "Output normalization failed" in str(exc)
        assert "No recognizable columns" in str(exc)
        assert "Provide valid mapping" in str(exc)


class TestNormalizeComputationResult:
    """Test normalize_computation_result function (AC: 1, 4)."""

    def test_renames_known_openfisca_variables(self) -> None:
        """'revenu_disponible' -> 'disposable_income', 'salaire_net' -> 'income'."""
        table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "revenu_disponible": pa.array([50000.0, 60000.0, 70000.0]),
            "salaire_net": pa.array([45000.0, 55000.0, 65000.0]),
            "taxe_carbone": pa.array([100.0, 200.0, 300.0]),
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="test-1.0.0",
            period=2025,
        )

        result = normalize_computation_result(comp_result, mapping_config=None)

        # Known variables renamed
        assert "disposable_income" in result.column_names
        assert "income" in result.column_names
        assert "carbon_tax" in result.column_names

        # Original OpenFisca names removed
        assert "revenu_disponible" not in result.column_names
        assert "salaire_net" not in result.column_names
        assert "taxe_carbone" not in result.column_names

        # Values preserved
        assert result.column("disposable_income").to_pylist() == [50000.0, 60000.0, 70000.0]
        assert result.column("income").to_pylist() == [45000.0, 55000.0, 65000.0]
        assert result.column("carbon_tax").to_pylist() == [100.0, 200.0, 300.0]

    def test_passes_through_unknown_columns(self) -> None:
        """Columns not in mapping are preserved."""
        table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([50000.0, 60000.0, 70000.0]),
            "unknown_field_1": pa.array(["a", "b", "c"]),
            "unknown_field_2": pa.array([10, 20, 30]),
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="test-1.0.0",
            period=2025,
        )

        result = normalize_computation_result(comp_result, mapping_config=None)

        # Unknown columns passed through unchanged
        assert "unknown_field_1" in result.column_names
        assert "unknown_field_2" in result.column_names
        assert result.column("unknown_field_1").to_pylist() == ["a", "b", "c"]
        assert result.column("unknown_field_2").to_pylist() == [10, 20, 30]

    def test_with_explicit_mapping_config(self) -> None:
        """Uses MappingConfig when provided."""
        # Create a custom MappingConfig
        mapping_config = MappingConfig(
            mappings=(),
        )

        # Since we're testing the path, we'll use a result with a required column
        # to pass validation
        table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([50000.0, 60000.0, 70000.0]),  # Required column
            "custom_field": pa.array([10, 20, 30]),
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="test-1.0.0",
            period=2025,
        )

        # With empty mapping, should pass through unchanged
        result = normalize_computation_result(comp_result, mapping_config=mapping_config)
        assert "income" in result.column_names
        assert "custom_field" in result.column_names

    def test_without_mapping_uses_defaults(self) -> None:
        """Uses _DEFAULT_OUTPUT_MAPPING."""
        table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "salaire_net": pa.array([45000.0, 55000.0, 65000.0]),  # Maps to income (required)
            "irpp": pa.array([3000.0, 4000.0, 5000.0]),  # Income tax
            "revenu_net": pa.array([47000.0, 56000.0, 65000.0]),  # Net income
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="test-1.0.0",
            period=2025,
        )

        result = normalize_computation_result(comp_result, mapping_config=None)

        # Default mapping applied
        assert "income" in result.column_names
        assert "income_tax" in result.column_names
        assert "net_income" in result.column_names
        assert "salaire_net" not in result.column_names
        assert "irpp" not in result.column_names
        assert "revenu_net" not in result.column_names

    def test_raises_on_empty_or_incompatible_schema(self) -> None:
        """NormalizationError when no columns from _MINIMUM_REQUIRED_COLUMNS are present."""
        table = pa.table({
            "ncc": pa.array([1, 2, 3]),
            "agec": pa.array([25, 30, 35]),
            "ageq": pa.array([40, 45, 50]),
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="test-1.0.0",
            period=2025,
        )

        expected_cols = sorted(list(_MINIMUM_REQUIRED_COLUMNS))
        available_cols = ["ncc", "agec", "ageq"]

        with pytest.raises(NormalizationError) as exc_info:
            normalize_computation_result(comp_result, mapping_config=None)

        error = exc_info.value
        assert error.what == "Output normalization failed"
        assert "no recognizable output columns" in error.why.lower()
        for col in expected_cols:
            assert col in error.why
        for col in available_cols:
            assert col in error.why
        assert "MappingConfig" in error.fix

    def test_minimum_columns_threshold(self) -> None:
        """Succeeds when at least one column from _MINIMUM_REQUIRED_COLUMNS survives."""
        # Only 'income' from required set - should pass
        table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "salaire_net": pa.array([45000.0, 55000.0, 65000.0]),  # Maps to 'income'
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="test-1.0.0",
            period=2025,
        )

        result = normalize_computation_result(comp_result, mapping_config=None)
        assert "income" in result.column_names

    def test_ensures_household_id_column(self) -> None:
        """Ensures household_id column exists (delegates to _ensure_household_id_column pattern)."""
        # Table without household_id but with person_id
        table = pa.table({
            "person_id": pa.array([100, 200, 300], type=pa.int64()),
            "income": pa.array([50000.0, 60000.0, 70000.0]),
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="test-1.0.0",
            period=2025,
        )

        result = normalize_computation_result(comp_result, mapping_config=None)
        assert "household_id" in result.column_names
        # person_id values should become household_id
        assert result.column("household_id").to_pylist() == [100, 200, 300]

    def test_default_mapping_constants(self) -> None:
        """Verify _DEFAULT_OUTPUT_MAPPING contains expected mappings."""
        assert _DEFAULT_OUTPUT_MAPPING.get("revenu_disponible") == "disposable_income"
        assert _DEFAULT_OUTPUT_MAPPING.get("irpp") == "income_tax"
        assert _DEFAULT_OUTPUT_MAPPING.get("impots_directs") == "direct_taxes"
        assert _DEFAULT_OUTPUT_MAPPING.get("revenu_net") == "net_income"
        assert _DEFAULT_OUTPUT_MAPPING.get("salaire_net") == "income"
        assert _DEFAULT_OUTPUT_MAPPING.get("revenu_brut") == "gross_income"
        assert _DEFAULT_OUTPUT_MAPPING.get("prestations_sociales") == "social_benefits"
        assert _DEFAULT_OUTPUT_MAPPING.get("taxe_carbone") == "carbon_tax"

    def test_minimum_required_columns_constant(self) -> None:
        """Verify _MINIMUM_REQUIRED_COLUMNS contains expected columns."""
        assert "household_id" in _MINIMUM_REQUIRED_COLUMNS
        assert "income" in _MINIMUM_REQUIRED_COLUMNS
        assert "disposable_income" in _MINIMUM_REQUIRED_COLUMNS
        assert "carbon_tax" in _MINIMUM_REQUIRED_COLUMNS

    def test_metadata_key_constants(self) -> None:
        """Verify metadata key constants are defined."""
        assert NORMALIZED_KEY == "normalized"
        assert MAPPING_APPLIED_KEY == "mapping_applied"


class TestCreateLiveNormalizer:
    """Test create_live_normalizer factory function (AC: 1)."""

    def test_returns_callable(self) -> None:
        """Factory returns a function accepting ComputationResult."""
        normalizer = create_live_normalizer(mapping_config=None)
        assert callable(normalizer)

        # Create a test ComputationResult
        table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "salaire_net": pa.array([45000.0, 55000.0, 65000.0]),
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="test-1.0.0",
            period=2025,
        )

        # Should not raise
        result = normalizer(comp_result)
        assert "income" in result.column_names

    def test_callable_produces_normalized_table(self) -> None:
        """Factory returns a callable that applies mapping correctly."""
        normalizer = create_live_normalizer(mapping_config=None)

        table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "revenu_disponible": pa.array([50000.0, 60000.0, 70000.0]),
            "taxe_carbone": pa.array([100.0, 200.0, 300.0]),
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="test-1.0.0",
            period=2025,
        )

        result = normalizer(comp_result)
        assert "disposable_income" in result.column_names
        assert "carbon_tax" in result.column_names
        assert result.column("disposable_income").to_pylist() == [50000.0, 60000.0, 70000.0]


class TestNormalizeEntityTables:
    """Test normalize_entity_tables function (AC: 1)."""

    def test_stub_returns_output_fields(self) -> None:
        """First-slice implementation returns comp_result.output_fields directly."""
        table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([50000.0, 60000.0, 70000.0]),
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="test-1.0.0",
            period=2025,
        )

        result = normalize_entity_tables(comp_result, mapping_config=None)

        # Stub returns output_fields directly
        assert result is table


class TestRuntimeModeBehavior:
    """Test runtime mode behavior integration (AC: 1, 5)."""

    def test_live_mode_applies_normalization(self) -> None:
        """Live mode uses normalizer."""
        # This test demonstrates how live mode would use the normalizer
        # Actual integration is in api.py, but we test the pattern here
        normalizer = create_live_normalizer(mapping_config=None)

        # Simulate live OpenFisca output (French variable names)
        table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "salaire_net": pa.array([45000.0, 55000.0, 65000.0]),
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="openfisca-france-44.0.0",
            period=2025,
        )

        result = normalizer(comp_result)
        # Normalization applied
        assert "income" in result.column_names
        assert "salaire_net" not in result.column_names

    def test_replay_mode_skips_normalization(self) -> None:
        """Replay mode passes through as-is (simulated by not calling normalizer)."""
        # In replay mode, normalizer would be None
        # This test shows that without normalizer, output stays the same
        table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([50000.0, 60000.0, 70000.0]),
            "disposable_income": pa.array([45000.0, 55000.0, 65000.0]),
        })
        comp_result = ComputationResult(
            output_fields=table,
            adapter_version="replay-v1.0.0",
            period=2025,
        )

        # Without normalizer (replay mode), output is unchanged
        result = comp_result.output_fields
        assert "income" in result.column_names
        assert "disposable_income" in result.column_names

    def test_both_modes_produce_same_column_names(self) -> None:
        """Both live (with normalizer) and replay (without) produce compatible column names."""
        # Live mode: French names, normalized
        live_table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "salaire_net": pa.array([45000.0, 55000.0, 65000.0]),
            "revenu_disponible": pa.array([47000.0, 57000.0, 67000.0]),
            "taxe_carbone": pa.array([100.0, 200.0, 300.0]),
        })
        live_result = ComputationResult(
            output_fields=live_table,
            adapter_version="openfisca-france-44.0.0",
            period=2025,
        )
        normalizer = create_live_normalizer(mapping_config=None)
        live_normalized = normalizer(live_result)

        # Replay mode: English names already
        replay_table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([45000.0, 55000.0, 65000.0]),
            "disposable_income": pa.array([47000.0, 57000.0, 67000.0]),
            "carbon_tax": pa.array([100.0, 200.0, 300.0]),
        })
        replay_result = ComputationResult(
            output_fields=replay_table,
            adapter_version="replay-v1.0.0",
            period=2025,
        )
        replay_normalized = replay_result.output_fields  # No normalizer

        # Both have the same columns
        assert set(live_normalized.column_names) == set(replay_normalized.column_names)
        assert "income" in live_normalized.column_names
        assert "disposable_income" in live_normalized.column_names
        assert "carbon_tax" in live_normalized.column_names
