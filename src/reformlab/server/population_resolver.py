# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Unified population resolver for the ReformLab server — Story 23.2.

Resolves population identifiers to executable datasets across three sources:
  1. Bundled populations (``data/populations/``)
  2. Uploaded populations (``~/.reformlab/uploaded-populations/``)
  3. Generated populations (bundled path + ``.manifest.json`` sidecar)

Resolution order: bundled → uploaded → generated (bundled shadows uploaded on
duplicate IDs, matching the existing behaviour in ``populations.py``).

FR-RUNTIME-3: Bundled, uploaded, and generated populations are executable
through the same live runtime contract.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Supported data file extensions, ordered by preference (Parquet first for
# performance; CSV as fallback).  A tuple guarantees deterministic resolution
# order regardless of PYTHONHASHSEED — required by the project determinism rule.
_DATA_EXTENSIONS: tuple[str, ...] = (".parquet", ".csv")

# Canonical source type
PopulationSource = Literal["bundled", "uploaded", "generated"]


# ---------------------------------------------------------------------------
# Domain types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResolvedPopulation:
    """Result of a successful population resolution.

    Attributes:
        population_id: The original identifier that was resolved.
        source: Which source class the population came from.
        data_path: Absolute path to the CSV or Parquet file to execute.
        row_count: Row count if known at resolution time, else None.
        metadata: Additional metadata from descriptor/manifest files.
    """

    population_id: str
    source: PopulationSource
    data_path: Path
    row_count: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class PopulationResolutionError(Exception):
    """Raised when a population_id cannot be resolved to an executable dataset.

    The first ``args`` element is a ``{"what", "why", "fix"}`` detail dict
    suitable for passing directly to ``HTTPException(detail=...)``.

    Attributes:
        population_id: The identifier that could not be resolved.
        available_ids: Sorted list of IDs that *are* available (for UX).
    """

    def __init__(
        self,
        population_id: str,
        available_ids: list[str] | None = None,
        *,
        reason: str | None = None,
    ) -> None:
        self.population_id = population_id
        self.available_ids: list[str] = available_ids or []

        what = f"Population '{population_id}' not found"
        if reason:
            why = reason
        else:
            ids_preview = self.available_ids[:10]
            ids_str = ", ".join(ids_preview) if ids_preview else "(none)"
            suffix = f" … and {len(self.available_ids) - 10} more" if len(self.available_ids) > 10 else ""
            why = (
                f"Checked bundled, uploaded, and generated sources. "
                f"Available: {ids_str}{suffix}"
            )
        fix = "Select a valid population ID from the available populations"

        super().__init__({"what": what, "why": why, "fix": fix})


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------


class PopulationResolver:
    """Resolve population IDs to executable datasets across all sources.

    Checks sources in priority order: bundled → uploaded → generated.
    Within each source, CSV and Parquet are both accepted.
    Folder-based populations (directory containing ``descriptor.json``) are
    supported for the bundled source.

    Args:
        data_dir: Path to the bundled populations directory
            (``data/populations/``).
        uploaded_dir: Path to the uploaded populations directory
            (``~/.reformlab/uploaded-populations/``).
    """

    def __init__(self, data_dir: Path, uploaded_dir: Path) -> None:
        self._data_dir = data_dir
        self._uploaded_dir = uploaded_dir

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self, population_id: str) -> ResolvedPopulation:
        """Resolve a population ID to its executable dataset.

        Checks sources in order:
        1. ``data/populations/`` (bundled or generated — manifest sidecar
           determines which classification is returned)
        2. Uploaded populations directory

        Args:
            population_id: The identifier to look up.

        Returns:
            A :class:`ResolvedPopulation` with the data path and source
            classification.

        Raises:
            PopulationResolutionError: If not found in any source.
        """
        # Guard against path traversal and empty/invalid IDs
        if (
            not population_id
            or "/" in population_id
            or "\\" in population_id
            or ".." in population_id
        ):
            raise PopulationResolutionError(
                population_id,
                reason=f"Population ID '{population_id}' contains invalid characters",
            )

        # 1. Data dir: bundled or generated (manifest sidecar distinguishes)
        resolved = self._resolve_bundled(population_id)
        if resolved is not None:
            return resolved

        # 2. Uploaded
        resolved = self._resolve_uploaded(population_id)
        if resolved is not None:
            return resolved

        available = self._list_available_ids()
        raise PopulationResolutionError(population_id, available)

    def _list_available_ids(self) -> list[str]:
        """Return a sorted list of all discoverable population IDs."""
        ids: set[str] = set()

        for directory in (self._data_dir, self._uploaded_dir):
            if not directory.exists():
                continue
            for path in directory.iterdir():
                if path.suffix.lower() in _DATA_EXTENSIONS:
                    ids.add(path.stem)
                elif path.is_dir():
                    # Folder-based populations: count if descriptor.json exists
                    if (path / "descriptor.json").exists():
                        ids.add(path.name)

        return sorted(ids)

    # ------------------------------------------------------------------
    # Private resolution helpers
    # ------------------------------------------------------------------

    def _resolve_bundled(self, population_id: str) -> ResolvedPopulation | None:
        """Check ``data/populations/`` for a bundled or generated population.

        Supports both single-file (``{id}.csv``) and folder-based
        (``{id}/descriptor.json``) formats.

        If a ``{id}.manifest.json`` sidecar exists next to the data file, the
        population is classified as ``"generated"`` rather than ``"bundled"``.
        This mirrors the classification logic in ``populations.py``.
        """
        if not self._data_dir.exists():
            return None

        # Single-file format
        for ext in _DATA_EXTENSIONS:
            path = self._data_dir / f"{population_id}{ext}"
            if path.exists():
                # Check for manifest sidecar → generated classification
                manifest_sidecar = self._data_dir / f"{population_id}.manifest.json"
                source: PopulationSource = "generated" if manifest_sidecar.exists() else "bundled"
                return ResolvedPopulation(
                    population_id=population_id,
                    source=source,
                    data_path=path,
                )

        # Folder format: data_dir/{id}/descriptor.json
        folder = self._data_dir / population_id
        if folder.is_dir():
            return self._load_folder_population(folder, population_id, "bundled")

        return None

    def _resolve_uploaded(self, population_id: str) -> ResolvedPopulation | None:
        """Check the uploaded populations directory."""
        if not self._uploaded_dir.exists():
            return None

        for ext in _DATA_EXTENSIONS:
            path = self._uploaded_dir / f"{population_id}{ext}"
            if path.exists():
                return ResolvedPopulation(
                    population_id=population_id,
                    source="uploaded",
                    data_path=path,
                )

        return None

    def _load_folder_population(
        self,
        folder_path: Path,
        population_id: str,
        source: PopulationSource,
    ) -> ResolvedPopulation | None:
        """Resolve a folder-based population via ``descriptor.json``.

        The descriptor must contain a ``"data_file"`` key pointing to a
        file inside the folder.  Returns ``None`` on any parse error so the
        caller can continue trying other sources.
        """
        descriptor_path = folder_path / "descriptor.json"
        if not descriptor_path.exists():
            return None

        try:
            descriptor: dict[str, Any] = json.loads(descriptor_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            logger.warning(
                "event=folder_descriptor_unreadable population_id=%s path=%s",
                population_id,
                descriptor_path,
            )
            return None

        data_file = descriptor.get("data_file")
        if not data_file:
            return None

        data_path = (folder_path / data_file).resolve()
        # Ensure data_file stays within the folder (prevent traversal via descriptor)
        if not data_path.is_relative_to(folder_path.resolve()):
            logger.warning(
                "event=folder_descriptor_traversal population_id=%s data_file=%s",
                population_id,
                data_file,
            )
            return None
        if not data_path.exists():
            return None

        return ResolvedPopulation(
            population_id=population_id,
            source=source,
            data_path=data_path,
            metadata=descriptor,
        )
