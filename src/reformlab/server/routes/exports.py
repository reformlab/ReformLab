"""File export/download routes."""

from __future__ import annotations

import io
import logging
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from reformlab.server.dependencies import ResultCache, get_result_cache, get_result_store
from reformlab.server.models import ExportRequest
from reformlab.server.result_store import ResultNotFound

if TYPE_CHECKING:
    from reformlab.server.result_store import ResultStore

logger = logging.getLogger(__name__)

router = APIRouter()


_MAX_EXPORT_BYTES = 500 * 1024 * 1024  # 500 MB safety limit


def _file_response(path: Path, media_type: str, filename: str) -> StreamingResponse:
    """Read file into memory and return as a download response.

    Reads eagerly so the temp directory can be cleaned up before the
    response is streamed to the client.  Rejects files over 500 MB.
    """
    size = path.stat().st_size
    limit_mb = _MAX_EXPORT_BYTES // 1024 // 1024
    if size > _MAX_EXPORT_BYTES:
        raise HTTPException(
            status_code=422,
            detail={
                "what": "Export file too large",
                "why": f"File is {size / 1024 / 1024:.0f} MB, limit is {limit_mb} MB",
                "fix": "Filter the dataset or use a smaller population",
            },
        )
    data = path.read_bytes()
    return StreamingResponse(
        io.BytesIO(data),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _lookup_run(
    run_id: str,
    cache: ResultCache,
    store: ResultStore,
) -> Any:
    """Two-step store/cache lookup. Returns SimulationResult with panel_output.

    Raises HTTPException(404) if unknown, HTTPException(409) if evicted.
    """
    try:
        store.get_metadata(run_id)
    except ResultNotFound:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Run '{run_id}' not found",
                "why": "No metadata record exists for this run_id",
                "fix": "Check the run_id and ensure the simulation has been executed",
            },
        )

    result = cache.get(run_id)
    if result is None or result.panel_output is None:
        raise HTTPException(
            status_code=409,
            detail={
                "what": f"Run '{run_id}' data is not available",
                "why": "The simulation result has been evicted from the in-memory cache",
                "fix": "Re-run the simulation or select runs with data_available=true",
            },
        )
    return result


@router.post("/csv")
async def export_csv(
    body: ExportRequest,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> StreamingResponse:
    """Export a cached simulation result as CSV."""
    result = _lookup_run(body.run_id, cache, store)

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = Path(tmp_dir) / f"reformlab-{body.run_id[:8]}.csv"
        result.panel_output.to_csv(csv_path)
        return _file_response(csv_path, "text/csv", csv_path.name)


@router.post("/parquet")
async def export_parquet(
    body: ExportRequest,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> StreamingResponse:
    """Export a cached simulation result as Parquet."""
    result = _lookup_run(body.run_id, cache, store)

    with tempfile.TemporaryDirectory() as tmp_dir:
        parquet_path = Path(tmp_dir) / f"reformlab-{body.run_id[:8]}.parquet"
        result.panel_output.to_parquet(parquet_path)
        return _file_response(
            parquet_path, "application/octet-stream", parquet_path.name
        )
