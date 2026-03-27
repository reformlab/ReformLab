# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for SyntheticAssetRegistry — Story 21.4.

Tests cover:
- Registry initialization with bundled synthetic populations
- Asset registration and retrieval
- Listing all registered assets
- Duplicate key rejection
"""

from __future__ import annotations

import pytest
import pyarrow as pa

from reformlab.data import create_structural_asset
from reformlab.data.synthetic_catalog import (
    SyntheticAssetRegistry,
    get_synthetic_registry,
)


class TestSyntheticAssetRegistry:
    """Test SyntheticAssetRegistry core functionality — Story 21.4 / AC1, AC7."""

    def test_registry_initialization(self) -> None:
        """Registry initializes with bundled synthetic populations — AC1, AC7."""
        registry = get_synthetic_registry()  # Use singleton to get bundled assets
        assets = registry.list_all()
        assert len(assets) > 0, "Registry should have at least one bundled asset"
        asset_ids = [a.descriptor.asset_id for a in assets]
        assert "fr-synthetic-2024" in asset_ids, "fr-synthetic-2024 should be bundled"

    def test_get_registered_asset(self) -> None:
        """Retrieve a registered asset by ID — AC1."""
        registry = get_synthetic_registry()  # Use singleton to get bundled assets
        asset = registry.get("fr-synthetic-2024")
        assert asset is not None, "Should retrieve fr-synthetic-2024"
        assert asset.descriptor.asset_id == "fr-synthetic-2024"
        assert asset.descriptor.origin == "synthetic-public"
        assert asset.descriptor.access_mode == "bundled"
        assert asset.descriptor.trust_status == "exploratory"

    def test_get_nonexistent_asset_returns_none(self) -> None:
        """Requesting unknown asset ID returns None — AC1."""
        registry = SyntheticAssetRegistry()
        asset = registry.get("nonexistent-asset")
        assert asset is None, "Unknown asset should return None"

    def test_list_all_returns_equal(self) -> None:
        """list_all returns equal results on repeated calls — AC1."""
        registry = SyntheticAssetRegistry()
        assets1 = registry.list_all()
        assets2 = registry.list_all()
        # Should be equal
        assert assets1 == assets2

    def test_register_duplicate_key_raises_error(self) -> None:
        """Registering duplicate asset_id raises ValueError — AC1."""
        # Use global registry which has fr-synthetic-2024 pre-registered
        registry = get_synthetic_registry()
        empty_table = pa.table({"_": pa.array([], type=pa.string())})
        asset = create_structural_asset(
            asset_id="fr-synthetic-2024",
            name="French Synthetic Population 2024",
            description="Duplicate entry",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
            table=empty_table,
            entity_type="household",
            record_count=0,
        )
        with pytest.raises(ValueError, match="already registered"):
            registry.register(asset)

    def test_register_new_asset(self) -> None:
        """Register a new synthetic asset — AC1."""
        registry = SyntheticAssetRegistry()
        empty_table = pa.table({"_": pa.array([], type=pa.string())})
        asset = create_structural_asset(
            asset_id="test-synthetic-2025",
            name="Test Synthetic 2025",
            description="Test synthetic population",
            origin="synthetic-public",
            access_mode="bundled",
            trust_status="exploratory",
            table=empty_table,
            entity_type="household",
            record_count=0,
        )
        registry.register(asset)
        retrieved = registry.get("test-synthetic-2025")
        assert retrieved is not None
        assert retrieved.descriptor.asset_id == "test-synthetic-2025"


class TestGetSyntheticRegistry:
    """Test module-level registry singleton."""

    def test_get_synthetic_registry_returns_singleton(self) -> None:
        """Module-level get_synthetic_registry returns singleton instance."""
        registry1 = get_synthetic_registry()
        registry2 = get_synthetic_registry()
        assert registry1 is registry2, "Should return same registry instance"

    def test_get_synthetic_registry_has_bundled_assets(self) -> None:
        """Global registry has bundled synthetic assets — AC7."""
        registry = get_synthetic_registry()
        assets = registry.list_all()
        assert len(assets) > 0
        asset_ids = [a.descriptor.asset_id for a in assets]
        assert "fr-synthetic-2024" in asset_ids
