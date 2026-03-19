"""Tests for heating system investment decision domain.

Tests HeatingDomainConfig, HeatingInvestmentDomain, apply_alternative,
HeatingStateUpdateStep, vintage integration, and sequential domain execution.

Story 14-4: Implement Heating System Decision Domain (FR47/FR50).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from dataclasses import replace as _replace

import pyarrow as pa
import pytest

from reformlab.computation.types import PopulationData
from reformlab.discrete_choice.domain import DecisionDomain
from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.heating import (
    HeatingDomainConfig,
    HeatingInvestmentDomain,
    HeatingStateUpdateStep,
    default_heating_domain_config,
)
from reformlab.discrete_choice.logit import DISCRETE_CHOICE_RESULT_KEY
from reformlab.discrete_choice.step import DISCRETE_CHOICE_METADATA_KEY
from reformlab.discrete_choice.types import Alternative, ChoiceResult, TasteParameters
from reformlab.orchestrator.step import StepRegistry, is_protocol_step
from reformlab.orchestrator.types import YearState
from reformlab.vintage.types import VintageCohort, VintageState

# ============================================================================
# TestHeatingDomainConfig (AC-4)
# ============================================================================


class TestHeatingDomainConfig:
    """Tests for HeatingDomainConfig frozen dataclass."""

    def test_default_config_has_five_alternatives(self) -> None:
        """AC-2: default config has exactly 5 alternatives."""
        config = default_heating_domain_config()
        assert len(config.alternatives) == 5

    def test_default_config_alternative_ids(self) -> None:
        """AC-2: alternative IDs are in correct order."""
        config = default_heating_domain_config()
        ids = [alt.id for alt in config.alternatives]
        assert ids == [
            "keep_current",
            "gas_boiler",
            "heat_pump",
            "electric",
            "wood_pellet",
        ]

    def test_default_config_alternative_names(self) -> None:
        """AC-2: alternative names match spec."""
        config = default_heating_domain_config()
        names = [alt.name for alt in config.alternatives]
        assert names == [
            "Keep Current Heating",
            "Install Gas Boiler",
            "Install Heat Pump",
            "Install Electric Heating",
            "Install Wood/Pellet Stove",
        ]

    def test_default_config_keep_current_empty_attributes(self) -> None:
        """AC-2: keep_current has empty attributes."""
        config = default_heating_domain_config()
        keep = config.alternatives[0]
        assert keep.id == "keep_current"
        assert keep.attributes == {}

    def test_default_config_gas_boiler_attributes(self) -> None:
        """AC-2: gas_boiler attributes."""
        config = default_heating_domain_config()
        gas = config.alternatives[1]
        assert gas.attributes == {
            "heating_type": "gas",
            "heating_age": 0,
            "heating_emissions_kgco2_kwh": 0.227,
        }

    def test_default_config_heat_pump_attributes(self) -> None:
        """AC-2: heat_pump attributes."""
        config = default_heating_domain_config()
        hp = config.alternatives[2]
        assert hp.attributes == {
            "heating_type": "heat_pump",
            "heating_age": 0,
            "heating_emissions_kgco2_kwh": 0.057,
        }

    def test_default_config_electric_attributes(self) -> None:
        """AC-2: electric attributes."""
        config = default_heating_domain_config()
        elec = config.alternatives[3]
        assert elec.attributes == {
            "heating_type": "electric",
            "heating_age": 0,
            "heating_emissions_kgco2_kwh": 0.057,
        }

    def test_default_config_wood_pellet_attributes(self) -> None:
        """AC-2: wood_pellet attributes."""
        config = default_heating_domain_config()
        wood = config.alternatives[4]
        assert wood.attributes == {
            "heating_type": "wood",
            "heating_age": 0,
            "heating_emissions_kgco2_kwh": 0.030,
        }

    def test_default_config_cost_column(self) -> None:
        """AC-4: default cost_column."""
        config = default_heating_domain_config()
        assert config.cost_column == "total_heating_cost"

    def test_default_config_entity_key(self) -> None:
        """AC-4: default entity_key."""
        config = default_heating_domain_config()
        assert config.entity_key == "menage"

    def test_default_config_non_purchase_ids(self) -> None:
        """AC-4: default non_purchase_ids."""
        config = default_heating_domain_config()
        assert config.non_purchase_ids == frozenset({"keep_current"})

    def test_config_is_frozen(self) -> None:
        """AC-4: config is immutable."""
        config = default_heating_domain_config()
        with pytest.raises(FrozenInstanceError):
            config.cost_column = "other"  # type: ignore[misc]

    def test_alternatives_is_tuple(self) -> None:
        """AC-4: alternatives stored as tuple."""
        config = default_heating_domain_config()
        assert isinstance(config.alternatives, tuple)


# ============================================================================
# TestHeatingInvestmentDomain (AC-1, AC-2, AC-3)
# ============================================================================


class TestHeatingInvestmentDomain:
    """Tests for HeatingInvestmentDomain protocol compliance and behavior."""

    def test_protocol_compliance(self) -> None:
        """AC-1: isinstance(domain, DecisionDomain) returns True."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        assert isinstance(domain, DecisionDomain)

    def test_name_is_heating(self) -> None:
        """AC-1: domain name is 'heating'."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        assert domain.name == "heating"

    def test_alternatives_match_config(self) -> None:
        """AC-2: alternatives match config."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        assert domain.alternatives == config.alternatives

    def test_cost_column_from_config(self) -> None:
        """AC-2: cost_column from config."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        assert domain.cost_column == "total_heating_cost"

    def test_has_slots(self) -> None:
        """AC-1: uses __slots__ for memory efficiency."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        assert hasattr(domain, "__slots__")


