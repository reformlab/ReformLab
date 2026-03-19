"""Static checks for the advanced Marimo notebook content.

These checks validate that the advanced notebook covers the full policy
assessment pipeline: data fusion, policy definition, discrete choice,
orchestration, indicators, governance, and export.
"""

from __future__ import annotations

from pathlib import Path

NOTEBOOK_PATH = Path(__file__).resolve().parents[2] / "notebooks" / "advanced.py"


def _read_source() -> str:
    return NOTEBOOK_PATH.read_text(encoding="utf-8")


def test_advanced_notebook_exists() -> None:
    """Marimo notebook exists at the expected path."""
    assert NOTEBOOK_PATH.exists()
    assert NOTEBOOK_PATH.suffix == ".py"


def test_advanced_notebook_is_valid_marimo() -> None:
    """Notebook is a valid Marimo app (imports marimo, defines app)."""
    source = _read_source()
    assert "import marimo" in source
    assert "app = marimo.App(" in source
    assert "@app.cell" in source


def test_advanced_notebook_section_1_builds_population_database() -> None:
    """Section 1 covers data fusion from institutional sources."""
    source = _read_source()
    assert "Build the Population Database" in source
    assert "PopulationPipeline" in source
    assert "UniformMergeMethod" in source
    assert "IPFMergeMethod" in source
    assert "ConditionalSamplingMethod" in source
    assert "FixtureLoader" in source
    assert "income_loader" in source
    assert "housing_loader" in source
    assert "vehicle_loader" in source
    assert "energy_loader" in source
    assert "PopulationValidator" in source
    assert "MarginalConstraint" in source
    assert "assumption_chain" in source


def test_advanced_notebook_section_2_defines_policy_portfolio() -> None:
    """Section 2 defines carbon tax + subsidies with interactive sliders."""
    source = _read_source()
    assert "Define the Policy Portfolio" in source
    assert "CARBON_TAX_SCHEDULE" in source
    assert "EV_SUBSIDY" in source
    assert "HEAT_PUMP_SUBSIDY" in source
    assert "PolicyConfig" in source
    assert "mo.ui.slider" in source


def test_advanced_notebook_section_3_wires_discrete_choice() -> None:
    """Section 3 configures vehicle and heating investment decisions."""
    source = _read_source()
    assert "Wire Investment Decisions" in source or "Discrete Choice" in source
    assert "DiscreteChoiceStep" in source
    assert "LogitChoiceStep" in source
    assert "VehicleInvestmentDomain" in source
    assert "HeatingInvestmentDomain" in source
    assert "EligibilityFilter" in source
    assert "EligibilityRule" in source
    assert "TasteParameters" in source
    assert "DecisionRecordStep" in source
    assert "VehicleStateUpdateStep" in source
    assert "HeatingStateUpdateStep" in source
    assert "beta_cost" in source


def test_advanced_notebook_section_4_runs_simulation() -> None:
    """Section 4 runs a 10-year orchestrated simulation."""
    source = _read_source()
    assert "OrchestratorConfig" in source
    assert "Orchestrator" in source
    assert "start_year=2025" in source
    assert "end_year=2034" in source
    assert "PanelOutput" in source
    assert "from_orchestrator_result" in source


def test_advanced_notebook_section_5_analyzes_results() -> None:
    """Section 5 covers fleet evolution and distributional indicators."""
    source = _read_source()
    assert "Fleet Evolution" in source or "vehicle_fleet" in source
    assert "stackplot" in source
    assert "compute_distributional_indicators" in source
    assert "carbon_tax" in source
    assert "Income Decile" in source


def test_advanced_notebook_section_6_governance_and_export() -> None:
    """Section 6 covers determinism verification, governance, and export."""
    source = _read_source()
    assert "Governance" in source
    assert "Determinism" in source or "determinism" in source
    assert "capture_discrete_choice_parameters" in source
    assert "to_governance_entries" in source
    assert "to_assumption" in source
    assert "to_parquet" in source
    assert "round-trip" in source.lower() or "Round-trip" in source


def test_advanced_notebook_uses_interactive_widgets() -> None:
    """Marimo notebook uses interactive UI widgets for policy exploration."""
    source = _read_source()
    assert "mo.ui.slider" in source
    assert "mo.md" in source
    assert "mo.vstack" in source


def test_advanced_notebook_does_not_use_quickstart_adapter() -> None:
    """Advanced notebook uses real pipeline, not the quickstart demo adapter."""
    source = _read_source()
    assert "create_quickstart_adapter" not in source


def test_advanced_notebook_section_ordering() -> None:
    """Sections in correct order: data → policy → decisions → simulation → analysis → governance."""
    source = _read_source()
    pos_data = source.find("Build the Population Database")
    pos_policy = source.find("Define the Policy Portfolio")
    pos_decisions = source.find("Wire Investment Decisions")
    pos_simulation = source.find("Run the 10-Year Simulation")
    pos_analysis = source.find("Analyze Results")
    pos_governance = source.find("Governance & Export")

    assert pos_data != -1
    assert pos_policy != -1
    assert pos_decisions != -1
    assert pos_simulation != -1
    assert pos_analysis != -1
    assert pos_governance != -1
    assert pos_data < pos_policy < pos_decisions < pos_simulation < pos_analysis < pos_governance
