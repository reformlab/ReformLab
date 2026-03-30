# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Typed asset schemas for each evidence taxonomy data class.

This module provides frozen dataclasses for structural, exogenous, calibration,
and validation asset types. Each asset type combines a DataAssetDescriptor
(governance envelope) with domain-specific payload fields.

The evidence taxonomy is defined in the synthetic data decision document
(Section 2.6): structural data defines who or what is modeled, exogenous data
provides observed/projected context inputs, calibration data fits the model to
reality, and validation data tests the model against independent observations.

Story 21.3 - implement-typed-structural-exogenous-calibration-and-validation-asset-schemas.

See also:
    - synthetic-data-decision-document-2026-03-23.md Section 2.7 for data taxonomy
    - descriptor.py for DataAssetDescriptor and governance envelope pattern
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, get_args

import pyarrow as pa

from reformlab.data.descriptor import (
    DataAssetAccessMode,
    DataAssetDescriptor,
    DataAssetOrigin,
    DataAssetTrustStatus,
)
from reformlab.data.errors import EvidenceAssetError

# ============================================================================
# Literal Type Definitions
# ============================================================================
# Story 21.3 / AC3, AC4
#
# These literal types define the valid values for calibration target types,
# validation types, and validation benchmark statuses.

CalibrationTargetType = Literal[
    "marginal",           # Distribution marginals
    "aggregate_total",    # Official aggregates (revenue, expenditure)
    "adoption_rate",      # Technology adoption rates
    "transition_rate",    # Year-over-year transition rates
]
"""Calibration target type literal.

Values define what aspect of the model is being calibrated:
- ``"marginal"``: Distribution marginals (e.g., income deciles)
- ``"aggregate_total"``: Official aggregates (e.g., total tax revenue)
- ``"adoption_rate"``: Technology adoption rates
- ``"transition_rate"``: Year-over-year transition rates

Story 21.3 / AC3.
"""

ValidationType = Literal[
    "marginal_check",           # Marginal distribution validation
    "joint_distribution",       # Cross-tab validation
    "subgroup_stability",       # Subgroup consistency checks
    "downstream_performance",   # Model output validation
]
"""Validation type literal.

Values define what kind of validation is performed:
- ``"marginal_check"``: Marginal distribution validation
- ``"joint_distribution"``: Cross-tabulation validation
- ``"subgroup_stability"``: Subgroup consistency checks
- ``"downstream_performance"``: Model output validation

Story 21.3 / AC4.
"""

ValidationBenchmarkStatus = Literal[
    "passed",
    "failed",
    "pending",
    "not_applicable",
]
"""Validation benchmark status literal.

Values define the outcome of a validation benchmark:
- ``"passed"``: Benchmark passed validation criteria
- ``"failed"``: Benchmark failed validation criteria
- ``"pending"``: Benchmark validation in progress
- ``"not_applicable"``: Benchmark not applicable to this asset

Story 21.3 / AC4.
"""

# ============================================================================
# Additional Literal Type Definitions — Story 21.5
# ============================================================================
#
# These literal types define valid values for train/test separation,
# calibration methods, and validation methods.

HoldoutGroup = Literal[
    "train",
    "validation",
    "test",
]
"""Holdout group literal for train/test separation.

Values define which holdout group a calibration or validation dataset belongs to:
- ``"train"``: In-sample training data for calibration
- ``"validation"``: Holdout validation set for tuning
- ``"test"``: Final test set for evaluation

Story 21.5 / Task 1.
"""

CalibrationMethod = Literal[
    "maximum_likelihood",
    "method_of_moments",
    "bayesian",
]
"""Calibration method literal.

Values define which statistical method is used for calibration:
- ``"maximum_likelihood"``: Maximum likelihood estimation
- ``"method_of_moments"``: Method of moments estimation
- ``"bayesian"``: Bayesian estimation with priors

Story 21.5 / Task 1.
"""

ValidationMethod = Literal[
    "holdout",
    "cross_validation",
    "external",
    "bootstrap",
]
"""Validation method literal.

Values define which validation method is used:
- ``"holdout"``: Single train/validation/test split
- ``"cross_validation"``: K-fold cross-validation
- ``"external"``: External validation against independent dataset
- ``"bootstrap"``: Bootstrap resampling validation

Story 21.5 / Task 1.
"""

# Runtime validation constants for Literal types
# Using get_args() ensures single source of truth from Literal definitions (Story 21.1 pattern)
_VALID_CALIBRATION_TARGET_TYPES = get_args(CalibrationTargetType)
_VALID_VALIDATION_TYPES = get_args(ValidationType)
_VALID_BENCHMARK_STATUSES = get_args(ValidationBenchmarkStatus)
_VALID_HOLDOUT_GROUPS = get_args(HoldoutGroup)
_VALID_CALIBRATION_METHODS = get_args(CalibrationMethod)
_VALID_VALIDATION_METHODS = get_args(ValidationMethod)

# ============================================================================
# Structural Asset
# ============================================================================
# Story 21.3 / AC1


