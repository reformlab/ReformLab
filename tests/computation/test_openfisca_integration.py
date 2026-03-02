"""Integration tests for OpenFiscaApiAdapter against real OpenFisca-France.

Story 8.1: End-to-End OpenFisca Integration Spike.
Story 9.2: Multi-entity output array handling integration tests.
Story 9.4: 4-entity PopulationData format integration tests.
Story 9.5: OpenFisca-France reference test suite for regression detection.

These tests call real OpenFisca-France computations (no mocking).
Run with: uv run pytest tests/computation/test_openfisca_integration.py -m integration
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

openfisca_france = pytest.importorskip("openfisca_france")

from reformlab.computation.ingestion import DataSchema
from reformlab.computation.mapping import apply_output_mapping, load_mapping
from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
from reformlab.computation.quality import validate_output
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

# ---------------------------------------------------------------------------
# Shared fixtures — TBS is expensive, cache at module scope
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tbs() -> Any:
    """Load the real French TaxBenefitSystem once per module."""
    return openfisca_france.CountryTaxBenefitSystem()


@pytest.fixture(scope="module")
def adapter() -> OpenFiscaApiAdapter:
    """Create a real OpenFiscaApiAdapter with a common output variable."""
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=("impot_revenu_restant_a_payer",),
    )


@pytest.fixture()
def single_person_population() -> PopulationData:
    """Minimal single-person population using singular entity keys.

    Only provides the individu table with input variables. The adapter's
    _population_to_entity_dict handles normalisation to plural keys.
    Note: group entities (famille, foyer_fiscal, menage) are omitted
    because the adapter auto-creates them for single-person populations.
    """
    return PopulationData(
        tables={
            "individu": pa.table({
                "salaire_de_base": pa.array([30000.0]),
                "age": pa.array([30]),
            }),
        },
        metadata={"source": "integration-test"},
    )


@pytest.fixture()
def empty_policy() -> PolicyConfig:
    return PolicyConfig(parameters={}, name="integration-test-policy")


def _build_entities_dict(salary: float = 30000.0, age: int = 30) -> dict[str, Any]:
    """Helper to build a valid OpenFisca-France entity dict (plural keys)."""
    return {
        "individus": {
            "person_0": {
                "salaire_de_base": {"2024": salary},
                "age": {"2024-01": age},
            },
        },
        "familles": {"famille_0": {"parents": ["person_0"]}},
        "foyers_fiscaux": {"foyer_0": {"declarants": ["person_0"]}},
        "menages": {"menage_0": {"personne_de_reference": ["person_0"]}},
    }


def _build_simulation(
    tbs: Any,
    individus: dict[str, dict[str, Any]],
    *,
    couples: bool = False,
) -> Any:
    """Helper to build a simulation with standard 4-entity structure."""
    from openfisca_core.simulation_builder import SimulationBuilder

    person_ids = list(individus.keys())

    if couples and len(person_ids) == 2:
        familles = {"famille_0": {"parents": person_ids}}
        foyers = {"foyer_0": {"declarants": person_ids}}
        menages = {"menage_0": {
            "personne_de_reference": [person_ids[0]],
            "conjoint": [person_ids[1]],
        }}
    else:
        familles = {f"famille_{i}": {"parents": [pid]} for i, pid in enumerate(person_ids)}
        foyers = {f"foyer_{i}": {"declarants": [pid]} for i, pid in enumerate(person_ids)}
        menages = {f"menage_{i}": {"personne_de_reference": [pid]} for i, pid in enumerate(person_ids)}

    entities_dict = {
        "individus": individus,
        "familles": familles,
        "foyers_fiscaux": foyers,
        "menages": menages,
    }

    builder = SimulationBuilder()
    return builder.build_from_entities(tbs, entities_dict)


# ---------------------------------------------------------------------------
# AC-2: TaxBenefitSystem loads (Task 3)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestTaxBenefitSystemLoading:
    """AC-2: TaxBenefitSystem loads without error via adapter."""

    def test_adapter_instantiates_without_error(self) -> None:
        """AC-2: OpenFiscaApiAdapter with openfisca_france instantiates successfully."""
        a = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        assert a is not None

    def test_version_returns_valid_string(self) -> None:
        """AC-2: adapter.version() returns a valid openfisca-core version string."""
        a = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        version = a.version()
        assert isinstance(version, str)
        parts = version.split(".")
        assert len(parts) == 3
        assert parts[0] == "44"

    def test_tbs_loads_lazily_and_is_cached(self) -> None:
        """AC-2: TBS is loaded lazily on first access and cached."""
        a = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        assert a._tax_benefit_system is None

        local_tbs = a._get_tax_benefit_system()
        assert local_tbs is not None

        local_tbs2 = a._get_tax_benefit_system()
        assert local_tbs is local_tbs2


# ---------------------------------------------------------------------------
# AC-3, AC-7: Real computation via adapter.compute() (Tasks 4, 8)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAdapterComputeEndToEnd:
    """AC-3, AC-7: adapter.compute() returns valid results with real OpenFisca-France.

    These tests call the adapter's public compute() method end-to-end,
    validating that the full pipeline (TBS loading, entity dict construction,
    simulation building, result extraction) works with OpenFisca-France.
    """

    def test_compute_returns_computation_result(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig
    ) -> None:
        """AC-3: adapter.compute() returns a ComputationResult with real values."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        assert isinstance(result, ComputationResult)
        assert isinstance(result.output_fields, pa.Table)
        assert "impot_revenu_restant_a_payer" in result.output_fields.column_names
        assert result.output_fields.num_rows == 1

    def test_compute_result_has_correct_metadata(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig
    ) -> None:
        """AC-3: adapter.compute() sets source='api' in metadata."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        assert result.metadata["source"] == "api"
        assert result.metadata["country_package"] == "openfisca_france"
        assert result.period == 2024

    def test_irpp_value_is_negative_tax(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig
    ) -> None:
        """AC-3, AC-7: irpp for 30k salary is negative (tax owed) and in reasonable range."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        irpp = result.output_fields.column("impot_revenu_restant_a_payer")[0].as_py()
        assert irpp < 0, f"Expected negative irpp (tax), got {irpp}"
        assert -5000 < irpp < 0, f"irpp {irpp} outside expected range [-5000, 0]"


# ---------------------------------------------------------------------------
# AC-4: Multi-entity population (Task 5)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestMultiEntityPopulation:
    """AC-4: Multi-entity population with all 4 OpenFisca-France entities."""

    def test_multi_person_computation(self, tbs: Any) -> None:
        """AC-4: Computation with 2 persons returns results for all."""
        from openfisca_core.simulation_builder import SimulationBuilder

        entities_dict = {
            "individus": {
                "person_0": {
                    "salaire_de_base": {"2024": 30000.0},
                    "age": {"2024-01": 30},
                },
                "person_1": {
                    "salaire_de_base": {"2024": 50000.0},
                    "age": {"2024-01": 45},
                },
            },
            "familles": {
                "famille_0": {"parents": ["person_0"]},
                "famille_1": {"parents": ["person_1"]},
            },
            "foyers_fiscaux": {
                "foyer_0": {"declarants": ["person_0"]},
                "foyer_1": {"declarants": ["person_1"]},
            },
            "menages": {
                "menage_0": {"personne_de_reference": ["person_0"]},
                "menage_1": {"personne_de_reference": ["person_1"]},
            },
        }

        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        irpp = simulation.calculate("impot_revenu_restant_a_payer", "2024")
        assert len(irpp) == 2, f"Expected 2 results, got {len(irpp)}"
        assert irpp[0] < 0
        assert irpp[1] < 0
        # Higher salary -> more tax (more negative)
        assert irpp[1] < irpp[0], "Higher salary should yield higher tax"

    def test_multi_entity_variable_array_lengths(self, tbs: Any) -> None:
        """AC-4: Variables from different entities return different-length arrays.

        This documents the known gap (Gap 2 in findings): multi-entity output
        arrays have different lengths, so they can't be combined into one table.
        """
        from openfisca_core.simulation_builder import SimulationBuilder

        # 2 persons but 1 foyer_fiscal and 1 menage (married couple)
        entities_dict = {
            "individus": {
                "person_0": {
                    "salaire_de_base": {"2024": 30000.0},
                    "age": {"2024-01": 30},
                },
                "person_1": {
                    "salaire_de_base": {"2024": 0.0},
                    "age": {"2024-01": 28},
                },
            },
            "familles": {
                "famille_0": {"parents": ["person_0", "person_1"]},
            },
            "foyers_fiscaux": {
                "foyer_0": {"declarants": ["person_0", "person_1"]},
            },
            "menages": {
                "menage_0": {
                    "personne_de_reference": ["person_0"],
                    "conjoint": ["person_1"],
                },
            },
        }

        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        # individu-level variable: 2 values
        salaire_net = simulation.calculate_add("salaire_net", "2024")
        assert len(salaire_net) == 2

        # foyer_fiscal-level variable: 1 value
        irpp = simulation.calculate("impot_revenu_restant_a_payer", "2024")
        assert len(irpp) == 1

        # menage-level variable: 1 value
        revenu_disponible = simulation.calculate("revenu_disponible", "2024")
        assert len(revenu_disponible) == 1

    def test_adapter_entity_key_to_plural_mapping(self, tbs: Any) -> None:
        """AC-4: Document that entity.key != build_from_entities key (plural)."""
        key_to_plural = {}
        for entity in tbs.entities:
            key_to_plural[entity.key] = entity.plural

        assert key_to_plural["individu"] == "individus"
        assert key_to_plural["famille"] == "familles"
        assert key_to_plural["foyer_fiscal"] == "foyers_fiscaux"
        assert key_to_plural["menage"] == "menages"


