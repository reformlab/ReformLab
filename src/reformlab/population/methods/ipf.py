"""Iterative Proportional Fitting (IPF) merge method for dataset fusion.

Implements a record-level IPF (raking) approach: adjusts per-row weights
in table A so that weighted marginal distributions match target values
from census or administrative data, then integerizes the weights and
matches with table B rows.

**What IPF does (plain language):**

IPF adjusts row weights so that the merged population's marginal
distributions match known targets — for example, census totals by
region or income distribution by bracket. It starts with equal weights
and iteratively adjusts them so that each marginal constraint is
satisfied, converging to weights that respect all constraints
simultaneously.

**The assumption:**

The joint distribution between unconstrained variables follows the
pattern in the seed data (table A), adjusted only to match the
specified marginals. This is a "minimum information" / maximum entropy
approach — it changes the data as little as possible while matching
the targets.

**When appropriate:**

- When you have reliable marginal distributions from census or
  administrative data that the merged population must respect.
- When the seed table has good coverage of all category combinations.

**When problematic:**

- When the seed data has structural zeros (categories with no
  observations) that should have non-zero representation.
- When marginal targets are mutually inconsistent (different grand
  totals across dimensions).

Implements Story 11.5 (IPF and conditional sampling merge methods).
References FR38 (statistical methods library), FR39 (plain-language
explanation of merge assumptions).
"""

from __future__ import annotations

import logging
import math
import random

import pyarrow as pa

from reformlab.population.methods.base import (
    IPFConstraint,
    IPFResult,
    MergeAssumption,
    MergeConfig,
    MergeResult,
)
from reformlab.population.methods.errors import (
    MergeConvergenceError,
    MergeValidationError,
)

_logger = logging.getLogger(__name__)


