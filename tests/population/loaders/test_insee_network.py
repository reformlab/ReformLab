# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Network integration tests for the INSEE data source loader.

These tests hit real INSEE servers and are excluded from CI by default.
Run with: ``uv run pytest -m network tests/population/loaders/test_insee_network.py``

Implements Story 11.2 (Implement INSEE data source loader).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reformlab.population.loaders.cache import SourceCache
from reformlab.population.loaders.insee import get_insee_loader, make_insee_config


@pytest.mark.network
class TestINSEELoaderRealDownload:
    """Integration tests that download real INSEE data."""

    def test_filosofi_commune_real_download(self, tmp_path: Path) -> None:
        """Given a real INSEE URL, when downloaded, then returns valid table."""
        cache = SourceCache(cache_root=tmp_path / "cache")
        loader = get_insee_loader("filosofi_2021_commune", cache=cache)
        config = make_insee_config("filosofi_2021_commune")

        table = loader.download(config)

        # Filosofi commune-level should have thousands of communes
        assert table.num_rows > 30000
        assert "commune_code" in table.schema.names
        assert "median_income" in table.schema.names
        assert table.schema.equals(loader.schema())
