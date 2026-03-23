# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Guardrails for stale-cache fallback boundaries in concrete loaders."""

from __future__ import annotations

import io
import zipfile
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest

from reformlab.population.loaders.ademe import get_ademe_loader, make_ademe_config
from reformlab.population.loaders.base import SourceConfig
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.errors import DataSourceValidationError
from reformlab.population.loaders.insee import get_insee_loader, make_insee_config
from reformlab.population.loaders.sdes import get_sdes_loader, make_sdes_config


def _mock_urlopen(data: bytes) -> MagicMock:
    response = MagicMock()
    response.read.return_value = data
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)
    return response


def _make_zip(csv_bytes: bytes, filename: str = "data.csv") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr(filename, csv_bytes)
    return buf.getvalue()


def _mark_current_cache_as_stale(source_cache: SourceCache, config: SourceConfig) -> None:
    cache_dir = source_cache.cache_path(config).parent
    current_key = source_cache.cache_key(config)
    stale_key = f"stale_{current_key}"
    for path in list(cache_dir.iterdir()):
        path.rename(cache_dir / path.name.replace(current_key, stale_key))


def test_insee_validation_error_does_not_trigger_stale_fallback(
    source_cache: SourceCache,
    filosofi_commune_csv_bytes: bytes,
) -> None:
    loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
    config = make_insee_config("filosofi_2021_commune")

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(_make_zip(filosofi_commune_csv_bytes))):
        loader.download(config)
    _mark_current_cache_as_stale(source_cache, config)

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(b"not a zip archive")):
        with pytest.raises(DataSourceValidationError, match="Invalid ZIP archive"):
            loader.download(config)


def test_ademe_validation_error_does_not_trigger_stale_fallback(
    source_cache: SourceCache,
    ademe_base_carbone_csv_bytes: bytes,
) -> None:
    loader = get_ademe_loader("base_carbone", cache=source_cache)
    config = make_ademe_config("base_carbone")

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(ademe_base_carbone_csv_bytes)):
        loader.download(config)
    _mark_current_cache_as_stale(source_cache, config)

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(b"\xff\xff\xff")):
        with pytest.raises(DataSourceValidationError, match="CSV parsing failed"):
            loader.download(config)


def test_sdes_parse_error_does_not_trigger_stale_fallback(
    source_cache: SourceCache,
    sdes_vehicle_fleet_csv_bytes: bytes,
) -> None:
    loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
    config = make_sdes_config("vehicle_fleet")

    with patch("urllib.request.urlopen", return_value=_mock_urlopen(sdes_vehicle_fleet_csv_bytes)):
        loader.download(config)
    _mark_current_cache_as_stale(source_cache, config)

    bad_csv = b"REGION_CODE;ONLY_ONE_COLUMN\n84;bad\n"
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(bad_csv)):
        with pytest.raises((pa.ArrowInvalid, pa.lib.ArrowKeyError)):
            loader.download(config)
