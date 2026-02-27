"""Tests for immutable run manifest schema, serialization, and integrity.

Test coverage:
- Manifest creation with required fields
- Frozen immutability behavior
- Canonical JSON serialization and round-trip equality
- Integrity hash computation and verification
- Tampering detection
- Validation failures for missing/invalid fields
"""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from reformlab.governance import (
    ManifestIntegrityError,
    ManifestValidationError,
    RunManifest,
)


class TestRunManifestCreation:
    """Test manifest creation and required fields."""

    def test_minimal_manifest_with_required_fields(
        self, minimal_manifest: RunManifest
    ) -> None:
        """Manifest can be created with only required fields."""
        assert minimal_manifest.manifest_id == "test-manifest-001"
        assert minimal_manifest.created_at == "2026-02-27T10:00:00Z"
        assert minimal_manifest.engine_version == "0.1.0"
        assert minimal_manifest.openfisca_version == "40.0.0"
        assert minimal_manifest.adapter_version == "1.0.0"
        assert minimal_manifest.scenario_version == "v1.0"
        assert minimal_manifest.data_hashes == {}
        assert minimal_manifest.output_hashes == {}
        assert minimal_manifest.seeds == {}
        assert minimal_manifest.parameters == {}
        assert minimal_manifest.assumptions == []
        assert minimal_manifest.step_pipeline == []
        assert minimal_manifest.integrity_hash == ""

    def test_full_manifest_with_all_fields(self, full_manifest: RunManifest) -> None:
        """Manifest supports all architecture-required fields."""
        assert full_manifest.manifest_id == "test-manifest-full-001"
        assert full_manifest.data_hashes == {
            "population.csv": "a" * 64,
            "emissions.parquet": "b" * 64,
        }
        assert full_manifest.output_hashes == {
            "results/2025.csv": "c" * 64,
            "results/2026.parquet": "d" * 64,
        }
        assert full_manifest.seeds == {
            "master": 42,
            "year_2025": 1001,
            "year_2026": 1002,
        }
        assert full_manifest.parameters["carbon_tax_rate"] == 44.6
        assert full_manifest.assumptions == [
            "constant_population",
            "linear_price_projection",
            "no_behavioral_response",
        ]
        assert full_manifest.step_pipeline == [
            "compute_baseline",
            "apply_carbon_tax",
            "vintage_transition",
            "state_carry_forward",
        ]

    def test_missing_required_field_raises_validation_error(self) -> None:
        """Missing required fields raise ManifestValidationError."""
        with pytest.raises(
            ManifestValidationError, match="Required field 'manifest_id'"
        ):
            RunManifest(
                manifest_id="",  # Empty string is invalid
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
            )

    def test_invalid_hash_format_raises_validation_error(self) -> None:
        """Invalid SHA-256 hash format raises ManifestValidationError."""
        with pytest.raises(
            ManifestValidationError, match="Invalid SHA-256 hash.*expected 64 hex"
        ):
            RunManifest(
                manifest_id="test-001",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                data_hashes={"invalid.csv": "not-a-valid-hash"},
            )

    def test_invalid_seed_type_raises_validation_error(self) -> None:
        """Non-integer seed values raise ManifestValidationError."""
        with pytest.raises(ManifestValidationError, match="Invalid seed value"):
            RunManifest(
                manifest_id="test-001",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                seeds={"master": "not-an-int"},  # type: ignore
            )

    def test_bool_seed_raises_validation_error(self) -> None:
        """Boolean seed values are rejected even though bool is an int subtype."""
        with pytest.raises(ManifestValidationError, match="Invalid seed value"):
            RunManifest(
                manifest_id="test-001",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                seeds={"master": True},  # type: ignore[arg-type]
            )

    def test_non_string_hash_key_raises_validation_error(self) -> None:
        """Hash maps require non-empty string keys."""
        with pytest.raises(ManifestValidationError, match="Invalid hash key"):
            RunManifest(
                manifest_id="test-001",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                data_hashes={123: "a" * 64},  # type: ignore[dict-item]
            )

    def test_non_json_compatible_parameter_value_raises_validation_error(self) -> None:
        """Parameters must contain deterministic JSON-compatible values."""
        with pytest.raises(
            ManifestValidationError, match="expected JSON-compatible type"
        ):
            RunManifest(
                manifest_id="test-001",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                parameters={"unsupported": {1, 2, 3}},
            )


