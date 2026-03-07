"""Replication package export, import, and reproduction for simulation runs.

Implements Story 16.1 (FR54): self-contained replication package export with a
manifest index listing all artifacts with roles and SHA-256 integrity hashes.

Implements Story 16.2: import of replication packages (directory or ZIP) with
integrity verification and reproduction of simulation runs.

A replication package is a directory (or ZIP archive) containing:
  data/panel-output.parquet    — simulation results
  config/policy.json           — policy parameters snapshot
  config/scenario-metadata.json — seeds, pipeline, assumptions, mappings
  manifests/run-manifest.json  — full RunManifest with provenance
  package-index.json           — artifact manifest index (not self-referential)

Public API:
    PackageArtifact: Single artifact entry in the index
    PackageIndex: The manifest index with package_id, timestamps, artifact list
    ReplicationPackageMetadata: Return value from export_replication_package()
    ImportedPackage: Loaded replication package with all typed artifacts
    ReproductionResult: Result of reproduce_from_package() with diagnostics
    export_replication_package: Main export function
    import_replication_package: Main import function
    reproduce_from_package: Re-execute simulation from an imported package
"""

from __future__ import annotations

import json
import logging
import shutil
import tempfile
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import pyarrow as pa
import pyarrow.parquet as pq

from reformlab.governance.errors import ReplicationPackageError
from reformlab.governance.hashing import hash_file
from reformlab.governance.manifest import RunManifest

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.interfaces.api import SimulationResult
    from reformlab.orchestrator.types import PipelineStep

logger = logging.getLogger(__name__)

# ============================================================
# Type Aliases
# ============================================================

PackageArtifactRole = Literal["input", "config", "output", "metadata"]
PackageArtifactType = Literal[
    "population", "scenario", "template", "manifest", "result", "lineage"
]

# ============================================================
# Domain Types
# ============================================================


@dataclass(frozen=True)
class PackageArtifact:
    """Single artifact entry in a replication package index.

    Attributes:
        role: Functional role of the artifact.
        artifact_type: Content type classification.
        path: Relative path within the package directory.
        hash: SHA-256 hex digest of the file content.
        description: Human-readable description of the artifact.
    """

    role: PackageArtifactRole
    artifact_type: PackageArtifactType
    path: str
    hash: str
    description: str


@dataclass(frozen=True)
class PackageIndex:
    """Manifest index for a replication package.

    Enumerates all artifacts with integrity hashes. Written as
    ``package-index.json`` at the package root.

    Attributes:
        package_id: UUID4 identifier for this package.
        created_at: ISO 8601 UTC timestamp of package creation.
        reformlab_version: ReformLab engine version string.
        source_manifest_id: Manifest ID of the originating simulation run.
        artifacts: Ordered tuple of artifact entries.
    """

    package_id: str
    created_at: str
    reformlab_version: str
    source_manifest_id: str
    artifacts: tuple[PackageArtifact, ...]

    def to_json(self) -> str:
        """Serialize to canonical JSON with sorted keys.

        Returns:
            Deterministic JSON string representation.
        """
        data: dict[str, Any] = {
            "package_id": self.package_id,
            "created_at": self.created_at,
            "reformlab_version": self.reformlab_version,
            "source_manifest_id": self.source_manifest_id,
            "artifacts": [
                {
                    "role": a.role,
                    "artifact_type": a.artifact_type,
                    "path": a.path,
                    "hash": a.hash,
                    "description": a.description,
                }
                for a in self.artifacts
            ],
        }
        return json.dumps(data, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, text: str) -> PackageIndex:
        """Deserialize from JSON string.

        Args:
            text: JSON string produced by ``to_json()``.

        Returns:
            Reconstructed PackageIndex instance.

        Raises:
            ValueError: If JSON is malformed or required fields are missing.
        """
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid PackageIndex JSON: {exc}") from exc

        required = ("package_id", "created_at", "reformlab_version", "source_manifest_id", "artifacts")
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"PackageIndex missing fields: {', '.join(missing)}")

        try:
            artifacts = tuple(
                PackageArtifact(
                    role=entry["role"],
                    artifact_type=entry["artifact_type"],
                    path=entry["path"],
                    hash=entry["hash"],
                    description=entry["description"],
                )
                for entry in data["artifacts"]
            )
        except (KeyError, TypeError) as exc:
            raise ValueError(f"PackageIndex artifact entry malformed: {exc}") from exc

        return cls(
            package_id=data["package_id"],
            created_at=data["created_at"],
            reformlab_version=data["reformlab_version"],
            source_manifest_id=data["source_manifest_id"],
            artifacts=artifacts,
        )


