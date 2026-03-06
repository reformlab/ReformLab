"""Indicator computation module for ReformLab.

Story 4.1: Implement Distributional Indicators by Income Decile
Story 4.2: Implement Geographic Aggregation Indicators
Story 4.3: Implement Welfare Indicators
Story 4.4: Implement Fiscal Indicators
Story 4.5: Implement Scenario Comparison Tables
Story 4.6: Implement Custom Derived Indicator Formulas
Story 12.5: Implement Multi-Portfolio Comparison and Notebook Demo

This module provides functions and types for computing indicators from
orchestrator panel outputs, including distributional analysis by income decile,
geographic aggregation by region, welfare comparison between scenarios,
fiscal budgetary analysis, multi-scenario comparison with delta computation,
custom derived indicator formulas, and multi-portfolio comparison.

Main API:
    - compute_distributional_indicators: Compute decile-based indicators
    - compute_geographic_indicators: Compute region-based indicators
    - compute_welfare_indicators: Compute welfare indicators (baseline vs reform)
    - compute_fiscal_indicators: Compute fiscal indicators (revenue, cost, balance)
    - compare_scenarios: Compare indicators across multiple scenarios
    - compare_portfolios: Compare indicators across multiple policy portfolios
    - apply_custom_formula: Apply custom formula to indicator results
    - apply_custom_formulas: Apply multiple custom formulas in sequence
    - DistributionalConfig: Configuration for distributional computation
    - GeographicConfig: Configuration for geographic computation
    - WelfareConfig: Configuration for welfare computation
    - FiscalConfig: Configuration for fiscal computation
    - ComparisonConfig: Configuration for scenario comparison
    - PortfolioComparisonConfig: Configuration for portfolio comparison
    - CustomFormulaConfig: Configuration for custom derived formulas
    - IndicatorResult: Container for indicator results with metadata
    - ComparisonResult: Container for scenario comparison results
    - PortfolioComparisonResult: Container for portfolio comparison results
    - ScenarioInput: Wrapper for scenario label and indicators
    - PortfolioComparisonInput: Wrapper for portfolio label and panel output
    - CrossComparisonMetric: Aggregate metric ranking portfolios
    - DecileIndicators: Single decile indicator metrics
    - RegionIndicators: Single region indicator metrics
    - WelfareIndicators: Welfare indicator metrics (winner/loser analysis)
    - FiscalIndicators: Fiscal indicator metrics (revenue, cost, balance)
    - FormulaValidationError: Exception for invalid formula syntax or references
"""

from reformlab.indicators.comparison import (
    ComparisonConfig,
    ComparisonResult,
    ScenarioInput,
    compare_scenarios,
)
from reformlab.indicators.custom import (
    CustomFormulaConfig,
    FormulaValidationError,
    apply_custom_formula,
    apply_custom_formulas,
)
from reformlab.indicators.distributional import compute_distributional_indicators
from reformlab.indicators.fiscal import compute_fiscal_indicators
from reformlab.indicators.geographic import compute_geographic_indicators
from reformlab.indicators.portfolio_comparison import (
    CrossComparisonMetric,
    PortfolioComparisonConfig,
    PortfolioComparisonInput,
    PortfolioComparisonResult,
    compare_portfolios,
)
from reformlab.indicators.types import (
    DecileIndicators,
    DistributionalConfig,
    FiscalConfig,
    FiscalIndicators,
    GeographicConfig,
    IndicatorResult,
    RegionIndicators,
    WelfareConfig,
    WelfareIndicators,
)
from reformlab.indicators.welfare import compute_welfare_indicators

__all__ = [
    "compute_distributional_indicators",
    "compute_geographic_indicators",
    "compute_welfare_indicators",
    "compute_fiscal_indicators",
    "compare_scenarios",
    "apply_custom_formula",
    "apply_custom_formulas",
    "DistributionalConfig",
    "GeographicConfig",
    "WelfareConfig",
    "FiscalConfig",
    "ComparisonConfig",
    "CustomFormulaConfig",
    "IndicatorResult",
    "ComparisonResult",
    "ScenarioInput",
    "DecileIndicators",
    "RegionIndicators",
    "WelfareIndicators",
    "FiscalIndicators",
    "FormulaValidationError",
    "compare_portfolios",
    "PortfolioComparisonInput",
    "PortfolioComparisonConfig",
    "PortfolioComparisonResult",
    "CrossComparisonMetric",
]
