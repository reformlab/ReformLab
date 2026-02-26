"""Story 1.2 ingestion tests for CSV/Parquet loading and validation."""

from __future__ import annotations

import gzip
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.csv as pcsv
import pyarrow.parquet as pq
import pytest

from reformlab.computation.ingestion import (
    DEFAULT_OPENFISCA_OUTPUT_SCHEMA,
    DataSchema,
    IngestionError,
    ingest,
    ingest_csv,
    ingest_parquet,
)
from reformlab.computation.openfisca_adapter import OpenFiscaAdapter
from reformlab.computation.types import PolicyConfig, PopulationData


@pytest.fixture()
def ingestion_schema() -> DataSchema:
    return DataSchema(
        schema=pa.schema(
            [
                pa.field("household_id", pa.int64()),
                pa.field("income_tax", pa.float64()),
                pa.field("carbon_tax", pa.float64()),
            ]
        ),
        required_columns=("household_id", "income_tax", "carbon_tax"),
        optional_columns=(),
    )


@pytest.fixture()
def ingestion_table() -> pa.Table:
    return pa.table(
        {
            "household_id": pa.array([10, 11, 12], type=pa.int64()),
            "income_tax": pa.array([3000.0, 6750.0, 12000.0], type=pa.float64()),
            "carbon_tax": pa.array([134.0, 200.0, 267.0], type=pa.float64()),
        }
    )


@pytest.fixture()
def sample_population_for_adapter() -> PopulationData:
    return PopulationData(tables={"default": pa.table({"x": pa.array([1])})})


@pytest.fixture()
def sample_policy_for_adapter() -> PolicyConfig:
    return PolicyConfig(parameters={"carbon_tax_rate": 44.6}, name="baseline")


class TestIngestionRoundTrips:
    def test_csv_round_trip(
        self, tmp_path: Path, ingestion_schema: DataSchema, ingestion_table: pa.Table
    ) -> None:
        """Given valid CSV data, when ingest_csv() is called,
        then output matches schema and values.
        """
        csv_path = tmp_path / "households.csv"
        pcsv.write_csv(ingestion_table, csv_path)

        result = ingest_csv(csv_path, ingestion_schema)

        assert result.format == "csv"
        assert result.source_path == csv_path
        assert result.row_count == 3
        assert result.table.schema.equals(ingestion_schema.schema)
        assert result.table.equals(ingestion_table)

    def test_parquet_round_trip(
        self, tmp_path: Path, ingestion_schema: DataSchema, ingestion_table: pa.Table
    ) -> None:
        """Given valid Parquet data, when ingest_parquet() is called,
        then output matches schema and values.
        """
        parquet_path = tmp_path / "households.parquet"
        pq.write_table(ingestion_table, parquet_path)

        result = ingest_parquet(parquet_path, ingestion_schema)

        assert result.format == "parquet"
        assert result.source_path == parquet_path
        assert result.row_count == 3
        assert result.table.schema.equals(ingestion_schema.schema)
        assert result.table.equals(ingestion_table)

    def test_csv_parquet_parity(
        self, tmp_path: Path, ingestion_schema: DataSchema, ingestion_table: pa.Table
    ) -> None:
        """Given identical CSV and Parquet files, when ingested,
        then resulting tables are identical.
        """
        csv_path = tmp_path / "same.csv"
        parquet_path = tmp_path / "same.parquet"
        pcsv.write_csv(ingestion_table, csv_path)
        pq.write_table(ingestion_table, parquet_path)

        csv_result = ingest(csv_path, ingestion_schema)
        parquet_result = ingest(parquet_path, ingestion_schema)

        assert csv_result.table.equals(parquet_result.table)
        assert csv_result.table.schema.equals(parquet_result.table.schema)


