from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from reformlab.templates.exceptions import ScenarioError
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    CustomPolicyType,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    ReformScenario,
    SubsidyParameters,
    YearSchedule,
    get_policy_type,
)

logger = logging.getLogger(__name__)

# Schema version supported by this loader
SCHEMA_VERSION = "1.0"
_SCHEMA_MAJOR_VERSION = 1

# policy_type is intentionally required in YAML pack files for readability,
# even though it is optional on the Python constructor (inferred from policy).
_REQUIRED_FIELDS = frozenset({"name", "policy_type", "version", "policy"})
_VALID_POLICY_TYPES = frozenset(pt.value for pt in PolicyType)
_MIN_YEAR_SCHEDULE_DURATION = 10
_SCHEMA_DIR = Path(__file__).parent / "schema"


def get_schema_path() -> Path:
    """Return the path to the JSON Schema file."""
    return _SCHEMA_DIR / "scenario-template.schema.json"


def validate_schema_version(
    version: str,
    *,
    strict: bool = False,
    file_path: Path | None = None,
) -> None:
    """Validate that a schema version is compatible with this loader.

    Args:
        version: The version string to validate (e.g., "1.0").
        strict: If True, raise on any version mismatch.
        file_path: Optional file path for error messages.

    Raises:
        ScenarioError: If version is incompatible (major version mismatch).
    """
    try:
        parts = version.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        logger.warning("Invalid schema version format: %s", version)
        return

    if major != _SCHEMA_MAJOR_VERSION:
        msg = (
            f"Schema version {version} is not compatible "
            f"with loader version {SCHEMA_VERSION}"
        )
        if strict:
            raise ScenarioError(
                file_path=file_path or Path("<unknown>"),
                summary="Schema version mismatch",
                reason=msg,
                fix=f"Update template to schema version {SCHEMA_VERSION} or migrate",
                invalid_fields=("version",),
            )
        else:
            logger.warning("%s", msg)
    elif minor > int(SCHEMA_VERSION.split(".")[1]):
        logger.warning(
            "Schema version %s is newer than loader version %s",
            version,
            SCHEMA_VERSION,
        )


