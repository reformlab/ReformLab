"""Tests for the INSEE data source loader.

Covers protocol compliance, schema correctness, CSV parsing (including
ZIP extraction, encoding fallback, suppressed value handling), factory
functions, and the full CachedLoader download lifecycle.

Implements Story 11.2 (Implement INSEE data source loader).
"""

from __future__ import annotations

import io
import logging
import urllib.error
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import DataSourceLoader, SourceConfig
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import DataSourceValidationError
from reformlab.population.loaders.insee import (
    _DATASET_SCHEMAS,
    AVAILABLE_DATASETS,
    INSEE_CATALOG,
    INSEEDataset,
    INSEELoader,
    get_insee_loader,
    make_insee_config,
)

# ====================================================================
# Helpers
# ====================================================================


def _make_zip(csv_bytes: bytes, filename: str = "data.csv") -> bytes:
    """Create a ZIP archive containing a single CSV file."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(filename, csv_bytes)
    return buf.getvalue()


def _make_zip_multi(files: dict[str, bytes]) -> bytes:
    """Create a ZIP archive containing multiple files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


def _mock_urlopen(data: bytes) -> MagicMock:
    """Create a mock context manager for urllib.request.urlopen."""
    mock_response = MagicMock()
    mock_response.read.return_value = data
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


# ====================================================================
# AC #1, #2: Protocol compliance
# ====================================================================


class TestINSEELoaderProtocol:
    """INSEELoader satisfies DataSourceLoader protocol."""

    def test_isinstance_check(self, source_cache: SourceCache) -> None:
        """Given an INSEELoader instance, it satisfies DataSourceLoader."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        assert isinstance(loader, DataSourceLoader)

    def test_has_download_method(self, source_cache: SourceCache) -> None:
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        assert callable(getattr(loader, "download", None))

    def test_has_status_method(self, source_cache: SourceCache) -> None:
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        assert callable(getattr(loader, "status", None))

    def test_has_schema_method(self, source_cache: SourceCache) -> None:
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        assert callable(getattr(loader, "schema", None))


# ====================================================================
# AC #1: Schema correctness
# ====================================================================


class TestINSEELoaderSchema:
    """schema() returns valid pa.Schema with expected fields and types."""

    def test_commune_schema_fields(self, source_cache: SourceCache) -> None:
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        schema = loader.schema()
        assert isinstance(schema, pa.Schema)
        expected_names = [
            "commune_code", "commune_name", "nb_fiscal_households",
            "median_income", "decile_1", "decile_2", "decile_3",
            "decile_4", "decile_5", "decile_6", "decile_7",
            "decile_8", "decile_9",
        ]
        assert schema.names == expected_names

    def test_commune_schema_types(self, source_cache: SourceCache) -> None:
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        schema = loader.schema()
        assert schema.field("commune_code").type == pa.utf8()
        assert schema.field("commune_name").type == pa.utf8()
        assert schema.field("nb_fiscal_households").type == pa.float64()
        assert schema.field("median_income").type == pa.float64()
        for i in range(1, 10):
            assert schema.field(f"decile_{i}").type == pa.float64()

    def test_iris_declared_schema_fields(self, source_cache: SourceCache) -> None:
        loader = get_insee_loader("filosofi_2021_iris_declared", cache=source_cache)
        schema = loader.schema()
        assert "iris_code" in schema.names
        assert "iris_name" in schema.names
        assert "commune_code" in schema.names
        assert "median_declared_income" in schema.names

    def test_iris_disposable_schema_fields(self, source_cache: SourceCache) -> None:
        loader = get_insee_loader("filosofi_2021_iris_disposable", cache=source_cache)
        schema = loader.schema()
        assert "iris_code" in schema.names
        assert "median_disposable_income" in schema.names

    def test_all_datasets_have_schemas(self) -> None:
        for ds_id in AVAILABLE_DATASETS:
            assert ds_id in _DATASET_SCHEMAS, f"Missing schema for {ds_id}"


# ====================================================================
# AC #1: _fetch() parsing
# ====================================================================


class TestINSEELoaderFetch:
    """_fetch() correctly parses CSV fixtures into pa.Table."""

    def test_commune_csv_parsing(
        self,
        source_cache: SourceCache,
        filosofi_commune_csv_bytes: bytes,
    ) -> None:
        """Given fixture CSV, _fetch returns correctly parsed pa.Table."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")

        zip_bytes = _make_zip(filosofi_commune_csv_bytes, "filo2021_cc_rev.csv")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(zip_bytes)):
            table = loader._fetch(config)

        assert isinstance(table, pa.Table)
        assert table.num_rows == 5
        assert table.schema.names == loader.schema().names

        # Check commune_code column
        codes = table.column("commune_code").to_pylist()
        assert codes[0] == "01001"
        assert codes[2] == "01003"

        # Check numeric values
        medians = table.column("median_income").to_pylist()
        assert medians[0] == 22050.0
        assert medians[2] == 19850.0

    def test_iris_declared_csv_parsing(
        self,
        source_cache: SourceCache,
        insee_fixture_dir: Path,
    ) -> None:
        """Given IRIS declared fixture CSV, _fetch returns correctly parsed pa.Table."""
        loader = get_insee_loader("filosofi_2021_iris_declared", cache=source_cache)
        config = make_insee_config("filosofi_2021_iris_declared")
        csv_bytes = (insee_fixture_dir / "filosofi_2021_iris_declared.csv").read_bytes()
        zip_bytes = _make_zip(csv_bytes, "BASE_TD_FILO_DISP_IRIS_2021.csv")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(zip_bytes)):
            table = loader._fetch(config)

        assert table.num_rows == 3
        assert "iris_code" in table.schema.names
        assert "median_declared_income" in table.schema.names
        assert table.column("iris_code").to_pylist()[0] == "010040101"