@dataclass(frozen=True)
class StructuralAsset:
    """Structural data asset with governance envelope.

    Combines DataAssetDescriptor (governance metadata) with structural-
    specific payload (entity tables, relationships, record counts).

    Structural data defines who or what is modeled — households, persons,
    firms, places, and the relationships between them.

    Attributes
    ----------
    descriptor : DataAssetDescriptor
        Governance envelope with asset_id, name, origin, trust status, etc.
        Must have ``data_class="structural"``.
    table : pa.Table
        PyArrow table containing the entity data.
    entity_type : str
        Type of entity (e.g., ``"household"``, ``"person"``, ``"firm"``).
    record_count : int
        Number of records in the table. Must match ``table.num_rows``.
    relationships : tuple[str, ...]
        Entity-to-entity relationship links (e.g., ``("household", "person")``).
    primary_key : str
        Primary key column name in the table.

    Story 21.3 / AC1.
    """

    descriptor: DataAssetDescriptor
    table: pa.Table
    entity_type: str
    record_count: int
    relationships: tuple[str, ...] = ()
    primary_key: str = ""

    def __post_init__(self) -> None:
        """Validate data_class and record count match.

        Raises EvidenceAssetError if validation fails.

        Note: Record count validation is skipped when table is empty,
        as this indicates a placeholder from ``from_json()`` deserialization
        where the caller must load and set the actual table.

        Story 21.3 / AC9.
        """
        if self.descriptor.data_class != "structural":
            raise EvidenceAssetError(
                f"StructuralAsset requires data_class='structural', "
                f"got '{self.descriptor.data_class}'"
            )

        # Skip record_count validation for empty tables (JSON deserialization placeholder)
        # The caller is responsible for loading the actual table and ensuring consistency
        if self.table.num_rows > 0 and self.record_count != self.table.num_rows:
            raise EvidenceAssetError(
                f"StructuralAsset record_count mismatch: "
                f"expected {self.table.num_rows}, got {self.record_count}"
            )

    def to_json(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict.

        The table is NOT serialized. Callers must store/retrieve tables
        separately using their own storage layer.

        Story 21.3 / AC6.

        Returns
        -------
        dict[str, Any]
            JSON-serializable representation.
        """
        result: dict[str, Any] = {
            "descriptor": self.descriptor.to_json(),
            "entity_type": self.entity_type,
            "record_count": self.record_count,
        }
        if self.relationships:
            result["relationships"] = list(self.relationships)
        if self.primary_key:
            result["primary_key"] = self.primary_key
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> StructuralAsset:
        """Deserialize from a JSON-compatible dict with validation.

        The caller must load the table separately and construct the full
        asset, as the table is not serialized.

        Story 21.3 / AC6.

        Parameters
        ----------
        data : dict[str, Any]
            JSON dict representation of a StructuralAsset.

        Returns
        -------
        StructuralAsset
            Immutable asset instance with descriptor restored from JSON.

        Raises
        ------
        EvidenceAssetError
            If validation fails (data_class mismatch, missing fields, etc.).
        """
        if not isinstance(data, dict):
            raise EvidenceAssetError(
                "StructuralAsset JSON must be an object - provide a JSON object"
            )

        # Validate required fields
        required_fields = ("descriptor", "entity_type", "record_count")
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise EvidenceAssetError(
                f"StructuralAsset JSON missing required fields: {', '.join(missing)}"
            )

        # Validate data_class through descriptor construction
        descriptor = DataAssetDescriptor.from_json(data["descriptor"])

        # Validate required field types (fail-loud, no coercion)
        if not isinstance(data["entity_type"], str):
            raise EvidenceAssetError(
                f"StructuralAsset JSON 'entity_type' has invalid type "
                f"{type(data['entity_type']).__name__} - expected string"
            )
        if not isinstance(data["record_count"], int) or isinstance(data["record_count"], bool):
            raise EvidenceAssetError(
                f"StructuralAsset JSON 'record_count' has invalid type "
                f"{type(data['record_count']).__name__} - expected integer"
            )

        # Extract optional fields with type validation
        relationships_raw = data.get("relationships", [])
        if relationships_raw is not None and not isinstance(relationships_raw, (list, tuple)):
            raise EvidenceAssetError(
                f"StructuralAsset JSON 'relationships' has invalid type "
                f"{type(relationships_raw).__name__} - expected list or tuple"
            )
        relationships = tuple(str(v) for v in relationships_raw) if relationships_raw else ()

        primary_key_raw = data.get("primary_key", "")
        if primary_key_raw is not None and not isinstance(primary_key_raw, str):
            raise EvidenceAssetError(
                f"StructuralAsset JSON 'primary_key' has invalid type "
                f"{type(primary_key_raw).__name__} - expected string or null"
            )
        primary_key = primary_key_raw if primary_key_raw is not None else ""

        # Construct instance (triggers __post_init__ validation)
        return cls(
            descriptor=descriptor,
            table=pa.Table.from_pydict({}),  # Empty placeholder - caller must replace
            entity_type=data["entity_type"],
            record_count=data["record_count"],
            relationships=relationships,
            primary_key=primary_key,
        )


# ============================================================================
# Exogenous Asset
# ============================================================================
# Story 21.3 / AC2


@dataclass(frozen=True)
class ExogenousAsset:
    """Exogenous time series asset with governance envelope.

    Exogenous data provides observed or projected context inputs — energy
    prices, carbon tax rates, technology costs, demographic projections, etc.

    The ``name`` field is the series identifier for lookup (e.g.,
    ``"energy_price_electricity"``), distinct from ``descriptor.name`` which
    is the human-readable display name.

    Attributes
    ----------
    descriptor : DataAssetDescriptor
        Governance envelope. Must have ``data_class="exogenous"``.
    name : str
        Series identifier for lookup (e.g., ``"energy_price_electricity"``).
        Distinct from ``descriptor.name`` (display name).
    values : dict[int, float]
        Year-indexed values. Keys must be integers, values must be finite.
    unit : str
        Physical unit (e.g., ``"EUR/kWh"``, ``"EUR/ton"``).
    frequency : str
        Source frequency (e.g., ``"annual"``, ``"quarterly"``).
    source : str
        Institutional provenance (e.g., ``"French Ministry of Ecology"``).
    vintage : str
        Publication vintage (e.g., ``"2024-Q1"``).
    interpolation_method : str
        Interpolation strategy: ``"linear"``, ``"step"``, or ``"none"``.
    aggregation_method : str
        How source values are aggregated (e.g., ``"mean"``, ``"sum"``).
    revision_policy : str
        How revisions are tracked (e.g., ``"latest"``, ``"vintaged"``).

    Story 21.3 / AC2.
    """

    descriptor: DataAssetDescriptor
    name: str
    values: dict[int, float]
    unit: str
    frequency: str = "annual"
    source: str = ""
    vintage: str = ""
    interpolation_method: str = "linear"
    aggregation_method: str = "mean"
    revision_policy: str = ""

    def __post_init__(self) -> None:
        """Validate data_class, values non-empty, and all values are finite.

        Raises EvidenceAssetError if validation fails.

        Story 21.3 / AC9, AC10.
        """
        if self.descriptor.data_class != "exogenous":
            raise EvidenceAssetError(
                f"ExogenousAsset requires data_class='exogenous', "
                f"got '{self.descriptor.data_class}'"
            )

        # Validate interpolation_method value (fail-fast at construction)
        if self.interpolation_method not in ("linear", "step", "none"):
            raise EvidenceAssetError(
                f"ExogenousAsset interpolation_method {self.interpolation_method!r} is invalid - "
                f"use 'linear', 'step', or 'none'"
            )

        if not self.values:
            raise EvidenceAssetError(
                "ExogenousAsset values must be non-empty - provide at least one year-value pair"
            )

        # Validate year keys are integers
        for year in self.values.keys():
            if not isinstance(year, int) or isinstance(year, bool):
                raise EvidenceAssetError(
                    f"ExogenousAsset years must be integers - got {type(year).__name__}: {year!r}"
                )

        # Validate values are finite (not NaN or infinite)
        for year, value in self.values.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise EvidenceAssetError(
                    f"ExogenousAsset value for year {year} must be numeric - "
                    f"got {type(value).__name__}: {value!r}"
                )
            if not math.isfinite(value):
                raise EvidenceAssetError(
                    f"ExogenousAsset values must be finite - "
                    f"year {year} has value {value!r} (NaN or infinite)"
                )

    def get_value(self, year: int) -> float:
        """Get value for year with interpolation.

        If the year is directly in ``values``, returns the exact value.
        Otherwise, interpolates according to ``interpolation_method``:
        - ``"linear"``: Linear interpolation between nearest years
        - ``"step"``: Use the value from the nearest previous year
        - ``"none"``: Raise ``EvidenceAssetError`` if year not in ``values``

        Story 21.3 / AC2.

        Parameters
        ----------
        year : int
            Year to look up.

        Returns
        -------
        float
            Value for the requested year.

        Raises
        ------
        EvidenceAssetError
            If year is outside the range of available data and interpolation
            is requested, or if interpolation method is ``"none"`` and the
            year is not directly available.
        """
        if year in self.values:
            return self.values[year]

        if self.interpolation_method == "none":
            raise EvidenceAssetError(
                f"ExogenousAsset has no data for year {year} "
                f"(interpolation_method='none')"
            )

        sorted_years = sorted(self.values.keys())
        min_year, max_year = sorted_years[0], sorted_years[-1]

        if year < min_year or year > max_year:
            raise EvidenceAssetError(
                f"ExogenousAsset year {year} is out of range "
                f"[{min_year}, {max_year}] - cannot extrapolate"
            )

        # Find surrounding years
        lower_year = max(y for y in sorted_years if y <= year)
        upper_year = min(y for y in sorted_years if y >= year)

        if self.interpolation_method == "step":
            # Use nearest previous year's value
            return self.values[lower_year]

        if self.interpolation_method == "linear":
            # Linear interpolation
            if lower_year == upper_year:
                return self.values[lower_year]

            lower_value = self.values[lower_year]
            upper_value = self.values[upper_year]
            weight = (year - lower_year) / (upper_year - lower_year)
            return lower_value + weight * (upper_value - lower_value)

        raise EvidenceAssetError(
            f"ExogenousAsset unsupported interpolation_method: {self.interpolation_method!r} - "
            f"use 'linear', 'step', or 'none'"
        )

    def validate_coverage(self, start_year: int, end_year: int) -> None:
        """Validate coverage for a range of years.

        Raises ``EvidenceAssetError`` if any year in the range is missing
        from ``values`` or if the range is inverted.

        Story 21.3 / AC2.

        Parameters
        ----------
        start_year : int
            First year of range (inclusive).
        end_year : int
            Last year of range (inclusive).

        Raises
        ------
        EvidenceAssetError
            If start_year > end_year or if any year in the range is missing.
        """
        if start_year > end_year:
            raise EvidenceAssetError(
                f"ExogenousAsset validate_coverage() start_year ({start_year}) "
                f"must be <= end_year ({end_year})"
            )
        missing = [y for y in range(start_year, end_year + 1) if y not in self.values]
        if missing:
            raise EvidenceAssetError(
                f"ExogenousAsset coverage incomplete - missing years: {missing}"
            )

    def to_json(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict.

        Story 21.3 / AC6.

        Returns
        -------
        dict[str, Any]
            JSON-serializable representation.
        """
        result: dict[str, Any] = {
            "descriptor": self.descriptor.to_json(),
            "name": self.name,
            "values": {str(year): value for year, value in self.values.items()},
            "unit": self.unit,
        }
        if self.frequency != "annual":
            result["frequency"] = self.frequency
        if self.source:
            result["source"] = self.source
        if self.vintage:
            result["vintage"] = self.vintage
        if self.interpolation_method != "linear":
            result["interpolation_method"] = self.interpolation_method
        if self.aggregation_method != "mean":
            result["aggregation_method"] = self.aggregation_method
        if self.revision_policy:
            result["revision_policy"] = self.revision_policy
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ExogenousAsset:
        """Deserialize from a JSON-compatible dict with full validation.

        Story 21.3 / AC6.

        Parameters
        ----------
        data : dict[str, Any]
            JSON dict representation of an ExogenousAsset.

        Returns
        -------
        ExogenousAsset
            Immutable asset instance.

        Raises
        ------
        EvidenceAssetError
            If validation fails.
        """
        if not isinstance(data, dict):
            raise EvidenceAssetError(
                "ExogenousAsset JSON must be an object - provide a JSON object"
            )

        required_fields = ("descriptor", "name", "values", "unit")
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise EvidenceAssetError(
                f"ExogenousAsset JSON missing required fields: {', '.join(missing)}"
            )

        # Validate values: year keys are strings in JSON, convert to int
        values_raw = data["values"]
        if not isinstance(values_raw, dict):
            raise EvidenceAssetError(
                f"ExogenousAsset JSON 'values' has invalid type "
                f"{type(values_raw).__name__} - expected object"
            )

        values: dict[int, float] = {}
        for year_str, value in values_raw.items():
            try:
                year = int(year_str)
            except (ValueError, TypeError) as exc:
                raise EvidenceAssetError(
                    f"ExogenousAsset JSON 'values' key {year_str!r} is not a valid year"
                ) from exc
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise EvidenceAssetError(
                    f"ExogenousAsset JSON 'values' year {year} has invalid value type "
                    f"{type(value).__name__} - expected number"
                )
            values[year] = float(value)

        # Construct descriptor and asset
        descriptor = DataAssetDescriptor.from_json(data["descriptor"])

        # Validate string field types (fail-loud, no coercion)
        if not isinstance(data["name"], str):
            raise EvidenceAssetError(
                f"ExogenousAsset JSON 'name' has invalid type "
                f"{type(data['name']).__name__} - expected string"
            )
        if not isinstance(data["unit"], str):
            raise EvidenceAssetError(
                f"ExogenousAsset JSON 'unit' has invalid type "
                f"{type(data['unit']).__name__} - expected string"
            )

        # Optional string fields with type validation
        frequency = data.get("frequency", "annual")
        if not isinstance(frequency, str):
            raise EvidenceAssetError(
                f"ExogenousAsset JSON 'frequency' has invalid type "
                f"{type(frequency).__name__} - expected string"
            )

        source = data.get("source", "")
        if source is not None and not isinstance(source, str):
            raise EvidenceAssetError(
                f"ExogenousAsset JSON 'source' has invalid type "
                f"{type(source).__name__} - expected string or null"
            )

        vintage = data.get("vintage", "")
        if vintage is not None and not isinstance(vintage, str):
            raise EvidenceAssetError(
                f"ExogenousAsset JSON 'vintage' has invalid type "
                f"{type(vintage).__name__} - expected string or null"
            )

        interpolation_method = data.get("interpolation_method", "linear")
        if not isinstance(interpolation_method, str):
            raise EvidenceAssetError(
                f"ExogenousAsset JSON 'interpolation_method' has invalid type "
                f"{type(interpolation_method).__name__} - expected string"
            )

        aggregation_method = data.get("aggregation_method", "mean")
        if not isinstance(aggregation_method, str):
            raise EvidenceAssetError(
                f"ExogenousAsset JSON 'aggregation_method' has invalid type "
                f"{type(aggregation_method).__name__} - expected string"
            )

        revision_policy = data.get("revision_policy", "")
        if revision_policy is not None and not isinstance(revision_policy, str):
            raise EvidenceAssetError(
                f"ExogenousAsset JSON 'revision_policy' has invalid type "
                f"{type(revision_policy).__name__} - expected string or null"
            )

        return cls(
            descriptor=descriptor,
            name=data["name"],
            values=values,
            unit=data["unit"],
            frequency=frequency,
            source=source if source is not None else "",
            vintage=vintage if vintage is not None else "",
            interpolation_method=interpolation_method,
            aggregation_method=aggregation_method,
            revision_policy=revision_policy if revision_policy is not None else "",
        )


# ============================================================================
# Calibration Asset
# ============================================================================
# Story 21.3 / AC3


@dataclass(frozen=True)
class CalibrationAsset:
    """Calibration target asset with governance envelope.

    Calibration data defines targets for fitting the model to observed reality —
    distribution marginals, official aggregates, technology adoption rates, etc.

    Story 21.5 extends CalibrationAsset with train/test separation fields to prevent
    leakage between calibration and validation data.

    Attributes
    ----------
    descriptor : DataAssetDescriptor
        Governance envelope. Must have ``data_class="calibration"``.
    target_type : CalibrationTargetType
        Type of calibration target (marginal, aggregate_total, etc.).
    coverage : str
        Geographic or demographic coverage (e.g., ``"national"``, ``"regional"``).
    source_material : tuple[str, ...]
        Literature citations or source references.
    margin_of_error : float | None
        Acceptable margin of error for calibration (e.g., ``0.05`` for 5%).
    confidence_level : float | None
        Statistical confidence level (e.g., ``0.95`` for 95% confidence).
    methodology_notes : str
        Free-text notes on calibration methodology.
    is_in_sample : bool
        Whether this calibration data is in-sample (True) or out-of-sample (False).
        Story 21.5 / Task 1.
    holdout_group : HoldoutGroup | None
        Holdout group designation for train/test separation. None if not applicable.
        Story 21.5 / Task 1.
    calibration_method : CalibrationMethod
        Statistical method used for calibration. Story 21.5 / Task 1.
    target_years : tuple[int, ...]
        Years covered by this calibration target. Story 21.5 / Task 1.

    Story 21.3 / AC3, Story 21.5 / Task 1.
    """

    descriptor: DataAssetDescriptor
    target_type: CalibrationTargetType
    coverage: str
    source_material: tuple[str, ...] = ()
    margin_of_error: float | None = None
    confidence_level: float | None = None
    methodology_notes: str = ""
    # Story 21.5 / Task 1: Train/test separation fields
    is_in_sample: bool = True
    holdout_group: HoldoutGroup | None = None
    calibration_method: CalibrationMethod = "maximum_likelihood"
    target_years: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        """Validate data_class, target_type, and new Story 21.5 fields.

        Raises EvidenceAssetError if validation fails.

        Story 21.3 / AC9, AC10, Story 21.5 / Task 1.
        """
        if self.descriptor.data_class != "calibration":
            raise EvidenceAssetError(
                f"CalibrationAsset requires data_class='calibration', "
                f"got '{self.descriptor.data_class}'"
            )

        if self.target_type not in _VALID_CALIBRATION_TARGET_TYPES:
            raise EvidenceAssetError(
                f"CalibrationAsset target_type {self.target_type!r} is not a valid "
                f"CalibrationTargetType - use one of {_VALID_CALIBRATION_TARGET_TYPES}"
            )

        # Story 21.5 / Task 1: Validate holdout_group is valid
        if self.holdout_group is not None and self.holdout_group not in _VALID_HOLDOUT_GROUPS:
            raise EvidenceAssetError(
                f"CalibrationAsset holdout_group {self.holdout_group!r} is not a valid "
                f"HoldoutGroup - use one of {_VALID_HOLDOUT_GROUPS} or None"
            )

        # Story 21.5 / Task 1: Validate calibration_method is valid
        if self.calibration_method not in _VALID_CALIBRATION_METHODS:
            raise EvidenceAssetError(
                f"CalibrationAsset calibration_method {self.calibration_method!r} is not a valid "
                f"CalibrationMethod - use one of {_VALID_CALIBRATION_METHODS}"
            )

    def to_json(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict.

        Story 21.3 / AC6, Story 21.5 / Task 1.

        Returns
        -------
        dict[str, Any]
            JSON-serializable representation.
        """
        result: dict[str, Any] = {
            "descriptor": self.descriptor.to_json(),
            "target_type": self.target_type,
            "coverage": self.coverage,
            # Story 21.5 / Task 1: New train/test separation fields
            "is_in_sample": self.is_in_sample,
            "calibration_method": self.calibration_method,
        }
        if self.source_material:
            result["source_material"] = list(self.source_material)
        if self.margin_of_error is not None:
            result["margin_of_error"] = self.margin_of_error
        if self.confidence_level is not None:
            result["confidence_level"] = self.confidence_level
        if self.methodology_notes:
            result["methodology_notes"] = self.methodology_notes
        # Story 21.5 / Task 1: Optional fields (include when not default)
        if self.holdout_group is not None:
            result["holdout_group"] = self.holdout_group
        if self.target_years:
            result["target_years"] = list(self.target_years)
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> CalibrationAsset:
        """Deserialize from a JSON-compatible dict with full validation.

        Story 21.3 / AC6, Story 21.5 / Task 1.

        Parameters
        ----------
        data : dict[str, Any]
            JSON dict representation of a CalibrationAsset.

        Returns
        -------
        CalibrationAsset
            Immutable asset instance.

        Raises
        ------
        EvidenceAssetError
            If validation fails.
        """
        if not isinstance(data, dict):
            raise EvidenceAssetError(
                "CalibrationAsset JSON must be an object - provide a JSON object"
            )

        required_fields = ("descriptor", "target_type", "coverage")
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise EvidenceAssetError(
                f"CalibrationAsset JSON missing required fields: {', '.join(missing)}"
            )

        # Validate target_type is a valid literal value
        target_type = data["target_type"]
        if target_type not in _VALID_CALIBRATION_TARGET_TYPES:
            raise EvidenceAssetError(
                f"CalibrationAsset JSON target_type {target_type!r} is not a valid "
                f"CalibrationTargetType - use one of {_VALID_CALIBRATION_TARGET_TYPES}"
            )

        # Story 21.5 / Task 1: Validate calibration_method
        calibration_method = data.get("calibration_method", "maximum_likelihood")
        if calibration_method not in _VALID_CALIBRATION_METHODS:
            raise EvidenceAssetError(
                f"CalibrationAsset JSON calibration_method {calibration_method!r} is not a valid "
                f"CalibrationMethod - use one of {_VALID_CALIBRATION_METHODS}"
            )

        # Story 21.5 / Task 1: Extract and validate is_in_sample (default True for backward compat)
        is_in_sample = data.get("is_in_sample", True)
        if not isinstance(is_in_sample, bool):
            raise EvidenceAssetError(
                f"CalibrationAsset JSON 'is_in_sample' has invalid type "
                f"{type(is_in_sample).__name__} - expected boolean"
            )

        # Story 21.5 / Task 1: Extract and validate holdout_group (optional)
        holdout_group = data.get("holdout_group")
        if holdout_group is not None and holdout_group not in _VALID_HOLDOUT_GROUPS:
            raise EvidenceAssetError(
                f"CalibrationAsset JSON holdout_group {holdout_group!r} is not a valid "
                f"HoldoutGroup - use one of {_VALID_HOLDOUT_GROUPS} or null"
            )

        # Story 21.5 / Task 1: Extract and validate target_years (optional)
        target_years_raw = data.get("target_years", [])
        if target_years_raw is not None and not isinstance(target_years_raw, (list, tuple)):
            raise EvidenceAssetError(
                f"CalibrationAsset JSON 'target_years' has invalid type "
                f"{type(target_years_raw).__name__} - expected list or tuple"
            )
        target_years: tuple[int, ...] = ()
        if target_years_raw:
            target_years_list = []
            for y in target_years_raw:
                if not isinstance(y, int) or isinstance(y, bool):
                    raise EvidenceAssetError(
                        f"CalibrationAsset JSON 'target_years' contains invalid value "
                        f"{y!r} (type {type(y).__name__}) - expected integers"
                    )
                target_years_list.append(int(y))
            target_years = tuple(target_years_list)

        # Extract optional fields with type validation
        source_material_raw = data.get("source_material", [])
        if source_material_raw is not None and not isinstance(source_material_raw, (list, tuple)):
            raise EvidenceAssetError(
                f"CalibrationAsset JSON 'source_material' has invalid type "
                f"{type(source_material_raw).__name__} - expected list or tuple"
            )
        source_material = tuple(str(v) for v in source_material_raw) if source_material_raw else ()

        margin_of_error = data.get("margin_of_error")
        if margin_of_error is not None and not isinstance(margin_of_error, (int, float)):
            raise EvidenceAssetError(
                f"CalibrationAsset JSON 'margin_of_error' has invalid type "
                f"{type(margin_of_error).__name__} - expected number or null"
            )

        confidence_level = data.get("confidence_level")
        if confidence_level is not None and not isinstance(confidence_level, (int, float)):
            raise EvidenceAssetError(
                f"CalibrationAsset JSON 'confidence_level' has invalid type "
                f"{type(confidence_level).__name__} - expected number or null"
            )

        methodology_notes = data.get("methodology_notes", "")
        if methodology_notes is not None and not isinstance(methodology_notes, str):
            raise EvidenceAssetError(
                f"CalibrationAsset JSON 'methodology_notes' has invalid type "
                f"{type(methodology_notes).__name__} - expected string or null"
            )

        # Validate required field types (fail-loud, no coercion)
        if not isinstance(data["coverage"], str):
            raise EvidenceAssetError(
                f"CalibrationAsset JSON 'coverage' has invalid type "
                f"{type(data['coverage']).__name__} - expected string"
            )

        # Construct descriptor and asset
        descriptor = DataAssetDescriptor.from_json(data["descriptor"])

        return cls(
            descriptor=descriptor,
            target_type=target_type,
            coverage=data["coverage"],
            source_material=source_material,
            margin_of_error=float(margin_of_error) if margin_of_error is not None else None,
            confidence_level=float(confidence_level) if confidence_level is not None else None,
            methodology_notes=methodology_notes if methodology_notes is not None else "",
            # Story 21.5 / Task 1: New train/test separation fields
            is_in_sample=is_in_sample,
            holdout_group=holdout_group,
            calibration_method=calibration_method,
            target_years=target_years,
        )


# ============================================================================
# Validation Asset
# ============================================================================
# Story 21.3 / AC4


@dataclass(frozen=True)
class ValidationAsset:
    """Validation benchmark asset with governance envelope.

    Validation data defines how the model is tested against independent
    observations — marginal distribution checks, joint distribution tests,
    subgroup stability verification, downstream performance validation, etc.

    Story 21.5 extends ValidationAsset with certification fields for explicit
    validation dossier requirements and production-safe trust status upgrades.

    Attributes
    ----------
    descriptor : DataAssetDescriptor
        Governance envelope. Must have ``data_class="validation"``.
    validation_type : ValidationType
        Type of validation (marginal_check, joint_distribution, etc.).
    benchmark_status : ValidationBenchmarkStatus
        Outcome of validation (passed, failed, pending, not_applicable).
    criteria : dict[str, Any]
        Validation criteria (e.g., ``{"max_relative_error": 0.05}``).
    last_validated : str
        ISO 8601 timestamp of last validation (e.g., ``"2024-03-15T10:30:00Z"``).
    validation_dossier : str
        URL or path to validation dossier documentation.
    trust_status_upgradable : bool
        Whether the benchmark status can be improved with additional evidence.
    certified_at : str | None
        ISO 8601 timestamp of certification (when trust_status upgraded to
        production-safe). Story 21.5 / Task 1.
    certified_by : str | None
        Actor identity (username or system ID) that certified this benchmark.
        Story 21.5 / Task 1.
    validation_method : ValidationMethod
        Validation method used (holdout, cross_validation, external, bootstrap).
        Story 21.5 / Task 1.
    holdout_years : tuple[int, ...]
        Holdout years covered by this validation benchmark. Story 21.5 / Task 1.

    Story 21.3 / AC4, Story 21.5 / Task 1.
    """

    descriptor: DataAssetDescriptor
    validation_type: ValidationType
    benchmark_status: ValidationBenchmarkStatus
    criteria: dict[str, Any]
    last_validated: str = ""
    validation_dossier: str = ""
    trust_status_upgradable: bool = False
    # Story 21.5 / Task 1: Certification fields
    certified_at: str | None = None
    certified_by: str | None = None
    validation_method: ValidationMethod = "holdout"
    holdout_years: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        """Validate data_class, validation_type, benchmark_status, and Story 21.5 fields.

        Raises EvidenceAssetError if validation fails.

        Story 21.3 / AC9, AC10, Story 21.5 / Task 1.
        """
        if self.descriptor.data_class != "validation":
            raise EvidenceAssetError(
                f"ValidationAsset requires data_class='validation', "
                f"got '{self.descriptor.data_class}'"
            )

        if self.validation_type not in _VALID_VALIDATION_TYPES:
            raise EvidenceAssetError(
                f"ValidationAsset validation_type {self.validation_type!r} is not a valid "
                f"ValidationType - use one of {_VALID_VALIDATION_TYPES}"
            )

        if self.benchmark_status not in _VALID_BENCHMARK_STATUSES:
            raise EvidenceAssetError(
                f"ValidationAsset benchmark_status {self.benchmark_status!r} is not a valid "
                f"ValidationBenchmarkStatus - use one of {_VALID_BENCHMARK_STATUSES}"
            )

        # Story 21.5 / Task 1: Validate validation_method is valid
        if self.validation_method not in _VALID_VALIDATION_METHODS:
            raise EvidenceAssetError(
                f"ValidationAsset validation_method {self.validation_method!r} is not a valid "
                f"ValidationMethod - use one of {_VALID_VALIDATION_METHODS}"
            )

    def to_json(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict.

        Story 21.3 / AC6, Story 21.5 / Task 1.

        Returns
        -------
        dict[str, Any]
            JSON-serializable representation.
        """
        result: dict[str, Any] = {
            "descriptor": self.descriptor.to_json(),
            "validation_type": self.validation_type,
            "benchmark_status": self.benchmark_status,
            "criteria": self.criteria,
            # Story 21.5 / Task 1: New certification fields
            "validation_method": self.validation_method,
        }
        if self.last_validated:
            result["last_validated"] = self.last_validated
        if self.validation_dossier:
            result["validation_dossier"] = self.validation_dossier
        if self.trust_status_upgradable:
            result["trust_status_upgradable"] = True
        # Story 21.5 / Task 1: Optional certification fields (include when set)
        if self.certified_at is not None:
            result["certified_at"] = self.certified_at
        if self.certified_by is not None:
            result["certified_by"] = self.certified_by
        if self.holdout_years:
            result["holdout_years"] = list(self.holdout_years)
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ValidationAsset:
        """Deserialize from a JSON-compatible dict with full validation.

        Story 21.3 / AC6, Story 21.5 / Task 1.

        Parameters
        ----------
        data : dict[str, Any]
            JSON dict representation of a ValidationAsset.

        Returns
        -------
        ValidationAsset
            Immutable asset instance.

        Raises
        ------
        EvidenceAssetError
            If validation fails.
        """
        if not isinstance(data, dict):
            raise EvidenceAssetError(
                "ValidationAsset JSON must be an object - provide a JSON object"
            )

        required_fields = ("descriptor", "validation_type", "benchmark_status", "criteria")
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise EvidenceAssetError(
                f"ValidationAsset JSON missing required fields: {', '.join(missing)}"
            )

        # Validate literal types
        validation_type = data["validation_type"]
        if validation_type not in _VALID_VALIDATION_TYPES:
            raise EvidenceAssetError(
                f"ValidationAsset JSON validation_type {validation_type!r} is not a valid "
                f"ValidationType - use one of {_VALID_VALIDATION_TYPES}"
            )

        benchmark_status = data["benchmark_status"]
        if benchmark_status not in _VALID_BENCHMARK_STATUSES:
            raise EvidenceAssetError(
                f"ValidationAsset JSON benchmark_status {benchmark_status!r} is not a valid "
                f"ValidationBenchmarkStatus - use one of {_VALID_BENCHMARK_STATUSES}"
            )

        # Validate criteria is a dict
        criteria = data["criteria"]
        if not isinstance(criteria, dict):
            raise EvidenceAssetError(
                f"ValidationAsset JSON 'criteria' has invalid type "
                f"{type(criteria).__name__} - expected object"
            )

        # Story 21.5 / Task 1: Validate validation_method
        validation_method = data.get("validation_method", "holdout")
        if validation_method not in _VALID_VALIDATION_METHODS:
            raise EvidenceAssetError(
                f"ValidationAsset JSON validation_method {validation_method!r} is not a valid "
                f"ValidationMethod - use one of {_VALID_VALIDATION_METHODS}"
            )

        # Story 21.5 / Task 1: Extract and validate certified_at (optional)
        certified_at = data.get("certified_at")
        if certified_at is not None and not isinstance(certified_at, str):
            raise EvidenceAssetError(
                f"ValidationAsset JSON 'certified_at' has invalid type "
                f"{type(certified_at).__name__} - expected string or null"
            )

        # Story 21.5 / Task 1: Extract and validate certified_by (optional)
        certified_by = data.get("certified_by")
        if certified_by is not None and not isinstance(certified_by, str):
            raise EvidenceAssetError(
                f"ValidationAsset JSON 'certified_by' has invalid type "
                f"{type(certified_by).__name__} - expected string or null"
            )

        # Story 21.5 / Task 1: Extract and validate holdout_years (optional)
        holdout_years_raw = data.get("holdout_years", [])
        if holdout_years_raw is not None and not isinstance(holdout_years_raw, (list, tuple)):
            raise EvidenceAssetError(
                f"ValidationAsset JSON 'holdout_years' has invalid type "
                f"{type(holdout_years_raw).__name__} - expected list or tuple"
            )
        holdout_years: tuple[int, ...] = ()
        if holdout_years_raw:
            holdout_years_list = []
            for y in holdout_years_raw:
                if not isinstance(y, int) or isinstance(y, bool):
                    raise EvidenceAssetError(
                        f"ValidationAsset JSON 'holdout_years' contains invalid value "
                        f"{y!r} (type {type(y).__name__}) - expected integers"
                    )
                holdout_years_list.append(int(y))
            holdout_years = tuple(holdout_years_list)

        # Extract optional fields with type validation
        last_validated = data.get("last_validated", "")
        if last_validated is not None and not isinstance(last_validated, str):
            raise EvidenceAssetError(
                f"ValidationAsset JSON 'last_validated' has invalid type "
                f"{type(last_validated).__name__} - expected string or null"
            )

        validation_dossier = data.get("validation_dossier", "")
        if validation_dossier is not None and not isinstance(validation_dossier, str):
            raise EvidenceAssetError(
                f"ValidationAsset JSON 'validation_dossier' has invalid type "
                f"{type(validation_dossier).__name__} - expected string or null"
            )

        trust_status_upgradable_raw = data.get("trust_status_upgradable", False)
        if trust_status_upgradable_raw is not None and not isinstance(trust_status_upgradable_raw, bool):
            raise EvidenceAssetError(
                f"ValidationAsset JSON 'trust_status_upgradable' has invalid type "
                f"{type(trust_status_upgradable_raw).__name__} - expected boolean or null"
            )
        trust_status_upgradable = (
            trust_status_upgradable_raw if trust_status_upgradable_raw is not None else False
        )

        # Construct descriptor and asset
        descriptor = DataAssetDescriptor.from_json(data["descriptor"])

        return cls(
            descriptor=descriptor,
            validation_type=validation_type,
            benchmark_status=benchmark_status,
            criteria=criteria,
            last_validated=last_validated if last_validated is not None else "",
            validation_dossier=validation_dossier if validation_dossier is not None else "",
            trust_status_upgradable=trust_status_upgradable,
            # Story 21.5 / Task 1: New certification fields
            certified_at=certified_at,
            certified_by=certified_by,
            validation_method=validation_method,
            holdout_years=holdout_years,
        )


# ============================================================================
# Factory Functions
# ============================================================================
# Story 21.3 / AC8


def create_structural_asset(
    # Descriptor fields
    asset_id: str,
    name: str,
    description: str,
    origin: DataAssetOrigin,
    access_mode: DataAssetAccessMode,
    trust_status: DataAssetTrustStatus,
    # Structural-specific fields
    table: pa.Table,
    entity_type: str,
    record_count: int,
    relationships: tuple[str, ...] = (),
    primary_key: str = "",
    # Optional descriptor fields
    source_url: str = "",
    license: str = "",
    version: str = "",
    geographic_coverage: tuple[str, ...] = (),
    years: tuple[int, ...] = (),
    intended_use: str = "",
    redistribution_allowed: bool = False,
    redistribution_notes: str = "",
    update_cadence: str = "",
    quality_notes: str = "",
    references: tuple[str, ...] = (),
) -> StructuralAsset:
    """Factory function for creating StructuralAsset with validated descriptor.

    Constructs a ``DataAssetDescriptor`` with ``data_class="structural"`` and
    wraps it in a ``StructuralAsset``.

    Story 21.3 / AC8.

    Parameters
    ----------
    asset_id : str
        Unique identifier for the asset.
    name : str
        Human-readable name of the asset.
    description : str
        Human-readable description of the asset.
    origin : DataAssetOrigin
        Where the asset comes from.
    access_mode : DataAssetAccessMode
        How ReformLab obtains the asset.
    trust_status : DataAssetTrustStatus
        What can be claimed about the asset.
    table : pa.Table
        PyArrow table containing the entity data.
    entity_type : str
        Type of entity (e.g., ``"household"``, ``"person"``).
    record_count : int
        Number of records in the table.
    relationships : tuple[str, ...]
        Entity-to-entity relationship links.
    primary_key : str
        Primary key column name.
    source_url : str
        Direct URL to the asset source.
    license : str
        License identifier.
    version : str
        Version or vintage identifier.
    geographic_coverage : tuple[str, ...]
        Geographic coverage.
    years : tuple[int, ...]
        Years covered by this asset.
    intended_use : str
        Description of intended use cases.
    redistribution_allowed : bool
        Whether redistribution is permitted.
    redistribution_notes : str
        Notes on redistribution restrictions.
    update_cadence : str
        How often the asset is updated.
    quality_notes : str
        Known quality issues or limitations.
    references : tuple[str, ...]
        URLs to documentation or source materials.

    Returns
    -------
    StructuralAsset
        Immutable asset instance with validated descriptor.

    Raises
    ------
    EvidenceAssetError
        If descriptor construction or asset-specific validation fails.
    """
    descriptor = DataAssetDescriptor(
        asset_id=asset_id,
        name=name,
        description=description,
        data_class="structural",  # Enforced by factory
        origin=origin,
        access_mode=access_mode,
        trust_status=trust_status,
        source_url=source_url,
        license=license,
        version=version,
        geographic_coverage=geographic_coverage,
        years=years,
        intended_use=intended_use,
        redistribution_allowed=redistribution_allowed,
        redistribution_notes=redistribution_notes,
        update_cadence=update_cadence,
        quality_notes=quality_notes,
        references=references,
    )
    return StructuralAsset(
        descriptor=descriptor,
        table=table,
        entity_type=entity_type,
        record_count=record_count,
        relationships=relationships,
        primary_key=primary_key,
    )


def create_exogenous_asset(
    # Descriptor fields (using display_name to avoid conflict with asset name field)
    asset_id: str,
    display_name: str,
    description: str,
    origin: DataAssetOrigin,
    access_mode: DataAssetAccessMode,
    trust_status: DataAssetTrustStatus,
    # Exogenous-specific fields
    series_name: str,
    values: dict[int, float],
    unit: str,
    frequency: str = "annual",
    source: str = "",
    vintage: str = "",
    interpolation_method: str = "linear",
    aggregation_method: str = "mean",
    revision_policy: str = "",
    # Optional descriptor fields
    source_url: str = "",
    license: str = "",
    version: str = "",
    geographic_coverage: tuple[str, ...] = (),
    years: tuple[int, ...] = (),
    intended_use: str = "",
    redistribution_allowed: bool = False,
    redistribution_notes: str = "",
    update_cadence: str = "",
    quality_notes: str = "",
    references: tuple[str, ...] = (),
) -> ExogenousAsset:
    """Factory function for creating ExogenousAsset with validated descriptor.

    Constructs a ``DataAssetDescriptor`` with ``data_class="exogenous"`` and
    wraps it in an ``ExogenousAsset``. The ``display_name`` parameter maps to
    ``descriptor.name`` (display name), while ``series_name`` maps to the
    asset's ``name`` field (series identifier for lookup).

    Story 21.3 / AC8.

    Parameters
    ----------
    asset_id : str
        Unique identifier for the asset.
    display_name : str
        Human-readable display name (maps to ``descriptor.name``).
    description : str
        Human-readable description of the asset.
    origin : DataAssetOrigin
        Where the asset comes from.
    access_mode : DataAssetAccessMode
        How ReformLab obtains the asset.
    trust_status : DataAssetTrustStatus
        What can be claimed about the asset.
    series_name : str
        Series identifier for lookup (maps to asset ``name`` field).
    values : dict[int, float]
        Year-indexed values.
    unit : str
        Physical unit.
    frequency : str
        Source frequency.
    source : str
        Institutional provenance.
    vintage : str
        Publication vintage.
    interpolation_method : str
        Interpolation strategy.
    aggregation_method : str
        How source values are aggregated.
    revision_policy : str
        How revisions are tracked.
    source_url : str
        Direct URL to the asset source.
    license : str
        License identifier.
    version : str
        Version or vintage identifier.
    geographic_coverage : tuple[str, ...]
        Geographic coverage.
    years : tuple[int, ...]
        Years covered by this asset.
    intended_use : str
        Description of intended use cases.
    redistribution_allowed : bool
        Whether redistribution is permitted.
    redistribution_notes : str
        Notes on redistribution restrictions.
    update_cadence : str
        How often the asset is updated.
    quality_notes : str
        Known quality issues or limitations.
    references : tuple[str, ...]
        URLs to documentation or source materials.

    Returns
    -------
    ExogenousAsset
        Immutable asset instance with validated descriptor.

    Raises
    ------
    EvidenceAssetError
        If descriptor construction or asset-specific validation fails.
    """
    descriptor = DataAssetDescriptor(
        asset_id=asset_id,
        name=display_name,  # display_name -> descriptor.name
        description=description,
        data_class="exogenous",  # Enforced by factory
        origin=origin,
        access_mode=access_mode,
        trust_status=trust_status,
        source_url=source_url,
        license=license,
        version=version,
        geographic_coverage=geographic_coverage,
        years=years,
        intended_use=intended_use,
        redistribution_allowed=redistribution_allowed,
        redistribution_notes=redistribution_notes,
        update_cadence=update_cadence,
        quality_notes=quality_notes,
        references=references,
    )
    return ExogenousAsset(
        descriptor=descriptor,
        name=series_name,  # series_name -> asset.name
        values=values,
        unit=unit,
        frequency=frequency,
        source=source,
        vintage=vintage,
        interpolation_method=interpolation_method,
        aggregation_method=aggregation_method,
        revision_policy=revision_policy,
    )


def create_calibration_asset(
    # Descriptor fields
    asset_id: str,
    name: str,
    description: str,
    origin: DataAssetOrigin,
    access_mode: DataAssetAccessMode,
    trust_status: DataAssetTrustStatus,
    # Calibration-specific fields
    target_type: CalibrationTargetType,
    coverage: str,
    source_material: tuple[str, ...] = (),
    margin_of_error: float | None = None,
    confidence_level: float | None = None,
    methodology_notes: str = "",
    # Story 21.5 / Task 1: Train/test separation fields
    is_in_sample: bool = True,
    holdout_group: HoldoutGroup | None = None,
    calibration_method: CalibrationMethod = "maximum_likelihood",
    target_years: tuple[int, ...] = (),
    # Optional descriptor fields
    source_url: str = "",
    license: str = "",
    version: str = "",
    geographic_coverage: tuple[str, ...] = (),
    years: tuple[int, ...] = (),
    intended_use: str = "",
    redistribution_allowed: bool = False,
    redistribution_notes: str = "",
    update_cadence: str = "",
    quality_notes: str = "",
    references: tuple[str, ...] = (),
) -> CalibrationAsset:
    """Factory function for creating CalibrationAsset with validated descriptor.

    Constructs a ``DataAssetDescriptor`` with ``data_class="calibration"`` and
    wraps it in a ``CalibrationAsset``.

    Story 21.3 / AC8, Story 21.5 / Task 1.

    Parameters
    ----------
    asset_id : str
        Unique identifier for the asset.
    name : str
        Human-readable name of the asset.
    description : str
        Human-readable description of the asset.
    origin : DataAssetOrigin
        Where the asset comes from.
    access_mode : DataAssetAccessMode
        How ReformLab obtains the asset.
    trust_status : DataAssetTrustStatus
        What can be claimed about the asset.
    target_type : CalibrationTargetType
        Type of calibration target.
    coverage : str
        Geographic or demographic coverage.
    source_material : tuple[str, ...]
        Literature citations or source references.
    margin_of_error : float | None
        Acceptable margin of error.
    confidence_level : float | None
        Statistical confidence level.
    methodology_notes : str
        Free-text notes on calibration methodology.
    is_in_sample : bool
        Whether this calibration data is in-sample. Story 21.5 / Task 1.
    holdout_group : HoldoutGroup | None
        Holdout group designation. Story 21.5 / Task 1.
    calibration_method : CalibrationMethod
        Statistical method for calibration. Story 21.5 / Task 1.
    target_years : tuple[int, ...]
        Years covered by calibration target. Story 21.5 / Task 1.
    source_url : str
        Direct URL to the asset source.
    license : str
        License identifier.
    version : str
        Version or vintage identifier.
    geographic_coverage : tuple[str, ...]
        Geographic coverage.
    years : tuple[int, ...]
        Years covered by this asset.
    intended_use : str
        Description of intended use cases.
    redistribution_allowed : bool
        Whether redistribution is permitted.
    redistribution_notes : str
        Notes on redistribution restrictions.
    update_cadence : str
        How often the asset is updated.
    quality_notes : str
        Known quality issues or limitations.
    references : tuple[str, ...]
        URLs to documentation or source materials.

    Returns
    -------
    CalibrationAsset
        Immutable asset instance with validated descriptor.

    Raises
    ------
    EvidenceAssetError
        If descriptor construction or asset-specific validation fails.
    """
    descriptor = DataAssetDescriptor(
        asset_id=asset_id,
        name=name,
        description=description,
        data_class="calibration",  # Enforced by factory
        origin=origin,
        access_mode=access_mode,
        trust_status=trust_status,
        source_url=source_url,
        license=license,
        version=version,
        geographic_coverage=geographic_coverage,
        years=years,
        intended_use=intended_use,
        redistribution_allowed=redistribution_allowed,
        redistribution_notes=redistribution_notes,
        update_cadence=update_cadence,
        quality_notes=quality_notes,
        references=references,
    )
    return CalibrationAsset(
        descriptor=descriptor,
        target_type=target_type,
        coverage=coverage,
        source_material=source_material,
        margin_of_error=margin_of_error,
        confidence_level=confidence_level,
        methodology_notes=methodology_notes,
        # Story 21.5 / Task 1: New train/test separation fields
        is_in_sample=is_in_sample,
        holdout_group=holdout_group,
        calibration_method=calibration_method,
        target_years=target_years,
    )


def create_validation_asset(
    # Descriptor fields
    asset_id: str,
    name: str,
    description: str,
    origin: DataAssetOrigin,
    access_mode: DataAssetAccessMode,
    trust_status: DataAssetTrustStatus,
    # Validation-specific fields
    validation_type: ValidationType,
    benchmark_status: ValidationBenchmarkStatus,
    criteria: dict[str, Any],
    last_validated: str = "",
    validation_dossier: str = "",
    trust_status_upgradable: bool = False,
    # Story 21.5 / Task 1: Certification fields
    certified_at: str | None = None,
    certified_by: str | None = None,
    validation_method: ValidationMethod = "holdout",
    holdout_years: tuple[int, ...] = (),
    # Optional descriptor fields
    source_url: str = "",
    license: str = "",
    version: str = "",
    geographic_coverage: tuple[str, ...] = (),
    years: tuple[int, ...] = (),
    intended_use: str = "",
    redistribution_allowed: bool = False,
    redistribution_notes: str = "",
    update_cadence: str = "",
    quality_notes: str = "",
    references: tuple[str, ...] = (),
) -> ValidationAsset:
    """Factory function for creating ValidationAsset with validated descriptor.

    Constructs a ``DataAssetDescriptor`` with ``data_class="validation"`` and
    wraps it in a ``ValidationAsset``.

    Story 21.3 / AC8, Story 21.5 / Task 1.

    Parameters
    ----------
    asset_id : str
        Unique identifier for the asset.
    name : str
        Human-readable name of the asset.
    description : str
        Human-readable description of the asset.
    origin : DataAssetOrigin
        Where the asset comes from.
    access_mode : DataAssetAccessMode
        How ReformLab obtains the asset.
    trust_status : DataAssetTrustStatus
        What can be claimed about the asset.
    validation_type : ValidationType
        Type of validation.
    benchmark_status : ValidationBenchmarkStatus
        Outcome of validation.
    criteria : dict[str, Any]
        Validation criteria.
    last_validated : str
        ISO 8601 timestamp of last validation.
    validation_dossier : str
        URL or path to validation dossier.
    trust_status_upgradable : bool
        Whether the benchmark status can be improved.
    certified_at : str | None
        ISO 8601 timestamp of certification. Story 21.5 / Task 1.
    certified_by : str | None
        Actor identity that certified this benchmark. Story 21.5 / Task 1.
    validation_method : ValidationMethod
        Validation method used. Story 21.5 / Task 1.
    holdout_years : tuple[int, ...]
        Holdout years covered. Story 21.5 / Task 1.
    source_url : str
        Direct URL to the asset source.
    license : str
        License identifier.
    version : str
        Version or vintage identifier.
    geographic_coverage : tuple[str, ...]
        Geographic coverage.
    years : tuple[int, ...]
        Years covered by this asset.
    intended_use : str
        Description of intended use cases.
    redistribution_allowed : bool
        Whether redistribution is permitted.
    redistribution_notes : str
        Notes on redistribution restrictions.
    update_cadence : str
        How often the asset is updated.
    quality_notes : str
        Known quality issues or limitations.
    references : tuple[str, ...]
        URLs to documentation or source materials.

    Returns
    -------
    ValidationAsset
        Immutable asset instance with validated descriptor.

    Raises
    ------
    EvidenceAssetError
        If descriptor construction or asset-specific validation fails.
    """
    descriptor = DataAssetDescriptor(
        asset_id=asset_id,
        name=name,
        description=description,
        data_class="validation",  # Enforced by factory
        origin=origin,
        access_mode=access_mode,
        trust_status=trust_status,
        source_url=source_url,
        license=license,
        version=version,
        geographic_coverage=geographic_coverage,
        years=years,
        intended_use=intended_use,
        redistribution_allowed=redistribution_allowed,
        redistribution_notes=redistribution_notes,
        update_cadence=update_cadence,
        quality_notes=quality_notes,
        references=references,
    )
    return ValidationAsset(
        descriptor=descriptor,
        validation_type=validation_type,
        benchmark_status=benchmark_status,
        criteria=criteria,
        last_validated=last_validated,
        validation_dossier=validation_dossier,
        trust_status_upgradable=trust_status_upgradable,
        # Story 21.5 / Task 1: New certification fields
        certified_at=certified_at,
        certified_by=certified_by,
        validation_method=validation_method,
        holdout_years=holdout_years,
    )


# ============================================================================
# Asset Load Functions — Story 21.5 / Task 1, Task 5
# ============================================================================


_CALIBRATION_ASSETS_BASE_PATH = Path("data/calibration/targets")
_VALIDATION_ASSETS_BASE_PATH = Path("data/validation/benchmarks")


def load_calibration_asset(asset_id: str) -> CalibrationAsset:
    """Load a calibration asset from disk by asset_id.

    Reads the asset folder at ``data/calibration/targets/{asset_id}/`` which
    contains ``descriptor.json``, ``metadata.json``, and optionally ``data.parquet``.

    Story 21.5 / Task 1, Task 5.

    Parameters
    ----------
    asset_id : str
        Unique identifier for the calibration asset.

    Returns
    -------
    CalibrationAsset
        Immutable calibration asset instance loaded from disk.

    Raises
    ------
    EvidenceAssetError
        If the asset folder does not exist, required files are missing,
        or validation fails.
    """
    # Security: Validate asset_id to prevent path traversal attacks
    if "/" in asset_id or "\\" in asset_id or ".." in asset_id:
        raise EvidenceAssetError(
            f"Calibration asset_id contains invalid path characters: {asset_id!r}"
        )

    asset_path = _CALIBRATION_ASSETS_BASE_PATH / asset_id

    # Check asset folder exists
    if not asset_path.exists():
        raise EvidenceAssetError(
            f"Calibration asset folder does not exist: {asset_path}"
        )
    if not asset_path.is_dir():
        raise EvidenceAssetError(
            f"Calibration asset path is not a directory: {asset_path}"
        )

    # Security: Resolve path and verify it's within base path (prevent symlink attacks)
    try:
        resolved_path = asset_path.resolve()
        base_resolved = _CALIBRATION_ASSETS_BASE_PATH.resolve()
        if not str(resolved_path).startswith(str(base_resolved)):
            raise EvidenceAssetError(
                f"Calibration asset path is outside base directory: {asset_path}"
            )
    except OSError as exc:
        raise EvidenceAssetError(
            f"Failed to resolve calibration asset path: {exc}"
        ) from exc

    # Load descriptor.json
    descriptor_path = asset_path / "descriptor.json"
    if not descriptor_path.exists():
        raise EvidenceAssetError(
            f"Calibration asset missing required file: {descriptor_path}"
        )

    try:
        with descriptor_path.open("r") as f:
            descriptor_data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise EvidenceAssetError(
            f"Failed to read calibration asset descriptor.json: {exc}"
        ) from exc

    # Load metadata.json
    metadata_path = asset_path / "metadata.json"
    if not metadata_path.exists():
        raise EvidenceAssetError(
            f"Calibration asset missing required file: {metadata_path}"
        )

    try:
        with metadata_path.open("r") as f:
            metadata = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise EvidenceAssetError(
            f"Failed to read calibration asset metadata.json: {exc}"
        ) from exc

    # Validate metadata.json structure
    if not isinstance(metadata, dict):
        raise EvidenceAssetError(
            f"Calibration asset metadata.json must be an object, got {type(metadata).__name__}"
        )

    # Structure: nested descriptor with metadata fields at top level
    asset_data = {"descriptor": descriptor_data, **metadata}

    # Construct CalibrationAsset via from_json for validation
    try:
        return CalibrationAsset.from_json(asset_data)
    except EvidenceAssetError:
        # Re-raise as-is (already has proper error message)
        raise
    except Exception as exc:
        raise EvidenceAssetError(
            f"Failed to construct CalibrationAsset from JSON: {exc}"
        ) from exc


def load_validation_asset(asset_id: str) -> ValidationAsset:
    """Load a validation asset from disk by asset_id.

    Reads the asset folder at ``data/validation/benchmarks/{asset_id}/`` which
    contains ``descriptor.json``, ``metadata.json``, and optionally ``data.parquet``.

    Story 21.5 / Task 1, Task 5.

    Parameters
    ----------
    asset_id : str
        Unique identifier for the validation asset.

    Returns
    -------
    ValidationAsset
        Immutable validation asset instance loaded from disk.

    Raises
    ------
    EvidenceAssetError
        If the asset folder does not exist, required files are missing,
        or validation fails.
    """
    # Security: Validate asset_id to prevent path traversal attacks
    if "/" in asset_id or "\\" in asset_id or ".." in asset_id:
        raise EvidenceAssetError(
            f"Validation asset_id contains invalid path characters: {asset_id!r}"
        )

    asset_path = _VALIDATION_ASSETS_BASE_PATH / asset_id

    # Check asset folder exists
    if not asset_path.exists():
        raise EvidenceAssetError(
            f"Validation asset folder does not exist: {asset_path}"
        )
    if not asset_path.is_dir():
        raise EvidenceAssetError(
            f"Validation asset path is not a directory: {asset_path}"
        )

    # Security: Resolve path and verify it's within base path (prevent symlink attacks)
    try:
        resolved_path = asset_path.resolve()
        base_resolved = _VALIDATION_ASSETS_BASE_PATH.resolve()
        if not str(resolved_path).startswith(str(base_resolved)):
            raise EvidenceAssetError(
                f"Validation asset path is outside base directory: {asset_path}"
            )
    except OSError as exc:
        raise EvidenceAssetError(
            f"Failed to resolve validation asset path: {exc}"
        ) from exc

    # Load descriptor.json
    descriptor_path = asset_path / "descriptor.json"
    if not descriptor_path.exists():
        raise EvidenceAssetError(
            f"Validation asset missing required file: {descriptor_path}"
        )

    try:
        with descriptor_path.open("r") as f:
            descriptor_data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise EvidenceAssetError(
            f"Failed to read validation asset descriptor.json: {exc}"
        ) from exc

    # Load metadata.json
    metadata_path = asset_path / "metadata.json"
    if not metadata_path.exists():
        raise EvidenceAssetError(
            f"Validation asset missing required file: {metadata_path}"
        )

    try:
        with metadata_path.open("r") as f:
            metadata = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise EvidenceAssetError(
            f"Failed to read validation asset metadata.json: {exc}"
        ) from exc

    # Validate metadata.json structure
    if not isinstance(metadata, dict):
        raise EvidenceAssetError(
            f"Validation asset metadata.json must be an object, got {type(metadata).__name__}"
        )

    # Structure: nested descriptor with metadata fields at top level
    asset_data = {"descriptor": descriptor_data, **metadata}

    # Construct ValidationAsset via from_json for validation
    try:
        return ValidationAsset.from_json(asset_data)
    except EvidenceAssetError:
        # Re-raise as-is (already has proper error message)
        raise
    except Exception as exc:
        raise EvidenceAssetError(
            f"Failed to construct ValidationAsset from JSON: {exc}"
        ) from exc
