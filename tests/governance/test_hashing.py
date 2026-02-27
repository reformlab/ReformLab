"""Tests for artifact hashing and verification.

Tests cover:
- hash_file with small and large files
- hash determinism (same content → same hash)
- hash_input_artifacts and hash_output_artifacts
- verify_artifact_hashes success and mismatch cases
- Error handling for missing/unreadable files
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reformlab.governance import (
    ArtifactVerificationResult,
    hash_file,
    hash_input_artifacts,
    hash_output_artifacts,
    verify_artifact_hashes,
)


class TestHashFile:
    """Tests for hash_file function."""

    def test_hash_small_file(self, tmp_path: Path) -> None:
        """Test hashing a small file (< 1KB)."""
        test_file = tmp_path / "small.txt"
        test_file.write_text("Hello, ReformLab!")

        hash_value = hash_file(test_file)

        # SHA-256 hash should be 64 hex characters
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_hash_large_file(self, tmp_path: Path) -> None:
        """Test hashing a large file (> 64KB) to exercise chunking."""
        test_file = tmp_path / "large.bin"
        # Create 200KB file
        large_data = b"x" * (200 * 1024)
        test_file.write_bytes(large_data)

        hash_value = hash_file(test_file)

        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_hash_determinism(self, tmp_path: Path) -> None:
        """Test that same content produces same hash across multiple calls."""
        test_file = tmp_path / "determinism.csv"
        content = "year,income,tax\n2025,50000,10000\n2026,52000,10500\n"
        test_file.write_text(content)

        hash1 = hash_file(test_file)
        hash2 = hash_file(test_file)
        hash3 = hash_file(test_file)

        assert hash1 == hash2 == hash3

    def test_hash_different_content_different_hash(self, tmp_path: Path) -> None:
        """Test that different content produces different hashes."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_text("Population data A")
        file2.write_text("Population data B")

        hash1 = hash_file(file1)
        hash2 = hash_file(file2)

        assert hash1 != hash2

    def test_hash_file_not_found(self, tmp_path: Path) -> None:
        """Test that missing file raises FileNotFoundError."""
        missing_file = tmp_path / "missing.csv"

        with pytest.raises(FileNotFoundError):
            hash_file(missing_file)

    def test_hash_binary_file(self, tmp_path: Path) -> None:
        """Test hashing binary Parquet-like file."""
        test_file = tmp_path / "data.parquet"
        # Simulate binary content
        binary_data = bytes(range(256)) * 100
        test_file.write_bytes(binary_data)

        hash_value = hash_file(test_file)

        assert len(hash_value) == 64


class TestHashInputArtifacts:
    """Tests for hash_input_artifacts function."""

    def test_hash_single_input(self, tmp_path: Path) -> None:
        """Test hashing a single input file."""
        input_file = tmp_path / "population.csv"
        input_file.write_text("household_id,income\n1,50000\n2,60000\n")

        paths = {"population.csv": input_file}
        hashes = hash_input_artifacts(paths)

        assert "population.csv" in hashes
        assert len(hashes["population.csv"]) == 64

    def test_hash_multiple_inputs(self, tmp_path: Path) -> None:
        """Test hashing multiple input files."""
        pop_file = tmp_path / "population.csv"
        emissions_file = tmp_path / "emissions.parquet"

        pop_file.write_text("id,income\n1,50000\n")
        emissions_file.write_bytes(b"PARQUET_DATA")

        paths = {
            "population.csv": pop_file,
            "emissions.parquet": emissions_file,
        }
        hashes = hash_input_artifacts(paths)

        assert len(hashes) == 2
        assert "population.csv" in hashes
        assert "emissions.parquet" in hashes
        assert hashes["population.csv"] != hashes["emissions.parquet"]

    def test_hash_input_missing_file(self, tmp_path: Path) -> None:
        """Test that missing input file raises FileNotFoundError with context."""
        missing = tmp_path / "missing.csv"
        paths = {"population": missing}

        with pytest.raises(FileNotFoundError) as exc_info:
            hash_input_artifacts(paths)

        assert "population" in str(exc_info.value)
        assert str(missing) in str(exc_info.value)

    def test_hash_empty_input_dict(self) -> None:
        """Test hashing empty input dictionary returns empty dict."""
        hashes = hash_input_artifacts({})
        assert hashes == {}


