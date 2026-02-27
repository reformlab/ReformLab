"""Vintage subsystem for cohort-based asset tracking.

This module provides vintage (cohort) state management for tracking
asset classes (e.g., vehicles) through time in multi-year simulations.

Public API:
- VintageCohort: Single age cohort with count and attributes
- VintageState: Collection of cohorts for an asset class
- VintageSummary: Derived metrics for downstream consumers
- VintageConfig: Configuration for vintage transition step
- VintageTransitionRule: Configuration for transition behavior
- VintageTransitionStep: OrchestratorStep for vintage transitions
- VintageConfigError: Invalid configuration error
- VintageTransitionError: Execution error

MVP scope: vehicle asset class. Extension points exist for future classes.
"""

from reformlab.vintage.config import VintageConfig, VintageTransitionRule
from reformlab.vintage.errors import VintageConfigError, VintageTransitionError
from reformlab.vintage.transition import VintageTransitionStep
from reformlab.vintage.types import VintageCohort, VintageState, VintageSummary

__all__ = [
    "VintageCohort",
    "VintageConfig",
    "VintageConfigError",
    "VintageState",
    "VintageSummary",
    "VintageTransitionError",
    "VintageTransitionRule",
    "VintageTransitionStep",
]
