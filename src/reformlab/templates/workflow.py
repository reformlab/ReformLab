# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Workflow configuration schema and loader for ReformLab.

This module provides:
- Schema dataclasses for defining workflow configurations
- YAML/JSON loader and serializer for workflow files
- JSON Schema validation with field-path error reporting
- Execution handoff API for delegating to runtime backends
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

try:
    from jsonschema import Draft202012Validator

    _HAS_JSONSCHEMA = True
except ImportError:
    _HAS_JSONSCHEMA = False
    Draft202012Validator = None

logger = logging.getLogger(__name__)

# Cached compiled JSON Schema validator
_WORKFLOW_SCHEMA_VALIDATOR: Draft202012Validator | None = None

# Schema version supported by this loader
WORKFLOW_SCHEMA_VERSION = "1.0"
_WORKFLOW_SCHEMA_MAJOR_VERSION = 1


class WorkflowError(Exception):
    """Structured workflow error with actionable messages.

    Provides:
    - file_path: The file that caused the error
    - summary: Brief description of what failed
    - reason: Technical explanation of why it failed
    - fix: Actionable guidance on how to resolve the issue
    - invalid_fields: Tuple of field names that are invalid/missing
    - line_number: Line number in source file (where available)
    """

    def __init__(
        self,
        *,
        file_path: Path | None = None,
        summary: str,
        reason: str,
        fix: str,
        invalid_fields: tuple[str, ...] = (),
        line_number: int | None = None,
    ) -> None:
        self.file_path = file_path
        self.summary = summary
        self.reason = reason
        self.fix = fix
        self.invalid_fields = invalid_fields
        self.line_number = line_number

        message = f"{summary} - {reason} - {fix}"
        if file_path:
            message += f" (file: {file_path})"
        if line_number is not None:
            message += f" (line: {line_number})"

        super().__init__(message)


class OutputType(Enum):
    """Supported output types for workflow results."""

    DISTRIBUTIONAL_INDICATORS = "distributional_indicators"
    COMPARISON_TABLE = "comparison_table"
    PANEL_EXPORT = "panel_export"
    SUMMARY_REPORT = "summary_report"


class OutputFormat(Enum):
    """Supported output formats for workflow exports."""

    CSV = "csv"
    PARQUET = "parquet"
    JSON = "json"
    YAML = "yaml"


@dataclass(frozen=True)
class DataSourceConfig:
    """Configuration for data sources in a workflow.

    Attributes:
        population: Registry reference or path to population data.
        emission_factors: Registry reference or path to emission factors.
    """

    population: str = ""
    emission_factors: str = "default"


@dataclass(frozen=True)
class ScenarioRef:
    """Reference to a scenario in a workflow.

    Attributes:
        role: Role of the scenario (e.g., "baseline", "reform").
        reference: Registry reference to the scenario (name or name@version).
    """

    role: str
    reference: str


@dataclass(frozen=True)
class OutputConfig:
    """Configuration for a workflow output.

    Attributes:
        type: Output type (distributional_indicators, comparison_table, etc.).
        by: Grouping dimensions for the output.
        format: Output format (csv, parquet, json, yaml).
        path: Output file path.
    """

    type: str
    by: tuple[str, ...] = ()
    format: str = ""
    path: str = ""


@dataclass(frozen=True)
class RunConfig:
    """Orchestrator run configuration.

    Attributes:
        projection_years: Number of years to project.
        start_year: Starting year for the projection.
        output_format: Default output format for results.
    """

    projection_years: int = 10
    start_year: int = 2025
    output_format: str = "csv"


