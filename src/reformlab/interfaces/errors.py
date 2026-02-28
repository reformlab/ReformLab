"""Exception types for the public API layer.

Provides user-friendly exception types with structured error information.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class ConfigurationError(Exception):
    """Raised when a configuration is invalid before execution begins.

    Follows the canonical error format: "[What failed] — [Why] — [How to fix]".

    Attributes:
        field_path: Dot-separated path to the invalid field (e.g., "scenario.start_year").
        expected: Description of expected type/value.
        actual: The actual invalid value provided.
        fix: Actionable guidance on how to resolve the error.
        message: Full error message combining all context.
    """

    def __init__(
        self,
        *,
        field_path: str,
        expected: str,
        actual: Any,
        message: str | None = None,
        fix: str | None = None,
    ) -> None:
        self.field_path = field_path
        self.expected = expected
        self.actual = actual
        self.fix = fix

        if message is None:
            # Follow canonical format: [What failed] — [Why] — [How to fix]
            what = f"Configuration error at '{field_path}'"
            why = f"Expected {expected}, got {actual!r}"

            if fix is None:
                # Generate default fix guidance
                fix = f"Provide a valid {expected}"

            self.fix = fix
            message = f"{what} — {why} — {fix}"

        self.message = message
        super().__init__(message)


class SimulationError(Exception):
    """Raised when a simulation fails during execution.

    Follows the canonical error format: "[What failed] — [Why] — [How to fix]".

    Attributes:
        message: Description of the execution failure.
        cause: Optional underlying exception that caused the failure.
        fix: Optional actionable guidance on how to resolve the error.
        partial_states: Optional partial states from orchestrator failures.
    """

    def __init__(
        self,
        message: str,
        *,
        cause: Exception | None = None,
        fix: str | None = None,
        partial_states: dict[int, Any] | None = None,
    ) -> None:
        self.message = message
        self.cause = cause
        self.fix = fix
        self.partial_states = partial_states or {}
        super().__init__(message)


@dataclass(frozen=True)
class ValidationIssue:
    """A single validation issue with structured context.

    Attributes:
        field_path: Dot-separated path to the invalid field.
        expected: Description of expected type/value.
        actual: The actual invalid value provided.
        fix: Actionable guidance on how to resolve the issue.
        message: Full formatted message for this issue.
    """

    field_path: str
    expected: str
    actual: Any
    fix: str
    message: str


class ValidationErrors(Exception):
    """Raised when multiple configuration validation issues are found.

    Aggregates all validation issues and reports them together instead of
    failing fast on the first error. Follows the canonical format for each issue.

    Attributes:
        issues: List of all validation issues found.
        message: Combined message listing all issues.
    """

    def __init__(self, issues: list[ValidationIssue]) -> None:
        self.issues = issues

        if len(issues) == 1:
            message = f"Configuration validation failed — {issues[0].message}"
        else:
            message_lines = [
                f"Configuration validation failed — {len(issues)} issues found — Fix the following errors:"
            ]
            for issue in issues:
                message_lines.append(f"  • {issue.message}")

            message = "\n".join(message_lines)

        self.message = message
        super().__init__(message)


class MemoryWarning(UserWarning):
    """Warning emitted when simulation may exceed available memory.

    Follows canonical format: "[What] — [Why] — [How to fix]".

    Attributes:
        estimate: MemoryEstimate with usage details.
        message: Formatted warning message.
    """

    def __init__(self, estimate: Any) -> None:
        """Initialize memory warning with estimate.

        Args:
            estimate: MemoryEstimate instance with memory usage details.
        """
        self.estimate = estimate
        message = (
            f"Memory warning — Population of {estimate.population_size:,} households "
            f"over {estimate.projection_years} years requires ~{estimate.estimated_gb:.1f}GB, "
            f"but only {estimate.available_gb:.1f}GB available "
            f"(threshold: {estimate.threshold_gb:.1f}GB for safe operation on 16GB machine) — "
            "Reduce population size, increase available memory, or set "
            "REFORMLAB_SKIP_MEMORY_WARNING=true to proceed"
        )
        super().__init__(message)
