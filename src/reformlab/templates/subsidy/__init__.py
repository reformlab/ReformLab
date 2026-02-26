"""Subsidy computation module for ReformLab.

This module provides:
- Subsidy eligibility computation per household
- Subsidy amount computation based on income caps and eligible categories
- Income decile assignment
- Result dataclasses for typed outputs
- Batch execution and comparison utilities
"""

from reformlab.templates.subsidy.compare import (
    ComparisonResult,
    compare_subsidy_decile_impacts,
    run_subsidy_batch,
    subsidy_decile_results_to_table,
)
from reformlab.templates.subsidy.compute import (
    SubsidyDecileResults,
    SubsidyResult,
    aggregate_subsidy_by_decile,
    compute_subsidy,
    compute_subsidy_amount,
    compute_subsidy_eligibility,
)

__all__ = [
    # Result types
    "ComparisonResult",
    "SubsidyDecileResults",
    "SubsidyResult",
    # Computation functions
    "aggregate_subsidy_by_decile",
    "compare_subsidy_decile_impacts",
    "compute_subsidy",
    "compute_subsidy_amount",
    "compute_subsidy_eligibility",
    "run_subsidy_batch",
    "subsidy_decile_results_to_table",
]
