from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from reformlab.templates.exceptions import ScenarioError
from reformlab.templates.loader import load_scenario_template
from reformlab.templates.reform import resolve_reform_definition
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    PolicyType,
    RebateParameters,
    ReformScenario,
    YearSchedule,
)


# ---------------------------------------------------------------------------
# Task 3 tests: Reform-as-delta mechanics (AC #2)
# ---------------------------------------------------------------------------


class TestBaselineRefValidation:
    """Tests for baseline_ref structural validation (Subtask 3.3)."""

    def test_reform_baseline_ref_valid_format(self) -> None:
        """Valid baseline_ref format is accepted."""
        scenario = ReformScenario(
            name="Test Reform",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="french-carbon-tax-2026",
            parameters=RebateParameters(rate_schedule={}),
        )
        assert scenario.baseline_ref == "french-carbon-tax-2026"

    def test_reform_baseline_ref_empty_raises(self) -> None:
        """Empty baseline_ref raises ValueError."""
        with pytest.raises(ValueError, match="baseline_ref"):
            ReformScenario(
                name="Test",
                policy_type=PolicyType.CARBON_TAX,
                baseline_ref="",
                parameters=RebateParameters(rate_schedule={}),
            )

    def test_reform_baseline_ref_whitespace_only_raises(self) -> None:
        """Whitespace-only baseline_ref raises ValueError."""
        with pytest.raises(ValueError, match="baseline_ref"):
            ReformScenario(
                name="Test",
                policy_type=PolicyType.CARBON_TAX,
                baseline_ref="   ",
                parameters=RebateParameters(rate_schedule={}),
            )

    def test_reform_yaml_missing_baseline_ref(self, tmp_path: Path) -> None:
        """Reform-like YAML without baseline_ref loads as BaselineScenario."""
        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "No Baseline Ref"
            policy_type: carbon_tax
            year_schedule:
              start_year: 2026
              end_year: 2036
            parameters:
              rate_schedule:
                2026: 44.60
        """)
        p = tmp_path / "no-baseline-ref.yaml"
        p.write_text(content, encoding="utf-8")
        scenario = load_scenario_template(p)
        assert isinstance(scenario, BaselineScenario)


class TestResolveReformDefinition:
    """Tests for resolve_reform_definition function (Subtask 3.4)."""

    @pytest.fixture()
    def baseline_scenario(self) -> BaselineScenario:
        """A sample baseline scenario for testing merges."""
        return BaselineScenario(
            name="French Carbon Tax 2026",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(start_year=2026, end_year=2036),
            parameters=CarbonTaxParameters(
                rate_schedule={
                    2026: 44.60, 2027: 50.00, 2028: 55.00,
                    2029: 60.00, 2030: 65.00, 2031: 70.00,
                    2032: 75.00, 2033: 80.00, 2034: 85.00,
                    2035: 90.00, 2036: 100.00,
                },
                exemptions=(
                    {"category": "heating_oil_essential", "rate_reduction": 0.5},
                    {"category": "agricultural_fuel", "rate_reduction": 1.0},
                ),
                covered_categories=("transport_fuel", "heating_fuel", "natural_gas"),
            ),
            description="Baseline carbon tax",
            version="1.0",
        )

    @pytest.fixture()
    def reform_scenario(self) -> ReformScenario:
        """A sample reform scenario with overrides."""
        return ReformScenario(
            name="Progressive Carbon Dividend",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="french-carbon-tax-2026",
            parameters=RebateParameters(
                rate_schedule={},  # Inherits from baseline
                rebate_type="progressive_dividend",
                income_weights={"decile_1": 1.5, "decile_10": 0.5},
            ),
            description="Reform with progressive redistribution",
            version="1.0",
        )

    def test_resolve_reform_inherits_year_schedule(
        self, baseline_scenario: BaselineScenario, reform_scenario: ReformScenario
    ) -> None:
        """Reform inherits year_schedule from baseline when not overridden."""
        resolved = resolve_reform_definition(reform_scenario, baseline_scenario)
        assert resolved.year_schedule.start_year == baseline_scenario.year_schedule.start_year
        assert resolved.year_schedule.end_year == baseline_scenario.year_schedule.end_year

    def test_resolve_reform_inherits_rate_schedule(
        self, baseline_scenario: BaselineScenario, reform_scenario: ReformScenario
    ) -> None:
        """Reform inherits rate_schedule from baseline when empty."""
        resolved = resolve_reform_definition(reform_scenario, baseline_scenario)
        # Rate schedule should come from baseline
        assert resolved.parameters.rate_schedule[2026] == 44.60
        assert resolved.parameters.rate_schedule[2036] == 100.00

    def test_resolve_reform_inherits_covered_categories(
        self, baseline_scenario: BaselineScenario, reform_scenario: ReformScenario
    ) -> None:
        """Reform inherits covered_categories from baseline."""
        resolved = resolve_reform_definition(reform_scenario, baseline_scenario)
        assert "transport_fuel" in resolved.parameters.covered_categories

    def test_resolve_reform_overrides_applied(
        self, baseline_scenario: BaselineScenario
    ) -> None:
        """Reform-specific overrides are preserved."""
        reform = ReformScenario(
            name="Modified Tax",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="french-carbon-tax-2026",
            parameters=CarbonTaxParameters(
                rate_schedule={2026: 50.00, 2027: 60.00},  # Override some years
                covered_categories=("transport_fuel",),  # Reduce coverage
            ),
            version="1.0",
        )
        resolved = resolve_reform_definition(reform, baseline_scenario)
        # Overridden values should be used
        assert resolved.parameters.rate_schedule[2026] == 50.00
        assert resolved.parameters.rate_schedule[2027] == 60.00
        # Non-overridden years should come from baseline
        assert resolved.parameters.rate_schedule[2028] == 55.00
        # Overridden covered_categories should be used
        assert resolved.parameters.covered_categories == ("transport_fuel",)

    def test_resolve_reform_year_schedule_override(
        self, baseline_scenario: BaselineScenario
    ) -> None:
        """Reform can override year_schedule."""
        reform = ReformScenario(
            name="Extended Reform",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="french-carbon-tax-2026",
            parameters=CarbonTaxParameters(rate_schedule={}),
            year_schedule=YearSchedule(start_year=2028, end_year=2040),
            version="1.0",
        )
        resolved = resolve_reform_definition(reform, baseline_scenario)
        assert resolved.year_schedule.start_year == 2028
        assert resolved.year_schedule.end_year == 2040

    def test_resolve_reform_preserves_reform_metadata(
        self, baseline_scenario: BaselineScenario, reform_scenario: ReformScenario
    ) -> None:
        """Reform's name, description, version are preserved."""
        resolved = resolve_reform_definition(reform_scenario, baseline_scenario)
        assert resolved.name == reform_scenario.name
        assert resolved.description == reform_scenario.description
        assert resolved.version == reform_scenario.version

    def test_resolve_reform_policy_type_mismatch_raises(
        self, baseline_scenario: BaselineScenario
    ) -> None:
        """Mismatched policy types raise ScenarioError."""
        reform = ReformScenario(
            name="Wrong Type",
            policy_type=PolicyType.SUBSIDY,  # Different from baseline
            baseline_ref="french-carbon-tax-2026",
            parameters=RebateParameters(rate_schedule={}),
            version="1.0",
        )
        with pytest.raises(ScenarioError, match="policy_type"):
            resolve_reform_definition(reform, baseline_scenario)

    def test_resolve_reform_returns_baseline_scenario(
        self, baseline_scenario: BaselineScenario, reform_scenario: ReformScenario
    ) -> None:
        """resolve_reform_definition returns a BaselineScenario (not Reform)."""
        resolved = resolve_reform_definition(reform_scenario, baseline_scenario)
        # The resolved scenario should be a BaselineScenario
        # (fully specified, no longer a delta)
        assert isinstance(resolved, BaselineScenario)

    def test_resolve_reform_deep_merge_rate_schedule(
        self, baseline_scenario: BaselineScenario
    ) -> None:
        """Rate schedule is deep merged (reform values override, baseline fills gaps)."""
        reform = ReformScenario(
            name="Partial Override",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="french-carbon-tax-2026",
            parameters=CarbonTaxParameters(
                rate_schedule={2030: 80.00, 2031: 90.00},  # Only override 2 years
            ),
            version="1.0",
        )
        resolved = resolve_reform_definition(reform, baseline_scenario)
        # Non-overridden years from baseline
        assert resolved.parameters.rate_schedule[2026] == 44.60
        assert resolved.parameters.rate_schedule[2029] == 60.00
        # Overridden years from reform
        assert resolved.parameters.rate_schedule[2030] == 80.00
        assert resolved.parameters.rate_schedule[2031] == 90.00
        # Later years from baseline
        assert resolved.parameters.rate_schedule[2036] == 100.00
