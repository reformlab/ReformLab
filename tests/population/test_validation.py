# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for population validation against known marginals.

Implements Story 11.7, FR42 — validate synthetic populations
against reference marginal distributions from institutional sources.
"""

from __future__ import annotations

import dataclasses
import math

import pyarrow as pa
import pytest

from reformlab.population.validation import (
    MarginalConstraint,
    MarginalConstraintMismatch,
    MarginalResult,
    PopulationValidationError,
    PopulationValidator,
    ValidationAssumption,
    ValidationResult,
)

# ====================================================================
# Test error hierarchy
# ====================================================================


class TestPopulationValidationErrorHierarchy:
    """Test PopulationValidationError exception hierarchy."""

    def test_population_validation_error_base_exception(self) -> None:
        """PopulationValidationError inherits Exception, summary-reason-fix pattern."""
        exc = PopulationValidationError(
            summary="Test summary",
            reason="Test reason",
            fix="Test fix",
        )
        assert isinstance(exc, Exception)
        assert exc.summary == "Test summary"
        assert exc.reason == "Test reason"
        assert exc.fix == "Test fix"
        assert "Test summary" in str(exc)
        assert "Test reason" in str(exc)
        assert "Test fix" in str(exc)

    def test_marginal_constraint_mismatch_inherits(self) -> None:
        """MarginalConstraintMismatch inherits PopulationValidationError, has additional attributes."""
        exc = MarginalConstraintMismatch(
            summary="Constraint failed",
            reason="Deviation exceeded tolerance",
            fix="Adjust population or tolerance",
            dimension="income_decile",
            tolerance=0.02,
            max_deviation=0.05,
            expected_values={"1": 0.08, "2": 0.12},
            actual_values={"1": 0.13, "2": 0.07},
        )
        assert isinstance(exc, PopulationValidationError)
        assert exc.dimension == "income_decile"
        assert exc.tolerance == 0.02
        assert exc.max_deviation == 0.05
        assert exc.expected_values == {"1": 0.08, "2": 0.12}
        assert exc.actual_values == {"1": 0.13, "2": 0.07}


# ====================================================================
# Test MarginalConstraint dataclass
# ====================================================================


class TestMarginalConstraint:
    """Test MarginalConstraint frozen dataclass."""

    def test_frozen_dataclass(self) -> None:
        """Frozen dataclass."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            constraint.distribution = {}  # type: ignore[misc]

    def test_holds_attributes(self) -> None:
        """Holds dimension, distribution, tolerance."""
        constraint = MarginalConstraint(
            dimension="income_decile",
            distribution={
                "1": 0.08,
                "2": 0.12,
                "3": 0.15,
                "4": 0.15,
                "5": 0.15,
                "6": 0.15,
                "7": 0.05,
                "8": 0.05,
                "9": 0.05,
                "10": 0.05,
            },
            tolerance=0.02,
        )
        assert constraint.dimension == "income_decile"
        assert constraint.distribution == {
            "1": 0.08,
            "2": 0.12,
            "3": 0.15,
            "4": 0.15,
            "5": 0.15,
            "6": 0.15,
            "7": 0.05,
            "8": 0.05,
            "9": 0.05,
            "10": 0.05,
        }
        assert constraint.tolerance == 0.02

    def test_empty_dimension_raises_value_error(self) -> None:
        """Empty dimension raises ValueError."""
        with pytest.raises(ValueError, match="dimension must be a non-empty string"):
            MarginalConstraint(
                dimension="",
                distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
                tolerance=0.03,
            )

    def test_whitespace_dimension_raises_value_error(self) -> None:
        """Whitespace-only dimension raises ValueError."""
        with pytest.raises(ValueError, match="dimension must be a non-empty string"):
            MarginalConstraint(
                dimension="   ",
                distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
                tolerance=0.03,
            )

    def test_empty_distribution_raises_value_error(self) -> None:
        """Empty distribution raises ValueError."""
        with pytest.raises(ValueError, match="distribution must be a non-empty dict"):
            MarginalConstraint(
                dimension="vehicle_type",
                distribution={},
                tolerance=0.03,
            )

    def test_negative_proportion_raises_value_error(self) -> None:
        """Negative proportion in distribution raises ValueError."""
        with pytest.raises(ValueError, match="distribution proportion for .* must be >= 0"):
            MarginalConstraint(
                dimension="vehicle_type",
                distribution={"car": 0.65, "suv": 0.20, "bike": -0.15},
                tolerance=0.03,
            )

    def test_proportions_not_summing_to_one_raise_value_error(self) -> None:
        """Proportions not summing to 1.0 raise ValueError."""
        with pytest.raises(ValueError, match="distribution proportions must sum to 1.0"):
            MarginalConstraint(
                dimension="vehicle_type",
                distribution={"car": 0.70, "suv": 0.20, "bike": 0.15},
                tolerance=0.03,
            )

    def test_tolerance_negative_raises_value_error(self) -> None:
        """Negative tolerance raises ValueError."""
        with pytest.raises(ValueError, match="tolerance must be >= 0"):
            MarginalConstraint(
                dimension="vehicle_type",
                distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
                tolerance=-0.01,
            )

    def test_zero_tolerance_is_valid(self) -> None:
        """Zero tolerance is valid (exact match required)."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.0,
        )
        assert constraint.tolerance == 0.0

    def test_distribution_coerced_to_dict_in_post_init(self) -> None:
        """Distribution coerced to dict in __post_init__."""
        original = {"car": 0.65, "suv": 0.20, "bike": 0.15}
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution=original,
            tolerance=0.03,
        )
        assert constraint.distribution is not original
        assert constraint.distribution == original


# ====================================================================
# Test MarginalResult dataclass
# ====================================================================


class TestMarginalResult:
    """Test MarginalResult frozen dataclass."""

    def test_frozen_dataclass(self) -> None:
        """Frozen dataclass."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        result = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.observed = {}  # type: ignore[misc]

    def test_holds_attributes(self) -> None:
        """Holds constraint, observed, deviations, max_deviation, passed."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        result = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        assert result.constraint is constraint
        assert result.observed == {"car": 0.67, "suv": 0.18, "bike": 0.15}
        assert result.deviations == {"car": 0.02, "suv": -0.02, "bike": 0.0}
        assert result.max_deviation == 0.02
        assert result.passed is True

    def test_all_category_keys_match(self) -> None:
        """All category keys match between constraint.distribution, observed, and deviations."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        result = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        # Keys should match
        assert set(constraint.distribution.keys()) == set(result.observed.keys())
        assert set(constraint.distribution.keys()) == set(result.deviations.keys())

    def test_max_deviation_equals_maximum_value_in_deviations_dict(self) -> None:
        """max_deviation equals maximum value in deviations dict."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        deviations = {"car": 0.02, "suv": -0.02, "bike": 0.01}
        result = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.16},
            deviations=deviations,
            max_deviation=0.02,
            passed=True,
        )
        assert result.max_deviation == max(abs(v) for v in deviations.values())

    def test_passed_is_boolean(self) -> None:
        """passed is boolean."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        result_true = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        result_false = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.05,
            passed=False,
        )
        assert isinstance(result_true.passed, bool)
        assert isinstance(result_false.passed, bool)

    def test_max_deviation_ge_zero(self) -> None:
        """max_deviation >= 0."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        result = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        assert result.max_deviation >= 0.0


# ====================================================================
# Test ValidationResult dataclass
# ====================================================================


class TestValidationResult:
    """Test ValidationResult frozen dataclass."""

    def test_frozen_dataclass(self) -> None:
        """Frozen dataclass."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        marginal_result = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        result = ValidationResult(
            all_passed=True,
            marginal_results=(marginal_result,),
            total_constraints=1,
            failed_count=0,
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.all_passed = False  # type: ignore[misc]

    def test_holds_attributes(self) -> None:
        """Holds all_passed, marginal_results, total_constraints, failed_count."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        marginal_result = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        result = ValidationResult(
            all_passed=True,
            marginal_results=(marginal_result,),
            total_constraints=1,
            failed_count=0,
        )
        assert result.all_passed is True
        assert result.marginal_results == (marginal_result,)
        assert result.total_constraints == 1
        assert result.failed_count == 0

    def test_marginal_results_is_tuple(self) -> None:
        """marginal_results is tuple."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        marginal_result = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        result = ValidationResult(
            all_passed=True,
            marginal_results=(marginal_result,),
            total_constraints=1,
            failed_count=0,
        )
        assert isinstance(result.marginal_results, tuple)

    def test_total_constraints_equals_len_marginal_results(self) -> None:
        """total_constraints equals len(marginal_results)."""
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        marginal_result = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        result = ValidationResult(
            all_passed=True,
            marginal_results=(marginal_result,),
            total_constraints=1,
            failed_count=0,
        )
        assert result.total_constraints == len(result.marginal_results)

    def test_failed_count_matches_count_of_failed_results(self) -> None:
        """failed_count matches count of failed results."""
        constraint1 = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        constraint2 = MarginalConstraint(
            dimension="income_decile",
            distribution={
                "1": 0.1,
                "2": 0.1,
                "3": 0.1,
                "4": 0.1,
                "5": 0.1,
                "6": 0.1,
                "7": 0.1,
                "8": 0.1,
                "9": 0.1,
                "10": 0.1,
            },
            tolerance=0.02,
        )
        marginal_result1 = MarginalResult(
            constraint=constraint1,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        marginal_result2 = MarginalResult(
            constraint=constraint2,
            observed={
                "1": 0.15,
                "2": 0.05,
                "3": 0.1,
                "4": 0.1,
                "5": 0.1,
                "6": 0.1,
                "7": 0.1,
                "8": 0.1,
                "9": 0.05,
                "10": 0.05,
            },
            deviations={
                "1": 0.05,
                "2": -0.05,
                "3": 0.0,
                "4": 0.0,
                "5": 0.0,
                "6": 0.0,
                "7": 0.0,
                "8": 0.0,
                "9": -0.05,
                "10": -0.05,
            },
            max_deviation=0.05,
            passed=False,
        )
        result = ValidationResult(
            all_passed=False,
            marginal_results=(marginal_result1, marginal_result2),
            total_constraints=2,
            failed_count=1,
        )
        assert result.failed_count == sum(1 for r in result.marginal_results if not r.passed)


# ====================================================================
# Test PopulationValidator construction
# ====================================================================


class TestPopulationValidatorConstruction:
    """Test PopulationValidator constructor."""

    def test_constructor_accepts_constraints_sequence(self) -> None:
        """Constructor accepts constraints sequence."""
        constraints = [
            MarginalConstraint(
                dimension="income_decile",
                distribution={
                    "1": 0.1,
                    "2": 0.1,
                    "3": 0.1,
                    "4": 0.1,
                    "5": 0.1,
                    "6": 0.1,
                    "7": 0.1,
                    "8": 0.1,
                    "9": 0.1,
                    "10": 0.1,
                },
                tolerance=0.02,
            ),
            MarginalConstraint(
                dimension="vehicle_type",
                distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
                tolerance=0.03,
            ),
        ]
        validator = PopulationValidator(constraints=constraints)
        assert validator is not None

    def test_empty_constraints_list_raises_value_error(self) -> None:
        """Empty constraints list raises ValueError."""
        with pytest.raises(ValueError, match="constraints must be a non-empty sequence"):
            PopulationValidator(constraints=[])

    def test_constraints_stored_as_tuple(self) -> None:
        """Constraints stored as tuple."""
        constraints = [
            MarginalConstraint(
                dimension="income_decile",
                distribution={
                    "1": 0.1,
                    "2": 0.1,
                    "3": 0.1,
                    "4": 0.1,
                    "5": 0.1,
                    "6": 0.1,
                    "7": 0.1,
                    "8": 0.1,
                    "9": 0.1,
                    "10": 0.1,
                },
                tolerance=0.02,
            ),
        ]
        validator = PopulationValidator(constraints=constraints)
        assert isinstance(validator._constraints, tuple)


# ====================================================================
# Test PopulationValidator.validate() single constraint
# ====================================================================


class TestPopulationValidatorValidateSingleConstraint:
    """Test PopulationValidator.validate() with single constraint."""

    def test_single_constraint_perfect_match(self) -> None:
        """Single constraint with perfect match → MarginalResult.passed is True, max_deviation == 0.0."""
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "suv", "bike"], type=pa.utf8()),
            }
        )
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.6, "suv": 0.2, "bike": 0.2},
            tolerance=0.01,
        )
        validator = PopulationValidator(constraints=[constraint])
        result = validator.validate(population)

        assert result.total_constraints == 1
        assert result.failed_count == 0
        assert result.all_passed is True
        assert len(result.marginal_results) == 1

        marginal_result = result.marginal_results[0]
        assert marginal_result.passed is True
        assert marginal_result.max_deviation == 0.0

    def test_single_constraint_within_tolerance(self) -> None:
        """Single constraint within tolerance → passed is True."""
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "suv", "bike"], type=pa.utf8()),
            }
        )
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.6, "suv": 0.2, "bike": 0.2},
            tolerance=0.03,
        )
        validator = PopulationValidator(constraints=[constraint])
        result = validator.validate(population)

        assert result.total_constraints == 1
        assert result.failed_count == 0
        assert result.all_passed is True

        marginal_result = result.marginal_results[0]
        assert marginal_result.passed is True

    def test_single_constraint_exceeding_tolerance(self) -> None:
        """Single constraint exceeding tolerance → passed is False, max_deviation > tolerance."""
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "car", "suv", "bike"], type=pa.utf8()),
            }
        )
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.6, "suv": 0.2, "bike": 0.2},
            tolerance=0.05,
        )
        validator = PopulationValidator(constraints=[constraint])
        result = validator.validate(population)

        assert result.total_constraints == 1
        assert result.failed_count == 1
        assert result.all_passed is False

        marginal_result = result.marginal_results[0]
        assert marginal_result.passed is False
        assert marginal_result.max_deviation > constraint.tolerance

    def test_observed_proportions_sum_to_one(self) -> None:
        """observed proportions sum to 1.0."""
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "suv", "bike"], type=pa.utf8()),
            }
        )
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.6, "suv": 0.2, "bike": 0.2},
            tolerance=0.01,
        )
        validator = PopulationValidator(constraints=[constraint])
        result = validator.validate(population)

        marginal_result = result.marginal_results[0]
        assert math.isclose(sum(marginal_result.observed.values()), 1.0, rel_tol=1e-9)

    def test_deviations_computed_correctly_per_category(self) -> None:
        """deviations computed correctly per category."""
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "car", "suv", "bike"], type=pa.utf8()),
            }
        )
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.6, "suv": 0.2, "bike": 0.2},
            tolerance=0.05,
        )
        validator = PopulationValidator(constraints=[constraint])
        result = validator.validate(population)

        marginal_result = result.marginal_results[0]
        # Observed: car=4/6=0.667, suv=1/6=0.167, bike=1/6=0.167
        # Expected: car=0.6, suv=0.2, bike=0.2
        # Deviations: car=0.067, suv=-0.033, bike=-0.033
        assert math.isclose(marginal_result.deviations["car"], 0.067, abs_tol=0.001)
        assert math.isclose(marginal_result.deviations["suv"], -0.033, abs_tol=0.001)
        assert math.isclose(marginal_result.deviations["bike"], -0.033, abs_tol=0.001)


