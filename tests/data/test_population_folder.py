# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for load_population_folder().

Covers: valid folder, missing schema.json, missing data file, missing source.json,
invalid schema, type mismatches, multiple data files.
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.csv as pcsv
import pytest

from reformlab.computation.ingestion import IngestionError
from reformlab.data.pipeline import load_population_folder


def _write_csv(path: Path, table: pa.Table) -> None:
    """Write a pa.Table to CSV."""
    pcsv.write_csv(table, path)


def _write_schema_json(folder: Path, schema_dict: dict) -> None:
    (folder / "schema.json").write_text(json.dumps(schema_dict), encoding="utf-8")


def _write_source_json(folder: Path, source_dict: dict) -> None:
    (folder / "source.json").write_text(json.dumps(source_dict), encoding="utf-8")


@pytest.fixture()
def sample_source() -> dict:
    return {
        "name": "test_dataset",
        "version": "1.0",
        "url": "https://example.com",
        "description": "Test dataset",
    }


@pytest.fixture()
def sample_schema() -> dict:
    return {
        "columns": [
            {"name": "household_id", "type": "int64", "required": True},
            {"name": "income", "type": "double", "required": True},
            {"name": "region_code", "type": "string", "required": False},
        ]
    }


@pytest.fixture()
def sample_table() -> pa.Table:
    return pa.table({
        "household_id": pa.array([1, 2, 3], type=pa.int64()),
        "income": pa.array([25000.0, 35000.0, 50000.0], type=pa.float64()),
        "region_code": pa.array(["11", "24", "31"], type=pa.utf8()),
    })


class TestLoadPopulationFolderValid:
    """Valid folder loading."""

    def test_loads_csv_with_metadata(
        self, tmp_path: Path, sample_table: pa.Table, sample_schema: dict, sample_source: dict,
    ) -> None:
        """Valid folder with data.csv + schema.json + source.json loads correctly."""
        folder = tmp_path / "dataset"
        folder.mkdir()
        _write_csv(folder / "data.csv", sample_table)
        _write_schema_json(folder, sample_schema)
        _write_source_json(folder, sample_source)

        pop, manifest = load_population_folder(folder, allowed_roots=(tmp_path,))

        assert pop.primary_table.num_rows == 3
        assert manifest.row_count == 3
        assert manifest.source.name == "test_dataset"
        assert manifest.source.version == "1.0"
        assert manifest.content_hash  # non-empty

    def test_loads_single_csv_without_data_prefix(
        self, tmp_path: Path, sample_table: pa.Table, sample_schema: dict, sample_source: dict,
    ) -> None:
        """Folder with a single CSV (not named data.csv) is found automatically."""
        folder = tmp_path / "dataset"
        folder.mkdir()
        _write_csv(folder / "my_data.csv", sample_table)
        _write_schema_json(folder, sample_schema)
        _write_source_json(folder, sample_source)

        pop, manifest = load_population_folder(folder, allowed_roots=(tmp_path,))
        assert pop.primary_table.num_rows == 3

    def test_entity_type_from_source_name(
        self, tmp_path: Path, sample_table: pa.Table, sample_schema: dict, sample_source: dict,
    ) -> None:
        """Entity type is derived from source name when it's a valid identifier."""
        folder = tmp_path / "dataset"
        folder.mkdir()
        _write_csv(folder / "data.csv", sample_table)
        _write_schema_json(folder, sample_schema)
        _write_source_json(folder, sample_source)

        pop, manifest = load_population_folder(folder, allowed_roots=(tmp_path,))
        assert "test_dataset" in pop.tables


class TestLoadPopulationFolderErrors:
    """Error cases for load_population_folder."""

    def test_not_a_directory(self, tmp_path: Path) -> None:
        """Non-directory path raises IngestionError."""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("hello")
        with pytest.raises(IngestionError, match="not a directory"):
            load_population_folder(file_path, allowed_roots=(tmp_path,))

    def test_missing_schema_json(
        self, tmp_path: Path, sample_table: pa.Table, sample_source: dict,
    ) -> None:
        """Missing schema.json raises IngestionError."""
        folder = tmp_path / "dataset"
        folder.mkdir()
        _write_csv(folder / "data.csv", sample_table)
        _write_source_json(folder, sample_source)

        with pytest.raises(IngestionError, match="schema.json not found"):
            load_population_folder(folder, allowed_roots=(tmp_path,))

    def test_missing_source_json(
        self, tmp_path: Path, sample_table: pa.Table, sample_schema: dict,
    ) -> None:
        """Missing source.json raises IngestionError."""
        folder = tmp_path / "dataset"
        folder.mkdir()
        _write_csv(folder / "data.csv", sample_table)
        _write_schema_json(folder, sample_schema)

        with pytest.raises(IngestionError, match="source.json not found"):
            load_population_folder(folder, allowed_roots=(tmp_path,))

    def test_no_data_file(
        self, tmp_path: Path, sample_schema: dict, sample_source: dict,
    ) -> None:
        """No CSV or Parquet file raises IngestionError."""
        folder = tmp_path / "dataset"
        folder.mkdir()
        _write_schema_json(folder, sample_schema)
        _write_source_json(folder, sample_source)

        with pytest.raises(IngestionError, match="no data file"):
            load_population_folder(folder, allowed_roots=(tmp_path,))

    def test_multiple_data_files(
        self, tmp_path: Path, sample_table: pa.Table, sample_schema: dict, sample_source: dict,
    ) -> None:
        """Multiple data files without a data.csv raises IngestionError."""
        folder = tmp_path / "dataset"
        folder.mkdir()
        _write_csv(folder / "file_a.csv", sample_table)
        _write_csv(folder / "file_b.csv", sample_table)
        _write_schema_json(folder, sample_schema)
        _write_source_json(folder, sample_source)

        with pytest.raises(IngestionError, match="multiple data files"):
            load_population_folder(folder, allowed_roots=(tmp_path,))

    def test_missing_required_column(
        self, tmp_path: Path, sample_source: dict,
    ) -> None:
        """Data missing a required column raises IngestionError."""
        folder = tmp_path / "dataset"
        folder.mkdir()

        # Table missing 'income' column
        table = pa.table({"household_id": pa.array([1, 2], type=pa.int64())})
        _write_csv(folder / "data.csv", table)
        _write_schema_json(folder, {
            "columns": [
                {"name": "household_id", "type": "int64", "required": True},
                {"name": "income", "type": "double", "required": True},
            ]
        })
        _write_source_json(folder, sample_source)

        with pytest.raises(IngestionError, match="missing required columns"):
            load_population_folder(folder, allowed_roots=(tmp_path,))