# ============================================================================
# TestApplyAlternative (AC-3)
# ============================================================================


class TestApplyAlternative:
    """Tests for HeatingInvestmentDomain.apply_alternative."""

    def test_keep_current_no_op(self) -> None:
        """AC-3: keep_current with empty attributes returns table unchanged."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        table = pa.table({
            "heating_type": pa.array(["gas", "electric"]),
            "heating_age": pa.array([5, 10], type=pa.int64()),
            "heating_emissions_kgco2_kwh": pa.array([0.227, 0.057]),
        })
        keep = domain.alternatives[0]
        result = domain.apply_alternative(table, keep)
        assert result.equals(table)

    def test_heat_pump_overrides(self) -> None:
        """AC-3: heat_pump overrides all three columns."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        table = pa.table({
            "heating_type": pa.array(["gas", "gas"]),
            "heating_age": pa.array([15, 20], type=pa.int64()),
            "heating_emissions_kgco2_kwh": pa.array([0.227, 0.227]),
        })
        hp = domain.alternatives[2]
        result = domain.apply_alternative(table, hp)
        assert result.column("heating_type").to_pylist() == ["heat_pump", "heat_pump"]
        assert result.column("heating_age").to_pylist() == [0, 0]
        assert result.column("heating_emissions_kgco2_kwh").to_pylist() == [0.057, 0.057]

    def test_type_preservation_existing_column(self) -> None:
        """AC-3: existing column type is preserved via PyArrow cast."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        table = pa.table({
            "heating_age": pa.array([5, 10], type=pa.int32()),
        })
        gas = domain.alternatives[1]
        result = domain.apply_alternative(table, gas)
        assert result.column("heating_age").type == pa.int32()
        assert result.column("heating_age").to_pylist() == [0, 0]

    def test_new_column_type_inference_str(self) -> None:
        """AC-3: new str column inferred as utf8."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        table = pa.table({"income": pa.array([30000.0, 45000.0])})
        gas = domain.alternatives[1]
        result = domain.apply_alternative(table, gas)
        assert "heating_type" in result.column_names
        assert result.column("heating_type").type == pa.utf8()

    def test_new_column_type_inference_int(self) -> None:
        """AC-3: new int column inferred as int64."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        table = pa.table({"income": pa.array([30000.0, 45000.0])})
        gas = domain.alternatives[1]
        result = domain.apply_alternative(table, gas)
        assert "heating_age" in result.column_names
        assert result.column("heating_age").type == pa.int64()

    def test_new_column_type_inference_float(self) -> None:
        """AC-3: new float column inferred as float64."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        table = pa.table({"income": pa.array([30000.0, 45000.0])})
        gas = domain.alternatives[1]
        result = domain.apply_alternative(table, gas)
        assert "heating_emissions_kgco2_kwh" in result.column_names
        assert result.column("heating_emissions_kgco2_kwh").type == pa.float64()

    def test_input_table_not_modified(self) -> None:
        """AC-3: input table is not modified."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        table = pa.table({
            "heating_type": pa.array(["gas", "electric"]),
            "heating_age": pa.array([5, 10], type=pa.int64()),
        })
        original_types = table.column("heating_type").to_pylist()
        hp = domain.alternatives[2]
        domain.apply_alternative(table, hp)
        assert table.column("heating_type").to_pylist() == original_types

    def test_incompatible_cast_raises(self) -> None:
        """AC-3: incompatible cast raises DiscreteChoiceError."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        table = pa.table({"heating_type": pa.array([1, 2], type=pa.int64())})
        gas = domain.alternatives[1]
        with pytest.raises(DiscreteChoiceError, match="Cannot cast"):
            domain.apply_alternative(table, gas)

    def test_unsupported_attribute_type_raises(self) -> None:
        """AC-3: unsupported Python type raises DiscreteChoiceError."""
        bad_alt = Alternative(
            id="bad", name="Bad", attributes={"x": [1, 2, 3]}
        )
        domain = HeatingInvestmentDomain(
            HeatingDomainConfig(alternatives=(bad_alt,))
        )
        table = pa.table({"income": pa.array([30000.0])})
        with pytest.raises(DiscreteChoiceError, match="Unsupported attribute type"):
            domain.apply_alternative(table, bad_alt)

    def test_multiple_attributes_applied(self) -> None:
        """AC-3: all attributes in the alternative are applied."""
        domain = HeatingInvestmentDomain(default_heating_domain_config())
        table = pa.table({"income": pa.array([40000.0])})
        wood = domain.alternatives[4]
        result = domain.apply_alternative(table, wood)
        assert result.column("heating_type")[0].as_py() == "wood"
        assert result.column("heating_age")[0].as_py() == 0
        assert result.column("heating_emissions_kgco2_kwh")[0].as_py() == 0.030
        # Original column preserved
        assert result.column("income")[0].as_py() == 40000.0