@dataclass(frozen=True)
class ReplicationPackageMetadata:
    """Metadata returned after exporting a replication package.

    Attributes:
        package_id: UUID4 identifier for the exported package.
        source_manifest_id: Manifest ID of the originating simulation run.
        package_path: Filesystem path to the package (directory or ZIP file).
        artifact_count: Number of artifacts included in the index.
        compressed: True if the package is a ZIP archive.
        index: The full PackageIndex that was written.
    """

    package_id: str
    source_manifest_id: str
    package_path: Path
    artifact_count: int
    compressed: bool
    index: PackageIndex


# ============================================================
# Import/Reproduction Types (Story 16.2)
# ============================================================


@dataclass(frozen=True)
class ImportedPackage:
    """A replication package loaded from disk with all artifacts resolved.

    Attributes:
        package_id: UUID identifier from the package index.
        source_manifest_id: Manifest ID of the originating simulation run.
        source_path: Filesystem path of the package as imported (dir or ZIP).
        index: The parsed PackageIndex from package-index.json.
        manifest: Deserialized RunManifest from manifests/run-manifest.json.
        panel_table: Panel output table from data/panel-output.parquet.
        policy: Policy parameters from config/policy.json.
        scenario_metadata: Scenario metadata from config/scenario-metadata.json.
        integrity_verified: True when all artifact hashes matched on import.

    Story 16.2 / AC-1, AC-3.
    """

    package_id: str
    source_manifest_id: str
    source_path: Path
    index: PackageIndex
    manifest: RunManifest
    panel_table: pa.Table
    policy: dict[str, Any]
    scenario_metadata: dict[str, Any]
    integrity_verified: bool

    def reproduce(
        self,
        adapter: ComputationAdapter,
        *,
        tolerance: float = 0.0,
        population_path: Path | None = None,
        steps: tuple[PipelineStep, ...] | None = None,
    ) -> ReproductionResult:
        """Re-execute the simulation and compare with original results.

        Convenience method delegating to ``reproduce_from_package()``.

        Args:
            adapter: Computation adapter to use for reproduction.
            tolerance: Absolute numeric tolerance for comparison. Default 0.0.
            population_path: Optional population data path override.
            steps: Optional additional pipeline steps.

        Returns:
            ReproductionResult with match status and diagnostics.

        Story 16.2 / AC-2.
        """
        return reproduce_from_package(
            self,
            adapter,
            tolerance=tolerance,
            population_path=population_path,
            steps=steps,
        )


@dataclass(frozen=True)
class ReproductionResult:
    """Result of reproducing a simulation from an imported replication package.

    Attributes:
        passed: True when both integrity check and numerical match passed.
        integrity_passed: True when all artifact hashes verified on import.
        numerical_match: True when reproduced panel output matches original.
        tolerance_used: The absolute tolerance applied to numeric comparisons.
        discrepancies: Human-readable descriptions of any mismatches found.
        original_manifest_id: Manifest ID of the package being reproduced.
        reproduced_result: The SimulationResult from reproduction, or None on failure.

    Story 16.2 / AC-5.
    """

    passed: bool
    integrity_passed: bool
    numerical_match: bool
    tolerance_used: float
    discrepancies: tuple[str, ...]
    original_manifest_id: str
    reproduced_result: SimulationResult | None

    def summary(self) -> str:
        """Return formatted diagnostic report for this reproduction result.

        Returns:
            Multi-line report string with status, integrity, match, and discrepancies.

        Story 16.2 / AC-5.
        """
        status = "PASSED" if self.passed else "FAILED"
        integrity = "PASSED" if self.integrity_passed else "FAILED"
        match = "PASSED" if self.numerical_match else "FAILED"

        lines = [
            "Reproduction Report",
            f"  Status: {status}",
            f"  Original manifest: {self.original_manifest_id}",
            f"  Integrity check: {integrity}",
            f"  Numerical match: {match} (tolerance={self.tolerance_used})",
            f"  Discrepancies: {len(self.discrepancies)}",
        ]
        for d in self.discrepancies:
            lines.append(f"    - {d}")
        return "\n".join(lines)


