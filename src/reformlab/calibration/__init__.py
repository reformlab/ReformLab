"""Calibration subsystem public API.

Provides calibration target format definition, file loading, semantic
validation, governance integration, and the calibration optimization engine
(Epic 15).

Public API:
    - :class:`CalibrationTarget` — a single observed transition rate
    - :class:`CalibrationTargetSet` — an immutable validated collection
    - :func:`load_calibration_targets` — load from CSV, Parquet, or YAML
    - :exc:`CalibrationError` — base exception
    - :exc:`CalibrationTargetLoadError` — file loading/parsing errors
    - :exc:`CalibrationTargetValidationError` — semantic consistency errors
    - :exc:`CalibrationOptimizationError` — optimization failure errors
    - :class:`CalibrationConfig` — optimization run configuration
    - :class:`CalibrationResult` — optimization result with diagnostics
    - :class:`RateComparison` — per-target observed vs simulated rate comparison
    - :class:`CalibrationEngine` — runs calibration optimization

Story 15.1 / FR52 — Define calibration target format and load observed transition rates.
Story 15.2 / FR52 — CalibrationEngine with objective function optimization.
"""

from __future__ import annotations

from reformlab.calibration.engine import CalibrationEngine
from reformlab.calibration.errors import (
    CalibrationError,
    CalibrationOptimizationError,
    CalibrationTargetLoadError,
    CalibrationTargetValidationError,
)
from reformlab.calibration.loader import load_calibration_targets
from reformlab.calibration.types import (
    CalibrationConfig,
    CalibrationResult,
    CalibrationTarget,
    CalibrationTargetSet,
    RateComparison,
)

__all__ = [
    "CalibrationConfig",
    "CalibrationEngine",
    "CalibrationError",
    "CalibrationOptimizationError",
    "CalibrationResult",
    "CalibrationTarget",
    "CalibrationTargetLoadError",
    "CalibrationTargetSet",
    "CalibrationTargetValidationError",
    "RateComparison",
    "load_calibration_targets",
]
