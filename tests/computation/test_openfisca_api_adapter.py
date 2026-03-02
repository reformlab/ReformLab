"""Tests for OpenFiscaApiAdapter (Story 1.6: Direct OpenFisca API mode).

All OpenFisca internals are mocked since openfisca-core is an optional
dependency and may not be installed in CI.

Story 9.2: Added tests for multi-entity output array handling — entity-aware
result extraction, per-entity tables, and backward compatibility.

Story 9.4: Added tests for 4-entity PopulationData format with membership
columns — detect membership columns, resolve valid role keys, validate entity
relationships, and refactored _population_to_entity_dict() for 4-entity mode.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pyarrow as pa
import pytest

np = pytest.importorskip("numpy")

from reformlab.computation.adapter import ComputationAdapter
from reformlab.computation.exceptions import ApiMappingError, CompatibilityError
from reformlab.computation.openfisca_api_adapter import OpenFiscaApiAdapter
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData

# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

# Install a fake openfisca_core.simulation_builder module so that
# `from openfisca_core.simulation_builder import SimulationBuilder`
# inside _build_simulation can be patched. We register it once in
# sys.modules so the import succeeds, then individual tests patch
# the SimulationBuilder attribute.

_mock_sim_builder_module = MagicMock()
sys.modules.setdefault("openfisca_core", MagicMock())
sys.modules.setdefault("openfisca_core.simulation_builder", _mock_sim_builder_module)


def _make_mock_tbs(
    entity_keys: tuple[str, ...] = ("persons", "households"),
    variable_names: tuple[str, ...] = ("income_tax", "carbon_tax", "salary"),
    person_entity: str = "persons",
) -> MagicMock:
    """Create a mock TaxBenefitSystem with configurable entities and variables."""
    tbs = MagicMock()

    entities = []
    entities_by_key: dict[str, SimpleNamespace] = {}
    for key in entity_keys:
        entity = SimpleNamespace(key=key, plural=key, is_person=(key == person_entity))
        entities.append(entity)
        entities_by_key[key] = entity
    tbs.entities = entities

    # Variables get a default entity (the person entity) for backward compatibility
    # with existing tests that don't need entity-aware behavior.
    # Story 9.3: Also set definition_period = "year" by default. Without this,
    # MagicMock().definition_period returns a MagicMock object whose str()
    # representation ("<MagicMock ...>") is not in _VALID_PERIODICITIES, causing
    # _resolve_variable_periodicities() to raise ApiMappingError("Unexpected
    # periodicity...") and breaking all existing compute() unit tests.
    default_entity = entities_by_key.get(person_entity, entities[0])
    variables: dict[str, Any] = {}
    for name in variable_names:
        var_mock = MagicMock()
        var_mock.entity = default_entity
        var_mock.definition_period = "year"
        variables[name] = var_mock
    tbs.variables = variables

    return tbs


def _make_mock_tbs_with_entities(
    entity_keys: tuple[str, ...] = ("individu", "foyer_fiscal", "menage"),
    entity_plurals: dict[str, str] | None = None,
    variable_entities: dict[str, str] | None = None,
    variable_periodicities: dict[str, str] | None = None,
    person_entity: str = "individu",
    entity_roles: dict[str, list[dict[str, str | None]]] | None = None,
) -> MagicMock:
    """Create a mock TBS where variables know their entity.

    Story 9.2: Extended mock for entity-aware extraction tests.
    Story 9.3: Added variable_periodicities parameter for periodicity-aware tests.
    Story 9.4: Added entity_roles parameter for 4-entity format tests.

    Args:
        entity_keys: Entity singular keys.
        entity_plurals: Mapping of singular key to plural form.
            Defaults to appending "s" (with special cases).
        variable_entities: Mapping of variable name to entity key.
        variable_periodicities: Mapping of variable name to periodicity string
            (e.g. "month", "year", "eternity"). Defaults to "year" for all.
        person_entity: Which entity key is the person entity.
        entity_roles: Mapping of group entity key to list of role dicts.
            Each role dict has "key" and "plural" (can be None).
            E.g. {"famille": [{"key": "parent", "plural": "parents"}, ...]}.
            Person entity gets empty roles list.

    Returns:
        Mock TBS with entity-aware variables and role information.
    """
    tbs = MagicMock()

    # Default plurals for French entities
    default_plurals = {
        "individu": "individus",
        "famille": "familles",
        "foyer_fiscal": "foyers_fiscaux",
        "menage": "menages",
    }
    if entity_plurals is None:
        entity_plurals = {}
    if variable_periodicities is None:
        variable_periodicities = {}
    if entity_roles is None:
        entity_roles = {}

    entities_by_key: dict[str, SimpleNamespace] = {}
    entities = []
    for key in entity_keys:
        plural = entity_plurals.get(key) or default_plurals.get(key) or key + "s"
        is_person = key == person_entity

        # Story 9.4: Build role objects for group entities
        roles: list[SimpleNamespace] = []
        if not is_person and key in entity_roles:
            for role_def in entity_roles[key]:
                roles.append(SimpleNamespace(
                    key=role_def["key"],
                    plural=role_def.get("plural"),
                ))

        entity = SimpleNamespace(
            key=key,
            plural=plural,
            is_person=is_person,
            roles=roles,
        )
        entities.append(entity)
        entities_by_key[key] = entity
    tbs.entities = entities

    # Build variables with entity references
    # Story 9.3: Also set definition_period (default "year" for backward compat)
    if variable_entities is None:
        variable_entities = {}
    variables: dict[str, Any] = {}
    for var_name, entity_key in variable_entities.items():
        var_mock = MagicMock()
        var_mock.entity = entities_by_key[entity_key]
        var_mock.definition_period = variable_periodicities.get(var_name, "year")
        variables[var_name] = var_mock
    tbs.variables = variables

    return tbs


# Story 9.4: Standard French entity roles for reuse across test classes
_FRENCH_ENTITY_ROLES: dict[str, list[dict[str, str | None]]] = {
    "famille": [
        {"key": "parent", "plural": "parents"},
        {"key": "enfant", "plural": "enfants"},
    ],
    "foyer_fiscal": [
        {"key": "declarant", "plural": "declarants"},
        {"key": "personne_a_charge", "plural": "personnes_a_charge"},
    ],
    "menage": [
        {"key": "personne_de_reference", "plural": None},
        {"key": "conjoint", "plural": None},
        {"key": "enfant", "plural": "enfants"},
        {"key": "autre", "plural": "autres"},
    ],
}


def _make_mock_simulation(
    results: dict[str, np.ndarray],
) -> MagicMock:
    """Create a mock Simulation that returns given arrays for calculate()."""
    sim = MagicMock()
    sim.calculate.side_effect = lambda var, period: results[var]
    return sim


def _patch_simulation_builder(mock_builder_instance: MagicMock):  # type: ignore[no-untyped-def]
    """Patch SimulationBuilder in the fake openfisca_core.simulation_builder module."""
    return patch.object(
        _mock_sim_builder_module,
        "SimulationBuilder",
        return_value=mock_builder_instance,
    )


@pytest.fixture()
def sample_population() -> PopulationData:
    return PopulationData(
        tables={
            "persons": pa.table(
                {
                    "person_id": pa.array([1, 2, 3]),
                    "salary": pa.array([30000.0, 45000.0, 60000.0]),
                }
            ),
        },
        metadata={"source": "test"},
    )


@pytest.fixture()
def sample_policy() -> PolicyConfig:
    return PolicyConfig(
        parameters={"salary": 35000.0},
        name="test-policy",
    )


@pytest.fixture()
def empty_policy() -> PolicyConfig:
    return PolicyConfig(parameters={}, name="no-params")


# ---------------------------------------------------------------------------
# AC-7: Protocol compliance
# ---------------------------------------------------------------------------


class TestProtocolCompliance:
    """AC-7: isinstance(OpenFiscaApiAdapter(...), ComputationAdapter) returns True."""

    def test_isinstance_check(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert isinstance(adapter, ComputationAdapter)

    def test_has_compute_method(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert callable(getattr(adapter, "compute", None))

    def test_has_version_method(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert callable(getattr(adapter, "version", None))


# ---------------------------------------------------------------------------
# AC-2: Version-pinned execution
# ---------------------------------------------------------------------------


class TestVersionChecking:
    """AC-2: Version validation reuses shared logic from openfisca_common."""

    def test_supported_version_passes(self) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaApiAdapter(output_variables=("income_tax",))
            assert adapter.version() == "44.2.2"

    def test_unsupported_version_raises(self) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="30.0.0",
        ):
            with pytest.raises(CompatibilityError) as exc_info:
                OpenFiscaApiAdapter(output_variables=("income_tax",))
            assert "30.0.0" in str(exc_info.value)

    def test_skip_version_check(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        assert adapter.version() == "unknown"


# ---------------------------------------------------------------------------
# AC-8: Graceful degradation when OpenFisca not installed
# ---------------------------------------------------------------------------


class TestGracefulDegradation:
    """AC-8: Missing openfisca-core raises CompatibilityError, not ImportError."""

    def test_not_installed_raises_compatibility_error(self) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="not-installed",
        ):
            with pytest.raises(CompatibilityError) as exc_info:
                OpenFiscaApiAdapter(output_variables=("income_tax",))
            assert "not installed" in str(exc_info.value).lower()
            assert exc_info.value.actual == "not-installed"

    def test_not_installed_is_not_import_error(self) -> None:
        """Verify the error type is CompatibilityError, NOT ImportError."""
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="not-installed",
        ):
            with pytest.raises(CompatibilityError):
                OpenFiscaApiAdapter(output_variables=("income_tax",))


# ---------------------------------------------------------------------------
# AC-3: TaxBenefitSystem configuration (lazy loading + caching)
# ---------------------------------------------------------------------------


class TestTaxBenefitSystemLoading:
    """AC-3: Country package is imported, TBS is instantiated and cached."""

    def test_missing_country_package_raises_compatibility_error(self) -> None:
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_nonexistent",
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        with patch(
            "importlib.import_module",
            side_effect=ImportError("No module named 'openfisca_nonexistent'"),
        ):
            with pytest.raises(CompatibilityError) as exc_info:
                adapter._get_tax_benefit_system()
            assert "openfisca_nonexistent" in str(exc_info.value)
            assert "not-installed" == exc_info.value.actual

    def test_tbs_is_cached_after_first_load(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        mock_module = MagicMock()
        mock_module.CountryTaxBenefitSystem.return_value = mock_tbs

        with patch(
            "importlib.import_module",
            return_value=mock_module,
        ) as mock_import:
            tbs1 = adapter._get_tax_benefit_system()
            tbs2 = adapter._get_tax_benefit_system()

            assert tbs1 is tbs2
            mock_import.assert_called_once()


# ---------------------------------------------------------------------------
# AC-1: Live computation via OpenFisca Python API
# ---------------------------------------------------------------------------


class TestCompute:
    """AC-1: compute() invokes SimulationBuilder and Simulation.calculate()."""

    def test_compute_returns_computation_result(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert isinstance(result, ComputationResult)
        assert isinstance(result.output_fields, pa.Table)
        assert result.period == 2025
        assert result.output_fields.num_rows == 3
        assert result.output_fields.column_names == ["income_tax"]

    def test_compute_with_policy_parameters(
        self, sample_population: PopulationData, sample_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3500.0, 3500.0, 3500.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, sample_policy, 2025)

        assert isinstance(result, ComputationResult)
        call_args = mock_builder_instance.build_from_entities.call_args
        entities_dict = call_args[0][1]
        for instance_data in entities_dict["persons"].values():
            assert "salary" in instance_data

    def test_compute_multiple_output_variables(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax", "carbon_tax"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {
                "income_tax": np.array([3000.0, 6750.0, 12000.0]),
                "carbon_tax": np.array([134.0, 200.0, 267.0]),
            }
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.output_fields.column_names == ["income_tax", "carbon_tax"]
        assert result.output_fields.num_rows == 3


# ---------------------------------------------------------------------------
# AC-4: Variable selection — unknown variables raise structured error
# ---------------------------------------------------------------------------


class TestOutputVariableValidation:
    """AC-4: Unknown variable names raise a clear error before computation."""

    def test_unknown_variable_raises_api_mapping_error(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax", "nonexistent_var"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "carbon_tax", "salary"))

        with pytest.raises(ApiMappingError) as exc_info:
            adapter._validate_output_variables(mock_tbs)

        assert "nonexistent_var" in str(exc_info.value)
        assert exc_info.value.invalid_names == ("nonexistent_var",)

    def test_valid_variables_pass_validation(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "carbon_tax"))
        adapter._validate_output_variables(mock_tbs)

    def test_suggestions_for_close_matches(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("incme_tax",),  # typo
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "carbon_tax", "salary"))

        with pytest.raises(ApiMappingError) as exc_info:
            adapter._validate_output_variables(mock_tbs)

        assert "incme_tax" in exc_info.value.invalid_names
        assert len(exc_info.value.suggestions) > 0

    def test_empty_output_variables_raises_error(self) -> None:
        """Empty output_variables tuple raises ApiMappingError at construction time."""
        with pytest.raises(ApiMappingError) as exc_info:
            OpenFiscaApiAdapter(
                output_variables=(),
                skip_version_check=True,
            )
        assert "Empty output_variables" in exc_info.value.summary


# ---------------------------------------------------------------------------
# AC-5: Period mapping
# ---------------------------------------------------------------------------


class TestPeriodFormatting:
    """AC-5: Integer period is correctly passed as OpenFisca period string."""

    def test_period_passed_as_string(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            adapter.compute(sample_population, empty_policy, 2025)

        mock_simulation.calculate.assert_called_once_with("income_tax", "2025")


# ---------------------------------------------------------------------------
# AC-6: ComputationResult compatibility
# ---------------------------------------------------------------------------


class TestComputationResultStructure:
    """AC-6: Result has correct metadata and structure."""

    def test_metadata_source_is_api(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.metadata["source"] == "api"

    def test_adapter_version_in_result(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        with patch(
            "reformlab.computation.openfisca_api_adapter._detect_openfisca_version",
            return_value="44.2.2",
        ):
            adapter = OpenFiscaApiAdapter(output_variables=("income_tax",))

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.adapter_version == "44.2.2"

    def test_output_fields_is_pyarrow_table(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert isinstance(result.output_fields, pa.Table)

    def test_metadata_includes_required_fields(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert "timing_seconds" in result.metadata
        assert "row_count" in result.metadata
        assert "source" in result.metadata
        assert "policy_name" in result.metadata
        assert "country_package" in result.metadata
        assert "output_variables" in result.metadata
        assert result.metadata["row_count"] == 3
        assert result.metadata["country_package"] == "openfisca_france"
        assert result.metadata["output_variables"] == ["income_tax"]

    def test_period_is_correct(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        assert result.period == 2025


# ---------------------------------------------------------------------------
# AC-9: Coexistence with pre-computed mode
# ---------------------------------------------------------------------------


class TestCoexistence:
    """AC-9: Both adapters instantiate independently."""

    def test_both_adapters_instantiate(self, tmp_path: object) -> None:
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

        pre_computed = OpenFiscaAdapter(data_dir=str(tmp_path), skip_version_check=True)
        api_adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        assert isinstance(pre_computed, ComputationAdapter)
        assert isinstance(api_adapter, ComputationAdapter)
        assert type(pre_computed) is not type(api_adapter)

    def test_adapters_do_not_share_state(self, tmp_path: object) -> None:
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

        pre_computed = OpenFiscaAdapter(data_dir=str(tmp_path), skip_version_check=True)
        api_adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        # Both return "unknown" when skip_version_check=True
        assert pre_computed.version() == "unknown"
        assert api_adapter.version() == "unknown"
        # They are distinct objects with no shared mutable state
        assert pre_computed is not api_adapter


# ---------------------------------------------------------------------------
# Entity mapping errors
# ---------------------------------------------------------------------------


class TestEntityMapping:
    """Entity keys in PopulationData must match TBS entity names."""

    def test_unknown_entity_raises_api_mapping_error(
        self, sample_policy: PolicyConfig
    ) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(entity_keys=("persons", "households"))
        adapter._tax_benefit_system = mock_tbs

        bad_population = PopulationData(
            tables={
                "unknown_entity": pa.table({"x": pa.array([1])}),
            },
        )

        mock_builder_instance = MagicMock()
        with _patch_simulation_builder(mock_builder_instance):
            with pytest.raises(ApiMappingError) as exc_info:
                adapter.compute(bad_population, sample_policy, 2025)

        assert "unknown_entity" in str(exc_info.value)
        assert exc_info.value.invalid_names == ("unknown_entity",)

    def test_unknown_policy_parameter_raises_api_mapping_error(self) -> None:
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs(variable_names=("income_tax", "salary"))
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "persons": pa.table({"salary": pa.array([30000.0])}),
            },
        )
        bad_policy = PolicyConfig(
            parameters={"nonexistent_param": 100.0},
            name="bad-policy",
        )

        mock_builder_instance = MagicMock()
        with _patch_simulation_builder(mock_builder_instance):
            with pytest.raises(ApiMappingError) as exc_info:
                adapter.compute(population, bad_policy, 2025)

        assert "nonexistent_param" in str(exc_info.value)


# ===========================================================================
# Story 9.2: Multi-entity output array handling
# ===========================================================================


class TestResolveVariableEntities:
    """Story 9.2 AC-1, AC-2, AC-5: Variable-to-entity mapping from TBS."""

    def test_groups_variables_by_entity(self) -> None:
        """AC-1: Variables are correctly grouped by their entity."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp", "revenu_disponible"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
                "revenu_disponible": "menage",
            },
        )
        adapter._tax_benefit_system = mock_tbs

        result = adapter._resolve_variable_entities(mock_tbs)

        assert "individus" in result
        assert "foyers_fiscaux" in result
        assert "menages" in result
        assert result["individus"] == ["salaire_net"]
        assert result["foyers_fiscaux"] == ["irpp"]
        assert result["menages"] == ["revenu_disponible"]

    def test_multiple_variables_same_entity(self) -> None:
        """AC-1: Multiple variables on the same entity are grouped together."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "age"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "age": "individu",
            },
        )
        adapter._tax_benefit_system = mock_tbs

        result = adapter._resolve_variable_entities(mock_tbs)

        assert len(result) == 1
        assert "individus" in result
        assert result["individus"] == ["salaire_net", "age"]

    def test_variable_without_entity_raises_error(self) -> None:
        """AC-5: Variable with no .entity attribute raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("broken_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={},
        )
        # Add a variable without entity attribute
        var_mock = MagicMock()
        var_mock.entity = None
        mock_tbs.variables["broken_var"] = var_mock

        with pytest.raises(ApiMappingError, match="Cannot determine entity"):
            adapter._resolve_variable_entities(mock_tbs)

    def test_variable_not_in_tbs_raises_error(self) -> None:
        """AC-5: Variable not in TBS raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("nonexistent_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={},
        )
        # TBS has no variables at all

        with pytest.raises(ApiMappingError, match="Cannot resolve variable entity"):
            adapter._resolve_variable_entities(mock_tbs)


class TestExtractResultsByEntity:
    """Story 9.2 AC-1, AC-2, AC-3: Per-entity result extraction."""

    def test_single_entity_extraction(self) -> None:
        """AC-1: Single entity produces one table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net",),
            skip_version_check=True,
        )
        mock_simulation = _make_mock_simulation(
            {"salaire_net": np.array([20000.0, 35000.0])}
        )
        vars_by_entity = {"individus": ["salaire_net"]}
        # Story 9.3: Pass variable_periodicities (required parameter)
        variable_periodicities = {"salaire_net": "year"}

        result = adapter._extract_results_by_entity(
            mock_simulation, 2024, vars_by_entity, variable_periodicities
        )

        assert "individus" in result
        assert result["individus"].num_rows == 2
        assert result["individus"].column_names == ["salaire_net"]

    def test_multi_entity_extraction(self) -> None:
        """AC-2, AC-3: Different entities produce separate tables with correct lengths."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp", "revenu_disponible"),
            skip_version_check=True,
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "irpp": np.array([-1500.0]),
            "revenu_disponible": np.array([40000.0]),
        })
        vars_by_entity = {
            "individus": ["salaire_net"],
            "foyers_fiscaux": ["irpp"],
            "menages": ["revenu_disponible"],
        }
        # Story 9.3: Pass variable_periodicities (required parameter)
        variable_periodicities = {
            "salaire_net": "year",
            "irpp": "year",
            "revenu_disponible": "year",
        }

        result = adapter._extract_results_by_entity(
            mock_simulation, 2024, vars_by_entity, variable_periodicities
        )

        assert len(result) == 3
        assert result["individus"].num_rows == 2
        assert result["foyers_fiscaux"].num_rows == 1
        assert result["menages"].num_rows == 1

    def test_multiple_variables_per_entity(self) -> None:
        """AC-3: Multiple variables on same entity are in the same table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "age"),
            skip_version_check=True,
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "age": np.array([30.0, 45.0]),
        })
        vars_by_entity = {"individus": ["salaire_net", "age"]}
        # Story 9.3: Pass variable_periodicities (required parameter)
        variable_periodicities = {"salaire_net": "year", "age": "year"}

        result = adapter._extract_results_by_entity(
            mock_simulation, 2024, vars_by_entity, variable_periodicities
        )

        assert result["individus"].num_rows == 2
        assert set(result["individus"].column_names) == {"salaire_net", "age"}


