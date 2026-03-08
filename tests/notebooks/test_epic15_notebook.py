"""Static checks for the Epic 15 calibration workflow notebook — Story 15.5 / FR52."""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).resolve().parents[2] / "notebooks" / "guides" / "10_calibration_workflow.ipynb"
CI_WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def _load_notebook() -> dict[str, object]:
    with NOTEBOOK_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _cell_source(cell: dict[str, object]) -> str:
    source = cell.get("source", [])
    if isinstance(source, list):
        return "".join(part for part in source if isinstance(part, str))
    if isinstance(source, str):
        return source
    return ""


def _all_sources(notebook: dict[str, object]) -> str:
    cells = notebook.get("cells", [])
    if not isinstance(cells, list):
        return ""
    return "\n".join(_cell_source(cell) for cell in cells if isinstance(cell, dict))


def test_notebook_exists() -> None:
    """Notebook deliverable exists at the expected path."""
    assert NOTEBOOK_PATH.exists()


def test_outputs_cleared() -> None:
    """Committed notebook keeps outputs empty for CI execution."""
    notebook = _load_notebook()
    cells = notebook.get("cells", [])
    assert isinstance(cells, list)
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        if cell.get("cell_type") != "code":
            continue
        assert cell.get("execution_count") is None
        assert cell.get("outputs") == []


def test_uses_public_api() -> None:
    """Notebook uses public API surfaces and avoids internal imports."""
    source = _all_sources(_load_notebook())
    # Imports from public calibration API
    assert "from reformlab.calibration import (" in source
    # Imports from public discrete choice API
    assert "from reformlab.discrete_choice import (" in source
    # No internal submodule imports (only top-level public API)
    assert "from reformlab.calibration." not in source
    assert "from reformlab.discrete_choice." not in source
    # No OpenFisca imports
    assert "from openfisca" not in source
    assert "import openfisca" not in source


def test_required_sections() -> None:
    """Notebook includes all required content sections."""
    source = _all_sources(_load_notebook())
    assert "Section 0: Setup" in source
    assert "Section 1: Load Calibration Targets" in source
    assert "Section 2: Build Cost Matrix" in source
    assert "Section 3: Run Calibration Engine" in source
    assert "Section 4: Visualize Training Fit" in source
    assert "Section 5: Holdout Validation" in source
    assert "Section 6: Governance Provenance" in source
    assert "Section 7: Parameter Round-Trip" in source
    assert "Section 8: Using Calibrated Parameters" in source
    assert "Section 9: Summary and Next Steps" in source


def test_key_api_calls() -> None:
    """Notebook includes key calibration workflow API calls."""
    source = _all_sources(_load_notebook())
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


def test_ci_includes_notebook() -> None:
    """CI workflow includes nbmake execution of this notebook."""
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "uv run pytest --nbmake notebooks/guides/10_calibration_workflow.ipynb -v" in ci_workflow
