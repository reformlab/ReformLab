from __future__ import annotations

from pathlib import Path
from typing import Any

from reformlab.templates.exceptions import ScenarioError
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    RebateParameters,
    ReformScenario,
    SubsidyParameters,
)


def resolve_reform_definition(
    reform: ReformScenario,
    baseline: BaselineScenario,
) -> BaselineScenario:
    """Merge a reform scenario with its baseline to produce a resolved scenario.

    This function implements the reform-as-delta pattern where reforms inherit
    unspecified parameters from their linked baseline. The result is a
    BaselineScenario with all parameters fully specified.

    Args:
        reform: The reform scenario with parameter overrides.
        baseline: The baseline scenario to inherit from.

    Returns:
        A new BaselineScenario with reform overrides applied to baseline values.

    Raises:
        ScenarioError: If policy types don't match between reform and baseline.
    """
    # Validate policy type match
    if reform.policy_type != baseline.policy_type:
        raise ScenarioError(
            file_path=Path("<in-memory>"),
            summary="Reform resolution failed",
            reason=(
                f"policy_type mismatch: reform has '{reform.policy_type.value}', "
                f"baseline has '{baseline.policy_type.value}'"
            ),
            fix="Ensure reform and baseline have the same policy_type",
            invalid_fields=("policy_type",),
        )

    # Resolve year_schedule: use reform's if specified, otherwise baseline's
    if reform.year_schedule:
        year_schedule = reform.year_schedule
    else:
        year_schedule = baseline.year_schedule

    # Merge parameters
    merged_params = _merge_parameters(reform.parameters, baseline.parameters)

    return BaselineScenario(
        name=reform.name,
        policy_type=reform.policy_type,
        year_schedule=year_schedule,
        parameters=merged_params,
        description=reform.description,
        version=reform.version,
        schema_ref=reform.schema_ref or baseline.schema_ref,
    )


def _merge_parameters(
    reform_params: PolicyParameters,
    baseline_params: PolicyParameters,
) -> PolicyParameters:
    """Merge reform parameters with baseline, reform values take precedence.

    For rate_schedule, deep merge is performed: reform values override,
    baseline fills gaps.
    """
    # Deep merge rate_schedule
    merged_rate_schedule = dict(baseline_params.rate_schedule)
    merged_rate_schedule.update(reform_params.rate_schedule)

    # For tuple fields, use reform if non-empty, otherwise baseline
    exemptions = reform_params.exemptions or baseline_params.exemptions
    thresholds = reform_params.thresholds or baseline_params.thresholds
    if reform_params.covered_categories:
        covered_categories = reform_params.covered_categories
    else:
        covered_categories = baseline_params.covered_categories

    # Handle subclass-specific fields
    is_carbon = isinstance(reform_params, CarbonTaxParameters)
    is_carbon = is_carbon or isinstance(baseline_params, CarbonTaxParameters)
    if is_carbon:
        return CarbonTaxParameters(
            rate_schedule=merged_rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
        )

    is_subsidy = isinstance(reform_params, SubsidyParameters)
    is_subsidy = is_subsidy or isinstance(baseline_params, SubsidyParameters)
    if is_subsidy:
        return _merge_subsidy_params(
            reform_params, baseline_params,
            merged_rate_schedule, exemptions, thresholds, covered_categories,
        )

    is_rebate = isinstance(reform_params, RebateParameters)
    is_rebate = is_rebate or isinstance(baseline_params, RebateParameters)
    if is_rebate:
        return _merge_rebate_params(
            reform_params, baseline_params,
            merged_rate_schedule, exemptions, thresholds, covered_categories,
        )

    is_feebate = isinstance(reform_params, FeebateParameters)
    is_feebate = is_feebate or isinstance(baseline_params, FeebateParameters)
    if is_feebate:
        return _merge_feebate_params(
            reform_params, baseline_params,
            merged_rate_schedule, exemptions, thresholds, covered_categories,
        )

    # Generic parameters
    return PolicyParameters(
        rate_schedule=merged_rate_schedule,
        exemptions=exemptions,
        thresholds=thresholds,
        covered_categories=covered_categories,
    )


