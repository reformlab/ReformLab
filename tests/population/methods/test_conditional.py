# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for ConditionalSamplingMethod.

Story 11.5 — AC #3: Conditional sampling matches within strata.
AC #4: Assumption record states conditioning variable and assumption.
AC #5: Pedagogical docstrings for policy analysts.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.population.methods.base import MergeConfig, MergeMethod
from reformlab.population.methods.conditional import ConditionalSamplingMethod
from reformlab.population.methods.errors import MergeValidationError

# ====================================================================
# Protocol compliance
# ====================================================================


class TestConditionalSamplingMethodProtocol:
    """AC #3: ConditionalSamplingMethod satisfies MergeMethod protocol."""

    def test_isinstance_check(self) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        assert isinstance(method, MergeMethod)


# ====================================================================
# Name property
# ====================================================================


class TestConditionalSamplingMethodName:
    """Name property returns 'conditional'."""

    def test_name(self) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        assert method.name == "conditional"


# ====================================================================
# Constructor validation
# ====================================================================


class TestConditionalSamplingMethodConstructorValidation:
    """Constructor validates strata_columns."""

    def test_empty_strata_columns_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty tuple"):
            ConditionalSamplingMethod(strata_columns=())

    def test_empty_string_in_strata_columns_raises(self) -> None:
        with pytest.raises(ValueError, match="empty strings"):
            ConditionalSamplingMethod(strata_columns=("",))

    def test_mixed_empty_string_raises(self) -> None:
        with pytest.raises(ValueError, match="empty strings"):
            ConditionalSamplingMethod(
                strata_columns=("income_bracket", "")
            )


# ====================================================================
# Basic merge behavior
# ====================================================================


