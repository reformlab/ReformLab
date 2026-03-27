# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Population dataset listing and explorer routes — Story 20.7."""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

import pyarrow as pa
import pyarrow.compute as pc
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from reformlab.server.dependencies import get_result_store
from reformlab.server.models import (
    ColumnProfile,
    ColumnProfileBoolean,
    ColumnProfileCategorical,
    ColumnProfileEntry,
    ColumnProfileNumeric,
    PopulationCrosstabResponse,
    PopulationLibraryItem,
    PopulationPreviewColumnInfo,
    PopulationPreviewResponse,
    PopulationProfileResponse,
    PopulationUploadResponse,
)

if TYPE_CHECKING:
    from reformlab.server.result_store import ResultStore

logger = logging.getLogger(__name__)

# Population endpoint constants
PREVIEW_DEFAULT_LIMIT = 100
PREVIEW_MAX_LIMIT = 100
CROSSTAB_MAX_COMBINATIONS = 1000
HISTOGRAM_BINS = 20
CATEGORICAL_TOP_VALUES = 50

router = APIRouter()

# Supported data file extensions
_DATA_EXTENSIONS = {".csv", ".parquet"}

# Known ReformLab columns for upload validation
_KNOWN_COLUMNS = {
    "household_id",
    "person_id",
    "income",
    "disposable_income",
    "age",
    "decile",
    "region",
    "has_children",
    "employment_status",
    "education_level",
}

# Required columns
_REQUIRED_COLUMNS = {"household_id"}

# Environment variable for uploaded populations directory
_UPLOADED_DIR_ENV = "REFORMLAB_UPLOADED_POPULATIONS_DIR"


def _get_uploaded_dir() -> Path:
    """Get the uploaded populations directory, creating if needed."""
    uploaded_dir = Path(os.environ.get(_UPLOADED_DIR_ENV, "~/.reformlab/uploaded-populations")).expanduser()
    uploaded_dir.mkdir(parents=True, exist_ok=True)
    return uploaded_dir


def _get_data_dir() -> Path:
    """Get the data populations directory."""
    data_dir_env = os.environ.get("REFORMLAB_DATA_DIR", "data")
    return Path(data_dir_env) / "populations"


# =============================================================================
# Population file resolution
# =============================================================================


def _find_population_file(population_id: str) -> Path | None:
    """Find a population file by ID, checking all directories in order."""
    data_dir = _get_data_dir()
    uploaded_dir = _get_uploaded_dir()

    # Check built-in populations first
    for ext in _DATA_EXTENSIONS:
        path = data_dir / f"{population_id}{ext}"
        if path.exists():
            return path

    # Check uploaded populations
    for ext in _DATA_EXTENSIONS:
        path = uploaded_dir / f"{population_id}{ext}"
        if path.exists():
            return path

    return None


def _get_population_origin(
    population_id: str, file_path: Path | None,
) -> Literal["built-in", "generated", "uploaded"]:
    """Determine the origin of a population."""
    if file_path is None:
        return "built-in"

    uploaded_dir = _get_uploaded_dir()

    # Check if in uploaded directory
    if file_path.parent == uploaded_dir:
        return "uploaded"

    # Check for manifest file (generated population)
    data_dir = _get_data_dir()
    manifest_path = data_dir / f"{population_id}.manifest.json"
    if manifest_path.exists():
        return "generated"

    return "built-in"


def _load_population_table(file_path: Path) -> pa.Table:
    """Load a population file as a PyArrow table."""
    if file_path.suffix.lower() == ".parquet":
        return pa.parquet.read_table(file_path)
    else:  # CSV
        return pa.csv.read_csv(file_path)


# =============================================================================
# Origin detection helpers
# =============================================================================


def _read_generated_metadata(population_id: str) -> dict[str, Any] | None:
    """Read metadata from a generated population manifest."""
    data_dir = _get_data_dir()
    manifest_path = data_dir / f"{population_id}.manifest.json"

    if not manifest_path.exists():
        return None

    try:
        result: dict[str, Any] = json.loads(manifest_path.read_text())
        return result
    except (json.JSONDecodeError, OSError):
        return None


