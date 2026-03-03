from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import CachedLoader, SourceConfig
from reformlab.population.loaders.cache import SourceCache


@pytest.fixture()
def cache_root(tmp_path: Path) -> Path:
    """Temporary cache root directory for tests."""
    return tmp_path / "cache" / "sources"


@pytest.fixture()
def source_cache(cache_root: Path) -> SourceCache:
    """A SourceCache instance using a temporary directory."""
    return SourceCache(cache_root=cache_root)


@pytest.fixture()
def mock_schema() -> pa.Schema:
    """Schema for mock loader tests."""
    return pa.schema(
        [
            pa.field("household_id", pa.int64()),
            pa.field("income", pa.float64()),
            pa.field("decile", pa.int32()),
        ]
    )


@pytest.fixture()
def mock_table(mock_schema: pa.Schema) -> pa.Table:
    """A table matching mock_schema."""
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([25000.0, 35000.0, 50000.0], type=pa.float64()),
            "decile": pa.array([2, 5, 8], type=pa.int32()),
        }
    )


class MockCachedLoader(CachedLoader):
    """Test double that simulates network fetch."""

    def __init__(
        self,
        cache: SourceCache,
        mock_table: pa.Table,
        mock_schema: pa.Schema,
        *,
        fail_fetch: bool = False,
        fail_with: type[Exception] = OSError,
    ) -> None:
        import logging

        super().__init__(cache=cache, logger=logging.getLogger("test.mock_loader"))
        self._mock_table = mock_table
        self._mock_schema = mock_schema
        self._fail_fetch = fail_fetch
        self._fail_with = fail_with
        self.fetch_called = False

    def _fetch(self, config: SourceConfig) -> pa.Table:
        self.fetch_called = True
        if self._fail_fetch:
            raise self._fail_with("Simulated network failure")
        return self._mock_table

    def schema(self) -> pa.Schema:
        return self._mock_schema