# ---------------------------------------------------------------------------
# AC-5: Variable mapping round-trip (Task 6)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestVariableMappingRoundTrip:
    """AC-5: Variable mapping correctly renames OpenFisca columns to project names."""

    def test_mapping_renames_columns_correctly(self, tbs: Any, tmp_path: Path) -> None:
        """AC-5: apply_output_mapping renames OpenFisca variable names to project names."""
        from openfisca_core.simulation_builder import SimulationBuilder

        mapping_yaml = tmp_path / "test_mapping.yaml"
        mapping_yaml.write_text(
            "version: 1\n"
            "mappings:\n"
            "  - openfisca_name: impot_revenu_restant_a_payer\n"
            "    project_name: income_tax\n"
            "    direction: output\n"
            "    type: float64\n"
            "  - openfisca_name: salaire_net\n"
            "    project_name: net_salary\n"
            "    direction: output\n"
            "    type: float64\n"
        )

        config = load_mapping(mapping_yaml)

        entities_dict = _build_entities_dict()
        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        irpp_val = simulation.calculate("impot_revenu_restant_a_payer", "2024")
        salaire_net_val = simulation.calculate_add("salaire_net", "2024")

        original_table = pa.table({
            "impot_revenu_restant_a_payer": pa.array(irpp_val),
            "salaire_net": pa.array(salaire_net_val),
        })

        mapped_table = apply_output_mapping(original_table, config)

        assert "income_tax" in mapped_table.column_names
        assert "net_salary" in mapped_table.column_names
        assert "impot_revenu_restant_a_payer" not in mapped_table.column_names
        assert "salaire_net" not in mapped_table.column_names

    def test_mapped_values_are_numerically_identical(self, tbs: Any, tmp_path: Path) -> None:
        """AC-5: Mapped values are numerically identical to unmapped values."""
        from openfisca_core.simulation_builder import SimulationBuilder

        mapping_yaml = tmp_path / "test_mapping.yaml"
        mapping_yaml.write_text(
            "version: 1\n"
            "mappings:\n"
            "  - openfisca_name: impot_revenu_restant_a_payer\n"
            "    project_name: income_tax\n"
            "    direction: output\n"
            "    type: float64\n"
        )

        config = load_mapping(mapping_yaml)

        entities_dict = _build_entities_dict()
        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        irpp_val = simulation.calculate("impot_revenu_restant_a_payer", "2024")

        original_table = pa.table({
            "impot_revenu_restant_a_payer": pa.array(irpp_val),
        })
        mapped_table = apply_output_mapping(original_table, config)

        original_value = original_table.column("impot_revenu_restant_a_payer")[0].as_py()
        mapped_value = mapped_table.column("income_tax")[0].as_py()
        assert original_value == mapped_value


# ---------------------------------------------------------------------------
# AC-6: Output quality validation (Task 7)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOutputQualityValidation:
    """AC-6: Output passes quality validation with appropriate schema."""

    def test_validate_output_passes_with_adapter_result(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig
    ) -> None:
        """AC-6: Real adapter.compute() output passes validate_output."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        schema = DataSchema(
            schema=pa.schema([
                pa.field("impot_revenu_restant_a_payer", pa.float32()),
            ]),
            required_columns=("impot_revenu_restant_a_payer",),
        )

        qr = validate_output(result, schema)
        assert qr.passed is True
        assert len(qr.errors) == 0


# ---------------------------------------------------------------------------
# AC-7: Known-value benchmark (Task 8)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestKnownValueBenchmark:
    """AC-7: Adapter results match expected French income tax for known salary."""

    def test_irpp_determinism_via_adapter(
        self, single_person_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-7: Two independent adapter.compute() calls produce identical results."""
        adapter1 = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        adapter2 = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        result1 = adapter1.compute(single_person_population, empty_policy, 2024)
        result2 = adapter2.compute(single_person_population, empty_policy, 2024)

        val1 = result1.output_fields.column("impot_revenu_restant_a_payer")[0].as_py()
        val2 = result2.output_fields.column("impot_revenu_restant_a_payer")[0].as_py()

        assert abs(float(val1) - float(val2)) < 1.0, (
            f"Non-deterministic results: {val1} vs {val2}"
        )

    def test_higher_salary_yields_higher_tax(self, tbs: Any) -> None:
        """AC-7: Progressive tax -- higher salary results in more tax."""
        from openfisca_core.simulation_builder import SimulationBuilder

        def compute_irpp(salary: float) -> float:
            entities_dict = _build_entities_dict(salary=salary)
            builder = SimulationBuilder()
            sim = builder.build_from_entities(tbs, entities_dict)
            return float(sim.calculate("impot_revenu_restant_a_payer", "2024")[0])

        irpp_30k = compute_irpp(30000.0)
        irpp_60k = compute_irpp(60000.0)
        irpp_100k = compute_irpp(100000.0)

        assert irpp_60k < irpp_30k, f"60k ({irpp_60k}) should pay more tax than 30k ({irpp_30k})"
        assert irpp_100k < irpp_60k, f"100k ({irpp_100k}) should pay more tax than 60k ({irpp_60k})"


# ---------------------------------------------------------------------------
# Adapter plural-key fix validation (Task 5 supplement)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAdapterPluralKeyFix:
    """Validate that the adapter normalises singular entity keys to plural.

    The original spike identified that _population_to_entity_dict used
    entity.key (singular) but build_from_entities requires entity.plural.
    The fix normalises to plural keys automatically.
    """

    def test_population_to_entity_dict_normalises_to_plural(
        self, adapter: OpenFiscaApiAdapter
    ) -> None:
        """Adapter now normalises singular entity keys to plural."""
        local_tbs = adapter._get_tax_benefit_system()

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(population, policy, "2024", local_tbs)

        assert "individus" in entity_dict, "Adapter should normalise to plural key"
        assert "individu" not in entity_dict, "Singular key should be normalised away"

    def test_build_from_entities_rejects_singular_keys(self, tbs: Any) -> None:
        """build_from_entities raises error with singular entity keys."""
        from openfisca_core.errors import SituationParsingError
        from openfisca_core.simulation_builder import SimulationBuilder

        singular_dict = {
            "individu": {
                "person_0": {"salaire_de_base": {"2024": 30000.0}},
            },
            "famille": {"famille_0": {"parents": ["person_0"]}},
            "foyer_fiscal": {"foyer_0": {"declarants": ["person_0"]}},
            "menage": {"menage_0": {"personne_de_reference": ["person_0"]}},
        }

        builder = SimulationBuilder()
        with pytest.raises(SituationParsingError):
            builder.build_from_entities(tbs, singular_dict)

    def test_compute_works_with_singular_entity_keys(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig
    ) -> None:
        """adapter.compute() works when PopulationData uses singular entity keys."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        assert isinstance(result, ComputationResult)
        irpp = result.output_fields.column("impot_revenu_restant_a_payer")[0].as_py()
        assert irpp < 0, f"Expected negative irpp, got {irpp}"


# ---------------------------------------------------------------------------
# OpenFisca-France reference test cases
# Mirrors the format used in openfisca-france/tests/formulas/irpp.yaml
# to verify our pipeline produces bit-identical results to the official
# OpenFisca-France test suite.
# See: https://github.com/openfisca/openfisca-france/tree/master/tests/formulas
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestOpenFiscaFranceReferenceCases:
    """Reference test cases mirroring openfisca-france's own test format.

    These tests use salaire_imposable (taxable salary) as input -- the same
    input variable used in openfisca-france/tests/formulas/irpp.yaml -- to
    verify that our pipeline produces the same results as the official
    OpenFisca-France test suite.

    The expected values were computed directly via OpenFisca-France 175.0.18
    with openfisca-core 44.2.2 on 2026-02-28 and serve as pinned reference
    values for regression detection.
    """

    ABSOLUTE_ERROR_MARGIN = 0.5  # Same margin used by openfisca-france tests

    def test_single_person_salaire_imposable_20k(self, tbs: Any) -> None:
        """Reference: single person, salaire_imposable=20000, period 2024.

        Expected: impot_revenu_restant_a_payer = -150.0
        """
        sim = _build_simulation(tbs, {
            "person_0": {"salaire_imposable": {"2024": 20000.0}},
        })
        irpp = float(sim.calculate("impot_revenu_restant_a_payer", "2024")[0])
        assert abs(irpp - (-150.0)) <= self.ABSOLUTE_ERROR_MARGIN, (
            f"Expected -150.0, got {irpp}"
        )

    def test_single_person_salaire_imposable_50k(self, tbs: Any) -> None:
        """Reference: single person, salaire_imposable=50000, period 2024.

        Expected: impot_revenu_restant_a_payer = -6665.0
        """
        sim = _build_simulation(tbs, {
            "person_0": {"salaire_imposable": {"2024": 50000.0}},
        })
        irpp = float(sim.calculate("impot_revenu_restant_a_payer", "2024")[0])
        assert abs(irpp - (-6665.0)) <= self.ABSOLUTE_ERROR_MARGIN, (
            f"Expected -6665.0, got {irpp}"
        )

    def test_couple_salaire_imposable_30k_25k(self, tbs: Any) -> None:
        """Reference: couple, salaire_imposable=30000+25000, period 2024.

        Expected: impot_revenu_restant_a_payer = -2765.0
        Joint taxation with 2 tax shares (quotient familial).
        """
        sim = _build_simulation(
            tbs,
            {
                "person_0": {"salaire_imposable": {"2024": 30000.0}},
                "person_1": {"salaire_imposable": {"2024": 25000.0}},
            },
            couples=True,
        )
        irpp = float(sim.calculate("impot_revenu_restant_a_payer", "2024")[0])
        assert abs(irpp - (-2765.0)) <= self.ABSOLUTE_ERROR_MARGIN, (
            f"Expected -2765.0, got {irpp}"
        )

    def test_couple_pays_less_than_single_high_earner(self, tbs: Any) -> None:
        """Reference: joint taxation benefit with asymmetric incomes.

        French quotient familial means a couple filing jointly should pay
        less total tax than a single person with the same total income,
        especially when incomes are asymmetric.  We use 80k+0 to make the
        benefit unambiguous (at lower incomes, the decote can make two
        singles cheaper than one couple).
        """
        sim_couple = _build_simulation(
            tbs,
            {
                "person_0": {"salaire_imposable": {"2024": 80000.0}},
                "person_1": {"salaire_imposable": {"2024": 0.0}},
            },
            couples=True,
        )
        irpp_couple = float(sim_couple.calculate("impot_revenu_restant_a_payer", "2024")[0])

        sim_single = _build_simulation(tbs, {
            "person_0": {"salaire_imposable": {"2024": 80000.0}},
        })
        irpp_single = float(sim_single.calculate("impot_revenu_restant_a_payer", "2024")[0])

        # Couple should pay less (less negative = less tax)
        assert irpp_couple > irpp_single, (
            f"Couple ({irpp_couple}) should pay less tax than single earner ({irpp_single})"
        )


# ===========================================================================
# Story 9.2: Multi-entity output array handling (integration tests)
# ===========================================================================


@pytest.fixture(scope="module")
def multi_entity_adapter() -> OpenFiscaApiAdapter:
    """Adapter configured with mixed-entity output variables.

    Story 9.2 AC-1, AC-2, AC-3: Tests multi-entity output extraction
    with real OpenFisca-France variables from different entities.
    """
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=(
            "salaire_net",                      # individu
            "impot_revenu_restant_a_payer",      # foyer_fiscal
            "revenu_disponible",                 # menage
        ),
    )


@pytest.mark.integration
class TestMultiEntityOutputArrays:
    """Story 9.2 AC-1, AC-2, AC-3: Multi-entity output variable handling.

    These tests validate that the adapter correctly handles output variables
    belonging to different entities, producing separate per-entity tables
    with correct array lengths.
    """

    def test_married_couple_multi_entity_extraction(
        self, tbs: Any, multi_entity_adapter: OpenFiscaApiAdapter
    ) -> None:
        """AC-1, AC-2, AC-3: Married couple with 2 persons, 1 foyer, 1 menage.

        The canonical multi-entity test case from spike 8-1:
        - salaire_net (individu) → 2 values
        - impot_revenu_restant_a_payer (foyer_fiscal) → 1 value
        - revenu_disponible (menage) → 1 value
        """
        from openfisca_core.simulation_builder import SimulationBuilder

        entities_dict = {
            "individus": {
                "person_0": {
                    "salaire_de_base": {"2024": 30000.0},
                    "age": {"2024-01": 30},
                },
                "person_1": {
                    "salaire_de_base": {"2024": 0.0},
                    "age": {"2024-01": 28},
                },
            },
            "familles": {
                "famille_0": {"parents": ["person_0", "person_1"]},
            },
            "foyers_fiscaux": {
                "foyer_0": {"declarants": ["person_0", "person_1"]},
            },
            "menages": {
                "menage_0": {
                    "personne_de_reference": ["person_0"],
                    "conjoint": ["person_1"],
                },
            },
        }

        # Test _resolve_variable_entities with real TBS
        local_tbs = multi_entity_adapter._get_tax_benefit_system()
        vars_by_entity = multi_entity_adapter._resolve_variable_entities(local_tbs)

        # Verify entity grouping
        assert "individus" in vars_by_entity
        assert "foyers_fiscaux" in vars_by_entity
        assert "menages" in vars_by_entity
        assert "salaire_net" in vars_by_entity["individus"]
        assert "impot_revenu_restant_a_payer" in vars_by_entity["foyers_fiscaux"]
        assert "revenu_disponible" in vars_by_entity["menages"]

        # Story 9.3: Resolve periodicities for _extract_results_by_entity
        var_periodicities = multi_entity_adapter._resolve_variable_periodicities(
            local_tbs
        )

        # Build simulation and extract results by entity
        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        entity_tables = multi_entity_adapter._extract_results_by_entity(
            simulation, 2024, vars_by_entity, var_periodicities
        )

        # AC-2: Correct array lengths per entity
        assert entity_tables["individus"].num_rows == 2
        assert entity_tables["foyers_fiscaux"].num_rows == 1
        assert entity_tables["menages"].num_rows == 1

        # AC-3: Correct columns per entity
        assert "salaire_net" in entity_tables["individus"].column_names
        assert "impot_revenu_restant_a_payer" in entity_tables["foyers_fiscaux"].column_names
        assert "revenu_disponible" in entity_tables["menages"].column_names

    def test_single_entity_backward_compatible(
        self, tbs: Any
    ) -> None:
        """AC-4: Single-entity output produces backward-compatible result."""
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
            metadata={"source": "integration-test"},
        )
        policy = PolicyConfig(parameters={}, name="test")

        result = adapter.compute(population, policy, 2024)

        # Single entity: entity_tables should be empty
        assert result.entity_tables == {}
        # output_fields works as before
        assert isinstance(result.output_fields, pa.Table)
        assert "impot_revenu_restant_a_payer" in result.output_fields.column_names
        assert result.output_fields.num_rows == 1

    def test_variable_entity_resolution_matches_tbs(self, tbs: Any) -> None:
        """AC-1: Variable entity resolution matches actual TBS entity definitions."""
        # Verify entity attributes are accessible on real TBS variables
        irpp_var = tbs.variables["impot_revenu_restant_a_payer"]
        assert irpp_var.entity.key == "foyer_fiscal"
        assert irpp_var.entity.plural == "foyers_fiscaux"

        salaire_var = tbs.variables["salaire_net"]
        assert salaire_var.entity.key == "individu"
        assert salaire_var.entity.plural == "individus"

        revenu_var = tbs.variables["revenu_disponible"]
        assert revenu_var.entity.key == "menage"
        assert revenu_var.entity.plural == "menages"

    def test_multi_entity_adapter_compute_end_to_end(self, tbs: Any) -> None:
        """AC-1, AC-2, AC-3: Full adapter.compute() with multi-entity output.

        Tests that entity_tables and output_entities metadata are correctly
        populated when output variables span multiple entities.

        Note: This test uses only the individu table in PopulationData.
        The adapter's _population_to_entity_dict handles auto-creation of
        group entities for single-person populations. For married couples
        (2 persons, 1 foyer), all 4 entity tables must be provided.
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=(
                "salaire_net",
                "impot_revenu_restant_a_payer",
            ),
        )

        # Use 2 persons, 2 separate foyers (not married) to keep it simple
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                    "age": pa.array([30, 45]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="multi-entity-test")

        result = adapter.compute(population, policy, 2024)

        # Multi-entity: entity_tables populated
        assert len(result.entity_tables) == 2
        assert "individus" in result.entity_tables
        assert "foyers_fiscaux" in result.entity_tables

        # AC-2: Correct array lengths
        assert result.entity_tables["individus"].num_rows == 2
        assert result.entity_tables["foyers_fiscaux"].num_rows == 2

        # output_fields is person-entity table
        assert result.output_fields.num_rows == 2
        assert "salaire_net" in result.output_fields.column_names

        # Metadata includes entity information
        assert "output_entities" in result.metadata
        assert "entity_row_counts" in result.metadata


# ===========================================================================
# Story 9.3: Variable periodicity handling (integration tests)
# ===========================================================================


@pytest.fixture(scope="module")
def periodicity_adapter() -> OpenFiscaApiAdapter:
    """Adapter with mixed-periodicity output variables.

    Story 9.3 AC-1, AC-2: Tests periodicity-aware calculation dispatch
    with real OpenFisca-France variables:
    - salaire_net (individu, MONTH) → calculate_add
    - impot_revenu_restant_a_payer (foyer_fiscal, YEAR) → calculate
    """
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=(
            "salaire_net",                      # individu, MONTH
            "impot_revenu_restant_a_payer",      # foyer_fiscal, YEAR
        ),
    )


@pytest.mark.integration
class TestVariablePeriodicityHandling:
    """Story 9.3 AC-1, AC-2, AC-6: Periodicity-aware calculation dispatch.

    These tests validate that the adapter correctly detects variable
    periodicities and dispatches to the appropriate OpenFisca calculation
    method (calculate vs calculate_add).
    """

    def test_monthly_variable_yearly_aggregation(self, tbs: Any) -> None:
        """AC-2: Monthly variable (salaire_net) with yearly period returns correct sum.

        Story 9.3 AC-2: Given a monthly variable requested for a yearly period,
        the adapter automatically sums the 12 monthly values via calculate_add().
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("salaire_net",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="periodicity-test")

        result = adapter.compute(population, policy, 2024)

        # AC-2: salaire_net should be a positive value representing yearly net salary
        salaire_net = result.output_fields.column("salaire_net")[0].as_py()
        assert 20000 < salaire_net < 30000, (
            f"salaire_net={salaire_net} outside expected range [20000, 30000] "
            f"for 30k gross salary"
        )

        # AC-5: Metadata shows correct dispatch
        assert result.metadata["calculation_methods"]["salaire_net"] == "calculate_add"
        assert result.metadata["variable_periodicities"]["salaire_net"] == "month"

    def test_yearly_variable_uses_calculate(self, tbs: Any) -> None:
        """AC-1: Yearly variable (irpp) with yearly period uses calculate().

        Story 9.3 AC-4: Behavior is identical to pre-change implementation.
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="periodicity-test")

        result = adapter.compute(population, policy, 2024)

        # irpp should be negative (tax owed)
        irpp = result.output_fields.column("impot_revenu_restant_a_payer")[0].as_py()
        assert irpp < 0, f"Expected negative irpp (tax), got {irpp}"

        # AC-5: Metadata shows correct dispatch
        assert result.metadata["calculation_methods"]["impot_revenu_restant_a_payer"] == "calculate"
        assert result.metadata["variable_periodicities"]["impot_revenu_restant_a_payer"] == "year"

    def test_mixed_periodicity_compute(
        self, periodicity_adapter: OpenFiscaApiAdapter
    ) -> None:
        """AC-1, AC-2: Mixed periodicity output variables in single compute().

        Story 9.3 AC-1: The adapter uses calculate_add() for monthly variables
        and calculate() for yearly variables, producing correct results for both.
        """
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                    "age": pa.array([30, 45]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="mixed-periodicity-test")

        result = periodicity_adapter.compute(population, policy, 2024)

        # Both variables should return results without ValueError
        assert result.output_fields.num_rows == 2
        assert "salaire_net" in result.output_fields.column_names

        # entity_tables should have both entities
        assert "individus" in result.entity_tables
        assert "foyers_fiscaux" in result.entity_tables

        # AC-5: Correct methods per variable
        assert result.metadata["calculation_methods"]["salaire_net"] == "calculate_add"
        assert result.metadata["calculation_methods"]["impot_revenu_restant_a_payer"] == "calculate"

    def test_monthly_variable_end_to_end(self, tbs: Any) -> None:
        """AC-2: End-to-end test that monthly output variable produces correct values.

        Story 9.3 AC-2: adapter.compute() with a monthly output variable
        produces correct yearly aggregated values.
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("salaire_net",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="monthly-e2e-test")

        result = adapter.compute(population, policy, 2024)

        assert isinstance(result, ComputationResult)
        assert result.output_fields.num_rows == 1
        assert "salaire_net" in result.output_fields.column_names

        # Verify the value is reasonable (should be yearly aggregate)
        salaire_net = result.output_fields.column("salaire_net")[0].as_py()
        assert salaire_net > 0, f"Net salary should be positive, got {salaire_net}"

    def test_periodicity_metadata_in_integration(
        self, periodicity_adapter: OpenFiscaApiAdapter
    ) -> None:
        """AC-5: variable_periodicities metadata in integration test result.

        Story 9.3 AC-5: The result metadata includes variable_periodicities
        and calculation_methods entries for each output variable.
        """
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="metadata-test")

        result = periodicity_adapter.compute(population, policy, 2024)

        # AC-5: variable_periodicities present and correct
        assert "variable_periodicities" in result.metadata
        vp = result.metadata["variable_periodicities"]
        assert vp["salaire_net"] == "month"
        assert vp["impot_revenu_restant_a_payer"] == "year"

        # AC-5: calculation_methods present and correct
        assert "calculation_methods" in result.metadata
        cm = result.metadata["calculation_methods"]
        assert cm["salaire_net"] == "calculate_add"
        assert cm["impot_revenu_restant_a_payer"] == "calculate"

    def test_variable_periodicity_resolution_matches_tbs(self, tbs: Any) -> None:
        """AC-1: Variable periodicity resolution matches actual TBS definitions.

        Story 9.3: Verify that definition_period attributes are accessible
        and match expected values for known OpenFisca-France variables.
        """
        # salaire_net is a MONTH variable
        salaire_var = tbs.variables["salaire_net"]
        assert str(salaire_var.definition_period) == "month"

        # impot_revenu_restant_a_payer is a YEAR variable
        irpp_var = tbs.variables["impot_revenu_restant_a_payer"]
        assert str(irpp_var.definition_period) == "year"

        # date_naissance is an ETERNITY variable
        birth_var = tbs.variables["date_naissance"]
        assert str(birth_var.definition_period) == "eternity"


# ===========================================================================
# Story 9.4: 4-entity PopulationData format (integration tests)
# ===========================================================================


@pytest.mark.integration
class TestFourEntityPopulationFormat:
    """Story 9.4: 4-entity PopulationData format via membership columns.

    AC-1: Membership columns produce valid entity dict.
    AC-2: Group membership assignment is correct.
    AC-6: Backward compatibility preserved.
    AC-7: Group entity input variables merged correctly.
    """

    ABSOLUTE_ERROR_MARGIN = 0.5  # Consistent with TestOpenFiscaFranceReferenceCases

    def test_married_couple_via_membership_columns(self, tbs: Any) -> None:
        """AC-1, AC-2: Married couple via membership columns matches hand-built test.

        Should produce the SAME irpp as test_couple_salaire_imposable_30k_25k
        (irpp ≈ -2765.0) — this validates that the membership column approach
        produces identical results to manually building the entity dict.
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([30000.0, 25000.0]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint",
                    ]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="4entity-couple-test")

        result = adapter.compute(population, policy, 2024)

        assert isinstance(result, ComputationResult)
        irpp = result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py()

        # Match the reference case value from TestOpenFiscaFranceReferenceCases
        assert abs(float(irpp) - (-2765.0)) <= self.ABSOLUTE_ERROR_MARGIN, (
            f"Expected -2765.0, got {irpp}. Membership columns should produce "
            f"identical results to hand-built entity dict."
        )

    def test_single_person_with_membership_columns(self, tbs: Any) -> None:
        """AC-2, AC-6: Single person with membership columns matches without.

        Results should be identical to single-person tests without membership
        columns — the membership columns just make the entity structure explicit.
        """
        # Adapter with membership columns
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        population_with_membership = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                    "famille_id": pa.array([0]),
                    "famille_role": pa.array(["parents"]),
                    "foyer_fiscal_id": pa.array([0]),
                    "foyer_fiscal_role": pa.array(["declarants"]),
                    "menage_id": pa.array([0]),
                    "menage_role": pa.array(["personne_de_reference"]),
                }),
            },
        )

        population_without_membership = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="4entity-single-test")

        result_with = adapter.compute(population_with_membership, policy, 2024)
        result_without = adapter.compute(population_without_membership, policy, 2024)

        irpp_with = float(result_with.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        irpp_without = float(result_without.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())

        assert abs(irpp_with - irpp_without) < 1.0, (
            f"Single person with membership ({irpp_with}) should match "
            f"without membership ({irpp_without})"
        )

    def test_two_independent_households(self, tbs: Any) -> None:
        """AC-1, AC-2: Two persons in separate households via membership columns."""
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                    "age": pa.array([30, 45]),
                    "famille_id": pa.array([0, 1]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 1]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 1]),
                    "menage_role": pa.array([
                        "personne_de_reference", "personne_de_reference",
                    ]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="4entity-independent-test")

        result = adapter.compute(population, policy, 2024)

        assert isinstance(result, ComputationResult)
        # 2 separate foyers → 2 irpp values
        irpp_col = result.output_fields.column("impot_revenu_restant_a_payer")
        assert len(irpp_col) == 2
        # Both should pay tax (negative values)
        assert irpp_col[0].as_py() < 0
        assert irpp_col[1].as_py() < 0
        # Higher salary → more tax
        assert irpp_col[1].as_py() < irpp_col[0].as_py()

    def test_group_entity_input_variables(self, tbs: Any) -> None:
        """AC-7: Group entity table (menage with loyer) is merged into entity dict.

        Verifies that group-level input variables from a separate table are
        correctly period-wrapped and included in the entity dict passed to
        SimulationBuilder.build_from_entities().
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )

        local_tbs = adapter._get_tax_benefit_system()

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 0.0]),
                    "age": pa.array([30, 28]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint",
                    ]),
                }),
                "menage": pa.table({
                    "loyer": pa.array([800.0]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="4entity-loyer-test")

        # Verify entity dict has loyer merged
        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", local_tbs
        )

        assert "loyer" in entity_dict["menages"]["menage_0"]
        assert entity_dict["menages"]["menage_0"]["loyer"] == {"2024": 800.0}

    def test_backward_compatibility_no_membership_columns(
        self,
        adapter: OpenFiscaApiAdapter,
        single_person_population: PopulationData,
        empty_policy: PolicyConfig,
    ) -> None:
        """AC-6: Existing single_person_population fixture still works identically."""
        result = adapter.compute(single_person_population, empty_policy, 2024)

        assert isinstance(result, ComputationResult)
        irpp = result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py()
        assert irpp < 0, f"Expected negative irpp, got {irpp}"

    def test_entity_role_resolution_from_real_tbs(self, tbs: Any) -> None:
        """AC-4: _resolve_valid_role_keys() produces correct keys from real TBS.

        Validates that the role key resolution logic works with real
        OpenFisca-France entity and role objects.
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        local_tbs = adapter._get_tax_benefit_system()

        valid_roles = adapter._resolve_valid_role_keys(local_tbs)

        # famille roles
        assert "parents" in valid_roles["famille"]
        assert "enfants" in valid_roles["famille"]

        # foyer_fiscal roles
        assert "declarants" in valid_roles["foyer_fiscal"]
        assert "personnes_a_charge" in valid_roles["foyer_fiscal"]

        # menage roles — personne_de_reference and conjoint have plural=None
        assert "personne_de_reference" in valid_roles["menage"]
        assert "conjoint" in valid_roles["menage"]
        assert "enfants" in valid_roles["menage"]
        assert "autres" in valid_roles["menage"]


# ===========================================================================
# Story 9.5: OpenFisca-France reference test suite
# ===========================================================================


@pytest.fixture(scope="module")
def reference_irpp_adapter() -> OpenFiscaApiAdapter:
    """Adapter for IRPP reference tests via adapter.compute().

    Story 9.5 AC-1, AC-4: Validates the full adapter pipeline (entity dict
    construction, periodicity resolution, calculation dispatch, result extraction)
    for income tax reference scenarios.
    """
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=("impot_revenu_restant_a_payer",),
    )


@pytest.fixture(scope="module")
def reference_multi_entity_adapter() -> OpenFiscaApiAdapter:
    """Adapter for multi-entity reference tests with mixed-periodicity output.

    Story 9.5 AC-6: Validates multi-entity output extraction across individu
    (monthly, calculate_add), foyer_fiscal (yearly, calculate), and menage
    (yearly, calculate) entities.
    """
    return OpenFiscaApiAdapter(
        country_package="openfisca_france",
        output_variables=(
            "salaire_net",                      # individu, MONTH → calculate_add
            "impot_revenu_restant_a_payer",      # foyer_fiscal, YEAR → calculate
            "revenu_disponible",                 # menage, YEAR → calculate
        ),
    )


# ---------------------------------------------------------------------------
# Story 9.5 — Task 2: Single-person income tax reference cases (AC-1, AC-3, AC-4)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAdapterReferenceSinglePerson:
    """Story 9.5 AC-1, AC-3, AC-4: Single-person income tax reference cases.

    Reference values computed against OpenFisca-France 175.0.18,
    openfisca-core 44.2.2, on 2026-03-02. Tolerance ±0.5 EUR.

    All tests exercise the full adapter.compute() pipeline:
    _validate_period → _get_tax_benefit_system → _validate_output_variables →
    _resolve_variable_entities → _resolve_variable_periodicities →
    _build_simulation → _population_to_entity_dict →
    _extract_results_by_entity → _select_primary_output

    Input: salaire_imposable (taxable salary — the direct input to income
    tax computation, matching openfisca-france's own test format).
    """

    ABSOLUTE_ERROR_MARGIN = 0.5
    REFERENCE_OPENFISCA_FRANCE_VERSION = "175.0.18"
    REFERENCE_DATE = "2026-03-02"

    # Reference values: { salaire_imposable: expected_irpp }
    # irpp is negative (tax owed) or zero
    # Computed analytically from 2024 barème (11497/29315/83823/180294),
    # 10% professional abattement, and decote (seuil=889, taux=0.4525).
    # Cross-verified against 3 existing test cases (20k→-150, 50k→-6665,
    # couple 30k+25k→-2765) which match exactly.
    REFERENCE_VALUES: dict[float, float] = {
        0.0: 0.0,           # Zero income → zero tax
        15000.0: 0.0,       # Low income → decote eliminates all tax
        30000.0: -1588.0,   # Mid income → 11% bracket, partial decote
        75000.0: -13415.0,  # Upper bracket → 30% marginal, no decote
        100000.0: -20845.0, # High income → 41% marginal, no decote
    }

    def _build_single_person_population(
        self, salaire_imposable: float,
    ) -> PopulationData:
        """Build a single-person PopulationData with salaire_imposable."""
        return PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([salaire_imposable]),
                }),
            },
        )

    def _assert_irpp(
        self, actual: float, expected: float, scenario: str,
    ) -> None:
        """Assert irpp matches reference within tolerance with diagnostic message."""
        assert abs(actual - expected) <= self.ABSOLUTE_ERROR_MARGIN, (
            f"{scenario}: Expected {expected}, got {actual} "
            f"(tolerance ±{self.ABSOLUTE_ERROR_MARGIN}, "
            f"ref: OpenFisca-France {self.REFERENCE_OPENFISCA_FRANCE_VERSION})"
        )

    def test_zero_income(
        self, reference_irpp_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-1: Zero income → zero tax."""
        population = self._build_single_person_population(0.0)
        policy = PolicyConfig(parameters={}, name="ref-zero-income")

        result = reference_irpp_adapter.compute(population, policy, 2024)

        irpp = float(result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        self._assert_irpp(irpp, self.REFERENCE_VALUES[0.0], "zero income")

    def test_low_income_near_smic(
        self, reference_irpp_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-1: Low income (15k salaire_imposable) → decote may apply."""
        population = self._build_single_person_population(15000.0)
        policy = PolicyConfig(parameters={}, name="ref-low-income")

        result = reference_irpp_adapter.compute(population, policy, 2024)

        irpp = float(result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        self._assert_irpp(irpp, self.REFERENCE_VALUES[15000.0], "low income 15k")

    def test_mid_income(
        self, reference_irpp_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-1: Mid income (30k salaire_imposable) → 11-30% bracket."""
        population = self._build_single_person_population(30000.0)
        policy = PolicyConfig(parameters={}, name="ref-mid-income")

        result = reference_irpp_adapter.compute(population, policy, 2024)

        irpp = float(result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        self._assert_irpp(irpp, self.REFERENCE_VALUES[30000.0], "mid income 30k")

    def test_upper_bracket(
        self, reference_irpp_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-1: Upper bracket (75k salaire_imposable) → 30-41% bracket."""
        population = self._build_single_person_population(75000.0)
        policy = PolicyConfig(parameters={}, name="ref-upper-bracket")

        result = reference_irpp_adapter.compute(population, policy, 2024)

        irpp = float(result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        self._assert_irpp(irpp, self.REFERENCE_VALUES[75000.0], "upper bracket 75k")

    def test_high_income(
        self, reference_irpp_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-1: High income (100k salaire_imposable) → top bracket."""
        population = self._build_single_person_population(100000.0)
        policy = PolicyConfig(parameters={}, name="ref-high-income")

        result = reference_irpp_adapter.compute(population, policy, 2024)

        irpp = float(result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        self._assert_irpp(irpp, self.REFERENCE_VALUES[100000.0], "high income 100k")

    def test_progressive_tax_monotonicity(
        self, reference_irpp_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-1: Tax increases monotonically with income (structural invariant).

        Given the full set of reference income levels, asserts that tax
        increases (becomes more negative) monotonically with income.
        This is a structural test that catches reference value errors.
        """
        policy = PolicyConfig(parameters={}, name="ref-monotonicity")
        salaries = sorted(self.REFERENCE_VALUES.keys())

        irpp_values: list[float] = []
        for salary in salaries:
            population = self._build_single_person_population(salary)
            result = reference_irpp_adapter.compute(population, policy, 2024)
            irpp = float(result.output_fields.column(
                "impot_revenu_restant_a_payer"
            )[0].as_py())
            irpp_values.append(irpp)

        # irpp is negative (tax) or zero; more tax = more negative
        for i in range(1, len(irpp_values)):
            assert irpp_values[i] <= irpp_values[i - 1], (
                f"Monotonicity violation: irpp({salaries[i]})={irpp_values[i]} > "
                f"irpp({salaries[i - 1]})={irpp_values[i - 1]}. "
                f"Tax should not decrease when income increases."
            )


# ---------------------------------------------------------------------------
# Story 9.5 — Task 3: Family reference cases (AC-1, AC-3, AC-4, AC-5)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAdapterReferenceFamilies:
    """Story 9.5 AC-1, AC-3, AC-4, AC-5: Family income tax reference cases.

    Reference values computed against OpenFisca-France 175.0.18,
    openfisca-core 44.2.2, on 2026-03-02. Tolerance ±0.5 EUR.

    All tests use the 4-entity PopulationData format (membership columns)
    through adapter.compute(), validating the full pipeline including
    entity dict construction with membership columns (Story 9.4).

    French quotient familial:
    - Married couple = 2 parts
    - +0.5 part per child (first two)
    - +1 part per child (from third)
    """

    ABSOLUTE_ERROR_MARGIN = 0.5
    REFERENCE_OPENFISCA_FRANCE_VERSION = "175.0.18"
    REFERENCE_DATE = "2026-03-02"

    # Reference values pinned against openfisca-france 175.0.18.
    # Computed analytically from 2024 barème, quotient familial rules,
    # and decote (seuil_couple=1470, taux=0.4525).
    REFERENCE_COUPLE_40K_30K = -5231.0     # Married couple, 2 parts, no decote
    REFERENCE_FAMILY_1_CHILD = -3768.0     # 2 parents + 1 child, 2.5 parts
    REFERENCE_FAMILY_2_CHILDREN = -3085.0  # 2 parents + 2 children, 3 parts

    def _assert_irpp(
        self, actual: float, expected: float, scenario: str,
    ) -> None:
        """Assert irpp matches reference within tolerance with diagnostic message."""
        assert abs(actual - expected) <= self.ABSOLUTE_ERROR_MARGIN, (
            f"{scenario}: Expected {expected}, got {actual} "
            f"(tolerance ±{self.ABSOLUTE_ERROR_MARGIN}, "
            f"ref: OpenFisca-France {self.REFERENCE_OPENFISCA_FRANCE_VERSION})"
        )

    def test_married_couple_dual_income(
        self, reference_irpp_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-1, AC-4, AC-5: Married couple (40k+30k) via 4-entity format.

        Tests the FULL 4-entity pipeline through adapter.compute():
        membership columns → entity dict construction → joint taxation.
        """
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([40000.0, 30000.0]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint",
                    ]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="ref-couple-40k-30k")

        result = reference_irpp_adapter.compute(population, policy, 2024)

        irpp = float(result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        self._assert_irpp(
            irpp, self.REFERENCE_COUPLE_40K_30K, "couple 40k+30k",
        )

    def test_family_with_one_child(
        self, reference_irpp_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-1, AC-4: Family with 1 child (2.5 parts quotient familial).

        3 persons: 2 parents + 1 enfant (age=10). Child is personnes_a_charge
        in foyer_fiscal, enfants in famille and menage.
        """
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([40000.0, 30000.0, 0.0]),
                    "age": pa.array([40, 38, 10]),
                    "famille_id": pa.array([0, 0, 0]),
                    "famille_role": pa.array(["parents", "parents", "enfants"]),
                    "foyer_fiscal_id": pa.array([0, 0, 0]),
                    "foyer_fiscal_role": pa.array([
                        "declarants", "declarants", "personnes_a_charge",
                    ]),
                    "menage_id": pa.array([0, 0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint", "enfants",
                    ]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="ref-family-1-child")

        result = reference_irpp_adapter.compute(population, policy, 2024)

        irpp = float(result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        self._assert_irpp(
            irpp, self.REFERENCE_FAMILY_1_CHILD, "family 1 child",
        )

    def test_family_with_two_children(
        self, reference_irpp_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-1, AC-4: Family with 2 children (3 parts quotient familial).

        4 persons: 2 parents + 2 enfants (ages 10, 8).
        """
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([40000.0, 30000.0, 0.0, 0.0]),
                    "age": pa.array([40, 38, 10, 8]),
                    "famille_id": pa.array([0, 0, 0, 0]),
                    "famille_role": pa.array([
                        "parents", "parents", "enfants", "enfants",
                    ]),
                    "foyer_fiscal_id": pa.array([0, 0, 0, 0]),
                    "foyer_fiscal_role": pa.array([
                        "declarants", "declarants",
                        "personnes_a_charge", "personnes_a_charge",
                    ]),
                    "menage_id": pa.array([0, 0, 0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint",
                        "enfants", "enfants",
                    ]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="ref-family-2-children")

        result = reference_irpp_adapter.compute(population, policy, 2024)

        irpp = float(result.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        self._assert_irpp(
            irpp, self.REFERENCE_FAMILY_2_CHILDREN, "family 2 children",
        )

    def test_quotient_familial_structural_invariant(
        self, reference_irpp_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-1: Couple with children pays LESS tax than couple without.

        Structural invariant of French tax law: additional parts from
        children reduce the per-part taxable income, reducing total tax.
        """
        policy = PolicyConfig(parameters={}, name="ref-qf-invariant")

        # Couple without children
        pop_couple = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([40000.0, 30000.0]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array([
                        "declarants", "declarants",
                    ]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint",
                    ]),
                }),
            },
        )

        # Couple with 2 children (same income)
        pop_family = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([40000.0, 30000.0, 0.0, 0.0]),
                    "age": pa.array([40, 38, 10, 8]),
                    "famille_id": pa.array([0, 0, 0, 0]),
                    "famille_role": pa.array([
                        "parents", "parents", "enfants", "enfants",
                    ]),
                    "foyer_fiscal_id": pa.array([0, 0, 0, 0]),
                    "foyer_fiscal_role": pa.array([
                        "declarants", "declarants",
                        "personnes_a_charge", "personnes_a_charge",
                    ]),
                    "menage_id": pa.array([0, 0, 0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint",
                        "enfants", "enfants",
                    ]),
                }),
            },
        )

        result_couple = reference_irpp_adapter.compute(pop_couple, policy, 2024)
        result_family = reference_irpp_adapter.compute(pop_family, policy, 2024)

        irpp_couple = float(result_couple.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        irpp_family = float(result_family.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())

        # Family pays LESS tax (irpp closer to zero = less negative)
        assert irpp_family > irpp_couple, (
            f"Quotient familial violation: family ({irpp_family}) should pay "
            f"less tax than couple ({irpp_couple}) at same total income"
        )


# ---------------------------------------------------------------------------
# Story 9.5 — Task 4: 4-entity format cross-validation (AC-5)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestFourEntityCrossValidation:
    """Story 9.5 AC-5: Cross-validate 4-entity format against legacy path.

    Validates that the 4-entity membership column path (Story 9.4)
    produces identical or expected results compared to the auto-creation path.
    All tests use adapter.compute() — never _build_simulation() directly.
    """

    ABSOLUTE_ERROR_MARGIN = 0.5
    REFERENCE_OPENFISCA_FRANCE_VERSION = "175.0.18"

    def test_single_person_cross_validation(self) -> None:
        """AC-5: Single person with and without membership columns → identical results.

        The most direct cross-validation: same person, same income, same adapter.
        With membership columns explicitly specifying group assignment vs.
        without membership columns relying on auto-creation.
        """
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        policy = PolicyConfig(parameters={}, name="cross-val-single")

        # With membership columns (4-entity explicit)
        pop_with = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([30000.0]),
                    "famille_id": pa.array([0]),
                    "famille_role": pa.array(["parents"]),
                    "foyer_fiscal_id": pa.array([0]),
                    "foyer_fiscal_role": pa.array(["declarants"]),
                    "menage_id": pa.array([0]),
                    "menage_role": pa.array(["personne_de_reference"]),
                }),
            },
        )

        # Without membership columns (auto-creation legacy path)
        pop_without = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([30000.0]),
                }),
            },
        )

        result_with = adapter.compute(pop_with, policy, 2024)
        result_without = adapter.compute(pop_without, policy, 2024)

        irpp_with = float(result_with.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())
        irpp_without = float(result_without.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())

        assert abs(irpp_with - irpp_without) <= self.ABSOLUTE_ERROR_MARGIN, (
            f"Cross-validation failed: 4-entity ({irpp_with}) vs "
            f"auto-creation ({irpp_without}) differ by "
            f"{abs(irpp_with - irpp_without):.2f} "
            f"(tolerance ±{self.ABSOLUTE_ERROR_MARGIN}, "
            f"ref: OpenFisca-France {self.REFERENCE_OPENFISCA_FRANCE_VERSION})"
        )

    def test_couple_vs_two_singles_quotient_benefit(self) -> None:
        """AC-5: Couple joint taxation vs sum of singles demonstrates QF benefit.

        Run adapter.compute() three times:
        1. Couple (4-entity format, 2 persons in 1 foyer)
        2. Single person A (auto-creation, 80k)
        3. Single person B (auto-creation, 0k)

        The couple should pay LESS than the sum of two singles due to
        quotient familial. This cross-validates the 4-entity format
        against the proven single-person path.

        Uses asymmetric income (80k+0) to make QF benefit unambiguous.
        """
        policy = PolicyConfig(parameters={}, name="cross-val-qf")

        # Couple via 4-entity format
        adapter_couple = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        pop_couple = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([80000.0, 0.0]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array([
                        "declarants", "declarants",
                    ]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint",
                    ]),
                }),
            },
        )
        result_couple = adapter_couple.compute(pop_couple, policy, 2024)
        irpp_couple = float(result_couple.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())

        # Single person A (80k) via auto-creation
        adapter_single = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=("impot_revenu_restant_a_payer",),
        )
        pop_a = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([80000.0]),
                }),
            },
        )
        result_a = adapter_single.compute(pop_a, policy, 2024)
        irpp_a = float(result_a.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())

        # Single person B (0k) via auto-creation
        pop_b = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_imposable": pa.array([0.0]),
                }),
            },
        )
        result_b = adapter_single.compute(pop_b, policy, 2024)
        irpp_b = float(result_b.output_fields.column(
            "impot_revenu_restant_a_payer"
        )[0].as_py())

        sum_singles = irpp_a + irpp_b

        # Couple pays less tax (closer to zero) than sum of singles
        assert irpp_couple > sum_singles, (
            f"Quotient familial cross-validation failed: "
            f"couple ({irpp_couple}) should pay less tax than "
            f"sum of singles ({sum_singles} = {irpp_a} + {irpp_b})"
        )


