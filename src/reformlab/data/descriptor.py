# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Unified dataset descriptor bridging data schemas and source metadata.

Replaces per-provider dataset dataclasses (``INSEEDataset``, ``ADEMEDataset``,
``EurostatDataset``, ``SDESDataset``) with a single ``DatasetDescriptor`` type
that combines schema, metadata, and column mapping in one place.

Every dataset — institutional or user-supplied — can be described declaratively
with a ``DatasetDescriptor``.

This module also defines the canonical evidence asset descriptor (``DataAssetDescriptor``)
for trust-governed open & synthetic evidence foundation. See Story 21.1 and
synthetic-data-decision-document-2026-03-23.md for the full evidence taxonomy.

Story 21.1 - implement-canonical-evidence-asset-descriptor-and-current-phase-source-matrix.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, get_args

from reformlab.computation.ingestion import DataSchema
from reformlab.data.errors import EvidenceAssetError

# ============================================================================
# Evidence Classification Literal Types
# ============================================================================
# Story 21.1 / AC2, AC3, AC4, AC5, AC6
#
# These literal types define the evidence taxonomy from the synthetic data
# decision document (Section 3.2). They classify data assets by origin,
# access mode, trust status, and data class.
#
# Runtime validation constants (_VALID_*) are derived from the Literal types
# using get_args() to ensure single source of truth and eliminate duplication.

DataAssetOrigin = Literal[
    "open-official",
    "synthetic-public",
    "synthetic-internal",  # reserved for future
    "restricted",  # reserved for future
]
"""Where the asset comes from.

Values:
- ``"open-official"``: Openly usable official or institutional data
- ``"synthetic-public"``: Public synthetic datasets from trusted external producers
- ``"synthetic-internal"``: Internally generated synthetic assets (future phase)
- ``"restricted"``: Access-controlled data (future phase)

Story 21.1 / AC2.
"""

DataAssetAccessMode = Literal[
    "bundled",
    "fetched",
    "deferred-user-connector",  # reserved for future
]
"""How ReformLab obtains the asset.

Values:
- ``"bundled"``: Distributed with the product or repository
- ``"fetched"``: Obtained automatically from public sources
- ``"deferred-user-connector"``: Reserved for future restricted-data integration

Story 21.1 / AC3.
"""

DataAssetTrustStatus = Literal[
    "production-safe",
    "exploratory",
    "demo-only",
    "validation-pending",
    "not-for-public-inference",
]
"""What can be claimed about the asset.

Values:
- ``"production-safe"``: Validated for decision-support use
- ``"exploratory"``: Suitable for exploration, not decision support
- ``"demo-only"``: Example data, not for analysis
- ``"validation-pending"``: Requires validation dossier before production use
- ``"not-for-public-inference"``: Internal use, cannot be used for public claims

Story 21.1 / AC4.
"""

DataAssetClass = Literal[
    "structural",
    "exogenous",
    "calibration",
    "validation",
]
"""The role of the data asset in the evidence taxonomy.

Values:
- ``"structural"``: Define who or what is modeled (households, firms, places)
- ``"exogenous"``: Observed/projected context inputs (prices, rates, costs)
- ``"calibration"``: Fit the model to observed reality
- ``"validation"``: Test the model against independent observations

Story 21.1 / AC5.
"""

# Runtime validation constants (single source of truth from Literal types)
# Using get_args() ensures these stay in sync with Literal definitions
_VALID_ORIGINS = get_args(DataAssetOrigin)
_VALID_ACCESS_MODES = get_args(DataAssetAccessMode)
_VALID_TRUST_STATUSES = get_args(DataAssetTrustStatus)
_VALID_DATA_CLASSES = get_args(DataAssetClass)

