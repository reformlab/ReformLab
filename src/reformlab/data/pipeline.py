# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import gettempdir
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from reformlab.computation.ingestion import (
    DataSchema,
    IngestionError,
    IngestionFormat,
    ingest,
)
from reformlab.computation.types import PopulationData
from reformlab.data.errors import EvidenceAssetError

if TYPE_CHECKING:
    from reformlab.data.descriptor import DataAssetDescriptor
else:
    from reformlab.data.descriptor import DataAssetDescriptor


@dataclass(frozen=True)
class DataSourceMetadata:
    """Immutable metadata describing the origin of an open-data dataset."""

    name: str
    version: str
    url: str
    description: str
    license: str = ""

    def to_json(self) -> dict[str, str]:
        """Serialize to a JSON-compatible dict."""
        result: dict[str, str] = {
            "name": self.name,
            "version": self.version,
            "url": self.url,
            "description": self.description,
        }
        if self.license:
            result["license"] = self.license
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> DataSourceMetadata:
        """Deserialize from a JSON-compatible dict."""
        try:
            return cls(
                name=data["name"],
                version=data["version"],
                url=data["url"],
                description=data["description"],
                license=data.get("license", ""),
            )
        except KeyError as exc:
            msg = f"DataSourceMetadata JSON missing required key: {exc}"
            raise ValueError(msg) from exc


@dataclass(frozen=True)
class DatasetManifest:
    """Immutable record of a loaded dataset with provenance."""

    source: DataSourceMetadata
    content_hash: str
    file_path: Path
    format: IngestionFormat
    row_count: int
    column_names: tuple[str, ...]
    loaded_at: str

    @property
    def dataset_key(self) -> str:
        """Unique key: ``{source.name}@{source.version}:{content_hash[:12]}``."""
        return f"{self.source.name}@{self.source.version}:{self.content_hash[:12]}"

    def __repr__(self) -> str:
        return (
            f"DatasetManifest(key={self.dataset_key!r}, "
            f"format={self.format!r}, "
            f"rows={self.row_count}, "
            f"cols={len(self.column_names)})"
        )


class DatasetRegistry:
    """Mutable registry of loaded dataset manifests.

    Append-only by unique ``dataset_key``.  Duplicate keys raise ``ValueError``.
    """

    def __init__(self) -> None:
        self._entries: dict[str, DatasetManifest] = {}

    def register(self, manifest: DatasetManifest) -> None:
        """Register a manifest.  Raises ``ValueError`` on duplicate key."""
        key = manifest.dataset_key
        if key in self._entries:
            raise ValueError(
                f"Dataset key already registered: {key} — "
                "each dataset_key must be unique within the registry"
            )
        self._entries[key] = manifest

    def get(self, dataset_key: str) -> DatasetManifest | None:
        """Return manifest for *dataset_key*, or ``None`` if not found."""
        return self._entries.get(dataset_key)

    def all(self) -> tuple[DatasetManifest, ...]:
        """Return all registered manifests."""
        return tuple(self._entries.values())

    def find_by_source(self, source_name: str) -> tuple[DatasetManifest, ...]:
        """Return all manifests whose source name matches *source_name*."""
        return tuple(
            m for m in self._entries.values() if m.source.name == source_name
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize registry to a JSON-compatible dict for manifest inclusion."""
        return {
            key: {
                "source": {
                    "name": m.source.name,
                    "version": m.source.version,
                    "url": m.source.url,
                    "description": m.source.description,
                    "license": m.source.license,
                },
                "content_hash": m.content_hash,
                "file_path": str(m.file_path),
                "format": m.format,
                "row_count": m.row_count,
                "column_names": list(m.column_names),
                "loaded_at": m.loaded_at,
            }
            for key, m in self._entries.items()
        }


def hash_file(path: Path) -> str:
    """Compute SHA-256 hex digest of a file using chunked reads."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def load_dataset(
    path: str | Path,
    schema: DataSchema,
    source: DataSourceMetadata,
    *,
    allowed_roots: tuple[Path, ...] | None = None,
) -> tuple[pa.Table, DatasetManifest]:
    """Load a dataset file with schema validation, hashing, and metadata tracking.

    Returns ``(table, manifest)`` on success.  Raises ``IngestionError`` on failure.
    """
    file_path = Path(path).expanduser().resolve()

    # Path safety policy
    if allowed_roots is None:
        allowed_roots = (Path.cwd().resolve(), Path(gettempdir()).resolve())

    if not file_path.exists():
        raise IngestionError(
            file_path=file_path,
            summary="Dataset load failed",
            reason="input file was not found",
            fix="Provide an existing dataset file path",
        )

    if not file_path.is_file():
        raise IngestionError(
            file_path=file_path,
            summary="Dataset load failed",
            reason="path is not a regular file",
            fix="Provide a path to a regular file, not a directory or special file",
        )

    if not any(
        _is_subpath(file_path, root.resolve()) for root in allowed_roots
    ):
        raise IngestionError(
            file_path=file_path,
            summary="Dataset load failed",
            reason=(
                "file path is outside allowed roots: "
                f"{', '.join(str(r) for r in allowed_roots)}"
            ),
            fix=(
                "Move the dataset file to a location within "
                "the allowed roots, or specify allowed_roots"
            ),
        )

    # Compute content hash before ingestion
    try:
        content_hash = hash_file(file_path)
    except OSError as exc:
        reason = exc.strerror or str(exc)
        raise IngestionError(
            file_path=file_path,
            summary="Dataset load failed",
            reason=f"unable to read file for hashing: {reason}",
            fix="Ensure the file is readable and retry",
        ) from None

    # Delegate to existing ingestion infrastructure
    result = ingest(file_path, schema)

    # Build manifest
    manifest = DatasetManifest(
        source=source,
        content_hash=content_hash,
        file_path=file_path,
        format=result.format,
        row_count=result.row_count,
        column_names=tuple(result.table.schema.names),
        loaded_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )

    return result.table, manifest