# ============================================================================
# TestHeatingStateUpdateStep (AC-5, AC-6, AC-7, AC-8, AC-9)
# ============================================================================


class TestHeatingStateUpdateStep:
    """Tests for HeatingStateUpdateStep orchestrator step."""

    @staticmethod
    def _make_state(
        *,
        n: int = 3,
        chosen: list[str] | None = None,
        existing_vintage: VintageState | None = None,
        existing_metadata: dict[str, object] | None = None,
    ) -> YearState:
        """Create a YearState with population + ChoiceResult for heating."""
        config = default_heating_domain_config()
        alt_ids = tuple(a.id for a in config.alternatives)

        table = pa.table({
            "household_id": pa.array(list(range(n)), type=pa.int64()),
            "heating_type": pa.array(["gas"] * n),
            "heating_age": pa.array([10] * n, type=pa.int64()),
            "heating_emissions_kgco2_kwh": pa.array([0.227] * n),
        })
        population = PopulationData(tables={"menage": table}, metadata={})

        if chosen is None:
            chosen = ["keep_current"] * n

        choice_result = ChoiceResult(
            chosen=pa.array(chosen),
            probabilities=pa.table({
                aid: pa.array([1.0 / 5] * n) for aid in alt_ids
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
            DISCRETE_CHOICE_METADATA_KEY: existing_metadata
            if existing_metadata is not None
            else {"domain_name": "heating"},
        }
        if existing_vintage is not None:
            data["vintage_heating"] = existing_vintage

        return YearState(year=2025, data=data, seed=42)

    def test_protocol_compliance(self) -> None:
        """AC-5: HeatingStateUpdateStep satisfies OrchestratorStep."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        assert is_protocol_step(step)

    def test_default_name_and_depends(self) -> None:
        """AC-5: default name and depends_on."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        assert step.name == "heating_state_update"
        assert step.depends_on == ("logit_choice",)

    def test_step_registry_registration(self) -> None:
        """AC-5: can be registered in StepRegistry."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        registry = StepRegistry()
        from reformlab.discrete_choice.logit import LogitChoiceStep

        logit = LogitChoiceStep(taste_parameters=TasteParameters(beta_cost=-0.01))
        registry.register(logit)
        registry.register(step)
        assert registry.get("heating_state_update") is step

    def test_execute_all_keep_current(self) -> None:
        """AC-7: all keep_current → population unchanged, no vintage."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        state = self._make_state(n=3, chosen=["keep_current"] * 3)
        result = step.execute(2025, state)

        # Population unchanged — verify ALL columns, not just heating_type (AC-7)
        orig = state.data["population_data"].tables["menage"]  # type: ignore[union-attr]
        updated = result.data["population_data"].tables["menage"]  # type: ignore[union-attr]
        assert updated.column_names == orig.column_names
        for col_name in orig.column_names:
            assert (
                updated.column(col_name).to_pylist() == orig.column(col_name).to_pylist()
            ), f"Column '{col_name}' changed unexpectedly when all chose keep_current"

        # Metadata extended
        meta = result.data[DISCRETE_CHOICE_METADATA_KEY]
        assert meta["heating_n_switchers"] == 0  # type: ignore[index]
        assert meta["heating_n_keepers"] == 3  # type: ignore[index]

        # No vintage created
        assert "vintage_heating" not in result.data

    def test_execute_mixed_choices(self) -> None:
        """AC-6: mixed choices update population per-household."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        state = self._make_state(
            n=3, chosen=["keep_current", "heat_pump", "wood_pellet"]
        )
        result = step.execute(2025, state)

        updated = result.data["population_data"].tables["menage"]  # type: ignore[union-attr]
        # HH0: kept current
        assert updated.column("heating_type")[0].as_py() == "gas"
        assert updated.column("heating_age")[0].as_py() == 10
        assert updated.column("heating_emissions_kgco2_kwh")[0].as_py() == 0.227
        # HH1: heat pump
        assert updated.column("heating_type")[1].as_py() == "heat_pump"
        assert updated.column("heating_age")[1].as_py() == 0
        assert updated.column("heating_emissions_kgco2_kwh")[1].as_py() == 0.057
        # HH2: wood pellet
        assert updated.column("heating_type")[2].as_py() == "wood"
        assert updated.column("heating_age")[2].as_py() == 0
        assert updated.column("heating_emissions_kgco2_kwh")[2].as_py() == 0.030

    def test_execute_creates_vintage_cohorts(self) -> None:
        """AC-8: installation choices create VintageCohort entries."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        state = self._make_state(
            n=3, chosen=["heat_pump", "heat_pump", "gas_boiler"]
        )
        result = step.execute(2025, state)

        vintage = result.data["vintage_heating"]
        assert isinstance(vintage, VintageState)
        assert vintage.asset_class == "heating"

        # 2 heat_pump + 1 gas → 2 cohorts (sorted by type)
        assert len(vintage.cohorts) == 2
        assert vintage.cohorts[0] == VintageCohort(
            age=0, count=1, attributes={"heating_type": "gas"}
        )
        assert vintage.cohorts[1] == VintageCohort(
            age=0, count=2, attributes={"heating_type": "heat_pump"}
        )

    def test_vintage_appended_to_existing(self) -> None:
        """AC-8: new cohorts appended to existing VintageState."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        existing = VintageState(
            asset_class="heating",
            cohorts=(VintageCohort(age=1, count=10, attributes={"heating_type": "gas"}),),
            metadata={"year": 2024},
        )
        state = self._make_state(
            n=1, chosen=["heat_pump"], existing_vintage=existing
        )
        result = step.execute(2025, state)

        vintage = result.data["vintage_heating"]
        assert isinstance(vintage, VintageState)
        assert len(vintage.cohorts) == 2
        # Old cohort preserved
        assert vintage.cohorts[0].age == 1
        assert vintage.cohorts[0].count == 10
        # New cohort appended
        assert vintage.cohorts[1].age == 0
        assert vintage.cohorts[1].count == 1

    def test_no_vintage_when_all_keep(self) -> None:
        """AC-8: no vintage when all keep_current and no existing vintage."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        state = self._make_state(n=2, chosen=["keep_current", "keep_current"])
        result = step.execute(2025, state)
        assert "vintage_heating" not in result.data

    def test_state_immutability(self) -> None:
        """AC-9: original state not modified."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        state = self._make_state(n=1, chosen=["heat_pump"])
        original_data_id = id(state.data)
        result = step.execute(2025, state)
        assert id(result.data) != original_data_id
        assert result is not state

    def test_metadata_extension(self) -> None:
        """AC-9: metadata extended with heating switch counts."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        state = self._make_state(
            n=3, chosen=["keep_current", "heat_pump", "gas_boiler"]
        )
        result = step.execute(2025, state)
        meta = result.data[DISCRETE_CHOICE_METADATA_KEY]
        assert meta["heating_n_switchers"] == 2  # type: ignore[index]
        assert meta["heating_n_keepers"] == 1  # type: ignore[index]
        assert isinstance(meta["heating_per_alternative_counts"], dict)  # type: ignore[index]
        assert meta["heating_per_alternative_counts"]["heat_pump"] == 1  # type: ignore[index]
        assert meta["heating_per_alternative_counts"]["gas_boiler"] == 1  # type: ignore[index]

    def test_metadata_preserves_existing_keys(self) -> None:
        """AC-9: existing metadata keys (e.g., vehicle domain) are preserved."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        state = self._make_state(
            n=1,
            chosen=["keep_current"],
            existing_metadata={
                "vehicle_n_switchers": 5,
                "vehicle_n_keepers": 10,
                "domain_name": "vehicle",
            },
        )
        result = step.execute(2025, state)
        meta = result.data[DISCRETE_CHOICE_METADATA_KEY]
        # Vehicle keys preserved
        assert meta["vehicle_n_switchers"] == 5  # type: ignore[index]
        assert meta["vehicle_n_keepers"] == 10  # type: ignore[index]
        # Heating keys added
        assert meta["heating_n_switchers"] == 0  # type: ignore[index]
        assert meta["heating_n_keepers"] == 1  # type: ignore[index]

    def test_missing_choice_result_raises(self) -> None:
        """Edge case: missing ChoiceResult raises DiscreteChoiceError."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        state = YearState(
            year=2025,
            data={"population_data": PopulationData(tables={}, metadata={})},
        )
        with pytest.raises(DiscreteChoiceError, match="ChoiceResult"):
            step.execute(2025, state)

    def test_missing_population_raises(self) -> None:
        """Edge case: missing PopulationData raises DiscreteChoiceError."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
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

    def test_non_dict_metadata_raises(self) -> None:
        """Edge case: non-dict metadata raises DiscreteChoiceError."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        state = self._make_state(n=1, chosen=["keep_current"])
        corrupted_data = dict(state.data)
        corrupted_data[DISCRETE_CHOICE_METADATA_KEY] = "not_a_dict"
        corrupted_state = _replace(state, data=corrupted_data)
        with pytest.raises(DiscreteChoiceError, match="Expected dict"):
            step.execute(2025, corrupted_state)

    def test_vintage_asset_class_mismatch_raises(self) -> None:
        """Edge case: existing vintage with wrong asset_class raises DiscreteChoiceError."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        wrong_vintage = VintageState(
            asset_class="vehicle",
            cohorts=(VintageCohort(age=1, count=5, attributes={"type": "petrol"}),),
            metadata={},
        )
        state = self._make_state(
            n=1, chosen=["heat_pump"], existing_vintage=wrong_vintage
        )
        with pytest.raises(DiscreteChoiceError, match="asset_class"):
            step.execute(2025, state)

    def test_entity_key_not_found_raises(self) -> None:
        """Edge case: entity_key not in population raises DiscreteChoiceError."""
        config = default_heating_domain_config()
        population = PopulationData(
            tables={"other_entity": pa.table({"x": pa.array([1])})},
            metadata={},
        )
        alt_ids = tuple(a.id for a in config.alternatives)
        choice_result = ChoiceResult(
            chosen=pa.array(["keep_current"]),
            probabilities=pa.table({
                aid: pa.array([1.0 / 5])
                for aid in alt_ids
            }),
            utilities=pa.table({
                aid: pa.array([-1.0])
                for aid in alt_ids
            }),
            alternative_ids=alt_ids,
            seed=42,
        )
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        state = YearState(
            year=2025,
            data={
                "population_data": population,
                DISCRETE_CHOICE_RESULT_KEY: choice_result,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
        )
        with pytest.raises(DiscreteChoiceError, match="Entity key"):
            step.execute(2025, state)


# ============================================================================
# TestVintageIntegration (AC-8)
# ============================================================================


class TestVintageIntegration:
    """Tests for vintage cohort integration behavior."""

    def test_new_vintage_state_created(self) -> None:
        """AC-8: new VintageState created when none exists."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        alt_ids = tuple(a.id for a in config.alternatives)

        table = pa.table({
            "household_id": pa.array([0], type=pa.int64()),
            "heating_type": pa.array(["gas"]),
            "heating_age": pa.array([10], type=pa.int64()),
            "heating_emissions_kgco2_kwh": pa.array([0.227]),
        })
        population = PopulationData(tables={"menage": table}, metadata={})
        choice_result = ChoiceResult(
            chosen=pa.array(["heat_pump"]),
            probabilities=pa.table({
                aid: pa.array([1.0 / 5]) for aid in alt_ids
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
        vintage = result.data["vintage_heating"]
        assert isinstance(vintage, VintageState)
        assert vintage.asset_class == "heating"
        assert len(vintage.cohorts) == 1
        assert vintage.cohorts[0] == VintageCohort(
            age=0, count=1, attributes={"heating_type": "heat_pump"}
        )

    def test_cohorts_correct_age_zero(self) -> None:
        """AC-8: all new cohorts have age=0."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        alt_ids = tuple(a.id for a in config.alternatives)

        table = pa.table({
            "household_id": pa.array([0, 1, 2], type=pa.int64()),
            "heating_type": pa.array(["gas"] * 3),
            "heating_age": pa.array([10] * 3, type=pa.int64()),
            "heating_emissions_kgco2_kwh": pa.array([0.227] * 3),
        })
        population = PopulationData(tables={"menage": table}, metadata={})
        choice_result = ChoiceResult(
            chosen=pa.array(["gas_boiler", "heat_pump", "electric"]),
            probabilities=pa.table({
                aid: pa.array([1.0 / 5] * 3) for aid in alt_ids
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
        vintage = result.data["vintage_heating"]
        assert isinstance(vintage, VintageState)
        for cohort in vintage.cohorts:
            assert cohort.age == 0

    def test_cohorts_appended_to_existing(self) -> None:
        """AC-8: new cohorts are appended, not replacing existing."""
        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)
        step = HeatingStateUpdateStep(domain=domain)
        alt_ids = tuple(a.id for a in config.alternatives)

        existing = VintageState(
            asset_class="heating",
            cohorts=(
                VintageCohort(age=2, count=5, attributes={"heating_type": "gas"}),
                VintageCohort(age=1, count=3, attributes={"heating_type": "electric"}),
            ),
            metadata={"year": 2023},
        )

        table = pa.table({
            "household_id": pa.array([0, 1], type=pa.int64()),
            "heating_type": pa.array(["gas", "gas"]),
            "heating_age": pa.array([10, 15], type=pa.int64()),
            "heating_emissions_kgco2_kwh": pa.array([0.227, 0.227]),
        })
        population = PopulationData(tables={"menage": table}, metadata={})
        choice_result = ChoiceResult(
            chosen=pa.array(["heat_pump", "heat_pump"]),
            probabilities=pa.table({
                aid: pa.array([1.0 / 5] * 2) for aid in alt_ids
            }),
            utilities=pa.table({
                aid: pa.array([-1.0] * 2) for aid in alt_ids
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
                "vintage_heating": existing,
            },
            seed=42,
        )
        result = step.execute(2025, state)
        vintage = result.data["vintage_heating"]
        assert isinstance(vintage, VintageState)
        # 2 existing + 1 new
        assert len(vintage.cohorts) == 3
        assert vintage.cohorts[0].age == 2
        assert vintage.cohorts[1].age == 1
        assert vintage.cohorts[2].age == 0
        assert vintage.cohorts[2].count == 2


# ============================================================================
# Integration test: full pipeline (AC: all)
# ============================================================================


class TestHeatingPipelineIntegration:
    """Integration test: DiscreteChoiceStep → LogitChoiceStep → HeatingStateUpdateStep."""

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

        config = default_heating_domain_config()
        domain = HeatingInvestmentDomain(config)

        def heating_compute_fn(
            population: PopulationData,
            policy: PolicyConfig,
            period: int,
        ) -> pa.Table:
            """Compute total_heating_cost based on heating attributes."""
            entity_key = sorted(population.tables.keys())[0]
            table = population.tables[entity_key]
            emissions = table.column("heating_emissions_kgco2_kwh").to_pylist()
            ages = table.column("heating_age").to_pylist()
            costs = [e * 1000.0 + a * 200.0 for e, a in zip(emissions, ages)]
            result_cols: dict[str, pa.Array] = {
                "total_heating_cost": pa.array(costs),
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
            version_string="mock-heating-1.0",
            compute_fn=heating_compute_fn,
        )
        policy = PolicyConfig(policy=CarbonTaxParameters(rate_schedule={2025: 44.6}), name="test")
        taste = TasteParameters(beta_cost=-0.001)

        dc_step = DiscreteChoiceStep(
            adapter=adapter, domain=domain, policy=policy
        )
        logit_step = LogitChoiceStep(taste_parameters=taste)
        update_step = HeatingStateUpdateStep(domain=domain)

        # Build population
        table = pa.table({
            "household_id": pa.array([0, 1, 2], type=pa.int64()),
            "income": pa.array([30000.0, 45000.0, 60000.0]),
            "heating_type": pa.array(["gas", "electric", "gas"]),
            "heating_age": pa.array([15, 8, 3], type=pa.int64()),
            "heating_emissions_kgco2_kwh": pa.array([0.227, 0.057, 0.227]),
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
        assert "heating_n_switchers" in meta  # type: ignore[operator]
        assert "heating_n_keepers" in meta  # type: ignore[operator]
        assert "heating_per_alternative_counts" in meta  # type: ignore[operator]
        assert meta["heating_n_switchers"] + meta["heating_n_keepers"] == 3  # type: ignore[index]

        # Population still has 3 rows
        updated_pop = state.data["population_data"]
        assert isinstance(updated_pop, PopulationData)
        assert updated_pop.tables["menage"].num_rows == 3


# ============================================================================
# Sequential domain test (AC-11)
# ============================================================================


class TestSequentialDomainExecution:
    """AC-11: Vehicle pipeline followed by heating pipeline."""

    def test_heating_receives_vehicle_updated_population(self) -> None:
        """Heating step receives population with vehicle updates applied."""
        from reformlab.computation.mock_adapter import MockAdapter
        from reformlab.computation.types import PolicyConfig
        from reformlab.discrete_choice.expansion import (
            TRACKING_COL_ALTERNATIVE_ID,
            TRACKING_COL_ORIGINAL_INDEX,
        )
        from reformlab.discrete_choice.logit import LogitChoiceStep
        from reformlab.discrete_choice.step import DiscreteChoiceStep
        from reformlab.discrete_choice.vehicle import (
            VehicleInvestmentDomain,
            VehicleStateUpdateStep,
            default_vehicle_domain_config,
        )
        from reformlab.templates.schema import CarbonTaxParameters

        # ---- Vehicle domain setup ----
        v_config = default_vehicle_domain_config()
        v_domain = VehicleInvestmentDomain(v_config)

        def vehicle_compute_fn(
            population: PopulationData,
            policy: PolicyConfig,
            period: int,
        ) -> pa.Table:
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

        v_adapter = MockAdapter(
            version_string="mock-vehicle-1.0", compute_fn=vehicle_compute_fn
        )

        # ---- Heating domain setup ----
        h_config = default_heating_domain_config()
        h_domain = HeatingInvestmentDomain(h_config)

        def heating_compute_fn(
            population: PopulationData,
            policy: PolicyConfig,
            period: int,
        ) -> pa.Table:
            entity_key = sorted(population.tables.keys())[0]
            table = population.tables[entity_key]
            emissions = table.column("heating_emissions_kgco2_kwh").to_pylist()
            ages = table.column("heating_age").to_pylist()
            costs = [e * 1000.0 + a * 200.0 for e, a in zip(emissions, ages)]
            result_cols: dict[str, pa.Array] = {
                "total_heating_cost": pa.array(costs),
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

        h_adapter = MockAdapter(
            version_string="mock-heating-1.0", compute_fn=heating_compute_fn
        )

        policy = PolicyConfig(policy=CarbonTaxParameters(rate_schedule={2025: 44.6}), name="test")
        taste = TasteParameters(beta_cost=-0.001)

        # Vehicle pipeline steps
        v_dc_step = DiscreteChoiceStep(
            adapter=v_adapter,
            domain=v_domain,
            policy=policy,
            name="discrete_choice_vehicle",
        )
        v_logit_step = LogitChoiceStep(
            taste_parameters=taste,
            name="logit_choice_vehicle",
            depends_on=("discrete_choice_vehicle",),
        )
        v_update_step = VehicleStateUpdateStep(
            domain=v_domain,
            name="vehicle_state_update",
            depends_on=("logit_choice_vehicle",),
        )

        # Heating pipeline steps
        h_dc_step = DiscreteChoiceStep(
            adapter=h_adapter,
            domain=h_domain,
            policy=policy,
            name="discrete_choice_heating",
            depends_on=("vehicle_state_update",),
        )
        h_logit_step = LogitChoiceStep(
            taste_parameters=taste,
            name="logit_choice_heating",
            depends_on=("discrete_choice_heating",),
        )
        h_update_step = HeatingStateUpdateStep(
            domain=h_domain,
            name="heating_state_update",
            depends_on=("logit_choice_heating",),
        )

        # Build population with both vehicle and heating columns
        table = pa.table({
            "household_id": pa.array([0, 1, 2], type=pa.int64()),
            "income": pa.array([30000.0, 45000.0, 60000.0]),
            "vehicle_type": pa.array(["petrol", "diesel", "petrol"]),
            "vehicle_age": pa.array([5, 8, 3], type=pa.int64()),
            "vehicle_emissions_gkm": pa.array([150.0, 130.0, 120.0]),
            "heating_type": pa.array(["gas", "electric", "gas"]),
            "heating_age": pa.array([15, 8, 3], type=pa.int64()),
            "heating_emissions_kgco2_kwh": pa.array([0.227, 0.057, 0.227]),
        })
        population = PopulationData(tables={"menage": table}, metadata={})

        # Use a fixed seed for deterministic behavior
        state = YearState(
            year=2025,
            data={"population_data": population},
            seed=42,
        )

        # Execute vehicle pipeline
        state = v_dc_step.execute(2025, state)
        state = v_logit_step.execute(2025, state)
        state = v_update_step.execute(2025, state)

        # Verify vehicle updates are applied before heating starts
        pop_after_vehicle = state.data["population_data"]
        assert isinstance(pop_after_vehicle, PopulationData)
        assert pop_after_vehicle.tables["menage"].num_rows == 3

        # Capture vehicle-mutated attribute values to verify they reach heating pipeline
        vehicle_types_after_vehicle = (
            pop_after_vehicle.tables["menage"].column("vehicle_type").to_pylist()
        )
        vehicle_ages_after_vehicle = (
            pop_after_vehicle.tables["menage"].column("vehicle_age").to_pylist()
        )

        # Vehicle metadata is present
        meta = state.data[DISCRETE_CHOICE_METADATA_KEY]
        assert "vehicle_n_switchers" in meta  # type: ignore[operator]
        assert "vehicle_n_keepers" in meta  # type: ignore[operator]

        # Execute heating pipeline (receives vehicle-updated population)
        state = h_dc_step.execute(2025, state)
        state = h_logit_step.execute(2025, state)
        state = h_update_step.execute(2025, state)

        # Validate final state
        final_pop = state.data["population_data"]
        assert isinstance(final_pop, PopulationData)
        assert final_pop.tables["menage"].num_rows == 3

        # Verify vehicle-mutated attributes survived the heating pipeline
        final_vehicle_types = final_pop.tables["menage"].column("vehicle_type").to_pylist()
        final_vehicle_ages = final_pop.tables["menage"].column("vehicle_age").to_pylist()
        assert final_vehicle_types == vehicle_types_after_vehicle, (
            "Vehicle type mutations lost during heating pipeline"
        )
        assert final_vehicle_ages == vehicle_ages_after_vehicle, (
            "Vehicle age mutations lost during heating pipeline"
        )

        # Heating metadata is present after heating pipeline
        final_meta = state.data[DISCRETE_CHOICE_METADATA_KEY]
        assert "heating_n_switchers" in final_meta  # type: ignore[operator]
        assert "heating_n_keepers" in final_meta  # type: ignore[operator]
        assert final_meta["heating_n_switchers"] + final_meta["heating_n_keepers"] == 3  # type: ignore[index]

        # Vehicle metadata keys are preserved across domains (AC-9 merge semantics)
        assert "vehicle_n_switchers" in final_meta  # type: ignore[operator]
        assert "vehicle_n_keepers" in final_meta  # type: ignore[operator]

        # Both vintage states exist independently under separate keys
        if "vintage_vehicle" in state.data:
            v_vintage = state.data["vintage_vehicle"]
            assert isinstance(v_vintage, VintageState)
            assert v_vintage.asset_class == "vehicle"
        if "vintage_heating" in state.data:
            h_vintage = state.data["vintage_heating"]
            assert isinstance(h_vintage, VintageState)
            assert h_vintage.asset_class == "heating"
