# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
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


class ApiMappingError(Exception):
    """Raised when entity or variable names cannot be resolved against OpenFisca.

    Follows the project structured error pattern: [summary] - [reason] - [fix].

    Attributes:
        summary: Short description of the error.
        reason: Explanation of what went wrong.
        fix: Actionable guidance to resolve the issue.
        invalid_names: Names that could not be resolved.
        valid_names: Names that are accepted.
        suggestions: Close-match suggestions for each invalid name.
    """

    def __init__(
        self,
        *,
        summary: str,
        reason: str,
        fix: str,
        invalid_names: tuple[str, ...] = (),
        valid_names: tuple[str, ...] = (),
        suggestions: dict[str, list[str]] | None = None,
    ) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        self.invalid_names = invalid_names
        self.valid_names = valid_names
        self.suggestions = suggestions or {}

        message = f"{summary} - {reason} - {fix}"
        super().__init__(message)
