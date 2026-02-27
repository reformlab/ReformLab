"""Tests for workflow configuration schema and loader."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from reformlab.templates.workflow import (
    DataSourceConfig,
    OutputConfig,
    RunConfig,
    ScenarioRef,
    WorkflowConfig,
    WorkflowError,
    WorkflowResult,
    WORKFLOW_SCHEMA_VERSION,
    dump_workflow_config,
    get_workflow_schema_path,
    load_workflow_config,
    prepare_workflow_request,
    run_workflow,
    validate_workflow_config,
    validate_workflow_with_schema,
    workflow_to_json,
    workflow_to_yaml,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def valid_workflow_dict() -> dict:
    """Return a valid workflow configuration dictionary."""
    return {
        "$schema": "./schema/workflow.schema.json",
        "version": "1.0",
        "name": "test_workflow",
        "description": "Test workflow description",
        "data_sources": {
            "population": "synthetic_french_2024",
            "emission_factors": "default",
        },
        "scenarios": [
            {"baseline": "carbon_tax_flat_44"},
            {"reform": "carbon_tax_progressive"},
        ],
        "run_config": {
            "projection_years": 10,
            "start_year": 2025,
            "output_format": "csv",
        },
        "outputs": [
            {
                "type": "distributional_indicators",
                "by": ["income_decile"],
            },
            {
                "type": "comparison_table",
                "format": "csv",
                "path": "outputs/comparison.csv",
            },
        ],
    }


@pytest.fixture
def minimal_workflow_dict() -> dict:
    """Return a minimal valid workflow configuration."""
    return {
        "version": "1.0",
        "name": "minimal_workflow",
        "scenarios": ["scenario_a"],
    }


@pytest.fixture
def valid_workflow_config() -> WorkflowConfig:
    """Return a valid WorkflowConfig instance."""
    return WorkflowConfig(
        name="test_workflow",
        version="1.0",
        description="Test workflow",
        data_sources=DataSourceConfig(
            population="synthetic_french_2024",
            emission_factors="default",
        ),
        scenarios=(
            ScenarioRef(role="baseline", reference="carbon_tax_flat_44"),
            ScenarioRef(role="reform", reference="carbon_tax_progressive"),
        ),
        run_config=RunConfig(
            projection_years=10,
            start_year=2025,
            output_format="csv",
        ),
        outputs=(
            OutputConfig(
                type="distributional_indicators",
                by=("income_decile",),
            ),
        ),
        schema_ref="./schema/workflow.schema.json",
        format="yaml",
    )


# ============================================================================
# Test: Schema version validation
# ============================================================================


def test_schema_version_constant():
    """WORKFLOW_SCHEMA_VERSION is defined and follows semver."""
    assert WORKFLOW_SCHEMA_VERSION == "1.0"
    parts = WORKFLOW_SCHEMA_VERSION.split(".")
    assert len(parts) == 2
    assert all(p.isdigit() for p in parts)


def test_schema_path_exists():
    """JSON Schema file exists at expected path."""
    schema_path = get_workflow_schema_path()
    assert schema_path.exists()
    assert schema_path.suffix == ".json"


# ============================================================================
# Test: validate_workflow_config - valid inputs
# ============================================================================


def test_validate_workflow_config_full(valid_workflow_dict: dict):
    """Full workflow config validates successfully."""
    config = validate_workflow_config(valid_workflow_dict)

    assert config.name == "test_workflow"
    assert config.version == "1.0"
    assert config.description == "Test workflow description"
    assert config.data_sources.population == "synthetic_french_2024"
    assert config.data_sources.emission_factors == "default"
    assert len(config.scenarios) == 2
    assert config.scenarios[0].role == "baseline"
    assert config.scenarios[0].reference == "carbon_tax_flat_44"
    assert config.run_config.projection_years == 10
    assert config.run_config.start_year == 2025
    assert len(config.outputs) == 2


def test_validate_workflow_config_minimal(minimal_workflow_dict: dict):
    """Minimal workflow config validates successfully."""
    config = validate_workflow_config(minimal_workflow_dict)

    assert config.name == "minimal_workflow"
    assert config.version == "1.0"
    assert len(config.scenarios) == 1
    assert config.scenarios[0].role == "scenario"
    assert config.scenarios[0].reference == "scenario_a"
    # Defaults
    assert config.data_sources.emission_factors == "default"
    assert config.run_config.projection_years == 10


def test_validate_workflow_config_string_scenarios():
    """String-format scenarios parse correctly."""
    data = {
        "version": "1.0",
        "name": "test",
        "scenarios": ["scenario_a", "scenario_b"],
    }
    config = validate_workflow_config(data)

    assert len(config.scenarios) == 2
    assert config.scenarios[0].role == "scenario"
    assert config.scenarios[0].reference == "scenario_a"
    assert config.scenarios[1].reference == "scenario_b"


# ============================================================================
# Test: validate_workflow_config - invalid inputs
# ============================================================================


def test_validate_workflow_config_not_dict():
    """Non-dict input raises WorkflowError."""
    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config("not a dict")  # type: ignore[arg-type]

    assert "must contain a YAML/JSON mapping" in str(exc_info.value)


def test_validate_workflow_config_missing_name():
    """Missing name field raises WorkflowError."""
    data = {"version": "1.0", "scenarios": ["a"]}

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data)

    # JSON Schema says "required property", dataclass validation says "missing required"
    error_str = str(exc_info.value).lower()
    assert "required" in error_str or "name" in error_str


def test_validate_workflow_config_missing_version():
    """Missing version field raises WorkflowError."""
    data = {"name": "test", "scenarios": ["a"]}

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data)

    # JSON Schema says "required property", dataclass validation says "missing required"
    error_str = str(exc_info.value).lower()
    assert "required" in error_str or "version" in error_str


def test_validate_workflow_config_missing_scenarios():
    """Missing scenarios field raises WorkflowError."""
    data = {"name": "test", "version": "1.0"}

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data)

    # JSON Schema says "required property", dataclass validation says "missing required"
    error_str = str(exc_info.value).lower()
    assert "required" in error_str or "scenarios" in error_str


def test_validate_workflow_config_missing_fields_lists_expected_types():
    """Missing required fields include all fields with expected types."""
    data = {}

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data)

    message = str(exc_info.value)
    assert "name (string)" in message
    assert "version (string)" in message
    assert "scenarios (array)" in message


def test_validate_workflow_config_empty_scenarios():
    """Empty scenarios list raises WorkflowError."""
    data = {"name": "test", "version": "1.0", "scenarios": []}

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data)

    # JSON Schema says "minItems", dataclass validation says "cannot be empty"
    error_str = str(exc_info.value).lower()
    assert "empty" in error_str or "minitems" in error_str or "at least" in error_str


def test_validate_workflow_config_invalid_scenario_type():
    """Invalid scenario type raises WorkflowError."""
    data = {"name": "test", "version": "1.0", "scenarios": [123]}

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data)

    # JSON Schema says "oneOf", dataclass validation says "must be a string or mapping"
    error_str = str(exc_info.value).lower()
    assert "string" in error_str or "oneof" in error_str or "valid" in error_str


def test_validate_workflow_config_multi_role_scenario_map_without_schema():
    """Fallback parser rejects scenario maps with more than one role."""
    data = {
        "name": "test",
        "version": "1.0",
        "scenarios": [{"baseline": "a", "reform": "b"}],
    }

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data, use_json_schema=False)

    assert "exactly one role mapping" in str(exc_info.value)


def test_validate_workflow_config_invalid_data_sources_type():
    """Invalid data_sources type raises WorkflowError."""
    data = {
        "name": "test",
        "version": "1.0",
        "scenarios": ["a"],
        "data_sources": "invalid",
    }

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data)

    # JSON Schema says "not of type 'object'", dataclass says "must be a mapping"
    error_str = str(exc_info.value).lower()
    assert "mapping" in error_str or "object" in error_str or "type" in error_str


def test_validate_workflow_config_invalid_run_config_type():
    """Invalid run_config type raises WorkflowError."""
    data = {
        "name": "test",
        "version": "1.0",
        "scenarios": ["a"],
        "run_config": "invalid",
    }

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data)

    # JSON Schema says "not of type 'object'", dataclass says "must be a mapping"
    error_str = str(exc_info.value).lower()
    assert "mapping" in error_str or "object" in error_str or "type" in error_str


def test_validate_workflow_config_invalid_run_config_values():
    """Invalid run_config numeric values raise WorkflowError."""
    data = {
        "name": "test",
        "version": "1.0",
        "scenarios": ["a"],
        "run_config": {"projection_years": "not a number"},
    }

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data)

    # JSON Schema says "not of type 'integer'", dataclass says "must be integers"
    error_str = str(exc_info.value).lower()
    assert "integer" in error_str or "type" in error_str


def test_validate_workflow_config_invalid_outputs_type():
    """Invalid outputs type raises WorkflowError."""
    data = {
        "name": "test",
        "version": "1.0",
        "scenarios": ["a"],
        "outputs": "invalid",
    }

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data)

    # JSON Schema says "not of type 'array'", dataclass says "must be a list"
    error_str = str(exc_info.value).lower()
    assert "list" in error_str or "array" in error_str or "type" in error_str


def test_validate_workflow_config_output_missing_type():
    """Output missing type field raises WorkflowError."""
    data = {
        "name": "test",
        "version": "1.0",
        "scenarios": ["a"],
        "outputs": [{"format": "csv"}],
    }

    with pytest.raises(WorkflowError) as exc_info:
        validate_workflow_config(data)

    # JSON Schema says "required property", dataclass says "missing required field"
    error_str = str(exc_info.value).lower()
    assert "required" in error_str or "type" in error_str


# ============================================================================
# Test: JSON Schema validation
# ============================================================================


def test_validate_with_schema_valid(valid_workflow_dict: dict):
    """Valid workflow passes JSON Schema validation."""
    errors = validate_workflow_with_schema(valid_workflow_dict)
    assert errors == []


def test_validate_with_schema_missing_required():
    """Missing required field produces schema error."""
    data = {"name": "test", "scenarios": ["a"]}  # missing version

    errors = validate_workflow_with_schema(data)

    # Should have at least one error about missing 'version'
    assert len(errors) >= 1
    error_fields = [e.invalid_fields[0] for e in errors if e.invalid_fields]
    # The error should mention version is missing
    assert any("required" in str(e) or "version" in str(e) for e in errors)


def test_validate_with_schema_invalid_type():
    """Invalid type produces schema error with field path."""
    data = {
        "name": "test",
        "version": "1.0",
        "scenarios": ["a"],
        "run_config": {"projection_years": "not a number"},
    }

    errors = validate_workflow_with_schema(data)

    # Should have error about projection_years type
    assert len(errors) >= 1
    assert any("projection_years" in field for e in errors for field in e.invalid_fields)
    assert any("json-pointer: /run_config/projection_years" in str(e) for e in errors)
    assert any("instead of 'str'" in str(e) for e in errors)


# ============================================================================
# Test: load_workflow_config from files
# ============================================================================


def test_load_workflow_config_yaml(valid_workflow_dict: dict):
    """Load workflow from YAML file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.safe_dump(valid_workflow_dict, f)
        path = Path(f.name)

    try:
        config = load_workflow_config(path)

        assert config.name == "test_workflow"
        assert config.format == "yaml"
    finally:
        path.unlink()


