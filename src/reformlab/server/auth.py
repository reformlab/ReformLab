"""Shared-password authentication middleware for MVP.

Designed for 2-10 trusted colleagues. Sessions expire after 24 hours.
Server restart clears all sessions.
"""

from __future__ import annotations

import logging
import os
import secrets
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from reformlab.server.models import LoginRequest, LoginResponse

logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS = 24 * 60 * 60  # 24 hours

# In-memory session store — maps token to creation timestamp
_active_sessions: dict[str, float] = {}

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

        # Check session expiry
        created_at = _active_sessions.get(token, 0.0)
        if time.monotonic() - created_at > SESSION_TTL_SECONDS:
            _active_sessions.pop(token, None)
            return JSONResponse(
                status_code=401,
                content={"error": "Session expired"},
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
    _active_sessions[token] = time.monotonic()
    logger.info("New session created (active sessions: %d)", len(_active_sessions))
    return LoginResponse(token=token)
