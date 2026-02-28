"""Pytest fixtures for benchmark tests.

Provides deterministic 100k household population for benchmarking.
Delegates to ``reformlab.data.synthetic`` for generation (Story 8.2).
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.data.synthetic import generate_synthetic_population


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
    return generate_synthetic_population(size=100_000, seed=42)