def test_load_workflow_config_yml_extension(minimal_workflow_dict: dict):
    """Load workflow from .yml file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False, encoding="utf-8"
    ) as f:
        yaml.safe_dump(minimal_workflow_dict, f)
        path = Path(f.name)

    try:
        config = load_workflow_config(path)

        assert config.name == "minimal_workflow"
        assert config.format == "yaml"
    finally:
        path.unlink()


def test_load_workflow_config_json(valid_workflow_dict: dict):
    """Load workflow from JSON file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(valid_workflow_dict, f)
        path = Path(f.name)

    try:
        config = load_workflow_config(path)

        assert config.name == "test_workflow"
        assert config.format == "json"
    finally:
        path.unlink()


def test_load_workflow_config_file_not_found():
    """Missing file raises WorkflowError."""
    with pytest.raises(WorkflowError) as exc_info:
        load_workflow_config("/nonexistent/workflow.yaml")

    assert "was not found" in str(exc_info.value)


def test_load_workflow_config_unsupported_extension():
    """Unsupported extension raises WorkflowError."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("name: test")
        path = Path(f.name)

    try:
        with pytest.raises(WorkflowError) as exc_info:
            load_workflow_config(path)

        assert "unsupported file extension" in str(exc_info.value)
    finally:
        path.unlink()


def test_load_workflow_config_invalid_yaml():
    """Invalid YAML syntax raises WorkflowError with line number."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        f.write("name: test\n  invalid: indentation")
        path = Path(f.name)

    try:
        with pytest.raises(WorkflowError) as exc_info:
            load_workflow_config(path)

        assert "invalid YAML syntax" in str(exc_info.value)
        # YAML errors should include line number
        assert exc_info.value.line_number is not None or "line" in str(exc_info.value)
    finally:
        path.unlink()


