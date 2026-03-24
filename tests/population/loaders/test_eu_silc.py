# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for the EU-SILC synthetic PUF data source loader.

Covers protocol compliance, schema correctness, ZIP-wrapped CSV parsing
(including missing value handling, bad ZIP detection), factory functions,
and the full CachedLoader download lifecycle.
"""

from __future__ import annotations

import logging
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import DataSourceLoader, SourceConfig
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import DataSourceValidationError
from reformlab.population.loaders.eu_silc import (
    _DATASET_SCHEMAS,
    EU_SILC_AVAILABLE_DATASETS,
    EU_SILC_CATALOG,
    EuSilcDataset,
    EuSilcLoader,
    get_eu_silc_loader,
    make_eu_silc_config,
)

# ====================================================================
# Fixtures
# ====================================================================

_FIXTURES_ROOT = Path(__file__).resolve().parent.parent.parent / "fixtures"
_EU_SILC_FIXTURE_DIR = _FIXTURES_ROOT / "eu_silc"


# ====================================================================
# Helpers
# ====================================================================


def _mock_urlopen(data: bytes) -> MagicMock:
    """Create a mock context manager for urllib.request.urlopen."""
    mock_response = MagicMock()
    mock_response.read.return_value = data
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


def _make_loader(
    dataset_id: str = "silc_puf_d_fr",
    *,
    source_cache: SourceCache,
    year: int = 2013,
) -> EuSilcLoader:
    """Create an EuSilcLoader with a given cache."""
    return get_eu_silc_loader(dataset_id, cache=source_cache, year=year)


@pytest.fixture()
def eu_silc_zip_bytes() -> bytes:
    """Raw bytes of the EU-SILC fixture ZIP archive."""
    return (_EU_SILC_FIXTURE_DIR / "FR_PUF_EUSILC.zip").read_bytes()


# ====================================================================
# Protocol compliance
# ====================================================================


class TestEuSilcLoaderProtocol:
    """EuSilcLoader satisfies DataSourceLoader protocol."""

    def test_isinstance(self, source_cache: SourceCache) -> None:
        loader = _make_loader(source_cache=source_cache)
        assert isinstance(loader, DataSourceLoader)

    def test_has_download_method(self, source_cache: SourceCache) -> None:
        loader = _make_loader(source_cache=source_cache)
        assert callable(getattr(loader, "download", None))

    def test_has_status_method(self, source_cache: SourceCache) -> None:
        loader = _make_loader(source_cache=source_cache)
        assert callable(getattr(loader, "status", None))

    def test_has_schema_method(self, source_cache: SourceCache) -> None:
        loader = _make_loader(source_cache=source_cache)
        assert callable(getattr(loader, "schema", None))


# ====================================================================
# Schema
# ====================================================================


class TestEuSilcLoaderSchema:
    """schema() returns valid pa.Schema with expected fields and types."""

    def test_d_file_schema_fields(self, source_cache: SourceCache) -> None:
        loader = _make_loader("silc_puf_d_fr", source_cache=source_cache)
        schema = loader.schema()
        assert isinstance(schema, pa.Schema)
        expected_names = [
            "survey_year",
            "country",
            "household_id",
            "region",
            "household_weight",
        ]
        assert schema.names == expected_names

    def test_d_file_schema_types(self, source_cache: SourceCache) -> None:
        loader = _make_loader("silc_puf_d_fr", source_cache=source_cache)
        schema = loader.schema()
        assert schema.field("survey_year").type == pa.int64()
        assert schema.field("country").type == pa.utf8()
        assert schema.field("household_weight").type == pa.float64()

    def test_h_file_schema_fields(self, source_cache: SourceCache) -> None:
        loader = _make_loader("silc_puf_h_fr", source_cache=source_cache)
        schema = loader.schema()
        assert "total_disposable_income" in schema.names
        assert "equivalised_disposable_income" in schema.names
        assert "household_size" in schema.names
        assert "poverty_indicator" in schema.names
        assert "ability_keep_home_warm" in schema.names

    def test_h_file_schema_types(self, source_cache: SourceCache) -> None:
        loader = _make_loader("silc_puf_h_fr", source_cache=source_cache)
        schema = loader.schema()
        assert schema.field("total_disposable_income").type == pa.float64()
        assert schema.field("household_size").type == pa.int64()
        assert schema.field("poverty_indicator").type == pa.int64()

    def test_all_datasets_have_schemas(self) -> None:
        for ds_id in EU_SILC_AVAILABLE_DATASETS:
            assert ds_id in _DATASET_SCHEMAS, f"Missing schema for {ds_id}"


# ====================================================================
# Fetch / parsing
# ====================================================================


class TestEuSilcLoaderFetch:
    """_fetch() correctly parses ZIP-wrapped CSV fixtures."""

    @patch("reformlab.population.loaders.eu_silc.urllib.request.urlopen")
    def test_parse_d_file(
        self,
        mock_urlopen_fn: MagicMock,
        source_cache: SourceCache,
        eu_silc_zip_bytes: bytes,
    ) -> None:
        mock_urlopen_fn.return_value = _mock_urlopen(eu_silc_zip_bytes)
        loader = _make_loader("silc_puf_d_fr", source_cache=source_cache)
        config = make_eu_silc_config("silc_puf_d_fr", year="2013")
        table = loader._fetch(config)
        assert table.num_rows == 5
        # Verify columns are PROJECT names (not raw)
        assert "survey_year" in table.column_names
        assert "household_id" in table.column_names
        assert "DB010" not in table.column_names

    @patch("reformlab.population.loaders.eu_silc.urllib.request.urlopen")
    def test_parse_h_file(
        self,
        mock_urlopen_fn: MagicMock,
        source_cache: SourceCache,
        eu_silc_zip_bytes: bytes,
    ) -> None:
        mock_urlopen_fn.return_value = _mock_urlopen(eu_silc_zip_bytes)
        loader = _make_loader("silc_puf_h_fr", source_cache=source_cache)
        config = make_eu_silc_config("silc_puf_h_fr", year="2013")
        table = loader._fetch(config)
        assert table.num_rows == 5
        assert "total_disposable_income" in table.column_names
        assert "equivalised_disposable_income" in table.column_names

        # Check values
        incomes = table.column("total_disposable_income").to_pylist()
        assert incomes[0] == 27954.90
        assert incomes[1] == 5588.84

    @patch("reformlab.population.loaders.eu_silc.urllib.request.urlopen")
    def test_d_file_values(
        self,
        mock_urlopen_fn: MagicMock,
        source_cache: SourceCache,
        eu_silc_zip_bytes: bytes,
    ) -> None:
        mock_urlopen_fn.return_value = _mock_urlopen(eu_silc_zip_bytes)
        loader = _make_loader("silc_puf_d_fr", source_cache=source_cache)
        config = make_eu_silc_config("silc_puf_d_fr", year="2013")
        table = loader._fetch(config)

        countries = table.column("country").to_pylist()
        assert all(c == "FR" for c in countries)

        regions = table.column("region").to_pylist()
        assert regions[0] == "FR10"

        weights = table.column("household_weight").to_pylist()
        assert weights[0] == 4079.79


# ====================================================================
# Missing value handling
# ====================================================================


class TestEuSilcLoaderFetchMissingValues:
    """Empty cells produce null values."""

    @patch("reformlab.population.loaders.eu_silc.urllib.request.urlopen")
    def test_empty_income_becomes_null(
        self,
        mock_urlopen_fn: MagicMock,
        source_cache: SourceCache,
        eu_silc_zip_bytes: bytes,
    ) -> None:
        """Row with empty HY010 produces null in total_gross_income."""
        mock_urlopen_fn.return_value = _mock_urlopen(eu_silc_zip_bytes)
        loader = _make_loader("silc_puf_h_fr", source_cache=source_cache)
        config = make_eu_silc_config("silc_puf_h_fr", year="2013")
        table = loader._fetch(config)

        # Last row (index 4) has empty HY010
        values = table.column("total_gross_income")
        assert values[4].as_py() is None


# ====================================================================
# Bad ZIP handling
# ====================================================================


class TestEuSilcLoaderFetchBadZip:
    """Corrupt ZIP content raises DataSourceValidationError (not OSError)."""

    @patch("reformlab.population.loaders.eu_silc.urllib.request.urlopen")
    def test_bad_zip_raises_validation_error(
        self,
        mock_urlopen_fn: MagicMock,
        source_cache: SourceCache,
    ) -> None:
        mock_urlopen_fn.return_value = _mock_urlopen(b"not a zip file")
        loader = _make_loader("silc_puf_d_fr", source_cache=source_cache)
        config = make_eu_silc_config("silc_puf_d_fr", year="2013")
        with pytest.raises(DataSourceValidationError, match="Corrupt ZIP archive"):
            loader._fetch(config)

    @patch("reformlab.population.loaders.eu_silc.urllib.request.urlopen")
    def test_missing_year_raises_validation_error(
        self,
        mock_urlopen_fn: MagicMock,
        source_cache: SourceCache,
        eu_silc_zip_bytes: bytes,
    ) -> None:
        """Requesting a year not in the archive raises DataSourceValidationError."""
        mock_urlopen_fn.return_value = _mock_urlopen(eu_silc_zip_bytes)
        loader = _make_loader("silc_puf_d_fr", source_cache=source_cache, year=2020)
        config = make_eu_silc_config("silc_puf_d_fr", year="2020")
        with pytest.raises(DataSourceValidationError, match="Year not found"):
            loader._fetch(config)


# ====================================================================
# HTTP errors
# ====================================================================


class TestEuSilcLoaderFetchHTTPError:
    """Network errors are caught and re-raised as OSError."""

    @patch("reformlab.population.loaders.eu_silc.urllib.request.urlopen")
    def test_http_error_raises_oserror(self, mock_urlopen_fn: MagicMock, source_cache: SourceCache) -> None:
        mock_urlopen_fn.side_effect = urllib.error.HTTPError(
            "url",
            404,
            "Not Found",
            {},
            None,  # type: ignore[arg-type]
        )
        loader = _make_loader(source_cache=source_cache)
        config = make_eu_silc_config("silc_puf_d_fr")
        with pytest.raises(OSError, match="Failed to download"):
            loader._fetch(config)

    @patch("reformlab.population.loaders.eu_silc.urllib.request.urlopen")
    def test_urlerror_raises_oserror(self, mock_urlopen_fn: MagicMock, source_cache: SourceCache) -> None:
        mock_urlopen_fn.side_effect = urllib.error.URLError("timeout")
        loader = _make_loader(source_cache=source_cache)
        config = make_eu_silc_config("silc_puf_d_fr")
        with pytest.raises(OSError, match="Failed to download"):
            loader._fetch(config)


# ====================================================================
# Download integration (cache lifecycle)
# ====================================================================


class TestEuSilcLoaderDownloadIntegration:
    """Full download() cycle: cache miss -> fetch -> cache -> hit."""

    @patch("reformlab.population.loaders.eu_silc.urllib.request.urlopen")
    def test_cache_miss_then_hit(
        self,
        mock_urlopen_fn: MagicMock,
        source_cache: SourceCache,
        eu_silc_zip_bytes: bytes,
    ) -> None:
        mock_urlopen_fn.return_value = _mock_urlopen(eu_silc_zip_bytes)
        loader = get_eu_silc_loader("silc_puf_d_fr", cache=source_cache)
        config = make_eu_silc_config("silc_puf_d_fr", year="2013")

        # First call: cache miss -> fetch
        pop1, manifest1 = loader.download(config)
        assert mock_urlopen_fn.called
        assert pop1.primary_table.num_rows == 5

        # Second call: cache hit -> no network
        with patch("reformlab.population.loaders.eu_silc.urllib.request.urlopen") as mock_url2:
            pop2, manifest2 = loader.download(config)
            mock_url2.assert_not_called()

        assert pop2.primary_table.num_rows == 5
        assert pop2.primary_table.schema.equals(pop1.primary_table.schema)


# ====================================================================
# Catalog
# ====================================================================


class TestEuSilcLoaderCatalog:
    """Catalog and factory function behavior."""

    def test_available_datasets_not_empty(self) -> None:
        assert len(EU_SILC_AVAILABLE_DATASETS) >= 2

    def test_available_datasets_contents(self) -> None:
        assert "silc_puf_d_fr" in EU_SILC_AVAILABLE_DATASETS
        assert "silc_puf_h_fr" in EU_SILC_AVAILABLE_DATASETS

    def test_catalog_entries_are_datasets(self) -> None:
        for ds_id, ds in EU_SILC_CATALOG.items():
            assert isinstance(ds, EuSilcDataset)
            assert ds.dataset_id == ds_id
            assert ds.url.startswith("https://")

    def test_factory_returns_loader(self, source_cache: SourceCache) -> None:
        for ds_id in EU_SILC_AVAILABLE_DATASETS:
            loader = get_eu_silc_loader(ds_id, cache=source_cache)
            assert isinstance(loader, EuSilcLoader)
            assert isinstance(loader, DataSourceLoader)

    def test_factory_invalid_id_raises(self, source_cache: SourceCache) -> None:
        with pytest.raises(DataSourceValidationError, match="Unknown EU-SILC dataset") as exc_info:
            get_eu_silc_loader("nonexistent", cache=source_cache)
        assert "silc_puf_d_fr" in str(exc_info.value)

    def test_factory_default_logger(self, source_cache: SourceCache) -> None:
        loader = get_eu_silc_loader("silc_puf_d_fr", cache=source_cache)
        assert loader._logger.name == "reformlab.population.loaders.eu_silc"

    def test_factory_custom_logger(self, source_cache: SourceCache) -> None:
        custom = logging.getLogger("custom")
        loader = get_eu_silc_loader("silc_puf_d_fr", cache=source_cache, logger=custom)
        assert loader._logger is custom


# ====================================================================
# make_config
# ====================================================================


class TestMakeEuSilcConfig:
    """make_eu_silc_config produces correct SourceConfig."""

    def test_basic_config(self) -> None:
        config = make_eu_silc_config("silc_puf_d_fr")
        assert isinstance(config, SourceConfig)
        assert config.provider == "eu_silc"
        assert config.dataset_id == "silc_puf_d_fr"

    def test_config_with_params(self) -> None:
        config = make_eu_silc_config("silc_puf_d_fr", year="2013")
        assert config.params == {"year": "2013"}

    def test_all_catalog_entries_produce_config(self) -> None:
        for ds_id in EU_SILC_AVAILABLE_DATASETS:
            config = make_eu_silc_config(ds_id)
            assert config.provider == "eu_silc"

    def test_invalid_id_raises(self) -> None:
        with pytest.raises(DataSourceValidationError):
            make_eu_silc_config("nonexistent")


# ====================================================================
# Dataset dataclass
# ====================================================================


class TestEuSilcDataset:
    """EuSilcDataset is a frozen dataclass."""

    def test_frozen(self) -> None:
        ds = list(EU_SILC_CATALOG.values())[0]
        with pytest.raises(AttributeError):
            ds.dataset_id = "mutated"  # type: ignore[misc]

    def test_defaults(self) -> None:
        ds = EuSilcDataset(
            dataset_id="test",
            description="test",
            url="https://example.com",
            file_suffix="d",
        )
        assert ds.encoding == "utf-8"
        assert ds.separator == ","
        assert ds.null_markers == ("",)