@dataclass(frozen=True)
class WorkflowConfig:
    """Complete workflow configuration.

    Immutable dataclass representing a validated workflow configuration
    that can be handed off to a runtime backend for execution.

    Attributes:
        name: Workflow identifier.
        version: Schema version for migration compatibility.
        description: Human-readable description.
        data_sources: Data source references.
        scenarios: List of scenario references.
        run_config: Orchestrator settings.
        outputs: Requested output configurations.
        schema_ref: JSON Schema reference for IDE validation.
        format: Source format (yaml/json) for deterministic serialization.
    """

    name: str
    version: str
    data_sources: DataSourceConfig
    scenarios: tuple[ScenarioRef, ...]
    run_config: RunConfig
    outputs: tuple[OutputConfig, ...] = ()
    description: str = ""
    schema_ref: str = ""
    format: str = "yaml"


# Required fields for workflow validation
_REQUIRED_FIELDS = frozenset({"name", "version", "scenarios"})
_REQUIRED_FIELD_TYPES = {
    "name": "string",
    "version": "string",
    "scenarios": "array",
}
_VALID_OUTPUT_TYPES = frozenset(output_type.value for output_type in OutputType)
_VALID_OUTPUT_FORMATS = frozenset(output_format.value for output_format in OutputFormat)
_WORKFLOW_SCHEMA_DIR = Path(__file__).parent / "schema"


def get_workflow_schema_path() -> Path:
    """Return the path to the workflow JSON Schema file."""
    return _WORKFLOW_SCHEMA_DIR / "workflow.schema.json"


def _get_workflow_schema_validator() -> Draft202012Validator | None:
    """Get or create the cached JSON Schema validator."""
    global _WORKFLOW_SCHEMA_VALIDATOR

    if not _HAS_JSONSCHEMA:
        return None

    if _WORKFLOW_SCHEMA_VALIDATOR is not None:
        return _WORKFLOW_SCHEMA_VALIDATOR

    schema_path = get_workflow_schema_path()
    if not schema_path.exists():
        logger.warning("Workflow JSON Schema not found at %s", schema_path)
        return None

    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    _WORKFLOW_SCHEMA_VALIDATOR = Draft202012Validator(schema)
    return _WORKFLOW_SCHEMA_VALIDATOR


def _json_path_to_field_path(path: list[str | int]) -> str:
    """Convert JSON Schema path to field path string."""
    parts = []
    for segment in path:
        if isinstance(segment, int):
            parts.append(f"[{segment}]")
        else:
            if parts:
                parts.append(f".{segment}")
            else:
                parts.append(segment)
    return "".join(parts)


def _json_pointer_escape(segment: str) -> str:
    """Escape a JSON pointer segment."""
    return segment.replace("~", "~0").replace("/", "~1")


def _json_path_to_pointer(path: list[str | int]) -> str:
    """Convert JSON Schema path to JSON pointer."""
    if not path:
        return "/"

    pointer_parts: list[str] = []
    for segment in path:
        pointer_parts.append(_json_pointer_escape(str(segment)))
    return "/" + "/".join(pointer_parts)


def _extract_missing_property(message: str) -> str | None:
    """Extract missing property name from jsonschema required-field messages."""
    # Typical format: "'version' is a required property"
    parts = message.split("'")
    if len(parts) >= 3 and "required property" in message:
        return parts[1]
    return None


def _expected_type_for_field(field_path: str) -> str:
    """Return expected type hints for known required top-level fields."""
    root_field = field_path.split(".", 1)[0].split("[", 1)[0]
    return _REQUIRED_FIELD_TYPES.get(root_field, "schema-defined")


