"""Tests for replication package export, import, and reproduction.

Story 16.1 / FR54 — AC-1 through AC-5 (export):
    AC-1: Self-contained package directory structure
    AC-2: Manifest index with role, artifact_type, path, hash per artifact
    AC-3: Optional compression to ZIP archive
    AC-4: Calibration assumptions present in exported run-manifest.json
    AC-5: Manifest index integrity (UUID, ISO timestamp, version, artifact hashes)

Story 16.2 — AC-1 through AC-5 (import and reproduction):
    AC-1: Package import with artifact restoration
    AC-2: Simulation reproduction within tolerance
    AC-3: Manifest integrity verification
    AC-4: Corrupted artifact detection
    AC-5: Reproduction comparison report
"""

from __future__ import annotations

import json
import uuid
import zipfile
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

from reformlab.governance.errors import ReplicationPackageError
from reformlab.governance.hashing import hash_file
from reformlab.governance.manifest import RunManifest
from reformlab.governance.replication import (
    PackageArtifact,
    PackageIndex,
    ReplicationPackageMetadata,
    ReproductionResult,
    export_replication_package,
    import_replication_package,
    reproduce_from_package,
)

# ============================================================
# Test fixtures
# ============================================================


def _make_manifest(
    *,
    manifest_id: str = "test-manifest-001",
    calibration: bool = False,
) -> RunManifest:
    """Build a minimal valid RunManifest for tests."""
    assumptions: list[dict[str, Any]] = []
    if calibration:
        assumptions = [
            {
                "key": "calibration.beta_income",
                "value": -0.0023,
                "source": "calibration",
                "is_default": False,
            },
            {
                "key": "calibration.run_id",
                "value": "calib-run-abc123",
                "source": "calibration",
                "is_default": False,
            },
        ]
    return RunManifest(
        manifest_id=manifest_id,
        created_at="2026-03-07T10:00:00Z",
        engine_version="0.1.0",
        openfisca_version="44.0.0",
        adapter_version="1.0.0",
        scenario_version="v1.0",
        policy={"carbon_tax_rate": 44.6},
        seeds={"master": 42},
        assumptions=assumptions,
    )


def _make_panel_output() -> Any:
    """Build a minimal PanelOutput for tests."""
    from reformlab.orchestrator.panel import PanelOutput

    table = pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "year": pa.array([2025, 2025, 2025], type=pa.int64()),
            "carbon_tax": pa.array([150.0, 200.0, 250.0], type=pa.float64()),
        }
    )
    return PanelOutput(table=table, metadata={"start_year": 2025, "end_year": 2025})


def _make_result(
    *,
    success: bool = True,
    manifest_id: str = "test-manifest-001",
    calibration: bool = False,
    child_manifests_meta: dict[int, str] | None = None,
) -> Any:
    """Build a minimal SimulationResult for tests."""
    from reformlab.interfaces.api import SimulationResult
    from reformlab.orchestrator.types import YearState

    panel = _make_panel_output() if success else None
    manifest = _make_manifest(manifest_id=manifest_id, calibration=calibration)
    meta: dict[str, Any] = {}
    if child_manifests_meta is not None:
        meta["child_manifests"] = child_manifests_meta

    return SimulationResult(
        success=success,
        scenario_id="carbon-tax-test",
        yearly_states={2025: YearState(year=2025)},
        panel_output=panel,
        manifest=manifest,
        metadata=meta,
    )


# ============================================================
# TestPackageArtifact — AC-2
# ============================================================


class TestPackageArtifact:
    """Story 16.1 / AC-2: PackageArtifact type correctness."""

    def test_creation_with_all_fields(self) -> None:
        artifact = PackageArtifact(
            role="output",
            artifact_type="result",
            path="data/panel-output.parquet",
            hash="a" * 64,
            description="Panel output",
        )
        assert artifact.role == "output"
        assert artifact.artifact_type == "result"
        assert artifact.path == "data/panel-output.parquet"
        assert artifact.hash == "a" * 64
        assert artifact.description == "Panel output"

    def test_frozen_immutability(self) -> None:
        artifact = PackageArtifact(
            role="config",
            artifact_type="scenario",
            path="config/policy.json",
            hash="b" * 64,
            description="Policy snapshot",
        )
        with pytest.raises((AttributeError, TypeError)):
            artifact.role = "output"  # type: ignore[misc]

    def test_all_valid_roles(self) -> None:
        for role in ("input", "config", "output", "metadata"):
            a = PackageArtifact(
                role=role,  # type: ignore[arg-type]
                artifact_type="result",
                path="x",
                hash="c" * 64,
                description="test",
            )
            assert a.role == role

    def test_all_valid_artifact_types(self) -> None:
        for atype in ("population", "scenario", "template", "manifest", "result", "lineage"):
            a = PackageArtifact(
                role="output",
                artifact_type=atype,  # type: ignore[arg-type]
                path="x",
                hash="d" * 64,
                description="test",
            )
            assert a.artifact_type == atype


# ============================================================
# TestPackageIndex — AC-2, AC-5
# ============================================================


