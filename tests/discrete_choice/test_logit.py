# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for conditional logit model and LogitChoiceStep.

Story 14-2: Conditional logit with seed-controlled draws.
AC-1: Logit probability computation
AC-2: Seed-controlled draws
AC-3: Reproducibility
AC-4: Stochastic variation
AC-5: Probability normalization
AC-6: Type system (TasteParameters, ChoiceResult)
AC-7: Step integration (LogitChoiceStep)
AC-8: State storage
AC-9: Logging
AC-10: No interface changes
"""

from __future__ import annotations

import math
import random

import pyarrow as pa
import pytest

from reformlab.discrete_choice.errors import DiscreteChoiceError, LogitError
from reformlab.discrete_choice.logit import (
    DISCRETE_CHOICE_RESULT_KEY,
    LogitChoiceStep,
    compute_probabilities,
    compute_utilities,
    draw_choices,
)
from reformlab.discrete_choice.step import (
    DISCRETE_CHOICE_COST_MATRIX_KEY,
    DISCRETE_CHOICE_METADATA_KEY,
)
from reformlab.discrete_choice.types import ChoiceResult, CostMatrix, TasteParameters
from reformlab.orchestrator.step import StepRegistry, is_protocol_step
from reformlab.orchestrator.types import YearState

# ============================================================================
# TestComputeUtilities (AC-1)
# ============================================================================


class TestComputeUtilities:
    """Tests for compute_utilities: V_ij = beta_cost × cost_ij."""

    def test_correct_values(self) -> None:
        """V_ij = beta_cost × cost_ij for each cell."""
        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([100.0, 200.0]),
                "b": pa.array([150.0, 300.0]),
            }),
            alternative_ids=("a", "b"),
        )
        taste = TasteParameters(beta_cost=-0.01)
        result = compute_utilities(cost_matrix, taste)

        assert result.num_rows == 2
        assert result.column_names == ["a", "b"]
        assert result.column("a")[0].as_py() == pytest.approx(-1.0)
        assert result.column("a")[1].as_py() == pytest.approx(-2.0)
        assert result.column("b")[0].as_py() == pytest.approx(-1.5)
        assert result.column("b")[1].as_py() == pytest.approx(-3.0)

    def test_empty_matrix(self) -> None:
        """Empty cost matrix (N=0) returns empty utility table."""
        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([], type=pa.float64()),
                "b": pa.array([], type=pa.float64()),
            }),
            alternative_ids=("a", "b"),
        )
        taste = TasteParameters(beta_cost=-1.0)
        result = compute_utilities(cost_matrix, taste)
        assert result.num_rows == 0
        assert result.column_names == ["a", "b"]

    def test_zero_beta(self) -> None:
        """beta_cost=0 produces all-zero utilities."""
        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([100.0]),
                "b": pa.array([200.0]),
            }),
            alternative_ids=("a", "b"),
        )
        taste = TasteParameters(beta_cost=0.0)
        result = compute_utilities(cost_matrix, taste)
        assert result.column("a")[0].as_py() == pytest.approx(0.0)
        assert result.column("b")[0].as_py() == pytest.approx(0.0)

    def test_negative_beta(self) -> None:
        """Negative beta: higher cost → lower utility."""
        cost_matrix = CostMatrix(
            table=pa.table({
                "cheap": pa.array([100.0]),
                "expensive": pa.array([500.0]),
            }),
            alternative_ids=("cheap", "expensive"),
        )
        taste = TasteParameters(beta_cost=-0.01)
        result = compute_utilities(cost_matrix, taste)
        assert result.column("cheap")[0].as_py() > result.column("expensive")[0].as_py()

    def test_nan_raises_logit_error(self) -> None:
        """NaN in cost matrix raises LogitError with cell positions."""
        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([1.0, float("nan")]),
                "b": pa.array([2.0, 3.0]),
            }),
            alternative_ids=("a", "b"),
        )
        taste = TasteParameters(beta_cost=-1.0)
        with pytest.raises(LogitError, match="NaN"):
            compute_utilities(cost_matrix, taste)

    def test_inf_raises_logit_error(self) -> None:
        """Inf in cost matrix raises LogitError."""
        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([float("inf")]),
                "b": pa.array([2.0]),
            }),
            alternative_ids=("a", "b"),
        )
        taste = TasteParameters(beta_cost=-1.0)
        with pytest.raises(LogitError, match="Inf"):
            compute_utilities(cost_matrix, taste)


# ============================================================================
# Story 21.7: Generalized compute_utilities() with ASCs and betas (AC-2)
# ============================================================================


class TestComputeUtilitiesGeneralized:
    """Tests for generalized compute_utilities with ASCs and multiple betas."""

    def test_legacy_mode_produces_identical_results(self) -> None:
        """Legacy mode (is_legacy_mode=True) produces identical results to current implementation."""
        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([100.0, 200.0]),
                "b": pa.array([150.0, 300.0]),
            }),
            alternative_ids=("a", "b"),
        )
        # Legacy TasteParameters
        taste = TasteParameters.from_beta_cost(-0.01)

        # Call without utility_attributes (legacy mode)
        result = compute_utilities(cost_matrix, taste)

        # Should match original V_ij = beta_cost × cost_ij
        assert result.column("a")[0].as_py() == pytest.approx(-1.0)
        assert result.column("a")[1].as_py() == pytest.approx(-2.0)
        assert result.column("b")[0].as_py() == pytest.approx(-1.5)
        assert result.column("b")[1].as_py() == pytest.approx(-3.0)

    def test_ascs_only_utilities(self) -> None:
        """Generalized mode with ASCs only (all betas fixed)."""
        cost_matrix = CostMatrix(
            table=pa.table({
                "ev": pa.array([100.0, 200.0]),
                "petrol": pa.array([150.0, 300.0]),
            }),
            alternative_ids=("ev", "petrol"),
        )
        taste = TasteParameters(
            beta_cost=0.0,
            asc={"ev": 0.0, "petrol": -0.5},
            betas={"cost": -0.01},
            calibrate=frozenset(),
            fixed=frozenset(["ev", "petrol", "cost"]),
            reference_alternative="ev",
        )

        # Without utility_attributes, use cost_matrix for "cost" beta
        result = compute_utilities(cost_matrix, taste)

        # V_ij = ASC_j + beta_cost × cost_ij
        # ev: 0.0 + (-0.01 × cost) = [-1.0, -2.0]
        # petrol: -0.5 + (-0.01 × cost) = [-2.0, -3.5]
        assert result.column("ev")[0].as_py() == pytest.approx(-1.0)
        assert result.column("ev")[1].as_py() == pytest.approx(-2.0)
        assert result.column("petrol")[0].as_py() == pytest.approx(-2.0)
        assert result.column("petrol")[1].as_py() == pytest.approx(-3.5)

    def test_betas_only_utilities(self) -> None:
        """Generalized mode with multiple betas (all ASCs fixed/zero)."""
        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([100.0, 200.0]),
                "b": pa.array([150.0, 300.0]),
            }),
            alternative_ids=("a", "b"),
        )

        # Create utility attributes for cost and emissions
        utility_attrs = {
            "cost": cost_matrix.table,  # Use cost matrix as cost attribute
            "emissions": pa.table({
                "a": pa.array([0.0, 0.0]),  # electric: zero emissions
                "b": pa.array([120.0, 120.0]),  # petrol: 120 g/km
            }),
        }

        taste = TasteParameters(
            beta_cost=0.0,
            asc={},  # No ASCs
            betas={"cost": -0.01, "emissions": -0.05},
            calibrate=frozenset(["cost"]),
            fixed=frozenset(["emissions"]),
            reference_alternative=None,
        )

        result = compute_utilities(cost_matrix, taste, utility_attributes=utility_attrs)

        # V_a = 0 + (-0.01 × 100) + (-0.05 × 0) = -1.0
        # V_b = 0 + (-0.01 × 150) + (-0.05 × 120) = -1.5 - 6.0 = -7.5
        assert result.column("a")[0].as_py() == pytest.approx(-1.0)
        assert result.column("b")[0].as_py() == pytest.approx(-7.5)

    def test_ascs_and_multiple_betas_utilities(self) -> None:
        """Full generalized mode with ASCs + multiple betas."""
        cost_matrix = CostMatrix(
            table=pa.table({
                "ev": pa.array([100.0, 200.0]),
                "petrol": pa.array([150.0, 300.0]),
            }),
            alternative_ids=("ev", "petrol"),
        )

        utility_attrs = {
            "cost": cost_matrix.table,
            "emissions": pa.table({
                "ev": pa.array([0.0, 0.0]),
                "petrol": pa.array([120.0, 120.0]),
            }),
        }

        taste = TasteParameters(
            beta_cost=0.0,
            asc={"ev": 0.0, "petrol": -0.3},  # petrol has negative inertia ASC
            betas={"cost": -0.01, "emissions": -0.05},
            calibrate=frozenset(["ev", "cost"]),
            fixed=frozenset(["petrol", "emissions"]),
            reference_alternative="ev",
        )

        result = compute_utilities(cost_matrix, taste, utility_attributes=utility_attrs)

        # V_ev_0 = 0 + (-0.01 × 100) + (-0.05 × 0) = -1.0
        # V_petrol_0 = -0.3 + (-0.01 × 150) + (-0.05 × 120) = -0.3 - 1.5 - 6.0 = -7.8
        assert result.column("ev")[0].as_py() == pytest.approx(-1.0)
        assert result.column("petrol")[0].as_py() == pytest.approx(-7.8)

    def test_multi_beta_requires_explicit_attributes(self) -> None:
        """Multi-beta without utility_attributes in generalized mode raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([100.0]),
                "b": pa.array([200.0]),
            }),
            alternative_ids=("a", "b"),
        )

        taste = TasteParameters(
            beta_cost=0.0,
            asc={},
            betas={"cost": -0.01, "emissions": -0.05},
            calibrate=frozenset(["cost"]),
            fixed=frozenset(["emissions"]),
        )

        with pytest.raises(DiscreteChoiceError, match="Multi-beta mode requires utility_attributes"):
            compute_utilities(cost_matrix, taste, utility_attributes=None)

    def test_utility_attributes_validation_shape(self) -> None:
        """Utility attributes with wrong shape raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([100.0, 200.0]),
                "b": pa.array([150.0, 300.0]),
            }),
            alternative_ids=("a", "b"),
        )

        utility_attrs = {
            "cost": cost_matrix.table,
            "emissions": pa.table({
                "a": pa.array([0.0]),  # Only 1 row, should be 2
                "b": pa.array([120.0]),
            }),
        }

        taste = TasteParameters(
            beta_cost=0.0,
            asc={},
            betas={"cost": -0.01, "emissions": -0.05},
            calibrate=frozenset(["cost"]),
            fixed=frozenset(["emissions"]),
        )

        with pytest.raises(DiscreteChoiceError, match="has 1 row.*expected 2"):
            compute_utilities(cost_matrix, taste, utility_attributes=utility_attrs)

    def test_utility_attributes_validation_columns(self) -> None:
        """Utility attributes with wrong columns raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([100.0]),
                "b": pa.array([200.0]),
            }),
            alternative_ids=("a", "b"),
        )

        utility_attrs = {
            "cost": cost_matrix.table,
            "emissions": pa.table({
                "x": pa.array([0.0]),  # Wrong column name
                "y": pa.array([120.0]),
            }),
        }

        taste = TasteParameters(
            beta_cost=0.0,
            asc={},
            betas={"cost": -0.01, "emissions": -0.05},
            calibrate=frozenset(["cost"]),
            fixed=frozenset(["emissions"]),
        )

        with pytest.raises(DiscreteChoiceError, match="has columns.*expected.*\\['a', 'b'\\]"):
            compute_utilities(cost_matrix, taste, utility_attributes=utility_attrs)

    def test_utility_attributes_validation_nan_inf(self) -> None:
        """Utility attributes with NaN/Inf raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([100.0]),
                "b": pa.array([200.0]),
            }),
            alternative_ids=("a", "b"),
        )

        utility_attrs = {
            "cost": cost_matrix.table,
            "emissions": pa.table({
                "a": pa.array([float("nan")]),  # NaN value
                "b": pa.array([120.0]),
            }),
        }

        taste = TasteParameters(
            beta_cost=0.0,
            asc={},
            betas={"cost": -0.01, "emissions": -0.05},
            calibrate=frozenset(["cost"]),
            fixed=frozenset(["emissions"]),
        )

        with pytest.raises(DiscreteChoiceError, match="NaN|Inf"):
            compute_utilities(cost_matrix, taste, utility_attributes=utility_attrs)

    def test_utility_attributes_missing_beta_raises(self) -> None:
        """Utility attributes missing table for a beta raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError

        cost_matrix = CostMatrix(
            table=pa.table({
                "a": pa.array([100.0]),
                "b": pa.array([200.0]),
            }),
            alternative_ids=("a", "b"),
        )

        utility_attrs = {
            "cost": cost_matrix.table,
            # Missing "emissions" table
        }

        taste = TasteParameters(
            beta_cost=0.0,
            asc={},
            betas={"cost": -0.01, "emissions": -0.05},
            calibrate=frozenset(["cost"]),
            fixed=frozenset(["emissions"]),
        )

        with pytest.raises(DiscreteChoiceError, match="Missing utility attribute.*emissions"):
            compute_utilities(cost_matrix, taste, utility_attributes=utility_attrs)