class TestSelectPrimaryOutput:
    """Story 9.2 AC-4: Primary output_fields selection for backward compatibility."""

    def test_single_entity_returns_that_table(self) -> None:
        """AC-4: With one entity, output_fields is that entity's table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net",),
            skip_version_check=True,
        )
        person_table = pa.table({"salaire_net": pa.array([20000.0, 35000.0])})
        mock_tbs = _make_mock_tbs_with_entities()

        result = adapter._select_primary_output({"individus": person_table}, mock_tbs)

        assert result is person_table

    def test_multi_entity_returns_person_table(self) -> None:
        """AC-4: With multiple entities, output_fields is the person-entity table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )
        person_table = pa.table({"salaire_net": pa.array([20000.0, 35000.0])})
        foyer_table = pa.table({"irpp": pa.array([-1500.0])})
        mock_tbs = _make_mock_tbs_with_entities()

        result = adapter._select_primary_output(
            {"individus": person_table, "foyers_fiscaux": foyer_table},
            mock_tbs,
        )

        assert result is person_table

    def test_multi_entity_without_person_returns_first(self) -> None:
        """AC-4: Without person entity in results, returns first entity's table."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("irpp", "revenu_disponible"),
            skip_version_check=True,
        )
        foyer_table = pa.table({"irpp": pa.array([-1500.0])})
        menage_table = pa.table({"revenu_disponible": pa.array([40000.0])})
        mock_tbs = _make_mock_tbs_with_entities()

        result = adapter._select_primary_output(
            {"foyers_fiscaux": foyer_table, "menages": menage_table},
            mock_tbs,
        )

        assert result is foyer_table


# ===========================================================================
# Story 9.3: Variable periodicity handling
# ===========================================================================


def _make_mock_simulation_with_methods(
    results: dict[str, np.ndarray],
) -> MagicMock:
    """Mock simulation that tracks calculate vs calculate_add calls.

    Story 9.3: Used for periodicity dispatch verification.
    """
    sim = MagicMock()
    sim.calculate.side_effect = lambda var, period: results[var]
    sim.calculate_add.side_effect = lambda var, period: results[var]
    return sim


class TestResolveVariablePeriodicities:
    """Story 9.3 AC-1, AC-2, AC-6: Periodicity detection from TBS variables."""

    def test_detects_yearly_periodicity(self) -> None:
        """AC-1: Yearly variable detected correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("irpp",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={"irpp": "foyer_fiscal"},
            variable_periodicities={"irpp": "year"},
        )

        result = adapter._resolve_variable_periodicities(mock_tbs)

        assert result == {"irpp": "year"}

    def test_detects_monthly_periodicity(self) -> None:
        """AC-2: Monthly variable detected correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={"salaire_net": "individu"},
            variable_periodicities={"salaire_net": "month"},
        )

        result = adapter._resolve_variable_periodicities(mock_tbs)

        assert result == {"salaire_net": "month"}

    def test_detects_eternity_periodicity(self) -> None:
        """AC-6: Eternity variable detected correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("date_naissance",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={"date_naissance": "individu"},
            variable_periodicities={"date_naissance": "eternity"},
        )

        result = adapter._resolve_variable_periodicities(mock_tbs)

        assert result == {"date_naissance": "eternity"}

    def test_detects_mixed_periodicities(self) -> None:
        """AC-1, AC-2, AC-6: Mixed periodicities detected for multiple variables."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp", "date_naissance"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
                "date_naissance": "individu",
            },
            variable_periodicities={
                "salaire_net": "month",
                "irpp": "year",
                "date_naissance": "eternity",
            },
        )

        result = adapter._resolve_variable_periodicities(mock_tbs)

        assert result == {
            "salaire_net": "month",
            "irpp": "year",
            "date_naissance": "eternity",
        }

    def test_missing_definition_period_raises_error(self) -> None:
        """AC-1: Variable with no definition_period attribute raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("broken_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={},
        )
        # Add variable without definition_period (set to None explicitly)
        var_mock = MagicMock()
        var_mock.entity = SimpleNamespace(key="individu", plural="individus", is_person=True)
        var_mock.definition_period = None
        mock_tbs.variables["broken_var"] = var_mock

        with pytest.raises(ApiMappingError, match="Cannot determine periodicity"):
            adapter._resolve_variable_periodicities(mock_tbs)

    def test_unexpected_periodicity_raises_error(self) -> None:
        """AC-1: Variable with unexpected periodicity value raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("broken_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={},
        )
        var_mock = MagicMock()
        var_mock.entity = SimpleNamespace(key="individu", plural="individus", is_person=True)
        var_mock.definition_period = "invalid_period"
        mock_tbs.variables["broken_var"] = var_mock

        with pytest.raises(ApiMappingError, match="Unexpected periodicity"):
            adapter._resolve_variable_periodicities(mock_tbs)

    def test_day_periodicity_detected(self) -> None:
        """AC-1: Day periodicity is detected correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("daily_var",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={"daily_var": "individu"},
            variable_periodicities={"daily_var": "day"},
        )

        result = adapter._resolve_variable_periodicities(mock_tbs)

        assert result == {"daily_var": "day"}


