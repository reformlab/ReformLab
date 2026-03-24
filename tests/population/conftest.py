# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pytest

from reformlab.computation.ingestion import DataSchema
from reformlab.computation.types import PopulationData
from reformlab.data.descriptor import DatasetDescriptor
from reformlab.data.pipeline import DatasetManifest, DataSourceMetadata
from reformlab.population.loaders.base import (
    CacheStatus,
    DataSourceLoader,
    SourceConfig,
)
from reformlab.population.validation import MarginalConstraint


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
                    11000.0,
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

    def download(self, config: SourceConfig) -> tuple[PopulationData, DatasetManifest]:
        population = PopulationData.from_table(self._table, entity_type="default")
        manifest = DatasetManifest(
            source=DataSourceMetadata(
                name=config.dataset_id,
                version="mock",
                url=config.url,
                description=config.description,
            ),
            content_hash=hashlib.sha256(b"mock").hexdigest(),
            file_path=Path("<mock>"),
            format="parquet",
            row_count=self._table.num_rows,
            column_names=tuple(self._table.column_names),
            loaded_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        return population, manifest

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(
            cached=True,
            path=None,
            downloaded_at=None,
            hash=None,
            stale=False,
        )

    def descriptor(self) -> DatasetDescriptor:
        all_cols = tuple(self._table.schema.names)
        return DatasetDescriptor(
            dataset_id="mock",
            provider="mock",
            description="mock dataset",
            schema=DataSchema(
                schema=self._table.schema,
                required_columns=all_cols,
            ),
        )


class _FailingLoader:
    """Mock loader that always raises on download."""

    def download(self, config: SourceConfig) -> tuple[PopulationData, DatasetManifest]:
        from reformlab.population.loaders.errors import DataSourceDownloadError

        raise DataSourceDownloadError(
            summary="Download failed",
            reason="mock failure for testing",
            fix="this is a test mock",
        )

    def status(self, config: SourceConfig) -> CacheStatus:
        return CacheStatus(cached=False, path=None, downloaded_at=None, hash=None, stale=False)

    def descriptor(self) -> DatasetDescriptor:
        return DatasetDescriptor(
            dataset_id="failing",
            provider="mock",
            description="failing mock",
            schema=DataSchema(
                schema=pa.schema([]),
                required_columns=(),
            ),
        )


# ====================================================================
# Validation fixtures (Story 11.7)
# ====================================================================


@pytest.fixture()
def population_table_valid() -> pa.Table:
    """PyArrow table with valid uniform distributions matching INSEE/SDES references.

    20 rows with income deciles: 2 households per decile (uniform 10% distribution).
    Vehicle types: 13 cars (65%), 4 suvs (20%), 3 bikes (15%) - matches constraint exactly.
    """
    return pa.table(
        {
            "income_decile": pa.array(
                [
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "8",
                    "9",
                    "10",
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "8",
                    "9",
                    "10",
                ],
                type=pa.utf8(),
            ),
            "vehicle_type": pa.array(
                [
                    "car",
                    "car",
                    "car",
                    "car",
                    "car",
                    "car",
                    "car",
                    "car",
                    "car",
                    "car",
                    "car",
                    "car",
                    "car",
                    "suv",
                    "suv",
                    "suv",
                    "suv",
                    "bike",
                    "bike",
                    "bike",
                ],
                type=pa.utf8(),
            ),
            "region_code": pa.array(
                [
                    "11",
                    "24",
                    "31",
                    "44",
                    "75",
                    "11",
                    "24",
                    "31",
                    "44",
                    "75",
                    "11",
                    "24",
                    "31",
                    "44",
                    "75",
                    "11",
                    "24",
                    "31",
                    "44",
                    "75",
                ],
                type=pa.utf8(),
            ),
        }
    )


@pytest.fixture()
def population_table_invalid_income() -> pa.Table:
    """PyArrow table with invalid income decile distribution.

    Same structure as population_table_valid but income decile distribution deviates:
    decile 1: 3 households (expected ~1), decile 10: 0 households (expected ~1).
    """
    return pa.table(
        {
            "income_decile": pa.array(["1", "1", "1", "2", "3", "4", "5", "6", "7", "8"], type=pa.utf8()),
            "vehicle_type": pa.array(
                ["car", "car", "car", "car", "car", "car", "car", "suv", "suv", "bike"], type=pa.utf8()
            ),
            "region_code": pa.array(
                ["11", "24", "31", "44", "75", "11", "24", "31", "44", "75"], type=pa.utf8()
            ),
        }
    )


@pytest.fixture()
def population_table_invalid_vehicle() -> pa.Table:
    """PyArrow table with invalid vehicle type distribution.

    Vehicle type distribution deviates: 10 cars, 0 suvs, 0 bikes (expected ~7/2/1).
    """
    return pa.table(
        {
            "income_decile": pa.array(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"], type=pa.utf8()),
            "vehicle_type": pa.array(
                ["car", "car", "car", "car", "car", "car", "car", "car", "car", "car"], type=pa.utf8()
            ),
            "region_code": pa.array(
                ["11", "24", "31", "44", "75", "11", "24", "31", "44", "75"], type=pa.utf8()
            ),
        }
    )


@pytest.fixture()
def constraint_income_decile() -> MarginalConstraint:
    """MarginalConstraint for income_decile with uniform distribution (INSEE reference).

    Uniform: decile 1-10 each 0.1 = 10%, tolerance 0.02.
    """
    return MarginalConstraint(
        dimension="income_decile",
        distribution={
            "1": 0.1,
            "2": 0.1,
            "3": 0.1,
            "4": 0.1,
            "5": 0.1,
            "6": 0.1,
            "7": 0.1,
            "8": 0.1,
            "9": 0.1,
            "10": 0.1,
        },
        tolerance=0.02,
    )


@pytest.fixture()
def constraint_vehicle_type() -> MarginalConstraint:
    """MarginalConstraint for vehicle_type with SDES reference distribution.

    Distribution: {"car": 0.65, "suv": 0.20, "bike": 0.15}, tolerance 0.03.
    """
    return MarginalConstraint(
        dimension="vehicle_type",
        distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
        tolerance=0.03,
    )


@pytest.fixture()
def constraint_region_code() -> MarginalConstraint:
    """MarginalConstraint for region_code with uniform distribution.

    Distribution: {"11": 0.2, "24": 0.2, "31": 0.2, "44": 0.2, "75": 0.2}, tolerance 0.05.
    """
    return MarginalConstraint(
        dimension="region_code",
        distribution={"11": 0.2, "24": 0.2, "31": 0.2, "44": 0.2, "75": 0.2},
        tolerance=0.05,
    )
