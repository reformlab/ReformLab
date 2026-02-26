from __future__ import annotations

import difflib
import logging
from dataclasses import dataclass
from pathlib import Path
from tempfile import gettempdir
from typing import Literal

import pyarrow as pa
import yaml

logger = logging.getLogger(__name__)

_PA_TYPE_MAP: dict[str, pa.DataType] = {
    "int8": pa.int8(),
    "int16": pa.int16(),
    "int32": pa.int32(),
    "int64": pa.int64(),
    "float16": pa.float16(),
    "float32": pa.float32(),
    "float64": pa.float64(),
    "string": pa.utf8(),
    "utf8": pa.utf8(),
    "bool": pa.bool_(),
    "boolean": pa.bool_(),
}

_VALID_DIRECTIONS = frozenset({"input", "output", "both"})
_REQUIRED_ENTRY_KEYS = frozenset({"openfisca_name", "project_name", "direction"})
_REQUIRED_TOP_KEYS = frozenset({"version", "mappings"})


# ---------------------------------------------------------------------------
# Data types (Task 1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FieldMapping:
    """A single mapping between an OpenFisca variable and a project schema field."""

    openfisca_name: str
    project_name: str
    direction: Literal["input", "output", "both"]
    pa_type: pa.DataType
    description: str = ""


@dataclass(frozen=True)
class MappingConfig:
    """Collection of field mappings with lookup helpers."""

    mappings: tuple[FieldMapping, ...]
    source_path: Path | None = None

    def by_openfisca_name(self, name: str) -> FieldMapping | None:
        """Find mapping by OpenFisca variable name."""
        for fm in self.mappings:
            if fm.openfisca_name == name:
                return fm
        return None

    def by_project_name(self, name: str) -> FieldMapping | None:
        """Find mapping by project schema field name."""
        for fm in self.mappings:
            if fm.project_name == name:
                return fm
        return None

    @property
    def input_mappings(self) -> tuple[FieldMapping, ...]:
        """Mappings applicable to input direction (input or both)."""
        return tuple(fm for fm in self.mappings if fm.direction in ("input", "both"))

    @property
    def output_mappings(self) -> tuple[FieldMapping, ...]:
        """Mappings applicable to output direction (output or both)."""
        return tuple(fm for fm in self.mappings if fm.direction in ("output", "both"))


class MappingError(Exception):
    """Structured mapping error following IngestionError pattern."""

    def __init__(
        self,
        *,
        file_path: Path,
        summary: str,
        reason: str,
        fix: str,
        invalid_fields: tuple[str, ...] = (),
    ) -> None:
        self.file_path = file_path
        self.invalid_fields = invalid_fields

        message = f"{summary} - {reason} - {fix} (file: {file_path})"
        super().__init__(message)


@dataclass(frozen=True)
class MappingValidationResult:
    """Result of validating a mapping against actual data columns."""

    warnings: tuple[str, ...]
    errors: tuple[str, ...]


# ---------------------------------------------------------------------------
# YAML loader (Task 2)
# ---------------------------------------------------------------------------


