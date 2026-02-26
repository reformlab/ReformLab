"""Data-quality checks for adapter output validation.

Validates ``ComputationResult.output_fields`` against a ``DataSchema`` for
null values in required fields, type mismatches, missing required columns,
and optional value-range warnings.

This module provides utilities only — it does **not** wire checks into the
orchestrator runtime.  Integration call-sites are deferred to later stories.
"""

from __future__ import annotations

from dataclasses import dataclass

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.computation.ingestion import DataSchema
from reformlab.computation.types import ComputationResult

_MAX_ROW_INDICES = 10


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QualityIssue:
    """A single quality finding — either a blocking error or a warning."""

    field: str
    issue_type: str
    message: str
    row_indices: tuple[int, ...] = ()
    expected: str = ""
    actual: str = ""


@dataclass(frozen=True)
class QualityCheckResult:
    """Aggregate outcome of all quality checks on a single result."""

    passed: bool
    errors: tuple[QualityIssue, ...]
    warnings: tuple[QualityIssue, ...]
    checked_columns: tuple[str, ...]
    row_count: int


@dataclass(frozen=True)
class RangeRule:
    """Defines acceptable value bounds for a numeric field."""

    field: str
    min_value: float | int | None
    max_value: float | int | None
    description: str = ""


class DataQualityError(Exception):
    """Raised when blocking quality issues are found in adapter output."""

    def __init__(self, result: QualityCheckResult) -> None:
        self.result = result
        lines = [
            "Data quality validation failed - "
            f"{len(result.errors)} blocking issue(s) found - "
            "Fix the reported fields and rerun"
        ]
        for issue in result.errors:
            lines.append(f"  {issue.field}: {issue.message}")
        super().__init__("\n".join(lines))


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def _check_missing_required_columns(
    table: pa.Table,
    schema: DataSchema,
) -> list[QualityIssue]:
    """Return a blocking ``QualityIssue`` for each required column absent
    from *table*.
    """
    available = set(table.column_names)
    issues: list[QualityIssue] = []
    for col in schema.required_columns:
        if col not in available:
            issues.append(
                QualityIssue(
                    field=col,
                    issue_type="missing_column",
                    message=(
                        f"Required column missing - "
                        f"'{col}' not found in output - "
                        f"Ensure the computation produces this column"
                    ),
                )
            )
    return issues


def _check_nulls(
    table: pa.Table,
    required_columns: tuple[str, ...],
) -> list[QualityIssue]:
    """Return a blocking ``QualityIssue`` for each required column containing
    null values.  Row indices are capped at ``_MAX_ROW_INDICES``.
    """
    available = set(table.column_names)
    issues: list[QualityIssue] = []
    for col in required_columns:
        if col not in available:
            continue
        column = table.column(col)
        if table.num_rows == 0:
            continue
        null_count = column.null_count
        if null_count == 0:
            continue
        null_mask = pc.is_null(column)
        null_indices_array = pc.indices_nonzero(null_mask)
        if len(null_indices_array) == 0:
            continue
        total = len(null_indices_array)
        sampled = tuple(
            int(null_indices_array[i].as_py())
            for i in range(min(total, _MAX_ROW_INDICES))
        )
        msg = (
            f"Null values in required field - "
            f"'{col}' has {total} null(s) at rows {list(sampled)}"
        )
        if total > _MAX_ROW_INDICES:
            msg += f" (showing first {_MAX_ROW_INDICES} of {total})"
        msg += " - Remove or fill null values in this column"
        issues.append(
            QualityIssue(
                field=col,
                issue_type="null_values",
                message=msg,
                row_indices=sampled,
            )
        )
    return issues


def _check_types(
    table: pa.Table,
    schema: DataSchema,
    columns: tuple[str, ...],
) -> list[QualityIssue]:
    """Return a blocking ``QualityIssue`` for each column whose actual type
    does not match the expected type declared in *schema*.
    """
    available = set(table.column_names)
    issues: list[QualityIssue] = []
    for col in columns:
        if col not in available:
            continue
        expected_type = schema.field(col).type
        actual_type = table.schema.field(col).type
        if not actual_type.equals(expected_type):
            issues.append(
                QualityIssue(
                    field=col,
                    issue_type="type_mismatch",
                    message=(
                        f"Type mismatch - "
                        f"'{col}' expected {expected_type}, got {actual_type} - "
                        f"Ensure the column type matches the declared schema"
                    ),
                    expected=str(expected_type),
                    actual=str(actual_type),
                )
            )
    return issues


def _supports_numeric_range_checks(data_type: pa.DataType) -> bool:
    """Return True when range comparisons are valid for *data_type*."""
    return (
        pa.types.is_integer(data_type)
        or pa.types.is_floating(data_type)
        or pa.types.is_decimal(data_type)
    )


