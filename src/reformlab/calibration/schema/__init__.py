"""Calibration schema package.

Contains JSON Schema files for YAML target validation.

This package exists so that ``importlib.resources.files("reformlab.calibration.schema")``
can locate the bundled ``calibration-targets.schema.json`` file at both development
time and when installed as a wheel.
"""

from __future__ import annotations
