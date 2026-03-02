"""Static checks for the advanced notebook content.

These checks enforce story 6-3 acceptance criteria that can be validated
without launching a Jupyter kernel in unit-test environments.
"""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).resolve().parents[2] / "notebooks" / "advanced.ipynb"
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


def test_advanced_notebook_exists() -> None:
    """Notebook deliverable exists at the expected path."""
    assert NOTEBOOK_PATH.exists()


def test_advanced_notebook_outputs_are_cleared() -> None:
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


def test_advanced_notebook_uses_public_api_surfaces() -> None:
    """Notebook should stay on public package imports and avoid internals."""
    source = _all_sources(_load_notebook())
    assert "from reformlab import (" in source
    assert "run_scenario" in source
    assert "RunConfig" in source
    assert "ScenarioConfig" in source
    assert "show," in source
    assert "from reformlab.vintage import (" in source
    assert "from reformlab.indicators import (" in source
    assert "from reformlab.indicators.comparison import" not in source
    assert "reformlab.computation" not in source
    assert "from openfisca import" not in source
    assert "import openfisca" not in source


def test_advanced_notebook_uses_visualization_api() -> None:
    """Notebook uses built-in visualization API instead of inline boilerplate."""
    source = _all_sources(_load_notebook())
    assert "plot_yearly(" in source
    assert "plot_comparison(" in source
    assert "create_figure(" in source
    assert "def show(" not in source


def test_advanced_notebook_covers_multi_year_vintage_and_comparison_sections() -> None:
    """Notebook includes core advanced workflow sections and scenario settings.

    Story 6.7 renamed Section 1 from "Multi-Year Simulation" to "Multi-Year Escalating Policy"
    and added typed policy objects throughout.
    """
    source = _all_sources(_load_notebook())
    assert "Section 1: Multi-Year Escalating Policy" in source
    assert "CarbonTaxParameters(" in source
    assert "start_year=2025" in source
    assert "end_year=2034" in source
    assert "sorted(result_multi.yearly_states.keys())" in source
    assert "Section 2: Vintage Tracking" in source
    assert "VintageConfig(" in source
    assert "VintageTransitionStep(" in source
    assert "vintage_vehicle" in source
    assert "VintageSummary.from_state(" in source
    assert "Section 3: Baseline vs. Reform Comparison" in source
    assert 'result_baseline.indicators("distributional")' in source
    assert "result_baseline.indicators(" in source
    assert '"fiscal"' in source
    assert "fiscal_comparison = compare_scenarios(" in source


def test_advanced_notebook_covers_reproducibility_and_lineage() -> None:
    """Notebook demonstrates reruns plus baseline/reform lineage visibility.

    Story 6.7 renumbered this section from Section 4 to Section 5 to make room
    for the new "Build Your Own Policy Type" Section 4.
    """
    source = _all_sources(_load_notebook())
    assert "Section 5: Lineage and Reproducibility" in source
    assert "result_rerun = run_scenario" in source
    assert "if original_tax == rerun_tax" in source
    assert "baseline_manifest = result_baseline.manifest" in source
    assert "reform_manifest = result_vintage.manifest" in source
    assert "steps=(vintage_step,)" in source
    assert "child_manifests" in source
    assert "quickstart notebook" in source.lower()


def test_advanced_notebook_includes_export_examples_and_roundtrip() -> None:
    """Story 6-5/6-7: notebook shows export flows and Parquet round-trip verification.

    Story 6.7 simplified the export section heading.
    """
    source = _all_sources(_load_notebook())
    assert "Export simulation results for external analysis" in source
    assert "result_vintage.export_parquet(" in source
    assert "fiscal_reform.export_parquet(" in source
    assert "fiscal_comparison.export_parquet(" in source
    assert "pq.read_table(" in source
    assert "schema_metadata" in source
    assert "result_vintage.scenario.start_year" not in source


def test_advanced_notebook_export_heading_precedes_export_code() -> None:
    """Export section heading should come before export directory and artifact writes.

    Story 6.7 simplified the export section heading.
    """
    source = _all_sources(_load_notebook())
    heading = source.find("Export simulation results for external analysis")
    export_dir = source.find("export_dir = Path(tempfile.mkdtemp())")
    panel_export = source.find("result_vintage.export_parquet(")
    indicator_export = source.find("fiscal_reform.export_parquet(")

    assert heading != -1
    assert export_dir != -1
    assert panel_export != -1
    assert indicator_export != -1
    assert heading < export_dir < panel_export < indicator_export


def test_ci_executes_advanced_notebook_with_nbmake() -> None:
    """CI should execute the advanced notebook in fresh kernel mode."""
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "uv run pytest --nbmake notebooks/advanced.ipynb -v" in ci_workflow
