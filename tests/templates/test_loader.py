from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from reformlab.templates.exceptions import ScenarioError
from reformlab.templates.loader import (
    dump_scenario_template,
    load_scenario_template,
)
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    PolicyType,
    ReformScenario,
    YearSchedule,
)

# ---------------------------------------------------------------------------
# Task 2 tests: YAML schema loader with validation (AC #1, #3)
# ---------------------------------------------------------------------------


class TestLoadScenarioTemplate:
    """Tests for load_scenario_template function (Subtask 2.1)."""

    def test_load_valid_baseline_scenario(self, valid_carbon_tax_yaml: Path) -> None:
        """Valid YAML loads into BaselineScenario with correct fields."""
        scenario = load_scenario_template(valid_carbon_tax_yaml)
        assert isinstance(scenario, BaselineScenario)
        assert scenario.name == "French Carbon Tax 2026"
        assert scenario.policy_type == PolicyType.CARBON_TAX
        assert scenario.year_schedule.start_year == 2026
        assert scenario.year_schedule.end_year == 2036
        assert isinstance(scenario.policy, CarbonTaxParameters)
        assert scenario.policy.rate_schedule[2026] == 44.60

    def test_load_valid_reform_scenario(self, valid_reform_yaml: Path) -> None:
        """Valid reform YAML loads into ReformScenario with baseline_ref."""
        scenario = load_scenario_template(valid_reform_yaml)
        assert isinstance(scenario, ReformScenario)
        assert scenario.name == "Progressive Carbon Dividend Reform"
        assert scenario.baseline_ref == "french-carbon-tax-2026"
        assert scenario.policy_type == PolicyType.CARBON_TAX

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Nonexistent file raises ScenarioError."""
        p = tmp_path / "does_not_exist.yaml"
        with pytest.raises(ScenarioError) as exc_info:
            load_scenario_template(p)
        assert "file was not found" in str(exc_info.value)

    def test_load_invalid_yaml_syntax(self, tmp_path: Path) -> None:
        """Invalid YAML syntax raises ScenarioError."""
        p = tmp_path / "bad.yaml"
        p.write_text("{{invalid: yaml: [", encoding="utf-8")
        with pytest.raises(ScenarioError) as exc_info:
            load_scenario_template(p)
        assert "YAML syntax" in str(exc_info.value)


class TestScenarioError:
    """Tests for ScenarioError exception (Subtask 2.2)."""

    def test_scenario_error_attributes(self) -> None:
        """Structured fields are accessible on ScenarioError."""
        err = ScenarioError(
            file_path=Path("test.yaml"),
            summary="Schema validation failed",
            reason="missing required field: policy_type",
            fix="Add 'policy_type' field with one of: carbon_tax, subsidy, rebate, feebate",
            invalid_fields=("policy_type",),
        )
        assert err.file_path == Path("test.yaml")
        assert "Schema validation failed" in str(err)
        assert "policy_type" in str(err)
        assert err.invalid_fields == ("policy_type",)

    def test_scenario_error_message_format(self) -> None:
        """Message follows standard format: summary - reason - fix (file)."""
        err = ScenarioError(
            file_path=Path("bad.yaml"),
            summary="Load failed",
            reason="invalid structure",
            fix="Fix the structure",
        )
        msg = str(err)
        assert "Load failed" in msg
        assert "invalid structure" in msg
        assert "Fix the structure" in msg
        assert "bad.yaml" in msg


class TestRequiredFieldValidation:
    """Tests for required field validation (Subtask 2.3)."""

    def test_missing_required_field_error(
        self, missing_required_field_yaml: Path
    ) -> None:
        """Missing required field raises ScenarioError with field name."""
        with pytest.raises(ScenarioError) as exc_info:
            load_scenario_template(missing_required_field_yaml)
        err = exc_info.value
        assert "policy_type" in str(err)
        assert "missing" in str(err).lower()

    def test_missing_version_field(self, tmp_path: Path) -> None:
        """Missing version field raises ScenarioError."""
        content = textwrap.dedent("""\
            name: "Test"
            policy_type: carbon_tax
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy: {}
        """)
        p = tmp_path / "no-version.yaml"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(ScenarioError) as exc_info:
            load_scenario_template(p)
        assert "version" in str(exc_info.value)

    def test_empty_policy_raises(self, tmp_path: Path) -> None:
        """Empty policy mapping raises ScenarioError."""
        content = textwrap.dedent("""\
            version: "1.0"
            name: "Empty Params"
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

    def test_policy_must_be_mapping(self, tmp_path: Path) -> None:
        """Non-mapping policy raises ScenarioError."""
        content = textwrap.dedent("""\
            version: "1.0"
            name: "Bad Params"
            policy_type: carbon_tax
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              - nope
        """)
        p = tmp_path / "bad-params.yaml"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(ScenarioError, match="policy"):
            load_scenario_template(p)