def _read_uploaded_metadata(population_id: str) -> dict[str, Any] | None:
    """Read metadata from an uploaded population sidecar."""
    uploaded_dir = _get_uploaded_dir()
    meta_path = uploaded_dir / f"{population_id}.meta.json"

    if not meta_path.exists():
        return None

    try:
        result: dict[str, Any] = json.loads(meta_path.read_text())
        return result
    except (json.JSONDecodeError, OSError):
        return None


# =============================================================================
# Extended list endpoint with origin detection — Task 20.7.1
# =============================================================================


def _scan_populations_with_origin() -> list[PopulationLibraryItem]:
    """Scan all population directories and return PopulationLibraryItem list."""
    items: list[PopulationLibraryItem] = []

    data_dir = _get_data_dir()
    uploaded_dir = _get_uploaded_dir()

    # Track seen IDs to avoid duplicates
    seen_ids: set[str] = set()

    # Scan built-in and generated populations
    if data_dir.exists():
        for path in sorted(data_dir.iterdir()):
            if path.suffix.lower() not in _DATA_EXTENSIONS:
                continue

            pop_id = path.stem
            if pop_id in seen_ids:
                continue
            seen_ids.add(pop_id)

            # Determine origin
            origin = _get_population_origin(pop_id, path)
            created_date: str | None = None
            column_count = 0

            # Load metadata based on origin
            if origin == "generated":
                meta = _read_generated_metadata(pop_id)
                if meta:
                    created_date = meta.get("generated_at")
                    column_count = meta.get("summary", {}).get("column_count", 0)
            elif origin == "uploaded":
                meta = _read_uploaded_metadata(pop_id)
                if meta:
                    created_date = meta.get("created_date")
                    # column_count will be loaded from file
            else:
                # Built-in: load column count from file
                try:
                    table = _load_population_table(path)
                    column_count = table.num_columns
                except Exception:
                    column_count = 0

            # Derive display name from filename
            name = pop_id.replace("-", " ").title()

            # Derive source, year, households from filename (legacy parsing)
            parts = pop_id.split("-")
            source = parts[0] if parts else "unknown"
            year = 2025
            households = 0

            for part in parts:
                if len(part) == 4 and part.isdigit():
                    year = int(part)
                elif part.endswith("k") and part[:-1].isdigit():
                    households = int(part[:-1]) * 1000
                elif part.isdigit() and len(part) >= 3:
                    households = int(part)

            items.append(
                PopulationLibraryItem(
                    id=pop_id,
                    name=name,
                    households=households,
                    source=source,
                    year=year,
                    origin=origin,
                    column_count=column_count,
                    created_date=created_date,
                )
            )

    # Scan uploaded populations
    if uploaded_dir.exists():
        for meta_path in sorted(uploaded_dir.glob("*.meta.json")):
            # meta_path.stem returns filename without .json, so we get "pop-id.meta"
            # We need to strip the ".meta" suffix too
            pop_id = meta_path.stem.removesuffix(".meta")
            if pop_id in seen_ids:
                continue
            seen_ids.add(pop_id)

            # Read metadata (pass the path directly to avoid re-reading env var)
            try:
                meta = json.loads(meta_path.read_text()) if meta_path.exists() else None
            except (json.JSONDecodeError, OSError):
                meta = None

            if not meta:
                logger.warning(
                    "Failed to read metadata for uploaded population '%s' from '%s'",
                    pop_id, meta_path,
                )
                continue

            # Load column count from data file
            column_count = 0
            data_path = uploaded_dir / f"{pop_id}.csv"
            if not data_path.exists():
                data_path = uploaded_dir / f"{pop_id}.parquet"

            if data_path.exists():
                try:
                    table = _load_population_table(data_path)
                    column_count = table.num_columns
                except Exception:
                    pass

            items.append(
                PopulationLibraryItem(
                    id=pop_id,
                    name=meta.get("original_filename", pop_id),
                    households=0,
                    source="uploaded",
                    year=2025,
                    origin="uploaded",
                    column_count=column_count,
                    created_date=meta.get("created_date"),
                )
            )

    return items


