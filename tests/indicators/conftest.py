"""Test fixtures for indicator tests.

Story 4.1: Implement Distributional Indicators by Income Decile
Story 12.5: Implement Multi-Portfolio Comparison and Notebook Demo
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.orchestrator.panel import PanelOutput


@pytest.fixture
def simple_income_distribution_panel() -> PanelOutput:
    """Create a simple panel with 100 households and known income distribution.

    Income ranges from 10k to 100k in 1k increments, creating a uniform
    distribution suitable for testing decile boundaries.
    """
    num_households = 100
    household_ids = list(range(num_households))
    incomes = [10000.0 + i * 1000.0 for i in range(num_households)]
    taxes = [1000.0 + i * 100.0 for i in range(num_households)]
    years = [2020] * num_households

    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "year": pa.array(years, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "tax": pa.array(taxes, type=pa.float64()),
        }
    )

    metadata = {
        "start_year": 2020,
        "end_year": 2020,
        "seed": 42,
    }

    return PanelOutput(table=table, metadata=metadata)


@pytest.fixture
def multi_year_panel() -> PanelOutput:
    """Create a multi-year panel with 3 years and 30 households per year.

    Total 90 rows (30 households × 3 years).
    """
    num_households = 30
    years = [2020, 2021, 2022]

    household_ids = []
    year_col = []
    incomes = []
    taxes = []

    for year in years:
        for hh_id in range(num_households):
            household_ids.append(hh_id)
            year_col.append(year)
            # Income increases slightly each year
            base_income = 20000.0 + hh_id * 2000.0
            year_adjustment = (year - 2020) * 1000.0
            incomes.append(base_income + year_adjustment)
            taxes.append(base_income * 0.1)

    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "year": pa.array(year_col, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "tax": pa.array(taxes, type=pa.float64()),
        }
    )

    metadata = {
        "start_year": 2020,
        "end_year": 2022,
        "seed": 42,
    }

    return PanelOutput(table=table, metadata=metadata)


@pytest.fixture
def panel_with_missing_income() -> PanelOutput:
    """Create a panel where 20% of households have null income."""
    num_households = 50
    household_ids = list(range(num_households))

    # Every 5th household has null income
    incomes = []
    for i in range(num_households):
        if i % 5 == 0:
            incomes.append(None)
        else:
            incomes.append(30000.0 + i * 1000.0)

    taxes = [3000.0 + i * 100.0 for i in range(num_households)]
    years = [2020] * num_households

    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "year": pa.array(years, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "tax": pa.array(taxes, type=pa.float64()),
        }
    )

    metadata = {
        "start_year": 2020,
        "end_year": 2020,
        "seed": 42,
    }

    return PanelOutput(table=table, metadata=metadata)


@pytest.fixture
def portfolio_panels() -> dict[str, PanelOutput]:
    """Create 3 PanelOutput objects simulating different portfolio outcomes.

    Story 12.5: Portfolio comparison test fixture.

    Portfolio A ("Carbon Tax Light"): carbon_tax=500 per household
    Portfolio B ("Carbon Tax + Subsidy"): carbon_tax=500, subsidy_amount=200
    Portfolio C ("Green Transition"): carbon_tax=800, subsidy_amount=300

    Each panel: 30 households x 3 years (2025-2027).
    """
    num_households = 30
    years = [2025, 2026, 2027]
    panels: dict[str, PanelOutput] = {}

    for portfolio_label, carbon_tax, subsidy in [
        ("Carbon Tax Light", 500.0, 0.0),
        ("Carbon Tax + Subsidy", 500.0, 200.0),
        ("Green Transition", 800.0, 300.0),
    ]:
        household_ids: list[int] = []
        year_col: list[int] = []
        incomes: list[float] = []
        carbon_taxes: list[float] = []
        subsidy_amounts: list[float] = []

        for year in years:
            for hh_id in range(num_households):
                household_ids.append(hh_id)
                year_col.append(year)
                base_income = 20000.0 + hh_id * 2000.0
                year_adj = (year - 2025) * 500.0
                incomes.append(base_income + year_adj)
                carbon_taxes.append(carbon_tax + hh_id * 10.0)
                subsidy_amounts.append(subsidy + hh_id * 5.0)

        table = pa.table(
            {
                "household_id": pa.array(household_ids, type=pa.int64()),
                "year": pa.array(year_col, type=pa.int64()),
                "income": pa.array(incomes, type=pa.float64()),
                "carbon_tax": pa.array(carbon_taxes, type=pa.float64()),
                "subsidy_amount": pa.array(subsidy_amounts, type=pa.float64()),
            }
        )

        panels[portfolio_label] = PanelOutput(
            table=table,
            metadata={"start_year": 2025, "end_year": 2027, "seed": 42},
        )

    return panels


@pytest.fixture
def empty_panel() -> PanelOutput:
    """Create an empty panel with no households."""
    table = pa.table(
        {
            "household_id": pa.array([], type=pa.int64()),
            "year": pa.array([], type=pa.int64()),
            "income": pa.array([], type=pa.float64()),
            "tax": pa.array([], type=pa.float64()),
        }
    )

    metadata = {
        "start_year": 2020,
        "end_year": 2020,
        "seed": 42,
    }

    return PanelOutput(table=table, metadata=metadata)