# ============================================================================
# TestComputeProbabilities (AC-1, AC-5)
# ============================================================================


class TestComputeProbabilities:
    """Tests for compute_probabilities: softmax with log-sum-exp trick."""

    def test_softmax_correctness(self) -> None:
        """Known utility values produce correct softmax probabilities."""
        utilities = pa.table({
            "a": pa.array([1.0]),
            "b": pa.array([2.0]),
        })
        result = compute_probabilities(utilities)

        # P(a) = exp(1) / (exp(1) + exp(2))
        # P(b) = exp(2) / (exp(1) + exp(2))
        exp1, exp2 = math.exp(1.0), math.exp(2.0)
        expected_a = exp1 / (exp1 + exp2)
        expected_b = exp2 / (exp1 + exp2)
        assert result.column("a")[0].as_py() == pytest.approx(expected_a, rel=1e-10)
        assert result.column("b")[0].as_py() == pytest.approx(expected_b, rel=1e-10)

    def test_sum_to_one(self) -> None:
        """All probability rows sum to 1.0 within tolerance."""
        utilities = pa.table({
            "a": pa.array([0.5, -1.0, 3.0]),
            "b": pa.array([1.5, 2.0, -1.0]),
            "c": pa.array([-0.5, 0.0, 1.0]),
        })
        result = compute_probabilities(utilities)

        for i in range(3):
            row_sum = sum(
                result.column(col)[i].as_py() for col in result.column_names
            )
            assert abs(row_sum - 1.0) < 1e-10

    def test_numerical_stability_large_values(self) -> None:
        """Log-sum-exp trick handles large utility values without overflow."""
        utilities = pa.table({
            "a": pa.array([500.0]),
            "b": pa.array([501.0]),
        })
        result = compute_probabilities(utilities)

        # With log-sum-exp: subtract max (501), compute exp(-1) and exp(0)
        prob_a = result.column("a")[0].as_py()
        prob_b = result.column("b")[0].as_py()
        assert math.isfinite(prob_a)
        assert math.isfinite(prob_b)
        assert abs(prob_a + prob_b - 1.0) < 1e-10

    def test_equal_costs_uniform(self) -> None:
        """Equal utilities → uniform distribution P = 1/M."""
        utilities = pa.table({
            "a": pa.array([5.0, 5.0]),
            "b": pa.array([5.0, 5.0]),
            "c": pa.array([5.0, 5.0]),
        })
        result = compute_probabilities(utilities)

        for i in range(2):
            for col in result.column_names:
                assert result.column(col)[i].as_py() == pytest.approx(1.0 / 3, rel=1e-10)

    def test_single_alternative_probability_one(self) -> None:
        """Single alternative → probability = 1.0."""
        utilities = pa.table({
            "only": pa.array([3.0, -1.0]),
        })
        result = compute_probabilities(utilities)

        for i in range(2):
            assert result.column("only")[i].as_py() == pytest.approx(1.0, rel=1e-10)

    def test_empty_population(self) -> None:
        """Empty utility table returns empty probability table."""
        utilities = pa.table({
            "a": pa.array([], type=pa.float64()),
            "b": pa.array([], type=pa.float64()),
        })
        result = compute_probabilities(utilities)
        assert result.num_rows == 0
        assert result.column_names == ["a", "b"]

    def test_negative_large_values_stability(self) -> None:
        """Large negative utilities don't cause underflow issues."""
        utilities = pa.table({
            "a": pa.array([-1000.0]),
            "b": pa.array([-999.0]),
        })
        result = compute_probabilities(utilities)
        prob_a = result.column("a")[0].as_py()
        prob_b = result.column("b")[0].as_py()
        assert math.isfinite(prob_a)
        assert math.isfinite(prob_b)
        assert abs(prob_a + prob_b - 1.0) < 1e-10


