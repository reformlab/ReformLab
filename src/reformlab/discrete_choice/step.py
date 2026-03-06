"""DiscreteChoiceStep for population expansion and cost matrix computation.

Implements the OrchestratorStep protocol to evaluate household alternatives
via ComputationAdapter using the expand → compute → reshape pattern.

Story 14-1: DiscreteChoiceStep with population expansion pattern.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING

from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.expansion import expand_population
from reformlab.discrete_choice.reshape import reshape_to_cost_matrix
from reformlab.discrete_choice.types import ChoiceSet

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.computation.types import PolicyConfig, PopulationData
    from reformlab.discrete_choice.domain import DecisionDomain
    from reformlab.orchestrator.types import YearState

logger = logging.getLogger(__name__)


# ============================================================================
# Stable state keys for YearState.data
# ============================================================================

DISCRETE_CHOICE_COST_MATRIX_KEY = "discrete_choice_cost_matrix"
DISCRETE_CHOICE_EXPANSION_KEY = "discrete_choice_expansion"
DISCRETE_CHOICE_METADATA_KEY = "discrete_choice_metadata"


class DiscreteChoiceStep:
    """Orchestrator step for discrete choice population expansion and cost evaluation.

    Implements the OrchestratorStep protocol. Orchestrates the
    expand → compute → reshape pipeline:

    1. Expand population by alternatives (N → N×M)
    2. Compute via adapter in one vectorized batch call
    3. Reshape results into N×M cost matrix
    4. Store results in YearState.data under stable keys

    The step guarantees:
    - Deterministic execution (no randomness — logit draws are Story 14.2)
    - Single batch adapter call (not M separate calls)
    - Immutable state updates (returns new YearState)
    - Structured key=value logging
    """

    __slots__ = (
        "_adapter",
        "_domain",
        "_policy",
        "_name",
        "_depends_on",
        "_description",
    )

    def __init__(
        self,
        adapter: ComputationAdapter,
        domain: DecisionDomain,
        policy: PolicyConfig,
        name: str = "discrete_choice",
        depends_on: tuple[str, ...] = (),
        description: str | None = None,
    ) -> None:
        """Initialize the discrete choice step.

        Args:
            adapter: ComputationAdapter for tax-benefit computation.
            domain: DecisionDomain defining alternatives and cost extraction.
            policy: PolicyConfig with scenario parameters.
            name: Step name for registry (default: "discrete_choice").
            depends_on: Names of steps this step depends on.
            description: Optional description for the step.
        """
        self._adapter = adapter
        self._domain = domain
        self._policy = policy
        self._name = name
        self._depends_on = depends_on
        self._description = (
            description
            or "Discrete choice step: population expansion and cost evaluation"
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
        """Execute discrete choice evaluation for a given year.

        Orchestrates expand → compute → reshape → store pipeline.

        Args:
            year: Current simulation year.
            state: Current year state (must contain population data).

        Returns:
            New YearState with cost matrix, expansion result, and metadata.

        Raises:
            DiscreteChoiceError: If any phase fails.
        """
        domain = self._domain
        alternatives = domain.alternatives
        choice_set = ChoiceSet(alternatives=alternatives)

        # Extract population from state
        population = self._get_population(state)

        n = 0
        if population.tables:
            first_key = sorted(population.tables.keys())[0]
            n = population.tables[first_key].num_rows
        m = choice_set.size

        logger.info(
            "year=%d step_name=%s domain=%s n_households=%d n_alternatives=%d "
            "event=step_start",
            year,
            self._name,
            domain.name,
            n,
            m,
        )

        # Phase 1: Expand population
        try:
            expansion = expand_population(population, choice_set, domain)
        except Exception as exc:
            raise DiscreteChoiceError(
                f"Population expansion failed at year {year} "
                f"for domain '{domain.name}': {exc}",
                year=year,
                step_name=self._name,
                domain_name=domain.name,
                original_error=exc if isinstance(exc, Exception) else None,
            ) from exc

        expanded_n = expansion.population.row_count
        logger.debug(
            "year=%d step_name=%s expanded_rows=%d event=expansion_complete",
            year,
            self._name,
            expanded_n,
        )

        # Phase 2: Compute via adapter (single batch call)
        # Skip adapter call for empty population (AC-3)
        if n == 0:
            import pyarrow as pa

            from reformlab.discrete_choice.types import CostMatrix

            empty_columns = {
                alt_id: pa.array([], type=pa.float64())
                for alt_id in choice_set.alternative_ids
            }
            cost_matrix = CostMatrix(
                table=pa.table(empty_columns),
                alternative_ids=choice_set.alternative_ids,
            )
        else:
            adapter_version = "<version-unavailable>"
            try:
                adapter_version = self._adapter.version()
            except Exception:
                logger.debug(
                    "year=%d step_name=%s event=adapter_version_fallback",
                    year,
                    self._name,
                )

            try:
                result = self._adapter.compute(
                    population=expansion.population,
                    policy=self._policy,
                    period=year,
                )
            except Exception as exc:
                raise DiscreteChoiceError(
                    f"Adapter computation failed at year {year} "
                    f"for domain '{domain.name}': {exc}",
                    year=year,
                    step_name=self._name,
                    domain_name=domain.name,
                    original_error=exc if isinstance(exc, Exception) else None,
                ) from exc

            logger.debug(
                "year=%d step_name=%s adapter_version=%s "
                "result_rows=%d event=compute_complete",
                year,
                self._name,
                adapter_version,
                result.output_fields.num_rows,
            )

            # Phase 3: Reshape to cost matrix
            try:
                cost_matrix = reshape_to_cost_matrix(
                    result, expansion, domain.cost_column
                )
            except Exception as exc:
                raise DiscreteChoiceError(
                    f"Cost matrix reshape failed at year {year} "
                    f"for domain '{domain.name}': {exc}",
                    year=year,
                    step_name=self._name,
                    domain_name=domain.name,
                    original_error=exc if isinstance(exc, Exception) else None,
                ) from exc

        # Phase 4: Store in YearState
        metadata_dict = {
            "domain_name": domain.name,
            "n_households": n,
            "n_alternatives": m,
            "alternative_names": list(choice_set.alternative_ids),
            "adapter_version": adapter_version if n > 0 else None,
        }

        new_data = dict(state.data)
        new_data[DISCRETE_CHOICE_COST_MATRIX_KEY] = cost_matrix
        new_data[DISCRETE_CHOICE_EXPANSION_KEY] = expansion
        new_data[DISCRETE_CHOICE_METADATA_KEY] = metadata_dict

        logger.info(
            "year=%d step_name=%s domain=%s cost_matrix_shape=%dx%d "
            "event=step_complete",
            year,
            self._name,
            domain.name,
            cost_matrix.n_households,
            cost_matrix.n_alternatives,
        )

        return replace(state, data=new_data)

    def _get_population(self, state: YearState) -> PopulationData:
        """Extract population data from YearState.

        Looks for PopulationData in state.data under common keys.

        Args:
            state: Current year state.

        Returns:
            PopulationData from state.

        Raises:
            DiscreteChoiceError: If no population data found in state.
        """
        from reformlab.computation.types import PopulationData

        # Check for population data under known keys
        for key in ("population_data", "population"):
            value = state.data.get(key)
            if isinstance(value, PopulationData):
                return value

        # Check if any value is PopulationData
        for key, value in state.data.items():
            if isinstance(value, PopulationData):
                return value

        raise DiscreteChoiceError(
            f"No PopulationData found in YearState.data. "
            f"Available keys: {list(state.data.keys())}",
            step_name=self._name,
        )
