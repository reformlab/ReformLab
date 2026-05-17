# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for discrete choice domain utils writeback functionality.

Story 28.3: Wire DiscreteChoiceStep outputs back into population frame.
Tests for incumbent column writeback, multi-year transitions, and type validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pyarrow as pa
import pytest

from reformlab.computation.types import PopulationData
from reformlab.discrete_choice.domain_utils import apply_choices_to_population
from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.types import Alternative, ChoiceResult
from reformlab.orchestrator.types import YearState

if TYPE_CHECKING:
    from reformlab.discrete_choice.types import Alternative


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def heating_alternatives() -> tuple[Alternative, ...]:
    """Standard heating alternatives for testing."""
    return (
        Alternative(id="keep_current", name="Keep Current", attributes={}),
        Alternative(
            id="heat_pump_air",
            name="Heat Pump",
            attributes={"heating_type": "heat_pump", "heating_age": 0},
        ),
        Alternative(
            id="condensing_boiler",
            name="Gas Boiler",
            attributes={"heating_type": "gas", "heating_age": 0},
        ),
    )


@pytest.fixture
def vehicle_alternatives() -> tuple[Alternative, ...]:
    """Standard vehicle alternatives for testing."""
    return (
        Alternative(id="keep_current", name="Keep Current", attributes={}),
        Alternative(id="ev", name="Electric", attributes={"vehicle_type": "ev", "vehicle_age": 0}),
        Alternative(id="petrol", name="Petrol", attributes={"vehicle_type": "petrol", "vehicle_age": 0}),
    )


# ============================================================================
# Task 1.1: domain_key parameter (backward compatibility)
# ============================================================================


class TestApplyChoicesBackwardCompatibility:
    """Test backward compatibility when domain_key is not provided."""

    # Story 28.3 / Task 1.1 / AC-11: Backward compatibility - no domain_key parameter
    def test_apply_choices_without_domain_key_no_incumbent_column(self, heating_alternatives):
        """Calling apply_choices_to_population without domain_key does NOT create incumbent column."""
        # Setup: Population with existing heating system column
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [0, 1, 2],
                    "heating_system": ["gas_boiler", "oil_boiler", "electric"],
                })
            },
            metadata={},
        )

        # Choice result: all households choose heat pump
        # Note: Single alternative must have probability = 1.0 (validation)
        choice_result = ChoiceResult(
            chosen=pa.array(["heat_pump_air"] * 3),
            probabilities=pa.table({"heat_pump_air": [1.0, 1.0, 1.0]}),
            utilities=pa.table({"heat_pump_air": [0.0, 0.0, 0.0]}),
            alternative_ids=("heat_pump_air",),
            seed=42,
        )

        # Apply choices WITHOUT domain_key (legacy behavior)
        result = apply_choices_to_population(
            population,
            choice_result,
            heating_alternatives,
            "menage",
            # domain_key not provided (None default)
        )

        # Assert NO incumbent_heating column created (backward compatible)
        assert "incumbent_heating" not in result.tables["menage"].column_names

        # Assert existing attribute columns still written
        assert "heating_system" in result.tables["menage"].column_names
        assert result.tables["menage"].column("heating_type").to_pylist() == ["heat_pump"] * 3


# ============================================================================
# Task 1.2-1.7: Incumbent column writeback
# ============================================================================


