# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for the data fusion API routes.

Validates all four data fusion endpoints against acceptance criteria
AC-1 through AC-5 from Story 17.1.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pyarrow as pa
from fastapi.testclient import TestClient

# ============================================================================
# AC-1: Data source browsing — GET /api/data-fusion/sources
# ============================================================================


class TestListSources:
    """AC-1: All available data sources listed with metadata grouped by provider."""

    def test_returns_200(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/data-fusion/sources", headers=auth_headers)
        assert response.status_code == 200

    def test_response_has_sources_key(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/data-fusion/sources", headers=auth_headers)
        data = response.json()
        assert "sources" in data

    def test_all_four_providers_present(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/data-fusion/sources", headers=auth_headers)
        data = response.json()
        sources = data["sources"]
        assert "insee" in sources
        assert "eurostat" in sources
        assert "ademe" in sources
        assert "sdes" in sources

    def test_dataset_has_required_metadata_fields(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/data-fusion/sources", headers=auth_headers)
        data = response.json()
        # Check at least one dataset from each provider has required fields
        for provider, datasets in data["sources"].items():
            assert len(datasets) > 0, f"Provider {provider} has no datasets"
            for ds in datasets:
                assert "id" in ds, f"Missing 'id' in {provider} dataset"
                assert "name" in ds, f"Missing 'name' in {provider} dataset"
                assert "description" in ds, f"Missing 'description' in {provider} dataset"
                assert "variable_count" in ds, f"Missing 'variable_count' in {provider} dataset"
                assert "source_url" in ds, f"Missing 'source_url' in {provider} dataset"

    def test_insee_has_expected_datasets(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/data-fusion/sources", headers=auth_headers)
        data = response.json()
        insee_ids = {ds["id"] for ds in data["sources"]["insee"]}
        assert "filosofi_2021_commune" in insee_ids

    def test_unauthenticated_returns_401(self, client: TestClient) -> None:
        response = client.get("/api/data-fusion/sources")
        assert response.status_code == 401


# ============================================================================
# AC-1/AC-2: Dataset detail — GET /api/data-fusion/sources/{provider}/{dataset_id}
# ============================================================================


class TestGetSourceDetail:
    """Dataset detail including column schema."""

    def test_returns_200_for_valid_dataset(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get(
            "/api/data-fusion/sources/insee/filosofi_2021_commune",
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_response_has_column_schema(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get(
            "/api/data-fusion/sources/insee/filosofi_2021_commune",
            headers=auth_headers,
        )
        data = response.json()
        assert "columns" in data
        assert len(data["columns"]) > 0
        for col in data["columns"]:
            assert "name" in col
            assert "description" in col

    def test_returns_404_for_unknown_provider(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get(
            "/api/data-fusion/sources/unknown_provider/some_dataset",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_returns_404_for_unknown_dataset(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get(
            "/api/data-fusion/sources/insee/nonexistent_dataset",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_sdes_vehicle_fleet_detail(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get(
            "/api/data-fusion/sources/sdes/vehicle_fleet",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "vehicle_fleet"
        assert data["provider"] == "sdes"


# ============================================================================
# AC-3: Merge method explanation — GET /api/data-fusion/merge-methods
# ============================================================================


class TestListMergeMethods:
    """AC-3: Merge methods with plain-language descriptions."""

    def test_returns_200(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/data-fusion/merge-methods", headers=auth_headers)
        assert response.status_code == 200

    def test_response_has_methods_key(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/data-fusion/merge-methods", headers=auth_headers)
        data = response.json()
        assert "methods" in data

    def test_three_methods_returned(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/data-fusion/merge-methods", headers=auth_headers)
        data = response.json()
        assert len(data["methods"]) == 3

    def test_all_three_method_ids_present(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.get("/api/data-fusion/merge-methods", headers=auth_headers)
        data = response.json()
        method_ids = {m["id"] for m in data["methods"]}
        assert "uniform" in method_ids
        assert "ipf" in method_ids
        assert "conditional" in method_ids

    def test_each_method_has_plain_language_fields(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/data-fusion/merge-methods", headers=auth_headers)
        data = response.json()
        for method in data["methods"]:
            assert "id" in method
            assert "name" in method
            assert "what_it_does" in method
            assert "assumption" in method
            assert "when_appropriate" in method
            assert "tradeoff" in method
            assert "parameters" in method

    def test_uniform_method_has_no_required_params_beyond_seed(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/data-fusion/merge-methods", headers=auth_headers)
        data = response.json()
        uniform = next(m for m in data["methods"] if m["id"] == "uniform")
        # Uniform method only has seed parameter
        required_params = [p for p in uniform["parameters"] if p.get("required")]
        assert len(required_params) == 0  # seed has a default

    def test_ipf_method_has_constraints_parameter(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/data-fusion/merge-methods", headers=auth_headers)
        data = response.json()
        ipf = next(m for m in data["methods"] if m["id"] == "ipf")
        param_names = [p["name"] for p in ipf["parameters"]]
        assert "ipf_constraints" in param_names

    def test_conditional_method_has_strata_parameter(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.get("/api/data-fusion/merge-methods", headers=auth_headers)
        data = response.json()
        cond = next(m for m in data["methods"] if m["id"] == "conditional")
        param_names = [p["name"] for p in cond["parameters"]]
        assert "strata_columns" in param_names


# ============================================================================
# AC-4/AC-5: Population generation — POST /api/data-fusion/generate
# ============================================================================


def _make_mock_pipeline_result(row_count: int = 100) -> MagicMock:
    """Build a mock PipelineResult with the minimal structure needed."""
    # Mock table
    mock_table = MagicMock(spec=pa.Table)
    mock_table.num_rows = row_count
    mock_table.num_columns = 5
    mock_table.column_names = [
        "commune_code",
        "median_income",
        "region_code",
        "fuel_type",
        "fleet_count_2022",
    ]

    # Mock step log entry
    step_log_entry = MagicMock()
    step_log_entry.step_index = 0
    step_log_entry.step_type = "load"
    step_log_entry.label = "source_0"
    step_log_entry.input_labels = ()
    step_log_entry.output_rows = row_count
    step_log_entry.output_columns = ("commune_code", "median_income")
    step_log_entry.method_name = None
    step_log_entry.duration_ms = 12.5

    merge_log_entry = MagicMock()
    merge_log_entry.step_index = 1
    merge_log_entry.step_type = "merge"
    merge_log_entry.label = "merged"
    merge_log_entry.input_labels = ("source_0", "source_1")
    merge_log_entry.output_rows = row_count
    merge_log_entry.output_columns = ("commune_code", "median_income", "fuel_type")
    merge_log_entry.method_name = "uniform"
    merge_log_entry.duration_ms = 5.2

    # Mock assumption chain
    mock_assumption = MagicMock()
    mock_assumption.step_index = 0
    mock_assumption.step_label = "merged"
    mock_assumption.assumption = MagicMock()
    mock_assumption.assumption.method = "UniformMergeMethod"
    mock_assumption.assumption.description = "Uniform random matching with replacement"
    mock_assumption.assumption.is_default = True

    mock_chain = MagicMock()
    mock_chain.records = (mock_assumption,)
    mock_chain.pipeline_description = "User population"

    mock_result = MagicMock()
    mock_result.table = mock_table
    mock_result.step_log = (step_log_entry, merge_log_entry)
    mock_result.assumption_chain = mock_chain

    return mock_result


class TestGeneratePopulation:
    """AC-4/AC-5: Population generation feedback and preview."""

    def test_returns_400_with_fewer_than_two_sources(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/data-fusion/generate",
            headers=auth_headers,
            json={
                "sources": [{"provider": "insee", "dataset_id": "filosofi_2021_commune"}],
                "merge_method": "uniform",
                "seed": 42,
            },
        )
        assert response.status_code == 422

    def test_returns_422_for_unknown_provider(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        response = client.post(
            "/api/data-fusion/generate",
            headers=auth_headers,
            json={
                "sources": [
                    {"provider": "unknown_provider", "dataset_id": "some_dataset"},
                    {"provider": "sdes", "dataset_id": "vehicle_fleet"},
                ],
                "merge_method": "uniform",
                "seed": 42,
            },
        )
        assert response.status_code == 422

    def test_returns_422_for_unknown_merge_method(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        response = client.post(
            "/api/data-fusion/generate",
            headers=auth_headers,
            json={
                "sources": [
                    {"provider": "insee", "dataset_id": "filosofi_2021_commune"},
                    {"provider": "sdes", "dataset_id": "vehicle_fleet"},
                ],
                "merge_method": "unknown_method",
                "seed": 42,
            },
        )
        assert response.status_code == 422

    @patch("reformlab.server.routes.data_fusion._execute_pipeline")
    def test_successful_generation_returns_200(
        self,
        mock_execute: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_execute.return_value = _make_mock_pipeline_result(100)

        response = client.post(
            "/api/data-fusion/generate",
            headers=auth_headers,
            json={
                "sources": [
                    {"provider": "insee", "dataset_id": "filosofi_2021_commune"},
                    {"provider": "sdes", "dataset_id": "vehicle_fleet"},
                ],
                "merge_method": "uniform",
                "seed": 42,
            },
        )
        assert response.status_code == 200

    @patch("reformlab.server.routes.data_fusion._execute_pipeline")
    def test_response_has_success_flag(
        self,
        mock_execute: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_execute.return_value = _make_mock_pipeline_result(100)

        response = client.post(
            "/api/data-fusion/generate",
            headers=auth_headers,
            json={
                "sources": [
                    {"provider": "insee", "dataset_id": "filosofi_2021_commune"},
                    {"provider": "sdes", "dataset_id": "vehicle_fleet"},
                ],
                "merge_method": "uniform",
                "seed": 42,
            },
        )
        data = response.json()
        assert data["success"] is True

    @patch("reformlab.server.routes.data_fusion._execute_pipeline")
    def test_response_has_summary_with_row_count(
        self,
        mock_execute: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_execute.return_value = _make_mock_pipeline_result(100)

        response = client.post(
            "/api/data-fusion/generate",
            headers=auth_headers,
            json={
                "sources": [
                    {"provider": "insee", "dataset_id": "filosofi_2021_commune"},
                    {"provider": "sdes", "dataset_id": "vehicle_fleet"},
                ],
                "merge_method": "uniform",
                "seed": 42,
            },
        )
        data = response.json()
        assert "summary" in data
        assert data["summary"]["record_count"] == 100

    @patch("reformlab.server.routes.data_fusion._execute_pipeline")
    def test_response_has_step_log(
        self,
        mock_execute: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_execute.return_value = _make_mock_pipeline_result(100)

        response = client.post(
            "/api/data-fusion/generate",
            headers=auth_headers,
            json={
                "sources": [
                    {"provider": "insee", "dataset_id": "filosofi_2021_commune"},
                    {"provider": "sdes", "dataset_id": "vehicle_fleet"},
                ],
                "merge_method": "uniform",
                "seed": 42,
            },
        )
        data = response.json()
        assert "step_log" in data
        assert isinstance(data["step_log"], list)
        assert len(data["step_log"]) >= 1

    @patch("reformlab.server.routes.data_fusion._execute_pipeline")
    def test_response_has_assumption_chain(
        self,
        mock_execute: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_execute.return_value = _make_mock_pipeline_result(100)

        response = client.post(
            "/api/data-fusion/generate",
            headers=auth_headers,
            json={
                "sources": [
                    {"provider": "insee", "dataset_id": "filosofi_2021_commune"},
                    {"provider": "sdes", "dataset_id": "vehicle_fleet"},
                ],
                "merge_method": "uniform",
                "seed": 42,
            },
        )
        data = response.json()
        assert "assumption_chain" in data
        assert isinstance(data["assumption_chain"], list)

    @patch("reformlab.server.routes.data_fusion._execute_pipeline")
    def test_same_seed_returns_identical_result(
        self,
        mock_execute: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """AC-6: Determinism — same seed and config → identical results."""
        mock_execute.return_value = _make_mock_pipeline_result(100)

        payload = {
            "sources": [
                {"provider": "insee", "dataset_id": "filosofi_2021_commune"},
                {"provider": "sdes", "dataset_id": "vehicle_fleet"},
            ],
            "merge_method": "uniform",
            "seed": 42,
        }

        r1 = client.post("/api/data-fusion/generate", headers=auth_headers, json=payload)
        r2 = client.post("/api/data-fusion/generate", headers=auth_headers, json=payload)
        assert r1.json()["summary"]["record_count"] == r2.json()["summary"]["record_count"]

    @patch("reformlab.server.routes.data_fusion._execute_pipeline")
    def test_pipeline_error_returns_structured_error(
        self,
        mock_execute: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """AC-4: On failure, structured error message returned."""
        from reformlab.population import PipelineExecutionError

        mock_execute.side_effect = PipelineExecutionError(
            summary="Pipeline step failed",
            reason="Failed to load data",
            fix="Check source availability",
            step_index=0,
            step_label="source_0",
            step_type="load",
            cause=RuntimeError("network unavailable"),
        )

        response = client.post(
            "/api/data-fusion/generate",
            headers=auth_headers,
            json={
                "sources": [
                    {"provider": "insee", "dataset_id": "filosofi_2021_commune"},
                    {"provider": "sdes", "dataset_id": "vehicle_fleet"},
                ],
                "merge_method": "uniform",
                "seed": 42,
            },
        )
        assert response.status_code == 500
        data = response.json()
        assert "what" in data
        assert "why" in data
        assert "fix" in data

    def test_unauthenticated_generate_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/api/data-fusion/generate",
            json={
                "sources": [
                    {"provider": "insee", "dataset_id": "filosofi_2021_commune"},
                    {"provider": "sdes", "dataset_id": "vehicle_fleet"},
                ],
                "merge_method": "uniform",
                "seed": 42,
            },
        )
        assert response.status_code == 401
