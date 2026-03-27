# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Validation/preflight routes — Story 20.7."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from reformlab.server.models import PreflightRequest, PreflightResponse
from reformlab.server.validation import run_checks

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/preflight", response_model=PreflightResponse)
async def preflight_validation(request: PreflightRequest) -> PreflightResponse:
    """Run pre-execution validation checks on a scenario.

    AC-2: Returns passed (overall pass/fail), checks[] (individual results),
    and warnings[] (non-blocking warnings) using an extensible check registry.

    The check registry allows EPIC-21 Story 21.5 to add trust-status rules
    without modifying the core validation infrastructure.
    """
    logger.debug("Running preflight validation for scenario")
    result = await run_checks(request)

    passed_status = "PASSED" if result.passed else "FAILED"
    logger.info(
        "Preflight validation %s: %d error checks, %d warnings",
        passed_status,
        len([c for c in result.checks if c.severity == "error"]),
        len(result.warnings),
    )

    return result
