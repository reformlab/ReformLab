# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for vehicle investment decision domain.

Tests VehicleDomainConfig, VehicleInvestmentDomain, apply_choices_to_population,
and VehicleStateUpdateStep.

Story 14-3: Implement Vehicle Investment Decision Domain (FR47/FR50).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pyarrow as pa
import pytest

from reformlab.computation.types import PopulationData
from reformlab.discrete_choice.domain import DecisionDomain
from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.logit import DISCRETE_CHOICE_RESULT_KEY
from reformlab.discrete_choice.step import DISCRETE_CHOICE_METADATA_KEY
from reformlab.discrete_choice.types import Alternative, ChoiceResult, TasteParameters
from reformlab.discrete_choice.vehicle import (
    VehicleDomainConfig,
    VehicleInvestmentDomain,
    VehicleStateUpdateStep,
    apply_choices_to_population,
    default_vehicle_domain_config,
)
from reformlab.orchestrator.step import StepRegistry, is_protocol_step
from reformlab.orchestrator.types import YearState
from reformlab.vintage.types import VintageCohort, VintageState

# ============================================================================
# TestVehicleDomainConfig (AC-4)
# ============================================================================


class TestVehicleDomainConfig:
    """Tests for VehicleDomainConfig frozen dataclass."""

    def test_default_config_has_six_alternatives(self) -> None:
        """AC-2: default config has exactly 6 alternatives."""
        config = default_vehicle_domain_config()
        assert len(config.alternatives) == 6

    def test_default_config_alternative_ids(self) -> None:
        """AC-2: alternative IDs are in correct order."""
        config = default_vehicle_domain_config()
        ids = [alt.id for alt in config.alternatives]
        assert ids == [
            "keep_current",
            "buy_petrol",
            "buy_diesel",
            "buy_hybrid",
            "buy_ev",
            "buy_no_vehicle",
        ]

    def test_default_config_alternative_names(self) -> None:
        """AC-2: alternative names match spec."""
        config = default_vehicle_domain_config()
        names = [alt.name for alt in config.alternatives]
        assert names == [
            "Keep Current Vehicle",
            "Buy Petrol Vehicle",
            "Buy Diesel Vehicle",
            "Buy Hybrid Vehicle",
            "Buy Electric Vehicle",
            "Give Up Vehicle",
        ]

    def test_default_config_keep_current_empty_attributes(self) -> None:
        """AC-2: keep_current has empty attributes."""
        config = default_vehicle_domain_config()
        keep = config.alternatives[0]
        assert keep.id == "keep_current"
        assert keep.attributes == {}

    def test_default_config_buy_petrol_attributes(self) -> None:
        """AC-2: buy_petrol attributes."""
        config = default_vehicle_domain_config()
        petrol = config.alternatives[1]
        assert petrol.attributes == {
            "vehicle_type": "petrol",
            "vehicle_age": 0,
            "vehicle_emissions_gkm": 120.0,
        }

    def test_default_config_buy_ev_attributes(self) -> None:
        """AC-2: buy_ev attributes."""
        config = default_vehicle_domain_config()
        ev = config.alternatives[4]
        assert ev.attributes == {
            "vehicle_type": "ev",
            "vehicle_age": 0,
            "vehicle_emissions_gkm": 0.0,
        }

    def test_default_config_buy_no_vehicle_attributes(self) -> None:
        """AC-2: buy_no_vehicle attributes."""
        config = default_vehicle_domain_config()
        no_vehicle = config.alternatives[5]
        assert no_vehicle.attributes == {
            "vehicle_type": "none",
            "vehicle_age": 0,
            "vehicle_emissions_gkm": 0.0,
        }

    def test_default_config_cost_column(self) -> None:
        """AC-4: default cost_column."""
        config = default_vehicle_domain_config()
        assert config.cost_column == "total_vehicle_cost"

    def test_default_config_entity_key(self) -> None:
        """AC-4: default entity_key."""
        config = default_vehicle_domain_config()
        assert config.entity_key == "menage"

    def test_default_config_non_purchase_ids(self) -> None:
        """AC-4: default non_purchase_ids."""
        config = default_vehicle_domain_config()
        assert config.non_purchase_ids == frozenset({"keep_current", "buy_no_vehicle"})

    def test_config_is_frozen(self) -> None:
        """AC-4: config is immutable."""
        config = default_vehicle_domain_config()
        with pytest.raises(FrozenInstanceError):
            config.cost_column = "other"  # type: ignore[misc]

    def test_alternatives_is_tuple(self) -> None:
        """AC-4: alternatives stored as tuple."""
        config = default_vehicle_domain_config()
        assert isinstance(config.alternatives, tuple)


# ============================================================================
# TestVehicleInvestmentDomain (AC-1, AC-2, AC-3)
# ============================================================================


