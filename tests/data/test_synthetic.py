# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for synthetic population generation.

Story 8.2 — Task 1: Validates that the reusable synthetic population generator
produces deterministic, bit-identical output matching the original
tests/benchmarks/conftest.py fixture.
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from reformlab.data.synthetic import (
    DEFAULT_SIZE,
    generate_synthetic_population,
    save_synthetic_population,
)

EXPECTED_COLUMNS = [
    "household_id",
    "person_id",
    "age",
    "income",
    "energy_transport_fuel",
    "energy_heating_fuel",
    "energy_natural_gas",
]


class TestGenerateSyntheticPopulation:
    """AC-1: Deterministic synthetic population generation."""

    def test_default_size_and_seed(self) -> None:
        """Default invocation produces 100k-row table with expected columns."""
        table = generate_synthetic_population()
        assert table.num_rows == DEFAULT_SIZE
        assert table.schema.names == EXPECTED_COLUMNS

    def test_column_types(self) -> None:
        """Columns have correct Arrow types."""
        table = generate_synthetic_population(size=10, seed=0)
        assert table.schema.field("household_id").type == pa.int64()
        assert table.schema.field("person_id").type == pa.int64()
        assert table.schema.field("age").type == pa.int64()
        assert table.schema.field("income").type == pa.float64()
        assert table.schema.field("energy_transport_fuel").type == pa.float64()
        assert table.schema.field("energy_heating_fuel").type == pa.float64()
        assert table.schema.field("energy_natural_gas").type == pa.float64()

    def test_deterministic_same_seed(self) -> None:
        """Same (size, seed) produces identical output."""
        t1 = generate_synthetic_population(size=500, seed=99)
        t2 = generate_synthetic_population(size=500, seed=99)
        assert t1.equals(t2)

    def test_different_seed_differs(self) -> None:
        """Different seeds produce different output."""
        t1 = generate_synthetic_population(size=500, seed=1)
        t2 = generate_synthetic_population(size=500, seed=2)
        assert not t1.equals(t2)

    def test_household_ids_start_at_zero(self) -> None:
        """Household IDs are 0-based consecutive integers."""
        table = generate_synthetic_population(size=100, seed=42)
        ids = table.column("household_id").to_pylist()
        assert ids == list(range(100))

    def test_person_id_equals_household_id(self) -> None:
        """Single-person simplification: person_id == household_id."""
        table = generate_synthetic_population(size=100, seed=42)
        assert table.column("person_id").to_pylist() == table.column("household_id").to_pylist()

    def test_age_range(self) -> None:
        """Ages are between 20 and 80."""
        table = generate_synthetic_population(size=1000, seed=42)
        ages = table.column("age").to_pylist()
        assert all(20 <= a <= 80 for a in ages)

    def test_income_range(self) -> None:
        """Incomes are positive and in a reasonable range."""
        table = generate_synthetic_population(size=1000, seed=42)
        incomes = table.column("income").to_pylist()
        assert all(i > 0 for i in incomes)
        assert min(incomes) > 10_000
        assert max(incomes) < 120_000

    def test_energy_columns_non_negative(self) -> None:
        """All energy consumption values are non-negative."""
        table = generate_synthetic_population(size=1000, seed=42)
        for col in ("energy_transport_fuel", "energy_heating_fuel", "energy_natural_gas"):
            values = table.column(col).to_pylist()
            assert all(v >= 0 for v in values), f"{col} has negative values"

    def test_energy_columns_non_zero(self) -> None:
        """Energy columns produce non-zero values for non-empty populations."""
        table = generate_synthetic_population(size=1000, seed=42)
        for col in ("energy_transport_fuel", "energy_heating_fuel", "energy_natural_gas"):
            values = table.column(col).to_pylist()
            assert sum(values) > 0, f"{col} is all zeros"

    def test_transport_fuel_income_correlated(self) -> None:
        """Higher income households tend to have higher transport fuel consumption."""
        table = generate_synthetic_population(size=1000, seed=42)
        incomes = table.column("income").to_pylist()
        fuel = table.column("energy_transport_fuel").to_pylist()
        # Compare mean of bottom and top quartile
        n = len(incomes)
        pairs = sorted(zip(incomes, fuel))
        bottom_mean = sum(f for _, f in pairs[: n // 4]) / (n // 4)
        top_mean = sum(f for _, f in pairs[3 * n // 4 :]) / (n // 4)
        assert top_mean > bottom_mean

    def test_empty_population(self) -> None:
        """size=0 produces empty table with correct schema."""
        table = generate_synthetic_population(size=0, seed=42)
        assert table.num_rows == 0
        assert table.schema.names == EXPECTED_COLUMNS

    def test_negative_size_raises(self) -> None:
        """Negative size raises ValueError."""
        with pytest.raises(ValueError, match="size must be >= 0"):
            generate_synthetic_population(size=-1)

    def test_no_carbon_emissions_column(self) -> None:
        """The dead carbon_emissions column has been removed."""
        table = generate_synthetic_population(size=10, seed=42)
        assert "carbon_emissions" not in table.schema.names


class TestSaveSyntheticPopulation:
    """AC-1: Persistent Parquet output with DatasetManifest provenance."""

    def test_save_creates_parquet(self, tmp_path: Path) -> None:
        """Saves Parquet file and returns manifest with SHA-256 hash."""
        table = generate_synthetic_population(size=100, seed=42)
        out = tmp_path / "pop.parquet"
        manifest = save_synthetic_population(table, out)

        assert out.exists()
        assert manifest.row_count == 100
        assert manifest.format == "parquet"
        assert manifest.content_hash  # non-empty SHA-256
        assert len(manifest.content_hash) == 64  # SHA-256 hex digest
        assert manifest.column_names == tuple(EXPECTED_COLUMNS)
        assert manifest.source.name == "synthetic-population"

    def test_save_round_trip(self, tmp_path: Path) -> None:
        """Saved Parquet can be loaded back and equals original table."""
        table = generate_synthetic_population(size=200, seed=7)
        out = tmp_path / "pop.parquet"
        save_synthetic_population(table, out)

        loaded = pq.read_table(out)
        assert loaded.equals(table)

    def test_save_deterministic_hash(self, tmp_path: Path) -> None:
        """Same table saved twice produces identical content hash."""
        table = generate_synthetic_population(size=50, seed=42)
        p1 = tmp_path / "a.parquet"
        p2 = tmp_path / "b.parquet"
        m1 = save_synthetic_population(table, p1)
        m2 = save_synthetic_population(table, p2)
        assert m1.content_hash == m2.content_hash

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Parent directories are created if missing."""
        table = generate_synthetic_population(size=10, seed=0)
        out = tmp_path / "nested" / "dir" / "pop.parquet"
        manifest = save_synthetic_population(table, out)
        assert out.exists()
        assert manifest.file_path == out