class TestIngestionValidation:
    def test_missing_columns_csv_reports_all(
        self, tmp_path: Path, ingestion_schema: DataSchema
    ) -> None:
        """Given missing required CSV columns,
        then a single IngestionError reports all missing columns.
        """
        bad_path = tmp_path / "missing.csv"
        bad_table = pa.table({"household_id": pa.array([1, 2, 3], type=pa.int64())})
        pcsv.write_csv(bad_table, bad_path)

        with pytest.raises(IngestionError) as exc_info:
            ingest_csv(bad_path, ingestion_schema)

        err = exc_info.value
        assert sorted(err.missing_columns) == ["carbon_tax", "income_tax"]
        message = str(err)
        assert "carbon_tax" in message
        assert "income_tax" in message

    def test_missing_columns_parquet_reports_all(
        self, tmp_path: Path, ingestion_schema: DataSchema
    ) -> None:
        """Given missing required Parquet columns,
        then a single IngestionError reports all missing columns.
        """
        bad_path = tmp_path / "missing.parquet"
        bad_table = pa.table({"household_id": pa.array([1, 2, 3], type=pa.int64())})
        pq.write_table(bad_table, bad_path)

        with pytest.raises(IngestionError) as exc_info:
            ingest_parquet(bad_path, ingestion_schema)

        err = exc_info.value
        assert sorted(err.missing_columns) == ["carbon_tax", "income_tax"]
        assert "missing required columns" in str(err).lower()

    def test_csv_type_mismatch_reports_column_and_types(
        self, tmp_path: Path, ingestion_schema: DataSchema
    ) -> None:
        """Given invalid CSV values for typed column,
        then error reports column + expected + actual type.
        """
        bad_path = tmp_path / "bad_type.csv"
        with bad_path.open("w", encoding="utf-8") as handle:
            handle.write("household_id,income_tax,carbon_tax\n")
            handle.write("1,3000.0,134.0\n")
            handle.write("2,NOT_A_FLOAT,200.0\n")

        with pytest.raises(IngestionError) as exc_info:
            ingest_csv(bad_path, ingestion_schema)

        err = exc_info.value
        assert err.type_mismatches
        mismatch = err.type_mismatches[0]
        assert mismatch.column == "income_tax"
        assert "double" in mismatch.expected_type or "float" in mismatch.expected_type
        assert mismatch.actual_type

    def test_parquet_type_mismatch_reports_column_and_types(
        self, tmp_path: Path, ingestion_schema: DataSchema
    ) -> None:
        """Given a Parquet file with wrong column types,
        then error reports column + expected + actual type.
        """
        bad_path = tmp_path / "bad_type.parquet"
        bad_table = pa.table(
            {
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "income_tax": pa.array(["3000", "6750", "12000"], type=pa.string()),
                "carbon_tax": pa.array([134.0, 200.0, 267.0], type=pa.float64()),
            }
        )
        pq.write_table(bad_table, bad_path)

        with pytest.raises(IngestionError) as exc_info:
            ingest_parquet(bad_path, ingestion_schema)

        err = exc_info.value
        assert len(err.type_mismatches) == 1
        mismatch = err.type_mismatches[0]
        assert mismatch.column == "income_tax"
        assert "double" in mismatch.expected_type or "float" in mismatch.expected_type
        assert "string" in mismatch.actual_type

    def test_schema_enforcement_excludes_extra_columns(
        self, tmp_path: Path, ingestion_schema: DataSchema
    ) -> None:
        """Given extra source columns, when ingested with schema,
        then extra columns are excluded.
        """
        csv_path = tmp_path / "extra.csv"
        extra_table = pa.table(
            {
                "household_id": pa.array([1, 2]),
                "income_tax": pa.array([100.0, 200.0]),
                "carbon_tax": pa.array([10.0, 20.0]),
                "extra_metric": pa.array([999, 1000]),
            }
        )
        pcsv.write_csv(extra_table, csv_path)

        result = ingest_csv(csv_path, ingestion_schema)

        assert result.table.column_names == ["household_id", "income_tax", "carbon_tax"]

    def test_empty_csv_with_headers_returns_empty_typed_table(
        self, tmp_path: Path, ingestion_schema: DataSchema
    ) -> None:
        """Given CSV with headers but no rows, when ingested,
        then result is empty table with correct schema.
        """
        csv_path = tmp_path / "empty.csv"
        with csv_path.open("w", encoding="utf-8") as handle:
            handle.write("household_id,income_tax,carbon_tax\n")

        result = ingest_csv(csv_path, ingestion_schema)

        assert result.row_count == 0
        assert result.table.schema.equals(ingestion_schema.schema)

    def test_empty_parquet_returns_empty_typed_table(
        self, tmp_path: Path, ingestion_schema: DataSchema
    ) -> None:
        """Given Parquet with zero rows, when ingested,
        then result is empty table with correct schema.
        """
        parquet_path = tmp_path / "empty.parquet"
        empty_table = pa.table(
            {
                "household_id": pa.array([], type=pa.int64()),
                "income_tax": pa.array([], type=pa.float64()),
                "carbon_tax": pa.array([], type=pa.float64()),
            }
        )
        pq.write_table(empty_table, parquet_path)

        result = ingest_parquet(parquet_path, ingestion_schema)

        assert result.row_count == 0
        assert result.table.schema.equals(ingestion_schema.schema)

    def test_unsupported_extension_raises_clear_error(
        self, tmp_path: Path, ingestion_schema: DataSchema
    ) -> None:
        """Given unsupported extension, when ingest() is called,
        then clear IngestionError is raised.
        """
        path = tmp_path / "data.xlsx"
        path.write_bytes(b"not-a-real-xlsx")

        with pytest.raises(IngestionError) as exc_info:
            ingest(path, ingestion_schema)

        assert "unsupported file extension" in str(exc_info.value).lower()
        assert ".xlsx" in str(exc_info.value)

    def test_ingestion_result_metadata(
        self, tmp_path: Path, ingestion_schema: DataSchema, ingestion_table: pa.Table
    ) -> None:
        """Given a successful ingest, metadata fields are populated."""
        csv_path = tmp_path / "meta.csv"
        pcsv.write_csv(ingestion_table, csv_path)

        result = ingest_csv(csv_path, ingestion_schema)

        assert result.source_path == csv_path
        assert result.format == "csv"
        assert result.row_count == result.table.num_rows
        assert "loaded_at" in result.metadata

    def test_compressed_csv_supported(
        self, tmp_path: Path, ingestion_schema: DataSchema, ingestion_table: pa.Table
    ) -> None:
        """Given .csv.gz input, when ingested, then output matches plain .csv output."""
        csv_path = tmp_path / "source.csv"
        gzip_path = tmp_path / "source.csv.gz"
        pcsv.write_csv(ingestion_table, csv_path)

        with csv_path.open("rb") as source, gzip.open(gzip_path, "wb") as target:
            target.write(source.read())

        plain_result = ingest(csv_path, ingestion_schema)
        gzip_result = ingest(gzip_path, ingestion_schema)

        assert gzip_result.format == "csv"
        assert plain_result.table.equals(gzip_result.table)


    def test_corrupt_gzip_raises_structured_error(
        self, tmp_path: Path, ingestion_schema: DataSchema
    ) -> None:
        """Given a corrupt .csv.gz file, when ingested,
        then a structured IngestionError is raised (not raw BadGzipFile).
        """
        bad_gz = tmp_path / "corrupt.csv.gz"
        bad_gz.write_bytes(b"this is not gzip data")

        with pytest.raises(IngestionError) as exc_info:
            ingest(bad_gz, ingestion_schema)

        assert "not valid gzip" in str(exc_info.value).lower()


