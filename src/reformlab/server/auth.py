"""Shared-password authentication middleware for MVP.

Designed for 2-10 trusted colleagues. Sessions expire after 24 hours.
Server restart clears all sessions.
"""

from __future__ import annotations

import logging
import os
import secrets
import time
from collections import defaultdict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from reformlab.server.models import LoginRequest, LoginResponse

logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS = 24 * 60 * 60  # 24 hours

# Rate limiting: max 5 login attempts per IP per 15-minute window
_RATE_LIMIT_MAX = 5
_RATE_LIMIT_WINDOW = 15 * 60  # seconds

# In-memory session store — maps token to creation timestamp
_active_sessions: dict[str, float] = {}

# Rate limiting store — maps IP to list of attempt timestamps
_login_attempts: dict[str, list[float]] = defaultdict(list)

SKIP_PATHS = {"/api/auth/login", "/api/health", "/api/docs", "/api/openapi.json"}

router = APIRouter()


def _check_rate_limit(client_ip: str) -> bool:
    """Return True if the IP is within rate limits, False if blocked."""
    now = time.monotonic()
    # Prune old attempts outside the window
    attempts = _login_attempts[client_ip]
    _login_attempts[client_ip] = [t for t in attempts if now - t < _RATE_LIMIT_WINDOW]
    return len(_login_attempts[client_ip]) < _RATE_LIMIT_MAX


def _record_attempt(client_ip: str) -> None:
    """Record a login attempt for rate limiting."""
    _login_attempts[client_ip].append(time.monotonic())


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
async def login(body: LoginRequest, request: Request) -> LoginResponse:
    """Validate password and issue a session token."""
    from fastapi import HTTPException

    client_ip = request.client.host if request.client else "unknown"

    # Rate limit check
    if not _check_rate_limit(client_ip):
        logger.warning("Rate limit exceeded for IP %s", client_ip)
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again in 15 minutes.",
        )

    expected = os.environ.get("REFORMLAB_PASSWORD", "")
    if not expected:
        logger.warning("REFORMLAB_PASSWORD not set — all logins will fail")
        raise HTTPException(status_code=401, detail="Server misconfigured: no password set")

    if not secrets.compare_digest(body.password, expected):
        _record_attempt(client_ip)
        raise HTTPException(status_code=401, detail="Invalid password")

    token = secrets.token_hex(32)
    _active_sessions[token] = time.monotonic()
    logger.info("New session created (active sessions: %d)", len(_active_sessions))
    return LoginResponse(token=token)


@router.post("/logout")
async def logout(request: Request) -> JSONResponse:
    """Invalidate the current session token."""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if token and token in _active_sessions:
        _active_sessions.pop(token, None)
        logger.info("Session revoked (active sessions: %d)", len(_active_sessions))
    return JSONResponse(content={"status": "ok"})
