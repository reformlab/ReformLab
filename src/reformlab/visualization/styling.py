"""Centralized chart styling for ReformLab visualizations.

Provides create_figure() and style_axes() for consistent matplotlib chart
appearance across all ReformLab plots.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


def create_figure(
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    figsize: tuple[float, float] = (10, 6),
) -> tuple[Figure, Axes]:
    """Create a pre-styled matplotlib figure and axes.

    Args:
        title: Chart title (fontsize 14, bold).
        xlabel: X-axis label (fontsize 12).
        ylabel: Y-axis label (fontsize 12).
        figsize: Figure size in inches. Defaults to (10, 6).

    Returns:
        Tuple of (Figure, Axes) ready for plotting.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=figsize)
    style_axes(ax, title=title, xlabel=xlabel, ylabel=ylabel)
    return fig, ax


def style_axes(
    ax: Axes,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    xticks: Sequence[Any] | None = None,
) -> None:
    """Apply consistent styling to an existing matplotlib axes.

    Args:
        ax: Matplotlib axes to style.
        title: Chart title (fontsize 14, bold).
        xlabel: X-axis label (fontsize 12).
        ylabel: Y-axis label (fontsize 12).
        xticks: Optional explicit x-axis tick values.
    """
    if title:
        ax.set_title(title, fontsize=14, fontweight="bold")
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=12)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=12)
    if xticks is not None:
        ax.set_xticks(xticks)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    fig = ax.get_figure()
    if fig is not None and hasattr(fig, "tight_layout"):
        fig.tight_layout()
