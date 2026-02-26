"""Carbon tax computation module for ReformLab.

This module provides:
- Tax burden computation per household
- Redistribution computation (lump sum and progressive)
- Income decile assignment
- Result dataclasses for typed outputs
- Batch execution and comparison utilities
"""

from reformlab.templates.carbon_tax.compare import (
    ComparisonResult,
    compare_decile_impacts,
    decile_results_to_table,
    run_carbon_tax_batch,
)
from reformlab.templates.carbon_tax.compute import (
    CarbonTaxResult,
    DecileResults,
    aggregate_by_decile,
    assign_income_deciles,
    compute_carbon_tax,
    compute_lump_sum_redistribution,
    compute_progressive_redistribution,
    compute_tax_burden,
    get_exemption_rate,
)

__all__ = [
    # Result types
    "CarbonTaxResult",
    "ComparisonResult",
    "DecileResults",
    # Computation functions
    "aggregate_by_decile",
    "assign_income_deciles",
    "compare_decile_impacts",
    "compute_carbon_tax",
    "compute_lump_sum_redistribution",
    "compute_progressive_redistribution",
    "compute_tax_burden",
    "decile_results_to_table",
    "get_exemption_rate",
    "run_carbon_tax_batch",
]
