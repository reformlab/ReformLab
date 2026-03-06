"""Population validation against known marginal distributions.

Validates synthetic populations produced by PopulationPipeline against
reference marginal distributions from institutional sources (INSEE, Eurostat,
ADEME, SDES). Provides absolute deviation metric per category with
configurable tolerances and governance integration.

Implements Story 11.7, FR42 — "System validates generated populations
against known marginal distributions from source data".

Key features:
- Non-blocking validation by default (informational warnings, not errors)
- Absolute deviation per category: |observed - expected|
- Configurable tolerances per marginal
- Governance integration via ValidationAssumption.to_governance_entry()
- Support for missing/extra categories in population
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Sequence

if TYPE_CHECKING:
    import pyarrow as pa

_logger = logging.getLogger(__name__)


# ====================================================================
# Exception hierarchy
# ====================================================================


class PopulationValidationError(Exception):
    """Base exception for population validation operations."""

    def __init__(self, *, summary: str, reason: str, fix: str) -> None:
        self.summary = summary
        self.reason = reason
        self.fix = fix
        super().__init__(f"{summary} - {reason} - {fix}")


class MarginalConstraintMismatch(PopulationValidationError):
    """Raised when a marginal constraint exceeds tolerance.

    Attributes:
        dimension: The dimension (column name) that failed validation.
        tolerance: The tolerance threshold that was exceeded.
        max_deviation: The maximum absolute deviation observed.
        expected_values: Expected distribution values.
        actual_values: Actual observed values.
    """

    def __init__(
        self,
        *,
        summary: str,
        reason: str,
        fix: str,
        dimension: str,
        tolerance: float,
        max_deviation: float,
        expected_values: dict[str, float],
        actual_values: dict[str, float],
    ) -> None:
        super().__init__(summary=summary, reason=reason, fix=fix)
        self.dimension = dimension
        self.tolerance = tolerance
        self.max_deviation = max_deviation
        self.expected_values = expected_values
        self.actual_values = actual_values


# ====================================================================
# Constraint and result types
# ====================================================================


@dataclass(frozen=True)
class MarginalConstraint:
    """A reference marginal distribution for validation.

    Specifies the expected distribution of a categorical variable
    in the population. Used to validate synthetic populations
    against institutional benchmarks.

    Attributes:
        dimension: Column name in the population table.
        distribution: Mapping from category value to expected proportion (sums to 1.0).
        tolerance: Maximum acceptable absolute deviation per category.
    """

    dimension: str
    distribution: dict[str, float]
    tolerance: float

    def __post_init__(self) -> None:
        # Validate dimension is non-empty string
        if not self.dimension or self.dimension.strip() == "":
            msg = "dimension must be a non-empty string"
            raise ValueError(msg)
        # Validate distribution is non-empty
        if not self.distribution:
            msg = "distribution must be a non-empty dict"
            raise ValueError(msg)
        # Validate all proportions are >= 0
        for cat, prop in self.distribution.items():
            if prop < 0:
                msg = f"distribution proportion for {cat!r} must be >= 0, got {prop}"
                raise ValueError(msg)
        # Validate proportions sum to 1.0 (within floating point tolerance)
        total = sum(self.distribution.values())
        if not math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9):
            msg = f"distribution proportions must sum to 1.0, got {total}"
            raise ValueError(msg)
        # Validate tolerance is positive
        if self.tolerance < 0:
            msg = f"tolerance must be >= 0, got {self.tolerance}"
            raise ValueError(msg)
        # Shallow copy — safe because values are floats (immutable)
        object.__setattr__(self, "distribution", dict(self.distribution))


@dataclass(frozen=True)
class MarginalResult:
    """Result of validating a single marginal constraint.

    Records of observed distribution in the population,
    deviation from expected, and whether validation passed.

    Attributes:
        constraint: The marginal constraint being validated.
        observed: Observed proportions in the population.
        deviations: Absolute deviation per category (observed - expected).
        max_deviation: Maximum absolute deviation across all categories.
        passed: Whether constraint passed (max_deviation <= tolerance).
    """

    constraint: MarginalConstraint
    observed: dict[str, float]
    deviations: dict[str, float]
    max_deviation: float
    passed: bool

    def __post_init__(self) -> None:
        # Validate all expected category keys are present in observed
        constraint_keys = set(self.constraint.distribution.keys())
        observed_keys = set(self.observed.keys())
        missing_expected = constraint_keys - observed_keys

        if missing_expected:
            msg = f"observed missing expected keys: {missing_expected}"
            raise ValueError(msg)

        # Validate deviations keys match constraint keys (only expected categories)
        deviations_keys = set(self.deviations.keys())

        if deviations_keys != constraint_keys:
            msg = f"deviations keys {deviations_keys} do not match constraint keys {constraint_keys}"
            raise ValueError(msg)

        # Validate passed is boolean
        if not isinstance(self.passed, bool):
            msg = f"passed must be bool, got {type(self.passed).__name__}"
            raise ValueError(msg)

        # Validate max_deviation >= 0
        if self.max_deviation < 0:
            msg = f"max_deviation must be >= 0, got {self.max_deviation}"
            raise ValueError(msg)


@dataclass(frozen=True)
class ValidationResult:
    """Overall result of population validation against marginals.

    Aggregates results from all marginal constraints and provides
    governance-integrated assumption recording.

    Attributes:
        all_passed: Whether all constraints passed within tolerance.
        marginal_results: Ordered results for each constraint.
        total_constraints: Number of constraints validated.
        failed_count: Number of constraints that failed.
    """

    all_passed: bool
    marginal_results: tuple[MarginalResult, ...]
    total_constraints: int
    failed_count: int

    def __post_init__(self) -> None:
        # Validate marginal_results is tuple
        if not isinstance(self.marginal_results, tuple):
            msg = f"marginal_results must be tuple, got {type(self.marginal_results).__name__}"
            raise ValueError(msg)
        # Validate total_constraints equals len(marginal_results)
        if self.total_constraints != len(self.marginal_results):
            msg = (
                f"total_constraints {self.total_constraints} != "
                f"len(marginal_results) {len(self.marginal_results)}"
            )
            raise ValueError(msg)
        # Validate failed_count matches actual failures
        actual_failed = sum(1 for r in self.marginal_results if not r.passed)
        if self.failed_count != actual_failed:
            msg = f"failed_count {self.failed_count} != actual failures {actual_failed}"
            raise ValueError(msg)

    def to_assumption(self) -> ValidationAssumption:
        """Convert validation result to governance-compatible assumption.

        Builds a ValidationAssumption with per-constraint details
        including dimension, tolerance, max_deviation, passed status, and
        expected vs. observed proportions.

        Returns:
            ValidationAssumption with all validation details.
        """
        marginal_details: dict[str, dict[str, Any]] = {}
        for result in self.marginal_results:
            marginal_details[result.constraint.dimension] = {
                "tolerance": result.constraint.tolerance,
                "max_deviation": result.max_deviation,
                "passed": result.passed,
                "expected": result.constraint.distribution,
                "observed": result.observed,
                "deviations": result.deviations,
            }

        return ValidationAssumption(
            all_passed=self.all_passed,
            total_constraints=self.total_constraints,
            failed_count=self.failed_count,
            marginal_details=marginal_details,
        )


# ====================================================================
# Governance integration
# ====================================================================


@dataclass(frozen=True)
class ValidationAssumption:
    """Structured assumption record from population validation.

    Records validation status and per-marginal results for
    governance integration. Can be converted to governance-compatible
    AssumptionEntry format via to_governance_entry().

    Attributes:
        all_passed: Whether all constraints passed within tolerance.
        total_constraints: Number of constraints validated.
        failed_count: Number of constraints that failed.
        marginal_details: Per-constraint details with deviations.
    """

    all_passed: bool
    total_constraints: int
    failed_count: int
    marginal_details: dict[str, dict[str, Any]]

    def __post_init__(self) -> None:
        # Coerce to dict for immutability
        # Deep-copy is unnecessary since all contents are primitives/floats
        object.__setattr__(self, "marginal_details", dict(self.marginal_details))

    def to_governance_entry(self, *, source_label: str = "population_validation") -> dict[str, Any]:
        """Convert to governance-compatible AssumptionEntry format.

        Returns a dict with keys: key, value, source, is_default.
        The value dict includes all validation details.

        Args:
            source_label: Label for the source field.
                Defaults to "population_validation".

        Returns:
            Dict matching governance.manifest.AssumptionEntry structure.
        """
        return {
            "key": "population_validation",
            "value": {
                "all_passed": self.all_passed,
                "total_constraints": self.total_constraints,
                "failed_count": self.failed_count,
                "marginal_details": self.marginal_details,
            },
            "source": source_label,
            "is_default": False,
        }


# ====================================================================
# PopulationValidator class
# ====================================================================


class PopulationValidator:
    """Validates synthetic populations against known marginal distributions.

    Supports multiple distance metrics and configurable tolerances.
    Results integrate with governance layer via assumption recording.

    Example:
        >>> validator = PopulationValidator(
        ...     constraints=[
        ...         MarginalConstraint(
        ...             dimension="income_decile",
        ...             distribution={"1": 0.08, "2": 0.12, "3": 0.15, ...},
        ...             tolerance=0.02,
        ...         ),
        ...         MarginalConstraint(
        ...             dimension="vehicle_type",
        ...             distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
        ...             tolerance=0.03,
        ...         ),
        ...     ],
        ... )
        >>> result = validator.validate(population_table)
        >>> result.all_passed  # True if all within tolerance
    """

    def __init__(self, constraints: Sequence[MarginalConstraint]) -> None:
        if not constraints:
            msg = "constraints must be a non-empty sequence"
            raise ValueError(msg)
        self._constraints = tuple(constraints)

    def validate(self, population: pa.Table) -> ValidationResult:
        """Validate population against all registered marginal constraints.

        Computes observed proportions for each dimension, calculates absolute
        deviations from expected distributions, and checks whether each
        constraint passes within tolerance.

        Does NOT raise exceptions when constraints fail — validation is
        informational. Check `ValidationResult.all_passed` or individual
        `MarginalResult.passed` flags. For strict validation, callers can
        raise `MarginalConstraintMismatch` if needed.

        Args:
            population: PyArrow table containing the population to validate.

        Returns:
            ValidationResult with per-constraint results and summary.

        Raises:
            KeyError: If a dimension column does not exist in the population.
        """
        _logger.info(
            "event=population_validation_start constraints=%d rows=%d",
            len(self._constraints),
            len(population),
        )

        marginal_results: list[MarginalResult] = []
        for constraint in self._constraints:
            # Extract dimension column from population
            column_data = population.column(constraint.dimension).to_pylist()

            # Count rows per category
            counts: dict[str, int] = {}
            for category in constraint.distribution.keys():
                counts[category] = column_data.count(category)

            # Count extra categories (not in expected distribution)
            all_categories = set(column_data)
            extra_categories = all_categories - set(constraint.distribution.keys())
            for category in extra_categories:
                counts[category] = column_data.count(category)

            total_rows = len(column_data)

            # Compute observed proportions
            observed: dict[str, float] = {}
            for category, count in counts.items():
                observed[category] = count / total_rows if total_rows > 0 else 0.0

            # Compute absolute deviations per category
            deviations: dict[str, float] = {}
            for category in constraint.distribution.keys():
                observed_val = observed.get(category, 0.0)
                expected_val = constraint.distribution[category]
                deviations[category] = observed_val - expected_val

            # Determine max deviation (absolute value)
            max_deviation = max(abs(d) for d in deviations.values())

            # Check if passed
            passed = max_deviation <= constraint.tolerance

            # Build MarginalResult
            marginal_result = MarginalResult(
                constraint=constraint,
                observed={cat: observed.get(cat, 0.0) for cat in constraint.distribution.keys()},
                deviations=deviations,
                max_deviation=max_deviation,
                passed=passed,
            )
            marginal_results.append(marginal_result)

        # Determine overall result
        failed_count = sum(1 for r in marginal_results if not r.passed)
        all_passed = failed_count == 0

        result = ValidationResult(
            all_passed=all_passed,
            marginal_results=tuple(marginal_results),
            total_constraints=len(marginal_results),
            failed_count=failed_count,
        )

        _logger.info(
            "event=population_validation_complete all_passed=%s failed_count=%d/%d",
            result.all_passed,
            result.failed_count,
            result.total_constraints,
        )

        return result