class TestApplyChoicesIncumbentWriteback:
    """Test incumbent column writeback functionality."""

    # Story 28.3 / Task 1.2 / AC-1: New incumbent column creation
    def test_incumbent_column_created_when_missing(self, heating_alternatives):
        """Incumbent column is created with dictionary encoding when missing."""
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [0, 1, 2],
                })
            },
            metadata={},
        )

        # Probabilities must sum to 1.0 per row
        choice_result = ChoiceResult(
            chosen=pa.array(["heat_pump_air", "condensing_boiler", "keep_current"]),
            probabilities=pa.table({
                "keep_current": [0.0, 0.0, 0.8],
                "heat_pump_air": [0.9, 0.3, 0.1],
                "condensing_boiler": [0.1, 0.7, 0.1],
            }),
            utilities=pa.table({
                "keep_current": [0.0, 0.0, 0.0],
                "heat_pump_air": [0.0, 0.0, 0.0],
                "condensing_boiler": [0.0, 0.0, 0.0],
            }),
            alternative_ids=("keep_current", "heat_pump_air", "condensing_boiler"),
            seed=42,
        )

        result = apply_choices_to_population(
            population,
            choice_result,
            heating_alternatives,
            "menage",
            domain_key="heating",
        )

        # Assert incumbent_heating column created
        assert "incumbent_heating" in result.tables["menage"].column_names
        incumbent_col = result.tables["menage"].column("incumbent_heating")

        # Assert dictionary encoding
        assert isinstance(incumbent_col.type, pa.DictionaryType)
        assert incumbent_col.type.index_type == pa.int32()
        assert incumbent_col.type.value_type == pa.utf8()

        # Assert values written correctly
        assert incumbent_col.to_pylist() == ["heat_pump_air", "condensing_boiler", "keep_current"]

    # Story 28.3 / Task 1.3 / AC-3: Preserve dictionary encoding when column exists
    def test_incumbent_column_preserves_dictionary_encoding(self, heating_alternatives):
        """When incumbent column exists, preserve its dictionary encoding."""
        # Create population with existing dictionary-encoded incumbent column
        existing_dict = pa.dictionary(pa.int32(), pa.utf8())
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [0, 1, 2],
                    "incumbent_heating": pa.array(
                        ["gas_boiler", "oil_boiler", "electric"],
                        type=existing_dict,
                    ),
                })
            },
            metadata={},
        )

        choice_result = ChoiceResult(
            chosen=pa.array(["heat_pump_air", "condensing_boiler", "keep_current"]),
            probabilities=pa.table({
                "keep_current": [0.0, 0.0, 0.8],
                "heat_pump_air": [0.9, 0.3, 0.1],
                "condensing_boiler": [0.1, 0.7, 0.1],
            }),
            utilities=pa.table({
                "keep_current": [0.0, 0.0, 0.0],
                "heat_pump_air": [0.0, 0.0, 0.0],
                "condensing_boiler": [0.0, 0.0, 0.0],
            }),
            alternative_ids=("keep_current", "heat_pump_air", "condensing_boiler"),
            seed=42,
        )

        result = apply_choices_to_population(
            population,
            choice_result,
            heating_alternatives,
            "menage",
            domain_key="heating",
        )

        # Assert dictionary encoding preserved
        incumbent_col = result.tables["menage"].column("incumbent_heating")
        assert isinstance(incumbent_col.type, pa.DictionaryType)
        assert incumbent_col.type.index_type == pa.int32()
        assert incumbent_col.type.value_type == pa.utf8()

        # Assert values updated correctly
        assert incumbent_col.to_pylist() == ["heat_pump_air", "condensing_boiler", "electric"]

    # Story 28.3 / Task 1.6 / AC-2: keep_current skip rule - preserves actual technology
    def test_keep_current_skip_rule_preserves_actual_technology(self, heating_alternatives):
        """When chosen is 'keep_current', preserve existing incumbent (not 'keep_current' string)."""
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [0, 1, 2],
                    "incumbent_heating": pa.array(
                        ["gas_boiler", "heat_pump_air", "electric"],
                        type=pa.dictionary(pa.int32(), pa.utf8())
                    ),
                })
            },
            metadata={},
        )

        choice_result = ChoiceResult(
            chosen=pa.array(["keep_current", "keep_current", "condensing_boiler"]),
            probabilities=pa.table({
                "keep_current": [0.7, 0.8, 0.1],
                "condensing_boiler": [0.3, 0.2, 0.9],
            }),
            utilities=pa.table({
                "keep_current": [0.0, 0.0, 0.0],
                "condensing_boiler": [0.0, 0.0, 0.0],
            }),
            alternative_ids=("keep_current", "condensing_boiler"),  # Must match table column order
            seed=42,
        )

        result = apply_choices_to_population(
            population,
            choice_result,
            heating_alternatives,
            "menage",
            domain_key="heating",
        )

        # Assert keep_current preserves actual technology values
        incumbents = result.tables["menage"].column("incumbent_heating").to_pylist()
        assert incumbents[0] == "gas_boiler"  # Kept gas_boiler
        assert incumbents[1] == "heat_pump_air"  # Kept heat_pump_air
        assert incumbents[2] == "condensing_boiler"  # Switched to condensing_boiler

    # Story 28.3 / Task 1.8 / AC-8: Type validation - wrong type raises DiscreteChoiceError
    def test_incumbent_column_wrong_type_raises_error(self, heating_alternatives):
        """Incumbent column with wrong type (plain string, not dictionary) raises DiscreteChoiceError."""
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [0, 1, 2],
                    "incumbent_heating": pa.array(
                        ["gas", "oil", "electric"],
                        type=pa.utf8(),
                    ),  # NOT dictionary
                })
            },
            metadata={},
        )

        choice_result = ChoiceResult(
            chosen=pa.array(["heat_pump_air"] * 3),
            probabilities=pa.table({"heat_pump_air": [1.0, 1.0, 1.0]}),
            utilities=pa.table({"heat_pump_air": [0.0, 0.0, 0.0]}),
            alternative_ids=("heat_pump_air",),
            seed=42,
        )

        with pytest.raises(DiscreteChoiceError, match="wrong type.*Expected pa.dictionary"):
            apply_choices_to_population(
                population,
                choice_result,
                heating_alternatives,
                "menage",
                domain_key="heating",
            )

    # Story 28.3 / Task 1.8: Wrong index type validation
    def test_incumbent_column_wrong_index_type_raises_error(self, heating_alternatives):
        """Incumbent column with wrong dictionary index type (not int32) raises DiscreteChoiceError."""
        # Create population with int8 dictionary (wrong index type)
        wrong_dict = pa.dictionary(pa.int8(), pa.utf8())
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [0, 1, 2],
                    "incumbent_heating": pa.array(["gas", "oil", "electric"], type=wrong_dict),
                })
            },
            metadata={},
        )

        choice_result = ChoiceResult(
            chosen=pa.array(["heat_pump_air"] * 3),
            probabilities=pa.table({"heat_pump_air": [1.0, 1.0, 1.0]}),
            utilities=pa.table({"heat_pump_air": [0.0, 0.0, 0.0]}),
            alternative_ids=("heat_pump_air",),
            seed=42,
        )

        with pytest.raises(DiscreteChoiceError, match="wrong dictionary index type.*Expected pa.int32"):
            apply_choices_to_population(
                population,
                choice_result,
                heating_alternatives,
                "menage",
                domain_key="heating",
            )