# Current-phase supported combinations (Story 21.1 / AC14)
#
# These combinations are supported in the current phase. Reserved values
# (synthetic-internal, restricted, deferred-user-connector) are not yet
# implemented and will raise EvidenceAssetError in __post_init__.
_CURRENT_PHASE_SUPPORTED: dict[
    DataAssetOrigin, dict[DataAssetAccessMode, tuple[DataAssetTrustStatus, ...]]
] = {
    "open-official": {
        "bundled": ("production-safe", "exploratory"),
        "fetched": ("production-safe", "exploratory"),
    },
    "synthetic-public": {
        "bundled": (
            "exploratory",
            "demo-only",
            "validation-pending",
            "not-for-public-inference",
        ),
        "fetched": (
            "exploratory",
            "demo-only",
            "validation-pending",
            "not-for-public-inference",
        ),
    },
}


@dataclass(frozen=True)
class DatasetDescriptor:
    """Declarative description of a dataset — schema, metadata, and column mappings.

    Attributes
    ----------
    dataset_id : str
        Unique identifier for the dataset within the provider namespace.
    provider : str
        Data provider identifier (e.g. ``"insee"``, ``"ademe"``, ``"user"``).
    description : str
        Human-readable description of the dataset.
    schema : DataSchema
        Target schema after column renaming (required/optional column semantics).
    url : str
        Download URL. Empty for user-supplied local files.
    license : str
        License identifier (e.g. ``"CC-BY-4.0"``).
    version : str
        Version or vintage identifier (e.g. ``"2021"``, ``"2024-Q1"``).
    column_mapping : tuple[tuple[str, str], ...]
        Raw source column name → project column name. Empty = no renaming.
    encoding : str
        Character encoding for CSV parsing.
    separator : str
        Field separator for CSV parsing.
    null_markers : tuple[str, ...]
        Strings treated as null values during CSV parsing.
    file_format : str
        Source file format: ``"csv"``, ``"zip"``, ``"csv.gz"``, ``"parquet"``.
    skip_rows : int
        Number of header rows to skip before the column name row.
    """

    # Identity
    dataset_id: str
    provider: str
    description: str

    # Schema (uses DataSchema for required/optional semantics)
    schema: DataSchema

    # Source
    url: str = ""
    license: str = ""
    version: str = ""

    # Column mapping (raw source name → project name)
    column_mapping: tuple[tuple[str, str], ...] = ()

    # Parse options
    encoding: str = "utf-8"
    separator: str = ","
    null_markers: tuple[str, ...] = ("",)
    file_format: str = "csv"
    skip_rows: int = 0

    def to_json(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        result: dict[str, Any] = {
            "dataset_id": self.dataset_id,
            "provider": self.provider,
            "description": self.description,
            "schema": self.schema.to_json(),
        }
        if self.url:
            result["url"] = self.url
        if self.license:
            result["license"] = self.license
        if self.version:
            result["version"] = self.version
        if self.column_mapping:
            result["column_mapping"] = [
                [raw, proj] for raw, proj in self.column_mapping
            ]
        if self.encoding != "utf-8":
            result["encoding"] = self.encoding
        if self.separator != ",":
            result["separator"] = self.separator
        if self.null_markers != ("",):
            result["null_markers"] = list(self.null_markers)
        if self.file_format != "csv":
            result["file_format"] = self.file_format
        if self.skip_rows != 0:
            result["skip_rows"] = self.skip_rows
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> DatasetDescriptor:
        """Deserialize from a JSON-compatible dict."""
        try:
            column_mapping_raw = data.get("column_mapping", [])
            column_mapping = tuple(
                (pair[0], pair[1]) for pair in column_mapping_raw
            )
            null_markers_raw = data.get("null_markers", [""])
            return cls(
                dataset_id=data["dataset_id"],
                provider=data["provider"],
                description=data["description"],
                schema=DataSchema.from_json(data["schema"]),
                url=data.get("url", ""),
                license=data.get("license", ""),
                version=data.get("version", ""),
                column_mapping=column_mapping,
                encoding=data.get("encoding", "utf-8"),
                separator=data.get("separator", ","),
                null_markers=tuple(null_markers_raw),
                file_format=data.get("file_format", "csv"),
                skip_rows=data.get("skip_rows", 0),
            )
        except KeyError as exc:
            msg = f"DatasetDescriptor JSON missing required key: {exc}"
            raise ValueError(msg) from exc
        except (TypeError, IndexError) as exc:
            msg = f"DatasetDescriptor JSON has malformed data: {exc}"
            raise ValueError(msg) from exc


# ============================================================================
# Evidence Asset Descriptor
# ============================================================================
# Story 21.1 / AC1, AC7, AC14


@dataclass(frozen=True)
class DataAssetDescriptor:
    """Canonical evidence asset descriptor with governance envelope.

    Combines origin, access mode, trust status, and extended provenance metadata
    into a single frozen dataclass for all data classes (structural, exogenous,
    calibration, validation).

    Attributes
    ----------
    asset_id : str
        Unique identifier for the asset (e.g., ``"reformlab-fr-synthetic-2024"``).
        Follows ``{provider}-{dataset}-{version}`` pattern using kebab-case.
    name : str
        Human-readable name of the asset.
    description : str
        Human-readable description of the asset.
    data_class : DataAssetClass
        Role in evidence taxonomy: structural, exogenous, calibration, or validation.
    origin : DataAssetOrigin
        Where the asset comes from: open-official, synthetic-public, etc.
    access_mode : DataAssetAccessMode
        How ReformLab obtains it: bundled, fetched, etc.
    trust_status : DataAssetTrustStatus
        What can be claimed: production-safe, exploratory, demo-only, etc.
    source_url : str
        Direct URL to the asset source (empty if bundled).
    license : str
        License identifier (e.g., ``"CC-BY-4.0"``).
    version : str
        Version or vintage identifier (e.g., ``"2021"``, ``"2024-Q1"``).
    geographic_coverage : tuple[str, ...]
        Geographic coverage (e.g., ``("FR",)`` for France-only).
    years : tuple[int, ...]
        Years covered by this asset (e.g., ``(2020, 2021, 2022, 2023, 2024)``).
    intended_use : str
        Description of intended use cases.
    redistribution_allowed : bool
        Whether redistribution is permitted under the license.
    redistribution_notes : str
        Notes on redistribution restrictions or requirements.
    update_cadence : str
        How often the asset is updated (e.g., ``"annual"``, ``"quarterly"``).
    quality_notes : str
        Known quality issues or limitations.
    references : tuple[str, ...]
        URLs to documentation, methodology papers, or source materials.

    Story 21.1 / AC1.
    """

    # Required fields
    asset_id: str
    name: str
    description: str
    data_class: DataAssetClass
    origin: DataAssetOrigin
    access_mode: DataAssetAccessMode
    trust_status: DataAssetTrustStatus

    # Optional fields with defaults
    source_url: str = ""
    license: str = ""
    version: str = ""
    geographic_coverage: tuple[str, ...] = ()
    years: tuple[int, ...] = ()
    intended_use: str = ""
    redistribution_allowed: bool = False
    redistribution_notes: str = ""
    update_cadence: str = ""
    quality_notes: str = ""
    references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate required fields, literal values, and cross-field combinations.

        Raises EvidenceAssetError with actionable message if validation fails.

        Story 21.1 / AC7, AC14.
        """
        # Validate required fields are non-empty strings
        for field_name in ("asset_id", "name", "description"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise EvidenceAssetError(
                    f"DataAssetDescriptor validation failed: {field_name} must be a "
                    f"non-empty string - provide a valid {field_name} value"
                )

        # Validate literal values using runtime constants (single source of truth)
        if self.origin not in _VALID_ORIGINS:
            raise EvidenceAssetError(
                f"DataAssetDescriptor validation failed: origin {self.origin!r} is not "
                f"a valid DataAssetOrigin - use one of {_VALID_ORIGINS}"
            )

        if self.access_mode not in _VALID_ACCESS_MODES:
            raise EvidenceAssetError(
                f"DataAssetDescriptor validation failed: access_mode {self.access_mode!r} "
                f"is not a valid DataAssetAccessMode - use one of {_VALID_ACCESS_MODES}"
            )

        if self.trust_status not in _VALID_TRUST_STATUSES:
            raise EvidenceAssetError(
                f"DataAssetDescriptor validation failed: trust_status {self.trust_status!r} "
                f"is not a valid DataAssetTrustStatus - use one of {_VALID_TRUST_STATUSES}"
            )

        if self.data_class not in _VALID_DATA_CLASSES:
            raise EvidenceAssetError(
                f"DataAssetDescriptor validation failed: data_class {self.data_class!r} "
                f"is not a valid DataAssetClass - use one of {_VALID_DATA_CLASSES}"
            )

        # Validate current-phase supported combinations (AC14)
        # Reserved values raise EvidenceAssetError in current phase
        if self.origin in ("synthetic-internal", "restricted"):
            raise EvidenceAssetError(
                f"DataAssetDescriptor validation failed: origin {self.origin!r} is "
                f"reserved for future phases - use 'open-official' or 'synthetic-public' "
                f"in the current phase"
            )

        if self.access_mode == "deferred-user-connector":
            raise EvidenceAssetError(
                "DataAssetDescriptor validation failed: access_mode "
                "'deferred-user-connector' is reserved for future phases - use "
                "'bundled' or 'fetched' in the current phase"
            )

        # Validate origin/access_mode/trust_status combination
        # Use None as sentinel for unsupported origin/access_mode pairs (not empty tuple)
        # This prevents validation bypass when new literals are added without updating support matrix
        allowed_statuses = _CURRENT_PHASE_SUPPORTED.get(self.origin, {}).get(
            self.access_mode, None
        )
        if allowed_statuses is None:
            raise EvidenceAssetError(
                f"DataAssetDescriptor validation failed: origin={self.origin!r}, "
                f"access_mode={self.access_mode!r} is not a supported combination - "
                f"this origin/access_mode pair is not defined in the current-phase "
                f"support matrix"
            )
        if self.trust_status not in allowed_statuses:
            raise EvidenceAssetError(
                f"DataAssetDescriptor validation failed: origin={self.origin!r}, "
                f"access_mode={self.access_mode!r}, trust_status={self.trust_status!r} "
                f"is not a supported combination - allowed trust statuses for this "
                f"origin/access_mode are: {allowed_statuses}"
            )

    def to_json(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict, omitting empty/default values.

        Returns a dict with only non-empty fields. Empty strings, empty tuples,
        and default bool values are omitted to keep JSON compact.

        Story 21.1 / AC7.

        Returns
        -------
        dict[str, Any]
            JSON-serializable representation of this descriptor.
        """
        result: dict[str, Any] = {
            "asset_id": self.asset_id,
            "name": self.name,
            "description": self.description,
            "data_class": self.data_class,
            "origin": self.origin,
            "access_mode": self.access_mode,
            "trust_status": self.trust_status,
        }

        # Add optional fields only if non-default
        if self.source_url:
            result["source_url"] = self.source_url
        if self.license:
            result["license"] = self.license
        if self.version:
            result["version"] = self.version
        if self.geographic_coverage:
            result["geographic_coverage"] = list(self.geographic_coverage)
        if self.years:
            result["years"] = list(self.years)
        if self.intended_use:
            result["intended_use"] = self.intended_use
        if self.redistribution_allowed:
            result["redistribution_allowed"] = True
        if self.redistribution_notes:
            result["redistribution_notes"] = self.redistribution_notes
        if self.update_cadence:
            result["update_cadence"] = self.update_cadence
        if self.quality_notes:
            result["quality_notes"] = self.quality_notes
        if self.references:
            result["references"] = list(self.references)

        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> DataAssetDescriptor:
        """Deserialize from a JSON-compatible dict with full validation.

        Validates all fields and raises EvidenceAssetError with actionable
        message on any failure.

        Story 21.1 / AC7.

        Parameters
        ----------
        data : dict[str, Any]
            JSON dict representation of a DataAssetDescriptor.

        Returns
        -------
        DataAssetDescriptor
            Immutable descriptor instance.

        Raises
        ------
        EvidenceAssetError
            If validation fails (missing fields, invalid types, invalid values,
            or unsupported combinations).
        """
        # Validate input type
        if not isinstance(data, dict):
            raise EvidenceAssetError(
                "DataAssetDescriptor validation failed: data must be an object - "
                "provide a JSON object"
            )

        # Check for required fields
        required_fields = (
            "asset_id",
            "name",
            "description",
            "data_class",
            "origin",
            "access_mode",
            "trust_status",
        )
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            raise EvidenceAssetError(
                f"DataAssetDescriptor JSON missing required fields: "
                f"{', '.join(missing_fields)} - provide all required fields"
            )

        # Validate field types for required fields
        for field_name in required_fields:
            if not isinstance(data[field_name], str):
                raise EvidenceAssetError(
                    f"DataAssetDescriptor JSON field '{field_name}' has invalid type "
                    f"{type(data[field_name]).__name__} - expected str"
                )

        # Validate optional string field types (strict, no coercion)
        for field_name in (
            "source_url", "license", "version", "intended_use",
            "redistribution_notes", "update_cadence", "quality_notes"
        ):
            value = data.get(field_name, "")
            if value != "" and not isinstance(value, str):
                raise EvidenceAssetError(
                    f"DataAssetDescriptor JSON field '{field_name}' has invalid type "
                    f"{type(value).__name__} - expected str"
                )

        # Extract and validate tuple/list fields with strict type checking
        geographic_coverage_raw = data.get("geographic_coverage", [])
        if not isinstance(geographic_coverage_raw, (list, tuple)):
            raise EvidenceAssetError(
                f"DataAssetDescriptor JSON field 'geographic_coverage' has invalid type "
                f"{type(geographic_coverage_raw).__name__} - expected list or tuple"
            )
        geographic_coverage = tuple(str(v) for v in geographic_coverage_raw)

        years_raw = data.get("years", [])
        if not isinstance(years_raw, (list, tuple)):
            raise EvidenceAssetError(
                f"DataAssetDescriptor JSON field 'years' has invalid type "
                f"{type(years_raw).__name__} - expected list or tuple"
            )
        # Strict type validation: reject non-integer values (bool is subclass of int in Python)
        years_list: list[int] = []
        for v in years_raw:
            if not isinstance(v, int) or isinstance(v, bool):
                raise EvidenceAssetError(
                    f"DataAssetDescriptor JSON field 'years' contains non-integer value "
                    f"{v!r} of type {type(v).__name__} - expected int"
                )
            years_list.append(v)
        years = tuple(years_list)

        references_raw = data.get("references", [])
        if not isinstance(references_raw, (list, tuple)):
            raise EvidenceAssetError(
                f"DataAssetDescriptor JSON field 'references' has invalid type "
                f"{type(references_raw).__name__} - expected list or tuple"
            )
        references = tuple(str(v) for v in references_raw)

        # Validate bool field (strict, no coercion)
        redistribution_allowed = data.get("redistribution_allowed", False)
        if not isinstance(redistribution_allowed, bool):
            raise EvidenceAssetError(
                f"DataAssetDescriptor JSON field 'redistribution_allowed' has invalid "
                f"type {type(redistribution_allowed).__name__} - expected bool"
            )

        # Construct instance (triggers __post_init__ validation)
        try:
            return cls(
                asset_id=data["asset_id"],
                name=data["name"],
                description=data["description"],
                data_class=data["data_class"],
                origin=data["origin"],
                access_mode=data["access_mode"],
                trust_status=data["trust_status"],
                source_url=data.get("source_url", ""),
                license=data.get("license", ""),
                version=data.get("version", ""),
                geographic_coverage=geographic_coverage,
                years=years,
                intended_use=data.get("intended_use", ""),
                redistribution_allowed=redistribution_allowed,
                redistribution_notes=data.get("redistribution_notes", ""),
                update_cadence=data.get("update_cadence", ""),
                quality_notes=data.get("quality_notes", ""),
                references=references,
            )
        except EvidenceAssetError:
            # Re-raise as-is (already has actionable message)
            raise
        except (TypeError, ValueError) as exc:
            # Catch any other errors and wrap with actionable message
            raise EvidenceAssetError(
                f"DataAssetDescriptor JSON construction failed: {exc}"
            ) from exc
