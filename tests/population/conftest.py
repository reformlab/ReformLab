from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import (
    CacheStatus,
    DataSourceLoader,
    SourceConfig,
)


@pytest.fixture()
def sample_source_config() -> SourceConfig:
    """A minimal SourceConfig for testing."""
    return SourceConfig(
        provider="insee",
        dataset_id="household_income",
        url="https://example.com/dataset.csv",
        params={"year": "2024"},
        description="INSEE household income data",
    )


@pytest.fixture()
def sample_table() -> pa.Table:
    """A small PyArrow table for cache round-trip testing."""
    return pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([25000.0, 35000.0, 50000.0], type=pa.float64()),
            "decile": pa.array([2, 5, 8], type=pa.int32()),
        }
    )


@pytest.fixture()
def sample_schema() -> pa.Schema:
    """Schema matching sample_table."""
    return pa.schema(
        [
            pa.field("household_id", pa.int64()),
            pa.field("income", pa.float64()),
            pa.field("decile", pa.int32()),
        ]
    )


# ====================================================================
# Mock loader fixtures for pipeline testing
# ====================================================================


@pytest.fixture()
def mock_loader_a() -> DataSourceLoader:
    """Mock loader that returns a fixed table with household attributes."""
    table = pa.table(
        {
            "household_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
            "income": pa.array(
                [25000.0, 35000.0, 50000.0, 65000.0, 80000.0],
                type=pa.float64(),
            ),
            "region_code": pa.array(["11", "24", "31", "44", "75"], type=pa.utf8()),
        }
    )
    return _MockLoader(table)


@pytest.fixture()
def mock_loader_b() -> DataSourceLoader:
    """Mock loader that returns a fixed table with vehicle attributes."""
    table = pa.table(
        {
            "vehicle_type": pa.array(
                ["car", "suv", "car", "truck", "van", "car", "suv", "bike"],
                type=pa.utf8(),
            ),
            "vehicle_age": pa.array([5, 2, 8, 3, 1, 4, 6, 7], type=pa.int64()),
            "fuel_type": pa.array(
                ["gasoline", "diesel", "gasoline", "diesel", "electric", "hybrid", "diesel", "electric"],
                type=pa.utf8(),
            ),
        }
    )
    return _MockLoader(table)


@pytest.fixture()
def mock_loader_c() -> DataSourceLoader:
    """Mock loader that returns a fixed table with heating attributes."""
    table = pa.table(
        {
            "income_bracket": pa.array(
                ["low", "medium", "high", "low", "medium", "high"],
                type=pa.utf8(),
            ),
            "heating_type": pa.array(
                ["gas", "electric", "heat_pump", "gas", "oil", "heat_pump"],
                type=pa.utf8(),
            ),
            "energy_kwh": pa.array(
                [12000.0, 8000.0, 5000.0, 15000.0, 18000.0, 6000.0],
                type=pa.float64(),
            ),
        }
    )
    return _MockLoader(table)


@pytest.fixture()
def mock_loader_shared() -> DataSourceLoader:
    """Mock loader that returns a table with shared columns (for conditional sampling)."""
    table = pa.table(
        {
            "income_bracket": pa.array(
                [
                    "low",
                    "low",
                    "medium",
                    "medium",
                    "high",
                    "high",
                    "low",
                    "medium",
                    "high",
                    "low",
                    "medium",
                    "high",
                ],
                type=pa.utf8(),
            ),
            "vehicle_type": pa.array(
                ["car", "suv", "car", "truck", "van", "car", "suv", "bike", "car", "suv", "truck", "van"],
                type=pa.utf8(),
            ),
            "energy_kwh": pa.array(
                [
                    12000.0,
                    15000.0,
                    8000.0,
                    18000.0,
                    5000.0,
                    10000.0,
                    14000.0,
                    6000.0,
                    13000.0,
                    9000.0,
                    16000.0,
                ],
                type=pa.float64(),
            ),
        }
    )
    return _MockLoader(table)


@pytest.fixture()
def mock_failing_loader() -> DataSourceLoader:
    """Mock loader that always raises on download."""
    return _FailingLoader()


@pytest.fixture()
def mock_source_config_a() -> SourceConfig:
    """Source config for mock_loader_a."""
    return SourceConfig(
        provider="mock",
        dataset_id="income",
        url="mock://income",
    )


@pytest.fixture()
def mock_source_config_b() -> SourceConfig:
    """Source config for mock_loader_b."""
    return SourceConfig(
        provider="mock",
        dataset_id="vehicles",
        url="mock://vehicles",
    )


@pytest.fixture()
def mock_source_config_c() -> SourceConfig:
    """Source config for mock_loader_c."""
    return SourceConfig(
        provider="mock",
        dataset_id="heating",
        url="mock://heating",
    )


@pytest.fixture()
def mock_source_config_shared() -> SourceConfig:
    """Source config for mock_loader_shared."""
    return SourceConfig(
        provider="mock",
        dataset_id="shared",
        url="mock://shared",
    )


# ====================================================================
# Mock loader implementations
# ====================================================================


class _MockLoader:
    """Minimal DataSourceLoader for testing."""

    def __init__(self, table: pa.Table) -> None:
        self._table = table

    def download(self, config: SourceConfig) -> pa.Table:
        return self._table

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(
            cached=True,
            path=None,
            downloaded_at=None,
            hash=None,
            stale=False,
        )

    def schema(self) -> pa.Schema:
        return self._table.schema


class _FailingLoader:
    """Mock loader that always raises on download."""

    def download(self, config: SourceConfig) -> pa.Table:
        from reformlab.population.loaders.errors import DataSourceDownloadError

        raise DataSourceDownloadError(
            summary="Download failed",
            reason="mock failure for testing",
            fix="this is a test mock",
        )

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(cached=False, path=None, downloaded_at=None, hash=None, stale=False)

    def schema(self) -> pa.Schema:
        return pa.schema([])
