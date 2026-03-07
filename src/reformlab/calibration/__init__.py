"""Calibration subsystem public API.

Provides calibration target format definition, file loading, semantic
validation, and governance integration for the discrete choice calibration
engine (Epic 15).

Public API:
    - :class:`CalibrationTarget` — a single observed transition rate
    - :class:`CalibrationTargetSet` — an immutable validated collection
    - :func:`load_calibration_targets` — load from CSV, Parquet, or YAML
    - :exc:`CalibrationError` — base exception
    - :exc:`CalibrationTargetLoadError` — file loading/parsing errors
    - :exc:`CalibrationTargetValidationError` — semantic consistency errors

Story 15.1 / FR52 — Define calibration target format and load observed transition rates.
"""

from __future__ import annotations

from reformlab.calibration.errors import (
    CalibrationError,
    CalibrationTargetLoadError,
    CalibrationTargetValidationError,
)
from reformlab.calibration.loader import load_calibration_targets
from reformlab.calibration.types import CalibrationTarget, CalibrationTargetSet

__all__ = [
    "CalibrationError",
    "CalibrationTarget",
    "CalibrationTargetLoadError",
    "CalibrationTargetSet",
    "CalibrationTargetValidationError",
    "load_calibration_targets",
]
