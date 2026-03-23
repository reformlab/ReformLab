# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for UniformMergeMethod.

Story 11.4 — AC #2: Uniform random matching with replacement, deterministic.
AC #3: Assumption record with exact statement text.
AC #4: Pedagogical docstring on independence assumption.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.population.methods.base import MergeConfig, MergeMethod
from reformlab.population.methods.errors import MergeValidationError
from reformlab.population.methods.uniform import UniformMergeMethod

# ====================================================================
# Protocol compliance
# ====================================================================


class TestUniformMergeMethodProtocol:
    """AC #1: UniformMergeMethod satisfies MergeMethod protocol."""

    def test_isinstance_check(self) -> None:
        method = UniformMergeMethod()
        assert isinstance(method, MergeMethod)


# ====================================================================
# Name property
# ====================================================================


class TestUniformMergeMethodName:
    """Name property returns 'uniform'."""

    def test_name(self) -> None:
        method = UniformMergeMethod()
        assert method.name == "uniform"


# ====================================================================
# Basic merge behavior
# ====================================================================


class TestUniformMergeMethodMerge:
    """AC #2: Basic merge functionality."""

    def test_merged_row_count_equals_table_a(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        result = method.merge(income_table, vehicle_table, default_config)
        assert result.table.num_rows == income_table.num_rows

    def test_merged_column_count(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        result = method.merge(income_table, vehicle_table, default_config)
        expected_cols = income_table.num_columns + vehicle_table.num_columns
        assert result.table.num_columns == expected_cols

    def test_merged_column_names(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        result = method.merge(income_table, vehicle_table, default_config)
        expected_names = (
            income_table.schema.names + vehicle_table.schema.names
        )
        assert result.table.schema.names == expected_names

    def test_table_a_values_preserved(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        result = method.merge(income_table, vehicle_table, default_config)
        for col_name in income_table.schema.names:
            assert result.table.column(col_name).equals(
                income_table.column(col_name)
            )

    def test_table_b_values_from_actual_rows(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        """Verify row-level coherence: matched rows must exist in table_b."""
        method = UniformMergeMethod()
        result = method.merge(income_table, vehicle_table, default_config)
        right_col_names = vehicle_table.schema.names
        valid_row_combos = set(
            zip(*(vehicle_table.column(c).to_pylist() for c in right_col_names))
        )
        for i in range(result.table.num_rows):
            combo = tuple(
                result.table.column(c)[i].as_py() for c in right_col_names
            )
            assert combo in valid_row_combos, (
                f"Row {i} {combo!r} is not a row from vehicle_table — "
                "merge is not preserving row-level coherence"
            )


# ====================================================================
# Determinism
# ====================================================================


class TestUniformMergeMethodDeterminism:
    """AC #2: Same seed → identical results; different seed → different."""

    def test_same_seed_same_result(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
    ) -> None:
        method = UniformMergeMethod()
        config = MergeConfig(seed=12345)
        result_1 = method.merge(income_table, vehicle_table, config)
        result_2 = method.merge(income_table, vehicle_table, config)
        assert result_1.table.equals(result_2.table)

    def test_different_seed_different_result(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
    ) -> None:
        method = UniformMergeMethod()
        result_1 = method.merge(
            income_table, vehicle_table, MergeConfig(seed=1)
        )
        result_2 = method.merge(
            income_table, vehicle_table, MergeConfig(seed=2)
        )
        # Deterministic: seeds 1 and 2 produce different PRNG sequences,
        # so the right-table columns must differ between the two results.
        right_cols = vehicle_table.schema.names
        matched_1 = {c: result_1.table.column(c).to_pylist() for c in right_cols}
        matched_2 = {c: result_2.table.column(c).to_pylist() for c in right_cols}
        assert matched_1 != matched_2


# ====================================================================
# Column conflict detection
# ====================================================================


class TestUniformMergeMethodColumnConflict:
    """AC #2: Overlapping column names raise MergeValidationError."""

    def test_overlapping_columns_raises(
        self,
        income_table: pa.Table,
        overlapping_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        with pytest.raises(
            MergeValidationError, match="region_code"
        ):
            method.merge(income_table, overlapping_table, default_config)

    def test_error_mentions_column_conflict(
        self,
        income_table: pa.Table,
        overlapping_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        with pytest.raises(MergeValidationError, match="Column name conflict"):
            method.merge(income_table, overlapping_table, default_config)


# ====================================================================
# drop_right_columns
# ====================================================================


class TestUniformMergeMethodDropRightColumns:
    """AC #2: drop_right_columns removes columns from right table."""

    def test_drop_resolves_conflict(
        self,
        income_table: pa.Table,
        overlapping_table: pa.Table,
    ) -> None:
        method = UniformMergeMethod()
        config = MergeConfig(seed=42, drop_right_columns=("region_code",))
        result = method.merge(income_table, overlapping_table, config)
        assert result.table.num_rows == income_table.num_rows
        assert "heating_type" in result.table.schema.names
        # region_code appears once (from income_table only)
        assert result.table.schema.names.count("region_code") == 1

    def test_nonexistent_column_raises(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
    ) -> None:
        method = UniformMergeMethod()
        config = MergeConfig(seed=42, drop_right_columns=("nonexistent",))
        with pytest.raises(
            MergeValidationError, match="nonexistent"
        ):
            method.merge(income_table, vehicle_table, config)


# ====================================================================
# Empty table validation
# ====================================================================


class TestUniformMergeMethodEmptyTable:
    """AC #2: Empty tables raise MergeValidationError."""

    def test_empty_table_a_raises(
        self,
        empty_table: pa.Table,
        vehicle_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        with pytest.raises(MergeValidationError, match="Empty left table"):
            method.merge(empty_table, vehicle_table, default_config)

    def test_empty_table_b_raises(
        self,
        income_table: pa.Table,
        empty_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        with pytest.raises(MergeValidationError, match="Empty right table"):
            method.merge(income_table, empty_table, default_config)


# ====================================================================
# Assumption record
# ====================================================================


class TestUniformMergeMethodAssumption:
    """AC #3: Assumption record with exact statement and governance entry."""

    def test_method_name(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        result = method.merge(income_table, vehicle_table, default_config)
        assert result.assumption.method_name == "uniform"

    def test_statement_text(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        result = method.merge(income_table, vehicle_table, default_config)
        assert result.assumption.statement == (
            "Each household in source A is matched to a household in "
            "source B with uniform probability \u2014 this assumes no "
            "correlation between the variables in the two sources."
        )

    def test_details_content(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        result = method.merge(income_table, vehicle_table, default_config)
        details = result.assumption.details
        assert details["table_a_rows"] == 5
        assert details["table_b_rows"] == 8
        assert details["seed"] == 42
        assert details["with_replacement"] is True
        assert details["dropped_right_columns"] == []

    def test_governance_entry(
        self,
        income_table: pa.Table,
        vehicle_table: pa.Table,
        default_config: MergeConfig,
    ) -> None:
        method = UniformMergeMethod()
        result = method.merge(income_table, vehicle_table, default_config)
        entry = result.assumption.to_governance_entry()
        assert entry["key"] == "merge_uniform"
        assert entry["source"] == "merge_step"
        assert entry["is_default"] is False
        assert "method" in entry["value"]
        assert "statement" in entry["value"]


# ====================================================================
# With-replacement behavior
# ====================================================================


class TestUniformMergeMethodWithReplacement:
    """AC #2: Merge works regardless of relative table sizes."""

    def test_table_a_larger_than_table_b(self) -> None:
        table_a = pa.table({"a": pa.array(range(20), type=pa.int64())})
        table_b = pa.table({"b": pa.array(range(3), type=pa.int64())})
        method = UniformMergeMethod()
        result = method.merge(table_a, table_b, MergeConfig(seed=0))
        assert result.table.num_rows == 20

    def test_table_a_smaller_than_table_b(self) -> None:
        table_a = pa.table({"a": pa.array(range(3), type=pa.int64())})
        table_b = pa.table({"b": pa.array(range(20), type=pa.int64())})
        method = UniformMergeMethod()
        result = method.merge(table_a, table_b, MergeConfig(seed=0))
        assert result.table.num_rows == 3

    def test_equal_size_tables(self) -> None:
        table_a = pa.table({"a": pa.array(range(10), type=pa.int64())})
        table_b = pa.table({"b": pa.array(range(10), type=pa.int64())})
        method = UniformMergeMethod()
        result = method.merge(table_a, table_b, MergeConfig(seed=0))
        assert result.table.num_rows == 10


# ====================================================================
# Docstring (pedagogical content)
# ====================================================================


class TestUniformMergeMethodDocstring:
    """AC #4: Pedagogical docstring on independence assumption."""

    def test_class_docstring_nonempty(self) -> None:
        assert UniformMergeMethod.__doc__
        assert len(UniformMergeMethod.__doc__.strip()) > 0

    def test_class_docstring_mentions_independence(self) -> None:
        doc = UniformMergeMethod.__doc__ or ""
        assert "no correlation" in doc.lower() or "independence" in doc.lower()

    def test_module_docstring_pedagogical(self) -> None:
        import reformlab.population.methods.uniform as mod

        doc = mod.__doc__ or ""
        assert "appropriate" in doc.lower()
        assert "problematic" in doc.lower()
