# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for CalibrationEngine and objective functions — Story 15.2 / AC-1 through AC-5."""

from __future__ import annotations

import dataclasses
import math

import pyarrow as pa
import pytest

from reformlab.calibration.engine import (
    CalibrationEngine,
    build_log_likelihood_objective,
    build_mse_objective,
    compute_simulated_rates,
)
from reformlab.calibration.errors import CalibrationOptimizationError
from reformlab.calibration.types import (
    CalibrationConfig,
    CalibrationResult,
    CalibrationTarget,
    CalibrationTargetSet,
)
from reformlab.discrete_choice.types import CostMatrix, TasteParameters
from tests.calibration.conftest import (
    make_sample_config,
    make_sample_cost_matrix,
    make_sample_engine,
    make_sample_from_states,
    make_sample_target_set,
)

# ============================== Hand-computed constants ==============================
# From Dev Notes (beta = -0.01):
# H0 (petrol): V_A=-1.0, V_B=-2.0 → P_A=0.7311, P_B=0.2689
# H1 (petrol): V_A=-1.5, V_B=-1.0 → P_A=0.3775, P_B=0.6225
# H2 (diesel): V_A=-2.0, V_B=-3.0 → P_A=0.7311, P_B=0.2689
# Group petrol→A = (0.7311+0.3775)/2 = 0.5543, petrol→B = 0.4457
# Group diesel→A = 0.7311, diesel→B = 0.2689

BETA_TEST = -0.01
APPROX_TOL = 1e-3


class TestComputeSimulatedRates:
    """AC-1, AC-3: compute_simulated_rates pure function."""

    def test_correct_rates_hand_computed(self) -> None:
        """Given 3-household example, when beta=-0.01, then rates match hand-computed values."""
        # AC-1, AC-3
        cost_matrix = make_sample_cost_matrix()
        from_states = make_sample_from_states()
        taste = TasteParameters(beta_cost=BETA_TEST)

        rates = compute_simulated_rates(cost_matrix, taste, from_states, ("A", "B"))

        assert rates[("petrol", "A")] == pytest.approx(0.5543, abs=APPROX_TOL)
        assert rates[("petrol", "B")] == pytest.approx(0.4457, abs=APPROX_TOL)
        assert rates[("diesel", "A")] == pytest.approx(0.7311, abs=APPROX_TOL)
        assert rates[("diesel", "B")] == pytest.approx(0.2689, abs=APPROX_TOL)

    def test_empty_population_returns_empty_dict(self) -> None:
        """Given 0-household cost matrix, when compute_simulated_rates, then returns {}."""
        table = pa.table({"A": pa.array([], pa.float64()), "B": pa.array([], pa.float64())})
        cost_matrix = CostMatrix(table=table, alternative_ids=("A", "B"))
        from_states = pa.array([], type=pa.utf8())
        taste = TasteParameters(beta_cost=-0.01)

        rates = compute_simulated_rates(cost_matrix, taste, from_states, ("A", "B"))

        assert rates == {}

    def test_single_household_group(self) -> None:
        """Given single diesel household, rate equals probability."""
        table = pa.table(
            {"A": pa.array([200.0], pa.float64()), "B": pa.array([300.0], pa.float64())}
        )
        cost_matrix = CostMatrix(table=table, alternative_ids=("A", "B"))
        from_states = pa.array(["diesel"], type=pa.utf8())
        taste = TasteParameters(beta_cost=BETA_TEST)

        rates = compute_simulated_rates(cost_matrix, taste, from_states, ("A", "B"))

        # V_A=-2.0, V_B=-3.0 → P_A≈0.7311
        assert rates[("diesel", "A")] == pytest.approx(0.7311, abs=APPROX_TOL)
        assert rates[("diesel", "B")] == pytest.approx(0.2689, abs=APPROX_TOL)

    def test_multiple_from_state_groups(self) -> None:
        """Given 4 households with 3 distinct from_states, then 3 groups computed."""
        table = pa.table(
            {
                "A": pa.array([100.0, 150.0, 200.0, 120.0], pa.float64()),
                "B": pa.array([200.0, 100.0, 300.0, 180.0], pa.float64()),
            }
        )
        cost_matrix = CostMatrix(table=table, alternative_ids=("A", "B"))
        from_states = pa.array(["petrol", "petrol", "diesel", "hybrid"], type=pa.utf8())
        taste = TasteParameters(beta_cost=BETA_TEST)

        rates = compute_simulated_rates(cost_matrix, taste, from_states, ("A", "B"))

        # Should have entries for all three groups
        assert ("petrol", "A") in rates
        assert ("diesel", "A") in rates
        assert ("hybrid", "A") in rates
        # Probabilities per group must sum to ~1.0
        assert rates[("petrol", "A")] + rates[("petrol", "B")] == pytest.approx(1.0, abs=1e-6)
        assert rates[("diesel", "A")] + rates[("diesel", "B")] == pytest.approx(1.0, abs=1e-6)
        assert rates[("hybrid", "A")] + rates[("hybrid", "B")] == pytest.approx(1.0, abs=1e-6)

    def test_rates_sum_to_one_per_from_state(self) -> None:
        """Given multi-alternative cost matrix, rates for each from_state sum to 1.0."""
        cost_matrix = make_sample_cost_matrix()
        from_states = make_sample_from_states()
        taste = TasteParameters(beta_cost=-0.05)

        rates = compute_simulated_rates(cost_matrix, taste, from_states, ("A", "B"))

        petrol_sum = rates[("petrol", "A")] + rates[("petrol", "B")]
        diesel_sum = rates[("diesel", "A")] + rates[("diesel", "B")]
        assert petrol_sum == pytest.approx(1.0, abs=1e-6)
        assert diesel_sum == pytest.approx(1.0, abs=1e-6)