# ============================================================================
# Task 1.7: Multi-domain writeback
# ============================================================================


class TestMultiDomainWriteback:
    """Test multi-domain writeback without clobbering."""

    # Story 28.3 / Task 1.7 / AC-4: Multi-domain writeback without clobbering
    def test_multi_domain_writeback_no_clobbering(self, heating_alternatives, vehicle_alternatives):
        """Applying heating and vehicle choices does not clobber each other's incumbent columns."""
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [0, 1, 2],
                })
            },
            metadata={},
        )

        heating_choice = ChoiceResult(
            chosen=pa.array(["heat_pump_air", "condensing_boiler", "heat_pump_air"]),
            probabilities=pa.table({
                "condensing_boiler": [0.1, 0.7, 0.1],
                "heat_pump_air": [0.9, 0.3, 0.9],
            }),
            utilities=pa.table({
                "condensing_boiler": [0.0, 0.0, 0.0],
                "heat_pump_air": [0.0, 0.0, 0.0],
            }),
            alternative_ids=("condensing_boiler", "heat_pump_air"),
            seed=42,
        )

        vehicle_choice = ChoiceResult(
            chosen=pa.array(["ev", "petrol", "ev"]),
            probabilities=pa.table({
                "ev": [0.8, 0.2, 0.8],
                "petrol": [0.2, 0.8, 0.2],
            }),
            utilities=pa.table({
                "ev": [0.0, 0.0, 0.0],
                "petrol": [0.0, 0.0, 0.0],
            }),
            alternative_ids=("ev", "petrol"),
            seed=42,
        )

        # Apply heating choices first
        result_after_heating = apply_choices_to_population(
            population,
            heating_choice,
            heating_alternatives,
            "menage",
            domain_key="heating",
        )

        # Apply vehicle choices (must not clobber heating incumbent)
        result_final = apply_choices_to_population(
            result_after_heating,
            vehicle_choice,
            vehicle_alternatives,
            "menage",
            domain_key="vehicle",
        )

        # Assert both incumbent columns present
        assert "incumbent_heating" in result_final.tables["menage"].column_names
        assert "incumbent_vehicle" in result_final.tables["menage"].column_names

        # Assert heating incumbents correct
        heating_incumbents = result_final.tables["menage"].column("incumbent_heating").to_pylist()
        assert heating_incumbents == ["heat_pump_air", "condensing_boiler", "heat_pump_air"]

        # Assert vehicle incumbents correct
        vehicle_incumbents = result_final.tables["menage"].column("incumbent_vehicle").to_pylist()
        assert vehicle_incumbents == ["ev", "petrol", "ev"]