def test_load_workflow_config_invalid_json():
    """Invalid JSON syntax raises WorkflowError with line number."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        f.write('{"name": "test", invalid}')
        path = Path(f.name)

    try:
        with pytest.raises(WorkflowError) as exc_info:
            load_workflow_config(path)

        assert "invalid JSON syntax" in str(exc_info.value)
        assert exc_info.value.line_number is not None
    finally:
        path.unlink()


# ============================================================================
# Test: dump_workflow_config and round-trip stability
# ============================================================================


def test_dump_workflow_config_yaml(valid_workflow_config: WorkflowConfig):
    """Dump workflow to YAML file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        path = Path(f.name)

    try:
        dump_workflow_config(valid_workflow_config, path)

        # File should exist and be valid YAML
        assert path.exists()
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["name"] == "test_workflow"
    finally:
        path.unlink()


def test_dump_workflow_config_json(valid_workflow_config: WorkflowConfig):
    """Dump workflow to JSON file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        path = Path(f.name)

    try:
        dump_workflow_config(valid_workflow_config, path)

        # File should exist and be valid JSON
        assert path.exists()
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["name"] == "test_workflow"
    finally:
        path.unlink()


def test_dump_workflow_config_invalid_format(valid_workflow_config: WorkflowConfig):
    """Unsupported dump format override raises WorkflowError."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        path = Path(f.name)

    try:
        with pytest.raises(WorkflowError) as exc_info:
            dump_workflow_config(valid_workflow_config, path, format="toml")

        assert "unsupported format override" in str(exc_info.value)
    finally:
        path.unlink()