# ============================================================
# Export Function
# ============================================================


def export_replication_package(
    result: SimulationResult,
    output_path: Path,
    *,
    compress: bool = False,
) -> ReplicationPackageMetadata:
    """Export a completed simulation run as a self-contained replication package.

    Creates a structured directory (or ZIP archive) containing the simulation
    panel output, policy configuration snapshot, scenario metadata, and run
    manifest. A ``package-index.json`` enumerates all artifacts with SHA-256
    hashes for integrity verification.

    Args:
        result: Completed ``SimulationResult`` (``success=True``).
        output_path: Existing directory where the package is written.
            The package subdirectory ``{package_id}/`` is created inside it.
        compress: If True, produce a ``.zip`` archive instead of a directory.

    Returns:
        ReplicationPackageMetadata with package location and index.

    Raises:
        ReplicationPackageError: If validation fails (failed run, missing panel
            output, or invalid output_path).

    Story 16.1 / FR54, AC-1 through AC-5.
    """
    # ── Validate inputs (AC-3 validation, AC-1 guard) ──────────────────────
    if not getattr(result, "success", False):
        raise ReplicationPackageError(
            "Cannot export replication package: simulation result has success=False. "
            "Only completed successful runs can be exported."
        )

    panel_output = getattr(result, "panel_output", None)
    if panel_output is None:
        raise ReplicationPackageError(
            "Cannot export replication package: result.panel_output is None. "
            "Panel output is required for export."
        )

    if not output_path.exists() or not output_path.is_dir():
        raise ReplicationPackageError(
            f"Cannot export replication package: output_path={output_path!r} "
            "does not exist or is not a directory."
        )

    manifest = result.manifest

    # ── Create package directory ────────────────────────────────────────────
    package_id = str(uuid.uuid4())
    package_dir = output_path / package_id
    package_dir.mkdir(parents=False, exist_ok=False)

    # Wrap all artifact I/O in try/finally so partial directories are cleaned
    # up on any failure, leaving no half-exported packages on disk.
    try:
        data_dir = package_dir / "data"
        config_dir = package_dir / "config"
        manifests_dir = package_dir / "manifests"
        data_dir.mkdir()
        config_dir.mkdir()
        manifests_dir.mkdir()

        # ── Export artifacts ────────────────────────────────────────────────────

        # AC-1: panel output (Parquet)
        parquet_path = data_dir / "panel-output.parquet"
        panel_output.to_parquet(parquet_path)

        # AC-1: policy parameters snapshot
        policy_path = config_dir / "policy.json"
        policy_data = getattr(manifest, "policy", {})
        policy_path.write_text(
            json.dumps(policy_data, sort_keys=True, indent=2),
            encoding="utf-8",
        )

        # AC-1: scenario metadata snapshot (seeds, pipeline, assumptions, mappings, warnings)
        scenario_meta_path = config_dir / "scenario-metadata.json"
        scenario_meta: dict[str, Any] = {
            "adapter_version": getattr(manifest, "adapter_version", ""),
            "assumptions": getattr(manifest, "assumptions", []),
            "engine_version": getattr(manifest, "engine_version", ""),
            "mappings": getattr(manifest, "mappings", []),
            "scenario_version": getattr(manifest, "scenario_version", ""),
            "seeds": getattr(manifest, "seeds", {}),
            "step_pipeline": getattr(manifest, "step_pipeline", []),
            "warnings": getattr(manifest, "warnings", []),
        }
        scenario_meta_path.write_text(
            json.dumps(scenario_meta, sort_keys=True, indent=2),
            encoding="utf-8",
        )

        # AC-1: run manifest (full RunManifest JSON)
        run_manifest_path = manifests_dir / "run-manifest.json"
        run_manifest_path.write_text(manifest.to_json(), encoding="utf-8")

        # AC-4: child manifests if available in metadata (year → manifest JSON string)
        child_manifests_meta: Any = result.metadata.get("child_manifests", {})
        child_manifests_written: list[Path] = []
        if isinstance(child_manifests_meta, dict) and child_manifests_meta:
            any_written = False
            for year_raw, manifest_value in sorted(child_manifests_meta.items()):
                if isinstance(manifest_value, str) and manifest_value.startswith("{"):
                    try:
                        year_int = int(year_raw)
                    except (TypeError, ValueError):
                        continue
                    child_path = manifests_dir / f"year-{year_int}.json"
                    child_path.write_text(manifest_value, encoding="utf-8")
                    child_manifests_written.append(child_path)
                    any_written = True
            if not any_written:
                logger.debug(
                    "event=child_manifests_absent package_id=%s reason=no_json_manifest_strings",
                    package_id,
                )
        else:
            logger.debug("event=child_manifests_absent package_id=%s", package_id)

        # ── Hash all artifact files ─────────────────────────────────────────────
        artifacts_info: list[tuple[Path, PackageArtifactRole, PackageArtifactType, str]] = [
            (parquet_path, "output", "result", "Panel output table (household × year)"),
            (policy_path, "config", "scenario", "Policy parameters snapshot"),
            (scenario_meta_path, "config", "scenario", "Seeds, step pipeline, assumptions, mappings"),
            (run_manifest_path, "metadata", "manifest", "Immutable run manifest with full provenance"),
        ]
        for child_path in child_manifests_written:
            year_label = child_path.stem  # e.g. "year-2025"
            artifacts_info.append(
                (child_path, "metadata", "manifest", f"Year manifest: {year_label}"),
            )

        package_artifacts: list[PackageArtifact] = []
        for file_path, role, artifact_type, description in artifacts_info:
            file_hash = hash_file(file_path)
            rel_path = file_path.relative_to(package_dir).as_posix()
            package_artifacts.append(
                PackageArtifact(
                    role=role,
                    artifact_type=artifact_type,
                    path=rel_path,
                    hash=file_hash,
                    description=description,
                )
            )

        # ── Build and write PackageIndex (AC-2, AC-5) ───────────────────────────
        created_at = datetime.now(timezone.utc).isoformat()
        reformlab_version = getattr(manifest, "engine_version", "unknown")
        source_manifest_id = getattr(manifest, "manifest_id", "")

        index = PackageIndex(
            package_id=package_id,
            created_at=created_at,
            reformlab_version=reformlab_version,
            source_manifest_id=source_manifest_id,
            artifacts=tuple(package_artifacts),
        )

        index_path = package_dir / "package-index.json"
        index_path.write_text(index.to_json(), encoding="utf-8")

        # ── Optional compression (AC-3) ─────────────────────────────────────────
        final_path: Path
        if compress:
            zip_path = output_path / f"{package_id}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in package_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(output_path)
                        zf.write(file_path, arcname)
            shutil.rmtree(package_dir)
            final_path = zip_path
        else:
            final_path = package_dir

    except Exception:
        # Clean up partial package directory so no half-exported packages remain.
        if package_dir.exists():
            shutil.rmtree(package_dir)
        raise

    logger.info(
        "event=replication_package_created package_id=%s artifact_count=%d compressed=%s",
        package_id,
        len(package_artifacts),
        compress,
    )

    return ReplicationPackageMetadata(
        package_id=package_id,
        source_manifest_id=source_manifest_id,
        package_path=final_path,
        artifact_count=len(package_artifacts),
        compressed=compress,
        index=index,
    )


