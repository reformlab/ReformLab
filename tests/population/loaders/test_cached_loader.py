"""Tests for CachedLoader lifecycle (cache hit, miss, offline, fallback).

Story 11.1 — AC #2 (caching), AC #3 (cache reuse), AC #4 (stale fallback),
AC #5 (offline mode), AC #1 (protocol compliance).
"""

from __future__ import annotations

import logging

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import DataSourceLoader, SourceConfig
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import (
    DataSourceDownloadError,
    DataSourceOfflineError,
    DataSourceValidationError,
)
from tests.population.loaders.conftest import MockCachedLoader

# ====================================================================
# Protocol compliance
# ====================================================================


class TestCachedLoaderProtocol:
    """CachedLoader instances satisfy the DataSourceLoader protocol."""

    def test_cached_loader_satisfies_protocol(
        self,
        source_cache: SourceCache,
        mock_table: pa.Table,
        mock_schema: pa.Schema,
    ) -> None:
        """Given a MockCachedLoader, it satisfies DataSourceLoader protocol."""
        loader = MockCachedLoader(source_cache, mock_table, mock_schema)
        assert isinstance(loader, DataSourceLoader)


# ====================================================================
# Cache hit — _fetch() NOT called (Task 9.10)
# ====================================================================


class TestCachedLoaderCacheHit:
    """When cache is fresh, _fetch() is not called."""

    def test_cache_hit_returns_cached_table(
        self,
        source_cache: SourceCache,
        mock_table: pa.Table,
        mock_schema: pa.Schema,
        sample_source_config: SourceConfig,
    ) -> None:
        """Given a fresh cache entry, download returns cached table without fetch."""
        # Pre-populate cache
        source_cache.put(sample_source_config, mock_table)

        loader = MockCachedLoader(source_cache, mock_table, mock_schema)
        result = loader.download(sample_source_config)

        assert result.equals(mock_table)
        assert loader.fetch_called is False


# ====================================================================
# Cache miss — _fetch() IS called (Task 9.11)
# ====================================================================


class TestCachedLoaderCacheMiss:
    """When cache is empty, _fetch() is called and result is cached."""

    def test_cache_miss_calls_fetch_and_caches_result(
        self,
        source_cache: SourceCache,
        mock_table: pa.Table,
        mock_schema: pa.Schema,
        sample_source_config: SourceConfig,
    ) -> None:
        """Given empty cache, download calls _fetch and caches result."""
        loader = MockCachedLoader(source_cache, mock_table, mock_schema)
        result = loader.download(sample_source_config)

        assert result.equals(mock_table)
        assert loader.fetch_called is True

        # Verify it was cached
        status = source_cache.status(sample_source_config)
        assert status.cached is True


# ====================================================================
# Network failure + existing cache: stale fallback (Task 9.12)
# ====================================================================