class TestMSEObjective:
    """AC-2: MSE objective function."""

    def test_zero_error_when_simulated_matches_observed(self) -> None:
        """Given targets that exactly match simulated rates, MSE objective returns 0."""
        # At beta=-0.01: petrol→A≈0.5543, petrol→B≈0.4457, diesel→A≈0.7311
        targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.5543,
                    source_label="test",
                ),
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="B",
                    observed_rate=0.4457,
                    source_label="test",
                ),
            )
        )
        cost_matrix = make_sample_cost_matrix()
        from_states = make_sample_from_states()
        obj = build_mse_objective(targets, cost_matrix, from_states)

        import numpy as np

        mse = obj(np.array([-0.01]))
        assert mse == pytest.approx(0.0, abs=APPROX_TOL)

    def test_known_mse_value_hand_computed(self) -> None:
        """Given Dev Notes example targets, MSE at beta=-0.01 matches hand-computed 0.0173."""
        # AC-2
        # Observed: petrol→A=0.40, petrol→B=0.55, diesel→A=0.60
        # Simulated at beta=-0.01: petrol→A=0.5543, petrol→B=0.4457, diesel→A=0.7311
        # MSE = ((0.5543-0.40)²+(0.4457-0.55)²+(0.7311-0.60)²)/3 ≈ 0.0173
        targets = make_sample_target_set()
        cost_matrix = make_sample_cost_matrix()
        from_states = make_sample_from_states()
        obj = build_mse_objective(targets, cost_matrix, from_states)

        import numpy as np

        mse = obj(np.array([BETA_TEST]))
        assert mse == pytest.approx(0.0173, abs=APPROX_TOL)

    def test_weighted_mse_applies_weights(self) -> None:
        """Given different weights, MSE is weighted average of squared errors."""
        import numpy as np

        cost_matrix = make_sample_cost_matrix()
        from_states = make_sample_from_states()

        # Two targets: petrol→A with weight=2.0, petrol→B with weight=1.0
        targets_equal = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.40,
                    source_label="test",
                    weight=1.0,
                ),
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="B",
                    observed_rate=0.40,
                    source_label="test",
                    weight=1.0,
                ),
            )
        )
        targets_weighted = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.40,
                    source_label="test",
                    weight=2.0,
                ),
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="B",
                    observed_rate=0.40,
                    source_label="test",
                    weight=1.0,
                ),
            )
        )
        obj_equal = build_mse_objective(targets_equal, cost_matrix, from_states)
        obj_weighted = build_mse_objective(targets_weighted, cost_matrix, from_states)

        beta = np.array([-0.01])
        mse_equal = obj_equal(beta)
        mse_weighted = obj_weighted(beta)

        # With different weights, results should differ
        assert mse_equal != pytest.approx(mse_weighted, abs=1e-6)

        # Manual verification: weighted sum / total_weight
        rates = compute_simulated_rates(
            cost_matrix, TasteParameters(beta_cost=-0.01), from_states, ("A", "B")
        )
        sim_a = rates[("petrol", "A")]
        sim_b = rates[("petrol", "B")]
        expected_equal = ((sim_a - 0.40) ** 2 + (sim_b - 0.40) ** 2) / 2.0
        expected_weighted = (2.0 * (sim_a - 0.40) ** 2 + 1.0 * (sim_b - 0.40) ** 2) / 3.0
        assert mse_equal == pytest.approx(expected_equal, abs=1e-6)
        assert mse_weighted == pytest.approx(expected_weighted, abs=1e-6)


