"""Portfolio integration tests for custom templates (vehicle malus, energy poverty aid).

Story 13.4: Validate custom templates in portfolios and build notebook demo.
Tests AC1 (custom template in portfolio execution), AC2 (portfolio execution
with all Epic 13 templates), AC3 (conflict detection for custom templates),
and AC7 (YAML round-trip with custom template in portfolio).
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import pyarrow as pa
import pytest

# Import custom template modules to trigger import-time registration
import reformlab.templates.energy_poverty_aid  # noqa: F401
import reformlab.templates.vehicle_malus  # noqa: F401
from reformlab.templates.energy_poverty_aid.compute import EnergyPovertyAidParameters
from reformlab.templates.portfolios.composition import (
    dump_portfolio,
    load_portfolio,
    validate_compatibility,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
from reformlab.templates.schema import (
    CarbonTaxParameters,
    PolicyType,
    SubsidyParameters,
    infer_policy_type,
)
from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters


# ====================================================================
# Cleanup fixture — save/restore custom registrations between tests
# ====================================================================


@pytest.fixture(autouse=True)
def _cleanup_custom_registrations() -> Any:
    """Save custom registrations before test, restore after."""
    from reformlab.templates.schema import (
        _CUSTOM_PARAMETERS_TO_POLICY_TYPE,
        _CUSTOM_POLICY_TYPES,
    )

    saved_types = dict(_CUSTOM_POLICY_TYPES)
    saved_params = dict(_CUSTOM_PARAMETERS_TO_POLICY_TYPE)
    yield
    _CUSTOM_POLICY_TYPES.clear()
    _CUSTOM_POLICY_TYPES.update(saved_types)
    _CUSTOM_PARAMETERS_TO_POLICY_TYPE.clear()
    _CUSTOM_PARAMETERS_TO_POLICY_TYPE.update(saved_params)


# ====================================================================
# TestCustomTemplatePortfolioExecution — AC1
# ====================================================================


class TestCustomTemplatePortfolioExecution:
    """Tests for custom templates in portfolio construction and validation.

    AC1: Custom template registered via Story 13.1 API, added to a PolicyPortfolio
    alongside built-in templates, constructs successfully and validates without error.
    """

    def test_vehicle_malus_with_carbon_tax_and_subsidy(self) -> None:
        """Portfolio with VehicleMalusParameters + CarbonTaxParameters + SubsidyParameters
        constructs and validates without conflict (AC1)."""
        carbon = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}),
            name="carbon-tax",
        )
        malus_params = VehicleMalusParameters(rate_schedule={2026: 50.0})
        malus = PolicyConfig(
            policy_type=infer_policy_type(malus_params),
            policy=malus_params,
            name="vehicle-malus",
        )
        subsidy = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=SubsidyParameters(rate_schedule={2026: 100.0}),
            name="subsidy",
        )
        portfolio = PolicyPortfolio(
            name="mixed-portfolio",
            policies=(carbon, malus, subsidy),
        )
        assert portfolio.policy_count == 3

        conflicts = validate_compatibility(portfolio)
        # Different policy types with no overlapping categories → no conflicts
        conflict_types = {c.conflict_type.value for c in conflicts}
        assert "same_policy_type" not in conflict_types

    def test_all_epic13_templates_in_portfolio(self) -> None:
        """Portfolio with VehicleMalusParameters + EnergyPovertyAidParameters +
        CarbonTaxParameters constructs successfully (AC2)."""
        carbon = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}),
            name="carbon-tax",
        )
        malus_params = VehicleMalusParameters(rate_schedule={2026: 50.0})
        malus = PolicyConfig(
            policy_type=infer_policy_type(malus_params),
            policy=malus_params,
            name="vehicle-malus",
        )
        aid_params = EnergyPovertyAidParameters(rate_schedule={2026: 0.0})
        aid = PolicyConfig(
            policy_type=infer_policy_type(aid_params),
            policy=aid_params,
            name="energy-aid",
        )
        portfolio = PolicyPortfolio(
            name="green-transition",
            policies=(carbon, malus, aid),
        )
        assert portfolio.policy_count == 3
        type_values = {pt.value for pt in portfolio.policy_types}
        assert "carbon_tax" in type_values
        assert "vehicle_malus" in type_values
        assert "energy_poverty_aid" in type_values

    def test_asdict_produces_complete_custom_fields(self) -> None:
        """asdict() conversion produces complete dict with custom fields
        (emission_threshold, income_ceiling, etc.) for adapter bridge (AC1, AC2)."""
        malus_params = VehicleMalusParameters(
            rate_schedule={2026: 50.0},
            emission_threshold=130.0,
            malus_rate_per_gkm=75.0,
        )
        d = asdict(malus_params)
        assert d["emission_threshold"] == 130.0
        assert d["malus_rate_per_gkm"] == 75.0
        assert d["rate_schedule"] == {2026: 50.0}

        aid_params = EnergyPovertyAidParameters(
            rate_schedule={2026: 0.0},
            income_ceiling=15000.0,
            energy_share_threshold=0.10,
            base_aid_amount=200.0,
        )
        d2 = asdict(aid_params)
        assert d2["income_ceiling"] == 15000.0
        assert d2["energy_share_threshold"] == 0.10
        assert d2["base_aid_amount"] == 200.0


# ====================================================================
# TestCustomTemplateConflictDetection — AC3
# ====================================================================


class TestCustomTemplateConflictDetection:
    """Tests for conflict detection with custom templates in portfolios.

    AC3: Two policies of the same custom type with overlapping rate_schedule years
    triggers same_policy_type and overlapping_years conflicts.
    """

    def test_two_vehicle_malus_overlapping_years(self) -> None:
        """Two VehicleMalusParameters with overlapping rate_schedule years triggers
        same_policy_type + overlapping_years conflicts (AC3)."""
        malus1 = VehicleMalusParameters(
            rate_schedule={2026: 50.0, 2027: 55.0},
            emission_threshold=118.0,
        )
        malus2 = VehicleMalusParameters(
            rate_schedule={2026: 75.0, 2027: 80.0},
            emission_threshold=100.0,
        )
        portfolio = PolicyPortfolio(
            name="conflict-test",
            policies=(
                PolicyConfig(
                    policy_type=infer_policy_type(malus1),
                    policy=malus1,
                    name="malus-standard",
                ),
                PolicyConfig(
                    policy_type=infer_policy_type(malus2),
                    policy=malus2,
                    name="malus-strict",
                ),
            ),
        )
        conflicts = validate_compatibility(portfolio)
        assert len(conflicts) >= 2
        conflict_types = {c.conflict_type.value for c in conflicts}
        assert "same_policy_type" in conflict_types
        assert "overlapping_years" in conflict_types

    def test_two_energy_poverty_aid_same_type(self) -> None:
        """Two EnergyPovertyAidParameters triggers same_policy_type conflict (AC3)."""
        aid1 = EnergyPovertyAidParameters(
            rate_schedule={2026: 0.0},
            income_ceiling=11000.0,
        )
        aid2 = EnergyPovertyAidParameters(
            rate_schedule={2026: 0.0},
            income_ceiling=15000.0,
        )
        portfolio = PolicyPortfolio(
            name="aid-conflict",
            policies=(
                PolicyConfig(
                    policy_type=infer_policy_type(aid1),
                    policy=aid1,
                    name="aid-standard",
                ),
                PolicyConfig(
                    policy_type=infer_policy_type(aid2),
                    policy=aid2,
                    name="aid-generous",
                ),
            ),
        )
        conflicts = validate_compatibility(portfolio)
        conflict_types = {c.conflict_type.value for c in conflicts}
        assert "same_policy_type" in conflict_types


# ====================================================================
# TestPortfolioComputationWithCustomTemplates — AC2
# ====================================================================


class TestPortfolioComputationWithCustomTemplates:
    """Tests for PortfolioComputationStep execution with custom templates.

    AC2: PortfolioComputationStep passes custom template parameters to adapter
    via asdict() and produces merged output with non-zero results.
    """

    def test_execute_portfolio_with_all_epic13_templates(self) -> None:
        """PortfolioComputationStep executes portfolio with custom + built-in
        templates, adapter receives correct calls, results are merged (AC2)."""
        from reformlab.computation.mock_adapter import MockAdapter
        from reformlab.computation.types import PopulationData
        from reformlab.orchestrator.portfolio_step import (
            COMPUTATION_RESULT_KEY,
            PortfolioComputationStep,
        )
        from reformlab.orchestrator.types import YearState

        output = pa.table({
            "household_id": pa.array([0, 1, 2]),
            "amount": pa.array([100.0, 200.0, 300.0]),
        })
        adapter = MockAdapter(version_string="mock-1.0", default_output=output)
        population = PopulationData(tables={})

        carbon = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}),
            name="Carbon Tax",
        )
        malus_params = VehicleMalusParameters(rate_schedule={2026: 50.0})
        malus = PolicyConfig(
            policy_type=infer_policy_type(malus_params),
            policy=malus_params,
            name="Vehicle Malus",
        )
        aid_params = EnergyPovertyAidParameters(rate_schedule={2026: 0.0})
        aid = PolicyConfig(
            policy_type=infer_policy_type(aid_params),
            policy=aid_params,
            name="Energy Aid",
        )
        portfolio = PolicyPortfolio(
            name="integration-test",
            policies=(carbon, malus, aid),
        )

        step = PortfolioComputationStep(
            adapter=adapter,
            population=population,
            portfolio=portfolio,
        )
        state = YearState(year=2026, data={}, seed=42, metadata={})
        new_state = step.execute(year=2026, state=state)

        # Adapter called 3 times (once per policy)
        assert len(adapter.call_log) == 3
        assert adapter.call_log[0]["policy_name"] == "Carbon Tax"
        assert adapter.call_log[1]["policy_name"] == "Vehicle Malus"
        assert adapter.call_log[2]["policy_name"] == "Energy Aid"

        # Merged result stored in state
        assert COMPUTATION_RESULT_KEY in new_state.data
        merged = new_state.data[COMPUTATION_RESULT_KEY]
        assert merged.output_fields.num_rows == 3

    def test_compute_vehicle_malus_nonzero_results(self) -> None:
        """compute_vehicle_malus produces non-zero malus totals for seeded
        population with emissions above threshold (AC2)."""
        import random

        from reformlab.templates.vehicle_malus.compute import compute_vehicle_malus

        random.seed(42)
        n = 100
        population = pa.table({
            "household_id": pa.array(list(range(n)), type=pa.int64()),
            "income": pa.array(
                [15000.0 + i * 850.0 + random.gauss(0, 2000) for i in range(n)],
                type=pa.float64(),
            ),
            "vehicle_emissions_gkm": pa.array(
                [80.0 + random.gauss(0, 50) + i * 1.7 for i in range(n)],
                type=pa.float64(),
            ),
        })
        policy = VehicleMalusParameters(rate_schedule={2026: 50.0})
        result = compute_vehicle_malus(population, policy, year=2026)
        assert result.total_revenue > 0

    def test_compute_energy_poverty_aid_nonzero_results(self) -> None:
        """compute_energy_poverty_aid produces non-zero aid totals for seeded
        population with low-income, high-energy-share households (AC2)."""
        import random

        from reformlab.templates.energy_poverty_aid.compute import (
            compute_energy_poverty_aid,
        )

        random.seed(42)
        n = 100
        # Low incomes with high energy expenditure shares to trigger eligibility
        # Eligibility: income < 11000 AND energy_share >= 0.08
        incomes = [5000.0 + i * 200.0 for i in range(n)]
        energy_exps = [max(50.0, inc * 0.12 + random.gauss(0, 50)) for inc in incomes]
        population = pa.table({
            "household_id": pa.array(list(range(n)), type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "energy_expenditure": pa.array(energy_exps, type=pa.float64()),
        })
        policy = EnergyPovertyAidParameters(rate_schedule={2026: 0.0})
        result = compute_energy_poverty_aid(population, policy, year=2026)
        assert result.total_cost > 0
        assert result.eligible_count > 0


# ====================================================================
# TestPortfolioYamlRoundTripWithCustomTemplates — AC7
# ====================================================================


class TestPortfolioYamlRoundTripWithCustomTemplates:
    """Tests for YAML round-trip of portfolios containing custom templates.

    AC7: dump_portfolio() + load_portfolio() round-trip preserves custom template
    fields (emission_threshold, income_ceiling, etc.).
    """

    def test_round_trip_preserves_vehicle_malus_fields(self, tmp_path: Any) -> None:
        """YAML round-trip preserves VehicleMalusParameters custom fields (AC7)."""
        malus_params = VehicleMalusParameters(
            rate_schedule={2026: 50.0, 2027: 55.0},
            emission_threshold=130.0,
            malus_rate_per_gkm=75.0,
            threshold_schedule={2027: 125.0},
        )
        carbon = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}),
            name="carbon-tax",
        )
        malus = PolicyConfig(
            policy_type=infer_policy_type(malus_params),
            policy=malus_params,
            name="vehicle-malus",
        )
        portfolio = PolicyPortfolio(
            name="round-trip-test",
            policies=(carbon, malus),
        )

        yaml_path = tmp_path / "portfolio.yaml"
        dump_portfolio(portfolio, yaml_path)

        # Import modules before loading to ensure registration side effects
        import reformlab.templates.vehicle_malus  # noqa: F811, F401

        reloaded = load_portfolio(yaml_path, validate=False)
        assert reloaded.policy_count == 2
        reloaded_malus = reloaded.policies[1].policy
        assert isinstance(reloaded_malus, VehicleMalusParameters)
        assert reloaded_malus.emission_threshold == 130.0
        assert reloaded_malus.malus_rate_per_gkm == 75.0
        assert reloaded_malus.threshold_schedule == {2027: 125.0}

    def test_round_trip_preserves_energy_poverty_aid_fields(self, tmp_path: Any) -> None:
        """YAML round-trip preserves EnergyPovertyAidParameters custom fields (AC7)."""
        aid_params = EnergyPovertyAidParameters(
            rate_schedule={2026: 0.0},
            income_ceiling=15000.0,
            energy_share_threshold=0.10,
            base_aid_amount=200.0,
            max_energy_factor=3.0,
            income_ceiling_schedule={2027: 16000.0},
        )
        carbon = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}),
            name="carbon-tax",
        )
        aid = PolicyConfig(
            policy_type=infer_policy_type(aid_params),
            policy=aid_params,
            name="energy-aid",
        )
        portfolio = PolicyPortfolio(
            name="aid-round-trip",
            policies=(carbon, aid),
        )

        yaml_path = tmp_path / "portfolio.yaml"
        dump_portfolio(portfolio, yaml_path)

        import reformlab.templates.energy_poverty_aid  # noqa: F811, F401

        reloaded = load_portfolio(yaml_path, validate=False)
        assert reloaded.policy_count == 2
        reloaded_aid = reloaded.policies[1].policy
        assert isinstance(reloaded_aid, EnergyPovertyAidParameters)
        assert reloaded_aid.income_ceiling == 15000.0
        assert reloaded_aid.energy_share_threshold == 0.10
        assert reloaded_aid.base_aid_amount == 200.0
        assert reloaded_aid.max_energy_factor == 3.0
        assert reloaded_aid.income_ceiling_schedule == {2027: 16000.0}

    def test_round_trip_mixed_custom_templates(self, tmp_path: Any) -> None:
        """YAML round-trip preserves fields for portfolio with multiple custom types (AC7)."""
        carbon = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(rate_schedule={2026: 44.6}),
            name="carbon-tax",
        )
        malus_params = VehicleMalusParameters(
            rate_schedule={2026: 50.0},
            emission_threshold=120.0,
        )
        malus = PolicyConfig(
            policy_type=infer_policy_type(malus_params),
            policy=malus_params,
            name="vehicle-malus",
        )
        aid_params = EnergyPovertyAidParameters(
            rate_schedule={2026: 0.0},
            income_ceiling=12000.0,
        )
        aid = PolicyConfig(
            policy_type=infer_policy_type(aid_params),
            policy=aid_params,
            name="energy-aid",
        )
        portfolio = PolicyPortfolio(
            name="mixed-round-trip",
            policies=(carbon, malus, aid),
        )

        yaml_path = tmp_path / "portfolio.yaml"
        dump_portfolio(portfolio, yaml_path)

        import reformlab.templates.energy_poverty_aid  # noqa: F811, F401
        import reformlab.templates.vehicle_malus  # noqa: F811, F401

        reloaded = load_portfolio(yaml_path, validate=False)
        assert reloaded.policy_count == 3

        reloaded_malus = reloaded.policies[1].policy
        assert isinstance(reloaded_malus, VehicleMalusParameters)
        assert reloaded_malus.emission_threshold == 120.0

        reloaded_aid = reloaded.policies[2].policy
        assert isinstance(reloaded_aid, EnergyPovertyAidParameters)
        assert reloaded_aid.income_ceiling == 12000.0
