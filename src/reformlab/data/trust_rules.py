# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Trust-status rule evaluation for evidence assets.

Pure-function rules that evaluate the trust status of data assets and produce
warnings for non-production-safe statuses. No blocking — warning-only enforcement.

Story 21.5 — separate calibration targets from validation benchmarks and
implement trust-status rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from reformlab.data.descriptor import DataAssetDescriptor

_NON_PRODUCTION_STATUSES: tuple[str, ...] = (
    "exploratory",
    "demo-only",
    "validation-pending",
    "not-for-public-inference",
)


@dataclass(frozen=True)
class TrustCheckResult:
    """Result of a trust-status check on a single asset.

    Attributes
    ----------
    asset_id : str
        Identifier of the checked asset.
    trust_status : str
        The trust status value of the asset.
    status : Literal["ok", "warning"]
        ``"ok"`` if production-safe, ``"warning"`` otherwise.
    message : str
        Human-readable explanation.
    """

    asset_id: str
    trust_status: str
    status: Literal["ok", "warning"]
    message: str


def check_asset_trust(descriptor: DataAssetDescriptor) -> TrustCheckResult:
    """Evaluate trust status of a single asset descriptor.

    Parameters
    ----------
    descriptor : DataAssetDescriptor
        The asset to check.

    Returns
    -------
    TrustCheckResult
        ``status="ok"`` if production-safe, ``status="warning"`` otherwise.
    """
    if descriptor.trust_status == "production-safe":
        return TrustCheckResult(
            asset_id=descriptor.asset_id,
            trust_status=descriptor.trust_status,
            status="ok",
            message=f"Asset '{descriptor.name}' is production-safe",
        )

    return TrustCheckResult(
        asset_id=descriptor.asset_id,
        trust_status=descriptor.trust_status,
        status="warning",
        message=(
            f"Asset '{descriptor.name}' has trust status "
            f"'{descriptor.trust_status}' — results should be treated "
            f"as {descriptor.trust_status}"
        ),
    )


def check_multiple_assets(
    descriptors: tuple[DataAssetDescriptor, ...],
) -> tuple[TrustCheckResult, ...]:
    """Evaluate trust status of multiple asset descriptors.

    Parameters
    ----------
    descriptors : tuple[DataAssetDescriptor, ...]
        Assets to check.

    Returns
    -------
    tuple[TrustCheckResult, ...]
        One result per descriptor, in the same order.
    """
    return tuple(check_asset_trust(d) for d in descriptors)


def summarize_trust_warnings(
    results: tuple[TrustCheckResult, ...],
) -> str | None:
    """Summarize all warning results into a human-readable string.

    Parameters
    ----------
    results : tuple[TrustCheckResult, ...]
        Results from ``check_asset_trust`` or ``check_multiple_assets``.

    Returns
    -------
    str | None
        Summary of warnings, or ``None`` if all assets are ok.
    """
    warnings = [r for r in results if r.status == "warning"]
    if not warnings:
        return None

    lines = [r.message for r in warnings]
    return "; ".join(lines)
