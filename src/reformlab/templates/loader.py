from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from reformlab.templates.exceptions import ScenarioError
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    ReformScenario,
    SubsidyParameters,
    YearSchedule,
)

logger = logging.getLogger(__name__)

# Schema version supported by this loader
SCHEMA_VERSION = "1.0"
_SCHEMA_MAJOR_VERSION = 1

_REQUIRED_FIELDS = frozenset({"name", "policy_type", "version"})
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

    policy_type = PolicyType(data["policy_type"])
    name = str(data["name"])
    version = str(data["version"])
    description = str(data.get("description", ""))
    schema_ref = str(data.get("$schema", ""))
    baseline_ref = data.get("baseline_ref")

    # Parse year_schedule if present
    year_schedule = None
    if "year_schedule" in data:
        year_schedule = _parse_year_schedule(file_path, data["year_schedule"], strict)

    # Parse parameters
    raw_params = data.get("parameters", {})
    parameters = _parse_parameters(file_path, policy_type, raw_params)

    if baseline_ref:
        # Reform scenario
        return ReformScenario(
            name=name,
            policy_type=policy_type,
            baseline_ref=str(baseline_ref),
            parameters=parameters,
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
            parameters=parameters,
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


def _validate_policy_type(file_path: Path, data: dict[str, Any]) -> None:
    """Validate policy_type is one of the supported values."""
    policy_type = data.get("policy_type")
    if policy_type not in _VALID_POLICY_TYPES:
        valid_types = ", ".join(sorted(_VALID_POLICY_TYPES))
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


def _parse_parameters(
    file_path: Path,
    policy_type: PolicyType,
    raw: dict[str, Any],
) -> PolicyParameters:
    """Parse policy parameters based on policy type."""
    # Convert string year keys to int in rate_schedule
    rate_schedule: dict[int, float] = {}
    if "rate_schedule" in raw:
        for k, v in raw["rate_schedule"].items():
            rate_schedule[int(k)] = float(v)

    # Parse common fields
    exemptions = tuple(raw.get("exemptions", []))
    thresholds = tuple(raw.get("thresholds", []))
    covered_categories = tuple(raw.get("covered_categories", []))

    # Build policy-specific parameters
    if policy_type == PolicyType.CARBON_TAX:
        return CarbonTaxParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
        )
    elif policy_type == PolicyType.SUBSIDY:
        eligible_categories = tuple(raw.get("eligible_categories", []))
        income_caps: dict[int, float] = {}
        if "income_caps" in raw:
            for k, v in raw["income_caps"].items():
                income_caps[int(k)] = float(v)
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
        income_weights: dict[str, float] = {}
        if "income_weights" in raw:
            for k, v in raw["income_weights"].items():
                income_weights[str(k)] = float(v)
        # Check in redistribution sub-dict too
        if "redistribution" in raw:
            redist = raw["redistribution"]
            if "type" in redist:
                rebate_type = str(redist["type"])
            if "income_weights" in redist:
                for k, v in redist["income_weights"].items():
                    income_weights[str(k)] = float(v)
        return RebateParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            rebate_type=rebate_type,
            income_weights=income_weights,
        )
    elif policy_type == PolicyType.FEEBATE:
        pivot_point = float(raw.get("pivot_point", 0.0))
        fee_rate = float(raw.get("fee_rate", 0.0))
        rebate_rate = float(raw.get("rebate_rate", 0.0))
        return FeebateParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            pivot_point=pivot_point,
            fee_rate=fee_rate,
            rebate_rate=rebate_rate,
        )
    else:
        # Generic parameters for unknown types
        return PolicyParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
        )


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

    # Serialize parameters
    data["parameters"] = _parameters_to_dict(scenario.parameters)

    return data


def _parameters_to_dict(params: PolicyParameters) -> dict[str, Any]:
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
    if isinstance(params, SubsidyParameters):
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
        if params.pivot_point:
            result["pivot_point"] = params.pivot_point
        if params.fee_rate:
            result["fee_rate"] = params.fee_rate
        if params.rebate_rate:
            result["rebate_rate"] = params.rebate_rate

    return result
