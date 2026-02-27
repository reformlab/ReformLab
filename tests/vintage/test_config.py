"""Tests for vintage configuration validation."""

import pytest

from reformlab.vintage.config import VintageConfig, VintageTransitionRule
from reformlab.vintage.errors import VintageConfigError
from reformlab.vintage.types import VintageState


class TestVintageTransitionRule:
    """Tests for VintageTransitionRule validation."""

    def test_fixed_entry_valid(self) -> None:
        """Valid fixed_entry rule."""
        rule = VintageTransitionRule(
            rule_type="fixed_entry",
            parameters={"count": 1000},
            description="Add 1000 new vehicles per year",
        )
        assert rule.rule_type == "fixed_entry"
        assert rule.parameters["count"] == 1000

    def test_proportional_entry_valid(self) -> None:
        """Valid proportional_entry rule."""
        rule = VintageTransitionRule(
            rule_type="proportional_entry",
            parameters={"rate": 0.05},
            description="Add 5% of fleet as new vehicles",
        )
        assert rule.rule_type == "proportional_entry"
        assert rule.parameters["rate"] == 0.05

    def test_max_age_retirement_valid(self) -> None:
        """Valid max_age_retirement rule."""
        rule = VintageTransitionRule(
            rule_type="max_age_retirement",
            parameters={"max_age": 20},
            description="Retire vehicles older than 20 years",
        )
        assert rule.rule_type == "max_age_retirement"
        assert rule.parameters["max_age"] == 20

    def test_invalid_rule_type_raises(self) -> None:
        """Invalid rule type raises VintageConfigError."""
        with pytest.raises(VintageConfigError, match="Invalid rule_type"):
            VintageTransitionRule(
                rule_type="unknown_rule",  # type: ignore[arg-type]
                parameters={},
            )

    def test_fixed_entry_missing_count_raises(self) -> None:
        """fixed_entry without count raises VintageConfigError."""
        with pytest.raises(VintageConfigError, match="'count' parameter"):
            VintageTransitionRule(
                rule_type="fixed_entry",
                parameters={},
            )

    def test_fixed_entry_negative_count_raises(self) -> None:
        """fixed_entry with negative count raises VintageConfigError."""
        with pytest.raises(VintageConfigError, match="non-negative integer"):
            VintageTransitionRule(
                rule_type="fixed_entry",
                parameters={"count": -10},
            )

    def test_fixed_entry_bool_count_raises(self) -> None:
        """fixed_entry with bool count raises VintageConfigError."""
        with pytest.raises(VintageConfigError, match="non-negative integer"):
            VintageTransitionRule(
                rule_type="fixed_entry",
                parameters={"count": True},
            )

    def test_proportional_entry_missing_rate_raises(self) -> None:
        """proportional_entry without rate raises VintageConfigError."""
        with pytest.raises(VintageConfigError, match="'rate' parameter"):
            VintageTransitionRule(
                rule_type="proportional_entry",
                parameters={},
            )

    def test_proportional_entry_negative_rate_raises(self) -> None:
        """proportional_entry with negative rate raises VintageConfigError."""
        with pytest.raises(VintageConfigError, match="non-negative number"):
            VintageTransitionRule(
                rule_type="proportional_entry",
                parameters={"rate": -0.1},
            )

    def test_proportional_entry_bool_rate_raises(self) -> None:
        """proportional_entry with bool rate raises VintageConfigError."""
        with pytest.raises(VintageConfigError, match="non-negative number"):
            VintageTransitionRule(
                rule_type="proportional_entry",
                parameters={"rate": False},
            )

    def test_max_age_retirement_missing_max_age_raises(self) -> None:
        """max_age_retirement without max_age raises VintageConfigError."""
        with pytest.raises(VintageConfigError, match="'max_age' parameter"):
            VintageTransitionRule(
                rule_type="max_age_retirement",
                parameters={},
            )

    def test_max_age_retirement_negative_max_age_raises(self) -> None:
        """max_age_retirement with negative max_age raises VintageConfigError."""
        with pytest.raises(VintageConfigError, match="non-negative integer"):
            VintageTransitionRule(
                rule_type="max_age_retirement",
                parameters={"max_age": -5},
            )

    def test_max_age_retirement_bool_max_age_raises(self) -> None:
        """max_age_retirement with bool max_age raises VintageConfigError."""
        with pytest.raises(VintageConfigError, match="non-negative integer"):
            VintageTransitionRule(
                rule_type="max_age_retirement",
                parameters={"max_age": True},
            )


