# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
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
    - 100,000 households (one person per household)
    - Deterministic income distribution (15,000 to 95,000 EUR)
    - Energy consumption columns for carbon tax computation
    - Fixed seed for reproducibility

    The population is generated at test runtime to avoid committing large
    binary artifacts to the repository.

    Returns:
        PyArrow Table with household_id, person_id, age, income, and
        energy consumption columns.
    """
    return generate_synthetic_population(size=100_000, seed=42)