class TestCalculateVariable:
    """Story 9.3 AC-1, AC-2, AC-6: Calculation dispatch based on periodicity."""

    def test_yearly_uses_calculate(self) -> None:
        """AC-1: Yearly variables use simulation.calculate()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("irpp",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"irpp": np.array([-1500.0])}
        )

        result = adapter._calculate_variable(sim, "irpp", "2024", "year")

        sim.calculate.assert_called_once_with("irpp", "2024")
        sim.calculate_add.assert_not_called()
        assert result[0] == -1500.0

    def test_monthly_uses_calculate_add(self) -> None:
        """AC-2: Monthly variables use simulation.calculate_add()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"salaire_net": np.array([24000.0])}
        )

        result = adapter._calculate_variable(sim, "salaire_net", "2024", "month")

        sim.calculate_add.assert_called_once_with("salaire_net", "2024")
        sim.calculate.assert_not_called()
        assert result[0] == 24000.0

    def test_eternity_uses_calculate(self) -> None:
        """AC-6: Eternity variables use simulation.calculate(), NOT calculate_add()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("date_naissance",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"date_naissance": np.array([19960101])}
        )

        adapter._calculate_variable(sim, "date_naissance", "2024", "eternity")

        sim.calculate.assert_called_once_with("date_naissance", "2024")
        sim.calculate_add.assert_not_called()

    def test_day_uses_calculate_add(self) -> None:
        """AC-1: Day-period variables use simulation.calculate_add()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("daily_var",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"daily_var": np.array([365.0])}
        )

        adapter._calculate_variable(sim, "daily_var", "2024", "day")

        sim.calculate_add.assert_called_once_with("daily_var", "2024")
        sim.calculate.assert_not_called()

    def test_week_uses_calculate_add(self) -> None:
        """AC-1: Week-period variables use simulation.calculate_add()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("weekly_var",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"weekly_var": np.array([52.0])}
        )

        adapter._calculate_variable(sim, "weekly_var", "2024", "week")

        sim.calculate_add.assert_called_once_with("weekly_var", "2024")
        sim.calculate.assert_not_called()

    def test_weekday_uses_calculate_add(self) -> None:
        """AC-1: Weekday-period variables use simulation.calculate_add()."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("weekday_var",),
            skip_version_check=True,
        )
        sim = _make_mock_simulation_with_methods(
            {"weekday_var": np.array([260.0])}
        )

        adapter._calculate_variable(sim, "weekday_var", "2024", "weekday")

        sim.calculate_add.assert_called_once_with("weekday_var", "2024")
        sim.calculate.assert_not_called()


