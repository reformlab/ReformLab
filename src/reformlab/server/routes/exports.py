"""File export/download routes."""

from __future__ import annotations

import io
import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from reformlab.server.dependencies import ResultCache, get_result_cache
from reformlab.server.models import ExportRequest

logger = logging.getLogger(__name__)

router = APIRouter()


def _file_response(path: Path, media_type: str, filename: str) -> StreamingResponse:
    """Read file into memory and return as a download response.

    Reads eagerly so the temp directory can be cleaned up before the
    response is streamed to the client.
    """
    data = path.read_bytes()
    return StreamingResponse(
        io.BytesIO(data),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/csv")
async def export_csv(
    body: ExportRequest,
    cache: ResultCache = Depends(get_result_cache),
) -> StreamingResponse:
    """Export a cached simulation result as CSV."""
    result = cache.get(body.run_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run ID '{body.run_id}' not found in cache",
        )

    if result.panel_output is None:
        raise HTTPException(
            status_code=422,
            detail="No panel output available for this run",
        )

    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_path = Path(tmp_dir) / f"reformlab-{body.run_id[:8]}.csv"
        result.panel_output.to_csv(csv_path)
        return _file_response(csv_path, "text/csv", csv_path.name)


@router.post("/parquet")
async def export_parquet(
    body: ExportRequest,
    cache: ResultCache = Depends(get_result_cache),
) -> StreamingResponse:
    """Export a cached simulation result as Parquet."""
    result = cache.get(body.run_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Run ID '{body.run_id}' not found in cache",
        )

    if result.panel_output is None:
        raise HTTPException(
            status_code=422,
            detail="No panel output available for this run",
        )

    with tempfile.TemporaryDirectory() as tmp_dir:
        parquet_path = Path(tmp_dir) / f"reformlab-{body.run_id[:8]}.parquet"
        result.panel_output.to_parquet(parquet_path)
        return _file_response(
            parquet_path, "application/octet-stream", parquet_path.name
        )