# ====================================================================
# Test PopulationValidator.validate() multiple constraints
# ====================================================================


class TestPopulationValidatorValidateMultipleConstraints:
    """Test PopulationValidator.validate() with multiple constraints."""

    def test_two_constraints_both_passing(self) -> None:
        """Two constraints, both passing → ValidationResult.all_passed is True, failed_count is 0."""
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "suv", "bike"], type=pa.utf8()),
                "income_decile": pa.array(["1", "2", "3", "4", "5"], type=pa.utf8()),
            }
        )
        constraints = [
            MarginalConstraint(
                dimension="vehicle_type",
                distribution={"car": 0.6, "suv": 0.2, "bike": 0.2},
                tolerance=0.03,
            ),
            MarginalConstraint(
                dimension="income_decile",
                distribution={"1": 0.2, "2": 0.2, "3": 0.2, "4": 0.2, "5": 0.2},
                tolerance=0.05,
            ),
        ]
        validator = PopulationValidator(constraints=constraints)
        result = validator.validate(population)

        assert result.total_constraints == 2
        assert result.failed_count == 0
        assert result.all_passed is True
        assert all(r.passed for r in result.marginal_results)

    def test_two_constraints_one_failing(self) -> None:
        """Two constraints, one failing → all_passed is False, failed_count is 1."""
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "car", "suv", "bike"], type=pa.utf8()),
                "income_decile": pa.array(["1", "2", "3", "4", "5", "6"], type=pa.utf8()),
            }
        )
        constraints = [
            MarginalConstraint(
                dimension="vehicle_type",
                distribution={"car": 0.6, "suv": 0.2, "bike": 0.2},
                tolerance=0.03,
            ),
            MarginalConstraint(
                dimension="income_decile",
                distribution={"1": 0.2, "2": 0.2, "3": 0.2, "4": 0.2, "5": 0.2},
                tolerance=0.05,
            ),
        ]
        validator = PopulationValidator(constraints=constraints)
        result = validator.validate(population)

        assert result.total_constraints == 2
        assert result.failed_count == 1
        assert result.all_passed is False
        assert sum(1 for r in result.marginal_results if r.passed) == 1

    def test_total_constraints_is_two(self) -> None:
        """total_constraints is 2."""
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "suv", "bike"], type=pa.utf8()),
                "income_decile": pa.array(["1", "2", "3", "4", "5"], type=pa.utf8()),
            }
        )
        constraints = [
            MarginalConstraint(
                dimension="vehicle_type",
                distribution={"car": 0.6, "suv": 0.2, "bike": 0.2},
                tolerance=0.03,
            ),
            MarginalConstraint(
                dimension="income_decile",
                distribution={"1": 0.2, "2": 0.2, "3": 0.2, "4": 0.2, "5": 0.2},
                tolerance=0.05,
            ),
        ]
        validator = PopulationValidator(constraints=constraints)
        result = validator.validate(population)

        assert result.total_constraints == 2

    def test_marginal_results_ordered_by_constraint_insertion_order(self) -> None:
        """marginal_results ordered by constraint insertion order."""
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "suv", "bike"], type=pa.utf8()),
                "income_decile": pa.array(["1", "2", "3", "4", "5"], type=pa.utf8()),
            }
        )
        constraints = [
            MarginalConstraint(
                dimension="vehicle_type",
                distribution={"car": 0.6, "suv": 0.2, "bike": 0.2},
                tolerance=0.03,
            ),
            MarginalConstraint(
                dimension="income_decile",
                distribution={"1": 0.2, "2": 0.2, "3": 0.2, "4": 0.2, "5": 0.2},
                tolerance=0.05,
            ),
        ]
        validator = PopulationValidator(constraints=constraints)
        result = validator.validate(population)

        assert result.marginal_results[0].constraint.dimension == "vehicle_type"
        assert result.marginal_results[1].constraint.dimension == "income_decile"


