"""Integration tests for subsidy, rebate, and feebate template pack loaders.

These tests verify that shipped template packs load correctly and meet AC-1, AC-6.
"""

from __future__ import annotations

import pytest

from reformlab.templates.loader import load_scenario_template
from reformlab.templates.packs import (
    get_feebate_pack_dir,
    get_rebate_pack_dir,
    get_subsidy_pack_dir,
    list_feebate_templates,
    list_rebate_templates,
    list_subsidy_templates,
    load_feebate_template,
    load_rebate_template,
    load_subsidy_template,
)
from reformlab.templates.schema import (
    BaselineScenario,
    FeebateParameters,
    PolicyType,
    RebateParameters,
    SubsidyParameters,
)


class TestSubsidyPackLoader:
    """Tests for subsidy template pack loading (AC-1, AC-6)."""

    def test_list_subsidy_templates_returns_at_least_one(self) -> None:
        """At least one subsidy template is available."""
        templates = list_subsidy_templates()
        assert len(templates) >= 1
        assert "subsidy-energy-retrofit" in templates

    def test_load_subsidy_template_returns_baseline_scenario(self) -> None:
        """Load returns BaselineScenario with SubsidyParameters."""
        scenario = load_subsidy_template("subsidy-energy-retrofit")
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.parameters, SubsidyParameters)
        assert scenario.policy_type == PolicyType.SUBSIDY

    def test_subsidy_template_has_10_year_schedule(self) -> None:
        """Subsidy template has at least 10 years (AC-1)."""
        scenario = load_subsidy_template("subsidy-energy-retrofit")
        assert scenario.year_schedule.duration >= 10

    def test_subsidy_template_has_required_fields(self) -> None:
        """Subsidy template has eligible_categories and income_caps."""
        scenario = load_subsidy_template("subsidy-energy-retrofit")
        params = scenario.parameters
        assert isinstance(params, SubsidyParameters)
        assert len(params.eligible_categories) > 0
        assert len(params.income_caps) > 0

    def test_load_nonexistent_subsidy_template_raises(self) -> None:
        """FileNotFoundError raised for missing template."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_subsidy_template("nonexistent-template")
        assert "not found" in str(exc_info.value)

    def test_get_subsidy_pack_dir_returns_existing_path(self) -> None:
        """Pack directory path exists."""
        pack_dir = get_subsidy_pack_dir()
        assert pack_dir.exists()
        assert pack_dir.is_dir()


class TestRebatePackLoader:
    """Tests for rebate template pack loading (AC-1, AC-6)."""

    def test_list_rebate_templates_returns_at_least_one(self) -> None:
        """At least one rebate template is available."""
        templates = list_rebate_templates()
        assert len(templates) >= 1
        assert "rebate-progressive-income" in templates

    def test_load_rebate_template_returns_baseline_scenario(self) -> None:
        """Load returns BaselineScenario with RebateParameters."""
        scenario = load_rebate_template("rebate-progressive-income")
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.parameters, RebateParameters)
        assert scenario.policy_type == PolicyType.REBATE

    def test_rebate_template_has_10_year_schedule(self) -> None:
        """Rebate template has at least 10 years (AC-1)."""
        scenario = load_rebate_template("rebate-progressive-income")
        assert scenario.year_schedule.duration >= 10

    def test_rebate_template_has_required_fields(self) -> None:
        """Rebate template has rebate_type and income_weights."""
        scenario = load_rebate_template("rebate-progressive-income")
        params = scenario.parameters
        assert isinstance(params, RebateParameters)
        assert params.rebate_type == "progressive_dividend"
        assert len(params.income_weights) > 0

    def test_load_nonexistent_rebate_template_raises(self) -> None:
        """FileNotFoundError raised for missing template."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_rebate_template("nonexistent-template")
        assert "not found" in str(exc_info.value)

    def test_get_rebate_pack_dir_returns_existing_path(self) -> None:
        """Pack directory path exists."""
        pack_dir = get_rebate_pack_dir()
        assert pack_dir.exists()
        assert pack_dir.is_dir()


class TestFeebatePackLoader:
    """Tests for feebate template pack loading (AC-1, AC-6)."""

    def test_list_feebate_templates_returns_at_least_one(self) -> None:
        """At least one feebate template is available."""
        templates = list_feebate_templates()
        assert len(templates) >= 1
        assert "feebate-vehicle-emissions" in templates

    def test_load_feebate_template_returns_baseline_scenario(self) -> None:
        """Load returns BaselineScenario with FeebateParameters."""
        scenario = load_feebate_template("feebate-vehicle-emissions")
        assert isinstance(scenario, BaselineScenario)
        assert isinstance(scenario.parameters, FeebateParameters)
        assert scenario.policy_type == PolicyType.FEEBATE

    def test_feebate_template_has_10_year_schedule(self) -> None:
        """Feebate template has at least 10 years (AC-1)."""
        scenario = load_feebate_template("feebate-vehicle-emissions")
        assert scenario.year_schedule.duration >= 10

    def test_feebate_template_has_required_fields(self) -> None:
        """Feebate template has pivot_point, fee_rate, rebate_rate."""
        scenario = load_feebate_template("feebate-vehicle-emissions")
        params = scenario.parameters
        assert isinstance(params, FeebateParameters)
        assert params.pivot_point > 0
        assert params.fee_rate > 0
        assert params.rebate_rate > 0

    def test_load_nonexistent_feebate_template_raises(self) -> None:
        """FileNotFoundError raised for missing template."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_feebate_template("nonexistent-template")
        assert "not found" in str(exc_info.value)

    def test_get_feebate_pack_dir_returns_existing_path(self) -> None:
        """Pack directory path exists."""
        pack_dir = get_feebate_pack_dir()
        assert pack_dir.exists()
        assert pack_dir.is_dir()


class TestAllTemplatesPassValidation:
    """All shipped templates pass load_scenario_template() validation (AC-1)."""

    def test_all_subsidy_templates_load(self) -> None:
        """All subsidy templates load without error."""
        pack_dir = get_subsidy_pack_dir()
        for yaml_file in pack_dir.glob("*.yaml"):
            scenario = load_scenario_template(yaml_file)
            assert isinstance(scenario, BaselineScenario)

    def test_all_rebate_templates_load(self) -> None:
        """All rebate templates load without error."""
        pack_dir = get_rebate_pack_dir()
        for yaml_file in pack_dir.glob("*.yaml"):
            scenario = load_scenario_template(yaml_file)
            assert isinstance(scenario, BaselineScenario)

    def test_all_feebate_templates_load(self) -> None:
        """All feebate templates load without error."""
        pack_dir = get_feebate_pack_dir()
        for yaml_file in pack_dir.glob("*.yaml"):
            scenario = load_scenario_template(yaml_file)
            assert isinstance(scenario, BaselineScenario)


class TestTemplateTotalCount:
    """Verify total template count meets AC-1 (at least 3 templates)."""

    def test_at_least_three_templates_available(self) -> None:
        """At least 3 templates total (one subsidy, one rebate, one feebate)."""
        subsidy_count = len(list_subsidy_templates())
        rebate_count = len(list_rebate_templates())
        feebate_count = len(list_feebate_templates())

        total = subsidy_count + rebate_count + feebate_count
        assert total >= 3

        # Each type must have at least one
        assert subsidy_count >= 1
        assert rebate_count >= 1
        assert feebate_count >= 1
