# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for CalibrationTarget, CalibrationTargetSet, and Story 15.2/15.3 types — Story 15.1, 15.2, 15.3."""

from __future__ import annotations

import dataclasses
import math

import pyarrow as pa
import pytest

from reformlab.calibration.errors import (
    CalibrationOptimizationError,
    CalibrationTargetLoadError,
    CalibrationTargetValidationError,
)
from reformlab.calibration.types import (
    CalibrationConfig,
    CalibrationResult,
    CalibrationTarget,
    CalibrationTargetSet,
    FitMetrics,
    RateComparison,
)
from reformlab.discrete_choice.types import TasteParameters
from tests.calibration.conftest import (
    make_multi_domain_set,
    make_sample_config,
    make_sample_cost_matrix,
    make_sample_from_states,
    make_sample_target_set,
    make_target,
    make_vehicle_set,
)


class TestCalibrationTarget:
    """AC-1: CalibrationTarget format specification."""

    def test_valid_construction(self) -> None:
        """Given valid field values, when constructing CalibrationTarget, then succeeds."""
        target = CalibrationTarget(
            domain="vehicle",
            period=2022,
            from_state="petrol",
            to_state="buy_electric",
            observed_rate=0.03,
            source_label="SDES vehicle fleet 2022",
        )
        assert target.domain == "vehicle"
        assert target.period == 2022
        assert target.from_state == "petrol"
        assert target.to_state == "buy_electric"
        assert target.observed_rate == 0.03
        assert target.source_label == "SDES vehicle fleet 2022"

    def test_source_metadata_defaults_to_empty_dict(self) -> None:
        """Given no source_metadata argument, when constructing, then defaults to {}."""
        target = make_target()
        assert target.source_metadata == {}

    def test_source_metadata_accepts_values(self) -> None:
        """Given source_metadata dict, when constructing, then stored correctly."""
        meta = {"dataset": "parc-2022", "url": "https://data.gouv.fr/..."}
        target = CalibrationTarget(
            domain="vehicle",
            period=2022,
            from_state="petrol",
            to_state="buy_electric",
            observed_rate=0.03,
            source_label="SDES 2022",
            source_metadata=meta,
        )
        assert target.source_metadata == meta

    def test_frozen_immutability(self) -> None:
        """Given a CalibrationTarget, when attempting field reassignment, then raises."""
        target = make_target()
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            target.domain = "heating"  # type: ignore[misc]

    def test_rate_below_zero_raises(self) -> None:
        """Given observed_rate < 0.0, when constructing, then raises CalibrationTargetValidationError."""
        with pytest.raises(CalibrationTargetValidationError, match="observed_rate"):
            CalibrationTarget(
                domain="vehicle",
                period=2022,
                from_state="petrol",
                to_state="buy_electric",
                observed_rate=-0.01,
                source_label="test",
            )

    def test_rate_above_one_raises(self) -> None:
        """Given observed_rate > 1.0, when constructing, then raises CalibrationTargetValidationError."""
        with pytest.raises(CalibrationTargetValidationError, match="observed_rate"):
            CalibrationTarget(
                domain="vehicle",
                period=2022,
                from_state="petrol",
                to_state="buy_electric",
                observed_rate=1.01,
                source_label="test",
            )

    def test_rate_zero_is_valid(self) -> None:
        """Given observed_rate == 0.0, when constructing, then succeeds (boundary)."""
        target = make_target(observed_rate=0.0)
        assert target.observed_rate == 0.0

    def test_rate_one_is_valid(self) -> None:
        """Given observed_rate == 1.0, when constructing, then succeeds (boundary)."""
        target = make_target(observed_rate=1.0)
        assert target.observed_rate == 1.0

    def test_empty_domain_raises(self) -> None:
        """Given empty domain, when constructing, then raises CalibrationTargetValidationError."""
        with pytest.raises(CalibrationTargetValidationError, match="domain"):
            make_target(domain="")

    def test_empty_from_state_raises(self) -> None:
        """Given empty from_state, when constructing, then raises CalibrationTargetValidationError."""
        with pytest.raises(CalibrationTargetValidationError, match="from_state"):
            make_target(from_state="")

    def test_empty_to_state_raises(self) -> None:
        """Given empty to_state, when constructing, then raises CalibrationTargetValidationError."""
        with pytest.raises(CalibrationTargetValidationError, match="to_state"):
            make_target(to_state="")


