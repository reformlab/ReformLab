"""Calibration target file loader.

Supports CSV, CSV.GZ, Parquet, YAML, and YML calibration target files.
Dispatches by file extension, validates schema and semantic consistency,
and returns an immutable CalibrationTargetSet.

Format dispatch:
- ``.csv``, ``.csv.gz`` → CSV path via :func:`~reformlab.computation.ingestion.ingest`
- ``.parquet``, ``.pq`` → Parquet path via :func:`~reformlab.computation.ingestion.ingest`
- ``.yaml``, ``.yml`` → YAML path with JSON Schema validation

Story 15.1 / FR52 — Define calibration target format and load observed transition rates.
"""

from __future__ import annotations

import importlib.resources
import json
import logging
import re
from pathlib import Path
from typing import Any

import pyarrow as pa
import yaml

from reformlab.calibration.errors import CalibrationTargetLoadError
from reformlab.calibration.types import CalibrationTarget, CalibrationTargetSet
from reformlab.computation.ingestion import DataSchema, IngestionError, ingest

logger = logging.getLogger(__name__)

# ============================== Schema Definition ==============================

CALIBRATION_TARGET_SCHEMA = DataSchema(
    schema=pa.schema(
        [
            pa.field("domain", pa.utf8()),
            pa.field("period", pa.int64()),
            pa.field("from_state", pa.utf8()),
            pa.field("to_state", pa.utf8()),
            pa.field("observed_rate", pa.float64()),
            pa.field("source_label", pa.utf8()),
        ]
    ),
    required_columns=("domain", "period", "from_state", "to_state", "observed_rate", "source_label"),
    optional_columns=(),
)

# ============================== JSON Schema Cache ==============================

_SCHEMA_CACHE: dict[str, Any] | None = None


def _get_schema_validator() -> Any:
    """Load and cache the jsonschema Draft202012Validator for YAML target files.

    Loads the bundled JSON Schema file via ``importlib.resources`` to support
    both development (editable install) and packaged (wheel) execution.

    Raises:
        CalibrationTargetLoadError: If ``jsonschema`` is not installed.
    """
    global _SCHEMA_CACHE

    try:
        import jsonschema
    except ImportError as exc:
        raise CalibrationTargetLoadError(
            "jsonschema is required for YAML calibration target validation; "
            "install it with: pip install jsonschema"
        ) from exc

    if _SCHEMA_CACHE is None:
        schema_text = (
            importlib.resources.files("reformlab.calibration.schema")
            .joinpath("calibration-targets.schema.json")
            .read_text(encoding="utf-8")
        )
        _SCHEMA_CACHE = json.loads(schema_text)

    return jsonschema.Draft202012Validator(_SCHEMA_CACHE)


# ============================== Helper Functions ==============================


def _extract_row_from_message(message: str) -> str | None:
    """Try to extract a 0-based row number from a PyArrow CSV error message.

    PyArrow type-conversion errors contain ``'Row #N'`` where N is 1-based.
    Returns ``'row=N'`` (0-based) if found, else ``None``.
    """
    match = re.search(r"Row #(\d+)", message)
    if match:
        row_0based = int(match.group(1)) - 1
        return f"row={row_0based}"
    return None


def _format_yaml_error(err: Any, path: Path) -> CalibrationTargetLoadError:
    """Translate a jsonschema ValidationError into a CalibrationTargetLoadError.

    Produces error messages in the form:
    ``field={field!r} location={location!r} file={path!r}: {message}``

    Location formats:
    - ``targets[N].field_name`` — error on a specific target item field
    - ``field_name`` — top-level or unknown location
    """
    abs_path = list(err.absolute_path)

    # Case 1: Type/value error on targets[N].field
    if len(abs_path) >= 3 and abs_path[0] == "targets":
        idx = abs_path[1]
        field_name = str(abs_path[2])
        location = f"targets[{idx}].{field_name}"
        return CalibrationTargetLoadError(
            f"field={field_name!r} location={location!r} file={str(path)!r}: {err.message}"
        )

    # Case 2: Required property missing on targets[N] item
    if len(abs_path) >= 2 and abs_path[0] == "targets" and err.validator == "required":
        idx = abs_path[1]
        prop_match = re.search(r"'([^']+)' is a required property", err.message)
        field_name = prop_match.group(1) if prop_match else "unknown"
        location = f"targets[{idx}].{field_name}"
        return CalibrationTargetLoadError(
            f"field={field_name!r} location={location!r} file={str(path)!r}: {err.message}"
        )

    # Case 3: Top-level schema error (e.g., missing 'targets' key)
    field_name = str(abs_path[-1]) if abs_path else "targets"
    return CalibrationTargetLoadError(
        f"field={field_name!r} location={field_name!r} file={str(path)!r}: {err.message}"
    )


# ============================== Table Conversion ==============================


