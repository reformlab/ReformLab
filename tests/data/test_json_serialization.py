# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for JSON serialization of DataSchema, DataSourceMetadata, and DatasetDescriptor.

Covers round-trip fidelity, edge cases, and error handling for
from_json()/to_json() methods.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.computation.ingestion import DataSchema
from reformlab.data.descriptor import DatasetDescriptor
from reformlab.data.pipeline import DataSourceMetadata

# ====================================================================
# DataSchema JSON round-trip
# ====================================================================


class TestDataSchemaJson:
    """DataSchema.to_json() / from_json() round-trip tests."""

    def test_round_trip_preserves_all_fields(self) -> None:
        """to_json → from_json preserves schema, required, optional."""
        schema = DataSchema(
            schema=pa.schema([
                pa.field("household_id", pa.int64()),
                pa.field("income", pa.float64()),
                pa.field("region_code", pa.utf8()),
            ]),
            required_columns=("household_id", "income"),
            optional_columns=("region_code",),
        )
        data = schema.to_json()
        restored = DataSchema.from_json(data)

        assert restored.required_columns == schema.required_columns
        assert restored.optional_columns == schema.optional_columns
        assert restored.schema.equals(schema.schema)

    def test_round_trip_all_required(self) -> None:
        """Round-trip with all columns required, no optional."""
        schema = DataSchema(
            schema=pa.schema([
                pa.field("a", pa.int32()),
                pa.field("b", pa.bool_()),
            ]),
            required_columns=("a", "b"),
        )
        data = schema.to_json()
        restored = DataSchema.from_json(data)
        assert restored.required_columns == ("a", "b")
        assert restored.optional_columns == ()

    def test_json_column_types(self) -> None:
        """Various PyArrow type strings round-trip correctly."""
        schema = DataSchema(
            schema=pa.schema([
                pa.field("i64", pa.int64()),
                pa.field("f64", pa.float64()),
                pa.field("s", pa.utf8()),
                pa.field("b", pa.bool_()),
                pa.field("d", pa.date32()),
                pa.field("i32", pa.int32()),
            ]),
            required_columns=("i64", "f64", "s", "b", "d", "i32"),
        )
        data = schema.to_json()
        restored = DataSchema.from_json(data)
        for name in schema.schema.names:
            assert restored.schema.field(name).type.equals(
                schema.schema.field(name).type
            )

    def test_from_json_missing_columns_raises(self) -> None:
        """from_json raises ValueError when columns list is missing."""
        with pytest.raises(ValueError, match="non-empty 'columns' list"):
            DataSchema.from_json({})

    def test_from_json_empty_columns_raises(self) -> None:
        """from_json raises ValueError when columns list is empty."""
        with pytest.raises(ValueError, match="non-empty 'columns' list"):
            DataSchema.from_json({"columns": []})

    def test_from_json_unknown_type_raises(self) -> None:
        """from_json raises ValueError for unknown PyArrow type alias."""
        with pytest.raises(ValueError, match="Unknown PyArrow type"):
            DataSchema.from_json({
                "columns": [{"name": "x", "type": "not_a_type", "required": True}]
            })

    def test_required_defaults_to_true(self) -> None:
        """Columns without 'required' field default to required=True."""
        data = {
            "columns": [
                {"name": "a", "type": "int64"},
                {"name": "b", "type": "string", "required": False},
            ]
        }
        schema = DataSchema.from_json(data)
        assert schema.required_columns == ("a",)
        assert schema.optional_columns == ("b",)


# ====================================================================
# DataSourceMetadata JSON round-trip
# ====================================================================


class TestDataSourceMetadataJson:
    """DataSourceMetadata.to_json() / from_json() round-trip tests."""

    def test_round_trip_with_license(self) -> None:
        """Round-trip preserves all fields including license."""
        source = DataSourceMetadata(
            name="filosofi_2021",
            version="2021",
            url="https://example.com/data",
            description="Income data",
            license="CC-BY-4.0",
        )
        data = source.to_json()
        restored = DataSourceMetadata.from_json(data)

        assert restored.name == source.name
        assert restored.version == source.version
        assert restored.url == source.url
        assert restored.description == source.description
        assert restored.license == source.license

    def test_round_trip_without_license(self) -> None:
        """Round-trip with empty license omits it from JSON."""
        source = DataSourceMetadata(
            name="test",
            version="1.0",
            url="https://example.com",
            description="Test data",
        )
        data = source.to_json()
        assert "license" not in data

        restored = DataSourceMetadata.from_json(data)
        assert restored.license == ""


# ====================================================================
# DatasetDescriptor JSON round-trip
# ====================================================================


class TestDatasetDescriptorJson:
    """DatasetDescriptor.to_json() / from_json() round-trip tests."""

    def test_round_trip_full(self) -> None:
        """Round-trip preserves all fields."""
        desc = DatasetDescriptor(
            dataset_id="filosofi_2021_commune",
            provider="insee",
            description="Filosofi commune data",
            schema=DataSchema(
                schema=pa.schema([
                    pa.field("commune_code", pa.utf8()),
                    pa.field("income", pa.float64()),
                ]),
                required_columns=("commune_code",),
                optional_columns=("income",),
            ),
            url="https://example.com/data.zip",
            license="CC-BY-4.0",
            version="2021",
            column_mapping=(("CODGEO", "commune_code"), ("MED21", "income")),
            encoding="utf-8",
            separator=";",
            null_markers=("s", "nd", ""),
            file_format="zip",
            skip_rows=1,
        )
        data = desc.to_json()
        restored = DatasetDescriptor.from_json(data)

        assert restored.dataset_id == desc.dataset_id
        assert restored.provider == desc.provider
        assert restored.description == desc.description
        assert restored.url == desc.url
        assert restored.license == desc.license
        assert restored.version == desc.version
        assert restored.column_mapping == desc.column_mapping
        assert restored.encoding == desc.encoding
        assert restored.separator == desc.separator
        assert restored.null_markers == desc.null_markers
        assert restored.file_format == desc.file_format
        assert restored.skip_rows == desc.skip_rows
        assert restored.schema.required_columns == desc.schema.required_columns
        assert restored.schema.optional_columns == desc.schema.optional_columns

    def test_round_trip_minimal(self) -> None:
        """Round-trip with only required fields (defaults for the rest)."""
        desc = DatasetDescriptor(
            dataset_id="simple",
            provider="user",
            description="Simple user dataset",
            schema=DataSchema(
                schema=pa.schema([pa.field("value", pa.float64())]),
                required_columns=("value",),
            ),
        )
        data = desc.to_json()
        restored = DatasetDescriptor.from_json(data)

        assert restored.dataset_id == desc.dataset_id
        assert restored.url == ""
        assert restored.column_mapping == ()
        assert restored.encoding == "utf-8"
        assert restored.separator == ","
        assert restored.file_format == "csv"
        assert restored.skip_rows == 0

    def test_json_omits_defaults(self) -> None:
        """to_json omits fields that match default values."""
        desc = DatasetDescriptor(
            dataset_id="test",
            provider="user",
            description="test",
            schema=DataSchema(
                schema=pa.schema([pa.field("a", pa.int64())]),
                required_columns=("a",),
            ),
        )
        data = desc.to_json()
        assert "url" not in data
        assert "license" not in data
        assert "version" not in data
        assert "column_mapping" not in data
        assert "encoding" not in data
        assert "separator" not in data
        assert "file_format" not in data
        assert "skip_rows" not in data
