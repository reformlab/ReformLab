# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Portfolio conflict and resolution enums.

Story 12.2: Implement portfolio compatibility validation and conflict resolution
"""

from __future__ import annotations

from enum import Enum


class ConflictType(Enum):
    """Types of conflicts that can occur in a portfolio."""

    SAME_POLICY_TYPE = "same_policy_type"
    OVERLAPPING_CATEGORIES = "overlapping_categories"
    OVERLAPPING_YEARS = "overlapping_years"
    PARAMETER_MISMATCH = "parameter_mismatch"


class ResolutionStrategy(Enum):
    """Strategies for resolving portfolio conflicts."""

    ERROR = "error"
    SUM = "sum"
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    MAX = "max"