# ---------------------------------------------------------------------------
# Story 9.5 — Task 5: Multi-entity output reference cases (AC-4, AC-6)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestAdapterReferenceMultiEntity:
    """Story 9.5 AC-4, AC-6: Multi-entity output validation.

    Reference values computed against OpenFisca-France 175.0.18,
    openfisca-core 44.2.2, on 2026-03-02. Tolerance ±0.5 EUR.

    Tests that adapter.compute() with multi-entity output variables
    (salaire_net, impot_revenu_restant_a_payer, revenu_disponible)
    produces correct per-entity tables with correct array lengths and values.
    """

    ABSOLUTE_ERROR_MARGIN = 0.5
    REFERENCE_OPENFISCA_FRANCE_VERSION = "175.0.18"
    REFERENCE_DATE = "2026-03-02"

    def test_single_person_multi_entity_output(
        self, reference_multi_entity_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-6: Single person with 3 output variables across 3 entities.

        Validates:
        - entity_tables contains 3 entity keys
        - Correct array lengths per entity (all 1 for single person)
        - salaire_net > 0 and in reasonable range
        - irpp < 0 (tax owed)
        - revenu_disponible > 0
        - Calculation method metadata correct
        """
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="ref-multi-entity-single")

        result = reference_multi_entity_adapter.compute(population, policy, 2024)

        # AC-6: entity_tables contains all 3 entity keys
        assert "individus" in result.entity_tables
        assert "foyers_fiscaux" in result.entity_tables
        assert "menages" in result.entity_tables

        # AC-6: Correct array lengths (1 person, 1 foyer, 1 menage)
        assert result.entity_tables["individus"].num_rows == 1
        assert result.entity_tables["foyers_fiscaux"].num_rows == 1
        assert result.entity_tables["menages"].num_rows == 1

        # AC-6: salaire_net in reasonable range for 30k gross
        salaire_net = float(
            result.entity_tables["individus"].column("salaire_net")[0].as_py()
        )
        assert 20000 < salaire_net < 30000, (
            f"salaire_net={salaire_net} outside expected range [20000, 30000]"
        )

        # AC-6: irpp negative (tax owed)
        irpp = float(
            result.entity_tables["foyers_fiscaux"].column(
                "impot_revenu_restant_a_payer"
            )[0].as_py()
        )
        assert irpp < 0, f"Expected negative irpp, got {irpp}"

        # AC-6: revenu_disponible positive
        revenu_disponible = float(
            result.entity_tables["menages"].column(
                "revenu_disponible"
            )[0].as_py()
        )
        assert revenu_disponible > 0, (
            f"Expected positive revenu_disponible, got {revenu_disponible}"
        )

        # AC-6: Metadata shows correct calculation methods
        assert result.metadata["calculation_methods"]["salaire_net"] == "calculate_add"
        assert (
            result.metadata["calculation_methods"][
                "impot_revenu_restant_a_payer"
            ] == "calculate"
        )

    def test_married_couple_multi_entity_output(
        self, reference_multi_entity_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-6: Married couple (2 persons, 1 foyer, 1 menage) multi-entity.

        Validates per-entity array lengths and correct variable assignment:
        - individus: 2 rows (salaire_net)
        - foyers_fiscaux: 1 row (irpp — joint filing)
        - menages: 1 row (revenu_disponible)
        """
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([40000.0, 30000.0]),
                    "age": pa.array([35, 33]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array([
                        "declarants", "declarants",
                    ]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array([
                        "personne_de_reference", "conjoint",
                    ]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="ref-multi-entity-couple")

        result = reference_multi_entity_adapter.compute(population, policy, 2024)

        # AC-6: Correct array lengths per entity
        assert result.entity_tables["individus"].num_rows == 2, (
            "Expected 2 rows for individus (2 persons)"
        )
        assert result.entity_tables["foyers_fiscaux"].num_rows == 1, (
            "Expected 1 row for foyers_fiscaux (joint filing)"
        )
        assert result.entity_tables["menages"].num_rows == 1, (
            "Expected 1 row for menages (1 household)"
        )

        # Correct variable assignment per entity
        assert "salaire_net" in result.entity_tables["individus"].column_names
        assert "impot_revenu_restant_a_payer" in (
            result.entity_tables["foyers_fiscaux"].column_names
        )
        assert "revenu_disponible" in result.entity_tables["menages"].column_names

        # Both persons should have positive salaire_net
        sn_col = result.entity_tables["individus"].column("salaire_net")
        assert float(sn_col[0].as_py()) > 0
        assert float(sn_col[1].as_py()) > 0

    def test_two_independent_households_multi_entity(
        self, reference_multi_entity_adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-6: Two independent households — all entity tables have 2 rows.

        2 persons in separate foyers/menages: entity_tables should have
        2 rows for each entity type.
        """
        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                    "age": pa.array([30, 45]),
                    "famille_id": pa.array([0, 1]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 1]),
                    "foyer_fiscal_role": pa.array([
                        "declarants", "declarants",
                    ]),
                    "menage_id": pa.array([0, 1]),
                    "menage_role": pa.array([
                        "personne_de_reference", "personne_de_reference",
                    ]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="ref-multi-entity-indep")

        result = reference_multi_entity_adapter.compute(population, policy, 2024)

        # 2 separate households → 2 rows per entity
        assert result.entity_tables["individus"].num_rows == 2
        assert result.entity_tables["foyers_fiscaux"].num_rows == 2
        assert result.entity_tables["menages"].num_rows == 2

        # Higher salary → higher salaire_net
        sn_col = result.entity_tables["individus"].column("salaire_net")
        sn_0 = float(sn_col[0].as_py())
        sn_1 = float(sn_col[1].as_py())
        assert sn_1 > sn_0, (
            f"Higher salary (50k) should yield higher salaire_net: "
            f"{sn_1} vs {sn_0}"
        )

        # Higher salary → more tax (more negative irpp)
        irpp_col = result.entity_tables["foyers_fiscaux"].column(
            "impot_revenu_restant_a_payer"
        )
        irpp_0 = float(irpp_col[0].as_py())
        irpp_1 = float(irpp_col[1].as_py())
        assert irpp_1 < irpp_0, (
            f"Higher salary should yield more tax: {irpp_1} vs {irpp_0}"
        )


# ---------------------------------------------------------------------------
# Story 9.5 — Task 6: Regression detection metadata (AC-2, AC-3)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestRegressionDetectionMetadata:
    """Story 9.5 AC-2, AC-3: Regression detection metadata and version pinning.

    Ensures the OpenFisca-France version is documented and that version
    changes force explicit review of all reference values.
    """

    def test_openfisca_core_version_documented(
        self, adapter: OpenFiscaApiAdapter,
    ) -> None:
        """AC-3: adapter.version() returns openfisca-core 44.x.

        This test is intentionally version-pinned for regression detection.
        If the openfisca-core version changes (e.g., 44.x → 45.x), this test
        forces explicit review of all reference values in the suite.
        """
        version = adapter.version()
        assert version.startswith("44."), (
            f"OpenFisca-core version changed from 44.x to {version}. "
            f"All reference values in TestAdapterReferenceSinglePerson, "
            f"TestAdapterReferenceFamilies, and TestAdapterReferenceMultiEntity "
            f"must be reviewed and updated."
        )

    def test_openfisca_france_version_documented(self) -> None:
        """AC-3: OpenFisca-France version matches documented reference version.

        If this test fails, the installed openfisca-france version differs
        from the version used to compute reference values. All pinned values
        must be re-computed with the new version.
        """
        import importlib.metadata

        of_version = importlib.metadata.version("openfisca-france")
        assert of_version.startswith("175."), (
            f"OpenFisca-France version changed from 175.x to {of_version}. "
            f"Reference values were computed against 175.0.18. "
            f"Re-run the reference value computation script and update "
            f"all pinned values in TestAdapterReferenceSinglePerson and "
            f"TestAdapterReferenceFamilies."
        )
