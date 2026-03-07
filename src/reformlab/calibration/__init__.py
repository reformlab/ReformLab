"""Calibration subsystem public API.

Provides calibration target format definition, file loading, semantic
validation, governance integration, the calibration optimization engine,
holdout validation, and run manifest provenance capture (Epic 15).

Public API:
    - :class:`CalibrationTarget` — a single observed transition rate
    - :class:`CalibrationTargetSet` — an immutable validated collection
    - :func:`load_calibration_targets` — load from CSV, Parquet, or YAML
    - :exc:`CalibrationError` — base exception
    - :exc:`CalibrationTargetLoadError` — file loading/parsing errors
    - :exc:`CalibrationTargetValidationError` — semantic consistency errors
    - :exc:`CalibrationOptimizationError` — optimization failure errors
    - :exc:`CalibrationProvenanceError` — provenance capture/extraction errors
    - :class:`CalibrationConfig` — optimization run configuration
    - :class:`CalibrationResult` — optimization result with diagnostics
    - :class:`RateComparison` — per-target observed vs simulated rate comparison
    - :class:`FitMetrics` — aggregate fit metrics (MSE, MAE) for comparisons
    - :class:`HoldoutValidationResult` — side-by-side training/holdout metrics
    - :class:`CalibrationEngine` — runs calibration optimization
    - :func:`validate_holdout` — validate calibrated parameters against holdout data
    - :func:`capture_calibration_provenance` — aggregate governance entries for manifest
    - :func:`make_calibration_reference` — create calibration run reference entry
    - :func:`extract_calibrated_parameters` — extract TasteParameters from manifest assumptions

Story 15.1 / FR52 — Define calibration target format and load observed transition rates.
Story 15.2 / FR52 — CalibrationEngine with objective function optimization.
Story 15.3 / FR53 — Calibration validation against holdout data.
Story 15.4 / FR52 — Record calibrated parameters in run manifests.
"""

from __future__ import annotations

from reformlab.calibration.engine import CalibrationEngine
from reformlab.calibration.errors import (
    CalibrationError,
    CalibrationOptimizationError,
    CalibrationProvenanceError,
    CalibrationTargetLoadError,
    CalibrationTargetValidationError,
)
from reformlab.calibration.loader import load_calibration_targets
from reformlab.calibration.provenance import (
    capture_calibration_provenance,
    extract_calibrated_parameters,
    make_calibration_reference,
)
from reformlab.calibration.types import (
    CalibrationConfig,
    CalibrationResult,
    CalibrationTarget,
    CalibrationTargetSet,
    FitMetrics,
    HoldoutValidationResult,
    RateComparison,
)
from reformlab.calibration.validation import validate_holdout

__all__ = [
    "CalibrationConfig",
    "CalibrationEngine",
    "CalibrationError",
    "CalibrationOptimizationError",
    "CalibrationProvenanceError",
    "CalibrationResult",
    "CalibrationTarget",
    "CalibrationTargetLoadError",
    "CalibrationTargetSet",
    "CalibrationTargetValidationError",
    "FitMetrics",
    "HoldoutValidationResult",
    "RateComparison",
    "capture_calibration_provenance",
    "extract_calibrated_parameters",
    "load_calibration_targets",
    "make_calibration_reference",
    "validate_holdout",
]
