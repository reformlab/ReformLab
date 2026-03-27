# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Population comparison utility for observed vs synthetic datasets.

Story 21.4 - add-public-synthetic-asset-ingestion-and-observed-versus-synthetic-comparison-flows.

This module provides utilities for comparing observed and synthetic populations,
computing distributional statistics (mean, median, std, quantiles) and relative
differences for common numeric columns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow as pa

if TYPE_CHECKING:
    from reformlab.data.descriptor import DataAssetDescriptor
else:
    from reformlab.data.descriptor import DataAssetDescriptor


@dataclass(frozen=True)
class NumericColumnComparison:
    """Comparison of a single numeric column between observed and synthetic populations.

    Attributes
    ----------
    column_name : str
        Name of the column being compared.
    observed_mean : float
        Mean value from observed population.
    synthetic_mean : float
        Mean value from synthetic population.
    relative_diff_pct : float
        Relative difference percentage: ((synthetic - observed) / observed) * 100.
    observed_median : float
        Median value from observed population.
    synthetic_median : float
        Median value from synthetic population.
    observed_std : float
        Standard deviation from observed population.
    synthetic_std : float
        Standard deviation from synthetic population.
    observed_p10 : float
        10th percentile from observed population.
    synthetic_p10 : float
        10th percentile from synthetic population.
    observed_p50 : float
        50th percentile (median) from observed population.
    synthetic_p50 : float
        50th percentile (median) from synthetic population.
    observed_p90 : float
        90th percentile from observed population.
    synthetic_p90 : float
        90th percentile from synthetic population.

    Story 21.4 / AC3, AC8.
    """

    column_name: str
    observed_mean: float
    synthetic_mean: float
    relative_diff_pct: float
    observed_median: float
    synthetic_median: float
    observed_std: float
    synthetic_std: float
    observed_p10: float
    synthetic_p10: float
    observed_p50: float
    synthetic_p50: float
    observed_p90: float
    synthetic_p90: float


@dataclass(frozen=True)
class PopulationComparison:
    """Result of comparing observed vs synthetic population.

    Attributes
    ----------
    observed_asset_id : str
        Asset ID of the observed population.
    synthetic_asset_id : str
        Asset ID of the synthetic population.
    row_counts : dict[str, int]
        Row counts for observed and synthetic populations.
        Keys: "observed", "synthetic".
    column_counts : dict[str, int]
        Column counts for observed and synthetic populations.
    common_numeric_columns : list[str]
        Intersection of numeric column names from both populations.
    numeric_comparison : dict[str, NumericColumnComparison]
        Comparison metrics for each common numeric column.
    trust_labels : dict[str, dict[str, str]]
        Trust governance labels for both populations.
        Keys: "observed", "synthetic". Each has: "origin", "access_mode", "trust_status".

    Story 21.4 / AC3, AC8.
    """

    observed_asset_id: str
    synthetic_asset_id: str
    row_counts: dict[str, int]
    column_counts: dict[str, int]
    common_numeric_columns: list[str]
    numeric_comparison: dict[str, NumericColumnComparison]
    trust_labels: dict[str, dict[str, str]]


