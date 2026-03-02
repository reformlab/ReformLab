from __future__ import annotations

from pathlib import Path

import pytest

from reformlab.templates.loader import dump_scenario_template, load_scenario_template
from reformlab.templates.reform import resolve_reform_definition
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    PolicyType,
    RebateParameters,
    ReformScenario,
)

# ---------------------------------------------------------------------------
# Task 5 tests: Golden file tests for schema validation (Subtask 5.5)
# ---------------------------------------------------------------------------


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "templates"


class TestGoldenCarbonTax:
    """Golden file tests for carbon tax baseline scenario."""

    @pytest.fixture()
    def golden_path(self) -> Path:
        return FIXTURES_DIR / "golden-carbon-tax.yaml"

    def test_load_golden_carbon_tax(self, golden_path: Path) -> None:
        """Golden carbon tax file loads successfully."""
        scenario = load_scenario_template(golden_path)
        assert isinstance(scenario, BaselineScenario)
        assert scenario.name == "French Carbon Tax 2026"

    def test_golden_carbon_tax_structure(self, golden_path: Path) -> None:
        """Golden carbon tax has expected structure."""
        scenario = load_scenario_template(golden_path)
        assert scenario.policy_type == PolicyType.CARBON_TAX
        assert scenario.year_schedule.start_year == 2026
        assert scenario.year_schedule.end_year == 2036
        assert scenario.year_schedule.duration == 11

    def test_golden_carbon_tax_parameters(self, golden_path: Path) -> None:
        """Golden carbon tax has expected parameters."""
        scenario = load_scenario_template(golden_path)
        assert isinstance(scenario.policy, CarbonTaxParameters)
        assert scenario.policy.rate_schedule[2026] == 44.60
        assert scenario.policy.rate_schedule[2036] == 100.00
        assert len(scenario.policy.exemptions) == 2
        assert len(scenario.policy.covered_categories) == 3

    def test_golden_carbon_tax_round_trip(
        self, golden_path: Path, tmp_path: Path
    ) -> None:
        """Golden carbon tax survives round-trip serialization."""
        original = load_scenario_template(golden_path)
        output_path = tmp_path / "roundtrip.yaml"
        dump_scenario_template(original, output_path)

        reloaded = load_scenario_template(output_path)
        assert reloaded.name == original.name
        assert reloaded.policy_type == original.policy_type
        assert reloaded.year_schedule.start_year == original.year_schedule.start_year
        assert reloaded.policy.rate_schedule == original.policy.rate_schedule


class TestGoldenReform:
    """Golden file tests for reform scenario."""

    @pytest.fixture()
    def golden_baseline_path(self) -> Path:
        return FIXTURES_DIR / "golden-carbon-tax.yaml"

    @pytest.fixture()
    def golden_reform_path(self) -> Path:
        return FIXTURES_DIR / "golden-reform.yaml"

    def test_load_golden_reform(self, golden_reform_path: Path) -> None:
        """Golden reform file loads successfully."""
        scenario = load_scenario_template(golden_reform_path)
        assert isinstance(scenario, ReformScenario)
        assert scenario.name == "Progressive Carbon Dividend Reform"

    def test_golden_reform_baseline_ref(self, golden_reform_path: Path) -> None:
        """Golden reform has correct baseline reference."""
        scenario = load_scenario_template(golden_reform_path)
        assert scenario.baseline_ref == "french-carbon-tax-2026"

    def test_golden_reform_parameters(self, golden_reform_path: Path) -> None:
        """Golden reform has carbon-tax redistribution overrides loaded."""
        scenario = load_scenario_template(golden_reform_path)
        assert isinstance(scenario.policy, CarbonTaxParameters)
        assert scenario.policy.redistribution_type == "progressive_dividend"
        assert scenario.policy.income_weights["decile_1"] == 1.5

    def test_golden_reform_resolution(
        self, golden_baseline_path: Path, golden_reform_path: Path
    ) -> None:
        """Golden reform can be resolved against golden baseline."""
        baseline = load_scenario_template(golden_baseline_path)
        assert isinstance(baseline, BaselineScenario)

        reform = load_scenario_template(golden_reform_path)
        assert isinstance(reform, ReformScenario)

        resolved = resolve_reform_definition(reform, baseline)
        assert isinstance(resolved, BaselineScenario)
        assert resolved.name == reform.name
        # Inherits year_schedule from baseline
        assert resolved.year_schedule.start_year == 2026
        assert resolved.year_schedule.end_year == 2036
        # Inherits rate_schedule from baseline
        assert resolved.policy.rate_schedule[2026] == 44.60
        # Keeps reform redistribution overrides
        assert isinstance(resolved.policy, CarbonTaxParameters)
        assert resolved.policy.redistribution_type == "progressive_dividend"
        assert resolved.policy.income_weights["decile_10"] == 0.2


