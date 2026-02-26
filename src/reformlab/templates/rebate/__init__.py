"""Rebate computation module for ReformLab.

This module provides:
- Rebate computation per household (lump sum and progressive)
- Income decile assignment for progressive distribution
- Result dataclasses for typed outputs
- Batch execution and comparison utilities
"""

from reformlab.templates.rebate.compare import (
    ComparisonResult,
    compare_rebate_decile_impacts,
    rebate_decile_results_to_table,
    run_rebate_batch,
)
from reformlab.templates.rebate.compute import (
    RebateDecileResults,
    RebateResult,
    aggregate_rebate_by_decile,
    compute_lump_sum_rebate,
    compute_progressive_rebate,
    compute_rebate,
)

__all__ = [
    # Result types
    "ComparisonResult",
    "RebateDecileResults",
    "RebateResult",
    # Computation functions
    "aggregate_rebate_by_decile",
    "compare_rebate_decile_impacts",
    "compute_lump_sum_rebate",
    "compute_progressive_rebate",
    "compute_rebate",
    "rebate_decile_results_to_table",
    "run_rebate_batch",
]