# ====================================================================
# Test PopulationValidator.validate() edge cases
# ====================================================================


class TestPopulationValidatorValidateMissingCategory:
    """Test PopulationValidator.validate() with missing category."""

    def test_population_missing_category_from_expected_distribution(self) -> None:
        """Population missing a category from expected distribution.

        Expected: observed proportion 0.0, deviation equals expected proportion.
        """
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "car"], type=pa.utf8()),
            }
        )
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.8, "suv": 0.1, "bike": 0.1},
            tolerance=0.05,
        )
        validator = PopulationValidator(constraints=[constraint])
        result = validator.validate(population)

        marginal_result = result.marginal_results[0]
        assert marginal_result.observed["suv"] == 0.0
        assert marginal_result.observed["bike"] == 0.0
        assert marginal_result.deviations["suv"] == -0.1
        assert marginal_result.deviations["bike"] == -0.1

    def test_constraint_fails_if_deviation_exceeds_tolerance(self) -> None:
        """Constraint fails if deviation exceeds tolerance."""
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "car"], type=pa.utf8()),
            }
        )
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.8, "suv": 0.1, "bike": 0.1},
            tolerance=0.05,
        )
        validator = PopulationValidator(constraints=[constraint])
        result = validator.validate(population)

        marginal_result = result.marginal_results[0]
        assert marginal_result.passed is False
        assert marginal_result.max_deviation > constraint.tolerance