class TestPeriodValidation:
    """Story 9.3 AC-3: Invalid period format rejection."""

    def test_zero_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Period of 0 raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, 0)

    def test_negative_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Negative period raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, -1)

    def test_two_digit_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Two-digit period (99) raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, 99)

    def test_five_digit_period_raises_error(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Five-digit period (99999) raises ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, 99999)

    def test_valid_period_2024_passes(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Valid period (2024) passes validation."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2024)

        assert result.period == 2024

    def test_valid_period_1000_passes(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Edge case — period 1000 (minimum valid) passes."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 1000)

        assert result.period == 1000

    def test_valid_period_9999_passes(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Edge case — period 9999 (maximum valid) passes."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 9999)

        assert result.period == 9999

    def test_period_error_includes_actual_value(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Error message includes the actual invalid value."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        with pytest.raises(ApiMappingError) as exc_info:
            adapter.compute(sample_population, empty_policy, 42)

        assert "42" in exc_info.value.reason
        assert "Invalid period" in exc_info.value.summary

    def test_period_validation_precedes_tbs_loading(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-3: Period validation fires BEFORE any TBS operations.

        AC-3 requires the period check to be "the very first check before any
        TBS operations". This test verifies the ordering constraint by NOT
        pre-loading the TBS — if _validate_period() truly runs first, the TBS
        will still be None after the ApiMappingError is raised.
        """
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        # Deliberately do NOT pre-load TBS — if validation runs first,
        # the TBS will still be None after the error.
        assert adapter._tax_benefit_system is None

        with pytest.raises(ApiMappingError, match="Invalid period"):
            adapter.compute(sample_population, empty_policy, 0)

        # Confirm TBS was never loaded — period check was genuinely first.
        assert adapter._tax_benefit_system is None


class TestPeriodicityMetadata:
    """Story 9.3 AC-5: Periodicity metadata in compute() result."""

    def test_variable_periodicities_in_metadata(
        self, empty_policy: PolicyConfig
    ) -> None:
        """AC-5: Metadata includes variable_periodicities dict."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
            },
            variable_periodicities={
                "salaire_net": "month",
                "irpp": "year",
            },
        )
        mock_simulation = _make_mock_simulation_with_methods({
            "salaire_net": np.array([24000.0, 40000.0]),
            "irpp": np.array([-1500.0]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        assert "variable_periodicities" in result.metadata
        assert result.metadata["variable_periodicities"] == {
            "salaire_net": "month",
            "irpp": "year",
        }

    def test_calculation_methods_in_metadata(
        self, empty_policy: PolicyConfig
    ) -> None:
        """AC-5: Metadata includes calculation_methods dict."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
            },
            variable_periodicities={
                "salaire_net": "month",
                "irpp": "year",
            },
        )
        mock_simulation = _make_mock_simulation_with_methods({
            "salaire_net": np.array([24000.0, 40000.0]),
            "irpp": np.array([-1500.0]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        assert "calculation_methods" in result.metadata
        assert result.metadata["calculation_methods"] == {
            "salaire_net": "calculate_add",
            "irpp": "calculate",
        }

    def test_eternity_variable_uses_calculate_in_metadata(self) -> None:
        """AC-5, AC-6: Eternity variables show 'calculate' method in metadata."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("date_naissance",),
            skip_version_check=True,
        )
        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={"date_naissance": "individu"},
            variable_periodicities={"date_naissance": "eternity"},
        )
        mock_simulation = _make_mock_simulation_with_methods({
            "date_naissance": np.array([19960101]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "age": pa.array([30]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        assert result.metadata["variable_periodicities"]["date_naissance"] == "eternity"
        assert result.metadata["calculation_methods"]["date_naissance"] == "calculate"


class TestComputeMultiEntity:
    """Story 9.2 AC-1, AC-2, AC-3, AC-4: End-to-end multi-entity compute()."""

    def test_compute_single_entity_backward_compatible(
        self, sample_population: PopulationData, empty_policy: PolicyConfig
    ) -> None:
        """AC-4: Single-entity output produces empty entity_tables (backward compat)."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs()
        mock_simulation = _make_mock_simulation(
            {"income_tax": np.array([3000.0, 6750.0, 12000.0])}
        )
        adapter._tax_benefit_system = mock_tbs

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(sample_population, empty_policy, 2025)

        # Single entity: entity_tables should be empty for backward compatibility
        assert result.entity_tables == {}
        # Metadata must be consistent with entity_tables — both empty for single-entity
        # (regression guard for the bug where output_entities was non-empty while
        # entity_tables was {}, causing consumers to see contradictory state).
        assert result.metadata["output_entities"] == []
        assert result.metadata["entity_row_counts"] == {}
        # output_fields still works
        assert result.output_fields.num_rows == 3
        assert result.output_fields.column_names == ["income_tax"]

    def test_compute_multi_entity_populates_entity_tables(self) -> None:
        """AC-1, AC-3: Multi-entity output populates entity_tables."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp", "revenu_disponible"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
                "revenu_disponible": "menage",
            },
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "irpp": np.array([-1500.0]),
            "revenu_disponible": np.array([40000.0]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        # Multi-entity: entity_tables populated
        assert len(result.entity_tables) == 3
        assert "individus" in result.entity_tables
        assert "foyers_fiscaux" in result.entity_tables
        assert "menages" in result.entity_tables

        # Correct array lengths per entity
        assert result.entity_tables["individus"].num_rows == 2
        assert result.entity_tables["foyers_fiscaux"].num_rows == 1
        assert result.entity_tables["menages"].num_rows == 1

        # output_fields is the person entity table
        assert result.output_fields.num_rows == 2
        assert "salaire_net" in result.output_fields.column_names

    def test_compute_multi_entity_metadata(self) -> None:
        """AC-1: Metadata includes output_entities and entity_row_counts."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("salaire_net", "irpp"),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs_with_entities(
            variable_entities={
                "salaire_net": "individu",
                "irpp": "foyer_fiscal",
            },
        )
        mock_simulation = _make_mock_simulation({
            "salaire_net": np.array([20000.0, 35000.0]),
            "irpp": np.array([-1500.0]),
        })
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                }),
            },
        )

        mock_builder_instance = MagicMock()
        mock_builder_instance.build_from_entities.return_value = mock_simulation

        with _patch_simulation_builder(mock_builder_instance):
            result = adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )

        assert "output_entities" in result.metadata
        assert sorted(result.metadata["output_entities"]) == [
            "foyers_fiscaux", "individus"
        ]
        assert "entity_row_counts" in result.metadata
        assert result.metadata["entity_row_counts"]["individus"] == 2
        assert result.metadata["entity_row_counts"]["foyers_fiscaux"] == 1

    def test_compute_entity_detection_error(self) -> None:
        """AC-5: Variable with no entity raises ApiMappingError during compute."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("broken_var",),
            skip_version_check=True,
        )

        mock_tbs = _make_mock_tbs_with_entities(variable_entities={})
        # Add variable with no entity
        var_mock = MagicMock()
        var_mock.entity = None
        mock_tbs.variables["broken_var"] = var_mock
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({"x": pa.array([1.0])}),
            },
        )

        # The error is raised in _resolve_variable_entities() — before _build_simulation().
        # No SimulationBuilder mock needed; the error fires before simulation construction.
        with pytest.raises(ApiMappingError, match="Cannot determine entity"):
            adapter.compute(
                population, PolicyConfig(parameters={}, name="test"), 2024
            )


# ===========================================================================
# Story 9.4: 4-Entity PopulationData format — membership columns
# ===========================================================================


def _make_french_mock_tbs(
    variable_entities: dict[str, str] | None = None,
    variable_periodicities: dict[str, str] | None = None,
) -> MagicMock:
    """Create a full French 4-entity mock TBS with roles for Story 9.4 tests."""
    return _make_mock_tbs_with_entities(
        entity_keys=("individu", "famille", "foyer_fiscal", "menage"),
        entity_roles=_FRENCH_ENTITY_ROLES,
        variable_entities=variable_entities or {},
        variable_periodicities=variable_periodicities or {},
        person_entity="individu",
    )


class TestDetectMembershipColumns:
    """Story 9.4 Task 1: _detect_membership_columns() detection logic.

    AC-1: Detect membership columns on person entity table.
    AC-3: Missing relationship validation (all-or-nothing, paired columns).
    AC-6: Backward compatibility (no membership columns → empty dict).
    """

    def test_detect_all_three_group_entities(self) -> None:
        """AC-1: All 3 group entity membership columns detected correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        })

        result = adapter._detect_membership_columns(person_table, mock_tbs)

        assert len(result) == 3
        assert result["famille"] == ("famille_id", "famille_role")
        assert result["foyer_fiscal"] == ("foyer_fiscal_id", "foyer_fiscal_role")
        assert result["menage"] == ("menage_id", "menage_role")

    def test_detect_none_backward_compat(self) -> None:
        """AC-6: No membership columns → empty dict (backward compatible)."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0]),
            "age": pa.array([30]),
        })

        result = adapter._detect_membership_columns(person_table, mock_tbs)
        assert result == {}

    def test_detect_partial_raises_error(self) -> None:
        """AC-3: Only famille_id present (missing foyer_fiscal, menage) → error."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0]),
            "famille_id": pa.array([0]),
            "famille_role": pa.array(["parents"]),
        })

        with pytest.raises(ApiMappingError, match="Incomplete entity membership columns"):
            adapter._detect_membership_columns(person_table, mock_tbs)

    def test_detect_unpaired_id_without_role_raises_error(self) -> None:
        """AC-3: famille_id exists but famille_role missing → unpaired error."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0]),
            "famille_id": pa.array([0]),
            # famille_role is missing — only _id without _role
            "foyer_fiscal_id": pa.array([0]),
            "foyer_fiscal_role": pa.array(["declarants"]),
            "menage_id": pa.array([0]),
            "menage_role": pa.array(["personne_de_reference"]),
        })

        with pytest.raises(ApiMappingError, match="Unpaired membership column"):
            adapter._detect_membership_columns(person_table, mock_tbs)

    def test_detect_unpaired_role_without_id_raises_error(self) -> None:
        """AC-3: famille_role exists but famille_id missing → unpaired error."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0]),
            # famille_id is missing — only _role without _id
            "famille_role": pa.array(["parents"]),
            "foyer_fiscal_id": pa.array([0]),
            "foyer_fiscal_role": pa.array(["declarants"]),
            "menage_id": pa.array([0]),
            "menage_role": pa.array(["personne_de_reference"]),
        })

        with pytest.raises(ApiMappingError, match="Unpaired membership column"):
            adapter._detect_membership_columns(person_table, mock_tbs)


class TestResolveValidRoleKeys:
    """Story 9.4 Task 2: _resolve_valid_role_keys() role key resolution.

    AC-4: Valid role keys queried from TBS.
    """

    def test_french_entity_role_keys(self) -> None:
        """AC-4: Correct role keys for all French group entities.

        Uses role.plural or role.key — matching build_from_entities() behavior.
        """
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        result = adapter._resolve_valid_role_keys(mock_tbs)

        assert result["famille"] == frozenset({"parents", "enfants"})
        assert result["foyer_fiscal"] == frozenset({"declarants", "personnes_a_charge"})
        # menage: personne_de_reference and conjoint have plural=None → uses key
        assert result["menage"] == frozenset({
            "personne_de_reference", "conjoint", "enfants", "autres",
        })

    def test_person_entity_excluded(self) -> None:
        """AC-4: Person entity (individu) is not in role keys dict."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        result = adapter._resolve_valid_role_keys(mock_tbs)
        assert "individu" not in result


class TestValidateEntityRelationships:
    """Story 9.4 Task 3: _validate_entity_relationships() validation.

    AC-3: Missing relationship validation.
    AC-4: Invalid role validation.
    AC-5: Null membership value rejection.
    """

    def test_null_in_id_column_raises_error(self) -> None:
        """AC-5: Null value in _id column → ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "famille_id": pa.array([0, None]),  # null in _id
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        })

        membership_cols = {
            "famille": ("famille_id", "famille_role"),
            "foyer_fiscal": ("foyer_fiscal_id", "foyer_fiscal_role"),
            "menage": ("menage_id", "menage_role"),
        }
        valid_roles = {
            "famille": frozenset({"parents", "enfants"}),
            "foyer_fiscal": frozenset({"declarants", "personnes_a_charge"}),
            "menage": frozenset({"personne_de_reference", "conjoint", "enfants", "autres"}),
        }

        with pytest.raises(ApiMappingError, match="Null value in membership column"):
            adapter._validate_entity_relationships(
                person_table, membership_cols, valid_roles
            )

    def test_null_in_role_column_raises_error(self) -> None:
        """AC-5: Null value in _role column → ApiMappingError."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", None]),  # null in _role
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        })

        membership_cols = {
            "famille": ("famille_id", "famille_role"),
            "foyer_fiscal": ("foyer_fiscal_id", "foyer_fiscal_role"),
            "menage": ("menage_id", "menage_role"),
        }
        valid_roles = {
            "famille": frozenset({"parents", "enfants"}),
            "foyer_fiscal": frozenset({"declarants", "personnes_a_charge"}),
            "menage": frozenset({"personne_de_reference", "conjoint", "enfants", "autres"}),
        }

        with pytest.raises(ApiMappingError, match="Null value in membership column"):
            adapter._validate_entity_relationships(
                person_table, membership_cols, valid_roles
            )

    def test_invalid_role_value_raises_error(self) -> None:
        """AC-4: Invalid role value → ApiMappingError with valid roles listed."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0]),
            "famille_id": pa.array([0]),
            "famille_role": pa.array(["parents"]),
            "foyer_fiscal_id": pa.array([0]),
            "foyer_fiscal_role": pa.array(["declarants"]),
            "menage_id": pa.array([0]),
            "menage_role": pa.array(["invalid_role"]),  # invalid role
        })

        membership_cols = {
            "famille": ("famille_id", "famille_role"),
            "foyer_fiscal": ("foyer_fiscal_id", "foyer_fiscal_role"),
            "menage": ("menage_id", "menage_role"),
        }
        valid_roles = {
            "famille": frozenset({"parents", "enfants"}),
            "foyer_fiscal": frozenset({"declarants", "personnes_a_charge"}),
            "menage": frozenset({"personne_de_reference", "conjoint", "enfants", "autres"}),
        }

        with pytest.raises(ApiMappingError, match="Invalid role value"):
            adapter._validate_entity_relationships(
                person_table, membership_cols, valid_roles
            )

    def test_all_valid_passes_silently(self) -> None:
        """AC-3, AC-4, AC-5: All valid data passes without error."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs()
        adapter._tax_benefit_system = mock_tbs

        person_table = pa.table({
            "salaire_de_base": pa.array([30000.0, 0.0]),
            "famille_id": pa.array([0, 0]),
            "famille_role": pa.array(["parents", "parents"]),
            "foyer_fiscal_id": pa.array([0, 0]),
            "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
            "menage_id": pa.array([0, 0]),
            "menage_role": pa.array(["personne_de_reference", "conjoint"]),
        })

        membership_cols = {
            "famille": ("famille_id", "famille_role"),
            "foyer_fiscal": ("foyer_fiscal_id", "foyer_fiscal_role"),
            "menage": ("menage_id", "menage_role"),
        }
        valid_roles = {
            "famille": frozenset({"parents", "enfants"}),
            "foyer_fiscal": frozenset({"declarants", "personnes_a_charge"}),
            "menage": frozenset({"personne_de_reference", "conjoint", "enfants", "autres"}),
        }

        # Should not raise
        adapter._validate_entity_relationships(
            person_table, membership_cols, valid_roles
        )