class TestManifestImmutability:
    """Test frozen dataclass immutability behavior."""

    def test_manifest_is_frozen(self, minimal_manifest: RunManifest) -> None:
        """Manifests are immutable after construction."""
        with pytest.raises(FrozenInstanceError):
            minimal_manifest.manifest_id = "modified"  # type: ignore

    def test_constructor_defensive_copy_prevents_alias_mutation(self) -> None:
        """Mutating caller-owned containers cannot alter a constructed manifest."""
        input_hashes = {"population.csv": "a" * 64}
        manifest = RunManifest(
            manifest_id="test-001",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            data_hashes=input_hashes,
        )
        input_hashes["population.csv"] = "b" * 64
        assert manifest.data_hashes["population.csv"] == "a" * 64

    def test_with_integrity_hash_uses_independent_container_copies(
        self, full_manifest: RunManifest
    ) -> None:
        """Derived manifest should not share mutable container references."""
        manifest_with_hash = full_manifest.with_integrity_hash()
        manifest_with_hash.data_hashes["new.csv"] = "e" * 64
        assert "new.csv" not in full_manifest.data_hashes


class TestManifestSerialization:
    """Test canonical JSON serialization and deserialization."""

    def test_to_json_produces_valid_json(self, minimal_manifest: RunManifest) -> None:
        """to_json() produces valid, parseable JSON."""
        json_str = minimal_manifest.to_json()
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        assert parsed["manifest_id"] == "test-manifest-001"

    def test_to_json_has_sorted_keys(self, full_manifest: RunManifest) -> None:
        """to_json() produces JSON with sorted keys for determinism."""
        json_str = full_manifest.to_json()
        # Parse and check that keys appear in sorted order
        parsed = json.loads(json_str)
        keys = list(parsed.keys())
        assert keys == sorted(keys)

    def test_to_json_is_deterministic(self, full_manifest: RunManifest) -> None:
        """Multiple calls to to_json() produce identical output."""
        json1 = full_manifest.to_json()
        json2 = full_manifest.to_json()
        assert json1 == json2
        # Byte-level equality
        assert json1.encode("utf-8") == json2.encode("utf-8")

    def test_from_json_recreates_manifest(self, minimal_manifest: RunManifest) -> None:
        """from_json() recreates an equivalent manifest."""
        json_str = minimal_manifest.to_json()
        restored = RunManifest.from_json(json_str)
        assert restored.manifest_id == minimal_manifest.manifest_id
        assert restored.created_at == minimal_manifest.created_at
        assert restored.engine_version == minimal_manifest.engine_version

    def test_round_trip_equality(self, full_manifest: RunManifest) -> None:
        """Serialization round-trip preserves all fields."""
        json_str = full_manifest.to_json()
        restored = RunManifest.from_json(json_str)

        # Check all fields match
        assert restored.manifest_id == full_manifest.manifest_id
        assert restored.data_hashes == full_manifest.data_hashes
        assert restored.output_hashes == full_manifest.output_hashes
        assert restored.seeds == full_manifest.seeds
        assert restored.parameters == full_manifest.parameters
        assert restored.assumptions == full_manifest.assumptions
        assert restored.step_pipeline == full_manifest.step_pipeline

    def test_from_json_with_invalid_json_raises_error(self) -> None:
        """from_json() raises ManifestValidationError for invalid JSON."""
        with pytest.raises(ManifestValidationError, match="Invalid JSON"):
            RunManifest.from_json("not valid json {")

    def test_from_json_with_missing_fields_raises_error(self) -> None:
        """from_json() raises ManifestValidationError for missing required fields."""
        incomplete_json = json.dumps({"manifest_id": "test-001"})
        with pytest.raises(ManifestValidationError, match="Missing required manifest"):
            RunManifest.from_json(incomplete_json)

    def test_from_json_with_unknown_fields_raises_error(self) -> None:
        """from_json() rejects unknown fields to avoid silent schema drift."""
        manifest_json = json.dumps(
            {
                "manifest_id": "test-001",
                "created_at": "2026-02-27T10:00:00Z",
                "engine_version": "0.1.0",
                "openfisca_version": "40.0.0",
                "adapter_version": "1.0.0",
                "scenario_version": "v1.0",
                "data_hashes": {},
                "output_hashes": {},
                "seeds": {},
                "parameters": {},
                "assumptions": [],
                "step_pipeline": [],
                "integrity_hash": "",
                "unexpected_field": "oops",
            }
        )
        with pytest.raises(ManifestValidationError, match="Unknown manifest fields"):
            RunManifest.from_json(manifest_json)


