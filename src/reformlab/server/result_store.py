# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Persistent result metadata storage for the ReformLab server.

Stores run metadata, panel data (Parquet), and manifest (JSON) on the
filesystem so past simulation runs are discoverable and loadable across
server restarts.

Storage layout:
    ~/.reformlab/results/{run_id}/metadata.json
    ~/.reformlab/results/{run_id}/panel.parquet   (Story 17.7)
    ~/.reformlab/results/{run_id}/manifest.json   (Story 17.7)

References: Story 17.3, Story 17.7, AC-2, AC-3
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.governance.manifest import RunManifest
    from reformlab.interfaces.api import SimulationResult
    from reformlab.orchestrator.panel import PanelOutput

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ResultStoreError(Exception):
    """Base exception for ResultStore operations."""


class ResultNotFound(ResultStoreError):
    """Raised when a run_id does not exist in the persistent store."""


# ---------------------------------------------------------------------------
# ResultMetadata dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ResultMetadata:
    """Metadata for a single simulation run.

    All timestamps are ISO 8601 UTC strings. Status is "completed" or "failed".
    """

    run_id: str
    timestamp: str  # ISO 8601 UTC — submission time
    run_kind: str  # "scenario" | "portfolio"
    start_year: int
    end_year: int
    population_id: str | None
    seed: int | None
    row_count: int  # 0 for failed runs
    manifest_id: str  # empty string for failed runs
    scenario_id: str  # empty string for failed runs
    adapter_version: str  # "unknown" for failed runs
    started_at: str  # ISO 8601 UTC — simulation start
    finished_at: str  # ISO 8601 UTC — simulation end
    status: str  # "completed" | "failed"
    template_name: str | None = None  # scenario runs only
    policy_type: str | None = None  # scenario runs only
    portfolio_name: str | None = None  # portfolio runs only
    portfolio_policy_count: int | None = None  # portfolio runs only
    portfolio_resolution_strategy: str | None = None  # portfolio runs only
    # Story 21.6 / AC6: Exogenous series fields for comparison dimension
    exogenous_series_hash: str | None = None  # SHA-256 hash of exogenous series
    exogenous_series_names: list[str] | None = None  # Series names for display
    # Story 23.1 / AC-4: Runtime mode from manifest ("live" or "replay")
    runtime_mode: str = "live"
    # Story 23.2 / AC-5: Population source classification from resolver
    population_source: str | None = None  # "bundled" | "uploaded" | "generated"


# ---------------------------------------------------------------------------
# ResultStore
# ---------------------------------------------------------------------------


