"""Tests for the Eurostat data source loader.

Covers protocol compliance, schema correctness, gzip-compressed SDMX-CSV
parsing (including missing value handling, bad gzip detection), factory
functions, and the full CachedLoader download lifecycle.

Implements Story 11.3 (Implement Eurostat, ADEME, SDES data source loaders).
"""

from __future__ import annotations

import gzip
import logging
import urllib.error
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import DataSourceLoader, SourceConfig
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import DataSourceValidationError
from reformlab.population.loaders.eurostat import (
    _DATASET_SCHEMAS,
    EUROSTAT_AVAILABLE_DATASETS,
    EUROSTAT_CATALOG,
    EurostatDataset,
    EurostatLoader,
    get_eurostat_loader,
    make_eurostat_config,
)

# ====================================================================
# Helpers
# ====================================================================


def _make_gzip(csv_bytes: bytes) -> bytes:
    """Create gzip-compressed bytes from CSV content."""
    return gzip.compress(csv_bytes)


def _mock_urlopen(data: bytes) -> MagicMock:
    """Create a mock context manager for urllib.request.urlopen."""
    mock_response = MagicMock()
    mock_response.read.return_value = data
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


# ====================================================================
# AC #1, #4: Protocol compliance
# ====================================================================


class TestEurostatLoaderProtocol:
    """EurostatLoader satisfies DataSourceLoader protocol."""

    def test_isinstance_check(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        assert isinstance(loader, DataSourceLoader)

    def test_has_download_method(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        assert callable(getattr(loader, "download", None))

    def test_has_status_method(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        assert callable(getattr(loader, "status", None))

    def test_has_schema_method(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        assert callable(getattr(loader, "schema", None))


# ====================================================================
# AC #1: Schema correctness
# ====================================================================


class TestEurostatLoaderSchema:
    """schema() returns valid pa.Schema with expected fields and types."""

    def test_ilc_di01_schema_fields(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        schema = loader.schema()
        assert isinstance(schema, pa.Schema)
        expected_names = [
            "frequency", "quantile", "indicator", "currency",
            "country", "time_period", "value", "obs_flag",
        ]
        assert schema.names == expected_names

    def test_ilc_di01_schema_types(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        schema = loader.schema()
        assert schema.field("frequency").type == pa.utf8()
        assert schema.field("value").type == pa.float64()
        assert schema.field("obs_flag").type == pa.utf8()

    def test_nrg_d_hhq_schema_fields(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("nrg_d_hhq", cache=source_cache)
        schema = loader.schema()
        assert "energy_balance" in schema.names
        assert "energy_product" in schema.names
        assert "unit" in schema.names
        assert "value" in schema.names

    def test_nrg_d_hhq_schema_types(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("nrg_d_hhq", cache=source_cache)
        schema = loader.schema()
        assert schema.field("value").type == pa.float64()
        assert schema.field("energy_balance").type == pa.utf8()

    def test_all_datasets_have_schemas(self) -> None:
        for ds_id in EUROSTAT_AVAILABLE_DATASETS:
            assert ds_id in _DATASET_SCHEMAS, f"Missing schema for {ds_id}"


# ====================================================================
# AC #1: _fetch() parsing
# ====================================================================


class TestEurostatLoaderFetch:
    """_fetch() correctly parses gzip-compressed SDMX-CSV fixtures."""

    def test_ilc_di01_csv_parsing(
        self,
        source_cache: SourceCache,
        eurostat_ilc_di01_csv_bytes: bytes,
    ) -> None:
        """Given gzip-compressed fixture CSV, _fetch returns correctly parsed pa.Table."""
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        config = make_eurostat_config("ilc_di01")
        gz_bytes = _make_gzip(eurostat_ilc_di01_csv_bytes)

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(gz_bytes)):
            table = loader._fetch(config)

        assert isinstance(table, pa.Table)
        assert table.num_rows == 5
        assert table.schema.names == loader.schema().names

        # Check dimension columns
        countries = table.column("country").to_pylist()
        assert countries[0] == "FR"
        assert countries[4] == "DE"

        quantiles = table.column("quantile").to_pylist()
        assert quantiles[0] == "D1"
        assert quantiles[3] == "D4"

        # Check numeric values
        values = table.column("value").to_pylist()
        assert values[0] == 3.3
        assert values[1] == 4.8

    def test_nrg_d_hhq_csv_parsing(
        self,
        source_cache: SourceCache,
        eurostat_nrg_d_hhq_csv_bytes: bytes,
    ) -> None:
        """Given nrg_d_hhq fixture, _fetch returns correctly parsed pa.Table."""
        loader = get_eurostat_loader("nrg_d_hhq", cache=source_cache)
        config = make_eurostat_config("nrg_d_hhq")
        gz_bytes = _make_gzip(eurostat_nrg_d_hhq_csv_bytes)

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(gz_bytes)):
            table = loader._fetch(config)

        assert table.num_rows == 5
        assert "energy_balance" in table.schema.names
        assert "energy_product" in table.schema.names
        assert table.column("energy_product").to_pylist()[0] == "G3000"
        assert table.column("value").to_pylist()[0] == 155.2


# ====================================================================
# AC #1: Missing value handling
# ====================================================================


class TestEurostatLoaderFetchMissingValues:
    """Empty cells and ':' markers produce null values."""

    def test_empty_obs_value_becomes_null(
        self,
        source_cache: SourceCache,
        eurostat_ilc_di01_csv_bytes: bytes,
    ) -> None:
        """Row with empty OBS_VALUE produces null in value column."""
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        config = make_eurostat_config("ilc_di01")
        gz_bytes = _make_gzip(eurostat_ilc_di01_csv_bytes)

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(gz_bytes)):
            table = loader._fetch(config)

        # Last row (index 4) has empty OBS_VALUE
        values = table.column("value")
        assert values[4].as_py() is None

    def test_obs_flag_preserved(
        self,
        source_cache: SourceCache,
        eurostat_ilc_di01_csv_bytes: bytes,
    ) -> None:
        """Observation flags are preserved as strings."""
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        config = make_eurostat_config("ilc_di01")
        gz_bytes = _make_gzip(eurostat_ilc_di01_csv_bytes)

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(gz_bytes)):
            table = loader._fetch(config)

        flags = table.column("obs_flag").to_pylist()
        assert flags[1] == "b"  # break in time series
        assert flags[4] == "c"  # confidential

    def test_colon_null_marker(
        self,
        source_cache: SourceCache,
        eurostat_nrg_d_hhq_csv_bytes: bytes,
    ) -> None:
        """':' in OBS_VALUE produces null (Eurostat convention)."""
        loader = get_eurostat_loader("nrg_d_hhq", cache=source_cache)
        config = make_eurostat_config("nrg_d_hhq")
        gz_bytes = _make_gzip(eurostat_nrg_d_hhq_csv_bytes)

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(gz_bytes)):
            table = loader._fetch(config)

        # Row 3 (index 3) has ':' in OBS_VALUE
        values = table.column("value")
        assert values[3].as_py() is None


# ====================================================================
# AC #1: Bad gzip handling
# ====================================================================


class TestEurostatLoaderFetchBadGzip:
    """Corrupt gzip content raises DataSourceValidationError (not OSError)."""

    def test_bad_gzip_raises_validation_error(self, source_cache: SourceCache) -> None:
        """BadGzipFile raises DataSourceValidationError, not OSError."""
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        config = make_eurostat_config("ilc_di01")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(b"not gzip data")):
            with pytest.raises(DataSourceValidationError, match="Gzip decompression failed"):
                loader._fetch(config)

    def test_bad_gzip_does_not_trigger_stale_fallback(self, source_cache: SourceCache) -> None:
        """Corrupt gzip should NOT be caught as OSError by CachedLoader."""
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        config = make_eurostat_config("ilc_di01")

        # Verify it raises DataSourceValidationError, not OSError
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(b"corrupt")):
            with pytest.raises(DataSourceValidationError):
                loader._fetch(config)


# ====================================================================
# AC #1: HTTP error handling
# ====================================================================


class TestEurostatLoaderFetchHTTPError:
    """Network errors are caught and re-raised as OSError."""

    def test_http_404_raises_oserror(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        config = make_eurostat_config("ilc_di01")

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(
                config.url, 404, "Not Found", {}, None  # type: ignore[arg-type]
            ),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)

    def test_urlerror_raises_oserror(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        config = make_eurostat_config("ilc_di01")

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)

    def test_connection_error_raises_oserror(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        config = make_eurostat_config("ilc_di01")

        with patch(
            "urllib.request.urlopen",
            side_effect=ConnectionResetError("Connection reset"),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)


# ====================================================================
# AC #4: Full download() integration via CachedLoader
# ====================================================================


class TestEurostatLoaderDownloadIntegration:
    """Full download() cycle: cache miss -> fetch -> cache -> cache hit."""

    def test_cache_miss_then_hit(
        self,
        source_cache: SourceCache,
        eurostat_ilc_di01_csv_bytes: bytes,
    ) -> None:
        """First download fetches from network, second reads from cache."""
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        config = make_eurostat_config("ilc_di01")
        gz_bytes = _make_gzip(eurostat_ilc_di01_csv_bytes)

        # First call: cache miss -> fetch
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(gz_bytes)) as mock_url:
            table1 = loader.download(config)
            assert mock_url.called

        assert table1.num_rows == 5

        # Second call: cache hit -> no network
        with patch("urllib.request.urlopen") as mock_url2:
            table2 = loader.download(config)
            mock_url2.assert_not_called()

        assert table2.num_rows == 5
        assert table2.schema.equals(table1.schema)


# ====================================================================
# AC #4: Catalog and factory
# ====================================================================


class TestEurostatLoaderCatalog:
    """EUROSTAT_AVAILABLE_DATASETS and get_eurostat_loader catalog behavior."""

    def test_available_datasets_has_minimum(self) -> None:
        assert len(EUROSTAT_AVAILABLE_DATASETS) >= 2

    def test_available_datasets_contents(self) -> None:
        assert "ilc_di01" in EUROSTAT_AVAILABLE_DATASETS
        assert "nrg_d_hhq" in EUROSTAT_AVAILABLE_DATASETS

    def test_catalog_entries_are_eurostat_datasets(self) -> None:
        for ds_id, ds in EUROSTAT_CATALOG.items():
            assert isinstance(ds, EurostatDataset)
            assert ds.dataset_id == ds_id
            assert ds.url.startswith("https://")

    def test_get_eurostat_loader_returns_loader(self, source_cache: SourceCache) -> None:
        for ds_id in EUROSTAT_AVAILABLE_DATASETS:
            loader = get_eurostat_loader(ds_id, cache=source_cache)
            assert isinstance(loader, EurostatLoader)
            assert isinstance(loader, DataSourceLoader)

    def test_get_eurostat_loader_invalid_id_raises(self, source_cache: SourceCache) -> None:
        with pytest.raises(DataSourceValidationError, match="Unknown Eurostat dataset") as exc_info:
            get_eurostat_loader("nonexistent_dataset", cache=source_cache)
        assert "ilc_di01" in str(exc_info.value)

    def test_get_eurostat_loader_default_logger(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        assert loader._logger.name == "reformlab.population.loaders.eurostat"

    def test_get_eurostat_loader_custom_logger(self, source_cache: SourceCache) -> None:
        custom_logger = logging.getLogger("test.custom")
        loader = get_eurostat_loader("ilc_di01", cache=source_cache, logger=custom_logger)
        assert loader._logger is custom_logger


# ====================================================================
# AC #1: make_eurostat_config
# ====================================================================


class TestMakeEurostatConfig:
    """make_eurostat_config produces correct SourceConfig."""

    def test_ilc_di01_config(self) -> None:
        config = make_eurostat_config("ilc_di01")
        assert isinstance(config, SourceConfig)
        assert config.provider == "eurostat"
        assert config.dataset_id == "ilc_di01"
        assert config.url == EUROSTAT_CATALOG["ilc_di01"].url
        assert config.description == EUROSTAT_CATALOG["ilc_di01"].description

    def test_nrg_d_hhq_config(self) -> None:
        config = make_eurostat_config("nrg_d_hhq")
        assert config.provider == "eurostat"
        assert config.dataset_id == "nrg_d_hhq"

    def test_config_with_params(self) -> None:
        config = make_eurostat_config("ilc_di01", geo="FR")
        assert config.params == {"geo": "FR"}

    def test_all_catalog_entries_produce_valid_config(self) -> None:
        for ds_id in EUROSTAT_AVAILABLE_DATASETS:
            config = make_eurostat_config(ds_id)
            assert config.provider == "eurostat"
            assert config.dataset_id == ds_id

    def test_invalid_id_raises(self) -> None:
        with pytest.raises(DataSourceValidationError, match="Unknown Eurostat dataset"):
            make_eurostat_config("nonexistent_dataset")


# ====================================================================
# EurostatDataset frozen dataclass
# ====================================================================


class TestEurostatDataset:
    """EurostatDataset is a frozen dataclass with correct defaults."""

    def test_frozen(self) -> None:
        ds = EurostatDataset(dataset_id="test", description="test", url="https://example.com")
        with pytest.raises(AttributeError):
            ds.dataset_id = "changed"  # type: ignore[misc]

    def test_defaults(self) -> None:
        ds = EurostatDataset(dataset_id="test", description="test", url="https://example.com")
        assert ds.encoding == "utf-8"
        assert ds.separator == ","
        assert ds.null_markers == ("", ":")
        assert ds.columns == ()
