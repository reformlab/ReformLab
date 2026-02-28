"""Population dataset listing routes."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import APIRouter

from reformlab.server.models import PopulationItem

logger = logging.getLogger(__name__)

router = APIRouter()

# Supported data file extensions
_DATA_EXTENSIONS = {".csv", ".parquet"}


def _scan_populations(data_dir: Path) -> list[PopulationItem]:
    """Scan a directory for population data files."""
    items: list[PopulationItem] = []

    if not data_dir.exists():
        return items

    for path in sorted(data_dir.iterdir()):
        if path.suffix.lower() not in _DATA_EXTENSIONS:
            continue

        # Derive metadata from filename convention:
        # e.g. "insee-households-2023-100k.csv"
        stem = path.stem
        parts = stem.split("-")

        source = parts[0] if parts else "unknown"
        year = 2025  # default
        households = 0

        for part in parts:
            # Try to parse year (4-digit number)
            if len(part) == 4 and part.isdigit():
                year = int(part)
            # Try to parse household count (e.g. "100k", "10000")
            elif part.endswith("k") and part[:-1].isdigit():
                households = int(part[:-1]) * 1000
            elif part.isdigit() and len(part) >= 3:
                households = int(part)

        items.append(
            PopulationItem(
                id=stem,
                name=stem.replace("-", " ").title(),
                households=households,
                source=source,
                year=year,
            )
        )

    return items


@router.get("", response_model=dict[str, list[PopulationItem]])
async def list_populations() -> dict[str, list[PopulationItem]]:
    """List available population datasets."""
    data_dir_env = os.environ.get("REFORMLAB_DATA_DIR", "data")
    data_dir = Path(data_dir_env) / "populations"

    populations = _scan_populations(data_dir)
    return {"populations": populations}