def load_scenario_template(
    path: str | Path,
    *,
    strict: bool = False,
) -> BaselineScenario | ReformScenario:
    """Load a YAML scenario template file and return a validated scenario.

    Args:
        path: Path to the YAML scenario template file.
        strict: If True, year schedules < 10 years raise errors instead of warnings.

    Returns:
        BaselineScenario if no baseline_ref, ReformScenario otherwise.

    Raises:
        ScenarioError: If the file is invalid, missing required fields, or
            contains unknown policy types.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise ScenarioError(
            file_path=file_path,
            summary="Scenario load failed",
            reason="scenario file was not found",
            fix="Provide an existing .yaml or .yml scenario template file path",
        )

    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ScenarioError(
            file_path=file_path,
            summary="Scenario load failed",
            reason=f"invalid YAML syntax: {exc}",
            fix="Fix the YAML syntax errors in the scenario template file",
        ) from None

    if not isinstance(data, dict):
        raise ScenarioError(
            file_path=file_path,
            summary="Scenario load failed",
            reason="scenario file must contain a YAML mapping (dict)",
            fix="Ensure the file has top-level keys: name, policy_type, version",
        )

    _validate_required_fields(file_path, data)
    _validate_policy_type(file_path, data)

    policy_type = get_policy_type(data["policy_type"])
    name = str(data["name"])
    version = str(data["version"])
    validate_schema_version(version, strict=strict, file_path=file_path)
    description = str(data.get("description", ""))
    schema_ref = str(data.get("$schema", ""))
    baseline_ref = data.get("baseline_ref")

    # Parse year_schedule if present
    year_schedule = None
    if "year_schedule" in data:
        year_schedule = _parse_year_schedule(file_path, data["year_schedule"], strict)

    # Parse policy
    raw_params = data.get("policy")
    if raw_params is None:
        raise ScenarioError(
            file_path=file_path,
            summary="Scenario validation failed",
            reason="missing required field: policy",
            fix="Add a non-empty policy mapping with policy parameter values",
            invalid_fields=("policy",),
        )
    if not isinstance(raw_params, dict):
        raise ScenarioError(
            file_path=file_path,
            summary="Scenario validation failed",
            reason="policy must be a mapping (dict)",
            fix="Define policy as a YAML object with policy fields",
            invalid_fields=("policy",),
        )
    if not raw_params:
        raise ScenarioError(
            file_path=file_path,
            summary="Scenario validation failed",
            reason="policy must include at least one policy value",
            fix="Add one or more parameter fields under policy",
            invalid_fields=("policy",),
        )
    parsed_policy = _parse_policy(file_path, policy_type, raw_params)

    if baseline_ref:
        # Reform scenario
        return ReformScenario(
            name=name,
            policy_type=policy_type,
            baseline_ref=str(baseline_ref),
            policy=parsed_policy,
            description=description,
            version=version,
            schema_ref=schema_ref,
            year_schedule=year_schedule,
        )
    else:
        # Baseline scenario - year_schedule is required
        if year_schedule is None:
            raise ScenarioError(
                file_path=file_path,
                summary="Scenario validation failed",
                reason="baseline scenarios require year_schedule",
                fix="Add year_schedule with start_year and end_year",
                invalid_fields=("year_schedule",),
            )
        return BaselineScenario(
            name=name,
            policy_type=policy_type,
            year_schedule=year_schedule,
            policy=parsed_policy,
            description=description,
            version=version,
            schema_ref=schema_ref,
        )


def dump_scenario_template(
    scenario: BaselineScenario | ReformScenario,
    path: str | Path,
) -> None:
    """Serialize a scenario to a YAML file.

    Args:
        scenario: The scenario to serialize.
        path: Output file path.
    """
    file_path = Path(path)
    data = _scenario_to_dict(scenario)

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def _validate_required_fields(file_path: Path, data: dict[str, Any]) -> None:
    """Check for required top-level fields."""
    missing = _REQUIRED_FIELDS - set(data.keys())
    if missing:
        names = ", ".join(sorted(missing))
        raise ScenarioError(
            file_path=file_path,
            summary="Scenario validation failed",
            reason=f"missing required fields: {names}",
            fix=f"Add the following fields to the scenario file: {names}",
            invalid_fields=tuple(sorted(missing)),
        )


def _get_all_valid_policy_types() -> frozenset[str]:
    """Return all valid policy type strings (built-in + registered custom)."""
    from reformlab.templates.schema import _CUSTOM_POLICY_TYPES

    return _VALID_POLICY_TYPES | frozenset(_CUSTOM_POLICY_TYPES.keys())


def _validate_policy_type(file_path: Path, data: dict[str, Any]) -> None:
    """Validate policy_type is one of the supported values (built-in or custom)."""
    policy_type = data.get("policy_type")
    all_valid = _get_all_valid_policy_types()
    if policy_type not in all_valid:
        valid_types = ", ".join(sorted(all_valid))
        raise ScenarioError(
            file_path=file_path,
            summary="Scenario validation failed",
            reason=f"unknown policy_type '{policy_type}'",
            fix=f"Use one of the valid policy types: {valid_types}",
            invalid_fields=("policy_type",),
        )


def _parse_year_schedule(
    file_path: Path,
    raw: dict[str, Any],
    strict: bool,
) -> YearSchedule:
    """Parse year_schedule from raw YAML data."""
    try:
        start_year = int(raw["start_year"])
        end_year = int(raw["end_year"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ScenarioError(
            file_path=file_path,
            summary="Scenario validation failed",
            reason=f"invalid year_schedule: {exc}",
            fix="year_schedule must have integer start_year and end_year",
            invalid_fields=("year_schedule",),
        ) from None

    year_schedule = YearSchedule(start_year=start_year, end_year=end_year)

    # Warn or error if duration < 10 years
    min_years = _MIN_YEAR_SCHEDULE_DURATION
    if year_schedule.duration < min_years:
        msg = (
            f"Year schedule has only {year_schedule.duration} years "
            f"({start_year}-{end_year}), recommended minimum is {min_years} years"
        )
        if strict:
            raise ScenarioError(
                file_path=file_path,
                summary="Scenario validation failed",
                reason=msg,
                fix=f"Extend year_schedule to cover at least {min_years} years",
                invalid_fields=("year_schedule",),
            )
        else:
            logger.warning("%s (file: %s)", msg, file_path)

    return year_schedule


def _parse_policy(
    file_path: Path,
    policy_type: PolicyType | CustomPolicyType,
    raw: dict[str, Any],
) -> PolicyParameters:
    """Parse policy parameters based on policy type."""
    # Convert string year keys to int in rate_schedule.
    rate_schedule: dict[int, float] = {}
    if "rate_schedule" in raw:
        raw_rate_schedule = raw["rate_schedule"]
        if not isinstance(raw_rate_schedule, dict):
            raise ScenarioError(
                file_path=file_path,
                summary="Scenario validation failed",
                reason="policy.rate_schedule must be a mapping of year -> number",
                fix="Set rate_schedule as a YAML object with numeric values",
                invalid_fields=("policy.rate_schedule",),
            )
        try:
            for k, v in raw_rate_schedule.items():
                rate_schedule[int(k)] = float(v)
        except (TypeError, ValueError):
            raise ScenarioError(
                file_path=file_path,
                summary="Scenario validation failed",
                reason="policy.rate_schedule contains non-numeric year or value",
                fix="Use integer-like years and numeric rate values in rate_schedule",
                invalid_fields=("policy.rate_schedule",),
            ) from None

    # Parse common fields
    exemptions = tuple(raw.get("exemptions", []))
    thresholds = tuple(raw.get("thresholds", []))
    covered_categories = tuple(raw.get("covered_categories", []))

    # Build policy-specific parameters
    if policy_type == PolicyType.CARBON_TAX:
        # Parse redistribution fields for carbon tax
        redistribution_type = ""
        income_weights: dict[str, float] = {}
        if "redistribution" in raw:
            redist = raw["redistribution"]
            if not isinstance(redist, dict):
                raise ScenarioError(
                    file_path=file_path,
                    summary="Scenario validation failed",
                    reason="policy.redistribution must be a mapping",
                    fix="Set redistribution as a YAML object with type/income_weights",
                    invalid_fields=("policy.redistribution",),
                )
            if "type" in redist:
                redistribution_type = str(redist["type"])
            if "income_weights" in redist:
                raw_weights = redist["income_weights"]
                if not isinstance(raw_weights, dict):
                    raise ScenarioError(
                        file_path=file_path,
                        summary="Scenario validation failed",
                        reason="policy.redistribution.income_weights must be a mapping",
                        fix="Set income_weights as decile -> numeric weight pairs",
                        invalid_fields=("policy.redistribution.income_weights",),
                    )
                try:
                    for k, v in raw_weights.items():
                        income_weights[str(k)] = float(v)
                except (TypeError, ValueError):
                    raise ScenarioError(
                        file_path=file_path,
                        summary="Scenario validation failed",
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
            raw_income_caps = raw["income_caps"]
            if not isinstance(raw_income_caps, dict):
                raise ScenarioError(
                    file_path=file_path,
                    summary="Scenario validation failed",
                    reason="policy.income_caps must be a mapping of year -> number",
                    fix="Set income_caps as a YAML object with numeric values",
                    invalid_fields=("policy.income_caps",),
                )
            try:
                for k, v in raw_income_caps.items():
                    income_caps[int(k)] = float(v)
            except (TypeError, ValueError):
                raise ScenarioError(
                    file_path=file_path,
                    summary="Scenario validation failed",
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
        rebate_income_weights: dict[str, float] = {}
        if "income_weights" in raw:
            raw_weights = raw["income_weights"]
            if not isinstance(raw_weights, dict):
                raise ScenarioError(
                    file_path=file_path,
                    summary="Scenario validation failed",
                    reason="policy.income_weights must be a mapping",
                    fix="Set income_weights as decile -> numeric weight pairs",
                    invalid_fields=("policy.income_weights",),
                )
            try:
                for k, v in raw_weights.items():
                    rebate_income_weights[str(k)] = float(v)
            except (TypeError, ValueError):
                raise ScenarioError(
                    file_path=file_path,
                    summary="Scenario validation failed",
                    reason="policy.income_weights has non-numeric values",
                    fix="Use numeric values for all income_weights",
                    invalid_fields=("policy.income_weights",),
                ) from None
        # Check in redistribution sub-dict too
        if "redistribution" in raw:
            redist = raw["redistribution"]
            if not isinstance(redist, dict):
                raise ScenarioError(
                    file_path=file_path,
                    summary="Scenario validation failed",
                    reason="policy.redistribution must be a mapping",
                    fix="Set redistribution as a YAML object with type/income_weights",
                    invalid_fields=("policy.redistribution",),
                )
            if "type" in redist:
                rebate_type = str(redist["type"])
            if "income_weights" in redist:
                raw_weights = redist["income_weights"]
                if not isinstance(raw_weights, dict):
                    raise ScenarioError(
                        file_path=file_path,
                        summary="Scenario validation failed",
                        reason="policy.redistribution.income_weights must be a mapping",
                        fix="Set income_weights as decile -> numeric weight pairs",
                        invalid_fields=("policy.redistribution.income_weights",),
                    )
                try:
                    for k, v in raw_weights.items():
                        rebate_income_weights[str(k)] = float(v)
                except (TypeError, ValueError):
                    raise ScenarioError(
                        file_path=file_path,
                        summary="Scenario validation failed",
                        reason="policy.redistribution.income_weights has non-numeric values",
                        fix="Use numeric values for all redistribution income_weights",
                        invalid_fields=("policy.redistribution.income_weights",),
                    ) from None
        return RebateParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            rebate_type=rebate_type,
            income_weights=rebate_income_weights,
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
            raise ScenarioError(
                file_path=file_path,
                summary="Scenario validation failed",
                reason=(
                    "feebate numeric fields must be numbers: "
                    "pivot_point, fee_rate, rebate_rate"
                ),
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
        # Custom type — dispatch to generic custom parser
        if isinstance(policy_type, CustomPolicyType):
            return _parse_generic_custom_policy(
                file_path, policy_type, raw, rate_schedule, exemptions, thresholds, covered_categories,
            )
        # Generic parameters for truly unknown types
        return PolicyParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
        )


def _parse_generic_custom_policy(
    file_path: Path,
    policy_type: CustomPolicyType,
    raw: dict[str, Any],
    rate_schedule: dict[int, float],
    exemptions: tuple[dict[str, Any], ...],
    thresholds: tuple[dict[str, Any], ...],
    covered_categories: tuple[str, ...],
) -> PolicyParameters:
    """Parse a custom policy type using dataclass field introspection.

    Constructs the registered custom PolicyParameters subclass from the raw
    YAML dict. Handles rate_schedule string→int key conversion automatically
    since it is inherited from PolicyParameters.
    """
    import dataclasses

    from reformlab.templates.schema import _CUSTOM_PARAMETERS_TO_POLICY_TYPE

    # Find the registered class for this custom type
    target_class: type[PolicyParameters] | None = None
    for cls, pt in _CUSTOM_PARAMETERS_TO_POLICY_TYPE.items():
        if isinstance(pt, CustomPolicyType) and pt.value == policy_type.value:
            target_class = cls
            break

    if target_class is None:
        raise ScenarioError(
            file_path=file_path,
            summary="Scenario validation failed",
            reason=(
                f"Custom policy type '{policy_type.value}' is registered "
                f"but has no associated PolicyParameters class"
            ),
            fix=(
                f"Register a PolicyParameters subclass for '{policy_type.value}' "
                f"with register_custom_template()"
            ),
            invalid_fields=("policy_type",),
        )

    # Build constructor kwargs from already-parsed base fields
    kwargs: dict[str, Any] = {
        "rate_schedule": rate_schedule,
        "exemptions": exemptions,
        "thresholds": thresholds,
        "covered_categories": covered_categories,
    }

    # Base field names that are already handled
    base_field_names = {"rate_schedule", "exemptions", "thresholds", "covered_categories"}

    # Add custom fields from the raw dict
    for f in dataclasses.fields(target_class):
        if f.name in base_field_names:
            continue
        if f.name in raw:
            kwargs[f.name] = raw[f.name]

    try:
        return target_class(**kwargs)
    except (TypeError, ValueError) as exc:
        raise ScenarioError(
            file_path=file_path,
            summary="Scenario validation failed",
            reason=f"failed to construct {target_class.__name__}: {exc}",
            fix=f"Check that all fields for policy_type '{policy_type.value}' are valid",
            invalid_fields=("policy",),
        ) from None


def _scenario_to_dict(scenario: BaselineScenario | ReformScenario) -> dict[str, Any]:
    """Convert a scenario to a dictionary for YAML serialization."""
    data: dict[str, Any] = {}

    # Add schema reference
    if scenario.schema_ref:
        data["$schema"] = scenario.schema_ref
    else:
        data["$schema"] = "./schema/scenario-template.schema.json"

    data["version"] = scenario.version
    data["name"] = scenario.name
    if scenario.description:
        data["description"] = scenario.description
    assert scenario.policy_type is not None  # Always set after __post_init__
    data["policy_type"] = scenario.policy_type.value

    # Add baseline_ref for reforms
    if isinstance(scenario, ReformScenario):
        data["baseline_ref"] = scenario.baseline_ref
        if scenario.year_schedule:
            data["year_schedule"] = {
                "start_year": scenario.year_schedule.start_year,
                "end_year": scenario.year_schedule.end_year,
            }
    else:
        data["year_schedule"] = {
            "start_year": scenario.year_schedule.start_year,
            "end_year": scenario.year_schedule.end_year,
        }

    # Serialize policy
    data["policy"] = _policy_to_dict(scenario.policy)

    return data


def _policy_to_dict(params: PolicyParameters) -> dict[str, Any]:
    """Convert PolicyParameters to a dict, omitting empty values."""
    result: dict[str, Any] = {}

    if params.rate_schedule:
        result["rate_schedule"] = params.rate_schedule

    if params.exemptions:
        result["exemptions"] = list(params.exemptions)

    if params.thresholds:
        result["thresholds"] = list(params.thresholds)

    if params.covered_categories:
        result["covered_categories"] = list(params.covered_categories)

    # Handle subclass-specific fields
    if isinstance(params, CarbonTaxParameters):
        # Serialize redistribution as a sub-dict for consistency with YAML format
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
    elif type(params) is not PolicyParameters:
        # Custom PolicyParameters subclass — serialize extra fields via introspection
        import dataclasses as dc

        base_field_names = {"rate_schedule", "exemptions", "thresholds", "covered_categories"}
        for f in dc.fields(params):
            if f.name in base_field_names:
                continue
            value = getattr(params, f.name)
            if value != f.default:
                result[f.name] = value

    return result
