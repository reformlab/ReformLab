from __future__ import annotations

from typing import Any

import pytest

from reformlab.templates.exceptions import TemplateError
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    ReformScenario,
    ScenarioTemplate,
    SubsidyParameters,
    YearSchedule,
    infer_policy_type,
)

# ---------------------------------------------------------------------------
# Task 1 tests: Core schema dataclasses (AC #1, #5)
# ---------------------------------------------------------------------------


class TestYearSchedule:
    """Tests for the YearSchedule frozen dataclass (Subtask 1.2)."""

    def test_create_valid_year_schedule(self) -> None:
        """Given valid args, when created, then all fields set."""
        ys = YearSchedule(start_year=2026, end_year=2036)
        assert ys.start_year == 2026
        assert ys.end_year == 2036

    def test_year_schedule_is_frozen(self) -> None:
        """Given a YearSchedule, when modifying, then raises."""
        ys = YearSchedule(start_year=2026, end_year=2036)
        with pytest.raises(AttributeError):
            ys.start_year = 2027  # type: ignore[misc]

    def test_year_schedule_duration(self) -> None:
        """Year schedule returns correct duration in years."""
        ys = YearSchedule(start_year=2026, end_year=2036)
        assert ys.duration == 11  # inclusive of both start and end

    def test_year_schedule_years_property(self) -> None:
        """Year schedule returns list of all years."""
        ys = YearSchedule(start_year=2026, end_year=2028)
        assert ys.years == (2026, 2027, 2028)

    def test_year_schedule_contains_year(self) -> None:
        """Year schedule supports 'in' operator for checking year inclusion."""
        ys = YearSchedule(start_year=2026, end_year=2036)
        assert 2030 in ys
        assert 2025 not in ys
        assert 2037 not in ys

    def test_year_schedule_invalid_range_raises(self) -> None:
        """Given start_year > end_year, when created, then raises."""
        with pytest.raises(ValueError, match="start_year.*end_year"):
            YearSchedule(start_year=2036, end_year=2026)


class TestPolicyParameters:
    """Tests for the PolicyParameters base dataclass (Subtask 1.3)."""

    def test_create_policy_parameters(self) -> None:
        """Given valid args, when created, then all fields set."""
        params = PolicyParameters(
            rate_schedule={2026: 44.60, 2027: 50.00},
            exemptions=({"category": "test", "rate_reduction": 0.5},),
        )
        assert params.rate_schedule[2026] == 44.60
        assert len(params.exemptions) == 1

    def test_policy_parameters_is_frozen(self) -> None:
        """Given a PolicyParameters, when modifying, then raises."""
        params = PolicyParameters(rate_schedule={})
        with pytest.raises(AttributeError):
            params.rate_schedule = {}  # type: ignore[misc]

    def test_policy_parameters_defaults(self) -> None:
        """PolicyParameters has sensible defaults."""
        params = PolicyParameters(rate_schedule={})
        assert params.exemptions == ()
        assert params.covered_categories == ()
        assert params.thresholds == ()


class TestCarbonTaxParameters:
    """Tests for the CarbonTaxParameters dataclass (Subtask 1.4)."""

    def test_create_carbon_tax_parameters(
        self, sample_carbon_tax_params_dict: dict[str, Any]
    ) -> None:
        """Given valid args, when created, then all fields set."""
        params = CarbonTaxParameters(
            rate_schedule=sample_carbon_tax_params_dict["rate_schedule"],
            exemptions=tuple(sample_carbon_tax_params_dict["exemptions"]),
            covered_categories=tuple(
                sample_carbon_tax_params_dict["covered_categories"]
            ),
        )
        assert params.rate_schedule[2026] == 44.60
        assert len(params.exemptions) == 2
        assert "transport_fuel" in params.covered_categories

    def test_carbon_tax_inherits_policy_parameters(self) -> None:
        """CarbonTaxParameters is a PolicyParameters subclass."""
        params = CarbonTaxParameters(rate_schedule={2026: 44.60})
        assert isinstance(params, PolicyParameters)

    def test_carbon_tax_with_redistribution_fields(self) -> None:
        """CarbonTaxParameters supports redistribution type and income weights (AC-3)."""
        params = CarbonTaxParameters(
            rate_schedule={2026: 44.60},
            redistribution_type="progressive_dividend",
            income_weights={
                "decile_1": 1.5,
                "decile_2": 1.3,
                "decile_10": 0.2,
            },
        )
        assert params.redistribution_type == "progressive_dividend"
        assert params.income_weights["decile_1"] == 1.5
        assert params.income_weights["decile_10"] == 0.2

    def test_carbon_tax_redistribution_defaults_to_empty(self) -> None:
        """CarbonTaxParameters redistribution fields default to empty values."""
        params = CarbonTaxParameters(rate_schedule={2026: 44.60})
        assert params.redistribution_type == ""
        assert params.income_weights == {}

    def test_carbon_tax_lump_sum_redistribution(self) -> None:
        """CarbonTaxParameters supports lump_sum redistribution type."""
        params = CarbonTaxParameters(
            rate_schedule={2026: 44.60},
            redistribution_type="lump_sum",
        )
        assert params.redistribution_type == "lump_sum"
        # lump_sum doesn't need income_weights
        assert params.income_weights == {}


