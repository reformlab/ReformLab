# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""DiscreteChoiceStep for population expansion and cost matrix computation.

Implements the OrchestratorStep protocol to evaluate household alternatives
via ComputationAdapter using the expand → compute → reshape pattern.

Story 14-1: DiscreteChoiceStep with population expansion pattern.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.expansion import expand_population
from reformlab.discrete_choice.reshape import reshape_to_cost_matrix
from reformlab.discrete_choice.types import ChoiceSet

if TYPE_CHECKING:
    from collections.abc import Mapping

    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.computation.types import PolicyConfig
    from reformlab.discrete_choice.domain import DecisionDomain
    from reformlab.discrete_choice.eligibility import EligibilityFilter
    from reformlab.discrete_choice.types import ExpansionResult
    from reformlab.orchestrator.types import YearState

logger = logging.getLogger(__name__)


# ============================================================================
# Stable state keys for YearState.data
# ============================================================================

DISCRETE_CHOICE_COST_MATRIX_KEY = "discrete_choice_cost_matrix"
DISCRETE_CHOICE_EXPANSION_KEY = "discrete_choice_expansion"
DISCRETE_CHOICE_METADATA_KEY = "discrete_choice_metadata"


def _inject_fuel_price_from_exogenous_context(
    expansion: ExpansionResult,
    domain: DecisionDomain,
    state_data: Mapping[str, Any],
    year: int,
    step_name: str,
) -> tuple[ExpansionResult, dict[str, Any] | None]:
    """Inject configured exogenous fuel price into expanded population tables."""
    config = getattr(domain, "config", None)
    fuel_price_series = getattr(config, "fuel_price_series", None)
    if not fuel_price_series or "exogenous_context" not in state_data:
        return expansion, None

    try:
        exogenous_context = state_data["exogenous_context"]
        fuel_price = float(exogenous_context.get_value(fuel_price_series, year))

        from reformlab.computation.types import PopulationData

        injected_tables: dict[str, pa.Table] = {}
        for table_name, table in expansion.population.tables.items():
            new_col = pa.array([fuel_price] * table.num_rows, type=pa.float64())
            if "fuel_price" in table.column_names:
                col_index = table.column_names.index("fuel_price")
                injected_tables[table_name] = table.set_column(
                    col_index, "fuel_price", new_col
                )
            else:
                injected_tables[table_name] = table.append_column(
                    "fuel_price", new_col
                )

        modified_population = PopulationData(
            tables=injected_tables,
            metadata=dict(expansion.population.metadata),
        )
    except Exception as exc:
        raise DiscreteChoiceError(
            f"Fuel price injection failed at year {year} "
            f"for domain '{domain.name}' using series {fuel_price_series!r}: {exc}",
            year=year,
            step_name=step_name,
            domain_name=domain.name,
            original_error=exc,
        ) from exc

    metadata = {
        "source": f"exogenous:{fuel_price_series}",
        "value": fuel_price,
        "unit": "EUR/litre",
    }

    logger.debug(
        "year=%d step_name=%s fuel_price=%s source=%s event=fuel_price_injected",
        year,
        step_name,
        fuel_price,
        fuel_price_series,
    )

    return replace(expansion, population=modified_population), metadata


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
        "_population_key",
        "_eligibility_filter",
    )

    def __init__(
        self,
        adapter: ComputationAdapter,
        domain: DecisionDomain,
        policy: PolicyConfig,
        name: str = "discrete_choice",
        depends_on: tuple[str, ...] = (),
        description: str | None = None,
        population_key: str = "population_data",
        eligibility_filter: EligibilityFilter | None = None,
    ) -> None:
        """Initialize the discrete choice step.

        Args:
            adapter: ComputationAdapter for tax-benefit computation.
            domain: DecisionDomain defining alternatives and cost extraction.
            policy: PolicyConfig with scenario parameters.
            name: Step name for registry (default: "discrete_choice").
            depends_on: Names of steps this step depends on.
            description: Optional description for the step.
            population_key: Key in YearState.data to retrieve PopulationData.
            eligibility_filter: Optional eligibility filter (Story 14-5).
                When provided, only eligible households are expanded.
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
        self._population_key = population_key
        self._eligibility_filter = eligibility_filter

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

        # Extract population from state using explicit key
        from reformlab.computation.types import PopulationData

        population = state.data.get(self._population_key)
        if not isinstance(population, PopulationData):
            raise DiscreteChoiceError(
                f"PopulationData not found in YearState.data['{self._population_key}']. "
                f"Available keys: {list(state.data.keys())}",
                step_name=self._name,
            )

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

        # Eligibility filtering (Story 14-5)
        eligibility_info = None
        if self._eligibility_filter is not None:
            from reformlab.discrete_choice.eligibility import (
                DISCRETE_CHOICE_ELIGIBILITY_KEY,
                EligibilityInfo,
                evaluate_eligibility,
                filter_population_by_eligibility,
            )

            entity_key = self._eligibility_filter.entity_key
            if entity_key not in population.tables:
                raise DiscreteChoiceError(
                    f"Eligibility entity_key '{entity_key}' not found. "
                    f"Available: {sorted(population.tables.keys())}",
                    year=year,
                    step_name=self._name,
                )
            eligible_mask = evaluate_eligibility(
                population.tables[entity_key], self._eligibility_filter
            )
            filtered_pop, eligible_indices = filter_population_by_eligibility(
                population, eligible_mask, entity_key
            )
            n_total = population.tables[entity_key].num_rows
            n_eligible = len(eligible_indices)

            logger.info(
                "year=%d step_name=%s n_total=%d n_eligible=%d "
                "event=eligibility_evaluated",
                year,
                self._name,
                n_total,
                n_eligible,
            )

            eligibility_info = EligibilityInfo(
                n_total=n_total,
                n_eligible=n_eligible,
                eligible_indices=eligible_indices,
                default_choice=self._eligibility_filter.default_choice,
                filter_description=self._eligibility_filter.description,
                alternative_ids=choice_set.alternative_ids,
                filter_rules=self._eligibility_filter.rules,
            )

            population = filtered_pop
            n = n_eligible

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
                original_error=exc,
            ) from exc

        expanded_n = expansion.population.row_count
        logger.debug(
            "year=%d step_name=%s expanded_rows=%d event=expansion_complete",
            year,
            self._name,
            expanded_n,
        )

        # Story 21.6 / AC5: Inject exogenous fuel prices before adapter computation
        expansion, fuel_price_metadata = _inject_fuel_price_from_exogenous_context(
            expansion,
            domain,
            state.data,
            year,
            self._name,
        )

        # Phase 2: Compute via adapter (single batch call)
        # Skip adapter call for empty population (AC-3)
        if n == 0:
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
                    original_error=exc,
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
                    original_error=exc,
                ) from exc

        # Phase 4: Store in YearState
        # Extend metadata — preserve existing keys from prior domain steps (AC-9)
        existing_metadata = state.data.get(DISCRETE_CHOICE_METADATA_KEY, {})
        if not isinstance(existing_metadata, dict):
            raise DiscreteChoiceError(
                f"Expected dict for metadata key '{DISCRETE_CHOICE_METADATA_KEY}', "
                f"got {type(existing_metadata).__name__}",
                year=year,
                step_name=self._name,
            )
        extended_metadata = dict(existing_metadata)
        extended_metadata["domain_name"] = domain.name
        extended_metadata["n_households"] = n
        extended_metadata["n_alternatives"] = m
        extended_metadata["alternative_names"] = list(choice_set.alternative_ids)
        extended_metadata["adapter_version"] = adapter_version if n > 0 else None

        new_data = dict(state.data)
        new_data[DISCRETE_CHOICE_COST_MATRIX_KEY] = cost_matrix
        new_data[DISCRETE_CHOICE_EXPANSION_KEY] = expansion

        # Store eligibility info if filtering was applied (Story 14-5)
        if eligibility_info is not None:
            from reformlab.discrete_choice.eligibility import (
                DISCRETE_CHOICE_ELIGIBILITY_KEY,
            )

            new_data[DISCRETE_CHOICE_ELIGIBILITY_KEY] = eligibility_info
            extended_metadata["eligibility_n_total"] = eligibility_info.n_total
            extended_metadata["eligibility_n_eligible"] = eligibility_info.n_eligible
            extended_metadata["eligibility_n_ineligible"] = (
                eligibility_info.n_total - eligibility_info.n_eligible
            )
            extended_metadata["eligibility_filter_description"] = (
                eligibility_info.filter_description
            )

        # Story 21.6 / AC5: Record fuel price metadata
        if fuel_price_metadata is not None:
            extended_metadata["vehicle_fuel_cost"] = fuel_price_metadata

        new_data[DISCRETE_CHOICE_METADATA_KEY] = extended_metadata

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