class TestTypeCoercion:
    """Tests for type coercion (Subtask 2.4)."""

    def test_year_coercion_from_string(self, tmp_path: Path) -> None:
        """Year values as strings are coerced to int."""
        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Test"
            policy_type: carbon_tax
            year_schedule:
              start_year: "2026"
              end_year: "2036"
            policy:
              rate_schedule:
                "2026": 44.60
        """)
        p = tmp_path / "string-years.yaml"
        p.write_text(content, encoding="utf-8")
        scenario = load_scenario_template(p)
        assert scenario.year_schedule.start_year == 2026
        assert 2026 in scenario.policy.rate_schedule


class TestYearScheduleValidation:
    """Tests for year schedule validation (Subtask 2.5)."""

    def test_short_year_schedule_warning(
        self, short_year_schedule_yaml: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Year schedule < 10 years emits warning by default."""
        caplog.set_level("WARNING")
        scenario = load_scenario_template(short_year_schedule_yaml)
        assert scenario.year_schedule.duration < 10
        logs = " ".join(record.getMessage() for record in caplog.records)
        assert "10 years" in logs or "year schedule" in logs.lower()

    def test_short_year_schedule_strict_error(
        self, short_year_schedule_yaml: Path
    ) -> None:
        """Year schedule < 10 years raises error in strict mode."""
        with pytest.raises(ScenarioError) as exc_info:
            load_scenario_template(short_year_schedule_yaml, strict=True)
        assert (
            "10 years" in str(exc_info.value)
            or "year schedule" in str(exc_info.value).lower()
        )


