# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Integration tests for Story 24.2: domain-layer live translation.

Tests the full path from API layer through translation to catalog updates.
Uses the FastAPI TestClient to verify:
- Translation integration in the API layer
- Catalog live_ready status for subsidy-family policies
- Non-regression for existing carbon_tax, rebate, feebate policies
- Normalization of subsidy-family output variables
"""

from __future__ import annotations

from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client() -> Generator[TestClient, Any, None]:
    """TestClient with custom types registered."""
    from reformlab.server.dependencies import get_registry
    from reformlab.templates.schema import (
        _CUSTOM_PARAMETERS_TO_POLICY_TYPE,
        _CUSTOM_POLICY_TYPES,
    )
    import shutil

    # Save existing registrations so we can restore after test
    saved_types = dict(_CUSTOM_POLICY_TYPES)
    saved_params = dict(_CUSTOM_PARAMETERS_TO_POLICY_TYPE)

    # Ensure vehicle_malus and energy_poverty_aid are registered
    import reformlab.templates.energy_poverty_aid  # noqa: F401
    import reformlab.templates.vehicle_malus  # noqa: F401
    from reformlab.server.app import create_app

    app = create_app()
    yield TestClient(app)

    # Clean up test-template from registry
    registry = get_registry()
    test_template_path = registry.path / "test-template"
    if test_template_path.exists():
        shutil.rmtree(test_template_path)

    # Restore registrations
    _CUSTOM_POLICY_TYPES.clear()
    _CUSTOM_POLICY_TYPES.update(saved_types)
    _CUSTOM_PARAMETERS_TO_POLICY_TYPE.clear()
    _CUSTOM_PARAMETERS_TO_POLICY_TYPE.update(saved_params)


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"password": "test-password-123"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


# ============================================================================
# Catalog live-readiness tests
# ============================================================================


class TestCatalogLiveReadiness:
    """Tests that catalog reflects live_ready for newly-live policies."""

    def test_subsidy_is_live_ready_in_catalog(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC #1: Subsidy templates have runtime_availability='live_ready'."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]
        subsidy_templates = [t for t in templates if t["type"] == "subsidy"]
        for t in subsidy_templates:
            if t.get("is_custom", False):
                continue
            assert t["runtime_availability"] == "live_ready", (
                f"Subsidy template '{t['id']}' should be live_ready"
            )

    def test_vehicle_malus_is_live_ready_in_catalog(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC #1: Vehicle malus templates have runtime_availability='live_ready'."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]
        vm_templates = [t for t in templates if t["type"] == "vehicle_malus"]
        for t in vm_templates:
            assert t["runtime_availability"] == "live_ready", (
                f"Vehicle malus template '{t['id']}' should be live_ready"
            )

    def test_energy_poverty_aid_is_live_ready_in_catalog(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC #1: Energy poverty aid templates have runtime_availability='live_ready'."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]
        epa_templates = [t for t in templates if t["type"] == "energy_poverty_aid"]
        for t in epa_templates:
            assert t["runtime_availability"] == "live_ready", (
                f"Energy poverty aid template '{t['id']}' should be live_ready"
            )


# ============================================================================
# Non-regression tests
# ============================================================================


class TestNonRegression:
    """Tests that existing policies continue to work after Story 24.2."""

    def test_carbon_tax_still_live_ready(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC #8: Carbon tax templates remain live_ready."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]
        ct_templates = [t for t in templates if t["type"] == "carbon_tax"]
        for t in ct_templates:
            assert t["runtime_availability"] == "live_ready", (
                f"Carbon tax template '{t['id']}' should remain live_ready"
            )

    def test_rebate_still_live_ready(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC #8: Rebate templates remain live_ready."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]
        rebate_templates = [t for t in templates if t["type"] == "rebate"]
        for t in rebate_templates:
            assert t["runtime_availability"] == "live_ready", (
                f"Rebate template '{t['id']}' should remain live_ready"
            )

    def test_feebate_still_live_ready(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC #8: Feebate templates remain live_ready."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]
        feebate_templates = [t for t in templates if t["type"] == "feebate"]
        for t in feebate_templates:
            assert t["runtime_availability"] == "live_ready", (
                f"Feebate template '{t['id']}' should remain live_ready"
            )


# ============================================================================
# Translation integration in the API layer
# ============================================================================


class TestTranslationAPIIntegration:
    """Tests for translation integration in the execution path."""

    def test_translate_policy_for_live_execution_subsidy(self) -> None:
        """AC #2: Subsidy policy is translated for adapter consumption."""
        from reformlab.interfaces.api import _translate_policy_for_live_execution
        from reformlab.templates.schema import SubsidyParameters

        policy = SubsidyParameters(
            rate_schedule={2025: 5000.0},
            income_caps={2025: 30000.0},
            eligible_categories=("low_income",),
        )
        result = _translate_policy_for_live_execution(policy, "test-subsidy")
        assert result is policy

    def test_translate_policy_for_live_execution_vehicle_malus(self) -> None:
        """AC #2: Vehicle malus policy is translated for adapter consumption."""
        from reformlab.interfaces.api import _translate_policy_for_live_execution
        from reformlab.templates.vehicle_malus.compute import VehicleMalusParameters

        policy = VehicleMalusParameters(
            rate_schedule={2025: 50.0},
            emission_threshold=118.0,
            malus_rate_per_gkm=50.0,
        )
        result = _translate_policy_for_live_execution(policy, "test-malus")
        assert result is policy

    def test_translate_policy_for_live_execution_energy_poverty_aid(self) -> None:
        """AC #2: Energy poverty aid policy is translated for adapter consumption."""
        from reformlab.interfaces.api import _translate_policy_for_live_execution
        from reformlab.templates.energy_poverty_aid.compute import (
            EnergyPovertyAidParameters,
        )

        policy = EnergyPovertyAidParameters(
            rate_schedule={2025: 150.0},
            income_ceiling=11000.0,
            base_aid_amount=150.0,
        )
        result = _translate_policy_for_live_execution(policy, "test-aid")
        assert result is policy

    def test_translate_policy_carbon_tax_passthrough(self) -> None:
        """AC #8: Carbon tax passes through translation unchanged."""
        from reformlab.interfaces.api import _translate_policy_for_live_execution
        from reformlab.templates.schema import CarbonTaxParameters

        policy = CarbonTaxParameters(rate_schedule={2025: 44.6})
        result = _translate_policy_for_live_execution(policy, "test-ct")
        assert result is policy

    def test_translate_policy_invalid_subsidy_raises_configuration_error(self) -> None:
        """AC #4: Invalid subsidy parameters raise ConfigurationError."""
        from reformlab.interfaces.api import _translate_policy_for_live_execution
        from reformlab.interfaces.errors import ConfigurationError
        from reformlab.templates.schema import SubsidyParameters

        policy = SubsidyParameters(rate_schedule={})
        with pytest.raises(ConfigurationError, match="rate_schedule"):
            _translate_policy_for_live_execution(policy, "test-bad-subsidy")


