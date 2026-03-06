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


class TestGenerateSyntheticPopulation:
    """AC-1: Deterministic synthetic population generation."""

    def test_default_size_and_seed(self) -> None:
        """Default invocation produces 100k-row table with expected columns."""
        table = generate_synthetic_population()
        assert table.num_rows == DEFAULT_SIZE
        assert table.schema.names == ["household_id", "income", "carbon_emissions"]

    def test_column_types(self) -> None:
        """Columns have correct Arrow types."""
        table = generate_synthetic_population(size=10, seed=0)
        assert table.schema.field("household_id").type == pa.int64()
        assert table.schema.field("income").type == pa.float64()
        assert table.schema.field("carbon_emissions").type == pa.float64()

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

    def test_income_range(self) -> None:
        """Incomes are positive and in a reasonable range."""
        table = generate_synthetic_population(size=1000, seed=42)
        incomes = table.column("income").to_pylist()
        assert all(i > 0 for i in incomes)
        assert min(incomes) > 10_000
        assert max(incomes) < 120_000

    def test_emissions_non_negative(self) -> None:
        """Carbon emissions are non-negative."""
        table = generate_synthetic_population(size=1000, seed=42)
        emissions = table.column("carbon_emissions").to_pylist()
        assert all(e >= 0 for e in emissions)

    def test_empty_population(self) -> None:
        """size=0 produces empty table with correct schema."""
        table = generate_synthetic_population(size=0, seed=42)
        assert table.num_rows == 0
        assert table.schema.names == ["household_id", "income", "carbon_emissions"]

    def test_negative_size_raises(self) -> None:
        """Negative size raises ValueError."""
        with pytest.raises(ValueError, match="size must be >= 0"):
            generate_synthetic_population(size=-1)

    def test_matches_conftest_fixture(self) -> None:
        """Generator output must match the original conftest.py fixture exactly.

        This is the critical compatibility test — any deviation breaks BKL-701
        benchmark reference values.
        """
        import random

        # Reproduce conftest.py logic inline
        seed = 42
        size = 1000  # Use smaller size for speed; algorithm is per-row deterministic

        # --- conftest.py logic ---
        household_ids = list(range(size))
        incomes: list[float] = []
        for i in range(size):
            random.seed(seed + i)
            base_income = 15_000.0
            income_range = 80_000.0
            income = base_income + (i / size) * income_range
            variation = random.uniform(-0.1, 0.1)
            income = income * (1 + variation)
            incomes.append(income)

        emissions: list[float] = []
        for i, inc in enumerate(incomes):
            random.seed(seed + size + i)
            base_emissions = 2.0
            emissions_range = 10.0
            emissions_val = base_emissions + (inc - 15_000) / 80_000 * emissions_range
            variation = random.uniform(-0.15, 0.15)
            emissions_val = emissions_val * (1 + variation)
            emissions.append(max(0.0, emissions_val))

        expected = pa.table(
            {
                "household_id": pa.array(household_ids, type=pa.int64()),
                "income": pa.array(incomes, type=pa.float64()),
                "carbon_emissions": pa.array(emissions, type=pa.float64()),
            }
        )

        # --- Generator output ---
        actual = generate_synthetic_population(size=size, seed=seed)
        assert actual.equals(expected), "Generator must match conftest.py algorithm exactly"


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
        assert manifest.column_names == ("household_id", "income", "carbon_emissions")
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
