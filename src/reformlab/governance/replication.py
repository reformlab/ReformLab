"""Replication package export for completed simulation runs.

Implements Story 16.1 (FR54): self-contained replication package export with a
manifest index listing all artifacts with roles and SHA-256 integrity hashes.

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
    export_replication_package: Main export function
"""

from __future__ import annotations

import json
import logging
import shutil
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from reformlab.governance.errors import ReplicationPackageError
from reformlab.governance.hashing import hash_file

if TYPE_CHECKING:
    pass

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
# Export Function
# ============================================================


def export_replication_package(
    result: Any,
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
        for year_raw, manifest_value in child_manifests_meta.items():
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
