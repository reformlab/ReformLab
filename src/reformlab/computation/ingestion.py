from __future__ import annotations

import csv
import gzip
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import pyarrow as pa
import pyarrow.csv as pcsv
import pyarrow.parquet as pq

IngestionFormat = Literal["csv", "parquet"]


@dataclass(frozen=True)
class DataSchema:
    """Schema contract for ingestion with required and optional columns."""

    schema: pa.Schema
    required_columns: tuple[str, ...]
    optional_columns: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        schema_names = set(self.schema.names)
        missing_declared = [
            name
            for name in (*self.required_columns, *self.optional_columns)
            if name not in schema_names
        ]
        if missing_declared:
            names = ", ".join(missing_declared)
            raise ValueError(
                "DataSchema declaration failed - "
                f"columns not present in schema: {names} - "
                "Ensure all required/optional columns are declared in schema"
            )

        overlap = set(self.required_columns).intersection(self.optional_columns)
        if overlap:
            names = ", ".join(sorted(overlap))
            raise ValueError(
                "DataSchema declaration failed - "
                f"columns marked both required and optional: {names} - "
                "Place each column in one group only"
            )

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(self.schema.names)

    def field(self, name: str) -> pa.Field:
        return self.schema.field(name)


@dataclass(frozen=True)
class TypeMismatch:
    """Describes a column whose incoming data type does not match the contract."""

    column: str
    expected_type: str
    actual_type: str


@dataclass(frozen=True)
class IngestionResult:
    """Successful ingestion output."""

    table: pa.Table
    source_path: Path
    format: IngestionFormat
    row_count: int
    metadata: dict[str, Any] = field(default_factory=dict)


class IngestionError(Exception):
    """Structured ingestion error used by CSV/Parquet ingestion functions."""

    def __init__(
        self,
        *,
        file_path: Path,
        summary: str,
        reason: str,
        fix: str,
        missing_columns: tuple[str, ...] = (),
        type_mismatches: tuple[TypeMismatch, ...] = (),
    ) -> None:
        self.file_path = file_path
        self.missing_columns = missing_columns
        self.type_mismatches = type_mismatches

        message = f"{summary} - {reason} - {fix} (file: {file_path})"
        super().__init__(message)


DEFAULT_OPENFISCA_OUTPUT_SCHEMA = DataSchema(
    schema=pa.schema(
        [
            pa.field("household_id", pa.int64()),
            pa.field("person_id", pa.int64()),
            pa.field("income_tax", pa.float64()),
            pa.field("carbon_tax", pa.float64()),
        ]
    ),
    required_columns=("income_tax", "carbon_tax"),
    optional_columns=("household_id", "person_id"),
)


def ingest_csv(path: str | Path, schema: DataSchema) -> IngestionResult:
    file_path = Path(path)
    if not file_path.exists():
        raise IngestionError(
            file_path=file_path,
            summary="CSV ingestion failed",
            reason="input file was not found",
            fix="Provide an existing .csv or .csv.gz file path",
        )

    header_columns = _read_csv_header(file_path)
    _validate_required_columns(file_path, schema, header_columns)

    include_columns = _resolve_include_columns(schema, header_columns)
    convert_options = pcsv.ConvertOptions(
        column_types={name: schema.field(name).type for name in include_columns},
        include_columns=list(include_columns),
        include_missing_columns=False,
        check_utf8=True,
    )

    try:
        table = pcsv.read_csv(
            file_path,
            read_options=pcsv.ReadOptions(use_threads=True),
            convert_options=convert_options,
        )
    except (pa.ArrowInvalid, pa.ArrowTypeError) as exc:
        mismatches = _detect_csv_type_mismatches(file_path, schema, include_columns)
        reason = str(exc).replace("\n", " ").strip()
        raise IngestionError(
            file_path=file_path,
            summary="CSV ingestion failed",
            reason=reason,
            fix=(
                "Align source values with declared schema types "
                "for all included columns"
            ),
            type_mismatches=mismatches,
        ) from None

    return _build_result(table, file_path, "csv")


