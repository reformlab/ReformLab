# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Exogenous asset loader for bundled time series data.

Story 21.6 / AC7, Task 7.

This module provides load_exogenous_asset() for loading exogenous time series
assets from disk. Each asset is stored in data/exogenous/{series_name}/ with
descriptor.json, values.json (simple series), and metadata.json files.

Security hardening follows the pattern from Story 21.5:
- Path traversal protection (rejects "/", "\", ".." in series_name)
- Symlink attack protection (resolves and verifies containment)
- Clear error messages for all failure modes
"""

from __future__ import annotations

import json
from pathlib import Path

from reformlab.data.assets import ExogenousAsset
from reformlab.data.descriptor import DataAssetDescriptor
from reformlab.data.errors import EvidenceAssetError

# Base path for exogenous asset folders
_EXOGENOUS_ASSETS_BASE_PATH = Path("data/exogenous")


def load_exogenous_asset(series_name: str) -> ExogenousAsset:
    """Load an exogenous asset from disk by series_name.

    Reads the asset folder at ``data/exogenous/{series_name}/`` which contains
    ``descriptor.json``, ``values.json``, and ``metadata.json``.

    Story 21.6 / AC7, Task 7.

    Parameters
    ----------
    series_name : str
        Series identifier for the exogenous asset (e.g., "energy_price_electricity").

    Returns
    -------
    ExogenousAsset
        Immutable exogenous asset instance loaded from disk.

    Raises
    ------
    EvidenceAssetError
        If the asset folder does not exist, required files are missing,
        or validation fails.
    """
    # Security: Validate series_name to prevent path traversal attacks
    if "/" in series_name or "\\" in series_name or ".." in series_name:
        raise EvidenceAssetError(
            f"Exogenous series_name contains invalid path characters: {series_name!r}"
        )

    asset_path = _EXOGENOUS_ASSETS_BASE_PATH / series_name

    # Check asset folder exists
    if not asset_path.exists():
        raise EvidenceAssetError(
            f"Exogenous asset folder does not exist: {asset_path}"
        )
    if not asset_path.is_dir():
        raise EvidenceAssetError(
            f"Exogenous asset path is not a directory: {asset_path}"
        )

    # Security: Resolve path and verify it's within base path (prevent symlink attacks)
    try:
        resolved_path = asset_path.resolve()
        base_resolved = _EXOGENOUS_ASSETS_BASE_PATH.resolve()
        if not str(resolved_path).startswith(str(base_resolved)):
            raise EvidenceAssetError(
                f"Exogenous asset path is outside base directory: {asset_path}"
            )
    except OSError as exc:
        raise EvidenceAssetError(
            f"Failed to resolve exogenous asset path: {exc}"
        ) from exc

    # Load descriptor.json
    descriptor_path = asset_path / "descriptor.json"
    if not descriptor_path.exists():
        raise EvidenceAssetError(
            f"Exogenous asset missing required file: {descriptor_path}"
        )

    try:
        with descriptor_path.open("r", encoding="utf-8") as f:
            descriptor_data = json.load(f)
        descriptor = DataAssetDescriptor.from_json(descriptor_data)
    except (json.JSONDecodeError, OSError) as exc:
        raise EvidenceAssetError(
            f"Failed to load descriptor.json: {exc}"
        ) from exc

    # Load values.json
    values_path = asset_path / "values.json"
    if not values_path.exists():
        raise EvidenceAssetError(
            f"Exogenous asset missing required file: {values_path}"
        )

    try:
        with values_path.open("r", encoding="utf-8") as f:
            values_raw = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise EvidenceAssetError(
            f"Failed to load values.json: {exc}"
        ) from exc

    # Validate and convert values (JSON has string year keys)
    if not isinstance(values_raw, dict):
        raise EvidenceAssetError(
            f"values.json must be an object - got {type(values_raw).__name__}"
        )

    values: dict[int, float] = {}
    for year_str, value in values_raw.items():
        try:
            year = int(year_str)
        except (ValueError, TypeError) as exc:
            raise EvidenceAssetError(
                f"values.json key {year_str!r} is not a valid year"
            ) from exc
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise EvidenceAssetError(
                f"values.json year {year} has invalid value type "
                f"{type(value).__name__} - expected number"
            )
        values[year] = float(value)

    # Load metadata.json
    metadata_path = asset_path / "metadata.json"
    if not metadata_path.exists():
        raise EvidenceAssetError(
            f"Exogenous asset missing required file: {metadata_path}"
        )

    try:
        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise EvidenceAssetError(
            f"Failed to load metadata.json: {exc}"
        ) from exc

    if not isinstance(metadata, dict):
        raise EvidenceAssetError(
            f"metadata.json must be an object - got {type(metadata).__name__}"
        )

    # Extract required metadata fields
    unit = metadata.get("unit")
    if not isinstance(unit, str):
        raise EvidenceAssetError(
            f"metadata.json 'unit' must be a string - got {type(unit).__name__}"
        )

    # Extract optional metadata fields with defaults
    frequency = metadata.get("frequency", "annual")
    if not isinstance(frequency, str):
        raise EvidenceAssetError(
            f"metadata.json 'frequency' must be a string - got {type(frequency).__name__}"
        )

    source = metadata.get("source", "")
    if source is not None and not isinstance(source, str):
        raise EvidenceAssetError(
            f"metadata.json 'source' must be a string or null - got {type(source).__name__}"
        )

    vintage = metadata.get("vintage", "")
    if vintage is not None and not isinstance(vintage, str):
        raise EvidenceAssetError(
            f"metadata.json 'vintage' must be a string or null - got {type(vintage).__name__}"
        )

    interpolation_method = metadata.get("interpolation_method", "linear")
    if not isinstance(interpolation_method, str):
        raise EvidenceAssetError(
            f"metadata.json 'interpolation_method' must be a string - got "
            f"{type(interpolation_method).__name__}"
        )

    aggregation_method = metadata.get("aggregation_method", "mean")
    if not isinstance(aggregation_method, str):
        raise EvidenceAssetError(
            f"metadata.json 'aggregation_method' must be a string - got {type(aggregation_method).__name__}"
        )

    revision_policy = metadata.get("revision_policy", "")
    if revision_policy is not None and not isinstance(revision_policy, str):
        raise EvidenceAssetError(
            f"metadata.json 'revision_policy' must be a string or null - got {type(revision_policy).__name__}"
        )

    # Construct ExogenousAsset (validates data_class and other constraints)
    return ExogenousAsset(
        descriptor=descriptor,
        name=series_name,
        values=values,
        unit=unit,
        frequency=frequency,
        source=source if source is not None else "",
        vintage=vintage if vintage is not None else "",
        interpolation_method=interpolation_method,
        aggregation_method=aggregation_method,
        revision_policy=revision_policy if revision_policy is not None else "",
    )
