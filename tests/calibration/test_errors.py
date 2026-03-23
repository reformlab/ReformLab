# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for calibration error hierarchy — Story 15.1 / AC-4, Story 15.2."""

from __future__ import annotations

import pytest

from reformlab.calibration.errors import (
    CalibrationError,
    CalibrationOptimizationError,
    CalibrationTargetLoadError,
    CalibrationTargetValidationError,
)


class TestCalibrationErrorHierarchy:
    """AC-4: Error hierarchy is correctly structured."""

    def test_calibration_error_is_exception(self) -> None:
        """Given CalibrationError, then it is a subclass of Exception."""
        assert issubclass(CalibrationError, Exception)

    def test_validation_error_is_calibration_error(self) -> None:
        """Given CalibrationTargetValidationError, then it is a subclass of CalibrationError."""
        assert issubclass(CalibrationTargetValidationError, CalibrationError)

    def test_load_error_is_calibration_error(self) -> None:
        """Given CalibrationTargetLoadError, then it is a subclass of CalibrationError."""
        assert issubclass(CalibrationTargetLoadError, CalibrationError)

    def test_validation_error_is_not_load_error(self) -> None:
        """Given CalibrationTargetValidationError and CalibrationTargetLoadError, then they are siblings."""
        assert not issubclass(CalibrationTargetValidationError, CalibrationTargetLoadError)
        assert not issubclass(CalibrationTargetLoadError, CalibrationTargetValidationError)

    def test_validation_error_can_be_raised_and_caught(self) -> None:
        """Given a CalibrationTargetValidationError, when raised, then catchable as CalibrationError."""
        with pytest.raises(CalibrationError):
            raise CalibrationTargetValidationError("rate out of range")

    def test_load_error_can_be_raised_and_caught(self) -> None:
        """Given a CalibrationTargetLoadError, when raised, then catchable as CalibrationError."""
        with pytest.raises(CalibrationError):
            raise CalibrationTargetLoadError("missing column: source_label")

    def test_error_messages_are_preserved(self) -> None:
        """Given an error with a message, when raised, then str() returns the message."""
        msg = "observed_rate=-0.5 is out of range"
        exc = CalibrationTargetValidationError(msg)
        assert msg in str(exc)


class TestCalibrationOptimizationError:
    """Story 15.2 / Task 4: CalibrationOptimizationError hierarchy."""

    def test_optimization_error_is_calibration_error(self) -> None:
        """Given CalibrationOptimizationError, then it is a subclass of CalibrationError."""
        assert issubclass(CalibrationOptimizationError, CalibrationError)

    def test_optimization_error_is_exception(self) -> None:
        """Given CalibrationOptimizationError, then it is a subclass of Exception."""
        assert issubclass(CalibrationOptimizationError, Exception)

    def test_optimization_error_catchable_as_calibration_error(self) -> None:
        """Given CalibrationOptimizationError raised, when caught as CalibrationError, succeeds."""
        with pytest.raises(CalibrationError):
            raise CalibrationOptimizationError("scipy optimization failed for domain='vehicle': ...")

    def test_optimization_error_message_preserved(self) -> None:
        """Given an error with a message, when raised, then str() returns the message."""
        msg = "No calibration targets for domain='heating'"
        exc = CalibrationOptimizationError(msg)
        assert msg in str(exc)

    def test_optimization_error_is_not_load_error(self) -> None:
        """Given CalibrationOptimizationError, it is a sibling of load/validation errors."""
        assert not issubclass(CalibrationOptimizationError, CalibrationTargetLoadError)
        assert not issubclass(CalibrationOptimizationError, CalibrationTargetValidationError)
