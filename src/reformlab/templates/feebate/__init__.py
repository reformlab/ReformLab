# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Feebate computation module for ReformLab.

This module provides:
- Feebate computation with pivot point logic
- Fee calculation for households above pivot
- Rebate calculation for households below pivot
- Income decile assignment for distributional analysis
- Result dataclasses for typed outputs
- Batch execution and comparison utilities
"""

from reformlab.templates.feebate.compare import (
    ComparisonResult,
    compare_feebate_decile_impacts,
    feebate_decile_results_to_table,
    run_feebate_batch,
)
from reformlab.templates.feebate.compute import (
    FeebateDecileResults,
    FeebateResult,
    aggregate_feebate_by_decile,
    compute_fee_amount,
    compute_feebate,
    compute_rebate_amount,
)

__all__ = [
    # Result types
    "ComparisonResult",
    "FeebateDecileResults",
    "FeebateResult",
    # Computation functions
    "aggregate_feebate_by_decile",
    "compare_feebate_decile_impacts",
    "compute_feebate",
    "compute_fee_amount",
    "compute_rebate_amount",
    "feebate_decile_results_to_table",
    "run_feebate_batch",
]