class TestCalibrationTargetSet:
    """AC-3: Multi-domain access and AC-2: Consistency validation."""

    def test_by_domain_returns_filtered_set(self) -> None:
        """Given a multi-domain set, when by_domain('vehicle'), then only vehicle targets returned."""
        target_set = make_multi_domain_set()
        vehicle_set = target_set.by_domain("vehicle")

        assert all(t.domain == "vehicle" for t in vehicle_set.targets)
        assert len(vehicle_set.targets) == 2

    def test_by_domain_heating_returns_heating_targets(self) -> None:
        """Given a multi-domain set, when by_domain('heating'), then only heating targets returned."""
        target_set = make_multi_domain_set()
        heating_set = target_set.by_domain("heating")

        assert all(t.domain == "heating" for t in heating_set.targets)
        assert len(heating_set.targets) == 2

    def test_by_domain_unknown_returns_empty_set(self) -> None:
        """Given a set with no 'transport' targets, when by_domain('transport'), then empty set."""
        target_set = make_vehicle_set()
        empty_set = target_set.by_domain("transport")
        assert len(empty_set.targets) == 0

    def test_domains_accessible_independently(self) -> None:
        """Given multi-domain targets, when filtered by each domain, then non-overlapping results."""
        target_set = make_multi_domain_set()
        vehicle_set = target_set.by_domain("vehicle")
        heating_set = target_set.by_domain("heating")

        vehicle_domains = {t.domain for t in vehicle_set.targets}
        heating_domains = {t.domain for t in heating_set.targets}
        assert vehicle_domains == {"vehicle"}
        assert heating_domains == {"heating"}
        assert vehicle_domains.isdisjoint(heating_domains)

    def test_validate_consistency_passes_valid_data(self) -> None:
        """Given rates summing to 0.95 per group, when validate_consistency(), then no error."""
        target_set = make_vehicle_set()  # rates sum to 0.95
        target_set.validate_consistency()  # must not raise

    def test_validate_consistency_passes_at_exactly_one(self) -> None:
        """Given rates summing exactly to 1.0, when validate_consistency(), then no error."""
        target_set = CalibrationTargetSet(
            targets=(
                make_target(to_state="buy_electric", observed_rate=0.3),
                make_target(to_state="keep_current", observed_rate=0.7),
            )
        )
        target_set.validate_consistency()  # must not raise

    def test_validate_consistency_passes_at_tolerance_boundary(self) -> None:
        """Given rates summing to exactly 1.0 + 1e-9, when validate_consistency(), then no error."""
        # sum = 1.0 + 1e-9 is at the tolerance boundary and should pass
        target_set = CalibrationTargetSet(
            targets=(
                make_target(to_state="buy_electric", observed_rate=0.5),
                make_target(to_state="keep_current", observed_rate=0.5 + 1e-9),
            )
        )
        target_set.validate_consistency()  # must not raise

    def test_validate_consistency_fails_when_sum_exceeds_tolerance(self) -> None:
        """Given rates summing to 1.0 + 2e-9, when validate_consistency(), then raises."""
        # sum = 1.0 + 2e-9 exceeds the tolerance and must be rejected
        target_set = CalibrationTargetSet(
            targets=(
                make_target(to_state="buy_electric", observed_rate=0.5),
                make_target(to_state="keep_current", observed_rate=0.5 + 2e-9),
            )
        )
        with pytest.raises(CalibrationTargetValidationError, match="rates sum"):
            target_set.validate_consistency()

    def test_validate_consistency_fails_clearly_over_one(self) -> None:
        """Given rates summing to 1.05 per group, when validate_consistency(), then raises with group info."""
        target_set = CalibrationTargetSet(
            targets=(
                make_target(to_state="buy_electric", observed_rate=0.70),
                make_target(to_state="keep_current", observed_rate=0.50),
            )
        )
        with pytest.raises(CalibrationTargetValidationError, match="1\\.2"):
            target_set.validate_consistency()

    def test_validate_consistency_fails_multiple_groups_checked(self) -> None:
        """Given one valid group and one invalid group, when validate_consistency(), then raises."""
        target_set = CalibrationTargetSet(
            targets=(
                # Valid group: vehicle/2022/ev — sum=0.97
                make_target(from_state="ev", to_state="keep_current", observed_rate=0.92),
                make_target(from_state="ev", to_state="buy_electric", observed_rate=0.05),
                # Invalid group: vehicle/2022/petrol — sum=1.20
                make_target(from_state="petrol", to_state="buy_electric", observed_rate=0.70),
                make_target(from_state="petrol", to_state="keep_current", observed_rate=0.50),
            )
        )
        with pytest.raises(CalibrationTargetValidationError):
            target_set.validate_consistency()

    def test_duplicate_rows_raise_load_error(self) -> None:
        """Given duplicate (domain, period, from_state, to_state), when validate_consistency(), raises."""
        target_set = CalibrationTargetSet(
            targets=(
                make_target(to_state="buy_electric", observed_rate=0.03),
                make_target(to_state="buy_electric", observed_rate=0.05),  # duplicate key
            )
        )
        with pytest.raises(CalibrationTargetLoadError, match="duplicate"):
            target_set.validate_consistency()

    def test_empty_set_passes_consistency(self) -> None:
        """Given an empty CalibrationTargetSet, when validate_consistency(), then no error."""
        target_set = CalibrationTargetSet(targets=())
        target_set.validate_consistency()  # must not raise


class TestCalibrationTargetWeight:
    """Story 15.2 / Task 2: weight field on CalibrationTarget."""

    def test_weight_defaults_to_one(self) -> None:
        """Given no weight argument, weight defaults to 1.0."""
        target = make_target()
        assert target.weight == 1.0

    def test_weight_positive_accepted(self) -> None:
        """Given weight=2.5, construction succeeds."""
        target = make_target(weight=2.5)
        assert target.weight == 2.5

    def test_weight_zero_accepted(self) -> None:
        """Given weight=0.0, construction succeeds (zero weight is valid per spec)."""
        target = make_target(weight=0.0)
        assert target.weight == 0.0

    def test_weight_negative_raises(self) -> None:
        """Given weight=-1.0, construction raises CalibrationTargetValidationError."""
        with pytest.raises(CalibrationTargetValidationError, match="weight"):
            make_target(weight=-1.0)


class TestRateComparison:
    """Story 15.2 / Task 3: RateComparison dataclass."""

    def test_construction(self) -> None:
        """Given valid fields, RateComparison constructs without error."""
        rc = RateComparison(
            from_state="petrol",
            to_state="A",
            observed_rate=0.40,
            simulated_rate=0.42,
            absolute_error=0.02,
            within_tolerance=True,
        )
        assert rc.from_state == "petrol"
        assert rc.to_state == "A"
        assert rc.observed_rate == 0.40
        assert rc.simulated_rate == 0.42
        assert rc.absolute_error == 0.02
        assert rc.within_tolerance is True

    def test_frozen_immutability(self) -> None:
        """Given RateComparison, when attempting mutation, raises."""
        rc = RateComparison(
            from_state="petrol",
            to_state="A",
            observed_rate=0.40,
            simulated_rate=0.42,
            absolute_error=0.02,
            within_tolerance=True,
        )
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            rc.from_state = "diesel"  # type: ignore[misc]


