from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import CachedLoader, SourceConfig
from reformlab.population.loaders.cache import SourceCache

# Paths to fixture directories
_FIXTURES_ROOT = Path(__file__).resolve().parent.parent.parent / "fixtures"
_FIXTURE_DIR = _FIXTURES_ROOT / "insee"
_EUROSTAT_FIXTURE_DIR = _FIXTURES_ROOT / "eurostat"
_ADEME_FIXTURE_DIR = _FIXTURES_ROOT / "ademe"
_SDES_FIXTURE_DIR = _FIXTURES_ROOT / "sdes"


@pytest.fixture()
def insee_fixture_dir() -> Path:
    """Path to the INSEE test fixture directory."""
    return _FIXTURE_DIR


@pytest.fixture()
def filosofi_commune_csv_path(insee_fixture_dir: Path) -> Path:
    """Path to the Filosofi commune-level CSV fixture."""
    return insee_fixture_dir / "filosofi_2021_commune.csv"


@pytest.fixture()
def filosofi_commune_csv_bytes(filosofi_commune_csv_path: Path) -> bytes:
    """Raw bytes of the Filosofi commune-level CSV fixture."""
    return filosofi_commune_csv_path.read_bytes()


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


# ====================================================================
# Eurostat fixtures
# ====================================================================


@pytest.fixture()
def eurostat_fixture_dir() -> Path:
    """Path to the Eurostat test fixture directory."""
    return _EUROSTAT_FIXTURE_DIR


@pytest.fixture()
def eurostat_ilc_di01_csv_bytes(eurostat_fixture_dir: Path) -> bytes:
    """Raw bytes of the Eurostat ilc_di01 CSV fixture (plain, not gzipped)."""
    return (eurostat_fixture_dir / "ilc_di01.csv").read_bytes()


@pytest.fixture()
def eurostat_nrg_d_hhq_csv_bytes(eurostat_fixture_dir: Path) -> bytes:
    """Raw bytes of the Eurostat nrg_d_hhq CSV fixture (plain, not gzipped)."""
    return (eurostat_fixture_dir / "nrg_d_hhq.csv").read_bytes()


# ====================================================================
# ADEME fixtures
# ====================================================================


@pytest.fixture()
def ademe_fixture_dir() -> Path:
    """Path to the ADEME test fixture directory."""
    return _ADEME_FIXTURE_DIR


@pytest.fixture()
def ademe_base_carbone_csv_bytes(ademe_fixture_dir: Path) -> bytes:
    """Raw bytes of the ADEME Base Carbone CSV fixture (Windows-1252 encoded)."""
    return (ademe_fixture_dir / "base_carbone.csv").read_bytes()


# ====================================================================
# SDES fixtures
# ====================================================================


@pytest.fixture()
def sdes_fixture_dir() -> Path:
    """Path to the SDES test fixture directory."""
    return _SDES_FIXTURE_DIR


@pytest.fixture()
def sdes_vehicle_fleet_csv_bytes(sdes_fixture_dir: Path) -> bytes:
    """Raw bytes of the SDES vehicle fleet CSV fixture."""
    return (sdes_fixture_dir / "vehicle_fleet.csv").read_bytes()


# ====================================================================
# Mock loader
# ====================================================================


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
