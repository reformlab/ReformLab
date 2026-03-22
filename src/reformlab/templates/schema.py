from __future__ import annotations

import dataclasses
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from reformlab.templates.exceptions import TemplateError

logger = logging.getLogger(__name__)

_SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")


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


# ====================================================================
# Custom policy type registry
# ====================================================================


@dataclass(frozen=True)
class CustomPolicyType:
    """Lightweight wrapper representing a custom (non-enum) policy type.

    Behaves like a PolicyType enum member for code that accesses ``.value``.
    """

    value: str

    def __repr__(self) -> str:
        return f"CustomPolicyType({self.value!r})"


# Registry of custom policy type strings → CustomPolicyType objects.
_CUSTOM_POLICY_TYPES: dict[str, CustomPolicyType] = {}

# Registry of custom parameter classes → policy type objects.
_CUSTOM_PARAMETERS_TO_POLICY_TYPE: dict[type[PolicyParameters], PolicyType | CustomPolicyType] = {}


def register_policy_type(type_name: str) -> CustomPolicyType:
    """Register a new custom policy type.

    Args:
        type_name: Policy type name — must be non-empty, lowercase, snake_case.

    Returns:
        A CustomPolicyType object representing the registered type.

    Raises:
        TemplateError: If type_name is invalid or already registered.
    """
    if not type_name:
        msg = "Policy type name must be non-empty."
        raise TemplateError(msg)

    if type_name != type_name.lower():
        msg = f"Policy type name must be lowercase: {type_name!r}"
        raise TemplateError(msg)

    if not _SNAKE_CASE_RE.match(type_name):
        msg = f"Policy type name must be snake_case: {type_name!r}"
        raise TemplateError(msg)

    # Check against built-in enum values
    builtin_values = {pt.value for pt in PolicyType}
    if type_name in builtin_values:
        msg = f"Policy type {type_name!r} is already registered (built-in)."
        raise TemplateError(msg)

    if type_name in _CUSTOM_POLICY_TYPES:
        msg = f"Policy type {type_name!r} is already registered."
        raise TemplateError(msg)

    custom_type = CustomPolicyType(value=type_name)
    _CUSTOM_POLICY_TYPES[type_name] = custom_type
    return custom_type


def register_custom_template(
    policy_type: PolicyType | CustomPolicyType | str,
    parameters_class: type[PolicyParameters],
) -> None:
    """Register a custom PolicyParameters subclass for a policy type.

    Args:
        policy_type: The policy type (CustomPolicyType, PolicyType, or string).
        parameters_class: A frozen dataclass that subclasses PolicyParameters.

    Raises:
        TemplateError: If parameters_class is invalid or already registered.
    """
    # Resolve string to CustomPolicyType
    if isinstance(policy_type, str):
        resolved = _CUSTOM_POLICY_TYPES.get(policy_type)
        if resolved is None:
            msg = (
                f"Unknown custom policy type {policy_type!r}. "
                f"Register it first with register_policy_type()."
            )
            raise TemplateError(msg)
        policy_type = resolved

    # Validate: must be a dataclass
    if not dataclasses.is_dataclass(parameters_class):
        msg = (
            f"{parameters_class.__name__} must be a frozen dataclass "
            f"subclass of PolicyParameters."
        )
        raise TemplateError(msg)

    # Validate: must be frozen (check via __dataclass_params__)
    dc_params = getattr(parameters_class, "__dataclass_params__", None)
    if dc_params is None or not dc_params.frozen:
        msg = (
            f"{parameters_class.__name__} must be a frozen dataclass "
            f"subclass of PolicyParameters."
        )
        raise TemplateError(msg)

    # Validate: must subclass PolicyParameters
    if not issubclass(parameters_class, PolicyParameters):
        msg = (
            f"{parameters_class.__name__} must be a subclass of PolicyParameters."
        )
        raise TemplateError(msg)

    # Check for duplicate class registration
    if parameters_class in _CUSTOM_PARAMETERS_TO_POLICY_TYPE:
        msg = f"{parameters_class.__name__} is already registered."
        raise TemplateError(msg)

    # Check if this policy type already has a registered class
    for cls, pt in _CUSTOM_PARAMETERS_TO_POLICY_TYPE.items():
        if isinstance(pt, CustomPolicyType) and isinstance(policy_type, CustomPolicyType):
            if pt.value == policy_type.value:
                msg = f"Policy type {policy_type.value!r} is already registered with {cls.__name__}."
                raise TemplateError(msg)

    _CUSTOM_PARAMETERS_TO_POLICY_TYPE[parameters_class] = policy_type


