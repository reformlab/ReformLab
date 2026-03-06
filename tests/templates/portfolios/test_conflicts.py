"""Tests for portfolio conflict detection and resolution.

Story 12.2: Implement portfolio compatibility validation and conflict resolution
AC1: Conflict detection for same policy type
AC2: Non-conflicting portfolio validation
AC3: Resolution strategy application
AC4: Validation blocking for unresolved conflicts
AC5: Deterministic conflict resolution
AC6: Backward compatibility
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reformlab.templates.portfolios import (
    Conflict,
    ConflictType,
    ResolutionStrategy,
)
from reformlab.templates.portfolios.composition import (
    dump_portfolio,
    load_portfolio,
    resolve_conflicts,
    validate_compatibility,
)
from reformlab.templates.portfolios.exceptions import PortfolioValidationError
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
from reformlab.templates.schema import (
    CarbonTaxParameters,
    PolicyType,
    SubsidyParameters,
)


class TestConflictDataStructures:
    """Tests for conflict detection data structures (Task 1)."""

    def test_conflict_type_enum_exists(self) -> None:
        """ConflictType enum exists with required values."""
        assert hasattr(ConflictType, "SAME_POLICY_TYPE")
        assert hasattr(ConflictType, "OVERLAPPING_CATEGORIES")
        assert hasattr(ConflictType, "OVERLAPPING_YEARS")
        assert hasattr(ConflictType, "PARAMETER_MISMATCH")

    def test_resolution_strategy_enum_exists(self) -> None:
        """ResolutionStrategy enum exists with required values."""
        assert hasattr(ResolutionStrategy, "ERROR")
        assert hasattr(ResolutionStrategy, "SUM")
        assert hasattr(ResolutionStrategy, "FIRST_WINS")
        assert hasattr(ResolutionStrategy, "LAST_WINS")
        assert hasattr(ResolutionStrategy, "MAX")

    def test_conflict_frozen_dataclass(self) -> None:
        """Conflict is a frozen dataclass with required fields."""
        conflict = Conflict(
            conflict_type=ConflictType.SAME_POLICY_TYPE,
            policy_indices=(0, 1),
            parameter_name="policy_type",
            conflicting_values=("carbon_tax", "carbon_tax"),
            description="Both policies are carbon_tax",
        )
        assert conflict.conflict_type == ConflictType.SAME_POLICY_TYPE
        assert conflict.policy_indices == (0, 1)
        assert conflict.parameter_name == "policy_type"
        assert conflict.conflicting_values == ("carbon_tax", "carbon_tax")
        assert conflict.description == "Both policies are carbon_tax"

        # Verify frozen
        with pytest.raises(Exception):
            conflict.conflict_type = ConflictType.OVERLAPPING_YEARS  # type: ignore[misc]

    def test_conflict_repr_readable(self) -> None:
        """Conflict has readable __repr__."""
        conflict = Conflict(
            conflict_type=ConflictType.SAME_POLICY_TYPE,
            policy_indices=(0, 1),
            parameter_name="policy_type",
            conflicting_values=("carbon_tax", "carbon_tax"),
            description="Both policies are carbon_tax",
        )
        repr_str = repr(conflict)
        assert "Conflict" in repr_str
        assert "same_policy_type" in repr_str
        assert "(0, 1)" in repr_str


class TestConflictDetection:
    """Tests for conflict detection logic (Task 3, AC1, AC2, AC5)."""

    def test_detect_same_policy_type_conflict(self, carbon_tax_params: CarbonTaxParameters) -> None:
        """AC1: Detect conflict when two policies have same policy_type."""
        # Create different rate schedules to avoid overlapping years conflict
        params1 = CarbonTaxParameters(
            rate_schedule={2026: 44.6, 2027: 50.0},
            exemptions=carbon_tax_params.exemptions,
            thresholds=carbon_tax_params.thresholds,
            covered_categories=carbon_tax_params.covered_categories,
            redistribution_type=carbon_tax_params.redistribution_type,
            income_weights=carbon_tax_params.income_weights,
        )
        params2 = CarbonTaxParameters(
            rate_schedule={2028: 55.0, 2029: 60.0},
            exemptions=carbon_tax_params.exemptions,
            thresholds=carbon_tax_params.thresholds,
            covered_categories=carbon_tax_params.covered_categories,
            redistribution_type=carbon_tax_params.redistribution_type,
            income_weights=carbon_tax_params.income_weights,
        )
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=params1,
            name="First Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=params2,
            name="Second Carbon Tax",
        )
        portfolio = PolicyPortfolio(
            name="Conflicting Portfolio",
            policies=(policy1, policy2),
        )
        conflicts = validate_compatibility(portfolio)
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == ConflictType.SAME_POLICY_TYPE
        assert conflicts[0].policy_indices == (0, 1)
        assert conflicts[0].parameter_name == "policy_type"

    def test_non_conflicting_portfolio(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """AC2: Non-conflicting portfolio passes validation."""
        # Create non-overlapping rate schedules
        carbon_params = CarbonTaxParameters(
            rate_schedule={2026: 44.6, 2027: 50.0},
            exemptions=carbon_tax_params.exemptions,
            thresholds=carbon_tax_params.thresholds,
            covered_categories=carbon_tax_params.covered_categories,
            redistribution_type=carbon_tax_params.redistribution_type,
            income_weights=carbon_tax_params.income_weights,
        )
        subsidy_params_non_overlap = SubsidyParameters(
            rate_schedule={2028: 5000.0, 2029: 5000.0},
            exemptions=subsidy_params.exemptions,
            thresholds=subsidy_params.thresholds,
            covered_categories=subsidy_params.covered_categories,
            eligible_categories=subsidy_params.eligible_categories,
            income_caps=subsidy_params.income_caps,
        )
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_params,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params_non_overlap,
            name="EV Subsidy",
        )
        portfolio = PolicyPortfolio(
            name="Valid Portfolio",
            policies=(policy1, policy2),
        )
        conflicts = validate_compatibility(portfolio)
        assert len(conflicts) == 0

    def test_detect_overlapping_years_conflict(self) -> None:
        """Detect conflict when rate_schedule years overlap."""
        carbon_tax1 = CarbonTaxParameters(rate_schedule={2026: 50.0, 2027: 55.0, 2028: 60.0})
        carbon_tax2 = CarbonTaxParameters(rate_schedule={2027: 100.0, 2028: 110.0, 2029: 120.0})
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax1,
            name="Tax A",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax2,
            name="Tax B",
        )
        portfolio = PolicyPortfolio(
            name="Overlapping Years",
            policies=(policy1, policy2),
        )
        conflicts = validate_compatibility(portfolio)
        # Should have SAME_POLICY_TYPE and OVERLAPPING_YEARS conflicts
        assert any(c.conflict_type == ConflictType.OVERLAPPING_YEARS for c in conflicts)

    def test_detect_overlapping_categories_conflict(self) -> None:
        """AC1: Detect conflict when categories overlap."""
        carbon_tax = CarbonTaxParameters(
            rate_schedule={2026: 50.0},
            covered_categories=("transport", "heating"),
        )
        subsidy = SubsidyParameters(
            rate_schedule={2027: 5000.0},
            covered_categories=("energy",),
            eligible_categories=("heating", "electricity"),
        )
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax,
            name="Carbon Tax",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy,
            name="Subsidy",
        )
        portfolio = PolicyPortfolio(
            name="Category Overlap",
            policies=(policy1, policy2),
        )
        conflicts = validate_compatibility(portfolio)
        # Should have OVERLAPPING_CATEGORIES conflict (heating overlaps)
        assert any(c.conflict_type == ConflictType.OVERLAPPING_CATEGORIES for c in conflicts)

    def test_deterministic_conflict_ordering(self, carbon_tax_params: CarbonTaxParameters) -> None:
        """AC5: Conflicts are deterministically ordered."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="First",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Second",
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
        )
        conflicts1 = validate_compatibility(portfolio)
        conflicts2 = validate_compatibility(portfolio)
        assert conflicts1 == conflicts2

    def test_conflict_ordering_sorted_by_indices_then_parameter(self) -> None:
        """AC5: Conflicts sorted by policy indices, then parameter name."""
        carbon_tax1 = CarbonTaxParameters(
            rate_schedule={2026: 50.0, 2027: 55.0},
            covered_categories=("transport",),
        )
        carbon_tax2 = CarbonTaxParameters(
            rate_schedule={2027: 60.0},
            covered_categories=("heating",),
        )
        subsidy = SubsidyParameters(
            rate_schedule={2027: 5000.0},
            covered_categories=("energy",),
            eligible_categories=("transport",),
        )
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax1,
            name="Tax 1",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax2,
            name="Tax 2",
        )
        policy3 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy,
            name="Subsidy",
        )
        portfolio = PolicyPortfolio(
            name="Multi Conflict",
            policies=(policy1, policy2, policy3),
        )
        conflicts = validate_compatibility(portfolio)
        # Verify conflicts are sorted
        for i in range(len(conflicts) - 1):
            curr = conflicts[i]
            next_conflict = conflicts[i + 1]
            # Sort key: (policy_indices[0], parameter_name)
            curr_key = (curr.policy_indices[0], curr.parameter_name)
            next_key = (next_conflict.policy_indices[0], next_conflict.parameter_name)
            assert curr_key <= next_key