class TestCalibrationResult:
    """Story 15.2 / Task 3: CalibrationResult dataclass."""

    def _make_result(self) -> CalibrationResult:
        rc = RateComparison(
            from_state="petrol",
            to_state="A",
            observed_rate=0.40,
            simulated_rate=0.42,
            absolute_error=0.02,
            within_tolerance=True,
        )
        return CalibrationResult(
            optimized_parameters=TasteParameters(beta_cost=-0.05),
            domain="vehicle",
            objective_type="mse",
            objective_value=0.001,
            convergence_flag=True,
            iterations=12,
            gradient_norm=1e-7,
            method="L-BFGS-B",
            rate_comparisons=(rc,),
            all_within_tolerance=True,
        )

    def test_construction(self) -> None:
        """Given valid fields, CalibrationResult constructs without error."""
        result = self._make_result()
        assert result.domain == "vehicle"
        assert result.convergence_flag is True
        assert result.iterations == 12

    def test_frozen_immutability(self) -> None:
        """Given CalibrationResult, when attempting mutation, raises."""
        result = self._make_result()
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            result.domain = "heating"  # type: ignore[misc]

    def test_gradient_norm_can_be_none(self) -> None:
        """Given gradient_norm=None (gradient-free method), construction succeeds."""
        rc = RateComparison(
            from_state="petrol",
            to_state="A",
            observed_rate=0.40,
            simulated_rate=0.42,
            absolute_error=0.02,
            within_tolerance=True,
        )
        result = CalibrationResult(
            optimized_parameters=TasteParameters(beta_cost=-0.05),
            domain="vehicle",
            objective_type="mse",
            objective_value=0.001,
            convergence_flag=True,
            iterations=12,
            gradient_norm=None,
            method="Nelder-Mead",
            rate_comparisons=(rc,),
            all_within_tolerance=True,
        )
        assert result.gradient_norm is None

    def test_to_governance_entry_structure(self) -> None:
        """Given CalibrationResult, to_governance_entry returns correct structure."""
        result = self._make_result()
        entry = result.to_governance_entry()

        assert entry["key"] == "calibration_result"
        assert entry["source"] == "calibration_engine"
        assert entry["is_default"] is False
        value = entry["value"]
        assert value["domain"] == "vehicle"
        assert value["optimized_beta_cost"] == pytest.approx(-0.05)
        assert value["objective_type"] == "mse"
        assert value["convergence_flag"] is True
        assert value["iterations"] == 12
        assert value["method"] == "L-BFGS-B"
        assert value["all_within_tolerance"] is True
        assert value["n_targets"] == 1

    def test_to_governance_entry_custom_source_label(self) -> None:
        """Given custom source_label, to_governance_entry uses it."""
        result = self._make_result()
        entry = result.to_governance_entry(source_label="my_run")
        assert entry["source"] == "my_run"


class TestCalibrationConfig:
    """Story 15.2 / Task 3: CalibrationConfig dataclass."""

    def test_construction_with_defaults(self) -> None:
        """Given required fields only, CalibrationConfig uses defaults."""
        config = make_sample_config()
        assert config.initial_beta == -0.01
        assert config.objective_type == "mse"
        assert config.method == "L-BFGS-B"
        assert config.max_iterations == 100
        assert config.tolerance == 1e-8
        assert config.beta_bounds == (-1.0, 0.0)
        assert config.rate_tolerance == 0.05

    def test_frozen_immutability(self) -> None:
        """Given CalibrationConfig, when attempting mutation, raises."""
        config = make_sample_config()
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            config.domain = "heating"  # type: ignore[misc]

    def test_invalid_objective_type_raises(self) -> None:
        """Given objective_type='invalid', post_init raises CalibrationOptimizationError."""
        with pytest.raises(CalibrationOptimizationError, match="objective_type"):
            CalibrationConfig(
                targets=make_sample_target_set(),
                cost_matrix=make_sample_cost_matrix(),
                from_states=make_sample_from_states(),
                domain="vehicle",
                objective_type="invalid",
            )

    def test_zero_max_iterations_raises(self) -> None:
        """Given max_iterations=0, post_init raises CalibrationOptimizationError."""
        with pytest.raises(CalibrationOptimizationError, match="max_iterations"):
            CalibrationConfig(
                targets=make_sample_target_set(),
                cost_matrix=make_sample_cost_matrix(),
                from_states=make_sample_from_states(),
                domain="vehicle",
                max_iterations=0,
            )

    def test_inverted_beta_bounds_raises(self) -> None:
        """Given beta_bounds=(0.0, -1.0), post_init raises CalibrationOptimizationError."""
        with pytest.raises(CalibrationOptimizationError, match="beta_bounds"):
            CalibrationConfig(
                targets=make_sample_target_set(),
                cost_matrix=make_sample_cost_matrix(),
                from_states=make_sample_from_states(),
                domain="vehicle",
                beta_bounds=(0.0, -1.0),
            )

    def test_zero_rate_tolerance_raises(self) -> None:
        """Given rate_tolerance=0.0, post_init raises CalibrationOptimizationError."""
        with pytest.raises(CalibrationOptimizationError, match="rate_tolerance"):
            CalibrationConfig(
                targets=make_sample_target_set(),
                cost_matrix=make_sample_cost_matrix(),
                from_states=make_sample_from_states(),
                domain="vehicle",
                rate_tolerance=0.0,
            )

    def test_from_states_length_mismatch_raises(self) -> None:
        """Given from_states with wrong length, post_init raises CalibrationOptimizationError."""
        wrong_from_states = pa.array(["petrol", "petrol"], type=pa.utf8())  # 2, not 3
        with pytest.raises(CalibrationOptimizationError, match="from_states length"):
            CalibrationConfig(
                targets=make_sample_target_set(),
                cost_matrix=make_sample_cost_matrix(),
                from_states=wrong_from_states,
                domain="vehicle",
            )