def validate_workflow_with_schema(
    data: dict[str, Any],
    *,
    file_path: Path | None = None,
) -> list[WorkflowError]:
    """Validate a workflow configuration against JSON Schema.

    Args:
        data: Workflow configuration dictionary.
        file_path: Optional file path for error messages.

    Returns:
        List of WorkflowError objects for each validation failure.
        Empty list if validation passes or jsonschema is not installed.
    """
    validator = _get_workflow_schema_validator()
    if validator is None:
        # Fall back to dataclass validation only
        return []

    errors: list[WorkflowError] = []
    sorted_errors = sorted(
        validator.iter_errors(data),
        key=lambda err: (
            _json_path_to_field_path(list(err.absolute_path)),
            err.message,
        ),
    )

    for error in sorted_errors:
        # Build field path from JSON Schema path
        path_segments = list(error.absolute_path)
        field_path = _json_path_to_field_path(path_segments)
        pointer = _json_path_to_pointer(path_segments)
        if not field_path:
            field_path = "(root)"

        reason = error.message

        # Generate actionable fix message
        if error.validator == "required":
            missing_property = _extract_missing_property(error.message)
            if missing_property is not None:
                if field_path == "(root)":
                    field_path = missing_property
                else:
                    field_path = f"{field_path}.{missing_property}"

                if pointer == "/":
                    pointer = f"/{_json_pointer_escape(missing_property)}"
                else:
                    pointer = f"{pointer}/{_json_pointer_escape(missing_property)}"

                expected_type = _expected_type_for_field(field_path)
                fix = (
                    f"Add required field '{field_path}' with expected type "
                    f"'{expected_type}'"
                )
            else:
                fix = "Add the missing required field(s)"
        elif error.validator == "type":
            expected = error.validator_value
            actual = type(error.instance).__name__
            fix = f"Use type '{expected}' instead of '{actual}'"
        elif error.validator == "enum":
            allowed = ", ".join(str(v) for v in error.validator_value)
            fix = f"Use one of the allowed values: {allowed}"
        elif error.validator == "pattern":
            fix = f"Value must match pattern: {error.validator_value}"
        elif error.validator == "minItems":
            fix = f"Add at least {error.validator_value} item(s)"
        elif error.validator == "minLength":
            fix = f"Value must be at least {error.validator_value} character(s)"
        else:
            fix = "Check the JSON Schema for valid values"

        if pointer != "/":
            reason = f"{reason} (json-pointer: {pointer})"

        errors.append(
            WorkflowError(
                file_path=file_path,
                summary="Workflow schema validation failed",
                reason=reason,
                fix=fix,
                invalid_fields=(field_path,),
            )
        )

    return errors


