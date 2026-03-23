# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for DataSourceLoader protocol, SourceConfig, and CacheStatus.

Story 11.1 — AC #1 (protocol), AC #2/#3 (SourceConfig), AC #6 (CacheStatus).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import (
    CachedLoader,
    CacheStatus,
    DataSourceLoader,
    SourceConfig,
)
from reformlab.population.loaders.cache import SourceCache

# ====================================================================
# SourceConfig tests (Task 9.2)
# ====================================================================


class TestSourceConfig:
    """SourceConfig is a frozen dataclass with validation."""

    def test_construction_with_all_fields(self) -> None:
        """Given valid fields, SourceConfig is created successfully."""
        config = SourceConfig(
            provider="insee",
            dataset_id="household_income",
            url="https://example.com/data.csv",
            params={"year": "2024"},
            description="Test dataset",
        )
        assert config.provider == "insee"
        assert config.dataset_id == "household_income"
        assert config.url == "https://example.com/data.csv"
        assert config.params == {"year": "2024"}
        assert config.description == "Test dataset"

    def test_construction_with_defaults(self) -> None:
        """Given only required fields, defaults are applied."""
        config = SourceConfig(
            provider="eurostat",
            dataset_id="eu_silc",
            url="https://example.com/eu_silc.csv",
        )
        assert config.params == {}
        assert config.description == ""

    def test_empty_provider_rejected(self) -> None:
        """Given empty provider, ValueError is raised."""
        with pytest.raises(ValueError, match="provider must be a non-empty string"):
            SourceConfig(provider="", dataset_id="x", url="https://example.com")

    def test_whitespace_only_provider_rejected(self) -> None:
        """Given whitespace-only provider, ValueError is raised."""
        with pytest.raises(ValueError, match="provider must be a non-empty string"):
            SourceConfig(provider="   ", dataset_id="x", url="https://example.com")

    def test_empty_dataset_id_rejected(self) -> None:
        """Given empty dataset_id, ValueError is raised."""
        with pytest.raises(ValueError, match="dataset_id must be a non-empty string"):
            SourceConfig(provider="insee", dataset_id="", url="https://example.com")

    def test_whitespace_only_dataset_id_rejected(self) -> None:
        """Given whitespace-only dataset_id, ValueError is raised."""
        with pytest.raises(ValueError, match="dataset_id must be a non-empty string"):
            SourceConfig(provider="insee", dataset_id="  ", url="https://example.com")

    def test_empty_url_rejected(self) -> None:
        """Given empty URL, ValueError is raised."""
        with pytest.raises(ValueError, match="url must be a non-empty string"):
            SourceConfig(provider="insee", dataset_id="x", url="")

    def test_provider_with_path_separator_rejected(self) -> None:
        """Given provider containing path separators, ValueError is raised."""
        with pytest.raises(ValueError, match="provider must not contain path separators"):
            SourceConfig(provider="in/see", dataset_id="x", url="https://example.com")

    def test_dataset_id_with_path_separator_rejected(self) -> None:
        """Given dataset_id containing path separators, ValueError is raised."""
        with pytest.raises(ValueError, match="dataset_id must not contain path separators"):
            SourceConfig(provider="insee", dataset_id="household/income", url="https://example.com")

    def test_frozen_immutability(self) -> None:
        """Given a SourceConfig, attribute assignment raises FrozenInstanceError."""
        config = SourceConfig(provider="insee", dataset_id="x", url="https://example.com")
        with pytest.raises(AttributeError):
            config.provider = "eurostat"  # type: ignore[misc]

    def test_params_deep_copy(self) -> None:
        """Given mutable params dict, mutation of original does not affect config."""
        original_params = {"year": "2024"}
        config = SourceConfig(
            provider="insee",
            dataset_id="x",
            url="https://example.com",
            params=original_params,
        )
        original_params["year"] = "2025"
        assert config.params == {"year": "2024"}


# ====================================================================
# CacheStatus tests (Task 9.3)
# ====================================================================


class TestCacheStatus:
    """CacheStatus is a frozen dataclass with all cache state fields."""

    def test_construction_cached(self) -> None:
        """Given a cached dataset, all fields are populated."""
        now = datetime.now(UTC)
        status = CacheStatus(
            cached=True,
            path=Path("/tmp/cache/data.parquet"),
            downloaded_at=now,
            hash="abc123",
            stale=False,
        )
        assert status.cached is True
        assert status.path == Path("/tmp/cache/data.parquet")
        assert status.downloaded_at == now
        assert status.hash == "abc123"
        assert status.stale is False

    def test_construction_uncached(self) -> None:
        """Given no cached data, optional fields are None."""
        status = CacheStatus(
            cached=False,
            path=None,
            downloaded_at=None,
            hash=None,
            stale=False,
        )
        assert status.cached is False
        assert status.path is None
        assert status.downloaded_at is None
        assert status.hash is None

    def test_frozen_immutability(self) -> None:
        """Given a CacheStatus, attribute assignment raises FrozenInstanceError."""
        status = CacheStatus(cached=False, path=None, downloaded_at=None, hash=None, stale=False)
        with pytest.raises(AttributeError):
            status.cached = True  # type: ignore[misc]


# ====================================================================
# DataSourceLoader protocol tests (Task 9.1)
# ====================================================================


class TestDataSourceLoaderProtocol:
    """DataSourceLoader is a runtime-checkable structural protocol."""

    def test_isinstance_check_with_conforming_class(self) -> None:
        """Given a class with download/status/schema, isinstance returns True."""

        class ConformingLoader:
            def download(self, config: SourceConfig) -> pa.Table:
                return pa.table({})

            def status(self, config: SourceConfig) -> CacheStatus:
                return CacheStatus(cached=False, path=None, downloaded_at=None, hash=None, stale=False)

            def schema(self) -> pa.Schema:
                return pa.schema([])

        loader = ConformingLoader()
        assert isinstance(loader, DataSourceLoader)

    def test_isinstance_check_with_nonconforming_class(self) -> None:
        """Given a class missing methods, isinstance returns False."""

        class Incomplete:
            def download(self, config: SourceConfig) -> pa.Table:
                return pa.table({})

        obj = Incomplete()
        assert not isinstance(obj, DataSourceLoader)

    def test_isinstance_check_with_unrelated_class(self) -> None:
        """Given an unrelated class, isinstance returns False."""
        assert not isinstance("not a loader", DataSourceLoader)


# ====================================================================
# CachedLoader construction checks
# ====================================================================


class TestCachedLoaderConstruction:
    """CachedLoader subclasses must implement schema() and _fetch()."""

    def test_missing_schema_override_rejected(self, source_cache: SourceCache) -> None:
        """Given a subclass without schema(), constructor raises TypeError."""

        class MissingSchemaLoader(CachedLoader):
            def _fetch(self, config: SourceConfig) -> pa.Table:
                return pa.table({})

        with pytest.raises(TypeError, match="must override schema"):
            MissingSchemaLoader(cache=source_cache, logger=logging.getLogger("test"))

    def test_missing_fetch_override_rejected(self, source_cache: SourceCache) -> None:
        """Given a subclass without _fetch(), constructor raises TypeError."""

        class MissingFetchLoader(CachedLoader):
            def schema(self) -> pa.Schema:
                return pa.schema([])

        with pytest.raises(TypeError, match="must override _fetch"):
            MissingFetchLoader(cache=source_cache, logger=logging.getLogger("test"))
