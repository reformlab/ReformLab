# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Domain-layer translation for live OpenFisca execution.

Story 24.2: Translates domain PolicyParameters into a format compatible
with the adapter's policy parameter handling. The translation boundary
sits between the domain layer (PolicyParameters dataclasses) and the
computation adapter. The adapter remains generic and unaware of
domain-specific policy semantics.

Translation functions validate that the policy parameters are structurally
correct for live execution and pass them through to the adapter, which
handles typed PolicyParameters via its existing contract. The primary
purpose of this layer is:

1. Validate domain-specific constraints before adapter invocation
2. Confirm the policy type is supported for live execution
3. Provide actionable error messages when translation fails

The adapter's compute() method receives the typed PolicyParameters via
PolicyConfig.policy — no dict conversion is needed. The adapter already
handles typed policies by using TBS defaults with population data.
"""

from __future__ import annotations

from collections.abc import Callable

from reformlab.templates.schema import PolicyParameters

_TranslatorFn = Callable[[PolicyParameters, str], PolicyParameters]


class TranslationError(Exception):
    """Structured translation error following project error pattern.

    Attributes:
        what: High-level description of what failed.
        why: Detailed reason for failure.
        fix: Actionable guidance to resolve issue.
    """

    def __init__(self, *, what: str, why: str, fix: str) -> None:
        self.what = what
        self.why = why
        self.fix = fix
        message = f"{what} — {why} — {fix}"
        super().__init__(message)


def translate_policy(
    policy: PolicyParameters,
    template_name: str,
) -> PolicyParameters:
    """Translate a domain policy for live OpenFisca execution.

    Dispatches to the appropriate translator based on policy type.
    For policy types that don't need translation (carbon_tax, rebate,
    feebate), returns the policy unchanged.

    Args:
        policy: Domain policy parameters instance.
        template_name: Template name for error messages.

    Returns:
        The validated policy, ready for adapter consumption.

    Raises:
        TranslationError: If the policy cannot be translated.
    """
    from reformlab.templates.schema import infer_policy_type

    policy_type = infer_policy_type(policy)
    policy_type_str = policy_type.value if hasattr(policy_type, "value") else str(policy_type)

    _TRANSLATORS: dict[str, _TranslatorFn] = {
        "subsidy": _translate_subsidy_policy,
        "vehicle_malus": _translate_vehicle_malus_policy,
        "energy_poverty_aid": _translate_energy_poverty_aid_policy,
    }

    # Types that pass through without translation
    _PASSTHROUGH_TYPES = {"carbon_tax", "rebate", "feebate"}

    if policy_type_str in _PASSTHROUGH_TYPES:
        return policy

    translator = _TRANSLATORS.get(policy_type_str)
    if translator is None:
        raise TranslationError(
            what=f"Translation failed for policy type '{policy_type_str}'",
            why=(
                f"Policy type '{policy_type_str}' is not supported for "
                f"live OpenFisca execution in this release"
            ),
            fix=(
                f"Supported types for live execution: "
                f"{', '.join(sorted(_PASSTHROUGH_TYPES | set(_TRANSLATORS.keys())))}. "
                f"See future stories for additional policy type support."
            ),
        )

    return translator(policy, template_name)


def _translate_subsidy_policy(
    policy: PolicyParameters,
    template_name: str,
) -> PolicyParameters:
    """Validate and pass through SubsidyParameters for live execution.

    Validates that the subsidy policy has the required fields for live
    OpenFisca execution. The adapter receives the typed policy directly.

    Args:
        policy: SubsidyParameters instance.
        template_name: Template name for error context.

    Returns:
        The validated policy instance.

    Raises:
        TranslationError: If required fields are missing or invalid.
    """
    from reformlab.templates.schema import SubsidyParameters

    if not isinstance(policy, SubsidyParameters):
        raise TranslationError(
            what=f"Translation failed for template '{template_name}'",
            why=f"Expected SubsidyParameters, got {type(policy).__name__}",
            fix="Ensure the policy is a SubsidyParameters instance",
        )

    if not policy.rate_schedule:
        raise TranslationError(
            what=f"Translation failed for template '{template_name}'",
            why="rate_schedule is required for subsidy translation but is empty",
            fix="Add at least one year entry to rate_schedule (e.g. {2025: 5000.0})",
        )

    return policy


def _translate_vehicle_malus_policy(
    policy: PolicyParameters,
    template_name: str,
) -> PolicyParameters:
    """Validate and pass through VehicleMalusParameters for live execution.

    Args:
        policy: VehicleMalusParameters instance.
        template_name: Template name for error context.

    Returns:
        The validated policy instance.

    Raises:
        TranslationError: If required fields are missing or invalid.
    """
    from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters

    if not isinstance(policy, VehicleMalusParameters):
        raise TranslationError(
            what=f"Translation failed for template '{template_name}'",
            why=f"Expected VehicleMalusParameters, got {type(policy).__name__}",
            fix="Ensure the policy is a VehicleMalusParameters instance",
        )

    if policy.emission_threshold < 0:
        raise TranslationError(
            what=f"Translation failed for template '{template_name}'",
            why=f"emission_threshold must be >= 0, got {policy.emission_threshold}",
            fix="Set emission_threshold to a non-negative value",
        )

    if policy.malus_rate_per_gkm < 0:
        raise TranslationError(
            what=f"Translation failed for template '{template_name}'",
            why=f"malus_rate_per_gkm must be >= 0, got {policy.malus_rate_per_gkm}",
            fix="Set malus_rate_per_gkm to a non-negative value",
        )

    return policy


def _translate_energy_poverty_aid_policy(
    policy: PolicyParameters,
    template_name: str,
) -> PolicyParameters:
    """Validate and pass through EnergyPovertyAidParameters for live execution.

    Args:
        policy: EnergyPovertyAidParameters instance.
        template_name: Template name for error context.

    Returns:
        The validated policy instance.

    Raises:
        TranslationError: If required fields are missing or invalid.
    """
    from reformlab.templates.energy_poverty_aid.compute import EnergyPovertyAidParameters

    if not isinstance(policy, EnergyPovertyAidParameters):
        raise TranslationError(
            what=f"Translation failed for template '{template_name}'",
            why=f"Expected EnergyPovertyAidParameters, got {type(policy).__name__}",
            fix="Ensure the policy is an EnergyPovertyAidParameters instance",
        )

    if policy.income_ceiling <= 0:
        raise TranslationError(
            what=f"Translation failed for template '{template_name}'",
            why=f"income_ceiling must be > 0, got {policy.income_ceiling}",
            fix="Set income_ceiling to a positive value",
        )

    if policy.base_aid_amount < 0:
        raise TranslationError(
            what=f"Translation failed for template '{template_name}'",
            why=f"base_aid_amount must be >= 0, got {policy.base_aid_amount}",
            fix="Set base_aid_amount to a non-negative value",
        )

    return policy
