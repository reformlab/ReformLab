# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Multi-portfolio comparison for side-by-side indicator analysis.

Story 12.5: Implement Multi-Portfolio Comparison and Notebook Demo
FR45: Analyst can compare results across different policy portfolios side-by-side

This module provides:
- PortfolioComparisonInput: Input wrapper associating a label with a PanelOutput
- PortfolioComparisonConfig: Configuration for portfolio comparison
- PortfolioComparisonResult: Container for comparison results with cross-metrics
- CrossComparisonMetric: Single aggregate metric ranking portfolios
- compare_portfolios: Main API for multi-portfolio comparison
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

from reformlab.indicators.comparison import (
    ComparisonConfig,
    ComparisonResult,
    ScenarioInput,
    compare_scenarios,
)
from reformlab.indicators.types import (
    FiscalConfig,
    FiscalIndicators,
    IndicatorResult,
    WelfareConfig,
    WelfareIndicators,
)

if TYPE_CHECKING:
    from reformlab.indicators.types import DistributionalConfig
    from reformlab.orchestrator.panel import PanelOutput

logger = logging.getLogger(__name__)
_SUPPORTED_INDICATOR_TYPES = frozenset({"distributional", "fiscal"})


# ============================================================================
# Types
# ============================================================================


@dataclass(frozen=True)
class PortfolioComparisonInput:
    """Input wrapper associating a portfolio label with its panel output.

    Attributes:
        label: Human-readable portfolio label (e.g., "Green Transition").
        panel: PanelOutput from orchestrator run for this portfolio.
    """

    label: str
    panel: PanelOutput

    def __post_init__(self) -> None:
        if not self.label.strip():
            msg = "Portfolio label must be a non-empty string."
            raise ValueError(msg)


@dataclass(frozen=True)
class PortfolioComparisonConfig:
    """Configuration for portfolio comparison operations.

    Attributes:
        baseline_label: Label of the baseline portfolio for delta computation.
            If None, the first portfolio is used. Defaults to None.
        indicator_types: Which indicator types to compute.
            Defaults to ("distributional", "fiscal").
        include_welfare: Whether to compute welfare indicators (requires
            baseline vs reform). Defaults to False.
        include_deltas: Compute absolute delta columns. Defaults to True.
        include_pct_deltas: Compute percentage delta columns. Defaults to True.
        distributional_config: Passed to compute_distributional_indicators.
        fiscal_config: Passed to compute_fiscal_indicators.
        welfare_config: Passed to compute_welfare_indicators.
    """

    baseline_label: str | None = None
    indicator_types: tuple[str, ...] = ("distributional", "fiscal")
    include_welfare: bool = False
    include_deltas: bool = True
    include_pct_deltas: bool = True
    distributional_config: DistributionalConfig | None = None
    fiscal_config: FiscalConfig | None = None
    welfare_config: WelfareConfig | None = None


@dataclass(frozen=True)
class CrossComparisonMetric:
    """Single aggregate metric ranking portfolios from best to worst.

    Attributes:
        criterion: Metric name (e.g., "max_fiscal_revenue", "min_fiscal_cost").
        best_portfolio: Label of the portfolio ranked first.
        value: Metric value for the best portfolio.
        all_values: Metric value per portfolio label, ordered by ranking.
    """

    criterion: str
    best_portfolio: str
    value: float
    all_values: dict[str, float]


@dataclass(frozen=True)
class PortfolioComparisonResult:
    """Container for multi-portfolio comparison results.

    Attributes:
        comparisons: Per-indicator-type ComparisonResult, keyed by type string
            (e.g., {"distributional": ..., "fiscal": ...}).
        cross_metrics: Aggregate metrics ranking portfolios.
        portfolio_labels: Ordered portfolio labels.
        metadata: Run metadata.
        warnings: Collected warnings from all indicator computations.
    """

    comparisons: dict[str, ComparisonResult]
    cross_metrics: tuple[CrossComparisonMetric, ...]
    portfolio_labels: tuple[str, ...]
    metadata: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


# ============================================================================
# Cross-comparison metrics computation
# ============================================================================