def load_mapping(path: str | Path) -> MappingConfig:
    """Load a YAML mapping configuration file and return a validated MappingConfig."""
    input_path = Path(path)
    file_path = _resolve_mapping_path(input_path)

    if not file_path.exists():
        raise MappingError(
            file_path=file_path,
            summary="Mapping load failed",
            reason="mapping file was not found",
            fix="Provide an existing .yaml or .yml mapping file path",
        )

    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise MappingError(
            file_path=file_path,
            summary="Mapping load failed",
            reason=f"invalid YAML syntax: {exc}",
            fix="Fix the YAML syntax errors in the mapping file",
        ) from None

    if not isinstance(data, dict):
        raise MappingError(
            file_path=file_path,
            summary="Mapping load failed",
            reason=(
                "mapping file must contain a YAML mapping (dict), not a scalar or list"
            ),
            fix="Ensure the file has top-level keys: version, mappings",
        )

    # Check required top-level keys
    missing_top = _REQUIRED_TOP_KEYS - set(data.keys())
    if missing_top:
        names = ", ".join(sorted(missing_top))
        raise MappingError(
            file_path=file_path,
            summary="Mapping load failed",
            reason=f"missing required top-level keys: {names}",
            fix=f"Add the following keys to the mapping file: {names}",
            invalid_fields=tuple(sorted(missing_top)),
        )

    raw_mappings = data["mappings"]
    if not isinstance(raw_mappings, list):
        raise MappingError(
            file_path=file_path,
            summary="Mapping load failed",
            reason="'mappings' must be a list of mapping entries",
            fix="Ensure 'mappings' is a YAML list (- item syntax)",
        )

    errors: list[str] = []
    field_mappings: list[FieldMapping] = []

    for i, entry in enumerate(raw_mappings):
        if not isinstance(entry, dict):
            errors.append(
                f"Entry {i + 1}: must be a mapping (dict), got {type(entry).__name__}"
            )
            continue

        # Check required entry keys
        missing_keys = _REQUIRED_ENTRY_KEYS - set(entry.keys())
        if missing_keys:
            names = ", ".join(sorted(missing_keys))
            errors.append(f"Entry {i + 1}: missing required keys: {names}")
            continue

        direction = entry["direction"]
        if direction not in _VALID_DIRECTIONS:
            errors.append(
                f"Entry {i + 1} ({entry['openfisca_name']}): "
                f"invalid direction '{direction}', must be one of: input, output, both"
            )
            continue

        # Resolve type string
        type_str = entry.get("type")
        if type_str is not None:
            pa_type = _PA_TYPE_MAP.get(str(type_str))
            if pa_type is None:
                valid_types = ", ".join(sorted(_PA_TYPE_MAP.keys()))
                errors.append(
                    f"Entry {i + 1} ({entry['openfisca_name']}): "
                    f"unknown type '{type_str}', valid types: {valid_types}"
                )
                continue
        else:
            pa_type = pa.utf8()

        field_mappings.append(
            FieldMapping(
                openfisca_name=str(entry["openfisca_name"]),
                project_name=str(entry["project_name"]),
                direction=direction,
                pa_type=pa_type,
                description=str(entry.get("description", "")),
            )
        )

    # Check for duplicates
    seen_openfisca: dict[str, int] = {}
    seen_project: dict[str, int] = {}
    for i, fm in enumerate(field_mappings):
        if fm.openfisca_name in seen_openfisca:
            errors.append(
                f"Duplicate openfisca_name '{fm.openfisca_name}' "
                f"in entries {seen_openfisca[fm.openfisca_name]} and {i + 1}"
            )
        else:
            seen_openfisca[fm.openfisca_name] = i + 1

        if fm.project_name in seen_project:
            errors.append(
                f"Duplicate project_name '{fm.project_name}' "
                f"in entries {seen_project[fm.project_name]} and {i + 1}"
            )
        else:
            seen_project[fm.project_name] = i + 1

    if errors:
        all_errors = "; ".join(errors)
        raise MappingError(
            file_path=file_path,
            summary="Mapping validation failed",
            reason=all_errors,
            fix="Fix all listed errors in the mapping file",
            invalid_fields=tuple(e.split(":")[0] for e in errors),
        )

    return MappingConfig(
        mappings=tuple(field_mappings),
        source_path=file_path,
    )


# ---------------------------------------------------------------------------
# Mapping application (Task 3)
# ---------------------------------------------------------------------------


def _rename_table(
    table: pa.Table,
    rename_map: dict[str, str],
    type_map: dict[str, pa.DataType] | None = None,
) -> pa.Table:
    """Rename columns in a table, preserving schema metadata."""
    new_names = [rename_map.get(name, name) for name in table.column_names]
    renamed = table.rename_columns(new_names)
    if type_map:
        renamed = _coerce_column_types(renamed, type_map)
    if table.schema.metadata:
        renamed = renamed.replace_schema_metadata(table.schema.metadata)
    return renamed


def apply_output_mapping(table: pa.Table, config: MappingConfig) -> pa.Table:
    """Rename OpenFisca columns to project names (output direction).

    Columns not in the mapping are passed through unchanged.
    """
    rename_map: dict[str, str] = {}
    type_map: dict[str, pa.DataType] = {}
    for mapping in config.output_mappings:
        rename_map[mapping.openfisca_name] = mapping.project_name
        type_map[mapping.project_name] = mapping.pa_type
    return _rename_table(table, rename_map, type_map)


def apply_input_mapping(table: pa.Table, config: MappingConfig) -> pa.Table:
    """Rename project columns to OpenFisca names (input direction).

    Columns not in the mapping are passed through unchanged.
    """
    rename_map: dict[str, str] = {}
    type_map: dict[str, pa.DataType] = {}
    for mapping in config.input_mappings:
        rename_map[mapping.project_name] = mapping.openfisca_name
        type_map[mapping.openfisca_name] = mapping.pa_type
    return _rename_table(table, rename_map, type_map)


