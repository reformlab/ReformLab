"""Tests for IPFMergeMethod.

Story 11.5 — AC #1: IPF matches marginal constraints within tolerance.
AC #2: Assumption record lists constraints and convergence status.
AC #5: Pedagogical docstrings for policy analysts.
"""

from __future__ import annotations

import logging

import pyarrow as pa
import pytest

from reformlab.population.methods.base import (
    IPFConstraint,
    MergeConfig,
    MergeMethod,
)
from reformlab.population.methods.errors import (
    MergeConvergenceError,
    MergeValidationError,
)
from reformlab.population.methods.ipf import IPFMergeMethod

# ====================================================================
# Protocol compliance
# ====================================================================


class TestIPFMergeMethodProtocol:
    """AC #1: IPFMergeMethod satisfies MergeMethod protocol."""

    def test_isinstance_check(
        self, simple_constraints: tuple[IPFConstraint, ...]
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        assert isinstance(method, MergeMethod)


# ====================================================================
# Name property
# ====================================================================


class TestIPFMergeMethodName:
    """Name property returns 'ipf'."""

    def test_name(
        self, simple_constraints: tuple[IPFConstraint, ...]
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        assert method.name == "ipf"


# ====================================================================
# Constructor validation
# ====================================================================


class TestIPFMergeMethodConstructorValidation:
    """Constructor validates constraints, max_iterations, tolerance."""

    def test_empty_constraints_raises(self) -> None:
        with pytest.raises(ValueError, match="non-empty tuple"):
            IPFMergeMethod(constraints=())

    def test_max_iterations_zero_raises(
        self, simple_constraints: tuple[IPFConstraint, ...]
    ) -> None:
        with pytest.raises(ValueError, match="max_iterations"):
            IPFMergeMethod(
                constraints=simple_constraints, max_iterations=0
            )

    def test_max_iterations_negative_raises(
        self, simple_constraints: tuple[IPFConstraint, ...]
    ) -> None:
        with pytest.raises(ValueError, match="max_iterations"):
            IPFMergeMethod(
                constraints=simple_constraints, max_iterations=-1
            )

    def test_tolerance_zero_raises(
        self, simple_constraints: tuple[IPFConstraint, ...]
    ) -> None:
        with pytest.raises(ValueError, match="tolerance"):
            IPFMergeMethod(
                constraints=simple_constraints, tolerance=0
            )

    def test_tolerance_negative_raises(
        self, simple_constraints: tuple[IPFConstraint, ...]
    ) -> None:
        with pytest.raises(ValueError, match="tolerance"):
            IPFMergeMethod(
                constraints=simple_constraints, tolerance=-0.1
            )


# ====================================================================
# Basic merge behavior
# ====================================================================


class TestIPFMergeMethodMerge:
    """AC #1: Basic IPF merge functionality."""

    def test_merged_table_has_correct_columns(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        result = method.merge(
            region_income_table, vehicle_table, MergeConfig(seed=42)
        )
        expected_names = (
            region_income_table.schema.names + vehicle_table.schema.names
        )
        assert result.table.schema.names == expected_names

    def test_table_b_values_from_actual_rows(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        """Verify row-level coherence: matched rows must exist in table_b."""
        method = IPFMergeMethod(constraints=simple_constraints)
        result = method.merge(
            region_income_table, vehicle_table, MergeConfig(seed=42)
        )
        right_col_names = vehicle_table.schema.names
        valid_row_combos = set(
            zip(
                *(vehicle_table.column(c).to_pylist() for c in right_col_names)
            )
        )
        for i in range(result.table.num_rows):
            combo = tuple(
                result.table.column(c)[i].as_py() for c in right_col_names
            )
            assert combo in valid_row_combos


# ====================================================================
# Marginal matching
# ====================================================================


class TestIPFMergeMethodMarginalMatch:
    """AC #1: Merged table marginals match targets within ±1."""

    def test_single_constraint_marginal_match(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        result = method.merge(
            region_income_table, vehicle_table, MergeConfig(seed=42)
        )
        counts: dict[str, int] = {}
        for val in result.table.column("income_bracket").to_pylist():
            counts[val] = counts.get(val, 0) + 1
        # Target: low=4, medium=3, high=3
        assert abs(counts.get("low", 0) - 4) <= 1
        assert abs(counts.get("medium", 0) - 3) <= 1
        assert abs(counts.get("high", 0) - 3) <= 1

    def test_multi_constraint_marginal_match(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        multi_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=multi_constraints)
        result = method.merge(
            region_income_table, vehicle_table, MergeConfig(seed=42)
        )
        # Check income_bracket: target low=4, medium=3, high=3
        income_counts: dict[str, int] = {}
        for val in result.table.column("income_bracket").to_pylist():
            income_counts[val] = income_counts.get(val, 0) + 1
        assert abs(income_counts.get("low", 0) - 4) <= 1
        assert abs(income_counts.get("medium", 0) - 3) <= 1
        assert abs(income_counts.get("high", 0) - 3) <= 1

        # Check region_code: target 84=3, 11=4, 75=3
        region_counts: dict[str, int] = {}
        for val in result.table.column("region_code").to_pylist():
            region_counts[val] = region_counts.get(val, 0) + 1
        assert abs(region_counts.get("84", 0) - 3) <= 1
        assert abs(region_counts.get("11", 0) - 4) <= 1
        assert abs(region_counts.get("75", 0) - 3) <= 1


# ====================================================================
# Convergence
# ====================================================================


class TestIPFMergeMethodConvergence:
    """AC #1, #2: Convergence status in assumption record."""

    def test_convergent_case(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        result = method.merge(
            region_income_table, vehicle_table, MergeConfig(seed=42)
        )
        assert result.assumption.details["converged"] is True
        assert result.assumption.details["iterations"] < 100

    def test_non_convergent_case_raises(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        inconsistent_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(
            constraints=inconsistent_constraints,
            max_iterations=100,
            tolerance=1e-6,
        )
        with pytest.raises(
            MergeConvergenceError, match="IPF did not converge"
        ):
            method.merge(
                region_income_table, vehicle_table, MergeConfig(seed=42)
            )


# ====================================================================
# Determinism
# ====================================================================


class TestIPFMergeMethodDeterminism:
    """AC #1: Same seed → identical result; different seed → different."""

    def test_same_seed_same_result(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        config = MergeConfig(seed=12345)
        result_1 = method.merge(region_income_table, vehicle_table, config)
        result_2 = method.merge(region_income_table, vehicle_table, config)
        assert result_1.table.equals(result_2.table)

    def test_different_seed_different_result(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        result_1 = method.merge(
            region_income_table, vehicle_table, MergeConfig(seed=1)
        )
        result_2 = method.merge(
            region_income_table, vehicle_table, MergeConfig(seed=2)
        )
        # Right-table columns should differ between different seeds
        right_cols = vehicle_table.schema.names
        matched_1 = {
            c: result_1.table.column(c).to_pylist() for c in right_cols
        }
        matched_2 = {
            c: result_2.table.column(c).to_pylist() for c in right_cols
        }
        assert matched_1 != matched_2


# ====================================================================
# Assumption record
# ====================================================================


class TestIPFMergeMethodAssumption:
    """AC #2: Assumption record lists constraints and convergence status."""

    def test_method_name(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        result = method.merge(
            region_income_table, vehicle_table, MergeConfig(seed=42)
        )
        assert result.assumption.method_name == "ipf"

    def test_statement_text(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        result = method.merge(
            region_income_table, vehicle_table, MergeConfig(seed=42)
        )
        assert "Iterative Proportional Fitting" in result.assumption.statement
        assert "marginal" in result.assumption.statement

    def test_details_content(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        result = method.merge(
            region_income_table, vehicle_table, MergeConfig(seed=42)
        )
        details = result.assumption.details
        assert "constraints" in details
        assert "iterations" in details
        assert "converged" in details
        assert "max_deviation" in details
        assert "tolerance" in details
        assert "expanded_rows" in details
        assert details["table_a_rows"] == 10
        assert details["table_b_rows"] == 8
        assert details["seed"] == 42

    def test_governance_entry(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        result = method.merge(
            region_income_table, vehicle_table, MergeConfig(seed=42)
        )
        entry = result.assumption.to_governance_entry()
        assert entry["key"] == "merge_ipf"
        assert entry["source"] == "merge_step"
        assert entry["is_default"] is False
        assert "method" in entry["value"]
        assert "statement" in entry["value"]


# ====================================================================
# Empty table validation
# ====================================================================


class TestIPFMergeMethodEmptyTable:
    """Empty tables raise MergeValidationError."""

    def test_empty_table_a_raises(
        self,
        empty_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        with pytest.raises(MergeValidationError, match="Empty left table"):
            method.merge(empty_table, vehicle_table, MergeConfig(seed=42))

    def test_empty_table_b_raises(
        self,
        region_income_table: pa.Table,
        empty_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        with pytest.raises(MergeValidationError, match="Empty right table"):
            method.merge(
                region_income_table, empty_table, MergeConfig(seed=42)
            )


# ====================================================================
# Column conflict detection
# ====================================================================


class TestIPFMergeMethodColumnConflict:
    """Overlapping column names raise MergeValidationError."""

    def test_overlapping_columns_raises(
        self,
        region_income_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        # Create a table with overlapping column name
        table_b = pa.table(
            {
                "income_bracket": pa.array(
                    ["low", "high"], type=pa.utf8()
                ),
                "extra_col": pa.array([1, 2], type=pa.int64()),
            }
        )
        method = IPFMergeMethod(constraints=simple_constraints)
        with pytest.raises(
            MergeValidationError, match="Column name conflict"
        ):
            method.merge(
                region_income_table, table_b, MergeConfig(seed=42)
            )


# ====================================================================
# drop_right_columns
# ====================================================================


class TestIPFMergeMethodDropRightColumns:
    """drop_right_columns removes columns from right table."""

    def test_drop_resolves_conflict(
        self,
        region_income_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        table_b = pa.table(
            {
                "income_bracket": pa.array(
                    ["low", "high", "medium"], type=pa.utf8()
                ),
                "extra_col": pa.array([1, 2, 3], type=pa.int64()),
            }
        )
        method = IPFMergeMethod(constraints=simple_constraints)
        config = MergeConfig(
            seed=42, drop_right_columns=("income_bracket",)
        )
        result = method.merge(region_income_table, table_b, config)
        assert "extra_col" in result.table.schema.names
        assert result.table.schema.names.count("income_bracket") == 1

    def test_nonexistent_drop_column_raises(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        simple_constraints: tuple[IPFConstraint, ...],
    ) -> None:
        method = IPFMergeMethod(constraints=simple_constraints)
        config = MergeConfig(seed=42, drop_right_columns=("nonexistent",))
        with pytest.raises(MergeValidationError, match="nonexistent"):
            method.merge(region_income_table, vehicle_table, config)


# ====================================================================
# Invalid constraint dimension
# ====================================================================


class TestIPFMergeMethodInvalidConstraintDimension:
    """Constraint dimension not in table_a raises MergeValidationError."""

    def test_invalid_dimension_raises(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
    ) -> None:
        constraints = (
            IPFConstraint(
                dimension="nonexistent_col",
                targets={"a": 5.0, "b": 5.0},
            ),
        )
        method = IPFMergeMethod(constraints=constraints)
        with pytest.raises(
            MergeValidationError, match="nonexistent_col"
        ):
            method.merge(
                region_income_table, vehicle_table, MergeConfig(seed=42)
            )


# ====================================================================
# Missing category warning
# ====================================================================


class TestIPFMergeMethodMissingCategory:
    """Constraint with missing target category logs warning but succeeds."""

    def test_missing_category_logs_warning(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        # Target has "extra" category not in table data
        constraints = (
            IPFConstraint(
                dimension="income_bracket",
                targets={
                    "low": 4.0,
                    "medium": 3.0,
                    "high": 3.0,
                    "extra": 0.0,
                },
            ),
        )
        method = IPFMergeMethod(constraints=constraints)
        with caplog.at_level(logging.WARNING):
            result = method.merge(
                region_income_table, vehicle_table, MergeConfig(seed=42)
            )
        assert result.table.num_rows > 0
        assert "ipf_missing_categories" in caplog.text

    def test_missing_category_with_nonzero_target_raises_convergence_error(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
    ) -> None:
        """Non-zero target for absent category prevents convergence."""
        constraints = (
            IPFConstraint(
                dimension="income_bracket",
                targets={
                    "low": 4.0,
                    "medium": 3.0,
                    "high": 3.0,
                    "extra": 2.0,
                },
            ),
        )
        method = IPFMergeMethod(
            constraints=constraints, max_iterations=50, tolerance=1e-6
        )
        with pytest.raises(
            MergeConvergenceError, match="IPF did not converge"
        ):
            method.merge(
                region_income_table, vehicle_table, MergeConfig(seed=42)
            )

    def test_all_categories_missing_raises(
        self,
        region_income_table: pa.Table,
        vehicle_table: pa.Table,
    ) -> None:
        constraints = (
            IPFConstraint(
                dimension="income_bracket",
                targets={"nonexistent_a": 5.0, "nonexistent_b": 5.0},
            ),
        )
        method = IPFMergeMethod(constraints=constraints)
        with pytest.raises(
            MergeValidationError, match="All IPF target categories missing"
        ):
            method.merge(
                region_income_table, vehicle_table, MergeConfig(seed=42)
            )

    def test_type_mismatch_error_mentions_cast(self) -> None:
        """Constraint on non-string column gives helpful error about type."""
        table_a = pa.table({
            "id": pa.array([1, 2, 3], type=pa.int64()),
            "val": pa.array([10.0, 20.0, 30.0], type=pa.float64()),
        })
        table_b = pa.table({
            "other": pa.array([1.0, 2.0], type=pa.float64()),
        })
        constraints = (
            IPFConstraint(dimension="id", targets={"1": 2.0, "2": 1.0}),
        )
        method = IPFMergeMethod(constraints=constraints)
        with pytest.raises(MergeValidationError, match="utf8"):
            method.merge(table_a, table_b, MergeConfig(seed=42))


# ====================================================================
# Docstring (pedagogical content)
# ====================================================================


class TestIPFMergeMethodDocstring:
    """AC #5: Pedagogical docstrings for policy analysts."""

    def test_class_docstring_nonempty(self) -> None:
        assert IPFMergeMethod.__doc__
        assert len(IPFMergeMethod.__doc__.strip()) > 0

    def test_class_docstring_mentions_marginal_or_reweight(self) -> None:
        doc = IPFMergeMethod.__doc__ or ""
        assert (
            "marginal" in doc.lower() or "reweight" in doc.lower()
        )

    def test_module_docstring_pedagogical(self) -> None:
        import reformlab.population.methods.ipf as mod

        doc = mod.__doc__ or ""
        assert "appropriate" in doc.lower()
        assert "problematic" in doc.lower()
