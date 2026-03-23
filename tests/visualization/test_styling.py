# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for reformlab.visualization.styling module."""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")

from reformlab.visualization.styling import create_figure, style_axes


class TestCreateFigure:
    """Tests for create_figure() factory function."""

    def test_returns_fig_and_axes(self) -> None:
        """Verify return types are Figure and Axes."""
        fig, ax = create_figure()
        assert isinstance(fig, matplotlib.figure.Figure)
        assert isinstance(ax, matplotlib.axes.Axes)
        plt.close(fig)

    def test_applies_title(self) -> None:
        """Verify ax.get_title() matches provided title."""
        fig, ax = create_figure(title="Test Title")
        assert ax.get_title() == "Test Title"
        plt.close(fig)

    def test_applies_labels(self) -> None:
        """Verify xlabel and ylabel are set."""
        fig, ax = create_figure(xlabel="X Label", ylabel="Y Label")
        assert ax.get_xlabel() == "X Label"
        assert ax.get_ylabel() == "Y Label"
        plt.close(fig)

    def test_default_figsize(self) -> None:
        """Verify default figsize is (10, 6)."""
        fig, ax = create_figure()
        width, height = fig.get_size_inches()
        assert abs(width - 10.0) < 0.1
        assert abs(height - 6.0) < 0.1
        plt.close(fig)

    def test_custom_figsize(self) -> None:
        """Verify custom figsize is applied."""
        fig, ax = create_figure(figsize=(12, 8))
        width, height = fig.get_size_inches()
        assert abs(width - 12.0) < 0.1
        assert abs(height - 8.0) < 0.1
        plt.close(fig)


class TestStyleAxes:
    """Tests for style_axes() utility function."""

    def test_applies_grid(self) -> None:
        """Verify grid is enabled on the axes."""
        fig, ax = plt.subplots()
        style_axes(ax)
        # Grid lines should exist after styling
        assert ax.yaxis.get_gridlines()[0].get_visible()
        plt.close(fig)

    def test_applies_xticks(self) -> None:
        """Verify explicit xticks are set."""
        fig, ax = plt.subplots()
        style_axes(ax, xticks=[1, 2, 3, 4, 5])
        ticks = [int(t) for t in ax.get_xticks()]
        assert ticks == [1, 2, 3, 4, 5]
        plt.close(fig)
