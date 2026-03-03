"""Tests for data source exception hierarchy.

Verifies that all exceptions follow the ``[summary] - [reason] - [fix]``
message pattern and expose structured diagnostic fields.

Story 11.1 — AC #4, #5 (exception semantics).
"""

from __future__ import annotations

import pytest

from reformlab.population.loaders.errors import (
    DataSourceDownloadError,
    DataSourceError,
    DataSourceOfflineError,
    DataSourceValidationError,
)


class TestDataSourceErrorHierarchy:
    """All data source exceptions inherit from DataSourceError."""

    def test_base_error_message_format(self) -> None:
        """Given summary/reason/fix, message follows 'summary - reason - fix' pattern."""
        exc = DataSourceError(
            summary="Download failed",
            reason="connection timeout",
            fix="retry later",
        )
        assert str(exc) == "Download failed - connection timeout - retry later"

    def test_base_error_exposes_fields(self) -> None:
        """Given a DataSourceError, structured fields are accessible."""
        exc = DataSourceError(summary="S", reason="R", fix="F")
        assert exc.summary == "S"
        assert exc.reason == "R"
        assert exc.fix == "F"

    def test_offline_error_is_datasource_error(self) -> None:
        exc = DataSourceOfflineError(summary="S", reason="R", fix="F")
        assert isinstance(exc, DataSourceError)
        assert str(exc) == "S - R - F"

    def test_download_error_is_datasource_error(self) -> None:
        exc = DataSourceDownloadError(summary="S", reason="R", fix="F")
        assert isinstance(exc, DataSourceError)

    def test_validation_error_is_datasource_error(self) -> None:
        exc = DataSourceValidationError(summary="S", reason="R", fix="F")
        assert isinstance(exc, DataSourceError)

    def test_all_errors_catchable_as_base(self) -> None:
        """Given any subclass, it can be caught as DataSourceError."""
        for cls in (DataSourceOfflineError, DataSourceDownloadError, DataSourceValidationError):
            with pytest.raises(DataSourceError):
                raise cls(summary="S", reason="R", fix="F")

    def test_keyword_only_constructor(self) -> None:
        """Given positional args, TypeError is raised (keyword-only)."""
        with pytest.raises(TypeError):
            DataSourceError("S", "R", "F")  # type: ignore[misc]
