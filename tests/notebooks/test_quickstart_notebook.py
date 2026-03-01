"""Static checks for the quickstart notebook content.

These checks enforce story 6-2 acceptance criteria that can be validated
without launching a Jupyter kernel in unit-test environments.
"""

from __future__ import annotations

import json
from pathlib import Path

NOTEBOOK_PATH = Path(__file__).resolve().parents[2] / "notebooks" / "quickstart.ipynb"


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
    return "\n".join(
        _cell_source(cell) for cell in cells if isinstance(cell, dict)
    )


def test_quickstart_notebook_exists() -> None:
    """Notebook deliverable exists at the expected path."""
    assert NOTEBOOK_PATH.exists()


def test_quickstart_notebook_outputs_are_cleared() -> None:
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


def test_quickstart_notebook_uses_public_api_only() -> None:
    """Notebook should not import internal ReformLab modules."""
    source = _all_sources(_load_notebook())
    assert "from reformlab import" in source
    assert "create_quickstart_adapter" in source
    assert "show," in source
    assert "reformlab.computation" not in source


def test_quickstart_notebook_uses_visualization_api() -> None:
    """Notebook uses built-in visualization API instead of inline boilerplate."""
    source = _all_sources(_load_notebook())
    assert "plot_deciles(" in source
    assert "plot_comparison(" in source
    assert "def show(" not in source


def test_quickstart_notebook_includes_story_key_sections() -> None:
    """Notebook includes required tutorial and reproducibility content."""
    source = _all_sources(_load_notebook())
    assert "Try It Yourself" in source
    assert "NEW_RATE = 100.0" in source
    assert "Baseline vs. Reform" in source
    assert "result.manifest" in source
    assert "import matplotlib.pyplot as plt" in source


def test_quickstart_notebook_includes_export_examples() -> None:
    """Story 6-5: notebook includes panel/indicator export and round-trip examples."""
    source = _all_sources(_load_notebook())
    assert "## 7. Export Actions" in source
    assert "result.export_csv(" in source
    assert "result.export_parquet(" in source
    assert "indicators.export_csv(" in source
    assert "pa_csv.read_csv(" in source


def test_quickstart_notebook_includes_population_loading() -> None:
    """Notebook demonstrates loading population CSV and the adapter pattern."""
    source = _all_sources(_load_notebook())
    assert "POPULATION_PATH" in source
    assert "population_path" in source
    assert "adapter pattern" in source.lower() or "adapter" in source.lower()


def test_quickstart_export_section_precedes_next_steps() -> None:
    """Export walkthrough should appear before final next-steps guidance."""
    source = _all_sources(_load_notebook())
    export_heading = source.find("## 7. Export Actions")
    panel_export = source.find("result.export_csv(")
    indicator_export = source.find("indicators.export_csv(")
    next_steps = source.find("## 8. Next Steps")

    assert export_heading != -1
    assert panel_export != -1
    assert indicator_export != -1
    assert next_steps != -1

    assert export_heading < panel_export < indicator_export < next_steps
    assert source.count("## 8. Next Steps") == 1