# ============================================================================
# TestDrawChoices (AC-2, AC-3, AC-4)
# ============================================================================


class TestDrawChoices:
    """Tests for draw_choices: inverse CDF sampling with seed control."""

    @staticmethod
    def _make_util_table(alt_ids: tuple[str, ...], n: int) -> pa.Table:
        """Build a dummy utility table with correct shape for draw tests."""
        return pa.table({
            aid: pa.array([0.0] * n) for aid in alt_ids
        })

    def test_determinism_same_seed(self) -> None:
        """Same seed → identical choices (AC-3)."""
        prob_table = pa.table({
            "a": pa.array([0.3, 0.7, 0.5]),
            "b": pa.array([0.7, 0.3, 0.5]),
        })
        alt_ids = ("a", "b")
        util_table = self._make_util_table(alt_ids, 3)

        r1 = draw_choices(prob_table, util_table, alt_ids, seed=42)
        r2 = draw_choices(prob_table, util_table, alt_ids, seed=42)

        assert r1.chosen.to_pylist() == r2.chosen.to_pylist()

    def test_variation_different_seed(self) -> None:
        """Different seeds produce different individual choices (AC-4)."""
        # Use enough households that different seeds will produce different results
        n = 100
        prob_table = pa.table({
            "a": pa.array([0.5] * n),
            "b": pa.array([0.5] * n),
        })
        alt_ids = ("a", "b")
        util_table = self._make_util_table(alt_ids, n)

        r1 = draw_choices(prob_table, util_table, alt_ids, seed=1)
        r2 = draw_choices(prob_table, util_table, alt_ids, seed=2)

        # With 100 households at 50/50, different seeds should produce at least
        # one different choice
        assert r1.chosen.to_pylist() != r2.chosen.to_pylist()

    def test_single_alternative_always_chosen(self) -> None:
        """With M=1, all households choose the only alternative."""
        prob_table = pa.table({
            "only": pa.array([1.0, 1.0, 1.0]),
        })
        alt_ids = ("only",)
        util_table = self._make_util_table(alt_ids, 3)
        result = draw_choices(prob_table, util_table, alt_ids, seed=42)
        assert result.chosen.to_pylist() == ["only", "only", "only"]

    def test_empty_population(self) -> None:
        """N=0 returns empty ChoiceResult."""
        prob_table = pa.table({
            "a": pa.array([], type=pa.float64()),
            "b": pa.array([], type=pa.float64()),
        })
        alt_ids = ("a", "b")
        util_table = self._make_util_table(alt_ids, 0)
        result = draw_choices(prob_table, util_table, alt_ids, seed=42)
        assert len(result.chosen) == 0
        assert result.seed == 42

    def test_inverse_cdf_correctness(self) -> None:
        """With known seed and probabilities, verify exact choice via inverse CDF."""
        # Set up a single household with known probabilities
        prob_table = pa.table({
            "a": pa.array([0.2]),
            "b": pa.array([0.3]),
            "c": pa.array([0.5]),
        })
        alt_ids = ("a", "b", "c")
        util_table = self._make_util_table(alt_ids, 1)

        # Determine what random.Random(99).random() gives
        rng = random.Random(99)
        u = rng.random()

        # Manually compute expected choice
        if u < 0.2:
            expected = "a"
        elif u < 0.5:
            expected = "b"
        else:
            expected = "c"

        result = draw_choices(prob_table, util_table, alt_ids, seed=99)
        assert result.chosen[0].as_py() == expected

    def test_seed_none_works(self) -> None:
        """None seed produces valid (non-deterministic) result."""
        prob_table = pa.table({
            "a": pa.array([0.5]),
            "b": pa.array([0.5]),
        })
        alt_ids = ("a", "b")
        util_table = self._make_util_table(alt_ids, 1)
        result = draw_choices(prob_table, util_table, alt_ids, seed=None)
        assert result.seed is None
        assert len(result.chosen) == 1
        assert result.chosen[0].as_py() in ("a", "b")

    def test_stochastic_variation_aggregate_consistency(self) -> None:
        """Different seeds: aggregate frequencies match expected probabilities (AC-4).

        For N >= 1000, |observed_freq - expected_prob| < 5 * sqrt(p*(1-p)/N)
        for each alternative.
        """
        n = 2000
        expected_probs = {"a": 0.7, "b": 0.3}
        prob_table = pa.table({
            aid: pa.array([p] * n) for aid, p in expected_probs.items()
        })
        alt_ids = ("a", "b")
        util_table = self._make_util_table(alt_ids, n)

        result = draw_choices(prob_table, util_table, alt_ids, seed=12345)
        choices = result.chosen.to_pylist()

        # Check each alternative's frequency (AC-4 requires per-alternative)
        for aid, expected_p in expected_probs.items():
            observed = choices.count(aid) / n
            se = math.sqrt(expected_p * (1 - expected_p) / n)
            assert abs(observed - expected_p) < 5 * se, (
                f"Alternative '{aid}': observed={observed:.4f}, "
                f"expected={expected_p:.4f}, 5*SE={5 * se:.4f}"
            )

    def test_result_fields_populated(self) -> None:
        """ChoiceResult has all expected fields populated with correct data."""
        prob_table = pa.table({
            "a": pa.array([0.6, 0.4]),
            "b": pa.array([0.4, 0.6]),
        })
        util_table = pa.table({
            "a": pa.array([-1.0, -2.0]),
            "b": pa.array([-1.5, -3.0]),
        })
        alt_ids = ("a", "b")
        result = draw_choices(prob_table, util_table, alt_ids, seed=7)

        assert isinstance(result.chosen, pa.Array)
        assert isinstance(result.probabilities, pa.Table)
        assert isinstance(result.utilities, pa.Table)
        assert result.alternative_ids == ("a", "b")
        assert result.seed == 7
        # Verify utilities are the actual utilities, not probabilities
        assert result.utilities.column("a")[0].as_py() == pytest.approx(-1.0)
        assert result.utilities.column("b")[1].as_py() == pytest.approx(-3.0)