def test_round_trip_yaml(valid_workflow_dict: dict):
    """YAML round-trip preserves semantic content."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    ) as f:
        yaml.safe_dump(valid_workflow_dict, f)
        path1 = Path(f.name)

    try:
        # Load -> dump -> load
        config1 = load_workflow_config(path1)

        path2 = Path(tempfile.mktemp(suffix=".yaml"))
        dump_workflow_config(config1, path2)

        config2 = load_workflow_config(path2)

        # Semantic content should be identical
        assert config1.name == config2.name
        assert config1.version == config2.version
        assert config1.data_sources == config2.data_sources
        assert config1.scenarios == config2.scenarios
        assert config1.run_config == config2.run_config
        assert config1.outputs == config2.outputs

        path2.unlink()
    finally:
        path1.unlink()


def test_round_trip_json(valid_workflow_dict: dict):
    """JSON round-trip preserves semantic content."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(valid_workflow_dict, f)
        path1 = Path(f.name)

    try:
        # Load -> dump -> load
        config1 = load_workflow_config(path1)

        path2 = Path(tempfile.mktemp(suffix=".json"))
        dump_workflow_config(config1, path2)

        config2 = load_workflow_config(path2)

        # Semantic content should be identical
        assert config1.name == config2.name
        assert config1.version == config2.version
        assert config1.data_sources == config2.data_sources
        assert config1.scenarios == config2.scenarios

        path2.unlink()
    finally:
        path1.unlink()


