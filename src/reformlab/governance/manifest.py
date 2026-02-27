"""Immutable run manifest schema for governance and reproducibility.

Every simulation run produces an immutable manifest documenting all parameters,
data sources, assumptions, and execution configuration. Manifests support:

- Frozen dataclasses (immutable after construction)
- Canonical JSON serialization (deterministic, cross-machine reproducible)
- Integrity hashing (SHA-256) with tamper detection
- Explicit validation with actionable error messages

This module implements FR25 (immutable run manifests) and NFR9 (automatic
manifest generation with zero manual effort).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from reformlab.governance.errors import (
    ManifestIntegrityError,
    ManifestValidationError,
)

# SHA-256 hex digest pattern (64 hex characters)
SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")


@dataclass(frozen=True)
class RunManifest:
    """Immutable run manifest documenting all parameters, data sources, and assumptions.

    Every simulation run produces one manifest. Integrity is verified via SHA-256 hash.
    All fields are immutable after construction.

    Attributes:
        manifest_id: Unique identifier for this manifest (UUID).
        created_at: ISO 8601 timestamp when manifest was created.
        engine_version: ReformLab package version.
        openfisca_version: OpenFisca package/model version used by adapter.
        adapter_version: OpenFiscaAdapter version string.
        scenario_version: Version ID from scenario registry.
        data_hashes: SHA-256 hashes of input files, keyed by path reference.
        output_hashes: SHA-256 hashes of output artifacts, keyed by artifact key/path.
        seeds: All random seeds used (master seed + per-year seeds).
        parameters: Complete parameter snapshot.
        assumptions: Explicit assumption keys used in this run.
        step_pipeline: Ordered step names executed.
        integrity_hash: SHA-256 hash of entire manifest content (excluding this field).
    """

    manifest_id: str
    created_at: str
    engine_version: str
    openfisca_version: str
    adapter_version: str
    scenario_version: str
    data_hashes: dict[str, str] = field(default_factory=dict)
    output_hashes: dict[str, str] = field(default_factory=dict)
    seeds: dict[str, int] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    step_pipeline: list[str] = field(default_factory=list)
    integrity_hash: str = ""

    def __post_init__(self) -> None:
        """Validate required fields and hash formats on construction."""
        # Validate required string fields are non-empty
        required_fields = [
            "manifest_id",
            "created_at",
            "engine_version",
            "openfisca_version",
            "adapter_version",
            "scenario_version",
        ]
        for field_name in required_fields:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ManifestValidationError(
                    f"Required field '{field_name}' must be a non-empty string"
                )

        # Validate hash formats (SHA-256 hex digests)
        for hash_dict_name in ["data_hashes", "output_hashes"]:
            hash_dict = getattr(self, hash_dict_name)
            if not isinstance(hash_dict, dict):
                raise ManifestValidationError(
                    f"Field '{hash_dict_name}' must be a dictionary"
                )
            for key, hash_value in hash_dict.items():
                if not isinstance(hash_value, str) or not SHA256_PATTERN.match(
                    hash_value
                ):
                    raise ManifestValidationError(
                        f"Invalid SHA-256 hash in '{hash_dict_name}[{key!r}]': "
                        f"expected 64 hex characters, got {hash_value!r}"
                    )

        # Validate integrity_hash format if present
        if self.integrity_hash and not SHA256_PATTERN.match(self.integrity_hash):
            raise ManifestValidationError(
                f"Invalid integrity_hash: expected 64 hex characters, "
                f"got {self.integrity_hash!r}"
            )

        # Validate seeds dictionary
        if not isinstance(self.seeds, dict):
            raise ManifestValidationError("Field 'seeds' must be a dictionary")
        for key, seed_value in self.seeds.items():
            if not isinstance(seed_value, int):
                raise ManifestValidationError(
                    f"Invalid seed value in 'seeds[{key!r}]': "
                    f"expected int, got {type(seed_value).__name__}"
                )

        # Validate parameters dictionary
        if not isinstance(self.parameters, dict):
            raise ManifestValidationError("Field 'parameters' must be a dictionary")

        # Validate assumptions list
        if not isinstance(self.assumptions, list):
            raise ManifestValidationError("Field 'assumptions' must be a list")
        for i, assumption in enumerate(self.assumptions):
            if not isinstance(assumption, str):
                raise ManifestValidationError(
                    f"Invalid assumption at index {i}: "
                    f"expected str, got {type(assumption).__name__}"
                )

        # Validate step_pipeline list
        if not isinstance(self.step_pipeline, list):
            raise ManifestValidationError("Field 'step_pipeline' must be a list")
        for i, step_name in enumerate(self.step_pipeline):
            if not isinstance(step_name, str):
                raise ManifestValidationError(
                    f"Invalid step name at index {i}: "
                    f"expected str, got {type(step_name).__name__}"
                )

    def to_json(self) -> str:
        """Serialize manifest to canonical JSON.

        Returns deterministic JSON with sorted keys, stable separators, UTF-8
        encoding. Serializing the same manifest on different machines produces
        byte-equivalent output.

        Returns:
            Canonical JSON string representation.
        """
        # Convert frozen dataclass to dict
        manifest_dict = asdict(self)

        # Canonical serialization: sorted keys, no indent, stable separators
        return json.dumps(manifest_dict, sort_keys=True, separators=(",", ":"))

    @classmethod
    def from_json(cls, json_str: str) -> RunManifest:
        """Deserialize manifest from JSON string.

        Validates schema and raises ManifestValidationError for structural issues.

        Args:
            json_str: JSON string representation of manifest.

        Returns:
            Immutable RunManifest instance.

        Raises:
            ManifestValidationError: If JSON is invalid or schema validation fails.
        """
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ManifestValidationError(f"Invalid JSON: {e}") from e

        if not isinstance(data, dict):
            raise ManifestValidationError(
                f"Invalid manifest JSON: expected object, got {type(data).__name__}"
            )

        # Extract fields with defaults for optional dict/list fields
        try:
            return cls(
                manifest_id=data.get("manifest_id", ""),
                created_at=data.get("created_at", ""),
                engine_version=data.get("engine_version", ""),
                openfisca_version=data.get("openfisca_version", ""),
                adapter_version=data.get("adapter_version", ""),
                scenario_version=data.get("scenario_version", ""),
                data_hashes=data.get("data_hashes", {}),
                output_hashes=data.get("output_hashes", {}),
                seeds=data.get("seeds", {}),
                parameters=data.get("parameters", {}),
                assumptions=data.get("assumptions", []),
                step_pipeline=data.get("step_pipeline", []),
                integrity_hash=data.get("integrity_hash", ""),
            )
        except (TypeError, KeyError) as e:
            raise ManifestValidationError(
                f"Failed to construct RunManifest from JSON: {e}"
            ) from e

    def compute_integrity_hash(self) -> str:
        """Compute SHA-256 hash of manifest content.

        Excludes the integrity_hash field itself from hash computation.
        Uses canonical JSON serialization for determinism.

        Returns:
            SHA-256 hex digest (64 hex characters).
        """
        # Create dict without integrity_hash
        manifest_dict = asdict(self)
        manifest_dict.pop("integrity_hash", None)

        # Canonical JSON: sorted keys, stable separators, UTF-8
        canonical = json.dumps(manifest_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify_integrity(self) -> None:
        """Verify manifest integrity against stored hash.

        Raises ManifestIntegrityError if current content does not match
        the stored integrity_hash, indicating tampering or corruption.

        Raises:
            ManifestIntegrityError: If integrity verification fails.
        """
        if not self.integrity_hash:
            raise ManifestIntegrityError(
                "Cannot verify integrity: integrity_hash is empty"
            )

        expected_hash = self.compute_integrity_hash()
        if expected_hash != self.integrity_hash:
            raise ManifestIntegrityError(
                f"Manifest integrity check failed: "
                f"expected hash {expected_hash}, got {self.integrity_hash}"
            )

    def with_integrity_hash(self) -> RunManifest:
        """Create new manifest with computed integrity hash.

        Since manifests are immutable, this creates a new instance with
        the integrity_hash field populated.

        Returns:
            New RunManifest instance with integrity_hash computed and set.
        """
        computed_hash = self.compute_integrity_hash()

        # Create new instance with all fields plus computed hash
        return RunManifest(
            manifest_id=self.manifest_id,
            created_at=self.created_at,
            engine_version=self.engine_version,
            openfisca_version=self.openfisca_version,
            adapter_version=self.adapter_version,
            scenario_version=self.scenario_version,
            data_hashes=self.data_hashes,
            output_hashes=self.output_hashes,
            seeds=self.seeds,
            parameters=self.parameters,
            assumptions=self.assumptions,
            step_pipeline=self.step_pipeline,
            integrity_hash=computed_hash,
        )