class TestPopulationToEntityDict4Entity:
    """Story 9.4 Task 4: Refactored _population_to_entity_dict() for 4-entity format.

    AC-1: 4-entity format produces valid entity dict.
    AC-2: Group membership assignment is correct.
    AC-6: Backward compatibility (no membership columns → old behavior).
    AC-7: Group entity input variables merged correctly.
    """

    def test_married_couple_entity_dict(self) -> None:
        """AC-1, AC-2: Married couple produces correct entity dict.

        2 persons in 1 famille, 1 foyer_fiscal, 1 menage with correct roles.
        """
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

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
                    "menage_role": pa.array(["personne_de_reference", "conjoint"]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # Person instances with period-wrapped variable values
        assert "individus" in entity_dict
        assert "individu_0" in entity_dict["individus"]
        assert "individu_1" in entity_dict["individus"]
        assert entity_dict["individus"]["individu_0"]["salaire_de_base"] == {"2024": 30000.0}
        assert entity_dict["individus"]["individu_1"]["age"] == {"2024": 28}

        # Membership columns should NOT appear in person instance data
        assert "famille_id" not in entity_dict["individus"]["individu_0"]
        assert "famille_role" not in entity_dict["individus"]["individu_0"]
        assert "foyer_fiscal_id" not in entity_dict["individus"]["individu_0"]
        assert "menage_id" not in entity_dict["individus"]["individu_0"]

        # Group entity instances with role assignments
        assert "familles" in entity_dict
        assert "famille_0" in entity_dict["familles"]
        assert entity_dict["familles"]["famille_0"]["parents"] == [
            "individu_0", "individu_1"
        ]

        assert "foyers_fiscaux" in entity_dict
        assert "foyer_fiscal_0" in entity_dict["foyers_fiscaux"]
        assert entity_dict["foyers_fiscaux"]["foyer_fiscal_0"]["declarants"] == [
            "individu_0", "individu_1"
        ]

        assert "menages" in entity_dict
        assert "menage_0" in entity_dict["menages"]
        assert entity_dict["menages"]["menage_0"]["personne_de_reference"] == ["individu_0"]
        assert entity_dict["menages"]["menage_0"]["conjoint"] == ["individu_1"]

    def test_family_with_child(self) -> None:
        """AC-1, AC-2: Family with 2 parents + 1 child, different roles."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([40000.0, 20000.0, 0.0]),
                    "age": pa.array([45, 42, 12]),
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
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # famille roles
        famille = entity_dict["familles"]["famille_0"]
        assert famille["parents"] == ["individu_0", "individu_1"]
        assert famille["enfants"] == ["individu_2"]

        # foyer_fiscal roles
        foyer = entity_dict["foyers_fiscaux"]["foyer_fiscal_0"]
        assert foyer["declarants"] == ["individu_0", "individu_1"]
        assert foyer["personnes_a_charge"] == ["individu_2"]

        # menage roles
        menage = entity_dict["menages"]["menage_0"]
        assert menage["personne_de_reference"] == ["individu_0"]
        assert menage["conjoint"] == ["individu_1"]
        assert menage["enfants"] == ["individu_2"]

    def test_backward_compat_no_membership_columns(self) -> None:
        """AC-6: No membership columns → identical to pre-change behavior."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "age": pa.array([30]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # Old behavior: all columns period-wrapped, no group entities
        assert "individus" in entity_dict
        assert entity_dict["individus"]["individu_0"]["salaire_de_base"] == {"2024": 30000.0}
        assert entity_dict["individus"]["individu_0"]["age"] == {"2024": 30}

    def test_two_independent_households(self) -> None:
        """AC-1, AC-2: Two independent single-person households."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
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
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # 2 familles, 2 foyers, 2 menages
        assert len(entity_dict["familles"]) == 2
        assert len(entity_dict["foyers_fiscaux"]) == 2
        assert len(entity_dict["menages"]) == 2

        assert entity_dict["familles"]["famille_0"]["parents"] == ["individu_0"]
        assert entity_dict["familles"]["famille_1"]["parents"] == ["individu_1"]

    def test_group_entity_input_variables(self) -> None:
        """AC-7: Group entity table with variables merged into entity dict."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 0.0]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array(["personne_de_reference", "conjoint"]),
                }),
                "menage": pa.table({
                    "loyer": pa.array([800.0]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # menage entity should have role assignments AND period-wrapped loyer
        menage = entity_dict["menages"]["menage_0"]
        assert menage["personne_de_reference"] == ["individu_0"]
        assert menage["conjoint"] == ["individu_1"]
        assert menage["loyer"] == {"2024": 800.0}

    def test_non_contiguous_group_ids(self) -> None:
        """Edge case: non-contiguous group IDs [0, 2] work correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 50000.0]),
                    "famille_id": pa.array([0, 2]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 2]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 2]),
                    "menage_role": pa.array([
                        "personne_de_reference", "personne_de_reference",
                    ]),
                }),
                "menage": pa.table({
                    "loyer": pa.array([800.0, 1200.0]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # Non-contiguous IDs: famille_0 and famille_2 (no famille_1)
        assert "famille_0" in entity_dict["familles"]
        assert "famille_2" in entity_dict["familles"]
        assert "famille_1" not in entity_dict["familles"]

        # Group table: row 0 → smallest ID (0), row 1 → second-smallest ID (2)
        assert entity_dict["menages"]["menage_0"]["loyer"] == {"2024": 800.0}
        assert entity_dict["menages"]["menage_2"]["loyer"] == {"2024": 1200.0}

    def test_group_table_row_count_mismatch_raises_error(self) -> None:
        """Edge case: group entity table has more rows than distinct group IDs."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "famille_id": pa.array([0]),
                    "famille_role": pa.array(["parents"]),
                    "foyer_fiscal_id": pa.array([0]),
                    "foyer_fiscal_role": pa.array(["declarants"]),
                    "menage_id": pa.array([0]),
                    "menage_role": pa.array(["personne_de_reference"]),
                }),
                "menage": pa.table({
                    "loyer": pa.array([800.0, 1200.0]),  # 2 rows but only 1 menage
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        with pytest.raises(ApiMappingError, match="Group entity table row count mismatch"):
            adapter._population_to_entity_dict(
                population, policy, "2024", mock_tbs
            )

    def test_policy_parameters_injected_in_4entity_mode(self) -> None:
        """AC-1: Policy parameters are injected into person instances in 4-entity mode."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        # Add the policy parameter variable to mock TBS
        policy_var = MagicMock()
        policy_var.entity = mock_tbs.entities[0]  # individu
        policy_var.definition_period = "year"
        mock_tbs.variables["custom_param"] = policy_var
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0]),
                    "famille_id": pa.array([0]),
                    "famille_role": pa.array(["parents"]),
                    "foyer_fiscal_id": pa.array([0]),
                    "foyer_fiscal_role": pa.array(["declarants"]),
                    "menage_id": pa.array([0]),
                    "menage_role": pa.array(["personne_de_reference"]),
                }),
            },
        )
        policy = PolicyConfig(parameters={"custom_param": 42.0}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        assert entity_dict["individus"]["individu_0"]["custom_param"] == {"2024": 42.0}

    def test_string_group_ids(self) -> None:
        """Edge case: String (utf8) group IDs work correctly."""
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individu": pa.table({
                    "salaire_de_base": pa.array([30000.0, 0.0]),
                    "famille_id": pa.array(["fam_a", "fam_a"]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array(["ff_a", "ff_a"]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array(["men_a", "men_a"]),
                    "menage_role": pa.array(["personne_de_reference", "conjoint"]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        assert "famille_fam_a" in entity_dict["familles"]
        assert "foyer_fiscal_ff_a" in entity_dict["foyers_fiscaux"]
        assert "menage_men_a" in entity_dict["menages"]
        assert entity_dict["menages"]["menage_men_a"]["personne_de_reference"] == [
            "individu_0",
        ]

    def test_plural_person_table_key(self) -> None:
        """Edge case: Person table key is plural ('individus' instead of 'individu').

        Person instance IDs should use the plural key prefix.
        """
        adapter = OpenFiscaApiAdapter(
            output_variables=("income_tax",),
            skip_version_check=True,
        )
        mock_tbs = _make_french_mock_tbs(
            variable_entities={"income_tax": "individu"},
        )
        adapter._tax_benefit_system = mock_tbs

        population = PopulationData(
            tables={
                "individus": pa.table({  # plural key
                    "salaire_de_base": pa.array([30000.0, 0.0]),
                    "famille_id": pa.array([0, 0]),
                    "famille_role": pa.array(["parents", "parents"]),
                    "foyer_fiscal_id": pa.array([0, 0]),
                    "foyer_fiscal_role": pa.array(["declarants", "declarants"]),
                    "menage_id": pa.array([0, 0]),
                    "menage_role": pa.array(["personne_de_reference", "conjoint"]),
                }),
            },
        )
        policy = PolicyConfig(parameters={}, name="test")

        entity_dict = adapter._population_to_entity_dict(
            population, policy, "2024", mock_tbs
        )

        # Person instance IDs use the original table key prefix ("individus")
        assert "individus_0" in entity_dict["individus"]
        assert "individus_1" in entity_dict["individus"]

        # Group role assignments also use "individus_" prefix
        assert entity_dict["familles"]["famille_0"]["parents"] == [
            "individus_0", "individus_1"
        ]
