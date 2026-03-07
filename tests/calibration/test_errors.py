"""Tests for calibration error hierarchy — Story 15.1 / AC-4."""

from __future__ import annotations

import pytest

from reformlab.calibration.errors import (
    CalibrationError,
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