class TestAdapterIntegration:
    def test_adapter_compute_uses_ingestion_layer(
        self,
        tmp_path: Path,
        sample_population_for_adapter: PopulationData,
        sample_policy_for_adapter: PolicyConfig,
    ) -> None:
        """Given OpenFiscaAdapter.compute(),
        then period file loading is delegated to ingestion module.
        """
        output = pa.table(
            {
                "person_id": pa.array([1, 2, 3], type=pa.int64()),
                "income_tax": pa.array([3000.0, 6750.0, 12000.0], type=pa.float64()),
                "carbon_tax": pa.array([134.0, 200.0, 267.0], type=pa.float64()),
            }
        )
        csv_path = tmp_path / "2025.csv"
        pcsv.write_csv(output, csv_path)

        with (
            patch(
                "reformlab.computation.openfisca_adapter._detect_openfisca_version",
                return_value="44.2.2",
            ),
            patch(
                "reformlab.computation.openfisca_adapter.ingest",
                wraps=ingest,
            ) as ingest_spy,
        ):
            adapter = OpenFiscaAdapter(data_dir=tmp_path)
            result = adapter.compute(
                sample_population_for_adapter,
                sample_policy_for_adapter,
                period=2025,
            )

        ingest_spy.assert_called_once()
        assert result.output_fields.equals(output)
        assert result.metadata["row_count"] == 3
        assert DEFAULT_OPENFISCA_OUTPUT_SCHEMA.required_columns
