# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for reformlab.visualization.plotting module."""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import pyarrow as pa
import pytest

matplotlib.use("Agg")

from reformlab.indicators.types import IndicatorResult
from reformlab.visualization.plotting import plot_comparison, plot_deciles, plot_yearly


class TestPlotDeciles:
    """Tests for plot_deciles() bar chart function."""

    def test_returns_fig_axes(self, sample_indicator_table: pa.Table) -> None:
        """Verify return types."""
        fig, ax = plot_deciles(sample_indicator_table, "carbon_tax")
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(ax, matplotlib.axes.Axes)
        plt.close(fig)

    def test_correct_bar_count(self, sample_indicator_table: pa.Table) -> None:
        """Verify 10 bars for 10 deciles."""
        fig, ax = plot_deciles(sample_indicator_table, "carbon_tax")
        bars = [p for p in ax.patches if hasattr(p, "get_height")]
        assert len(bars) == 10
        plt.close(fig)

    def test_auto_title(self, sample_indicator_table: pa.Table) -> None:
        """Verify title contains field name."""
        fig, ax = plot_deciles(sample_indicator_table, "carbon_tax")
        assert "carbon_tax" in ax.get_title()
        plt.close(fig)

    def test_field_not_found(self, sample_indicator_table: pa.Table) -> None:
        """Verify ValueError raised for nonexistent field."""
        with pytest.raises(ValueError, match="not found"):
            plot_deciles(sample_indicator_table, "nonexistent_field")

    def test_empty_indicators(self) -> None:
        """Verify ValueError raised for empty table with valid field."""
        empty_table = pa.table(
            {
                "field_name": pa.array([], type=pa.utf8()),
                "decile": pa.array([], type=pa.int64()),
                "year": pa.array([], type=pa.int64()),
                "metric": pa.array([], type=pa.utf8()),
                "value": pa.array([], type=pa.float64()),
            }
        )
        with pytest.raises(ValueError, match="not found"):
            plot_deciles(empty_table, "carbon_tax")


class TestPlotYearly:
    """Tests for plot_yearly() line chart function."""

    def test_returns_fig_axes(self, sample_multi_year_panel: pa.Table) -> None:
        """Verify return types."""
        fig, ax = plot_yearly(sample_multi_year_panel, "carbon_tax")
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(ax, matplotlib.axes.Axes)
        plt.close(fig)

    def test_line_data_points(self, sample_multi_year_panel: pa.Table) -> None:
        """Verify line has correct number of points (2 years)."""
        fig, ax = plot_yearly(sample_multi_year_panel, "carbon_tax")
        lines = ax.get_lines()
        assert len(lines) == 1
        xdata = lines[0].get_xdata()
        assert len(xdata) == 2
        plt.close(fig)

    def test_field_not_found(self, sample_multi_year_panel: pa.Table) -> None:
        """Verify ValueError raised for nonexistent field."""
        with pytest.raises(ValueError, match="not found"):
            plot_yearly(sample_multi_year_panel, "nonexistent_field")


class TestPlotYearlyMetrics:
    """Tests for plot_yearly() with different aggregation metrics."""

    def test_median_metric(self, sample_multi_year_panel: pa.Table) -> None:
        """Verify plot_yearly works with metric='median'."""
        fig, ax = plot_yearly(sample_multi_year_panel, "carbon_tax", metric="median")
        lines = ax.get_lines()
        assert len(lines) == 1
        assert len(lines[0].get_xdata()) == 2
        plt.close(fig)

    def test_sum_metric(self, sample_multi_year_panel: pa.Table) -> None:
        """Verify plot_yearly works with metric='sum'."""
        fig, ax = plot_yearly(sample_multi_year_panel, "carbon_tax", metric="sum")
        lines = ax.get_lines()
        assert len(lines) == 1
        plt.close(fig)

    def test_unsupported_metric(self, sample_multi_year_panel: pa.Table) -> None:
        """Verify ValueError for unsupported metric."""
        with pytest.raises(ValueError, match="Unsupported metric"):
            plot_yearly(sample_multi_year_panel, "carbon_tax", metric="mode")


class TestPlotComparison:
    """Tests for plot_comparison() grouped bar chart function."""

    def test_returns_fig_axes(self, sample_indicator_table: pa.Table) -> None:
        """Verify return types."""
        fig, ax = plot_comparison(
            sample_indicator_table, sample_indicator_table, "carbon_tax"
        )
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(ax, matplotlib.axes.Axes)
        plt.close(fig)

    def test_grouped_bars(self, sample_indicator_table: pa.Table) -> None:
        """Verify two bar groups exist (20 bars total: 10 baseline + 10 reform)."""
        fig, ax = plot_comparison(
            sample_indicator_table, sample_indicator_table, "carbon_tax"
        )
        bars = [p for p in ax.patches if hasattr(p, "get_height")]
        assert len(bars) == 20  # 10 baseline + 10 reform
        plt.close(fig)

    def test_legend_labels(self, sample_indicator_table: pa.Table) -> None:
        """Verify legend has baseline/reform labels."""
        fig, ax = plot_comparison(
            sample_indicator_table,
            sample_indicator_table,
            "carbon_tax",
            baseline_label="Baseline",
            reform_label="Reform",
        )
        legend = ax.get_legend()
        assert legend is not None
        labels = [text.get_text() for text in legend.get_texts()]
        assert "Baseline" in labels
        assert "Reform" in labels
        plt.close(fig)

    def test_decile_mismatch_raises(self) -> None:
        """Verify ValueError when baseline and reform have different deciles."""
        baseline = pa.table(
            {
                "field_name": pa.array(["tax"] * 10, type=pa.utf8()),
                "decile": pa.array(list(range(1, 11)), type=pa.int64()),
                "year": pa.array([None] * 10, type=pa.int64()),
                "metric": pa.array(["mean"] * 10, type=pa.utf8()),
                "value": pa.array([float(i) for i in range(10)], type=pa.float64()),
            }
        )
        reform = pa.table(
            {
                "field_name": pa.array(["tax"] * 5, type=pa.utf8()),
                "decile": pa.array(list(range(1, 6)), type=pa.int64()),
                "year": pa.array([None] * 5, type=pa.int64()),
                "metric": pa.array(["mean"] * 5, type=pa.utf8()),
                "value": pa.array([float(i) for i in range(5)], type=pa.float64()),
            }
        )
        with pytest.raises(ValueError, match="Decile mismatch"):
            plot_comparison(baseline, reform, "tax")


class TestIndicatorResultPlotDeciles:
    """Tests for IndicatorResult.plot_deciles() convenience method."""

    def test_returns_fig_axes(self, sample_indicator_result: IndicatorResult) -> None:
        """Verify the convenience method returns (Figure, Axes)."""
        fig, ax = sample_indicator_result.plot_deciles("carbon_tax")
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(ax, matplotlib.axes.Axes)
        plt.close(fig)

    def test_custom_title(self, sample_indicator_result: IndicatorResult) -> None:
        """Verify custom title is applied."""
        fig, ax = sample_indicator_result.plot_deciles(
            "carbon_tax", title="Custom Title"
        )
        assert ax.get_title() == "Custom Title"
        plt.close(fig)