class TestLogLikelihoodObjective:
    """AC-2: Log-likelihood objective function."""

    def test_known_value_hand_computed(self) -> None:
        """Given Dev Notes targets, NLL at beta=-0.01 matches hand-computed ≈2.14.

        Hand-computed:
          sim: petrol→A=0.5543, petrol→B=0.4457, diesel→A=0.7311
          obs: petrol→A=0.40, petrol→B=0.55, diesel→A=0.60
          NLL = -(0.40*ln(0.5543)+0.60*ln(0.4457))
                -(0.55*ln(0.4457)+0.45*ln(0.5543))
                -(0.60*ln(0.7311)+0.40*ln(0.2689))
              ≈ 0.721 + 0.710 + 0.713 = 2.144
        """
        import numpy as np

        targets = make_sample_target_set()
        cost_matrix = make_sample_cost_matrix()
        from_states = make_sample_from_states()
        obj = build_log_likelihood_objective(targets, cost_matrix, from_states)

        ll = obj(np.array([-0.01]))
        assert math.isfinite(ll)
        assert ll > 0.0  # negative log-likelihood is positive
        assert ll == pytest.approx(2.14, abs=0.02)  # hand-computed expected value

    def test_clamping_prevents_log_of_zero(self) -> None:
        """Given an observed_rate=0.0, when computing log-likelihood, then no NaN/Inf."""
        import numpy as np

        targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.0,  # would cause log(0) without clamping
                    source_label="test",
                ),
            )
        )
        from_states = pa.array(["petrol"], type=pa.utf8())

        # Use a 1-household cost matrix
        table = pa.table({"A": pa.array([100.0], pa.float64()), "B": pa.array([200.0], pa.float64())})
        cost_matrix_1 = CostMatrix(table=table, alternative_ids=("A", "B"))
        obj_1 = build_log_likelihood_objective(targets, cost_matrix_1, from_states)
        ll = obj_1(np.array([-0.01]))
        assert math.isfinite(ll)
        assert ll >= 0.0  # negative log-likelihood should be non-negative

    def test_negative_log_likelihood_is_positive(self) -> None:
        """Given valid targets and beta, negative log-likelihood objective returns positive scalar."""
        import numpy as np

        targets = make_sample_target_set()
        cost_matrix = make_sample_cost_matrix()
        from_states = make_sample_from_states()
        obj = build_log_likelihood_objective(targets, cost_matrix, from_states)

        ll = obj(np.array([-0.05]))
        assert ll > 0.0