# ====================================================================
# AC #1: ZIP extraction
# ====================================================================


class TestINSEELoaderFetchZip:
    """ZIP-wrapped CSV extraction works correctly."""

    def test_zip_extraction(
        self,
        source_cache: SourceCache,
        filosofi_commune_csv_bytes: bytes,
    ) -> None:
        """Given a ZIP-wrapped CSV, extraction succeeds."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")
        zip_bytes = _make_zip(filosofi_commune_csv_bytes, "nested/data.CSV")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(zip_bytes)):
            table = loader._fetch(config)

        assert table.num_rows == 5

    def test_zip_no_csv_raises(self, source_cache: SourceCache) -> None:
        """Given a ZIP with no CSV files, raises DataSourceValidationError."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")
        zip_bytes = _make_zip_multi({"readme.txt": b"hello"})

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(zip_bytes)):
            with pytest.raises(DataSourceValidationError, match="No CSV file"):
                loader._fetch(config)

    def test_zip_multiple_csv_raises(
        self,
        source_cache: SourceCache,
        filosofi_commune_csv_bytes: bytes,
    ) -> None:
        """Given a ZIP with multiple CSVs, raises DataSourceValidationError."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")
        zip_bytes = _make_zip_multi({
            "data1.csv": filosofi_commune_csv_bytes,
            "data2.csv": filosofi_commune_csv_bytes,
        })

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(zip_bytes)):
            with pytest.raises(DataSourceValidationError, match="Multiple CSV files"):
                loader._fetch(config)

    def test_invalid_zip_raises(self, source_cache: SourceCache) -> None:
        """Given invalid ZIP data, raises DataSourceValidationError."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(b"not a zip")):
            with pytest.raises(DataSourceValidationError, match="Invalid ZIP archive"):
                loader._fetch(config)


# ====================================================================
# AC #1: Encoding fallback
# ====================================================================


