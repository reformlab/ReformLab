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
