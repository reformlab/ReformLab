# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Synthetic asset registry for bundled public synthetic datasets.

Story 21.4 - add-public-synthetic-asset-ingestion-and-observed-versus-synthetic-comparison-flows.

This module provides a registry for cataloging bundled public synthetic datasets.
Each synthetic asset is represented as a StructuralAsset with a DataAssetDescriptor
governance envelope specifying origin="synthetic-public", access_mode="bundled",
and trust_status="exploratory" (or other appropriate trust status).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import pyarrow as pa

from reformlab.data.assets import (
    StructuralAsset,
    create_structural_asset,
)

# Registry singleton instance
_registry: SyntheticAssetRegistry | None = None


def get_synthetic_registry() -> SyntheticAssetRegistry:
    """Get the singleton synthetic asset registry instance.

    Creates and initializes the registry on first call, then returns
    the same instance on subsequent calls.

    Returns
    -------
    SyntheticAssetRegistry
        The global synthetic asset registry with bundled assets pre-registered.
    """
    global _registry
    if _registry is None:
        _registry = SyntheticAssetRegistry()
        _initialize_bundled_assets(_registry)
    return _registry


def _initialize_bundled_assets(registry: SyntheticAssetRegistry) -> None:
    """Register bundled synthetic assets — Story 21.4 / AC7.

    This function is called once during registry initialization to register
    all synthetic datasets bundled with the product.

    Currently bundled assets:
    - fr-synthetic-2024: 100k French synthetic households for benchmarking

    The actual data files are stored in data/populations/fr-synthetic-2024/.
    """
    # Create a minimal empty table for the catalog entry
    # The full data is loaded separately via the ingestion pipeline
    _empty_table = pa.table({"_catalog": pa.array([], type=pa.string())})

    # Register fr-synthetic-2024 synthetic population
    asset = create_structural_asset(
        # Descriptor fields
        asset_id="fr-synthetic-2024",
        name="French Synthetic Population 2024",
        description=(
            "100k synthetic households for France - exploratory use only. "
            "Generated deterministically with seed=42 for benchmarking and "
            "scale validation. Not for production decision support."
        ),
        origin="synthetic-public",
        access_mode="bundled",
        trust_status="exploratory",
        # Structural-specific fields
        table=_empty_table,
        entity_type="household",
        record_count=0,  # Placeholder; actual count from data file
        primary_key="household_id",
        # Optional descriptor fields
        source_url="",
        license="AGPL-3.0-or-later",
        version="1.0.0",
        geographic_coverage=("FR",),
        years=(2024,),
        intended_use=(
            "Benchmarking, scale validation, and exploratory analysis. "
            "Not suitable for production decision support."
        ),
        redistribution_allowed=True,
        redistribution_notes=(
            "Redistribution permitted under AGPL-3.0-or-later. "
            "Users must retain exploratory trust status labeling."
        ),
        update_cadence="",
        quality_notes=(
            "Synthetic data with deterministic generation (seed=42). "
            "Income distribution: 15k-95k EUR with linear ramp. "
            "Age: uniform 20-80. Energy values correlated with income."
        ),
        references=(),
    )
    registry.register(asset)


@dataclass(frozen=True)
class SyntheticAssetRegistry:
    """Mutable registry for bundled synthetic asset descriptors.

    The registry catalogs StructuralAsset instances representing synthetic
    populations bundled with the product. Each asset has a DataAssetDescriptor
    with origin="synthetic-public" and appropriate governance metadata.

    The registry is append-only by asset_id. Attempting to register a duplicate
    asset_id raises ValueError.

    Story 21.4 / AC1.
    """

    def __post_init__(self) -> None:
        """Initialize the registry storage."""
        object.__setattr__(self, "_assets", {})

    def register(self, asset: StructuralAsset) -> None:
        """Register a synthetic asset.

        Parameters
        ----------
        asset : StructuralAsset
            The synthetic asset to register. Must have descriptor.asset_id
            and descriptor.origin == "synthetic-public".

        Raises
        ------
        ValueError
            If an asset with the same asset_id is already registered.
        """
        asset_id = asset.descriptor.asset_id
        assets = cast(dict[str, StructuralAsset], object.__getattribute__(self, "_assets"))
        if asset_id in assets:
            raise ValueError(
                f"Asset {asset_id!r} is already registered in the synthetic "
                f"asset registry - each asset_id must be unique"
            )
        assets[asset_id] = asset

    def get(self, asset_id: str) -> StructuralAsset | None:
        """Retrieve a registered asset by ID.

        Parameters
        ----------
        asset_id : str
            The unique identifier of the asset to retrieve.

        Returns
        -------
        StructuralAsset | None
            The registered asset, or None if not found.
        """
        assets = cast(dict[str, StructuralAsset], object.__getattribute__(self, "_assets"))
        return assets.get(asset_id)

    def list_all(self) -> tuple[StructuralAsset, ...]:
        """Return all registered synthetic assets.

        Returns
        -------
        tuple[StructuralAsset, ...]
            A tuple of all registered assets. Returns a copy to prevent
            external mutation of the registry.
        """
        assets = cast(dict[str, StructuralAsset], object.__getattribute__(self, "_assets"))
        # Create a new tuple each call to ensure we don't return the same object
        return tuple(dict(assets).values())