class TestPopulationValidatorValidateExtraCategory:
    """Test PopulationValidator.validate() with extra category."""

    def test_population_has_category_not_in_expected_distribution(self) -> None:
        """Population has category not in expected distribution.

        Expected: observed proportion for that category, but deviation only
        computed for expected categories.
        """
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "suv", "truck"], type=pa.utf8()),
            }
        )
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.6, "suv": 0.2, "bike": 0.2},
            tolerance=0.05,
        )
        validator = PopulationValidator(constraints=[constraint])
        result = validator.validate(population)

        marginal_result = result.marginal_results[0]
        # Observed: car=3/5=0.6, suv=1/5=0.2, truck=1/5=0.2
        # Expected: car=0.6, suv=0.2, bike=0.2
        # Deviations only for expected categories: car=0.0, suv=0.0, bike=-0.2
        assert "truck" not in marginal_result.deviations
        assert "bike" in marginal_result.deviations
        assert math.isclose(marginal_result.deviations["bike"], -0.2, abs_tol=0.001)

    def test_extra_category_counts_toward_total_rows_for_proportion_calculation(self) -> None:
        """Extra category counts toward total rows for proportion calculation."""
        population = pa.table(
            {
                "vehicle_type": pa.array(["car", "car", "car", "suv", "truck"], type=pa.utf8()),
            }
        )
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.6, "suv": 0.2, "bike": 0.2},
            tolerance=0.05,
        )
        validator = PopulationValidator(constraints=[constraint])
        result = validator.validate(population)

        marginal_result = result.marginal_results[0]
        # Total rows = 5, so proportions are based on 5, not 4
        # observed only includes expected categories (car, suv, bike), not truck
        # car=3/5=0.6, suv=1/5=0.2, bike=0/5=0.0 → sum = 0.8
        assert math.isclose(sum(marginal_result.observed.values()), 0.8, rel_tol=1e-9)
        # car=3/5=0.6, suv=1/5=0.2, bike=0/5=0.0
        assert math.isclose(marginal_result.observed["car"], 0.6, abs_tol=0.001)
        assert math.isclose(marginal_result.observed["suv"], 0.2, abs_tol=0.001)


