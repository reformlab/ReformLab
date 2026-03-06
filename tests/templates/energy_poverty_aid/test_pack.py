"""Tests for energy poverty aid template pack loading and portfolio integration.

Story 13.3 — AC #6, #7.
"""

from __future__ import annotations

import pytest

from reformlab.templates.energy_poverty_aid.compute import EnergyPovertyAidParameters
from reformlab.templates.packs import (
    get_energy_poverty_aid_pack_dir,
    list_energy_poverty_aid_templates,
    load_energy_poverty_aid_template,
)
from reformlab.templates.schema import BaselineScenario


class TestEnergyPovertyAidPack:
    """AC #6: Template YAML pack."""

    def test_list_templates(self) -> None:
        templates = list_energy_poverty_aid_templates()
        assert len(templates) >= 2
        assert "energy-poverty-cheque-energie" in templates
        assert "energy-poverty-generous" in templates

    def test_load_cheque_energie_template(self) -> None:
        scenario = load_energy_poverty_aid_template("energy-poverty-cheque-energie")
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.policy, EnergyPovertyAidParameters)
        assert scenario.policy.income_ceiling == 11000.0
        assert scenario.policy.energy_share_threshold == 0.08
        assert scenario.policy.base_aid_amount == 150.0
        assert scenario.policy_type is not None
        assert scenario.policy_type.value == "energy_poverty_aid"

    def test_load_generous_template(self) -> None:
        scenario = load_energy_poverty_aid_template("energy-poverty-generous")
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.policy, EnergyPovertyAidParameters)
        assert scenario.policy.income_ceiling == 15000.0
        assert scenario.policy.energy_share_threshold == 0.10
        assert scenario.policy.base_aid_amount == 300.0

    def test_yaml_round_trip(self, tmp_path: object) -> None:
        """AC #6: YAML round-trip preserves all field values."""
        from pathlib import Path

        from reformlab.templates.loader import (
            dump_scenario_template,
            load_scenario_template,
        )

        original = load_energy_poverty_aid_template("energy-poverty-cheque-energie")
        out_path = Path(str(tmp_path)) / "round-trip.yaml"
        dump_scenario_template(original, out_path)

        # Ensure energy_poverty_aid type is registered before reload
        import reformlab.templates.energy_poverty_aid  # noqa: F401

        reloaded = load_scenario_template(out_path)
        assert isinstance(reloaded, BaselineScenario)
        assert isinstance(reloaded.policy, EnergyPovertyAidParameters)
        assert reloaded.policy.income_ceiling == original.policy.income_ceiling
        assert reloaded.policy.energy_share_threshold == original.policy.energy_share_threshold
        assert reloaded.policy.base_aid_amount == original.policy.base_aid_amount
        assert reloaded.policy.max_energy_factor == original.policy.max_energy_factor

    def test_load_nonexistent_raises(self) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            load_energy_poverty_aid_template("nonexistent-template")

    def test_pack_dir_exists(self) -> None:
        pack_dir = get_energy_poverty_aid_pack_dir()
        assert pack_dir.exists()
        assert pack_dir.is_dir()


class TestPortfolioIntegration:
    """AC #7: Portfolio composition with energy poverty aid."""

    def test_energy_poverty_aid_in_portfolio(self) -> None:
        """AC #7a: Portfolio construction succeeds with energy poverty aid + carbon tax."""
        from reformlab.templates.portfolios import PolicyConfig, PolicyPortfolio
        from reformlab.templates.schema import CarbonTaxParameters, PolicyType, infer_policy_type

        energy_policy = EnergyPovertyAidParameters(
            rate_schedule={2026: 0.0},
            income_ceiling=11000.0,
        )
        carbon_policy = CarbonTaxParameters(
            rate_schedule={2026: 44.6},
            covered_categories=("transport_fuel",),
        )

        energy_type = infer_policy_type(energy_policy)
        portfolio = PolicyPortfolio(
            name="mixed-portfolio",
            policies=(
                PolicyConfig(
                    policy_type=energy_type,
                    policy=energy_policy,
                    name="energy-aid",
                ),
                PolicyConfig(
                    policy_type=PolicyType.CARBON_TAX,
                    policy=carbon_policy,
                    name="carbon-tax",
                ),
            ),
        )
        assert len(portfolio.policies) == 2

    def test_validate_compatibility_detects_same_type_conflicts(self) -> None:
        """AC #7b: validate_compatibility detects same-policy-type conflicts."""
        from reformlab.templates.portfolios import PolicyConfig, PolicyPortfolio, validate_compatibility
        from reformlab.templates.schema import infer_policy_type

        p1 = EnergyPovertyAidParameters(
            rate_schedule={2026: 0.0},
            income_ceiling=11000.0,
        )
        p2 = EnergyPovertyAidParameters(
            rate_schedule={2026: 0.0},
            income_ceiling=15000.0,
        )

        energy_type = infer_policy_type(p1)
        portfolio = PolicyPortfolio(
            name="conflict-portfolio",
            policies=(
                PolicyConfig(policy_type=energy_type, policy=p1, name="aid-1"),
                PolicyConfig(policy_type=energy_type, policy=p2, name="aid-2"),
            ),
        )
        conflicts = validate_compatibility(portfolio)
        assert len(conflicts) >= 1
        conflict_types = [c.conflict_type.value for c in conflicts]
        assert "overlapping_years" in conflict_types
