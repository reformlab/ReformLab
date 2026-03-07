"""Tests for calibration validation module — Story 15.3 / FR53 / AC: all."""

from __future__ import annotations

import dataclasses

import pyarrow as pa
import pytest

from reformlab.calibration.errors import CalibrationOptimizationError
from reformlab.calibration.types import (
    CalibrationTargetSet,
    FitMetrics,
    HoldoutValidationResult,
    RateComparison,
)
from reformlab.calibration.validation import compute_fit_metrics, validate_holdout
from reformlab.discrete_choice.types import CostMatrix
from tests.calibration.conftest import (
    make_holdout_cost_matrix,
    make_holdout_from_states,
    make_holdout_target_set,
    make_sample_engine,
)

# ============================== Helpers ==============================


def _make_rc(absolute_error: float, within_tolerance: bool = True) -> RateComparison:
    """Build a minimal RateComparison with the given absolute_error."""
    return RateComparison(
        from_state="A",
        to_state="B",
        observed_rate=0.5,
        simulated_rate=0.5 + absolute_error,
        absolute_error=absolute_error,
        within_tolerance=within_tolerance,
    )


def _get_calibration_result() -> object:
    """Run the sample engine and return the CalibrationResult."""
    return make_sample_engine().calibrate()


# ============================== TestComputeFitMetrics ==============================


class TestComputeFitMetrics:
    """AC-2, AC-3: FitMetrics computation from rate comparisons."""

    def test_hand_computed_mse_mae(self) -> None:
        """Given 3 known absolute_errors, when compute_fit_metrics(), then MSE/MAE match hand computation.

        absolute_errors: 0.05, 0.10, 0.02
        MSE = (0.05² + 0.10² + 0.02²) / 3 = (0.0025 + 0.01 + 0.0004) / 3 ≈ 0.0043
        MAE = (0.05 + 0.10 + 0.02) / 3 ≈ 0.0567
        """
        # AC-2: unweighted gap metrics
        rcs = (
            _make_rc(0.05, True),
            _make_rc(0.10, False),
            _make_rc(0.02, True),
        )
        result = compute_fit_metrics(rcs)

        expected_mse = (0.05**2 + 0.10**2 + 0.02**2) / 3
        expected_mae = (0.05 + 0.10 + 0.02) / 3
        assert result.mse == pytest.approx(expected_mse, abs=1e-4)
        assert result.mae == pytest.approx(expected_mae, abs=1e-4)
        assert result.n_targets == 3

    def test_all_within_tolerance_true_when_all_pass(self) -> None:
        """Given all within_tolerance=True, FitMetrics.all_within_tolerance is True."""
        rcs = (
            _make_rc(0.01, True),
            _make_rc(0.02, True),
        )
        result = compute_fit_metrics(rcs)
        assert result.all_within_tolerance is True

    def test_all_within_tolerance_false_when_any_fail(self) -> None:
        """Given at least one within_tolerance=False, all_within_tolerance is False."""
        rcs = (
            _make_rc(0.01, True),
            _make_rc(0.10, False),
        )
        result = compute_fit_metrics(rcs)
        assert result.all_within_tolerance is False

    def test_single_comparison(self) -> None:
        """Given a single RateComparison, FitMetrics is correctly computed."""
        rcs = (_make_rc(0.03, True),)
        result = compute_fit_metrics(rcs)
        assert result.mse == pytest.approx(0.03**2, abs=1e-8)
        assert result.mae == pytest.approx(0.03, abs=1e-8)
        assert result.n_targets == 1
        assert result.all_within_tolerance is True

    def test_empty_tuple_raises(self) -> None:
        """Given empty tuple, compute_fit_metrics raises CalibrationOptimizationError."""
        # AC-2: divide-by-zero prevention
        with pytest.raises(CalibrationOptimizationError, match="empty"):
            compute_fit_metrics(())

    def test_zero_errors_yields_zero_mse_mae(self) -> None:
        """Given all absolute_error=0.0, MSE and MAE are both zero."""
        rcs = (
            _make_rc(0.0, True),
            _make_rc(0.0, True),
        )
        result = compute_fit_metrics(rcs)
        assert result.mse == pytest.approx(0.0)
        assert result.mae == pytest.approx(0.0)

    def test_metrics_are_unweighted(self) -> None:
        """Given comparisons with implied equal contribution, metrics match unweighted formula.

        AC-2: metrics are unweighted regardless of CalibrationTarget.weight.
        The function takes RateComparison (no weight field), so every comparison
        contributes equally — verified here with a hand-computed example.
        """
        # absolute_errors: 0.20, 0.10 → unweighted MSE = (0.04+0.01)/2=0.025, MAE = 0.15
        rcs = (
            _make_rc(0.20, False),
            _make_rc(0.10, False),
        )
        result = compute_fit_metrics(rcs)
        assert result.mse == pytest.approx((0.20**2 + 0.10**2) / 2, abs=1e-8)
        assert result.mae == pytest.approx((0.20 + 0.10) / 2, abs=1e-8)