# ============================================================
# Import Function (Story 16.2)
# ============================================================


def import_replication_package(package_path: Path) -> ImportedPackage:
    """Load a replication package from a directory or ZIP archive.

    Reads all artifacts, verifies SHA-256 integrity hashes against the
    package index, and returns a typed ``ImportedPackage`` with all fields
    populated.

    Args:
        package_path: Path to the package directory or ``.zip`` archive.

    Returns:
        ImportedPackage with all artifacts loaded and integrity_verified set.

    Raises:
        ReplicationPackageError: If the path does not exist, is not a valid
            package, has missing artifacts, or has integrity hash mismatches.

    Story 16.2 / AC-1, AC-3, AC-4.
    """
    # ── 1. Validate path exists ──────────────────────────────────────────────
    if not package_path.exists():
        raise ReplicationPackageError(
            f"Replication package path does not exist: {package_path!r}"
        )

    # ── 2. Detect format and resolve package_dir ─────────────────────────────
    _tmp_dir_ctx: tempfile.TemporaryDirectory[str] | None = None
    package_dir: Path

    if package_path.is_dir():
        package_dir = package_path
    elif package_path.suffix.lower() == ".zip":
        _tmp_dir_ctx = tempfile.TemporaryDirectory()
        tmp_root = Path(_tmp_dir_ctx.name)
        with zipfile.ZipFile(package_path, "r") as zf:
            zf.extractall(tmp_root)
        entries = list(tmp_root.iterdir())
        if len(entries) != 1 or not entries[0].is_dir():
            if _tmp_dir_ctx is not None:
                _tmp_dir_ctx.cleanup()
            raise ReplicationPackageError(
                f"Expected a single root directory in ZIP archive, found: "
                f"{[e.name for e in entries]!r}"
            )
        package_dir = entries[0]
    else:
        raise ReplicationPackageError(
            f"Package path must be a directory or .zip archive, got: {package_path!r}"
        )

    try:
        result = _load_package_from_dir(package_dir, source_path=package_path)
    finally:
        if _tmp_dir_ctx is not None:
            _tmp_dir_ctx.cleanup()

    return result


