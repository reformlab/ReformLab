# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for descriptor.json support in pipeline — Story 21.4.

Tests cover:
- load_population_folder with descriptor.json
- Fallback to source.json when descriptor.json is missing
- Error handling for malformed descriptor.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from reformlab.computation.ingestion import DataSchema, IngestionError
from reformlab.data import load_population_folder


class TestLoadPopulationFolderWithDescriptor:
    """Test load_population_folder with descriptor.json — Story 21.4 / AC2."""

    def test_loads_with_descriptor_json(self, tmp_path: Path) -> None:
        """Successfully loads population with descriptor.json — AC2."""
        # Create schema.json
        schema = DataSchema(
            schema=pa.schema([
                pa.field("household_id", pa.int64()),
                pa.field("income", pa.float64()),
            ]),
            required_columns=("household_id", "income"),
        )
        schema_path = tmp_path / "schema.json"
        schema_path.write_text(json.dumps(schema.to_json()))

        # Create descriptor.json
        descriptor = {
            "asset_id": "test-synthetic-2024",
            "name": "Test Synthetic Population",
            "description": "Test synthetic population for unit test",
            "data_class": "structural",
            "origin": "synthetic-public",
            "access_mode": "bundled",
            "trust_status": "exploratory",
            "version": "1.0.0",
            "source_url": "",
            "license": "AGPL-3.0-or-later",
        }
        descriptor_path = tmp_path / "descriptor.json"
        descriptor_path.write_text(json.dumps(descriptor))

        # Create data.parquet
        table = pa.table({
            "household_id": [1, 2, 3],
            "income": [1000.0, 2000.0, 3000.0],
        })
        data_path = tmp_path / "data.parquet"
        pq.write_table(table, data_path)

        # Load should succeed
        population, manifest = load_population_folder(tmp_path)
        assert population is not None
        assert manifest.row_count == 3
        assert manifest.source.name == "test-synthetic-2024"
        assert manifest.source.version == "1.0.0"

    def test_fallback_to_source_json_when_descriptor_missing(self, tmp_path: Path) -> None:
        """Falls back to source.json when descriptor.json is missing — AC2."""
        # Create schema.json
        schema = DataSchema(
            schema=pa.schema([
                pa.field("household_id", pa.int64()),
                pa.field("income", pa.float64()),
            ]),
            required_columns=("household_id", "income"),
        )
        schema_path = tmp_path / "schema.json"
        schema_path.write_text(json.dumps(schema.to_json()))

        # Create source.json (legacy format)
        source = {
            "name": "test-legacy",
            "version": "1.0.0",
            "url": "https://example.com",
            "description": "Legacy source format",
            "license": "MIT",
        }
        source_path = tmp_path / "source.json"
        source_path.write_text(json.dumps(source))

        # Create data.parquet
        table = pa.table({
            "household_id": [1, 2, 3],
            "income": [1000.0, 2000.0, 3000.0],
        })
        data_path = tmp_path / "data.parquet"
        pq.write_table(table, data_path)

        # Load should succeed with source.json fallback
        population, manifest = load_population_folder(tmp_path)
        assert population is not None
        assert manifest.row_count == 3
        assert manifest.source.name == "test-legacy"

    def test_malformed_descriptor_json_raises_error(self, tmp_path: Path) -> None:
        """Malformed descriptor.json raises IngestionError — AC2."""
        # Create schema.json
        schema = DataSchema(
            schema=pa.schema([pa.field("household_id", pa.int64())]),
            required_columns=("household_id",),
        )
        schema_path = tmp_path / "schema.json"
        schema_path.write_text(json.dumps(schema.to_json()))

        # Create malformed descriptor.json
        descriptor_path = tmp_path / "descriptor.json"
        descriptor_path.write_text("{invalid json")

        # Create data.parquet
        table = pa.table({"household_id": [1, 2, 3]})
        data_path = tmp_path / "data.parquet"
        pq.write_table(table, data_path)

        # Load should fail with IngestionError
        with pytest.raises(IngestionError, match="invalid descriptor.json"):
            load_population_folder(tmp_path)

    def test_invalid_descriptor_json_raises_error(self, tmp_path: Path) -> None:
        """Invalid descriptor.json (missing required fields) raises IngestionError — AC2."""
        # Create schema.json
        schema = DataSchema(
            schema=pa.schema([pa.field("household_id", pa.int64())]),
            required_columns=("household_id",),
        )
        schema_path = tmp_path / "schema.json"
        schema_path.write_text(json.dumps(schema.to_json()))

        # Create invalid descriptor.json (missing required fields)
        descriptor = {
            "asset_id": "test-incomplete",
            # Missing required fields: name, description, data_class, origin, access_mode, trust_status
        }
        descriptor_path = tmp_path / "descriptor.json"
        descriptor_path.write_text(json.dumps(descriptor))

        # Create data.parquet
        table = pa.table({"household_id": [1, 2, 3]})
        data_path = tmp_path / "data.parquet"
        pq.write_table(table, data_path)

        # Load should fail with IngestionError
        with pytest.raises(IngestionError, match="invalid descriptor.json"):
            load_population_folder(tmp_path)

    def test_no_descriptor_or_source_json_raises_error(self, tmp_path: Path) -> None:
        """Missing both descriptor.json and source.json raises IngestionError — AC2."""
        # Create schema.json only
        schema = DataSchema(
            schema=pa.schema([pa.field("household_id", pa.int64())]),
            required_columns=("household_id",),
        )
        schema_path = tmp_path / "schema.json"
        schema_path.write_text(json.dumps(schema.to_json()))

        # Create data.parquet
        table = pa.table({"household_id": [1, 2, 3]})
        data_path = tmp_path / "data.parquet"
        pq.write_table(table, data_path)

        # Load should fail with IngestionError
        with pytest.raises(IngestionError, match="neither descriptor.json nor source.json"):
            load_population_folder(tmp_path)

    def test_descriptor_json_takes_precedence_over_source_json(self, tmp_path: Path) -> None:
        """descriptor.json takes precedence when both files exist — AC2."""
        # Create schema.json
        schema = DataSchema(
            schema=pa.schema([pa.field("household_id", pa.int64())]),
            required_columns=("household_id",),
        )
        schema_path = tmp_path / "schema.json"
        schema_path.write_text(json.dumps(schema.to_json()))

        # Create descriptor.json
        descriptor = {
            "asset_id": "from-descriptor",
            "name": "From Descriptor",
            "description": "Should take precedence",
            "data_class": "structural",
            "origin": "synthetic-public",
            "access_mode": "bundled",
            "trust_status": "exploratory",
            "version": "2.0.0",
            "source_url": "",
            "license": "AGPL-3.0-or-later",
        }
        descriptor_path = tmp_path / "descriptor.json"
        descriptor_path.write_text(json.dumps(descriptor))

        # Also create source.json (should be ignored)
        source = {
            "name": "from-source",
            "version": "1.0.0",
            "url": "https://example.com",
            "description": "Should be ignored",
        }
        source_path = tmp_path / "source.json"
        source_path.write_text(json.dumps(source))

        # Create data.parquet
        table = pa.table({"household_id": [1, 2, 3]})
        data_path = tmp_path / "data.parquet"
        pq.write_table(table, data_path)

        # Load should use descriptor.json values
        population, manifest = load_population_folder(tmp_path)
        assert manifest.source.name == "from-descriptor"
        assert manifest.source.version == "2.0.0"
