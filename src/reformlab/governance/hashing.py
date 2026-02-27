"""Artifact hashing and verification for reproducibility.

Provides SHA-256 hashing of input/output files for integrity verification.
All hashing uses streaming/chunked reads for memory efficiency with large files.

This module implements FR25 (immutable run manifests with data hashes) and NFR12
(input paths referenced not embedded).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

# 64KB chunks for memory-efficient hashing of large CSV/Parquet files
CHUNK_SIZE = 65536


def hash_file(path: Path) -> str:
    """Compute SHA-256 hash of a file using streaming reads.

    Uses 64KB chunks for memory efficiency with large files (up to 500k households).
    Hash computation is deterministic across machines and platforms.

    Args:
        path: Path to the file to hash.

    Returns:
        SHA-256 hex digest (64 lowercase hex characters).

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """
    sha256 = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha256.update(chunk)
    return sha256.hexdigest()


def hash_input_artifacts(paths: dict[str, Path]) -> dict[str, str]:
    """Compute SHA-256 hashes for input data files.

    Args:
        paths: Dictionary mapping path keys to file paths.
               Keys are used as references in the manifest.

    Returns:
        Dictionary mapping path keys to SHA-256 hex digests.

    Raises:
        FileNotFoundError: If any input file is missing (with path context).
        OSError: If any file cannot be read.
    """
    hashes: dict[str, str] = {}
    for key, path in paths.items():
        try:
            hashes[key] = hash_file(path)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Input file not found for key '{key}': {path}"
            ) from e
        except OSError as e:
            raise OSError(f"Cannot read input file '{key}' at {path}: {e}") from e
    return hashes


def hash_output_artifacts(paths: dict[str, Path]) -> dict[str, str]:
    """Compute SHA-256 hashes for output artifacts.

    Output artifacts include: yearly panel datasets, indicator exports,
    comparison tables.

    Args:
        paths: Dictionary mapping artifact keys to file paths.
               Keys are used as references in the manifest.

    Returns:
        Dictionary mapping artifact keys to SHA-256 hex digests.

    Raises:
        FileNotFoundError: If any output file is missing (with path context).
        OSError: If any file cannot be read.
    """
    hashes: dict[str, str] = {}
    for key, path in paths.items():
        try:
            hashes[key] = hash_file(path)
        except FileNotFoundError as e:
            raise FileNotFoundError(
                f"Output file not found for key '{key}': {path}"
            ) from e
        except OSError as e:
            raise OSError(f"Cannot read output file '{key}' at {path}: {e}") from e
    return hashes


@dataclass(frozen=True)
class ArtifactVerificationResult:
    """Result of artifact hash verification.

    Attributes:
        passed: True if all hashes match, False otherwise.
        mismatches: List of path keys where hash does not match expected.
        missing: List of path keys where file was not found.
    """

    passed: bool
    mismatches: list[str]
    missing: list[str]


def verify_artifact_hashes(
    manifest_hashes: dict[str, str],
    artifact_paths: dict[str, Path],
) -> ArtifactVerificationResult:
    """Verify stored hashes against current file contents.

    Compares hashes in the manifest against recomputed hashes from files.
    Does not raise exceptions on mismatch - returns structured result.

    Args:
        manifest_hashes: Hashes stored in manifest (data_hashes or output_hashes).
        artifact_paths: Dictionary mapping keys to current file paths.

    Returns:
        ArtifactVerificationResult with verification status and diagnostics.
    """
    mismatches: list[str] = []
    missing: list[str] = []

    for key, expected_hash in manifest_hashes.items():
        # Check if path exists in provided artifacts
        if key not in artifact_paths:
            missing.append(key)
            continue

        path = artifact_paths[key]

        # Try to compute current hash
        try:
            actual_hash = hash_file(path)
        except FileNotFoundError:
            missing.append(key)
            continue
        except OSError:
            # File exists but can't be read - treat as missing
            missing.append(key)
            continue

        # Compare hashes
        if actual_hash != expected_hash:
            mismatches.append(key)

    passed = len(mismatches) == 0 and len(missing) == 0

    return ArtifactVerificationResult(
        passed=passed,
        mismatches=mismatches,
        missing=missing,
    )
