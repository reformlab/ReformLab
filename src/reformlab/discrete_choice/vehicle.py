"""Vehicle investment decision domain for discrete choice modeling.

Defines vehicle alternatives, applies attribute overrides during population
expansion, and updates household state after choice draws. Integrates with
the vintage tracking subsystem for new vehicle purchase cohorts.

Story 14-3: Implement Vehicle Investment Decision Domain (FR47/FR50).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.logit import DISCRETE_CHOICE_RESULT_KEY
from reformlab.discrete_choice.step import DISCRETE_CHOICE_METADATA_KEY
from reformlab.discrete_choice.types import Alternative

if TYPE_CHECKING:
    from reformlab.computation.types import PopulationData
    from reformlab.discrete_choice.types import ChoiceResult
    from reformlab.orchestrator.types import YearState
    from reformlab.vintage.types import VintageCohort

logger = logging.getLogger(__name__)


# ============================================================================
# VehicleDomainConfig (AC-4)
# ============================================================================


@dataclass(frozen=True)
class VehicleDomainConfig:
    """Configuration for the vehicle investment decision domain.

    Attributes:
        alternatives: Ordered tuple of vehicle alternatives.
        cost_column: Column name for cost metric in computation results.
        entity_key: Entity key in PopulationData.tables (default: "menage").
        non_purchase_ids: Alternative IDs that do not create vintage entries.
    """

    alternatives: tuple[Alternative, ...]
    cost_column: str = "total_vehicle_cost"
    entity_key: str = "menage"
    non_purchase_ids: frozenset[str] = frozenset({"keep_current", "buy_no_vehicle"})


def default_vehicle_domain_config() -> VehicleDomainConfig:
    """Factory returning French market default vehicle domain config.

    Returns:
        VehicleDomainConfig with 6 alternatives per AC-2.
    """
    return VehicleDomainConfig(
        alternatives=(
            Alternative(
                id="keep_current",
                name="Keep Current Vehicle",
                attributes={},
            ),
            Alternative(
                id="buy_petrol",
                name="Buy Petrol Vehicle",
                attributes={
                    "vehicle_type": "petrol",
                    "vehicle_age": 0,
                    "vehicle_emissions_gkm": 120.0,
                },
            ),
            Alternative(
                id="buy_diesel",
                name="Buy Diesel Vehicle",
                attributes={
                    "vehicle_type": "diesel",
                    "vehicle_age": 0,
                    "vehicle_emissions_gkm": 110.0,
                },
            ),
            Alternative(
                id="buy_hybrid",
                name="Buy Hybrid Vehicle",
                attributes={
                    "vehicle_type": "hybrid",
                    "vehicle_age": 0,
                    "vehicle_emissions_gkm": 50.0,
                },
            ),
            Alternative(
                id="buy_ev",
                name="Buy Electric Vehicle",
                attributes={
                    "vehicle_type": "ev",
                    "vehicle_age": 0,
                    "vehicle_emissions_gkm": 0.0,
                },
            ),
            Alternative(
                id="buy_no_vehicle",
                name="Give Up Vehicle",
                attributes={
                    "vehicle_type": "none",
                    "vehicle_age": 0,
                    "vehicle_emissions_gkm": 0.0,
                },
            ),
        ),
    )


# ============================================================================
# Type inference helper
# ============================================================================


def _infer_pa_type(value: object) -> pa.DataType:
    """Infer PyArrow type from Python value.

    Args:
        value: Python value to infer type from.

    Returns:
        PyArrow DataType.

    Raises:
        DiscreteChoiceError: If type is unsupported.
    """
    if isinstance(value, str):
        return pa.utf8()
    if isinstance(value, bool):
        raise DiscreteChoiceError(
            f"Unsupported attribute type: {type(value).__name__} ({value!r})"
        )
    if isinstance(value, int):
        return pa.int64()
    if isinstance(value, float):
        return pa.float64()
    raise DiscreteChoiceError(
        f"Unsupported attribute type: {type(value).__name__} ({value!r})"
    )


# ============================================================================
# VehicleInvestmentDomain (AC-1, AC-2, AC-3)
# ============================================================================


class VehicleInvestmentDomain:
    """Vehicle investment decision domain.

    Satisfies the DecisionDomain protocol via structural typing.
    Stateless — all domain-specific logic is encoded in the config
    alternatives and apply_alternative method.

    Uses __slots__ for memory efficiency (AC-1).
    """

    __slots__ = ("_config",)

    def __init__(self, config: VehicleDomainConfig) -> None:
        self._config = config

    @property
    def name(self) -> str:
        """Domain identifier."""
        return "vehicle"

    @property
    def alternatives(self) -> tuple[Alternative, ...]:
        """Available vehicle alternatives."""
        return self._config.alternatives

    @property
    def cost_column(self) -> str:
        """Cost column name for computation results."""
        return self._config.cost_column

    def apply_alternative(
        self, table: pa.Table, alternative: Alternative
    ) -> pa.Table:
        """Return a new table with attributes modified for a given alternative.

        The input table is not modified (PyArrow tables are immutable).

        For existing columns, the existing column's PyArrow type is preserved
        via cast. For new columns, the type is inferred from the Python value.

        Args:
            table: Entity table from PopulationData.
            alternative: The alternative whose attribute overrides to apply.

        Returns:
            New table with alternative-specific attribute values.

        Raises:
            DiscreteChoiceError: If cast is incompatible or type unsupported.
        """
        if not alternative.attributes:
            return table

        n = table.num_rows
        for col_name, col_value in alternative.attributes.items():
            if col_name in table.column_names:
                existing_type = table.column(col_name).type
                try:
                    new_col = pa.array([col_value] * n, type=existing_type)
                except (pa.ArrowInvalid, pa.ArrowTypeError) as exc:
                    raise DiscreteChoiceError(
                        f"Cannot cast {col_value!r} to {existing_type}: {exc}"
                    ) from exc
                idx = table.column_names.index(col_name)
                table = table.set_column(idx, col_name, new_col)
            else:
                inferred_type = _infer_pa_type(col_value)
                new_col = pa.array([col_value] * n, type=inferred_type)
                table = table.append_column(col_name, new_col)

        return table


# ============================================================================
# apply_choices_to_population (AC-6, AC-7)
# ============================================================================


def apply_choices_to_population(
    population: PopulationData,
    choice_result: ChoiceResult,
    alternatives: tuple[Alternative, ...],
    entity_key: str,
) -> PopulationData:
    """Apply per-household choice results to population entity table.

    Each row gets the attributes of its chosen alternative.
    Columns present in the table are replaced (preserving existing type).
    Columns absent from the table are appended with inferred type.

    Args:
        population: Current population data.
        choice_result: Logit choice result with chosen alternatives.
        alternatives: Tuple of all alternatives in the domain.
        entity_key: Key in population.tables to update.

    Returns:
        New PopulationData with updated entity table.

    Raises:
        DiscreteChoiceError: On length mismatch or unknown alternative IDs.
    """
    from reformlab.computation.types import PopulationData as _PopulationData

    table = population.tables[entity_key]
    n = table.num_rows
    chosen_list: list[Any] = choice_result.chosen.to_pylist()

    # Validate dimensions (AC-6)
    if len(chosen_list) != n:
        raise DiscreteChoiceError(
            f"ChoiceResult chosen length ({len(chosen_list)}) does not match "
            f"entity table row count ({n})"
        )

    alt_map = {alt.id: alt for alt in alternatives}

    # Validate all chosen IDs are known (edge case)
    unknown_ids = set(chosen_list) - set(alt_map)
    if unknown_ids:
        raise DiscreteChoiceError(
            f"Unknown alternative IDs in chosen: {sorted(unknown_ids)}, "
            f"valid: {sorted(alt_map)}"
        )

    if n == 0:
        return population

    # Collect all attribute keys across all alternatives (sorted for determinism)
    all_attr_keys = sorted({k for alt in alternatives for k in alt.attributes})

    if not all_attr_keys:
        return population

    # Build per-column values based on each household's chosen alternative
    for attr_key in all_attr_keys:
        values: list[Any] = []
        for i in range(n):
            alt = alt_map[chosen_list[i]]
            if attr_key in alt.attributes:
                values.append(alt.attributes[attr_key])
            elif attr_key in table.column_names:
                values.append(table.column(attr_key)[i].as_py())
            else:
                values.append(None)

        # Determine type
        if attr_key in table.column_names:
            col_type = table.column(attr_key).type
        else:
            # Infer from first non-None value
            first_val = next((v for v in values if v is not None), None)
            if first_val is None:
                continue
            col_type = _infer_pa_type(first_val)

        try:
            new_col = pa.array(values, type=col_type)
        except (pa.ArrowInvalid, pa.ArrowTypeError) as exc:
            raise DiscreteChoiceError(
                f"Cannot cast values for '{attr_key}' to {col_type}: {exc}"
            ) from exc

        if attr_key in table.column_names:
            idx = table.column_names.index(attr_key)
            table = table.set_column(idx, attr_key, new_col)
        else:
            table = table.append_column(attr_key, new_col)

    new_tables = dict(population.tables)
    new_tables[entity_key] = table
    return _PopulationData(tables=new_tables, metadata=dict(population.metadata))


# ============================================================================
# VehicleStateUpdateStep (AC-5, AC-8, AC-9)
# ============================================================================


def _create_vintage_entries(
    choice_result: ChoiceResult,
    alternatives: tuple[Alternative, ...],
    non_purchase_ids: frozenset[str],
) -> tuple[VintageCohort, ...]:
    """Create vintage cohort entries for new vehicle purchases.

    Args:
        choice_result: Logit choice result.
        alternatives: Domain alternatives.
        non_purchase_ids: Alternative IDs excluded from vintage tracking.

    Returns:
        Tuple of VintageCohort entries sorted by vehicle_type.
    """
    from reformlab.vintage.types import VintageCohort as _VintageCohort

    alt_map = {alt.id: alt for alt in alternatives}
    chosen_list: list[str] = choice_result.chosen.to_pylist()

    switcher_counts: dict[str, int] = {}
    for chosen_id in chosen_list:
        if chosen_id not in non_purchase_ids:
            alt = alt_map[chosen_id]
            vtype = str(alt.attributes.get("vehicle_type", chosen_id))
            switcher_counts[vtype] = switcher_counts.get(vtype, 0) + 1

    return tuple(
        _VintageCohort(age=0, count=count, attributes={"vehicle_type": vtype})
        for vtype, count in sorted(switcher_counts.items())
    )


class VehicleStateUpdateStep:
    """Orchestrator step for vehicle state updates after logit choice draws.

    Reads ChoiceResult and PopulationData from YearState, applies
    per-household attribute overrides, creates vintage cohort entries
    for new purchases, and returns updated state.

    Implements the OrchestratorStep protocol (AC-5).

    Story 14-3, AC-5/AC-6/AC-7/AC-8/AC-9.
    """

    __slots__ = (
        "_domain",
        "_population_key",
        "_vintage_key",
        "_name",
        "_depends_on",
        "_description",
    )

    def __init__(
        self,
        domain: VehicleInvestmentDomain,
        population_key: str = "population_data",
        vintage_key: str = "vintage_vehicle",
        name: str = "vehicle_state_update",
        depends_on: tuple[str, ...] = ("logit_choice",),
        description: str | None = None,
    ) -> None:
        self._domain = domain
        self._population_key = population_key
        self._vintage_key = vintage_key
        self._name = name
        self._depends_on = depends_on
        self._description = (
            description
            or "Vehicle state update: apply choices and track vintage cohorts"
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
        """Execute vehicle state update for a given year.

        Reads ChoiceResult and PopulationData from state, applies
        per-household attribute overrides, creates vintage entries
        for new purchases, and returns new YearState.

        Args:
            year: Current simulation year.
            state: Current year state.

        Returns:
            New YearState with updated population and vintage state.

        Raises:
            DiscreteChoiceError: If required data missing from state.
        """
        from reformlab.computation.types import PopulationData as _PopulationData
        from reformlab.discrete_choice.types import ChoiceResult as _ChoiceResult
        from reformlab.vintage.types import VintageState as _VintageState

        config = self._domain._config

        # Read ChoiceResult from state
        choice_result = state.data.get(DISCRETE_CHOICE_RESULT_KEY)
        if not isinstance(choice_result, _ChoiceResult):
            raise DiscreteChoiceError(
                f"ChoiceResult not found in YearState.data['{DISCRETE_CHOICE_RESULT_KEY}']. "
                f"Available keys: {list(state.data.keys())}",
                year=year,
                step_name=self._name,
            )

        # Read PopulationData from state
        population = state.data.get(self._population_key)
        if not isinstance(population, _PopulationData):
            raise DiscreteChoiceError(
                f"PopulationData not found in YearState.data['{self._population_key}']. "
                f"Available keys: {list(state.data.keys())}",
                year=year,
                step_name=self._name,
            )

        n = 0
        if config.entity_key in population.tables:
            n = population.tables[config.entity_key].num_rows

        logger.info(
            "year=%d step_name=%s n_households=%d event=step_start",
            year,
            self._name,
            n,
        )

        # Apply per-household choices to population (AC-6, AC-7)
        updated_population = apply_choices_to_population(
            population,
            choice_result,
            config.alternatives,
            config.entity_key,
        )

        # Create vintage entries for new purchases (AC-8)
        new_cohorts = _create_vintage_entries(
            choice_result,
            config.alternatives,
            config.non_purchase_ids,
        )

        # Merge with existing vintage state
        existing_vintage = state.data.get(self._vintage_key)
        if isinstance(existing_vintage, _VintageState):
            merged_vintage = _VintageState(
                asset_class="vehicle",
                cohorts=existing_vintage.cohorts + new_cohorts,
                metadata={**existing_vintage.metadata, "last_choice_year": year},
            )
        elif new_cohorts:
            merged_vintage = _VintageState(
                asset_class="vehicle",
                cohorts=new_cohorts,
                metadata={"last_choice_year": year},
            )
        else:
            merged_vintage = None

        # Count switchers and keepers (AC-9)
        chosen_list: list[str] = choice_result.chosen.to_pylist()
        n_switchers = sum(
            1 for cid in chosen_list if cid not in config.non_purchase_ids
        )
        n_keepers = len(chosen_list) - n_switchers

        per_alt_counts: dict[str, int] = {}
        for cid in chosen_list:
            per_alt_counts[cid] = per_alt_counts.get(cid, 0) + 1

        # Build new state data (AC-9)
        new_data = dict(state.data)
        new_data[self._population_key] = updated_population

        if merged_vintage is not None:
            new_data[self._vintage_key] = merged_vintage

        # Extend metadata
        existing_metadata = state.data.get(DISCRETE_CHOICE_METADATA_KEY, {})
        if not isinstance(existing_metadata, dict):
            existing_metadata = {}
        extended_metadata = dict(existing_metadata)
        extended_metadata["vehicle_n_switchers"] = n_switchers
        extended_metadata["vehicle_n_keepers"] = n_keepers
        extended_metadata["vehicle_per_alternative_counts"] = per_alt_counts
        new_data[DISCRETE_CHOICE_METADATA_KEY] = extended_metadata

        logger.info(
            "year=%d step_name=%s n_households=%d n_switchers=%d "
            "n_keepers=%d event=step_complete",
            year,
            self._name,
            n,
            n_switchers,
            n_keepers,
        )

        return replace(state, data=new_data)
