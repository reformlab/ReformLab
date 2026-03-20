"""Visualization utilities for ReformLab result objects.

Provides plotting functions for indicator and panel data, plus a formatted
table display utility. All plot functions return (Figure, Axes) tuples for
user customization.

Public API:
    - show: Formatted text display for PyArrow tables
    - create_figure: Create a pre-styled matplotlib figure
    - style_axes: Apply consistent styling to existing axes
    - plot_deciles: Bar chart by income decile
    - plot_yearly: Line chart over time
    - plot_comparison: Side-by-side baseline vs reform bar chart
"""

from __future__ import annotations

from reformlab.visualization.display import show
from reformlab.visualization.plotting import (
    create_figure_grid,
    plot_bar_series,
    plot_comparison,
    plot_deciles,
    plot_histogram,
    plot_yearly,
    show_figure,
)
from reformlab.visualization.styling import create_figure, style_axes

__all__ = [
    "show",
    "create_figure",
    "create_figure_grid",
    "style_axes",
    "plot_bar_series",
    "plot_comparison",
    "plot_deciles",
    "plot_histogram",
    "plot_yearly",
    "show_figure",
]