class ResultStore:
    """Filesystem-backed persistent store for result metadata.

    Writes atomic metadata.json files under ~/.reformlab/results/{run_id}/.
    Full SimulationResult objects are NOT stored here; they remain in the
    in-memory ResultCache.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        """Initialise the store.

        Args:
            base_dir: Root directory for result storage.
                Defaults to ``~/.reformlab/results``.
        """
        if base_dir is None:
            base_dir = Path.home() / ".reformlab" / "results"
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_safe(self, run_id: str) -> Path:
        """Resolve the run directory path and guard against path traversal.

        Args:
            run_id: Caller-supplied run identifier.

        Returns:
            Resolved absolute path to the run directory.

        Raises:
            ResultStoreError: If the resolved path escapes the base directory.
        """
        run_dir = (self._base_dir / run_id).resolve()
        try:
            run_dir.relative_to(self._base_dir.resolve())
        except ValueError:
            raise ResultStoreError(f"Invalid run_id: {run_id!r}") from None
        return run_dir

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def save_metadata(self, run_id: str, metadata: ResultMetadata) -> None:
        """Atomically persist metadata for a run.

        Writes to a temp file then renames to prevent partial writes.

        Args:
            run_id: Unique run identifier (UUID).
            metadata: Run metadata to persist.
        """
        run_dir = self._resolve_safe(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        target = run_dir / "metadata.json"
        tmp = run_dir / ".metadata.json.tmp"

        data = asdict(metadata)
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        os.replace(tmp, target)

        logger.info(
            "event=metadata_saved run_id=%s status=%s",
            run_id,
            metadata.status,
        )

    # ------------------------------------------------------------------
    # Read — single
    # ------------------------------------------------------------------

    def get_metadata(self, run_id: str) -> ResultMetadata:
        """Load metadata for a single run.

        Args:
            run_id: Unique run identifier.

        Returns:
            ResultMetadata for the run.

        Raises:
            ResultNotFound: If the run directory or metadata file is missing.
        """
        run_dir = self._resolve_safe(run_id)
        metadata_path = run_dir / "metadata.json"

        if not run_dir.exists() or not metadata_path.exists():
            raise ResultNotFound(f"No metadata found for run_id={run_id!r}")

        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        return _dict_to_metadata(data)

    # ------------------------------------------------------------------
    # Read — list
    # ------------------------------------------------------------------

    def list_results(self) -> list[ResultMetadata]:
        """Return all stored results sorted by timestamp descending.

        Corrupt or missing entries are skipped with a warning.

        Returns:
            List of ResultMetadata sorted newest-first.
        """
        results: list[ResultMetadata] = []

        if not self._base_dir.exists():
            return results

        for run_dir in self._base_dir.iterdir():
            if not run_dir.is_dir():
                continue
            metadata_path = run_dir / "metadata.json"
            if not metadata_path.exists():
                continue
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                results.append(_dict_to_metadata(data))
            except Exception:
                logger.warning(
                    "level=WARNING event=corrupt_metadata run_id=%s",
                    run_dir.name,
                )

        # Sort by timestamp descending (parse as datetime for correct ordering)
        results.sort(
            key=lambda m: _parse_timestamp(m.timestamp),
            reverse=True,
        )
        return results

    # ------------------------------------------------------------------
    # Panel persistence (Story 17.7)
    # ------------------------------------------------------------------

    def save_panel(self, run_id: str, panel_output: PanelOutput) -> None:
        """Atomically persist panel data as Parquet.

        Encodes PanelOutput.metadata as JSON in the Parquet schema metadata
        so it survives the round-trip. Writes to a temp file then renames
        to prevent a crash mid-write from leaving a corrupt panel.parquet.

        Args:
            run_id: Unique run identifier.
            panel_output: Panel data to persist.
        """
        run_dir = self._resolve_safe(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        target = run_dir / "panel.parquet"
        tmp = run_dir / ".panel.parquet.tmp"
        schema_metadata: dict[str, str | bytes] = {
            "reformlab_panel_metadata": json.dumps(panel_output.metadata)
        }
        try:
            panel_output.to_parquet(tmp, schema_metadata=schema_metadata)
            os.replace(tmp, target)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
        logger.info("event=panel_saved run_id=%s", run_id)

    def save_manifest(self, run_id: str, manifest_json: str) -> None:
        """Atomically persist manifest as JSON.

        Args:
            run_id: Unique run identifier.
            manifest_json: Canonical JSON string from RunManifest.to_json().
        """
        run_dir = self._resolve_safe(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        target = run_dir / "manifest.json"
        tmp = run_dir / ".manifest.json.tmp"
        try:
            tmp.write_text(manifest_json, encoding="utf-8")
            os.replace(tmp, target)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise
        logger.info("event=manifest_saved run_id=%s", run_id)

    def has_panel(self, run_id: str) -> bool:
        """Return True if panel.parquet exists for this run.

        Only checks filesystem presence — does not load the file.

        Args:
            run_id: Unique run identifier.

        Returns:
            True if panel.parquet exists, False otherwise.
        """
        try:
            run_dir = self._resolve_safe(run_id)
        except ResultStoreError:
            return False
        return (run_dir / "panel.parquet").exists()

    # ------------------------------------------------------------------
    # Panel loading (Story 17.7)
    # ------------------------------------------------------------------

    def load_panel(self, run_id: str) -> PanelOutput:
        """Load panel data from disk.

        Reads panel.parquet and reconstructs PanelOutput including metadata
        stored in the Parquet schema metadata under 'reformlab_panel_metadata'.

        Args:
            run_id: Unique run identifier.

        Returns:
            PanelOutput with table and metadata.

        Raises:
            ResultNotFound: If panel.parquet does not exist.
            ResultStoreError: If the file is corrupt or unreadable.
        """
        import pyarrow.parquet as pq

        from reformlab.orchestrator.panel import PanelOutput

        run_dir = self._resolve_safe(run_id)
        panel_path = run_dir / "panel.parquet"
        if not panel_path.exists():
            raise ResultNotFound(f"No panel.parquet found for run_id={run_id!r}")
        try:
            table = pq.read_table(panel_path)
        except Exception as exc:
            raise ResultStoreError(
                f"Failed to read panel.parquet for run_id={run_id!r}: {exc}"
            ) from exc
        raw_meta = table.schema.metadata or {}
        panel_meta_bytes = raw_meta.get(b"reformlab_panel_metadata", b"{}")
        try:
            panel_metadata: dict[str, Any] = json.loads(panel_meta_bytes)
        except (json.JSONDecodeError, ValueError):
            logger.warning("event=panel_metadata_corrupt run_id=%s", run_id)
            panel_metadata = {}
        return PanelOutput(table=table, metadata=panel_metadata)

    def load_manifest(self, run_id: str) -> RunManifest:
        """Load manifest from disk.

        Args:
            run_id: Unique run identifier.

        Returns:
            RunManifest deserialized from manifest.json.

        Raises:
            ResultNotFound: If manifest.json does not exist.
            ResultStoreError: If the file is unreadable or JSON is corrupt.
        """
        from reformlab.governance.errors import ManifestValidationError
        from reformlab.governance.manifest import RunManifest

        run_dir = self._resolve_safe(run_id)
        manifest_path = run_dir / "manifest.json"
        if not manifest_path.exists():
            raise ResultNotFound(f"No manifest.json found for run_id={run_id!r}")
        try:
            manifest_json = manifest_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ResultStoreError(
                f"Failed to read manifest.json for run_id={run_id!r}: {exc}"
            ) from exc
        try:
            return RunManifest.from_json(manifest_json)
        except (ManifestValidationError, Exception) as exc:
            raise ResultStoreError(
                f"Corrupt manifest.json for run_id={run_id!r}: {exc}"
            ) from exc

    def load_from_disk(self, run_id: str) -> SimulationResult | None:
        """Reconstruct a minimal SimulationResult from disk artifacts.

        Returns None if no panel.parquet exists (failed runs, pre-17.7 runs).
        If the panel file is corrupt, logs a warning and returns None.

        Args:
            run_id: Unique run identifier.

        Returns:
            SimulationResult with panel_output and manifest, or None.
        """
        from reformlab.interfaces.api import SimulationResult

        if not self.has_panel(run_id):
            return None

        try:
            panel = self.load_panel(run_id)
        except ResultStoreError:
            logger.warning("event=panel_load_corrupt run_id=%s", run_id)
            return None

        try:
            metadata = self.get_metadata(run_id)
        except ResultStoreError:
            logger.warning("event=metadata_load_failed run_id=%s", run_id)
            return None

        try:
            manifest = self.load_manifest(run_id)
        except (ResultNotFound, ResultStoreError):
            manifest = _make_minimal_manifest(metadata)

        return SimulationResult(
            success=metadata.status == "completed",
            scenario_id=metadata.scenario_id,
            yearly_states={},
            panel_output=panel,
            manifest=manifest,
            metadata={},
        )

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_result(self, run_id: str) -> None:
        """Remove a result directory from the store.

        Args:
            run_id: Unique run identifier.

        Raises:
            ResultNotFound: If the run directory does not exist.
        """
        run_dir = self._resolve_safe(run_id)
        if not run_dir.exists():
            raise ResultNotFound(f"No metadata found for run_id={run_id!r}")

        import shutil

        shutil.rmtree(run_dir)
        logger.info("event=metadata_deleted run_id=%s", run_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _dict_to_metadata(data: dict[str, object]) -> ResultMetadata:
    """Construct ResultMetadata from a JSON-decoded dict."""
    raw_population_id = data.get("population_id")
    raw_seed = data.get("seed")
    raw_template = data.get("template_name")
    raw_policy_type = data.get("policy_type")
    raw_portfolio = data.get("portfolio_name")
    # Story 23.1 / AC-3: Extract runtime_mode with "live" fallback for legacy data
    raw_runtime_mode = data.get("runtime_mode", "live")
    # Story 23.2 / AC-5: Extract population_source with None fallback for legacy data
    raw_population_source = data.get("population_source")
    return ResultMetadata(
        run_id=str(data["run_id"]),
        timestamp=str(data["timestamp"]),
        run_kind=str(data["run_kind"]),
        start_year=int(str(data["start_year"])),
        end_year=int(str(data["end_year"])),
        population_id=str(raw_population_id) if raw_population_id is not None else None,
        seed=int(str(raw_seed)) if raw_seed is not None else None,
        row_count=int(str(data["row_count"])),
        manifest_id=str(data["manifest_id"]),
        scenario_id=str(data["scenario_id"]),
        adapter_version=str(data["adapter_version"]),
        started_at=str(data["started_at"]),
        finished_at=str(data["finished_at"]),
        status=str(data["status"]),
        template_name=str(raw_template) if raw_template is not None else None,
        policy_type=str(raw_policy_type) if raw_policy_type is not None else None,
        portfolio_name=str(raw_portfolio) if raw_portfolio is not None else None,
        runtime_mode=str(raw_runtime_mode),
        population_source=str(raw_population_source) if raw_population_source is not None else None,
    )


def _parse_timestamp(ts: str) -> datetime:
    """Parse an ISO 8601 UTC timestamp string to datetime."""
    try:
        # Handle both 'Z' suffix and '+00:00'
        normalized = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except (ValueError, AttributeError):
        return datetime.min.replace(tzinfo=timezone.utc)


def _make_minimal_manifest(metadata: ResultMetadata) -> RunManifest:
    """Construct a minimal RunManifest from ResultMetadata fields.

    Used as a fallback when manifest.json is missing or corrupt (e.g.,
    runs from before Story 17.7 or partial disk artifacts).

    Story 23.1 / AC-3: Include runtime_mode from metadata (defaults to "live").
    """
    from reformlab.governance.manifest import RunManifest

    manifest_id = metadata.manifest_id if metadata.manifest_id else "unknown"
    adapter_version = metadata.adapter_version if metadata.adapter_version else "unknown"
    return RunManifest(
        manifest_id=manifest_id,
        created_at=metadata.started_at or datetime.now(timezone.utc).isoformat(),
        engine_version="unknown",
        openfisca_version="unknown",
        adapter_version=adapter_version,
        scenario_version="unknown",
        runtime_mode=metadata.runtime_mode,  # Story 23.1 / AC-3
    )
