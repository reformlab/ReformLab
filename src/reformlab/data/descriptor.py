# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Unified dataset descriptor bridging data schemas and source metadata.

Replaces per-provider dataset dataclasses (``INSEEDataset``, ``ADEMEDataset``,
``EurostatDataset``, ``SDESDataset``) with a single ``DatasetDescriptor`` type
that combines schema, metadata, and column mapping in one place.

Every dataset — institutional or user-supplied — can be described declaratively
with a ``DatasetDescriptor``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from reformlab.computation.ingestion import DataSchema


@dataclass(frozen=True)
class DatasetDescriptor:
    """Declarative description of a dataset — schema, metadata, and column mappings.

    Attributes
    ----------
    dataset_id : str
        Unique identifier for the dataset within the provider namespace.
    provider : str
        Data provider identifier (e.g. ``"insee"``, ``"ademe"``, ``"user"``).
    description : str
        Human-readable description of the dataset.
    schema : DataSchema
        Target schema after column renaming (required/optional column semantics).
    url : str
        Download URL. Empty for user-supplied local files.
    license : str
        License identifier (e.g. ``"CC-BY-4.0"``).
    version : str
        Version or vintage identifier (e.g. ``"2021"``, ``"2024-Q1"``).
    column_mapping : tuple[tuple[str, str], ...]
        Raw source column name → project column name. Empty = no renaming.
    encoding : str
        Character encoding for CSV parsing.
    separator : str
        Field separator for CSV parsing.
    null_markers : tuple[str, ...]
        Strings treated as null values during CSV parsing.
    file_format : str
        Source file format: ``"csv"``, ``"zip"``, ``"csv.gz"``, ``"parquet"``.
    skip_rows : int
        Number of header rows to skip before the column name row.
    """

    # Identity
    dataset_id: str
    provider: str
    description: str

    # Schema (uses DataSchema for required/optional semantics)
    schema: DataSchema

    # Source
    url: str = ""
    license: str = ""
    version: str = ""

    # Column mapping (raw source name → project name)
    column_mapping: tuple[tuple[str, str], ...] = ()

    # Parse options
    encoding: str = "utf-8"
    separator: str = ","
    null_markers: tuple[str, ...] = ("",)
    file_format: str = "csv"
    skip_rows: int = 0

    def to_json(self) -> dict[str, Any]:
        """Serialize to a JSON-compatible dict."""
        result: dict[str, Any] = {
            "dataset_id": self.dataset_id,
            "provider": self.provider,
            "description": self.description,
            "schema": self.schema.to_json(),
        }
        if self.url:
            result["url"] = self.url
        if self.license:
            result["license"] = self.license
        if self.version:
            result["version"] = self.version
        if self.column_mapping:
            result["column_mapping"] = [
                [raw, proj] for raw, proj in self.column_mapping
            ]
        if self.encoding != "utf-8":
            result["encoding"] = self.encoding
        if self.separator != ",":
            result["separator"] = self.separator
        if self.null_markers != ("",):
            result["null_markers"] = list(self.null_markers)
        if self.file_format != "csv":
            result["file_format"] = self.file_format
        if self.skip_rows != 0:
            result["skip_rows"] = self.skip_rows
        return result

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> DatasetDescriptor:
        """Deserialize from a JSON-compatible dict."""
        try:
            column_mapping_raw = data.get("column_mapping", [])
            column_mapping = tuple(
                (pair[0], pair[1]) for pair in column_mapping_raw
            )
            null_markers_raw = data.get("null_markers", [""])
            return cls(
                dataset_id=data["dataset_id"],
                provider=data["provider"],
                description=data["description"],
                schema=DataSchema.from_json(data["schema"]),
                url=data.get("url", ""),
                license=data.get("license", ""),
                version=data.get("version", ""),
                column_mapping=column_mapping,
                encoding=data.get("encoding", "utf-8"),
                separator=data.get("separator", ","),
                null_markers=tuple(null_markers_raw),
                file_format=data.get("file_format", "csv"),
                skip_rows=data.get("skip_rows", 0),
            )
        except KeyError as exc:
            msg = f"DatasetDescriptor JSON missing required key: {exc}"
            raise ValueError(msg) from exc
        except (TypeError, IndexError) as exc:
            msg = f"DatasetDescriptor JSON has malformed data: {exc}"
            raise ValueError(msg) from exc