class TestINSEELoaderFetchEncodingFallback:
    """Latin-1 fallback when UTF-8 decode fails."""

    def test_latin1_fallback(self, source_cache: SourceCache) -> None:
        """Given Latin-1 encoded CSV, encoding fallback succeeds."""
        # Raw bytes with Latin-1 byte 0xe9 (é) that forces PyArrow
        # to fail UTF-8 parsing and trigger the Latin-1 fallback
        bad_utf8_csv = (
            b"CODGEO;LIBGEO;NBMENFISC21;MED21;D121;D221;D321;D421;D521;D621;D721;D821;D921\n"
            b"01001;L'Abergement-Cl\xe9menciat;330;22050;12180;14790;17120;19460;22050;24950;28420;33500;42890\n"
        )
        zip_bytes = _make_zip(bad_utf8_csv, "data.csv")

        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(zip_bytes)):
            table = loader._fetch(config)

        assert table.num_rows == 1
        # The accented character should be preserved via Latin-1 fallback
        name = table.column("commune_name").to_pylist()[0]
        assert "menciat" in name


# ====================================================================
# AC #1: Suppressed value handling
# ====================================================================


class TestINSEELoaderFetchSuppressedValues:
    """INSEE null markers ('s', 'nd') produce null values in output."""

    def test_suppressed_values_become_null(
        self,
        source_cache: SourceCache,
        filosofi_commune_csv_bytes: bytes,
    ) -> None:
        """Rows with 's' and 'nd' in numeric columns produce nulls."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")
        zip_bytes = _make_zip(filosofi_commune_csv_bytes, "data.csv")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(zip_bytes)):
            table = loader._fetch(config)

        # Row 3 (index 3) has "s" markers — all numeric columns should be null
        median_col = table.column("median_income")
        assert median_col[3].as_py() is None

        nb_households = table.column("nb_fiscal_households")
        assert nb_households[3].as_py() is None

        # Row 4 (index 4) has "nd" markers
        assert median_col[4].as_py() is None
        assert nb_households[4].as_py() is None

        # Decile columns should also be null
        for i in range(1, 10):
            d = table.column(f"decile_{i}")
            assert d[3].as_py() is None, f"decile_{i} row 3 should be null (suppressed 's')"
            assert d[4].as_py() is None, f"decile_{i} row 4 should be null (suppressed 'nd')"

    def test_non_suppressed_values_are_present(
        self,
        source_cache: SourceCache,
        filosofi_commune_csv_bytes: bytes,
    ) -> None:
        """Non-suppressed rows have actual numeric values."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")
        zip_bytes = _make_zip(filosofi_commune_csv_bytes, "data.csv")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(zip_bytes)):
            table = loader._fetch(config)

        # Row 0 has real values
        assert table.column("median_income")[0].as_py() == 22050.0
        assert table.column("decile_1")[0].as_py() == 12180.0
        assert table.column("nb_fiscal_households")[0].as_py() == 330.0


# ====================================================================
# AC #1: HTTP error handling
# ====================================================================


class TestINSEELoaderFetchHTTPError:
    """Network errors are caught and re-raised as OSError."""

    def test_http_404_raises_oserror(self, source_cache: SourceCache) -> None:
        """HTTPError (404) is re-raised as OSError."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(
                config.url, 404, "Not Found", {}, None  # type: ignore[arg-type]
            ),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)

    def test_urlerror_raises_oserror(self, source_cache: SourceCache) -> None:
        """URLError is re-raised as OSError."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)

    def test_connection_error_raises_oserror(self, source_cache: SourceCache) -> None:
        """Generic OSError is re-raised as OSError."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")

        with patch(
            "urllib.request.urlopen",
            side_effect=ConnectionResetError("Connection reset"),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)


# ====================================================================
# AC #1: Full download() integration via CachedLoader
# ====================================================================


class TestINSEELoaderDownloadIntegration:
    """Full download() cycle: cache miss → fetch → cache → cache hit."""

    def test_cache_miss_then_hit(
        self,
        source_cache: SourceCache,
        filosofi_commune_csv_bytes: bytes,
    ) -> None:
        """First download fetches from network, second reads from cache."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        config = make_insee_config("filosofi_2021_commune")
        zip_bytes = _make_zip(filosofi_commune_csv_bytes, "data.csv")

        # First call: cache miss → fetch
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(zip_bytes)) as mock_url:
            table1 = loader.download(config)
            assert mock_url.called

        assert table1.num_rows == 5

        # Second call: cache hit → no network
        with patch("urllib.request.urlopen") as mock_url2:
            table2 = loader.download(config)
            mock_url2.assert_not_called()

        assert table2.num_rows == 5
        assert table2.schema.equals(table1.schema)


