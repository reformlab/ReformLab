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

    Uses seeded random generation identical to tests/benchmarks/conftest.py
    so that benchmark reference values remain valid.

    The generation algorithm:
    - Household IDs: 0 to size-1
    - Income: base (15k-95k linear ramp) with ±10% random variation,
      seeded per-household as ``seed + i``
    - Emissions: 2-12 tCO2/year correlated with income, ±15% variation,
      seeded as ``seed + size + i``

    Args:
        size: Number of households to generate.
        seed: Base random seed for reproducibility.

    Returns:
        PyArrow Table with household_id, income, and carbon_emissions columns.
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

    # Generate carbon emissions (2.0 to 12.0 tCO2/year, correlated with income)
    emissions: list[float] = []
    for i, income in enumerate(incomes):
        random.seed(seed + size + i)
        base_emissions = 2.0
        emissions_range = 10.0
        emissions_val = base_emissions + (income - 15_000) / 80_000 * emissions_range
        variation = random.uniform(-0.15, 0.15)
        emissions_val = emissions_val * (1 + variation)
        emissions.append(max(0.0, emissions_val))

    return pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "carbon_emissions": pa.array(emissions, type=pa.float64()),
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