# ====================================================================
# Test PopulationValidator.validate() with realistic populations
# ====================================================================


class TestPopulationValidatorValidateAgainstRealisticPopulation:
    """Test PopulationValidator.validate() with realistic population fixtures."""

    def test_population_table_valid_with_income_and_vehicle_constraints(
        self,
        population_table_valid: pa.Table,
        constraint_income_decile: MarginalConstraint,
        constraint_vehicle_type: MarginalConstraint,
    ) -> None:
        """Use population_table_valid with constraints.

        Expected: both constraint_income_decile and constraint_vehicle_type
        pass within tolerance.
        """
        validator = PopulationValidator(constraints=[constraint_income_decile, constraint_vehicle_type])
        result = validator.validate(population_table_valid)

        assert result.total_constraints == 2
        assert result.failed_count == 0
        assert result.all_passed is True

    def test_population_table_valid_with_region_constraint(
        self,
        population_table_valid: pa.Table,
        constraint_region_code: MarginalConstraint,
    ) -> None:
        """Use population_table_valid with constraint_region_code → passes within tolerance."""
        validator = PopulationValidator(constraints=[constraint_region_code])
        result = validator.validate(population_table_valid)

        assert result.total_constraints == 1
        assert result.failed_count == 0
        assert result.all_passed is True

    def test_population_table_invalid_income(
        self,
        population_table_invalid_income: pa.Table,
        constraint_income_decile: MarginalConstraint,
    ) -> None:
        """Use population_table_invalid_income.

        Expected: constraint_income_decile fails with max deviation documented.
        """
        validator = PopulationValidator(constraints=[constraint_income_decile])
        result = validator.validate(population_table_invalid_income)

        assert result.total_constraints == 1
        assert result.failed_count == 1
        assert result.all_passed is False

        marginal_result = result.marginal_results[0]
        assert marginal_result.passed is False
        assert marginal_result.max_deviation > constraint_income_decile.tolerance
        # Document max deviation: decile 1 has 3/10=0.3, expected 0.1, deviation 0.2
        assert math.isclose(marginal_result.max_deviation, 0.2, abs_tol=0.01)

    def test_population_table_invalid_vehicle(
        self,
        population_table_invalid_vehicle: pa.Table,
        constraint_vehicle_type: MarginalConstraint,
    ) -> None:
        """Use population_table_invalid_vehicle.

        Expected: constraint_vehicle_type fails with max deviation documented.
        """
        validator = PopulationValidator(constraints=[constraint_vehicle_type])
        result = validator.validate(population_table_invalid_vehicle)

        assert result.total_constraints == 1
        assert result.failed_count == 1
        assert result.all_passed is False

        marginal_result = result.marginal_results[0]
        assert marginal_result.passed is False
        assert marginal_result.max_deviation > constraint_vehicle_type.tolerance
        # Document max deviation: car has 10/10=1.0, expected 0.65, deviation 0.35
        assert math.isclose(marginal_result.max_deviation, 0.35, abs_tol=0.01)


