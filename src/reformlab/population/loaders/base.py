# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
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

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from reformlab.population.loaders.errors import (
    DataSourceDownloadError,
    DataSourceOfflineError,
    DataSourceValidationError,
)

if TYPE_CHECKING:
    import pyarrow as pa

    from reformlab.computation.types import PopulationData
    from reformlab.data.descriptor import DatasetDescriptor
    from reformlab.data.pipeline import DatasetManifest
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
        if not self.url.strip():
            raise ValueError("url must be a non-empty string")
        if "/" in self.provider or "\\" in self.provider:
            raise ValueError("provider must not contain path separators")
        if "/" in self.dataset_id or "\\" in self.dataset_id:
            raise ValueError("dataset_id must not contain path separators")
        # Deep-copy mutable container (frozen dataclass pattern)
        object.__setattr__(self, "params", dict(self.params))

    def __repr__(self) -> str:
        return (
            f"SourceConfig(provider={self.provider!r}, "
            f"dataset_id={self.dataset_id!r})"
        )


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

    def __repr__(self) -> str:
        dl = self.downloaded_at.isoformat(timespec="seconds") if self.downloaded_at else None
        return (
            f"CacheStatus(cached={self.cached}, "
            f"stale={self.stale}, "
            f"downloaded_at={dl!r})"
        )


# ====================================================================
# Protocol
# ====================================================================


@runtime_checkable
class DataSourceLoader(Protocol):
    """Interface for institutional data source loaders.

    Structural (duck-typed) protocol: any class that implements
    ``download()``, ``status()``, and ``descriptor()`` with the correct
    signatures satisfies the contract — no explicit inheritance required.

    Each loader handles one institutional data source (e.g. INSEE, Eurostat).
    The loader downloads, schema-validates, caches, and returns
    ``(PopulationData, DatasetManifest)`` with full provenance tracking.
    Offline-first semantics: cached data is preferred over network
    access, and stale cache is used as fallback on network failure.

    See Also
    --------
    ``ComputationAdapter`` : Equivalent protocol for computation backends.
    ``CachedLoader`` : Convenience base class implementing cache logic.
    """

    def download(self, config: SourceConfig) -> tuple[PopulationData, DatasetManifest]:
        """Download (or retrieve from cache) a dataset.

        Args:
            config: Source configuration identifying the dataset.

        Returns:
            A ``(PopulationData, DatasetManifest)`` tuple with the
            schema-validated dataset and full provenance metadata.
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

    def descriptor(self) -> DatasetDescriptor:
        """Return the ``DatasetDescriptor`` for this loader's dataset."""
        ...


# ====================================================================
# CachedLoader base class
# ====================================================================


