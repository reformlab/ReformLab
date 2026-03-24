# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Network integration tests for the Eurostat data source loader.

These tests download real data from Eurostat SDMX API and validate
schema and basic structure. They are excluded from CI by default
(require ``pytest -m network``).

Implements Story 11.3 (Implement Eurostat, ADEME, SDES data source loaders).
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.eurostat import (
    get_eurostat_loader,
    make_eurostat_config,
)


@pytest.mark.network()
class TestEurostatNetworkDownload:
    """Real network downloads from Eurostat SDMX API."""

    def test_ilc_di01_download(self, source_cache: SourceCache) -> None:
        """Download ilc_di01 (income distribution, ~75 KB compressed)."""
        loader = get_eurostat_loader("ilc_di01", cache=source_cache)
        config = make_eurostat_config("ilc_di01")
        pop, manifest = loader.download(config)
        table = pop.primary_table

        assert isinstance(table, pa.Table)
        assert table.num_rows > 100
        assert table.schema.equals(loader.schema())

        # Verify France data exists
        countries = table.column("country").to_pylist()
        assert "FR" in countries

    def test_nrg_d_hhq_download(self, source_cache: SourceCache) -> None:
        """Download nrg_d_hhq (household energy consumption)."""
        loader = get_eurostat_loader("nrg_d_hhq", cache=source_cache)
        config = make_eurostat_config("nrg_d_hhq")
        pop, manifest = loader.download(config)
        table = pop.primary_table

        assert isinstance(table, pa.Table)
        assert table.num_rows > 100
        assert table.schema.equals(loader.schema())