def _check_ranges(
    table: pa.Table,
    range_rules: tuple[RangeRule, ...],
) -> list[QualityIssue]:
    """Return non-blocking ``QualityIssue`` warnings for values outside
    declared bounds.  Nulls are safely ignored.
    """
    available = set(table.column_names)
    warnings: list[QualityIssue] = []
    for rule in range_rules:
        if rule.field not in available:
            warnings.append(
                QualityIssue(
                    field=rule.field,
                    issue_type="range_rule_invalid",
                    message=(
                        "Range rule skipped - "
                        f"'{rule.field}' not found in output columns - "
                        "Define range rules for columns present in adapter output"
                    ),
                    actual=rule.field,
                )
            )
            continue
        if rule.min_value is None and rule.max_value is None:
            warnings.append(
                QualityIssue(
                    field=rule.field,
                    issue_type="range_rule_invalid",
                    message=(
                        "Range rule skipped - "
                        f"'{rule.field}' has no bounds configured - "
                        "Set min_value and/or max_value for this rule"
                    ),
                    expected="at least one of min_value/max_value",
                    actual="min_value=None,max_value=None",
                )
            )
            continue
        if (
            rule.min_value is not None
            and rule.max_value is not None
            and rule.min_value > rule.max_value
        ):
            warnings.append(
                QualityIssue(
                    field=rule.field,
                    issue_type="range_rule_invalid",
                    message=(
                        "Range rule skipped - "
                        f"'{rule.field}' has invalid bounds (min > max) - "
                        "Use bounds where min_value <= max_value"
                    ),
                    expected=f"min <= max ({rule.min_value} <= {rule.max_value})",
                    actual=f"min > max ({rule.min_value} > {rule.max_value})",
                )
            )
            continue
        if table.num_rows == 0:
            continue
        column = table.column(rule.field)
        col_type = column.type

        if not _supports_numeric_range_checks(col_type):
            warnings.append(
                QualityIssue(
                    field=rule.field,
                    issue_type="range_rule_invalid",
                    message=(
                        "Range rule skipped - "
                        f"'{rule.field}' has non-numeric type {col_type} - "
                        "Apply range rules only to integer/float/decimal columns"
                    ),
                    actual=str(col_type),
                )
            )
            continue

        # Build a mask of violating rows (nulls are excluded by pyarrow).
        violation_mask: pa.ChunkedArray | None = None

        try:
            if rule.min_value is not None:
                below = pc.less(column, pa.scalar(rule.min_value, col_type))
                violation_mask = below

            if rule.max_value is not None:
                above = pc.greater(column, pa.scalar(rule.max_value, col_type))
                violation_mask = (
                    pc.or_(violation_mask, above)
                    if violation_mask is not None
                    else above
                )
        except (pa.ArrowTypeError, pa.ArrowInvalid) as err:
            warnings.append(
                QualityIssue(
                    field=rule.field,
                    issue_type="range_rule_invalid",
                    message=(
                        "Range rule skipped - "
                        f"Failed to evaluate bounds for '{rule.field}' - "
                        "Use bounds compatible with the column data type"
                    ),
                    expected=(
                        f"[min={rule.min_value}, max={rule.max_value}]"
                    ),
                    actual=str(err),
                )
            )
            continue

        if violation_mask is None:
            continue

        # Replace nulls with False so indices_nonzero doesn't count them.
        violation_mask = pc.if_else(pc.is_null(violation_mask), False, violation_mask)
        violation_indices = pc.indices_nonzero(violation_mask)
        count = len(violation_indices)
        if count == 0:
            continue

        sampled = tuple(
            int(violation_indices[i].as_py())
            for i in range(min(count, _MAX_ROW_INDICES))
        )
        bounds_desc = []
        if rule.min_value is not None:
            bounds_desc.append(f"min={rule.min_value}")
        if rule.max_value is not None:
            bounds_desc.append(f"max={rule.max_value}")
        bounds_str = ", ".join(bounds_desc)
        desc = f" ({rule.description})" if rule.description else ""

        warnings.append(
            QualityIssue(
                field=rule.field,
                issue_type="range_violation",
                message=(
                    f"Range violation{desc} - "
                    f"'{rule.field}' has {count} value(s) outside [{bounds_str}] "
                    f"at rows {list(sampled)}"
                ),
                row_indices=sampled,
            )
        )
    return warnings


# ---------------------------------------------------------------------------
# Orchestration function
# ---------------------------------------------------------------------------


def validate_output(
    result: ComputationResult,
    schema: DataSchema,
    *,
    range_rules: tuple[RangeRule, ...] = (),
) -> QualityCheckResult:
    """Validate adapter output against a declared schema.

    Runs checks in order: missing required columns → nulls → types → ranges.
    All blocking issues are aggregated.  Raises ``DataQualityError`` when
    blocking issues exist; otherwise returns ``QualityCheckResult(passed=True, ...)``.
    """
    table = result.output_fields
    errors: list[QualityIssue] = []
    all_warnings: list[QualityIssue] = []

    # 1. Missing required columns
    errors.extend(_check_missing_required_columns(table, schema))

    # Determine which declared columns are actually present (for subsequent checks)
    available = set(table.column_names)
    present_required = tuple(c for c in schema.required_columns if c in available)
    all_declared = (*schema.required_columns, *schema.optional_columns)
    present_declared = tuple(c for c in all_declared if c in available)

    # 2. Null checks on present required columns
    errors.extend(_check_nulls(table, present_required))

    # 3. Type checks on present declared columns
    errors.extend(_check_types(table, schema, present_declared))

    # 4. Range warnings
    all_warnings.extend(_check_ranges(table, range_rules))

    checked = present_declared
    qr = QualityCheckResult(
        passed=len(errors) == 0,
        errors=tuple(errors),
        warnings=tuple(all_warnings),
        checked_columns=checked,
        row_count=table.num_rows,
    )

    if not qr.passed:
        raise DataQualityError(qr)

    return qr