# ============================================================================
# Normalization mapping tests
# ============================================================================


class TestNormalizationMappings:
    """Tests for subsidy-family output variable normalization."""

    def test_default_mapping_includes_subsidy_amount(self) -> None:
        from reformlab.computation.result_normalizer import _DEFAULT_OUTPUT_MAPPING

        assert "montant_subvention" in _DEFAULT_OUTPUT_MAPPING
        assert _DEFAULT_OUTPUT_MAPPING["montant_subvention"] == "subsidy_amount"

    def test_default_mapping_includes_subsidy_eligible(self) -> None:
        from reformlab.computation.result_normalizer import _DEFAULT_OUTPUT_MAPPING

        assert "eligible_subvention" in _DEFAULT_OUTPUT_MAPPING
        assert _DEFAULT_OUTPUT_MAPPING["eligible_subvention"] == "subsidy_eligible"

    def test_default_mapping_includes_vehicle_malus(self) -> None:
        from reformlab.computation.result_normalizer import _DEFAULT_OUTPUT_MAPPING

        assert "malus_ecologique" in _DEFAULT_OUTPUT_MAPPING
        assert _DEFAULT_OUTPUT_MAPPING["malus_ecologique"] == "vehicle_malus"

    def test_default_mapping_includes_energy_poverty_aid(self) -> None:
        from reformlab.computation.result_normalizer import _DEFAULT_OUTPUT_MAPPING

        assert "aide_energie" in _DEFAULT_OUTPUT_MAPPING
        assert _DEFAULT_OUTPUT_MAPPING["aide_energie"] == "energy_poverty_aid"

    def test_live_output_variables_include_new_french_names(self) -> None:
        from reformlab.computation.result_normalizer import _DEFAULT_LIVE_OUTPUT_VARIABLES

        assert "montant_subvention" in _DEFAULT_LIVE_OUTPUT_VARIABLES
        assert "eligible_subvention" in _DEFAULT_LIVE_OUTPUT_VARIABLES
        assert "malus_ecologique" in _DEFAULT_LIVE_OUTPUT_VARIABLES
        assert "aide_energie" in _DEFAULT_LIVE_OUTPUT_VARIABLES

    def test_normalization_renames_subsidy_columns(self) -> None:
        """AC #7: Subsidy-family outputs are normalized correctly."""
        import pyarrow as pa

        from reformlab.computation.result_normalizer import _apply_default_mapping

        table = pa.table({
            "montant_subvention": pa.array([1000.0, 2000.0]),
            "eligible_subvention": pa.array([1.0, 0.0]),
            "salaire_net": pa.array([30000.0, 50000.0]),
        })
        result = _apply_default_mapping(table)
        assert "subsidy_amount" in result.column_names
        assert "subsidy_eligible" in result.column_names
        assert "income" in result.column_names

    def test_normalization_renames_vehicle_malus_column(self) -> None:
        import pyarrow as pa

        from reformlab.computation.result_normalizer import _apply_default_mapping

        table = pa.table({
            "malus_ecologique": pa.array([500.0, 0.0]),
            "salaire_net": pa.array([30000.0, 50000.0]),
        })
        result = _apply_default_mapping(table)
        assert "vehicle_malus" in result.column_names

    def test_normalization_renames_energy_poverty_aid_column(self) -> None:
        import pyarrow as pa

        from reformlab.computation.result_normalizer import _apply_default_mapping

        table = pa.table({
            "aide_energie": pa.array([150.0, 0.0]),
            "salaire_net": pa.array([30000.0, 50000.0]),
        })
        result = _apply_default_mapping(table)
        assert "energy_poverty_aid" in result.column_names


# ============================================================================
# Adapter interface non-modification tests (AC #3)
# ============================================================================


class TestAdapterInterfaceUnchanged:
    """Tests that adapter interfaces were not modified."""

    def test_computation_adapter_protocol_unchanged(self) -> None:
        """AC #3: ComputationAdapter protocol has no subsidy-specific methods."""
        from reformlab.computation.adapter import ComputationAdapter

        # Only compute() and version() should be in the protocol
        protocol_methods = {
            name
            for name in dir(ComputationAdapter)
            if not name.startswith("_")
        }
        # Must contain compute and version, must NOT contain subsidy/malus/aid methods
        assert "compute" in protocol_methods
        assert "version" in protocol_methods
        for forbidden in ("translate", "subsidy", "malus", "energy_poverty"):
            matching = [m for m in protocol_methods if forbidden in m.lower()]
            assert len(matching) == 0, (
                f"ComputationAdapter should not have '{forbidden}' methods: {matching}"
            )
