"""Vehicle malus computation module for ReformLab.

This module provides:
- Vehicle malus (emission penalty) computation
- Year-indexed schedules for both rate and threshold
- Income decile assignment for distributional analysis
- Result dataclasses for typed outputs
- Batch execution and comparison utilities

Story 13.2 — Models the French malus ecologique using a simplified linear
rate approach appropriate for population-level microsimulation.
"""

from reformlab.templates.schema import register_custom_template, register_policy_type
from reformlab.templates.vehicle_malus.compare import (
    ComparisonResult,
    compare_vehicle_malus_decile_impacts,
    run_vehicle_malus_batch,
    vehicle_malus_decile_results_to_table,
)
from reformlab.templates.vehicle_malus.compute import (
    VehicleMalusDecileResults,
    VehicleMalusParameters,
    VehicleMalusResult,
    aggregate_vehicle_malus_by_decile,
    compute_vehicle_malus,
)

# Register vehicle_malus as a custom policy type at import time.
# This is a "built-in custom" type shipped with the package.
_vehicle_malus_type = register_policy_type("vehicle_malus")
register_custom_template(_vehicle_malus_type, VehicleMalusParameters)

__all__ = [
    # Result types
    "ComparisonResult",
    "VehicleMalusDecileResults",
    "VehicleMalusParameters",
    "VehicleMalusResult",
    # Computation functions
    "aggregate_vehicle_malus_by_decile",
    "compare_vehicle_malus_decile_impacts",
    "compute_vehicle_malus",
    "run_vehicle_malus_batch",
    "vehicle_malus_decile_results_to_table",
]