class IPFMergeMethod:
    """Merge two tables using Iterative Proportional Fitting (raking).

    Adjusts per-row weights in table A so that marginal distributions
    match specified target values, then integerizes weights and randomly
    matches with table B rows. This reweighting approach preserves the
    joint distribution structure of the seed data while matching known
    marginals from census or administrative sources.

    The merge is deterministic given the same ``MergeConfig.seed`` and
    constraint configuration.
    """

    def __init__(
        self,
        constraints: tuple[IPFConstraint, ...],
        max_iterations: int = 100,
        tolerance: float = 1e-6,
    ) -> None:
        if not constraints:
            msg = "constraints must be a non-empty tuple"
            raise ValueError(msg)
        if max_iterations < 1:
            msg = f"max_iterations must be >= 1, got {max_iterations}"
            raise ValueError(msg)
        if tolerance <= 0:
            msg = f"tolerance must be > 0, got {tolerance}"
            raise ValueError(msg)
        self._constraints = constraints
        self._max_iterations = max_iterations
        self._tolerance = tolerance

    @property
    def name(self) -> str:
        """Short identifier: ``"ipf"``."""
        return "ipf"

    # ================================================================
    # IPF core algorithm
    # ================================================================

    def _run_ipf(self, table_a: pa.Table) -> IPFResult:
        """Run IPF on table_a to compute per-row weights.

        Algorithm: record-level iterative proportional fitting.
        Adjusts weights so weighted marginal totals match constraint
        targets within tolerance.
        """
        n = table_a.num_rows
        weights = [1.0] * n

        _logger.info(
            "event=ipf_start rows=%d constraints=%d max_iter=%d tol=%s",
            n,
            len(self._constraints),
            self._max_iterations,
            self._tolerance,
        )

        # Validate constraint dimensions exist in table_a
        table_cols = set(table_a.schema.names)
        for constraint in self._constraints:
            if constraint.dimension not in table_cols:
                _logger.warning(
                    "event=merge_error method=ipf error=invalid_constraint_dimension dimension=%s",
                    constraint.dimension,
                )
                raise MergeValidationError(
                    summary="Invalid IPF constraint dimension",
                    reason=(
                        f"Column {constraint.dimension!r} not found in table_a. "
                        f"Available columns: {sorted(table_cols)}"
                    ),
                    fix="Use a column name that exists in table_a",
                )

        # Pre-extract column values for each constraint
        constraint_cols: list[list[object]] = []
        for constraint in self._constraints:
            col_values = table_a.column(constraint.dimension).to_pylist()
            # Validate that at least one target category exists
            col_categories = set(col_values)
            present = set(constraint.targets.keys()) & col_categories
            missing = set(constraint.targets.keys()) - col_categories
            if not present:
                _logger.warning(
                    "event=merge_error method=ipf error=all_categories_missing dimension=%s",
                    constraint.dimension,
                )
                raise MergeValidationError(
                    summary="All IPF target categories missing",
                    reason=(
                        f"None of the target categories {sorted(constraint.targets.keys())} "
                        f"exist in column {constraint.dimension!r}. "
                        f"Column contains: {sorted(str(v) for v in col_categories)}"
                    ),
                    fix="Check that target category values match the column values",
                )
            if missing:
                _logger.warning(
                    "event=ipf_missing_categories dimension=%s missing=%s",
                    constraint.dimension,
                    sorted(missing),
                )
            constraint_cols.append(col_values)

        # IPF iteration loop
        converged = False
        max_deviation = 0.0
        iteration = 0

        for iteration in range(self._max_iterations):
            max_deviation = 0.0

            for c_idx, constraint in enumerate(self._constraints):
                col_values = constraint_cols[c_idx]

                # Compute current weighted totals per category
                current_totals: dict[object, float] = {}
                for k in range(n):
                    cat = col_values[k]
                    current_totals[cat] = current_totals.get(cat, 0.0) + weights[k]

                # Compute and apply adjustment factors
                for cat, target in constraint.targets.items():
                    current = current_totals.get(cat, 0.0)
                    if current > 0:
                        factor = target / current
                        max_deviation = max(max_deviation, abs(current - target))
                    else:
                        factor = 1.0
                        max_deviation = max(max_deviation, target)

                    # Apply factor to all rows in this category
                    for k in range(n):
                        if col_values[k] == cat:
                            weights[k] *= factor

            _logger.debug(
                "event=ipf_iteration iteration=%d max_deviation=%s",
                iteration + 1,
                max_deviation,
            )

            if max_deviation < self._tolerance:
                converged = True
                _logger.info(
                    "event=ipf_converged iterations=%d max_deviation=%s",
                    iteration + 1,
                    max_deviation,
                )
                break

        if not converged:
            _logger.warning(
                "event=ipf_not_converged iterations=%d max_deviation=%s",
                self._max_iterations,
                max_deviation,
            )

        return IPFResult(
            weights=tuple(weights),
            iterations=iteration + 1,
            converged=converged,
            max_deviation=max_deviation,
        )

    # ================================================================
    # Weight integerization
    # ================================================================

    def _integerize_weights(
        self,
        weights: tuple[float, ...],
        target_count: int,
        rng: random.Random,
    ) -> list[int]:
        """Convert float weights to integer counts via probabilistic rounding.

        Normalizes weights to sum to target_count, then rounds each
        weight using deterministic probabilistic rounding: the fractional
        part is the probability of rounding up.
        """
        total = sum(weights)
        if total == 0:
            return [0] * len(weights)
        scale = target_count / total
        int_weights: list[int] = []
        for w in weights:
            scaled = w * scale
            integer_part = math.floor(scaled)
            fractional = scaled - integer_part
            if rng.random() < fractional:
                int_weights.append(integer_part + 1)
            else:
                int_weights.append(integer_part)
        return int_weights

    # ================================================================
    # Merge
    # ================================================================

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        """Merge two tables using IPF reweighting and random matching.

        1. Run IPF on table_a to compute per-row weights matching
           marginal constraints.
        2. Integerize weights to get row repetition counts.
        3. Expand table_a by repeating rows per integer weight.
        4. Randomly match expanded rows with table_b rows.

        Parameters
        ----------
        table_a:
            Left table. Rows are reweighted to match marginal constraints.
        table_b:
            Right table. Rows are sampled with replacement.
        config:
            Merge configuration (seed, drop_right_columns, etc.).

        Returns
        -------
        MergeResult
            Merged table and assumption record.

        Raises
        ------
        MergeValidationError
            If either table is empty, columns overlap after drops,
            ``drop_right_columns`` references nonexistent columns,
            or constraint dimensions are invalid.
        MergeConvergenceError
            If IPF does not converge within max_iterations.
        """
        _logger.info(
            "event=merge_start method=ipf rows_a=%d rows_b=%d seed=%d",
            table_a.num_rows,
            table_b.num_rows,
            config.seed,
        )

        # Validate non-empty inputs
        if table_a.num_rows == 0:
            _logger.warning(
                "event=merge_error method=ipf error=empty_table_a"
            )
            raise MergeValidationError(
                summary="Empty left table",
                reason="table_a has 0 rows — cannot merge an empty table",
                fix="Provide a table_a with at least one row",
            )
        if table_b.num_rows == 0:
            _logger.warning(
                "event=merge_error method=ipf error=empty_table_b"
            )
            raise MergeValidationError(
                summary="Empty right table",
                reason="table_b has 0 rows — cannot sample from an empty table",
                fix="Provide a table_b with at least one row",
            )

        # Drop specified right columns
        right_table = table_b
        for col in config.drop_right_columns:
            if col not in right_table.schema.names:
                _logger.warning(
                    "event=merge_error method=ipf error=invalid_drop_column column=%s",
                    col,
                )
                raise MergeValidationError(
                    summary="Invalid drop_right_columns",
                    reason=(
                        f"Column {col!r} not found in table_b. "
                        f"Available columns: {right_table.schema.names}"
                    ),
                    fix="Check drop_right_columns against table_b schema",
                )
            col_idx = right_table.schema.get_field_index(col)
            right_table = right_table.remove_column(col_idx)

        # Check column name conflicts
        overlap = set(table_a.schema.names) & set(right_table.schema.names)
        if overlap:
            _logger.warning(
                "event=merge_error method=ipf error=column_conflict columns=%s",
                sorted(overlap),
            )
            raise MergeValidationError(
                summary="Column name conflict",
                reason=(
                    f"Columns {sorted(overlap)} exist in both tables "
                    f"after drop_right_columns removal"
                ),
                fix=(
                    "Add conflicting column names to "
                    "config.drop_right_columns or rename them before merging"
                ),
            )

        # Run IPF
        ipf_result = self._run_ipf(table_a)

        # Check convergence
        if not ipf_result.converged:
            raise MergeConvergenceError(
                summary="IPF did not converge",
                reason=(
                    f"After {ipf_result.iterations} iterations, "
                    f"max deviation is {ipf_result.max_deviation:.6g} "
                    f"(tolerance: {self._tolerance})"
                ),
                fix=(
                    "Increase max_iterations, relax tolerance, or check "
                    "that marginal constraints are mutually consistent "
                    "(e.g., grand totals across dimensions should match)"
                ),
            )

        # Integerize weights
        int_weights = self._integerize_weights(
            ipf_result.weights, table_a.num_rows, random.Random(config.seed)
        )

        # Expand table_a by repeating rows per integer weight
        expanded_indices = [
            k for k, w in enumerate(int_weights) for _ in range(w)
        ]

        if len(expanded_indices) == 0:
            _logger.warning(
                "event=merge_error method=ipf error=empty_expansion"
            )
            raise MergeValidationError(
                summary="IPF produced empty expansion",
                reason=(
                    "All row weights integerized to 0 — "
                    "no rows survive expansion"
                ),
                fix=(
                    "Check constraint targets for extreme values "
                    "or structural zeros"
                ),
            )

        expanded_a = table_a.take(pa.array(expanded_indices))

        # Random matching with replacement (different seed stream)
        rng_match = random.Random(config.seed + 1)
        m = right_table.num_rows
        b_indices = pa.array(
            [rng_match.randrange(m) for _ in range(expanded_a.num_rows)]
        )
        matched_b = right_table.take(b_indices)

        # Combine columns: expanded table_a first, then matched table_b
        all_columns: dict[str, pa.ChunkedArray] = {}
        for col_name in expanded_a.schema.names:
            if col_name in all_columns:
                raise MergeValidationError(
                    summary="Duplicate column in left table",
                    reason=f"column {col_name!r} appears multiple times in table_a",
                    fix="Ensure column names are unique before merging",
                )
            all_columns[col_name] = expanded_a.column(col_name)
        for col_name in matched_b.schema.names:
            if col_name in all_columns:
                raise MergeValidationError(
                    summary="Duplicate column after merge",
                    reason=f"column {col_name!r} exists in both tables after assembly",
                    fix="Rename or drop duplicate columns before merging",
                )
            all_columns[col_name] = matched_b.column(col_name)
        merged = pa.table(all_columns)

        # Build assumption record
        assumption = MergeAssumption(
            method_name="ipf",
            statement=(
                "The merged population is reweighted using Iterative "
                "Proportional Fitting so that marginal distributions "
                "match the specified targets \u2014 this assumes the joint "
                "distribution between unconstrained variables follows "
                "the seed pattern, adjusted only to match target marginals."
            ),
            details={
                "table_a_rows": table_a.num_rows,
                "table_b_rows": table_b.num_rows,
                "expanded_rows": expanded_a.num_rows,
                "seed": config.seed,
                "constraints": [
                    {
                        "dimension": c.dimension,
                        "targets": dict(c.targets),
                    }
                    for c in self._constraints
                ],
                "iterations": ipf_result.iterations,
                "converged": ipf_result.converged,
                "max_deviation": ipf_result.max_deviation,
                "tolerance": self._tolerance,
                "dropped_right_columns": list(config.drop_right_columns),
            },
        )

        _logger.info(
            "event=merge_complete method=ipf merged_rows=%d merged_cols=%d "
            "ipf_iterations=%d",
            merged.num_rows,
            merged.num_columns,
            ipf_result.iterations,
        )

        return MergeResult(table=merged, assumption=assumption)
