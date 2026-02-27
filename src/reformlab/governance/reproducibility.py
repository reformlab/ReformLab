"""Reproducibility check harness for simulation runs.

This module provides functionality to re-execute simulation runs using manifests
and verify outputs are bit-identical or within tolerances. Implements NFR6
(bit-identical on same machine) and NFR7 (identical across machines).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pyarrow as pa
import pyarrow.csv as pa_csv
import pyarrow.parquet as pq

from reformlab.governance.hashing import verify_artifact_hashes
from reformlab.governance.manifest import RunManifest


@dataclass(frozen=True)
class ReproducibilityResult:
    """Result of reproducibility check.

    Attributes:
        passed: True if all hashes match or are within tolerance, False otherwise.
        hash_mismatches: List of artifact keys where hash does not match expected.
        missing_artifacts: List of artifact keys where file was not found.
        rerun_seeds: Seeds used in the rerun execution.
        original_seeds: Seeds from the original manifest.
        year_range: Tuple of (start_year, end_year) executed.
        tolerance_used: Floating-point tolerance used for soft comparison.
    """

    passed: bool
    hash_mismatches: list[str]
    missing_artifacts: list[str]
    rerun_seeds: dict[str, int]
    original_seeds: dict[str, int]
    year_range: tuple[int, int]
    tolerance_used: float

    def details(self) -> str:
        """Return human-readable diagnostic summary.

        Returns:
            Formatted string with check status and diagnostics.
        """
        lines = [f"Reproducibility check: {'PASSED' if self.passed else 'FAILED'}"]
        lines.append(f"Year range: {self.year_range[0]}-{self.year_range[1]}")
        lines.append(f"Tolerance: {self.tolerance_used}")

        if self.original_seeds:
            lines.append(f"Original seeds: {self.original_seeds}")
        if self.rerun_seeds:
            lines.append(f"Rerun seeds: {self.rerun_seeds}")

        if self.hash_mismatches:
            lines.append(f"Hash mismatches ({len(self.hash_mismatches)}): ")
            for key in self.hash_mismatches:
                lines.append(f"  - {key}")

        if self.missing_artifacts:
            lines.append(f"Missing artifacts ({len(self.missing_artifacts)}): ")
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
    """Re-execute a run and verify outputs match original.

    This function orchestrates a full reproducibility check cycle:
    1. Extract rerun parameters from the manifest
    2. Execute the rerun via the provided callable
    3. Compare output hashes against the original manifest
    4. Optionally perform tolerance-based soft comparison for mismatches

    The governance harness delegates execution to the caller-provided rerun_callable
    to preserve subsystem boundaries. The harness does not instantiate orchestrator
    components directly.

    Args:
        manifest: Original run manifest with seeds, parameters, hashes.
        input_paths: Mapping of manifest data_hash keys to current file paths.
        output_paths: Mapping of manifest output_hash keys to rerun output paths.
        rerun_callable: Callable that executes the rerun using manifest-derived config.
                       The callable is responsible for orchestration - this harness
                       only validates reproducibility.
        tolerance: Floating-point tolerance for soft comparison (0.0 = strict).
                  When tolerance > 0, artifacts that fail strict hash checks are
                  compared numerically against reference outputs.
        reference_output_paths: Optional original output artifact paths used for
                               tolerance-based comparisons when strict hashes differ.
                               Required when tolerance > 0.

    Returns:
        ReproducibilityResult with comparison outcome and diagnostics.

    Raises:
        ValueError: If tolerance validation fails (negative tolerance, tolerance > 0
                   without reference_output_paths).
    """
    # Validate tolerance contract
    if tolerance < 0:
        raise ValueError(f"tolerance must be >= 0, got {tolerance}")

    if tolerance > 0 and not reference_output_paths:
        raise ValueError(
            "reference_output_paths is required when tolerance > 0 for soft comparison"
        )

    # Extract year range from child_manifests keys
    year_range = _extract_year_range(manifest)

    # Extract seeds
    original_seeds = dict(manifest.seeds)
    master_seed = manifest.seeds.get("master")
    rerun_seeds = {"master": master_seed} if master_seed is not None else {}

    # Execute rerun via callable (governance does not construct orchestrator directly)
    # The callable is responsible for setting up and executing the rerun
    rerun_callable()

    # Compare outputs using strict hash verification
    verification = verify_artifact_hashes(manifest.output_hashes, output_paths)

    # If strict verification passes or tolerance is zero, return strict result
    if verification.passed or tolerance == 0.0:
        return ReproducibilityResult(
            passed=verification.passed,
            hash_mismatches=verification.mismatches,
            missing_artifacts=verification.missing,
            rerun_seeds=rerun_seeds,
            original_seeds=original_seeds,
            year_range=year_range,
            tolerance_used=tolerance,
        )

    # Perform tolerance-based soft comparison for hash mismatches
    return _compare_with_tolerance(
        manifest=manifest,
        output_paths=output_paths,
        reference_output_paths=reference_output_paths,
        strict_verification=verification,
        tolerance=tolerance,
        year_range=year_range,
        rerun_seeds=rerun_seeds,
        original_seeds=original_seeds,
    )


def _extract_year_range(manifest: RunManifest) -> tuple[int, int]:
    """Extract year range from manifest child_manifests keys.

    Args:
        manifest: Run manifest with child_manifests dictionary.

    Returns:
        Tuple of (min_year, max_year) from child_manifests keys,
        or (0, 0) if no child manifests.
    """
    if not manifest.child_manifests:
        return (0, 0)

    years = list(manifest.child_manifests.keys())
    return (min(years), max(years))


def _compare_with_tolerance(
    manifest: RunManifest,
    output_paths: dict[str, Path],
    reference_output_paths: dict[str, Path] | None,
    strict_verification: Any,
    tolerance: float,
    year_range: tuple[int, int],
    rerun_seeds: dict[str, int],
    original_seeds: dict[str, int],
) -> ReproducibilityResult:
    """Perform tolerance-based soft comparison for artifacts with hash mismatches.

    Only compares artifacts that failed strict hash checks. For each mismatch,
    loads both the rerun output and reference output and compares numeric columns
    within tolerance.

    Args:
        manifest: Original run manifest.
        output_paths: Rerun output artifact paths.
        reference_output_paths: Original output artifact paths for comparison.
        strict_verification: Result from strict hash verification.
        tolerance: Floating-point tolerance for numeric comparison.
        year_range: Year range executed.
        rerun_seeds: Seeds used in rerun.
        original_seeds: Original seeds from manifest.

    Returns:
        ReproducibilityResult with soft comparison outcome.
    """
    # Start with strict verification results
    remaining_mismatches = list(strict_verification.mismatches)
    missing = list(strict_verification.missing)

    # For each hash mismatch, try soft comparison
    for key in strict_verification.mismatches:
        # Check if we have both rerun and reference paths
        if key not in output_paths:
            # Already in missing list from strict verification
            continue

        if not reference_output_paths or key not in reference_output_paths:
            # Missing reference for soft comparison - keep as mismatch
            # This is explicitly documented: no silent pass/fallback
            continue

        rerun_path = output_paths[key]
        reference_path = reference_output_paths[key]

        # Try to load and compare artifacts
        if _artifacts_match_within_tolerance(rerun_path, reference_path, tolerance):
            # Soft comparison passed - remove from mismatches
            remaining_mismatches.remove(key)

    # Check passed if no remaining mismatches and no missing artifacts
    passed = len(remaining_mismatches) == 0 and len(missing) == 0

    return ReproducibilityResult(
        passed=passed,
        hash_mismatches=remaining_mismatches,
        missing_artifacts=missing,
        rerun_seeds=rerun_seeds,
        original_seeds=original_seeds,
        year_range=year_range,
        tolerance_used=tolerance,
    )


def _artifacts_match_within_tolerance(
    rerun_path: Path,
    reference_path: Path,
    tolerance: float,
) -> bool:
    """Compare two artifact files within tolerance.

    Supports Parquet and CSV files. Compares numeric columns within tolerance,
    requires exact match for non-numeric columns.

    Args:
        rerun_path: Path to rerun output artifact.
        reference_path: Path to reference (original) output artifact.
        tolerance: Floating-point tolerance for numeric comparison.

    Returns:
        True if artifacts match within tolerance, False otherwise.
    """
    try:
        # Determine file type by extension
        if rerun_path.suffix.lower() == ".parquet":
            rerun_table = pq.read_table(rerun_path)
            reference_table = pq.read_table(reference_path)
        elif rerun_path.suffix.lower() == ".csv":
            rerun_table = pa_csv.read_csv(rerun_path)
            reference_table = pa_csv.read_csv(reference_path)
        else:
            # Unknown file type - cannot perform soft comparison
            return False

        # Check schema match
        if rerun_table.schema != reference_table.schema:
            return False

        # Check row count match
        if len(rerun_table) != len(reference_table):
            return False

        # Check column count match
        if rerun_table.num_columns != reference_table.num_columns:
            return False

        # Compare each column
        for col_name in rerun_table.column_names:
            rerun_col = rerun_table.column(col_name)
            reference_col = reference_table.column(col_name)

            # Check if column is numeric
            if pa.types.is_floating(rerun_col.type) or pa.types.is_integer(
                rerun_col.type
            ):
                # Numeric column - compare within tolerance
                if not _numeric_columns_match(rerun_col, reference_col, tolerance):
                    return False
            else:
                # Non-numeric column - require exact match
                if not rerun_col.equals(reference_col):
                    return False

        return True

    except Exception:
        # Any error during comparison means mismatch
        return False


def _numeric_columns_match(
    rerun_col: pa.ChunkedArray,
    reference_col: pa.ChunkedArray,
    tolerance: float,
) -> bool:
    """Compare two numeric columns within tolerance.

    Args:
        rerun_col: Rerun output column.
        reference_col: Reference (original) output column.
        tolerance: Absolute tolerance for numeric comparison.

    Returns:
        True if all values match within tolerance, False otherwise.
    """
    # Convert to numpy for efficient comparison
    rerun_arr = rerun_col.to_numpy()
    reference_arr = reference_col.to_numpy()

    # Check for null mismatches
    if (rerun_arr is None) != (reference_arr is None):
        return False

    # Compute absolute differences
    try:
        abs_diff = abs(rerun_arr - reference_arr)
        return bool((abs_diff <= tolerance).all())
    except Exception:
        return False
