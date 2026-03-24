# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for the ADEME data source loader.

Covers protocol compliance, schema correctness, Windows-1252 CSV parsing
(including encoding fallback, null handling), factory functions, and the
full CachedLoader download lifecycle.

Implements Story 11.3 (Implement Eurostat, ADEME, SDES data source loaders).
"""

from __future__ import annotations

import logging
import urllib.error
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest

from reformlab.population.loaders.ademe import (
    _DATASET_SCHEMAS,
    ADEME_AVAILABLE_DATASETS,
    ADEME_CATALOG,
    ADEMEDataset,
    ADEMELoader,
    get_ademe_loader,
    make_ademe_config,
)
from reformlab.population.loaders.base import DataSourceLoader, SourceConfig
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import DataSourceValidationError

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


# ====================================================================
# AC #2, #4: Protocol compliance
# ====================================================================


class TestADEMELoaderProtocol:
    """ADEMELoader satisfies DataSourceLoader protocol."""

    def test_isinstance_check(self, source_cache: SourceCache) -> None:
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        assert isinstance(loader, DataSourceLoader)

    def test_has_download_method(self, source_cache: SourceCache) -> None:
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        assert callable(getattr(loader, "download", None))

    def test_has_status_method(self, source_cache: SourceCache) -> None:
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        assert callable(getattr(loader, "status", None))

    def test_has_schema_method(self, source_cache: SourceCache) -> None:
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        assert callable(getattr(loader, "schema", None))


# ====================================================================
# AC #2: Schema correctness
# ====================================================================


class TestADEMELoaderSchema:
    """schema() returns valid pa.Schema with expected fields and types."""

    def test_base_carbone_schema_fields(self, source_cache: SourceCache) -> None:
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        schema = loader.schema()
        assert isinstance(schema, pa.Schema)
        expected_names = [
            "element_id", "name_fr", "attribute_name_fr", "line_type",
            "unit_fr", "total_co2e", "co2_fossil", "ch4_fossil",
            "ch4_biogenic", "n2o", "co2_biogenic", "other_ghg",
            "geography", "sub_geography", "contributor",
        ]
        assert schema.names == expected_names

    def test_base_carbone_schema_types(self, source_cache: SourceCache) -> None:
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        schema = loader.schema()
        assert schema.field("element_id").type == pa.int64()
        assert schema.field("name_fr").type == pa.utf8()
        assert schema.field("total_co2e").type == pa.float64()
        assert schema.field("co2_fossil").type == pa.float64()
        assert schema.field("geography").type == pa.utf8()

    def test_all_datasets_have_schemas(self) -> None:
        for ds_id in ADEME_AVAILABLE_DATASETS:
            assert ds_id in _DATASET_SCHEMAS, f"Missing schema for {ds_id}"


# ====================================================================
# AC #2: _fetch() parsing
# ====================================================================


class TestADEMELoaderFetch:
    """_fetch() correctly parses Windows-1252 CSV fixtures."""

    def test_base_carbone_csv_parsing(
        self,
        source_cache: SourceCache,
        ademe_base_carbone_csv_bytes: bytes,
    ) -> None:
        """Given Windows-1252 fixture CSV, _fetch returns correctly parsed pa.Table."""
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        config = make_ademe_config("base_carbone")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(ademe_base_carbone_csv_bytes)):
            table = loader._fetch(config)

        assert isinstance(table, pa.Table)
        assert table.num_rows == 4
        assert table.schema.names == loader.schema().names

        # Check element_id column (int64)
        ids = table.column("element_id").to_pylist()
        assert ids[0] == 1234
        assert ids[2] == 9012

        # Check numeric emission values
        total = table.column("total_co2e").to_pylist()
        assert total[0] == 0.227
        assert total[1] == 3.25

        # Check French text with accents
        names = table.column("name_fr").to_pylist()
        assert names[0] == "Gaz naturel"
        assert names[2] == "\xc9lectricit\xe9"  # Électricité

        # Check geography with accents
        geo = table.column("geography").to_pylist()
        assert "m\xe9tropolitaine" in geo[0]  # métropolitaine


# ====================================================================
# AC #2: Encoding fallback
# ====================================================================


class TestADEMELoaderFetchEncodingFallback:
    """UTF-8 fallback when primary Windows-1252 encoding fails."""

    def test_utf8_fallback(self, source_cache: SourceCache) -> None:
        """Given a UTF-8 CSV, encoding fallback succeeds."""
        # Build a valid UTF-8 CSV (not Windows-1252)
        utf8_csv = (
            "Identifiant de l'\xe9l\xe9ment;Nom base fran\xe7ais;Nom attribut fran\xe7ais;"
            "Type Ligne;Unit\xe9 fran\xe7ais;Total poste non d\xe9compos\xe9;CO2f;CH4f;"
            "CH4b;N2O;CO2b;Autre GES;Localisation g\xe9ographique;"
            "Sous-localisation g\xe9ographique fran\xe7ais;Contributeur\r\n"
            "1234;Gaz naturel;PCI;\xc9l\xe9ment;kgCO2e/kWh PCI;0.227;0.205;0.004;"
            "0;0.018;0;0;France m\xe9tropolitaine;;ADEME\r\n"
        ).encode("utf-8")

        loader = get_ademe_loader("base_carbone", cache=source_cache)
        config = make_ademe_config("base_carbone")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(utf8_csv)):
            table = loader._fetch(config)

        assert table.num_rows == 1
        name = table.column("name_fr").to_pylist()[0]
        assert name == "Gaz naturel"
        # Verify non-ASCII content decoded correctly via UTF-8 fallback
        geo = table.column("geography").to_pylist()[0]
        assert "m\xe9tropolitaine" in geo  # métropolitaine


# ====================================================================
# AC #2: HTTP error handling
# ====================================================================


class TestADEMELoaderFetchHTTPError:
    """Network errors are caught and re-raised as OSError."""

    def test_http_404_raises_oserror(self, source_cache: SourceCache) -> None:
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        config = make_ademe_config("base_carbone")

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(
                config.url, 404, "Not Found", {}, None  # type: ignore[arg-type]
            ),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)

    def test_urlerror_raises_oserror(self, source_cache: SourceCache) -> None:
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        config = make_ademe_config("base_carbone")

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)

    def test_connection_error_raises_oserror(self, source_cache: SourceCache) -> None:
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        config = make_ademe_config("base_carbone")

        with patch(
            "urllib.request.urlopen",
            side_effect=ConnectionResetError("Connection reset"),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)


# ====================================================================
# AC #4: Full download() integration via CachedLoader
# ====================================================================


class TestADEMELoaderDownloadIntegration:
    """Full download() cycle: cache miss -> fetch -> cache -> cache hit."""

    def test_cache_miss_then_hit(
        self,
        source_cache: SourceCache,
        ademe_base_carbone_csv_bytes: bytes,
    ) -> None:
        """First download fetches from network, second reads from cache."""
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        config = make_ademe_config("base_carbone")

        # First call: cache miss -> fetch
        mock_resp = _mock_urlopen(ademe_base_carbone_csv_bytes)
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            pop1, manifest1 = loader.download(config)
            assert mock_url.called

        assert pop1.primary_table.num_rows == 4

        # Second call: cache hit -> no network
        with patch("urllib.request.urlopen") as mock_url2:
            pop2, manifest2 = loader.download(config)
            mock_url2.assert_not_called()

        assert pop2.primary_table.num_rows == 4
        assert pop2.primary_table.schema.equals(pop1.primary_table.schema)


# ====================================================================
# AC #4: Catalog and factory
# ====================================================================


class TestADEMELoaderCatalog:
    """ADEME_AVAILABLE_DATASETS and get_ademe_loader catalog behavior."""

    def test_available_datasets_has_minimum(self) -> None:
        assert len(ADEME_AVAILABLE_DATASETS) >= 1

    def test_available_datasets_contents(self) -> None:
        assert "base_carbone" in ADEME_AVAILABLE_DATASETS

    def test_catalog_entries_are_ademe_datasets(self) -> None:
        for ds_id, ds in ADEME_CATALOG.items():
            assert isinstance(ds, ADEMEDataset)
            assert ds.dataset_id == ds_id
            assert ds.url.startswith("https://")

    def test_get_ademe_loader_returns_loader(self, source_cache: SourceCache) -> None:
        for ds_id in ADEME_AVAILABLE_DATASETS:
            loader = get_ademe_loader(ds_id, cache=source_cache)
            assert isinstance(loader, ADEMELoader)
            assert isinstance(loader, DataSourceLoader)

    def test_get_ademe_loader_invalid_id_raises(self, source_cache: SourceCache) -> None:
        with pytest.raises(DataSourceValidationError, match="Unknown ADEME dataset") as exc_info:
            get_ademe_loader("nonexistent_dataset", cache=source_cache)
        assert "base_carbone" in str(exc_info.value)

    def test_get_ademe_loader_default_logger(self, source_cache: SourceCache) -> None:
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        assert loader._logger.name == "reformlab.population.loaders.ademe"

    def test_get_ademe_loader_custom_logger(self, source_cache: SourceCache) -> None:
        custom_logger = logging.getLogger("test.custom")
        loader = get_ademe_loader("base_carbone", cache=source_cache, logger=custom_logger)
        assert loader._logger is custom_logger


# ====================================================================
# AC #2: make_ademe_config
# ====================================================================


class TestMakeAdemeConfig:
    """make_ademe_config produces correct SourceConfig."""

    def test_base_carbone_config(self) -> None:
        config = make_ademe_config("base_carbone")
        assert isinstance(config, SourceConfig)
        assert config.provider == "ademe"
        assert config.dataset_id == "base_carbone"
        assert config.url == ADEME_CATALOG["base_carbone"].url
        assert config.description == ADEME_CATALOG["base_carbone"].description

    def test_config_with_params(self) -> None:
        config = make_ademe_config("base_carbone", version="23.6")
        assert config.params == {"version": "23.6"}

    def test_all_catalog_entries_produce_valid_config(self) -> None:
        for ds_id in ADEME_AVAILABLE_DATASETS:
            config = make_ademe_config(ds_id)
            assert config.provider == "ademe"
            assert config.dataset_id == ds_id

    def test_invalid_id_raises(self) -> None:
        with pytest.raises(DataSourceValidationError, match="Unknown ADEME dataset"):
            make_ademe_config("nonexistent_dataset")


# ====================================================================
# ADEMEDataset frozen dataclass
# ====================================================================


class TestADEMEDataset:
    """ADEMEDataset is a frozen dataclass with correct defaults."""

    def test_frozen(self) -> None:
        ds = ADEMEDataset(dataset_id="test", description="test", url="https://example.com")
        with pytest.raises(AttributeError):
            ds.dataset_id = "changed"  # type: ignore[misc]

    def test_defaults(self) -> None:
        ds = ADEMEDataset(dataset_id="test", description="test", url="https://example.com")
        assert ds.encoding == "windows-1252"
        assert ds.separator == ";"
        assert ds.null_markers == ("",)
        assert ds.columns == ()
