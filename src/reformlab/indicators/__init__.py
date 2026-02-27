"""Indicator computation module for ReformLab.

Story 4.1: Implement Distributional Indicators by Income Decile
Story 4.2: Implement Geographic Aggregation Indicators
Story 4.3: Implement Welfare Indicators
Story 4.4: Implement Fiscal Indicators

This module provides functions and types for computing indicators from
orchestrator panel outputs, including distributional analysis by income decile,
geographic aggregation by region, welfare comparison between scenarios,
and fiscal budgetary analysis.

Main API:
    - compute_distributional_indicators: Compute decile-based indicators
    - compute_geographic_indicators: Compute region-based indicators
    - compute_welfare_indicators: Compute welfare indicators (baseline vs reform)
    - compute_fiscal_indicators: Compute fiscal indicators (revenue, cost, balance)
    - DistributionalConfig: Configuration for distributional computation
    - GeographicConfig: Configuration for geographic computation
    - WelfareConfig: Configuration for welfare computation
    - FiscalConfig: Configuration for fiscal computation
    - IndicatorResult: Container for indicator results with metadata
    - DecileIndicators: Single decile indicator metrics
    - RegionIndicators: Single region indicator metrics
    - WelfareIndicators: Welfare indicator metrics (winner/loser analysis)
    - FiscalIndicators: Fiscal indicator metrics (revenue, cost, balance)
"""

from reformlab.indicators.distributional import compute_distributional_indicators
from reformlab.indicators.fiscal import compute_fiscal_indicators
from reformlab.indicators.geographic import compute_geographic_indicators
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
    "DistributionalConfig",
    "GeographicConfig",
    "WelfareConfig",
    "FiscalConfig",
    "IndicatorResult",
    "DecileIndicators",
    "RegionIndicators",
    "WelfareIndicators",
    "FiscalIndicators",
]