class TestInvalidPolicyType:
    """Tests for invalid policy type validation."""

    def test_unknown_policy_type_error(self, invalid_policy_type_yaml: Path) -> None:
        """Unknown policy type raises error listing valid types."""
        with pytest.raises(ScenarioError) as exc_info:
            load_scenario_template(invalid_policy_type_yaml)
        err_msg = str(exc_info.value)
        assert "unknown_policy" in err_msg
        assert "carbon_tax" in err_msg
        assert "subsidy" in err_msg

    def test_schema_version_major_mismatch_strict(self, tmp_path: Path) -> None:
        """Major schema version mismatch raises in strict mode."""
        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "2.0"
            name: "Wrong Version"
            policy_type: carbon_tax
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              rate_schedule:
                2026: 44.6
        """)
        p = tmp_path / "wrong-version.yaml"
        p.write_text(content, encoding="utf-8")
        with pytest.raises(ScenarioError, match="version"):
            load_scenario_template(p, strict=True)


class TestDumpScenarioTemplate:
    """Tests for dump_scenario_template serializer (Subtask 2.6)."""

    def test_dump_baseline_scenario(self, tmp_path: Path) -> None:
        """Baseline scenario can be serialized to YAML."""
        scenario = BaselineScenario(
            name="Test Carbon Tax",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2026, 2036),
            policy=CarbonTaxParameters(
                rate_schedule={2026: 44.60, 2027: 50.00},
                covered_categories=("transport_fuel",),
            ),
            description="Test scenario",
            version="1.0",
        )
        output_path = tmp_path / "output.yaml"
        dump_scenario_template(scenario, output_path)
        assert output_path.exists()
        content = output_path.read_text()
        assert "Test Carbon Tax" in content
        assert "carbon_tax" in content

    def test_round_trip_baseline(self, tmp_path: Path) -> None:
        """Load → save → load preserves all data (AC-5)."""
        scenario = BaselineScenario(
            name="Round Trip Test",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2026, 2036),
            policy=CarbonTaxParameters(
                rate_schedule={
                    2026: 44.60,
                    2027: 50.00,
                    2028: 55.00,
                    2029: 60.00,
                    2030: 65.00,
                    2031: 70.00,
                    2032: 75.00,
                    2033: 80.00,
                    2034: 85.00,
                    2035: 90.00,
                    2036: 100.00,
                },
                exemptions=({"category": "test", "rate_reduction": 0.5},),
                covered_categories=("transport_fuel", "heating_fuel"),
            ),
            description="Test round trip",
            version="1.0",
        )
        output_path = tmp_path / "roundtrip.yaml"
        dump_scenario_template(scenario, output_path)

        loaded = load_scenario_template(output_path)
        assert isinstance(loaded, BaselineScenario)
        assert loaded.name == scenario.name
        assert loaded.policy_type == scenario.policy_type
        assert loaded.year_schedule.start_year == scenario.year_schedule.start_year
        assert loaded.policy.rate_schedule == scenario.policy.rate_schedule
        assert loaded.policy.exemptions == scenario.policy.exemptions
        assert (
            loaded.policy.covered_categories
            == scenario.policy.covered_categories
        )

    def test_round_trip_reform(self, tmp_path: Path) -> None:
        """Load → save → load preserves reform scenario data (AC-5)."""
        from reformlab.templates.schema import RebateParameters

        scenario = ReformScenario(
            name="Reform Round Trip",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="test-baseline",
            policy=RebateParameters(
                rate_schedule={2026: 500.0},
                rebate_type="progressive_dividend",
                income_weights={"decile_1": 1.5, "decile_10": 0.5},
            ),
            description="Reform test",
            version="1.0",
        )
        output_path = tmp_path / "reform-roundtrip.yaml"
        dump_scenario_template(scenario, output_path)

        loaded = load_scenario_template(output_path)
        assert isinstance(loaded, ReformScenario)
        assert loaded.name == scenario.name
        assert loaded.baseline_ref == scenario.baseline_ref
        assert loaded.policy.rate_schedule == scenario.policy.rate_schedule


class TestCarbonTaxRedistributionLoading:
    """Tests for loading carbon tax templates with redistribution fields (Story 2.2)."""

    def test_load_carbon_tax_with_lump_sum_redistribution(self, tmp_path: Path) -> None:
        """Carbon tax template with lump_sum redistribution loads correctly."""
        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Carbon Tax with Lump Sum Dividend"
            policy_type: carbon_tax
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              rate_schedule:
                2026: 44.60
                2027: 50.00
                2028: 55.00
                2029: 60.00
                2030: 65.00
                2031: 70.00
                2032: 75.00
                2033: 80.00
                2034: 85.00
                2035: 90.00
                2036: 100.00
              covered_categories:
                - transport_fuel
                - heating_fuel
              redistribution:
                type: lump_sum
        """)
        p = tmp_path / "carbon-tax-lump-sum.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.policy, CarbonTaxParameters)
        assert scenario.policy.redistribution_type == "lump_sum"
        assert scenario.policy.income_weights == {}

    def test_load_carbon_tax_with_progressive_dividend(self, tmp_path: Path) -> None:
        """Carbon tax template with progressive_dividend redistribution loads correctly."""
        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Carbon Tax with Progressive Dividend"
            policy_type: carbon_tax
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              rate_schedule:
                2026: 44.60
                2027: 50.00
                2028: 55.00
                2029: 60.00
                2030: 65.00
                2031: 70.00
                2032: 75.00
                2033: 80.00
                2034: 85.00
                2035: 90.00
                2036: 100.00
              covered_categories:
                - transport_fuel
                - heating_fuel
              redistribution:
                type: progressive_dividend
                income_weights:
                  decile_1: 1.5
                  decile_2: 1.3
                  decile_3: 1.1
                  decile_4: 1.0
                  decile_5: 1.0
                  decile_6: 0.9
                  decile_7: 0.8
                  decile_8: 0.7
                  decile_9: 0.5
                  decile_10: 0.2
        """)
        p = tmp_path / "carbon-tax-progressive.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.policy, CarbonTaxParameters)
        assert scenario.policy.redistribution_type == "progressive_dividend"
        assert scenario.policy.income_weights["decile_1"] == 1.5
        assert scenario.policy.income_weights["decile_10"] == 0.2

    def test_load_carbon_tax_no_redistribution(
        self, valid_carbon_tax_yaml: Path
    ) -> None:
        """Carbon tax template without redistribution defaults to empty values."""
        scenario = load_scenario_template(valid_carbon_tax_yaml)
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.policy, CarbonTaxParameters)
        assert scenario.policy.redistribution_type == ""
        assert scenario.policy.income_weights == {}

    def test_round_trip_carbon_tax_with_redistribution(self, tmp_path: Path) -> None:
        """Carbon tax with redistribution can round-trip through dump/load."""
        scenario = BaselineScenario(
            name="Carbon Tax Progressive",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2026, 2036),
            policy=CarbonTaxParameters(
                rate_schedule={
                    2026: 44.60,
                    2027: 50.00,
                    2028: 55.00,
                    2029: 60.00,
                    2030: 65.00,
                    2031: 70.00,
                    2032: 75.00,
                    2033: 80.00,
                    2034: 85.00,
                    2035: 90.00,
                    2036: 100.00,
                },
                covered_categories=("transport_fuel", "heating_fuel"),
                redistribution_type="progressive_dividend",
                income_weights={"decile_1": 1.5, "decile_10": 0.2},
            ),
            description="Test carbon tax with redistribution",
            version="1.0",
        )
        output_path = tmp_path / "roundtrip-redist.yaml"
        dump_scenario_template(scenario, output_path)

        loaded = load_scenario_template(output_path)
        assert isinstance(loaded, BaselineScenario)
        assert isinstance(loaded.policy, CarbonTaxParameters)
        assert loaded.policy.redistribution_type == "progressive_dividend"
        assert loaded.policy.income_weights == {"decile_1": 1.5, "decile_10": 0.2}


class TestSubsidyParameterLoading:
    """Tests for loading subsidy templates (Story 2.3)."""

    def test_load_subsidy_with_eligible_categories_and_income_caps(
        self, tmp_path: Path
    ) -> None:
        """Subsidy template with eligible_categories and income_caps loads correctly."""
        from reformlab.templates.schema import SubsidyParameters

        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Energy Retrofit Subsidy"
            policy_type: subsidy
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              rate_schedule:
                2026: 5000.0
                2027: 4500.0
                2028: 4000.0
                2029: 3500.0
                2030: 3000.0
                2031: 2500.0
                2032: 2000.0
                2033: 1500.0
                2034: 1000.0
                2035: 500.0
                2036: 250.0
              eligible_categories:
                - owner_occupier
                - low_efficiency_home
              income_caps:
                2026: 45000.0
                2027: 42000.0
                2028: 40000.0
                2029: 38000.0
                2030: 36000.0
                2031: 35000.0
                2032: 34000.0
                2033: 33000.0
                2034: 32000.0
                2035: 31000.0
                2036: 30000.0
        """)
        p = tmp_path / "subsidy-retrofit.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.policy, SubsidyParameters)
        assert scenario.policy.eligible_categories == (
            "owner_occupier",
            "low_efficiency_home",
        )
        assert scenario.policy.income_caps[2026] == 45000.0
        assert scenario.policy.income_caps[2027] == 42000.0
        assert scenario.policy.rate_schedule[2026] == 5000.0

    def test_load_subsidy_minimal(self, tmp_path: Path) -> None:
        """Subsidy template with minimal fields loads with defaults."""
        from reformlab.templates.schema import SubsidyParameters

        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Minimal Subsidy"
            policy_type: subsidy
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              rate_schedule:
                2026: 1000.0
                2027: 1000.0
                2028: 1000.0
                2029: 1000.0
                2030: 1000.0
                2031: 1000.0
                2032: 1000.0
                2033: 1000.0
                2034: 1000.0
                2035: 1000.0
                2036: 1000.0
        """)
        p = tmp_path / "subsidy-minimal.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert isinstance(scenario.policy, SubsidyParameters)
        assert scenario.policy.eligible_categories == ()
        assert scenario.policy.income_caps == {}


class TestRebateParameterLoading:
    """Tests for loading rebate templates (Story 2.3)."""

    def test_load_rebate_with_lump_sum(self, tmp_path: Path) -> None:
        """Rebate template with lump_sum type loads correctly."""
        from reformlab.templates.schema import RebateParameters

        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Lump Sum Rebate"
            policy_type: rebate
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              rate_schedule:
                2026: 100.0
                2027: 100.0
                2028: 100.0
                2029: 100.0
                2030: 100.0
                2031: 100.0
                2032: 100.0
                2033: 100.0
                2034: 100.0
                2035: 100.0
                2036: 100.0
              rebate_type: lump_sum
        """)
        p = tmp_path / "rebate-lump-sum.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.policy, RebateParameters)
        assert scenario.policy.rebate_type == "lump_sum"
        assert scenario.policy.income_weights == {}

    def test_load_rebate_with_progressive_dividend(self, tmp_path: Path) -> None:
        """Rebate template with progressive_dividend type and weights loads correctly."""
        from reformlab.templates.schema import RebateParameters

        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Progressive Rebate"
            policy_type: rebate
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              rate_schedule:
                2026: 100.0
                2027: 110.0
                2028: 120.0
                2029: 130.0
                2030: 140.0
                2031: 150.0
                2032: 160.0
                2033: 170.0
                2034: 180.0
                2035: 190.0
                2036: 200.0
              rebate_type: progressive_dividend
              income_weights:
                decile_1: 2.0
                decile_2: 1.8
                decile_3: 1.5
                decile_4: 1.3
                decile_5: 1.1
                decile_6: 0.9
                decile_7: 0.7
                decile_8: 0.5
                decile_9: 0.3
                decile_10: 0.2
        """)
        p = tmp_path / "rebate-progressive.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert isinstance(scenario.policy, RebateParameters)
        assert scenario.policy.rebate_type == "progressive_dividend"
        assert scenario.policy.income_weights["decile_1"] == 2.0
        assert scenario.policy.income_weights["decile_10"] == 0.2


class TestFeebateParameterLoading:
    """Tests for loading feebate templates (Story 2.3)."""

    def test_load_feebate_with_pivot_and_rates(self, tmp_path: Path) -> None:
        """Feebate template with pivot_point, fee_rate, rebate_rate loads correctly."""
        from reformlab.templates.schema import FeebateParameters

        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Vehicle Emissions Feebate"
            policy_type: feebate
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              pivot_point: 120.0
              fee_rate: 50.0
              rebate_rate: 50.0
              covered_categories:
                - passenger_vehicle
        """)
        p = tmp_path / "feebate-vehicle.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.policy, FeebateParameters)
        assert scenario.policy.pivot_point == 120.0
        assert scenario.policy.fee_rate == 50.0
        assert scenario.policy.rebate_rate == 50.0
        assert scenario.policy.covered_categories == ("passenger_vehicle",)

    def test_load_feebate_minimal_empty_policy_raises(self, tmp_path: Path) -> None:
        """Feebate template with empty policy is invalid."""
        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Minimal Feebate"
            policy_type: feebate
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy: {}
        """)
        p = tmp_path / "feebate-minimal.yaml"
        p.write_text(content, encoding="utf-8")

        with pytest.raises(ScenarioError, match="policy"):
            load_scenario_template(p)

    def test_load_feebate_asymmetric_rates(self, tmp_path: Path) -> None:
        """Feebate template with different fee and rebate rates loads correctly."""
        from reformlab.templates.schema import FeebateParameters

        content = textwrap.dedent("""\
            $schema: "./schema/scenario-template.schema.json"
            version: "1.0"
            name: "Asymmetric Feebate"
            policy_type: feebate
            year_schedule:
              start_year: 2026
              end_year: 2036
            policy:
              pivot_point: 100.0
              fee_rate: 75.0
              rebate_rate: 25.0
        """)
        p = tmp_path / "feebate-asymmetric.yaml"
        p.write_text(content, encoding="utf-8")

        scenario = load_scenario_template(p)
        assert isinstance(scenario.policy, FeebateParameters)
        assert scenario.policy.fee_rate == 75.0
        assert scenario.policy.rebate_rate == 25.0
