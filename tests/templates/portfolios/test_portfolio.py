"""Tests for PolicyPortfolio frozen dataclass construction and inspection.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
AC1: Frozen dataclass composition
AC2: Policy inspection
AC4: Validation error handling
"""

from __future__ import annotations

import pytest

from reformlab.templates.portfolios.exceptions import (
    PortfolioValidationError,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
from reformlab.templates.schema import (
    CarbonTaxParameters,
    PolicyType,
    SubsidyParameters,
)


class TestPolicyConfigConstruction:
    """Tests for PolicyConfig wrapper creation and validation."""

    def test_policy_config_creation_with_carbon_tax(self, carbon_tax_params: CarbonTaxParameters) -> None:
        """PolicyConfig can be created with carbon tax parameters."""
        config = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Carbon Tax Component",
        )
        assert config.policy_type == PolicyType.CARBON_TAX
        assert config.policy is carbon_tax_params
        assert config.name == "Carbon Tax Component"

    def test_policy_config_creation_with_subsidy(self, subsidy_params: SubsidyParameters) -> None:
        """PolicyConfig can be created with subsidy parameters."""
        config = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="EV Bonus",
        )
        assert config.policy_type == PolicyType.SUBSIDY
        assert config.policy is subsidy_params
        assert config.name == "EV Bonus"

    def test_policy_config_default_name(self, carbon_tax_params: CarbonTaxParameters) -> None:
        """PolicyConfig name defaults to empty string."""
        config = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        assert config.name == ""

    def test_policy_config_get_summary(self, carbon_tax_params: CarbonTaxParameters) -> None:
        """PolicyConfig.get_summary() extracts type and key parameters."""
        config = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Test Tax",
        )
        summary = config.get_summary()
        assert summary["name"] == "Test Tax"
        assert summary["type"] == "carbon_tax"
        assert summary["rate_schedule_years"] == [2026, 2027, 2028]

    def test_policy_config_frozen(self, carbon_tax_params: CarbonTaxParameters) -> None:
        """PolicyConfig is frozen (immutable)."""
        config = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        with pytest.raises(AttributeError):
            config.name = "Modified"  # type: ignore

    def test_policy_config_type_validation_mismatch(self, subsidy_params: SubsidyParameters) -> None:
        """PolicyConfig validates that policy matches declared policy_type."""
        with pytest.raises(PortfolioValidationError, match="does not match"):
            PolicyConfig(
                policy_type=PolicyType.CARBON_TAX,
                policy=subsidy_params,  # Wrong type!
                name="Invalid",
            )


