# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Shared fixtures for visualization tests."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import pyarrow as pa
import pytest

from reformlab.indicators.types import DecileIndicators, IndicatorResult


@pytest.fixture()
def sample_multi_year_panel() -> pa.Table:
    """Two-year panel with 10 households per year."""
    ids = list(range(10)) * 2
    years = [2025] * 10 + [2026] * 10
    income = [15000.0 + i * 8000.0 for i in range(10)] * 2
    carbon_tax = [150.0 + i * 5.0 for i in range(10)] + [
        160.0 + i * 5.0 for i in range(10)
    ]
    return pa.table(
        {
            "household_id": pa.array(ids, type=pa.int64()),
            "year": pa.array(years, type=pa.int64()),
            "income": pa.array(income, type=pa.float64()),
            "carbon_tax": pa.array(carbon_tax, type=pa.float64()),
            "disposable_income": pa.array(
                [inc - tax for inc, tax in zip(income, carbon_tax)],
                type=pa.float64(),
            ),
        }
    )


@pytest.fixture()
def sample_indicator_table() -> pa.Table:
    """Long-form indicator table: 10 deciles × 6 metrics for carbon_tax."""
    metrics = ("count", "mean", "median", "sum", "min", "max")
    field_names: list[str] = []
    deciles: list[int] = []
    years: list[int | None] = []
    metric_names: list[str] = []
    values: list[float] = []

    for decile in range(1, 11):
        for metric in metrics:
            field_names.append("carbon_tax")
            deciles.append(decile)
            years.append(None)
            metric_names.append(metric)
            if metric == "count":
                values.append(10.0)
            elif metric == "mean":
                values.append(150.0 + decile * 5.0)
            elif metric == "median":
                values.append(149.0 + decile * 5.0)
            elif metric == "sum":
                values.append(1500.0 + decile * 50.0)
            elif metric == "min":
                values.append(140.0 + decile * 5.0)
            else:  # max
                values.append(160.0 + decile * 5.0)

    return pa.table(
        {
            "field_name": pa.array(field_names, type=pa.utf8()),
            "decile": pa.array(deciles, type=pa.int64()),
            "year": pa.array(years, type=pa.int64()),
            "metric": pa.array(metric_names, type=pa.utf8()),
            "value": pa.array(values, type=pa.float64()),
        }
    )


@pytest.fixture()
def sample_indicator_result(sample_indicator_table: pa.Table) -> IndicatorResult:
    """IndicatorResult wrapping distributional indicators for carbon_tax."""
    indicators = [
        DecileIndicators(
            field_name="carbon_tax",
            decile=decile,
            year=None,
            count=10,
            mean=150.0 + decile * 5.0,
            median=149.0 + decile * 5.0,
            sum=1500.0 + decile * 50.0,
            min=140.0 + decile * 5.0,
            max=160.0 + decile * 5.0,
        )
        for decile in range(1, 11)
    ]
    return IndicatorResult(
        indicators=indicators,
        metadata={"income_field": "income", "indicator_type": "distributional"},
    )