# ====================================================================
# AC #2, #3: Catalog and factory
# ====================================================================


class TestINSEELoaderCatalog:
    """AVAILABLE_DATASETS and get_insee_loader catalog behavior."""

    def test_available_datasets_has_minimum(self) -> None:
        """At least 3 income distribution datasets are available."""
        assert len(AVAILABLE_DATASETS) >= 3

    def test_available_datasets_contents(self) -> None:
        assert "filosofi_2021_commune" in AVAILABLE_DATASETS
        assert "filosofi_2021_iris_declared" in AVAILABLE_DATASETS
        assert "filosofi_2021_iris_disposable" in AVAILABLE_DATASETS

    def test_catalog_entries_are_insee_datasets(self) -> None:
        for ds_id, ds in INSEE_CATALOG.items():
            assert isinstance(ds, INSEEDataset)
            assert ds.dataset_id == ds_id
            assert ds.url.startswith("https://")

    def test_get_insee_loader_returns_loader(self, source_cache: SourceCache) -> None:
        for ds_id in AVAILABLE_DATASETS:
            loader = get_insee_loader(ds_id, cache=source_cache)
            assert isinstance(loader, INSEELoader)
            assert isinstance(loader, DataSourceLoader)

    def test_get_insee_loader_invalid_id_raises(self, source_cache: SourceCache) -> None:
        """Invalid dataset ID raises DataSourceValidationError with suggestions."""
        with pytest.raises(DataSourceValidationError, match="Unknown INSEE dataset") as exc_info:
            get_insee_loader("nonexistent_dataset", cache=source_cache)
        assert "filosofi_2021_commune" in str(exc_info.value)

    def test_get_insee_loader_default_logger(self, source_cache: SourceCache) -> None:
        """When logger is None, a default logger is used."""
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        assert loader._logger.name == "reformlab.population.loaders.insee"

    def test_get_insee_loader_custom_logger(self, source_cache: SourceCache) -> None:
        """Custom logger is passed through."""
        custom_logger = logging.getLogger("test.custom")
        loader = get_insee_loader(
            "filosofi_2021_commune",
            cache=source_cache,
            logger=custom_logger,
        )
        assert loader._logger is custom_logger


# ====================================================================
# AC #1, #2: make_insee_config
# ====================================================================


class TestMakeInseeConfig:
    """make_insee_config produces correct SourceConfig."""

    def test_commune_config(self) -> None:
        config = make_insee_config("filosofi_2021_commune")
        assert isinstance(config, SourceConfig)
        assert config.provider == "insee"
        assert config.dataset_id == "filosofi_2021_commune"
        assert config.url == INSEE_CATALOG["filosofi_2021_commune"].url
        assert config.description == INSEE_CATALOG["filosofi_2021_commune"].description

    def test_config_with_params(self) -> None:
        config = make_insee_config("filosofi_2021_commune", year="2021")
        assert config.params == {"year": "2021"}

    def test_all_catalog_entries_produce_valid_config(self) -> None:
        for ds_id in AVAILABLE_DATASETS:
            config = make_insee_config(ds_id)
            assert config.provider == "insee"
            assert config.dataset_id == ds_id

    def test_invalid_id_raises(self) -> None:
        with pytest.raises(DataSourceValidationError, match="Unknown INSEE dataset"):
            make_insee_config("nonexistent_dataset")


# ====================================================================
# INSEEDataset frozen dataclass
# ====================================================================


class TestINSEEDataset:
    """INSEEDataset is a frozen dataclass with correct defaults."""

    def test_frozen(self) -> None:
        ds = INSEEDataset(dataset_id="test", description="test", url="https://example.com", file_format="csv")
        with pytest.raises(AttributeError):
            ds.dataset_id = "changed"  # type: ignore[misc]

    def test_defaults(self) -> None:
        ds = INSEEDataset(dataset_id="test", description="test", url="https://example.com", file_format="csv")
        assert ds.encoding == "utf-8"
        assert ds.separator == ";"
        assert ds.null_markers == ("s", "nd", "")
        assert ds.columns == ()