# ============================== TestValidateHoldout ==============================


class TestValidateHoldout:
    """AC-1, AC-2, AC-3, AC-4: validate_holdout() correct result structure and computation."""

    def test_result_structure(self) -> None:
        """Given valid calibration result and holdout data, result is HoldoutValidationResult."""
        # AC-1: holdout execution; AC-4: side-by-side reporting
        cal_result = make_sample_engine().calibrate()
        result = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )

        assert isinstance(result, HoldoutValidationResult)
        assert result.domain == "vehicle"
        assert isinstance(result.training_fit, FitMetrics)
        assert isinstance(result.holdout_fit, FitMetrics)

    def test_training_fit_populated_from_calibration_result(self) -> None:
        """Given calibration result, training_fit comes from its rate_comparisons."""
        # AC-4: side-by-side reporting
        cal_result = make_sample_engine().calibrate()
        result = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )

        expected_training_fit = compute_fit_metrics(cal_result.rate_comparisons)
        assert result.training_fit.mse == pytest.approx(expected_training_fit.mse, abs=1e-8)
        assert result.training_fit.mae == pytest.approx(expected_training_fit.mae, abs=1e-8)
        assert result.training_fit.n_targets == expected_training_fit.n_targets

    def test_holdout_fit_computed_from_holdout_data(self) -> None:
        """Given holdout data, holdout_fit is computed from simulated vs holdout observed rates."""
        # AC-2: gap metrics; AC-3: generalization assessment
        cal_result = make_sample_engine().calibrate()
        result = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )

        # holdout_fit must be computed correctly from holdout rate comparisons
        assert result.holdout_fit.n_targets == len(make_holdout_target_set().targets)
        # Verify exact values: MSE and MAE must match the formula applied to returned comparisons
        rcs = result.holdout_rate_comparisons
        expected_mse = sum(rc.absolute_error**2 for rc in rcs) / len(rcs)
        expected_mae = sum(rc.absolute_error for rc in rcs) / len(rcs)
        assert result.holdout_fit.mse == pytest.approx(expected_mse, abs=1e-8)
        assert result.holdout_fit.mae == pytest.approx(expected_mae, abs=1e-8)

    def test_holdout_rate_comparisons_count(self) -> None:
        """Given 3 holdout targets, holdout_rate_comparisons has 3 entries."""
        # AC-3: per-target rate comparisons available
        cal_result = make_sample_engine().calibrate()
        result = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )

        assert len(result.holdout_rate_comparisons) == 3

    def test_holdout_rate_comparisons_sorted_by_from_to_state(self) -> None:
        """Given holdout targets, rate_comparisons are sorted by (from_state, to_state)."""
        cal_result = make_sample_engine().calibrate()
        result = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )

        keys = [(rc.from_state, rc.to_state) for rc in result.holdout_rate_comparisons]
        assert keys == sorted(keys)

    def test_holdout_comparisons_reference_holdout_observed_rates(self) -> None:
        """Given holdout targets with known observed rates, comparisons reflect them."""
        # AC-3: per-target observed vs simulated
        cal_result = make_sample_engine().calibrate()
        holdout_targets = make_holdout_target_set()
        result = validate_holdout(
            cal_result,
            holdout_targets,
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )

        holdout_observed = {
            (t.from_state, t.to_state): t.observed_rate
            for t in holdout_targets.targets
        }
        for rc in result.holdout_rate_comparisons:
            key = (rc.from_state, rc.to_state)
            assert rc.observed_rate == pytest.approx(holdout_observed[key], abs=1e-9)

    def test_rate_tolerance_stored_in_result(self) -> None:
        """Given rate_tolerance=0.10, result.rate_tolerance reflects it."""
        # AC-4: rate_tolerance in result
        cal_result = make_sample_engine().calibrate()
        result = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
            rate_tolerance=0.10,
        )

        assert result.rate_tolerance == pytest.approx(0.10)

    def test_all_within_tolerance_consistency(self) -> None:
        """Given a very generous tolerance, all_within_tolerance is True."""
        cal_result = make_sample_engine().calibrate()
        result = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
            rate_tolerance=1.0,  # any rate passes
        )

        assert result.holdout_fit.all_within_tolerance is True


