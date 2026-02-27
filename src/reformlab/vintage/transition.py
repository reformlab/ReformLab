"""Vintage transition step for deterministic cohort aging and turnover.

This module provides:
- VintageTransitionStep: OrchestratorStep implementation for vintage transitions

The step handles:
- Aging existing cohorts (age += 1)
- Retiring cohorts above configured max age
- Adding new entry cohorts (age = 0)

MVP scope: vehicle asset class.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from reformlab.vintage.config import VintageConfig
from reformlab.vintage.errors import VintageTransitionError
from reformlab.vintage.types import VintageCohort, VintageState

if TYPE_CHECKING:
    from reformlab.orchestrator.types import YearState


def _state_key(asset_class: str) -> str:
    """Generate the YearState.data key for a vintage state.

    Args:
        asset_class: Asset class identifier.

    Returns:
        Key string for YearState.data (e.g., "vintage_vehicle").
    """
    return f"vintage_{asset_class}"


class VintageTransitionStep:
    """Orchestrator step for vintage cohort transitions.

    Implements the OrchestratorStep protocol to age, retire, and add
    cohorts according to configured rules.

    The step guarantees:
    - Deterministic execution (same inputs produce identical outputs)
    - Cohorts processed in sorted age order
    - Immutable state updates (returns new YearState)
    - State stored under stable key pattern: "vintage_{asset_class}"
    """

    __slots__ = ("_config", "_name", "_depends_on", "_description")

    def __init__(
        self,
        config: VintageConfig,
        name: str = "vintage_transition",
        depends_on: tuple[str, ...] = (),
        description: str | None = None,
    ) -> None:
        """Initialize the vintage transition step.

        Args:
            config: VintageConfig with rules for transition behavior.
            name: Step name for registry (default: "vintage_transition").
            depends_on: Names of steps this step depends on.
            description: Optional description for the step.
        """
        self._config = config
        self._name = name
        self._depends_on = depends_on
        self._description = (
            description
            or f"Vintage transition step for {config.asset_class} cohort aging"
        )

    @property
    def name(self) -> str:
        """Unique identifier for this step."""
        return self._name

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Names of steps this step depends on."""
        return self._depends_on

    @property
    def description(self) -> str:
        """Human-readable description of the step."""
        return self._description

    @property
    def config(self) -> VintageConfig:
        """The configuration for this step."""
        return self._config

    def execute(self, year: int, state: "YearState") -> "YearState":
        """Execute vintage transition for a given year.

        Performs the transition in deterministic order:
        1. Load or initialize vintage state
        2. Age all existing cohorts
        3. Remove cohorts above max age (retirement)
        4. Add new entry cohorts (age = 0)
        5. Store updated state

        Args:
            year: Current simulation year.
            state: Current year state.

        Returns:
            New YearState with updated vintage data.

        Raises:
            VintageTransitionError: If transition fails.
        """
        key = _state_key(self._config.asset_class)

        # Load existing vintage state or use initial/empty state
        vintage_state = self._load_or_init_state(state, key)

        # Apply transition sequence
        vintage_state = self._age_cohorts(vintage_state)
        vintage_state = self._apply_retirement(vintage_state)
        vintage_state = self._apply_entry(vintage_state, year, state)

        # Store updated state
        new_data = dict(state.data)
        new_data[key] = vintage_state

        return replace(state, data=new_data)

    def _load_or_init_state(
        self, state: "YearState", key: str
    ) -> VintageState:
        """Load existing vintage state or initialize from config.

        Args:
            state: Current year state.
            key: State data key for vintage state.

        Returns:
            VintageState to use for transition.

        Raises:
            VintageTransitionError: If state data is invalid.
        """
        existing = state.data.get(key)

        if existing is not None:
            if not isinstance(existing, VintageState):
                raise VintageTransitionError(
                    f"Invalid vintage state at '{key}': expected VintageState, "
                    f"got {type(existing).__name__}"
                )
            if existing.asset_class != self._config.asset_class:
                raise VintageTransitionError(
                    f"Asset class mismatch: state has '{existing.asset_class}', "
                    f"config expects '{self._config.asset_class}'"
                )
            return existing

        # Use initial state from config if provided
        if self._config.initial_state is not None:
            return self._config.initial_state

        # Return empty state
        return VintageState(asset_class=self._config.asset_class)

    def _age_cohorts(self, vintage_state: VintageState) -> VintageState:
        """Age all cohorts by one year.

        Args:
            vintage_state: Current vintage state.

        Returns:
            New VintageState with aged cohorts.
        """
        if not vintage_state.cohorts:
            return vintage_state

        # Age each cohort, maintaining sorted order
        aged_cohorts = tuple(
            VintageCohort(
                age=cohort.age + 1,
                count=cohort.count,
                attributes=dict(cohort.attributes),
            )
            for cohort in sorted(vintage_state.cohorts, key=lambda c: c.age)
        )

        return VintageState(
            asset_class=vintage_state.asset_class,
            cohorts=aged_cohorts,
            metadata=dict(vintage_state.metadata),
        )

    def _apply_retirement(self, vintage_state: VintageState) -> VintageState:
        """Remove cohorts above configured max age.

        Args:
            vintage_state: Current vintage state (after aging).

        Returns:
            New VintageState with retired cohorts removed.
        """
        max_age = self._config.max_age

        surviving_cohorts = tuple(
            cohort
            for cohort in vintage_state.cohorts
            if cohort.age <= max_age
        )

        return VintageState(
            asset_class=vintage_state.asset_class,
            cohorts=surviving_cohorts,
            metadata=dict(vintage_state.metadata),
        )

    def _apply_entry(
        self, vintage_state: VintageState, year: int, state: "YearState"
    ) -> VintageState:
        """Add new entry cohorts based on configured rules.

        Args:
            vintage_state: Current vintage state (after retirement).
            year: Current simulation year.
            state: Full year state (for proportional calculations).

        Returns:
            New VintageState with entry cohorts added.
        """
        entry_count = 0

        # Calculate total entry from all entry rules
        for rule in self._config.entry_rules:
            if rule.rule_type == "fixed_entry":
                entry_count += int(rule.parameters["count"])
            elif rule.rule_type == "proportional_entry":
                rate = float(rule.parameters["rate"])
                current_total = vintage_state.total_count
                entry_count += int(current_total * rate)

        if entry_count <= 0:
            return vintage_state

        # Check if age=0 cohort already exists (shouldn't after aging, but be safe)
        existing_cohorts = list(vintage_state.cohorts)
        age_zero_cohort = None
        other_cohorts = []

        for cohort in existing_cohorts:
            if cohort.age == 0:
                age_zero_cohort = cohort
            else:
                other_cohorts.append(cohort)

        if age_zero_cohort is not None:
            # Merge with existing age=0 cohort
            new_age_zero = VintageCohort(
                age=0,
                count=age_zero_cohort.count + entry_count,
                attributes=dict(age_zero_cohort.attributes),
            )
        else:
            # Create new age=0 cohort
            new_age_zero = VintageCohort(age=0, count=entry_count)

        # Rebuild cohorts in sorted age order
        all_cohorts = [new_age_zero] + other_cohorts
        sorted_cohorts = tuple(sorted(all_cohorts, key=lambda c: c.age))

        return VintageState(
            asset_class=vintage_state.asset_class,
            cohorts=sorted_cohorts,
            metadata=dict(vintage_state.metadata),
        )