class TestSubsidyParameters:
    """Tests for the SubsidyParameters dataclass (Subtask 1.4)."""

    def test_create_subsidy_parameters(self) -> None:
        """Given valid args, when created, then all fields set."""
        params = SubsidyParameters(
            rate_schedule={2026: 1000.0},
            eligible_categories=("electric_vehicle", "heat_pump"),
            income_caps={2026: 50000.0},
        )
        assert params.rate_schedule[2026] == 1000.0
        assert "electric_vehicle" in params.eligible_categories
        assert params.income_caps[2026] == 50000.0

    def test_subsidy_parameters_defaults(self) -> None:
        """SubsidyParameters has sensible defaults."""
        params = SubsidyParameters(rate_schedule={})
        assert params.eligible_categories == ()
        assert params.income_caps == {}


class TestRebateParameters:
    """Tests for the RebateParameters dataclass (Subtask 1.4)."""

    def test_create_rebate_parameters(self) -> None:
        """Given valid args, when created, then all fields set."""
        params = RebateParameters(
            rate_schedule={2026: 500.0},
            rebate_type="lump_sum",
            income_weights={"decile_1": 1.5, "decile_10": 0.5},
        )
        assert params.rate_schedule[2026] == 500.0
        assert params.rebate_type == "lump_sum"
        assert params.income_weights["decile_1"] == 1.5

    def test_rebate_parameters_defaults(self) -> None:
        """RebateParameters has sensible defaults."""
        params = RebateParameters(rate_schedule={})
        assert params.rebate_type == ""
        assert params.income_weights == {}


class TestFeebateParameters:
    """Tests for the FeebateParameters dataclass (Subtask 1.4)."""

    def test_create_feebate_parameters(self) -> None:
        """Given valid args, when created, then all fields set."""
        params = FeebateParameters(
            rate_schedule={2026: 100.0},
            pivot_point=150.0,
            fee_rate=0.01,
            rebate_rate=0.02,
        )
        assert params.rate_schedule[2026] == 100.0
        assert params.pivot_point == 150.0
        assert params.fee_rate == 0.01
        assert params.rebate_rate == 0.02

    def test_feebate_parameters_defaults(self) -> None:
        """FeebateParameters has sensible defaults."""
        params = FeebateParameters(rate_schedule={})
        assert params.pivot_point == 0.0
        assert params.fee_rate == 0.0
        assert params.rebate_rate == 0.0


class TestBaselineScenario:
    """Tests for the BaselineScenario dataclass (Subtask 1.5)."""

    def test_create_baseline_scenario(self) -> None:
        """Given valid args, when created, then all fields set."""
        year_schedule = YearSchedule(start_year=2026, end_year=2036)
        params = CarbonTaxParameters(rate_schedule={2026: 44.60})
        scenario = BaselineScenario(
            name="French Carbon Tax 2026",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=year_schedule,
            policy=params,
            description="Baseline scenario",
            version="1.0",
        )
        assert scenario.name == "French Carbon Tax 2026"
        assert scenario.policy_type == PolicyType.CARBON_TAX
        assert scenario.year_schedule.start_year == 2026
        assert scenario.description == "Baseline scenario"
        assert scenario.version == "1.0"

    def test_baseline_scenario_is_frozen(self) -> None:
        """Given a BaselineScenario, when modifying, then raises."""
        scenario = BaselineScenario(
            name="test",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2026, 2036),
            policy=CarbonTaxParameters(rate_schedule={}),
        )
        with pytest.raises(AttributeError):
            scenario.name = "modified"  # type: ignore[misc]

    def test_baseline_scenario_defaults(self) -> None:
        """BaselineScenario has sensible defaults."""
        scenario = BaselineScenario(
            name="test",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2026, 2036),
            policy=CarbonTaxParameters(rate_schedule={}),
        )
        assert scenario.description == ""
        assert scenario.version == "1.0"

    def test_baseline_is_scenario_template(self) -> None:
        """BaselineScenario subclasses ScenarioTemplate."""
        scenario = BaselineScenario(
            name="test",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2026, 2036),
            policy=CarbonTaxParameters(rate_schedule={}),
        )
        assert isinstance(scenario, ScenarioTemplate)