def _compute_cross_comparison_metrics(
    fiscal_indicators: dict[str, IndicatorResult] | None,
    welfare_indicators: dict[str, IndicatorResult] | None,
    portfolio_labels: list[str],
) -> tuple[CrossComparisonMetric, ...]:
    """Compute aggregate cross-comparison metrics from per-portfolio indicators.

    Args:
        fiscal_indicators: Per-portfolio fiscal IndicatorResult, keyed by label.
        welfare_indicators: Per-portfolio welfare IndicatorResult, keyed by label.
        portfolio_labels: Ordered portfolio labels.

    Returns:
        Tuple of CrossComparisonMetric objects.
    """
    metrics: list[CrossComparisonMetric] = []

    if fiscal_indicators is not None:
        metrics.extend(_fiscal_cross_metrics(fiscal_indicators, portfolio_labels))

    if welfare_indicators is not None:
        metrics.extend(_welfare_cross_metrics(welfare_indicators, portfolio_labels))

    return tuple(metrics)


def _fiscal_cross_metrics(
    fiscal_indicators: dict[str, IndicatorResult],
    portfolio_labels: list[str],
) -> list[CrossComparisonMetric]:
    """Compute fiscal cross-comparison metrics."""
    metrics: list[CrossComparisonMetric] = []

    # Compute per-portfolio aggregates
    portfolio_totals: dict[str, dict[str, float]] = {}
    for label in portfolio_labels:
        if label not in fiscal_indicators:
            continue
        result = fiscal_indicators[label]
        total_revenue = 0.0
        total_cost = 0.0
        total_balance = 0.0
        for ind in result.indicators:
            if not isinstance(ind, FiscalIndicators):
                continue
            total_revenue += ind.revenue
            total_cost += ind.cost
            total_balance += ind.balance
        portfolio_totals[label] = {
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_balance": total_balance,
        }

    if not portfolio_totals:
        return metrics

    # max_fiscal_revenue (highest first)
    metrics.append(
        _build_metric(
            "max_fiscal_revenue",
            portfolio_totals,
            "total_revenue",
            descending=True,
            portfolio_labels=portfolio_labels,
        )
    )

    # min_fiscal_cost (lowest first)
    metrics.append(
        _build_metric(
            "min_fiscal_cost",
            portfolio_totals,
            "total_cost",
            descending=False,
            portfolio_labels=portfolio_labels,
        )
    )

    # max_fiscal_balance (highest first)
    metrics.append(
        _build_metric(
            "max_fiscal_balance",
            portfolio_totals,
            "total_balance",
            descending=True,
            portfolio_labels=portfolio_labels,
        )
    )

    return metrics


def _welfare_cross_metrics(
    welfare_indicators: dict[str, IndicatorResult],
    portfolio_labels: list[str],
) -> list[CrossComparisonMetric]:
    """Compute welfare cross-comparison metrics."""
    metrics: list[CrossComparisonMetric] = []

    portfolio_totals: dict[str, dict[str, float]] = {}
    for label in portfolio_labels:
        if label not in welfare_indicators:
            continue
        result = welfare_indicators[label]
        net_changes: list[float] = []
        total_winners = 0
        total_losers = 0
        for ind in result.indicators:
            if not isinstance(ind, WelfareIndicators):
                continue
            net_changes.append(ind.net_change)
            total_winners += ind.winner_count
            total_losers += ind.loser_count

        mean_net_change = sum(net_changes) / len(net_changes) if net_changes else 0.0
        portfolio_totals[label] = {
            "mean_net_change": mean_net_change,
            "total_winners": float(total_winners),
            "total_losers": float(total_losers),
        }

    if not portfolio_totals:
        return metrics

    # max_mean_welfare_net_change (highest first)
    metrics.append(
        _build_metric(
            "max_mean_welfare_net_change",
            portfolio_totals,
            "mean_net_change",
            descending=True,
            portfolio_labels=portfolio_labels,
        )
    )

    # max_total_winners (most winners first)
    metrics.append(
        _build_metric(
            "max_total_winners",
            portfolio_totals,
            "total_winners",
            descending=True,
            portfolio_labels=portfolio_labels,
        )
    )

    # min_total_losers (fewest losers first)
    metrics.append(
        _build_metric(
            "min_total_losers",
            portfolio_totals,
            "total_losers",
            descending=False,
            portfolio_labels=portfolio_labels,
        )
    )

    return metrics


