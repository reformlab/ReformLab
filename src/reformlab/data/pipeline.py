from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from tempfile import gettempdir
from typing import Any

import pyarrow as pa

from reformlab.computation.ingestion import (
    DataSchema,
    IngestionError,
    IngestionFormat,
    ingest,
)


@dataclass(frozen=True)
class DataSourceMetadata:
    """Immutable metadata describing the origin of an open-data dataset."""

    name: str
    version: str
    url: str
    description: str
    license: str = ""


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


def _is_subpath(path: Path, root: Path) -> bool:
    """Check if *path* is under *root* (both must be resolved)."""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
