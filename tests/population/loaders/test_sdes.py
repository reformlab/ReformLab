# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for the SDES data source loader.

Covers protocol compliance, schema correctness, DiDo CSV parsing
(including skip_rows handling, null handling), factory functions, and
the full CachedLoader download lifecycle.

Implements Story 11.3 (Implement Eurostat, ADEME, SDES data source loaders).
"""

from __future__ import annotations

import logging
import urllib.error
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest

from reformlab.population.loaders.base import DataSourceLoader, SourceConfig
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import DataSourceValidationError
from reformlab.population.loaders.sdes import (
    _DATASET_SCHEMAS,
    SDES_AVAILABLE_DATASETS,
    SDES_CATALOG,
    SDESDataset,
    SDESLoader,
    get_sdes_loader,
    make_sdes_config,
)

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
# AC #3, #4: Protocol compliance
# ====================================================================


class TestSDESLoaderProtocol:
    """SDESLoader satisfies DataSourceLoader protocol."""

    def test_isinstance_check(self, source_cache: SourceCache) -> None:
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        assert isinstance(loader, DataSourceLoader)

    def test_has_download_method(self, source_cache: SourceCache) -> None:
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        assert callable(getattr(loader, "download", None))

    def test_has_status_method(self, source_cache: SourceCache) -> None:
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        assert callable(getattr(loader, "status", None))

    def test_has_schema_method(self, source_cache: SourceCache) -> None:
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        assert callable(getattr(loader, "schema", None))


# ====================================================================
# AC #3: Schema correctness
# ====================================================================


class TestSDESLoaderSchema:
    """schema() returns valid pa.Schema with expected fields and types."""

    def test_vehicle_fleet_schema_fields(self, source_cache: SourceCache) -> None:
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        schema = loader.schema()
        assert isinstance(schema, pa.Schema)
        expected_names = [
            "region_code", "region_name", "vehicle_class", "vehicle_category",
            "fuel_type", "vehicle_age", "critair_sticker", "fleet_count_2022",
        ]
        assert schema.names == expected_names

    def test_vehicle_fleet_schema_types(self, source_cache: SourceCache) -> None:
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        schema = loader.schema()
        assert schema.field("region_code").type == pa.utf8()
        assert schema.field("region_name").type == pa.utf8()
        assert schema.field("fuel_type").type == pa.utf8()
        assert schema.field("vehicle_age").type == pa.utf8()
        assert schema.field("fleet_count_2022").type == pa.float64()

    def test_all_datasets_have_schemas(self) -> None:
        for ds_id in SDES_AVAILABLE_DATASETS:
            assert ds_id in _DATASET_SCHEMAS, f"Missing schema for {ds_id}"


# ====================================================================
# AC #3: _fetch() parsing
# ====================================================================


class TestSDESLoaderFetch:
    """_fetch() correctly parses DiDo CSV fixtures."""

    def test_vehicle_fleet_csv_parsing(
        self,
        source_cache: SourceCache,
        sdes_vehicle_fleet_csv_bytes: bytes,
    ) -> None:
        """Given fixture CSV, _fetch returns correctly parsed pa.Table."""
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        config = make_sdes_config("vehicle_fleet")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(sdes_vehicle_fleet_csv_bytes)):
            table = loader._fetch(config)

        assert isinstance(table, pa.Table)
        assert table.num_rows == 5
        assert table.schema.names == loader.schema().names

        # Check region columns
        regions = table.column("region_code").to_pylist()
        assert regions[0] == "84"
        assert regions[3] == "11"

        region_names = table.column("region_name").to_pylist()
        assert region_names[0] == "Auvergne-Rh\xf4ne-Alpes"  # Auvergne-Rhône-Alpes
        assert region_names[3] == "\xcele-de-France"  # Île-de-France

        # Check fuel types
        fuels = table.column("fuel_type").to_pylist()
        assert fuels[0] == "Diesel"
        assert fuels[1] == "Essence"
        assert fuels[2] == "Electrique"

        # Check fleet count
        counts = table.column("fleet_count_2022").to_pylist()
        assert counts[0] == 450000.0
        assert counts[2] == 95000.0

    def test_null_fleet_count_handling(
        self,
        source_cache: SourceCache,
        sdes_vehicle_fleet_csv_bytes: bytes,
    ) -> None:
        """Row with empty fleet count produces null."""
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        config = make_sdes_config("vehicle_fleet")

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(sdes_vehicle_fleet_csv_bytes)):
            table = loader._fetch(config)

        # Last row (index 4) has empty fleet count and critair
        counts = table.column("fleet_count_2022")
        assert counts[4].as_py() is None

        # critair_sticker is utf8 — empty values are empty strings, not null
        critair = table.column("critair_sticker")
        assert critair[4].as_py() == ""


# ====================================================================
# AC #3: skip_rows handling
# ====================================================================


class TestSDESLoaderFetchSkipRows:
    """skip_rows correctly skips leading description rows."""

    def test_skip_rows_skips_header_lines(self, source_cache: SourceCache) -> None:
        """Given CSV with description rows before header, skip_rows works."""
        # Build a CSV with 2 description rows before the actual header
        csv_with_desc = (
            "Description line 1\r\n"
            "Description line 2\r\n"
            "REGION_CODE;REGION_LIBELLE;CLASSE_VEHICULE;CATEGORIE_VEHICULE;"
            "CARBURANT;AGE;CRITAIR;PARC_2022\r\n"
            "84;Auvergne-Rh\xf4ne-Alpes;VP;M1;Diesel;De 1 \xe0 5 ans;Crit'Air 2;450000\r\n"
        ).encode("utf-8")

        # Create a custom dataset with skip_rows=2
        from reformlab.population.loaders.sdes import _VEHICLE_FLEET_COLUMNS, SDESDataset, SDESLoader

        ds = SDESDataset(
            dataset_id="vehicle_fleet",
            description="test",
            url="https://example.com",
            columns=_VEHICLE_FLEET_COLUMNS,
            skip_rows=2,
        )
        loader = SDESLoader(
            cache=source_cache,
            logger=logging.getLogger("test"),
            dataset=ds,
        )
        config = SourceConfig(
            provider="sdes",
            dataset_id="vehicle_fleet",
            url="https://example.com",
        )

        with patch("urllib.request.urlopen", return_value=_mock_urlopen(csv_with_desc)):
            table = loader._fetch(config)

        assert table.num_rows == 1
        assert table.column("region_code").to_pylist()[0] == "84"
        assert table.column("fleet_count_2022").to_pylist()[0] == 450000.0


# ====================================================================
# AC #3: HTTP error handling
# ====================================================================


class TestSDESLoaderFetchHTTPError:
    """Network errors are caught and re-raised as OSError."""

    def test_http_404_raises_oserror(self, source_cache: SourceCache) -> None:
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        config = make_sdes_config("vehicle_fleet")

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(
                config.url, 404, "Not Found", {}, None  # type: ignore[arg-type]
            ),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)

    def test_urlerror_raises_oserror(self, source_cache: SourceCache) -> None:
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        config = make_sdes_config("vehicle_fleet")

        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.URLError("Connection refused"),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)

    def test_connection_error_raises_oserror(self, source_cache: SourceCache) -> None:
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        config = make_sdes_config("vehicle_fleet")

        with patch(
            "urllib.request.urlopen",
            side_effect=ConnectionResetError("Connection reset"),
        ):
            with pytest.raises(OSError, match="Failed to download"):
                loader._fetch(config)


# ====================================================================
# AC #4: Full download() integration via CachedLoader
# ====================================================================


class TestSDESLoaderDownloadIntegration:
    """Full download() cycle: cache miss -> fetch -> cache -> cache hit."""

    def test_cache_miss_then_hit(
        self,
        source_cache: SourceCache,
        sdes_vehicle_fleet_csv_bytes: bytes,
    ) -> None:
        """First download fetches from network, second reads from cache."""
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        config = make_sdes_config("vehicle_fleet")

        # First call: cache miss -> fetch
        mock_resp = _mock_urlopen(sdes_vehicle_fleet_csv_bytes)
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_url:
            pop1, manifest1 = loader.download(config)
            assert mock_url.called

        assert pop1.primary_table.num_rows == 5

        # Second call: cache hit -> no network
        with patch("urllib.request.urlopen") as mock_url2:
            pop2, manifest2 = loader.download(config)
            mock_url2.assert_not_called()

        assert pop2.primary_table.num_rows == 5
        assert pop2.primary_table.schema.equals(pop1.primary_table.schema)


# ====================================================================
# AC #4: Catalog and factory
# ====================================================================


class TestSDESLoaderCatalog:
    """SDES_AVAILABLE_DATASETS and get_sdes_loader catalog behavior."""

    def test_available_datasets_has_minimum(self) -> None:
        assert len(SDES_AVAILABLE_DATASETS) >= 1

    def test_available_datasets_contents(self) -> None:
        assert "vehicle_fleet" in SDES_AVAILABLE_DATASETS

    def test_catalog_entries_are_sdes_datasets(self) -> None:
        for ds_id, ds in SDES_CATALOG.items():
            assert isinstance(ds, SDESDataset)
            assert ds.dataset_id == ds_id
            assert ds.url.startswith("https://")

    def test_get_sdes_loader_returns_loader(self, source_cache: SourceCache) -> None:
        for ds_id in SDES_AVAILABLE_DATASETS:
            loader = get_sdes_loader(ds_id, cache=source_cache)
            assert isinstance(loader, SDESLoader)
            assert isinstance(loader, DataSourceLoader)

    def test_get_sdes_loader_invalid_id_raises(self, source_cache: SourceCache) -> None:
        with pytest.raises(DataSourceValidationError, match="Unknown SDES dataset") as exc_info:
            get_sdes_loader("nonexistent_dataset", cache=source_cache)
        assert "vehicle_fleet" in str(exc_info.value)

    def test_get_sdes_loader_default_logger(self, source_cache: SourceCache) -> None:
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        assert loader._logger.name == "reformlab.population.loaders.sdes"

    def test_get_sdes_loader_custom_logger(self, source_cache: SourceCache) -> None:
        custom_logger = logging.getLogger("test.custom")
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache, logger=custom_logger)
        assert loader._logger is custom_logger


# ====================================================================
# AC #3: make_sdes_config
# ====================================================================


class TestMakeSDESConfig:
    """make_sdes_config produces correct SourceConfig."""

    def test_vehicle_fleet_config(self) -> None:
        config = make_sdes_config("vehicle_fleet")
        assert isinstance(config, SourceConfig)
        assert config.provider == "sdes"
        assert config.dataset_id == "vehicle_fleet"
        assert config.url == SDES_CATALOG["vehicle_fleet"].url
        assert config.description == SDES_CATALOG["vehicle_fleet"].description

    def test_config_with_params(self) -> None:
        config = make_sdes_config("vehicle_fleet", millesime="2023")
        assert config.params == {"millesime": "2023"}

    def test_all_catalog_entries_produce_valid_config(self) -> None:
        for ds_id in SDES_AVAILABLE_DATASETS:
            config = make_sdes_config(ds_id)
            assert config.provider == "sdes"
            assert config.dataset_id == ds_id

    def test_invalid_id_raises(self) -> None:
        with pytest.raises(DataSourceValidationError, match="Unknown SDES dataset"):
            make_sdes_config("nonexistent_dataset")


# ====================================================================
# SDESDataset frozen dataclass
# ====================================================================


class TestSDESDataset:
    """SDESDataset is a frozen dataclass with correct defaults."""

    def test_frozen(self) -> None:
        ds = SDESDataset(dataset_id="test", description="test", url="https://example.com")
        with pytest.raises(AttributeError):
            ds.dataset_id = "changed"  # type: ignore[misc]

    def test_defaults(self) -> None:
        ds = SDESDataset(dataset_id="test", description="test", url="https://example.com")
        assert ds.encoding == "utf-8"
        assert ds.separator == ";"
        assert ds.null_markers == ("",)
        assert ds.columns == ()
        assert ds.skip_rows == 0