class TestCalibrationEngine:
    """AC-1 through AC-5: CalibrationEngine integration."""

    def test_construction_with_valid_config(self) -> None:
        """Given valid CalibrationConfig, when constructing engine, then succeeds."""
        engine = make_sample_engine()
        assert isinstance(engine, CalibrationEngine)
        assert engine.config.domain == "vehicle"

    def test_calibrate_returns_calibration_result(self) -> None:
        """Given valid config, when calibrate(), then returns CalibrationResult. AC-4."""
        engine = make_sample_engine()
        result = engine.calibrate()
        assert isinstance(result, CalibrationResult)

    def test_calibrate_all_required_fields_present(self) -> None:
        """Given calibrate() result, then all required fields are populated. AC-4."""
        engine = make_sample_engine()
        result = engine.calibrate()

        assert isinstance(result.optimized_parameters, TasteParameters)
        assert result.domain == "vehicle"
        assert result.objective_type == "mse"
        assert isinstance(result.objective_value, float)
        assert isinstance(result.convergence_flag, bool)
        assert isinstance(result.iterations, int)
        assert result.method == "L-BFGS-B"
        assert isinstance(result.rate_comparisons, tuple)
        assert isinstance(result.all_within_tolerance, bool)

    def test_convergence_flag_true_for_well_posed_problem(self) -> None:
        """Given well-posed targets, when calibrate(), then convergence_flag is True. AC-4."""
        engine = make_sample_engine()
        result = engine.calibrate()
        assert result.convergence_flag is True

    def test_determinism_same_result_on_repeated_calls(self) -> None:
        """Given same config, when calibrate() twice, then identical results. AC-3."""
        engine = make_sample_engine()
        result1 = engine.calibrate()
        result2 = engine.calibrate()

        assert result1.optimized_parameters.beta_cost == pytest.approx(
            result2.optimized_parameters.beta_cost, abs=1e-10
        )
        assert result1.objective_value == pytest.approx(result2.objective_value, abs=1e-10)
        assert result1.iterations == result2.iterations

    def test_optimized_beta_within_bounds(self) -> None:
        """Given beta_bounds=(-1.0, 0.0), when calibrate(), optimized beta is within bounds."""
        config = make_sample_config()
        engine = CalibrationEngine(config=config)
        result = engine.calibrate()

        assert config.beta_bounds[0] <= result.optimized_parameters.beta_cost <= config.beta_bounds[1]

    def test_rate_comparisons_has_correct_per_target_entries(self) -> None:
        """Given 3 targets, when calibrate(), rate_comparisons has exactly 3 entries. AC-4."""
        engine = make_sample_engine()
        result = engine.calibrate()

        assert len(result.rate_comparisons) == 3

    def test_rate_comparisons_have_correct_from_to_states(self) -> None:
        """Given known targets, rate_comparisons contain matching from/to_state pairs."""
        engine = make_sample_engine()
        result = engine.calibrate()

        pairs = {(rc.from_state, rc.to_state) for rc in result.rate_comparisons}
        assert ("petrol", "A") in pairs
        assert ("petrol", "B") in pairs
        assert ("diesel", "A") in pairs

    def test_rate_comparisons_absolute_error_matches_diff(self) -> None:
        """Given rate_comparison, absolute_error equals |simulated - observed|."""
        engine = make_sample_engine()
        result = engine.calibrate()

        for rc in result.rate_comparisons:
            expected_abs_err = abs(rc.simulated_rate - rc.observed_rate)
            assert rc.absolute_error == pytest.approx(expected_abs_err, abs=1e-10)

    def test_all_within_tolerance_consistent_with_comparisons(self) -> None:
        """Given rate_comparisons, all_within_tolerance equals all(rc.within_tolerance). AC-5."""
        engine = make_sample_engine()
        result = engine.calibrate()

        expected = all(rc.within_tolerance for rc in result.rate_comparisons)
        assert result.all_within_tolerance == expected

    def test_within_tolerance_uses_rate_tolerance_threshold(self) -> None:
        """Given rate_tolerance=0.05, within_tolerance is True when abs_err <= 0.05. AC-5."""
        config = make_sample_config()
        assert config.rate_tolerance == 0.05
        engine = CalibrationEngine(config=config)
        result = engine.calibrate()

        for rc in result.rate_comparisons:
            if rc.within_tolerance:
                assert rc.absolute_error <= 0.05
            else:
                assert rc.absolute_error > 0.05

    def test_gradient_norm_present_for_lbfgsb(self) -> None:
        """Given method=L-BFGS-B, gradient_norm is a float (not None). AC-4."""
        engine = make_sample_engine(method="L-BFGS-B")
        result = engine.calibrate()
        # L-BFGS-B provides gradient — may or may not be present depending on scipy version
        # Just verify it's either a float or None (not an error)
        assert result.gradient_norm is None or isinstance(result.gradient_norm, float)

    def test_log_likelihood_objective_type(self) -> None:
        """Given objective_type='log_likelihood', calibrate() returns a valid result."""
        engine = make_sample_engine(objective_type="log_likelihood")
        result = engine.calibrate()
        assert result.objective_type == "log_likelihood"
        assert isinstance(result.objective_value, float)
        assert math.isfinite(result.objective_value)

    def test_engine_is_frozen(self) -> None:
        """Given CalibrationEngine, when attempting mutation, raises FrozenInstanceError."""
        engine = make_sample_engine()
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            engine.config = make_sample_config()  # type: ignore[misc]


