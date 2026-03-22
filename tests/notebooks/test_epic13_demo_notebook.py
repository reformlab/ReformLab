"""Static checks for the Epic 13 custom templates notebook content.

Story 13.4: Validate custom templates in portfolios and build notebook demo.
Tests AC6: static notebook validation (existence, cleared outputs, public API,
key API calls, section coverage, portfolio comparison, YAML round-trip).

These checks validate notebook structure without launching a Jupyter kernel.
"""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[2] / "notebooks" / "guides" / "07_custom_templates.ipynb"
)
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


def test_epic13_notebook_exists() -> None:
    """Notebook deliverable exists at expected path (AC6-a)."""
    assert NOTEBOOK_PATH.exists()


def test_epic13_notebook_outputs_are_cleared() -> None:
    """All code cells have execution_count=None, outputs=[] (AC6-b)."""
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


def test_epic13_notebook_uses_public_api_only() -> None:
    """Uses public API imports only — no computation internals or openfisca (AC6-c).

    Must contain key API calls: register_policy_type, register_custom_template,
    PolicyPortfolio, validate_compatibility.
    """
    source = _all_sources(_load_notebook())
    # Required public API calls
    assert "register_policy_type" in source
    assert "register_custom_template" in source
    assert "PolicyPortfolio" in source
    assert "validate_compatibility" in source
    # No internal imports
    assert "reformlab.computation" not in source
    assert "from openfisca import" not in source


def test_epic13_notebook_covers_custom_template_lifecycle() -> None:
    """Contains key sections: Define a Custom Template, Register and Use,
    Portfolios with Custom Templates (AC6-d)."""
    source = _all_sources(_load_notebook())
    assert "Define a Custom Template" in source
    assert "Register and Use" in source
    assert "Portfolios with Custom Templates" in source


def test_epic13_notebook_covers_portfolio_comparison() -> None:
    """Contains portfolio comparison code (AC6-e)."""
    source = _all_sources(_load_notebook())
    assert "compare_vehicle_malus_decile_impacts" in source or "Compare Portfolios" in source
    assert "run_vehicle_malus_batch" in source or "run_energy_poverty_aid_batch" in source


def test_epic13_notebook_covers_yaml_round_trip() -> None:
    """Contains dump_portfolio and load_portfolio for YAML round-trip (AC6-f)."""
    source = _all_sources(_load_notebook())
    assert "dump_portfolio" in source
    assert "load_portfolio" in source


def test_epic13_ci_includes_notebook() -> None:
    """CI workflow includes nbmake execution of this notebook."""
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "uv run pytest --nbmake notebooks/guides/07_custom_templates.ipynb -v" in ci_workflow