class TestCachedLoaderStaleFallback:
    """On network failure with stale cache, use stale data + log warning."""

    def test_network_failure_with_stale_cache_returns_stale_data(
        self,
        source_cache: SourceCache,
        mock_table: pa.Table,
        mock_schema: pa.Schema,
        sample_source_config: SourceConfig,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Given a cached entry that is stale and network fails, stale table is returned."""
        # Pre-populate cache, then make it "stale" by changing the cache key
        source_cache.put(sample_source_config, mock_table)

        # Make the cache_key return a different key so existing cache appears stale
        monkeypatch.setattr(
            source_cache,
            "cache_key",
            lambda config: "different_key_123",  # noqa: ARG005
        )

        loader = MockCachedLoader(
            source_cache,
            mock_table,
            mock_schema,
            fail_fetch=True,
            fail_with=OSError,
        )

        with caplog.at_level(logging.WARNING):
            result = loader.download(sample_source_config)

        assert result.equals(mock_table)
        assert "stale_cache_used" in caplog.text


# ====================================================================
# Network failure + no cache: error (Task 9.13)
# ====================================================================


class TestCachedLoaderNetworkFailureNoCache:
    """On network failure without cache, DataSourceDownloadError is raised."""

    def test_network_failure_no_cache_raises_download_error(
        self,
        source_cache: SourceCache,
        mock_table: pa.Table,
        mock_schema: pa.Schema,
        sample_source_config: SourceConfig,
    ) -> None:
        """Given empty cache and network failure, DataSourceDownloadError is raised."""
        loader = MockCachedLoader(
            source_cache,
            mock_table,
            mock_schema,
            fail_fetch=True,
            fail_with=OSError,
        )

        with pytest.raises(DataSourceDownloadError, match="Download failed"):
            loader.download(sample_source_config)


# ====================================================================
# Offline mode + cache hit (Task 9.14)
# ====================================================================


class TestCachedLoaderOfflineCacheHit:
    """In offline mode with fresh cache, table is returned without fetch."""

    def test_offline_mode_with_cache_returns_cached_table(
        self,
        source_cache: SourceCache,
        mock_table: pa.Table,
        mock_schema: pa.Schema,
        sample_source_config: SourceConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given REFORMLAB_OFFLINE=1 and cached data, cached table is returned."""
        source_cache.put(sample_source_config, mock_table)
        monkeypatch.setenv("REFORMLAB_OFFLINE", "1")

        loader = MockCachedLoader(source_cache, mock_table, mock_schema)
        result = loader.download(sample_source_config)

        assert result.equals(mock_table)
        assert loader.fetch_called is False


# ====================================================================
# Offline mode + cache miss (Task 9.15)
# ====================================================================


class TestCachedLoaderOfflineCacheMiss:
    """In offline mode without cache, DataSourceOfflineError is raised."""

    def test_offline_mode_no_cache_raises_offline_error(
        self,
        source_cache: SourceCache,
        mock_table: pa.Table,
        mock_schema: pa.Schema,
        sample_source_config: SourceConfig,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given REFORMLAB_OFFLINE=1 and no cached data, offline error is raised."""
        monkeypatch.setenv("REFORMLAB_OFFLINE", "1")

        loader = MockCachedLoader(source_cache, mock_table, mock_schema)

        with pytest.raises(DataSourceOfflineError, match="Offline mode cache miss"):
            loader.download(sample_source_config)


# ====================================================================
# Schema validation failure (Task 9.16)
# ====================================================================


class TestCachedLoaderSchemaValidation:
    """Downloaded data failing schema check raises DataSourceValidationError."""

    def test_schema_mismatch_columns_raises_validation_error(
        self,
        source_cache: SourceCache,
        sample_source_config: SourceConfig,
    ) -> None:
        """Given fetched data missing required columns, validation error is raised."""
        # Table with wrong columns
        wrong_table = pa.table({"wrong_col": pa.array([1, 2, 3], type=pa.int64())})
        expected_schema = pa.schema(
            [
                pa.field("household_id", pa.int64()),
                pa.field("income", pa.float64()),
            ]
        )

        loader = MockCachedLoader(source_cache, wrong_table, expected_schema)

        with pytest.raises(DataSourceValidationError, match="Schema validation failed"):
            loader.download(sample_source_config)

    def test_schema_mismatch_types_raises_validation_error(
        self,
        source_cache: SourceCache,
        sample_source_config: SourceConfig,
    ) -> None:
        """Given fetched data with wrong column types, validation error is raised."""
        # Table with correct column names but wrong types
        wrong_types_table = pa.table(
            {"household_id": pa.array(["a", "b", "c"], type=pa.string())}
        )
        expected_schema = pa.schema([pa.field("household_id", pa.int64())])

        loader = MockCachedLoader(source_cache, wrong_types_table, expected_schema)

        with pytest.raises(DataSourceValidationError, match="Schema validation failed"):
            loader.download(sample_source_config)


# ====================================================================
# status() delegation
# ====================================================================


class TestCachedLoaderStatus:
    """CachedLoader.status() delegates to SourceCache.status()."""

    def test_status_delegates_to_cache(
        self,
        source_cache: SourceCache,
        mock_table: pa.Table,
        mock_schema: pa.Schema,
        sample_source_config: SourceConfig,
    ) -> None:
        """Given a loader, status() returns same result as cache.status()."""
        loader = MockCachedLoader(source_cache, mock_table, mock_schema)
        status = loader.status(sample_source_config)

        assert status.cached is False

        # After caching
        source_cache.put(sample_source_config, mock_table)
        status = loader.status(sample_source_config)
        assert status.cached is True
