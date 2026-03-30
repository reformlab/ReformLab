# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Exogenous time series asset routes — Story 21.6, AC8."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

import reformlab.data.exogenous_loader as exogenous_loader
from reformlab.data.descriptor import (
    DataAssetOrigin,
)
from reformlab.data.errors import EvidenceAssetError
from reformlab.server.models import (
    ExogenousAssetRequest,
    ExogenousAssetResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _asset_to_response(asset: Any) -> ExogenousAssetResponse:
    """Convert an ExogenousAsset domain object to ExogenousAssetResponse.

    Parameters
    ----------
    asset : ExogenousAsset
        The domain asset object.

    Returns
    -------
    ExogenousAssetResponse
        Pydantic response model.
    """
    descriptor = asset.descriptor

    # Convert origin/access_mode/trust_status to strings for JSON serialization
    origin_str: str = descriptor.origin
    access_mode_str: str = descriptor.access_mode
    trust_status_str: str = descriptor.trust_status

    return ExogenousAssetResponse(
        # Descriptor fields
        asset_id=descriptor.asset_id,
        name=descriptor.name,
        description=descriptor.description,
        data_class="exogenous",
        origin=origin_str,  # type: ignore[arg-type]
        access_mode=access_mode_str,  # type: ignore[arg-type]
        trust_status=trust_status_str,  # type: ignore[arg-type]
        source_url=descriptor.source_url,
        license=descriptor.license,
        version=descriptor.version,
        geographic_coverage=list(descriptor.geographic_coverage),
        years=list(descriptor.years),
        intended_use=descriptor.intended_use,
        redistribution_allowed=descriptor.redistribution_allowed,
        redistribution_notes=descriptor.redistribution_notes,
        update_cadence=descriptor.update_cadence,
        quality_notes=descriptor.quality_notes,
        references=list(descriptor.references),
        # Exogenous-specific fields
        unit=asset.unit,
        values=asset.values,
        frequency=asset.frequency,
        source=asset.source,
        vintage=asset.vintage,
        interpolation_method=asset.interpolation_method,
        aggregation_method=asset.aggregation_method,
        revision_policy=asset.revision_policy,
    )


def _list_asset_folders() -> list[str]:
    """List all exogenous asset folders in the data directory.

    Returns
    -------
    list[str]
        List of series names (folder names) that exist in data/exogenous/.
    """
    base_path = exogenous_loader._EXOGENOUS_ASSETS_BASE_PATH
    if not base_path.exists():
        return []

    series_names: list[str] = []
    for entry in base_path.iterdir():
        if entry.is_dir() and not entry.name.startswith("_"):
            # Check for required files
            descriptor_path = entry / "descriptor.json"
            values_path = entry / "values.json"
            metadata_path = entry / "metadata.json"
            if all(p.exists() for p in [descriptor_path, values_path, metadata_path]):
                series_names.append(entry.name)

    return sorted(series_names)


@router.get("/series", response_model=list[ExogenousAssetResponse], tags=["exogenous"])
async def list_exogenous_series(
    origin: DataAssetOrigin | None = Query(None, description="Filter by origin"),
    unit: str | None = Query(None, description="Filter by unit (exact match)"),
    source: str | None = Query(None, description="Filter by source (substring match)"),
) -> list[ExogenousAssetResponse]:
    """List all available exogenous time series assets.

    Story 21.6 / AC8.

    Args
    ----
    origin : Optional[DataAssetOrigin]
        Filter by data origin (open-official, open-third-party, proprietary).
    unit : Optional[str]
        Filter by unit (exact match, e.g., "EUR/kWh").
    source : Optional[str]
        Filter by source (substring match, e.g., "Eurostat").

    Returns
    -------
    list[ExogenousAssetResponse]
        List of all exogenous assets (optionally filtered).
    """
    series_names = _list_asset_folders()
    assets: list[ExogenousAssetResponse] = []

    for series_name in series_names:
        try:
            asset = exogenous_loader.load_exogenous_asset(series_name)
            response = _asset_to_response(asset)

            # Apply filters
            if origin is not None and response.origin != origin:
                continue
            if unit is not None and response.unit != unit:
                continue
            if source is not None and source.lower() not in response.source.lower():
                continue

            assets.append(response)
        except EvidenceAssetError as exc:
            # Log but skip assets that fail to load
            logger.warning("Failed to load exogenous asset '%s': %s", series_name, exc)

    return assets


@router.get(
    "/series/{series_name}",
    response_model=ExogenousAssetResponse,
    tags=["exogenous"],
)
async def get_exogenous_series(series_name: str) -> ExogenousAssetResponse:
    """Get a specific exogenous time series asset by name.

    Story 21.6 / AC8.

    Args
    ----
    series_name : str
        The series name (e.g., "energy_price_electricity").

    Returns
    -------
    ExogenousAssetResponse
        The requested exogenous asset.

    Raises
    ------
    HTTPException
        404 if the asset does not exist.
    """
    try:
        asset = exogenous_loader.load_exogenous_asset(series_name)
        return _asset_to_response(asset)
    except EvidenceAssetError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Exogenous asset not found: {series_name}",
                "why": str(exc),
                "fix": "Check the series name is correct and the asset files exist in data/exogenous/.",
            },
        ) from exc


