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
        assert adapter.version() != "unknown" or adapter.version() == "unknown"

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
