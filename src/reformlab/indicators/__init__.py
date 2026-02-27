"""Indicator computation module for ReformLab.

Story 4.1: Implement Distributional Indicators by Income Decile
Story 4.2: Implement Geographic Aggregation Indicators

This module provides functions and types for computing indicators from
orchestrator panel outputs, including distributional analysis by income decile
and geographic aggregation by region.

Main API:
    - compute_distributional_indicators: Compute decile-based indicators
    - compute_geographic_indicators: Compute region-based indicators
    - DistributionalConfig: Configuration for distributional computation
    - GeographicConfig: Configuration for geographic computation
    - IndicatorResult: Container for indicator results with metadata
    - DecileIndicators: Single decile indicator metrics
    - RegionIndicators: Single region indicator metrics
"""

from reformlab.indicators.distributional import compute_distributional_indicators
from reformlab.indicators.geographic import compute_geographic_indicators
from reformlab.indicators.types import (
    DecileIndicators,
    DistributionalConfig,
    GeographicConfig,
    IndicatorResult,
    RegionIndicators,
)

__all__ = [
    "compute_distributional_indicators",
    "compute_geographic_indicators",
    "DistributionalConfig",
    "GeographicConfig",
    "IndicatorResult",
    "DecileIndicators",
    "RegionIndicators",
]
