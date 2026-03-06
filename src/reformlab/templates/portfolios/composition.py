"""Portfolio YAML serialization, deserialization, and conflict detection.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
Story 12.2: Implement portfolio compatibility validation and conflict resolution
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import yaml

from reformlab.templates.portfolios.enums import ConflictType
from reformlab.templates.portfolios.exceptions import (
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
from reformlab.templates.schema import PolicyType

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Conflict:
    """Represents a detected conflict between policies in a portfolio.

    Attributes:
        conflict_type: Type of conflict detected
        policy_indices: Indices of conflicting policies in the portfolio
        parameter_name: Name of the conflicting parameter (e.g., "policy_type", "rate_schedule")
        conflicting_values: The actual conflicting values
        description: Human-readable description of the conflict
    """

    conflict_type: ConflictType
    policy_indices: tuple[int, ...]
    parameter_name: str
    conflicting_values: tuple[Any, ...]
    description: str

    def __repr__(self) -> str:
        """Readable representation of the conflict."""
        return (
            f"Conflict({self.conflict_type.value}, "
            f"indices={self.policy_indices}, "
            f"parameter={self.parameter_name})"
        )


def portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]:
    """Convert PolicyPortfolio to dictionary for YAML serialization.

    Args:
        portfolio: The portfolio to convert

    Returns:
        Dictionary with canonical structure for YAML serialization
    """
    schema_path = Path(__file__).parent.parent / "schema" / "portfolio.schema.json"
    policies_data = []
    for config in portfolio.policies:
        policy_dict: dict[str, Any] = {
            "name": config.name,
            "policy_type": config.policy_type.value,
            "policy": _policy_parameters_to_dict(config.policy),
        }
        policies_data.append(policy_dict)

    return {
        "$schema": str(schema_path),
        "name": portfolio.name,
        "version": portfolio.version,
        "description": portfolio.description,
        "policies": policies_data,
        "resolution_strategy": portfolio.resolution_strategy,
    }


def _policy_parameters_to_dict(policy: Any) -> dict[str, Any]:
    """Convert PolicyParameters to dictionary.

    Args:
        policy: PolicyParameters instance

    Returns:
        Dictionary representation
    """
    result: dict[str, Any] = {}

    # Common fields
    if hasattr(policy, "rate_schedule") and policy.rate_schedule:
        result["rate_schedule"] = dict(policy.rate_schedule)

    if hasattr(policy, "exemptions") and policy.exemptions:
        result["exemptions"] = list(policy.exemptions)

    if hasattr(policy, "thresholds") and policy.thresholds:
        result["thresholds"] = list(policy.thresholds)

    if hasattr(policy, "covered_categories") and policy.covered_categories:
        result["covered_categories"] = list(policy.covered_categories)

    # Carbon tax specific
    if hasattr(policy, "redistribution_type") and policy.redistribution_type:
        result["redistribution"] = {"type": policy.redistribution_type}
        if hasattr(policy, "income_weights") and policy.income_weights:
            result["redistribution"]["income_weights"] = dict(policy.income_weights)

    # Subsidy specific
    if hasattr(policy, "eligible_categories") and policy.eligible_categories:
        result["eligible_categories"] = list(policy.eligible_categories)

    if hasattr(policy, "income_caps") and policy.income_caps:
        result["income_caps"] = dict(policy.income_caps)

    # Rebate specific
    if hasattr(policy, "rebate_type") and policy.rebate_type:
        result["rebate_type"] = policy.rebate_type

    # Rebate income_weights (top-level field, not inside redistribution)
    if (
        hasattr(policy, "income_weights")
        and policy.income_weights
        and not hasattr(policy, "redistribution_type")
    ):
        result["income_weights"] = dict(policy.income_weights)

    # Feebate specific
    if hasattr(policy, "pivot_point") and policy.pivot_point is not None:
        result["pivot_point"] = policy.pivot_point

    if hasattr(policy, "fee_rate") and policy.fee_rate is not None:
        result["fee_rate"] = policy.fee_rate

    if hasattr(policy, "rebate_rate") and policy.rebate_rate is not None:
        result["rebate_rate"] = policy.rebate_rate

    return result


def dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio:
    """Convert dictionary to PolicyPortfolio.

    Args:
        data: Dictionary with portfolio data

    Returns:
        PolicyPortfolio instance

    Raises:
        PortfolioValidationError: If data is invalid
    """
    from reformlab.templates.schema import (
        PolicyType,
    )

    # Validate required fields
    if "name" not in data:
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason="missing required field: name",
            fix="Add 'name' field to portfolio YAML",
            invalid_fields=("name",),
        )

    if "policies" not in data:
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason="missing required field: policies",
            fix="Add 'policies' field to portfolio YAML",
            invalid_fields=("policies",),
        )

    policies_data = data.get("policies", [])
    if not isinstance(policies_data, list):
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason="'policies' must be a list",
            fix="Ensure 'policies' is a YAML list",
            invalid_fields=("policies",),
        )

    policies = []
    for idx, policy_data in enumerate(policies_data):
        if not isinstance(policy_data, dict):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"policies[{idx}] must be a mapping",
                fix=f"Ensure policies[{idx}] is a YAML mapping",
                invalid_fields=(f"policies[{idx}]",),
            )

        if "policy_type" not in policy_data:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"policies[{idx}] missing required field: policy_type",
                fix=f"Add 'policy_type' to policies[{idx}]",
                invalid_fields=(f"policies[{idx}].policy_type",),
            )

        if "policy" not in policy_data:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"policies[{idx}] missing required field: policy",
                fix=f"Add 'policy' to policies[{idx}]",
                invalid_fields=(f"policies[{idx}].policy",),
            )
        if not isinstance(policy_data["policy"], dict):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"policies[{idx}].policy must be a mapping",
                fix=f"Ensure policies[{idx}].policy is a YAML mapping",
                invalid_fields=(f"policies[{idx}].policy",),
            )

        policy_data_dict = policy_data["policy"]

        # Validate and convert policy_type
        policy_type_str = policy_data["policy_type"]
        if not isinstance(policy_type_str, str):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"policies[{idx}].policy_type must be a string, got {type(policy_type_str).__name__}",
                fix=f"Ensure policies[{idx}].policy_type is a string",
                invalid_fields=(f"policies[{idx}].policy_type",),
            )
        try:
            policy_type = PolicyType(policy_type_str)
        except (ValueError, TypeError):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"policies[{idx}] has invalid policy_type: {policy_type_str}",
                fix="Use one of: carbon_tax, subsidy, rebate, feebate",
                invalid_fields=(f"policies[{idx}].policy_type",),
            ) from None

        policy_params = _dict_to_policy_parameters(policy_data_dict, policy_type, f"policies[{idx}].policy")
        config = PolicyConfig(
            policy_type=policy_type,
            policy=policy_params,
            name=policy_data.get("name", ""),
        )
        policies.append(config)

    return PolicyPortfolio(
        name=data["name"],
        policies=tuple(policies),
        version=data.get("version", "1.0"),
        description=data.get("description", ""),
        resolution_strategy=data.get("resolution_strategy", "error"),
    )


def _dict_to_policy_parameters(data: dict[str, Any], policy_type: PolicyType, field_path: str) -> Any:
    """Convert dictionary to appropriate PolicyParameters subclass.

    Args:
        data: Policy parameters dictionary
        policy_type: Type of policy
        field_path: Field path for error messages

    Returns:
        PolicyParameters instance

    Raises:
        PortfolioValidationError: If data is invalid
    """
    from reformlab.templates.schema import (
        CarbonTaxParameters,
        FeebateParameters,
        RebateParameters,
        SubsidyParameters,
    )

    # Extract rate_schedule
    rate_schedule_data = data.get("rate_schedule", {})
    if not isinstance(rate_schedule_data, dict):
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"{field_path}.rate_schedule must be a mapping",
            fix=f"Ensure {field_path}.rate_schedule is a YAML mapping",
            invalid_fields=(f"{field_path}.rate_schedule",),
        )

    try:
        rate_schedule = {int(k): float(v) for k, v in rate_schedule_data.items()}
    except (ValueError, TypeError) as exc:
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"{field_path}.rate_schedule has invalid year/rate values: {exc}",
            fix=f"Ensure {field_path}.rate_schedule has integer years and numeric rates",
            invalid_fields=(f"{field_path}.rate_schedule",),
        ) from None

    # Build parameters based on policy type
    if policy_type == PolicyType.CARBON_TAX:
        redistribution_data = data.get("redistribution", {})
        if not isinstance(redistribution_data, dict):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.redistribution must be a mapping",
                fix=f"Ensure {field_path}.redistribution is a YAML mapping",
                invalid_fields=(f"{field_path}.redistribution",),
            )

        redistribution_type = redistribution_data.get("type", "lump_sum")
        income_weights_data = redistribution_data.get("income_weights", {})
        if not isinstance(income_weights_data, dict):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.redistribution.income_weights must be a mapping",
                fix=f"Ensure {field_path}.redistribution.income_weights is a YAML mapping",
                invalid_fields=(f"{field_path}.redistribution.income_weights",),
            )

        try:
            income_weights = {k: float(v) for k, v in income_weights_data.items()}
        except (ValueError, TypeError) as exc:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.redistribution.income_weights has invalid values: {exc}",
                fix=f"Ensure {field_path}.redistribution.income_weights has numeric values",
                invalid_fields=(f"{field_path}.redistribution.income_weights",),
            ) from None

        return CarbonTaxParameters(
            rate_schedule=rate_schedule,
            exemptions=tuple(data.get("exemptions", [])),
            thresholds=tuple(data.get("thresholds", [])),
            covered_categories=tuple(data.get("covered_categories", [])),
            redistribution_type=redistribution_type,
            income_weights=income_weights,
        )

    elif policy_type == PolicyType.SUBSIDY:
        eligible_categories_data = data.get("eligible_categories", [])
        if not isinstance(eligible_categories_data, list):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.eligible_categories must be a list",
                fix=f"Ensure {field_path}.eligible_categories is a YAML list",
                invalid_fields=(f"{field_path}.eligible_categories",),
            )

        income_caps_data = data.get("income_caps", {})
        if not isinstance(income_caps_data, dict):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.income_caps must be a mapping",
                fix=f"Ensure {field_path}.income_caps is a YAML mapping",
                invalid_fields=(f"{field_path}.income_caps",),
            )

        try:
            income_caps = {k: float(v) for k, v in income_caps_data.items()}
        except (ValueError, TypeError) as exc:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.income_caps has invalid values: {exc}",
                fix=f"Ensure {field_path}.income_caps has numeric values",
                invalid_fields=(f"{field_path}.income_caps",),
            ) from None

        return SubsidyParameters(
            rate_schedule=rate_schedule,
            exemptions=tuple(data.get("exemptions", [])),
            thresholds=tuple(data.get("thresholds", [])),
            covered_categories=tuple(data.get("covered_categories", [])),
            eligible_categories=tuple(eligible_categories_data),
            income_caps=income_caps,
        )

    elif policy_type == PolicyType.REBATE:
        rebate_type = data.get("rebate_type", "lump_sum")
        income_weights_data = data.get("income_weights", {})
        if not isinstance(income_weights_data, dict):
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.income_weights must be a mapping",
                fix=f"Ensure {field_path}.income_weights is a YAML mapping",
                invalid_fields=(f"{field_path}.income_weights",),
            )

        try:
            income_weights = {k: float(v) for k, v in income_weights_data.items()}
        except (ValueError, TypeError) as exc:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path}.income_weights has invalid values: {exc}",
                fix=f"Ensure {field_path}.income_weights has numeric values",
                invalid_fields=(f"{field_path}.income_weights",),
            ) from None

        return RebateParameters(
            rate_schedule=rate_schedule,
            exemptions=tuple(data.get("exemptions", [])),
            thresholds=tuple(data.get("thresholds", [])),
            covered_categories=tuple(data.get("covered_categories", [])),
            rebate_type=rebate_type,
            income_weights=income_weights,
        )

    elif policy_type == PolicyType.FEEBATE:
        try:
            pivot_point = float(data["pivot_point"]) if "pivot_point" in data else 0.0
            fee_rate = float(data["fee_rate"]) if "fee_rate" in data else 0.0
            rebate_rate = float(data["rebate_rate"]) if "rebate_rate" in data else 0.0
        except (ValueError, TypeError) as exc:
            raise PortfolioValidationError(
                summary="Portfolio validation failed",
                reason=f"{field_path} has invalid feebate numeric values: {exc}",
                fix=f"Ensure {field_path} pivot_point, fee_rate, and rebate_rate are numeric",
                invalid_fields=(
                    f"{field_path}.pivot_point",
                    f"{field_path}.fee_rate",
                    f"{field_path}.rebate_rate",
                ),
            ) from None

        return FeebateParameters(
            rate_schedule=rate_schedule,
            exemptions=tuple(data.get("exemptions", [])),
            thresholds=tuple(data.get("thresholds", [])),
            covered_categories=tuple(data.get("covered_categories", [])),
            pivot_point=pivot_point,
            fee_rate=fee_rate,
            rebate_rate=rebate_rate,
        )

    else:
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"Unsupported policy_type: {policy_type.value}",
            fix="Use one of: carbon_tax, subsidy, rebate, feebate",
            invalid_fields=(f"{field_path}.policy_type",),
        )


def validate_compatibility(portfolio: PolicyPortfolio) -> tuple[Conflict, ...]:
    """Validate portfolio for compatibility conflicts.

    Args:
        portfolio: The portfolio to validate

    Returns:
        Tuple of detected conflicts (empty if no conflicts)
    """
    conflicts: list[Conflict] = []

    # Detect same policy type conflicts
    for i in range(len(portfolio.policies)):
        for j in range(i + 1, len(portfolio.policies)):
            if portfolio.policies[i].policy_type == portfolio.policies[j].policy_type:
                conflict = Conflict(
                    conflict_type=ConflictType.SAME_POLICY_TYPE,
                    policy_indices=(i, j),
                    parameter_name="policy_type",
                    conflicting_values=(
                        portfolio.policies[i].policy_type.value,
                        portfolio.policies[j].policy_type.value,
                    ),
                    description=f"Both policies[{i}] and [{j}] are {portfolio.policies[i].policy_type.value}",
                )
                conflicts.append(conflict)

    # Detect overlapping years conflicts
    for i in range(len(portfolio.policies)):
        for j in range(i + 1, len(portfolio.policies)):
            policy_i_years = set(portfolio.policies[i].policy.rate_schedule.keys())
            policy_j_years = set(portfolio.policies[j].policy.rate_schedule.keys())
            overlap = policy_i_years & policy_j_years
            if overlap:
                conflict = Conflict(
                    conflict_type=ConflictType.OVERLAPPING_YEARS,
                    policy_indices=(i, j),
                    parameter_name="rate_schedule",
                    conflicting_values=(
                        tuple(sorted(policy_i_years)),
                        tuple(sorted(policy_j_years)),
                    ),
                    description=f"rate_schedule years overlap: {sorted(overlap)}",
                )
                conflicts.append(conflict)

    # Detect overlapping categories conflicts (symmetric - check all attribute combinations)
    for i in range(len(portfolio.policies)):
        for j in range(i + 1, len(portfolio.policies)):
            # Check all category attribute pairs for overlap
            for attr_i in ("covered_categories", "eligible_categories"):
                for attr_j in ("covered_categories", "eligible_categories"):
                    policy_i_cats = getattr(portfolio.policies[i].policy, attr_i, ())
                    policy_j_cats = getattr(portfolio.policies[j].policy, attr_j, ())
                    overlap = set(policy_i_cats) & set(policy_j_cats)
                    if overlap:
                        conflict = Conflict(
                            conflict_type=ConflictType.OVERLAPPING_CATEGORIES,
                            policy_indices=(i, j),
                            parameter_name=f"{attr_i} vs {attr_j}",
                            conflicting_values=(
                                tuple(sorted(policy_i_cats)),
                                tuple(sorted(policy_j_cats)),
                            ),
                            description=f"categories overlap: {sorted(overlap)}",
                        )
                        conflicts.append(conflict)

    # Detect PARAMETER_MISMATCH conflicts
    # When policies affect overlapping categories but have different parameter values
    # that affect how the policy is applied (e.g., redistribution_type, income_caps)
    for i in range(len(portfolio.policies)):
        for j in range(i + 1, len(portfolio.policies)):
            # Get overlapping categories between policies
            cats_i = set(getattr(portfolio.policies[i].policy, "covered_categories", ()))
            cats_j = set(getattr(portfolio.policies[j].policy, "covered_categories", ()))
            overlap = cats_i & cats_j

            # Only check for parameter mismatches if categories overlap
            if not overlap:
                continue

            # Check for mismatches in key parameters that affect policy application
            # Note: This is a metadata-based proxy detection as per story requirements
            params_to_check = [
                ("redistribution_type", "redistribution_type"),
                ("rebate_type", "rebate_type"),
                ("income_caps", "income_caps"),
                ("pivot_point", "pivot_point"),
            ]

            for param_name, attr_name in params_to_check:
                val_i = getattr(portfolio.policies[i].policy, attr_name, None)
                val_j = getattr(portfolio.policies[j].policy, attr_name, None)

                # Only report mismatch if both policies have the parameter and values differ
                if val_i is not None and val_j is not None and val_i != val_j:
                    conflict = Conflict(
                        conflict_type=ConflictType.PARAMETER_MISMATCH,
                        policy_indices=(i, j),
                        parameter_name=param_name,
                        conflicting_values=(str(val_i), str(val_j)),
                        description=f"{param_name} mismatch for overlapping categories: {sorted(overlap)}",
                    )
                    conflicts.append(conflict)

    # Sort conflicts by policy indices, then parameter name for deterministic ordering
    conflicts.sort(key=lambda c: (c.policy_indices[0], c.parameter_name))

    return tuple(conflicts)


def resolve_conflicts(portfolio: PolicyPortfolio, conflicts: tuple[Conflict, ...]) -> PolicyPortfolio:
    """Resolve conflicts according to portfolio's resolution strategy.

    Args:
        portfolio: The portfolio with conflicts
        conflicts: Detected conflicts

    Returns:
        New portfolio with resolved conflicts (if strategy != "error")

    Raises:
        PortfolioValidationError: If strategy is "error" and conflicts exist
    """
    if not conflicts:
        return portfolio

    if portfolio.resolution_strategy == "error":
        conflict_details = "\n".join(f"  - {c.description}" for c in conflicts)
        raise PortfolioValidationError(
            summary="Portfolio has unresolved conflicts",
            reason=f"{len(conflicts)} conflicts detected:\n{conflict_details}",
            fix="Set resolution_strategy to 'sum', 'first_wins', 'last_wins', or 'max' "
            "to automatically resolve conflicts",
            invalid_fields=tuple(f"policies[{i}]" for c in conflicts for i in c.policy_indices),
        )

    # Log warning for non-error strategies
    logger.warning(
        "event=portfolio_conflicts strategy=%s conflict_count=%d portfolio=%s",
        portfolio.resolution_strategy,
        len(conflicts),
        portfolio.name,
    )

    # Apply resolution strategy
    if portfolio.resolution_strategy == "sum":
        resolved_policies = _apply_sum_strategy(portfolio.policies, conflicts)
    elif portfolio.resolution_strategy == "first_wins":
        resolved_policies = _apply_first_wins_strategy(portfolio.policies, conflicts)
    elif portfolio.resolution_strategy == "last_wins":
        resolved_policies = _apply_last_wins_strategy(portfolio.policies, conflicts)
    elif portfolio.resolution_strategy == "max":
        resolved_policies = _apply_max_strategy(portfolio.policies, conflicts)
    else:
        # Unknown strategy - treat as error
        raise PortfolioValidationError(
            summary="Invalid resolution strategy",
            reason=f"Unknown resolution_strategy: {portfolio.resolution_strategy}",
            fix="Use one of: error, sum, first_wins, last_wins, max",
            invalid_fields=("resolution_strategy",),
        )

    # Create description suffix (idempotent - don't duplicate if already resolved)
    resolution_marker = (
        f"Resolved {len(conflicts)} conflicts using '{portfolio.resolution_strategy}' strategy."
    )
    if resolution_marker not in portfolio.description:
        description_suffix = f"\n\n{resolution_marker}"
    else:
        # Already has resolution metadata - don't add again
        description_suffix = ""

    # Return new portfolio with resolved policies
    return PolicyPortfolio(
        name=portfolio.name,
        policies=resolved_policies,
        version=portfolio.version,
        description=portfolio.description + description_suffix,
        resolution_strategy=portfolio.resolution_strategy,
    )


def _apply_sum_strategy(policies: tuple[Any, ...], conflicts: tuple[Conflict, ...]) -> tuple[Any, ...]:
    """Apply sum resolution strategy - add rates for overlapping years.

    Args:
        policies: Original policies
        conflicts: Detected conflicts

    Returns:
        New tuple of policies with resolved rate schedules
    """

    resolved = list(policies)

    # Group conflicts by overlapping years
    year_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.OVERLAPPING_YEARS]

    # For each overlapping year conflict, add the rates
    for conflict in year_conflicts:
        i, j = conflict.policy_indices[0], conflict.policy_indices[1]
        policy_i = resolved[i]
        policy_j = resolved[j]

        # Get overlapping years
        years_i = set(policy_i.policy.rate_schedule.keys())
        years_j = set(policy_j.policy.rate_schedule.keys())
        overlap_years = years_i & years_j

        # Add rates for overlapping years (apply to policy with lower index)
        new_rate_schedule = dict(policy_i.policy.rate_schedule)
        for year in overlap_years:
            new_rate_schedule[year] = (
                policy_i.policy.rate_schedule[year] + policy_j.policy.rate_schedule[year]
            )

        # Create new policy with merged rate schedule
        new_policy = replace(policy_i.policy, rate_schedule=new_rate_schedule)
        resolved[i] = replace(policy_i, policy=new_policy)

    return tuple(resolved)


def _apply_first_wins_strategy(policies: tuple[Any, ...], conflicts: tuple[Conflict, ...]) -> tuple[Any, ...]:
    """Apply first_wins resolution strategy - use first policy's values.

    Args:
        policies: Original policies
        conflicts: Detected conflicts

    Returns:
        Original policies tuple (first policy already wins by definition)
    """
    # First policy wins by definition - no changes needed
    return policies


def _apply_last_wins_strategy(policies: tuple[Any, ...], conflicts: tuple[Conflict, ...]) -> tuple[Any, ...]:
    """Apply last_wins resolution strategy - use last policy's values.

    Args:
        policies: Original policies
        conflicts: Detected conflicts

    Returns:
        New tuple with last conflicting policy values
    """

    resolved = list(policies)

    # For overlapping years, use last policy's rates
    year_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.OVERLAPPING_YEARS]

    for conflict in year_conflicts:
        i, j = conflict.policy_indices[0], conflict.policy_indices[1]
        policy_i = resolved[i]
        policy_j = resolved[j]

        # Get overlapping years
        years_i = set(policy_i.policy.rate_schedule.keys())
        years_j = set(policy_j.policy.rate_schedule.keys())
        overlap_years = years_i & years_j

        # Use last policy's rates for overlapping years
        new_rate_schedule = dict(policy_i.policy.rate_schedule)
        for year in overlap_years:
            new_rate_schedule[year] = policy_j.policy.rate_schedule[year]

        # Create new policy with updated rate schedule
        new_policy = replace(policy_i.policy, rate_schedule=new_rate_schedule)
        resolved[i] = replace(policy_i, policy=new_policy)

    return tuple(resolved)


def _apply_max_strategy(policies: tuple[Any, ...], conflicts: tuple[Conflict, ...]) -> tuple[Any, ...]:
    """Apply max resolution strategy - use maximum rate for overlapping years.

    Args:
        policies: Original policies
        conflicts: Detected conflicts

    Returns:
        New tuple of policies with maximum rates applied
    """

    resolved = list(policies)

    # For overlapping years, use maximum rate
    year_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.OVERLAPPING_YEARS]

    for conflict in year_conflicts:
        i, j = conflict.policy_indices[0], conflict.policy_indices[1]
        policy_i = resolved[i]
        policy_j = resolved[j]

        # Get overlapping years
        years_i = set(policy_i.policy.rate_schedule.keys())
        years_j = set(policy_j.policy.rate_schedule.keys())
        overlap_years = years_i & years_j

        # Use maximum rate for overlapping years
        new_rate_schedule = dict(policy_i.policy.rate_schedule)
        for year in overlap_years:
            new_rate_schedule[year] = max(
                policy_i.policy.rate_schedule[year], policy_j.policy.rate_schedule[year]
            )

        # Create new policy with updated rate schedule
        new_policy = replace(policy_i.policy, rate_schedule=new_rate_schedule)
        resolved[i] = replace(policy_i, policy=new_policy)

    return tuple(resolved)


def dump_portfolio(portfolio: PolicyPortfolio, path: Path | str) -> None:
    """Serialize portfolio to YAML file with canonical formatting.

    Args:
        portfolio: The portfolio to serialize
        path: Output file path
    """
    file_path = Path(path)
    data = portfolio_to_dict(portfolio)

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=True)


def load_portfolio(path: Path | str, validate: bool = True) -> PolicyPortfolio:
    """Load portfolio from YAML file.

    Args:
        path: Path to YAML file
        validate: Whether to validate for conflicts (default: True)

    Returns:
        PolicyPortfolio instance

    Raises:
        PortfolioSerializationError: If file not found or invalid YAML
        PortfolioValidationError: If data is invalid or conflicts detected
    """
    file_path = Path(path)

    if not file_path.exists():
        raise PortfolioSerializationError(
            summary="Portfolio load failed",
            reason=f"file was not found: {file_path}",
            fix="Provide an existing .yaml or .yml portfolio file path",
            file_path=file_path,
        )

    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise PortfolioSerializationError(
            summary="Portfolio load failed",
            reason=f"invalid YAML syntax: {exc}",
            fix="Fix the YAML syntax errors in the portfolio file",
            file_path=file_path,
        ) from None

    if not isinstance(data, dict):
        raise PortfolioValidationError(
            summary="Portfolio load failed",
            reason="portfolio file must contain a YAML mapping (dict)",
            fix="Ensure the file has top-level keys: name, version, policies",
            file_path=file_path,
        )

    portfolio = dict_to_portfolio(data)

    # Validate for conflicts if requested
    if validate:
        conflicts = validate_compatibility(portfolio)
        portfolio = resolve_conflicts(portfolio, conflicts)

    return portfolio
