# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Subsystem-specific exceptions for data source loaders.

All exceptions follow the ``[summary] - [reason] - [fix]`` message
pattern established by ``IngestionError`` in the computation subsystem.

Implements Story 11.1 (DataSourceLoader protocol and caching infrastructure).
"""

from __future__ import annotations


class DataSourceError(Exception):
    """Base exception for data source operations.

    All data source exceptions use keyword-only constructor arguments
    and produce a structured ``summary - reason - fix`` message.
    """

    def __init__(self, *, summary: str, reason: str, fix: str) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        super().__init__(f"{summary} - {reason} - {fix}")


class DataSourceOfflineError(DataSourceError):
    """Raised when offline mode prevents a data source download.

    Triggered when ``REFORMLAB_OFFLINE=1`` is set and the requested
    dataset is not in the local cache.
    """


class DataSourceDownloadError(DataSourceError):
    """Raised on network/download failures without a cache fallback.

    Triggered when a download fails and no cached version exists
    for graceful degradation.
    """


class DataSourceValidationError(DataSourceError):
    """Raised when downloaded data fails schema validation.

    Triggered when the data returned by a loader does not conform
    to the expected PyArrow schema.
    """
