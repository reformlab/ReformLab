# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for custom template CRUD endpoints — Story 4.

Verifies POST /api/templates/custom and DELETE /api/templates/custom/{name}.
"""

from __future__ import annotations

from typing import Any, Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, Any, None]:
    """TestClient with clean custom template registrations."""
    import shutil

    from reformlab.server.dependencies import get_registry
    from reformlab.templates.schema import (
        _CUSTOM_PARAMETERS_TO_POLICY_TYPE,
        _CUSTOM_POLICY_TYPES,
        _reset_custom_registrations,
    )

    # Save existing registrations so we can restore after test
    saved_types = dict(_CUSTOM_POLICY_TYPES)
    saved_params = dict(_CUSTOM_PARAMETERS_TO_POLICY_TYPE)

    _reset_custom_registrations()

    from reformlab.server.app import create_app

    app = create_app()
    yield TestClient(app)

    # Clean up my_custom_tax template from registry
    registry = get_registry()
    my_custom_path = registry.path / "my_custom_tax"
    if my_custom_path.exists():
        shutil.rmtree(my_custom_path)

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


_VALID_BODY = {
    "name": "my_custom_tax",
    "description": "A custom tax template",
    "parameters": [
        {"name": "rate", "type": "float", "default": 10.0, "unit": "EUR/t"},
        {"name": "threshold", "type": "int", "default": 100},
    ],
}


class TestCreateCustomTemplate:
    """POST /api/templates/custom."""

    def test_create_returns_201(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/templates/custom", headers=auth_headers, json=_VALID_BODY
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "my_custom_tax"
        assert data["parameter_count"] == 2
        assert data["is_custom"] is True

    def test_created_template_appears_in_listing(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        client.post("/api/templates/custom", headers=auth_headers, json=_VALID_BODY)
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        templates = response.json()["templates"]
        custom = [t for t in templates if t["name"] == "my_custom_tax"]
        assert len(custom) == 1
        assert custom[0]["is_custom"] is True

    def test_reject_non_snake_case_name(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        body = {**_VALID_BODY, "name": "MyCustomTax"}
        response = client.post(
            "/api/templates/custom", headers=auth_headers, json=body
        )
        assert response.status_code == 422

    def test_reject_builtin_name_collision(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        body = {**_VALID_BODY, "name": "carbon_tax"}
        response = client.post(
            "/api/templates/custom", headers=auth_headers, json=body
        )
        assert response.status_code == 409

    def test_reject_empty_parameters(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        body = {**_VALID_BODY, "parameters": []}
        response = client.post(
            "/api/templates/custom", headers=auth_headers, json=body
        )
        assert response.status_code == 422

    def test_reject_duplicate_registration(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        client.post("/api/templates/custom", headers=auth_headers, json=_VALID_BODY)
        response = client.post(
            "/api/templates/custom", headers=auth_headers, json=_VALID_BODY
        )
        assert response.status_code == 409


class TestDeleteCustomTemplate:
    """DELETE /api/templates/custom/{name}."""

    def test_delete_returns_204(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        client.post("/api/templates/custom", headers=auth_headers, json=_VALID_BODY)
        response = client.delete(
            "/api/templates/custom/my_custom_tax", headers=auth_headers
        )
        assert response.status_code == 204

    def test_delete_removes_from_listing(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        client.post("/api/templates/custom", headers=auth_headers, json=_VALID_BODY)
        client.delete("/api/templates/custom/my_custom_tax", headers=auth_headers)
        response = client.get("/api/templates", headers=auth_headers)
        templates = response.json()["templates"]
        custom = [t for t in templates if t["name"] == "my_custom_tax"]
        assert len(custom) == 0

    def test_delete_builtin_returns_403(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.delete(
            "/api/templates/custom/carbon_tax", headers=auth_headers
        )
        assert response.status_code == 403

    def test_delete_nonexistent_returns_404(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.delete(
            "/api/templates/custom/nonexistent", headers=auth_headers
        )
        assert response.status_code == 404


# ============================================================================
# Story 25.3: POST /api/templates/from-scratch
# ============================================================================

class TestCreateBlankPolicy:
    """Tests for POST /api/templates/from-scratch endpoint — Story 25.3."""

    def test_create_blank_policy_tax_carbon_emissions(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC-2, AC-3: Valid tax policy with carbon_emissions category."""
        response = client.post(
            "/api/templates/from-scratch",
            headers=auth_headers,
            json={"policy_type": "tax", "category_id": "carbon_emissions"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Tax — Carbon Emissions"
        assert data["policy_type"] == "tax"
        assert data["category_id"] == "carbon_emissions"
        assert "parameters" in data
        assert data["parameters"]["rate"] == 0
        assert data["parameters"]["threshold"] == 0
        assert data["parameters"]["ceiling"] is None
        # AC-4: Tax policies have 4 default parameter groups
        assert set(data["parameter_groups"]) == {
            "Mechanism", "Eligibility", "Schedule", "Redistribution"
        }
        assert data["rate_schedule"] == {}

    def test_create_blank_policy_subsidy_housing(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC-5: Subsidy policy has 3 default parameter groups (no Redistribution)."""
        response = client.post(
            "/api/templates/from-scratch",
            headers=auth_headers,
            json={"policy_type": "subsidy", "category_id": "housing"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Subsidy — Housing"
        assert data["policy_type"] == "subsidy"
        assert data["category_id"] == "housing"
        # AC-5: Subsidy policies have 3 default parameter groups
        assert set(data["parameter_groups"]) == {"Mechanism", "Eligibility", "Schedule"}

    def test_create_blank_policy_transfer_income(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC-6: Transfer policy has 3 default parameter groups (no Redistribution)."""
        response = client.post(
            "/api/templates/from-scratch",
            headers=auth_headers,
            json={"policy_type": "transfer", "category_id": "income"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Transfer — Income"
        assert data["policy_type"] == "transfer"
        assert data["category_id"] == "income"
        # AC-6: Transfer policies have 3 default parameter groups
        assert set(data["parameter_groups"]) == {"Mechanism", "Eligibility", "Schedule"}

    def test_create_blank_policy_invalid_type(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Reject invalid policy type (not in closed set: tax, subsidy, transfer)."""
        response = client.post(
            "/api/templates/from-scratch",
            headers=auth_headers,
            json={"policy_type": "invalid_type", "category_id": "carbon_emissions"},
        )
        assert response.status_code == 400
        data = response.json()["detail"]
        assert data["what"] == "Invalid policy type 'invalid_type'"
        assert "tax" in data["why"]
        assert "subsidy" in data["why"]
        assert "transfer" in data["why"]

    def test_create_blank_policy_capitalized_type_rejected(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Policy type must be lowercase (frontend normalizes)."""
        response = client.post(
            "/api/templates/from-scratch",
            headers=auth_headers,
            json={"policy_type": "Tax", "category_id": "carbon_emissions"},
        )
        assert response.status_code == 400
        data = response.json()["detail"]
        assert data["what"] == "Invalid policy type 'Tax'"

    def test_create_blank_policy_invalid_category(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Reject non-existent category_id."""
        response = client.post(
            "/api/templates/from-scratch",
            headers=auth_headers,
            json={"policy_type": "tax", "category_id": "nonexistent_category"},
        )
        assert response.status_code == 400
        data = response.json()["detail"]
        assert "not found" in data["what"].lower()

    def test_create_blank_policy_incompatible_category(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC-2: Reject category if compatible_types excludes policy_type.

        Income category only supports "transfer", not "tax".
        """
        response = client.post(
            "/api/templates/from-scratch",
            headers=auth_headers,
            json={"policy_type": "tax", "category_id": "income"},
        )
        assert response.status_code == 400
        data = response.json()["detail"]
        assert "not compatible" in data["what"].lower()
        assert "income" in data["what"].lower()
        assert "transfer" in data["why"]

    def test_create_blank_policy_vehicle_emissions_tax_ok(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC-2: Vehicle emissions category is compatible with tax."""
        response = client.post(
            "/api/templates/from-scratch",
            headers=auth_headers,
            json={"policy_type": "tax", "category_id": "vehicle_emissions"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Tax — Vehicle Emissions"

    def test_create_blank_policy_vehicle_emissions_subsidy_ok(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC-2: Vehicle emissions category is compatible with subsidy."""
        response = client.post(
            "/api/templates/from-scratch",
            headers=auth_headers,
            json={"policy_type": "subsidy", "category_id": "vehicle_emissions"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Subsidy — Vehicle Emissions"

    def test_create_blank_policy_vehicle_emissions_transfer_rejected(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """AC-2: Vehicle emissions category does NOT support transfer."""
        response = client.post(
            "/api/templates/from-scratch",
            headers=auth_headers,
            json={"policy_type": "transfer", "category_id": "vehicle_emissions"},
        )
        assert response.status_code == 400
        data = response.json()["detail"]
        assert "not compatible" in data["what"].lower()

    def test_create_blank_policy_auth_required(
        self, client: TestClient
    ) -> None:
        """Endpoint requires authentication."""
        response = client.post(
            "/api/templates/from-scratch",
            json={"policy_type": "tax", "category_id": "carbon_emissions"},
        )
        assert response.status_code == 401
