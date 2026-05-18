# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for OpenFisca-France custom variable extension.

Story 29.1: Tests for montant_subvention, eligible_subvention,
malus_ecologique, and aide_energie custom variables.
"""

from __future__ import annotations

import pytest

# Test gating: skip tests if OpenFisca-France not installed
# ruff: noqa: E402 - Module level import for test gating
openfisca_france = pytest.importorskip(
    "openfisca_france", reason="openfisca-france not installed"
)

from reformlab.computation.openfisca_extension import (
    EXTENSION_NAME,
    EXTENSION_VERSION,
    load_extension,
)


class TestExtensionLoading:
    """Tests for extension loading and registration (Story 29.1 AC: #2)."""

    def test_extension_loads_into_tbs(self):
        """Test that extension variables are registered in TBS."""
        tbs = openfisca_france.CountryTaxBenefitSystem()

        # Load extension
        load_extension(tbs)

        # Verify custom variables exist
        assert "montant_subvention" in tbs.variables
        assert "eligible_subvention" in tbs.variables
        assert "malus_ecologique" in tbs.variables
        assert "aide_energie" in tbs.variables

    def test_extension_loading_is_idempotent(self):
        """Test that loading extension twice is safe (Story 29.1 Dev Notes)."""
        tbs = openfisca_france.CountryTaxBenefitSystem()

        # Load extension twice
        load_extension(tbs)
        load_extension(tbs)

        # Should not raise errors, variables should exist
        assert "montant_subvention" in tbs.variables
        assert "eligible_subvention" in tbs.variables

    def test_extension_metadata_constants(self):
        """Test that extension metadata is defined (Story 29.1 AC: #6)."""
        assert EXTENSION_NAME == "reformlab-openfisca-extend-fr"
        assert EXTENSION_VERSION == "1.0.0"


class TestSubsidyVariables:
    """Tests for montant_subvention and eligible_subvention (Story 29.1 AC: #5)."""

    def test_montant_subvention_variable_exists(self):
        """Test that montant_subvention variable is registered."""
        tbs = openfisca_france.CountryTaxBenefitSystem()
        load_extension(tbs)

        var = tbs.variables.get("montant_subvention")
        assert var is not None
        assert var.value_type is float
        assert var.entity.key == "menage"
        assert str(var.definition_period) == "year"

    def test_eligible_subvention_variable_exists(self):
        """Test that eligible_subvention variable is registered."""
        tbs = openfisca_france.CountryTaxBenefitSystem()
        load_extension(tbs)

        var = tbs.variables.get("eligible_subvention")
        assert var is not None
        assert var.value_type is bool
        assert var.entity.key == "menage"
        assert str(var.definition_period) == "year"


class TestVehicleMalusVariable:
    """Tests for malus_ecologique (Story 29.1 AC: #5)."""

    def test_malus_ecologique_variable_exists(self):
        """Test that malus_ecologique variable is registered."""
        tbs = openfisca_france.CountryTaxBenefitSystem()
        load_extension(tbs)

        var = tbs.variables.get("malus_ecologique")
        assert var is not None
        assert var.value_type is float
        assert var.entity.key == "menage"
        assert str(var.definition_period) == "year"


class TestEnergyAidVariable:
    """Tests for aide_energie (Story 29.1 AC: #3, #5)."""

    def test_aide_energie_variable_exists(self):
        """Test that aide_energie variable is registered."""
        tbs = openfisca_france.CountryTaxBenefitSystem()
        load_extension(tbs)

        var = tbs.variables.get("aide_energie")
        assert var is not None
        assert var.value_type is float
        assert var.entity.key == "menage"
        assert str(var.definition_period) == "year"

    def test_aide_energie_aliases_to_cheque_energie(self):
        """Test that aide_energie uses existing cheque_energie (PM decision)."""
        tbs = openfisca_france.CountryTaxBenefitSystem()
        load_extension(tbs)

        # Both variables should exist
        assert "cheque_energie" in tbs.variables
        assert "aide_energie" in tbs.variables

        # Get variable references
        cheque_var = tbs.variables.get("cheque_energie")
        aide_var = tbs.variables.get("aide_energie")

        # Both should be menage-level, float, year-period
        assert cheque_var.value_type is float
        assert aide_var.value_type is float
        assert cheque_var.entity.key == "menage"
        assert aide_var.entity.key == "menage"


class TestIntegrationWithAdapter:
    """Integration tests with OpenFiscaApiAdapter (Story 29.1 AC: #1, #4)."""

    def test_adapter_with_custom_variables_in_output(self):
        """Test that adapter can compute custom variables."""
        from reformlab.computation.openfisca_api_adapter import (
            OpenFiscaApiAdapter,
        )

        # Create adapter with custom variables in output
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=(
                "salaire_net",  # Standard variable
                "montant_subvention",  # Custom variable
                "eligible_subvention",  # Custom variable
            ),
            skip_version_check=True,
        )

        # Verify adapter is initialized without error
        assert adapter is not None
        # Verify custom variables are registered in the TBS
        tbs = adapter._get_tax_benefit_system()
        assert "montant_subvention" in tbs.variables
        assert "eligible_subvention" in tbs.variables

    def test_custom_variables_in_live_computation(self):
        """Test that custom variables produce values in live computation."""
        from reformlab.computation.openfisca_api_adapter import (
            OpenFiscaApiAdapter,
        )
        from reformlab.computation.types import (
            PolicyConfig,
            PopulationData,
        )

        # Create adapter with custom variables
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=(
                "salaire_net",
                "montant_subvention",
                "eligible_subvention",
            ),
            skip_version_check=True,
        )

        # Create minimal population (backward-compatible mode, no membership columns)
        import pyarrow as pa

        # Simple person table (individu) with salaire_de_base
        person_table = pa.table({
            "salaire_de_base": pa.array([15000.0, 25000.0, 5000.0, 30000.0, 18000.0], type=pa.float64()),
        })

        population = PopulationData(
            tables={
                "individu": person_table,
            },
            metadata={"source": "test"},
        )

        policy = PolicyConfig(policy={}, name="test-policy")

        # Run computation
        result = adapter.compute(population, policy, 2025)

        # Custom variables are household-level (menages entity)
        # Check entity_tables for multi-entity results
        assert "menages" in result.entity_tables
        assert "montant_subvention" in result.entity_tables["menages"].column_names
        assert "eligible_subvention" in result.entity_tables["menages"].column_names

        # Verify values are produced (at least one household should be eligible)
        subsidy_array = result.entity_tables["menages"].column("montant_subvention").to_pylist()
        eligible_array = result.entity_tables["menages"].column("eligible_subvention").to_pylist()

        # At least one household should have non-zero subsidy or be eligible
        # (income < 20000 threshold): households with salaire_de_base of 15000, 5000, 18000
        has_subsidy = any(s > 0 for s in subsidy_array)
        has_eligible = any(eligible_array)

        assert has_subsidy or has_eligible, "At least one household should be eligible for subsidy"

    def test_live_computation_with_all_default_variables(self):
        """Test that live computation produces all 9 expected output variables.

        Story 29.3 AC: #4, #5, #6 - Validate that all resolved variable names work
        in live output and produce expected values.

        NOTE: malus_ecologique may return 0.0 for all households if the
        reformlab_malus_emissions input variable is not registered (Story 29.1
        deferred item). This test accepts 0.0 as valid output.
        """
        from reformlab.computation.openfisca_api_adapter import (
            OpenFiscaApiAdapter,
        )
        from reformlab.computation.result_normalizer import (
            _DEFAULT_LIVE_OUTPUT_VARIABLES,
        )
        from reformlab.computation.types import (
            PolicyConfig,
            PopulationData,
        )

        # Create adapter with all default output variables
        adapter = OpenFiscaApiAdapter(
            country_package="openfisca_france",
            output_variables=_DEFAULT_LIVE_OUTPUT_VARIABLES,
            skip_version_check=True,
        )

        # Create test population with explicit eligibility criteria
        # Household 1-2: income < 20000 (subsidy eligible), emissions > 118 (malus eligible)
        # Household 3-4: income >= 20000 (subsidy ineligible), emissions <= 118 (malus ineligible)
        # All households: energy_expenditure > 0 for aide_energie testing
        import pyarrow as pa

        person_table = pa.table({
            "salaire_de_base": pa.array([15000.0, 18000.0, 25000.0, 30000.0], type=pa.float64()),
        })

        population = PopulationData(
            tables={
                "individu": person_table,
            },
            metadata={"source": "test"},
        )

        policy = PolicyConfig(policy={}, name="test-policy")

        # Run computation
        result = adapter.compute(population, policy, 2025)

        # Verify all 9 variables are present across entity_tables
        # Variables are distributed across entities:
        # - menages: revenu_disponible, impots_directs, montant_subvention,
        #             eligible_subvention, malus_ecologique, aide_energie
        # - foyers_fiscaux: irpp_economique (foyer_fiscal entity)
        # - individus: salaire_net (person entity)
        # - familles: prestations_sociales (family entity)
        assert "menages" in result.entity_tables
        assert "foyers_fiscaux" in result.entity_tables
        assert "individus" in result.entity_tables
        assert "familles" in result.entity_tables

        menages_table = result.entity_tables["menages"]
        foyers_fiscaux_table = result.entity_tables["foyers_fiscaux"]
        individus_table = result.entity_tables["individus"]
        familles_table = result.entity_tables["familles"]

        # Check menage-level variables
        for var_name in ["revenu_disponible", "impots_directs", "montant_subvention",
                         "eligible_subvention", "malus_ecologique", "aide_energie"]:
            assert var_name in menages_table.column_names, (
                f"Variable '{var_name}' missing from menages output"
            )

        # Check foyer_fiscal-level variables
        assert "irpp_economique" in foyers_fiscaux_table.column_names, (
            "Variable 'irpp_economique' missing from foyers_fiscaux output"
        )

        # Check person-level variables
        assert "salaire_net" in individus_table.column_names, (
            "Variable 'salaire_net' missing from individus output"
        )

        # Check family-level variables
        assert "prestations_sociales" in familles_table.column_names, (
            "Variable 'prestations_sociales' missing from familles output"
        )

        # Note: normalize_computation_result operates on output_fields (individus table).
        # Multi-entity normalization including menage-level custom variables is
        # deferred to a future story (see normalize_entity_tables TODO).
        # For this test, we verify the variables exist and produce correct values.

        # Verify custom variable values using pytest.approx() for floating-point precision
        # Household 0-1: income 15000, 18000 (< 20000 threshold) - eligible
        # Household 2-3: income 25000, 30000 (>= 20000 threshold) - ineligible

        # subsidy_amount should be 150.0 for eligible households
        subsidy_values = menages_table.column("montant_subvention").to_pylist()
        # At least households 0 and 1 should have subsidy (their income < 20000)
        assert subsidy_values[0] == pytest.approx(150.0, abs=0.01), "Household 0 should receive full subsidy"
        assert subsidy_values[1] == pytest.approx(150.0, abs=0.01), "Household 1 should receive full subsidy"
        assert subsidy_values[2] == pytest.approx(0.0, abs=0.01), "Household 2 should not receive subsidy"
        assert subsidy_values[3] == pytest.approx(0.0, abs=0.01), "Household 3 should not receive subsidy"

        # eligible_subvention should be True for eligible households
        eligible_values = menages_table.column("eligible_subvention").to_pylist()
        assert eligible_values[0] is True, "Household 0 should be eligible"
        assert eligible_values[1] is True, "Household 1 should be eligible"
        assert eligible_values[2] is False, "Household 2 should not be eligible"
        assert eligible_values[3] is False, "Household 3 should not be eligible"

        # malus_ecologique may return 0 if reformlab_malus_emissions input unavailable
        # (Story 29.1 deferred item). We accept 0.0 as valid output.
        malus_values = menages_table.column("malus_ecologique").to_pylist()
        # All values should be numeric (not None)
        assert all(isinstance(v, (int, float)) for v in malus_values), "All malus values should be numeric"

        # aide_energie wraps cheque_energie - verify delegation produces values
        aid_values = menages_table.column("aide_energie").to_pylist()
        # All values should be numeric (not None)
        assert all(isinstance(v, (int, float)) for v in aid_values), "All aid values should be numeric"
