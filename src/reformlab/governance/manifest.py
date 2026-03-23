# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
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
import math
import re
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from typing import Any, TypedDict

from reformlab.governance.errors import (
    ManifestIntegrityError,
    ManifestValidationError,
)

# SHA-256 hex digest pattern (64 hex characters)
SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")
# UUID pattern (standard 8-4-4-4-12 format)
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
REQUIRED_STRING_FIELDS = (
    "manifest_id",
    "created_at",
    "engine_version",
    "openfisca_version",
    "adapter_version",
    "scenario_version",
)
REQUIRED_JSON_FIELDS = (
    *REQUIRED_STRING_FIELDS,
    "data_hashes",
    "output_hashes",
    "seeds",
    "policy",
    "assumptions",
    "mappings",
    "warnings",
    "step_pipeline",
    "parent_manifest_id",
    "child_manifests",
    "integrity_hash",
)


class AssumptionEntry(TypedDict):
    """Structured assumption entry for manifest capture.

    Attributes:
        key: The assumption key/identifier.
        value: The assumption value (JSON-compatible type).
        source: Source of the assumption (e.g., "default", "user", "scenario").
        is_default: Whether this is a default value or user override.
    """

    key: str
    value: Any
    source: str
    is_default: bool


class MappingEntry(TypedDict, total=False):
    """Structured mapping entry for manifest capture.

    Attributes:
        openfisca_name: OpenFisca variable name.
        project_name: Project schema field name.
        direction: Mapping direction ("input", "output", or "both").
        source_file: Optional path to mapping file.
        transform: Optional transform identifier if configured.
    """

    openfisca_name: str
    project_name: str
    direction: str
    source_file: str  # optional
    transform: str  # optional


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
        policy: Complete parameter snapshot.
        assumptions: Structured assumption entries (key/value/source/is_default).
        mappings: Variable mapping configuration used at runtime.
        warnings: List of warning messages from execution.
        step_pipeline: Ordered step names executed.
        parent_manifest_id: Parent manifest UUID for lineage (empty string for root).
        child_manifests: Mapping of year to child manifest UUID for lineage.
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
    policy: dict[str, Any] = field(default_factory=dict)
    assumptions: list[AssumptionEntry] = field(default_factory=list)
    mappings: list[MappingEntry] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    step_pipeline: list[str] = field(default_factory=list)
    parent_manifest_id: str = ""
    child_manifests: dict[int, str] = field(default_factory=dict)
    integrity_hash: str = ""

    def __post_init__(self) -> None:
        """Validate required fields and hash formats on construction."""
        self._validate()
        self._normalize_mutable_fields()

    def _validate(self) -> None:
        """Validate manifest schema and field invariants."""
        # Validate required string fields are non-empty.
        for field_name in REQUIRED_STRING_FIELDS:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ManifestValidationError(
                    f"Required field '{field_name}' must be a non-empty string"
                )

        # Validate hash formats (SHA-256 hex digests).
        for hash_dict_name in ["data_hashes", "output_hashes"]:
            hash_dict = getattr(self, hash_dict_name)
            if not isinstance(hash_dict, dict):
                raise ManifestValidationError(
                    f"Field '{hash_dict_name}' must be a dictionary"
                )
            for key, hash_value in hash_dict.items():
                if not isinstance(key, str) or not key.strip():
                    raise ManifestValidationError(
                        f"Invalid hash key in '{hash_dict_name}': expected non-empty "
                        f"string, got {key!r}"
                    )
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

        # Validate parent_manifest_id format if present (AC-2)
        if self.parent_manifest_id and not UUID_PATTERN.match(self.parent_manifest_id):
            raise ManifestValidationError(
                f"Invalid parent_manifest_id: expected UUID format, "
                f"got {self.parent_manifest_id!r}"
            )

        # Validate child_manifests dictionary (AC-1)
        if not isinstance(self.child_manifests, dict):
            raise ManifestValidationError(
                "Field 'child_manifests' must be a dictionary"
            )
        for year, child_id in self.child_manifests.items():
            if not isinstance(year, int) or isinstance(year, bool):
                raise ManifestValidationError(
                    f"Invalid child_manifests key: expected int year, "
                    f"got {type(year).__name__}"
                )
            if not isinstance(child_id, str) or not child_id.strip():
                raise ManifestValidationError(
                    f"Invalid child_manifests value for year {year}: "
                    f"expected non-empty string UUID, got {child_id!r}"
                )
            if not UUID_PATTERN.match(child_id):
                raise ManifestValidationError(
                    f"Invalid child_manifests value for year {year}: "
                    f"expected UUID format, got {child_id!r}"
                )

        # Validate seeds dictionary.
        if not isinstance(self.seeds, dict):
            raise ManifestValidationError("Field 'seeds' must be a dictionary")
        for key, seed_value in self.seeds.items():
            if not isinstance(key, str) or not key.strip():
                raise ManifestValidationError(
                    f"Invalid seed key: expected non-empty string, got {key!r}"
                )
            if not isinstance(seed_value, int) or isinstance(seed_value, bool):
                raise ManifestValidationError(
                    f"Invalid seed value in 'seeds[{key!r}]': "
                    f"expected int, got {type(seed_value).__name__}"
                )

        # Validate policy dictionary.
        if not isinstance(self.policy, dict):
            raise ManifestValidationError("Field 'policy' must be a dictionary")
        _validate_json_compatible(self.policy, "policy")

        # Validate assumptions list.
        if not isinstance(self.assumptions, list):
            raise ManifestValidationError("Field 'assumptions' must be a list")
        for i, assumption in enumerate(self.assumptions):
            if not isinstance(assumption, dict):
                raise ManifestValidationError(
                    f"Invalid assumption at index {i}: "
                    f"expected dict, got {type(assumption).__name__}"
                )
            # Validate required assumption entry fields
            for required_key in ("key", "value", "source", "is_default"):
                if required_key not in assumption:
                    raise ManifestValidationError(
                        f"Invalid assumption at index {i}: "
                        f"missing required field '{required_key}'"
                    )
            if not isinstance(assumption["key"], str) or not assumption["key"].strip():
                raise ManifestValidationError(
                    f"Invalid assumption at index {i}: "
                    f"field 'key' must be a non-empty string"
                )
            if (
                not isinstance(assumption["source"], str)
                or not assumption["source"].strip()
            ):
                raise ManifestValidationError(
                    f"Invalid assumption at index {i}: "
                    f"field 'source' must be a non-empty string"
                )
            if not isinstance(assumption["is_default"], bool):
                raise ManifestValidationError(
                    f"Invalid assumption at index {i}: "
                    f"field 'is_default' must be a boolean"
                )
            # Validate value is JSON-compatible
            _validate_json_compatible(assumption["value"], f"assumptions[{i}].value")

        # Validate mappings list.
        if not isinstance(self.mappings, list):
            raise ManifestValidationError("Field 'mappings' must be a list")
        for i, mapping in enumerate(self.mappings):
            if not isinstance(mapping, dict):
                raise ManifestValidationError(
                    f"Invalid mapping at index {i}: "
                    f"expected dict, got {type(mapping).__name__}"
                )
            # Validate required mapping entry fields
            for required_key in ("openfisca_name", "project_name", "direction"):
                if required_key not in mapping:
                    raise ManifestValidationError(
                        f"Invalid mapping at index {i}: "
                        f"missing required field '{required_key}'"
                    )
            if (
                not isinstance(mapping["openfisca_name"], str)
                or not mapping["openfisca_name"].strip()
            ):
                raise ManifestValidationError(
                    f"Invalid mapping at index {i}: "
                    f"field 'openfisca_name' must be a non-empty string"
                )
            if (
                not isinstance(mapping["project_name"], str)
                or not mapping["project_name"].strip()
            ):
                raise ManifestValidationError(
                    f"Invalid mapping at index {i}: "
                    f"field 'project_name' must be a non-empty string"
                )
            if not isinstance(mapping["direction"], str) or mapping[
                "direction"
            ] not in ("input", "output", "both"):
                raise ManifestValidationError(
                    f"Invalid mapping at index {i}: "
                    f"field 'direction' must be one of: input, output, both"
                )
            if "source_file" in mapping and (
                not isinstance(mapping["source_file"], str)
                or not mapping["source_file"].strip()
            ):
                raise ManifestValidationError(
                    f"Invalid mapping at index {i}: "
                    f"field 'source_file' must be a non-empty string when provided"
                )
            if "transform" in mapping and (
                not isinstance(mapping["transform"], str)
                or not mapping["transform"].strip()
            ):
                raise ManifestValidationError(
                    f"Invalid mapping at index {i}: "
                    f"field 'transform' must be a non-empty string when provided"
                )
            _validate_json_compatible(mapping, f"mappings[{i}]")

        # Validate warnings list.
        if not isinstance(self.warnings, list):
            raise ManifestValidationError("Field 'warnings' must be a list")
        for i, warning in enumerate(self.warnings):
            if not isinstance(warning, str) or not warning.strip():
                raise ManifestValidationError(
                    f"Invalid warning at index {i}: "
                    f"expected non-empty str, got {type(warning).__name__}"
                )

        # Validate step_pipeline list.
        if not isinstance(self.step_pipeline, list):
            raise ManifestValidationError("Field 'step_pipeline' must be a list")
        for i, step_name in enumerate(self.step_pipeline):
            if not isinstance(step_name, str) or not step_name.strip():
                raise ManifestValidationError(
                    f"Invalid step name at index {i}: "
                    f"expected str, got {type(step_name).__name__}"
                )

    def _normalize_mutable_fields(self) -> None:
        """Copy mutable containers to prevent external aliasing side effects."""
        object.__setattr__(self, "data_hashes", dict(self.data_hashes))
        object.__setattr__(self, "output_hashes", dict(self.output_hashes))
        object.__setattr__(self, "seeds", dict(self.seeds))
        object.__setattr__(self, "policy", deepcopy(self.policy))
        object.__setattr__(self, "assumptions", deepcopy(self.assumptions))
        object.__setattr__(self, "mappings", deepcopy(self.mappings))
        object.__setattr__(self, "warnings", list(self.warnings))
        object.__setattr__(self, "step_pipeline", list(self.step_pipeline))
        object.__setattr__(self, "child_manifests", dict(self.child_manifests))

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

        missing_fields = [key for key in REQUIRED_JSON_FIELDS if key not in data]
        if missing_fields:
            raise ManifestValidationError(
                "Missing required manifest fields: " + ", ".join(sorted(missing_fields))
            )

        unknown_fields = sorted(set(data) - set(REQUIRED_JSON_FIELDS))
        if unknown_fields:
            raise ManifestValidationError(
                "Unknown manifest fields: " + ", ".join(unknown_fields)
            )

        try:
            # JSON serializes int keys as strings, so convert them back
            child_manifests_raw = data["child_manifests"]
            if not isinstance(child_manifests_raw, dict):
                raise ManifestValidationError(
                    "Field 'child_manifests' must be a dictionary"
                )
            child_manifests: dict[int, str] = {}
            for key, value in child_manifests_raw.items():
                try:
                    child_manifests[int(key)] = value
                except (ValueError, TypeError) as conv_err:
                    raise ManifestValidationError(
                        f"Invalid child_manifests key: cannot convert {key!r} "
                        f"to int year: {conv_err}"
                    ) from conv_err

            return cls(
                manifest_id=data["manifest_id"],
                created_at=data["created_at"],
                engine_version=data["engine_version"],
                openfisca_version=data["openfisca_version"],
                adapter_version=data["adapter_version"],
                scenario_version=data["scenario_version"],
                data_hashes=data["data_hashes"],
                output_hashes=data["output_hashes"],
                seeds=data["seeds"],
                policy=data["policy"],
                assumptions=data["assumptions"],
                mappings=data["mappings"],
                warnings=data["warnings"],
                step_pipeline=data["step_pipeline"],
                parent_manifest_id=data["parent_manifest_id"],
                child_manifests=child_manifests,
                integrity_hash=data["integrity_hash"],
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
        self._validate()

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
            policy=self.policy,
            assumptions=self.assumptions,
            mappings=self.mappings,
            warnings=self.warnings,
            step_pipeline=self.step_pipeline,
            parent_manifest_id=self.parent_manifest_id,
            child_manifests=self.child_manifests,
            integrity_hash=computed_hash,
        )


def _validate_json_compatible(value: Any, path: str) -> None:
    """Validate that a value is canonical-JSON compatible and deterministic."""
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if not isinstance(key, str) or not key.strip():
                raise ManifestValidationError(
                    f"Invalid key at {path}: expected non-empty string, got {key!r}"
                )
            _validate_json_compatible(nested_value, f"{path}[{key!r}]")
        return

    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            _validate_json_compatible(nested_value, f"{path}[{index}]")
        return

    if isinstance(value, bool | str | int) or value is None:
        return

    if isinstance(value, float):
        if math.isfinite(value):
            return
        raise ManifestValidationError(
            f"Invalid float at {path}: expected finite JSON number, got {value!r}"
        )

    raise ManifestValidationError(
        f"Invalid value at {path}: expected JSON-compatible type, "
        f"got {type(value).__name__}"
    )
