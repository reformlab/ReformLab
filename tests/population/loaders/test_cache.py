"""Tests for SourceCache disk-based caching infrastructure.

Story 11.1 — AC #2 (cache storage), AC #3 (cache reuse), AC #5 (offline),
AC #6 (CacheStatus from status()).
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import SourceConfig
from reformlab.population.loaders.cache import SourceCache


@pytest.fixture()
def config() -> SourceConfig:
    return SourceConfig(
        provider="insee",
        dataset_id="household_income",
        url="https://example.com/dataset.csv",
        params={"year": "2024"},
    )


@pytest.fixture()
def table() -> pa.Table:
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([25000.0, 35000.0, 50000.0], type=pa.float64()),
        }
    )


# ====================================================================
# put() + get() round-trip (Task 9.4)
# ====================================================================


class TestSourceCacheRoundTrip:
    """Cache write + read produces identical data."""

    def test_put_then_get_returns_identical_table(
        self,
        source_cache: SourceCache,
        config: SourceConfig,
        table: pa.Table,
    ) -> None:
        """Given a put, get returns the same table content."""
        source_cache.put(config, table)
        result = source_cache.get(config)

        assert result is not None
        cached_table, cache_status = result
        assert cached_table.equals(table)
        assert cache_status.cached is True
        assert cache_status.stale is False

    def test_put_returns_valid_cache_status(
        self,
        source_cache: SourceCache,
        config: SourceConfig,
        table: pa.Table,
    ) -> None:
        """Given a put, returned CacheStatus has all fields populated."""
        status = source_cache.put(config, table)

        assert status.cached is True
        assert status.path is not None
        assert status.path.exists()
        assert status.downloaded_at is not None
        assert status.hash is not None
        assert len(status.hash) == 64  # SHA-256 hex digest
        assert status.stale is False


# ====================================================================
# Cache miss (Task 9.5)
# ====================================================================


class TestSourceCacheMiss:
    """Cache miss returns None."""

    def test_get_on_empty_cache_returns_none(
        self,
        source_cache: SourceCache,
        config: SourceConfig,
    ) -> None:
        """Given no cached data, get returns None."""
        assert source_cache.get(config) is None


# ====================================================================
# status() (Task 9.6)
# ====================================================================


class TestSourceCacheStatus:
    """status() returns correct CacheStatus for cached and uncached datasets."""

    def test_status_for_uncached_dataset(
        self,
        source_cache: SourceCache,
        config: SourceConfig,
    ) -> None:
        """Given no cached data, status shows not cached."""
        status = source_cache.status(config)
        assert status.cached is False
        assert status.path is None
        assert status.downloaded_at is None
        assert status.hash is None

    def test_status_for_cached_dataset(
        self,
        source_cache: SourceCache,
        config: SourceConfig,
        table: pa.Table,
    ) -> None:
        """Given cached data, status shows cached with all fields."""
        source_cache.put(config, table)
        status = source_cache.status(config)

        assert status.cached is True
        assert status.path is not None
        assert status.downloaded_at is not None
        assert status.hash is not None
        assert status.stale is False


# ====================================================================
# Directory structure (Task 9.7)
# ====================================================================


class TestSourceCacheDirectoryLayout:
    """Cache creates proper {provider}/{dataset_id}/{hash}.parquet layout."""

    def test_cache_directory_structure(
        self,
        source_cache: SourceCache,
        config: SourceConfig,
        table: pa.Table,
    ) -> None:
        """Given a put, files are stored in provider/dataset_id/ directory."""
        source_cache.put(config, table)

        provider_dir = source_cache.cache_root / "insee"
        dataset_dir = provider_dir / "household_income"

        assert provider_dir.is_dir()
        assert dataset_dir.is_dir()

        parquet_files = list(dataset_dir.glob("*.parquet"))
        # Filter out .meta.json files that also contain .parquet in name
        parquet_files = [f for f in parquet_files if not f.name.endswith(".meta.json")]
        assert len(parquet_files) == 1

        meta_files = list(dataset_dir.glob("*.meta.json"))
        assert len(meta_files) == 1

    def test_cache_path_matches_expected_layout(
        self,
        source_cache: SourceCache,
        config: SourceConfig,
    ) -> None:
        """Given a config, cache_path follows {root}/{provider}/{dataset_id}/{key}.parquet."""
        path = source_cache.cache_path(config)
        assert path.parent.name == "household_income"
        assert path.parent.parent.name == "insee"
        assert path.suffix == ".parquet"

    def test_no_directory_created_on_init(
        self,
        cache_root: Path,
    ) -> None:
        """Given a SourceCache, constructor does not create directories."""
        _cache = SourceCache(cache_root=cache_root)
        assert not cache_root.exists()


# ====================================================================
# Metadata JSON (Task 9.8)
# ====================================================================


class TestSourceCacheMetadata:
    """Metadata JSON contains download timestamp, hash, URL, params."""

    def test_metadata_json_contents(
        self,
        source_cache: SourceCache,
        config: SourceConfig,
        table: pa.Table,
    ) -> None:
        """Given a put, metadata JSON has all required fields."""
        source_cache.put(config, table)
        meta_path = source_cache.metadata_path(config)

        assert meta_path.exists()
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))

        assert metadata["url"] == "https://example.com/dataset.csv"
        assert metadata["params"] == {"year": "2024"}
        assert "downloaded_at" in metadata
        assert "content_hash" in metadata
        assert len(metadata["content_hash"]) == 64
        assert metadata["provider"] == "insee"
        assert metadata["dataset_id"] == "household_income"
        assert "date_prefix" in metadata


# ====================================================================
# is_offline() (Task 9.9)
# ====================================================================


class TestSourceCacheOfflineMode:
    """is_offline() respects REFORMLAB_OFFLINE env var."""

    def test_offline_false_when_unset(
        self,
        source_cache: SourceCache,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Given no env var, is_offline returns False."""
        monkeypatch.delenv("REFORMLAB_OFFLINE", raising=False)
        assert source_cache.is_offline() is False

    @pytest.mark.parametrize("value", ["1", "true", "yes", "True", "YES"])
    def test_offline_true_for_truthy_values(
        self,
        source_cache: SourceCache,
        monkeypatch: pytest.MonkeyPatch,
        value: str,
    ) -> None:
        """Given truthy REFORMLAB_OFFLINE, is_offline returns True."""
        monkeypatch.setenv("REFORMLAB_OFFLINE", value)
        assert source_cache.is_offline() is True

    @pytest.mark.parametrize("value", ["0", "false", "no", ""])
    def test_offline_false_for_falsy_values(
        self,
        source_cache: SourceCache,
        monkeypatch: pytest.MonkeyPatch,
        value: str,
    ) -> None:
        """Given non-truthy REFORMLAB_OFFLINE, is_offline returns False."""
        monkeypatch.setenv("REFORMLAB_OFFLINE", value)
        assert source_cache.is_offline() is False


# ====================================================================
# Cache key determinism
# ====================================================================


class TestSourceCacheCacheKey:
    """cache_key() is deterministic for same inputs."""

    def test_same_config_produces_same_key(
        self,
        source_cache: SourceCache,
        config: SourceConfig,
    ) -> None:
        """Given identical config, cache_key is consistent."""
        key1 = source_cache.cache_key(config)
        key2 = source_cache.cache_key(config)
        assert key1 == key2
        assert len(key1) == 16  # truncated SHA-256

    def test_different_params_produce_different_keys(
        self,
        source_cache: SourceCache,
    ) -> None:
        """Given different params, cache keys differ."""
        config1 = SourceConfig(provider="insee", dataset_id="x", url="https://example.com", params={"a": "1"})
        config2 = SourceConfig(provider="insee", dataset_id="x", url="https://example.com", params={"a": "2"})
        assert source_cache.cache_key(config1) != source_cache.cache_key(config2)
