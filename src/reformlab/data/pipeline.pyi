from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow as pa

from reformlab.computation.ingestion import (
    DataSchema,
    IngestionFormat,
)

@dataclass(frozen=True)
class DataSourceMetadata:
    name: str
    version: str
    url: str
    description: str
    license: str = ...

@dataclass(frozen=True)
class DatasetManifest:
    source: DataSourceMetadata
    content_hash: str
    file_path: Path
    format: IngestionFormat
    row_count: int
    column_names: tuple[str, ...]
    loaded_at: str

    @property
    def dataset_key(self) -> str: ...

class DatasetRegistry:
    def __init__(self) -> None: ...
    def register(self, manifest: DatasetManifest) -> None: ...
    def get(
        self, dataset_key: str
    ) -> DatasetManifest | None: ...
    def all(self) -> tuple[DatasetManifest, ...]: ...
    def find_by_source(
        self, source_name: str
    ) -> tuple[DatasetManifest, ...]: ...
    def to_dict(self) -> dict[str, Any]: ...

def hash_file(path: Path) -> str: ...
def load_dataset(
    path: str | Path,
    schema: DataSchema,
    source: DataSourceMetadata,
    *,
    allowed_roots: tuple[Path, ...] | None = ...,
) -> tuple[pa.Table, DatasetManifest]: ...
