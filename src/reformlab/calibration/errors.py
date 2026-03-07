"""Calibration subsystem error hierarchy.

Provides subsystem-specific exceptions for target loading, schema validation,
semantic consistency checks, and optimization failures.

Story 15.1 / FR52 — Define calibration target format and load observed transition rates.
Story 15.2 / FR52 — CalibrationEngine with objective function optimization.
"""

from __future__ import annotations


class CalibrationError(Exception):
    """Base error for calibration subsystem."""


class CalibrationTargetValidationError(CalibrationError):
    """Raised when calibration targets fail semantic consistency checks.

    Examples: rates sum > 1.0 for a (domain, period, from_state) group;
    observed_rate outside [0.0, 1.0]; empty required string fields.
    """


class CalibrationTargetLoadError(CalibrationError):
    """Raised when a calibration target file cannot be loaded or parsed.

    Examples: missing required columns; unsupported file format;
    YAML schema validation failure; duplicate (domain, period, from_state, to_state) rows.
    """


class CalibrationOptimizationError(CalibrationError):
    """Raised when calibration optimization fails (convergence, invalid parameters, input validation)."""