def validate_workflow_schema_version(
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
        WorkflowError: If version is incompatible (major version mismatch).
    """
    try:
        parts = version.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        logger.warning("Invalid workflow schema version format: %s", version)
        return

    if major != _WORKFLOW_SCHEMA_MAJOR_VERSION:
        msg = (
            f"Workflow schema version {version} is not compatible "
            f"with loader version {WORKFLOW_SCHEMA_VERSION}"
        )
        if strict:
            raise WorkflowError(
                file_path=file_path,
                summary="Workflow schema version mismatch",
                reason=msg,
                fix=f"Update workflow to version {WORKFLOW_SCHEMA_VERSION} or migrate",
                invalid_fields=("version",),
            )
        else:
            logger.warning("%s", msg)
    elif minor > int(WORKFLOW_SCHEMA_VERSION.split(".")[1]):
        logger.warning(
            "Workflow schema version %s is newer than loader version %s",
            version,
            WORKFLOW_SCHEMA_VERSION,
        )


def _validate_required_fields(
    file_path: Path | None,
    data: dict[str, Any],
) -> None:
    """Check for required top-level fields."""
    missing = _REQUIRED_FIELDS - set(data.keys())
    if missing:
        names_with_types = ", ".join(
            f"{field} ({_REQUIRED_FIELD_TYPES[field]})" for field in sorted(missing)
        )
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason=f"missing required fields: {names_with_types}",
            fix=f"Add the following fields with expected types: {names_with_types}",
            invalid_fields=tuple(sorted(missing)),
        )


def _parse_data_sources(
    file_path: Path | None,
    raw: Any,
) -> DataSourceConfig:
    """Parse data_sources from raw data."""
    if raw is None:
        return DataSourceConfig()

    if not isinstance(raw, dict):
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason="data_sources must be a mapping (dict)",
            fix="Define data_sources as a YAML object with population/emission_factors",
            invalid_fields=("data_sources",),
        )

    return DataSourceConfig(
        population=str(raw.get("population", "")),
        emission_factors=str(raw.get("emission_factors", "default")),
    )


def _parse_scenarios(
    file_path: Path | None,
    raw: Any,
) -> tuple[ScenarioRef, ...]:
    """Parse scenarios from raw data."""
    if raw is None:
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason="missing required field: scenarios",
            fix="Add a 'scenarios' list with at least one scenario reference",
            invalid_fields=("scenarios",),
        )

    if not isinstance(raw, list):
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason="scenarios must be a list",
            fix="Define scenarios as a YAML list of scenario references",
            invalid_fields=("scenarios",),
        )

    if not raw:
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason="scenarios list cannot be empty",
            fix="Add at least one scenario reference to the scenarios list",
            invalid_fields=("scenarios",),
        )

    scenarios: list[ScenarioRef] = []
    for i, item in enumerate(raw):
        if isinstance(item, dict):
            if not item:
                raise WorkflowError(
                    file_path=file_path,
                    summary="Workflow validation failed",
                    reason=f"scenarios[{i}] mapping cannot be empty",
                    fix=f"Set scenarios[{i}] to a single role: reference mapping",
                    invalid_fields=(f"scenarios[{i}]",),
                )
            if len(item) != 1:
                raise WorkflowError(
                    file_path=file_path,
                    summary="Workflow validation failed",
                    reason=f"scenarios[{i}] must have exactly one role mapping",
                    fix=f"Use a single key in scenarios[{i}], e.g. {{baseline: '...'}}",
                    invalid_fields=(f"scenarios[{i}]",),
                )
            # Dict format: {baseline: "name"} or {reform: "name"}
            for role, reference in item.items():
                if not isinstance(reference, str) or not reference.strip():
                    raise WorkflowError(
                        file_path=file_path,
                        summary="Workflow validation failed",
                        reason=f"scenarios[{i}].{role} must be a non-empty string reference",
                        fix=f"Use a string reference for scenarios[{i}].{role}",
                        invalid_fields=(f"scenarios[{i}].{role}",),
                    )
                scenarios.append(ScenarioRef(role=str(role), reference=str(reference)))
        elif isinstance(item, str):
            if not item.strip():
                raise WorkflowError(
                    file_path=file_path,
                    summary="Workflow validation failed",
                    reason=f"scenarios[{i}] must be a non-empty string reference",
                    fix=f"Set scenarios[{i}] to a valid scenario reference",
                    invalid_fields=(f"scenarios[{i}]",),
                )
            # String format: plain scenario reference
            scenarios.append(ScenarioRef(role="scenario", reference=item))
        else:
            raise WorkflowError(
                file_path=file_path,
                summary="Workflow validation failed",
                reason=f"scenarios[{i}] must be a string or mapping",
                fix=f"Use a string or role:reference mapping for scenarios[{i}]",
                invalid_fields=(f"scenarios[{i}]",),
            )

    return tuple(scenarios)


def _parse_run_config(
    file_path: Path | None,
    raw: Any,
) -> RunConfig:
    """Parse run_config from raw data."""
    if raw is None:
        return RunConfig()

    if not isinstance(raw, dict):
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason="run_config must be a mapping (dict)",
            fix="Define run_config as a YAML object with projection_years, start_year",
            invalid_fields=("run_config",),
        )

    try:
        projection_years = int(raw.get("projection_years", 10))
        start_year = int(raw.get("start_year", 2025))
    except (TypeError, ValueError):
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason="run_config projection_years and start_year must be integers",
            fix="Use integer values for projection_years and start_year",
            invalid_fields=("run_config",),
        ) from None

    if projection_years < 1 or projection_years > 100:
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason="run_config.projection_years must be between 1 and 100",
            fix="Set run_config.projection_years to an integer in [1, 100]",
            invalid_fields=("run_config.projection_years",),
        )

    if start_year < 1900 or start_year > 2200:
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason="run_config.start_year must be between 1900 and 2200",
            fix="Set run_config.start_year to an integer in [1900, 2200]",
            invalid_fields=("run_config.start_year",),
        )

    output_format = str(raw.get("output_format", "csv"))
    if output_format and output_format not in _VALID_OUTPUT_FORMATS:
        allowed = ", ".join(sorted(_VALID_OUTPUT_FORMATS))
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason=f"run_config.output_format must be one of: {allowed}",
            fix=f"Set run_config.output_format to one of: {allowed}",
            invalid_fields=("run_config.output_format",),
        )

    return RunConfig(
        projection_years=projection_years,
        start_year=start_year,
        output_format=output_format,
    )


def _parse_outputs(
    file_path: Path | None,
    raw: Any,
) -> tuple[OutputConfig, ...]:
    """Parse outputs from raw data."""
    if raw is None:
        return ()

    if not isinstance(raw, list):
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason="outputs must be a list",
            fix="Define outputs as a YAML list of output configurations",
            invalid_fields=("outputs",),
        )

    outputs: list[OutputConfig] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise WorkflowError(
                file_path=file_path,
                summary="Workflow validation failed",
                reason=f"outputs[{i}] must be a mapping (dict)",
                fix=f"Define outputs[{i}] as a YAML object with type, format, etc.",
                invalid_fields=(f"outputs[{i}]",),
            )

        output_type = item.get("type")
        if not output_type:
            raise WorkflowError(
                file_path=file_path,
                summary="Workflow validation failed",
                reason=f"outputs[{i}] missing required field: type",
                fix=f"Add a 'type' field to outputs[{i}]",
                invalid_fields=(f"outputs[{i}].type",),
            )

        output_type_value = str(output_type)
        if output_type_value not in _VALID_OUTPUT_TYPES:
            allowed = ", ".join(sorted(_VALID_OUTPUT_TYPES))
            raise WorkflowError(
                file_path=file_path,
                summary="Workflow validation failed",
                reason=f"outputs[{i}].type must be one of: {allowed}",
                fix=f"Set outputs[{i}].type to one of: {allowed}",
                invalid_fields=(f"outputs[{i}].type",),
            )

        by_raw = item.get("by", [])
        if isinstance(by_raw, list):
            by = tuple(str(b) for b in by_raw)
        elif isinstance(by_raw, str):
            by = (by_raw,)
        elif by_raw in ("", None):
            by = ()
        else:
            raise WorkflowError(
                file_path=file_path,
                summary="Workflow validation failed",
                reason=f"outputs[{i}].by must be a string or list of strings",
                fix=f"Set outputs[{i}].by to a string or list of strings",
                invalid_fields=(f"outputs[{i}].by",),
            )

        output_format = str(item.get("format", ""))
        if output_format and output_format not in _VALID_OUTPUT_FORMATS:
            allowed = ", ".join(sorted(_VALID_OUTPUT_FORMATS))
            raise WorkflowError(
                file_path=file_path,
                summary="Workflow validation failed",
                reason=f"outputs[{i}].format must be one of: {allowed}",
                fix=f"Set outputs[{i}].format to one of: {allowed}",
                invalid_fields=(f"outputs[{i}].format",),
            )

        outputs.append(
            OutputConfig(
                type=output_type_value,
                by=by,
                format=output_format,
                path=str(item.get("path", "")),
            )
        )

    return tuple(outputs)


def validate_workflow_config(
    data: dict[str, Any],
    *,
    file_path: Path | None = None,
    strict: bool = False,
    use_json_schema: bool = True,
) -> WorkflowConfig:
    """Validate a workflow configuration dictionary.

    Args:
        data: Workflow configuration dictionary.
        file_path: Optional file path for error messages.
        strict: If True, raise on minor version mismatches.
        use_json_schema: If True, also validate against JSON Schema.

    Returns:
        Validated WorkflowConfig dataclass.

    Raises:
        WorkflowError: If validation fails.
    """
    if not isinstance(data, dict):
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow validation failed",
            reason="workflow file must contain a YAML/JSON mapping (dict)",
            fix="Ensure the file has top-level keys: name, version, scenarios",
        )

    _validate_required_fields(file_path, data)

    # Run JSON Schema validation first if available
    if use_json_schema:
        schema_errors = validate_workflow_with_schema(data, file_path=file_path)
        if schema_errors:
            # Raise the first error (most significant)
            raise schema_errors[0]

    # Validate and extract fields
    name = str(data["name"])
    version = str(data["version"])
    validate_workflow_schema_version(version, strict=strict, file_path=file_path)
    description = str(data.get("description", ""))
    schema_ref = str(data.get("$schema", ""))

    # Parse nested structures
    data_sources = _parse_data_sources(file_path, data.get("data_sources"))
    scenarios = _parse_scenarios(file_path, data.get("scenarios"))
    run_config = _parse_run_config(file_path, data.get("run_config"))
    outputs = _parse_outputs(file_path, data.get("outputs"))

    return WorkflowConfig(
        name=name,
        version=version,
        description=description,
        data_sources=data_sources,
        scenarios=scenarios,
        run_config=run_config,
        outputs=outputs,
        schema_ref=schema_ref,
    )


def _detect_format(path: Path) -> str:
    """Detect file format from extension."""
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        return "yaml"
    elif suffix == ".json":
        return "json"
    else:
        raise WorkflowError(
            file_path=path,
            summary="Workflow load failed",
            reason=f"unsupported file extension: {suffix}",
            fix="Use .yaml, .yml, or .json extension for workflow files",
        )


def load_workflow_config(
    path: str | Path,
    *,
    strict: bool = False,
) -> WorkflowConfig:
    """Load a workflow configuration from YAML or JSON file.

    Args:
        path: Path to the workflow configuration file.
        strict: If True, raise on minor schema version mismatches.

    Returns:
        Validated WorkflowConfig dataclass.

    Raises:
        WorkflowError: If the file is invalid, missing required fields,
            or has validation errors.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow load failed",
            reason="workflow file was not found",
            fix="Provide an existing .yaml, .yml, or .json workflow configuration file",
        )

    file_format = _detect_format(file_path)

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        if file_format == "yaml":
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)

    except yaml.YAMLError as exc:
        # Extract line number from YAML error if available
        line_number = None
        if hasattr(exc, "problem_mark") and exc.problem_mark is not None:
            line_number = exc.problem_mark.line + 1

        raise WorkflowError(
            file_path=file_path,
            summary="Workflow load failed",
            reason=f"invalid YAML syntax: {exc}",
            fix="Fix the YAML syntax errors in the workflow file",
            line_number=line_number,
        ) from None

    except json.JSONDecodeError as exc:
        raise WorkflowError(
            file_path=file_path,
            summary="Workflow load failed",
            reason=f"invalid JSON syntax: {exc.msg}",
            fix="Fix the JSON syntax errors in the workflow file",
            line_number=exc.lineno,
        ) from None

    config = validate_workflow_config(data, file_path=file_path, strict=strict)

    # Return with format metadata
    return WorkflowConfig(
        name=config.name,
        version=config.version,
        description=config.description,
        data_sources=config.data_sources,
        scenarios=config.scenarios,
        run_config=config.run_config,
        outputs=config.outputs,
        schema_ref=config.schema_ref,
        format=file_format,
    )