# ============================================================================
# Task 1.6 / AC-2: Multi-year incumbents carry forward
# ============================================================================


class TestMultiYearIncumbentWriteback:
    """Test multi-year execution where incumbents carry forward."""

    # Story 28.3 / AC-2: Multi-year incumbents carry forward correctly
    def test_multi_year_incumbent_writeback(self, heating_alternatives):
        """Incumbents from year 1 are preserved as starting point for year 2."""
        # Year 1: Start with keep_current, choose heat_pump_air
        pop_year1 = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [0, 1, 2],
                    "incumbent_heating": pa.array(
                        ["keep_current", "keep_current", "keep_current"],
                        type=pa.dictionary(pa.int32(), pa.utf8())
                    ),
                })
            },
            metadata={},
        )

        choice_result_year1 = ChoiceResult(
            chosen=pa.array(["heat_pump_air", "condensing_boiler", "keep_current"]),
            probabilities=pa.table({
                "keep_current": [0.0, 0.0, 0.8],
                "heat_pump_air": [0.9, 0.3, 0.1],
                "condensing_boiler": [0.1, 0.7, 0.1],
            }),
            utilities=pa.table({
                "keep_current": [0.0, 0.0, 0.0],
                "heat_pump_air": [0.0, 0.0, 0.0],
                "condensing_boiler": [0.0, 0.0, 0.0],
            }),
            alternative_ids=("keep_current", "heat_pump_air", "condensing_boiler"),
            seed=42,
        )

        pop_year1_updated = apply_choices_to_population(
            pop_year1,
            choice_result_year1,
            heating_alternatives,
            "menage",
            domain_key="heating",
        )

        # Assert year 1 incumbents written
        incumbents_year1 = pop_year1_updated.tables["menage"].column("incumbent_heating").to_pylist()
        assert incumbents_year1 == ["heat_pump_air", "condensing_boiler", "keep_current"]

        # Year 2: Start with heat_pump_air as incumbent for household 0
        # Simulate by passing pop_year1_updated as input
        choice_result_year2 = ChoiceResult(
            chosen=pa.array(["keep_current", "heat_pump_air", "condensing_boiler"]),
            probabilities=pa.table({
                "condensing_boiler": [0.3, 0.8, 0.9],
                "keep_current": [0.7, 0.2, 0.1],
            }),
            utilities=pa.table({
                "condensing_boiler": [0.0, 0.0, 0.0],
                "keep_current": [0.0, 0.0, 0.0],
            }),
            alternative_ids=("condensing_boiler", "keep_current"),
            seed=43,
        )

        pop_year2_updated = apply_choices_to_population(
            pop_year1_updated,
            choice_result_year2,
            heating_alternatives,
            "menage",
            domain_key="heating",
        )

        # Assert household 0 keeps heat pump from year 1
        incumbents_year2 = pop_year2_updated.tables["menage"].column("incumbent_heating").to_pylist()
        assert incumbents_year2[0] == "heat_pump_air"  # Kept heat pump from year 1
        assert incumbents_year2[1] == "heat_pump_air"  # Switched to heat pump
        assert incumbents_year2[2] == "condensing_boiler"  # Switched to condensing boiler