class TestPackageIndex:
    """Story 16.1 / AC-2, AC-5: PackageIndex serialization and integrity."""

    def _make_index(self) -> PackageIndex:
        artifact = PackageArtifact(
            role="output",
            artifact_type="result",
            path="data/panel-output.parquet",
            hash="a" * 64,
            description="Panel output",
        )
        return PackageIndex(
            package_id=str(uuid.uuid4()),
            created_at="2026-03-07T17:50:00+00:00",
            reformlab_version="0.1.0",
            source_manifest_id="test-manifest-001",
            artifacts=(artifact,),
        )

    def test_creation_with_artifacts(self) -> None:
        index = self._make_index()
        assert len(index.artifacts) == 1
        assert index.reformlab_version == "0.1.0"
        assert index.source_manifest_id == "test-manifest-001"

    def test_to_json_produces_valid_json(self) -> None:
        index = self._make_index()
        text = index.to_json()
        parsed = json.loads(text)
        assert "package_id" in parsed
        assert "created_at" in parsed
        assert "reformlab_version" in parsed
        assert "source_manifest_id" in parsed
        assert "artifacts" in parsed
        assert isinstance(parsed["artifacts"], list)
        assert len(parsed["artifacts"]) == 1

    def test_to_json_has_sorted_keys(self) -> None:
        index = self._make_index()
        text = index.to_json()
        parsed = json.loads(text)
        keys = list(parsed.keys())
        assert keys == sorted(keys), "Top-level JSON keys must be sorted"

    def test_from_json_round_trip_is_lossless(self) -> None:
        index = self._make_index()
        text = index.to_json()
        reconstructed = PackageIndex.from_json(text)
        assert reconstructed.package_id == index.package_id
        assert reconstructed.created_at == index.created_at
        assert reconstructed.reformlab_version == index.reformlab_version
        assert reconstructed.source_manifest_id == index.source_manifest_id
        assert len(reconstructed.artifacts) == len(index.artifacts)
        orig_a = index.artifacts[0]
        recon_a = reconstructed.artifacts[0]
        assert recon_a.role == orig_a.role
        assert recon_a.artifact_type == orig_a.artifact_type
        assert recon_a.path == orig_a.path
        assert recon_a.hash == orig_a.hash
        assert recon_a.description == orig_a.description

    def test_from_json_raises_on_invalid_json(self) -> None:
        with pytest.raises(ValueError, match="Invalid PackageIndex JSON"):
            PackageIndex.from_json("not-json")

    def test_from_json_raises_on_missing_fields(self) -> None:
        with pytest.raises(ValueError, match="PackageIndex missing fields"):
            PackageIndex.from_json('{"package_id": "x"}')

    def test_artifacts_is_tuple(self) -> None:
        index = self._make_index()
        assert isinstance(index.artifacts, tuple)


# ============================================================
# TestExportReplicationPackage — AC-1, AC-2, AC-5
# ============================================================