# ============================== TestValidateHoldoutValidation ==============================


class TestValidateHoldoutValidation:
    """AC-4 / Task 3.4: Input validation in validate_holdout()."""

    def test_zero_rate_tolerance_raises(self) -> None:
        """Given rate_tolerance=0.0, raises CalibrationOptimizationError."""
        cal_result = make_sample_engine().calibrate()
        with pytest.raises(CalibrationOptimizationError, match="rate_tolerance"):
            validate_holdout(
                cal_result,
                make_holdout_target_set(),
                make_holdout_cost_matrix(),
                make_holdout_from_states(),
                rate_tolerance=0.0,
            )

    def test_negative_rate_tolerance_raises(self) -> None:
        """Given rate_tolerance=-0.05, raises CalibrationOptimizationError."""
        cal_result = make_sample_engine().calibrate()
        with pytest.raises(CalibrationOptimizationError, match="rate_tolerance"):
            validate_holdout(
                cal_result,
                make_holdout_target_set(),
                make_holdout_cost_matrix(),
                make_holdout_from_states(),
                rate_tolerance=-0.05,
            )

    def test_nan_rate_tolerance_raises(self) -> None:
        """Given rate_tolerance=nan, raises CalibrationOptimizationError."""
        cal_result = make_sample_engine().calibrate()
        with pytest.raises(CalibrationOptimizationError, match="rate_tolerance"):
            validate_holdout(
                cal_result,
                make_holdout_target_set(),
                make_holdout_cost_matrix(),
                make_holdout_from_states(),
                rate_tolerance=float("nan"),
            )

    def test_inf_rate_tolerance_raises(self) -> None:
        """Given rate_tolerance=inf, raises CalibrationOptimizationError."""
        cal_result = make_sample_engine().calibrate()
        with pytest.raises(CalibrationOptimizationError, match="rate_tolerance"):
            validate_holdout(
                cal_result,
                make_holdout_target_set(),
                make_holdout_cost_matrix(),
                make_holdout_from_states(),
                rate_tolerance=float("inf"),
            )

    def test_empty_holdout_targets_raises(self) -> None:
        """Given holdout target set with no targets for domain, raises CalibrationOptimizationError."""
        cal_result = make_sample_engine().calibrate()
        empty_targets = CalibrationTargetSet(targets=())
        with pytest.raises(CalibrationOptimizationError, match="No holdout"):
            validate_holdout(
                cal_result,
                empty_targets,
                make_holdout_cost_matrix(),
                make_holdout_from_states(),
            )

    def test_duplicate_holdout_target_rows_raise(self) -> None:
        """Given holdout targets with duplicate (domain, period, from_state, to_state), raises."""
        from reformlab.calibration.types import CalibrationTarget

        cal_result = make_sample_engine().calibrate()
        dup_targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.45,
                    source_label="test",
                ),
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.50,
                    source_label="test",
                ),
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="diesel",
                    to_state="A",
                    observed_rate=0.65,
                    source_label="test",
                ),
            )
        )
        with pytest.raises(CalibrationOptimizationError, match="consistency"):
            validate_holdout(
                cal_result,
                dup_targets,
                make_holdout_cost_matrix(),
                make_holdout_from_states(),
            )

    def test_unknown_to_state_raises(self) -> None:
        """Given holdout target with to_state not in cost_matrix alternatives, raises."""
        from reformlab.calibration.types import CalibrationTarget

        cal_result = make_sample_engine().calibrate()
        bad_targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="petrol",
                    to_state="C",  # not in ("A", "B")
                    observed_rate=0.45,
                    source_label="test",
                ),
            )
        )
        with pytest.raises(CalibrationOptimizationError, match="Unknown holdout to_state"):
            validate_holdout(
                cal_result,
                bad_targets,
                make_holdout_cost_matrix(),
                make_holdout_from_states(),
            )

    def test_missing_from_state_raises(self) -> None:
        """Given holdout target with from_state not in holdout_from_states, raises."""
        from reformlab.calibration.types import CalibrationTarget

        cal_result = make_sample_engine().calibrate()
        bad_targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="electric",  # not in ["petrol", "petrol", "diesel"]
                    to_state="A",
                    observed_rate=0.45,
                    source_label="test",
                ),
            )
        )
        with pytest.raises(CalibrationOptimizationError, match="Missing holdout from_state"):
            validate_holdout(
                cal_result,
                bad_targets,
                make_holdout_cost_matrix(),
                make_holdout_from_states(),
            )

    def test_dimension_mismatch_raises(self) -> None:
        """Given from_states length != cost_matrix.n_households, raises CalibrationOptimizationError."""
        cal_result = make_sample_engine().calibrate()
        wrong_from_states = pa.array(["petrol", "petrol"], type=pa.utf8())  # 2 instead of 3

        with pytest.raises(CalibrationOptimizationError, match="from_states length"):
            validate_holdout(
                cal_result,
                make_holdout_target_set(),
                make_holdout_cost_matrix(),
                wrong_from_states,
            )

    def test_null_from_states_raises(self) -> None:
        """Given holdout_from_states with nulls, raises CalibrationOptimizationError.

        Data contracts fail loudly — null household origin states are not silently dropped.
        """
        cal_result = make_sample_engine().calibrate()
        null_from_states = pa.array(["petrol", None, "diesel"], type=pa.utf8())  # null in position 1

        with pytest.raises(CalibrationOptimizationError, match="null values"):
            validate_holdout(
                cal_result,
                make_holdout_target_set(),
                make_holdout_cost_matrix(),
                null_from_states,
            )