@router.post(
    "/series",
    response_model=ExogenousAssetResponse,
    tags=["exogenous"],
)
async def create_exogenous_series(request: ExogenousAssetRequest) -> ExogenousAssetResponse:
    """Create a new exogenous time series asset.

    Story 21.6 / AC8.

    Args
    ----
    request : ExogenousAssetRequest
        The asset creation request with descriptor and data.

    Returns
    -------
    ExogenousAssetResponse
        The created asset.

    Raises
    ------
    HTTPException
        400 if validation fails, 409 if asset already exists.
    """
    # Security: Validate series_name to prevent path traversal
    series_name = request.name
    if "/" in series_name or "\\" in series_name or ".." in series_name:
        raise HTTPException(
            status_code=400,
            detail={
                "what": f"Invalid series name: {series_name}",
                "why": "Series name cannot contain '/', '\\', or '..'",
                "fix": "Use a simple identifier like 'energy_price_electricity'",
            },
        )

    asset_path = exogenous_loader._EXOGENOUS_ASSETS_BASE_PATH / series_name

    # Check if asset already exists
    if asset_path.exists():
        raise HTTPException(
            status_code=409,
            detail={
                "what": f"Exogenous asset already exists: {series_name}",
                "why": "An asset with this name already exists in data/exogenous/",
                "fix": "Use a different name or delete the existing asset first",
            },
        )

    try:
        # Create asset folder
        asset_path.mkdir(parents=True, exist_ok=True)

        # Write descriptor.json
        descriptor_data = {
            "asset_id": series_name,
            "name": request.name,
            "description": request.description,
            "data_class": "exogenous",
            "origin": request.origin,
            "access_mode": request.access_mode,
            "trust_status": request.trust_status,
            "source_url": request.source_url,
            "license": request.license,
            "version": request.version,
            "geographic_coverage": request.geographic_coverage,
            "years": request.years,
            "intended_use": request.intended_use,
            "redistribution_allowed": request.redistribution_allowed,
            "redistribution_notes": request.redistribution_notes,
            "update_cadence": request.update_cadence,
            "quality_notes": request.quality_notes,
            "references": request.references,
        }
        with (asset_path / "descriptor.json").open("w", encoding="utf-8") as f:
            json.dump(descriptor_data, f, indent=2)

        # Write values.json (values have string year keys in JSON)
        with (asset_path / "values.json").open("w", encoding="utf-8") as f:
            json.dump(request.values, f, indent=2)

        # Write metadata.json
        metadata_data = {
            "unit": request.unit,
            "frequency": request.frequency,
            "source": request.source,
            "vintage": request.vintage,
            "interpolation_method": request.interpolation_method,
            "aggregation_method": request.aggregation_method,
            "revision_policy": request.revision_policy,
        }
        with (asset_path / "metadata.json").open("w", encoding="utf-8") as f:
            json.dump(metadata_data, f, indent=2)

        # Load and return the created asset
        asset = exogenous_loader.load_exogenous_asset(series_name)
        return _asset_to_response(asset)

    except (OSError, json.JSONDecodeError) as exc:
        # Cleanup on failure
        try:
            if asset_path.exists():
                for p in asset_path.iterdir():
                    p.unlink()
                asset_path.rmdir()
        except OSError:
            pass

        raise HTTPException(
            status_code=400,
            detail={
                "what": "Failed to create exogenous asset",
                "why": str(exc),
                "fix": "Check the request data is valid and the file system is writable",
            },
        ) from exc
    except EvidenceAssetError as exc:
        # Validation error from domain layer
        raise HTTPException(
            status_code=400,
            detail={
                "what": "Exogenous asset validation failed",
                "why": str(exc),
                "fix": "Check all required fields are provided and values are valid",
            },
        ) from exc
