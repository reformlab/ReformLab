"""Persistent result metadata storage for the ReformLab server.

Stores lightweight run metadata on the filesystem so past simulation runs
are discoverable across server restarts. Full SimulationResult objects
remain in the in-memory ResultCache; this module persists only the metadata
needed for listing and identification.

Storage layout:
    ~/.reformlab/results/{run_id}/metadata.json

References: Story 17.3, AC-2, AC-3
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

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
    )


def _parse_timestamp(ts: str) -> datetime:
    """Parse an ISO 8601 UTC timestamp string to datetime."""
    try:
        # Handle both 'Z' suffix and '+00:00'
        normalized = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except (ValueError, AttributeError):
        return datetime.min.replace(tzinfo=timezone.utc)
