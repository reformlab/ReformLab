# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for DatasetDescriptor integration with concrete loaders.

Verifies that each loader's descriptor() method returns a valid
DatasetDescriptor with correct metadata.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reformlab.data.descriptor import DatasetDescriptor
from reformlab.population.loaders.ademe import get_ademe_loader
from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.eurostat import get_eurostat_loader
from reformlab.population.loaders.insee import get_insee_loader
from reformlab.population.loaders.sdes import get_sdes_loader


@pytest.fixture()
def source_cache(tmp_path: Path) -> SourceCache:
    return SourceCache(cache_root=tmp_path / "cache")


class TestINSEEDescriptor:
    def test_descriptor_returns_dataset_descriptor(self, source_cache: SourceCache) -> None:
        loader = get_insee_loader("filosofi_2021_commune", cache=source_cache)
        desc = loader.descriptor()
        assert isinstance(desc, DatasetDescriptor)
        assert desc.dataset_id == "filosofi_2021_commune"
        assert desc.provider == "insee"
        assert desc.url.startswith("https://")
        assert len(desc.column_mapping) > 0
        assert len(desc.schema.required_columns) > 0


class TestEurostatDescriptor:
    def test_descriptor_returns_dataset_descriptor(self, source_cache: SourceCache) -> None:
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        desc = loader.descriptor()
        assert isinstance(desc, DatasetDescriptor)
        assert desc.dataset_id == "ilc_di01"
        assert desc.provider == "eurostat"
        assert desc.file_format == "csv.gz"


class TestADEMEDescriptor:
    def test_descriptor_returns_dataset_descriptor(self, source_cache: SourceCache) -> None:
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        desc = loader.descriptor()
        assert isinstance(desc, DatasetDescriptor)
        assert desc.dataset_id == "base_carbone"
        assert desc.provider == "ademe"
        assert desc.encoding == "windows-1252"


class TestSDESDescriptor:
    def test_descriptor_returns_dataset_descriptor(self, source_cache: SourceCache) -> None:
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        desc = loader.descriptor()
        assert isinstance(desc, DatasetDescriptor)
        assert desc.dataset_id == "vehicle_fleet"
        assert desc.provider == "sdes"
        assert desc.separator == ";"
