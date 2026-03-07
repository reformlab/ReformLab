"""Calibration schema package.

Contains JSON Schema files for YAML target validation.

This package exists so that ``importlib.resources.files("reformlab.calibration.schema")``
can locate the bundled ``calibration-targets.schema.json`` file at both development
time and when installed as a wheel.

Story 15.1 / FR52 — Define calibration target format and load observed transition rates (schema definition).
Story 15.2 / FR52 — CalibrationEngine with objective function optimization (schema used by loader).
"""

from __future__ import annotations