def _load_package_from_dir(
    package_dir: Path,
    source_path: Path,
) -> ImportedPackage:
    """Load and verify a replication package from an extracted directory.

    Internal helper — caller is responsible for temp-dir lifecycle.
    """
    # ── 3. Read package-index.json ───────────────────────────────────────────
    index_path = package_dir / "package-index.json"
    if not index_path.exists():
        raise ReplicationPackageError(
            f"package-index.json not found in package at {package_dir!r}"
        )
    index = PackageIndex.from_json(index_path.read_text(encoding="utf-8"))

    # ── 4. Verify all artifact hashes ───────────────────────────────────────
    for artifact in index.artifacts:
        full_path = package_dir / artifact.path
        if not full_path.exists():
            raise ReplicationPackageError(
                f"Artifact missing: {artifact.path} — expected hash {artifact.hash}"
            )
        actual_hash = hash_file(full_path)
        if actual_hash != artifact.hash:
            raise ReplicationPackageError(
                f"Integrity check failed for {artifact.path}: "
                f"expected {artifact.hash}, got {actual_hash}"
            )

    # ── 5. Load artifacts ────────────────────────────────────────────────────
    run_manifest_path = package_dir / "manifests" / "run-manifest.json"
    manifest = RunManifest.from_json(run_manifest_path.read_text(encoding="utf-8"))

    parquet_path = package_dir / "data" / "panel-output.parquet"
    panel_table = pq.read_table(parquet_path)

    policy_path = package_dir / "config" / "policy.json"
    policy: dict[str, Any] = json.loads(policy_path.read_text(encoding="utf-8"))

    scenario_meta_path = package_dir / "config" / "scenario-metadata.json"
    scenario_metadata: dict[str, Any] = json.loads(
        scenario_meta_path.read_text(encoding="utf-8")
    )

    # ── 6. Build and return ImportedPackage ──────────────────────────────────
    logger.info(
        "event=replication_package_imported package_id=%s artifact_count=%d "
        "integrity_verified=True",
        index.package_id,
        len(index.artifacts),
    )

    return ImportedPackage(
        package_id=index.package_id,
        source_manifest_id=index.source_manifest_id,
        source_path=source_path,
        index=index,
        manifest=manifest,
        panel_table=panel_table,
        policy=policy,
        scenario_metadata=scenario_metadata,
        integrity_verified=True,
    )


