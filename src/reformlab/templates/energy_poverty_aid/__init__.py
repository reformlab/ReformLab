"""Energy poverty aid computation module for ReformLab.

This module provides:
- Energy poverty aid computation for low-income, energy-burdened households
- Year-indexed schedules for income ceiling, energy share threshold, and base aid
- Income decile assignment for distributional analysis
- Result dataclasses for typed outputs
- Batch execution and comparison utilities

Story 13.3 — Models the French cheque energie using a simplified linear
model appropriate for population-level microsimulation.
"""

from __future__ import annotations

from reformlab.templates.energy_poverty_aid.compare import (
    ComparisonResult,
    compare_energy_poverty_aid_decile_impacts,
    energy_poverty_aid_decile_results_to_table,
    run_energy_poverty_aid_batch,
)
from reformlab.templates.energy_poverty_aid.compute import (
    EnergyPovertyAidDecileResults,
    EnergyPovertyAidParameters,
    EnergyPovertyAidResult,
    aggregate_energy_poverty_aid_by_decile,
    compute_energy_poverty_aid,
)
from reformlab.templates.schema import (
    _CUSTOM_PARAMETERS_TO_POLICY_TYPE,
    _CUSTOM_POLICY_TYPES,
    register_custom_template,
    register_policy_type,
)

# Register energy_poverty_aid as a custom policy type at import time.
# This is a "built-in custom" type shipped with the package.
# Idempotent: skip registration if already registered (e.g. module reload).
if "energy_poverty_aid" not in _CUSTOM_POLICY_TYPES:
    _energy_poverty_aid_type = register_policy_type("energy_poverty_aid")
    register_custom_template(_energy_poverty_aid_type, EnergyPovertyAidParameters)
elif EnergyPovertyAidParameters not in _CUSTOM_PARAMETERS_TO_POLICY_TYPE:
    register_custom_template(
        _CUSTOM_POLICY_TYPES["energy_poverty_aid"], EnergyPovertyAidParameters
    )

__all__ = [
    # Result types
    "ComparisonResult",
    "EnergyPovertyAidDecileResults",
    "EnergyPovertyAidParameters",
    "EnergyPovertyAidResult",
    # Computation functions
    "aggregate_energy_poverty_aid_by_decile",
    "compare_energy_poverty_aid_decile_impacts",
    "compute_energy_poverty_aid",
    "energy_poverty_aid_decile_results_to_table",
    "run_energy_poverty_aid_batch",
]
