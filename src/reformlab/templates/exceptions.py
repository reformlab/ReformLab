from __future__ import annotations

from pathlib import Path


class ScenarioError(Exception):
    """Structured scenario error following IngestionError/MappingError pattern.

    Provides actionable error messages with:
    - file_path: The file that caused the error
    - summary: Brief description of what failed
    - reason: Technical explanation of why it failed
    - fix: Actionable guidance on how to resolve the issue
    - invalid_fields: Tuple of field names that are invalid/missing
    """

    def __init__(
        self,
        *,
        file_path: Path,
        summary: str,
        reason: str,
        fix: str,
        invalid_fields: tuple[str, ...] = (),
    ) -> None:
        self.file_path = file_path
        self.invalid_fields = invalid_fields

        message = f"{summary} - {reason} - {fix} (file: {file_path})"
        super().__init__(message)
