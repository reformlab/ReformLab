"""Eligibility filtering for discrete choice performance optimization.

Provides rule-based eligibility evaluation to restrict population expansion
to only eligible households per decision domain, reducing N×M expansion
cost for multi-year simulations with 100k+ households.

Types:
- EligibilityRule: Single column-operator-threshold condition
- EligibilityFilter: Composed rule set with AND/OR logic
- EligibilityInfo: State payload with eligibility metadata for merge step
- EligibilityMergeStep: Orchestrator step to merge filtered choices back to full N

Functions:
- evaluate_eligibility: Evaluate rules against entity table → boolean mask
- filter_population_by_eligibility: Filter population to eligible rows only

Story 14-5: Implement Eligibility Filtering for Performance Optimization (FR48).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.compute as pc

from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.logit import DISCRETE_CHOICE_RESULT_KEY
from reformlab.discrete_choice.step import DISCRETE_CHOICE_METADATA_KEY

if TYPE_CHECKING:
    from reformlab.computation.types import PopulationData
    from reformlab.orchestrator.types import YearState

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

VALID_OPERATORS: frozenset[str] = frozenset({"gt", "ge", "lt", "le", "eq", "ne"})
VALID_LOGIC: frozenset[str] = frozenset({"all", "any"})

DISCRETE_CHOICE_ELIGIBILITY_KEY = "discrete_choice_eligibility"

_OPERATOR_MAP = {
    "gt": pc.greater,
    "ge": pc.greater_equal,
    "lt": pc.less,
    "le": pc.less_equal,
    "eq": pc.equal,
    "ne": pc.not_equal,
}


# ============================================================================
# Eligibility types (AC-1, AC-9)
# ============================================================================


@dataclass(frozen=True)
class EligibilityRule:
    """Single eligibility condition: column operator threshold.

    Validated at construction — invalid operator raises DiscreteChoiceError.

    Attributes:
        column: Column name in entity table to evaluate.
        operator: Comparison operator (gt, ge, lt, le, eq, ne).
        threshold: Value to compare against.
        description: Human-readable description of the rule.
    """

    column: str
    operator: str
    threshold: int | float | str
    description: str = ""

    def __post_init__(self) -> None:
        if self.operator not in VALID_OPERATORS:
            raise DiscreteChoiceError(
                f"Invalid eligibility operator '{self.operator}'. "
                f"Valid operators: {sorted(VALID_OPERATORS)}"
            )


@dataclass(frozen=True)
class EligibilityFilter:
    """Composed eligibility filter with AND/OR logic.

    Validates logic value at construction.

    Attributes:
        rules: Tuple of eligibility rules to evaluate.
        logic: Combination logic — "all" for AND, "any" for OR.
        default_choice: Alternative ID assigned to ineligible households.
        entity_key: Entity key in PopulationData.tables to evaluate.
        description: Human-readable filter description.
    """

    rules: tuple[EligibilityRule, ...]
    logic: str = "all"
    default_choice: str = "keep_current"
    entity_key: str = "menage"
    description: str = ""

    def __post_init__(self) -> None:
        if self.logic not in VALID_LOGIC:
            raise DiscreteChoiceError(
                f"Invalid eligibility logic '{self.logic}'. "
                f"Valid values: {sorted(VALID_LOGIC)}"
            )


@dataclass(frozen=True)
class EligibilityInfo:
    """State payload carrying eligibility metadata for the merge step.

    Stored in YearState.data[DISCRETE_CHOICE_ELIGIBILITY_KEY] by
    DiscreteChoiceStep when eligibility filtering is applied.

    Attributes:
        n_total: Original population size (N).
        n_eligible: Number of eligible households (N').
        eligible_indices: Original row indices of eligible households.
        default_choice: Alternative ID for ineligible households.
        filter_description: Human-readable filter description.
        alternative_ids: Tuple of all alternative IDs in the choice set.
        filter_rules: Originating eligibility rules for manifest auditability.
    """

    n_total: int
    n_eligible: int
    eligible_indices: tuple[int, ...]
    default_choice: str
    filter_description: str
    alternative_ids: tuple[str, ...]
    filter_rules: tuple[EligibilityRule, ...]


# ============================================================================
# evaluate_eligibility (AC-2)
# ============================================================================


def evaluate_eligibility(
    table: pa.Table,
    eligibility_filter: EligibilityFilter,
) -> pa.ChunkedArray:
    """Evaluate eligibility rules against an entity table.

    Returns a boolean mask where True = eligible. Uses PyArrow compute
    functions for efficient evaluation at 100k+ scale.

    Args:
        table: Entity table to evaluate rules against.
        eligibility_filter: Filter with rules and combination logic.

    Returns:
        Boolean ChunkedArray (True = eligible).

    Raises:
        DiscreteChoiceError: If a rule column is not in the table.
    """
    n = table.num_rows

    if not eligibility_filter.rules:
        return pa.chunked_array([pa.array([True] * n)])

    masks: list[pa.ChunkedArray] = []
    for rule in eligibility_filter.rules:
        if rule.column not in table.column_names:
            raise DiscreteChoiceError(
                f"Eligibility column '{rule.column}' not found. "
                f"Available: {sorted(table.column_names)}"
            )
        col = table.column(rule.column)
        op_fn = _OPERATOR_MAP[rule.operator]
        mask = op_fn(col, rule.threshold)
        masks.append(mask)

    result = masks[0]
    if eligibility_filter.logic == "all":
        for m in masks[1:]:
            result = pc.and_(result, m)
    else:  # "any"
        for m in masks[1:]:
            result = pc.or_(result, m)

    return result


# ============================================================================
# filter_population_by_eligibility (AC-3)
# ============================================================================


def filter_population_by_eligibility(
    population: PopulationData,
    eligible_mask: pa.ChunkedArray,
    entity_key: str,
) -> tuple[PopulationData, tuple[int, ...]]:
    """Filter population to eligible households only.

    Returns a new PopulationData containing only the entity_key table
    filtered by the eligible mask, plus the original row indices of
    eligible households. Other entity tables are excluded.

    Args:
        population: Full population data.
        eligible_mask: Boolean mask (True = eligible).
        entity_key: Entity key to filter.

    Returns:
        Tuple of (filtered PopulationData, eligible_indices).

    Raises:
        DiscreteChoiceError: If entity_key not in population.tables.
    """
    from reformlab.computation.types import PopulationData as _PopulationData

    if entity_key not in population.tables:
        raise DiscreteChoiceError(
            f"Entity key '{entity_key}' not found in population tables. "
            f"Available keys: {sorted(population.tables.keys())}"
        )

    table = population.tables[entity_key]
    filtered_table = table.filter(eligible_mask)

    # Build eligible_indices from mask
    mask_list = eligible_mask.to_pylist()
    eligible_indices = tuple(i for i, v in enumerate(mask_list) if v)

    filtered_population = _PopulationData(
        tables={entity_key: filtered_table},
        metadata=dict(population.metadata),
    )

    return filtered_population, eligible_indices


# ============================================================================
# EligibilityMergeStep (AC-5)
# ============================================================================


class EligibilityMergeStep:
    """Orchestrator step that merges filtered choice results back to full population.

    Reads the N' ChoiceResult (from logit) and EligibilityInfo (from
    DiscreteChoiceStep), produces a full N-entry ChoiceResult where
    eligible households get logit choices and ineligible households get
    default_choice with probability 1.0.

    Pass-through when no eligibility filtering was applied (safe to
    always include in pipeline).

    Implements the OrchestratorStep protocol.

    Story 14-5, AC-5.
    """

    __slots__ = ("_name", "_depends_on", "_description")

    def __init__(
        self,
        name: str = "eligibility_merge",
        depends_on: tuple[str, ...] = ("logit_choice",),
        description: str | None = None,
    ) -> None:
        self._name = name
        self._depends_on = depends_on
        self._description = (
            description
            or "Eligibility merge: expand filtered choices to full population"
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

    def execute(self, year: int, state: YearState) -> YearState:
        """Merge filtered choices back to full population size.

        If no EligibilityInfo in state, returns state unchanged (pass-through).

        Args:
            year: Current simulation year.
            state: Current year state.

        Returns:
            New YearState with merged full-population ChoiceResult.

        Raises:
            DiscreteChoiceError: If required data missing or invalid.
        """
        from reformlab.discrete_choice.types import ChoiceResult as _ChoiceResult

        eligibility_info = state.data.get(DISCRETE_CHOICE_ELIGIBILITY_KEY)
        if eligibility_info is None:
            return state

        if not isinstance(eligibility_info, EligibilityInfo):
            raise DiscreteChoiceError(
                f"Expected EligibilityInfo for key '{DISCRETE_CHOICE_ELIGIBILITY_KEY}', "
                f"got {type(eligibility_info).__name__}",
                year=year,
                step_name=self._name,
            )

        # Read ChoiceResult from state
        choice_result = state.data.get(DISCRETE_CHOICE_RESULT_KEY)
        if not isinstance(choice_result, _ChoiceResult):
            raise DiscreteChoiceError(
                f"ChoiceResult not found in YearState.data['{DISCRETE_CHOICE_RESULT_KEY}']. "
                f"Available keys: {list(state.data.keys())}",
                year=year,
                step_name=self._name,
            )

        n_total = eligibility_info.n_total
        n_eligible = eligibility_info.n_eligible
        eligible_indices = eligibility_info.eligible_indices
        default_choice = eligibility_info.default_choice
        alt_ids = eligibility_info.alternative_ids

        # Validate default_choice is a valid alternative ID
        if default_choice not in alt_ids:
            raise DiscreteChoiceError(
                f"default_choice '{default_choice}' is not a valid alternative. "
                f"Valid alternatives: {sorted(alt_ids)}",
                year=year,
                step_name=self._name,
            )

        logger.info(
            "year=%d step_name=%s n_total=%d n_eligible=%d "
            "default_choice=%s event=merge_start",
            year,
            self._name,
            n_total,
            n_eligible,
            default_choice,
        )

        # Build eligible index set for O(1) lookup
        eligible_set = set(eligible_indices)
        eligible_pos_map = {idx: j for j, idx in enumerate(eligible_indices)}

        # Extract N' arrays from choice_result
        cr_chosen = choice_result.chosen.to_pylist()
        cr_probs = {
            aid: choice_result.probabilities.column(aid).to_pylist()
            for aid in alt_ids
        }
        cr_utils = {
            aid: choice_result.utilities.column(aid).to_pylist()
            for aid in alt_ids
        }

        # Build full N arrays
        full_chosen: list[str] = []
        full_probs: dict[str, list[float]] = {aid: [] for aid in alt_ids}
        full_utils: dict[str, list[float]] = {aid: [] for aid in alt_ids}

        for i in range(n_total):
            if i in eligible_set:
                j = eligible_pos_map[i]
                full_chosen.append(cr_chosen[j])
                for aid in alt_ids:
                    full_probs[aid].append(cr_probs[aid][j])
                    full_utils[aid].append(cr_utils[aid][j])
            else:
                full_chosen.append(default_choice)
                for aid in alt_ids:
                    full_probs[aid].append(1.0 if aid == default_choice else 0.0)
                    full_utils[aid].append(0.0)

        merged = _ChoiceResult(
            chosen=pa.array(full_chosen),
            probabilities=pa.table(
                {aid: pa.array(full_probs[aid]) for aid in alt_ids}
            ),
            utilities=pa.table(
                {aid: pa.array(full_utils[aid]) for aid in alt_ids}
            ),
            alternative_ids=alt_ids,
            seed=choice_result.seed,
        )

        # Store merged result, remove consumed EligibilityInfo
        new_data = dict(state.data)
        new_data[DISCRETE_CHOICE_RESULT_KEY] = merged
        del new_data[DISCRETE_CHOICE_ELIGIBILITY_KEY]

        # Extend metadata
        existing_metadata = state.data.get(DISCRETE_CHOICE_METADATA_KEY, {})
        if not isinstance(existing_metadata, dict):
            raise DiscreteChoiceError(
                f"Expected dict for metadata key '{DISCRETE_CHOICE_METADATA_KEY}', "
                f"got {type(existing_metadata).__name__}",
                year=year,
                step_name=self._name,
            )
        extended_metadata = dict(existing_metadata)
        n_defaulted = n_total - n_eligible
        extended_metadata["eligibility_merge_n_defaulted"] = n_defaulted
        new_data[DISCRETE_CHOICE_METADATA_KEY] = extended_metadata

        logger.info(
            "year=%d step_name=%s n_total=%d n_eligible=%d "
            "n_defaulted=%d default_choice=%s event=eligibility_merge_complete",
            year,
            self._name,
            n_total,
            n_eligible,
            n_defaulted,
            default_choice,
        )

        return replace(state, data=new_data)