class TestConditionalSamplingMethodMerge:
    """AC #3: Basic conditional sampling merge functionality."""

    def test_merged_row_count_equals_table_a(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        result = method.merge(
            region_income_table,
            energy_vehicle_table,
            MergeConfig(seed=42),
        )
        assert result.table.num_rows == region_income_table.num_rows

    def test_merged_table_has_correct_columns(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        result = method.merge(
            region_income_table,
            energy_vehicle_table,
            MergeConfig(seed=42),
        )
        # table_a columns + table_b columns minus strata column from b
        expected = region_income_table.schema.names + [
            c
            for c in energy_vehicle_table.schema.names
            if c != "income_bracket"
        ]
        assert result.table.schema.names == expected


# ====================================================================
# Strata respected
# ====================================================================


class TestConditionalSamplingMethodStrataRespected:
    """AC #3: Matches respect stratum membership."""

    def test_matches_within_strata(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        """Every merged row's income_bracket matches the donor's bracket."""
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        result = method.merge(
            region_income_table,
            energy_vehicle_table,
            MergeConfig(seed=42),
        )
        # Build lookup: for each vehicle_type + energy_kwh combo,
        # find which income_bracket(s) it came from in table_b
        b_rows: dict[tuple[object, ...], set[str]] = {}
        vt_list = energy_vehicle_table.column("vehicle_type").to_pylist()
        ek_list = energy_vehicle_table.column("energy_kwh").to_pylist()
        ib_list = energy_vehicle_table.column("income_bracket").to_pylist()
        for i in range(energy_vehicle_table.num_rows):
            key = (vt_list[i], ek_list[i])
            b_rows.setdefault(key, set()).add(ib_list[i])

        # For each merged row, the donor's income_bracket should match
        merged_ib = result.table.column("income_bracket").to_pylist()
        merged_vt = result.table.column("vehicle_type").to_pylist()
        merged_ek = result.table.column("energy_kwh").to_pylist()
        for i in range(result.table.num_rows):
            donor_key = (merged_vt[i], merged_ek[i])
            assert merged_ib[i] in b_rows[donor_key], (
                f"Row {i}: income_bracket={merged_ib[i]} but donor "
                f"came from bracket(s) {b_rows[donor_key]}"
            )


# ====================================================================
# Determinism
# ====================================================================


class TestConditionalSamplingMethodDeterminism:
    """Same seed → identical result; different seed → different."""

    def test_same_seed_same_result(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        config = MergeConfig(seed=12345)
        result_1 = method.merge(
            region_income_table, energy_vehicle_table, config
        )
        result_2 = method.merge(
            region_income_table, energy_vehicle_table, config
        )
        assert result_1.table.equals(result_2.table)

    def test_different_seed_different_result(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        result_1 = method.merge(
            region_income_table,
            energy_vehicle_table,
            MergeConfig(seed=1),
        )
        result_2 = method.merge(
            region_income_table,
            energy_vehicle_table,
            MergeConfig(seed=2),
        )
        # Right-table columns should differ
        right_cols = [
            c
            for c in energy_vehicle_table.schema.names
            if c != "income_bracket"
        ]
        matched_1 = {
            c: result_1.table.column(c).to_pylist() for c in right_cols
        }
        matched_2 = {
            c: result_2.table.column(c).to_pylist() for c in right_cols
        }
        assert matched_1 != matched_2


# ====================================================================
# Column conflict detection
# ====================================================================


class TestConditionalSamplingMethodColumnConflict:
    """Overlapping non-strata columns raise MergeValidationError."""

    def test_overlapping_columns_raises(self) -> None:
        table_a = pa.table(
            {
                "stratum": pa.array(["a", "b"], type=pa.utf8()),
                "shared_col": pa.array([1, 2], type=pa.int64()),
            }
        )
        table_b = pa.table(
            {
                "stratum": pa.array(["a", "b"], type=pa.utf8()),
                "shared_col": pa.array([3, 4], type=pa.int64()),
            }
        )
        method = ConditionalSamplingMethod(strata_columns=("stratum",))
        with pytest.raises(
            MergeValidationError, match="Column name conflict"
        ):
            method.merge(table_a, table_b, MergeConfig(seed=42))


# ====================================================================
# drop_right_columns
# ====================================================================


class TestConditionalSamplingMethodDropRightColumns:
    """drop_right_columns and auto-drop of strata columns."""

    def test_strata_columns_auto_dropped_from_table_b(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        """Strata columns from table_b are not duplicated in output."""
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        result = method.merge(
            region_income_table,
            energy_vehicle_table,
            MergeConfig(seed=42),
        )
        # income_bracket appears once (from table_a only)
        assert (
            result.table.schema.names.count("income_bracket") == 1
        )

    def test_drop_right_columns_works(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        config = MergeConfig(
            seed=42, drop_right_columns=("energy_kwh",)
        )
        result = method.merge(
            region_income_table, energy_vehicle_table, config
        )
        assert "energy_kwh" not in result.table.schema.names
        assert "vehicle_type" in result.table.schema.names

    def test_strata_in_drop_right_columns_no_error(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        """When strata column also in drop_right_columns, no error (dedup)."""
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        config = MergeConfig(
            seed=42, drop_right_columns=("income_bracket",)
        )
        result = method.merge(
            region_income_table, energy_vehicle_table, config
        )
        assert result.table.num_rows == region_income_table.num_rows

    def test_nonexistent_drop_column_raises(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        config = MergeConfig(seed=42, drop_right_columns=("nonexistent",))
        with pytest.raises(MergeValidationError, match="nonexistent"):
            method.merge(
                region_income_table, energy_vehicle_table, config
            )


# ====================================================================
# Empty table validation
# ====================================================================


class TestConditionalSamplingMethodEmptyTable:
    """Empty tables raise MergeValidationError."""

    def test_empty_table_a_raises(
        self,
        empty_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        with pytest.raises(MergeValidationError, match="Empty left table"):
            method.merge(
                empty_table, energy_vehicle_table, MergeConfig(seed=42)
            )

    def test_empty_table_b_raises(
        self,
        region_income_table: pa.Table,
        empty_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        with pytest.raises(
            MergeValidationError, match="Empty right table"
        ):
            method.merge(
                region_income_table, empty_table, MergeConfig(seed=42)
            )


# ====================================================================
# Missing strata column
# ====================================================================


class TestConditionalSamplingMethodMissingStrataColumn:
    """Missing strata columns raise MergeValidationError."""

    def test_missing_in_table_a(
        self,
        vehicle_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        """vehicle_table has no income_bracket column."""
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        with pytest.raises(
            MergeValidationError, match="table_a"
        ):
            method.merge(
                vehicle_table, energy_vehicle_table, MergeConfig(seed=42)
            )

    def test_missing_in_table_b(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
    ) -> None:
        """vehicle_table has no income_bracket column."""
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        with pytest.raises(
            MergeValidationError, match="table_b"
        ):
            method.merge(
                region_income_table, vehicle_table, MergeConfig(seed=42)
            )


# ====================================================================
# Empty stratum
# ====================================================================


class TestConditionalSamplingMethodEmptyStratum:
    """Stratum in table_a without donors in table_b raises error."""

    def test_empty_stratum_raises(self) -> None:
        table_a = pa.table(
            {
                "stratum": pa.array(["a", "b", "c"], type=pa.utf8()),
                "val_a": pa.array([1, 2, 3], type=pa.int64()),
            }
        )
        # table_b has no rows with stratum "c"
        table_b = pa.table(
            {
                "stratum": pa.array(["a", "b", "a"], type=pa.utf8()),
                "val_b": pa.array([10, 20, 30], type=pa.int64()),
            }
        )
        method = ConditionalSamplingMethod(strata_columns=("stratum",))
        with pytest.raises(
            MergeValidationError, match="Strata without donors"
        ):
            method.merge(table_a, table_b, MergeConfig(seed=42))


# ====================================================================
# Assumption record
# ====================================================================


class TestConditionalSamplingMethodAssumption:
    """AC #4: Assumption record states conditioning variable."""

    def test_method_name(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        result = method.merge(
            region_income_table,
            energy_vehicle_table,
            MergeConfig(seed=42),
        )
        assert result.assumption.method_name == "conditional"

    def test_statement_text(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        result = method.merge(
            region_income_table,
            energy_vehicle_table,
            MergeConfig(seed=42),
        )
        assert "conditional independence" in result.assumption.statement
        assert "income_bracket" in result.assumption.statement

    def test_details_content(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        result = method.merge(
            region_income_table,
            energy_vehicle_table,
            MergeConfig(seed=42),
        )
        details = result.assumption.details
        assert details["strata_columns"] == ["income_bracket"]
        assert details["strata_count"] == 3  # low, medium, high
        assert "strata_sizes" in details
        assert details["table_a_rows"] == 10
        assert details["table_b_rows"] == 12
        assert details["seed"] == 42

    def test_governance_entry(
        self,
        region_income_table: pa.Table,
        energy_vehicle_table: pa.Table,
    ) -> None:
        method = ConditionalSamplingMethod(
            strata_columns=("income_bracket",)
        )
        result = method.merge(
            region_income_table,
            energy_vehicle_table,
            MergeConfig(seed=42),
        )
        entry = result.assumption.to_governance_entry()
        assert entry["key"] == "merge_conditional"
        assert entry["source"] == "merge_step"
        assert entry["is_default"] is False
        assert "method" in entry["value"]
        assert "statement" in entry["value"]


# ====================================================================
# Multiple strata columns
# ====================================================================


class TestConditionalSamplingMethodMultipleStrataColumns:
    """Merge with 2 strata columns respects both dimensions."""

    def test_two_strata_columns(self) -> None:
        table_a = pa.table(
            {
                "region": pa.array(
                    ["north", "north", "south", "south"],
                    type=pa.utf8(),
                ),
                "bracket": pa.array(
                    ["low", "high", "low", "high"],
                    type=pa.utf8(),
                ),
                "id": pa.array([1, 2, 3, 4], type=pa.int64()),
            }
        )
        table_b = pa.table(
            {
                "region": pa.array(
                    [
                        "north", "north", "north", "north",
                        "south", "south", "south", "south",
                    ],
                    type=pa.utf8(),
                ),
                "bracket": pa.array(
                    [
                        "low", "low", "high", "high",
                        "low", "low", "high", "high",
                    ],
                    type=pa.utf8(),
                ),
                "energy": pa.array(
                    [100, 110, 200, 210, 120, 130, 220, 230],
                    type=pa.int64(),
                ),
            }
        )
        method = ConditionalSamplingMethod(
            strata_columns=("region", "bracket")
        )
        result = method.merge(table_a, table_b, MergeConfig(seed=42))
        assert result.table.num_rows == 4

        # Verify strata respected for both dimensions
        merged_region = result.table.column("region").to_pylist()
        merged_bracket = result.table.column("bracket").to_pylist()
        merged_energy = result.table.column("energy").to_pylist()

        # Build valid energy values per (region, bracket) stratum
        valid: dict[tuple[str, str], set[int]] = {}
        for i in range(table_b.num_rows):
            key = (
                table_b.column("region")[i].as_py(),
                table_b.column("bracket")[i].as_py(),
            )
            valid.setdefault(key, set()).add(
                table_b.column("energy")[i].as_py()
            )

        for i in range(result.table.num_rows):
            key = (merged_region[i], merged_bracket[i])
            assert merged_energy[i] in valid[key], (
                f"Row {i}: energy={merged_energy[i]} not valid "
                f"for stratum {key}"
            )


# ====================================================================
# Docstring (pedagogical content)
# ====================================================================


class TestConditionalSamplingMethodDocstring:
    """AC #5: Pedagogical docstrings for policy analysts."""

    def test_class_docstring_nonempty(self) -> None:
        assert ConditionalSamplingMethod.__doc__
        assert len(ConditionalSamplingMethod.__doc__.strip()) > 0

    def test_class_docstring_mentions_conditional(self) -> None:
        doc = ConditionalSamplingMethod.__doc__ or ""
        assert (
            "conditional independence" in doc.lower()
            or "strata" in doc.lower()
        )

    def test_module_docstring_pedagogical(self) -> None:
        import reformlab.population.methods.conditional as mod

        doc = mod.__doc__ or ""
        assert "appropriate" in doc.lower()
        assert "problematic" in doc.lower()