# ============================================================================
# Golden value test (AC-1, AC-2, AC-3)
# ============================================================================


class TestGoldenValues:
    """Hand-computed 3×3 logit probabilities and draws with known seed."""

    def test_golden_3x3(self) -> None:
        """Full pipeline: cost → utility → probability → draw with known values."""
        # 3 households × 3 alternatives
        cost_matrix = CostMatrix(
            table=pa.table({
                "x": pa.array([100.0, 200.0, 300.0]),
                "y": pa.array([200.0, 100.0, 200.0]),
                "z": pa.array([300.0, 300.0, 100.0]),
            }),
            alternative_ids=("x", "y", "z"),
        )
        taste = TasteParameters(beta_cost=-0.01)

        # Step 1: Compute utilities
        utilities = compute_utilities(cost_matrix, taste)
        assert utilities.column("x")[0].as_py() == pytest.approx(-1.0)
        assert utilities.column("y")[0].as_py() == pytest.approx(-2.0)
        assert utilities.column("z")[0].as_py() == pytest.approx(-3.0)

        # Step 2: Compute probabilities (log-sum-exp)
        probabilities = compute_probabilities(utilities)

        # Row 0: V = [-1, -2, -3], max = -1
        # shifted: [0, -1, -2]
        # exp: [1, e^-1, e^-2]
        exp_vals_0 = [1.0, math.exp(-1), math.exp(-2)]
        total_0 = sum(exp_vals_0)
        expected_p0 = [v / total_0 for v in exp_vals_0]

        assert probabilities.column("x")[0].as_py() == pytest.approx(expected_p0[0], rel=1e-10)
        assert probabilities.column("y")[0].as_py() == pytest.approx(expected_p0[1], rel=1e-10)
        assert probabilities.column("z")[0].as_py() == pytest.approx(expected_p0[2], rel=1e-10)

        # Verify sum-to-one for all rows
        for i in range(3):
            row_sum = sum(
                probabilities.column(col)[i].as_py()
                for col in ("x", "y", "z")
            )
            assert abs(row_sum - 1.0) < 1e-10

        # Step 3: Draw choices with known seed
        result = draw_choices(probabilities, utilities, ("x", "y", "z"), seed=42)
        assert len(result.chosen) == 3
        assert result.seed == 42

        # Verify determinism
        result2 = draw_choices(probabilities, utilities, ("x", "y", "z"), seed=42)
        assert result.chosen.to_pylist() == result2.chosen.to_pylist()