class TestReformScenario:
    """Tests for the ReformScenario dataclass (Subtask 1.5)."""

    def test_create_reform_scenario(self) -> None:
        """Given valid args, when created, then all fields set."""
        params = RebateParameters(
            rate_schedule={},
            rebate_type="progressive_dividend",
            income_weights={"decile_1": 1.5},
        )
        scenario = ReformScenario(
            name="Progressive Carbon Dividend Reform",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="french-carbon-tax-2026",
            policy=params,
            description="Reform with progressive redistribution",
            version="1.0",
        )
        assert scenario.name == "Progressive Carbon Dividend Reform"
        assert scenario.baseline_ref == "french-carbon-tax-2026"
        assert scenario.year_schedule is None  # Inherited from baseline

    def test_reform_scenario_is_frozen(self) -> None:
        """Given a ReformScenario, when modifying, then raises."""
        scenario = ReformScenario(
            name="test",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="baseline",
            policy=RebateParameters(rate_schedule={}),
        )
        with pytest.raises(AttributeError):
            scenario.baseline_ref = "other"  # type: ignore[misc]

    def test_reform_scenario_requires_baseline_ref(self) -> None:
        """ReformScenario requires baseline_ref to be non-empty."""
        with pytest.raises(ValueError, match="baseline_ref"):
            ReformScenario(
                name="test",
                policy_type=PolicyType.CARBON_TAX,
                baseline_ref="",  # Empty string not allowed
                policy=RebateParameters(rate_schedule={}),
            )

    def test_reform_with_year_schedule_override(self) -> None:
        """ReformScenario can optionally override year_schedule."""
        year_schedule = YearSchedule(start_year=2028, end_year=2038)
        scenario = ReformScenario(
            name="test",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="baseline",
            policy=RebateParameters(rate_schedule={}),
            year_schedule=year_schedule,
        )
        assert scenario.year_schedule is not None
        assert scenario.year_schedule.start_year == 2028


class TestPolicyType:
    """Tests for the PolicyType enum."""

    def test_policy_type_values(self) -> None:
        """All required policy types are defined."""
        assert PolicyType.CARBON_TAX.value == "carbon_tax"
        assert PolicyType.SUBSIDY.value == "subsidy"
        assert PolicyType.REBATE.value == "rebate"
        assert PolicyType.FEEBATE.value == "feebate"

    def test_policy_type_from_string(self) -> None:
        """Policy type can be created from string."""
        assert PolicyType("carbon_tax") == PolicyType.CARBON_TAX
        assert PolicyType("subsidy") == PolicyType.SUBSIDY


# ---------------------------------------------------------------------------
# Story 10.2 tests: Policy type inference (AC #1, #2, #3, #4)
# ---------------------------------------------------------------------------


class TestInferPolicyType:
    """Tests for infer_policy_type() function (Story 10.2, Task 6)."""

    def test_infer_carbon_tax(self) -> None:
        """AC#2: CarbonTaxParameters infers PolicyType.CARBON_TAX."""
        params = CarbonTaxParameters(rate_schedule={2026: 44.60})
        assert infer_policy_type(params) == PolicyType.CARBON_TAX

    def test_infer_subsidy(self) -> None:
        """AC#2: SubsidyParameters infers PolicyType.SUBSIDY."""
        params = SubsidyParameters(rate_schedule={})
        assert infer_policy_type(params) == PolicyType.SUBSIDY

    def test_infer_rebate(self) -> None:
        """AC#2: RebateParameters infers PolicyType.REBATE."""
        params = RebateParameters(rate_schedule={})
        assert infer_policy_type(params) == PolicyType.REBATE

    def test_infer_feebate(self) -> None:
        """AC#2: FeebateParameters infers PolicyType.FEEBATE."""
        params = FeebateParameters(rate_schedule={})
        assert infer_policy_type(params) == PolicyType.FEEBATE

    def test_infer_base_policy_parameters_raises(self) -> None:
        """AC#3: Base PolicyParameters raises TemplateError with guidance."""
        params = PolicyParameters(rate_schedule={})
        with pytest.raises(TemplateError, match="Cannot infer PolicyType"):
            infer_policy_type(params)

    def test_infer_error_includes_registration_guidance(self) -> None:
        """AC#3: Error message explains how to register the mapping."""
        params = PolicyParameters(rate_schedule={})
        with pytest.raises(TemplateError, match="register_custom_template"):
            infer_policy_type(params)