class TestConflictResolution:
    """Tests for conflict resolution strategies (Task 4, AC3, AC4, AC5)."""

    def test_error_strategy_raises_exception(self, carbon_tax_params: CarbonTaxParameters) -> None:
        """AC4: Error strategy raises PortfolioValidationError."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="First",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
            name="Second",
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
            resolution_strategy="error",
        )
        conflicts = validate_compatibility(portfolio)
        with pytest.raises(PortfolioValidationError, match="conflict"):
            resolve_conflicts(portfolio, conflicts)

    def test_sum_strategy_adds_rates(self) -> None:
        """AC3: Sum strategy adds rates for overlapping years."""
        carbon_tax1 = CarbonTaxParameters(rate_schedule={2026: 50.0, 2027: 55.0})
        carbon_tax2 = CarbonTaxParameters(rate_schedule={2027: 30.0, 2028: 35.0})
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax1,
            name="Tax A",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax2,
            name="Tax B",
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
            resolution_strategy="sum",
        )
        conflicts = validate_compatibility(portfolio)
        resolved = resolve_conflicts(portfolio, conflicts)
        # Check that resolution metadata was appended to description
        assert "Resolved" in resolved.description
        assert "sum" in resolved.description
        # Check deterministic resolution
        assert resolved.policies[0].policy.rate_schedule[2027] == 85.0  # 55 + 30

    def test_first_wins_strategy(self) -> None:
        """AC3: First wins strategy uses first policy values."""
        carbon_tax1 = CarbonTaxParameters(rate_schedule={2026: 50.0, 2027: 55.0})
        carbon_tax2 = CarbonTaxParameters(rate_schedule={2027: 30.0, 2028: 35.0})
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax1,
            name="Tax A",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax2,
            name="Tax B",
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
            resolution_strategy="first_wins",
        )
        conflicts = validate_compatibility(portfolio)
        resolved = resolve_conflicts(portfolio, conflicts)
        assert resolved.policies[0].policy.rate_schedule[2027] == 55.0  # first wins

    def test_last_wins_strategy(self) -> None:
        """AC3: Last wins strategy uses last policy values."""
        carbon_tax1 = CarbonTaxParameters(rate_schedule={2026: 50.0, 2027: 55.0})
        carbon_tax2 = CarbonTaxParameters(rate_schedule={2027: 30.0, 2028: 35.0})
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax1,
            name="Tax A",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax2,
            name="Tax B",
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
            resolution_strategy="last_wins",
        )
        conflicts = validate_compatibility(portfolio)
        resolved = resolve_conflicts(portfolio, conflicts)
        assert resolved.policies[0].policy.rate_schedule[2027] == 30.0  # last wins

    def test_max_strategy(self) -> None:
        """AC3: Max strategy uses maximum rate."""
        carbon_tax1 = CarbonTaxParameters(rate_schedule={2026: 50.0, 2027: 55.0})
        carbon_tax2 = CarbonTaxParameters(rate_schedule={2027: 30.0, 2028: 35.0})
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax1,
            name="Tax A",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax2,
            name="Tax B",
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
            resolution_strategy="max",
        )
        conflicts = validate_compatibility(portfolio)
        resolved = resolve_conflicts(portfolio, conflicts)
        assert resolved.policies[0].policy.rate_schedule[2027] == 55.0  # max wins

    def test_deterministic_resolution(self) -> None:
        """AC5: Identical inputs produce identical resolution."""
        carbon_tax1 = CarbonTaxParameters(rate_schedule={2026: 50.0, 2027: 55.0})
        carbon_tax2 = CarbonTaxParameters(rate_schedule={2027: 30.0, 2028: 35.0})
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax1,
            name="Tax A",
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax2,
            name="Tax B",
        )
        portfolio = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
            resolution_strategy="sum",
        )
        conflicts = validate_compatibility(portfolio)
        resolved1 = resolve_conflicts(portfolio, conflicts)
        resolved2 = resolve_conflicts(portfolio, conflicts)
        assert resolved1 == resolved2


class TestResolutionStrategyField:
    """Tests for resolution_strategy field in PolicyPortfolio (Task 2, AC3, AC5, AC6)."""

    def test_default_resolution_strategy_is_error(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """AC6: Default resolution_strategy is 'error' for backward compatibility."""
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
        assert portfolio.resolution_strategy == "error"

    def test_yaml_round_trip_preserves_strategy(
        self,
        carbon_tax_params: CarbonTaxParameters,
        subsidy_params: SubsidyParameters,
        temp_portfolio_dir: Path,
    ) -> None:
        """AC5: YAML round-trip preserves resolution_strategy."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        original = PolicyPortfolio(
            name="Test",
            policies=(policy1, policy2),
            resolution_strategy="sum",
        )
        file_path = temp_portfolio_dir / "test-roundtrip.yaml"
        dump_portfolio(original, file_path)
        loaded = load_portfolio(file_path, validate=False)
        assert loaded.resolution_strategy == "sum"

    def test_invalid_resolution_strategy_raises_error(
        self, carbon_tax_params: CarbonTaxParameters, subsidy_params: SubsidyParameters
    ) -> None:
        """Invalid resolution_strategy raises PortfolioValidationError."""
        policy1 = PolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=carbon_tax_params,
        )
        policy2 = PolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=subsidy_params,
        )
        with pytest.raises(PortfolioValidationError, match="resolution_strategy"):
            PolicyPortfolio(
                name="Test",
                policies=(policy1, policy2),
                resolution_strategy="invalid",  # noqa: S107
            )


