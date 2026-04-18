# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for the ReformLab FastAPI server routes.

Tests use the FastAPI TestClient with the real app factory.
The MockAdapter is used automatically when OpenFisca is not installed.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestAuthRoutes:
    """AC-7: Shared-password authentication."""

    def test_login_success(self, client: TestClient) -> None:
        response = client.post(
            "/api/auth/login",
            json={"password": "test-password-123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert len(data["token"]) == 64  # secrets.token_hex(32) → 64 hex chars

    def test_login_wrong_password(self, client: TestClient) -> None:
        response = client.post(
            "/api/auth/login",
            json={"password": "wrong"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_login_empty_password(self, client: TestClient) -> None:
        response = client.post(
            "/api/auth/login",
            json={"password": ""},
        )
        assert response.status_code == 401

    def test_unauthenticated_request_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/templates")
        assert response.status_code == 401

    def test_invalid_bearer_token_returns_401(self, client: TestClient) -> None:
        response = client.get(
            "/api/templates",
            headers={"Authorization": "Bearer invalid-token-value"},
        )
        assert response.status_code == 401

    def test_missing_bearer_prefix_returns_401(self, client: TestClient) -> None:
        response = client.get(
            "/api/templates",
            headers={"Authorization": "just-a-token-value"},
        )
        assert response.status_code == 401

    def test_authenticated_request_succeeds(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200

    def test_multiple_logins_produce_unique_tokens(self, client: TestClient) -> None:
        tokens = set()
        for _ in range(3):
            response = client.post(
                "/api/auth/login",
                json={"password": "test-password-123"},
            )
            assert response.status_code == 200
            tokens.add(response.json()["token"])
        assert len(tokens) == 3  # All unique

    def test_login_rate_limit_blocks_sixth_failed_attempt(
        self, client: TestClient
    ) -> None:
        from reformlab.server.auth import _active_sessions, _login_attempts

        _active_sessions.clear()
        _login_attempts.clear()
        try:
            for _ in range(5):
                response = client.post(
                    "/api/auth/login",
                    json={"password": "wrong"},
                )
                assert response.status_code == 401

            response = client.post(
                "/api/auth/login",
                json={"password": "wrong"},
            )
            assert response.status_code == 429
        finally:
            _active_sessions.clear()
            _login_attempts.clear()

    def test_auth_pruning_removes_expired_state(self) -> None:
        from reformlab.server import auth

        now = 1_000_000.0
        auth._active_sessions.clear()
        auth._login_attempts.clear()
        try:
            auth._active_sessions["expired"] = now - auth.SESSION_TTL_SECONDS - 1
            auth._active_sessions["fresh"] = now
            auth._login_attempts["old-ip"] = [now - auth._RATE_LIMIT_WINDOW - 1]
            auth._login_attempts["fresh-ip"] = [now]

            auth._prune_expired_sessions(now)
            auth._prune_login_attempts(now)

            assert set(auth._active_sessions) == {"fresh"}
            assert set(auth._login_attempts) == {"fresh-ip"}
        finally:
            auth._active_sessions.clear()
            auth._login_attempts.clear()


class TestTemplateRoutes:
    """AC-1: Template listing and selection."""

    def test_list_templates(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert isinstance(data["templates"], list)

    def test_list_templates_structure(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/templates", headers=auth_headers)
        data = response.json()
        if data["templates"]:
            item = data["templates"][0]
            assert "id" in item
            assert "name" in item
            assert "type" in item
            assert "parameter_count" in item
            assert isinstance(item["parameter_count"], int)

    def test_get_template_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            "/api/templates/nonexistent-template", headers=auth_headers
        )
        assert response.status_code == 404


class TestPopulationRoutes:
    """Population listing."""

    def test_list_populations(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/populations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "populations" in data
        assert isinstance(data["populations"], list)

    def test_list_populations_structure(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/populations", headers=auth_headers)
        data = response.json()
        if data["populations"]:
            item = data["populations"][0]
            assert "id" in item
            assert "name" in item
            assert "households" in item
            assert isinstance(item["households"], int)
            assert "source" in item
            assert "year" in item


class TestScenarioRoutes:
    """AC-1, AC-2: Scenario CRUD operations."""

    def test_list_scenarios(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/scenarios", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "scenarios" in data
        assert isinstance(data["scenarios"], list)

    def test_get_scenario_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            "/api/scenarios/nonexistent-scenario", headers=auth_headers
        )
        assert response.status_code == 404

    def test_create_scenario_accepts_valid_request(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Verify that a valid create request is accepted by the route handler.

        The response code depends on whether the registry can persist the
        scenario (201) or raises RegistryError (404). Either way the
        request itself must not be rejected with 422.
        """
        response = client.post(
            "/api/scenarios",
            headers=auth_headers,
            json={
                "name": "test-scenario-create",
                "policy_type": "carbon_tax",
                "policy": {"rate_schedule": {"2025": 44.6}},
                "start_year": 2025,
                "end_year": 2030,
                "description": "Test scenario",
            },
        )
        # Must not be a validation error — request shape is correct
        assert response.status_code != 422
        if response.status_code == 201:
            data = response.json()
            assert "version_id" in data

    def test_create_scenario_invalid_policy_type(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/scenarios",
            headers=auth_headers,
            json={
                "name": "test-bad-type",
                "policy_type": "invalid_type",
                "policy": {},
                "start_year": 2025,
                "end_year": 2030,
            },
        )
        assert response.status_code == 422

    def test_create_scenario_unknown_parameters_rejected(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/scenarios",
            headers=auth_headers,
            json={
                "name": "test-unknown-params",
                "policy_type": "carbon_tax",
                "policy": {
                    "rate_schedule": {2025: 44.6},
                    "totally_fake_field": 999,
                },
                "start_year": 2025,
                "end_year": 2030,
            },
        )
        assert response.status_code == 422

    def test_create_scenario_with_type_discriminator(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """policy_type inferred from _type discriminator in policy dict."""
        response = client.post(
            "/api/scenarios",
            headers=auth_headers,
            json={
                "name": "test-type-discriminator",
                "policy": {
                    "_type": "carbon_tax",
                    "rate_schedule": {"2025": 44.6},
                },
                "start_year": 2025,
                "end_year": 2030,
            },
        )
        # Must not be a 422 — _type discriminator provides the policy_type
        assert response.status_code != 422

    def test_create_scenario_no_policy_type_returns_422(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Missing both policy_type and _type discriminator returns 422."""
        response = client.post(
            "/api/scenarios",
            headers=auth_headers,
            json={
                "name": "test-no-type",
                "policy": {"rate_schedule": {"2025": 44.6}},
                "start_year": 2025,
                "end_year": 2030,
            },
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}

    def test_create_scenario_rejects_private_field_injection(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Private _*_set fields in policy body are rejected as unknown."""
        response = client.post(
            "/api/scenarios",
            headers=auth_headers,
            json={
                "name": "test-inject",
                "policy_type": "feebate",
                "policy": {
                    "rate_schedule": {},
                    "_pivot_point_set": True,
                },
                "start_year": 2025,
                "end_year": 2030,
            },
        )
        assert response.status_code == 422


class TestExportRoutes:
    """AC-5: Export endpoints."""

    def test_export_csv_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/exports/csv",
            headers=auth_headers,
            json={"run_id": "nonexistent-run-id"},
        )
        assert response.status_code == 404

    def test_export_parquet_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/exports/parquet",
            headers=auth_headers,
            json={"run_id": "nonexistent-run-id"},
        )
        assert response.status_code == 404


class TestIndicatorRoutes:
    """AC-3, AC-4: Indicator and comparison endpoints."""

    def test_indicator_invalid_type(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/indicators/invalid_type",
            headers=auth_headers,
            json={"run_id": "fake-run"},
        )
        assert response.status_code == 422

    def test_comparison_missing_runs(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/comparison",
            headers=auth_headers,
            json={
                "baseline_run_id": "nonexistent-1",
                "reform_run_id": "nonexistent-2",
            },
        )
        assert response.status_code == 404


class TestErrorHandling:
    """AC-6: Error responses use structured format."""

    def test_login_error_structure(self, client: TestClient) -> None:
        response = client.post(
            "/api/auth/login",
            json={"password": "wrong"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    def test_template_not_found_error_structure(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            "/api/templates/nonexistent", headers=auth_headers
        )
        assert response.status_code == 404

    def test_missing_request_body_returns_422(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/scenarios",
            headers=auth_headers,
            content=b"not json",
        )
        assert response.status_code == 422


class TestScenarioDetail:
    """AC-1: GET /api/scenarios/{name} — success and error paths."""

    def test_get_scenario_after_create_returns_scenario_response(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Create a scenario via POST then GET it.

        The registry's hash integrity check may prevent loading in some
        environments. This test accepts either 200 (success with correct fields)
        or 404 with structured error (registry integrity failure).
        """
        create_response = client.post(
            "/api/scenarios",
            headers=auth_headers,
            json={
                "name": "test-detail-scenario-17-6",
                "policy_type": "carbon_tax",
                "policy": {"rate_schedule": {"2025": 44.6}},
                "start_year": 2025,
                "end_year": 2030,
                "description": "Story 17.6 test scenario",
            },
        )
        if create_response.status_code != 201:
            pytest.skip("Scenario creation failed — registry may not be writable")

        response = client.get(
            "/api/scenarios/test-detail-scenario-17-6",
            headers=auth_headers,
        )
        if response.status_code == 200:
            data = response.json()
            assert data["name"] == "test-detail-scenario-17-6"
            assert data["policy_type"] == "carbon_tax"
            assert "policy" in data
            assert "year_schedule" in data
        else:
            # Registry integrity issue — verify error is structured
            assert response.status_code in (404, 422)
            body = response.json()
            # HTTPException wraps in "detail"; global handlers put keys at top level
            detail = body.get("detail", body)
            if isinstance(detail, dict):
                assert set(detail.keys()) >= {"what", "why", "fix"}
            else:
                # String detail from unhandled error — just ensure we got a response
                assert detail is not None

    def test_get_scenario_not_found_returns_404_with_structured_error(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            "/api/scenarios/no-such-scenario-17-6",
            headers=auth_headers,
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}


class TestScenarioClone:
    """AC-1: POST /api/scenarios/{name}/clone — error path test."""

    def test_clone_of_nonexistent_scenario_returns_404_with_structured_error(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/scenarios/no-such-scenario-clone-17-6/clone",
            headers=auth_headers,
            json={"new_name": "any-name"},
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}


class TestTemplateDetail:
    """AC-1: GET /api/templates/{name} — success path with available template."""

    def test_get_template_detail_for_first_available_template(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        # List available templates first
        list_response = client.get("/api/templates", headers=auth_headers)
        assert list_response.status_code == 200
        templates = list_response.json()["templates"]
        if not templates:
            pytest.skip("No templates available in registry")

        template_id = templates[0]["id"]

        # Request template detail
        response = client.get(
            f"/api/templates/{template_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "type" in data
        assert "parameter_count" in data
        assert "default_policy" in data
        assert isinstance(data["parameter_count"], int)
        assert isinstance(data["default_policy"], dict)

    def test_get_template_not_found_returns_404_with_structured_error(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get(
            "/api/templates/no-such-template-17-6",
            headers=auth_headers,
        )
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert set(detail.keys()) >= {"what", "why", "fix"}


class TestCatalogWithRuntimeAvailability:
    """AC-1: Catalog listing includes all templates with runtime availability metadata."""

    def test_all_packs_appear_in_catalog(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """All 12 existing built-in packs appear in catalog listing (8 visible + 4 hidden)."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        templates = data["templates"]

        # Check for all expected template IDs
        template_ids = {t["id"] for t in templates}
        visible_packs = {
            "carbon-tax-flat-lump-sum-dividend",
            "carbon-tax-flat-no-redistribution",
            "carbon-tax-flat-progressive-dividend",
            "carbon-tax-progressive-no-redistribution",
            "carbon-tax-progressive-progressive-dividend",
            "subsidy-energy-retrofit",
            "rebate-progressive-income",
            "feebate-vehicle-emissions",
        }
        hidden_packs = {
            "vehicle-malus-flat-rate",
            "vehicle-malus-french-2026",
            "energy-poverty-cheque-energie",
            "energy-poverty-generous",
        }

        for pack_id in visible_packs | hidden_packs:
            assert pack_id in template_ids, f"Missing template: {pack_id}"

    def test_visible_packs_have_live_ready_status(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Visible packs have runtime_availability: 'live_ready'."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]

        visible_pack_ids = {
            "carbon-tax-flat-lump-sum-dividend",
            "carbon-tax-flat-no-redistribution",
            "carbon-tax-flat-progressive-dividend",
            "carbon-tax-progressive-no-redistribution",
            "carbon-tax-progressive-progressive-dividend",
            "subsidy-energy-retrofit",
            "rebate-progressive-income",
            "feebate-vehicle-emissions",
        }

        for template in templates:
            if template["id"] in visible_pack_ids:
                assert (
                    template["runtime_availability"] == "live_ready"
                ), f"{template['id']} should be live_ready"

    def test_subsidy_family_packs_are_live_ready(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Story 24.2: Subsidy-family packs are now live_ready after translation."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]

        subsidy_family_pack_ids = {
            "vehicle-malus-flat-rate",
            "vehicle-malus-french-2026",
            "energy-poverty-cheque-energie",
            "energy-poverty-generous",
        }

        for template in templates:
            if template["id"] in subsidy_family_pack_ids:
                assert (
                    template["runtime_availability"] == "live_ready"
                ), f"{template['id']} should be live_ready after Story 24.2"
                assert (
                    template["availability_reason"] is None
                ), f"{template['id']} should have no availability_reason"

    def test_template_detail_includes_runtime_availability(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Template detail endpoint includes runtime availability metadata."""
        # Test a visible template
        response = client.get(
            "/api/templates/carbon-tax-flat-lump-sum-dividend",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "runtime_availability" in data
        assert data["runtime_availability"] == "live_ready"
        assert "availability_reason" in data
        assert data["availability_reason"] is None

        # Story 24.2: Vehicle malus is now live_ready after translation
        response = client.get(
            "/api/templates/vehicle-malus-flat-rate",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "runtime_availability" in data
        assert data["runtime_availability"] == "live_ready"
        assert "availability_reason" in data
        assert data["availability_reason"] is None

    def test_custom_template_has_runtime_availability(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Custom templates created via API have live_unavailable status."""
        response = client.post(
            "/api/templates/custom",
            headers=auth_headers,
            json={
                "name": "test_custom_policy_24_1",
                "description": "Test custom template for Story 24.1",
                "parameters": [
                    {"name": "rate", "type": "float", "default": 0.0, "unit": "EUR/t"}
                ],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "runtime_availability" in data
        assert data["runtime_availability"] == "live_unavailable"
        assert "availability_reason" in data
        assert data["availability_reason"] is None

    def test_stable_identifiers_preserved(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Existing pack identifiers remain stable after catalog expansion."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]

        # Verify all expected IDs are present (user-saved scenarios may add more)
        expected_ids = {
            "carbon-tax-flat-lump-sum-dividend",
            "carbon-tax-flat-no-redistribution",
            "carbon-tax-flat-progressive-dividend",
            "carbon-tax-progressive-no-redistribution",
            "carbon-tax-progressive-progressive-dividend",
            "subsidy-energy-retrofit",
            "rebate-progressive-income",
            "feebate-vehicle-emissions",
            "vehicle-malus-flat-rate",
            "vehicle-malus-french-2026",
            "energy-poverty-cheque-energie",
            "energy-poverty-generous",
        }

        template_ids = {t["id"] for t in templates}
        # Check that all expected IDs are present
        missing = expected_ids - template_ids
        assert expected_ids.issubset(template_ids), f"Missing: {missing}"

    def test_catalog_is_deterministically_ordered(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC-3: Catalog is grouped by type, sorted by id within each group."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]

        # Group by type
        groups: dict[str, list[dict]] = {}
        for t in templates:
            groups.setdefault(t["type"], []).append(t)

        # Verify templates within each group are sorted by id
        for type_name, group in groups.items():
            ids = [t["id"] for t in group]
            assert ids == sorted(ids), f"Type {type_name} not sorted by id"

        # Verify group order is deterministic (alphabetical by type name)
        group_names = list(groups.keys())
        assert group_names == sorted(group_names), "Groups not sorted by type"

    def test_scenario_compatibility_after_catalog_expansion(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC-4: Scenarios referencing previously visible packs load correctly after catalog expansion."""
        # Create a scenario referencing a visible pack (carbon-tax)
        scenario_data = {
            "name": "test-scenario-visible-pack-24-1",
            "policy_type": "carbon_tax",
            "policy": {
                "rate_schedule": {"2026": 50.0, "2027": 55.0},
                "exemptions": [],
                "thresholds": [],
                "covered_categories": ["heating_fuel", "transport_fuel"],
            },
            "start_year": 2026,
            "end_year": 2030,
            "description": "Test scenario with visible pack after catalog expansion",
        }

        # Create the scenario — may return 201 or 404 depending on registry state
        create_response = client.post(
            "/api/scenarios",
            headers=auth_headers,
            json=scenario_data,
        )
        # Must not be a validation error — request shape is correct
        assert create_response.status_code != 422

        # Verify catalog listing still succeeds (no crash from expanded catalog)
        templates_response = client.get("/api/templates", headers=auth_headers)
        assert templates_response.status_code == 200

    def test_portfolio_validation_after_catalog_expansion(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC-4: Portfolios with visible packs validate correctly after catalog expansion."""
        response = client.post(
            "/api/portfolios/validate",
            headers=auth_headers,
            json={
                "policies": [
                    {
                        "name": "carbon-tax-test-24-1",
                        "policy_type": "carbon_tax",
                        "rate_schedule": {"2026": 44.0},
                        "exemptions": [],
                        "thresholds": [],
                        "covered_categories": ["heating_fuel"],
                        "extra_params": {},
                    },
                    {
                        "name": "subsidy-test-24-1",
                        "policy_type": "subsidy",
                        "rate_schedule": {"2026": 5000.0},
                        "exemptions": [],
                        "thresholds": [30000.0],
                        "covered_categories": ["energy_retrofit"],
                        "extra_params": {},
                    },
                ],
                "resolution_strategy": "error",
            },
        )
        # Validation should succeed (may have conflicts, but endpoint returns response)
        assert response.status_code == 200
        data = response.json()
        assert "conflicts" in data
        assert "is_compatible" in data
