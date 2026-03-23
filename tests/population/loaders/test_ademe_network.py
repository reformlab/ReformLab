# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Network integration tests for the ADEME data source loader.

These tests download real data from data.gouv.fr and validate
schema and basic structure. They are excluded from CI by default
(require ``pytest -m network``).

Implements Story 11.3 (Implement Eurostat, ADEME, SDES data source loaders).
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.population.loaders.ademe import (
    get_ademe_loader,
    make_ademe_config,
)
from reformlab.population.loaders.cache import SourceCache


@pytest.mark.network()
class TestADEMENetworkDownload:
    """Real network downloads from data.gouv.fr."""

    def test_base_carbone_download(self, source_cache: SourceCache) -> None:
        """Download Base Carbone (~10 MB)."""
        loader = get_ademe_loader("base_carbone", cache=source_cache)
        config = make_ademe_config("base_carbone")
        table = loader.download(config)

        assert isinstance(table, pa.Table)
        assert table.num_rows > 1000
        assert table.schema.equals(loader.schema())

        # Verify emission factor data exists
        names = table.column("name_fr").to_pylist()
        assert any("naturel" in str(n).lower() for n in names)
