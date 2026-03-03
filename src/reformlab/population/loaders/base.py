"""DataSourceLoader protocol, supporting types, and CachedLoader base class.

Defines the structural protocol for institutional data source loaders,
the ``SourceConfig`` and ``CacheStatus`` frozen dataclasses, and the
``CachedLoader`` convenience base class that wraps cache logic around
the download lifecycle.

Implements Story 11.1 (DataSourceLoader protocol and caching infrastructure).

References
----------
- ``ComputationAdapter`` in ``src/reformlab/computation/adapter.py`` (protocol pattern)
- ``OrchestratorStep`` in ``src/reformlab/orchestrator/step.py`` (protocol pattern)
- Architecture: External Data Caching & Offline Strategy section
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    import pyarrow as pa

    from reformlab.population.loaders.cache import SourceCache


# ====================================================================
# Data types
# ====================================================================


@dataclass(frozen=True)
class SourceConfig:
    """Immutable configuration for a data source download.

    Attributes
    ----------
    provider : str
        Institutional data provider identifier (e.g. ``"insee"``, ``"eurostat"``).
    dataset_id : str
        Dataset identifier within the provider namespace.
    url : str
        Download URL for the dataset.
    params : dict[str, str]
        Query parameters for the download request.
    description : str
        Human-readable description of the dataset.
    """

    provider: str
    dataset_id: str
    url: str
    params: dict[str, str] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider must be a non-empty string")
        if not self.dataset_id.strip():
            raise ValueError("dataset_id must be a non-empty string")
        # Deep-copy mutable container (frozen dataclass pattern)
        object.__setattr__(self, "params", dict(self.params))


@dataclass(frozen=True)
class CacheStatus:
    """Status of a cached data source.

    Returned by ``DataSourceLoader.status()`` and ``SourceCache.status()``.

    Attributes
    ----------
    cached : bool
        Whether a cached version of the dataset exists on disk.
    path : Path | None
        Path to the cached Parquet file, or ``None`` if not cached.
    downloaded_at : datetime | None
        Timestamp of the last successful download.
    hash : str | None
        SHA-256 hex digest of the cached Parquet file content.
    stale : bool
        Whether the cached version is considered stale (date prefix mismatch).
    """

    cached: bool
    path: Path | None
    downloaded_at: datetime | None
    hash: str | None
    stale: bool


# ====================================================================
# Protocol
# ====================================================================


@runtime_checkable
class DataSourceLoader(Protocol):
    """Interface for institutional data source loaders.

    Structural (duck-typed) protocol: any class that implements
    ``download()``, ``status()``, and ``schema()`` with the correct
    signatures satisfies the contract — no explicit inheritance required.

    Each loader handles one institutional data source (e.g. INSEE, Eurostat).
    The loader downloads, schema-validates, caches, and returns ``pa.Table``
    data. Offline-first semantics: cached data is preferred over network
    access, and stale cache is used as fallback on network failure.

    See Also
    --------
    ``ComputationAdapter`` : Equivalent protocol for computation backends.
    ``CachedLoader`` : Convenience base class implementing cache logic.
    """

    def download(self, config: SourceConfig) -> pa.Table:
        """Download (or retrieve from cache) a dataset.

        Args:
            config: Source configuration identifying the dataset.

        Returns:
            A ``pa.Table`` containing the schema-validated dataset.
        """
        ...

    def status(self, config: SourceConfig) -> CacheStatus:
        """Check cache status for a dataset without loading data.

        Args:
            config: Source configuration identifying the dataset.

        Returns:
            A ``CacheStatus`` describing the cache state.
        """
        ...

    def schema(self) -> pa.Schema:
        """Return the expected PyArrow schema for this loader's datasets."""
        ...


# ====================================================================
# CachedLoader base class
# ====================================================================