# ====================================================================
# Test ValidationAssumption.to_governance_entry()
# ====================================================================


class TestValidationAssumptionGovernanceEntry:
    """Test ValidationAssumption.to_governance_entry()."""

    def test_to_governance_entry_returns_dict_with_required_keys(self) -> None:
        """Given ValidationAssumption, to_governance_entry() returns dict.

        Expected keys: key, value, source, is_default.
        """
        assumption = ValidationAssumption(
            all_passed=True,
            total_constraints=2,
            failed_count=0,
            marginal_details={
                "income_decile": {
                    "tolerance": 0.02,
                    "max_deviation": 0.01,
                    "passed": True,
                    "expected": {
                        "1": 0.1,
                        "2": 0.1,
                        "3": 0.1,
                        "4": 0.1,
                        "5": 0.1,
                        "6": 0.1,
                        "7": 0.1,
                        "8": 0.1,
                        "9": 0.1,
                        "10": 0.1,
                    },
                    "observed": {
                        "1": 0.1,
                        "2": 0.1,
                        "3": 0.1,
                        "4": 0.1,
                        "5": 0.1,
                        "6": 0.1,
                        "7": 0.1,
                        "8": 0.1,
                        "9": 0.1,
                        "10": 0.1,
                    },
                    "deviations": {
                        "1": 0.0,
                        "2": 0.0,
                        "3": 0.0,
                        "4": 0.0,
                        "5": 0.0,
                        "6": 0.0,
                        "7": 0.0,
                        "8": 0.0,
                        "9": 0.0,
                        "10": 0.0,
                    },
                },
            },
        )
        entry = assumption.to_governance_entry()

        assert isinstance(entry, dict)
        assert "key" in entry
        assert "value" in entry
        assert "source" in entry
        assert "is_default" in entry

    def test_is_default_is_false(self) -> None:
        """is_default is False."""
        assumption = ValidationAssumption(
            all_passed=True,
            total_constraints=1,
            failed_count=0,
            marginal_details={},
        )
        entry = assumption.to_governance_entry()
        assert entry["is_default"] is False

    def test_default_source_is_population_validation(self) -> None:
        """Default source is "population_validation"."""
        assumption = ValidationAssumption(
            all_passed=True,
            total_constraints=1,
            failed_count=0,
            marginal_details={},
        )
        entry = assumption.to_governance_entry()
        assert entry["source"] == "population_validation"

    def test_custom_source_label_is_respected(self) -> None:
        """Custom source_label is respected."""
        assumption = ValidationAssumption(
            all_passed=True,
            total_constraints=1,
            failed_count=0,
            marginal_details={},
        )
        entry = assumption.to_governance_entry(source_label="custom_source")
        assert entry["source"] == "custom_source"

    def test_value_dict_contains_all_required_fields(self) -> None:
        """value dict contains all_passed, total_constraints, failed_count, marginal_details."""
        assumption = ValidationAssumption(
            all_passed=False,
            total_constraints=2,
            failed_count=1,
            marginal_details={
                "income_decile": {
                    "tolerance": 0.02,
                    "max_deviation": 0.05,
                    "passed": False,
                    "expected": {
                        "1": 0.1,
                        "2": 0.1,
                        "3": 0.1,
                        "4": 0.1,
                        "5": 0.1,
                        "6": 0.1,
                        "7": 0.1,
                        "8": 0.1,
                        "9": 0.1,
                        "10": 0.1,
                    },
                    "observed": {
                        "1": 0.15,
                        "2": 0.05,
                        "3": 0.1,
                        "4": 0.1,
                        "5": 0.1,
                        "6": 0.1,
                        "7": 0.1,
                        "8": 0.1,
                        "9": 0.05,
                        "10": 0.05,
                    },
                    "deviations": {
                        "1": 0.05,
                        "2": -0.05,
                        "3": 0.0,
                        "4": 0.0,
                        "5": 0.0,
                        "6": 0.0,
                        "7": 0.0,
                        "8": 0.0,
                        "9": -0.05,
                        "10": -0.05,
                    },
                },
            },
        )
        entry = assumption.to_governance_entry()

        assert "all_passed" in entry["value"]
        assert "total_constraints" in entry["value"]
        assert "failed_count" in entry["value"]
        assert "marginal_details" in entry["value"]

    def test_marginal_details_contains_per_constraint_details(self) -> None:
        """marginal_details contains per-constraint entries.

        Expected fields: tolerance, max_deviation, passed, expected,
        observed, deviations.
        """
        assumption = ValidationAssumption(
            all_passed=True,
            total_constraints=1,
            failed_count=0,
            marginal_details={
                "vehicle_type": {
                    "tolerance": 0.03,
                    "max_deviation": 0.02,
                    "passed": True,
                    "expected": {"car": 0.65, "suv": 0.20, "bike": 0.15},
                    "observed": {"car": 0.67, "suv": 0.18, "bike": 0.15},
                    "deviations": {"car": 0.02, "suv": -0.02, "bike": 0.0},
                },
            },
        )
        entry = assumption.to_governance_entry()

        marginal_detail = entry["value"]["marginal_details"]["vehicle_type"]
        assert "tolerance" in marginal_detail
        assert "max_deviation" in marginal_detail
        assert "passed" in marginal_detail
        assert "expected" in marginal_detail
        assert "observed" in marginal_detail
        assert "deviations" in marginal_detail