def _merge_subsidy_params(
    reform_params: PolicyParameters,
    baseline_params: PolicyParameters,
    rate_schedule: dict[int, float],
    exemptions: tuple[dict[str, Any], ...],
    thresholds: tuple[dict[str, Any], ...],
    covered_categories: tuple[str, ...],
) -> SubsidyParameters:
    """Merge subsidy-specific parameters."""
    reform_sub: SubsidyParameters | None = None
    base_sub: SubsidyParameters | None = None
    if isinstance(reform_params, SubsidyParameters):
        reform_sub = reform_params
    if isinstance(baseline_params, SubsidyParameters):
        base_sub = baseline_params

    if reform_sub and reform_sub.eligible_categories:
        eligible_categories = reform_sub.eligible_categories
    elif base_sub:
        eligible_categories = base_sub.eligible_categories
    else:
        eligible_categories = ()

    income_caps: dict[int, float] = dict(base_sub.income_caps if base_sub else {})
    if reform_sub and reform_sub.income_caps:
        income_caps.update(reform_sub.income_caps)

    return SubsidyParameters(
        rate_schedule=rate_schedule,
        exemptions=exemptions,
        thresholds=thresholds,
        covered_categories=covered_categories,
        eligible_categories=eligible_categories,
        income_caps=income_caps,
    )


def _merge_rebate_params(
    reform_params: PolicyParameters,
    baseline_params: PolicyParameters,
    rate_schedule: dict[int, float],
    exemptions: tuple[dict[str, Any], ...],
    thresholds: tuple[dict[str, Any], ...],
    covered_categories: tuple[str, ...],
) -> RebateParameters:
    """Merge rebate-specific parameters."""
    reform_reb: RebateParameters | None = None
    base_reb: RebateParameters | None = None
    if isinstance(reform_params, RebateParameters):
        reform_reb = reform_params
    if isinstance(baseline_params, RebateParameters):
        base_reb = baseline_params

    if reform_reb and reform_reb.rebate_type:
        rebate_type = reform_reb.rebate_type
    elif base_reb:
        rebate_type = base_reb.rebate_type
    else:
        rebate_type = ""

    income_weights: dict[str, float] = dict(
        base_reb.income_weights if base_reb else {}
    )
    if reform_reb and reform_reb.income_weights:
        income_weights.update(reform_reb.income_weights)

    return RebateParameters(
        rate_schedule=rate_schedule,
        exemptions=exemptions,
        thresholds=thresholds,
        covered_categories=covered_categories,
        rebate_type=rebate_type,
        income_weights=income_weights,
    )


def _merge_feebate_params(
    reform_params: PolicyParameters,
    baseline_params: PolicyParameters,
    rate_schedule: dict[int, float],
    exemptions: tuple[dict[str, Any], ...],
    thresholds: tuple[dict[str, Any], ...],
    covered_categories: tuple[str, ...],
) -> FeebateParameters:
    """Merge feebate-specific parameters."""
    reform_fee: FeebateParameters | None = None
    base_fee: FeebateParameters | None = None
    if isinstance(reform_params, FeebateParameters):
        reform_fee = reform_params
    if isinstance(baseline_params, FeebateParameters):
        base_fee = baseline_params

    if reform_fee and reform_fee.pivot_point:
        pivot_point = reform_fee.pivot_point
    elif base_fee:
        pivot_point = base_fee.pivot_point
    else:
        pivot_point = 0.0

    if reform_fee and reform_fee.fee_rate:
        fee_rate = reform_fee.fee_rate
    elif base_fee:
        fee_rate = base_fee.fee_rate
    else:
        fee_rate = 0.0

    if reform_fee and reform_fee.rebate_rate:
        rebate_rate = reform_fee.rebate_rate
    elif base_fee:
        rebate_rate = base_fee.rebate_rate
    else:
        rebate_rate = 0.0

    return FeebateParameters(
        rate_schedule=rate_schedule,
        exemptions=exemptions,
        thresholds=thresholds,
        covered_categories=covered_categories,
        pivot_point=pivot_point,
        fee_rate=fee_rate,
        rebate_rate=rebate_rate,
    )