class TestExportReplicationPackage:
    """Story 16.1 / AC-1, AC-2, AC-5: successful export produces correct layout."""

    def test_creates_correct_directory_structure(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        pkg_dir = meta.package_path
        assert pkg_dir.is_dir()
        assert (pkg_dir / "data").is_dir()
        assert (pkg_dir / "config").is_dir()
        assert (pkg_dir / "manifests").is_dir()

    def test_all_expected_files_exist(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        pkg_dir = meta.package_path
        assert (pkg_dir / "data" / "panel-output.parquet").exists()
        assert (pkg_dir / "config" / "policy.json").exists()
        assert (pkg_dir / "config" / "scenario-metadata.json").exists()
        assert (pkg_dir / "manifests" / "run-manifest.json").exists()
        assert (pkg_dir / "package-index.json").exists()

    def test_policy_json_contains_policy_data(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        policy_path = meta.package_path / "config" / "policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        assert policy["carbon_tax_rate"] == 44.6

    def test_scenario_metadata_json_contains_required_fields(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        meta_path = meta.package_path / "config" / "scenario-metadata.json"
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        assert "seeds" in data
        assert "step_pipeline" in data
        assert "assumptions" in data
        assert "mappings" in data
        assert "warnings" in data
        assert "engine_version" in data
        assert data["seeds"]["master"] == 42

    def test_run_manifest_json_is_valid_run_manifest(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        manifest_path = meta.package_path / "manifests" / "run-manifest.json"
        text = manifest_path.read_text(encoding="utf-8")
        # Should be deserializable as RunManifest
        manifest = RunManifest.from_json(text)
        assert manifest.manifest_id == "test-manifest-001"

    def test_artifact_hashes_match_file_contents(self, tmp_path: Path) -> None:
        """AC-5: Every listed artifact hash verifiable against actual file."""
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        pkg_dir = meta.package_path
        for artifact in meta.index.artifacts:
            file_path = pkg_dir / artifact.path
            actual_hash = hash_file(file_path)
            assert actual_hash == artifact.hash, (
                f"Hash mismatch for {artifact.path}: expected {artifact.hash}, got {actual_hash}"
            )

    def test_manifest_index_lists_all_artifacts_with_correct_roles(self, tmp_path: Path) -> None:
        """AC-2: index lists artifacts with correct roles and types."""
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        index = meta.index
        paths = {a.path for a in index.artifacts}
        assert "data/panel-output.parquet" in paths
        assert "config/policy.json" in paths
        assert "config/scenario-metadata.json" in paths
        assert "manifests/run-manifest.json" in paths

        # Verify roles
        role_by_path = {a.path: a.role for a in index.artifacts}
        assert role_by_path["data/panel-output.parquet"] == "output"
        assert role_by_path["config/policy.json"] == "config"
        assert role_by_path["config/scenario-metadata.json"] == "config"
        assert role_by_path["manifests/run-manifest.json"] == "metadata"

    def test_manifest_index_artifact_types_correct(self, tmp_path: Path) -> None:
        """AC-2: artifact_type values are correct."""
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        assert any(a.artifact_type == "result" for a in meta.index.artifacts)
        assert any(a.artifact_type == "scenario" for a in meta.index.artifacts)
        assert any(a.artifact_type == "manifest" for a in meta.index.artifacts)

    def test_package_id_is_unique_per_call(self, tmp_path: Path) -> None:
        result = _make_result()
        meta1 = export_replication_package(result, tmp_path)
        meta2 = export_replication_package(result, tmp_path)
        assert meta1.package_id != meta2.package_id

    def test_package_index_not_self_referential(self, tmp_path: Path) -> None:
        """package-index.json itself is NOT listed in artifacts."""
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        paths = {a.path for a in meta.index.artifacts}
        assert "package-index.json" not in paths

    def test_metadata_returns_correct_artifact_count(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)
        assert meta.artifact_count == len(meta.index.artifacts)
        assert meta.artifact_count == 4  # parquet + policy.json + scenario-metadata.json + run-manifest.json

    def test_metadata_compressed_false_by_default(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)
        assert meta.compressed is False


# ============================================================
# TestExportCompression — AC-3
# ============================================================


class TestExportCompression:
    """Story 16.1 / AC-3: optional ZIP compression."""

    def test_compress_true_produces_zip_file(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path, compress=True)

        assert meta.compressed is True
        assert meta.package_path.suffix == ".zip"
        assert meta.package_path.exists()

    def test_compress_true_removes_directory(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path, compress=True)

        # The directory should be gone, replaced by the ZIP
        pkg_dir = tmp_path / meta.package_id
        assert not pkg_dir.exists()

    def test_zip_contains_all_expected_files(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path, compress=True)

        with zipfile.ZipFile(meta.package_path, "r") as zf:
            names = set(zf.namelist())

        pkg_id = meta.package_id
        assert f"{pkg_id}/data/panel-output.parquet" in names
        assert f"{pkg_id}/config/policy.json" in names
        assert f"{pkg_id}/config/scenario-metadata.json" in names
        assert f"{pkg_id}/manifests/run-manifest.json" in names
        assert f"{pkg_id}/package-index.json" in names

    def test_zip_entries_match_artifact_index(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path, compress=True)

        pkg_id = meta.package_id
        with zipfile.ZipFile(meta.package_path, "r") as zf:
            zip_names = set(zf.namelist())

        for artifact in meta.index.artifacts:
            expected_entry = f"{pkg_id}/{artifact.path}"
            assert expected_entry in zip_names, f"Expected {expected_entry} in ZIP"

    def test_compress_false_produces_directory(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path, compress=False)

        assert meta.compressed is False
        assert meta.package_path.is_dir()


# ============================================================
# TestExportCalibrationInclusion — AC-4
# ============================================================


class TestExportCalibrationInclusion:
    """Story 16.1 / AC-4: calibration assumptions included in exported manifest."""

    def test_calibration_assumptions_present_in_run_manifest(self, tmp_path: Path) -> None:
        result = _make_result(calibration=True)
        meta = export_replication_package(result, tmp_path)

        manifest_path = meta.package_path / "manifests" / "run-manifest.json"
        text = manifest_path.read_text(encoding="utf-8")
        manifest = RunManifest.from_json(text)

        keys = {a["key"] for a in manifest.assumptions}
        assert "calibration.beta_income" in keys
        assert "calibration.run_id" in keys

    def test_calibration_values_correct_in_exported_manifest(self, tmp_path: Path) -> None:
        result = _make_result(calibration=True)
        meta = export_replication_package(result, tmp_path)

        manifest_path = meta.package_path / "manifests" / "run-manifest.json"
        text = manifest_path.read_text(encoding="utf-8")
        manifest = RunManifest.from_json(text)

        beta = next(a for a in manifest.assumptions if a["key"] == "calibration.beta_income")
        assert beta["value"] == -0.0023
        assert beta["source"] == "calibration"

    def test_calibration_also_in_scenario_metadata(self, tmp_path: Path) -> None:
        result = _make_result(calibration=True)
        meta = export_replication_package(result, tmp_path)

        meta_path = meta.package_path / "config" / "scenario-metadata.json"
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        assumption_keys = {a["key"] for a in data["assumptions"]}
        assert "calibration.beta_income" in assumption_keys


# ============================================================
# TestExportValidation — AC all (error paths)
# ============================================================


class TestExportValidation:
    """Story 16.1: input validation raises ReplicationPackageError."""

    def test_failed_result_raises_error(self, tmp_path: Path) -> None:
        result = _make_result(success=False)
        with pytest.raises(ReplicationPackageError, match="success=False"):
            export_replication_package(result, tmp_path)

    def test_missing_panel_output_raises_error(self, tmp_path: Path) -> None:
        # Build a "success" result but with no panel_output
        from reformlab.interfaces.api import SimulationResult

        manifest = _make_manifest()
        result = SimulationResult(
            success=True,
            scenario_id="test",
            yearly_states={},
            panel_output=None,
            manifest=manifest,
        )
        with pytest.raises(ReplicationPackageError, match="panel_output is None"):
            export_replication_package(result, tmp_path)

    def test_nonexistent_output_path_raises_error(self, tmp_path: Path) -> None:
        result = _make_result()
        missing = tmp_path / "does_not_exist"
        with pytest.raises(ReplicationPackageError, match="does not exist"):
            export_replication_package(result, missing)

    def test_file_as_output_path_raises_error(self, tmp_path: Path) -> None:
        result = _make_result()
        file_path = tmp_path / "file.txt"
        file_path.write_text("not a dir", encoding="utf-8")
        with pytest.raises(ReplicationPackageError, match="does not exist or is not a directory"):
            export_replication_package(result, file_path)


# ============================================================
# TestManifestIndexIntegrity — AC-5
# ============================================================


class TestManifestIndexIntegrity:
    """Story 16.1 / AC-5: package-index.json header fields and hash verification."""

    def test_package_index_has_valid_uuid(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        # package_id must be a valid UUID4
        parsed = uuid.UUID(meta.index.package_id)
        assert str(parsed) == meta.index.package_id

    def test_package_index_has_iso_timestamp(self, tmp_path: Path) -> None:
        from datetime import datetime

        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        # created_at must be parseable as ISO 8601
        # Python's fromisoformat handles +00:00 but not Z in 3.10-
        ts = meta.index.created_at
        # Try standard parse
        parsed = datetime.fromisoformat(ts)
        assert parsed is not None

    def test_package_index_has_reformlab_version(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        assert meta.index.reformlab_version == "0.1.0"

    def test_package_index_has_source_manifest_id(self, tmp_path: Path) -> None:
        result = _make_result(manifest_id="test-manifest-001")
        meta = export_replication_package(result, tmp_path)

        assert meta.index.source_manifest_id == "test-manifest-001"

    def test_every_artifact_hash_verifiable(self, tmp_path: Path) -> None:
        """AC-5: verify every artifact hash against actual file."""
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        pkg_dir = meta.package_path
        for artifact in meta.index.artifacts:
            file_path = pkg_dir / artifact.path
            assert file_path.exists(), f"Artifact file missing: {artifact.path}"
            actual = hash_file(file_path)
            assert actual == artifact.hash, f"Hash mismatch for {artifact.path}"

    def test_package_index_json_on_disk_matches_returned_index(self, tmp_path: Path) -> None:
        """Index written to disk must match the returned PackageIndex."""
        result = _make_result()
        meta = export_replication_package(result, tmp_path)

        index_text = (meta.package_path / "package-index.json").read_text(encoding="utf-8")
        disk_index = PackageIndex.from_json(index_text)
        assert disk_index.package_id == meta.index.package_id
        assert disk_index.source_manifest_id == meta.index.source_manifest_id
        assert len(disk_index.artifacts) == len(meta.index.artifacts)


# ============================================================
# TestExportWithChildManifests
# ============================================================


class TestExportWithChildManifests:
    """Story 16.1: child manifest JSON strings written when available."""

    def test_child_manifest_json_written_when_present(self, tmp_path: Path) -> None:
        # Build a child manifest JSON string
        child_manifest = RunManifest(
            manifest_id="22345678-1234-1234-1234-123456789abc",
            created_at="2026-03-07T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="44.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="12345678-1234-1234-1234-123456789abc",
        )
        child_json = child_manifest.to_json()

        result = _make_result(child_manifests_meta={2025: child_json})
        meta = export_replication_package(result, tmp_path)

        year_path = meta.package_path / "manifests" / "year-2025.json"
        assert year_path.exists()
        # Should be valid RunManifest JSON
        loaded = RunManifest.from_json(year_path.read_text(encoding="utf-8"))
        assert loaded.manifest_id == "22345678-1234-1234-1234-123456789abc"

    def test_child_manifest_written_in_artifact_index(self, tmp_path: Path) -> None:
        child_manifest = RunManifest(
            manifest_id="22345678-1234-1234-1234-123456789abc",
            created_at="2026-03-07T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="44.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            parent_manifest_id="12345678-1234-1234-1234-123456789abc",
        )
        result = _make_result(child_manifests_meta={2025: child_manifest.to_json()})
        meta = export_replication_package(result, tmp_path)

        paths = {a.path for a in meta.index.artifacts}
        assert "manifests/year-2025.json" in paths

    def test_uuid_child_manifest_ids_not_written_as_files(self, tmp_path: Path) -> None:
        # Regular manifest has child_manifests as UUID IDs (not JSON strings)
        result = _make_result(child_manifests_meta={2025: "22345678-1234-1234-1234-123456789abc"})
        meta = export_replication_package(result, tmp_path)

        # UUIDs are not JSON strings, so no file should be written
        year_path = meta.package_path / "manifests" / "year-2025.json"
        assert not year_path.exists()


# ============================================================
# TestSimulationResultConvenience — Task 4.2
# ============================================================


class TestSimulationResultConvenience:
    """Story 16.1 / Task 4.2: SimulationResult.export_replication_package() delegates correctly."""

    def test_convenience_method_returns_metadata(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = result.export_replication_package(tmp_path)

        assert isinstance(meta, ReplicationPackageMetadata)
        assert meta.package_path.exists()

    def test_convenience_method_compress_kwarg(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = result.export_replication_package(tmp_path, compress=True)

        assert meta.compressed is True
        assert meta.package_path.suffix == ".zip"

    def test_convenience_method_raises_on_failed_result(self, tmp_path: Path) -> None:
        result = _make_result(success=False)
        with pytest.raises(ReplicationPackageError):
            result.export_replication_package(tmp_path)

    def test_convenience_method_returns_correct_artifact_count(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = result.export_replication_package(tmp_path)
        assert meta.artifact_count == 4


# ============================================================
# Story 16.2 helpers
# ============================================================


def _make_fixed_adapter() -> Any:
    """MockAdapter that always returns a fixed panel table."""
    from reformlab.computation.mock_adapter import MockAdapter

    output = pa.table(
        {
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "year": pa.array([2025, 2025, 2025], type=pa.int64()),
            "carbon_tax": pa.array([150.0, 200.0, 250.0], type=pa.float64()),
        }
    )
    return MockAdapter(default_output=output, version_string="mock-1.0.0")


def _export_and_import(tmp_path: Path, *, compress: bool = False) -> Any:
    """Helper: export a package then import it, returning ImportedPackage."""
    result = _make_result()
    meta = export_replication_package(result, tmp_path, compress=compress)
    return import_replication_package(meta.package_path)


# ============================================================
# TestImportedPackage — Story 16.2 / AC-1
# ============================================================


class TestImportedPackage:
    """Story 16.2 / AC-1: ImportedPackage type correctness."""

    def test_creation_with_all_fields(self, tmp_path: Path) -> None:
        """ImportedPackage has all required typed fields."""
        pkg = _export_and_import(tmp_path)
        assert isinstance(pkg.package_id, str)
        assert isinstance(pkg.source_manifest_id, str)
        assert isinstance(pkg.source_path, Path)
        assert isinstance(pkg.index, PackageIndex)
        assert isinstance(pkg.manifest, RunManifest)
        assert isinstance(pkg.panel_table, pa.Table)
        assert isinstance(pkg.policy, dict)
        assert isinstance(pkg.scenario_metadata, dict)
        assert isinstance(pkg.integrity_verified, bool)

    def test_frozen_immutability(self, tmp_path: Path) -> None:
        """ImportedPackage is frozen."""
        pkg = _export_and_import(tmp_path)
        with pytest.raises((AttributeError, TypeError)):
            pkg.package_id = "mutated"  # type: ignore[misc]

    def test_all_fields_present_in_imported_package(self, tmp_path: Path) -> None:
        """All AC-1 required fields are accessible."""
        pkg = _export_and_import(tmp_path)
        # Policy field
        assert "carbon_tax_rate" in pkg.policy
        # Scenario metadata
        assert "seeds" in pkg.scenario_metadata
        # Manifest
        assert pkg.manifest.manifest_id == "test-manifest-001"
        # Panel table schema
        assert "household_id" in pkg.panel_table.column_names
        assert "year" in pkg.panel_table.column_names


# ============================================================
# TestReproductionResult — Story 16.2 / AC-5
# ============================================================


class TestReproductionResult:
    """Story 16.2 / AC-5: ReproductionResult type and summary format."""

    def _make_result_obj(self, *, passed: bool = True) -> ReproductionResult:
        return ReproductionResult(
            passed=passed,
            integrity_passed=True,
            numerical_match=passed,
            tolerance_used=0.0,
            discrepancies=() if passed else ("Column 'x' row 0: 1.0 vs 2.0 (diff=1.0)",),
            original_manifest_id="abc-123",
            reproduced_result=None,
        )

    def test_creation_with_all_fields(self) -> None:
        result = self._make_result_obj()
        assert result.passed is True
        assert result.integrity_passed is True
        assert result.numerical_match is True
        assert result.tolerance_used == 0.0
        assert result.discrepancies == ()
        assert result.original_manifest_id == "abc-123"
        assert result.reproduced_result is None

    def test_frozen_immutability(self) -> None:
        result = self._make_result_obj()
        with pytest.raises((AttributeError, TypeError)):
            result.passed = False  # type: ignore[misc]

    def test_summary_passed_format(self) -> None:
        """summary() output for a passing reproduction."""
        result = self._make_result_obj(passed=True)
        s = result.summary()
        assert "PASSED" in s
        assert "abc-123" in s
        assert "Integrity check: PASSED" in s
        assert "Numerical match: PASSED" in s
        assert "Discrepancies: 0" in s

    def test_summary_failed_format(self) -> None:
        """summary() output for a failing reproduction includes discrepancy detail."""
        result = self._make_result_obj(passed=False)
        s = result.summary()
        assert "FAILED" in s
        assert "Discrepancies: 1" in s
        assert "Column 'x' row 0" in s

    def test_summary_tolerance_shown(self) -> None:
        result = ReproductionResult(
            passed=True,
            integrity_passed=True,
            numerical_match=True,
            tolerance_used=1.5,
            discrepancies=(),
            original_manifest_id="xyz",
            reproduced_result=None,
        )
        assert "tolerance=1.5" in result.summary()


# ============================================================
# TestImportFromDirectory — Story 16.2 / AC-1, AC-3
# ============================================================


class TestImportFromDirectory:
    """Story 16.2 / AC-1, AC-3: round-trip via directory format."""

    def test_imported_package_manifest_matches(self, tmp_path: Path) -> None:
        result = _make_result(manifest_id="abc-import-dir")
        meta = export_replication_package(result, tmp_path)
        pkg = import_replication_package(meta.package_path)

        assert pkg.manifest.manifest_id == "abc-import-dir"
        assert pkg.source_manifest_id == "abc-import-dir"
        assert pkg.package_id == meta.package_id

    def test_imported_package_policy_matches(self, tmp_path: Path) -> None:
        pkg = _export_and_import(tmp_path)
        assert pkg.policy["carbon_tax_rate"] == 44.6

    def test_imported_package_panel_table_schema_matches(self, tmp_path: Path) -> None:
        pkg = _export_and_import(tmp_path)
        assert "household_id" in pkg.panel_table.column_names
        assert "year" in pkg.panel_table.column_names
        assert "carbon_tax" in pkg.panel_table.column_names
        assert pkg.panel_table.num_rows == 3

    def test_imported_package_index_matches(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)
        pkg = import_replication_package(meta.package_path)

        assert pkg.index.package_id == meta.package_id
        assert len(pkg.index.artifacts) == meta.artifact_count

    def test_integrity_verified_true(self, tmp_path: Path) -> None:
        """AC-3: integrity_verified is True when all hashes match."""
        pkg = _export_and_import(tmp_path)
        assert pkg.integrity_verified is True

    def test_source_path_is_directory(self, tmp_path: Path) -> None:
        pkg = _export_and_import(tmp_path)
        assert pkg.source_path.is_dir()


# ============================================================
# TestImportFromZip — Story 16.2 / AC-1
# ============================================================


class TestImportFromZip:
    """Story 16.2 / AC-1: round-trip via ZIP format handled transparently."""

    def test_imported_package_from_zip_matches_directory(self, tmp_path: Path) -> None:
        result = _make_result(manifest_id="zip-test-001")
        meta = export_replication_package(result, tmp_path, compress=True)
        pkg = import_replication_package(meta.package_path)

        assert pkg.manifest.manifest_id == "zip-test-001"
        assert pkg.integrity_verified is True
        assert pkg.policy["carbon_tax_rate"] == 44.6
        assert pkg.panel_table.num_rows == 3

    def test_imported_package_zip_source_path_is_zip(self, tmp_path: Path) -> None:
        pkg = _export_and_import(tmp_path, compress=True)
        assert pkg.source_path.suffix == ".zip"

    def test_zip_and_directory_produce_equivalent_imports(self, tmp_path: Path) -> None:
        result = _make_result()
        dir_meta = export_replication_package(result, tmp_path)
        zip_meta = export_replication_package(result, tmp_path, compress=True)

        dir_pkg = import_replication_package(dir_meta.package_path)
        zip_pkg = import_replication_package(zip_meta.package_path)

        # Same policy
        assert dir_pkg.policy == zip_pkg.policy
        # Same panel shape
        assert dir_pkg.panel_table.schema == zip_pkg.panel_table.schema
        assert dir_pkg.panel_table.num_rows == zip_pkg.panel_table.num_rows


# ============================================================
# TestImportIntegrityVerification — Story 16.2 / AC-4
# ============================================================


class TestImportIntegrityVerification:
    """Story 16.2 / AC-4: corrupted artifact raises ReplicationPackageError."""

    def test_corrupted_artifact_raises_error_with_path_info(
        self, tmp_path: Path
    ) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)
        pkg_dir = meta.package_path

        # Corrupt the panel parquet file
        parquet_path = pkg_dir / "data" / "panel-output.parquet"
        parquet_path.write_bytes(b"CORRUPTED_CONTENT")

        with pytest.raises(
            ReplicationPackageError,
            match="Integrity check failed for data/panel-output.parquet",
        ):
            import_replication_package(pkg_dir)

    def test_corrupted_artifact_error_contains_expected_hash(
        self, tmp_path: Path
    ) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)
        pkg_dir = meta.package_path

        # Find the expected hash for the policy file
        policy_artifact = next(
            a for a in meta.index.artifacts if a.path == "config/policy.json"
        )
        policy_path = pkg_dir / "config" / "policy.json"
        policy_path.write_text('{"corrupted": true}', encoding="utf-8")

        with pytest.raises(
            ReplicationPackageError, match=policy_artifact.hash[:10]
        ):
            import_replication_package(pkg_dir)


# ============================================================
# TestImportMissingArtifact — Story 16.2 / AC-4
# ============================================================


class TestImportMissingArtifact:
    """Story 16.2 / AC-4: missing artifact raises ReplicationPackageError."""

    def test_missing_parquet_raises_error(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)
        pkg_dir = meta.package_path

        parquet_path = pkg_dir / "data" / "panel-output.parquet"
        parquet_path.unlink()

        with pytest.raises(
            ReplicationPackageError,
            match="Artifact missing: data/panel-output.parquet",
        ):
            import_replication_package(pkg_dir)

    def test_missing_policy_json_raises_error(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)
        pkg_dir = meta.package_path

        (pkg_dir / "config" / "policy.json").unlink()

        with pytest.raises(
            ReplicationPackageError,
            match="Artifact missing: config/policy.json",
        ):
            import_replication_package(pkg_dir)


# ============================================================
# TestImportMissingIndex — Story 16.2 / AC-4
# ============================================================


class TestImportMissingIndex:
    """Story 16.2 / AC-4: missing package-index.json raises ReplicationPackageError."""

    def test_missing_index_raises_error(self, tmp_path: Path) -> None:
        result = _make_result()
        meta = export_replication_package(result, tmp_path)
        pkg_dir = meta.package_path

        (pkg_dir / "package-index.json").unlink()

        with pytest.raises(
            ReplicationPackageError,
            match="package-index.json not found",
        ):
            import_replication_package(pkg_dir)


# ============================================================
# TestImportInvalidPath — Story 16.2 / AC-4
# ============================================================


class TestImportInvalidPath:
    """Story 16.2 / AC-4: invalid paths raise ReplicationPackageError."""

    def test_nonexistent_path_raises_error(self, tmp_path: Path) -> None:
        missing = tmp_path / "no_such_package"
        with pytest.raises(
            ReplicationPackageError,
            match="does not exist",
        ):
            import_replication_package(missing)

    def test_file_not_zip_raises_error(self, tmp_path: Path) -> None:
        not_a_zip = tmp_path / "package.txt"
        not_a_zip.write_text("not a zip", encoding="utf-8")
        with pytest.raises(
            ReplicationPackageError,
            match="must be a directory or .zip archive",
        ):
            import_replication_package(not_a_zip)

    def test_zip_with_multiple_root_dirs_raises_error(self, tmp_path: Path) -> None:
        """ZIP with multiple root dirs raises ReplicationPackageError."""
        bad_zip = tmp_path / "bad.zip"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("dir_a/file.txt", "a")
            zf.writestr("dir_b/file.txt", "b")

        with pytest.raises(
            ReplicationPackageError,
            match="Expected a single root directory",
        ):
            import_replication_package(bad_zip)


# ============================================================
# TestReproduceFromPackage — Story 16.2 / AC-2
# ============================================================


class TestReproduceFromPackage:
    """Story 16.2 / AC-2: export → import → reproduce → passed=True."""

    def test_reproduce_passes_with_same_adapter(self, tmp_path: Path) -> None:
        adapter = _make_fixed_adapter()
        result = _make_result()
        meta = export_replication_package(result, tmp_path)
        pkg = import_replication_package(meta.package_path)
        repro = reproduce_from_package(pkg, adapter)

        assert repro.passed is True
        assert repro.numerical_match is True
        assert repro.integrity_passed is True
        assert repro.discrepancies == ()

    def test_reproduce_returns_reproduction_result_type(self, tmp_path: Path) -> None:
        adapter = _make_fixed_adapter()
        pkg = _export_and_import(tmp_path)
        repro = reproduce_from_package(pkg, adapter)
        assert isinstance(repro, ReproductionResult)

    def test_reproduce_original_manifest_id_matches(self, tmp_path: Path) -> None:
        adapter = _make_fixed_adapter()
        result = _make_result(manifest_id="repro-manifest-001")
        meta = export_replication_package(result, tmp_path)
        pkg = import_replication_package(meta.package_path)
        repro = reproduce_from_package(pkg, adapter)

        assert repro.original_manifest_id == "repro-manifest-001"

    def test_reproduce_result_stored_on_success(self, tmp_path: Path) -> None:
        adapter = _make_fixed_adapter()
        pkg = _export_and_import(tmp_path)
        repro = reproduce_from_package(pkg, adapter)

        assert repro.reproduced_result is not None


# ============================================================
# TestReproduceWithTolerance — Story 16.2 / AC-2
# ============================================================


class TestReproduceWithTolerance:
    """Story 16.2 / AC-2: tolerance=0 fails, tolerance=1 passes for small diff."""

    def test_strict_tolerance_fails_on_different_output(self, tmp_path: Path) -> None:
        """Adapter producing slightly different values fails strict comparison."""
        from reformlab.computation.mock_adapter import MockAdapter

        # Export with original adapter
        original_adapter = _make_fixed_adapter()
        result = _make_result()
        meta = export_replication_package(result, tmp_path)
        pkg = import_replication_package(meta.package_path)

        # Reproduce with slightly different adapter output (+0.001 offset)
        different_output = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "year": pa.array([2025, 2025, 2025], type=pa.int64()),
                "carbon_tax": pa.array([150.001, 200.001, 250.001], type=pa.float64()),
            }
        )
        different_adapter = MockAdapter(
            default_output=different_output, version_string="mock-1.0.0"
        )

        repro_strict = reproduce_from_package(pkg, different_adapter, tolerance=0.0)
        assert repro_strict.passed is False
        assert repro_strict.numerical_match is False
        assert len(repro_strict.discrepancies) > 0

        _ = original_adapter  # referenced to avoid linter warnings

    def test_wide_tolerance_passes_on_small_diff(self, tmp_path: Path) -> None:
        """Adapter with 0.001 diff passes with tolerance=1.0."""
        from reformlab.computation.mock_adapter import MockAdapter

        result = _make_result()
        meta = export_replication_package(result, tmp_path)
        pkg = import_replication_package(meta.package_path)

        different_output = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "year": pa.array([2025, 2025, 2025], type=pa.int64()),
                "carbon_tax": pa.array([150.001, 200.001, 250.001], type=pa.float64()),
            }
        )
        different_adapter = MockAdapter(
            default_output=different_output, version_string="mock-1.0.0"
        )

        repro_loose = reproduce_from_package(pkg, different_adapter, tolerance=1.0)
        assert repro_loose.passed is True
        assert repro_loose.numerical_match is True


# ============================================================
# TestReproduceComparisonReport — Story 16.2 / AC-5
# ============================================================


class TestReproduceComparisonReport:
    """Story 16.2 / AC-5: ReproductionResult.summary() contains expected sections."""

    def test_summary_contains_status_section(self, tmp_path: Path) -> None:
        adapter = _make_fixed_adapter()
        pkg = _export_and_import(tmp_path)
        repro = reproduce_from_package(pkg, adapter)
        s = repro.summary()
        assert "Status:" in s

    def test_summary_contains_integrity_section(self, tmp_path: Path) -> None:
        adapter = _make_fixed_adapter()
        pkg = _export_and_import(tmp_path)
        repro = reproduce_from_package(pkg, adapter)
        s = repro.summary()
        assert "Integrity check:" in s

    def test_summary_contains_match_info(self, tmp_path: Path) -> None:
        adapter = _make_fixed_adapter()
        pkg = _export_and_import(tmp_path)
        repro = reproduce_from_package(pkg, adapter)
        s = repro.summary()
        assert "Numerical match:" in s
        assert "tolerance=" in s

    def test_summary_contains_original_manifest_id(self, tmp_path: Path) -> None:
        result = _make_result(manifest_id="summary-manifest-001")
        meta = export_replication_package(result, tmp_path)
        pkg = import_replication_package(meta.package_path)
        adapter = _make_fixed_adapter()
        repro = reproduce_from_package(pkg, adapter)
        s = repro.summary()
        assert "summary-manifest-001" in s


# ============================================================
# TestReproduceFailure — Story 16.2 / AC-2
# ============================================================


class TestReproduceFailure:
    """Story 16.2 / AC-2: adapter exception → passed=False, error in discrepancies."""

    def test_failing_adapter_produces_failed_result(self, tmp_path: Path) -> None:
        from reformlab.computation.mock_adapter import MockAdapter
        from reformlab.computation.types import PolicyConfig, PopulationData

        def _always_fails(
            pop: PopulationData, pol: PolicyConfig, period: int
        ) -> pa.Table:
            raise RuntimeError("Adapter exploded")

        failing_adapter = MockAdapter(
            compute_fn=_always_fails, version_string="failing-1.0.0"
        )
        pkg = _export_and_import(tmp_path)
        repro = reproduce_from_package(pkg, failing_adapter)

        assert repro.passed is False
        assert repro.numerical_match is False
        assert repro.reproduced_result is None
        assert len(repro.discrepancies) > 0
        assert "failed" in repro.discrepancies[0].lower()


# ============================================================
# TestImportedPackageConvenience — Story 16.2 / AC-2
# ============================================================


class TestImportedPackageConvenience:
    """Story 16.2 / AC-2: ImportedPackage.reproduce() delegates to reproduce_from_package()."""

    def test_convenience_reproduce_returns_reproduction_result(
        self, tmp_path: Path
    ) -> None:
        adapter = _make_fixed_adapter()
        pkg = _export_and_import(tmp_path)
        repro = pkg.reproduce(adapter)
        assert isinstance(repro, ReproductionResult)

    def test_convenience_reproduce_passes_with_same_adapter(
        self, tmp_path: Path
    ) -> None:
        adapter = _make_fixed_adapter()
        pkg = _export_and_import(tmp_path)
        repro = pkg.reproduce(adapter)
        assert repro.passed is True

    def test_convenience_reproduce_forwards_tolerance(self, tmp_path: Path) -> None:
        adapter = _make_fixed_adapter()
        pkg = _export_and_import(tmp_path)
        repro = pkg.reproduce(adapter, tolerance=0.5)
        assert repro.tolerance_used == 0.5
