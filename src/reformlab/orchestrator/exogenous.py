# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""ExogenousContext for scenario-specific exogenous time series.

ExogenousContext wraps multiple ExogenousAsset instances and provides
unified lookup, coverage validation, and provenance access.

Story 21.6 / AC1: ExogenousContext frozen dataclass with series mapping,
value lookup with interpolation, coverage validation, and asset access.

See also:
    - synthetic-data-decision-document-2026-03-23.md Section 2.3: Exogenous Data
    - Story 21.3: ExogenousAsset schema with get_value(), validate_coverage()
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from reformlab.data.assets import ExogenousAsset
from reformlab.data.errors import EvidenceAssetError
from reformlab.orchestrator.errors import OrchestratorError

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)

__all__ = ["ExogenousContext"]


@dataclass(frozen=True)
class ExogenousContext:
    """Read-only exogenous time series context for scenario execution.

    Wraps multiple ExogenousAsset instances and provides unified lookup
    and coverage validation. Each scenario carries its own ExogenousContext,
    enabling comparison across divergent exogenous assumptions.

    The internal ``_series`` mapping is private (accessed via methods only)
    to enforce read-only semantics — ExogenousContext never mutates
    underlying assets.

    Attributes
    ----------
    _series : dict[str, ExogenousAsset]
        Internal mapping of series name → ExogenousAsset (private).

    Story 21.6 / AC1.
    """

    _series: Mapping[str, ExogenousAsset]

    def __post_init__(self) -> None:
        """Validate internal state on construction."""
        # Ensure _series is a dict-like mapping
        if not hasattr(self._series, "__getitem__") or not hasattr(
            self._series, "__contains__"
        ):
            raise TypeError("ExogenousContext _series must be a mapping")

    def get_value(self, series_name: str, year: int) -> float:
        """Look up value for series and year with interpolation.

        Delegates to the asset's ``get_value()`` method, which handles
        interpolation according to the asset's ``interpolation_method``
        (linear, step, or none).

        Parameters
        ----------
        series_name : str
            Series identifier (e.g., ``"energy_price_electricity"``).
        year : int
            Year to look up.

        Returns
        -------
        float
            Value for the requested year.

        Raises
        ------
        KeyError
            If ``series_name`` not found.
        EvidenceAssetError
            If year is missing and interpolation disabled, or if year
            is outside the asset's range.

        Story 21.6 / AC1.
        """
        if series_name not in self._series:
            available = sorted(self._series.keys()) if self._series else []
            raise KeyError(
                f"Series '{series_name}' not found in ExogenousContext. "
                f"Available series: {available}"
            )

        asset = self._series[series_name]
        return asset.get_value(year)

    def validate_coverage(self, start_year: int, end_year: int) -> None:
        """Validate ALL series have complete coverage for year range.

        For each series, checks that the range [start_year, end_year]
        is fully covered by the asset's data, accounting for interpolation
        method. Series with ``interpolation_method="none"`` must have
        explicit values for every year; linear/step methods can interpolate.

        Parameters
        ----------
        start_year : int
            First year (inclusive).
        end_year : int
            Last year (inclusive).

        Raises
        ------
        ValueError
            If ``start_year > end_year``.
        OrchestratorError
            If any series has missing coverage for the requested range.

        Story 21.6 / AC1.
        """
        if start_year > end_year:
            raise ValueError(
                f"start_year ({start_year}) must be <= end_year ({end_year})"
            )

        # Check coverage for each series
        missing_coverage = {}
        for series_name, asset in self._series.items():
            try:
                asset.validate_coverage(start_year, end_year)
            except EvidenceAssetError as exc:
                missing_coverage[series_name] = str(exc)

        if missing_coverage:
            series_list = ", ".join(sorted(missing_coverage.keys()))
            issues = "; ".join(
                f"{name}: {msg}" for name, msg in sorted(missing_coverage.items())
            )
            raise OrchestratorError(
                summary=f"Missing exogenous coverage for {len(missing_coverage)} series",
                reason=f"Series without coverage: {series_list}. Details: {issues}",
                year=start_year,
                step_name="exogenous_coverage",
            )

    def get_asset(self, series_name: str) -> ExogenousAsset:
        """Retrieve full asset for provenance metadata.

        Parameters
        ----------
        series_name : str
            Series identifier.

        Returns
        -------
        ExogenousAsset
            The full asset with descriptor, values, and metadata.

        Raises
        ------
        KeyError
            If ``series_name`` not found.

        Story 21.6 / AC1.
        """
        if series_name not in self._series:
            available = sorted(self._series.keys()) if self._series else []
            raise KeyError(
                f"Series '{series_name}' not found in ExogenousContext. "
                f"Available series: {available}"
            )

        return self._series[series_name]

    @property
    def series_names(self) -> tuple[str, ...]:
        """Sorted tuple of available series names.

        Returns
        -------
        tuple[str, ...]
            Alphabetically sorted series identifiers.

        Story 21.6 / AC1.
        """
        return tuple(sorted(self._series.keys()))

    @classmethod
    def from_assets(cls, assets: tuple[ExogenousAsset, ...]) -> ExogenousContext:
        """Create context from tuple of ExogenousAsset instances.

        Validates that series names are unique (duplicates raise error).

        Parameters
        ----------
        assets : tuple[ExogenousAsset, ...]
            Tuple of exogenous assets.

        Returns
        -------
        ExogenousContext
            Context with name → asset mapping.

        Raises
        ------
        ValueError
            If duplicate series names detected.

        Story 21.6 / AC1.
        """
        # Build mapping and check for duplicates
        series_map: dict[str, ExogenousAsset] = {}
        seen_names: set[str] = set()
        duplicates: set[str] = set()

        for asset in assets:
            name = asset.name
            if name in seen_names:
                duplicates.add(name)
            seen_names.add(name)
            series_map[name] = asset

        if duplicates:
            dup_list = ", ".join(sorted(duplicates))
            raise ValueError(
                f"Duplicate series names detected: {dup_list}. "
                f"Each series must have a unique name."
            )

        return cls(_series=series_map)

    def to_json(self) -> dict[str, Any]:
        """Serialize to JSON-compatible dict.

        Returns a dict with series names. Assets are stored separately
        by series name and loaded via ``load_exogenous_asset()``.

        Story 21.6 / AC4.

        Returns
        -------
        dict[str, Any]
            JSON-serializable representation with ``series_names`` key.
        """
        return {"series_names": list(self.series_names)}

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> ExogenousContext:
        """Deserialize from JSON-compatible dict.

        Loads each asset via ``load_exogenous_asset()`` using series
        names and builds context via ``from_assets()``.

        Note: ``load_exogenous_asset()`` is implemented in Task 7.
        For now, this method raises ``NotImplementedError`` with a
        clear message.

        Story 21.6 / AC4.

        Parameters
        ----------
        data : dict[str, Any]
            JSON dict with ``series_names`` key.

        Returns
        -------
        ExogenousContext
            Deserialized context with assets loaded from disk.

        Raises
        ------
        NotImplementedError
            Until ``load_exogenous_asset()`` is implemented (Task 7).
        """
        raise NotImplementedError(
            "ExogenousContext.from_json() requires load_exogenous_asset() "
            "which will be implemented in Task 7. "
            "For now, use ExogenousContext.from_assets() directly."
        )