# ============================================================================
# Task 1.6 / AC-7: Eligibility invariance
# ============================================================================


class TestEligibilityInvariance:
    """Test that ineligible households keep their original incumbent technology."""

    # Story 28.3 / AC-7: Eligibility invariance - ineligible households keep original technology
    def test_eligibility_invariance(self, heating_alternatives):
        """Ineligible households (who receive default_choice='keep_current') keep original technology."""
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                    "incumbent_heating": pa.array(
                        ["condensing_boiler"] * 10,
                        type=pa.dictionary(pa.int32(), pa.utf8())
                    ),
                })
            },
            metadata={},
        )

        # After EligibilityMergeStep: ChoiceResult has 10 values (N_total)
        # Eligible households (indices 0,1,3,5,6,8,9) chose heat_pump_air
        # Ineligible households (indices 2,4,7) received default_choice="keep_current"
        choice_result = ChoiceResult(
            chosen=pa.array([
                "heat_pump_air", "heat_pump_air", "keep_current",  # 0,1,2
                "heat_pump_air", "keep_current", "heat_pump_air",  # 3,4,5
                "heat_pump_air", "keep_current", "heat_pump_air", "heat_pump_air",  # 6,7,8,9
            ]),
            probabilities=pa.table({
                "heat_pump_air": [0.9, 0.9, 0.1, 0.9, 0.1, 0.9, 0.9, 0.1, 0.9, 0.9],
                "keep_current": [0.1, 0.1, 0.9, 0.1, 0.9, 0.1, 0.1, 0.9, 0.1, 0.1],
            }),
            utilities=pa.table({
                "heat_pump_air": [0.0] * 10,
                "keep_current": [0.0] * 10,
            }),
            alternative_ids=("heat_pump_air", "keep_current"),
            seed=42,
        )

        updated = apply_choices_to_population(
            population,
            choice_result,
            heating_alternatives,
            "menage",
            domain_key="heating",
        )

        incumbents = updated.tables["menage"].column("incumbent_heating").to_pylist()
        # Eligible households changed
        assert incumbents[0] == "heat_pump_air"
        assert incumbents[1] == "heat_pump_air"
        # Ineligible households (2,4,7) kept original technology
        assert incumbents[2] == "condensing_boiler"
        assert incumbents[4] == "condensing_boiler"
        assert incumbents[7] == "condensing_boiler"


# ============================================================================
# Integration tests for StateUpdateStep
# ============================================================================


