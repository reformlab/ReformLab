from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, TypeAlias

import pyarrow as pa

IngestionFormat: TypeAlias = Literal["csv", "parquet"]

@dataclass(frozen=True)
class DataSchema:
    schema: pa.Schema
    required_columns: tuple[str, ...]
    optional_columns: tuple[str, ...] = ...

    @property
    def column_names(self) -> tuple[str, ...]: ...
    def field(self, name: str) -> pa.Field: ...
    def to_json(self) -> dict[str, Any]: ...
    @classmethod
    def from_json(cls, data: dict[str, Any]) -> DataSchema: ...

@dataclass(frozen=True)
class TypeMismatch:
    column: str
    expected_type: str
    actual_type: str

@dataclass(frozen=True)
class IngestionResult:
    table: pa.Table
    source_path: Path
    format: IngestionFormat
    row_count: int
    metadata: dict[str, Any] = ...

class IngestionError(Exception):
    file_path: Path
    missing_columns: tuple[str, ...]
    type_mismatches: tuple[TypeMismatch, ...]

    def __init__(
        self,
        *,
        file_path: Path,
        summary: str,
        reason: str,
        fix: str,
        missing_columns: tuple[str, ...] = (),
        type_mismatches: tuple[TypeMismatch, ...] = (),
    ) -> None: ...

DEFAULT_OPENFISCA_OUTPUT_SCHEMA: DataSchema

def ingest_csv(path: str | Path, schema: DataSchema) -> IngestionResult: ...
def ingest_parquet(path: str | Path, schema: DataSchema) -> IngestionResult: ...
def ingest(path: str | Path, schema: DataSchema) -> IngestionResult: ...
