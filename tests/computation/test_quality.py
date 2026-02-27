"""Story 1.5 data-quality check tests for adapter-output validation."""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.computation.ingestion import DataSchema
from reformlab.computation.quality import (
    DataQualityError,
    QualityCheckResult,
    QualityIssue,
    RangeRule,
    validate_output,
)
from reformlab.computation.types import ComputationResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def output_schema() -> DataSchema:
    """Schema with required and optional columns for quality-check tests."""
    return DataSchema(
        schema=pa.schema(
            [
                pa.field("household_id", pa.int64()),
                pa.field("person_id", pa.int64()),
                pa.field("income_tax", pa.float64()),
                pa.field("carbon_tax", pa.float64()),
            ]
        ),
        required_columns=("income_tax", "carbon_tax"),
        optional_columns=("household_id", "person_id"),
    )


@pytest.fixture()
def valid_result() -> ComputationResult:
    """A fully valid ComputationResult."""
    table = pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "person_id": pa.array([10, 20, 30], type=pa.int64()),
            "income_tax": pa.array([3000.0, 6750.0, 12000.0], type=pa.float64()),
            "carbon_tax": pa.array([134.0, 200.0, 267.0], type=pa.float64()),
        }
    )
    return ComputationResult(
        output_fields=table, adapter_version="test-1.0", period=2025
    )


# ---------------------------------------------------------------------------
# AC-1: Null detection in required fields
# ---------------------------------------------------------------------------