class TestPolicyPortfolioConstruction:
    """Tests for portfolio creation and validation (AC1)."""

    def test_portfolio_creation_with_two_policies(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """Portfolio can be created with 2 policies."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="EV Subsidy",
        )
        portfolio = PolicyPortfolio(
            name="Green Transition 2030",
            policies=(policy1, policy2),
        )
        assert portfolio.name == "Green Transition 2030"
        assert len(portfolio.policies) == 2
        assert portfolio.policies[0] is policy1
        assert portfolio.policies[1] is policy2

    def test_portfolio_requires_at_least_two_policies(self, carbon_tax_params: CarbonTaxParameters) -> None:
        """Portfolio with <2 policies raises clear error (AC4)."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Single Policy",
        )
        with pytest.raises(PortfolioValidationError, match="at least 2 policies"):
            PolicyPortfolio(
                name="Invalid Portfolio",
                policies=(policy1,),
            )

    def test_portfolio_requires_at_least_two_policies_empty(self) -> None:
        """Portfolio with 0 policies raises clear error (AC4)."""
        with pytest.raises(PortfolioValidationError, match="at least 2 policies"):
            PolicyPortfolio(
                name="Empty Portfolio",
                policies=(),
            )

    def test_portfolio_default_version(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """Portfolio version defaults to '1.0'."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        portfolio = PolicyPortfolio(
            name="Test Portfolio",
            policies=(policy1, policy2),
        )
        assert portfolio.version == "1.0"

    def test_portfolio_default_description(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """Portfolio description defaults to empty string."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        portfolio = PolicyPortfolio(
            name="Test Portfolio",
            policies=(policy1, policy2),
        )
        assert portfolio.description == ""

    def test_portfolio_frozen(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """Portfolio is frozen (immutable)."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        portfolio = PolicyPortfolio(
            name="Test Portfolio",
            policies=(policy1, policy2),
        )
        with pytest.raises(AttributeError):
            portfolio.name = "Modified"  # type: ignore

    def test_portfolio_preserves_policy_order(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """Portfolio preserves the order of policies as provided."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="First",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="Second",
        )
        policy3 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Third",
        )
        portfolio = PolicyPortfolio(
            name="Multi Policy",
            policies=(policy1, policy2, policy3),
        )
        assert portfolio.policies[0].name == "First"
        assert portfolio.policies[1].name == "Second"
        assert portfolio.policies[2].name == "Third"

    def test_portfolio_repr(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """Portfolio has a notebook-friendly repr."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="EV Subsidy",
        )
        portfolio = PolicyPortfolio(
            name="Test Portfolio",
            policies=(policy1, policy2),
            version="2.0",
        )
        repr_str = repr(portfolio)
        assert "PolicyPortfolio" in repr_str
        assert "Test Portfolio" in repr_str
        assert "2.0" in repr_str
        assert "2 policies" in repr_str


class TestPolicyPortfolioInspection:
    """Tests for portfolio inspection methods (AC2)."""

    def test_portfolio_policy_types_property(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """portfolio.policy_types returns types in order."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        policy3 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2, policy3),
        )
        assert portfolio.policy_types == (
            PolicyType.CARBON_TAX,
            PolicyType.SUBSIDY,
            PolicyType.CARBON_TAX,
        )

    def test_portfolio_policy_count_property(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """portfolio.policy_count returns number of policies."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
        )
        assert portfolio.policy_count == 2

    def test_portfolio_policy_summaries_property(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """portfolio.policy_summaries returns summaries in order."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="EV Subsidy",
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
        )
        summaries = portfolio.policy_summaries
        assert len(summaries) == 2
        assert summaries[0]["name"] == "Carbon Tax"
        assert summaries[0]["type"] == "carbon_tax"
        assert summaries[1]["name"] == "EV Subsidy"
        assert summaries[1]["type"] == "subsidy"

    def test_portfolio_list_policies(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """portfolio.list_policies() returns detailed policy info."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="EV Subsidy",
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
        )
        policies_list = portfolio.list_policies()
        assert len(policies_list) == 2
        assert policies_list[0]["name"] == "Carbon Tax"
        assert policies_list[0]["type"] == "carbon_tax"
        assert "rate_schedule" in policies_list[0]
        assert policies_list[1]["name"] == "EV Subsidy"
        assert policies_list[1]["type"] == "subsidy"

    def test_portfolio_get_policy_by_type_found(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """portfolio.get_policy_by_type() returns first matching policy."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="First Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
            name="EV Subsidy",
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
        )
        result = portfolio.get_policy_by_type(PolicyType.SUBSIDY)
        assert result is not None
        assert result.name == "EV Subsidy"

    def test_portfolio_get_policy_by_type_not_found(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """portfolio.get_policy_by_type() returns None if not found."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
        )
        result = portfolio.get_policy_by_type(PolicyType.REBATE)
        assert result is None

    def test_portfolio_has_policy_type_true(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """portfolio.has_policy_type() returns True if type present."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
        )
        assert portfolio.has_policy_type(PolicyType.CARBON_TAX) is True
        assert portfolio.has_policy_type(PolicyType.SUBSIDY) is True

    def test_portfolio_has_policy_type_false(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """portfolio.has_policy_type() returns False if type absent."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
        )
        assert portfolio.has_policy_type(PolicyType.REBATE) is False
        assert portfolio.has_policy_type(PolicyType.FEEBATE) is False