def test_json_output_deterministic():
    """JSON output has stable key ordering."""
    config = WorkflowConfig(
        name="test",
        version="1.0",
        data_sources=DataSourceConfig(),
        scenarios=(ScenarioRef(role="baseline", reference="a"),),
        run_config=RunConfig(),
    )

    json_str1 = workflow_to_json(config)
    json_str2 = workflow_to_json(config)

    assert json_str1 == json_str2


def test_yaml_output_readable():
    """YAML output is human-readable (not flow style)."""
    config = WorkflowConfig(
        name="test",
        version="1.0",
        data_sources=DataSourceConfig(population="test_pop"),
        scenarios=(ScenarioRef(role="baseline", reference="a"),),
        run_config=RunConfig(),
    )

    yaml_str = workflow_to_yaml(config)

    # Should not use flow style (inline {})
    assert "{" not in yaml_str or "$schema" in yaml_str
    # Should have proper indentation
    assert "\n" in yaml_str


# ============================================================================
# Test: Execution handoff API
# ============================================================================


def test_prepare_workflow_request(valid_workflow_config: WorkflowConfig):
    """prepare_workflow_request creates valid request payload."""
    request = prepare_workflow_request(valid_workflow_config)

    assert request["name"] == "test_workflow"
    assert request["version"] == "1.0"
    assert request["data_sources"]["population"] == "synthetic_french_2024"
    assert len(request["scenarios"]) == 2
    assert request["scenarios"][0]["role"] == "baseline"
    assert request["run_config"]["projection_years"] == 10


def test_run_workflow_no_runner(valid_workflow_config: WorkflowConfig):
    """run_workflow without runner raises WorkflowError."""
    with pytest.raises(WorkflowError) as exc_info:
        run_workflow(valid_workflow_config)

    assert "no runtime backend is configured" in str(exc_info.value)
    assert "EPIC-3" in str(exc_info.value)  # Should mention orchestrator


def test_run_workflow_with_runner(valid_workflow_config: WorkflowConfig):
    """run_workflow with runner delegates correctly."""

    class MockRunner:
        def run(self, request: dict) -> WorkflowResult:
            return WorkflowResult(
                success=True,
                outputs={"test": "output"},
                metadata={"request_name": request["name"]},
            )

    runner = MockRunner()
    result = run_workflow(valid_workflow_config, runner=runner)

    assert result.success is True
    assert result.outputs == {"test": "output"}
    assert result.metadata["request_name"] == "test_workflow"


def test_run_workflow_runner_returns_dict(valid_workflow_config: WorkflowConfig):
    """run_workflow handles runner returning dict."""

    class DictRunner:
        def run(self, request: dict) -> dict:
            return {
                "success": True,
                "outputs": {"data": "result"},
            }

    runner = DictRunner()
    result = run_workflow(valid_workflow_config, runner=runner)

    assert isinstance(result, WorkflowResult)
    assert result.success is True
    assert result.outputs == {"data": "result"}


