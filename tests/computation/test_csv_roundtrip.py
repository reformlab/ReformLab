# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Test 5.3: CSV ingestion round-trip test with fixture data."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pyarrow as pa

from reformlab.computation.openfisca_adapter import OpenFiscaAdapter
from reformlab.computation.types import PolicyConfig, PopulationData


class TestCSVRoundTrip:
    """AC-1: Given an OpenFisca output dataset (CSV), when compute() is
    called, then it returns a ComputationResult with mapped output fields."""

    def test_csv_compute_returns_correct_fields(
        self,
        fixtures_dir: Path,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given a CSV file for period 2025, when compute() is called,
        then the result contains all expected output columns."""
        with patch(
            "reformlab.computation.openfisca_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaAdapter(data_dir=fixtures_dir)
            result = adapter.compute(sample_population, sample_policy, period=2025)

        assert result.period == 2025
        assert result.adapter_version == "44.2.2"
        assert "person_id" in result.output_fields.column_names
        assert "income_tax" in result.output_fields.column_names
        assert "carbon_tax" in result.output_fields.column_names

    def test_csv_compute_preserves_row_count(
        self,
        fixtures_dir: Path,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given a 3-row CSV fixture, when compute() is called,
        then the result has exactly 3 rows."""
        with patch(
            "reformlab.computation.openfisca_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaAdapter(data_dir=fixtures_dir)
            result = adapter.compute(sample_population, sample_policy, period=2025)

        assert result.output_fields.num_rows == 3
        assert result.metadata["row_count"] == 3

    def test_csv_compute_records_metadata(
        self,
        fixtures_dir: Path,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given a compute() call, then metadata includes timing and source."""
        with patch(
            "reformlab.computation.openfisca_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaAdapter(data_dir=fixtures_dir)
            result = adapter.compute(sample_population, sample_policy, period=2025)

        assert "timing_seconds" in result.metadata
        assert result.metadata["source"] == "pre-computed"
        assert result.metadata["policy_name"] == "carbon-tax-baseline"

    def test_csv_data_values_match(
        self,
        fixtures_dir: Path,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
        output_table: pa.Table,
    ) -> None:
        """Given known fixture data, when compute() is called,
        then the output values match the original fixture."""
        with patch(
            "reformlab.computation.openfisca_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaAdapter(data_dir=fixtures_dir)
            result = adapter.compute(sample_population, sample_policy, period=2025)

        assert result.output_fields.column("income_tax").to_pylist() == [
            3000.0,
            6750.0,
            12000.0,
        ]
