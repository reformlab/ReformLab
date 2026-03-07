"""Tests for CalibrationTarget and CalibrationTargetSet — Story 15.1 / AC-1, AC-3."""

from __future__ import annotations

import dataclasses

import pytest

from reformlab.calibration.errors import (
    CalibrationTargetLoadError,
    CalibrationTargetValidationError,
)
from reformlab.calibration.types import CalibrationTarget, CalibrationTargetSet
from tests.calibration.conftest import make_multi_domain_set, make_target, make_vehicle_set


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