def test_run_workflow_invalid_runner(valid_workflow_config: WorkflowConfig):
    """run_workflow with invalid runner raises WorkflowError."""

    class InvalidRunner:
        pass  # No run method

    with pytest.raises(WorkflowError) as exc_info:
        run_workflow(valid_workflow_config, runner=InvalidRunner())

    assert "callable 'run(request)' method" in str(exc_info.value)


def test_run_workflow_runner_invalid_response_type(
    valid_workflow_config: WorkflowConfig,
):
    """run_workflow rejects unsupported runner response payload types."""

    class InvalidResponseRunner:
        def run(self, request: dict) -> int:
            return 123

    with pytest.raises(WorkflowError) as exc_info:
        run_workflow(valid_workflow_config, runner=InvalidResponseRunner())

    assert "must return WorkflowResult or dict" in str(exc_info.value)


def test_run_workflow_runner_exception_is_wrapped(valid_workflow_config: WorkflowConfig):
    """Runner exceptions are wrapped as WorkflowError with context."""

    class CrashingRunner:
        def run(self, request: dict) -> WorkflowResult:
            raise RuntimeError("backend crashed")

    with pytest.raises(WorkflowError) as exc_info:
        run_workflow(valid_workflow_config, runner=CrashingRunner())

    assert "runner raised RuntimeError: backend crashed" in str(exc_info.value)


def test_run_workflow_validates_empty_reference():
    """run_workflow validates scenario references."""
    config = WorkflowConfig(
        name="test",
        version="1.0",
        data_sources=DataSourceConfig(),
        scenarios=(ScenarioRef(role="baseline", reference=""),),  # Empty reference
        run_config=RunConfig(),
    )

    with pytest.raises(WorkflowError) as exc_info:
        run_workflow(config)

    assert "empty reference" in str(exc_info.value)


# ============================================================================
# Test: Shipped example validation
# ============================================================================


def test_load_carbon_tax_analysis_example():
    """carbon_tax_analysis.yaml example validates."""
    example_path = Path("examples/workflows/carbon_tax_analysis.yaml")
    if not example_path.exists():
        pytest.skip("Example file not found (run from project root)")

    config = load_workflow_config(example_path)

    assert config.name == "carbon_tax_analysis"
    assert config.version == "1.0"
    assert len(config.scenarios) >= 1


def test_load_scenario_comparison_example():
    """scenario_comparison.yaml example validates."""
    example_path = Path("examples/workflows/scenario_comparison.yaml")
    if not example_path.exists():
        pytest.skip("Example file not found (run from project root)")

    config = load_workflow_config(example_path)

    assert config.name == "carbon_tax_comparison"
    assert len(config.scenarios) >= 2


def test_load_batch_sensitivity_example():
    """batch_sensitivity.json example validates."""
    example_path = Path("examples/workflows/batch_sensitivity.json")
    if not example_path.exists():
        pytest.skip("Example file not found (run from project root)")

    config = load_workflow_config(example_path)

    assert config.name == "batch_sensitivity_analysis"
    assert config.format == "json"
    assert len(config.scenarios) >= 3


# ============================================================================
# Test: Error message quality
# ============================================================================


def test_error_includes_file_path():
    """WorkflowError includes file path in message."""
    error = WorkflowError(
        file_path=Path("/test/file.yaml"),
        summary="Test error",
        reason="test reason",
        fix="test fix",
    )

    assert "/test/file.yaml" in str(error)


def test_error_includes_line_number():
    """WorkflowError includes line number when available."""
    error = WorkflowError(
        file_path=Path("/test/file.yaml"),
        summary="Test error",
        reason="test reason",
        fix="test fix",
        line_number=42,
    )

    assert "line: 42" in str(error)


def test_error_includes_invalid_fields():
    """WorkflowError tracks invalid fields."""
    error = WorkflowError(
        summary="Test error",
        reason="test reason",
        fix="test fix",
        invalid_fields=("field1", "field2"),
    )

    assert error.invalid_fields == ("field1", "field2")
