"""Capture helpers for manifest generation.

Provides functions to capture assumptions, mappings, parameters, and warnings
at orchestrator execution time for immutable manifest storage.

This module implements the capture logic for FR26 (assumption/mapping transparency)
and FR27 (unvalidated template warnings).
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.computation.mapping import MappingConfig


def capture_assumptions(
    *,
    defaults: dict[str, Any] | None = None,
    overrides: dict[str, Any] | None = None,
    source_label: str = "runtime",
) -> list[dict[str, Any]]:
    """Capture structured assumption entries from defaults and overrides.

    Args:
        defaults: Default assumption values (key -> value mapping).
        overrides: User-provided override values (key -> value mapping).
        source_label: Source label for assumptions (e.g., "scenario", "runtime").

    Returns:
        List of structured assumption entries with key/value/source/is_default.

    Example:
        >>> defaults = {"discount_rate": 0.03, "inflation": 0.02}
        >>> overrides = {"discount_rate": 0.05}
        >>> capture_assumptions(defaults=defaults, overrides=overrides)
        [
            {
                "key": "discount_rate",
                "value": 0.05,
                "source": "runtime",
                "is_default": False
            },
            {
                "key": "inflation",
                "value": 0.02,
                "source": "runtime",
                "is_default": True
            }
        ]
    """
    defaults = defaults or {}
    overrides = overrides or {}

    assumptions: list[dict[str, Any]] = []

    # Collect all keys
    all_keys = set(defaults.keys()) | set(overrides.keys())

    for key in sorted(all_keys):
        if key in overrides:
            # User override
            assumptions.append(
                {
                    "key": key,
                    "value": deepcopy(overrides[key]),
                    "source": source_label,
                    "is_default": False,
                }
            )
        else:
            # Default value
            assumptions.append(
                {
                    "key": key,
                    "value": deepcopy(defaults[key]),
                    "source": source_label,
                    "is_default": True,
                }
            )

    return assumptions


def capture_mappings(config: MappingConfig) -> list[dict[str, Any]]:
    """Capture mapping configuration as structured entries.

    Args:
        config: MappingConfig object from runtime execution.

    Returns:
        List of mapping entries with openfisca_name/project_name/direction/source_file.

    Example:
        >>> mapping_config = load_mapping("path/to/mapping.yaml")
        >>> capture_mappings(mapping_config)
        [
            {
                "openfisca_name": "household_income",
                "project_name": "income",
                "direction": "input",
                "source_file": "/path/to/mapping.yaml"
            },
            ...
        ]
    """
    mappings: list[dict[str, Any]] = []

    for field_mapping in config.mappings:
        entry: dict[str, Any] = {
            "openfisca_name": field_mapping.openfisca_name,
            "project_name": field_mapping.project_name,
            "direction": field_mapping.direction,
        }

        # Add source file if available
        if config.source_path is not None:
            entry["source_file"] = str(config.source_path)

        mappings.append(entry)

    return mappings


def capture_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    """Capture parameter snapshot with deep copy for immutability.

    Creates a detached deep copy of the parameter dictionary to ensure
    the manifest capture is immutable and not affected by subsequent
    mutations of the source parameters.

    Args:
        parameters: Parameter dictionary from scenario/template.

    Returns:
        Deep-copied parameter dictionary (JSON-compatible).

    Example:
        >>> params = {"tax_rate": 0.15, "exemptions": ["food", "medicine"]}
        >>> snapshot = capture_parameters(params)
        >>> params["tax_rate"] = 0.20  # Mutation does not affect snapshot
        >>> snapshot["tax_rate"]
        0.15
    """
    return deepcopy(parameters)


def capture_unvalidated_template_warning(
    *,
    scenario_name: str,
    scenario_version: str,
    is_validated: bool = False,
) -> str | None:
    """Generate warning if template/scenario is not validated.

    Args:
        scenario_name: Name of the scenario/template.
        scenario_version: Version identifier.
        is_validated: Whether the scenario is marked as validated.

    Returns:
        Warning message string if not validated, None otherwise.

    Example:
        >>> warning = capture_unvalidated_template_warning(
        ...     scenario_name="carbon-tax-2026",
        ...     scenario_version="abc123",
        ...     is_validated=False
        ... )
        >>> print(warning)
        WARNING: Scenario 'carbon-tax-2026' (version 'abc123') is not marked as
        validated in registry metadata. Action: Mark this scenario as validated
        before relying on outputs for production decisions.
    """
    if is_validated:
        return None

    return (
        f"WARNING: Scenario '{scenario_name}' (version '{scenario_version}') is not "
        "marked as validated in registry metadata. Action: Mark this scenario as "
        "validated before relying on outputs for production decisions."
    )


def capture_warnings(
    *,
    scenario_name: str = "",
    scenario_version: str = "",
    is_validated: bool = False,
    additional_warnings: list[str] | None = None,
) -> list[str]:
    """Capture all warnings for manifest generation.

    Consolidates unvalidated template warnings and any additional warnings
    from execution.

    Args:
        scenario_name: Name of the scenario/template.
        scenario_version: Version identifier.
        is_validated: Whether the scenario is marked as validated.
        additional_warnings: Optional list of additional warning strings.

    Returns:
        List of warning strings (empty if no warnings).

    Example:
        >>> warnings = capture_warnings(
        ...     scenario_name="test-scenario",
        ...     scenario_version="v1",
        ...     is_validated=False,
        ...     additional_warnings=["Data quality issue detected"]
        ... )
        >>> len(warnings)
        2
    """
    warnings: list[str] = []

    # Add unvalidated template warning if applicable
    if scenario_name and scenario_version:
        unvalidated_warning = capture_unvalidated_template_warning(
            scenario_name=scenario_name,
            scenario_version=scenario_version,
            is_validated=is_validated,
        )
        if unvalidated_warning:
            warnings.append(unvalidated_warning)

    # Add any additional warnings
    if additional_warnings:
        warnings.extend(additional_warnings)

    return warnings