# ====================================================================
# Test ValidationResult.to_assumption()
# ====================================================================


class TestValidationResultToAssumption:
    """Test ValidationResult.to_assumption()."""

    def test_validation_result_with_all_passed(self) -> None:
        """Given ValidationResult with all passed.

        Expected: to_assumption() produces ValidationAssumption with
        all_passed=True.
        """
        constraint = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        marginal_result = MarginalResult(
            constraint=constraint,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        validation_result = ValidationResult(
            all_passed=True,
            marginal_results=(marginal_result,),
            total_constraints=1,
            failed_count=0,
        )

        assumption = validation_result.to_assumption()
        assert assumption.all_passed is True
        assert assumption.total_constraints == 1
        assert assumption.failed_count == 0

    def test_validation_result_with_failures(self) -> None:
        """Given ValidationResult with failures.

        Expected: to_assumption() produces ValidationAssumption with
        all_passed=False and correct failed_count.
        """
        constraint1 = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        constraint2 = MarginalConstraint(
            dimension="income_decile",
            distribution={
                "1": 0.1,
                "2": 0.1,
                "3": 0.1,
                "4": 0.1,
                "5": 0.1,
                "6": 0.1,
                "7": 0.1,
                "8": 0.1,
                "9": 0.1,
                "10": 0.1,
            },
            tolerance=0.02,
        )
        marginal_result1 = MarginalResult(
            constraint=constraint1,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        marginal_result2 = MarginalResult(
            constraint=constraint2,
            observed={
                "1": 0.15,
                "2": 0.05,
                "3": 0.1,
                "4": 0.1,
                "5": 0.1,
                "6": 0.1,
                "7": 0.1,
                "8": 0.1,
                "9": 0.05,
                "10": 0.05,
            },
            deviations={
                "1": 0.05,
                "2": -0.05,
                "3": 0.0,
                "4": 0.0,
                "5": 0.0,
                "6": 0.0,
                "7": 0.0,
                "8": 0.0,
                "9": -0.05,
                "10": -0.05,
            },
            max_deviation=0.05,
            passed=False,
        )
        validation_result = ValidationResult(
            all_passed=False,
            marginal_results=(marginal_result1, marginal_result2),
            total_constraints=2,
            failed_count=1,
        )

        assumption = validation_result.to_assumption()
        assert assumption.all_passed is False
        assert assumption.total_constraints == 2
        assert assumption.failed_count == 1

    def test_marginal_details_contains_per_constraint_details(self) -> None:
        """marginal_details contains per-constraint details extracted from marginal_results."""
        constraint1 = MarginalConstraint(
            dimension="vehicle_type",
            distribution={"car": 0.65, "suv": 0.20, "bike": 0.15},
            tolerance=0.03,
        )
        constraint2 = MarginalConstraint(
            dimension="income_decile",
            distribution={
                "1": 0.1,
                "2": 0.1,
                "3": 0.1,
                "4": 0.1,
                "5": 0.1,
                "6": 0.1,
                "7": 0.1,
                "8": 0.1,
                "9": 0.1,
                "10": 0.1,
            },
            tolerance=0.02,
        )
        marginal_result1 = MarginalResult(
            constraint=constraint1,
            observed={"car": 0.67, "suv": 0.18, "bike": 0.15},
            deviations={"car": 0.02, "suv": -0.02, "bike": 0.0},
            max_deviation=0.02,
            passed=True,
        )
        marginal_result2 = MarginalResult(
            constraint=constraint2,
            observed={
                "1": 0.15,
                "2": 0.05,
                "3": 0.1,
                "4": 0.1,
                "5": 0.1,
                "6": 0.1,
                "7": 0.1,
                "8": 0.1,
                "9": 0.05,
                "10": 0.05,
            },
            deviations={
                "1": 0.05,
                "2": -0.05,
                "3": 0.0,
                "4": 0.0,
                "5": 0.0,
                "6": 0.0,
                "7": 0.0,
                "8": 0.0,
                "9": -0.05,
                "10": -0.05,
            },
            max_deviation=0.05,
            passed=False,
        )
        validation_result = ValidationResult(
            all_passed=False,
            marginal_results=(marginal_result1, marginal_result2),
            total_constraints=2,
            failed_count=1,
        )

        assumption = validation_result.to_assumption()

        assert "vehicle_type" in assumption.marginal_details
        assert "income_decile" in assumption.marginal_details

        vehicle_detail = assumption.marginal_details["vehicle_type"]
        assert vehicle_detail["tolerance"] == 0.03
        assert vehicle_detail["max_deviation"] == 0.02
        assert vehicle_detail["passed"] is True
        assert vehicle_detail["expected"] == {"car": 0.65, "suv": 0.20, "bike": 0.15}
        assert vehicle_detail["observed"] == {"car": 0.67, "suv": 0.18, "bike": 0.15}
        assert vehicle_detail["deviations"] == {"car": 0.02, "suv": -0.02, "bike": 0.0}