@router.get("", response_model=dict[str, list[PopulationLibraryItem]])
async def list_populations() -> dict[str, list[PopulationLibraryItem]]:
    """List available population datasets with origin tags — AC-1, #1."""
    populations = _scan_populations_with_origin()
    return {"populations": populations}


# =============================================================================
# Preview endpoint — Task 20.7.2
# =============================================================================


def _map_arrow_type_to_string(arrow_type: pa.DataType) -> str:
    """Map PyArrow type to string type identifier."""
    if pa.types.is_integer(arrow_type):
        return "integer"
    elif pa.types.is_floating(arrow_type):
        return "float"
    elif pa.types.is_string(arrow_type) or pa.types.is_large_string(arrow_type):
        return "string"
    elif pa.types.is_boolean(arrow_type):
        return "boolean"
    else:
        return "string"


@router.get("/{population_id}/preview", response_model=PopulationPreviewResponse)
async def preview_population(
    population_id: str,
    offset: int = 0,
    limit: int = PREVIEW_DEFAULT_LIMIT,
    sort_by: str | None = None,
    order: Literal["asc", "desc"] = "asc",
) -> PopulationPreviewResponse:
    """Get a paginated preview of population rows — AC-1, #3."""
    file_path = _find_population_file(population_id)

    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Population '{population_id}' not found",
                "why": "No population file exists for this ID",
                "fix": "Check available populations via GET /api/populations",
            },
        )

    # Enforce max limit
    limit = min(limit, PREVIEW_MAX_LIMIT)

    try:
        table = _load_population_table(file_path)

        # Apply sorting if requested
        if sort_by:
            if sort_by not in table.column_names:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "what": f"Column '{sort_by}' not found",
                        "why": "The specified column does not exist in this population",
                        "fix": "Check available columns via GET /api/populations/{id}/profile",
                    },
                )

            sort_order = "ascending" if order == "asc" else "descending"
            table = table.sort_by([(sort_by, sort_order)])

        # Apply pagination
        total_rows = table.num_rows
        end_idx = min(offset + limit, total_rows)
        table = table.slice(offset, end_idx - offset)

        # Convert rows to list of dicts
        rows = table.to_pylist()

        # Build column info
        columns = []
        for i, name in enumerate(table.column_names):
            arrow_type = table.schema[i].type
            columns.append(
                PopulationPreviewColumnInfo(
                    name=name,
                    type=_map_arrow_type_to_string(arrow_type),
                    description="",
                )
            )

        return PopulationPreviewResponse(
            id=population_id,
            name=population_id.replace("-", " ").title(),
            rows=rows,
            columns=columns,
            total_rows=total_rows,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to preview population '%s'", population_id)
        raise HTTPException(
            status_code=500,
            detail={
                "what": "Failed to load population preview",
                "why": str(e),
                "fix": "Check that the file is a valid CSV or Parquet file",
            },
        )


# =============================================================================
# Profile endpoint — Task 20.7.3
# =============================================================================


def _compute_numeric_profile(table: pa.Table, column_name: str) -> ColumnProfileNumeric:
    """Compute profile statistics for a numeric column."""
    column = table.column(column_name)
    count = len(column)
    null_count = column.null_count
    null_pct = (null_count / count * 100) if count > 0 else 0

    # Get non-null values for statistics
    valid_data = column.drop_null()

    if valid_data.length == 0:
        # All nulls
        return ColumnProfileNumeric(
            type="numeric",
            count=count,
            nulls=null_count,
            null_pct=null_pct,
            min=0,
            max=0,
            mean=0,
            median=0,
            std=0,
            percentiles={},
            histogram_buckets=[],
        )

    # Compute statistics
    min_val = pc.min(valid_data).as_py()
    max_val = pc.max(valid_data).as_py()
    mean_val = float(pc.mean(valid_data).as_py())

    # pc.quantile returns an array with one element
    median_array = pc.quantile(valid_data, q=0.5)
    median_val = float(median_array[0].as_py())

    # pc.stddev also returns a scalar
    std_val = 0.0
    if len(valid_data) > 1:
        std_result = pc.stddev(valid_data)
        std_val = float(std_result.as_py() if hasattr(std_result, "as_py") else std_result)

    # Compute percentiles
    percentiles = {}
    for p in [1, 5, 25, 50, 75, 95, 99]:
        q = p / 100
        try:
            result_array = pc.quantile(valid_data, q=q)
            percentiles[f"p{p}"] = float(result_array[0].as_py())
        except Exception:
            percentiles[f"p{p}"] = 0

    # Compute histogram (20 equal-width bins)
    histogram_buckets = []
    if max_val > min_val:
        bin_width = (max_val - min_val) / HISTOGRAM_BINS
        for i in range(HISTOGRAM_BINS):
            bin_start = min_val + i * bin_width
            bin_end = min_val + (i + 1) * bin_width

            # Count values in this bin
            # Last bin includes the max value
            if i == HISTOGRAM_BINS - 1:
                mask = pc.greater_equal(valid_data, bin_start)
            else:
                mask = pc.and_(
                    pc.greater_equal(valid_data, bin_start),
                    pc.less(valid_data, bin_end),
                )
            count_val = pc.sum(mask.cast(pa.int32())).as_py()

            histogram_buckets.append({
                "bin_start": float(bin_start),
                "bin_end": float(bin_end),
                "count": int(count_val) if count_val is not None else 0,
            })

    return ColumnProfileNumeric(
        type="numeric",
        count=count,
        nulls=null_count,
        null_pct=null_pct,
        min=float(min_val),
        max=float(max_val),
        mean=mean_val,
        median=median_val,
        std=std_val,
        percentiles=percentiles,
        histogram_buckets=histogram_buckets,
    )


def _compute_categorical_profile(table: pa.Table, column_name: str) -> ColumnProfileCategorical:
    """Compute profile statistics for a categorical column."""
    column = table.column(column_name)
    count = len(column)
    null_count = column.null_count
    null_pct = (null_count / count * 100) if count > 0 else 0

    # Compute value counts
    valid_data = column.drop_null()
    cardinality = len(valid_data.unique())

    # Get top 50 values
    value_counts_list = []
    try:
        value_counts_table = pc.value_counts(valid_data)
        sorted_table = value_counts_table.sort_by([("counts", "descending")])

        # Take top N values
        limit = min(CATEGORICAL_TOP_VALUES, sorted_table.num_rows)
        for i in range(limit):
            val = sorted_table["values"][i].as_py()
            cnt = sorted_table["counts"][i].as_py()
            value_counts_list.append({"value": str(val), "count": int(cnt)})
    except Exception:
        pass

    return ColumnProfileCategorical(
        type="categorical",
        count=count,
        nulls=null_count,
        null_pct=null_pct,
        cardinality=cardinality,
        value_counts=value_counts_list,
    )


def _compute_boolean_profile(table: pa.Table, column_name: str) -> ColumnProfileBoolean:
    """Compute profile statistics for a boolean column."""
    column = table.column(column_name)
    count = len(column)
    null_count = column.null_count
    null_pct = (null_count / count * 100) if count > 0 else 0

    # Count true and false values
    valid_data = column.drop_null()
    true_count = 0
    false_count = 0

    if len(valid_data) > 0:
        try:
            true_count = int(pc.sum(valid_data.cast(pa.int32())).as_py())
            false_count = len(valid_data) - true_count
        except Exception:
            pass

    return ColumnProfileBoolean(
        type="boolean",
        count=count,
        nulls=null_count,
        null_pct=null_pct,
        true_count=true_count,
        false_count=false_count,
    )


@router.get("/{population_id}/profile", response_model=PopulationProfileResponse)
async def profile_population(population_id: str) -> PopulationProfileResponse:
    """Get per-column profile statistics — AC-1, #3."""
    file_path = _find_population_file(population_id)

    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Population '{population_id}' not found",
                "why": "No population file exists for this ID",
                "fix": "Check available populations via GET /api/populations",
            },
        )

    try:
        table = _load_population_table(file_path)
        columns = []

        for col_name in table.column_names:
            column = table.column(col_name)
            arrow_type = column.type

            # Determine profile type based on PyArrow type
            if pa.types.is_integer(arrow_type) or pa.types.is_floating(arrow_type):
                profile: ColumnProfile = _compute_numeric_profile(table, col_name)
            elif pa.types.is_boolean(arrow_type):
                profile = _compute_boolean_profile(table, col_name)
            else:
                # String or other types are treated as categorical
                profile = _compute_categorical_profile(table, col_name)

            columns.append(
                ColumnProfileEntry(
                    name=col_name,
                    profile=profile,
                )
            )

        return PopulationProfileResponse(
            id=population_id,
            columns=columns,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to profile population '%s'", population_id)
        raise HTTPException(
            status_code=500,
            detail={
                "what": "Failed to compute population profile",
                "why": str(e),
                "fix": "Check that the file is a valid CSV or Parquet file",
            },
        )


# =============================================================================
# Crosstab endpoint — Task 20.7.4
# =============================================================================


@router.get("/{population_id}/crosstab", response_model=PopulationCrosstabResponse)
async def crosstab_population(
    population_id: str,
    col_a: str,
    col_b: str,
) -> PopulationCrosstabResponse:
    """Get cross-tabulation of two columns — AC-1, #3."""
    file_path = _find_population_file(population_id)

    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Population '{population_id}' not found",
                "why": "No population file exists for this ID",
                "fix": "Check available populations via GET /api/populations",
            },
        )

    try:
        table = _load_population_table(file_path)

        # Validate columns exist
        if col_a not in table.column_names:
            raise HTTPException(
                status_code=400,
                detail={
                    "what": f"Column '{col_a}' not found",
                    "why": "The specified column does not exist in this population",
                    "fix": "Check available columns via GET /api/populations/{id}/profile",
                },
            )

        if col_b not in table.column_names:
            raise HTTPException(
                status_code=400,
                detail={
                    "what": f"Column '{col_b}' not found",
                    "why": "The specified column does not exist in this population",
                    "fix": "Check available columns via GET /api/populations/{id}/profile",
                },
            )

        # Compute cross-tabulation using groupby
        try:
            grouped = table.group_by([col_a, col_b]).aggregate(
                [(col_a, "count")]
            )

            # Sort by count descending
            sorted_table = grouped.sort_by([(col_a + "_count", "descending")])

            # Limit to max combinations
            total_rows = sorted_table.num_rows
            truncated = total_rows > CROSSTAB_MAX_COMBINATIONS
            limited_table = sorted_table.slice(0, min(CROSSTAB_MAX_COMBINATIONS, total_rows))

            # Convert to list of dicts
            data = []
            for i in range(limited_table.num_rows):
                row = {}
                for j, name in enumerate(limited_table.column_names):
                    val = limited_table[j][i].as_py()
                    row[name] = val
                data.append(row)

            return PopulationCrosstabResponse(
                col_a=col_a,
                col_b=col_b,
                data=data,
                truncated=truncated,
            )

        except Exception as e:
            logger.exception("Failed to compute crosstab for population '%s'", population_id)
            raise HTTPException(
                status_code=500,
                detail={
                    "what": "Failed to compute cross-tabulation",
                    "why": str(e),
                    "fix": "Ensure both columns contain compatible data types",
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to crosstab population '%s'", population_id)
        raise HTTPException(
            status_code=500,
            detail={
                "what": "Failed to load population for crosstab",
                "why": str(e),
                "fix": "Check that the file is a valid CSV or Parquet file",
            },
        )


# =============================================================================
# Upload endpoint — Task 20.7.5
# =============================================================================


@router.post("/upload", response_model=PopulationUploadResponse)
async def upload_population(
    file: UploadFile = File(...),
) -> PopulationUploadResponse:
    """Upload a CSV or Parquet file as a new population — AC-1, #3."""
    # Validate file extension
    filename = file.filename or "upload"
    ext = Path(filename).suffix.lower()

    if ext not in _DATA_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "what": "Invalid file type",
                "why": "Only CSV and Parquet files are supported",
                "fix": "Upload a .csv or .parquet file",
            },
        )

    # Generate unique population ID
    population_id = f"uploaded-{uuid.uuid4()}"
    uploaded_dir = _get_uploaded_dir()

    # Save file
    data_file = uploaded_dir / f"{population_id}{ext}"
    try:
        contents = file.file.read()
        data_file.write_bytes(contents)
    except Exception as e:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(
            status_code=500,
            detail={
                "what": "Failed to save uploaded file",
                "why": str(e),
                "fix": "Try uploading the file again",
            },
        )

    # Load and validate
    try:
        table = _load_population_table(data_file)
        row_count = table.num_rows
        column_count = table.num_columns
        column_names = set(table.column_names)

        # Validate columns
        matched_columns = list(column_names & _KNOWN_COLUMNS)
        unrecognized_columns = list(column_names - _KNOWN_COLUMNS)
        missing_required = list(_REQUIRED_COLUMNS - column_names)

        valid = len(missing_required) == 0

        # Create metadata sidecar
        meta = {
            "id": population_id,
            "origin": "uploaded",
            "created_date": datetime.now(timezone.utc).isoformat(),
            "original_filename": filename,
            "file_path": str(data_file),
        }

        meta_file = uploaded_dir / f"{population_id}.meta.json"
        meta_file.write_text(json.dumps(meta, indent=2))

        return PopulationUploadResponse(
            id=population_id,
            name=filename,
            row_count=row_count,
            column_count=column_count,
            matched_columns=matched_columns,
            unrecognized_columns=unrecognized_columns,
            missing_required=missing_required,
            valid=valid,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to validate uploaded file")
        # Clean up data file on error
        try:
            data_file.unlink()
        except Exception:
            pass
        raise HTTPException(
            status_code=400,
            detail={
                "what": "Failed to parse uploaded file",
                "why": str(e),
                "fix": "Ensure the file is a valid CSV or Parquet file",
            },
        )


# =============================================================================
# Delete endpoint — Task 20.7.6
# =============================================================================


@router.delete("/{population_id}", status_code=204)
async def delete_population(
    population_id: str,
    store: ResultStore = Depends(get_result_store),
) -> None:
    """Delete an uploaded or generated population — AC-1."""
    file_path = _find_population_file(population_id)

    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Population '{population_id}' not found",
                "why": "No population file exists for this ID",
                "fix": "Check available populations via GET /api/populations",
            },
        )

    origin = _get_population_origin(population_id, file_path)

    if origin == "built-in":
        raise HTTPException(
            status_code=403,
            detail={
                "what": "Cannot delete built-in population",
                "why": "Built-in populations are protected and cannot be deleted",
                "fix": "Only uploaded and generated populations can be deleted",
            },
        )

    # Delete data file and sidecar
    try:
        file_path.unlink()
    except Exception:
        pass

    uploaded_dir = _get_uploaded_dir()

    if origin == "uploaded":
        meta_file = uploaded_dir / f"{population_id}.meta.json"
        try:
            meta_file.unlink()
        except Exception:
            pass
    elif origin == "generated":
        data_dir = _get_data_dir()
        manifest_file = data_dir / f"{population_id}.manifest.json"
        try:
            manifest_file.unlink()
        except Exception:
            pass

    return None