def load_population(
    path: str | Path,
    schema: DataSchema,
    source: DataSourceMetadata,
    *,
    allowed_roots: tuple[Path, ...] | None = None,
) -> PopulationData:
    """Load a dataset and wrap it as :class:`PopulationData`.

    Convenience wrapper around :func:`load_dataset` +
    :meth:`PopulationData.from_table`.
    """
    table, _manifest = load_dataset(path, schema, source, allowed_roots=allowed_roots)
    entity_type = source.name if source.name and source.name.isidentifier() else "default"
    return PopulationData.from_table(table, entity_type=entity_type)


def load_population_folder(
    path: str | Path,
    *,
    allowed_roots: tuple[Path, ...] | None = None,
) -> tuple[PopulationData, DatasetManifest]:
    """Load a dataset from a folder containing data + JSON metadata.

    Expects a folder layout::

        my-dataset/
        ├── data.csv          # or data.parquet
        ├── schema.json       # DataSchema as JSON
        └── descriptor.json   # DataAssetDescriptor as JSON (preferred)
        # OR legacy:
        └── source.json       # DataSourceMetadata as JSON (fallback)

    Story 21.4 / AC2: If ``descriptor.json`` exists, it is used for
    governance metadata. Otherwise, falls back to legacy ``source.json``.
    If ``schema.json`` is missing, raises ``IngestionError``.
    If no data file is found, raises ``IngestionError``.

    Returns ``(PopulationData, DatasetManifest)``.
    """
    folder = Path(path).expanduser().resolve()

    if not folder.is_dir():
        raise IngestionError(
            file_path=folder,
            summary="Folder load failed",
            reason="path is not a directory",
            fix="Provide a path to a folder containing data + schema.json + descriptor.json (or source.json)",
        )

    # Validate folder against allowed_roots before reading any files
    if allowed_roots is not None:
        if not any(_is_subpath(folder, root.resolve()) for root in allowed_roots):
            raise IngestionError(
                file_path=folder,
                summary="Folder load failed",
                reason=f"folder {folder} is outside all allowed roots",
                fix="Add the folder's parent directory to allowed_roots",
            )

    # Locate schema.json
    schema_path = folder / "schema.json"
    if not schema_path.is_file():
        raise IngestionError(
            file_path=folder,
            summary="Folder load failed",
            reason="schema.json not found in folder",
            fix="Add a schema.json file describing the data columns",
        )

    # Story 21.4 / AC2: Check for descriptor.json first, fallback to source.json
    descriptor_path = folder / "descriptor.json"
    source_path = folder / "source.json"

    # Try descriptor.json first (new format)
    if descriptor_path.is_file():
        # Read and validate descriptor.json
        try:
            descriptor_data = json.loads(descriptor_path.read_text(encoding="utf-8"))
            _descriptor = DataAssetDescriptor.from_json(descriptor_data)
        except (json.JSONDecodeError, ValueError, KeyError, EvidenceAssetError) as exc:
            raise IngestionError(
                file_path=descriptor_path,
                summary="Folder load failed",
                reason=f"invalid descriptor.json: {exc}",
                fix="Fix the descriptor.json file (must be valid DataAssetDescriptor JSON)",
            ) from exc

        # Build DataSourceMetadata from descriptor for backward compatibility
        source = DataSourceMetadata(
            name=_descriptor.asset_id,
            version=_descriptor.version,
            url=_descriptor.source_url,
            description=_descriptor.description,
            license=_descriptor.license,
        )
    # Fallback to source.json (legacy format)
    elif source_path.is_file():
        try:
            source_data = json.loads(source_path.read_text(encoding="utf-8"))
            source = DataSourceMetadata.from_json(source_data)
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            raise IngestionError(
                file_path=source_path,
                summary="Folder load failed",
                reason=f"invalid source.json: {exc}",
                fix="Fix the source.json file (required keys: name, version, url, description)",
            ) from exc
    else:
        raise IngestionError(
            file_path=folder,
            summary="Folder load failed",
            reason="neither descriptor.json nor source.json found in folder",
            fix=(
                "Add a descriptor.json (preferred) or source.json (legacy) "
                "file describing the data source metadata"
            ),
        )

    # Read and parse schema.json
    try:
        schema_data = json.loads(schema_path.read_text(encoding="utf-8"))
        schema = DataSchema.from_json(schema_data)
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        raise IngestionError(
            file_path=schema_path,
            summary="Folder load failed",
            reason=f"invalid schema.json: {exc}",
            fix="Fix the schema.json file (expected format: "
            '{"columns": [{"name": str, "type": str, "required": bool}]})',
        ) from exc

    # Find data file: prefer data.csv / data.parquet, else single CSV/Parquet in folder
    data_file = _find_data_file(folder)

    # Delegate to load_dataset
    table, manifest = load_dataset(
        data_file, schema, source, allowed_roots=allowed_roots,
    )

    entity_type = source.name if source.name and source.name.isidentifier() else "default"
    population = PopulationData.from_table(table, entity_type=entity_type)
    return population, manifest


def _find_data_file(folder: Path) -> Path:
    """Find the data file in a dataset folder.

    Prefers ``data.csv`` or ``data.parquet``, else the single CSV/Parquet
    file in the folder.
    """
    for name in ("data.csv", "data.parquet"):
        candidate = folder / name
        if candidate.is_file():
            return candidate

    # Fallback: find the single CSV or Parquet file
    data_files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in (".csv", ".parquet", ".pq")
    ]
    if len(data_files) == 1:
        return data_files[0]
    if len(data_files) == 0:
        raise IngestionError(
            file_path=folder,
            summary="Folder load failed",
            reason="no data file (CSV or Parquet) found in folder",
            fix="Add a data.csv or data.parquet file to the folder",
        )
    names = ", ".join(f.name for f in sorted(data_files))
    raise IngestionError(
        file_path=folder,
        summary="Folder load failed",
        reason=f"multiple data files found: {names}",
        fix="Rename the target file to data.csv or data.parquet",
    )


def _is_subpath(path: Path, root: Path) -> bool:
    """Check if *path* is under *root* (both must be resolved)."""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