class TestFitMetrics:
    """Story 15.3 / Task 1: FitMetrics dataclass."""

    def test_construction(self) -> None:
        """Given valid fields, FitMetrics constructs without error."""
        fm = FitMetrics(mse=0.01, mae=0.05, n_targets=3, all_within_tolerance=True)
        assert fm.mse == 0.01
        assert fm.mae == 0.05
        assert fm.n_targets == 3
        assert fm.all_within_tolerance is True

    def test_frozen_immutability(self) -> None:
        """Given FitMetrics, when attempting mutation, raises."""
        fm = FitMetrics(mse=0.01, mae=0.05, n_targets=3, all_within_tolerance=True)
        with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
            fm.mse = 0.02  # type: ignore[misc]

    def test_zero_n_targets_raises(self) -> None:
        """Given n_targets=0, __post_init__ raises CalibrationOptimizationError."""
        with pytest.raises(CalibrationOptimizationError, match="n_targets"):
            FitMetrics(mse=0.01, mae=0.05, n_targets=0, all_within_tolerance=True)

    def test_negative_n_targets_raises(self) -> None:
        """Given n_targets=-1, __post_init__ raises CalibrationOptimizationError."""
        with pytest.raises(CalibrationOptimizationError, match="n_targets"):
            FitMetrics(mse=0.01, mae=0.05, n_targets=-1, all_within_tolerance=True)

    def test_negative_mse_raises(self) -> None:
        """Given mse=-0.01, __post_init__ raises CalibrationOptimizationError."""
        with pytest.raises(CalibrationOptimizationError, match="mse"):
            FitMetrics(mse=-0.01, mae=0.05, n_targets=3, all_within_tolerance=True)

    def test_negative_mae_raises(self) -> None:
        """Given mae=-0.05, __post_init__ raises CalibrationOptimizationError."""
        with pytest.raises(CalibrationOptimizationError, match="mae"):
            FitMetrics(mse=0.01, mae=-0.05, n_targets=3, all_within_tolerance=True)

    def test_zero_mse_mae_valid(self) -> None:
        """Given mse=0.0, mae=0.0, construction succeeds (perfect fit boundary)."""
        fm = FitMetrics(mse=0.0, mae=0.0, n_targets=1, all_within_tolerance=True)
        assert fm.mse == 0.0
        assert fm.mae == 0.0

    def test_all_within_tolerance_false(self) -> None:
        """Given all_within_tolerance=False, construction succeeds."""
        fm = FitMetrics(mse=0.5, mae=0.5, n_targets=2, all_within_tolerance=False)
        assert fm.all_within_tolerance is False

    def test_nan_mse_raises(self) -> None:
        """Given mse=nan, __post_init__ raises CalibrationOptimizationError."""
        with pytest.raises(CalibrationOptimizationError, match="mse"):
            FitMetrics(mse=math.nan, mae=0.05, n_targets=3, all_within_tolerance=True)

    def test_inf_mse_raises(self) -> None:
        """Given mse=inf, __post_init__ raises CalibrationOptimizationError."""
        with pytest.raises(CalibrationOptimizationError, match="mse"):
            FitMetrics(mse=math.inf, mae=0.05, n_targets=3, all_within_tolerance=True)

    def test_nan_mae_raises(self) -> None:
        """Given mae=nan, __post_init__ raises CalibrationOptimizationError."""
        with pytest.raises(CalibrationOptimizationError, match="mae"):
            FitMetrics(mse=0.01, mae=math.nan, n_targets=3, all_within_tolerance=True)