# ============================================================
# Reproduction Function (Story 16.2)
# ============================================================


def reproduce_from_package(
    package: ImportedPackage,
    adapter: ComputationAdapter,
    *,
    tolerance: float = 0.0,
    population_path: Path | None = None,
    steps: tuple[PipelineStep, ...] | None = None,
) -> ReproductionResult:
    """Re-execute a simulation from an imported replication package.

    Extracts the configuration from the package (policy, seeds, year range),
    runs the simulation, and compares the reproduced panel output with the
    original using column-by-column comparison within ``tolerance``.

    Args:
        package: Imported replication package.
        adapter: Computation adapter to use for reproduction.
        tolerance: Absolute numeric tolerance for comparison. Default 0.0
            means exact match is required.
        population_path: Optional population data path override.
        steps: Optional additional pipeline steps.

    Returns:
        ReproductionResult with pass/fail status, discrepancy list, and
        optional reproduced SimulationResult.

    Story 16.2 / AC-2, AC-5.
    """
    if tolerance < 0:
        raise ReplicationPackageError(
            f"tolerance must be >= 0, got {tolerance}"
        )

    # ── Extract scenario config from package ─────────────────────────────────
    year_col = package.panel_table.column("year")
    year_values = year_col.to_pylist()
    start_year = int(min(year_values))
    end_year = int(max(year_values))

    seed_raw = package.manifest.seeds.get("master")
    seed: int | None = int(seed_raw) if seed_raw is not None else None

    # ── Runtime import to avoid circular dependencies ─────────────────────────
    from reformlab.interfaces.api import ScenarioConfig, run_scenario  # noqa: PLC0415

    config = ScenarioConfig(
        template_name="reproduction",
        policy=package.policy,
        start_year=start_year,
        end_year=end_year,
        seed=seed,
        population_path=population_path,
    )

    # ── Execute reproduction ──────────────────────────────────────────────────
    try:
        reproduced = run_scenario(
            config, adapter, steps=steps, skip_memory_check=True
        )
    except Exception as exc:
        logger.info(
            "event=reproduction_completed passed=False tolerance=%s discrepancy_count=1",
            tolerance,
        )
        return ReproductionResult(
            passed=False,
            integrity_passed=package.integrity_verified,
            numerical_match=False,
            tolerance_used=tolerance,
            discrepancies=(f"Reproduction execution failed: {exc}",),
            original_manifest_id=package.source_manifest_id,
            reproduced_result=None,
        )

    # ── Compare panel tables ──────────────────────────────────────────────────
    reproduced_table = reproduced.panel_output.table if reproduced.panel_output else pa.table({})
    numerical_match, discrepancies = _compare_panel_tables(
        package.panel_table, reproduced_table, tolerance
    )

    passed = package.integrity_verified and numerical_match

    logger.info(
        "event=reproduction_completed passed=%s tolerance=%s discrepancy_count=%d",
        passed,
        tolerance,
        len(discrepancies),
    )

    return ReproductionResult(
        passed=passed,
        integrity_passed=package.integrity_verified,
        numerical_match=numerical_match,
        tolerance_used=tolerance,
        discrepancies=discrepancies,
        original_manifest_id=package.source_manifest_id,
        reproduced_result=reproduced,
    )


# ============================================================
# Internal Helpers (Story 16.2)
# ============================================================


