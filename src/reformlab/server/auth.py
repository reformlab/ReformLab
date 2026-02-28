"""Shared-password authentication middleware for MVP.

Designed for 2-10 trusted colleagues. No expiry, no persistence.
Server restart clears all sessions.
"""

from __future__ import annotations

import logging
import os
import secrets

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from reformlab.server.models import LoginRequest, LoginResponse

logger = logging.getLogger(__name__)

# In-memory session store — cleared on server restart
_active_sessions: set[str] = set()

SKIP_PATHS = {"/api/auth/login", "/api/docs", "/api/openapi.json"}

router = APIRouter()


class AuthMiddleware(BaseHTTPMiddleware):
    """Shared-password auth for MVP (2-10 trusted colleagues)."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if request.url.path in SKIP_PATHS:
            return await call_next(request)

        token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not token or token not in _active_sessions:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized"},
            )

        return await call_next(request)


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> LoginResponse:
    """Validate password and issue a session token."""
    from fastapi import HTTPException

    expected = os.environ.get("REFORMLAB_PASSWORD", "")
    if not expected:
        logger.warning("REFORMLAB_PASSWORD not set — all logins will fail")
        raise HTTPException(status_code=401, detail="Server misconfigured: no password set")

    if not secrets.compare_digest(body.password, expected):
        raise HTTPException(status_code=401, detail="Invalid password")

    token = secrets.token_hex(32)
    _active_sessions.add(token)
    logger.info("New session created (active sessions: %d)", len(_active_sessions))
    return LoginResponse(token=token)
