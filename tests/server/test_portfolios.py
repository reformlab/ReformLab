# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for portfolio CRUD API routes — Story 17.2.

Tests cover all endpoints in /api/portfolios:
- GET /api/portfolios (list)
- GET /api/portfolios/{name} (detail)
- POST /api/portfolios (create)
- PUT /api/portfolios/{name} (update)
- DELETE /api/portfolios/{name} (delete)
- POST /api/portfolios/{name}/clone (clone)
- POST /api/portfolios/validate (validate)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Shared payload helpers
# ---------------------------------------------------------------------------

_VALID_POLICIES = [
    {
        "name": "Carbon Tax",
        "policy_type": "carbon_tax",
        "rate_schedule": {"2025": 50.0, "2026": 60.0},
        "exemptions": [],
        "thresholds": [],
        "covered_categories": [],
        "extra_params": {},
    },
    {
        "name": "Energy Subsidy",
        "policy_type": "subsidy",
        "rate_schedule": {"2025": 5000.0},
        "exemptions": [],
        "thresholds": [],
        "covered_categories": [],
        "extra_params": {},
    },
]

_CREATE_BODY = {
    "name": "test-portfolio",
    "description": "Test portfolio",
    "policies": _VALID_POLICIES,
    "resolution_strategy": "error",
}


# ---------------------------------------------------------------------------
# Validate endpoint (static route — must be matched before /{name})
# ---------------------------------------------------------------------------


