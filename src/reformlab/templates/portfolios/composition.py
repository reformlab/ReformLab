"""Portfolio YAML serialization and deserialization.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from reformlab.templates.portfolios.exceptions import (
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
from reformlab.templates.schema import (
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    SubsidyParameters,
)

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = "1.0"
_SCHEMA_DIR = Path(__file__).parent.parent / "schema"


def get_portfolio_schema_path() -> Path:
    """Return path to portfolio JSON Schema."""
    return _SCHEMA_DIR / "portfolio.schema.json"


def _load_schema() -> dict[str, Any]:
    """Load portfolio JSON Schema from disk."""
    schema_path = get_portfolio_schema_path()
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]:
    """Convert PolicyPortfolio to dictionary with deterministic ordering.

    Keys are sorted alphabetically for canonical output.

    Args:
        portfolio: The portfolio to convert

    Returns:
        Dictionary with canonical key ordering
    """
    data: dict[str, Any] = {}

    data["$schema"] = "./schema/portfolio.schema.json"
    data["version"] = portfolio.version
    data["name"] = portfolio.name

    if portfolio.description:
        data["description"] = portfolio.description

    policies_list = []
    for config in portfolio.policies:
        policy_dict: dict[str, Any] = {}
        if config.name:
            policy_dict["name"] = config.name
        policy_dict["policy_type"] = config.policy_type.value
        policy_dict["policy"] = _policy_params_to_dict(config.policy)
        policies_list.append(policy_dict)

    data["policies"] = policies_list

    return data


def _policy_params_to_dict(params: PolicyParameters) -> dict[str, Any]:
    """Convert PolicyParameters to dictionary for YAML serialization."""
    result: dict[str, Any] = {}

    if params.rate_schedule:
        result["rate_schedule"] = params.rate_schedule

    if params.exemptions:
        result["exemptions"] = list(params.exemptions)

    if params.thresholds:
        result["thresholds"] = list(params.thresholds)

    if params.covered_categories:
        result["covered_categories"] = list(params.covered_categories)

    if isinstance(params, CarbonTaxParameters):
        if params.redistribution_type or params.income_weights:
            redistribution: dict[str, Any] = {}
            if params.redistribution_type:
                redistribution["type"] = params.redistribution_type
            if params.income_weights:
                redistribution["income_weights"] = params.income_weights
            result["redistribution"] = redistribution
    elif isinstance(params, SubsidyParameters):
        if params.eligible_categories:
            result["eligible_categories"] = list(params.eligible_categories)
        if params.income_caps:
            result["income_caps"] = params.income_caps
    elif isinstance(params, RebateParameters):
        if params.rebate_type:
            result["rebate_type"] = params.rebate_type
        if params.income_weights:
            result["income_weights"] = params.income_weights
    elif isinstance(params, FeebateParameters):
        if params._pivot_point_set or params.pivot_point != 0.0:
            result["pivot_point"] = params.pivot_point
        if params._fee_rate_set or params.fee_rate != 0.0:
            result["fee_rate"] = params.fee_rate
        if params._rebate_rate_set or params.rebate_rate != 0.0:
            result["rebate_rate"] = params.rebate_rate

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
    try:
        schema = _load_schema()
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"Schema validation error: {e.message}",
            fix="Ensure portfolio YAML follows the schema structure",
            invalid_fields=(e.json_path,),
        ) from None
    except jsonschema.SchemaError as e:
        logger.error("Schema error: %s", e)
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"Invalid schema: {e}",
            fix="Check portfolio.schema.json file",
        ) from None

    name = str(data["name"])
    version = str(data.get("version", _SCHEMA_VERSION))
    description = str(data.get("description", ""))

    policies_list = []
    for idx, policy_data in enumerate(data["policies"]):
        policy_name = str(policy_data.get("name", ""))
        policy_type_str = str(policy_data["policy_type"])
        policy_type = PolicyType(policy_type_str)
        policy_params_data = policy_data["policy"]

        policy_params = _dict_to_policy_params(policy_type, policy_params_data)
        config = PolicyConfig(
            policy_type=policy_type,
            policy=policy_params,
            name=policy_name,
        )
        policies_list.append(config)

    portfolio = PolicyPortfolio(
        name=name,
        policies=tuple(policies_list),
        version=version,
        description=description,
    )

    return portfolio


def _dict_to_policy_params(policy_type: PolicyType, raw: dict[str, Any]) -> PolicyParameters:
    """Parse policy parameters from dict based on policy type."""
    rate_schedule: dict[int, float] = {}
    if "rate_schedule" in raw:
        raw_rate = raw["rate_schedule"]
        if not isinstance(raw_rate, dict):
            raise PortfolioValidationError(
                summary="Policy validation failed",
                reason="policy.rate_schedule must be a mapping",
                fix="Set rate_schedule as a YAML object with numeric values",
                invalid_fields=("policy.rate_schedule",),
            )
        try:
            for k, v in raw_rate.items():
                rate_schedule[int(k)] = float(v)
        except (TypeError, ValueError):
            raise PortfolioValidationError(
                summary="Policy validation failed",
                reason="policy.rate_schedule contains non-numeric year or value",
                fix="Use integer-like years and numeric rate values in rate_schedule",
                invalid_fields=("policy.rate_schedule",),
            ) from None

    exemptions = tuple(raw.get("exemptions", []))
    thresholds = tuple(raw.get("thresholds", []))
    covered_categories = tuple(raw.get("covered_categories", []))

    if policy_type == PolicyType.CARBON_TAX:
        redistribution_type = ""
        income_weights: dict[str, float] = {}
        if "redistribution" in raw:
            redist = raw["redistribution"]
            if not isinstance(redist, dict):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.redistribution must be a mapping",
                    fix="Set redistribution as a YAML object with type/income_weights",
                    invalid_fields=("policy.redistribution",),
                )
            if "type" in redist:
                redistribution_type = str(redist["type"])
            if "income_weights" in redist:
                raw_weights = redist["income_weights"]
                if not isinstance(raw_weights, dict):
                    raise PortfolioValidationError(
                        summary="Policy validation failed",
                        reason="policy.redistribution.income_weights must be a mapping",
                        fix="Set income_weights as decile -> numeric weight pairs",
                        invalid_fields=("policy.redistribution.income_weights",),
                    )
                try:
                    for k, v in raw_weights.items():
                        income_weights[str(k)] = float(v)
                except (TypeError, ValueError):
                    raise PortfolioValidationError(
                        summary="Policy validation failed",
                        reason="policy.redistribution.income_weights has non-numeric values",
                        fix="Use numeric values for all redistribution income_weights",
                        invalid_fields=("policy.redistribution.income_weights",),
                    ) from None
        return CarbonTaxParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            redistribution_type=redistribution_type,
            income_weights=income_weights,
        )
    elif policy_type == PolicyType.SUBSIDY:
        eligible_categories = tuple(raw.get("eligible_categories", []))
        income_caps: dict[int, float] = {}
        if "income_caps" in raw:
            raw_caps = raw["income_caps"]
            if not isinstance(raw_caps, dict):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_caps must be a mapping",
                    fix="Set income_caps as a YAML object with numeric values",
                    invalid_fields=("policy.income_caps",),
                )
            try:
                for k, v in raw_caps.items():
                    income_caps[int(k)] = float(v)
            except (TypeError, ValueError):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_caps contains non-numeric year or value",
                    fix="Use integer-like years and numeric values in income_caps",
                    invalid_fields=("policy.income_caps",),
                ) from None
        return SubsidyParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            eligible_categories=eligible_categories,
            income_caps=income_caps,
        )
    elif policy_type == PolicyType.REBATE:
        rebate_type = str(raw.get("rebate_type", ""))
        rebate_weights: dict[str, float] = {}
        if "income_weights" in raw:
            raw_weights = raw["income_weights"]
            if not isinstance(raw_weights, dict):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_weights must be a mapping",
                    fix="Set income_weights as decile -> numeric weight pairs",
                    invalid_fields=("policy.income_weights",),
                )
            try:
                for k, v in raw_weights.items():
                    rebate_weights[str(k)] = float(v)
            except (TypeError, ValueError):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_weights has non-numeric values",
                    fix="Use numeric values for all income_weights",
                    invalid_fields=("policy.income_weights",),
                ) from None
        return RebateParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            rebate_type=rebate_type,
            income_weights=rebate_weights,
        )
    elif policy_type == PolicyType.FEEBATE:
        pivot_point_set = "pivot_point" in raw
        fee_rate_set = "fee_rate" in raw
        rebate_rate_set = "rebate_rate" in raw
        try:
            pivot_point = float(raw.get("pivot_point", 0.0))
            fee_rate = float(raw.get("fee_rate", 0.0))
            rebate_rate = float(raw.get("rebate_rate", 0.0))
        except (TypeError, ValueError):
            raise PortfolioValidationError(
                summary="Policy validation failed",
                reason="feebate numeric fields must be numbers",
                fix="Use numeric values for pivot_point, fee_rate, and rebate_rate",
                invalid_fields=("policy",),
            ) from None
        return FeebateParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            pivot_point=pivot_point,
            fee_rate=fee_rate,
            rebate_rate=rebate_rate,
            _pivot_point_set=pivot_point_set,
            _fee_rate_set=fee_rate_set,
            _rebate_rate_set=rebate_rate_set,
        )
    else:
        return PolicyParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
        )


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


def load_portfolio(path: Path | str) -> PolicyPortfolio:
    """Load portfolio from YAML file.

    Args:
        path: Path to YAML file

    Returns:
        PolicyPortfolio instance

    Raises:
        PortfolioSerializationError: If file not found or invalid YAML
        PortfolioValidationError: If data is invalid
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
    return portfolio
