# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Network integration tests for the SDES data source loader.

These tests download real data from data.gouv.fr and validate
schema and basic structure. They are excluded from CI by default
(require ``pytest -m network``).

Implements Story 11.3 (Implement Eurostat, ADEME, SDES data source loaders).
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.sdes import (
    get_sdes_loader,
    make_sdes_config,
)


@pytest.mark.network()
class TestSDESNetworkDownload:
    """Real network downloads from data.gouv.fr."""

    def test_vehicle_fleet_download(self, source_cache: SourceCache) -> None:
        """Download vehicle fleet data (~10 MB)."""
        loader = get_sdes_loader("vehicle_fleet", cache=source_cache)
        config = make_sdes_config("vehicle_fleet")
        pop, manifest = loader.download(config)
        table = pop.primary_table

        assert isinstance(table, pa.Table)
        assert table.num_rows > 1000
        assert table.schema.equals(loader.schema())

        # Verify fleet data has expected fuel types
        fuels = set(table.column("fuel_type").to_pylist())
        assert len(fuels) > 1
