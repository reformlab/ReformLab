# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Synthetic population generation for benchmarking and scale validation.

Story 8.2: Generate 100k-Household Synthetic Population

This module extracts the deterministic population generation logic from
tests/benchmarks/conftest.py into a reusable module. The generator produces
bit-identical output for the same (size, seed) pair, preserving benchmark
reference value validity (BKL-701).
"""

from __future__ import annotations

import random
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from reformlab.data.pipeline import DatasetManifest, DataSourceMetadata, hash_file

SEED = 42
DEFAULT_SIZE = 100_000


# ============================================================================
# Population generation
# ============================================================================


def generate_synthetic_population(
    size: int = DEFAULT_SIZE,
    seed: int = SEED,
) -> pa.Table:
    """Generate deterministic synthetic population for benchmarking.

    Produces a single-person-per-household population with energy consumption
    columns suitable for carbon tax computation.

    The generation algorithm:
    - Household/person IDs: 0 to size-1 (one person per household)
    - Age: uniform 20-80, seeded as ``seed + 3 * size + i``
    - Income: base (15k-95k linear ramp) with ±10% random variation,
      seeded per-household as ``seed + i``
    - Transport fuel: 500-1500 L/year, income-correlated, seeded ``seed + size + i``
    - Heating fuel: 200-800 L/year, weakly income-correlated, seeded ``seed + 2*size + i``
    - Natural gas: 300-1200 m³/year, weakly income-correlated, seeded ``seed + 3*size + i``

    Args:
        size: Number of households to generate.
        seed: Base random seed for reproducibility.

    Returns:
        PyArrow Table with household_id, person_id, age, income, and
        energy consumption columns.
    """
    if size < 0:
        raise ValueError(f"size must be >= 0, got {size!r}")

    household_ids = list(range(size))

    # Generate income distribution (15k to 95k EUR)
    incomes: list[float] = []
    for i in range(size):
        random.seed(seed + i)
        base_income = 15_000.0
        income_range = 80_000.0
        income = base_income + (i / size) * income_range
        variation = random.uniform(-0.1, 0.1)
        income = income * (1 + variation)
        incomes.append(income)

    # Income fraction (0-1) for correlation
    def _income_frac(inc: float) -> float:
        return max(0.0, min(1.0, (inc - 15_000) / 80_000))

    # Transport fuel: 500-1500 L/year (strong income correlation)
    transport_fuel: list[float] = []
    for i, inc in enumerate(incomes):
        random.seed(seed + size + i)
        base = 500.0 + _income_frac(inc) * 1000.0
        variation = random.uniform(-0.15, 0.15)
        transport_fuel.append(max(0.0, base * (1 + variation)))

    # Heating fuel: 200-800 L/year (weak income correlation)
    heating_fuel: list[float] = []
    for i, inc in enumerate(incomes):
        random.seed(seed + 2 * size + i)
        base = 200.0 + _income_frac(inc) * 300.0 + random.uniform(0, 300)
        variation = random.uniform(-0.10, 0.10)
        heating_fuel.append(max(0.0, base * (1 + variation)))

    # Natural gas: 300-1200 m³/year (weak income correlation)
    natural_gas: list[float] = []
    for i, inc in enumerate(incomes):
        random.seed(seed + 3 * size + i)
        base = 300.0 + _income_frac(inc) * 400.0 + random.uniform(0, 500)
        variation = random.uniform(-0.10, 0.10)
        natural_gas.append(max(0.0, base * (1 + variation)))

    # Age: uniform 20-80
    ages: list[int] = []
    for i in range(size):
        random.seed(seed + 4 * size + i)
        ages.append(random.randint(20, 80))

    return pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "person_id": pa.array(household_ids, type=pa.int64()),
            "age": pa.array(ages, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "energy_transport_fuel": pa.array(transport_fuel, type=pa.float64()),
            "energy_heating_fuel": pa.array(heating_fuel, type=pa.float64()),
            "energy_natural_gas": pa.array(natural_gas, type=pa.float64()),
        }
    )


# ============================================================================
# Persistent save with provenance
# ============================================================================


def save_synthetic_population(
    table: pa.Table,
    path: Path,
    source: DataSourceMetadata | None = None,
    *,
    seed: int | None = None,
) -> DatasetManifest:
    """Save population to Parquet with provenance manifest.

    Args:
        table: PyArrow table to persist.
        path: Output Parquet file path.
        source: Optional metadata describing the data origin.
        seed: Seed used for generation (included in default source metadata).

    Returns:
        DatasetManifest with SHA-256 hash and provenance metadata.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)

    if source is None:
        seed_info = f", seed={seed}" if seed is not None else ""
        source = DataSourceMetadata(
            name="synthetic-population",
            version="1.0.0",
            url="",
            description=f"Deterministic synthetic population ({len(table)} households{seed_info})",
            license="internal",
        )

    content_hash = hash_file(path)

    return DatasetManifest(
        source=source,
        content_hash=content_hash,
        file_path=path,
        format="parquet",
        row_count=len(table),
        column_names=tuple(table.schema.names),
        loaded_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )
