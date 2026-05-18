# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for population validation module.

Story 28.2: Validate incumbent technology columns in population data.
"""

from __future__ import annotations

import pytest

from reformlab.computation.types import PopulationData
from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.population_validation import (
    add_incumbent_columns_to_population,
    validate_population_for_technology_set,
)
from reformlab.discrete_choice.technology_set import DEFAULT_TECHNOLOGY_SET


class TestPopulationValidation:
    """Test population validation for incumbent technology columns."""

    # Story 28.2 / AC-2: Valid population with incumbents passes validation
    def test_validate_population_valid_incumbents(self):
        """Valid population with dictionary-encoded incumbent columns passes."""
        # Create population with both heating and vehicle incumbent columns
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2, 3],
                    "incumbent_heating": pa.array(
                        ["condensing_boiler", "heat_pump_air", "keep_current"],
                        type=pa.dictionary(pa.int32(), pa.utf8()),
                    ),
                    "incumbent_vehicle": pa.array(
                        ["diesel", "ev", "keep_current"],
                        type=pa.dictionary(pa.int32(), pa.utf8()),
                    ),
                })
            },
            metadata={},
        )
        technology_set = DEFAULT_TECHNOLOGY_SET

        warnings = validate_population_for_technology_set(
            population, technology_set, entity_key="menage"
        )
        assert warnings == []

    # Story 28.2 / AC-2: Plain string columns also work (non-dictionary)
    def test_validate_population_valid_incumbents_plain_string(self):
        """Valid population with plain string incumbent columns passes."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2, 3],
                    "incumbent_heating": ["condensing_boiler", "heat_pump_air", "keep_current"],
                    "incumbent_vehicle": ["diesel", "ev", "keep_current"],
                })
            },
            metadata={},
        )
        technology_set = DEFAULT_TECHNOLOGY_SET

        warnings = validate_population_for_technology_set(
            population, technology_set, entity_key="menage"
        )
        assert warnings == []

    # Story 28.2 / AC-3: Unknown incumbent IDs raise error
    def test_validate_population_unknown_incumbent_ids(self):
        """Unknown incumbent technology IDs raise DiscreteChoiceError."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2],
                    "incumbent_heating": pa.array(
                        ["condensing_boiler", "unknown_tech"],
                        type=pa.dictionary(pa.int32(), pa.utf8()),
                    ),
                })
            },
            metadata={},
        )
        technology_set = DEFAULT_TECHNOLOGY_SET

        with pytest.raises(DiscreteChoiceError, match="unknown incumbent technology IDs"):
            validate_population_for_technology_set(
                population, technology_set, entity_key="menage"
            )

    # Story 28.2 / AC-3: Error message lists unknown IDs and valid alternatives
    def test_validate_population_unknown_incumbent_ids_error_message(self):
        """Error message includes unknown IDs and valid alternatives."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2],
                    "incumbent_vehicle": pa.array(
                        ["ev", "spaceship"],  # spaceship is unknown
                        type=pa.dictionary(pa.int32(), pa.utf8()),
                    ),
                })
            },
            metadata={},
        )
        technology_set = DEFAULT_TECHNOLOGY_SET

        with pytest.raises(DiscreteChoiceError) as exc_info:
            validate_population_for_technology_set(
                population, technology_set, entity_key="menage"
            )

        error_msg = str(exc_info.value)
        assert "spaceship" in error_msg
        assert "vehicle" in error_msg
        assert "Valid alternatives" in error_msg

    # Story 28.2 / AC-4: Missing incumbent column returns warning
    def test_validate_population_missing_incumbent_column(self):
        """Missing incumbent column returns warning, not error."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2, 3],
                    # No incumbent_heating column
                })
            },
            metadata={},
        )
        technology_set = DEFAULT_TECHNOLOGY_SET

        warnings = validate_population_for_technology_set(
            population, technology_set, entity_key="menage"
        )
        # DEFAULT_TECHNOLOGY_SET has both heating and vehicle enabled
        assert len(warnings) == 2
        assert any("incumbent_heating" in w for w in warnings)
        assert any("incumbent_vehicle" in w for w in warnings)
        assert all("reference alternative" in w for w in warnings)

    # Story 28.2 / AC-4: Warning mentions reference alternative
    def test_validate_population_missing_incumbent_column_shows_reference(self):
        """Warning message includes reference alternative ID."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2],
                })
            },
            metadata={},
        )
        technology_set = DEFAULT_TECHNOLOGY_SET

        warnings = validate_population_for_technology_set(
            population, technology_set, entity_key="menage"
        )
        assert len(warnings) == 2  # Both heating and vehicle missing
        for warning in warnings:
            assert "keep_current" in warning  # Reference alternative

    # Story 28.2 / AC-8: Disabled investment decisions short-circuit
    def test_validate_population_disabled_decisions_none_technology_set(self):
        """When technology_set is None, validation returns empty warnings."""
        import pyarrow as pa

        population = PopulationData(
            tables={"menage": pa.table({"household_id": [1, 2, 3]})},
            metadata={},
        )
        technology_set = None  # Decisions disabled

        warnings = validate_population_for_technology_set(
            population, technology_set, entity_key="menage"
        )
        assert warnings == []

    # Multiple enabled domains: both heating and vehicle validated
    def test_validate_population_multiple_domains(self):
        """Both heating and vehicle domains validated when enabled."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2],
                    "incumbent_heating": pa.array(
                        ["condensing_boiler", "heat_pump_air"],
                        type=pa.dictionary(pa.int32(), pa.utf8()),
                    ),
                    "incumbent_vehicle": pa.array(
                        ["diesel", "ev"],
                        type=pa.dictionary(pa.int32(), pa.utf8()),
                    ),
                })
            },
            metadata={},
        )
        technology_set = DEFAULT_TECHNOLOGY_SET

        warnings = validate_population_for_technology_set(
            population, technology_set, entity_key="menage"
        )
        assert warnings == []

    # Only one domain enabled: only that domain validated
    def test_validate_population_single_enabled_domain(self):
        """When only heating enabled, only heating incumbent validated."""
        import pyarrow as pa

        from reformlab.discrete_choice.technology_set import (
            DEFAULT_HEATING_TECHNOLOGY_SET,
            TechnologySet,
        )

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2],
                    "incumbent_heating": ["condensing_boiler", "heat_pump_air"],
                    "incumbent_vehicle": ["diesel", "ev"],  # Should be ignored
                })
            },
            metadata={},
        )
        # Create technology set with only heating enabled
        technology_set = TechnologySet(
            version="fr-default-2026-04-26",
            domains={"heating": DEFAULT_HEATING_TECHNOLOGY_SET},
        )

        warnings = validate_population_for_technology_set(
            population, technology_set, entity_key="menage"
        )
        assert warnings == []

    # Missing entity key returns warning
    def test_validate_population_missing_entity_key(self):
        """Missing entity key returns warning."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "individu": pa.table({  # Wrong entity key
                    "person_id": [1, 2],
                })
            },
            metadata={},
        )
        technology_set = DEFAULT_TECHNOLOGY_SET

        warnings = validate_population_for_technology_set(
            population, technology_set, entity_key="menage"
        )
        assert len(warnings) == 2  # Both heating and vehicle domains
        assert all("Entity key 'menage' not found" in w for w in warnings)

    # Empty population: validation still works
    def test_validate_population_empty(self):
        """Empty population (0 rows) validation still works."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": pa.array([], type=pa.int64()),
                    "incumbent_heating": pa.array([], type=pa.dictionary(pa.int32(), pa.utf8())),
                    "incumbent_vehicle": pa.array([], type=pa.dictionary(pa.int32(), pa.utf8())),
                })
            },
            metadata={},
        )
        technology_set = DEFAULT_TECHNOLOGY_SET

        warnings = validate_population_for_technology_set(
            population, technology_set, entity_key="menage"
        )
        # Empty population has no unknown values, should pass
        assert warnings == []

    # Story 28.2 / AC-7: Population without incumbents + technology_set → warnings
    def test_validate_population_without_incumbents_returns_warnings(self):
        """Population without incumbent columns returns warnings, not errors."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2, 3],
                    # No incumbent columns
                })
            },
            metadata={},
        )
        technology_set = DEFAULT_TECHNOLOGY_SET

        warnings = validate_population_for_technology_set(
            population, technology_set, entity_key="menage"
        )
        # Should return warnings, not raise
        assert len(warnings) == 2  # heating and vehicle
        assert all("not found" in w for w in warnings)


class TestAddIncumbentColumnsToPopulation:
    """Tests for add_incumbent_columns_to_population utility function."""

    def test_adds_columns_to_empty_population(self):
        """Should add default keep_current columns when source columns missing."""
        import pyarrow as pa

        population = PopulationData(
            tables={"menage": pa.table({"household_id": [1, 2, 3]})},
            metadata={},
        )

        result = add_incumbent_columns_to_population(population)

        assert "incumbent_heating" in result.tables["menage"].column_names
        assert "incumbent_vehicle" in result.tables["menage"].column_names
        assert result.tables["menage"].column("incumbent_heating").to_pylist() == [
            "keep_current",
            "keep_current",
            "keep_current",
        ]
        assert result.tables["menage"].column("incumbent_vehicle").to_pylist() == [
            "keep_current",
            "keep_current",
            "keep_current",
        ]

    def test_maps_heating_type_to_incumbent(self):
        """Should map heating_type values to incumbent alternatives."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2, 3, 4, 5],
                    "heating_type": ["gas", "electric", "heat_pump", "district", "unknown"],
                })
            },
            metadata={},
        )

        result = add_incumbent_columns_to_population(population)

        incumbents = result.tables["menage"].column("incumbent_heating").to_pylist()
        assert incumbents == [
            "condensing_boiler",  # gas
            "heat_pump_air",  # electric
            "heat_pump_air",  # heat_pump
            "district_heating",  # district
            "keep_current",  # unknown -> default
        ]

    def test_maps_vehicle_type_to_incumbent(self):
        """Should map vehicle_type values to incumbent alternatives."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2, 3, 4],
                    "vehicle_type": ["petrol", "diesel", "hybrid", "electric"],
                })
            },
            metadata={},
        )

        result = add_incumbent_columns_to_population(population)

        incumbents = result.tables["menage"].column("incumbent_vehicle").to_pylist()
        assert incumbents == ["petrol", "diesel", "hybrid", "ev"]

    def test_idempotent_when_columns_already_exist(self):
        """Should be idempotent - skip if columns already present."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2, 3],
                    "incumbent_heating": pa.array(
                        ["gas_boiler", "heat_pump", "electric"],
                        type=pa.dictionary(pa.int32(), pa.utf8()),
                    ),
                    "incumbent_vehicle": pa.array(
                        ["petrol", "diesel", "ev"],
                        type=pa.dictionary(pa.int32(), pa.utf8()),
                    ),
                })
            },
            metadata={},
        )

        result = add_incumbent_columns_to_population(population)

        # Should preserve existing columns, not add duplicates
        assert result.tables["menage"].num_columns == 3  # household_id + 2 incumbents
        assert result.tables["menage"].column("incumbent_heating").to_pylist() == [
            "gas_boiler",
            "heat_pump",
            "electric",
        ]
        assert result.tables["menage"].column("incumbent_vehicle").to_pylist() == [
            "petrol",
            "diesel",
            "ev",
        ]

    def test_missing_entity_key_returns_unchanged(self):
        """Should return population unchanged when entity key missing."""
        import pyarrow as pa

        population = PopulationData(
            tables={
                "individu": pa.table({  # Wrong entity key
                    "person_id": [1, 2],
                })
            },
            metadata={},
        )

        result = add_incumbent_columns_to_population(population)

        # Should return unchanged population
        assert result.tables == population.tables
        assert "incumbent_heating" not in result.tables.get("individu", {}).column_names

    def test_returns_new_population_without_mutation(self):
        """Should return new PopulationData without modifying original."""
        import pyarrow as pa

        population = PopulationData(
            tables={"menage": pa.table({"household_id": [1, 2, 3]})},
            metadata={"seed": 42},
        )

        original_tables = population.tables
        result = add_incumbent_columns_to_population(population)

        # Original unchanged
        assert "incumbent_heating" not in population.tables["menage"].column_names
        assert population.tables is original_tables
        # Result has new columns
        assert "incumbent_heating" in result.tables["menage"].column_names
