"""Indicator computation module for ReformLab.

Story 4.1: Implement Distributional Indicators by Income Decile

This module provides functions and types for computing indicators from
orchestrator panel outputs, including distributional analysis by income decile.

Main API:
    - compute_distributional_indicators: Compute decile-based indicators
    - DistributionalConfig: Configuration for distributional computation
    - IndicatorResult: Container for indicator results with metadata
    - DecileIndicators: Single decile indicator metrics
"""

from reformlab.indicators.distributional import compute_distributional_indicators
from reformlab.indicators.types import (
    DecileIndicators,
    DistributionalConfig,
    IndicatorResult,
)

__all__ = [
    "compute_distributional_indicators",
    "DistributionalConfig",
    "IndicatorResult",
    "DecileIndicators",
]