class TestVintageConfig:
    """Tests for VintageConfig validation."""

    @pytest.fixture
    def valid_rules(self) -> tuple[VintageTransitionRule, ...]:
        """Fixture providing valid rules for testing."""
        return (
            VintageTransitionRule(
                rule_type="fixed_entry",
                parameters={"count": 1000},
            ),
            VintageTransitionRule(
                rule_type="max_age_retirement",
                parameters={"max_age": 20},
            ),
        )

    def test_valid_config(
        self, valid_rules: tuple[VintageTransitionRule, ...]
    ) -> None:
        """Valid configuration for vehicle asset class."""
        config = VintageConfig(
            asset_class="vehicle",
            rules=valid_rules,
        )
        assert config.asset_class == "vehicle"
        assert len(config.rules) == 2

    def test_unsupported_asset_class_raises(
        self, valid_rules: tuple[VintageTransitionRule, ...]
    ) -> None:
        """Unsupported asset class raises VintageConfigError."""
        with pytest.raises(VintageConfigError, match="Unsupported asset_class"):
            VintageConfig(
                asset_class="heating",  # Not supported in MVP
                rules=valid_rules,
            )

    def test_missing_retirement_rule_raises(self) -> None:
        """Missing retirement rule raises VintageConfigError."""
        rules = (
            VintageTransitionRule(
                rule_type="fixed_entry",
                parameters={"count": 1000},
            ),
        )
        with pytest.raises(VintageConfigError, match="retirement rule"):
            VintageConfig(asset_class="vehicle", rules=rules)

    def test_missing_entry_rule_raises(self) -> None:
        """Missing entry rule raises VintageConfigError."""
        rules = (
            VintageTransitionRule(
                rule_type="max_age_retirement",
                parameters={"max_age": 20},
            ),
        )
        with pytest.raises(VintageConfigError, match="entry rule"):
            VintageConfig(asset_class="vehicle", rules=rules)

    def test_initial_state_asset_class_mismatch_raises(
        self, valid_rules: tuple[VintageTransitionRule, ...]
    ) -> None:
        """Initial state with mismatched asset class raises VintageConfigError."""
        initial = VintageState(asset_class="different_asset")
        with pytest.raises(VintageConfigError, match="does not match"):
            VintageConfig(
                asset_class="vehicle",
                rules=valid_rules,
                initial_state=initial,
            )

    def test_initial_state_matching_asset_class(
        self, valid_rules: tuple[VintageTransitionRule, ...]
    ) -> None:
        """Initial state with matching asset class is accepted."""
        initial = VintageState(asset_class="vehicle")
        config = VintageConfig(
            asset_class="vehicle",
            rules=valid_rules,
            initial_state=initial,
        )
        assert config.initial_state is initial

    def test_max_age_property(
        self, valid_rules: tuple[VintageTransitionRule, ...]
    ) -> None:
        """max_age property returns configured max age."""
        config = VintageConfig(asset_class="vehicle", rules=valid_rules)
        assert config.max_age == 20

    def test_entry_rules_property(
        self, valid_rules: tuple[VintageTransitionRule, ...]
    ) -> None:
        """entry_rules property returns entry rules only."""
        config = VintageConfig(asset_class="vehicle", rules=valid_rules)
        entry_rules = config.entry_rules
        assert len(entry_rules) == 1
        assert entry_rules[0].rule_type == "fixed_entry"

    def test_retirement_rules_property(
        self, valid_rules: tuple[VintageTransitionRule, ...]
    ) -> None:
        """retirement_rules property returns retirement rules only."""
        config = VintageConfig(asset_class="vehicle", rules=valid_rules)
        retirement_rules = config.retirement_rules
        assert len(retirement_rules) == 1
        assert retirement_rules[0].rule_type == "max_age_retirement"

    def test_rules_list_normalized_to_tuple(self) -> None:
        """Rules provided as list are normalized to tuple."""
        rules = [
            VintageTransitionRule(
                rule_type="fixed_entry",
                parameters={"count": 1000},
            ),
            VintageTransitionRule(
                rule_type="max_age_retirement",
                parameters={"max_age": 20},
            ),
        ]
        config = VintageConfig(
            asset_class="vehicle",
            rules=rules,  # type: ignore[arg-type]
        )
        assert isinstance(config.rules, tuple)
