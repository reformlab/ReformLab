from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from reformlab.templates.loader import (
    SCHEMA_VERSION,
    get_schema_path,
    load_scenario_template,
    validate_schema_version,
)


# ---------------------------------------------------------------------------
# Task 4 tests: JSON Schema for YAML validation (AC #4)
# ---------------------------------------------------------------------------


class TestJSONSchemaFile:
    """Tests for JSON Schema file existence and validity (Subtask 4.1, 4.2)."""

    def test_json_schema_file_exists(self) -> None:
        """JSON Schema file exists at expected location."""
        schema_path = get_schema_path()
        assert schema_path.exists()
        assert schema_path.name == "scenario-template.schema.json"

    def test_json_schema_is_valid_json(self) -> None:
        """JSON Schema file is valid JSON."""
        schema_path = get_schema_path()
        content = schema_path.read_text(encoding="utf-8")
        schema = json.loads(content)  # Should not raise
        assert isinstance(schema, dict)

    def test_json_schema_has_required_structure(self) -> None:
        """JSON Schema has required $schema and properties."""
        schema_path = get_schema_path()
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        assert "$schema" in schema
        assert "properties" in schema
        assert "required" in schema
        assert "parameters" in schema["required"]

    def test_json_schema_requires_non_empty_parameters(self) -> None:
        """Schema enforces at least one parameter key."""
        schema_path = get_schema_path()
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        params = schema["properties"]["parameters"]
        assert params.get("minProperties") == 1

    def test_json_schema_has_field_descriptions(self) -> None:
        """JSON Schema includes descriptions for IDE autocompletion (AC-4)."""
        schema_path = get_schema_path()
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        # Check top-level description
        assert "description" in schema

        # Check key properties have descriptions
        props = schema["properties"]
        assert "description" in props.get("name", {})
        assert "description" in props.get("policy_type", {})
        assert "description" in props.get("version", {})
        assert "description" in props.get("year_schedule", {})
        assert "description" in props.get("parameters", {})

    def test_json_schema_defines_policy_types(self) -> None:
        """JSON Schema enum matches Python PolicyType values."""
        schema_path = get_schema_path()
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        policy_type_prop = schema["properties"]["policy_type"]
        assert "enum" in policy_type_prop
        assert set(policy_type_prop["enum"]) == {"carbon_tax", "subsidy", "rebate", "feebate"}


class TestSchemaVersionInTemplates:
    """Tests for schema version validation (Subtask 4.3, 4.4)."""

    def test_schema_version_constant_defined(self) -> None:
        """SCHEMA_VERSION constant is defined."""
        assert SCHEMA_VERSION == "1.0"

    def test_loaded_scenario_has_version(self, valid_carbon_tax_yaml: Path) -> None:
        """Loaded scenarios have version field."""
        scenario = load_scenario_template(valid_carbon_tax_yaml)
        assert scenario.version == "1.0"

    def test_validate_schema_version_accepts_matching(self) -> None:
        """validate_schema_version accepts matching version."""
        # Should not raise
        validate_schema_version("1.0")

    def test_validate_schema_version_warns_minor_mismatch(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """validate_schema_version warns on minor version mismatch."""
        caplog.set_level("WARNING")
        validate_schema_version("1.1")  # Minor version higher than supported
        logs = " ".join(record.getMessage() for record in caplog.records)
        assert "version" in logs.lower()

    def test_validate_schema_version_errors_major_mismatch(self) -> None:
        """validate_schema_version raises on major version mismatch."""
        from reformlab.templates.exceptions import ScenarioError

        with pytest.raises(ScenarioError, match="version"):
            validate_schema_version("2.0", strict=True)

    def test_missing_schema_ref_in_yaml_loads_successfully(
        self, tmp_path: Path
    ) -> None:
        """YAML without $schema loads successfully with default version."""
        content = textwrap.dedent("""\
            version: "1.0"
            name: "No Schema Ref"
            policy_type: carbon_tax
            year_schedule:
              start_year: 2026
              end_year: 2036
            parameters:
              rate_schedule:
                2026: 44.60
        """)
        p = tmp_path / "no-schema-ref.yaml"
        p.write_text(content, encoding="utf-8")
        scenario = load_scenario_template(p)
        assert scenario.version == "1.0"
