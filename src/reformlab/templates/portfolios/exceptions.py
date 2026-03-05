"""Portfolio-specific exceptions.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


class PortfolioError(Exception):
    """Base exception for portfolio-related errors."""

    def __init__(
        self,
        *,
        summary: str,
        reason: str,
        fix: str,
        invalid_fields: tuple[str, ...] = (),
        file_path: Path | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(summary, **kwargs)
        self.summary = summary
        self.reason = reason
        self.fix = fix
        self.invalid_fields = invalid_fields
        self.file_path = file_path

    def __str__(self) -> str:
        parts = [self.summary]
        if self.file_path:
            parts.insert(0, f"[{self.file_path}]")
        return f"{': '.join(parts)} - {self.reason}"


class PortfolioValidationError(PortfolioError):
    """Raised when portfolio structure or policy configuration is invalid."""

    pass


class PortfolioSerializationError(PortfolioError):
    """Raised when YAML serialization or deserialization fails."""

    pass
