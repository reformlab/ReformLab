"""Tests for manifest capture helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from reformlab.computation.mapping import FieldMapping, MappingConfig
from reformlab.governance.capture import (
    capture_assumptions,
    capture_mappings,
    capture_parameters,
    capture_unvalidated_template_warning,
    capture_warnings,
)


class TestCaptureAssumptions:
    """Tests for capture_assumptions()."""

    def test_capture_defaults_only(self) -> None:
        """Capture assumptions from defaults only."""
        defaults = {"discount_rate": 0.03, "inflation": 0.02}
        result = capture_assumptions(defaults=defaults, source_label="scenario")

        assert len(result) == 2
        assert result[0] == {
            "key": "discount_rate",
            "value": 0.03,
            "source": "scenario",
            "is_default": True,
        }
        assert result[1] == {
            "key": "inflation",
            "value": 0.02,
            "source": "scenario",
            "is_default": True,
        }

    def test_capture_overrides_only(self) -> None:
        """Capture assumptions from overrides only."""
        overrides = {"custom_param": 42}
        result = capture_assumptions(overrides=overrides, source_label="user")

        assert len(result) == 1
        assert result[0] == {
            "key": "custom_param",
            "value": 42,
            "source": "user",
            "is_default": False,
        }

    def test_capture_mixed_defaults_and_overrides(self) -> None:
        """Capture assumptions with both defaults and overrides."""
        defaults = {"discount_rate": 0.03, "inflation": 0.02, "tax_rate": 0.15}
        overrides = {"discount_rate": 0.05}

        result = capture_assumptions(
            defaults=defaults, overrides=overrides, source_label="runtime"
        )

        assert len(result) == 3

        # Overridden value
        discount_entry = next(r for r in result if r["key"] == "discount_rate")
        assert discount_entry["value"] == 0.05
        assert discount_entry["is_default"] is False

        # Default values
        inflation_entry = next(r for r in result if r["key"] == "inflation")
        assert inflation_entry["value"] == 0.02
        assert inflation_entry["is_default"] is True

        tax_entry = next(r for r in result if r["key"] == "tax_rate")
        assert tax_entry["value"] == 0.15
        assert tax_entry["is_default"] is True

    def test_capture_empty(self) -> None:
        """Capture assumptions with no inputs."""
        result = capture_assumptions()
        assert result == []

    def test_capture_detaches_from_source(self) -> None:
        """Captured assumptions are detached from source dictionaries."""
        defaults = {"nested": {"value": 100}}
        result = capture_assumptions(defaults=defaults)

        # Mutate source
        defaults["nested"]["value"] = 200

        # Captured value should be unchanged
        assert result[0]["value"] == {"value": 100}

    def test_capture_sorted_keys(self) -> None:
        """Assumptions are captured in sorted key order."""
        defaults = {"z_param": 1, "a_param": 2, "m_param": 3}
        result = capture_assumptions(defaults=defaults)

        keys = [r["key"] for r in result]
        assert keys == ["a_param", "m_param", "z_param"]


class TestCaptureMappings:
    """Tests for capture_mappings()."""

    def test_capture_mappings_with_source_path(self) -> None:
        """Capture mappings with source file path."""
        config = MappingConfig(
            mappings=(
                FieldMapping(
                    openfisca_name="household_income",
                    project_name="income",
                    direction="input",
                    pa_type=None,  # type: ignore[arg-type]
                ),
                FieldMapping(
                    openfisca_name="carbon_tax_paid",
                    project_name="tax_paid",
                    direction="output",
                    pa_type=None,  # type: ignore[arg-type]
                ),
            ),
            source_path=Path("/tmp/mappings.yaml"),
        )

        result = capture_mappings(config)

        assert len(result) == 2
        assert result[0] == {
            "openfisca_name": "household_income",
            "project_name": "income",
            "direction": "input",
            "source_file": "/tmp/mappings.yaml",
        }
        assert result[1] == {
            "openfisca_name": "carbon_tax_paid",
            "project_name": "tax_paid",
            "direction": "output",
            "source_file": "/tmp/mappings.yaml",
        }

    def test_capture_mappings_without_source_path(self) -> None:
        """Capture mappings without source file path."""
        config = MappingConfig(
            mappings=(
                FieldMapping(
                    openfisca_name="age",
                    project_name="person_age",
                    direction="both",
                    pa_type=None,  # type: ignore[arg-type]
                ),
            ),
            source_path=None,
        )

        result = capture_mappings(config)

        assert len(result) == 1
        assert result[0] == {
            "openfisca_name": "age",
            "project_name": "person_age",
            "direction": "both",
        }

    def test_capture_empty_mappings(self) -> None:
        """Capture empty mapping configuration."""
        config = MappingConfig(mappings=(), source_path=None)
        result = capture_mappings(config)
        assert result == []

    def test_capture_mappings_with_transform_identifier(self) -> None:
        """Capture transform metadata when present on mapping objects."""
        config = SimpleNamespace(
            mappings=(
                SimpleNamespace(
                    openfisca_name="income",
                    project_name="household_income",
                    direction="input",
                    transform="normalize_income",
                ),
            ),
            source_path=Path("/tmp/mappings.yaml"),
        )

        result = capture_mappings(config)  # type: ignore[arg-type]

        assert result[0]["transform"] == "normalize_income"


class TestCaptureParameters:
    """Tests for capture_parameters()."""

    def test_capture_simple_parameters(self) -> None:
        """Capture simple parameter dictionary."""
        params = {"rate": 0.15, "threshold": 1000}
        result = capture_parameters(params)

        assert result == {"rate": 0.15, "threshold": 1000}

    def test_capture_nested_parameters(self) -> None:
        """Capture nested parameter structure."""
        params = {
            "tax": {"rate": 0.15, "brackets": [10000, 50000, 100000]},
            "rebate": {"amount": 500},
        }
        result = capture_parameters(params)

        assert result == params

    def test_capture_detaches_from_source(self) -> None:
        """Parameter snapshot is detached from source."""
        params = {"nested": {"value": 100}}
        snapshot = capture_parameters(params)

        # Mutate source
        params["nested"]["value"] = 200

        # Snapshot should be unchanged
        assert snapshot["nested"]["value"] == 100

    def test_capture_empty_parameters(self) -> None:
        """Capture empty parameter dictionary."""
        result = capture_parameters({})
        assert result == {}

    def test_capture_parameters_rejects_non_dict(self) -> None:
        """Parameter capture enforces dictionary payloads."""
        with pytest.raises(TypeError, match="parameters must be a dictionary"):
            capture_parameters([])  # type: ignore[arg-type]


class TestCaptureUnvalidatedTemplateWarning:
    """Tests for capture_unvalidated_template_warning()."""

    def test_warning_for_unvalidated_scenario(self) -> None:
        """Generate warning for unvalidated scenario."""
        warning = capture_unvalidated_template_warning(
            scenario_name="test-scenario",
            scenario_version="v1.0",
            is_validated=False,
        )

        assert warning is not None
        assert "test-scenario" in warning
        assert "v1.0" in warning
        assert "not marked as validated" in warning
        assert "Action:" in warning

    def test_no_warning_for_validated_scenario(self) -> None:
        """No warning for validated scenario."""
        warning = capture_unvalidated_template_warning(
            scenario_name="test-scenario",
            scenario_version="v1.0",
            is_validated=True,
        )

        assert warning is None


class TestCaptureWarnings:
    """Tests for capture_warnings()."""

    def test_capture_unvalidated_warning_only(self) -> None:
        """Capture unvalidated template warning only."""
        warnings = capture_warnings(
            scenario_name="test", scenario_version="v1", is_validated=False
        )

        assert len(warnings) == 1
        assert "test" in warnings[0]
        assert "not marked as validated" in warnings[0]

    def test_capture_additional_warnings_only(self) -> None:
        """Capture additional warnings only."""
        warnings = capture_warnings(
            additional_warnings=["Warning 1", "Warning 2"],
        )

        assert len(warnings) == 2
        assert warnings == ["Warning 1", "Warning 2"]

    def test_capture_combined_warnings(self) -> None:
        """Capture both unvalidated and additional warnings."""
        warnings = capture_warnings(
            scenario_name="test",
            scenario_version="v1",
            is_validated=False,
            additional_warnings=["Data quality issue"],
        )

        assert len(warnings) == 2
        assert "not marked as validated" in warnings[0]
        assert warnings[1] == "Data quality issue"

    def test_capture_no_warnings(self) -> None:
        """No warnings captured when all validated."""
        warnings = capture_warnings(
            scenario_name="test", scenario_version="v1", is_validated=True
        )

        assert warnings == []

    def test_capture_validated_with_additional_warnings(self) -> None:
        """Capture only additional warnings when scenario is validated."""
        warnings = capture_warnings(
            scenario_name="test",
            scenario_version="v1",
            is_validated=True,
            additional_warnings=["Custom warning"],
        )

        assert len(warnings) == 1
        assert warnings[0] == "Custom warning"

    def test_capture_warning_with_missing_version_metadata(self) -> None:
        """Missing validation metadata still emits actionable warning."""
        warnings = capture_warnings(
            scenario_name="policy-x",
            scenario_version="",
            is_validated=None,
        )

        assert len(warnings) == 1
        assert "policy-x" in warnings[0]
        assert "version 'unknown'" in warnings[0]
