from reformlab.computation.ingestion import DataSchema as DataSchema
from reformlab.computation.types import ComputationResult as ComputationResult

class QualityIssue:
    field: str
    issue_type: str
    message: str
    row_indices: tuple[int, ...]
    expected: str
    actual: str
    def __init__(
        self,
        field: str,
        issue_type: str,
        message: str,
        row_indices: tuple[int, ...] = ...,
        expected: str = ...,
        actual: str = ...,
    ) -> None: ...

class QualityCheckResult:
    passed: bool
    errors: tuple[QualityIssue, ...]
    warnings: tuple[QualityIssue, ...]
    checked_columns: tuple[str, ...]
    row_count: int
    def __init__(
        self,
        passed: bool,
        errors: tuple[QualityIssue, ...],
        warnings: tuple[QualityIssue, ...],
        checked_columns: tuple[str, ...],
        row_count: int,
    ) -> None: ...

class RangeRule:
    field: str
    min_value: float | int | None
    max_value: float | int | None
    description: str
    def __init__(
        self,
        field: str,
        min_value: float | int | None,
        max_value: float | int | None,
        description: str = ...,
    ) -> None: ...

class DataQualityError(Exception):
    result: QualityCheckResult
    def __init__(self, result: QualityCheckResult) -> None: ...

def validate_output(
    result: ComputationResult,
    schema: DataSchema,
    *,
    range_rules: tuple[RangeRule, ...] = ...,
) -> QualityCheckResult: ...
