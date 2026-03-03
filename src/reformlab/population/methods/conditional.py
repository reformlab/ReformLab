"""Conditional sampling merge method for statistical dataset fusion.

Implements stratum-based matching: groups both tables by shared
stratification variable(s), then randomly matches rows only within
the same group. This preserves the correlation between the
stratification variable and all other variables in each source.

**What conditional sampling does (plain language):**

Instead of matching rows randomly from the entire table, conditional
sampling first groups both datasets by a shared variable (e.g., income
bracket). Then, within each group, it randomly matches rows. A "low
income" household will only be matched with vehicle/energy records
from other "low income" households, preserving the relationship between
income and the other variables.

**The assumption (conditional independence):**

Within each stratum, the unique variables from table A and table B are
assumed independent. The correlation between them is captured entirely
by the stratification variable. For example, if stratifying by income
bracket, the method assumes that within the "low income" group, a
household's region has no additional relationship with its vehicle
type beyond what income already captures.

**When appropriate:**

- When both datasets share a variable that is correlated with the
  unique variables in each dataset (e.g., income bracket correlates
  with both energy consumption and vehicle ownership).
- When you want to preserve known correlations without the complexity
  of full statistical matching.

**When problematic:**

- When the strata are too coarse (residual correlation within strata
  is large) — e.g., using only 3 income brackets when within-bracket
  variation is substantial.
- When some strata have very few observations in one table (small
  sample noise dominates the matches within that stratum).

Implements Story 11.5 (IPF and conditional sampling merge methods).
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


class ConditionalSamplingMethod:
    """Merge two tables by random matching within shared strata.

    Groups both tables by one or more shared stratification columns,
    then matches rows randomly within each group. This preserves the
    correlation between the stratification variable(s) and all other
    variables — a conditional independence assumption that is stronger
    than uniform matching but weaker than full statistical matching.

    The merge is deterministic given the same ``MergeConfig.seed``.
    """

    def __init__(
        self,
        strata_columns: tuple[str, ...],
    ) -> None:
        if not strata_columns:
            msg = "strata_columns must be a non-empty tuple"
            raise ValueError(msg)
        for col in strata_columns:
            if not col:
                msg = "strata_columns must not contain empty strings"
                raise ValueError(msg)
        self._strata_columns = strata_columns

    @property
    def name(self) -> str:
        """Short identifier: ``"conditional"``."""
        return "conditional"

    def merge(
        self,
        table_a: pa.Table,
        table_b: pa.Table,
        config: MergeConfig,
    ) -> MergeResult:
        """Merge two tables using conditional sampling within strata.

        For each row in table A, finds the stratum (defined by the
        stratification column values), then randomly selects a donor
        row from table B within the same stratum.

        Parameters
        ----------
        table_a:
            Left table. All rows are preserved in the output.
        table_b:
            Right table. Rows are sampled within strata.
        config:
            Merge configuration (seed, drop_right_columns, etc.).

        Returns
        -------
        MergeResult
            Merged table and assumption record.

        Raises
        ------
        MergeValidationError
            If either table is empty, strata columns are missing,
            columns overlap after drops, a stratum in table A has
            no donors in table B, or drop_right_columns references
            nonexistent columns.
        """
        _logger.info(
            "event=merge_start method=conditional rows_a=%d rows_b=%d seed=%d strata=%s",
            table_a.num_rows,
            table_b.num_rows,
            config.seed,
            self._strata_columns,
        )

        # Validate non-empty inputs
        if table_a.num_rows == 0:
            _logger.warning(
                "event=merge_error method=conditional error=empty_table_a"
            )
            raise MergeValidationError(
                summary="Empty left table",
                reason="table_a has 0 rows — cannot merge an empty table",
                fix="Provide a table_a with at least one row",
            )
        if table_b.num_rows == 0:
            _logger.warning(
                "event=merge_error method=conditional error=empty_table_b"
            )
            raise MergeValidationError(
                summary="Empty right table",
                reason="table_b has 0 rows — cannot sample from an empty table",
                fix="Provide a table_b with at least one row",
            )

        # Validate strata columns exist in BOTH tables
        a_cols = set(table_a.schema.names)
        b_cols = set(table_b.schema.names)
        for col in self._strata_columns:
            if col not in a_cols:
                _logger.warning(
                    "event=merge_error method=conditional error=missing_strata_column table=a column=%s",
                    col,
                )
                raise MergeValidationError(
                    summary="Missing strata column in table_a",
                    reason=(
                        f"Strata column {col!r} not found in table_a. "
                        f"Available columns: {sorted(a_cols)}"
                    ),
                    fix="Use a column that exists in both tables as strata",
                )
            if col not in b_cols:
                _logger.warning(
                    "event=merge_error method=conditional error=missing_strata_column table=b column=%s",
                    col,
                )
                raise MergeValidationError(
                    summary="Missing strata column in table_b",
                    reason=(
                        f"Strata column {col!r} not found in table_b. "
                        f"Available columns: {sorted(b_cols)}"
                    ),
                    fix="Use a column that exists in both tables as strata",
                )

        # Compute effective drop list: strata columns + config.drop_right_columns
        # Deduplicate while preserving order
        effective_drop = tuple(
            dict.fromkeys(list(self._strata_columns) + list(config.drop_right_columns))
        )

        # Drop effective_drop columns from table_b
        right_table = table_b
        for col in effective_drop:
            if col not in right_table.schema.names:
                # Strata columns are guaranteed present (validated above),
                # so this can only trigger for drop_right_columns entries
                _logger.warning(
                    "event=merge_error method=conditional error=invalid_drop_column column=%s",
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

        # Check column name conflicts on remaining columns
        overlap = set(table_a.schema.names) & set(right_table.schema.names)
        if overlap:
            _logger.warning(
                "event=merge_error method=conditional error=column_conflict columns=%s",
                sorted(overlap),
            )
            raise MergeValidationError(
                summary="Column name conflict",
                reason=(
                    f"Columns {sorted(overlap)} exist in both tables "
                    f"after strata and drop_right_columns removal"
                ),
                fix=(
                    "Add conflicting column names to "
                    "config.drop_right_columns or rename them before merging"
                ),
            )

        # Build stratum keys for each row
        n = table_a.num_rows
        m = table_b.num_rows

        strata_a: dict[tuple[object, ...], list[int]] = {}
        strata_b: dict[tuple[object, ...], list[int]] = {}

        # Pre-extract strata column values
        a_strata_cols = [
            table_a.column(c).to_pylist() for c in self._strata_columns
        ]
        b_strata_cols = [
            table_b.column(c).to_pylist() for c in self._strata_columns
        ]

        for k in range(n):
            key = tuple(col[k] for col in a_strata_cols)
            strata_a.setdefault(key, []).append(k)

        for k in range(m):
            key = tuple(col[k] for col in b_strata_cols)
            strata_b.setdefault(key, []).append(k)

        _logger.info(
            "event=strata_built strata_count=%d",
            len(strata_a),
        )

        # Validate coverage: every table_a stratum must have donors in table_b
        empty_strata = [
            key for key in strata_a if key not in strata_b
        ]
        if empty_strata:
            formatted = [
                "|".join(str(x) for x in key) for key in empty_strata
            ]
            _logger.warning(
                "event=merge_error method=conditional error=empty_strata strata=%s",
                formatted,
            )
            raise MergeValidationError(
                summary="Strata without donors in table_b",
                reason=(
                    f"The following strata in table_a have no matching "
                    f"rows in table_b: {formatted}"
                ),
                fix=(
                    "Ensure table_b has at least one row for every "
                    "stratum present in table_a, or use coarser "
                    "stratification variables"
                ),
            )

        # Random matching within strata
        rng = random.Random(config.seed)
        # Build key for each row of table_a in order
        a_keys = [
            tuple(col[k] for col in a_strata_cols) for k in range(n)
        ]
        matched_b_indices = [
            rng.choice(strata_b[key]) for key in a_keys
        ]

        # Build matched right table
        matched_right = right_table.take(pa.array(matched_b_indices))

        # Combine columns: table_a first, then matched right
        all_columns: dict[str, pa.ChunkedArray] = {}
        for col_name in table_a.schema.names:
            if col_name in all_columns:
                raise MergeValidationError(
                    summary="Duplicate column in left table",
                    reason=f"column {col_name!r} appears multiple times in table_a",
                    fix="Ensure column names are unique before merging",
                )
            all_columns[col_name] = table_a.column(col_name)
        for col_name in matched_right.schema.names:
            if col_name in all_columns:
                raise MergeValidationError(
                    summary="Duplicate column after merge",
                    reason=f"column {col_name!r} exists in both tables after assembly",
                    fix="Rename or drop duplicate columns before merging",
                )
            all_columns[col_name] = matched_right.column(col_name)
        merged = pa.table(all_columns)

        # Build strata sizes for assumption details
        strata_sizes = {
            "|".join(str(x) for x in key): {
                "table_a": len(strata_a[key]),
                "table_b": len(strata_b.get(key, [])),
            }
            for key in strata_a
        }

        strata_column_list = ", ".join(self._strata_columns)
        assumption = MergeAssumption(
            method_name="conditional",
            statement=(
                f"Rows are matched within strata defined by "
                f"[{strata_column_list}] \u2014 this assumes that, "
                f"within each stratum, the unique variables from each "
                f"source are independent (conditional independence "
                f"given the stratification variables)."
            ),
            details={
                "table_a_rows": n,
                "table_b_rows": m,
                "seed": config.seed,
                "strata_columns": list(self._strata_columns),
                "strata_count": len(strata_a),
                "strata_sizes": strata_sizes,
                "dropped_right_columns": list(effective_drop),
            },
        )

        _logger.info(
            "event=merge_complete method=conditional merged_rows=%d merged_cols=%d strata_count=%d",
            merged.num_rows,
            merged.num_columns,
            len(strata_a),
        )

        return MergeResult(table=merged, assumption=assumption)
