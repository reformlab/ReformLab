# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
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

SKIP_PATHS = {"/up", "/api/auth/login", "/api/health", "/api/docs", "/api/openapi.json"}

router = APIRouter()


def _prune_expired_sessions(now: float | None = None) -> None:
    """Remove expired sessions from the process-local session store."""
    current = time.monotonic() if now is None else now
    expired = [
        token
        for token, created_at in _active_sessions.items()
        if current - created_at > SESSION_TTL_SECONDS
    ]
    for token in expired:
        _active_sessions.pop(token, None)


def _prune_login_attempts(now: float | None = None) -> None:
    """Remove expired and empty rate-limit buckets."""
    current = time.monotonic() if now is None else now
    for client_ip, attempts in list(_login_attempts.items()):
        fresh_attempts = [t for t in attempts if current - t < _RATE_LIMIT_WINDOW]
        if fresh_attempts:
            _login_attempts[client_ip] = fresh_attempts
        else:
            _login_attempts.pop(client_ip, None)


def _check_rate_limit(client_ip: str) -> bool:
    """Return True if the IP is within rate limits, False if blocked."""
    _prune_login_attempts()
    return len(_login_attempts.get(client_ip, [])) < _RATE_LIMIT_MAX


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

        _prune_expired_sessions()

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

    _prune_expired_sessions()
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