class CachedLoader:
    """Base class wrapping ``DataSourceLoader`` protocol with cache logic.

    Concrete loaders (e.g. INSEELoader, EurostatLoader) subclass this
    and override ``_fetch()``, ``schema()``, and ``descriptor()``.
    The ``download()`` method orchestrates: check cache -> if miss,
    check offline -> fetch -> validate schema -> cache -> wrap as
    ``(PopulationData, DatasetManifest)`` -> return.

    This is a concrete implementation convenience, not a protocol or ABC.
    Concrete loaders satisfy the ``DataSourceLoader`` protocol via duck
    typing (they have ``download()``, ``status()``, ``descriptor()``).

    Pattern: ``CachedLoader`` is to ``DataSourceLoader`` what
    ``OpenFiscaAdapter`` is to ``ComputationAdapter``.
    """

    def __init__(self, *, cache: SourceCache, logger: logging.Logger) -> None:
        if self.__class__.schema is CachedLoader.schema:
            raise TypeError(f"{self.__class__.__name__} must override schema()")
        if self.__class__._fetch is CachedLoader._fetch:
            raise TypeError(f"{self.__class__.__name__} must override _fetch()")
        if self.__class__.descriptor is CachedLoader.descriptor:
            raise TypeError(f"{self.__class__.__name__} must override descriptor()")
        self._cache = cache
        self._logger = logger

    def download(self, config: SourceConfig) -> tuple[PopulationData, DatasetManifest]:
        """Download a dataset with cache-first semantics.

        Lifecycle:
        1. Check cache — if fresh hit, return immediately.
        2. If offline mode and cache miss, raise ``DataSourceOfflineError``.
        3. Attempt network fetch via ``_fetch()``.
        4. On network failure with stale cache, use stale cache + log warning.
        5. On network failure without cache, raise ``DataSourceDownloadError``.
        6. Validate fetched data against ``schema()``.
        7. Store in cache.
        8. Build ``DatasetManifest``, wrap as ``PopulationData``, return.
        """
        # 1. Check cache status first to avoid loading stale tables eagerly
        cache_status = self._cache.status(config)
        if cache_status.cached and not cache_status.stale:
            fresh_result = self._cache.get(config)
            if fresh_result is not None:
                fresh_table, _ = fresh_result
                return self._wrap_result(fresh_table, config)

        # At this point: either no cache, or cache is stale
        stale_available = cache_status.cached and cache_status.stale

        # 2. Check offline mode
        if self._cache.is_offline():
            if stale_available:
                stale_result = self._cache.get(config)
                if stale_result is not None:
                    stale_table, stale_status = stale_result
                    self._log_stale_warning(config, stale_status)
                    return self._wrap_result(stale_table, config)
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
        except OSError as exc:
            # 4. Network failure with stale cache — use stale
            if stale_available:
                stale_result = self._cache.get(config)
                if stale_result is not None:
                    stale_table, stale_status = stale_result
                    self._log_stale_warning(config, stale_status)
                    return self._wrap_result(stale_table, config)
            # 5. Network failure without cache
            raise DataSourceDownloadError(
                summary="Download failed",
                reason=f"network error for {config.provider}/{config.dataset_id}: {exc}",
                fix="Check network connectivity and retry, "
                "or populate the cache manually",
            ) from exc

        # 6. Validate schema using DataSchema from descriptor
        desc = self.descriptor()
        data_schema = desc.schema
        actual_names = set(table.schema.names)

        # Check required columns
        missing_required = [
            name for name in data_schema.required_columns
            if name not in actual_names
        ]
        if missing_required:
            raise DataSourceValidationError(
                summary="Schema validation failed",
                reason=f"downloaded data for {config.provider}/{config.dataset_id} "
                f"is missing required columns: {', '.join(sorted(missing_required))}",
                fix="Check the data source URL and parameters, "
                "or update the loader schema",
            )

        # Check types for all included columns (required + available optional)
        for col_name in data_schema.schema.names:
            if col_name in actual_names:
                expected_type = data_schema.schema.field(col_name).type
                actual_type = table.schema.field(col_name).type
                if not actual_type.equals(expected_type):
                    raise DataSourceValidationError(
                        summary="Schema validation failed",
                        reason=f"column '{col_name}' has type {actual_type}, "
                        f"expected {expected_type}",
                        fix="Check the data source format or update the loader schema",
                    )

        # 7. Store in cache
        self._cache.put(config, table)

        # 8. Wrap and return
        return self._wrap_result(table, config, desc=desc)

    def _wrap_result(
        self,
        table: pa.Table,
        config: SourceConfig,
        *,
        desc: DatasetDescriptor | None = None,
    ) -> tuple[PopulationData, DatasetManifest]:
        """Wrap a ``pa.Table`` as ``(PopulationData, DatasetManifest)``."""
        import pyarrow as pa  # noqa: F811
        import pyarrow.parquet as pq

        from reformlab.computation.types import PopulationData as _PopulationData
        from reformlab.data.pipeline import DatasetManifest as _DatasetManifest
        from reformlab.data.pipeline import DataSourceMetadata as _DataSourceMetadata

        if desc is None:
            desc = self.descriptor()

        # Build DataSourceMetadata from descriptor
        source = _DataSourceMetadata(
            name=desc.dataset_id,
            version=desc.version,
            url=desc.url,
            description=desc.description,
            license=desc.license,
        )

        # Compute content hash from table bytes (serialized as Parquet in-memory)
        sink = pa.BufferOutputStream()
        pq.write_table(table, sink)
        content_hash = hashlib.sha256(sink.getvalue().to_pybytes()).hexdigest()

        manifest = _DatasetManifest(
            source=source,
            content_hash=content_hash,
            file_path=Path(f"<cache:{config.provider}/{config.dataset_id}>"),
            format="parquet",
            row_count=table.num_rows,
            column_names=tuple(table.column_names),
            loaded_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )

        entity_type = (
            desc.dataset_id
            if desc.dataset_id and desc.dataset_id.isidentifier()
            else "default"
        )
        population = _PopulationData.from_table(table, entity_type=entity_type)
        return population, manifest

    def status(self, config: SourceConfig) -> CacheStatus:
        """Delegate to the underlying cache status check."""
        return self._cache.status(config)

    def schema(self) -> pa.Schema:
        """Return the expected PyArrow schema. Subclasses must override."""
        raise NotImplementedError

    def descriptor(self) -> DatasetDescriptor:
        """Return the ``DatasetDescriptor``. Subclasses must override."""
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
