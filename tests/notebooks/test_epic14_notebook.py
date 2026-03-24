# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Static checks for the Epic 14 discrete choice demo script.

These checks enforce story 14-7 acceptance criteria that can be validated
by reading the demo source file.
"""

from __future__ import annotations

from pathlib import Path

DEMO_PATH = Path(__file__).resolve().parents[2] / "demos" / "guides" / "08_discrete_choice_model.py"
CI_WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def _read_source() -> str:
    return DEMO_PATH.read_text(encoding="utf-8")


def test_demo_exists() -> None:
    """Demo script exists at the expected path."""
    assert DEMO_PATH.exists()


def test_uses_public_api() -> None:
    """Demo uses public API surfaces and avoids internal imports."""
    source = _read_source()
    assert "from reformlab.discrete_choice import" in source
    assert "from reformlab.orchestrator.runner import Orchestrator" in source
    assert "from reformlab.orchestrator.panel import PanelOutput" in source
    assert "from reformlab.computation.mock_adapter import MockAdapter" in source
    assert "from reformlab.computation.types import PolicyConfig, PopulationData" in source
    assert "from reformlab.computation.adapter import" not in source
    assert "from reformlab.computation.openfisca" not in source
    assert "from openfisca import" not in source
    assert "import openfisca" not in source


def test_required_sections() -> None:
    """Demo includes all required content sections."""
    source = _read_source()
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
    """Demo includes key discrete choice API calls."""
    source = _read_source()
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
    """Demo keeps the behavioral-response logic and reproducibility check honest."""
    source = _read_source()
    assert "vehicle_emissions_gkm" in source
    assert "heating_emissions_kgco2_kwh" in source
    assert "energy_consumption" in source
    assert "COMPUTATION_RESULT_KEY" in source


def test_ci_includes_demo() -> None:
    """CI workflow includes execution of this demo."""
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "uv run python demos/guides/08_discrete_choice_model.py" in ci_workflow
