from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PolicyType(Enum):
    """Supported policy types for scenario templates.

    Per FR7: carbon tax, subsidy, rebate, feebate.
    """

    CARBON_TAX = "carbon_tax"
    SUBSIDY = "subsidy"
    REBATE = "rebate"
    FEEBATE = "feebate"


@dataclass(frozen=True)
class YearSchedule:
    """Year range for policy parameter schedules.

    Supports at least 10 years of policy parameters (FR12).
    """

    start_year: int
    end_year: int

    def __post_init__(self) -> None:
        if self.start_year > self.end_year:
            raise ValueError(
                f"start_year ({self.start_year}) must be <= end_year ({self.end_year})"
            )

    @property
    def duration(self) -> int:
        """Number of years in schedule (inclusive)."""
        return self.end_year - self.start_year + 1

    @property
    def years(self) -> tuple[int, ...]:
        """All years in the schedule."""
        return tuple(range(self.start_year, self.end_year + 1))

    def __contains__(self, year: int) -> bool:
        """Check if year is within the schedule range."""
        return self.start_year <= year <= self.end_year


@dataclass(frozen=True)
class PolicyParameters:
    """Base class for policy-specific parameters.

    Common fields: rate schedules, exemptions, thresholds, covered categories.
    """

    rate_schedule: dict[int, float]
    exemptions: tuple[dict[str, Any], ...] = ()
    thresholds: tuple[dict[str, Any], ...] = ()
    covered_categories: tuple[str, ...] = ()


@dataclass(frozen=True)
class CarbonTaxParameters(PolicyParameters):
    """Carbon tax specific parameters.

    Includes rate schedule (EUR per tonne CO2), exemptions by category,
    covered energy categories, and optional redistribution configuration.

    Redistribution types:
    - "" (empty): No redistribution, tax revenue retained by government
    - "lump_sum": Equal per-capita dividend to all households
    - "progressive_dividend": Income-weighted dividend, lower deciles receive more

    When redistribution_type is "progressive_dividend", income_weights should
    map decile names (e.g., "decile_1") to weight multipliers (e.g., 1.5).
    """

    redistribution_type: str = ""
    income_weights: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class SubsidyParameters(PolicyParameters):
    """Subsidy specific parameters.

    Includes eligible categories and income caps for means testing.
    """

    eligible_categories: tuple[str, ...] = ()
    income_caps: dict[int, float] = field(default_factory=dict)


@dataclass(frozen=True)
class RebateParameters(PolicyParameters):
    """Rebate/dividend specific parameters.

    Includes rebate type (lump_sum, progressive_dividend) and
    income weights for progressive distribution.
    """

    rebate_type: str = ""
    income_weights: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class FeebateParameters(PolicyParameters):
    """Feebate specific parameters.

    Includes pivot point and fee/rebate rates.
    """

    pivot_point: float = 0.0
    fee_rate: float = 0.0
    rebate_rate: float = 0.0
    # Track whether numeric fields were explicitly provided in source config.
    # This allows reform merges to distinguish "unset" from explicit zero values.
    _pivot_point_set: bool = field(default=False, repr=False, compare=False)
    _fee_rate_set: bool = field(default=False, repr=False, compare=False)
    _rebate_rate_set: bool = field(default=False, repr=False, compare=False)


@dataclass(frozen=True)
class ScenarioTemplate:
    """Base scenario template shape shared by baseline and reform variants."""

    name: str
    policy_type: PolicyType
    year_schedule: YearSchedule
    parameters: PolicyParameters
    description: str = ""
    version: str = "1.0"
    schema_ref: str = ""


@dataclass(frozen=True)
class BaselineScenario(ScenarioTemplate):
    """A baseline scenario template configuration.

    Immutable dataclass representing a complete baseline policy scenario
    with all parameters specified.
    """


@dataclass(frozen=True)
class ReformScenario:
    """A reform scenario that overrides a baseline.

    Reform scenarios inherit unspecified parameters from their baseline.
    The baseline_ref links to the baseline scenario ID.
    """

    name: str
    policy_type: PolicyType
    baseline_ref: str
    parameters: PolicyParameters
    description: str = ""
    version: str = "1.0"
    schema_ref: str = ""
    year_schedule: YearSchedule | None = None  # Optionally override baseline schedule

    def __post_init__(self) -> None:
        if not self.baseline_ref or not self.baseline_ref.strip():
            raise ValueError("baseline_ref is required for ReformScenario")
