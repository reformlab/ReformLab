"""Calibration target domain types.

Defines CalibrationTarget and CalibrationTargetSet as immutable frozen
dataclasses representing observed real-world transition rates (e.g., vehicle
adoption from ADEME/SDES) used to calibrate discrete choice taste parameters.

Story 15.1 / FR52 — Define calibration target format and load observed transition rates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from reformlab.calibration.errors import (
    CalibrationTargetLoadError,
    CalibrationTargetValidationError,
)

logger = logging.getLogger(__name__)

# ============================== Target Dataclass ==============================


@dataclass(frozen=True)
class CalibrationTarget:
    """A single observed transition rate from real-world institutional data.

    Attributes:
        domain: Decision domain (e.g., ``'vehicle'``, ``'heating'``).
        period: Reference year (e.g., ``2022``).
        from_state: Origin state (e.g., ``'petrol'``, ``'gas'``).
        to_state: Destination alternative (e.g., ``'buy_electric'``, ``'heat_pump'``).
        observed_rate: Fraction of households in ``from_state`` that chose ``to_state``.
            Must be in [0.0, 1.0].
        source_label: Human-readable data source identifier (e.g., ``'SDES vehicle fleet 2022'``).
        source_metadata: Optional key-value metadata (dataset id, URL, vintage year, etc.).
    """

    domain: str
    period: int
    from_state: str
    to_state: str
    observed_rate: float
    source_label: str
    source_metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.domain:
            raise CalibrationTargetValidationError("domain must be non-empty")
        if not self.from_state:
            raise CalibrationTargetValidationError("from_state must be non-empty")
        if not self.to_state:
            raise CalibrationTargetValidationError("to_state must be non-empty")
        if not (0.0 <= self.observed_rate <= 1.0):
            raise CalibrationTargetValidationError(
                f"observed_rate={self.observed_rate!r} is out of range; must be in [0.0, 1.0]"
            )


# ============================== Target Set ==============================


@dataclass(frozen=True)
class CalibrationTargetSet:
    """Immutable, validated collection of calibration targets across domains and periods.

    Attributes:
        targets: All calibration targets held in this set.
    """

    targets: tuple[CalibrationTarget, ...]

    def by_domain(self, domain: str) -> CalibrationTargetSet:
        """Return a new CalibrationTargetSet containing only targets for ``domain``.

        Given a domain name, when called on a multi-domain set, returns a filtered
        set with only that domain's targets. Returns an empty set if no match.
        """
        filtered = tuple(t for t in self.targets if t.domain == domain)
        return CalibrationTargetSet(targets=filtered)

    def validate_consistency(self) -> None:
        """Assert semantic consistency of the target collection.

        Checks performed (in order):

        1. **Duplicate detection** — ``(domain, period, from_state, to_state)`` must be
           unique. Raises :class:`CalibrationTargetLoadError` immediately.

        2. **Rate sum constraint** — For each ``(domain, period, from_state)`` group,
           the sum of ``observed_rate`` values must be ≤ 1.0 + 1e-9.
           Raises :class:`CalibrationTargetValidationError` on violation.

        Raises:
            CalibrationTargetLoadError: Duplicate ``(domain, period, from_state, to_state)`` row.
            CalibrationTargetValidationError: Rate sum exceeds ``1.0 + 1e-9`` for any group.
        """
        # --- Duplicate detection (always a hard error) ---
        seen: set[tuple[str, int, str, str]] = set()
        for t in self.targets:
            key = (t.domain, t.period, t.from_state, t.to_state)
            if key in seen:
                raise CalibrationTargetLoadError(
                    f"duplicate row detected: domain={t.domain!r} period={t.period!r} "
                    f"from_state={t.from_state!r} to_state={t.to_state!r} — "
                    "deduplicate before loading"
                )
            seen.add(key)

        # --- Rate sum constraint ---
        group_sums: dict[tuple[str, int, str], float] = {}
        for t in self.targets:
            group_key = (t.domain, t.period, t.from_state)
            group_sums[group_key] = group_sums.get(group_key, 0.0) + t.observed_rate

        for (domain, period, from_state), total in group_sums.items():
            if total > 1.0 + 1e-9:
                raise CalibrationTargetValidationError(
                    f"rates sum to {total:.10f} > 1.0 for group "
                    f"domain={domain!r} period={period!r} from_state={from_state!r}"
                )

        logger.debug(
            "event=consistency_validated n_groups=%d n_targets=%d",
            len(group_sums),
            len(self.targets),
        )

    def to_governance_entry(self, *, source_label: str = "calibration_targets") -> dict[str, Any]:
        """Return an AssumptionEntry-compatible dict for governance manifests.

        Given a CalibrationTargetSet, when called, returns a dict with
        ``key``, ``value``, ``source``, and ``is_default`` fields compatible
        with the governance manifest format (Story 15.4).
        """
        return {
            "key": "calibration_targets",
            "value": {
                "domains": sorted({t.domain for t in self.targets}),
                "n_targets": len(self.targets),
                "periods": sorted({t.period for t in self.targets}),
                "sources": sorted({t.source_label for t in self.targets}),
            },
            "source": source_label,
            "is_default": False,
        }