class TestHashOutputArtifacts:
    """Tests for hash_output_artifacts function."""

    def test_hash_single_output(self, tmp_path: Path) -> None:
        """Test hashing a single output artifact."""
        output_file = tmp_path / "results_2025.csv"
        output_file.write_text("household_id,tax_paid\n1,5000\n2,6000\n")

        paths = {"results/2025.csv": output_file}
        hashes = hash_output_artifacts(paths)

        assert "results/2025.csv" in hashes
        assert len(hashes["results/2025.csv"]) == 64

    def test_hash_multiple_outputs(self, tmp_path: Path) -> None:
        """Test hashing multiple output artifacts."""
        year1 = tmp_path / "2025.parquet"
        year2 = tmp_path / "2026.parquet"
        comparison = tmp_path / "comparison.csv"

        year1.write_bytes(b"PARQUET_2025")
        year2.write_bytes(b"PARQUET_2026")
        comparison.write_text("scenario,total_tax\nbaseline,1000000\n")

        paths = {
            "yearly/2025": year1,
            "yearly/2026": year2,
            "comparison": comparison,
        }
        hashes = hash_output_artifacts(paths)

        assert len(hashes) == 3
        assert all(len(h) == 64 for h in hashes.values())

    def test_hash_output_missing_file(self, tmp_path: Path) -> None:
        """Test that missing output file raises FileNotFoundError with context."""
        missing = tmp_path / "missing_output.csv"
        paths = {"output_key": missing}

        with pytest.raises(FileNotFoundError) as exc_info:
            hash_output_artifacts(paths)

        assert "output_key" in str(exc_info.value)

    def test_hash_empty_output_dict(self) -> None:
        """Test hashing empty output dictionary returns empty dict."""
        hashes = hash_output_artifacts({})
        assert hashes == {}


class TestVerifyArtifactHashes:
    """Tests for verify_artifact_hashes function."""

    def test_verify_all_match(self, tmp_path: Path) -> None:
        """Test verification passes when all hashes match."""
        file1 = tmp_path / "file1.csv"
        file2 = tmp_path / "file2.csv"

        file1.write_text("data1")
        file2.write_text("data2")

        # Compute expected hashes
        expected_hashes = {
            "file1": hash_file(file1),
            "file2": hash_file(file2),
        }

        artifact_paths = {"file1": file1, "file2": file2}
        result = verify_artifact_hashes(expected_hashes, artifact_paths)

        assert result.passed is True
        assert result.mismatches == []
        assert result.missing == []

    def test_verify_hash_mismatch(self, tmp_path: Path) -> None:
        """Test verification detects when file content has changed."""
        test_file = tmp_path / "data.csv"
        test_file.write_text("original content")

        # Store hash of original content
        original_hash = hash_file(test_file)
        manifest_hashes = {"data.csv": original_hash}

        # Modify file content
        test_file.write_text("modified content")

        artifact_paths = {"data.csv": test_file}
        result = verify_artifact_hashes(manifest_hashes, artifact_paths)

        assert result.passed is False
        assert "data.csv" in result.mismatches
        assert result.missing == []

    def test_verify_missing_file(self, tmp_path: Path) -> None:
        """Test verification detects missing files."""
        # Hash from manifest references file that doesn't exist
        manifest_hashes = {"missing.csv": "a" * 64}
        artifact_paths = {"missing.csv": tmp_path / "nonexistent.csv"}

        result = verify_artifact_hashes(manifest_hashes, artifact_paths)

        assert result.passed is False
        assert result.mismatches == []
        assert "missing.csv" in result.missing

    def test_verify_missing_path_key(self, tmp_path: Path) -> None:
        """Test verification when manifest has key not in artifact paths."""
        manifest_hashes = {"file1": "a" * 64, "file2": "b" * 64}
        artifact_paths = {"file1": tmp_path / "file1.csv"}

        result = verify_artifact_hashes(manifest_hashes, artifact_paths)

        assert result.passed is False
        assert "file2" in result.missing

    def test_verify_multiple_issues(self, tmp_path: Path) -> None:
        """Test verification with both mismatches and missing files."""
        file1 = tmp_path / "file1.csv"
        file1.write_text("original")

        original_hash = hash_file(file1)

        # Change file1 content
        file1.write_text("modified")

        manifest_hashes = {
            "file1": original_hash,  # Will mismatch
            "file2": "c" * 64,  # Will be missing
        }

        artifact_paths = {
            "file1": file1,
            "file2": tmp_path / "missing.csv",
        }

        result = verify_artifact_hashes(manifest_hashes, artifact_paths)

        assert result.passed is False
        assert "file1" in result.mismatches
        assert "file2" in result.missing

    def test_verify_empty_manifest(self) -> None:
        """Test verification with empty manifest hashes."""
        result = verify_artifact_hashes({}, {})

        assert result.passed is True
        assert result.mismatches == []
        assert result.missing == []

    def test_verify_unreadable_file_treated_as_missing(self, tmp_path: Path) -> None:
        """Test that unreadable files are treated as missing."""
        test_file = tmp_path / "data.csv"
        test_file.write_text("content")

        original_hash = hash_file(test_file)
        manifest_hashes = {"data": original_hash}

        # Delete file to simulate unreadable
        test_file.unlink()

        artifact_paths = {"data": test_file}
        result = verify_artifact_hashes(manifest_hashes, artifact_paths)

        assert result.passed is False
        assert "data" in result.missing