def _compare_panel_tables(
    original: pa.Table,
    reproduced: pa.Table,
    tolerance: float,
) -> tuple[bool, tuple[str, ...]]:
    """Compare two panel tables column-by-column within absolute tolerance.

    Sort keys (household_id, year) are used when present for deterministic
    comparison. Numeric columns use absolute tolerance; non-numeric use exact
    equality.

    Args:
        original: Original panel table from the replication package.
        reproduced: Reproduced panel table from re-execution.
        tolerance: Absolute tolerance for numeric column comparison.

    Returns:
        Tuple of (match: bool, discrepancies: tuple[str, ...]).

    Story 16.2 / AC-2.
    """
    discrepancies: list[str] = []

    # ── Schema check (column names, order-independent) ───────────────────────
    orig_cols = set(original.column_names)
    repr_cols = set(reproduced.column_names)
    if orig_cols != repr_cols:
        missing = sorted(orig_cols - repr_cols)
        extra = sorted(repr_cols - orig_cols)
        parts = []
        if missing:
            parts.append(f"missing in reproduced: {missing}")
        if extra:
            parts.append(f"extra in reproduced: {extra}")
        return False, (f"Column mismatch: {'; '.join(parts)}",)

    # ── Row count check ───────────────────────────────────────────────────────
    if original.num_rows != reproduced.num_rows:
        return False, (
            f"Row count mismatch: original={original.num_rows}, "
            f"reproduced={reproduced.num_rows}",
        )

    # ── Sort both tables for deterministic comparison ─────────────────────────
    sort_keys = ["household_id", "year"]
    has_sort_keys = all(k in original.column_names for k in sort_keys)
    if has_sort_keys:
        import pyarrow.compute as pc

        orig_sort_indices = pc.sort_indices(
            original, sort_keys=[(k, "ascending") for k in sort_keys]
        )
        repr_sort_indices = pc.sort_indices(
            reproduced, sort_keys=[(k, "ascending") for k in sort_keys]
        )
        original = original.take(orig_sort_indices)
        reproduced = reproduced.take(repr_sort_indices)
    else:
        logger.warning(
            "event=compare_panel_tables sort_keys_absent reason=household_id_or_year_missing"
        )

    # ── Column-by-column comparison ───────────────────────────────────────────
    for col_name in original.column_names:
        orig_col = original.column(col_name)
        repr_col = reproduced.column(col_name)
        col_type = orig_col.type

        if pa.types.is_floating(col_type) or pa.types.is_integer(col_type):
            orig_vals = orig_col.to_pylist()
            repr_vals = repr_col.to_pylist()
            for row_idx, (ov, rv) in enumerate(zip(orig_vals, repr_vals)):
                # NaN and null are non-matching regardless of tolerance
                if ov is None or rv is None:
                    if ov != rv:
                        discrepancies.append(
                            f"Column '{col_name}' row {row_idx}: null mismatch "
                            f"(original={ov!r}, reproduced={rv!r})"
                        )
                    continue
                try:
                    fov, frv = float(ov), float(rv)
                except (TypeError, ValueError):
                    discrepancies.append(
                        f"Column '{col_name}' row {row_idx}: cannot compare values "
                        f"{ov!r} and {rv!r}"
                    )
                    continue
                import math

                if math.isnan(fov) or math.isnan(frv):
                    discrepancies.append(
                        f"Column '{col_name}' row {row_idx}: NaN value(s) "
                        f"(original={fov}, reproduced={frv})"
                    )
                    continue
                diff = abs(fov - frv)
                if diff > tolerance:
                    discrepancies.append(
                        f"Column '{col_name}' row {row_idx}: "
                        f"{fov} vs {frv} (diff={diff})"
                    )
        else:
            orig_list = orig_col.to_pylist()
            repr_list = repr_col.to_pylist()
            if orig_list != repr_list:
                # Report first mismatch
                for row_idx, (ov, rv) in enumerate(zip(orig_list, repr_list)):
                    if ov != rv:
                        discrepancies.append(
                            f"Column '{col_name}' row {row_idx}: "
                            f"{ov!r} vs {rv!r}"
                        )
                        break

    return len(discrepancies) == 0, tuple(discrepancies)