# ---------------------------------------------------------------------------
# Mapping validation against data (Task 4)
# ---------------------------------------------------------------------------


def validate_mapping(
    config: MappingConfig,
    available_columns: tuple[str, ...],
) -> MappingValidationResult:
    """Validate that output-mapped OpenFisca names exist in available columns.

    Unknown variables produce errors with closest-match suggestions.
    All unknowns are reported at once.
    """
    available_set = set(available_columns)
    errors: list[str] = []
    warnings: list[str] = []

    for fm in config.output_mappings:
        if fm.openfisca_name not in available_set:
            close = difflib.get_close_matches(
                fm.openfisca_name,
                list(available_columns),
                n=3,
                cutoff=0.5,
            )
            suggestion = f" Did you mean: {', '.join(close)}?" if close else ""
            errors.append(
                f"Unknown OpenFisca variable '{fm.openfisca_name}' "
                f"not found in available columns.{suggestion}"
            )

    return MappingValidationResult(
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


# ---------------------------------------------------------------------------
# Mapping composition (Task 5)
# ---------------------------------------------------------------------------


def merge_mappings(*configs: MappingConfig) -> MappingConfig:
    """Merge multiple MappingConfigs; later configs override earlier by openfisca_name.

    Conflicts (same openfisca_name in multiple configs) are logged as warnings.
    """
    merged: dict[str, FieldMapping] = {}
    sources: dict[str, str] = {}

    for config in configs:
        source_label = str(config.source_path) if config.source_path else "<unknown>"
        for fm in config.mappings:
            if fm.openfisca_name in merged:
                logger.warning(
                    "Merge conflict: openfisca_name '%s' from '%s' overridden by "
                    "'%s' (project_name: '%s' -> '%s')",
                    fm.openfisca_name,
                    sources[fm.openfisca_name],
                    source_label,
                    merged[fm.openfisca_name].project_name,
                    fm.project_name,
                )
            merged[fm.openfisca_name] = fm
            sources[fm.openfisca_name] = source_label

    return MappingConfig(mappings=tuple(merged.values()))


def load_mappings(*paths: str | Path) -> MappingConfig:
    """Load multiple YAML mapping files and merge them.

    Later files override earlier ones by openfisca_name.
    """
    configs = tuple(load_mapping(p) for p in paths)
    return merge_mappings(*configs)


def _coerce_column_types(
    table: pa.Table,
    type_map: dict[str, pa.DataType],
) -> pa.Table:
    """Cast mapped columns to declared types when current type differs."""
    coerced = table
    for index, name in enumerate(coerced.column_names):
        expected = type_map.get(name)
        if expected is None:
            continue
        current = coerced.schema.field(name).type
        if current.equals(expected):
            continue
        try:
            casted = coerced.column(index).cast(expected)
        except (pa.ArrowInvalid, pa.ArrowTypeError) as exc:
            raise MappingError(
                file_path=Path("<in-memory>"),
                summary="Mapping application failed",
                reason=(
                    "column "
                    f"'{name}' cannot be cast from {current} to {expected}: {exc}"
                ),
                fix=(
                    "Update mapping type definitions or input values so mapped fields "
                    "can be cast safely"
                ),
            ) from None
        coerced = coerced.set_column(index, name, casted)
    return coerced


def _resolve_mapping_path(path: Path) -> Path:
    """Resolve and validate mapping path to reduce traversal risk."""
    resolved = path.expanduser().resolve(strict=False)
    allowed_roots = _allowed_mapping_roots()
    if any(_is_within(resolved, root) for root in allowed_roots):
        return resolved

    roots = ", ".join(str(root) for root in allowed_roots)
    raise MappingError(
        file_path=resolved,
        summary="Mapping load failed",
        reason=f"path is outside allowed mapping directories: {resolved}",
        fix=f"Move the mapping file under one of: {roots}",
    )


def _allowed_mapping_roots() -> tuple[Path, ...]:
    """Return directories where mapping files are allowed by default."""
    roots: list[Path] = []
    for candidate in (Path.cwd(), Path(gettempdir())):
        resolved = candidate.resolve()
        if resolved not in roots:
            roots.append(resolved)
    return tuple(roots)


def _is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents
