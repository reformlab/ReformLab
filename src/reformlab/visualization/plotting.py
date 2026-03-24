# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Standalone plot functions for ReformLab indicator and panel data.

Provides plot_deciles(), plot_yearly(), and plot_comparison() for common
chart types used in policy analysis notebooks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pyarrow as pa
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure


def create_figure_grid(
    nrows: int,
    ncols: int,
    *,
    figsize: tuple[float, float] = (10, 6),
) -> tuple[Figure, list[Axes]]:
    """Create a grid of subplots and return (figure, flat list of axes).

    Args:
        nrows: Number of rows.
        ncols: Number of columns.
        figsize: Figure size in inches.

    Returns:
        Tuple of (Figure, list[Axes]).
    """
    import matplotlib.pyplot as plt
    import numpy as np

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    flat = list(np.asarray(axes).flat) if nrows * ncols > 1 else [axes]
    fig.tight_layout(pad=3.0)
    return fig, flat


def plot_histogram(
    values: list[float],
    *,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "Count",
    bins: int | range | list[int] = 10,
    color: str = "steelblue",
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Histogram of a list of numeric values.

    Args:
        values: Data to plot.
        title: Chart title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        bins: Number of bins or bin edges.
        color: Bar color.
        ax: Existing axes to plot on. Creates new figure if None.

    Returns:
        Tuple of (Figure, Axes).
    """
    from reformlab.visualization.styling import create_figure, style_axes

    if ax is None:
        fig, ax = create_figure()
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
    ax.hist(values, bins=bins, color=color, alpha=0.8, edgecolor="white")
    style_axes(ax, title=title, xlabel=xlabel, ylabel=ylabel)
    return fig, ax


def plot_bar_series(
    labels: list[str],
    values: list[float],
    *,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: list[str] | str = "steelblue",
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Bar chart from labels and values.

    Args:
        labels: Category labels.
        values: Bar heights.
        title: Chart title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        colors: Bar color(s).
        ax: Existing axes to plot on. Creates new figure if None.

    Returns:
        Tuple of (Figure, Axes).
    """
    from reformlab.visualization.styling import create_figure, style_axes

    if ax is None:
        fig, ax = create_figure()
    else:
        fig = ax.get_figure()  # type: ignore[assignment]
    ax.bar(labels, values, color=colors, alpha=0.8)
    style_axes(ax, title=title, xlabel=xlabel, ylabel=ylabel)
    return fig, ax


def show_figure(fig: Figure) -> None:
    """Display a matplotlib figure (calls plt.show in interactive contexts)."""
    import matplotlib.pyplot as plt

    plt.show()


def plot_grouped_bars(
    labels: list[str],
    series: dict[str, list[float]],
    *,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    colors: list[str] | None = None,
    xtick_rotation: float = 0,
    ylim: tuple[float, float] | None = None,
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Grouped bar chart with multiple named series sharing the same x-axis labels.

    Args:
        labels: Category labels for the x-axis.
        series: Mapping of series name to values (each list same length as *labels*).
        title: Chart title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        colors: Optional list of colors, one per series. Uses matplotlib cycle if None.
        xtick_rotation: Rotation angle for x-tick labels in degrees.
        ylim: Optional (min, max) limits for the y-axis.
        ax: Existing axes to plot on. Creates new figure if None.

    Returns:
        Tuple of (Figure, Axes).
    """
    import numpy as np

    from reformlab.visualization.styling import create_figure, style_axes

    if ax is None:
        fig, ax = create_figure()
    else:
        fig = ax.get_figure()  # type: ignore[assignment]

    n_series = len(series)
    n_labels = len(labels)
    x = np.arange(n_labels)
    width = 0.8 / max(n_series, 1)

    for i, (name, values) in enumerate(series.items()):
        offset = (i - (n_series - 1) / 2) * width
        bar_color = colors[i] if colors is not None and i < len(colors) else None
        ax.bar(x + offset, values, width, label=name, alpha=0.8, color=bar_color)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=xtick_rotation)
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.legend(fontsize=11)
    style_axes(ax, title=title, xlabel=xlabel, ylabel=ylabel)
    return fig, ax


def plot_stacked_area(
    x: list[int] | list[float],
    series: dict[str, list[float]],
    *,
    title: str = "",
    xlabel: str = "",
    ylabel: str = "",
    label_map: dict[str, str] | None = None,
    color_map: dict[str, str] | None = None,
    legend_loc: str = "best",
    ax: Axes | None = None,
) -> tuple[Figure, Axes]:
    """Stacked area chart from a dict of named series.

    Args:
        x: Shared x-axis values (e.g. years).
        series: Mapping of series key to y-values (same length as *x*).
        title: Chart title.
        xlabel: X-axis label.
        ylabel: Y-axis label.
        label_map: Optional mapping from series key to display label.
        color_map: Optional mapping from series key to color.
        legend_loc: Legend location string.
        ax: Existing axes to plot on. Creates new figure if None.

    Returns:
        Tuple of (Figure, Axes).
    """
    from reformlab.visualization.styling import create_figure, style_axes

    if ax is None:
        fig, ax = create_figure()
    else:
        fig = ax.get_figure()  # type: ignore[assignment]

    label_map = label_map or {}
    color_map = color_map or {}

    keys = list(series.keys())
    labels = [label_map.get(k, k) for k in keys]
    colors = [color_map.get(k, None) for k in keys]
    y_data = [series[k] for k in keys]

    # Filter out None colors so matplotlib uses its cycle
    kwargs: dict[str, Any] = {}
    if all(c is not None for c in colors):
        kwargs["colors"] = colors

    ax.stackplot(x, *y_data, labels=labels, alpha=0.8, **kwargs)
    ax.legend(loc=legend_loc, fontsize=10)
    style_axes(ax, title=title, xlabel=xlabel, ylabel=ylabel)
    return fig, ax


def plot_deciles(
    indicator_table: pa.Table,
    field: str,
    metric: str = "mean",
    *,
    title: str | None = None,
    color: str = "steelblue",
) -> tuple[Figure, Axes]:
    """Bar chart of indicator values by income decile.

    Args:
        indicator_table: Long-form PyArrow table with columns
            field_name, decile, year, metric, value.
        field: Name of the field to plot (e.g., "carbon_tax").
        metric: Metric to plot (e.g., "mean", "median", "sum").
        title: Chart title. Auto-generated if None.
        color: Bar color. Defaults to "steelblue".

    Returns:
        Tuple of (Figure, Axes).

    Raises:
        ValueError: If field or metric not found in table.
    """
    import pyarrow.compute as pc

    from reformlab.visualization.styling import create_figure, style_axes

    _validate_field(indicator_table, field)

    filtered = indicator_table.filter(
        pc.and_(
            pc.equal(indicator_table["field_name"], field),
            pc.equal(indicator_table["metric"], metric),
        )
    )
    if filtered.num_rows == 0:
        msg = f"No data found for field={field!r}, metric={metric!r}"
        raise ValueError(msg)

    filtered = filtered.sort_by([("decile", "ascending")])
    deciles = filtered["decile"].to_pylist()
    values = filtered["value"].to_pylist()

    chart_title = title or f"{field} by Income Decile ({metric})"
    fig, ax = create_figure()
    ax.bar(deciles, values, color=color, alpha=0.8)
    style_axes(
        ax,
        title=chart_title,
        xlabel="Income Decile",
        ylabel=f"{metric.capitalize()} {field}",
        xticks=deciles,
    )
    return fig, ax


def plot_yearly(
    panel_table: pa.Table,
    field: str,
    metric: str = "mean",
    *,
    title: str | None = None,
    color: str = "steelblue",
) -> tuple[Figure, Axes]:
    """Line chart of a field's metric over time.

    Args:
        panel_table: PyArrow table with at least 'year' and the target field columns.
        field: Name of the field to aggregate (e.g., "carbon_tax").
        metric: Aggregation metric ("mean", "median", "sum").
        title: Chart title. Auto-generated if None.
        color: Line color. Defaults to "steelblue".

    Returns:
        Tuple of (Figure, Axes).

    Raises:
        ValueError: If field not found in table.
    """
    import pyarrow.compute as pc

    from reformlab.visualization.styling import create_figure, style_axes

    if field not in panel_table.column_names:
        msg = f"Field {field!r} not found in table. Available: {panel_table.column_names}"
        raise ValueError(msg)

    years = sorted(y for y in set(panel_table["year"].to_pylist()) if y is not None)
    values: list[Any] = []

    agg_func = _get_agg_func(metric)
    for year in years:
        year_data = panel_table.filter(pc.equal(panel_table["year"], year))
        agg_value = agg_func(year_data[field]).as_py()
        values.append(agg_value)

    chart_title = title or f"{field} Over Time ({metric})"
    fig, ax = create_figure()
    ax.plot(years, values, marker="o", linewidth=2, color=color, markersize=8)
    style_axes(
        ax,
        title=chart_title,
        xlabel="Year",
        ylabel=f"{metric.capitalize()} {field}",
        xticks=years,
    )
    return fig, ax


def plot_comparison(
    baseline_table: pa.Table,
    reform_table: pa.Table,
    field: str,
    metric: str = "mean",
    *,
    baseline_label: str = "Baseline",
    reform_label: str = "Reform",
    title: str | None = None,
) -> tuple[Figure, Axes]:
    """Side-by-side grouped bar chart comparing two indicator tables by decile.

    Args:
        baseline_table: Long-form indicator table for baseline scenario.
        reform_table: Long-form indicator table for reform scenario.
        field: Name of the field to compare (e.g., "carbon_tax").
        metric: Metric to compare (e.g., "mean").
        baseline_label: Legend label for baseline bars.
        reform_label: Legend label for reform bars.
        title: Chart title. Auto-generated if None.

    Returns:
        Tuple of (Figure, Axes).

    Raises:
        ValueError: If field or metric not found in either table.
    """
    from reformlab.visualization.styling import create_figure, style_axes

    _validate_field(baseline_table, field)
    _validate_field(reform_table, field)

    baseline_filtered = _filter_field_metric(baseline_table, field, metric)
    reform_filtered = _filter_field_metric(reform_table, field, metric)

    if baseline_filtered.num_rows == 0 or reform_filtered.num_rows == 0:
        msg = f"No data found for field={field!r}, metric={metric!r} in one or both tables"
        raise ValueError(msg)

    baseline_filtered = baseline_filtered.sort_by([("decile", "ascending")])
    reform_filtered = reform_filtered.sort_by([("decile", "ascending")])

    deciles = baseline_filtered["decile"].to_pylist()
    reform_deciles = reform_filtered["decile"].to_pylist()
    if deciles != reform_deciles:
        msg = (
            f"Decile mismatch between baseline ({deciles}) "
            f"and reform ({reform_deciles})"
        )
        raise ValueError(msg)
    baseline_values = baseline_filtered["value"].to_pylist()
    reform_values = reform_filtered["value"].to_pylist()

    chart_title = title or f"{baseline_label} vs {reform_label}: {field} ({metric})"
    fig, ax = create_figure()

    x_pos = list(range(len(deciles)))
    width = 0.35
    ax.bar(
        [p - width / 2 for p in x_pos],
        baseline_values,
        width,
        label=baseline_label,
        color="steelblue",
        alpha=0.8,
    )
    ax.bar(
        [p + width / 2 for p in x_pos],
        reform_values,
        width,
        label=reform_label,
        color="coral",
        alpha=0.8,
    )
    ax.legend(fontsize=11)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(deciles)
    style_axes(
        ax,
        title=chart_title,
        xlabel="Income Decile",
        ylabel=f"{metric.capitalize()} {field}",
    )
    return fig, ax


# ====================================================================
# Internal helpers
# ====================================================================


def _validate_field(table: pa.Table, field: str) -> None:
    """Raise ValueError if field_name column doesn't contain the given field."""
    import pyarrow.compute as pc

    unique_fields = pc.unique(table["field_name"]).to_pylist()
    if field not in unique_fields:
        msg = f"Field {field!r} not found in table. Available fields: {unique_fields}"
        raise ValueError(msg)


def _filter_field_metric(table: pa.Table, field: str, metric: str) -> pa.Table:
    """Filter a long-form indicator table by field_name and metric."""
    import pyarrow.compute as pc

    return table.filter(
        pc.and_(
            pc.equal(table["field_name"], field),
            pc.equal(table["metric"], metric),
        )
    )


def _get_agg_func(metric: str) -> Any:
    """Return the pyarrow.compute aggregation function for the given metric name."""
    import pyarrow.compute as pc

    funcs: dict[str, Any] = {
        "mean": pc.mean,
        "median": lambda col: pc.quantile(col, q=0.5)[0],
        "sum": pc.sum,
    }
    if metric not in funcs:
        msg = f"Unsupported metric {metric!r}. Supported: {list(funcs.keys())}"
        raise ValueError(msg)
    return funcs[metric]
