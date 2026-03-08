"""Static checks for the Epic 14 discrete choice notebook content.

These checks enforce story 14-7 acceptance criteria that can be validated
without launching a Jupyter kernel in unit-test environments.
"""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK_PATH = (
    Path(__file__).resolve().parents[2] / "notebooks" / "guides" / "08_discrete_choice_model.ipynb"
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
    # Imports from public discrete choice API
    assert "from reformlab.discrete_choice import (" in source
    # Imports from public orchestrator API
    assert "from reformlab.orchestrator.runner import Orchestrator" in source
    assert "from reformlab.orchestrator.panel import PanelOutput" in source
    # Imports from public computation types (NOT internal adapter)
    assert "from reformlab.computation.mock_adapter import MockAdapter" in source
    assert "from reformlab.computation.types import PolicyConfig, PopulationData" in source
    # No internal adapter imports
    assert "from reformlab.computation.adapter import" not in source
    assert "from reformlab.computation.openfisca" not in source
    # No OpenFisca imports
    assert "from openfisca import" not in source
    assert "import openfisca" not in source


def test_required_sections() -> None:
    """Notebook includes all required content sections."""
    source = _all_sources(_load_notebook())
    assert "Section 0: Setup" in source
    assert "Section 1: Build Population" in source
    assert "Section 2: Configure Policy Portfolio" in source
    assert "Section 3: Wire Discrete Choice Pipeline" in source
    assert "Section 4: Run 10-Year Simulation" in source
    assert "Section 5: Fleet Composition Over Time" in source
    assert "Section 6: Panel Output and Decision Records" in source
    assert "Section 7: Distributional Indicators" in source
    assert "Section 8: Governance and Reproducibility" in source
    assert "Section 9: Export and Next Steps" in source


def test_key_api_calls() -> None:
    """Notebook includes key discrete choice API calls."""
    source = _all_sources(_load_notebook())
    assert "DiscreteChoiceStep(" in source
    assert "LogitChoiceStep(" in source
    assert "VehicleStateUpdateStep(" in source
    assert "HeatingStateUpdateStep(" in source
    assert "DecisionRecordStep(" in source
    assert "EligibilityMergeStep(" in source
    assert "PanelOutput.from_orchestrator_result(" in source
    assert "capture_discrete_choice_parameters" in source
    assert "EligibilityFilter(" in source
    assert "EligibilityRule(" in source
    assert "TasteParameters(" in source


def test_behavioral_response_logic_is_wired_correctly() -> None:
    """Notebook keeps the behavioral-response logic and reproducibility check honest."""
    source = _all_sources(_load_notebook())
    assert "vehicle_emissions_gkm" in source
    assert "heating_emissions_kgco2_kwh" in source
    assert "energy_consumption" in source
    assert 'current_population = state.data["population_data"]' in source
    assert "COMPUTATION_RESULT_KEY" in source
    assert "ComputationStep(" not in source
    assert "orchestrator_rerun.run()" in source
    assert "result_rerun = orchestrator.run()" not in source


def test_ci_includes_notebook() -> None:
    """CI workflow includes nbmake execution of this notebook."""
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "uv run pytest --nbmake notebooks/guides/08_discrete_choice_model.ipynb -v" in ci_workflow