def _workflow_to_dict(config: WorkflowConfig) -> dict[str, Any]:
    """Convert a WorkflowConfig to a dictionary for serialization."""
    data: dict[str, Any] = {}

    # Add schema reference
    if config.schema_ref:
        data["$schema"] = config.schema_ref
    else:
        data["$schema"] = "./schema/workflow.schema.json"

    data["version"] = config.version
    data["name"] = config.name
    if config.description:
        data["description"] = config.description

    # Data sources
    has_population = config.data_sources.population
    has_custom_emission = config.data_sources.emission_factors != "default"
    if has_population or has_custom_emission:
        data["data_sources"] = {}
        if has_population:
            data["data_sources"]["population"] = config.data_sources.population
        if config.data_sources.emission_factors:
            emission_factors = config.data_sources.emission_factors
            data["data_sources"]["emission_factors"] = emission_factors

    # Scenarios
    scenarios_list: list[dict[str, str] | str] = []
    for scenario in config.scenarios:
        if scenario.role == "scenario":
            scenarios_list.append(scenario.reference)
        else:
            scenarios_list.append({scenario.role: scenario.reference})
    data["scenarios"] = scenarios_list

    # Run config
    data["run_config"] = {
        "projection_years": config.run_config.projection_years,
        "start_year": config.run_config.start_year,
    }
    if config.run_config.output_format:
        data["run_config"]["output_format"] = config.run_config.output_format

    # Outputs
    if config.outputs:
        outputs_list: list[dict[str, Any]] = []
        for output in config.outputs:
            output_dict: dict[str, Any] = {"type": output.type}
            if output.by:
                output_dict["by"] = list(output.by)
            if output.format:
                output_dict["format"] = output.format
            if output.path:
                output_dict["path"] = output.path
            outputs_list.append(output_dict)
        data["outputs"] = outputs_list

    return data


