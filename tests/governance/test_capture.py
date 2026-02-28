"""Tests for manifest capture helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from reformlab.computation.mapping import FieldMapping, MappingConfig
from reformlab.governance.capture import (
    TESTED_MAX_HORIZON_YEARS,
    TESTED_MAX_POPULATION_SIZE,
    capture_assumptions,
    capture_mappings,
    capture_parameters,
    capture_unsupported_config_warning,
    capture_unvalidated_mapping_warning,
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

    def test_capture_mapping_warning_via_capture_warnings(self) -> None:
        """capture_warnings emits mapping warning when mapping_config is unvalidated."""
        config = MappingConfig(
            mappings=(),
            source_path=Path("/tmp/test-mapping.yaml"),
            is_validated=False,
        )
        warnings = capture_warnings(
            scenario_name="test",
            scenario_version="v1",
            is_validated=True,
            mapping_config=config,
        )

        assert len(warnings) == 1
        assert "test-mapping.yaml" in warnings[0]
        assert "not marked as validated" in warnings[0]

    def test_capture_no_mapping_warning_when_validated(self) -> None:
        """capture_warnings skips mapping warning when mapping_config is validated."""
        config = MappingConfig(
            mappings=(),
            source_path=Path("/tmp/test-mapping.yaml"),
            is_validated=True,
        )
        warnings = capture_warnings(
            scenario_name="test",
            scenario_version="v1",
            is_validated=True,
            mapping_config=config,
        )

        assert warnings == []


class TestCaptureUnvalidatedMappingWarning:
    """Tests for capture_unvalidated_mapping_warning() (Story 5-6, AC-2)."""

    def test_warning_for_unvalidated_mapping(self) -> None:
        """Generate warning for unvalidated mapping."""
        warning = capture_unvalidated_mapping_warning(
            source_file="/tmp/mappings.yaml",
            is_validated=False,
        )

        assert warning is not None
        assert "mappings.yaml" in warning
        assert "not marked as validated" in warning
        assert "Action:" in warning

    def test_no_warning_for_validated_mapping(self) -> None:
        """No warning for validated mapping."""
        warning = capture_unvalidated_mapping_warning(
            source_file="/tmp/mappings.yaml",
            is_validated=True,
        )

        assert warning is None

    def test_warning_with_none_validation(self) -> None:
        """Warning emitted when is_validated is None (unknown)."""
        warning = capture_unvalidated_mapping_warning(
            source_file="/tmp/mappings.yaml",
            is_validated=None,
        )

        assert warning is not None
        assert "not marked as validated" in warning

    def test_warning_with_empty_source_file(self) -> None:
        """Empty source_file defaults to 'unknown'."""
        warning = capture_unvalidated_mapping_warning(
            source_file="",
            is_validated=False,
        )

        assert warning is not None
        assert "'unknown'" in warning

    def test_warning_format_matches_ac2(self) -> None:
        """Warning format matches AC-2 specification."""
        warning = capture_unvalidated_mapping_warning(
            source_file="my-mapping.yaml",
            is_validated=False,
        )

        assert warning == (
            "WARNING: Mapping configuration 'my-mapping.yaml' is not marked as "
            "validated. Action: Review mapping correctness before relying on outputs."
        )


class TestCaptureUnsupportedConfigWarning:
    """Tests for capture_unsupported_config_warning() (Story 5-6, AC-3)."""

    def test_no_warnings_within_tested_range(self) -> None:
        """No warnings when parameters are within tested ranges."""
        warnings = capture_unsupported_config_warning(
            horizon_years=10,
            population_size=50_000,
        )
        assert warnings == []

    def test_warning_for_large_horizon(self) -> None:
        """Warning for projection horizon exceeding tested range."""
        warnings = capture_unsupported_config_warning(horizon_years=25)

        assert len(warnings) == 1
        assert "25 years" in warnings[0]
        assert "exceeds tested range" in warnings[0]
        assert "Action:" in warnings[0]

    def test_warning_for_large_population(self) -> None:
        """Warning for population size exceeding test coverage."""
        warnings = capture_unsupported_config_warning(population_size=200_000)

        assert len(warnings) == 1
        assert "200,000" in warnings[0]
        assert "exceeds standard test coverage" in warnings[0]
        assert "Action:" in warnings[0]

    def test_both_warnings(self) -> None:
        """Both warnings emitted when both exceed ranges."""
        warnings = capture_unsupported_config_warning(
            horizon_years=30,
            population_size=500_000,
        )
        assert len(warnings) == 2

    def test_no_warning_at_boundary(self) -> None:
        """No warning when exactly at tested limits."""
        warnings = capture_unsupported_config_warning(
            horizon_years=TESTED_MAX_HORIZON_YEARS,
            population_size=TESTED_MAX_POPULATION_SIZE,
        )
        assert warnings == []

    def test_warning_one_above_boundary(self) -> None:
        """Warning when one above tested limits."""
        warnings = capture_unsupported_config_warning(
            horizon_years=TESTED_MAX_HORIZON_YEARS + 1,
        )
        assert len(warnings) == 1

    def test_no_warnings_with_none_values(self) -> None:
        """No warnings when parameters are None."""
        warnings = capture_unsupported_config_warning(
            horizon_years=None,
            population_size=None,
        )
        assert warnings == []

    def test_horizon_warning_format_matches_ac3(self) -> None:
        """Horizon warning format matches AC-3 specification."""
        warnings = capture_unsupported_config_warning(horizon_years=25)
        assert warnings[0] == (
            "WARNING: Projection horizon of 25 years exceeds tested "
            f"range (10-{TESTED_MAX_HORIZON_YEARS} years). Action: Results for years "
            "beyond tested range may have reduced credibility."
        )

    def test_population_warning_format_matches_ac3(self) -> None:
        """Population warning format matches AC-3 specification."""
        warnings = capture_unsupported_config_warning(population_size=200_000)
        assert warnings[0] == (
            "WARNING: Population size (200,000 households) exceeds "
            f"standard test coverage ({TESTED_MAX_POPULATION_SIZE:,}). Action: "
            "Review memory usage and consider chunked processing."
        )
