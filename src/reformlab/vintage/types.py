"""Vintage domain types for cohort-based asset tracking.

This module provides:
- VintageCohort: Single age cohort with count and attributes
- VintageState: Collection of cohorts for an asset class
- VintageSummary: Derived metrics for downstream consumers

MVP scope: vehicle asset class. Extension points exist for future classes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VintageCohort:
    """Single age cohort within a vintage state.

    Represents a group of assets of the same age within an asset class.
    Immutable by design for deterministic state transitions.

    Attributes:
        age: Age of cohort in years (0 = new this year).
        count: Number of assets in this cohort.
        attributes: Optional cohort-level attributes (e.g., fuel type, region).
    """

    age: int
    count: int
    attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate cohort invariants."""
        if not isinstance(self.age, int) or isinstance(self.age, bool):
            raise ValueError(f"Cohort age must be an integer, got {self.age!r}")
        if self.age < 0:
            raise ValueError(f"Cohort age must be non-negative, got {self.age}")
        if not isinstance(self.count, int) or isinstance(self.count, bool):
            raise ValueError(
                f"Cohort count must be an integer, got {self.count!r}"
            )
        if self.count < 0:
            raise ValueError(f"Cohort count must be non-negative, got {self.count}")


@dataclass(frozen=True)
class VintageState:
    """Collection of cohorts for a single asset class.

    Tracks the vintage composition of an asset class across age cohorts.
    Stored in YearState.data["vintage_{asset_class}"].

    Attributes:
        asset_class: Asset class identifier (e.g., "vehicle").
        cohorts: Tuple of VintageCohort instances, sorted by age.
        metadata: Optional metadata (e.g., source, last_updated).
    """

    asset_class: str
    cohorts: tuple[VintageCohort, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Normalize and validate vintage state."""
        # Ensure cohorts is a tuple
        object.__setattr__(self, "cohorts", tuple(self.cohorts))

        # Validate asset class
        if not self.asset_class or not self.asset_class.strip():
            raise ValueError("asset_class must be a non-empty string")

    @property
    def total_count(self) -> int:
        """Total number of assets across all cohorts."""
        return sum(c.count for c in self.cohorts)

    @property
    def age_distribution(self) -> dict[int, int]:
        """Mapping of age to count for all cohorts."""
        distribution: dict[int, int] = {}
        for cohort in self.cohorts:
            distribution[cohort.age] = distribution.get(cohort.age, 0) + cohort.count
        return distribution

    def cohort_by_age(self, age: int) -> VintageCohort | None:
        """Get cohort by age, or None if not found."""
        for cohort in self.cohorts:
            if cohort.age == age:
                return cohort
        return None


@dataclass(frozen=True)
class VintageSummary:
    """Derived metrics for downstream consumers.

    Provides summary statistics from a VintageState for use by
    indicators, panel outputs, and reporting.

    Attributes:
        asset_class: Asset class identifier.
        total_count: Total assets across all cohorts.
        cohort_count: Number of distinct age cohorts.
        age_distribution: Mapping of age to count.
        mean_age: Weighted mean age of fleet.
        max_age: Maximum age in fleet.
        metadata: Optional summary metadata.
    """

    asset_class: str
    total_count: int
    cohort_count: int
    age_distribution: dict[int, int]
    mean_age: float
    max_age: int
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_state(cls, state: VintageState) -> VintageSummary:
        """Create summary from a VintageState.

        Args:
            state: VintageState to summarize.

        Returns:
            VintageSummary with derived metrics.
        """
        total = state.total_count
        ages = state.age_distribution

        if total > 0:
            mean_age = sum(age * count for age, count in ages.items()) / total
            max_age = max(ages.keys()) if ages else 0
        else:
            mean_age = 0.0
            max_age = 0

        return cls(
            asset_class=state.asset_class,
            total_count=total,
            cohort_count=len(state.cohorts),
            age_distribution=dict(ages),
            mean_age=mean_age,
            max_age=max_age,
            metadata=dict(state.metadata),
        )
