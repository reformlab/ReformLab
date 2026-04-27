# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for categories API — Story 25.1."""

from __future__ import annotations

from fastapi.testclient import TestClient

# ============================================================================
# Story 25.1 / AC-1: GET /api/categories returns categories with full schema
# ============================================================================

class TestListCategories:
    """Tests for GET /api/categories endpoint — Story 25.1, AC-1."""

    def test_categories_response_shape(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """AC-1: Categories endpoint returns array with correct structure."""
        response = client.get("/api/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # First category should have all required fields
        cat = data[0]
        assert "id" in cat
        assert "label" in cat
        assert "columns" in cat
        assert "compatible_types" in cat
        assert "formula_explanation" in cat
        assert "description" in cat

    def test_categories_field_types(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """AC-1: Category fields have correct types."""
        response = client.get("/api/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        cat = data[0]

        assert isinstance(cat["id"], str)
        assert isinstance(cat["label"], str)
        assert isinstance(cat["columns"], list)
        assert all(isinstance(col, str) for col in cat["columns"])
        assert isinstance(cat["compatible_types"], list)
        assert all(isinstance(t, str) for t in cat["compatible_types"])
        assert isinstance(cat["formula_explanation"], str)
        assert isinstance(cat["description"], str)

    def test_categories_content(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """AC-1: Categories contain expected content from story spec."""
        response = client.get("/api/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        # Should have carbon_emissions category
        carbon_cat = next((c for c in data if c["id"] == "carbon_emissions"), None)
        assert carbon_cat is not None
        assert carbon_cat["label"] == "Carbon Emissions"
        assert "emissions_co2" in carbon_cat["columns"]
        assert "tax" in carbon_cat["compatible_types"]
        assert carbon_cat["formula_explanation"] == "emissions_co2 × tax_rate"

    def test_categories_auth_required(self, client: TestClient) -> None:
        """AC-1: Categories endpoint requires authentication."""
        response = client.get("/api/categories")
        assert response.status_code == 401


# ============================================================================
# Story 25.1 / Task 1.6: category_id field in template listings
# ============================================================================

class TestTemplateCategoryMapping:
    """Tests for category_id in TemplateListItem — Story 25.1, Task 1.6."""

    def test_template_list_includes_category_id(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Task 1.6: Template list items include category_id field."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        templates = data["templates"]
        assert len(templates) > 0

        # All templates should have category_id field
        for tmpl in templates:
            assert "category_id" in tmpl
            # category_id can be None for templates without a category

    def test_carbon_tax_templates_mapped_to_carbon_emissions(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Task 1.6: Carbon tax templates map to carbon_emissions category."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        templates = data["templates"]

        # Find carbon_tax templates
        carbon_tax_templates = [t for t in templates if t["type"] == "carbon_tax"]
        assert len(carbon_tax_templates) > 0, "Expected at least one carbon_tax template"
        for tmpl in carbon_tax_templates:
            assert tmpl["category_id"] == "carbon_emissions"

    def test_vehicle_malus_templates_mapped_to_vehicle_emissions(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Task 1.6: Vehicle malus templates map to vehicle_emissions category."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        templates = data["templates"]

        # Find vehicle_malus templates
        vehicle_templates = [t for t in templates if t["type"] == "vehicle_malus"]
        assert len(vehicle_templates) > 0, "Expected at least one vehicle_malus template"
        for tmpl in vehicle_templates:
            assert tmpl["category_id"] == "vehicle_emissions"

    def test_energy_poverty_aid_templates_mapped_to_income(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Task 1.6: Energy poverty aid templates map to income category."""
        response = client.get("/api/templates", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        templates = data["templates"]

        # Find energy_poverty_aid templates
        energy_templates = [t for t in templates if t["type"] == "energy_poverty_aid"]
        assert len(energy_templates) > 0, "Expected at least one energy_poverty_aid template"
        for tmpl in energy_templates:
            assert tmpl["category_id"] == "income"