class TestManifestIntegrity:
    """Test integrity hash computation and verification."""

    def test_compute_integrity_hash_produces_sha256(
        self, minimal_manifest: RunManifest
    ) -> None:
        """compute_integrity_hash() produces valid SHA-256 hex digest."""
        hash_value = minimal_manifest.compute_integrity_hash()
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_compute_integrity_hash_is_deterministic(
        self, full_manifest: RunManifest
    ) -> None:
        """Multiple calls to compute_integrity_hash() produce same hash."""
        hash1 = full_manifest.compute_integrity_hash()
        hash2 = full_manifest.compute_integrity_hash()
        assert hash1 == hash2

    def test_compute_integrity_hash_excludes_integrity_hash_field(self) -> None:
        """compute_integrity_hash() excludes integrity_hash from computation."""
        manifest1 = RunManifest(
            manifest_id="test-001",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            integrity_hash="",
        )
        manifest2 = RunManifest(
            manifest_id="test-001",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            integrity_hash="a" * 64,  # Valid SHA-256 hex, but different from computed
        )
        # Hashes should be identical since integrity_hash is excluded
        assert manifest1.compute_integrity_hash() == manifest2.compute_integrity_hash()

    def test_different_content_produces_different_hash(self) -> None:
        """Manifests with different content produce different integrity hashes."""
        manifest1 = RunManifest(
            manifest_id="test-001",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
        )
        manifest2 = RunManifest(
            manifest_id="test-002",  # Different ID
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
        )
        assert manifest1.compute_integrity_hash() != manifest2.compute_integrity_hash()

    def test_with_integrity_hash_creates_new_manifest(
        self, minimal_manifest: RunManifest
    ) -> None:
        """with_integrity_hash() creates new manifest with computed hash."""
        manifest_with_hash = minimal_manifest.with_integrity_hash()
        assert manifest_with_hash.integrity_hash != ""
        assert len(manifest_with_hash.integrity_hash) == 64
        # Original unchanged
        assert minimal_manifest.integrity_hash == ""

    def test_verify_integrity_succeeds_for_valid_hash(
        self, minimal_manifest: RunManifest
    ) -> None:
        """verify_integrity() succeeds when hash matches content."""
        manifest_with_hash = minimal_manifest.with_integrity_hash()
        # Should not raise
        manifest_with_hash.verify_integrity()

    def test_verify_integrity_fails_for_empty_hash(
        self, minimal_manifest: RunManifest
    ) -> None:
        """verify_integrity() raises error when integrity_hash is empty."""
        with pytest.raises(ManifestIntegrityError, match="integrity_hash is empty"):
            minimal_manifest.verify_integrity()

    def test_verify_integrity_detects_tampering(self) -> None:
        """verify_integrity() detects when manifest content has been altered."""
        # Create manifest with valid hash
        original = RunManifest(
            manifest_id="test-001",
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
        ).with_integrity_hash()

        # Manually create tampered manifest with same hash but different content
        tampered = RunManifest(
            manifest_id="test-001-TAMPERED",  # Changed ID
            created_at="2026-02-27T10:00:00Z",
            engine_version="0.1.0",
            openfisca_version="40.0.0",
            adapter_version="1.0.0",
            scenario_version="v1.0",
            # Old hash doesn't match new content:
            integrity_hash=original.integrity_hash,
        )

        with pytest.raises(
            ManifestIntegrityError, match="Manifest integrity check failed"
        ):
            tampered.verify_integrity()

    def test_verify_integrity_validates_structure_before_hash_check(
        self, minimal_manifest: RunManifest
    ) -> None:
        """Structural tampering must raise validation errors during verification."""
        manifest_with_hash = minimal_manifest.with_integrity_hash()
        manifest_with_hash.data_hashes["invalid"] = "not-a-hash"
        with pytest.raises(ManifestValidationError, match="Invalid SHA-256 hash"):
            manifest_with_hash.verify_integrity()


