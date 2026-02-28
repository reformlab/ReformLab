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
from fastapi.responses import JSONResponse

import reformlab
from reformlab.server.auth import AuthMiddleware
from reformlab.server.auth import router as auth_router
from reformlab.server.routes.exports import router as exports_router
from reformlab.server.routes.indicators import comparison_router
from reformlab.server.routes.indicators import router as indicators_router
from reformlab.server.routes.populations import router as populations_router
from reformlab.server.routes.runs import router as runs_router
from reformlab.server.routes.scenarios import router as scenarios_router
from reformlab.server.routes.templates import router as templates_router

logger = logging.getLogger(__name__)


def _cors_origins() -> list[str]:
    """Build CORS allowed origins list."""
    origins = ["http://localhost:5173"]  # Vite dev server
    extra = os.environ.get("REFORMLAB_CORS_ORIGINS", "")
    if extra:
        origins.extend(o.strip() for o in extra.split(",") if o.strip())
    return origins


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ReformLab API",
        version=reformlab.__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    # CORS must be added BEFORE auth middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth middleware (skips /api/auth/login and /api/docs)
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
        return JSONResponse(
            status_code=500,
            content={
                "error": "Simulation error",
                "what": exc.message,
                "why": str(exc.cause) if exc.cause else "Unknown cause",
                "fix": exc.fix or "Check server logs for details",
                "status_code": 500,
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
