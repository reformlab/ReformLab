"""Reproducibility check harness for simulation runs.

This module re-executes simulation runs using manifest-derived inputs and seeds
and verifies output artifacts are bit-identical or, when configured, within
numeric tolerances for floating-point drift.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.csv as pa_csv
import pyarrow.parquet as pq

from reformlab.governance.errors import ReproducibilityValidationError
from reformlab.governance.hashing import (
    ArtifactVerificationResult,
    verify_artifact_hashes,
)
from reformlab.governance.manifest import RunManifest


@dataclass(frozen=True)
class ReproducibilityResult:
    """Result of reproducibility check."""

    passed: bool
    hash_mismatches: list[str]
    missing_artifacts: list[str]
    rerun_seeds: dict[str, int]
    original_seeds: dict[str, int]
    year_range: tuple[int, int]
    tolerance_used: float

    def details(self) -> str:
        """Return human-readable diagnostic summary."""
        lines = [f"Reproducibility check: {'PASSED' if self.passed else 'FAILED'}"]
        lines.append(f"Year range: {self.year_range[0]}-{self.year_range[1]}")
        lines.append(f"Tolerance: {self.tolerance_used}")

        if self.original_seeds:
            lines.append(f"Original seeds: {self.original_seeds}")
        if self.rerun_seeds:
            lines.append(f"Rerun seeds: {self.rerun_seeds}")

        if self.hash_mismatches:
            lines.append(f"Hash mismatches ({len(self.hash_mismatches)}):")
            for key in self.hash_mismatches:
                lines.append(f"  - {key}")

        if self.missing_artifacts:
            lines.append(f"Missing artifacts ({len(self.missing_artifacts)}):")
            for key in self.missing_artifacts:
                lines.append(f"  - {key}")

        return "\n".join(lines)


def check_reproducibility(
    manifest: RunManifest,
    input_paths: dict[str, Path],
    output_paths: dict[str, Path],
    rerun_callable: Callable[..., Any],
    tolerance: float = 0.0,
    reference_output_paths: dict[str, Path] | None = None,
) -> ReproducibilityResult:
    """Re-execute a run and verify outputs match original artifacts.

    Args:
        manifest: Original run manifest with seeds, parameters, and hashes.
        input_paths: Mapping of data-hash keys to input file paths.
        output_paths: Mapping of output-hash keys to rerun output file paths.
        rerun_callable: Callable invoked to execute the rerun. It receives
            manifest-derived context:
            seeds, parameters, scenario_version, step_pipeline, year_range,
            and input_paths.
        tolerance: Floating-point tolerance for soft comparison. Defaults to
            strict, bit-identical verification.
        reference_output_paths: Baseline output files used when `tolerance > 0`.

    Returns:
        Structured reproducibility result with diagnostics.
    """
    _validate_tolerance_contract(tolerance, reference_output_paths)
    _validate_required_input_paths(manifest, input_paths)

    year_range = _extract_year_range(manifest)
    original_seeds = dict(manifest.seeds)
    rerun_seeds = dict(manifest.seeds)

    rerun_inputs = (
        {key: input_paths[key] for key in manifest.data_hashes}
        if manifest.data_hashes
        else dict(input_paths)
    )

    rerun_callable(
        seeds=dict(manifest.seeds),
        parameters=dict(manifest.parameters),
        scenario_version=manifest.scenario_version,
        step_pipeline=list(manifest.step_pipeline),
        year_range=year_range,
        input_paths=rerun_inputs,
    )

    strict_verification = verify_artifact_hashes(manifest.output_hashes, output_paths)
    if strict_verification.passed or tolerance == 0.0:
        return ReproducibilityResult(
            passed=strict_verification.passed,
            hash_mismatches=strict_verification.mismatches,
            missing_artifacts=strict_verification.missing,
            rerun_seeds=rerun_seeds,
            original_seeds=original_seeds,
            year_range=year_range,
            tolerance_used=tolerance,
        )

    return _compare_with_tolerance(
        output_paths=output_paths,
        reference_output_paths=reference_output_paths or {},
        strict_verification=strict_verification,
        tolerance=tolerance,
        year_range=year_range,
        rerun_seeds=rerun_seeds,
        original_seeds=original_seeds,
    )


def _validate_tolerance_contract(
    tolerance: float,
    reference_output_paths: dict[str, Path] | None,
) -> None:
    """Validate tolerance configuration before running reproducibility checks."""
    if tolerance < 0:
        raise ReproducibilityValidationError(f"tolerance must be >= 0, got {tolerance}")
    if tolerance > 0 and reference_output_paths is None:
        raise ReproducibilityValidationError(
            "reference_output_paths is required when tolerance > 0 for soft comparison"
        )


def _validate_required_input_paths(
    manifest: RunManifest,
    input_paths: dict[str, Path],
) -> None:
    """Ensure all manifest data-hash keys are present in input path mapping."""
    missing_keys = sorted(set(manifest.data_hashes) - set(input_paths))
    if missing_keys:
        raise ReproducibilityValidationError(
            "Missing input_paths keys required by manifest.data_hashes: "
            + ", ".join(missing_keys)
        )


def _extract_year_range(manifest: RunManifest) -> tuple[int, int]:
    """Extract `(start_year, end_year)` from manifest child-manifest keys."""
    if not manifest.child_manifests:
        return (0, 0)

    years = list(manifest.child_manifests.keys())
    return (min(years), max(years))


def _compare_with_tolerance(
    output_paths: dict[str, Path],
    reference_output_paths: dict[str, Path],
    strict_verification: ArtifactVerificationResult,
    tolerance: float,
    year_range: tuple[int, int],
    rerun_seeds: dict[str, int],
    original_seeds: dict[str, int],
) -> ReproducibilityResult:
    """Perform tolerance-based soft comparison for strict hash mismatches."""
    remaining_mismatches = list(strict_verification.mismatches)
    missing_artifacts = list(strict_verification.missing)
    missing_references: list[str] = []

    for key in strict_verification.mismatches:
        rerun_path = output_paths.get(key)
        if rerun_path is None:
            continue

        reference_path = reference_output_paths.get(key)
        if reference_path is None or not reference_path.exists():
            missing_references.append(f"reference:{key}")
            continue

        if _artifacts_match_within_tolerance(rerun_path, reference_path, tolerance):
            remaining_mismatches.remove(key)

    merged_missing = _merge_unique(missing_artifacts, missing_references)
    passed = not remaining_mismatches and not merged_missing

    return ReproducibilityResult(
        passed=passed,
        hash_mismatches=remaining_mismatches,
        missing_artifacts=merged_missing,
        rerun_seeds=rerun_seeds,
        original_seeds=original_seeds,
        year_range=year_range,
        tolerance_used=tolerance,
    )


def _merge_unique(primary: list[str], secondary: list[str]) -> list[str]:
    """Merge two ordered string lists while keeping first-seen order."""
    merged = list(primary)
    for value in secondary:
        if value not in merged:
            merged.append(value)
    return merged


def _artifacts_match_within_tolerance(
    rerun_path: Path,
    reference_path: Path,
    tolerance: float,
) -> bool:
    """Compare two CSV/Parquet artifact files within tolerance."""
    if rerun_path.suffix.lower() != reference_path.suffix.lower():
        return False

    try:
        rerun_table = _read_table(rerun_path)
        reference_table = _read_table(reference_path)
    except (OSError, pa.ArrowException):
        return False

    if rerun_table.schema != reference_table.schema:
        return False
    if len(rerun_table) != len(reference_table):
        return False
    if rerun_table.num_columns != reference_table.num_columns:
        return False

    for col_name in rerun_table.column_names:
        rerun_col = rerun_table.column(col_name)
        reference_col = reference_table.column(col_name)

        if pa.types.is_floating(rerun_col.type) or pa.types.is_integer(rerun_col.type):
            if not _numeric_columns_match(rerun_col, reference_col, tolerance):
                return False
        elif rerun_col.to_pylist() != reference_col.to_pylist():
            return False

    return True


def _read_table(path: Path) -> pa.Table:
    """Read a CSV/Parquet file as a PyArrow table."""
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pq.read_table(path)
    if suffix == ".csv":
        return pa_csv.read_csv(path)
    raise pa.ArrowInvalid(f"Unsupported artifact type for tolerance check: {path}")


def _numeric_columns_match(
    rerun_col: pa.ChunkedArray,
    reference_col: pa.ChunkedArray,
    tolerance: float,
) -> bool:
    """Compare two numeric columns within an absolute tolerance."""
    rerun_values = rerun_col.to_pylist()
    reference_values = reference_col.to_pylist()

    if len(rerun_values) != len(reference_values):
        return False

    for rerun_value, reference_value in zip(
        rerun_values, reference_values, strict=True
    ):
        if rerun_value is None or reference_value is None:
            if rerun_value != reference_value:
                return False
            continue

        if abs(float(rerun_value) - float(reference_value)) > tolerance:
            return False

    return True