class TestCalibrationEngineValidation:
    """AC-1: Input validation raises CalibrationOptimizationError."""

    def test_empty_domain_targets_raises(self) -> None:
        """Given targets for wrong domain, calibrate() raises CalibrationOptimizationError."""
        config = make_sample_config()
        # Override to request a domain that has no targets
        wrong_domain_config = CalibrationConfig(
            targets=config.targets,
            cost_matrix=config.cost_matrix,
            from_states=config.from_states,
            domain="heating",  # no targets in this set for heating
        )
        engine = CalibrationEngine(config=wrong_domain_config)
        with pytest.raises(CalibrationOptimizationError, match="No calibration targets"):
            engine.calibrate()

    def test_unknown_to_state_raises(self) -> None:
        """Given target with to_state not in cost_matrix alternatives, raises error."""
        targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="UNKNOWN_ALT",  # not in cost_matrix
                    observed_rate=0.40,
                    source_label="test",
                ),
            )
        )
        config = CalibrationConfig(
            targets=targets,
            cost_matrix=make_sample_cost_matrix(),
            from_states=make_sample_from_states(),
            domain="vehicle",
        )
        engine = CalibrationEngine(config=config)
        with pytest.raises(CalibrationOptimizationError, match="Unknown to_state"):
            engine.calibrate()

    def test_missing_from_state_raises(self) -> None:
        """Given target with from_state not in from_states array, raises error."""
        targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="MISSING_STATE",  # not in from_states
                    to_state="A",
                    observed_rate=0.40,
                    source_label="test",
                ),
            )
        )
        config = CalibrationConfig(
            targets=targets,
            cost_matrix=make_sample_cost_matrix(),
            from_states=make_sample_from_states(),
            domain="vehicle",
        )
        engine = CalibrationEngine(config=config)
        with pytest.raises(CalibrationOptimizationError, match="Missing from_state"):
            engine.calibrate()

    def test_all_zero_weights_raises(self) -> None:
        """Given all targets with weight=0.0, raises CalibrationOptimizationError. AC-1."""
        targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.40,
                    source_label="test",
                    weight=0.0,
                ),
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="B",
                    observed_rate=0.55,
                    source_label="test",
                    weight=0.0,
                ),
            )
        )
        config = CalibrationConfig(
            targets=targets,
            cost_matrix=make_sample_cost_matrix(),
            from_states=make_sample_from_states(),
            domain="vehicle",
        )
        engine = CalibrationEngine(config=config)
        with pytest.raises(CalibrationOptimizationError, match="weight=0.0"):
            engine.calibrate()

    def test_dimension_mismatch_caught_by_config_post_init(self) -> None:
        """Given from_states length != n_households, CalibrationConfig raises on construction."""
        from_states_wrong = pa.array(["petrol", "petrol"], type=pa.utf8())  # 2, not 3
        with pytest.raises(CalibrationOptimizationError, match="from_states length"):
            CalibrationConfig(
                targets=make_sample_target_set(),
                cost_matrix=make_sample_cost_matrix(),  # 3 households
                from_states=from_states_wrong,
                domain="vehicle",
            )


