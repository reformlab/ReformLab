"""Fixtures for portfolio tests.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reformlab.templates.schema import (
    CarbonTaxParameters,
    SubsidyParameters,
    YearSchedule,
)


@pytest.fixture
def carbon_tax_params() -> CarbonTaxParameters:
    """Sample carbon tax parameters."""
    return CarbonTaxParameters(
        rate_schedule={
            2026: 44.60,
            2027: 50.00,
            2028: 55.00,
        },
        redistribution_type="lump_sum",
    )


@pytest.fixture
def subsidy_params() -> SubsidyParameters:
    """Sample subsidy parameters."""
    return SubsidyParameters(
        rate_schedule={
            2026: 5000.0,
            2027: 5000.0,
        },
        eligible_categories=("electric_vehicle",),
    )


@pytest.fixture
def year_schedule() -> YearSchedule:
    """Sample year schedule."""
    return YearSchedule(start_year=2026, end_year=2035)


@pytest.fixture
def temp_portfolio_dir(tmp_path: Path) -> Path:
    """Temporary directory for portfolio YAML files."""
    portfolio_dir = tmp_path / "portfolios"
    portfolio_dir.mkdir(exist_ok=True)
    return portfolio_dir