def _build_metric(
    criterion: str,
    portfolio_totals: dict[str, dict[str, float]],
    value_key: str,
    *,
    descending: bool,
    portfolio_labels: list[str],
) -> CrossComparisonMetric:
    """Build a single CrossComparisonMetric with sorted ranking.

    Uses stable sort to maintain input order for tie-breaking.
    """
    # Build list of (label, value) maintaining input order for stable sort
    items = [
        (label, portfolio_totals[label][value_key])
        for label in portfolio_labels
        if label in portfolio_totals
    ]

    # Stable sort: descending for "max_*", ascending for "min_*"
    items.sort(key=lambda x: x[1], reverse=descending)

    all_values = {label: value for label, value in items}
    best_label, best_value = items[0]

    return CrossComparisonMetric(
        criterion=criterion,
        best_portfolio=best_label,
        value=best_value,
        all_values=all_values,
    )


def _validate_indicator_types(indicator_types: tuple[str, ...]) -> tuple[str, ...]:
    """Validate and normalize requested indicator types.

    Returns lowercase, de-duplicated indicator types preserving input order.
    """
    normalized: list[str] = []
    seen: set[str] = set()

    for indicator_type in indicator_types:
        if not isinstance(indicator_type, str) or not indicator_type.strip():
            msg = "Indicator types must be non-empty strings."
            raise ValueError(msg)

        normalized_type = indicator_type.strip().lower()
        if normalized_type == "welfare":
            msg = (
                "Indicator type 'welfare' is controlled by include_welfare=True. "
                "Remove 'welfare' from indicator_types and set include_welfare=True."
            )
            raise ValueError(msg)
        if normalized_type not in _SUPPORTED_INDICATOR_TYPES:
            msg = (
                f"Unknown indicator type '{indicator_type}'. "
                f"Supported types: {sorted(_SUPPORTED_INDICATOR_TYPES)}. "
                "Use include_welfare=True for welfare comparison."
            )
            raise ValueError(msg)
        if normalized_type in seen:
            continue
        seen.add(normalized_type)
        normalized.append(normalized_type)

    return tuple(normalized)


# ============================================================================
# Main comparison function
# ============================================================================


def compare_portfolios(
    portfolios: list[PortfolioComparisonInput],
    config: PortfolioComparisonConfig | None = None,
) -> PortfolioComparisonResult:
    """Compare indicator results across multiple policy portfolios side-by-side.

    Computes indicators for each portfolio, then uses compare_scenarios() for
    each indicator type to produce side-by-side comparison tables. Adds
    cross-comparison aggregate metrics on top.

    Args:
        portfolios: List of PortfolioComparisonInput objects (min 2).
        config: Comparison configuration. If None, uses defaults.

    Returns:
        PortfolioComparisonResult with per-indicator comparisons and
        cross-comparison metrics.

    Raises:
        ValueError: If fewer than 2 portfolios, duplicate labels, empty labels,
            or labels conflict with reserved column names.
    """
    if config is None:
        config = PortfolioComparisonConfig()
    normalized_indicator_types = _validate_indicator_types(config.indicator_types)

    # --- Input validation ---
    if len(portfolios) < 2:
        msg = (
            f"Comparison requires at least 2 portfolios, got {len(portfolios)}. "
            f"Provide at least two PortfolioComparisonInput objects."
        )
        raise ValueError(msg)
    if not normalized_indicator_types and not config.include_welfare:
        msg = (
            "No indicators requested. Provide at least one indicator type "
            "(distributional or fiscal), or set include_welfare=True."
        )
        raise ValueError(msg)

    labels = [p.label for p in portfolios]
    if any(not label.strip() for label in labels):
        msg = "Portfolio labels must be non-empty strings."
        raise ValueError(msg)

    if len(labels) != len(set(labels)):
        duplicate_labels = [label for label in set(labels) if labels.count(label) > 1]
        msg = (
            f"Duplicate portfolio labels detected: {duplicate_labels}. "
            f"Each portfolio must have a unique label."
        )
        raise ValueError(msg)

    # Check reserved names (same as compare_scenarios)
    reserved_labels = {
        "field_name", "decile", "year", "metric", "value", "region",
    }
    invalid_labels = [label for label in labels if label in reserved_labels]
    if invalid_labels:
        msg = (
            f"Invalid portfolio labels: {invalid_labels}. "
            f"Portfolio labels cannot match reserved table columns: {sorted(reserved_labels)}."
        )
        raise ValueError(msg)

    prefix_conflicts = [
        label
        for label in labels
        if label.startswith("delta_") or label.startswith("pct_delta_")
    ]
    if prefix_conflicts:
        msg = (
            f"Invalid portfolio labels: {prefix_conflicts}. "
            "Portfolio labels cannot start with 'delta_' or 'pct_delta_' because "
            "these prefixes are reserved for computed columns."
        )
        raise ValueError(msg)

    # Resolve baseline label
    baseline_label = config.baseline_label or labels[0]
    if baseline_label not in labels:
        msg = (
            f"Baseline label '{baseline_label}' not found in portfolio labels: {labels}. "
            f"Ensure the baseline_label matches one of the provided portfolio labels."
        )
        raise ValueError(msg)

    all_warnings: list[str] = []
    comparisons: dict[str, ComparisonResult] = {}
    fiscal_indicators_map: dict[str, IndicatorResult] | None = None
    welfare_indicators_map: dict[str, IndicatorResult] | None = None

    # --- Compute indicators per type ---

    for indicator_type in normalized_indicator_types:
        per_portfolio_results: dict[str, IndicatorResult] = {}

        for portfolio in portfolios:
            ind_result = _compute_indicators_for_type(
                indicator_type, portfolio, config, all_warnings
            )
            if ind_result is not None:
                per_portfolio_results[portfolio.label] = ind_result

        if not per_portfolio_results:
            all_warnings.append(
                f"[{indicator_type}] No indicator results computed for any portfolio."
            )
            continue

        # Track fiscal indicators for cross-comparison
        if indicator_type == "fiscal":
            fiscal_indicators_map = per_portfolio_results

        # Wrap as ScenarioInput and compare
        scenario_inputs = [
            ScenarioInput(label=label, indicators=result)
            for label, result in per_portfolio_results.items()
        ]

        if len(scenario_inputs) >= 2:
            comparison_config = ComparisonConfig(
                baseline_label=baseline_label if baseline_label in per_portfolio_results else None,
                include_deltas=config.include_deltas,
                include_pct_deltas=config.include_pct_deltas,
            )
            comparison_result = compare_scenarios(scenario_inputs, comparison_config)
            for w in comparison_result.warnings:
                all_warnings.append(f"[{indicator_type}] {w}")
            comparisons[indicator_type] = comparison_result

    # --- Welfare indicators (opt-in) ---
    if config.include_welfare:
        welfare_indicators_map = _compute_welfare_portfolios(
            portfolios, config, baseline_label, labels, comparisons, all_warnings
        )

    # --- Cross-comparison metrics ---
    cross_metrics = _compute_cross_comparison_metrics(
        fiscal_indicators_map, welfare_indicators_map, labels
    )

    # --- Build metadata ---
    metadata: dict[str, Any] = {
        "portfolio_labels": labels,
        "baseline_label": baseline_label,
        "indicator_types": list(normalized_indicator_types),
        "computed_indicator_types": list(comparisons.keys()),
        "include_welfare": config.include_welfare,
        "config": {
            "baseline_label": config.baseline_label,
            "indicator_types": list(config.indicator_types),
            "include_welfare": config.include_welfare,
            "include_deltas": config.include_deltas,
            "include_pct_deltas": config.include_pct_deltas,
            "distributional_config": (
                asdict(config.distributional_config)
                if config.distributional_config is not None
                else None
            ),
            "fiscal_config": (
                asdict(config.fiscal_config)
                if config.fiscal_config is not None
                else None
            ),
            "welfare_config": (
                asdict(config.welfare_config)
                if config.welfare_config is not None
                else None
            ),
        },
    }

    return PortfolioComparisonResult(
        comparisons=comparisons,
        cross_metrics=cross_metrics,
        portfolio_labels=tuple(labels),
        metadata=metadata,
        warnings=all_warnings,
    )


def _compute_indicators_for_type(
    indicator_type: str,
    portfolio: PortfolioComparisonInput,
    config: PortfolioComparisonConfig,
    warnings_list: list[str],
) -> IndicatorResult | None:
    """Compute indicators for a given type and portfolio.

    Returns None if computation fails (adds warning instead of raising).
    """
    from reformlab.indicators.distributional import compute_distributional_indicators
    from reformlab.indicators.fiscal import compute_fiscal_indicators

    try:
        if indicator_type == "distributional":
            return compute_distributional_indicators(
                portfolio.panel, config.distributional_config
            )
        elif indicator_type == "fiscal":
            return compute_fiscal_indicators(portfolio.panel, config.fiscal_config)
        else:
            msg = (
                f"Unknown indicator type '{indicator_type}'. "
                f"Supported types: {sorted(_SUPPORTED_INDICATOR_TYPES)}."
            )
            raise ValueError(msg)
    except ValueError as e:
        warnings_list.append(
            f"[{indicator_type}] Skipping portfolio '{portfolio.label}': {e}"
        )
        return None


def _compute_welfare_portfolios(
    portfolios: list[PortfolioComparisonInput],
    config: PortfolioComparisonConfig,
    baseline_label: str,
    labels: list[str],
    comparisons: dict[str, ComparisonResult],
    all_warnings: list[str],
) -> dict[str, IndicatorResult]:
    """Compute welfare indicators for each non-baseline portfolio vs baseline.

    Returns per-portfolio welfare IndicatorResult dict.
    """
    from reformlab.indicators.welfare import compute_welfare_indicators

    # Find baseline panel
    baseline_panel = None
    for p in portfolios:
        if p.label == baseline_label:
            baseline_panel = p.panel
            break

    if baseline_panel is None:
        all_warnings.append(
            f"[welfare] Baseline portfolio '{baseline_label}' not found; "
            "skipping welfare computation."
        )
        return {}

    welfare_results: dict[str, IndicatorResult] = {}
    for portfolio in portfolios:
        if portfolio.label == baseline_label:
            continue
        try:
            welfare_result = compute_welfare_indicators(
                baseline_panel, portfolio.panel, config.welfare_config
            )
        except ValueError as e:
            all_warnings.append(
                f"[welfare] Skipping portfolio '{portfolio.label}': {e}"
            )
            continue
        for w in welfare_result.warnings:
            all_warnings.append(f"[welfare] {w}")
        welfare_results[portfolio.label] = welfare_result

    if not welfare_results:
        return {}

    # Build scenario inputs for welfare comparison
    scenario_inputs = [
        ScenarioInput(label=label, indicators=result)
        for label, result in welfare_results.items()
    ]

    if len(scenario_inputs) >= 2:
        comparison_config = ComparisonConfig(
            baseline_label=None,
            include_deltas=config.include_deltas,
            include_pct_deltas=config.include_pct_deltas,
        )
        welfare_comparison = compare_scenarios(scenario_inputs, comparison_config)
        for w in welfare_comparison.warnings:
            all_warnings.append(f"[welfare] {w}")
        comparisons["welfare"] = welfare_comparison
    elif len(scenario_inputs) == 1:
        # Edge case: exactly 2 portfolios means 1 non-baseline welfare result
        all_warnings.append(
            "[welfare] Only 2 portfolios provided; welfare indicators computed "
            "without cross-portfolio deltas. Use 3+ portfolios for welfare comparison."
        )
        # Store single-portfolio welfare as a degenerate comparison
        single = scenario_inputs[0]
        comparisons["welfare"] = ComparisonResult(
            table=single.indicators.to_table(),
            metadata={
                "scenario_labels": [single.label],
                "baseline_label": single.label,
                "indicator_schema": "decile",
                "single_portfolio_welfare": True,
            },
            warnings=[
                "Single-portfolio welfare result; no cross-portfolio deltas available."
            ],
        )

    return welfare_results
