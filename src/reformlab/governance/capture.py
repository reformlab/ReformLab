# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Capture helpers for manifest generation.

Provides functions to capture assumptions, mappings, parameters, and warnings
at orchestrator execution time for immutable manifest storage.

This module implements the capture logic for FR26 (assumption/mapping transparency),
FR27 (unvalidated template warnings), and FR50/FR51 (discrete choice parameters).
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.computation.mapping import MappingConfig
    from reformlab.discrete_choice.technology_set import TechnologySet


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
    normalized_source = source_label.strip() or "runtime"

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
                    "source": normalized_source,
                    "is_default": False,
                }
            )
        else:
            # Default value
            assumptions.append(
                {
                    "key": key,
                    "value": deepcopy(defaults[key]),
                    "source": normalized_source,
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
        transform_identifier = getattr(field_mapping, "transform", None)
        if isinstance(transform_identifier, str) and transform_identifier.strip():
            entry["transform"] = transform_identifier

        mappings.append(entry)

    return mappings


def capture_policy(policy: dict[str, Any]) -> dict[str, Any]:
    """Capture policy snapshot with deep copy for immutability.

    Creates a detached deep copy of the policy dictionary to ensure
    the manifest capture is immutable and not affected by subsequent
    mutations of the source policy.

    Args:
        policy: Policy dictionary from scenario/template.

    Returns:
        Deep-copied policy dictionary (JSON-compatible).

    Example:
        >>> params = {"tax_rate": 0.15, "exemptions": ["food", "medicine"]}
        >>> snapshot = capture_policy(params)
        >>> params["tax_rate"] = 0.20  # Mutation does not affect snapshot
        >>> snapshot["tax_rate"]
        0.15
    """
    if not isinstance(policy, dict):
        raise TypeError(
            f"policy must be a dictionary, got {type(policy).__name__}"
        )
    return deepcopy(policy)


def capture_unvalidated_template_warning(
    *,
    scenario_name: str = "",
    scenario_version: str = "",
    is_validated: bool | None = None,
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
    if is_validated is True:
        return None
    normalized_name = scenario_name.strip() or "unknown"
    normalized_version = scenario_version.strip() or "unknown"

    return (
        f"WARNING: Scenario '{normalized_name}' "
        f"(version '{normalized_version}') is not "
        "marked as validated in registry metadata. Action: Mark this scenario as "
        "validated before relying on outputs for production decisions."
    )


def capture_unvalidated_mapping_warning(
    *,
    source_file: str = "",
    is_validated: bool | None = None,
) -> str | None:
    """Generate warning if mapping configuration is not validated.

    Args:
        source_file: Path to the mapping configuration file.
        is_validated: Whether the mapping is marked as validated.

    Returns:
        Warning message string if not validated, None otherwise.
    """
    if is_validated is True:
        return None
    normalized_source = source_file.strip() or "unknown"
    return (
        f"WARNING: Mapping configuration '{normalized_source}' is not marked as "
        "validated. Action: Review mapping correctness before relying on outputs."
    )


# Constants for tested ranges
TESTED_MAX_HORIZON_YEARS = 20
TESTED_MAX_POPULATION_SIZE = 100_000


def capture_unsupported_config_warning(
    *,
    horizon_years: int | None = None,
    population_size: int | None = None,
) -> list[str]:
    """Generate warnings for run configurations outside tested ranges.

    Args:
        horizon_years: Number of years in the projection horizon.
        population_size: Number of households in the population.

    Returns:
        List of warning strings (empty if all within tested ranges).
    """
    warnings: list[str] = []

    if horizon_years is not None and horizon_years > TESTED_MAX_HORIZON_YEARS:
        warnings.append(
            f"WARNING: Projection horizon of {horizon_years} years exceeds tested "
            f"range (10-{TESTED_MAX_HORIZON_YEARS} years). Action: Results for years "
            "beyond tested range may have reduced credibility."
        )

    if population_size is not None and population_size > TESTED_MAX_POPULATION_SIZE:
        warnings.append(
            f"WARNING: Population size ({population_size:,} households) exceeds "
            f"standard test coverage ({TESTED_MAX_POPULATION_SIZE:,}). Action: "
            "Review memory usage and consider chunked processing."
        )

    return warnings


def capture_warnings(
    *,
    scenario_name: str = "",
    scenario_version: str = "",
    is_validated: bool | None = None,
    mapping_config: MappingConfig | None = None,
    additional_warnings: list[str] | None = None,
) -> list[str]:
    """Capture all warnings for manifest generation.

    Consolidates unvalidated template warnings and any additional warnings
    from execution.

    Args:
        scenario_name: Name of the scenario/template.
        scenario_version: Version identifier.
        is_validated: Whether the scenario is marked as validated.
        mapping_config: Optional mapping configuration to check validation status.
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

    # Emit template validation warning when:
    # - A scenario identity is present (name or version), OR
    # - is_validated is explicitly False (even without identity, uses "unknown").
    # When is_validated=None and no identity: skip (no scenario context to warn about).
    should_emit_validation_warning = bool(
        scenario_name.strip() or scenario_version.strip()
    )
    if is_validated is False:
        should_emit_validation_warning = True
    if should_emit_validation_warning:
        unvalidated_warning = capture_unvalidated_template_warning(
            scenario_name=scenario_name,
            scenario_version=scenario_version,
            is_validated=is_validated,
        )
        if unvalidated_warning:
            warnings.append(unvalidated_warning)

    # Add unvalidated mapping warning if applicable.
    if mapping_config is not None:
        mapping_warning = capture_unvalidated_mapping_warning(
            source_file=str(mapping_config.source_path or ""),
            is_validated=mapping_config.is_validated,
        )
        if mapping_warning:
            warnings.append(mapping_warning)

    # Add any additional warnings
    if additional_warnings:
        warnings.extend(
            warning.strip()
            for warning in additional_warnings
            if isinstance(warning, str) and warning.strip()
        )

    return warnings


def capture_discrete_choice_parameters(
    yearly_states: dict[int, Any],
) -> list[dict[str, Any]]:
    """Extract taste parameters per domain from decision log in yearly states.

    Scans yearly states for DECISION_LOG_KEY and extracts per-domain
    taste parameters, seed, and eligibility summary. Uses the first year
    containing a decision log (parameters are consistent across years).

    Story 14-6, AC-5.

    Args:
        yearly_states: Dict mapping year to YearState (or state-like objects
            with .data attribute).

    Returns:
        Sorted list of dicts with domain_name, alternative_ids, taste params,
        choice_seed, eligibility_summary per domain. Empty list if no
        discrete choice.
    """
    from reformlab.discrete_choice.decision_record import DECISION_LOG_KEY

    for year in sorted(yearly_states.keys()):
        state = yearly_states[year]
        data = state.data if hasattr(state, "data") else {}
        decision_log = data.get(DECISION_LOG_KEY)
        if not isinstance(decision_log, tuple) or not decision_log:
            continue

        entries: list[dict[str, Any]] = []
        for record in decision_log:
            entry: dict[str, Any] = {
                "domain_name": record.domain_name,
                "alternative_ids": list(record.alternative_ids),
            }
            entry.update(record.taste_parameters)
            if record.seed is not None:
                entry["choice_seed"] = record.seed
            if record.eligibility_summary is not None:
                entry["eligibility_summary"] = dict(record.eligibility_summary)
            entries.append(entry)

        return sorted(entries, key=lambda x: x.get("domain_name", ""))

    return []


def capture_technology_set(
    technology_set: TechnologySet | dict[str, Any] | None,
) -> dict[str, Any]:
    """Capture technology set configuration for manifest.

    Story 28.3 / AC-6: Serialize TechnologySet to manifest-compatible dict.

    Args:
        technology_set: TechnologySet with domain alternatives, dict representation,
            or None. Dict input is for backward compatibility with legacy code paths.

    Returns:
        Dict with domains, alternatives, reference IDs for reproducibility.
    """
    if technology_set is None:
        return {}

    # Handle dict-like and object types
    if hasattr(technology_set, "domains") and hasattr(technology_set, "version"):
        # TechnologySet object
        version = getattr(technology_set, "version", "")
        domains = getattr(technology_set, "domains", {})
    elif isinstance(technology_set, dict):
        # Dict representation
        version = technology_set.get("version", "")
        domains = technology_set.get("domains", {})
    else:
        return {}

    domains_dict: dict[str, Any] = {}
    for domain_name, domain_config in domains.items():
        # Handle both dict and DomainTechnologySet object
        if hasattr(domain_config, "alternatives"):
            # DomainTechnologySet object
            alternatives = getattr(domain_config, "alternatives", ())
            enabled = getattr(domain_config, "enabled", True)
            ref_id = getattr(domain_config, "reference_alternative_id", "")
        elif isinstance(domain_config, dict):
            # Dict representation
            alternatives = domain_config.get("alternatives", [])
            enabled = domain_config.get("enabled", True)
            ref_id = domain_config.get("reference_alternative_id", "")
        else:
            continue

        if not enabled:
            continue

        alternatives_list = []
        for alt in alternatives:
            # Handle both dict and Alternative object
            if hasattr(alt, "id"):
                # Alternative object
                alt_dict = {
                    "id": getattr(alt, "id", ""),
                    "name": getattr(alt, "name", ""),
                    "attributes": getattr(alt, "attributes", {}),
                }
            elif isinstance(alt, dict):
                # Dict representation
                alt_dict = {
                    "id": alt.get("id", ""),
                    "name": alt.get("name", ""),
                    "attributes": alt.get("attributes", {}),
                }
            else:
                continue
            alternatives_list.append(alt_dict)

        domains_dict[domain_name] = {
            "reference_alternative_id": ref_id,
            "alternatives": alternatives_list,
        }

    return {
        "version": version,
        "domains": domains_dict,
    }