# ============================== TestValidateHoldoutEdgeCases ==============================


class TestValidateHoldoutEdgeCases:
    """Edge cases for validate_holdout()."""

    def test_single_holdout_target(self) -> None:
        """Given a single holdout target, validate_holdout returns valid result."""
        from reformlab.calibration.types import CalibrationTarget

        cal_result = make_sample_engine().calibrate()
        single_target = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.45,
                    source_label="test",
                ),
            )
        )
        result = validate_holdout(
            cal_result,
            single_target,
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
        )

        assert result.holdout_fit.n_targets == 1
        assert len(result.holdout_rate_comparisons) == 1

    def test_holdout_with_different_cost_matrix_than_training(self) -> None:
        """Given holdout cost_matrix different from training, result is valid."""
        # AC-1: holdout data is independent from training data
        cal_result = make_sample_engine().calibrate()
        result = validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),  # different from make_sample_cost_matrix()
            make_holdout_from_states(),
        )

        assert result.domain == "vehicle"
        assert result.holdout_fit.n_targets == 3

    def test_perfect_generalization_yields_near_zero_mse(self) -> None:
        """Given holdout observed rates matching simulated rates, MSE ≈ 0."""
        from reformlab.calibration.engine import compute_simulated_rates
        from reformlab.calibration.types import CalibrationTarget

        # Run calibration to get the optimized beta
        cal_result = make_sample_engine().calibrate()
        beta = cal_result.optimized_parameters

        # Compute what the model predicts on holdout data
        holdout_cm = make_holdout_cost_matrix()
        holdout_fs = make_holdout_from_states()
        simulated = compute_simulated_rates(holdout_cm, beta, holdout_fs, holdout_cm.alternative_ids)

        # Set holdout observed rates = simulated rates → MSE should be ≈ 0
        perfect_targets = CalibrationTargetSet(
            targets=tuple(
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state=fs,
                    to_state=ts,
                    observed_rate=rate,
                    source_label="perfect",
                )
                for (fs, ts), rate in simulated.items()
            )
        )
        result = validate_holdout(
            cal_result,
            perfect_targets,
            holdout_cm,
            holdout_fs,
        )

        assert result.holdout_fit.mse == pytest.approx(0.0, abs=1e-10)
        assert result.holdout_fit.mae == pytest.approx(0.0, abs=1e-10)

    def test_poor_generalization_does_not_raise(self) -> None:
        """Given holdout rates far from simulated rates, no exception is raised (non-blocking)."""
        from reformlab.calibration.types import CalibrationTarget

        # Holdout observed rates far from what any reasonable beta would produce
        cal_result = make_sample_engine().calibrate()
        far_targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.01,  # very far from typical simulated ~0.5+
                    source_label="test",
                ),
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="petrol",
                    to_state="B",
                    observed_rate=0.01,
                    source_label="test",
                ),
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="diesel",
                    to_state="A",
                    observed_rate=0.01,
                    source_label="test",
                ),
            )
        )
        # Must NOT raise even with very poor generalization
        result = validate_holdout(
            cal_result,
            far_targets,
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
            rate_tolerance=0.05,
        )

        assert result.holdout_fit.mse > 0.0
        assert result.holdout_fit.all_within_tolerance is False

    def test_holdout_with_different_n_households_than_training(self) -> None:
        """Given holdout with more households than training, result is valid."""
        from reformlab.calibration.types import CalibrationTarget

        # 5-household holdout vs 3-household training
        bigger_cm_table = pa.table(
            {
                "A": pa.array([110.0, 130.0, 120.0, 140.0, 210.0], pa.float64()),
                "B": pa.array([190.0, 170.0, 180.0, 160.0, 280.0], pa.float64()),
            }
        )
        bigger_cm = CostMatrix(table=bigger_cm_table, alternative_ids=("A", "B"))
        bigger_fs = pa.array(["petrol", "petrol", "petrol", "petrol", "diesel"], type=pa.utf8())

        cal_result = make_sample_engine().calibrate()
        bigger_targets = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="petrol",
                    to_state="A",
                    observed_rate=0.45,
                    source_label="test",
                ),
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="diesel",
                    to_state="A",
                    observed_rate=0.65,
                    source_label="test",
                ),
            )
        )
        result = validate_holdout(
            cal_result,
            bigger_targets,
            bigger_cm,
            bigger_fs,
        )

        assert result.holdout_fit.n_targets == 2