def dump_workflow_config(
    config: WorkflowConfig,
    path: str | Path,
    *,
    format: str | None = None,
) -> None:
    """Serialize a workflow configuration to a YAML or JSON file.

    Args:
        config: The workflow configuration to serialize.
        path: Output file path.
        format: Output format ("yaml" or "json"). If None, infers from path extension.
    """
    file_path = Path(path)
    data = _workflow_to_dict(config)

    if format is None:
        format = _detect_format(file_path)
    else:
        normalized_format = format.lower()
        if normalized_format == "yml":
            normalized_format = "yaml"
        if normalized_format not in {"yaml", "json"}:
            raise WorkflowError(
                file_path=file_path,
                summary="Workflow dump failed",
                reason=f"unsupported format override: {format}",
                fix="Use format='yaml' or format='json'",
            )
        format = normalized_format

    with open(file_path, "w", encoding="utf-8") as f:
        if format == "yaml":
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        else:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")


def workflow_to_yaml(config: WorkflowConfig) -> str:
    """Convert a workflow configuration to a YAML string.

    Args:
        config: The workflow configuration.

    Returns:
        YAML-formatted string.
    """
    data = _workflow_to_dict(config)
    result: str = yaml.safe_dump(data, default_flow_style=False, sort_keys=False)
    return result


