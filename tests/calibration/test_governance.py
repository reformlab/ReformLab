# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for CalibrationTargetSet governance integration — Story 15.1 / AC-1."""

from __future__ import annotations

from reformlab.calibration.types import CalibrationTarget, CalibrationTargetSet
from tests.calibration.conftest import make_multi_domain_set, make_target, make_vehicle_set


class TestGovernanceEntry:
    """AC-1: Governance integration via to_governance_entry()."""

    def test_returns_dict_with_required_keys(self) -> None:
        """Given a CalibrationTargetSet, when to_governance_entry(), then has key/value/source/is_default."""
        target_set = make_vehicle_set()
        entry = target_set.to_governance_entry()

        assert "key" in entry
        assert "value" in entry
        assert "source" in entry
        assert "is_default" in entry

    def test_key_is_calibration_targets(self) -> None:
        """Given any CalibrationTargetSet, when to_governance_entry(), then key='calibration_targets'."""
        entry = make_vehicle_set().to_governance_entry()
        assert entry["key"] == "calibration_targets"

    def test_is_default_is_false(self) -> None:
        """Given any CalibrationTargetSet, when to_governance_entry(), then is_default=False."""
        entry = make_vehicle_set().to_governance_entry()
        assert entry["is_default"] is False

    def test_value_contains_domains(self) -> None:
        """Given a multi-domain set, when to_governance_entry(), then value.domains lists all domains."""
        target_set = make_multi_domain_set()
        entry = target_set.to_governance_entry()
        value = entry["value"]

        assert "domains" in value
        assert sorted(value["domains"]) == ["heating", "vehicle"]

    def test_value_contains_n_targets(self) -> None:
        """Given a set with 4 targets, when to_governance_entry(), then value.n_targets=4."""
        target_set = make_vehicle_set()
        entry = target_set.to_governance_entry()
        assert entry["value"]["n_targets"] == 4

    def test_value_contains_periods(self) -> None:
        """Given targets for period 2022, when to_governance_entry(), then value.periods=[2022]."""
        target_set = make_vehicle_set()
        entry = target_set.to_governance_entry()
        assert entry["value"]["periods"] == [2022]

    def test_value_contains_sources(self) -> None:
        """Given targets from a known source, when to_governance_entry(), then source appears in sources."""
        target_set = CalibrationTargetSet(
            targets=(
                make_target(source_label="SDES 2022"),
                make_target(to_state="keep_current", source_label="ADEME 2022"),
            )
        )
        entry = target_set.to_governance_entry()
        assert sorted(entry["value"]["sources"]) == ["ADEME 2022", "SDES 2022"]

    def test_custom_source_label(self) -> None:
        """Given source_label='my_run', when to_governance_entry(), then source='my_run'."""
        entry = make_vehicle_set().to_governance_entry(source_label="my_run")
        assert entry["source"] == "my_run"

    def test_default_source_label(self) -> None:
        """Given no source_label argument, when to_governance_entry(), then source='calibration_targets'."""
        entry = make_vehicle_set().to_governance_entry()
        assert entry["source"] == "calibration_targets"

    def test_domains_are_sorted(self) -> None:
        """Given multi-domain targets, when to_governance_entry(), then value.domains is sorted."""
        target_set = make_multi_domain_set()
        entry = target_set.to_governance_entry()
        domains = entry["value"]["domains"]
        assert domains == sorted(domains)

    def test_periods_are_sorted(self) -> None:
        """Given targets from multiple periods, when to_governance_entry(), then periods sorted."""
        target_set = CalibrationTargetSet(
            targets=(
                CalibrationTarget(
                    domain="vehicle",
                    period=2023,
                    from_state="petrol",
                    to_state="buy_electric",
                    observed_rate=0.05,
                    source_label="SDES 2023",
                ),
                CalibrationTarget(
                    domain="vehicle",
                    period=2021,
                    from_state="petrol",
                    to_state="buy_electric",
                    observed_rate=0.02,
                    source_label="SDES 2021",
                ),
            )
        )
        entry = target_set.to_governance_entry()
        periods = entry["value"]["periods"]
        assert periods == sorted(periods)
        assert periods == [2021, 2023]

    def test_empty_set_entry(self) -> None:
        """Given an empty CalibrationTargetSet, when to_governance_entry(), then empty lists returned."""
        target_set = CalibrationTargetSet(targets=())
        entry = target_set.to_governance_entry()

        assert entry["key"] == "calibration_targets"
        assert entry["value"]["domains"] == []
        assert entry["value"]["n_targets"] == 0
        assert entry["value"]["periods"] == []
        assert entry["value"]["sources"] == []
        assert entry["is_default"] is False
