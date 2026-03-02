from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from reformlab.templates.exceptions import TemplateError

logger = logging.getLogger(__name__)


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


# ====================================================================
# Policy type inference
# ====================================================================

_PARAMETERS_TO_POLICY_TYPE: dict[type[PolicyParameters], PolicyType] = {
    CarbonTaxParameters: PolicyType.CARBON_TAX,
    SubsidyParameters: PolicyType.SUBSIDY,
    RebateParameters: PolicyType.REBATE,
    FeebateParameters: PolicyType.FEEBATE,
}


def infer_policy_type(policy: PolicyParameters) -> PolicyType:
    """Infer PolicyType from a policy parameters instance.

    Uses isinstance checks to handle subclasses correctly.

    Raises:
        TemplateError: If the parameters class is not registered.
    """
    for cls, policy_type in _PARAMETERS_TO_POLICY_TYPE.items():
        if isinstance(policy, cls):
            return policy_type
    msg = (
        f"Cannot infer PolicyType from {type(policy).__name__}. "
        f"Register the mapping in _PARAMETERS_TO_POLICY_TYPE in "
        f"src/reformlab/templates/schema.py."
    )
    raise TemplateError(msg)


# ====================================================================
# Scenario templates
# ====================================================================


def _resolve_policy_type(
    policy: PolicyParameters,
    policy_type: PolicyType | None,
) -> PolicyType:
    """Resolve policy_type: infer from *policy* if None, validate if explicit.

    When *policy_type* is ``None`` the type is inferred from the concrete
    *policy* class.  When explicitly provided, a mismatch with the inferred
    type logs a warning but the explicit value is kept.
    """
    if policy_type is None:
        return infer_policy_type(policy)
    try:
        inferred = infer_policy_type(policy)
    except TemplateError:
        return policy_type
    if policy_type != inferred:
        logger.warning(
            "Explicit policy_type=%s does not match inferred type %s "
            "from %s. Using explicit value.",
            policy_type.value,
            inferred.value,
            type(policy).__name__,
        )
    return policy_type


@dataclass(frozen=True)
class ScenarioTemplate:
    """Base scenario template shape shared by baseline and reform variants.

    ``policy_type`` can be omitted when constructing instances with a typed
    ``policy`` object — it will be inferred automatically from the parameter
    class (e.g. ``CarbonTaxParameters`` → ``PolicyType.CARBON_TAX``).
    """

    name: str
    year_schedule: YearSchedule
    policy: PolicyParameters
    policy_type: PolicyType | None = None
    description: str = ""
    version: str = "1.0"
    schema_ref: str = ""

    def __post_init__(self) -> None:
        resolved = _resolve_policy_type(self.policy, self.policy_type)
        if resolved is not self.policy_type:
            object.__setattr__(self, "policy_type", resolved)


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

    ``policy_type`` can be omitted — it will be inferred from the ``policy``
    parameter class.
    """

    name: str
    baseline_ref: str
    policy: PolicyParameters
    policy_type: PolicyType | None = None
    description: str = ""
    version: str = "1.0"
    schema_ref: str = ""
    year_schedule: YearSchedule | None = None  # Optionally override baseline schedule

    def __post_init__(self) -> None:
        if not self.baseline_ref or not self.baseline_ref.strip():
            raise ValueError("baseline_ref is required for ReformScenario")
        resolved = _resolve_policy_type(self.policy, self.policy_type)
        if resolved is not self.policy_type:
            object.__setattr__(self, "policy_type", resolved)