def compare_populations(
    observed_table: pa.Table,
    synthetic_table: pa.Table,
    observed_descriptor: DataAssetDescriptor,
    synthetic_descriptor: DataAssetDescriptor,
) -> PopulationComparison:
    """Compare observed and synthetic populations.

    Computes distributional statistics for all common numeric columns:
    mean, median, std, p10/p50/p90 quantiles, and relative difference percentages.

    Handles schema mismatch by comparing only the intersection of numeric columns.
    Raises ValueError if no common numeric columns exist.

    Parameters
    ----------
    observed_table : pa.Table
        Observed population data.
    synthetic_table : pa.Table
        Synthetic population data.
    observed_descriptor : DataAssetDescriptor
        Governance metadata for observed population (origin="open-official").
    synthetic_descriptor : DataAssetDescriptor
        Governance metadata for synthetic population (origin="synthetic-public").

    Returns
    -------
    PopulationComparison
        Comparison result with statistics and trust labels.

    Raises
    ------
    ValueError
        If no common numeric columns exist between the populations.

    Story 21.4 / AC3, AC8.
    """
    import pyarrow.compute as pc

    # Find common numeric columns
    observed_numeric = _get_numeric_column_names(observed_table)
    synthetic_numeric = _get_numeric_column_names(synthetic_table)
    common = sorted(observed_numeric & synthetic_numeric)

    if not common:
        raise ValueError(
            "No common numeric columns between observed and synthetic populations - "
            "comparison requires at least one shared numeric column"
        )

    # Compute comparison for each common column
    numeric_comparison: dict[str, NumericColumnComparison] = {}
    for col_name in common:
        observed_col = observed_table.column(col_name)
        synthetic_col = synthetic_table.column(col_name)

        # Drop nulls for statistics
        observed_valid = observed_col.drop_null()
        synthetic_valid = synthetic_col.drop_null()

        # Handle empty columns
        if observed_valid.length == 0 or synthetic_valid.length == 0:
            continue

        # Compute statistics
        obs_mean = float(pc.mean(observed_valid).as_py())
        syn_mean = float(pc.mean(synthetic_valid).as_py())
        relative_diff_pct = ((syn_mean - obs_mean) / obs_mean * 100) if obs_mean != 0 else 0.0

        # Median (p50) - computed once
        obs_median = float(pc.quantile(observed_valid, q=0.5)[0].as_py())
        syn_median = float(pc.quantile(synthetic_valid, q=0.5)[0].as_py())

        obs_std = 0.0
        syn_std = 0.0
        if observed_valid.length > 1:
            obs_std = float(pc.stddev(observed_valid).as_py())
        if synthetic_valid.length > 1:
            syn_std = float(pc.stddev(synthetic_valid).as_py())

        # Other quantiles
        obs_p10 = float(pc.quantile(observed_valid, q=0.1)[0].as_py())
        syn_p10 = float(pc.quantile(synthetic_valid, q=0.1)[0].as_py())
        obs_p90 = float(pc.quantile(observed_valid, q=0.9)[0].as_py())
        syn_p90 = float(pc.quantile(synthetic_valid, q=0.9)[0].as_py())

        numeric_comparison[col_name] = NumericColumnComparison(
            column_name=col_name,
            observed_mean=obs_mean,
            synthetic_mean=syn_mean,
            relative_diff_pct=relative_diff_pct,
            observed_median=obs_median,
            synthetic_median=syn_median,
            observed_std=obs_std,
            synthetic_std=syn_std,
            observed_p10=obs_p10,
            synthetic_p10=syn_p10,
            observed_p50=obs_median,  # p50 is median
            synthetic_p50=syn_median,  # p50 is median
            observed_p90=obs_p90,
            synthetic_p90=syn_p90,
        )

    # Build trust labels (explicit type for mypy compatibility)
    trust_labels: dict[str, dict[str, str]] = {
        "observed": {
            "origin": observed_descriptor.origin,
            "access_mode": observed_descriptor.access_mode,
            "trust_status": observed_descriptor.trust_status,
        },
        "synthetic": {
            "origin": synthetic_descriptor.origin,
            "access_mode": synthetic_descriptor.access_mode,
            "trust_status": synthetic_descriptor.trust_status,
        },
    }

    return PopulationComparison(
        observed_asset_id=observed_descriptor.asset_id,
        synthetic_asset_id=synthetic_descriptor.asset_id,
        row_counts={
            "observed": observed_table.num_rows,
            "synthetic": synthetic_table.num_rows,
        },
        column_counts={
            "observed": observed_table.num_columns,
            "synthetic": synthetic_table.num_columns,
        },
        common_numeric_columns=common,
        numeric_comparison=numeric_comparison,
        trust_labels=trust_labels,
    )


def _get_numeric_column_names(table: pa.Table) -> set[str]:
    """Get the set of numeric column names from a PyArrow table."""
    numeric_names: set[str] = set()
    for i, field in enumerate(table.schema):
        if pa.types.is_integer(field.type) or pa.types.is_floating(field.type):
            numeric_names.add(field.name)
    return numeric_names