def get_policy_type(value: str) -> PolicyType | CustomPolicyType:
    """Look up a policy type by its string value.

    Checks the built-in PolicyType enum first, then the custom registry.

    Args:
        value: The policy type string.

    Returns:
        PolicyType enum member or CustomPolicyType instance.

    Raises:
        TemplateError: If the value is not found.
    """
    # Check built-in enum first
    for pt in PolicyType:
        if pt.value == value:
            return pt

    # Check custom registry
    custom = _CUSTOM_POLICY_TYPES.get(value)
    if custom is not None:
        return custom

    msg = f"Unknown policy type: {value!r}"
    raise TemplateError(msg)


def unregister_policy_type(type_name: str) -> None:
    """Unregister a custom policy type and its associated parameter class.

    Args:
        type_name: Policy type name to remove.

    Raises:
        TemplateError: If type_name is not a registered custom type.
    """
    if type_name not in _CUSTOM_POLICY_TYPES:
        msg = f"Custom policy type {type_name!r} is not registered."
        raise TemplateError(msg)

    _CUSTOM_POLICY_TYPES.pop(type_name)

    # Remove associated parameter class mapping
    to_remove = [
        cls
        for cls, pt in _CUSTOM_PARAMETERS_TO_POLICY_TYPE.items()
        if isinstance(pt, CustomPolicyType) and pt.value == type_name
    ]
    for cls in to_remove:
        del _CUSTOM_PARAMETERS_TO_POLICY_TYPE[cls]


def list_custom_registrations() -> dict[str, type[PolicyParameters]]:
    """Return a mapping of custom type name → parameters class.

    Returns:
        Dict mapping each registered custom type name to its parameter class.
    """
    result: dict[str, type[PolicyParameters]] = {}
    for cls, pt in _CUSTOM_PARAMETERS_TO_POLICY_TYPE.items():
        if isinstance(pt, CustomPolicyType):
            result[pt.value] = cls
    return result


def _reset_custom_registrations() -> None:
    """Reset all custom type registrations. For test teardown only."""
    _CUSTOM_POLICY_TYPES.clear()
    _CUSTOM_PARAMETERS_TO_POLICY_TYPE.clear()


def infer_policy_type(policy: PolicyParameters) -> PolicyType | CustomPolicyType:
    """Infer PolicyType from a policy parameters instance.

    Uses isinstance checks to handle subclasses correctly.
    Checks custom registrations first (more specific), then built-in.

    Raises:
        TemplateError: If the parameters class is not registered.
    """
    # Check custom registrations first (custom classes are more specific)
    for cls, policy_type in _CUSTOM_PARAMETERS_TO_POLICY_TYPE.items():
        if isinstance(policy, cls):
            return policy_type

    # Check built-in registrations
    for cls, policy_type in _PARAMETERS_TO_POLICY_TYPE.items():
        if isinstance(policy, cls):
            return policy_type
    msg = (
        f"Cannot infer PolicyType from {type(policy).__name__}. "
        f"Register it with register_custom_template()."
    )
    raise TemplateError(msg)


# ====================================================================
# Scenario templates
# ====================================================================


def _resolve_policy_type(
    policy: PolicyParameters,
    policy_type: PolicyType | CustomPolicyType | None,
) -> PolicyType | CustomPolicyType:
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

    Custom policy types registered via ``register_policy_type()`` and
    ``register_custom_template()`` are also supported. The JSON Schema
    validation only covers built-in types; custom types bypass JSON Schema
    and are validated at runtime by the registration registry.
    """

    name: str
    year_schedule: YearSchedule
    policy: PolicyParameters
    policy_type: PolicyType | CustomPolicyType | None = None
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
    policy_type: PolicyType | CustomPolicyType | None = None
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