def _table_to_target_set(table: pa.Table, path: Path) -> CalibrationTargetSet:
    """Convert a PyArrow table (from CSV or Parquet) into a CalibrationTargetSet.

    Rows are converted one-by-one so that conversion errors report their 0-based
    row index in the CalibrationTargetLoadError message.
    """
    n_rows = table.num_rows

    domain_col: list[str] = table.column("domain").to_pylist()
    period_col: list[int] = table.column("period").to_pylist()
    from_state_col: list[str] = table.column("from_state").to_pylist()
    to_state_col: list[str] = table.column("to_state").to_pylist()
    observed_rate_col: list[float] = table.column("observed_rate").to_pylist()
    source_label_col: list[str] = table.column("source_label").to_pylist()

    targets: list[CalibrationTarget] = []
    for row in range(n_rows):
        try:
            target = CalibrationTarget(
                domain=domain_col[row],
                period=int(period_col[row]),
                from_state=from_state_col[row],
                to_state=to_state_col[row],
                observed_rate=float(observed_rate_col[row]),
                source_label=source_label_col[row],
            )
        except Exception as exc:
            raise CalibrationTargetLoadError(
                f"field='row' location='row={row}' file={str(path)!r}: {exc}"
            ) from exc
        targets.append(target)

    return CalibrationTargetSet(targets=tuple(targets))


# ============================== Format-Specific Loaders ==============================


def _load_tabular(path: Path) -> CalibrationTargetSet:
    """Load calibration targets from a CSV, CSV.GZ, or Parquet file.

    Uses :func:`~reformlab.computation.ingestion.ingest` for schema-validated
    tabular loading via PyArrow.

    Raises:
        CalibrationTargetLoadError: On missing columns or type/parse errors.
    """
    try:
        result = ingest(path, CALIBRATION_TARGET_SCHEMA)
    except IngestionError as exc:
        if exc.missing_columns:
            field_name = exc.missing_columns[0]
            raise CalibrationTargetLoadError(
                f"field={field_name!r} location='column' file={str(path)!r}: "
                "missing required column"
            ) from exc

        # Type or parse error — try to extract row info from the error message
        field_name = exc.type_mismatches[0].column if exc.type_mismatches else "unknown"
        msg = str(exc)
        location = _extract_row_from_message(msg) or "row=unknown"
        raise CalibrationTargetLoadError(
            f"field={field_name!r} location={location!r} file={str(path)!r}: {exc}"
        ) from exc

    return _table_to_target_set(result.table, path)


def _load_yaml(path: Path) -> CalibrationTargetSet:
    """Load calibration targets from a YAML or YML file.

    Validates the raw document against the bundled JSON Schema before
    constructing CalibrationTarget objects.

    Raises:
        CalibrationTargetLoadError: On YAML parse errors or schema violations.
    """
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CalibrationTargetLoadError(
            f"field='unknown' location='file' file={str(path)!r}: YAML parse error: {exc}"
        ) from exc

    validator = _get_schema_validator()
    errors = list(validator.iter_errors(raw))
    if errors:
        raise _format_yaml_error(errors[0], path)

    raw_targets: list[dict[str, Any]] = raw.get("targets", [])
    targets: list[CalibrationTarget] = []
    for idx, item in enumerate(raw_targets):
        try:
            target = CalibrationTarget(
                domain=item["domain"],
                period=int(item["period"]),
                from_state=item["from_state"],
                to_state=item["to_state"],
                observed_rate=float(item["observed_rate"]),
                source_label=item["source_label"],
                source_metadata=dict(item.get("source_metadata") or {}),
            )
        except Exception as exc:
            raise CalibrationTargetLoadError(
                f"field='unknown' location='targets[{idx}]' file={str(path)!r}: {exc}"
            ) from exc
        targets.append(target)

    return CalibrationTargetSet(targets=tuple(targets))


# ============================== Public API ==============================


def load_calibration_targets(path: Path) -> CalibrationTargetSet:
    """Load calibration targets from a file and return a validated CalibrationTargetSet.

    Dispatches to the appropriate loader based on the file extension, then
    calls :meth:`CalibrationTargetSet.validate_consistency` before returning.

    Supported formats:
    - ``.csv``, ``.csv.gz`` — CSV with required columns per CALIBRATION_TARGET_SCHEMA
    - ``.parquet``, ``.pq`` — Parquet with the same column contract
    - ``.yaml``, ``.yml`` — YAML validated against calibration-targets.schema.json

    Args:
        path: Path to the calibration target file.

    Returns:
        A validated, immutable :class:`CalibrationTargetSet`.

    Raises:
        CalibrationTargetLoadError: If the file cannot be read, parsed, or has
            structural errors (missing columns, schema violations, duplicate rows,
            unsupported extension).
        CalibrationTargetValidationError: If rate sums exceed 1.0 + 1e-9 for any
            ``(domain, period, from_state)`` group.
    """
    path = Path(path)
    suffixes = tuple(part.lower() for part in path.suffixes)

    if suffixes[-2:] == (".csv", ".gz") or suffixes[-1:] == (".csv",):
        target_set = _load_tabular(path)
    elif suffixes[-1:] in ((".parquet",), (".pq",)):
        target_set = _load_tabular(path)
    elif suffixes[-1:] in ((".yaml",), (".yml",)):
        target_set = _load_yaml(path)
    else:
        extension = "".join(path.suffixes) or "<none>"
        raise CalibrationTargetLoadError(
            f"field='format' location='file' file={str(path)!r}: "
            f"unsupported file extension {extension!r}; "
            "supported: .csv, .csv.gz, .parquet, .pq, .yaml, .yml"
        )

    target_set.validate_consistency()

    logger.info(
        "event=targets_loaded file=%s n_targets=%d",
        path,
        len(target_set.targets),
    )
    return target_set
