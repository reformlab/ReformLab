"""Test 5.4: Parquet ingestion round-trip test with fixture data."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pyarrow as pa

from reformlab.computation.openfisca_adapter import OpenFiscaAdapter
from reformlab.computation.types import PolicyConfig, PopulationData


class TestParquetRoundTrip:
    """AC-1: Given an OpenFisca output dataset (Parquet), when compute()
    is called, then it returns a ComputationResult with mapped output fields."""

    def test_parquet_compute_returns_correct_fields(
        self,
        fixtures_dir: Path,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given a Parquet file for period 2026, when compute() is called,
        then the result contains all expected output columns."""
        with patch(
            "reformlab.computation.openfisca_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaAdapter(data_dir=fixtures_dir)
            result = adapter.compute(sample_population, sample_policy, period=2026)

        assert result.period == 2026
        assert "person_id" in result.output_fields.column_names
        assert "income_tax" in result.output_fields.column_names
        assert "carbon_tax" in result.output_fields.column_names

    def test_parquet_compute_preserves_row_count(
        self,
        fixtures_dir: Path,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given a 3-row Parquet fixture, when compute() is called,
        then the result has exactly 3 rows."""
        with patch(
            "reformlab.computation.openfisca_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaAdapter(data_dir=fixtures_dir)
            result = adapter.compute(sample_population, sample_policy, period=2026)

        assert result.output_fields.num_rows == 3
        assert result.metadata["row_count"] == 3

    def test_parquet_data_values_match(
        self,
        fixtures_dir: Path,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
        output_table: pa.Table,
    ) -> None:
        """Given known Parquet fixture data, when compute() is called,
        then the output values match the original fixture."""
        with patch(
            "reformlab.computation.openfisca_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaAdapter(data_dir=fixtures_dir)
            result = adapter.compute(sample_population, sample_policy, period=2026)

        assert result.output_fields.column("carbon_tax").to_pylist() == [
            134.0,
            200.0,
            267.0,
        ]

    def test_missing_period_raises_file_not_found(
        self,
        fixtures_dir: Path,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given no file exists for period 2099, when compute() is called,
        then FileNotFoundError is raised."""
        import pytest

        with patch(
            "reformlab.computation.openfisca_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaAdapter(data_dir=fixtures_dir)
            with pytest.raises(FileNotFoundError, match="2099"):
                adapter.compute(sample_population, sample_policy, period=2099)
