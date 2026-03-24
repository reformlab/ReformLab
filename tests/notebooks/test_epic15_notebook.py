# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Static checks for the Epic 15 calibration workflow demo — Story 15.5 / FR52."""

from __future__ import annotations

from pathlib import Path

DEMO_PATH = Path(__file__).resolve().parents[2] / "demos" / "guides" / "10_calibration_workflow.py"
CI_WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def _read_source() -> str:
    return DEMO_PATH.read_text(encoding="utf-8")


def test_demo_exists() -> None:
    """Demo script exists at the expected path."""
    assert DEMO_PATH.exists()


def test_uses_public_api() -> None:
    """Demo uses public API surfaces and avoids internal imports."""
    source = _read_source()
    assert "from reformlab.calibration import" in source
    assert "from reformlab.discrete_choice import" in source
    assert "from openfisca" not in source
    assert "import openfisca" not in source


def test_required_sections() -> None:
    """Demo includes all required content sections."""
    source = _read_source()
    assert "Section 0: Setup" in source
    assert "Section 1: Load Calibration Targets" in source
    assert "Section 2: Build Cost Matrix" in source
    assert "Section 3: Run Calibration Engine" in source
    assert "Section 4: Visualize Training Fit" in source
    assert "Section 5: Holdout Validation" in source
    assert "Section 6: Governance Provenance" in source
    assert "Section 7: Parameter Round-Trip" in source
    assert "Section 8: Using Calibrated Parameters" in source
    assert "Section 9: Summary" in source


def test_key_api_calls() -> None:
    """Demo includes key calibration workflow API calls."""
    source = _read_source()
    assert "load_calibration_targets(" in source
    assert "CalibrationEngine(" in source
    assert ".calibrate()" in source
    assert "validate_holdout(" in source
    assert "capture_calibration_provenance(" in source
    assert "make_calibration_reference(" in source
    assert "extract_calibrated_parameters(" in source
    assert "TasteParameters(" in source
    assert "CostMatrix(" in source
    assert "RunManifest(" in source


def test_ci_includes_demo() -> None:
    """CI workflow includes execution of this demo."""
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "uv run python demos/guides/10_calibration_workflow.py" in ci_workflow
