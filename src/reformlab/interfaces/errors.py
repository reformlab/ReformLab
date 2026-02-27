"""Exception types for the public API layer.

Provides user-friendly exception types with structured error information.
"""

from __future__ import annotations

from typing import Any


class ConfigurationError(Exception):
    """Raised when a configuration is invalid before execution begins.

    Attributes:
        field_path: Dot-separated path to the invalid field (e.g., "scenario.start_year").
        expected: Description of expected type/value.
        actual: The actual invalid value provided.
        message: Full error message combining all context.
    """

    def __init__(
        self,
        *,
        field_path: str,
        expected: str,
        actual: Any,
        message: str | None = None,
    ) -> None:
        self.field_path = field_path
        self.expected = expected
        self.actual = actual

        if message is None:
            message = (
                f"Configuration error at '{field_path}': "
                f"expected {expected}, got {actual!r}"
            )

        self.message = message
        super().__init__(message)


class SimulationError(Exception):
    """Raised when a simulation fails during execution.

    Attributes:
        message: Description of the execution failure.
        cause: Optional underlying exception that caused the failure.
    """

    def __init__(
        self,
        message: str,
        *,
        cause: Exception | None = None,
    ) -> None:
        self.message = message
        self.cause = cause
        super().__init__(message)
