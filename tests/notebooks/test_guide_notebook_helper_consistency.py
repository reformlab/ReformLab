"""Static checks for shared helper usage across guide notebooks."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDES_DIR = ROOT / "notebooks" / "guides"


def _load_sources(path: Path) -> str:
    with path.open(encoding="utf-8") as handle:
        notebook = json.load(handle)
    cells = notebook.get("cells", [])
    if not isinstance(cells, list):
        return ""
    sources: list[str] = []
    for cell in cells:
        if not isinstance(cell, dict) or cell.get("cell_type") != "code":
            continue
        source = cell.get("source", [])
        if isinstance(source, list):
            sources.append("".join(part for part in source if isinstance(part, str)))
        elif isinstance(source, str):
            sources.append(source)
    return "\n".join(sources)


def test_guides_use_shared_table_display_helper() -> None:
    """Guide notebooks should use the shared table-display helper."""
    for path in sorted(GUIDES_DIR.glob("*.ipynb")):
        source = _load_sources(path)
        assert "def show" not in source, f"{path.name} still defines a local show()"


def test_viz_heavy_guides_use_shared_visualization_helpers() -> None:
    """Visualization-heavy guides should rely on shared plotting helpers."""
    expectations = {
        "08_discrete_choice_model.ipynb": ["plot_stacked_area(", "plot_bar_series(", "show_figure("],
        "09_population_generation.ipynb": ["plot_histogram(", "plot_bar_series(", "show_figure("],
        "10_calibration_workflow.ipynb": ["plot_grouped_bars(", "show_figure("],
    }
    for name, required_tokens in expectations.items():
        source = _load_sources(GUIDES_DIR / name)
        assert "import matplotlib.pyplot as plt" not in source
        assert "from reformlab.visualization import" in source
        for token in required_tokens:
            assert token in source
