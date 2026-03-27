# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Data-layer errors for evidence asset validation.

This module defines explicit error types for evidence asset operations:
- EvidenceAssetError: Validation failures for DataAssetDescriptor

Story 21.1 / FR: Trust-governed open & synthetic evidence foundation.
"""

from __future__ import annotations


class EvidenceAssetError(Exception):
    """Raised when evidence asset validation fails.

    Indicates missing required fields, invalid field types, invalid literal
    values, unsupported origin/access_mode/trust_status combinations, or
    other DataAssetDescriptor validation issues.

    Error messages follow the pattern:
    "DataAssetDescriptor validation failed: {field_name} {issue} - {fix_suggestion}"

    Story 21.1 / AC8, AC14.
    """

    pass