class TestManifestValidation:
    """Test explicit validation and error messages."""

    def test_validation_on_construction(self) -> None:
        """Validation runs during manifest construction."""
        with pytest.raises(ManifestValidationError):
            RunManifest(
                manifest_id="",  # Invalid
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
            )

    def test_validation_on_deserialization(self) -> None:
        """Validation runs when deserializing from JSON."""
        invalid_json = json.dumps({
            "manifest_id": "",  # Invalid
            "created_at": "2026-02-27T10:00:00Z",
            "engine_version": "0.1.0",
            "openfisca_version": "40.0.0",
            "adapter_version": "1.0.0",
            "scenario_version": "v1.0",
            "data_hashes": {},
            "output_hashes": {},
            "seeds": {},
            "parameters": {},
            "assumptions": [],
            "step_pipeline": [],
            "integrity_hash": "",
        })
        with pytest.raises(ManifestValidationError, match="Required field"):
            RunManifest.from_json(invalid_json)

    def test_invalid_integrity_hash_format_raises_validation_error(self) -> None:
        """Invalid integrity_hash format raises ManifestValidationError."""
        with pytest.raises(
            ManifestValidationError, match="Invalid integrity_hash.*expected 64 hex"
        ):
            RunManifest(
                manifest_id="test-001",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                integrity_hash="invalid-hash",
            )

    def test_validation_error_messages_are_actionable(self) -> None:
        """Validation errors include field names and expected formats."""
        with pytest.raises(
            ManifestValidationError,
            match=r"Invalid SHA-256 hash.*'data_hashes\['bad.csv'\]'.*expected 64 hex",
        ):
            RunManifest(
                manifest_id="test-001",
                created_at="2026-02-27T10:00:00Z",
                engine_version="0.1.0",
                openfisca_version="40.0.0",
                adapter_version="1.0.0",
                scenario_version="v1.0",
                data_hashes={"bad.csv": "too-short"},
            )


class TestCrossmachineReproducibility:
    """Test deterministic serialization for cross-machine reproducibility."""

    def test_same_manifest_produces_identical_json_on_multiple_runs(
        self, full_manifest: RunManifest
    ) -> None:
        """Same manifest content produces byte-identical JSON across runs."""
        runs = [full_manifest.to_json() for _ in range(5)]
        assert all(run == runs[0] for run in runs)

    def test_recreating_manifest_produces_identical_hash(self) -> None:
        """Recreating manifest from same data produces same integrity hash."""
        data = {
            "manifest_id": "test-001",
            "created_at": "2026-02-27T10:00:00Z",
            "engine_version": "0.1.0",
            "openfisca_version": "40.0.0",
            "adapter_version": "1.0.0",
            "scenario_version": "v1.0",
            "data_hashes": {"data.csv": "a" * 64},
        }

        manifest1 = RunManifest(**data)
        manifest2 = RunManifest(**data)

        assert manifest1.compute_integrity_hash() == manifest2.compute_integrity_hash()