class TestVehicleInvestmentDomain:
    """Tests for VehicleInvestmentDomain protocol compliance and behavior."""

    def test_protocol_compliance(self) -> None:
        """AC-1: isinstance(domain, DecisionDomain) returns True."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        assert isinstance(domain, DecisionDomain)

    def test_name_is_vehicle(self) -> None:
        """AC-1: domain name is 'vehicle'."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        assert domain.name == "vehicle"

    def test_alternatives_match_config(self) -> None:
        """AC-2: alternatives match config."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        assert domain.alternatives == config.alternatives

    def test_cost_column_from_config(self) -> None:
        """AC-2: cost_column from config."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        assert domain.cost_column == "total_vehicle_cost"

    def test_has_slots(self) -> None:
        """AC-1: uses __slots__ for memory efficiency."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        assert hasattr(domain, "__slots__")


# ============================================================================
# TestApplyAlternative (AC-3)
# ============================================================================


class TestApplyAlternative:
    """Tests for VehicleInvestmentDomain.apply_alternative."""

    def test_keep_current_no_op(self) -> None:
        """AC-3: keep_current with empty attributes returns table unchanged."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        table = pa.table({
            "vehicle_type": pa.array(["petrol", "diesel"]),
            "vehicle_age": pa.array([5, 10], type=pa.int64()),
            "vehicle_emissions_gkm": pa.array([150.0, 130.0]),
        })
        keep = domain.alternatives[0]
        result = domain.apply_alternative(table, keep)
        assert result.equals(table)

    def test_buy_ev_overrides_three_columns(self) -> None:
        """AC-3: buy_ev overrides vehicle_type, vehicle_age, vehicle_emissions_gkm."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        table = pa.table({
            "vehicle_type": pa.array(["petrol", "diesel"]),
            "vehicle_age": pa.array([5, 10], type=pa.int64()),
            "vehicle_emissions_gkm": pa.array([150.0, 130.0]),
        })
        ev = domain.alternatives[4]
        result = domain.apply_alternative(table, ev)
        assert result.column("vehicle_type").to_pylist() == ["ev", "ev"]
        assert result.column("vehicle_age").to_pylist() == [0, 0]
        assert result.column("vehicle_emissions_gkm").to_pylist() == [0.0, 0.0]

    def test_type_preservation_existing_column(self) -> None:
        """AC-3: existing column type is preserved via PyArrow cast."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        # vehicle_age is int32 in table, override value is int (0)
        table = pa.table({
            "vehicle_age": pa.array([5, 10], type=pa.int32()),
        })
        petrol = domain.alternatives[1]
        result = domain.apply_alternative(table, petrol)
        assert result.column("vehicle_age").type == pa.int32()
        assert result.column("vehicle_age").to_pylist() == [0, 0]

    def test_new_column_type_inference_str(self) -> None:
        """AC-3: new str column inferred as utf8."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        table = pa.table({"income": pa.array([30000.0, 45000.0])})
        petrol = domain.alternatives[1]
        result = domain.apply_alternative(table, petrol)
        assert "vehicle_type" in result.column_names
        assert result.column("vehicle_type").type == pa.utf8()

    def test_new_column_type_inference_int(self) -> None:
        """AC-3: new int column inferred as int64."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        table = pa.table({"income": pa.array([30000.0, 45000.0])})
        petrol = domain.alternatives[1]
        result = domain.apply_alternative(table, petrol)
        assert "vehicle_age" in result.column_names
        assert result.column("vehicle_age").type == pa.int64()

    def test_new_column_type_inference_float(self) -> None:
        """AC-3: new float column inferred as float64."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        table = pa.table({"income": pa.array([30000.0, 45000.0])})
        petrol = domain.alternatives[1]
        result = domain.apply_alternative(table, petrol)
        assert "vehicle_emissions_gkm" in result.column_names
        assert result.column("vehicle_emissions_gkm").type == pa.float64()

    def test_input_table_not_modified(self) -> None:
        """AC-3: input table is not modified."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        table = pa.table({
            "vehicle_type": pa.array(["petrol", "diesel"]),
            "vehicle_age": pa.array([5, 10], type=pa.int64()),
        })
        original_types = table.column("vehicle_type").to_pylist()
        ev = domain.alternatives[4]
        domain.apply_alternative(table, ev)
        assert table.column("vehicle_type").to_pylist() == original_types

    def test_incompatible_cast_raises(self) -> None:
        """AC-3: incompatible cast raises DiscreteChoiceError."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        # vehicle_type column is int, but override is str "petrol"
        table = pa.table({"vehicle_type": pa.array([1, 2], type=pa.int64())})
        petrol = domain.alternatives[1]
        with pytest.raises(DiscreteChoiceError, match="Cannot cast"):
            domain.apply_alternative(table, petrol)

    def test_unsupported_attribute_type_raises(self) -> None:
        """AC-3: unsupported Python type raises DiscreteChoiceError."""
        bad_alt = Alternative(
            id="bad", name="Bad", attributes={"x": [1, 2, 3]}
        )
        domain = VehicleInvestmentDomain(
            VehicleDomainConfig(
                alternatives=(bad_alt,),
                cost_column="total_vehicle_cost",
            )
        )
        table = pa.table({"income": pa.array([30000.0])})
        with pytest.raises(DiscreteChoiceError, match="Unsupported attribute type"):
            domain.apply_alternative(table, bad_alt)

    def test_buy_no_vehicle_sets_none_type(self) -> None:
        """AC-3: buy_no_vehicle sets vehicle_type='none'."""
        domain = VehicleInvestmentDomain(default_vehicle_domain_config())
        table = pa.table({
            "vehicle_type": pa.array(["petrol"]),
            "vehicle_age": pa.array([5], type=pa.int64()),
            "vehicle_emissions_gkm": pa.array([150.0]),
        })
        no_vehicle = domain.alternatives[5]
        result = domain.apply_alternative(table, no_vehicle)
        assert result.column("vehicle_type").to_pylist() == ["none"]
        assert result.column("vehicle_age").to_pylist() == [0]
        assert result.column("vehicle_emissions_gkm").to_pylist() == [0.0]


# ============================================================================
# TestApplyChoicesToPopulation (AC-6, AC-7)
# ============================================================================


class TestApplyChoicesToPopulation:
    """Tests for apply_choices_to_population function."""

    def _make_population(self, n: int = 3) -> PopulationData:
        """Create a test population with n households."""
        table = pa.table({
            "household_id": pa.array(list(range(n)), type=pa.int64()),
            "vehicle_type": pa.array(["petrol"] * n),
            "vehicle_age": pa.array([5] * n, type=pa.int64()),
            "vehicle_emissions_gkm": pa.array([150.0] * n),
        })
        return PopulationData(tables={"menage": table}, metadata={"source": "test"})

    def test_per_household_application(self) -> None:
        """AC-6: each row gets its chosen alternative's attributes."""
        config = default_vehicle_domain_config()
        population = self._make_population(3)
        # HH0: keep_current, HH1: buy_ev, HH2: buy_petrol
        choice_result = ChoiceResult(
            chosen=pa.array(["keep_current", "buy_ev", "buy_petrol"]),
            probabilities=pa.table({
                aid: pa.array([1.0 / 6] * 3) for aid in
                [a.id for a in config.alternatives]
            }),
            utilities=pa.table({
                aid: pa.array([-1.0] * 3) for aid in
                [a.id for a in config.alternatives]
            }),
            alternative_ids=tuple(a.id for a in config.alternatives),
            seed=42,
        )
        result = apply_choices_to_population(
            population, choice_result, config.alternatives, "menage"
        )
        table = result.tables["menage"]
        # HH0 kept current: petrol, age=5, emissions=150
        assert table.column("vehicle_type")[0].as_py() == "petrol"
        assert table.column("vehicle_age")[0].as_py() == 5
        assert table.column("vehicle_emissions_gkm")[0].as_py() == 150.0
        # HH1 bought EV: ev, age=0, emissions=0
        assert table.column("vehicle_type")[1].as_py() == "ev"
        assert table.column("vehicle_age")[1].as_py() == 0
        assert table.column("vehicle_emissions_gkm")[1].as_py() == 0.0
        # HH2 bought petrol: petrol, age=0, emissions=120
        assert table.column("vehicle_type")[2].as_py() == "petrol"
        assert table.column("vehicle_age")[2].as_py() == 0
        assert table.column("vehicle_emissions_gkm")[2].as_py() == 120.0

    def test_keep_current_unchanged(self) -> None:
        """AC-7: keep_current leaves all columns unchanged."""
        config = default_vehicle_domain_config()
        population = self._make_population(2)
        choice_result = ChoiceResult(
            chosen=pa.array(["keep_current", "keep_current"]),
            probabilities=pa.table({
                aid: pa.array([1.0 / 6] * 2) for aid in
                [a.id for a in config.alternatives]
            }),
            utilities=pa.table({
                aid: pa.array([-1.0] * 2) for aid in
                [a.id for a in config.alternatives]
            }),
            alternative_ids=tuple(a.id for a in config.alternatives),
            seed=42,
        )
        result = apply_choices_to_population(
            population, choice_result, config.alternatives, "menage"
        )
        orig = population.tables["menage"]
        updated = result.tables["menage"]
        assert updated.column("vehicle_type").to_pylist() == orig.column("vehicle_type").to_pylist()
        assert updated.column("vehicle_age").to_pylist() == orig.column("vehicle_age").to_pylist()

    def test_empty_population(self) -> None:
        """Edge case: empty population returns unchanged."""
        config = default_vehicle_domain_config()
        table = pa.table({
            "household_id": pa.array([], type=pa.int64()),
            "vehicle_type": pa.array([], type=pa.utf8()),
            "vehicle_age": pa.array([], type=pa.int64()),
            "vehicle_emissions_gkm": pa.array([], type=pa.float64()),
        })
        population = PopulationData(tables={"menage": table}, metadata={})
        choice_result = ChoiceResult(
            chosen=pa.array([], type=pa.string()),
            probabilities=pa.table({
                aid: pa.array([], type=pa.float64()) for aid in
                [a.id for a in config.alternatives]
            }),
            utilities=pa.table({
                aid: pa.array([], type=pa.float64()) for aid in
                [a.id for a in config.alternatives]
            }),
            alternative_ids=tuple(a.id for a in config.alternatives),
            seed=42,
        )
        result = apply_choices_to_population(
            population, choice_result, config.alternatives, "menage"
        )
        assert result.tables["menage"].num_rows == 0

    def test_length_mismatch_raises(self) -> None:
        """Edge case: length mismatch raises DiscreteChoiceError."""
        config = default_vehicle_domain_config()
        population = self._make_population(3)
        choice_result = ChoiceResult(
            chosen=pa.array(["keep_current", "buy_ev"]),  # only 2, population has 3
            probabilities=pa.table({
                aid: pa.array([1.0 / 6] * 2) for aid in
                [a.id for a in config.alternatives]
            }),
            utilities=pa.table({
                aid: pa.array([-1.0] * 2) for aid in
                [a.id for a in config.alternatives]
            }),
            alternative_ids=tuple(a.id for a in config.alternatives),
            seed=42,
        )
        with pytest.raises(DiscreteChoiceError, match="length"):
            apply_choices_to_population(
                population, choice_result, config.alternatives, "menage"
            )

    def test_unknown_alternative_id_raises(self) -> None:
        """Edge case: unknown alternative ID raises DiscreteChoiceError."""
        config = default_vehicle_domain_config()
        population = self._make_population(1)
        choice_result = ChoiceResult(
            chosen=pa.array(["nonexistent"]),
            probabilities=pa.table({
                aid: pa.array([1.0 / 6]) for aid in
                [a.id for a in config.alternatives]
            }),
            utilities=pa.table({
                aid: pa.array([-1.0]) for aid in
                [a.id for a in config.alternatives]
            }),
            alternative_ids=tuple(a.id for a in config.alternatives),
            seed=42,
        )
        with pytest.raises(DiscreteChoiceError, match="Unknown alternative"):
            apply_choices_to_population(
                population, choice_result, config.alternatives, "menage"
            )

    def test_new_columns_appended(self) -> None:
        """AC-3: columns not in table are appended."""
        config = default_vehicle_domain_config()
        # Population missing vehicle columns
        table = pa.table({
            "household_id": pa.array([0], type=pa.int64()),
            "income": pa.array([30000.0]),
        })
        population = PopulationData(tables={"menage": table}, metadata={})
        choice_result = ChoiceResult(
            chosen=pa.array(["buy_ev"]),
            probabilities=pa.table({
                aid: pa.array([1.0 / 6]) for aid in
                [a.id for a in config.alternatives]
            }),
            utilities=pa.table({
                aid: pa.array([-1.0]) for aid in
                [a.id for a in config.alternatives]
            }),
            alternative_ids=tuple(a.id for a in config.alternatives),
            seed=42,
        )
        result = apply_choices_to_population(
            population, choice_result, config.alternatives, "menage"
        )
        updated = result.tables["menage"]
        assert "vehicle_type" in updated.column_names
        assert "vehicle_age" in updated.column_names
        assert "vehicle_emissions_gkm" in updated.column_names
        assert updated.column("vehicle_type")[0].as_py() == "ev"