class TestPortfolioLoadingValidation:
    """Tests for validation integration into load_portfolio (Task 5, AC4, AC6)."""

    def test_load_validates_by_default(
        self, carbon_tax_params: CarbonTaxParameters, temp_portfolio_dir: Path
    ) -> None:
        """AC4: load_portfolio validates by default."""
        file_path = temp_portfolio_dir / "conflicting.yaml"
        file_path.write_text(
            """
name: "Conflicting Portfolio"
version: "1.0"
policies:
  - policy_type: carbon_tax
    name: "First"
    policy:
      rate_schedule: {2026: 50}
  - policy_type: carbon_tax
    name: "Second"
    policy:
      rate_schedule: {2027: 60}
"""
        )
        with pytest.raises(PortfolioValidationError, match="conflict"):
            load_portfolio(file_path)

    def test_load_with_validate_false_skips_validation(
        self, carbon_tax_params: CarbonTaxParameters, temp_portfolio_dir: Path
    ) -> None:
        """validate=False skips conflict detection."""
        file_path = temp_portfolio_dir / "conflicting.yaml"
        file_path.write_text(
            """
name: "Conflicting Portfolio"
version: "1.0"
policies:
  - policy_type: carbon_tax
    name: "First"
    policy:
      rate_schedule: {2026: 50}
  - policy_type: carbon_tax
    name: "Second"
    policy:
      rate_schedule: {2027: 60}
"""
        )
        portfolio = load_portfolio(file_path, validate=False)
        assert portfolio.name == "Conflicting Portfolio"

    def test_backward_compatibility_no_strategy_field(
        self,
        carbon_tax_params: CarbonTaxParameters,
        subsidy_params: SubsidyParameters,
        temp_portfolio_dir: Path,
    ) -> None:
        """AC6: Portfolios without resolution_strategy field default to 'error'."""
        file_path = temp_portfolio_dir / "old-portfolio.yaml"
        file_path.write_text(
            """
name: "Old Portfolio"
version: "1.0"
policies:
  - policy_type: carbon_tax
    name: "Tax"
    policy:
      rate_schedule: {2026: 50}
  - policy_type: subsidy
    name: "Subsidy"
    policy:
      rate_schedule: {2027: 5000}
"""
        )
        portfolio = load_portfolio(file_path)
        assert portfolio.resolution_strategy == "error"

    def test_error_message_includes_suggestions(
        self, carbon_tax_params: CarbonTaxParameters, temp_portfolio_dir: Path
    ) -> None:
        """AC4: Error messages include suggested resolution strategies."""
        file_path = temp_portfolio_dir / "conflicting.yaml"
        file_path.write_text(
            """
name: "Conflicting"
version: "1.0"
policies:
  - policy_type: carbon_tax
    name: "First"
    policy:
      rate_schedule: {2026: 50, 2027: 60}
  - policy_type: carbon_tax
    name: "Second"
    policy:
      rate_schedule: {2027: 70, 2028: 80}
"""
        )
        with pytest.raises(PortfolioValidationError, match="sum|first_wins|last_wins|max"):
            load_portfolio(file_path)

    def test_warning_log_format_for_non_error_strategy(
        self, temp_portfolio_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """AC4: Warning log uses structured key=value format."""
        import logging

        file_path = temp_portfolio_dir / "conflicting.yaml"
        file_path.write_text(
            """
name: "Test Portfolio"
version: "1.0"
resolution_strategy: "sum"
policies:
  - policy_type: carbon_tax
    name: "First"
    policy:
      rate_schedule: {2026: 50, 2027: 60}
  - policy_type: carbon_tax
    name: "Second"
    policy:
      rate_schedule: {2027: 70, 2028: 80}
"""
        )
        with caplog.at_level(logging.WARNING):
            _ = load_portfolio(file_path)  # noqa: F841

        # Verify warning was logged with structured format
        assert len(caplog.records) > 0
        warning_record = caplog.records[0]
        assert warning_record.levelname == "WARNING"
        # Check that log message contains structured key=value pairs
        message = warning_record.getMessage()
        assert "event=portfolio_conflicts" in message
        assert "strategy=sum" in message
        assert "conflict_count=" in message
        assert "portfolio=Test Portfolio" in message


class TestSchemaValidation:
    """Tests for JSON Schema validation with resolution_strategy field."""

    def test_schema_includes_resolution_strategy(self) -> None:
        """JSON Schema includes resolution_strategy field."""
        import json

        schema_path = (
            Path(__file__).parent.parent.parent.parent
            / "src/reformlab/templates/schema/portfolio.schema.json"
        )
        with open(schema_path) as f:
            schema = json.load(f)
        assert "resolution_strategy" in schema["properties"]
        assert "enum" in schema["properties"]["resolution_strategy"]

    def test_yaml_without_strategy_validates(
        self,
        carbon_tax_params: CarbonTaxParameters,
        subsidy_params: SubsidyParameters,
        temp_portfolio_dir: Path,
    ) -> None:
        """YAML without resolution_strategy field validates against schema."""
        file_path = temp_portfolio_dir / "no-strategy.yaml"
        file_path.write_text(
            """
name: "No Strategy"
version: "1.0"
policies:
  - policy_type: carbon_tax
    policy:
      rate_schedule: {2026: 50}
  - policy_type: subsidy
    policy:
      rate_schedule: {2027: 5000}
"""
        )
        portfolio = load_portfolio(file_path)
        assert portfolio.resolution_strategy == "error"
