"""Calibration provenance capture, reference creation, and parameter extraction.

Provides functions to record calibrated discrete choice parameters, optimization
diagnostics, calibration target metadata, and holdout validation metrics in run
manifests. Supports round-trip parameter extraction from manifest assumptions.

Story 15.4 / FR52 — Record calibrated parameters in run manifests.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from reformlab.calibration.errors import CalibrationProvenanceError
from reformlab.calibration.types import (
    CalibrationResult,
    CalibrationTargetSet,
    HoldoutValidationResult,
)

if TYPE_CHECKING:
    from reformlab.discrete_choice.types import TasteParameters

logger = logging.getLogger(__name__)


# ============================== Public Functions ==============================


def capture_calibration_provenance(
    calibration_result: CalibrationResult,
    *,
    target_set: CalibrationTargetSet | None = None,
    holdout_result: HoldoutValidationResult | None = None,
    source_label: str = "calibration_engine",
) -> list[dict[str, Any]]:
    """Aggregate all calibration governance entries for manifest recording.

    Collects assumption entries from the calibration result, and optionally
    from the calibration target set and holdout validation result. Each entry
    follows the AssumptionEntry format (key, value, source, is_default).

    The source_label is propagated to all entries for consistent attribution.

    Args:
        calibration_result: Result from CalibrationEngine.calibrate().
        target_set: Optional CalibrationTargetSet used for calibration.
        holdout_result: Optional HoldoutValidationResult from validation.
        source_label: Source label for all entries. Defaults to
            "calibration_engine".

    Returns:
        List of AssumptionEntry-compatible dicts, sorted by key.

    Raises:
        TypeError: If calibration_result is not a CalibrationResult.

    Story 15.4 / FR52 — Record calibrated parameters in run manifests.
    """
    if not isinstance(calibration_result, CalibrationResult):
        msg = (
            f"calibration_result must be a CalibrationResult, "
            f"got {type(calibration_result).__name__}"
        )
        raise TypeError(msg)

    entries: list[dict[str, Any]] = []

    # 1. Always include calibration result
    entries.append(
        calibration_result.to_governance_entry(source_label=source_label)
    )

    # 2. Optionally include target set metadata
    if target_set is not None:
        entries.append(
            target_set.to_governance_entry(source_label=source_label)
        )

    # 3. Optionally include holdout validation
    if holdout_result is not None:
        entries.append(
            holdout_result.to_governance_entry(source_label=source_label)
        )

    logger.info(
        "event=calibration_provenance_captured domain=%s n_entries=%d",
        calibration_result.domain,
        len(entries),
    )

    return sorted(entries, key=lambda e: e["key"])


def make_calibration_reference(
    calibration_manifest_id: str,
    *,
    calibration_integrity_hash: str = "",
) -> dict[str, Any]:
    """Create an AssumptionEntry-compatible reference to a calibration run.

    Used when a simulation run uses calibrated parameters from a prior
    calibration run. The reference enables traceability from the simulation
    manifest back to the calibration manifest.

    Args:
        calibration_manifest_id: Manifest ID (UUID) of the calibration run.
        calibration_integrity_hash: Optional integrity hash of the calibration
            manifest for tamper-proof verification.

    Returns:
        AssumptionEntry-compatible dict with key "calibration_reference".

    Raises:
        CalibrationProvenanceError: If calibration_manifest_id is empty.

    Story 15.4 / FR52 — Record calibrated parameters in run manifests.
    """
    if not calibration_manifest_id or not calibration_manifest_id.strip():
        raise CalibrationProvenanceError(
            "calibration_manifest_id must be a non-empty string"
        )

    value: dict[str, str] = {
        "calibration_manifest_id": calibration_manifest_id,
    }
    if calibration_integrity_hash:
        value["calibration_integrity_hash"] = calibration_integrity_hash

    return {
        "key": "calibration_reference",
        "value": value,
        "source": "calibration_provenance",
        "is_default": False,
    }


def extract_calibrated_parameters(
    assumptions: list[dict[str, Any]],
    domain: str,
) -> TasteParameters:
    """Extract TasteParameters from manifest assumptions for a given domain.

    Scans the assumptions list for an entry with key "calibration_result"
    whose value["domain"] matches the requested domain. Extracts the
    optimized_beta_cost and returns a TasteParameters instance.

    Args:
        assumptions: List of AssumptionEntry-compatible dicts (from RunManifest).
        domain: Decision domain to extract parameters for (e.g., "vehicle").

    Returns:
        TasteParameters with the exact beta_cost from the calibration result.

    Raises:
        CalibrationProvenanceError: If no calibration_result entry is found
            for the requested domain, if assumptions is empty, if multiple
            entries exist for the same domain, or if optimized_beta_cost is
            not a numeric type.

    Story 15.4 / FR52 — Record calibrated parameters in run manifests.
    """
    from reformlab.discrete_choice.types import TasteParameters

    if not assumptions:
        raise CalibrationProvenanceError(
            "Cannot extract calibrated parameters from empty assumptions list"
        )

    matches = [
        entry for entry in assumptions
        if entry.get("key") == "calibration_result"
        and entry.get("value", {}).get("domain") == domain
    ]

    if len(matches) > 1:
        raise CalibrationProvenanceError(
            f"Found {len(matches)} calibration_result entries for domain={domain!r}; "
            "expected exactly 1. Manifest may have been corrupted or incorrectly assembled."
        )

    if not matches:
        raise CalibrationProvenanceError(
            f"No calibration_result entry found for domain={domain!r} "
            f"in assumptions list (checked {len(assumptions)} entries)"
        )

    value = matches[0].get("value", {})
    beta_cost = value.get("optimized_beta_cost")
    if beta_cost is None:
        raise CalibrationProvenanceError(
            f"calibration_result entry for domain={domain!r} is missing "
            "'optimized_beta_cost' in value"
        )
    if not isinstance(beta_cost, (float, int)) or isinstance(beta_cost, bool):
        raise CalibrationProvenanceError(
            f"Expected 'optimized_beta_cost' for domain={domain!r} to be a float or int, "
            f"but found type {type(beta_cost).__name__!r} with value {beta_cost!r}"
        )

    logger.info(
        "event=calibration_parameters_extracted domain=%s beta_cost=%f",
        domain,
        beta_cost,
    )

    return TasteParameters(beta_cost=float(beta_cost))