class CachedLoader:
    """Base class wrapping ``DataSourceLoader`` protocol with cache logic.

    Concrete loaders (e.g. INSEELoader, EurostatLoader) subclass this
    and override ``_fetch()`` and ``schema()``. The ``download()`` method
    orchestrates: check cache -> if miss, check offline -> fetch ->
    validate schema -> cache -> return.

    This is a concrete implementation convenience, not a protocol or ABC.
    Concrete loaders satisfy the ``DataSourceLoader`` protocol via duck
    typing (they have ``download()``, ``status()``, ``schema()``).

    Pattern: ``CachedLoader`` is to ``DataSourceLoader`` what
    ``OpenFiscaAdapter`` is to ``ComputationAdapter``.
    """

    def __init__(self, *, cache: SourceCache, logger: logging.Logger) -> None:
        self._cache = cache
        self._logger = logger

    def download(self, config: SourceConfig) -> pa.Table:
        """Download a dataset with cache-first semantics.

        Lifecycle:
        1. Check cache — if fresh hit, return immediately.
        2. If offline mode and cache miss, raise ``DataSourceOfflineError``.
        3. Attempt network fetch via ``_fetch()``.
        4. On network failure with stale cache, use stale cache + log warning.
        5. On network failure without cache, raise ``DataSourceDownloadError``.
        6. Validate fetched data against ``schema()``.
        7. Store in cache and return.
        """
        from reformlab.population.loaders.errors import (
            DataSourceDownloadError,
            DataSourceOfflineError,
            DataSourceValidationError,
        )

        # 1. Check cache
        cached = self._cache.get(config)
        if cached is not None:
            table, cache_status = cached
            if not cache_status.stale:
                return table

        # At this point: either no cache, or cache is stale
        stale_result = cached  # May be None or (table, status)

        # 2. Check offline mode
        if self._cache.is_offline():
            if stale_result is not None:
                stale_table, stale_status = stale_result
                self._log_stale_warning(config, stale_status)
                return stale_table
            raise DataSourceOfflineError(
                summary="Offline mode cache miss",
                reason=f"no cached data for {config.provider}/{config.dataset_id} "
                f"and REFORMLAB_OFFLINE is set",
                fix="Run once with network access to populate the cache, "
                "or unset REFORMLAB_OFFLINE",
            )

        # 3. Attempt network fetch
        try:
            table = self._fetch(config)
        except (OSError, Exception) as exc:
            # 4. Network failure with stale cache — use stale
            if stale_result is not None:
                stale_table, stale_status = stale_result
                self._log_stale_warning(config, stale_status)
                return stale_table
            # 5. Network failure without cache
            if isinstance(exc, OSError):
                raise DataSourceDownloadError(
                    summary="Download failed",
                    reason=f"network error for {config.provider}/{config.dataset_id}: {exc}",
                    fix="Check network connectivity and retry, "
                    "or populate the cache manually",
                ) from exc
            raise

        # 6. Validate schema
        expected_schema = self.schema()
        actual_names = set(table.schema.names)
        expected_names = set(expected_schema.names)
        missing = expected_names - actual_names
        if missing:
            raise DataSourceValidationError(
                summary="Schema validation failed",
                reason=f"downloaded data for {config.provider}/{config.dataset_id} "
                f"is missing columns: {', '.join(sorted(missing))}",
                fix="Check the data source URL and parameters, "
                "or update the loader schema",
            )

        for field_name in expected_schema.names:
            if field_name in actual_names:
                expected_type = expected_schema.field(field_name).type
                actual_type = table.schema.field(field_name).type
                if not actual_type.equals(expected_type):
                    raise DataSourceValidationError(
                        summary="Schema validation failed",
                        reason=f"column '{field_name}' has type {actual_type}, "
                        f"expected {expected_type}",
                        fix="Check the data source format or update the loader schema",
                    )

        # 7. Store in cache and return
        self._cache.put(config, table)
        return table

    def status(self, config: SourceConfig) -> CacheStatus:
        """Delegate to the underlying cache status check."""
        return self._cache.status(config)

    def schema(self) -> pa.Schema:
        """Return the expected PyArrow schema. Subclasses must override."""
        raise NotImplementedError

    def _fetch(self, config: SourceConfig) -> pa.Table:
        """Perform the actual network download. Subclasses must override."""
        raise NotImplementedError

    def _log_stale_warning(self, config: SourceConfig, cache_status: CacheStatus) -> None:
        """Log a governance warning when using stale cache."""
        self._logger.warning(
            "event=stale_cache_used provider=%s dataset_id=%s downloaded_at=%s hash=%s",
            config.provider,
            config.dataset_id,
            cache_status.downloaded_at,
            cache_status.hash,
        )
