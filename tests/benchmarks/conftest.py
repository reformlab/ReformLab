"""Pytest fixtures for benchmark tests.

Provides deterministic 100k household population for benchmarking.
"""

from __future__ import annotations

import pyarrow as pa
import pytest


@pytest.fixture
def benchmark_population() -> pa.Table:
    """Generate deterministic 100k household population for benchmarks.

    This fixture creates a synthetic population table with:
    - 100,000 households
    - Deterministic income distribution (15,000 to 95,000 EUR)
    - Deterministic carbon emissions (2.0 to 12.0 tCO2/year)
    - Fixed seed for reproducibility

    The population is generated at test runtime to avoid committing large
    binary artifacts to the repository.

    Returns:
        PyArrow Table with household_id, income, and carbon_emissions columns.
    """
    import random

    # Fixed seed for reproducibility
    SEED = 42
    HOUSEHOLD_COUNT = 100_000

    random.seed(SEED)

    # Generate household IDs
    household_ids = list(range(HOUSEHOLD_COUNT))

    # Generate income distribution (15k to 95k EUR, roughly log-normal)
    # Use deterministic method: combine base + random component
    incomes = []
    for i in range(HOUSEHOLD_COUNT):
        # Seeded random value for this household
        random.seed(SEED + i)
        base_income = 15_000.0
        income_range = 80_000.0
        # Generate income with some variation
        income = base_income + (i / HOUSEHOLD_COUNT) * income_range
        # Add small random variation (±10%)
        variation = random.uniform(-0.1, 0.1)
        income = income * (1 + variation)
        incomes.append(income)

    # Generate carbon emissions (2.0 to 12.0 tCO2/year, correlated with income)
    emissions = []
    for i, income in enumerate(incomes):
        # Higher income -> higher emissions (roughly)
        random.seed(SEED + HOUSEHOLD_COUNT + i)
        base_emissions = 2.0
        emissions_range = 10.0
        # Emissions roughly proportional to income decile
        emissions_val = base_emissions + (income - 15_000) / 80_000 * emissions_range
        # Add small random variation (±15%)
        variation = random.uniform(-0.15, 0.15)
        emissions_val = emissions_val * (1 + variation)
        emissions.append(max(0.0, emissions_val))

    # Build PyArrow table
    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "carbon_emissions": pa.array(emissions, type=pa.float64()),
        }
    )

    return table