# ============================== TestHoldoutValidationResult ==============================


class TestHoldoutValidationResult:
    """AC-4: HoldoutValidationResult construction, immutability, governance entry."""

    def _make_result(self) -> HoldoutValidationResult:
        cal_result = make_sample_engine().calibrate()
        return validate_holdout(
            cal_result,
            make_holdout_target_set(),
            make_holdout_cost_matrix(),
            make_holdout_from_states(),
            rate_tolerance=0.05,
        )

    def test_construction(self) -> None:
        """Given valid inputs, HoldoutValidationResult constructs without error."""
        result = self._make_result()
        assert result.domain == "vehicle"
        assert result.rate_tolerance == pytest.approx(0.05)

    def test_frozen_immutability(self) -> None:
        """Given HoldoutValidationResult, when attempting mutation, raises."""
        result = self._make_result()
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            result.domain = "heating"  # type: ignore[misc]

    def test_to_governance_entry_structure(self) -> None:
        """Given a HoldoutValidationResult, to_governance_entry returns expected structure."""
        # AC-4: governance entry
        result = self._make_result()
        entry = result.to_governance_entry()

        assert entry["key"] == "holdout_validation"
        assert entry["source"] == "holdout_validation"
        assert entry["is_default"] is False
        value = entry["value"]
        assert value["domain"] == "vehicle"
        assert value["holdout_rate_tolerance"] == pytest.approx(0.05)
        assert "training" in value
        assert "holdout" in value
        assert "mse" in value["training"]
        assert "mae" in value["training"]
        assert "n_targets" in value["training"]
        assert "all_within_tolerance" in value["training"]
        assert "mse" in value["holdout"]
        assert "mae" in value["holdout"]
        assert "n_targets" in value["holdout"]
        assert "all_within_tolerance" in value["holdout"]

    def test_to_governance_entry_custom_source_label(self) -> None:
        """Given custom source_label, to_governance_entry uses it."""
        result = self._make_result()
        entry = result.to_governance_entry(source_label="my_holdout_run")
        assert entry["source"] == "my_holdout_run"