def workflow_to_json(config: WorkflowConfig) -> str:
    """Convert a workflow configuration to a JSON string.

    Args:
        config: The workflow configuration.

    Returns:
        JSON-formatted string.
    """
    data = _workflow_to_dict(config)
    return json.dumps(data, indent=2, sort_keys=True)


@dataclass
class WorkflowResult:
    """Result of a workflow execution.

    Attributes:
        success: Whether the workflow completed successfully.
        outputs: Dictionary of output paths/data by output type.
        errors: List of error messages if execution failed.
        metadata: Additional metadata about the execution.
    """

    success: bool
    outputs: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def prepare_workflow_request(
    config: WorkflowConfig,
) -> dict[str, Any]:
    """Normalize a workflow config into a runtime request payload.

    This prepares the workflow configuration for handoff to an execution
    backend by converting the dataclass into a standardized request format.

    Args:
        config: The workflow configuration.

    Returns:
        Dictionary suitable for passing to a runtime backend.
    """
    return {
        "name": config.name,
        "version": config.version,
        "data_sources": {
            "population": config.data_sources.population,
            "emission_factors": config.data_sources.emission_factors,
        },
        "scenarios": [
            {"role": s.role, "reference": s.reference} for s in config.scenarios
        ],
        "run_config": {
            "projection_years": config.run_config.projection_years,
            "start_year": config.run_config.start_year,
            "output_format": config.run_config.output_format,
        },
        "outputs": [
            {
                "type": o.type,
                "by": list(o.by),
                "format": o.format,
                "path": o.path,
            }
            for o in config.outputs
        ],
    }