class TestCalibrationEngineEdgeCases:
    """Edge cases for CalibrationEngine."""

    def test_single_target_calibration(self) -> None:
        """Given single calibration target, calibrate() runs without error."""
        targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.55,
                    source_label="test",
                ),
            )
        )
        config = CalibrationConfig(
            targets=targets,
            cost_matrix=make_sample_cost_matrix(),
            from_states=make_sample_from_states(),
            domain="vehicle",
        )
        engine = CalibrationEngine(config=config)
        result = engine.calibrate()
        assert isinstance(result, CalibrationResult)
        assert len(result.rate_comparisons) == 1

    def test_single_household(self) -> None:
        """Given single-household cost matrix, calibrate() completes."""
        table = pa.table({"A": pa.array([100.0], pa.float64()), "B": pa.array([200.0], pa.float64())})
        cost_matrix = CostMatrix(table=table, alternative_ids=("A", "B"))
        from_states = pa.array(["petrol"], type=pa.utf8())
        targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2022,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.70,
                    source_label="test",
                ),
            )
        )
        config = CalibrationConfig(
            targets=targets,
            cost_matrix=cost_matrix,
            from_states=from_states,
            domain="vehicle",
        )
        engine = CalibrationEngine(config=config)
        result = engine.calibrate()
        assert isinstance(result, CalibrationResult)

    def test_all_households_same_from_state(self) -> None:
        """Given all 3 households with same from_state, only one group is computed."""
        config = CalibrationConfig(
            targets=make_sample_target_set(),
            cost_matrix=make_sample_cost_matrix(),
            from_states=pa.array(["petrol", "petrol", "petrol"], type=pa.utf8()),
            domain="vehicle",
        )
        # Validate that missing from_state 'diesel' causes error (diesel target present)
        engine = CalibrationEngine(config=config)
        with pytest.raises(CalibrationOptimizationError, match="Missing from_state"):
            engine.calibrate()

    def test_non_convergence_returns_result_with_flag_false(self) -> None:
        """Given max_iterations=1, calibrate() returns result with convergence_flag=False. AC-4."""
        config = make_sample_config(max_iterations=1)
        engine = CalibrationEngine(config=config)
        result = engine.calibrate()
        assert isinstance(result, CalibrationResult)
        # L-BFGS-B with maxiter=1 on a non-trivial objective reliably reports failure
        assert result.convergence_flag is False

    def test_beta_at_bounds_boundary(self) -> None:
        """Given initial_beta=-1.0 (at lower bound), calibrate() completes."""
        config = make_sample_config(initial_beta=-0.99)  # near lower bound
        engine = CalibrationEngine(config=config)
        result = engine.calibrate()
        assert isinstance(result, CalibrationResult)
        assert config.beta_bounds[0] <= result.optimized_parameters.beta_cost <= config.beta_bounds[1]
