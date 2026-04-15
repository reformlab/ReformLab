# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""FastAPI app factory for ReformLab.

Run with:
    uvicorn reformlab.server.app:create_app --factory --host 0.0.0.0 --port 8000

Dev mode:
    uvicorn reformlab.server.app:create_app --factory --reload --port 8000
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

import reformlab
from reformlab.server.auth import AuthMiddleware
from reformlab.server.auth import router as auth_router
from reformlab.server.routes.data_fusion import router as data_fusion_router
from reformlab.server.routes.decisions import router as decisions_router
from reformlab.server.routes.exogenous import router as exogenous_router
from reformlab.server.routes.exports import router as exports_router
from reformlab.server.routes.indicators import comparison_router
from reformlab.server.routes.indicators import router as indicators_router
from reformlab.server.routes.populations import router as populations_router
from reformlab.server.routes.portfolios import router as portfolios_router
from reformlab.server.routes.results import router as results_router
from reformlab.server.routes.runs import router as runs_router
from reformlab.server.routes.scenarios import router as scenarios_router
from reformlab.server.routes.templates import router as templates_router
from reformlab.server.routes.validation import router as validation_router

logger = logging.getLogger(__name__)


def _cors_origins() -> list[str]:
    """Build CORS allowed origins list."""
    origins = ["http://localhost:5173"]  # Vite dev server
    extra = os.environ.get("REFORMLAB_CORS_ORIGINS", "")
    if extra:
        origins.extend(o.strip() for o in extra.split(",") if o.strip())
    return origins


def _is_dev() -> bool:
    """Check if running in development mode."""
    return os.environ.get("REFORMLAB_ENV", "production").lower() in ("dev", "development")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    dev_mode = _is_dev()
    app = FastAPI(
        title="ReformLab API",
        version=reformlab.__version__,
        # API docs only available in dev mode
        docs_url="/api/docs" if dev_mode else None,
        openapi_url="/api/openapi.json" if dev_mode else None,
    )

    # Health endpoint (unauthenticated, used by Docker healthcheck and uptime monitors)
    @app.get("/api/health")
    async def health() -> PlainTextResponse:
        return PlainTextResponse("ok")

    # Kamal proxy readiness endpoint.
    @app.get("/up")
    async def up() -> PlainTextResponse:
        return PlainTextResponse("ok")

    # CORS must be added BEFORE auth middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    # Auth middleware (skips /api/auth/login, /api/health, and docs in dev mode)
    app.add_middleware(AuthMiddleware)

    # Register route groups
    app.include_router(auth_router, prefix="/api/auth")
    app.include_router(scenarios_router, prefix="/api/scenarios")
    app.include_router(runs_router, prefix="/api/runs")
    app.include_router(indicators_router, prefix="/api/indicators")
    app.include_router(comparison_router, prefix="/api/comparison")
    app.include_router(exports_router, prefix="/api/exports")
    app.include_router(templates_router, prefix="/api/templates")
    app.include_router(populations_router, prefix="/api/populations")
    app.include_router(data_fusion_router, prefix="/api/data-fusion", tags=["data-fusion"])
    app.include_router(exogenous_router, prefix="/api/exogenous", tags=["exogenous"])
    app.include_router(portfolios_router, prefix="/api/portfolios", tags=["portfolios"])
    app.include_router(results_router, prefix="/api/results", tags=["results"])
    app.include_router(decisions_router, prefix="/api/decisions", tags=["decisions"])
    app.include_router(validation_router, prefix="/api/validation", tags=["validation"])

    # Register exception handlers
    _register_exception_handlers(app)

    logger.info("ReformLab API v%s initialized", reformlab.__version__)

    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for domain errors."""
    from reformlab.interfaces.errors import (
        ConfigurationError,
        SimulationError,
        ValidationErrors,
    )
    from reformlab.templates.registry import RegistryError

    @app.exception_handler(ConfigurationError)
    async def configuration_error_handler(
        request: object, exc: ConfigurationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "Configuration error",
                "what": exc.field_path,
                "why": f"Expected {exc.expected}, got {exc.actual!r}",
                "fix": exc.fix or f"Provide a valid {exc.expected}",
                "status_code": 422,
            },
        )

    @app.exception_handler(ValidationErrors)
    async def validation_errors_handler(
        request: object, exc: ValidationErrors
    ) -> JSONResponse:
        issues = [
            {"field": issue.field_path, "message": issue.message, "fix": issue.fix}
            for issue in exc.issues
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation failed",
                "what": f"{len(exc.issues)} issues found",
                "why": str(issues),
                "fix": "Fix the reported issues",
                "status_code": 422,
            },
        )

    @app.exception_handler(SimulationError)
    async def simulation_error_handler(
        request: object, exc: SimulationError
    ) -> JSONResponse:
        status_code = exc.status_code
        cause = exc.cause
        what = exc.message
        why = str(cause) if cause else "Unknown cause"
        fix = exc.fix or "Check server logs for details"
        error = "Simulation error"

        if status_code == 422:
            error = "Normalization error"
            cause_what = getattr(cause, "what", None)
            cause_why = getattr(cause, "why", None)
            cause_fix = getattr(cause, "fix", None)
            if isinstance(cause_what, str):
                what = cause_what
            if isinstance(cause_why, str):
                why = cause_why
            if isinstance(cause_fix, str):
                fix = cause_fix

        return JSONResponse(
            status_code=status_code,
            content={
                "error": error,
                "what": what,
                "why": why,
                "fix": fix,
                "status_code": status_code,
            },
        )

    @app.exception_handler(RegistryError)
    async def registry_error_handler(
        request: object, exc: RegistryError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not found",
                "what": exc.summary,
                "why": exc.reason,
                "fix": exc.fix,
                "status_code": 404,
            },
        )