def run_workflow(
    config: WorkflowConfig,
    *,
    runner: Any | None = None,
) -> WorkflowResult:
    """Execute a workflow configuration.

    Delegates to an injected runner or existing runtime API entrypoint.
    If no runtime backend is available, raises a WorkflowError with
    actionable guidance.

    Args:
        config: The workflow configuration to execute.
        runner: Optional runtime backend. If provided, must have a
            `run(request: dict) -> WorkflowResult` method.

    Returns:
        WorkflowResult with execution outcomes.

    Raises:
        WorkflowError: If runtime backend is unavailable or execution fails.
    """
    # Prepare the request payload
    request = prepare_workflow_request(config)

    # Validate scenario references exist (if registry is available)
    # This is a lightweight check before handoff
    _validate_scenario_references(config)

    # If a runner is provided, delegate to it
    if runner is not None:
        run_method = getattr(runner, "run", None)
        if not callable(run_method):
            raise WorkflowError(
                summary="Invalid workflow runner",
                reason="runner must have a callable 'run(request)' method",
                fix="Provide a runner with run(request: dict) -> WorkflowResult",
            )

        try:
            result = run_method(request)
        except Exception as exc:
            raise WorkflowError(
                summary="Workflow execution failed",
                reason=f"runner raised {type(exc).__name__}: {exc}",
                fix="Fix the runner implementation or pass a different runner",
            ) from exc

        if isinstance(result, WorkflowResult):
            return result
        # If runner returns a dict, wrap it
        if isinstance(result, dict):
            return WorkflowResult(
                success=result.get("success", True),
                outputs=result.get("outputs", {}),
                errors=result.get("errors", []),
                metadata=result.get("metadata", {}),
            )
        raise WorkflowError(
            summary="Invalid workflow runner response",
            reason=(
                "runner.run(request) must return WorkflowResult or dict, "
                f"got {type(result).__name__}"
            ),
            fix=(
                "Update runner.run(request) to return WorkflowResult or a "
                "dict with keys: success, outputs, errors, metadata"
            ),
        )

    # No runtime backend available
    raise WorkflowError(
        summary="Workflow runtime unavailable",
        reason="no runtime backend is configured for workflow execution",
        fix=(
            "Provide a runner parameter or install an orchestrator backend. "
            "Workflow execution will be available when EPIC-3 is implemented."
        ),
    )


def _validate_scenario_references(config: WorkflowConfig) -> None:
    """Validate that scenario references can be resolved.

    This is a lightweight check that validates the reference format
    without loading the full scenario data. Registry lookups are
    deferred to runtime execution.
    """
    if config.data_sources.population and not config.data_sources.population.strip():
        raise WorkflowError(
            summary="Workflow validation failed",
            reason="data_sources.population must not be blank",
            fix="Set data_sources.population to a non-empty reference when provided",
            invalid_fields=("data_sources.population",),
        )
    if not config.data_sources.emission_factors.strip():
        raise WorkflowError(
            summary="Workflow validation failed",
            reason="data_sources.emission_factors must not be blank",
            fix="Set data_sources.emission_factors to a non-empty reference",
            invalid_fields=("data_sources.emission_factors",),
        )

    for i, scenario_ref in enumerate(config.scenarios):
        if not scenario_ref.reference.strip():
            raise WorkflowError(
                summary="Workflow validation failed",
                reason=f"scenarios[{i}] has empty reference",
                fix=f"Provide a valid scenario reference for scenarios[{i}]",
                invalid_fields=(f"scenarios[{i}].reference",),
            )
        # Basic format validation: reference should be non-empty
        # Full registry validation is deferred to runtime