class TestStateUpdateStepIntegration:
    """Integration tests for VehicleStateUpdateStep and HeatingStateUpdateStep."""

    # Story 28.3 / Task 2.7: Concurrent StateUpdateStep execution
    def test_concurrent_state_update_steps(self, heating_alternatives, vehicle_alternatives):
        """Vehicle and Heating StateUpdateSteps execute in same year without clobbering."""
        from reformlab.discrete_choice.heating import (
            HeatingDomainConfig,
            HeatingInvestmentDomain,
            HeatingStateUpdateStep,
        )
        from reformlab.discrete_choice.vehicle import (
            VehicleDomainConfig,
            VehicleInvestmentDomain,
            VehicleStateUpdateStep,
        )

        # Setup: population with both incumbent columns
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [0, 1, 2],
                    "incumbent_vehicle": pa.array(
                        ["gasoline", "diesel", "keep_current"],
                        type=pa.dictionary(pa.int32(), pa.utf8())
                    ),
                    "incumbent_heating": pa.array(
                        ["gas_boiler", "condensing_boiler", "keep_current"],
                        type=pa.dictionary(pa.int32(), pa.utf8())
                    ),
                })
            },
            metadata={},
        )

        # Create state with population and choice results
        vehicle_choice = ChoiceResult(
            chosen=pa.array(["ev", "petrol", "keep_current"]),
            probabilities=pa.table({
                "ev": [0.8, 0.2, 0.1],
                "keep_current": [0.0, 0.0, 0.8],
                "petrol": [0.2, 0.8, 0.1],
            }),
            utilities=pa.table({
                "ev": [0.0, 0.0, 0.0],
                "keep_current": [0.0, 0.0, 0.0],
                "petrol": [0.0, 0.0, 0.0],
            }),
            alternative_ids=("ev", "keep_current", "petrol"),  # Must match table column order
            seed=42,
        )

        heating_choice = ChoiceResult(
            chosen=pa.array(["heat_pump_air", "keep_current", "condensing_boiler"]),
            probabilities=pa.table({
                "condensing_boiler": [0.1, 0.1, 0.8],
                "heat_pump_air": [0.9, 0.1, 0.2],
                "keep_current": [0.0, 0.8, 0.0],
            }),
            utilities=pa.table({
                "condensing_boiler": [0.0, 0.0, 0.0],
                "heat_pump_air": [0.0, 0.0, 0.0],
                "keep_current": [0.0, 0.0, 0.0],
            }),
            # Must match table column order
            alternative_ids=("condensing_boiler", "heat_pump_air", "keep_current"),
            seed=43,
        )

        # Create domains and steps
        vehicle_domain = VehicleInvestmentDomain(VehicleDomainConfig(alternatives=vehicle_alternatives))
        heating_domain = HeatingInvestmentDomain(HeatingDomainConfig(alternatives=heating_alternatives))

        vehicle_step = VehicleStateUpdateStep(vehicle_domain)
        heating_step = HeatingStateUpdateStep(heating_domain)

        # Create initial state
        state = YearState(year=2025, data={
            "population_data": population,
            "discrete_choice_result": vehicle_choice,  # Will be overwritten
        })

        # Execute VehicleStateUpdateStep
        from dataclasses import replace
        state_for_vehicle = replace(
            state,
            data={**state.data, "discrete_choice_result": vehicle_choice},
        )
        state_after_vehicle = vehicle_step.execute(2025, state_for_vehicle)

        # Execute HeatingStateUpdateStep (uses state after vehicle)
        state_for_heating = replace(
            state_after_vehicle,
            data={**state_after_vehicle.data, "discrete_choice_result": heating_choice},
        )
        state_final = heating_step.execute(2025, state_for_heating)

        # Assert both incumbent columns present and correct
        final_pop = state_final.data["population_data"]
        assert "incumbent_vehicle" in final_pop.tables["menage"].column_names
        assert "incumbent_heating" in final_pop.tables["menage"].column_names

        vehicle_incumbents = final_pop.tables["menage"].column("incumbent_vehicle").to_pylist()
        assert vehicle_incumbents == ["ev", "petrol", "keep_current"]  # keep_current preserved keep_current

        heating_incumbents = final_pop.tables["menage"].column("incumbent_heating").to_pylist()
        assert heating_incumbents == ["heat_pump_air", "condensing_boiler", "condensing_boiler"]
