# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Static checks for shared helper usage across guide demo scripts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GUIDES_DIR = ROOT / "demos" / "guides"


def _load_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_guides_use_shared_table_display_helper() -> None:
    """Guide demos should use the shared table-display helper."""
    for path in sorted(GUIDES_DIR.glob("*.py")):
        source = _load_source(path)
        assert "def show" not in source, f"{path.name} still defines a local show()"


def test_viz_heavy_guides_use_shared_visualization_helpers() -> None:
    """Visualization-heavy guides should rely on shared plotting helpers."""
    expectations = {
        "08_discrete_choice_model.py": ["plot_stacked_area(", "plot_bar_series(", "show_figure("],
        "09_population_generation.py": ["plot_histogram(", "plot_bar_series(", "show_figure("],
        "10_calibration_workflow.py": ["plot_grouped_bars(", "show_figure("],
    }
    for name, required_tokens in expectations.items():
        source = _load_source(GUIDES_DIR / name)
        assert "import matplotlib.pyplot as plt" not in source
        assert "from reformlab.visualization import" in source
        for token in required_tokens:
            assert token in source, f"{name} missing {token}"
