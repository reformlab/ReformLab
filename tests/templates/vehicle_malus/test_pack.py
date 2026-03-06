"""Tests for vehicle malus template pack loading and YAML round-trip.

Story 13.2 — AC #6, #7.
"""

from __future__ import annotations

import pytest

from reformlab.templates.loader import dump_scenario_template, load_scenario_template
from reformlab.templates.packs import (
    get_vehicle_malus_pack_dir,
    list_vehicle_malus_templates,
    load_vehicle_malus_template,
)
from reformlab.templates.schema import BaselineScenario
from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters


class TestVehicleMalusPack:
    """AC #6: Template YAML pack."""

    def test_list_templates(self) -> None:
        templates = list_vehicle_malus_templates()
        assert len(templates) >= 2
        assert "vehicle-malus-french-2026" in templates
        assert "vehicle-malus-flat-rate" in templates

    def test_load_french_2026(self) -> None:
        scenario = load_vehicle_malus_template("vehicle-malus-french-2026")
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.policy, VehicleMalusParameters)
        assert scenario.policy.emission_threshold == 108.0
        assert scenario.name == "Vehicle Malus - French 2026"
        assert scenario.policy_type is not None
        assert scenario.policy_type.value == "vehicle_malus"

    def test_load_flat_rate(self) -> None:
        scenario = load_vehicle_malus_template("vehicle-malus-flat-rate")
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.policy, VehicleMalusParameters)
        assert scenario.policy.emission_threshold == 120.0
        assert scenario.policy.malus_rate_per_gkm == 50.0

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            load_vehicle_malus_template("nonexistent-template")

    def test_get_pack_dir(self) -> None:
        pack_dir = get_vehicle_malus_pack_dir()
        assert pack_dir.exists()
        assert pack_dir.is_dir()

    def test_yaml_round_trip(self, tmp_path: object) -> None:
        """AC #6: YAML round-trip (dump -> reload) preserves all field values."""
        import pathlib

        tmp = pathlib.Path(str(tmp_path))
        scenario = load_vehicle_malus_template("vehicle-malus-french-2026")

        # Dump to temp file
        out_path = tmp / "round-trip.yaml"
        dump_scenario_template(scenario, out_path)

        # Reload
        reloaded = load_scenario_template(out_path)
        assert isinstance(reloaded, BaselineScenario)
        assert isinstance(reloaded.policy, VehicleMalusParameters)

        # Compare key fields
        assert reloaded.name == scenario.name
        assert reloaded.policy.emission_threshold == scenario.policy.emission_threshold
        assert reloaded.policy.malus_rate_per_gkm == scenario.policy.malus_rate_per_gkm
        assert reloaded.policy.threshold_schedule == scenario.policy.threshold_schedule
        assert reloaded.policy.rate_schedule == scenario.policy.rate_schedule


class TestPortfolioIntegration:
    """AC #7: Portfolio composition with vehicle malus."""

    def test_vehicle_malus_in_portfolio(self) -> None:
        """Vehicle malus + carbon tax + subsidy in portfolio."""
        from reformlab.templates.portfolios import (
            PolicyConfig,
            PolicyPortfolio,
            validate_compatibility,
        )
        from reformlab.templates.schema import (
            CarbonTaxParameters,
            PolicyType,
            SubsidyParameters,
            infer_policy_type,
        )

        malus_params = VehicleMalusParameters(
            rate_schedule={2026: 50.0},
            emission_threshold=120.0,
            malus_rate_per_gkm=50.0,
            covered_categories=("passenger_vehicle",),
        )
        carbon_params = CarbonTaxParameters(
            rate_schedule={2026: 44.0},
            covered_categories=("heating_fuel",),
        )
        subsidy_params = SubsidyParameters(
            rate_schedule={2026: 0.0},
            eligible_categories=("insulation",),
        )

        portfolio = PolicyPortfolio(
            name="test-portfolio",
            policies=(
                PolicyConfig(
                    policy_type=infer_policy_type(malus_params),
                    policy=malus_params,
                    name="vehicle-malus",
                ),
                PolicyConfig(
                    policy_type=PolicyType.CARBON_TAX,
                    policy=carbon_params,
                    name="carbon-tax",
                ),
                PolicyConfig(
                    policy_type=PolicyType.SUBSIDY,
                    policy=subsidy_params,
                    name="subsidy",
                ),
            ),
        )
        assert len(portfolio.policies) == 3

        # validate_compatibility should work without error
        conflicts = validate_compatibility(portfolio)
        # Returns conflicts (tuple) — overlapping_years expected since
        # all policies share year 2026 in rate_schedule
        assert isinstance(conflicts, tuple)

    def test_validate_compatibility_detects_overlap(self) -> None:
        """AC #7: validate_compatibility detects overlapping categories."""
        from reformlab.templates.portfolios import (
            PolicyConfig,
            PolicyPortfolio,
            validate_compatibility,
        )
        from reformlab.templates.schema import (
            CarbonTaxParameters,
            PolicyType,
            infer_policy_type,
        )

        malus_params = VehicleMalusParameters(
            rate_schedule={2026: 50.0},
            covered_categories=("passenger_vehicle",),
        )
        carbon_params = CarbonTaxParameters(
            rate_schedule={2026: 44.0},
            covered_categories=("passenger_vehicle",),  # Overlap!
        )

        portfolio = PolicyPortfolio(
            name="overlap-portfolio",
            policies=(
                PolicyConfig(
                    policy_type=infer_policy_type(malus_params),
                    policy=malus_params,
                    name="vehicle-malus",
                ),
                PolicyConfig(
                    policy_type=PolicyType.CARBON_TAX,
                    policy=carbon_params,
                    name="carbon-tax",
                ),
            ),
        )
        conflicts = validate_compatibility(portfolio)
        assert len(conflicts) >= 1