class TestNullDetection:
    def test_null_in_required_field_raises_blocking_error(
        self, output_schema: DataSchema
    ) -> None:
        """Given nulls in a required field, then DataQualityError is raised
        with exact field name and row indices.
        """
        table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "person_id": pa.array([10, 20, 30], type=pa.int64()),
                "income_tax": pa.array([3000.0, None, 12000.0], type=pa.float64()),
                "carbon_tax": pa.array([134.0, 200.0, 267.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )

        with pytest.raises(DataQualityError) as exc_info:
            validate_output(result, output_schema)

        qr = exc_info.value.result
        assert not qr.passed
        assert len(qr.errors) >= 1
        null_issue = next(i for i in qr.errors if i.field == "income_tax")
        assert null_issue.issue_type == "null_values"
        assert 1 in null_issue.row_indices

    def test_null_in_optional_field_is_non_blocking(
        self, output_schema: DataSchema
    ) -> None:
        """Given nulls in an optional field, validation passes silently."""
        table = pa.table(
            {
                "household_id": pa.array([1, None, 3], type=pa.int64()),
                "person_id": pa.array([10, 20, 30], type=pa.int64()),
                "income_tax": pa.array([3000.0, 6750.0, 12000.0], type=pa.float64()),
                "carbon_tax": pa.array([134.0, 200.0, 267.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )

        qr = validate_output(result, output_schema)
        assert qr.passed

    def test_null_row_indices_capped_at_ten(self, output_schema: DataSchema) -> None:
        """Given >10 null rows, row_indices is capped at 10 entries."""
        n = 20
        income = [None] * n
        table = pa.table(
            {
                "household_id": pa.array(list(range(n)), type=pa.int64()),
                "person_id": pa.array(list(range(n)), type=pa.int64()),
                "income_tax": pa.array(income, type=pa.float64()),
                "carbon_tax": pa.array([100.0] * n, type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )

        with pytest.raises(DataQualityError) as exc_info:
            validate_output(result, output_schema)

        null_issue = next(
            i for i in exc_info.value.result.errors if i.field == "income_tax"
        )
        assert len(null_issue.row_indices) <= 10


# ---------------------------------------------------------------------------
# AC-2: Type mismatch detection
# ---------------------------------------------------------------------------


class TestTypeMismatch:
    def test_type_mismatch_detected(self, output_schema: DataSchema) -> None:
        """Given a column with wrong type, then blocking error reports
        column name, expected type, and actual type.
        """
        table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "person_id": pa.array([10, 20, 30], type=pa.int64()),
                "income_tax": pa.array(["3000", "6750", "12000"], type=pa.string()),
                "carbon_tax": pa.array([134.0, 200.0, 267.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )

        with pytest.raises(DataQualityError) as exc_info:
            validate_output(result, output_schema)

        qr = exc_info.value.result
        type_issue = next(i for i in qr.errors if i.issue_type == "type_mismatch")
        assert type_issue.field == "income_tax"
        assert type_issue.expected == "double"
        assert type_issue.actual == "string"


# ---------------------------------------------------------------------------
# AC-3: Missing required column detection
# ---------------------------------------------------------------------------


class TestMissingColumns:
    def test_missing_required_columns_detected(self, output_schema: DataSchema) -> None:
        """Given missing required columns, then blocking error identifies all."""
        table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "person_id": pa.array([10, 20, 30], type=pa.int64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )

        with pytest.raises(DataQualityError) as exc_info:
            validate_output(result, output_schema)

        qr = exc_info.value.result
        missing_issues = [i for i in qr.errors if i.issue_type == "missing_column"]
        missing_fields = sorted(i.field for i in missing_issues)
        assert missing_fields == ["carbon_tax", "income_tax"]


# ---------------------------------------------------------------------------
# AC-4: Silent pass for valid output
# ---------------------------------------------------------------------------


class TestValidOutput:
    def test_valid_output_passes_silently(
        self, output_schema: DataSchema, valid_result: ComputationResult
    ) -> None:
        """Given valid output, checks pass and return QualityCheckResult."""
        qr = validate_output(valid_result, output_schema)

        assert qr.passed
        assert len(qr.errors) == 0
        assert len(qr.warnings) == 0
        assert qr.row_count == 3
        assert len(qr.checked_columns) > 0


# ---------------------------------------------------------------------------
# AC-5: Multi-error aggregation
# ---------------------------------------------------------------------------


class TestMultiErrorAggregation:
    def test_multiple_issues_aggregated(self, output_schema: DataSchema) -> None:
        """Given nulls AND type mismatches, all issues reported together."""
        table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "person_id": pa.array([10, 20, 30], type=pa.int64()),
                "income_tax": pa.array([None, None, None], type=pa.float64()),
                "carbon_tax": pa.array(["a", "b", "c"], type=pa.string()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )

        with pytest.raises(DataQualityError) as exc_info:
            validate_output(result, output_schema)

        qr = exc_info.value.result
        issue_types = {i.issue_type for i in qr.errors}
        assert "null_values" in issue_types
        assert "type_mismatch" in issue_types

    def test_missing_columns_and_type_mismatch_aggregated(self) -> None:
        """Given missing columns AND type mismatches, all reported together."""
        schema = DataSchema(
            schema=pa.schema(
                [
                    pa.field("col_a", pa.float64()),
                    pa.field("col_b", pa.int64()),
                    pa.field("col_c", pa.float64()),
                ]
            ),
            required_columns=("col_a", "col_b", "col_c"),
        )
        table = pa.table(
            {
                "col_a": pa.array([1.0, 2.0], type=pa.float64()),
                "col_b": pa.array(["x", "y"], type=pa.string()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )

        with pytest.raises(DataQualityError) as exc_info:
            validate_output(result, schema)

        qr = exc_info.value.result
        issue_types = {i.issue_type for i in qr.errors}
        assert "missing_column" in issue_types
        assert "type_mismatch" in issue_types


# ---------------------------------------------------------------------------
# AC-6: Value range warnings (non-blocking)
# ---------------------------------------------------------------------------


class TestRangeWarnings:
    def test_range_violations_produce_warnings(self, output_schema: DataSchema) -> None:
        """Given anomalous values with range rules, warnings are emitted
        without blocking execution.
        """
        table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "person_id": pa.array([10, 20, 30], type=pa.int64()),
                "income_tax": pa.array([-500.0, 6750.0, 12000.0], type=pa.float64()),
                "carbon_tax": pa.array([134.0, 200.0, 267.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )
        rules = (
            RangeRule(
                field="income_tax",
                min_value=0.0,
                max_value=None,
                description="Income tax should be non-negative",
            ),
        )

        qr = validate_output(result, output_schema, range_rules=rules)

        assert qr.passed  # warnings are non-blocking
        assert len(qr.warnings) >= 1
        w = qr.warnings[0]
        assert w.field == "income_tax"
        assert w.issue_type == "range_violation"

    def test_range_warnings_with_blocking_errors_all_reported(
        self, output_schema: DataSchema
    ) -> None:
        """Given range warnings AND null errors, both are in the result."""
        table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "person_id": pa.array([10, 20, 30], type=pa.int64()),
                "income_tax": pa.array([None, 6750.0, -100.0], type=pa.float64()),
                "carbon_tax": pa.array([134.0, 200.0, 267.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )
        rules = (
            RangeRule(
                field="income_tax",
                min_value=0.0,
                max_value=None,
                description="non-negative",
            ),
        )

        with pytest.raises(DataQualityError) as exc_info:
            validate_output(result, output_schema, range_rules=rules)

        qr = exc_info.value.result
        assert len(qr.errors) >= 1
        assert len(qr.warnings) >= 1

    def test_range_check_handles_nullable_column(
        self, output_schema: DataSchema
    ) -> None:
        """Given nullable numeric columns, range checks ignore nulls safely."""
        table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "person_id": pa.array([10, None, 30], type=pa.int64()),
                "income_tax": pa.array([3000.0, 6750.0, 12000.0], type=pa.float64()),
                "carbon_tax": pa.array([134.0, 200.0, 267.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )
        rules = (
            RangeRule(
                field="person_id",
                min_value=0,
                max_value=100,
                description="Person ID in valid range",
            ),
        )

        qr = validate_output(result, output_schema, range_rules=rules)
        assert qr.passed

    def test_range_only_warnings_path(self, output_schema: DataSchema) -> None:
        """Given only range violations (no blocking errors),
        result passes with warnings.
        """
        table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "person_id": pa.array([10, 20, 30], type=pa.int64()),
                "income_tax": pa.array([3000.0, 6750.0, 12000.0], type=pa.float64()),
                "carbon_tax": pa.array([134.0, 200.0, 1500.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )
        rules = (
            RangeRule(
                field="carbon_tax",
                min_value=0.0,
                max_value=1000.0,
                description="Carbon tax should be under 1000",
            ),
        )

        qr = validate_output(result, output_schema, range_rules=rules)
        assert qr.passed
        assert len(qr.warnings) == 1
        assert qr.warnings[0].field == "carbon_tax"

    def test_non_numeric_range_rule_is_non_blocking_warning(self) -> None:
        """Given a range rule on a non-numeric field, validation does not crash
        and emits a structured warning.
        """
        schema = DataSchema(
            schema=pa.schema(
                [
                    pa.field("income_tax", pa.float64()),
                    pa.field("carbon_tax", pa.float64()),
                    pa.field("segment", pa.string()),
                ]
            ),
            required_columns=("income_tax", "carbon_tax"),
            optional_columns=("segment",),
        )
        table = pa.table(
            {
                "income_tax": pa.array([3000.0, 6750.0], type=pa.float64()),
                "carbon_tax": pa.array([134.0, 200.0], type=pa.float64()),
                "segment": pa.array(["urban", "rural"], type=pa.string()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )
        rules = (
            RangeRule(
                field="segment",
                min_value=0,
                max_value=100,
                description="Invalid rule for string field",
            ),
        )

        qr = validate_output(result, schema, range_rules=rules)
        assert qr.passed
        assert len(qr.warnings) == 1
        warning = qr.warnings[0]
        assert warning.field == "segment"
        assert warning.issue_type == "range_rule_invalid"
        assert "non-numeric type" in warning.message

    def test_unknown_field_range_rule_is_non_blocking_warning(
        self, output_schema: DataSchema
    ) -> None:
        """Given a rule for a missing field, emit a structured warning."""
        table = pa.table(
            {
                "household_id": pa.array([1, 2], type=pa.int64()),
                "person_id": pa.array([10, 20], type=pa.int64()),
                "income_tax": pa.array([3000.0, 6750.0], type=pa.float64()),
                "carbon_tax": pa.array([134.0, 200.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )
        rules = (RangeRule(field="unknown_field", min_value=0.0, max_value=1.0),)

        qr = validate_output(result, output_schema, range_rules=rules)
        assert qr.passed
        assert len(qr.warnings) == 1
        warning = qr.warnings[0]
        assert warning.field == "unknown_field"
        assert warning.issue_type == "range_rule_invalid"
        assert "not found in output columns" in warning.message

    def test_range_rule_without_bounds_is_non_blocking_warning(
        self, output_schema: DataSchema
    ) -> None:
        """Given min/max are both None, emit a structured warning."""
        table = pa.table(
            {
                "household_id": pa.array([1, 2], type=pa.int64()),
                "person_id": pa.array([10, 20], type=pa.int64()),
                "income_tax": pa.array([3000.0, 6750.0], type=pa.float64()),
                "carbon_tax": pa.array([134.0, 200.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )
        rules = (RangeRule(field="income_tax", min_value=None, max_value=None),)

        qr = validate_output(result, output_schema, range_rules=rules)
        assert qr.passed
        assert len(qr.warnings) == 1
        warning = qr.warnings[0]
        assert warning.field == "income_tax"
        assert warning.issue_type == "range_rule_invalid"
        assert "no bounds configured" in warning.message

    def test_inverted_bounds_range_rule_is_non_blocking_warning(
        self, output_schema: DataSchema
    ) -> None:
        """Given min_value > max_value, emit invalid-rule warning."""
        table = pa.table(
            {
                "household_id": pa.array([1, 2], type=pa.int64()),
                "person_id": pa.array([10, 20], type=pa.int64()),
                "income_tax": pa.array([3000.0, 6750.0], type=pa.float64()),
                "carbon_tax": pa.array([134.0, 200.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )
        rules = (RangeRule(field="income_tax", min_value=500.0, max_value=100.0),)

        qr = validate_output(result, output_schema, range_rules=rules)
        assert qr.passed
        assert len(qr.warnings) == 1
        warning = qr.warnings[0]
        assert warning.field == "income_tax"
        assert warning.issue_type == "range_rule_invalid"
        assert "invalid bounds" in warning.message


# ---------------------------------------------------------------------------
# Empty table behavior
# ---------------------------------------------------------------------------


class TestEmptyTable:
    def test_empty_table_passes_validation(self, output_schema: DataSchema) -> None:
        """Given empty table with correct schema, validation passes."""
        table = pa.table(
            {
                "household_id": pa.array([], type=pa.int64()),
                "person_id": pa.array([], type=pa.int64()),
                "income_tax": pa.array([], type=pa.float64()),
                "carbon_tax": pa.array([], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )

        qr = validate_output(result, output_schema)
        assert qr.passed
        assert qr.row_count == 0


# ---------------------------------------------------------------------------
# DataQualityError formatting
# ---------------------------------------------------------------------------


class TestDataQualityErrorFormat:
    def test_error_message_is_multi_line_summary(
        self, output_schema: DataSchema
    ) -> None:
        """DataQualityError message contains a concise multi-line summary."""
        table = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "person_id": pa.array([10], type=pa.int64()),
                "income_tax": pa.array([None], type=pa.float64()),
                "carbon_tax": pa.array([134.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )

        with pytest.raises(DataQualityError) as exc_info:
            validate_output(result, output_schema)

        message = str(exc_info.value)
        assert "income_tax" in message
        assert "null" in message.lower()

    def test_error_carries_quality_check_result(
        self, output_schema: DataSchema
    ) -> None:
        """DataQualityError.result is programmatically inspectable."""
        table = pa.table(
            {
                "household_id": pa.array([1], type=pa.int64()),
                "person_id": pa.array([10], type=pa.int64()),
                "income_tax": pa.array([None], type=pa.float64()),
                "carbon_tax": pa.array([134.0], type=pa.float64()),
            }
        )
        result = ComputationResult(
            output_fields=table, adapter_version="test-1.0", period=2025
        )

        with pytest.raises(DataQualityError) as exc_info:
            validate_output(result, output_schema)

        qr = exc_info.value.result
        assert isinstance(qr, QualityCheckResult)
        assert isinstance(qr.errors, tuple)
        assert all(isinstance(e, QualityIssue) for e in qr.errors)
