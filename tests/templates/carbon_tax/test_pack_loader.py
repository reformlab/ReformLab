from __future__ import annotations

import pytest

from reformlab.templates import (
    BaselineScenario,
    CarbonTaxParameters,
    PolicyType,
    get_carbon_tax_pack_dir,
    list_carbon_tax_templates,
    load_carbon_tax_template,
)


class TestListCarbonTaxTemplates:
    """Tests for list_carbon_tax_templates function."""

    def test_returns_list(self) -> None:
        """Function returns a list of variant names."""
        result = list_carbon_tax_templates()
        assert isinstance(result, list)

    def test_returns_at_least_4_variants(self) -> None:
        """Pack provides at least 4 variants (AC-1)."""
        result = list_carbon_tax_templates()
        assert len(result) >= 4

    def test_variants_are_strings(self) -> None:
        """Variant names are strings."""
        result = list_carbon_tax_templates()
        assert all(isinstance(v, str) for v in result)

    def test_variants_are_descriptive(self) -> None:
        """Variants have descriptive names (AC-1)."""
        result = list_carbon_tax_templates()
        # Should contain common patterns
        assert any("flat" in v for v in result)
        assert any("redistribution" in v or "dividend" in v for v in result)

    def test_expected_variants_present(self) -> None:
        """Expected variant names are present."""
        result = list_carbon_tax_templates()
        assert "carbon-tax-flat-no-redistribution" in result
        assert "carbon-tax-flat-lump-sum-dividend" in result
        assert "carbon-tax-flat-progressive-dividend" in result


class TestLoadCarbonTaxTemplate:
    """Tests for load_carbon_tax_template function."""

    def test_load_flat_no_redistribution(self) -> None:
        """Load flat no redistribution variant."""
        template = load_carbon_tax_template("carbon-tax-flat-no-redistribution")
        assert isinstance(template, BaselineScenario)
        assert template.policy_type == PolicyType.CARBON_TAX
        assert isinstance(template.parameters, CarbonTaxParameters)

    def test_load_flat_lump_sum(self) -> None:
        """Load flat lump sum dividend variant."""
        template = load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend")
        assert isinstance(template, BaselineScenario)
        assert template.parameters.redistribution_type == "lump_sum"

    def test_load_progressive_dividend(self) -> None:
        """Load flat progressive dividend variant."""
        template = load_carbon_tax_template("carbon-tax-flat-progressive-dividend")
        assert isinstance(template, BaselineScenario)
        assert template.parameters.redistribution_type == "progressive_dividend"
        assert len(template.parameters.income_weights) == 10  # All 10 deciles

    def test_year_schedule_at_least_10_years(self) -> None:
        """All templates have year schedules of at least 10 years (AC-1)."""
        for variant in list_carbon_tax_templates():
            template = load_carbon_tax_template(variant)
            assert template.year_schedule.duration >= 10, f"{variant} has < 10 years"

    def test_all_templates_pass_validation(self) -> None:
        """All templates pass load_scenario_template validation (AC-1)."""
        for variant in list_carbon_tax_templates():
            template = load_carbon_tax_template(variant)
            assert isinstance(template, BaselineScenario)
            assert template.policy_type == PolicyType.CARBON_TAX

    def test_load_nonexistent_raises(self) -> None:
        """Loading nonexistent variant raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_carbon_tax_template("nonexistent-variant")
        assert "nonexistent-variant" in str(exc_info.value)
        assert "Available variants" in str(exc_info.value)


class TestGetCarbonTaxPackDir:
    """Tests for get_carbon_tax_pack_dir function."""

    def test_returns_path(self) -> None:
        """Function returns a Path object."""
        from pathlib import Path

        result = get_carbon_tax_pack_dir()
        assert isinstance(result, Path)

    def test_directory_exists(self) -> None:
        """The pack directory exists."""
        result = get_carbon_tax_pack_dir()
        assert result.exists()
        assert result.is_dir()

    def test_contains_yaml_files(self) -> None:
        """Pack directory contains YAML template files."""
        pack_dir = get_carbon_tax_pack_dir()
        yaml_files = list(pack_dir.glob("*.yaml"))
        assert len(yaml_files) >= 4

    def test_contains_readme(self) -> None:
        """Pack directory contains README documentation (AC-5)."""
        pack_dir = get_carbon_tax_pack_dir()
        readme = pack_dir / "README.md"
        assert readme.exists()