# ============================================================================
# TestVehicleStateUpdateStep (AC-5, AC-8, AC-9)
# ============================================================================


class TestVehicleStateUpdateStep:
    """Tests for VehicleStateUpdateStep orchestrator step."""

    def _make_state(
        self,
        *,
        n: int = 3,
        chosen: list[str] | None = None,
        existing_vintage: VintageState | None = None,
    ) -> YearState:
        """Create a YearState with population + ChoiceResult."""
        config = default_vehicle_domain_config()
        alt_ids = tuple(a.id for a in config.alternatives)

        table = pa.table({
            "household_id": pa.array(list(range(n)), type=pa.int64()),
            "vehicle_type": pa.array(["petrol"] * n),
            "vehicle_age": pa.array([5] * n, type=pa.int64()),
            "vehicle_emissions_gkm": pa.array([150.0] * n),
        })
        population = PopulationData(tables={"menage": table}, metadata={})

        if chosen is None:
            chosen = ["keep_current"] * n

        choice_result = ChoiceResult(
            chosen=pa.array(chosen),
            probabilities=pa.table({
                aid: pa.array([1.0 / 6] * n) for aid in alt_ids
            }),
            utilities=pa.table({
                aid: pa.array([-1.0] * n) for aid in alt_ids
            }),
            alternative_ids=alt_ids,
            seed=42,
        )

        data: dict[str, object] = {
            "population_data": population,
            DISCRETE_CHOICE_RESULT_KEY: choice_result,
            DISCRETE_CHOICE_METADATA_KEY: {"domain_name": "vehicle"},
        }
        if existing_vintage is not None:
            data["vintage_vehicle"] = existing_vintage

        return YearState(year=2025, data=data, seed=42)

    def test_protocol_compliance(self) -> None:
        """AC-5: VehicleStateUpdateStep satisfies OrchestratorStep."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        assert is_protocol_step(step)

    def test_default_name_and_depends(self) -> None:
        """AC-5: default name and depends_on."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        assert step.name == "vehicle_state_update"
        assert step.depends_on == ("logit_choice",)

    def test_step_registry_registration(self) -> None:
        """AC-5: can be registered in StepRegistry."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        registry = StepRegistry()
        # Register dependency first
        from reformlab.discrete_choice.logit import LogitChoiceStep

        logit = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        registry.register(logit)
        registry.register(step)
        assert registry.get("vehicle_state_update") is step

    def test_execute_all_keep_current(self) -> None:
        """AC-7: all keep_current → population unchanged, no vintage."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        state = self._make_state(n=3, chosen=["keep_current"] * 3)
        result = step.execute(2025, state)

        # Population unchanged
        orig = state.data["population_data"].tables["menage"]  # type: ignore[union-attr]
        updated = result.data["population_data"].tables["menage"]  # type: ignore[union-attr]
        assert updated.column("vehicle_type").to_pylist() == orig.column("vehicle_type").to_pylist()

        # Metadata extended
        meta = result.data[DISCRETE_CHOICE_METADATA_KEY]
        assert meta["vehicle_n_switchers"] == 0
        assert meta["vehicle_n_keepers"] == 3

    def test_execute_mixed_choices(self) -> None:
        """AC-6: mixed choices update population per-household."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        state = self._make_state(
            n=3, chosen=["keep_current", "buy_ev", "buy_diesel"]
        )
        result = step.execute(2025, state)

        updated = result.data["population_data"].tables["menage"]  # type: ignore[union-attr]
        # HH0: kept current
        assert updated.column("vehicle_type")[0].as_py() == "petrol"
        assert updated.column("vehicle_age")[0].as_py() == 5
        # HH1: bought EV
        assert updated.column("vehicle_type")[1].as_py() == "ev"
        assert updated.column("vehicle_age")[1].as_py() == 0
        assert updated.column("vehicle_emissions_gkm")[1].as_py() == 0.0
        # HH2: bought diesel
        assert updated.column("vehicle_type")[2].as_py() == "diesel"
        assert updated.column("vehicle_age")[2].as_py() == 0
        assert updated.column("vehicle_emissions_gkm")[2].as_py() == 110.0

    def test_execute_creates_vintage_cohorts(self) -> None:
        """AC-8: purchase choices create VintageCohort entries."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        state = self._make_state(
            n=3, chosen=["buy_ev", "buy_ev", "buy_diesel"]
        )
        result = step.execute(2025, state)

        vintage = result.data["vintage_vehicle"]
        assert isinstance(vintage, VintageState)
        assert vintage.asset_class == "vehicle"

        # 2 EV + 1 diesel → 2 cohorts (sorted by type)
        assert len(vintage.cohorts) == 2
        # Sorted: diesel first, then ev
        assert vintage.cohorts[0] == VintageCohort(
            age=0, count=1, attributes={"vehicle_type": "diesel"}
        )
        assert vintage.cohorts[1] == VintageCohort(
            age=0, count=2, attributes={"vehicle_type": "ev"}
        )

    def test_buy_no_vehicle_excluded_from_vintage(self) -> None:
        """AC-8: buy_no_vehicle does NOT create vintage entry."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        state = self._make_state(
            n=2, chosen=["buy_no_vehicle", "buy_ev"]
        )
        result = step.execute(2025, state)

        vintage = result.data["vintage_vehicle"]
        assert isinstance(vintage, VintageState)
        # Only EV creates vintage (buy_no_vehicle is in non_purchase_ids)
        assert len(vintage.cohorts) == 1
        assert vintage.cohorts[0].attributes["vehicle_type"] == "ev"

    def test_vintage_appended_to_existing(self) -> None:
        """AC-8: new cohorts appended to existing VintageState."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        existing = VintageState(
            asset_class="vehicle",
            cohorts=(VintageCohort(age=1, count=10, attributes={"vehicle_type": "petrol"}),),
            metadata={"year": 2024},
        )
        state = self._make_state(
            n=1, chosen=["buy_ev"], existing_vintage=existing
        )
        result = step.execute(2025, state)

        vintage = result.data["vintage_vehicle"]
        assert isinstance(vintage, VintageState)
        assert len(vintage.cohorts) == 2
        # Old cohort preserved
        assert vintage.cohorts[0].age == 1
        assert vintage.cohorts[0].count == 10
        # New cohort appended
        assert vintage.cohorts[1].age == 0
        assert vintage.cohorts[1].count == 1

    def test_no_vintage_when_all_keep(self) -> None:
        """AC-8: no vintage entries when all keep_current."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        state = self._make_state(n=2, chosen=["keep_current", "keep_current"])
        result = step.execute(2025, state)
        # No vintage key set when no purchases and no existing vintage
        assert "vintage_vehicle" not in result.data or (
            isinstance(result.data.get("vintage_vehicle"), VintageState)
            and result.data["vintage_vehicle"].total_count == 0
        )

    def test_state_immutability(self) -> None:
        """AC-9: original state not modified."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        state = self._make_state(n=1, chosen=["buy_ev"])
        original_data_id = id(state.data)
        result = step.execute(2025, state)
        # Original state not modified
        assert id(result.data) != original_data_id
        assert result is not state

    def test_metadata_extension(self) -> None:
        """AC-9: metadata extended with switch counts."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        state = self._make_state(
            n=3, chosen=["keep_current", "buy_ev", "buy_no_vehicle"]
        )
        result = step.execute(2025, state)
        meta = result.data[DISCRETE_CHOICE_METADATA_KEY]
        assert meta["vehicle_n_switchers"] == 1  # only buy_ev is a purchase
        assert meta["vehicle_n_keepers"] == 2  # keep + no_vehicle
        assert isinstance(meta["vehicle_per_alternative_counts"], dict)
        assert meta["vehicle_per_alternative_counts"]["buy_ev"] == 1

    def test_missing_choice_result_raises(self) -> None:
        """Edge case: missing ChoiceResult raises DiscreteChoiceError."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        state = YearState(
            year=2025,
            data={"population_data": PopulationData(tables={}, metadata={})},
        )
        with pytest.raises(DiscreteChoiceError, match="ChoiceResult"):
            step.execute(2025, state)

    def test_missing_population_raises(self) -> None:
        """Edge case: missing PopulationData raises DiscreteChoiceError."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        alt_ids = tuple(a.id for a in config.alternatives)
        state = YearState(
            year=2025,
            data={
                DISCRETE_CHOICE_RESULT_KEY: ChoiceResult(
                    chosen=pa.array([], type=pa.string()),
                    probabilities=pa.table({
                        aid: pa.array([], type=pa.float64()) for aid in alt_ids
                    }),
                    utilities=pa.table({
                        aid: pa.array([], type=pa.float64()) for aid in alt_ids
                    }),
                    alternative_ids=alt_ids,
                    seed=42,
                ),
            },
        )
        with pytest.raises(DiscreteChoiceError, match="PopulationData"):
            step.execute(2025, state)

    def test_missing_entity_key_raises(self) -> None:
        """Edge case: entity_key not in population raises DiscreteChoiceError."""
        config = default_vehicle_domain_config()
        population = PopulationData(
            tables={"other_entity": pa.table({"x": pa.array([1])})},
            metadata={},
        )
        choice_result = ChoiceResult(
            chosen=pa.array(["keep_current"]),
            probabilities=pa.table({
                aid: pa.array([1.0 / 6])
                for aid in [a.id for a in config.alternatives]
            }),
            utilities=pa.table({
                aid: pa.array([-1.0])
                for aid in [a.id for a in config.alternatives]
            }),
            alternative_ids=tuple(a.id for a in config.alternatives),
            seed=42,
        )
        with pytest.raises(DiscreteChoiceError, match="Entity key"):
            apply_choices_to_population(
                population, choice_result, config.alternatives, "menage"
            )

    def test_non_dict_metadata_raises(self) -> None:
        """Edge case: non-dict metadata raises DiscreteChoiceError."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        state = self._make_state(n=1, chosen=["keep_current"])
        # Corrupt metadata to non-dict
        corrupted_data = dict(state.data)
        corrupted_data[DISCRETE_CHOICE_METADATA_KEY] = "not_a_dict"
        from dataclasses import replace as _replace

        corrupted_state = _replace(state, data=corrupted_data)
        with pytest.raises(DiscreteChoiceError, match="Expected dict"):
            step.execute(2025, corrupted_state)

    def test_vintage_asset_class_mismatch_raises(self) -> None:
        """Edge case: existing vintage with wrong asset_class raises DiscreteChoiceError."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        wrong_vintage = VintageState(
            asset_class="heating",
            cohorts=(VintageCohort(age=1, count=5, attributes={"type": "gas"}),),
            metadata={},
        )
        state = self._make_state(n=1, chosen=["buy_ev"], existing_vintage=wrong_vintage)
        with pytest.raises(DiscreteChoiceError, match="asset_class"):
            step.execute(2025, state)


# ============================================================================
# TestVintageIntegration (AC-8)
# ============================================================================


class TestVintageIntegration:
    """Tests for vintage cohort integration behavior."""

    def test_new_vintage_state_created(self) -> None:
        """AC-8: new VintageState created when none exists."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        alt_ids = tuple(a.id for a in config.alternatives)

        table = pa.table({
            "household_id": pa.array([0], type=pa.int64()),
            "vehicle_type": pa.array(["petrol"]),
            "vehicle_age": pa.array([5], type=pa.int64()),
            "vehicle_emissions_gkm": pa.array([150.0]),
        })
        population = PopulationData(tables={"menage": table}, metadata={})
        choice_result = ChoiceResult(
            chosen=pa.array(["buy_hybrid"]),
            probabilities=pa.table({
                aid: pa.array([1.0 / 6]) for aid in alt_ids
            }),
            utilities=pa.table({
                aid: pa.array([-1.0]) for aid in alt_ids
            }),
            alternative_ids=alt_ids,
            seed=42,
        )
        state = YearState(
            year=2025,
            data={
                "population_data": population,
                DISCRETE_CHOICE_RESULT_KEY: choice_result,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
            seed=42,
        )
        result = step.execute(2025, state)
        vintage = result.data["vintage_vehicle"]
        assert isinstance(vintage, VintageState)
        assert vintage.asset_class == "vehicle"
        assert len(vintage.cohorts) == 1
        assert vintage.cohorts[0] == VintageCohort(
            age=0, count=1, attributes={"vehicle_type": "hybrid"}
        )

    def test_cohorts_correct_age_zero(self) -> None:
        """AC-8: all new cohorts have age=0."""
        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)
        step = VehicleStateUpdateStep(domain=domain)
        alt_ids = tuple(a.id for a in config.alternatives)

        table = pa.table({
            "household_id": pa.array([0, 1, 2], type=pa.int64()),
            "vehicle_type": pa.array(["petrol"] * 3),
            "vehicle_age": pa.array([5] * 3, type=pa.int64()),
            "vehicle_emissions_gkm": pa.array([150.0] * 3),
        })
        population = PopulationData(tables={"menage": table}, metadata={})
        choice_result = ChoiceResult(
            chosen=pa.array(["buy_petrol", "buy_diesel", "buy_ev"]),
            probabilities=pa.table({
                aid: pa.array([1.0 / 6] * 3) for aid in alt_ids
            }),
            utilities=pa.table({
                aid: pa.array([-1.0] * 3) for aid in alt_ids
            }),
            alternative_ids=alt_ids,
            seed=42,
        )
        state = YearState(
            year=2025,
            data={
                "population_data": population,
                DISCRETE_CHOICE_RESULT_KEY: choice_result,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
            seed=42,
        )
        result = step.execute(2025, state)
        vintage = result.data["vintage_vehicle"]
        assert isinstance(vintage, VintageState)
        for cohort in vintage.cohorts:
            assert cohort.age == 0


# ============================================================================
# Integration test: full pipeline (AC: all)
# ============================================================================


class TestVehiclePipelineIntegration:
    """Integration test: DiscreteChoiceStep → LogitChoiceStep → VehicleStateUpdateStep."""

    def test_full_pipeline(self) -> None:
        """Full pipeline with MockAdapter produces valid state."""
        from reformlab.computation.mock_adapter import MockAdapter
        from reformlab.computation.types import PolicyConfig
        from reformlab.discrete_choice.expansion import (
            TRACKING_COL_ALTERNATIVE_ID,
            TRACKING_COL_ORIGINAL_INDEX,
        )
        from reformlab.discrete_choice.logit import LogitChoiceStep
        from reformlab.discrete_choice.step import DiscreteChoiceStep
        from reformlab.templates.schema import CarbonTaxParameters

        config = default_vehicle_domain_config()
        domain = VehicleInvestmentDomain(config)

        def vehicle_compute_fn(
            population: PopulationData,
            policy: PolicyConfig,
            period: int,
        ) -> pa.Table:
            """Compute total_vehicle_cost based on vehicle attributes."""
            entity_key = sorted(population.tables.keys())[0]
            table = population.tables[entity_key]
            emissions = table.column("vehicle_emissions_gkm").to_pylist()
            ages = table.column("vehicle_age").to_pylist()
            costs = [e * 100.0 + a * 50.0 for e, a in zip(emissions, ages)]
            result_cols: dict[str, pa.Array] = {
                "total_vehicle_cost": pa.array(costs),
            }
            if TRACKING_COL_ALTERNATIVE_ID in table.column_names:
                result_cols[TRACKING_COL_ALTERNATIVE_ID] = table.column(
                    TRACKING_COL_ALTERNATIVE_ID
                )
            if TRACKING_COL_ORIGINAL_INDEX in table.column_names:
                result_cols[TRACKING_COL_ORIGINAL_INDEX] = table.column(
                    TRACKING_COL_ORIGINAL_INDEX
                )
            return pa.table(result_cols)

        adapter = MockAdapter(
            version_string="mock-vehicle-1.0",
            compute_fn=vehicle_compute_fn,
        )
        policy = PolicyConfig(policy=CarbonTaxParameters(rate_schedule={2025: 44.6}), name="test")
        taste = TasteParameters(beta_cost=-0.001)

        dc_step = DiscreteChoiceStep(
            adapter=adapter, domain=domain, policy=policy
        )
        logit_step = LogitChoiceStep(taste_parameters=taste)
        update_step = VehicleStateUpdateStep(domain=domain)

        # Build population
        table = pa.table({
            "household_id": pa.array([0, 1, 2], type=pa.int64()),
            "income": pa.array([30000.0, 45000.0, 60000.0]),
            "vehicle_type": pa.array(["petrol", "diesel", "petrol"]),
            "vehicle_age": pa.array([5, 8, 3], type=pa.int64()),
            "vehicle_emissions_gkm": pa.array([150.0, 130.0, 120.0]),
            "fuel_cost": pa.array([0.15, 0.18, 0.12]),
        })
        population = PopulationData(tables={"menage": table}, metadata={})
        state = YearState(
            year=2025,
            data={"population_data": population},
            seed=12345,
        )

        # Execute pipeline
        state = dc_step.execute(2025, state)
        state = logit_step.execute(2025, state)
        state = update_step.execute(2025, state)

        # Validate outputs
        assert "population_data" in state.data
        assert DISCRETE_CHOICE_METADATA_KEY in state.data
        meta = state.data[DISCRETE_CHOICE_METADATA_KEY]
        assert "vehicle_n_switchers" in meta
        assert "vehicle_n_keepers" in meta
        assert "vehicle_per_alternative_counts" in meta
        assert meta["vehicle_n_switchers"] + meta["vehicle_n_keepers"] == 3

        # Population still has 3 rows
        updated_pop = state.data["population_data"]
        assert isinstance(updated_pop, PopulationData)
        assert updated_pop.tables["menage"].num_rows == 3


# ============================================================================
# Story 21.7: Generalized taste parameter tests
# ============================================================================


class TestVehicleDomainConfigGeneralized:
    """Tests for VehicleDomainConfig with generalized taste parameters (Story 21.7 / AC-7)."""

    def test_default_config_has_no_taste_parameters(self) -> None:
        """Given default config, taste_parameters is None (uses legacy mode)."""
        from reformlab.discrete_choice.vehicle import default_vehicle_domain_config

        config = default_vehicle_domain_config()
        assert config.taste_parameters is None

    def test_effective_taste_parameters_returns_legacy_for_none(self) -> None:
        """Given config with taste_parameters=None, effective_taste_parameters returns legacy."""
        from reformlab.discrete_choice.vehicle import default_vehicle_domain_config

        config = default_vehicle_domain_config()
        taste_params = config.effective_taste_parameters

        assert taste_params.is_legacy_mode is True
        assert taste_params.beta_cost == -0.01

    def test_effective_taste_parameters_returns_provided(self) -> None:
        """Given config with taste_parameters, effective_taste_parameters returns it."""
        from reformlab.discrete_choice.types import TasteParameters
        from reformlab.discrete_choice.vehicle import VehicleDomainConfig

        taste_params = TasteParameters(
            beta_cost=0.0,
            asc={"keep_current": 0.0, "buy_ev": -0.5},
            betas={"cost": -0.01},
            calibrate=frozenset(["buy_ev"]),
            fixed=frozenset(["keep_current", "cost"]),
            reference_alternative="keep_current",
        )

        config = VehicleDomainConfig(
            alternatives=default_vehicle_domain_config().alternatives,
            taste_parameters=taste_params,
        )

        effective = config.effective_taste_parameters
        assert effective is taste_params
        assert effective.is_legacy_mode is False

    def test_create_vehicle_config_with_taste_parameters_valid(self) -> None:
        """Given valid inputs, factory creates config with generalized taste parameters."""
        from reformlab.discrete_choice.vehicle import create_vehicle_config_with_taste_parameters

        config = create_vehicle_config_with_taste_parameters(
            asc={"keep_current": 0.0, "buy_ev": -0.5, "buy_petrol": -0.3},
            betas={"cost": -0.01},
            calibrate={"buy_ev"},
            fixed={"cost", "keep_current", "buy_petrol"},
            reference_alternative="keep_current",
        )

        assert config.taste_parameters is not None
        assert config.taste_parameters.is_legacy_mode is False
        assert len(config.taste_parameters.asc) == 3
        assert config.taste_parameters.asc["keep_current"] == 0.0

    def test_create_vehicle_config_with_unknown_asc_raises(self) -> None:
        """Given ASC with unknown alternative ID, factory raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError
        from reformlab.discrete_choice.vehicle import create_vehicle_config_with_taste_parameters

        with pytest.raises(DiscreteChoiceError, match="Unknown alternative"):
            create_vehicle_config_with_taste_parameters(
                asc={"unknown_alt": 0.0},
                betas={"cost": -0.01},
                calibrate={"cost"},
            )

    def test_create_vehicle_config_with_unknown_reference_raises(self) -> None:
        """Given unknown reference_alternative, factory raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError
        from reformlab.discrete_choice.vehicle import create_vehicle_config_with_taste_parameters

        with pytest.raises(DiscreteChoiceError, match="not found"):
            create_vehicle_config_with_taste_parameters(
                asc={"keep_current": 0.0},
                betas={"cost": -0.01},
                calibrate={"cost"},
                reference_alternative="unknown_alt",
            )

    def test_create_vehicle_config_with_empty_betas_raises(self) -> None:
        """Given empty betas, factory raises DiscreteChoiceError."""
        from reformlab.discrete_choice.errors import DiscreteChoiceError
        from reformlab.discrete_choice.vehicle import create_vehicle_config_with_taste_parameters

        with pytest.raises(DiscreteChoiceError, match="At least one beta"):
            create_vehicle_config_with_taste_parameters(
                asc={"keep_current": 0.0},
                betas={},
                calibrate=set(),
            )


class TestTasteParametersGovernanceEntry:
    """Tests for TasteParameters.to_governance_entry() (Story 21.7 / AC-8)."""

    def test_legacy_mode_governance_entry_structure(self) -> None:
        """Given legacy mode TasteParameters, governance entry has correct structure."""
        from reformlab.discrete_choice.types import TasteParameters

        taste_params = TasteParameters.from_beta_cost(-0.01)
        entry = taste_params.to_governance_entry()

        assert entry["key"] == "taste_parameters"
        assert entry["source"] == "taste_parameters"
        assert entry["is_default"] is False
        assert entry["value"]["is_legacy_mode"] is True
        assert entry["value"]["asc_names"] == []
        assert entry["value"]["beta_names"] == ["cost"]
        assert entry["value"]["n_calibrated"] == 1
        assert entry["value"]["n_fixed"] == 0

    def test_generalized_mode_governance_entry_structure(self) -> None:
        """Given generalized mode TasteParameters, governance entry includes all fields."""
        from reformlab.discrete_choice.types import TasteParameters

        taste_params = TasteParameters(
            beta_cost=0.0,
            asc={"keep_current": 0.0, "buy_ev": -0.5},
            betas={"cost": -0.01, "emissions": -0.05},
            calibrate=frozenset(["buy_ev", "cost"]),
            fixed=frozenset(["keep_current", "emissions"]),
            reference_alternative="keep_current",
            literature_sources={"emissions": "Dargay & Gately 1999"},
        )
        entry = taste_params.to_governance_entry()

        assert entry["key"] == "taste_parameters"
        assert entry["value"]["is_legacy_mode"] is False
        assert set(entry["value"]["asc_names"]) == {"keep_current", "buy_ev"}
        assert set(entry["value"]["beta_names"]) == {"cost", "emissions"}
        assert "buy_ev" in entry["value"]["calibrated_asc_names"]
        assert "cost" in entry["value"]["calibrated_beta_names"]
        assert entry["value"]["reference_alternative"] == "keep_current"
        assert entry["value"]["literature_sources"]["emissions"] == "Dargay & Gately 1999"

    def test_governance_entry_custom_source_label(self) -> None:
        """Given custom source_label, governance entry uses it."""
        from reformlab.discrete_choice.types import TasteParameters

        taste_params = TasteParameters.from_beta_cost(-0.01)
        entry = taste_params.to_governance_entry(source_label="my_custom_source")

        assert entry["source"] == "my_custom_source"


class TestCalibrationResultGovernanceEntry:
    """Tests for CalibrationResult.to_governance_entry() with diagnostics (Story 21.7 / AC-8)."""

    def test_governance_entry_includes_diagnostics(self) -> None:
        """Given CalibrationResult with diagnostics, governance entry includes them."""
        from reformlab.calibration.types import (
            CalibrationResult,
            ParameterDiagnostics,
            RateComparison,
        )
        from reformlab.discrete_choice.types import TasteParameters

        taste_params = TasteParameters.from_beta_cost(-0.05)
        param_diags = {
            "beta_cost": ParameterDiagnostics(
                optimized_value=-0.048,
                initial_value=-0.05,
                absolute_change=0.002,
                relative_change_pct=4.0,
                at_lower_bound=False,
                at_upper_bound=False,
                gradient_component=0.001,
            )
        }

        rate_comparisons = (
            RateComparison(
                from_state="petrol",
                to_state="buy_ev",
                observed_rate=0.03,
                simulated_rate=0.035,
                absolute_error=0.005,
                within_tolerance=True,
            ),
        )

        result = CalibrationResult(
            optimized_parameters=taste_params,
            domain="vehicle",
            objective_type="mse",
            objective_value=0.001,
            convergence_flag=True,
            iterations=50,
            gradient_norm=0.001,
            method="L-BFGS-B",
            rate_comparisons=rate_comparisons,
            all_within_tolerance=True,
            parameter_diagnostics=param_diags,
            convergence_warnings=[],
            identifiability_flags={},
        )

        entry = result.to_governance_entry()

        assert entry["key"] == "calibration_result"
        assert "parameter_diagnostics" in entry["value"]
        assert "beta_cost" in entry["value"]["parameter_diagnostics"]
        diag_entry = entry["value"]["parameter_diagnostics"]["beta_cost"]
        assert diag_entry["optimized_value"] == -0.048
        assert diag_entry["at_lower_bound"] is False
        assert entry["value"]["convergence_warnings"] == []
        assert entry["value"]["identifiability_flags"] == {}
        assert "taste_parameters" in entry["value"]