class TestEdgeCases:
    """Edge case tests for comprehensive coverage."""

    def test_subsidy_scenario(self, tmp_path: Path) -> None:
        """Subsidy policy type with specific parameters."""
        import textwrap

        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Electric Vehicle Subsidy"
            policy_type: subsidy
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              rate_schedule:
                2026: 5000.0
                2027: 4500.0
              eligible_categories:
                - "electric_vehicle"
                - "heat_pump"
              income_caps:
                2026: 50000.0
                2027: 48000.0
        """)
        p = tmp_path / "subsidy.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert scenario.policy_type == PolicyType.SUBSIDY
        from reformlab.templates.schema import SubsidyParameters

        assert isinstance(scenario.policy, SubsidyParameters)
        assert "electric_vehicle" in scenario.policy.eligible_categories
        assert scenario.policy.income_caps[2026] == 50000.0

    def test_feebate_scenario(self, tmp_path: Path) -> None:
        """Feebate policy type with specific parameters."""
        import textwrap

        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Vehicle Feebate"
            policy_type: feebate
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              rate_schedule:
                2026: 100.0
              pivot_point: 150.0
              fee_rate: 0.01
              rebate_rate: 0.02
        """)
        p = tmp_path / "feebate.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert scenario.policy_type == PolicyType.FEEBATE
        from reformlab.templates.schema import FeebateParameters

        assert isinstance(scenario.policy, FeebateParameters)
        assert scenario.policy.pivot_point == 150.0
        assert scenario.policy.fee_rate == 0.01
        assert scenario.policy.rebate_rate == 0.02

    def test_rebate_scenario(self, tmp_path: Path) -> None:
        """Rebate policy type with specific parameters."""
        import textwrap

        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Flat Dividend"
            policy_type: rebate
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              rate_schedule:
                2026: 500.0
              rebate_type: "flat_dividend"
              income_weights:
                decile_1: 1.0
                decile_10: 1.0
        """)
        p = tmp_path / "rebate.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert scenario.policy_type == PolicyType.REBATE

        assert isinstance(scenario.policy, RebateParameters)
        assert scenario.policy.rebate_type == "flat_dividend"
        assert scenario.policy.income_weights["decile_1"] == 1.0

    def test_empty_parameters(self, tmp_path: Path) -> None:
        """Scenario with empty parameters section is rejected."""
        import textwrap

        from reformlab.templates.exceptions import ScenarioError

        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Minimal Scenario"
            policy_type: carbon_tax
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy: {}
        """)
        p = tmp_path / "empty-params.yaml"
        p.write_text(content, encoding="utf-8")

        with pytest.raises(ScenarioError, match="policy"):
            load_scenario_template(p)

    def test_minimal_valid_scenario(self, tmp_path: Path) -> None:
        """Minimal scenario with empty parameters is invalid."""
        import textwrap

        from reformlab.templates.exceptions import ScenarioError

        content = textwrap.dedent("""\
            version: "1.0"
            name: "Minimal"
            policy_type: carbon_tax
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy: {}
        """)
        p = tmp_path / "minimal.yaml"
        p.write_text(content, encoding="utf-8")

        with pytest.raises(ScenarioError, match="policy"):
            load_scenario_template(p)