class TestBaselineScenarioInference:
    """Tests for BaselineScenario policy_type inference (Story 10.2)."""

    def test_baseline_infers_policy_type(self) -> None:
        """AC#1: BaselineScenario without policy_type infers from policy."""
        scenario = BaselineScenario(
            name="test",
            year_schedule=YearSchedule(2026, 2036),
            policy=CarbonTaxParameters(rate_schedule={2026: 44.60}),
        )
        assert scenario.policy_type == PolicyType.CARBON_TAX

    def test_baseline_explicit_policy_type_still_works(self) -> None:
        """Existing callers with explicit policy_type still work."""
        scenario = BaselineScenario(
            name="test",
            policy_type=PolicyType.CARBON_TAX,
            year_schedule=YearSchedule(2026, 2036),
            policy=CarbonTaxParameters(rate_schedule={}),
        )
        assert scenario.policy_type == PolicyType.CARBON_TAX

    def test_baseline_mismatch_uses_explicit_with_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """AC#4: Explicit policy_type overrides inferred type, with warning."""
        import logging

        with caplog.at_level(logging.WARNING):
            scenario = BaselineScenario(
                name="test",
                policy_type=PolicyType.SUBSIDY,
                year_schedule=YearSchedule(2026, 2036),
                policy=CarbonTaxParameters(rate_schedule={}),
            )
        assert scenario.policy_type == PolicyType.SUBSIDY
        assert "does not match inferred type" in caplog.text


class TestReformScenarioInference:
    """Tests for ReformScenario policy_type inference (Story 10.2)."""

    def test_reform_infers_policy_type(self) -> None:
        """AC#1: ReformScenario without policy_type infers from policy."""
        scenario = ReformScenario(
            name="test",
            baseline_ref="baseline",
            policy=RebateParameters(rate_schedule={}),
        )
        assert scenario.policy_type == PolicyType.REBATE

    def test_reform_explicit_policy_type_still_works(self) -> None:
        """Existing callers with explicit policy_type still work."""
        scenario = ReformScenario(
            name="test",
            policy_type=PolicyType.CARBON_TAX,
            baseline_ref="baseline",
            policy=RebateParameters(rate_schedule={}),
        )
        assert scenario.policy_type == PolicyType.CARBON_TAX

    def test_reform_mismatch_uses_explicit_with_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """AC#4: Explicit policy_type overrides inferred type, with warning."""
        import logging

        with caplog.at_level(logging.WARNING):
            scenario = ReformScenario(
                name="test",
                policy_type=PolicyType.SUBSIDY,
                baseline_ref="baseline",
                policy=FeebateParameters(rate_schedule={}),
            )
        assert scenario.policy_type == PolicyType.SUBSIDY
        assert "does not match inferred type" in caplog.text


class TestServerCreateScenarioInference:
    """Tests for CreateScenarioRequest with policy_type=None (Story 10.2, Task 6.6)."""

    def test_create_scenario_request_policy_type_optional(self) -> None:
        """AC#1: CreateScenarioRequest accepts policy_type=None."""
        from reformlab.server.models import CreateScenarioRequest

        request = CreateScenarioRequest(
            name="test",
            policy={"rate_schedule": {2026: 44.60}},
            start_year=2026,
            end_year=2036,
        )
        assert request.policy_type is None

    def test_create_scenario_request_with_explicit_policy_type(self) -> None:
        """CreateScenarioRequest still accepts explicit policy_type."""
        from reformlab.server.models import CreateScenarioRequest

        request = CreateScenarioRequest(
            name="test",
            policy_type="carbon_tax",
            policy={"rate_schedule": {2026: 44.60}},
            start_year=2026,
            end_year=2036,
        )
        assert request.policy_type == "carbon_tax"
