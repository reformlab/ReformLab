# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for multi-portfolio comparison.

Story 12.5: Implement Multi-Portfolio Comparison and Notebook Demo

Tests cover:
- AC1: Multi-portfolio side-by-side comparison
- AC2: Cross-comparison aggregate metrics
- AC3: Backward compatibility with pairwise comparison API
- AC5: Input validation and error handling
- AC6: Export support
"""

from __future__ import annotations

from typing import Any

import pytest

from reformlab.indicators.comparison import (
    ScenarioInput,
    compare_scenarios,
)
from reformlab.indicators.portfolio_comparison import (
    CrossComparisonMetric,
    PortfolioComparisonConfig,
    PortfolioComparisonInput,
    PortfolioComparisonResult,
    compare_portfolios,
)
from reformlab.indicators.types import FiscalConfig, WelfareConfig
from reformlab.orchestrator.panel import PanelOutput


def _make_portfolio_input(
    label: str, panel: PanelOutput
) -> PortfolioComparisonInput:
    return PortfolioComparisonInput(label=label, panel=panel)


class TestComparePortfoliosBasic:
    """AC1: Multi-portfolio side-by-side comparison with distributional indicators."""

    def test_three_portfolios_distributional(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """Compare 3 portfolios with distributional indicators."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        config = PortfolioComparisonConfig(indicator_types=("distributional",))
        result = compare_portfolios(inputs, config)

        assert isinstance(result, PortfolioComparisonResult)
        assert "distributional" in result.comparisons
        comparison = result.comparisons["distributional"]
        assert comparison.table.num_rows > 0

        # All portfolio labels should appear as column names
        for label in portfolio_panels:
            assert label in comparison.table.column_names

    def test_portfolio_labels_in_result(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """Assert portfolio_labels tuple matches input order."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        result = compare_portfolios(inputs)
        assert result.portfolio_labels == tuple(portfolio_panels.keys())

    def test_metadata_contains_required_keys(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """AC1: metadata dict contains portfolio_labels, baseline_label, indicator_types."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        result = compare_portfolios(inputs)
        assert "portfolio_labels" in result.metadata
        assert "baseline_label" in result.metadata
        assert "indicator_types" in result.metadata
        assert "computed_indicator_types" in result.metadata
        assert "config" in result.metadata
        assert result.metadata["config"]["include_welfare"] is False
        assert isinstance(result.warnings, list)


class TestComparePortfoliosFiscal:
    """AC1: Multi-portfolio side-by-side comparison with fiscal indicators."""

    def test_three_portfolios_fiscal(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """Compare 3 portfolios with fiscal indicators."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        config = PortfolioComparisonConfig(
            indicator_types=("fiscal",),
            fiscal_config=FiscalConfig(
                revenue_fields=["carbon_tax"],
                cost_fields=["subsidy_amount"],
            ),
        )
        result = compare_portfolios(inputs, config)

        assert "fiscal" in result.comparisons
        comparison = result.comparisons["fiscal"]
        assert comparison.table.num_rows > 0
        for label in portfolio_panels:
            assert label in comparison.table.column_names


class TestComparePortfoliosWelfare:
    """AC1, AC2: Welfare indicators with baseline vs reform."""

    def test_welfare_with_three_portfolios(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """Welfare comparison uses baseline panel vs each reform panel."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        config = PortfolioComparisonConfig(
            indicator_types=(),
            include_welfare=True,
            welfare_config=WelfareConfig(
                welfare_field="carbon_tax",
                income_field="income",
            ),
        )
        result = compare_portfolios(inputs, config)

        assert "welfare" in result.comparisons
        welfare_comparison = result.comparisons["welfare"]
        # Baseline is excluded from welfare comparison
        baseline_label = list(portfolio_panels.keys())[0]
        assert baseline_label not in welfare_comparison.metadata.get(
            "scenario_labels", []
        )

    def test_welfare_two_portfolios_edge_case(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """With exactly 2 portfolios, welfare has no cross-portfolio deltas."""
        labels = list(portfolio_panels.keys())[:2]
        inputs = [
            _make_portfolio_input(label, portfolio_panels[label])
            for label in labels
        ]
        config = PortfolioComparisonConfig(
            indicator_types=(),
            include_welfare=True,
            welfare_config=WelfareConfig(
                welfare_field="carbon_tax",
                income_field="income",
            ),
        )
        result = compare_portfolios(inputs, config)

        assert "welfare" in result.comparisons
        # Should have a warning about 2-portfolio edge case
        welfare_warnings = [w for w in result.warnings if "welfare" in w.lower()]
        assert any("2 portfolios" in w for w in welfare_warnings)

    def test_welfare_skips_invalid_reform_with_warning(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """Invalid welfare input for one reform is skipped, not fatal."""
        labels = list(portfolio_panels.keys())
        invalid_panel_src = portfolio_panels[labels[2]]
        invalid_panel = PanelOutput(
            table=invalid_panel_src.table.drop_columns(["carbon_tax"]),
            metadata=invalid_panel_src.metadata,
        )
        inputs = [
            _make_portfolio_input(labels[0], portfolio_panels[labels[0]]),
            _make_portfolio_input(labels[1], portfolio_panels[labels[1]]),
            _make_portfolio_input(labels[2], invalid_panel),
        ]
        config = PortfolioComparisonConfig(
            indicator_types=(),
            include_welfare=True,
            welfare_config=WelfareConfig(
                welfare_field="carbon_tax",
                income_field="income",
            ),
        )

        result = compare_portfolios(inputs, config)

        assert "welfare" in result.comparisons
        assert result.comparisons["welfare"].metadata.get("single_portfolio_welfare") is True
        assert any(
            f"Skipping portfolio '{labels[2]}'" in warning for warning in result.warnings
        )


class TestCrossComparisonMetrics:
    """AC2: Cross-comparison aggregate metrics."""

    def test_fiscal_cross_metrics(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """Fiscal cross-metrics include revenue, cost, balance rankings."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        config = PortfolioComparisonConfig(
            indicator_types=("fiscal",),
            fiscal_config=FiscalConfig(
                revenue_fields=["carbon_tax"],
                cost_fields=["subsidy_amount"],
            ),
        )
        result = compare_portfolios(inputs, config)

        assert len(result.cross_metrics) > 0
        criteria = {m.criterion for m in result.cross_metrics}
        assert "max_fiscal_revenue" in criteria
        assert "min_fiscal_cost" in criteria
        assert "max_fiscal_balance" in criteria

        for metric in result.cross_metrics:
            assert isinstance(metric, CrossComparisonMetric)
            assert metric.best_portfolio in portfolio_panels
            assert len(metric.all_values) == 3
            # all_values should be sorted by ranking
            values = list(metric.all_values.values())
            if metric.criterion.startswith("max_"):
                assert values == sorted(values, reverse=True)
            else:
                assert values == sorted(values)


class TestCrossComparisonMetricsWelfare:
    """AC2: Welfare cross-metrics."""

    def test_welfare_cross_metrics(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """Welfare cross-metrics include net_change, winners, losers."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        config = PortfolioComparisonConfig(
            indicator_types=(),
            include_welfare=True,
            welfare_config=WelfareConfig(
                welfare_field="carbon_tax",
                income_field="income",
            ),
        )
        result = compare_portfolios(inputs, config)

        criteria = {m.criterion for m in result.cross_metrics}
        assert "max_mean_welfare_net_change" in criteria
        assert "max_total_winners" in criteria
        assert "min_total_losers" in criteria


class TestBackwardCompatibility:
    """AC3: Backward compatibility with pairwise comparison API."""

    def test_compare_scenarios_with_portfolio_results(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """compare_scenarios() works directly with portfolio ScenarioInputs."""
        from reformlab.indicators.distributional import compute_distributional_indicators

        labels = list(portfolio_panels.keys())[:2]
        panels = [portfolio_panels[label] for label in labels]

        # Compute indicators for each
        indicators = [
            compute_distributional_indicators(panel) for panel in panels
        ]

        scenario_inputs = [
            ScenarioInput(label=label, indicators=ind)
            for label, ind in zip(labels, indicators)
        ]

        # Direct compare_scenarios call should work
        result = compare_scenarios(scenario_inputs)
        assert result.table.num_rows > 0
        for label in labels:
            assert label in result.table.column_names

    def test_compare_portfolios_matches_compare_scenarios(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """compare_portfolios per-indicator result matches compare_scenarios."""
        from reformlab.indicators.distributional import compute_distributional_indicators

        labels = list(portfolio_panels.keys())[:2]
        panels = [portfolio_panels[label] for label in labels]

        # Via compare_portfolios
        portfolio_inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in zip(labels, panels)
        ]
        portfolio_config = PortfolioComparisonConfig(
            indicator_types=("distributional",)
        )
        portfolio_result = compare_portfolios(portfolio_inputs, portfolio_config)

        # Via compare_scenarios directly
        indicators = [
            compute_distributional_indicators(panel) for panel in panels
        ]
        scenario_inputs = [
            ScenarioInput(label=label, indicators=ind)
            for label, ind in zip(labels, indicators)
        ]
        direct_result = compare_scenarios(scenario_inputs)

        # Tables should have the same shape
        ptable = portfolio_result.comparisons["distributional"].table
        dtable = direct_result.table
        assert ptable.num_rows == dtable.num_rows
        assert ptable.num_columns == dtable.num_columns


class TestComparePortfoliosValidation:
    """AC5: Input validation and error handling."""

    def test_fewer_than_two_portfolios(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """ValueError for fewer than 2 portfolios."""
        label = list(portfolio_panels.keys())[0]
        inputs = [_make_portfolio_input(label, portfolio_panels[label])]
        with pytest.raises(ValueError, match="at least 2 portfolios"):
            compare_portfolios(inputs)

    def test_empty_list(self) -> None:
        """ValueError for empty list."""
        with pytest.raises(ValueError, match="at least 2 portfolios"):
            compare_portfolios([])

    def test_duplicate_labels(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """ValueError for duplicate labels."""
        panel = list(portfolio_panels.values())[0]
        inputs = [
            _make_portfolio_input("same", panel),
            _make_portfolio_input("same", panel),
        ]
        with pytest.raises(ValueError, match="Duplicate portfolio labels"):
            compare_portfolios(inputs)

    def test_empty_label(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """ValueError for empty label in PortfolioComparisonInput."""
        panel = list(portfolio_panels.values())[0]
        with pytest.raises(ValueError, match="non-empty"):
            _make_portfolio_input("", panel)

    def test_whitespace_label(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """ValueError for whitespace-only label."""
        panel = list(portfolio_panels.values())[0]
        with pytest.raises(ValueError, match="non-empty"):
            _make_portfolio_input("   ", panel)

    def test_reserved_label(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """ValueError for labels matching reserved column names."""
        panels = list(portfolio_panels.values())
        inputs = [
            _make_portfolio_input("value", panels[0]),
            _make_portfolio_input("other", panels[1]),
        ]
        with pytest.raises(ValueError, match="reserved table columns"):
            compare_portfolios(inputs)

    def test_delta_prefix_label(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """ValueError for labels starting with delta_ or pct_delta_."""
        panels = list(portfolio_panels.values())
        inputs = [
            _make_portfolio_input("delta_x", panels[0]),
            _make_portfolio_input("other", panels[1]),
        ]
        with pytest.raises(ValueError, match="delta_"):
            compare_portfolios(inputs)

    def test_unknown_indicator_type(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """ValueError for unsupported indicator type."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        config = PortfolioComparisonConfig(indicator_types=("unknown",))
        with pytest.raises(ValueError, match="Unknown indicator type"):
            compare_portfolios(inputs, config)

    def test_welfare_indicator_type_requires_include_flag(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """welfare in indicator_types should fail with guidance."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        config = PortfolioComparisonConfig(indicator_types=("welfare",))
        with pytest.raises(ValueError, match="include_welfare=True"):
            compare_portfolios(inputs, config)

    def test_empty_indicator_types_without_welfare(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """At least one indicator must be requested unless welfare is enabled."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        with pytest.raises(ValueError, match="No indicators requested"):
            compare_portfolios(inputs, PortfolioComparisonConfig(indicator_types=()))


class TestComparePortfoliosExport:
    """AC6: Export support for comparison results."""

    def test_export_csv_and_parquet(
        self, portfolio_panels: dict[str, PanelOutput], tmp_path: Any
    ) -> None:
        """Export each comparison to CSV and Parquet, verify round-trip."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        config = PortfolioComparisonConfig(
            indicator_types=("distributional", "fiscal"),
            fiscal_config=FiscalConfig(
                revenue_fields=["carbon_tax"],
                cost_fields=["subsidy_amount"],
            ),
        )
        result = compare_portfolios(inputs, config)

        for indicator_type, comparison in result.comparisons.items():
            csv_path = comparison.export_csv(tmp_path / f"{indicator_type}.csv")
            parquet_path = comparison.export_parquet(
                tmp_path / f"{indicator_type}.parquet"
            )

            assert csv_path.exists()
            assert parquet_path.exists()

            # Verify round-trip shape
            import pyarrow.parquet as pq

            roundtrip = pq.read_table(str(parquet_path))
            assert roundtrip.num_rows == comparison.table.num_rows
            assert roundtrip.num_columns == comparison.table.num_columns

    def test_cross_metrics_are_tuple(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """Cross-comparison metrics are available as a tuple for programmatic access."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        config = PortfolioComparisonConfig(
            indicator_types=("fiscal",),
            fiscal_config=FiscalConfig(
                revenue_fields=["carbon_tax"],
                cost_fields=["subsidy_amount"],
            ),
        )
        result = compare_portfolios(inputs, config)
        assert isinstance(result.cross_metrics, tuple)
        for metric in result.cross_metrics:
            assert isinstance(metric, CrossComparisonMetric)


class TestComparePortfoliosConfig:
    """AC1: Custom configuration options."""

    def test_custom_baseline_label(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """Set baseline_label to non-first portfolio."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        non_first_label = list(portfolio_panels.keys())[1]
        config = PortfolioComparisonConfig(
            indicator_types=("distributional",),
            baseline_label=non_first_label,
        )
        result = compare_portfolios(inputs, config)
        assert result.metadata["baseline_label"] == non_first_label

    def test_include_deltas_false(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """include_deltas=False produces no delta columns."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        config = PortfolioComparisonConfig(
            indicator_types=("distributional",),
            include_deltas=False,
            include_pct_deltas=False,
        )
        result = compare_portfolios(inputs, config)
        comparison = result.comparisons["distributional"]
        delta_cols = [
            c for c in comparison.table.column_names if c.startswith("delta_")
        ]
        pct_delta_cols = [
            c for c in comparison.table.column_names if c.startswith("pct_delta_")
        ]
        assert len(delta_cols) == 0
        assert len(pct_delta_cols) == 0

    def test_fiscal_only_indicator_type(
        self, portfolio_panels: dict[str, PanelOutput]
    ) -> None:
        """indicator_types=('fiscal',) produces only fiscal comparison."""
        inputs = [
            _make_portfolio_input(label, panel)
            for label, panel in portfolio_panels.items()
        ]
        config = PortfolioComparisonConfig(
            indicator_types=("fiscal",),
            fiscal_config=FiscalConfig(
                revenue_fields=["carbon_tax"],
                cost_fields=["subsidy_amount"],
            ),
        )
        result = compare_portfolios(inputs, config)
        assert "fiscal" in result.comparisons
        assert "distributional" not in result.comparisons
