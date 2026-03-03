"""Uniform distribution merge method for statistical dataset fusion.

Implements the simplest statistical matching approach: each row from
table A is independently matched to a uniformly random row from table B
(with replacement). This assumes **no correlation** between the variables
in the two sources.

**Independence assumption (plain language):**

The uniform merge treats every row in table B as equally likely to be
paired with any row in table A. This is equivalent to assuming that
the variables in the two datasets are statistically independent — for
example, that a household's income (from INSEE) has no relationship
with its vehicle type (from SDES).

**When this is appropriate:**

- Merging genuinely independent surveys with no linking variable.
- As a baseline/starting point before applying more sophisticated
  methods (IPF, conditional sampling).
- When the merged variables are known to be weakly correlated.

**When this is problematic:**

- When variables are correlated — e.g., income and vehicle ownership
  are correlated (higher-income households are more likely to own
  newer, more expensive vehicles). Using uniform matching here would
  understate the correlation and distort distributional analyses.
- When the two datasets share a common variable that could be used
  as a stratification key — in that case, conditional sampling or
  statistical matching would be more appropriate.

Implements Story 11.4 (MergeMethod protocol and uniform distribution).
References FR38 (statistical methods library), FR39 (plain-language
explanation of merge assumptions).
"""

from __future__ import annotations

import logging
import random

import pyarrow as pa

from reformlab.population.methods.base import (
    MergeAssumption,
    MergeConfig,
    MergeResult,
)
from reformlab.population.methods.errors import MergeValidationError

_logger = logging.getLogger(__name__)


class UniformMergeMethod:
    """Merge two tables by uniformly random row matching with replacement.

    Each row from table A is independently matched to a uniformly random
    row from table B. This assumes **no correlation** between the
    variables in the two sources — the weakest possible assumption,
    suitable as a baseline but unrealistic when variables are correlated
    (e.g., income and vehicle ownership).

    The merge is deterministic given the same ``MergeConfig.seed``.
    """

    @property
    def name(self) -> str:
        """Short identifier: ``"uniform"``."""
        return "uniform"

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        """Merge two tables using uniform random matching.

        For each of the N rows in *table_a*, independently draw a random
        index from ``[0, M)`` where ``M = table_b.num_rows``, select the
        corresponding row from *table_b* (with replacement), and
        concatenate columns from both tables.

        Column ordering: all columns from *table_a* appear first (in
        their original order), followed by all remaining columns from
        *table_b* (after ``drop_right_columns`` removal).

        Parameters
        ----------
        table_a:
            Left table. All rows are preserved in the output.
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
            or ``drop_right_columns`` references nonexistent columns.
        """
        _logger.info(
            "event=merge_start method=uniform rows_a=%d rows_b=%d seed=%d",
            table_a.num_rows,
            table_b.num_rows,
            config.seed,
        )

        # Validate non-empty inputs
        if table_a.num_rows == 0:
            raise MergeValidationError(
                summary="Empty left table",
                reason="table_a has 0 rows — cannot merge an empty table",
                fix="Provide a table_a with at least one row",
            )
        if table_b.num_rows == 0:
            raise MergeValidationError(
                summary="Empty right table",
                reason="table_b has 0 rows — cannot sample from an empty table",
                fix="Provide a table_b with at least one row",
            )

        # Drop specified right columns
        right_table = table_b
        for col in config.drop_right_columns:
            if col not in right_table.schema.names:
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

        # Random matching with replacement
        rng = random.Random(config.seed)
        n = table_a.num_rows
        m = right_table.num_rows
        indices = pa.array([rng.randrange(m) for _ in range(n)])
        matched_b = right_table.take(indices)

        # Combine columns: table_a first, then matched table_b
        all_columns: dict[str, pa.Array] = {}
        for col_name in table_a.schema.names:
            all_columns[col_name] = table_a.column(col_name)
        for col_name in matched_b.schema.names:
            all_columns[col_name] = matched_b.column(col_name)
        merged = pa.table(all_columns)

        # Build assumption record
        assumption = MergeAssumption(
            method_name="uniform",
            statement=(
                "Each household in source A is matched to a household in "
                "source B with uniform probability \u2014 this assumes no "
                "correlation between the variables in the two sources."
            ),
            details={
                "table_a_rows": n,
                "table_b_rows": m,
                "seed": config.seed,
                "with_replacement": True,
                "dropped_right_columns": list(config.drop_right_columns),
            },
        )

        _logger.info(
            "event=merge_complete method=uniform merged_rows=%d merged_cols=%d",
            merged.num_rows,
            merged.num_columns,
        )

        return MergeResult(table=merged, assumption=assumption)
