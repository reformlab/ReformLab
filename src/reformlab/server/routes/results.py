# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Results CRUD routes — Story 17.3, Story 17.7.

Exposes saved simulation run metadata via REST endpoints. Full SimulationResult
objects are served from the in-memory ResultCache when available; on cache miss,
panel data is loaded from disk (panel.parquet) when present (Story 17.7).

Endpoint table:
    GET    /api/results                       — list all saved results (metadata)
    GET    /api/results/{run_id}              — get result detail
    DELETE /api/results/{run_id}              — delete from store and cache
    GET    /api/results/{run_id}/export/csv   — download panel data as CSV
    GET    /api/results/{run_id}/export/parquet — download panel data as Parquet
    GET    /api/results/{run_id}/manifest     — get full run manifest (Story 26.4)

References: Story 17.3, Story 17.7, Story 26.4, AC-2, AC-3, AC-4
"""

from __future__ import annotations

import io
import logging
from typing import Any, Literal, cast

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from reformlab.server.dependencies import ResultCache, get_result_cache, get_result_store
from reformlab.server.models import ManifestResponse, ResultDetailResponse, ResultListItem
from reformlab.server.result_store import ResultMetadata, ResultNotFound, ResultStore, ResultStoreError

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _metadata_to_list_item(
    meta: ResultMetadata,
    data_available: bool,
) -> ResultListItem:
    return ResultListItem(
        run_id=meta.run_id,
        timestamp=meta.timestamp,
        run_kind=meta.run_kind,
        start_year=meta.start_year,
        end_year=meta.end_year,
        row_count=meta.row_count,
        status=meta.status,
        data_available=data_available,
        template_name=meta.template_name,
        policy_type=meta.policy_type,
        portfolio_name=meta.portfolio_name,
    )


def _metadata_to_detail(
    meta: ResultMetadata,
    cache: ResultCache,
    store: ResultStore,
) -> ResultDetailResponse:
    """Build a ResultDetailResponse, enriching with cache/disk data if available."""
    sim_result = cache.get_or_load(meta.run_id, store)
    data_available = sim_result is not None and sim_result.panel_output is not None

    indicators: dict[str, Any] | None = None
    columns: list[str] | None = None
    column_count: int | None = None

    if sim_result is not None and sim_result.panel_output is not None:
        table = sim_result.panel_output.table
        columns = table.schema.names
        column_count = len(columns)
        # Build a lightweight indicator summary (field names only for now)
        indicators = {"columns": columns, "row_count": table.num_rows}

    # Story 21.8 / AC4: Populate evidence_assets from manifest
    evidence_assets: list[dict[str, Any]] | None = None
    if sim_result is not None and sim_result.manifest.evidence_assets:
        evidence_assets = sim_result.manifest.evidence_assets

    return ResultDetailResponse(
        run_id=meta.run_id,
        timestamp=meta.timestamp,
        run_kind=meta.run_kind,
        start_year=meta.start_year,
        end_year=meta.end_year,
        population_id=meta.population_id,
        seed=meta.seed,
        row_count=meta.row_count,
        manifest_id=meta.manifest_id,
        scenario_id=meta.scenario_id,
        adapter_version=meta.adapter_version,
        started_at=meta.started_at,
        finished_at=meta.finished_at,
        status=meta.status,
        data_available=data_available,
        template_name=meta.template_name,
        policy_type=meta.policy_type,
        portfolio_name=meta.portfolio_name,
        indicators=indicators,
        columns=columns,
        column_count=column_count,
        # Story 21.6 / AC6: Exogenous series fields for comparison dimension
        exogenous_series_hash=meta.exogenous_series_hash,
        exogenous_series_names=meta.exogenous_series_names,
        # Story 21.8 / AC4: Evidence assets from manifest
        evidence_assets=evidence_assets,
        # Story 23.1 / AC-4: Runtime mode from metadata
        runtime_mode=cast(
            Literal["live", "replay"],
            meta.runtime_mode if meta.runtime_mode in ("live", "replay") else "live",
        ),
        # Story 23.2 / AC-5: Population source classification from resolver
        population_source=cast(
            "Literal['bundled', 'uploaded', 'generated'] | None",
            meta.population_source
            if meta.population_source in ("bundled", "uploaded", "generated")
            else None,
        ),
    )


# ---------------------------------------------------------------------------
# GET /api/results
# ---------------------------------------------------------------------------


@router.get("", response_model=list[ResultListItem])
async def list_results(
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> list[ResultListItem]:
    """List all saved simulation results in reverse chronological order.

    data_available is True for any run that has a panel.parquet on disk or
    a SimulationResult with panel_output in the in-memory cache.
    Avoids loading panels into memory for listing (uses has_panel() only).
    """
    items = store.list_results()
    result_items = []
    for meta in items:
        cache_result = cache.get(meta.run_id)
        data_available = (
            store.has_panel(meta.run_id)
            or (cache_result is not None and cache_result.panel_output is not None)
        )
        result_items.append(_metadata_to_list_item(meta, data_available=data_available))
    return result_items


# ---------------------------------------------------------------------------
# GET /api/results/{run_id}
# ---------------------------------------------------------------------------


@router.get("/{run_id}", response_model=ResultDetailResponse)
async def get_result(
    run_id: str,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> ResultDetailResponse:
    """Return detail for a single simulation result.

    If the SimulationResult is in cache or on disk, full data (indicators,
    columns) is included with data_available=True. Otherwise metadata-only
    with data_available=False.
    """
    try:
        meta = store.get_metadata(run_id)
    except ResultNotFound:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Result not found: {run_id!r}",
                "why": "No metadata file exists for this run ID",
                "fix": "Check the run ID or re-run the simulation",
            },
        )
    except ResultStoreError:
        raise HTTPException(
            status_code=400,
            detail={
                "what": f"Invalid run_id: {run_id!r}",
                "why": "run_id contains disallowed characters",
                "fix": "Use a valid run ID obtained from POST /api/runs",
            },
        )
    return _metadata_to_detail(meta, cache, store)


# ---------------------------------------------------------------------------
# DELETE /api/results/{run_id}
# ---------------------------------------------------------------------------


@router.delete("/{run_id}", status_code=204)
async def delete_result(
    run_id: str,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> None:
    """Delete a simulation result from the persistent store and cache."""
    try:
        store.delete_result(run_id)
    except ResultNotFound:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Result not found: {run_id!r}",
                "why": "No metadata file exists for this run ID",
                "fix": "Check the run ID",
            },
        )
    except ResultStoreError:
        raise HTTPException(
            status_code=400,
            detail={
                "what": f"Invalid run_id: {run_id!r}",
                "why": "run_id contains disallowed characters",
                "fix": "Use a valid run ID obtained from POST /api/runs",
            },
        )
    cache.delete(run_id)
    logger.info("event=result_deleted run_id=%s", run_id)


# ---------------------------------------------------------------------------
# GET /api/results/{run_id}/export/csv
# ---------------------------------------------------------------------------


@router.get("/{run_id}/export/csv")
async def export_csv(
    run_id: str,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> StreamingResponse:
    """Stream the panel data table as a CSV download.

    Returns 404 if run_id not found in persistent store.
    Returns 409 if result has no panel data (failed run or pre-17.7 run).
    """
    # Verify run exists in persistent store
    try:
        store.get_metadata(run_id)
    except ResultNotFound:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Result not found: {run_id!r}",
                "why": "No metadata file exists for this run ID",
                "fix": "Check the run ID or re-run the simulation",
            },
        )
    except ResultStoreError:
        raise HTTPException(
            status_code=400,
            detail={
                "what": f"Invalid run_id: {run_id!r}",
                "why": "run_id contains disallowed characters",
                "fix": "Use a valid run ID obtained from POST /api/runs",
            },
        )

    sim_result = cache.get_or_load(run_id, store)
    if sim_result is None or sim_result.panel_output is None:
        raise HTTPException(
            status_code=409,
            detail={
                "what": "Full result data is not available",
                "why": "The simulation result has been evicted from the in-memory cache",
                "fix": "Re-run the simulation to access full data for export",
            },
        )

    import pyarrow.csv as pa_csv

    buf = io.BytesIO()
    pa_csv.write_csv(sim_result.panel_output.table, buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{run_id}.csv"'},
    )


# ---------------------------------------------------------------------------
# GET /api/results/{run_id}/export/parquet
# ---------------------------------------------------------------------------


@router.get("/{run_id}/export/parquet")
async def export_parquet(
    run_id: str,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> StreamingResponse:
    """Stream the panel data table as a Parquet download.

    Returns 404 if run_id not found in persistent store.
    Returns 409 if result has no panel data (failed run or pre-17.7 run).
    """
    # Verify run exists in persistent store
    try:
        store.get_metadata(run_id)
    except ResultNotFound:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Result not found: {run_id!r}",
                "why": "No metadata file exists for this run ID",
                "fix": "Check the run ID or re-run the simulation",
            },
        )
    except ResultStoreError:
        raise HTTPException(
            status_code=400,
            detail={
                "what": f"Invalid run_id: {run_id!r}",
                "why": "run_id contains disallowed characters",
                "fix": "Use a valid run ID obtained from POST /api/runs",
            },
        )

    sim_result = cache.get_or_load(run_id, store)
    if sim_result is None or sim_result.panel_output is None:
        raise HTTPException(
            status_code=409,
            detail={
                "what": "Full result data is not available",
                "why": "The simulation result has been evicted from the in-memory cache",
                "fix": "Re-run the simulation to access full data for export",
            },
        )

    import pyarrow.parquet as pq

    buf = io.BytesIO()
    pq.write_table(sim_result.panel_output.table, buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{run_id}.parquet"'},
    )


# ---------------------------------------------------------------------------
# GET /api/results/{run_id}/manifest — Story 26.4
# ---------------------------------------------------------------------------


@router.get("/{run_id}/manifest", response_model=ManifestResponse)
async def get_manifest(
    run_id: str,
    cache: ResultCache = Depends(get_result_cache),
    store: ResultStore = Depends(get_result_store),
) -> ManifestResponse:
    """Return the full RunManifest for a single simulation result.

    Returns 404 if run_id not found in persistent store.
    Returns 409 if SimulationResult and manifest.json are both unavailable (truly unrecoverable).
    Returns 200 with metadata_only=True when only metadata.json and manifest.json exist (no panel.parquet).

    The manifest includes all assumptions, mappings, hashes, lineage, and
    reproducibility metadata needed for the Stage 5 Run Manifest Viewer.
    """
    # Verify run exists in persistent store
    try:
        meta = store.get_metadata(run_id)
    except ResultNotFound:
        raise HTTPException(
            status_code=404,
            detail={
                "what": f"Result not found: {run_id!r}",
                "why": "No metadata file exists for this run ID",
                "fix": "Check the run ID or re-run the simulation",
            },
        )
    except ResultStoreError:
        raise HTTPException(
            status_code=400,
            detail={
                "what": f"Invalid run_id: {run_id!r}",
                "why": "run_id contains disallowed characters",
                "fix": "Use a valid run ID obtained from POST /api/runs",
            },
        )

    # Try to load SimulationResult (from cache or disk)
    sim_result = cache.get_or_load(run_id, store)

    if sim_result is None:
        # Panel data unavailable, try loading manifest from disk
        try:
            manifest = store.load_manifest(run_id)
            # Return degraded response with available manifest data
            return ManifestResponse(
                run_id=run_id,
                manifest_id=manifest.manifest_id,
                created_at=manifest.created_at,
                started_at=meta.started_at if hasattr(meta, "started_at") else "",
                finished_at=meta.finished_at if hasattr(meta, "finished_at") else "",
                status="metadata_only",
                engine_version=manifest.engine_version,
                openfisca_version=manifest.openfisca_version,
                adapter_version=manifest.adapter_version,
                scenario_version=manifest.scenario_version,
                data_hashes=manifest.data_hashes,
                output_hashes=manifest.output_hashes,
                integrity_hash=manifest.integrity_hash,
                seeds=manifest.seeds,
                policy=manifest.policy,
                assumptions=[dict(a) for a in manifest.assumptions],
                mappings=[dict(m) for m in manifest.mappings],
                warnings=list(manifest.warnings) + ["Panel data not available - showing metadata only"],
                step_pipeline=list(manifest.step_pipeline),
                parent_manifest_id=manifest.parent_manifest_id,
                child_manifests={str(k): v for k, v in manifest.child_manifests.items()},
                exogenous_series=list(manifest.exogenous_series),
                taste_parameters=dict(manifest.taste_parameters),
                evidence_assets=[dict(e) for e in manifest.evidence_assets],
                calibration_assets=[dict(c) for c in manifest.calibration_assets],
                validation_assets=[dict(v) for v in manifest.validation_assets],
                evidence_summary=dict(manifest.evidence_summary),
                runtime_mode=cast(Literal["live", "replay"], manifest.runtime_mode),
                population_id=manifest.population_id,
                population_source=cast(
                    Literal["bundled", "uploaded", "generated"] | None,
                    manifest.population_source or None,
                ),
                metadata_only=True,
            )
        except ResultNotFound:
            # Neither SimulationResult nor manifest.json available
            raise HTTPException(
                status_code=409,
                detail={
                    "what": "Full manifest data is not available",
                    "why": (
                        "The simulation result has been evicted from the "
                        "in-memory cache and neither panel.parquet nor "
                        "manifest.json exist on disk"
                    ),
                    "fix": "Re-run the simulation to access the full manifest",
                },
            )

    # Full SimulationResult available
    manifest = sim_result.manifest

    # Convert RunManifest dataclass to ManifestResponse Pydantic model
    # RunManifest uses tuples for exogenous_series; convert to list
    # RunManifest uses frozen dataclasses; convert to dicts for JSON serialization
    return ManifestResponse(
        run_id=run_id,
        manifest_id=manifest.manifest_id,
        created_at=manifest.created_at,
        started_at=meta.started_at if hasattr(meta, "started_at") else "",
        finished_at=meta.finished_at if hasattr(meta, "finished_at") else "",
        status=meta.status if hasattr(meta, "status") else "completed",
        engine_version=manifest.engine_version,
        openfisca_version=manifest.openfisca_version,
        adapter_version=manifest.adapter_version,
        scenario_version=manifest.scenario_version,
        data_hashes=manifest.data_hashes,
        output_hashes=manifest.output_hashes,
        integrity_hash=manifest.integrity_hash,
        seeds=manifest.seeds,
        policy=manifest.policy,
        assumptions=[dict(a) for a in manifest.assumptions],
        mappings=[dict(m) for m in manifest.mappings],
        warnings=list(manifest.warnings),
        step_pipeline=list(manifest.step_pipeline),
        parent_manifest_id=manifest.parent_manifest_id,
        child_manifests={str(k): v for k, v in manifest.child_manifests.items()},
        exogenous_series=list(manifest.exogenous_series),
        taste_parameters=dict(manifest.taste_parameters),
        evidence_assets=[dict(e) for e in manifest.evidence_assets],
        calibration_assets=[dict(c) for c in manifest.calibration_assets],
        validation_assets=[dict(v) for v in manifest.validation_assets],
        evidence_summary=dict(manifest.evidence_summary),
        runtime_mode=cast(Literal["live", "replay"], manifest.runtime_mode),
        population_id=manifest.population_id,
        population_source=cast(
            Literal["bundled", "uploaded", "generated"] | None,
            manifest.population_source
            if manifest.population_source in ("bundled", "uploaded", "generated")
            else (
                meta.population_source
                if meta.population_source in ("bundled", "uploaded", "generated")
                else None
            ),
        ),
        metadata_only=False,
    )
