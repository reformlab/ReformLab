from __future__ import annotations


class CompatibilityError(Exception):
    """Raised when an unsupported computation backend version is detected.

    Attributes:
        expected: Version or range expected by the adapter.
        actual: Version actually installed.
        details: Additional context (e.g. link to compatibility matrix).
    """

    def __init__(
        self,
        expected: str,
        actual: str,
        details: str = "",
    ) -> None:
        self.expected = expected
        self.actual = actual
        self.details = details
        message = (
            f"Incompatible version: expected {expected}, got {actual}."
            f"{' ' + details if details else ''}"
        )
        super().__init__(message)