class TestValidateEndpoint:
    """AC-6: Conflict validation without saving."""

    def test_validate_non_conflicting_portfolio(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/portfolios/validate",
            json={"policies": _VALID_POLICIES, "resolution_strategy": "error"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "conflicts" in data
        assert "is_compatible" in data
        assert isinstance(data["conflicts"], list)
        assert isinstance(data["is_compatible"], bool)

    def test_validate_requires_min_2_policies(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/portfolios/validate",
            json={"policies": [_VALID_POLICIES[0]], "resolution_strategy": "error"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_validate_invalid_policy_type(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        bad_policies = [
            {**_VALID_POLICIES[0], "policy_type": "not_a_type"},
            _VALID_POLICIES[1],
        ]
        response = client.post(
            "/api/portfolios/validate",
            json={"policies": bad_policies, "resolution_strategy": "error"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_validate_invalid_resolution_strategy(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/portfolios/validate",
            json={"policies": _VALID_POLICIES, "resolution_strategy": "bad_strategy"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_validate_response_structure(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/portfolios/validate",
            json={"policies": _VALID_POLICIES, "resolution_strategy": "error"},
            headers=auth_headers,
        )
        data = response.json()
        assert set(data.keys()) >= {"conflicts", "is_compatible"}


# ---------------------------------------------------------------------------
# List portfolios
# ---------------------------------------------------------------------------


class TestListPortfolios:
    """GET /api/portfolios — returns list of portfolio summaries."""

    def test_list_returns_list(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/portfolios", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/portfolios")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Create portfolio
# ---------------------------------------------------------------------------


class TestCreatePortfolio:
    """POST /api/portfolios — creates and saves a portfolio."""

    def test_create_returns_version_id(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            response = client.post(
                "/api/portfolios",
                json=_CREATE_BODY,
                headers=auth_headers,
            )
            assert response.status_code == 201
            data = response.json()
            assert "version_id" in data
            assert isinstance(data["version_id"], str)
            assert len(data["version_id"]) > 0
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]

    def test_create_requires_min_2_policies(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        body = {**_CREATE_BODY, "policies": [_VALID_POLICIES[0]]}
        response = client.post("/api/portfolios", json=body, headers=auth_headers)
        assert response.status_code == 400

    def test_create_rejects_invalid_name(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        body = {**_CREATE_BODY, "name": "INVALID_NAME"}
        response = client.post("/api/portfolios", json=body, headers=auth_headers)
        assert response.status_code == 422

    def test_create_rejects_reserved_name_validate(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        body = {**_CREATE_BODY, "name": "validate"}
        response = client.post("/api/portfolios", json=body, headers=auth_headers)
        assert response.status_code == 422

    def test_create_rejects_reserved_name_clone(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        body = {**_CREATE_BODY, "name": "clone"}
        response = client.post("/api/portfolios", json=body, headers=auth_headers)
        assert response.status_code == 422

    def test_create_invalid_policy_type(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        bad_policies = [{**_VALID_POLICIES[0], "policy_type": "unknown"}, _VALID_POLICIES[1]]
        body = {**_CREATE_BODY, "policies": bad_policies}
        response = client.post("/api/portfolios", json=body, headers=auth_headers)
        assert response.status_code == 422

    def test_create_conflict_409_on_duplicate_name(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            # First create
            r1 = client.post("/api/portfolios", json=_CREATE_BODY, headers=auth_headers)
            assert r1.status_code == 201
            # Second create same name
            r2 = client.post("/api/portfolios", json=_CREATE_BODY, headers=auth_headers)
            assert r2.status_code == 409
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]


# ---------------------------------------------------------------------------
# Get portfolio
# ---------------------------------------------------------------------------


class TestGetPortfolio:
    """GET /api/portfolios/{name} — returns portfolio detail."""

    def test_get_nonexistent_returns_404(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            response = client.get("/api/portfolios/does-not-exist", headers=auth_headers)
            assert response.status_code == 404
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]

    def test_get_returns_portfolio_detail(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            # Create first
            client.post("/api/portfolios", json=_CREATE_BODY, headers=auth_headers)
            # Then get
            response = client.get("/api/portfolios/test-portfolio", headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "test-portfolio"
            assert "version_id" in data
            assert "policies" in data
            assert data["policy_count"] == 2
            assert data["resolution_strategy"] == "error"
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]

    def test_get_detail_policy_structure(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            client.post("/api/portfolios", json=_CREATE_BODY, headers=auth_headers)
            response = client.get("/api/portfolios/test-portfolio", headers=auth_headers)
            data = response.json()
            policy = data["policies"][0]
            assert "name" in policy
            assert "policy_type" in policy
            assert "rate_schedule" in policy
            assert "parameters" in policy
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]


# ---------------------------------------------------------------------------
# Update portfolio
# ---------------------------------------------------------------------------


class TestUpdatePortfolio:
    """PUT /api/portfolios/{name} — updates portfolio."""

    def test_update_nonexistent_returns_404(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            body = {"policies": _VALID_POLICIES, "resolution_strategy": "error"}
            response = client.put("/api/portfolios/does-not-exist", json=body, headers=auth_headers)
            assert response.status_code == 404
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]

    def test_update_returns_updated_detail(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            # Create
            client.post("/api/portfolios", json=_CREATE_BODY, headers=auth_headers)
            # Update with new description
            update_body = {
                "description": "Updated description",
                "policies": _VALID_POLICIES,
                "resolution_strategy": "sum",
            }
            response = client.put("/api/portfolios/test-portfolio", json=update_body, headers=auth_headers)
            assert response.status_code == 200
            data = response.json()
            assert data["resolution_strategy"] == "sum"
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]

    def test_update_requires_min_2_policies(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            client.post("/api/portfolios", json=_CREATE_BODY, headers=auth_headers)
            body = {"policies": [_VALID_POLICIES[0]], "resolution_strategy": "error"}
            response = client.put("/api/portfolios/test-portfolio", json=body, headers=auth_headers)
            assert response.status_code == 400
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]


# ---------------------------------------------------------------------------
# Delete portfolio
# ---------------------------------------------------------------------------


class TestDeletePortfolio:
    """DELETE /api/portfolios/{name} — removes a portfolio."""

    def test_delete_nonexistent_returns_404(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            response = client.delete("/api/portfolios/does-not-exist", headers=auth_headers)
            assert response.status_code == 404
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]

    def test_delete_returns_204(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            # Create
            client.post("/api/portfolios", json=_CREATE_BODY, headers=auth_headers)
            # Delete
            response = client.delete("/api/portfolios/test-portfolio", headers=auth_headers)
            assert response.status_code == 204
            # Confirm gone
            get_resp = client.get("/api/portfolios/test-portfolio", headers=auth_headers)
            assert get_resp.status_code == 404
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]


# ---------------------------------------------------------------------------
# Clone portfolio
# ---------------------------------------------------------------------------


class TestClonePortfolio:
    """POST /api/portfolios/{name}/clone — clones a portfolio."""

    def test_clone_source_not_found_returns_404(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            response = client.post(
                "/api/portfolios/does-not-exist/clone",
                json={"new_name": "cloned-portfolio"},
                headers=auth_headers,
            )
            assert response.status_code == 404
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]

    def test_clone_returns_201_with_detail(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            client.post("/api/portfolios", json=_CREATE_BODY, headers=auth_headers)
            response = client.post(
                "/api/portfolios/test-portfolio/clone",
                json={"new_name": "cloned-portfolio"},
                headers=auth_headers,
            )
            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "cloned-portfolio"
            assert data["policy_count"] == 2
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]

    def test_clone_conflict_409_if_target_exists(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            client.post("/api/portfolios", json=_CREATE_BODY, headers=auth_headers)
            second_body = {**_CREATE_BODY, "name": "second-portfolio"}
            client.post("/api/portfolios", json=second_body, headers=auth_headers)
            # Clone to existing name
            response = client.post(
                "/api/portfolios/test-portfolio/clone",
                json={"new_name": "second-portfolio"},
                headers=auth_headers,
            )
            assert response.status_code == 409
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]

    def test_clone_invalid_new_name_returns_422(
        self, client: TestClient, auth_headers: dict[str, str], tmp_path: object
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            client.post("/api/portfolios", json=_CREATE_BODY, headers=auth_headers)
            response = client.post(
                "/api/portfolios/test-portfolio/clone",
                json={"new_name": "INVALID"},
                headers=auth_headers,
            )
            assert response.status_code == 422
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]


# ---------------------------------------------------------------------------
# Name validation
# ---------------------------------------------------------------------------


class TestPortfolioNameValidation:
    """Portfolio name slug validation."""

    @pytest.mark.parametrize("valid_name", [
        "abc",
        "my-portfolio",
        "green-transition-2030",
        "a1",
        "ab",
    ])
    def test_valid_names_accepted(
        self, client: TestClient, auth_headers: dict[str, str], valid_name: str,
        tmp_path: object,
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            body = {**_CREATE_BODY, "name": valid_name}
            response = client.post("/api/portfolios", json=body, headers=auth_headers)
            assert response.status_code in {201, 409}  # 409 if name already exists
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]

    @pytest.mark.parametrize("invalid_name", [
        "UPPERCASE",
        "has spaces",
        "-starts-with-dash",
        "ends-with-dash-",
        "has/slash",
        "",
        "validate",
        "clone",
    ])
    def test_invalid_names_rejected(
        self, client: TestClient, auth_headers: dict[str, str], invalid_name: str
    ) -> None:
        body = {**_CREATE_BODY, "name": invalid_name}
        response = client.post("/api/portfolios", json=body, headers=auth_headers)
        assert response.status_code in {422, 400}


# ---------------------------------------------------------------------------
# Resolution strategy validation
# ---------------------------------------------------------------------------


class TestResolutionStrategy:
    """Resolution strategy enum validation."""

    @pytest.mark.parametrize("strategy", ["error", "sum", "first_wins", "last_wins", "max"])
    def test_valid_strategies_accepted(
        self, client: TestClient, auth_headers: dict[str, str], strategy: str,
        tmp_path: object,
    ) -> None:
        import os
        os.environ["REFORMLAB_REGISTRY_PATH"] = str(tmp_path)
        try:
            slug = strategy.replace("_", "-")
            body = {**_CREATE_BODY, "name": f"test-{slug}", "resolution_strategy": strategy}
            response = client.post("/api/portfolios", json=body, headers=auth_headers)
            assert response.status_code == 201
        finally:
            del os.environ["REFORMLAB_REGISTRY_PATH"]

    def test_invalid_strategy_rejected(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        body = {**_CREATE_BODY, "resolution_strategy": "invalid_strategy"}
        response = client.post("/api/portfolios", json=body, headers=auth_headers)
        assert response.status_code == 422