# ============================================================================
# TestLogitChoiceStep (AC-7, AC-8, AC-9, AC-10)
# ============================================================================


def _make_cost_matrix_state(
    seed: int | None = 42,
    year: int = 2025,
) -> YearState:
    """Build a YearState containing a CostMatrix and metadata for testing."""
    cost_table = pa.table({
        "option_a": pa.array([100.0, 200.0, 300.0]),
        "option_b": pa.array([200.0, 100.0, 200.0]),
        "option_c": pa.array([300.0, 300.0, 100.0]),
    })
    cost_matrix = CostMatrix(
        table=cost_table,
        alternative_ids=("option_a", "option_b", "option_c"),
    )
    metadata = {
        "domain_name": "test_domain",
        "n_households": 3,
        "n_alternatives": 3,
    }
    return YearState(
        year=year,
        data={
            DISCRETE_CHOICE_COST_MATRIX_KEY: cost_matrix,
            DISCRETE_CHOICE_METADATA_KEY: metadata,
        },
        seed=seed,
    )


class TestLogitChoiceStep:
    """Tests for LogitChoiceStep: OrchestratorStep integration."""

    def test_protocol_compliance(self) -> None:
        """LogitChoiceStep satisfies OrchestratorStep protocol (AC-7)."""
        step = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        assert is_protocol_step(step)

    def test_step_registry_registration(self) -> None:
        """LogitChoiceStep can be registered in StepRegistry."""
        registry = StepRegistry()
        step = LogitChoiceStep(
            taste_parameters=TasteParameters(beta_cost=-0.01),
            depends_on=(),
        )
        registry.register(step)
        assert registry.get("logit_choice") is step

    def test_default_properties(self) -> None:
        """Default name, depends_on, description."""
        step = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        assert step.name == "logit_choice"
        assert step.depends_on == ("discrete_choice",)
        assert step.description is not None

    def test_custom_properties(self) -> None:
        """Custom name, depends_on, description."""
        step = LogitChoiceStep(
            taste_parameters=TasteParameters(beta_cost=-0.5),
            name="my_logit",
            depends_on=("step_a", "step_b"),
            description="Custom logit step",
        )
        assert step.name == "my_logit"
        assert step.depends_on == ("step_a", "step_b")
        assert step.description == "Custom logit step"

    def test_full_execute_cycle(self) -> None:
        """Execute reads CostMatrix, computes logit, stores ChoiceResult (AC-7)."""
        step = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        state = _make_cost_matrix_state(seed=42)

        new_state = step.execute(2025, state)

        # ChoiceResult stored under DISCRETE_CHOICE_RESULT_KEY
        result = new_state.data[DISCRETE_CHOICE_RESULT_KEY]
        assert isinstance(result, ChoiceResult)
        assert len(result.chosen) == 3
        assert result.seed == 42
        assert result.alternative_ids == ("option_a", "option_b", "option_c")

        # Probabilities sum to 1 per row
        for i in range(3):
            row_sum = sum(
                result.probabilities.column(col)[i].as_py()
                for col in result.alternative_ids
            )
            assert abs(row_sum - 1.0) < 1e-10

    def test_metadata_extension(self) -> None:
        """Metadata dict extended with beta_cost and choice_seed (AC-8)."""
        step = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.5))
        state = _make_cost_matrix_state(seed=99)

        new_state = step.execute(2025, state)

        metadata = new_state.data[DISCRETE_CHOICE_METADATA_KEY]
        # Original metadata preserved
        assert metadata["domain_name"] == "test_domain"
        assert metadata["n_households"] == 3
        # New fields added
        assert metadata["beta_cost"] == -0.5
        assert metadata["choice_seed"] == 99

    def test_metadata_not_mutated_in_place(self) -> None:
        """Original metadata dict is not mutated (AC-8, immutability)."""
        step = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        state = _make_cost_matrix_state(seed=42)
        original_metadata = state.data[DISCRETE_CHOICE_METADATA_KEY]
        original_keys = set(original_metadata.keys())

        step.execute(2025, state)

        # Original dict should not have been modified
        assert set(original_metadata.keys()) == original_keys

    def test_null_seed_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """WARNING log emitted when seed is None (AC-9)."""
        import logging

        step = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        state = _make_cost_matrix_state(seed=None)

        with caplog.at_level(logging.WARNING):
            step.execute(2025, state)

        assert any("null_seed" in record.message for record in caplog.records)

    def test_structured_logging(self, caplog: pytest.LogCaptureFixture) -> None:
        """Structured key=value logging at INFO level (AC-9)."""
        import logging

        step = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        state = _make_cost_matrix_state(seed=42)

        with caplog.at_level(logging.INFO):
            step.execute(2025, state)

        info_messages = [r.message for r in caplog.records if r.levelno == logging.INFO]
        assert any("event=step_start" in msg for msg in info_messages)
        assert any("event=step_complete" in msg for msg in info_messages)

    def test_missing_cost_matrix_error(self) -> None:
        """Missing CostMatrix raises DiscreteChoiceError (AC-7)."""
        step = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        state = YearState(year=2025, data={}, seed=42)

        with pytest.raises(DiscreteChoiceError, match="CostMatrix not found"):
            step.execute(2025, state)

    def test_determinism(self) -> None:
        """Same state + same seed → identical results (AC-3)."""
        step = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        state = _make_cost_matrix_state(seed=42)

        r1 = step.execute(2025, state)
        r2 = step.execute(2025, state)

        cr1 = r1.data[DISCRETE_CHOICE_RESULT_KEY]
        cr2 = r2.data[DISCRETE_CHOICE_RESULT_KEY]
        assert cr1.chosen.to_pylist() == cr2.chosen.to_pylist()

    def test_immutable_state_update(self) -> None:
        """Execute returns new YearState without modifying original (AC-10)."""
        step = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        state = _make_cost_matrix_state(seed=42)
        original_keys = set(state.data.keys())

        new_state = step.execute(2025, state)

        # Original state unchanged
        assert set(state.data.keys()) == original_keys
        assert DISCRETE_CHOICE_RESULT_KEY not in state.data
        # New state has the result
        assert DISCRETE_CHOICE_RESULT_KEY in new_state.data

    def test_utilities_in_choice_result(self) -> None:
        """ChoiceResult contains actual utilities, not probabilities."""
        step = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        state = _make_cost_matrix_state(seed=42)

        new_state = step.execute(2025, state)
        result = new_state.data[DISCRETE_CHOICE_RESULT_KEY]

        # Utilities should be V = beta * cost, not probabilities
        # First household, option_a cost=100, V = -0.01 * 100 = -1.0
        assert result.utilities.column("option_a")[0].as_py() == pytest.approx(-1.0)