def ingest_parquet(path: str | Path, schema: DataSchema) -> IngestionResult:
    file_path = Path(path)
    if not file_path.exists():
        raise IngestionError(
            file_path=file_path,
            summary="Parquet ingestion failed",
            reason="input file was not found",
            fix="Provide an existing .parquet or .pq file path",
        )

    _thrift_limits = {
        "thrift_string_size_limit": 100_000_000,
        "thrift_container_size_limit": 1_000_000,
    }

    pf = pq.ParquetFile(file_path, **_thrift_limits)
    file_schema = pf.schema_arrow
    file_columns = tuple(file_schema.names)

    _validate_required_columns(file_path, schema, file_columns)

    include_columns = _resolve_include_columns(schema, file_columns)
    mismatches = _detect_parquet_type_mismatches(file_schema, schema, include_columns)
    if mismatches:
        mismatch_details = ", ".join(
            (
                f"{m.column}: expected {m.expected_type}, actual {m.actual_type}"
                for m in mismatches
            )
        )
        raise IngestionError(
            file_path=file_path,
            summary="Parquet ingestion failed",
            reason=f"declared schema type mismatch: {mismatch_details}",
            fix="Update file types or declared schema so each column type matches",
            type_mismatches=mismatches,
        )

    projected_schema = pa.schema([schema.field(name) for name in include_columns])
    table = pq.read_table(
        file_path,
        columns=list(include_columns),
        schema=projected_schema,
        **_thrift_limits,
    )

    return _build_result(table, file_path, "parquet")


def ingest(path: str | Path, schema: DataSchema) -> IngestionResult:
    file_path = Path(path)
    suffixes = tuple(part.lower() for part in file_path.suffixes)

    if suffixes[-2:] == (".csv", ".gz") or suffixes[-1:] == (".csv",):
        return ingest_csv(file_path, schema)
    if suffixes[-1:] in ((".parquet",), (".pq",)):
        return ingest_parquet(file_path, schema)

    extension = "".join(file_path.suffixes) or "<none>"
    raise IngestionError(
        file_path=file_path,
        summary="Ingestion failed",
        reason=f"unsupported file extension: {extension}",
        fix="Use one of: .csv, .csv.gz, .parquet, .pq",
    )


def _read_csv_header(path: Path) -> tuple[str, ...]:
    opener = gzip.open if path.suffix.lower() == ".gz" else open

    try:
        with opener(path, "rt", encoding="utf-8", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, None)
    except gzip.BadGzipFile:
        raise IngestionError(
            file_path=path,
            summary="CSV ingestion failed",
            reason="file has .gz extension but is not valid gzip",
            fix="Provide a valid gzip-compressed CSV file",
        ) from None

    return tuple(header or ())


def _resolve_include_columns(
    schema: DataSchema,
    available_columns: tuple[str, ...] | list[str],
) -> tuple[str, ...]:
    declared = set(schema.column_names)
    # Preserve source-file order while restricting to declared columns.
    return tuple(name for name in available_columns if name in declared)


def _validate_required_columns(
    path: Path,
    schema: DataSchema,
    available_columns: tuple[str, ...] | list[str],
) -> None:
    available = set(available_columns)
    missing = tuple(name for name in schema.required_columns if name not in available)
    if missing:
        names = ", ".join(missing)
        raise IngestionError(
            file_path=path,
            summary="Ingestion failed",
            reason=f"missing required columns: {names}",
            fix="Add all required columns to the source file and retry",
            missing_columns=missing,
        )


def _detect_csv_type_mismatches(
    path: Path,
    schema: DataSchema,
    include_columns: tuple[str, ...],
) -> tuple[TypeMismatch, ...]:
    try:
        inferred = pcsv.read_csv(
            path,
            read_options=pcsv.ReadOptions(use_threads=True),
            convert_options=pcsv.ConvertOptions(
                include_columns=list(include_columns),
                include_missing_columns=False,
                check_utf8=True,
            ),
        )
    except (pa.ArrowInvalid, pa.ArrowTypeError):
        # Secondary read also failed — cannot determine per-column types.
        return ()

    mismatches: list[TypeMismatch] = []
    for name in include_columns:
        expected = str(schema.field(name).type)

        if name not in inferred.schema.names:
            continue

        actual = str(inferred.schema.field(name).type)
        if actual != expected:
            mismatches.append(
                TypeMismatch(
                    column=name,
                    expected_type=expected,
                    actual_type=actual,
                )
            )

    return tuple(mismatches)


def _detect_parquet_type_mismatches(
    file_schema: pa.Schema,
    schema: DataSchema,
    include_columns: tuple[str, ...],
) -> tuple[TypeMismatch, ...]:
    mismatches: list[TypeMismatch] = []

    for name in include_columns:
        expected = schema.field(name).type
        actual = file_schema.field(name).type
        if not actual.equals(expected):
            mismatches.append(
                TypeMismatch(
                    column=name,
                    expected_type=str(expected),
                    actual_type=str(actual),
                )
            )

    return tuple(mismatches)


def _build_result(
    table: pa.Table,
    file_path: Path,
    file_format: IngestionFormat,
) -> IngestionResult:
    return IngestionResult(
        table=table,
        source_path=file_path,
        format=file_format,
        row_count=table.num_rows,
        metadata={"loaded_at": datetime.now(UTC).isoformat(timespec="seconds")},
    )
