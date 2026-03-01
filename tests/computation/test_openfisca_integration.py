"""Integration tests for OpenFiscaApiAdapter against real OpenFisca-France.

Story 8.1: End-to-End OpenFisca Integration Spike.
Story 9.2: Multi-entity output array handling integration tests.

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

        # Build simulation and extract results by entity
        builder = SimulationBuilder()
        simulation = builder.build_from_entities(tbs, entities_dict)

        entity_tables = multi_entity_adapter._extract_results_by_entity(
            simulation, 2024, vars_by_entity
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