class TestArtifactVerificationResult:
    """Tests for ArtifactVerificationResult dataclass."""

    def test_result_immutable(self) -> None:
        """Test that ArtifactVerificationResult is immutable."""
        result = ArtifactVerificationResult(
            passed=True, mismatches=[], missing=[]
        )

        with pytest.raises(AttributeError):
            result.passed = False  # type: ignore[misc]

    def test_result_fields(self) -> None:
        """Test ArtifactVerificationResult fields."""
        result = ArtifactVerificationResult(
            passed=False,
            mismatches=["file1", "file2"],
            missing=["file3"],
        )

        assert result.passed is False
        assert result.mismatches == ["file1", "file2"]
        assert result.missing == ["file3"]


class TestHashIntegration:
    """Integration tests for hashing workflow."""

    def test_full_workflow_input_output_verification(self, tmp_path: Path) -> None:
        """Test complete workflow: hash inputs, hash outputs, verify both."""
        # Create input files
        input_dir = tmp_path / "inputs"
        input_dir.mkdir()
        pop_file = input_dir / "population.csv"
        pop_file.write_text("id,income\n1,50000\n2,60000\n")

        # Create output files
        output_dir = tmp_path / "outputs"
        output_dir.mkdir()
        results_file = output_dir / "results.csv"
        results_file.write_text("id,tax\n1,5000\n2,6000\n")

        # Hash inputs
        input_paths = {"population": pop_file}
        input_hashes = hash_input_artifacts(input_paths)

        # Hash outputs
        output_paths = {"results": results_file}
        output_hashes = hash_output_artifacts(output_paths)

        # Verify inputs
        input_verify = verify_artifact_hashes(input_hashes, input_paths)
        assert input_verify.passed is True

        # Verify outputs
        output_verify = verify_artifact_hashes(output_hashes, output_paths)
        assert output_verify.passed is True

    def test_hash_matches_sha256_library(self, tmp_path: Path) -> None:
        """Test that our hash_file matches standard SHA-256."""
        import hashlib

        test_file = tmp_path / "test.txt"
        content = b"Test content for SHA-256 verification"
        test_file.write_bytes(content)

        our_hash = hash_file(test_file)
        expected_hash = hashlib.sha256(content).hexdigest()

        assert our_hash == expected_hash
