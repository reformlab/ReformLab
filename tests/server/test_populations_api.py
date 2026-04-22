# SPDX-License-Identifier: ACSEL-1.0
# Copyright 2026 Lucas Vivier
"""Tests for population explorer API endpoints — Story 20.7.

AC-1: Population API Endpoints Exist and Match Frontend Contracts
AC-2: Validation/Preflight Endpoint Returns Pass/Fail with Check-Level Detail
AC-3: All New Endpoints Return Typed Responses Matching Frontend Model Contracts
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pytest
from fastapi.testclient import TestClient

# =============================================================================
# Test fixtures
# =============================================================================


@pytest.fixture()
def populations_dir(tmp_path: Path) -> Path:
    """Create a temporary populations directory with test data."""
    data_dir = tmp_path / "data" / "populations"
    data_dir.mkdir(parents=True)

    # Create a test CSV population
    test_csv = data_dir / "test-population.csv"
    test_csv.write_text(
        "household_id,person_id,income,age,decile\n"
        "1,1,50000,45,5\n"
        "1,2,30000,40,4\n"
        "2,1,60000,50,6\n"
    )

    return data_dir


@pytest.fixture()
def uploaded_dir(tmp_path: Path) -> Path:
    """Create a temporary uploaded populations directory."""
    uploaded = tmp_path / ".reformlab" / "uploaded-populations"
    uploaded.mkdir(parents=True)
    return uploaded


@pytest.fixture()
def sample_csv_population(tmp_path: Path) -> Path:
    """Create a sample CSV population file for testing."""
    pop_file = tmp_path / "sample.csv"
    pop_file.write_text(
        "household_id,person_id,income,age,decile\n"
        "1,1,50000,45,5\n"
        "1,2,30000,40,4\n"
        "2,1,60000,50,6\n"
        "3,1,45000,35,3\n"
    )
    return pop_file


@pytest.fixture()
def sample_parquet_population(tmp_path: Path) -> Path:
    """Create a sample Parquet population file for testing."""
    pop_file = tmp_path / "sample.parquet"
    table = pa.table({
        "household_id": [1, 1, 2, 3],
        "person_id": [1, 2, 1, 1],
        "income": [50000, 30000, 60000, 45000],
        "age": [45, 40, 50, 35],
        "decile": [5, 4, 6, 3],
    })
    pa.parquet.write_table(table, pop_file)
    return pop_file


# =============================================================================
# Task 20.7.1: GET /api/populations with PopulationLibraryItem
# =============================================================================


class TestPopulationListEndpoint:
    """Tests for GET /api/populations returning PopulationLibraryItem with origin tags."""

    def test_list_populations_returns_library_items_with_origin(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #1: GET /api/populations returns PopulationLibraryItem[] with origin field."""
        # Point to test populations directory
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        response = client.get("/api/populations", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "populations" in data
        populations = data["populations"]

        # Should have at least the test-population
        assert len(populations) >= 1

        # Check PopulationLibraryItem fields
        pop = next((p for p in populations if p["id"] == "test-population"), None)
        assert pop is not None
        assert "origin" in pop
        assert pop["origin"] in ["built-in", "generated", "uploaded"]
        assert "column_count" in pop
        assert isinstance(pop["column_count"], int)
        assert "created_date" in pop

    def test_list_populations_includes_uploaded_origin(
        self,
        populations_dir: Path,
        uploaded_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #1: Uploaded populations have origin='uploaded' and metadata from sidecar."""
        # Set env vars before creating client
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))
        monkeypatch.setenv("REFORMLAB_UPLOADED_POPULATIONS_DIR", str(uploaded_dir))

        # Create client AFTER setting env vars
        from fastapi.testclient import TestClient

        from reformlab.server.app import create_app

        app = create_app()
        client = TestClient(app)

        # Authenticate
        response = client.post("/api/auth/login", json={"password": "test-password-123"})
        assert response.status_code == 200
        token = response.json()["token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Create an uploaded population with sidecar
        pop_id = "uploaded-test-12345"
        data_file = uploaded_dir / f"{pop_id}.csv"
        data_file.write_text("household_id,income\n1,50000\n")

        meta_file = uploaded_dir / f"{pop_id}.meta.json"
        meta_file.write_text(json.dumps({
            "id": pop_id,
            "origin": "uploaded",
            "created_date": "2026-03-27T12:00:00Z",
            "original_filename": "my-population.csv",
            "file_path": str(data_file),
        }))

        response = client.get("/api/populations", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        populations = data["populations"]

        uploaded_pop = next((p for p in populations if p["id"] == pop_id), None)
        assert uploaded_pop is not None
        assert uploaded_pop["origin"] == "uploaded"
        assert uploaded_pop["created_date"] == "2026-03-27T12:00:00Z"

    def test_list_populations_detects_generated_origin(
        self,
        populations_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #1: Generated populations have origin='generated' detected from manifest."""
        # Set env vars before creating client
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        # Create client AFTER setting env vars
        from fastapi.testclient import TestClient

        from reformlab.server.app import create_app

        app = create_app()
        client = TestClient(app)

        # Authenticate
        response = client.post("/api/auth/login", json={"password": "test-password-123"})
        assert response.status_code == 200
        token = response.json()["token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Create a generated population with manifest
        data_file = populations_dir / "generated-pop.csv"
        data_file.write_text("household_id,income\n1,50000\n")

        manifest_file = populations_dir / "generated-pop.manifest.json"
        manifest_file.write_text(json.dumps({
            "generated_at": "2026-03-27T12:00:00Z",
        }))

        response = client.get("/api/populations", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        populations = data["populations"]

        gen_pop = next((p for p in populations if p["id"] == "generated-pop"), None)
        assert gen_pop is not None
        assert gen_pop["origin"] == "generated"
        assert gen_pop["created_date"] == "2026-03-27T12:00:00Z"


# =============================================================================
# Task 20.7.2: GET /api/populations/{id}/preview
# =============================================================================


class TestPopulationPreviewEndpoint:
    """Tests for GET /api/populations/{id}/preview endpoint."""

    def test_preview_returns_first_100_rows_by_default(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Preview endpoint returns rows, columns, total_rows matching frontend contract."""
        # Create test population
        test_file = populations_dir / "preview-test.csv"
        test_file.write_text(
            "household_id,person_id,income,age\n"
            "1,1,50000,45\n"
            "1,2,30000,40\n"
            "2,1,60000,50\n"
        )

        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        response = client.get("/api/populations/preview-test/preview", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        # Check PopulationPreviewResponse fields
        assert data["id"] == "preview-test"
        assert "name" in data
        assert "rows" in data
        assert "columns" in data
        assert "total_rows" in data
        assert data["total_rows"] == 3
        assert len(data["rows"]) == 3

        # Check column info
        columns = data["columns"]
        assert len(columns) == 4
        col_names = [c["name"] for c in columns]
        assert "household_id" in col_names
        assert "income" in col_names

    def test_preview_respects_limit_offset(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Preview respects offset and limit query parameters."""
        # Create test population with 10 rows
        rows = ["household_id,income\n"]
        for i in range(10):
            rows.append(f"{i+1},{50000 + i * 1000}\n")
        test_file = populations_dir / "paginate-test.csv"
        test_file.write_text("".join(rows))

        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        # Get second page
        response = client.get(
            "/api/populations/paginate-test/preview?offset=3&limit=2",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["rows"]) == 2
        assert data["total_rows"] == 10
        assert data["rows"][0]["household_id"] == 4

    def test_preview_returns_404_for_missing_population(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Preview returns 404 ErrorResponse for non-existent population."""
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        response = client.get("/api/populations/nonexistent/preview", headers=auth_headers)
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "what" in data["detail"]
        assert "Population 'nonexistent' not found" in data["detail"]["what"]


# =============================================================================
# Task 20.7.3: GET /api/populations/{id}/profile
# =============================================================================


class TestPopulationProfileEndpoint:
    """Tests for GET /api/populations/{id}/profile endpoint."""

    def test_profile_returns_per_column_statistics(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Profile endpoint returns numeric/categorical/boolean profiles."""
        # Create test population with mixed column types
        test_file = populations_dir / "profile-test.csv"
        test_file.write_text(
            "household_id,income,age,has_children,region\n"
            "1,50000,45,true,North\n"
            "2,60000,50,false,South\n"
            "3,45000,35,true,North\n"
            "4,70000,55,false,East\n"
            "5,,30,true,North\n"
        )

        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        response = client.get("/api/populations/profile-test/profile", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "profile-test"
        assert "columns" in data

        columns = {c["name"]: c["profile"] for c in data["columns"]}

        # Numeric column profile
        income_profile = columns["income"]
        assert income_profile["type"] == "numeric"
        assert "count" in income_profile
        assert "mean" in income_profile
        assert "min" in income_profile
        assert "max" in income_profile
        assert "nulls" in income_profile
        assert income_profile["nulls"] == 1
        assert "histogram_buckets" in income_profile

        # Boolean column profile
        has_children_profile = columns["has_children"]
        assert has_children_profile["type"] == "boolean"
        assert "true_count" in has_children_profile
        assert "false_count" in has_children_profile

        # Categorical column profile
        region_profile = columns["region"]
        assert region_profile["type"] == "categorical"
        assert "cardinality" in region_profile
        assert "value_counts" in region_profile

    def test_profile_returns_404_for_missing_population(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Profile returns 404 ErrorResponse for non-existent population."""
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        response = client.get("/api/populations/nonexistent/profile", headers=auth_headers)
        assert response.status_code == 404


# =============================================================================
# Task 20.7.4: GET /api/populations/{id}/crosstab
# =============================================================================


class TestPopulationCrosstabEndpoint:
    """Tests for GET /api/populations/{id}/crosstab endpoint."""

    def test_crosstab_returns_cross_tabulated_data(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Crosstab endpoint returns cross-tabulated data with col_a, col_b, count."""
        # Create test population
        test_file = populations_dir / "crosstab-test.csv"
        test_file.write_text(
            "household_id,region,decile\n"
            "1,North,5\n"
            "2,North,3\n"
            "3,South,5\n"
            "4,South,3\n"
            "5,North,5\n"
        )

        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        response = client.get(
            "/api/populations/crosstab-test/crosstab?col_a=region&col_b=decile",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["col_a"] == "region"
        assert data["col_b"] == "decile"
        assert "data" in data
        assert "truncated" in data

        # Should have 4 combinations (North-5, North-3, South-5, South-3)
        assert len(data["data"]) == 4

    def test_crosstab_returns_400_for_invalid_column(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Crosstab returns 400 ErrorResponse for non-existent column."""
        test_file = populations_dir / "crosstab-test.csv"
        test_file.write_text("household_id,income\n1,50000\n")

        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        response = client.get(
            "/api/populations/crosstab-test/crosstab?col_a=nonexistent&col_b=income",
            headers=auth_headers,
        )
        assert response.status_code == 400

        data = response.json()
        assert "detail" in data
        assert "what" in data["detail"]
        assert "Column" in data["detail"]["what"]
        assert "not found" in data["detail"]["what"]


# =============================================================================
# Task 20.7.5: POST /api/populations/upload
# =============================================================================


class TestPopulationUploadEndpoint:
    """Tests for POST /api/populations/upload endpoint."""

    def test_upload_csv_creates_population_with_sidecar(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        uploaded_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Upload endpoint creates population file and metadata sidecar."""
        monkeypatch.setenv("REFORMLAB_UPLOADED_POPULATIONS_DIR", str(uploaded_dir))

        csv_content = "household_id,person_id,income\n1,1,50000\n1,2,30000\n"
        files = {"file": ("test-pop.csv", csv_content, "text/csv")}

        response = client.post(
            "/api/populations/upload",
            headers=auth_headers,
            files=files,
        )
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert data["id"].startswith("uploaded-")
        assert data["valid"] is True
        assert "row_count" in data
        assert "column_count" in data
        assert "matched_columns" in data

        # Check files were created
        population_id = data["id"]
        data_file = uploaded_dir / f"{population_id}.csv"
        meta_file = uploaded_dir / f"{population_id}.meta.json"
        assert data_file.exists()
        assert meta_file.exists()

        # Check metadata
        meta = json.loads(meta_file.read_text())
        assert meta["origin"] == "uploaded"
        assert meta["id"] == population_id

    def test_upload_rejects_non_csv_parquet_files(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        uploaded_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Upload endpoint rejects non-CSV/Parquet files."""
        monkeypatch.setenv("REFORMLAB_UPLOADED_POPULATIONS_DIR", str(uploaded_dir))

        files = {"file": ("test.txt", "not a csv", "text/plain")}

        response = client.post(
            "/api/populations/upload",
            headers=auth_headers,
            files=files,
        )
        assert response.status_code == 400


# =============================================================================
# Task 20.7.6: DELETE /api/populations/{id}
# =============================================================================


class TestPopulationDeleteEndpoint:
    """Tests for DELETE /api/populations/{id} endpoint."""

    def test_delete_allows_removing_uploaded_population(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        uploaded_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1: DELETE endpoint removes uploaded population files and returns 204."""
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))
        monkeypatch.setenv("REFORMLAB_UPLOADED_POPULATIONS_DIR", str(uploaded_dir))

        # Create uploaded population
        pop_id = "uploaded-test-123"
        data_file = uploaded_dir / f"{pop_id}.csv"
        data_file.write_text("household_id,income\n1,50000\n")

        meta_file = uploaded_dir / f"{pop_id}.meta.json"
        meta_file.write_text(json.dumps({
            "id": pop_id,
            "origin": "uploaded",
            "created_date": "2026-03-27T12:00:00Z",
        }))

        response = client.delete(f"/api/populations/{pop_id}", headers=auth_headers)
        assert response.status_code == 204
        assert not data_file.exists()
        assert not meta_file.exists()

    def test_delete_rejects_removing_builtin_population(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1: DELETE endpoint returns 403 for built-in populations."""
        # Create a built-in population (in data/populations/)
        test_file = populations_dir / "builtin-test.csv"
        test_file.write_text("household_id,income\n1,50000\n")

        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        response = client.delete("/api/populations/builtin-test", headers=auth_headers)
        assert response.status_code == 403

        data = response.json()
        assert "detail" in data
        assert "what" in data["detail"]
        assert "Cannot delete built-in population" in data["detail"]["what"]

    def test_delete_returns_404_for_nonexistent_population(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1: DELETE endpoint returns 404 for non-existent population."""
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        response = client.delete("/api/populations/nonexistent", headers=auth_headers)
        assert response.status_code == 404


# =============================================================================
# Task 20.7.7: POST /api/validation/preflight
# =============================================================================


class TestPreflightValidationEndpoint:
    """Tests for POST /api/validation/preflight endpoint."""

    def test_preflight_returns_check_results(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """AC-2: Preflight endpoint returns passed, checks[], and warnings[]."""
        request_body = {
            "scenario": {
                "name": "Test Scenario",
                "portfolioName": "test-portfolio",
                "populationIds": ["test-pop"],
                "engineConfig": {
                    "startYear": 2025,
                    "endYear": 2030,
                    "seed": 42,
                },
            },
        }

        response = client.post(
            "/api/validation/preflight",
            headers=auth_headers,
            json=request_body,
        )
        assert response.status_code == 200

        data = response.json()
        assert "passed" in data
        assert "checks" in data
        assert "warnings" in data
        assert isinstance(data["checks"], list)

    def test_preflight_includes_all_builtin_checks(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """AC-2: Preflight runs all built-in checks (portfolio, population, time-horizon, memory)."""
        request_body = {
            "scenario": {
                "portfolioName": "test-portfolio",
                "populationIds": ["test-pop"],
                "engineConfig": {
                    "startYear": 2025,
                    "endYear": 2030,
                },
            },
        }

        response = client.post(
            "/api/validation/preflight",
            headers=auth_headers,
            json=request_body,
        )
        assert response.status_code == 200

        data = response.json()
        check_ids = [c["id"] for c in data["checks"]]

        # Verify built-in checks are present
        assert "portfolio-selected" in check_ids
        assert "population-selected" in check_ids
        assert "time-horizon-valid" in check_ids
        assert "memory-preflight" in check_ids

    def test_preflight_fails_for_invalid_scenario(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """AC-2: Preflight returns passed=false for scenario with validation errors."""
        request_body = {
            "scenario": {
                "portfolioName": "",  # Empty portfolio
                "populationIds": [],  # Empty population
                "engineConfig": {
                    "startYear": 2030,
                    "endYear": 2025,  # Invalid: end before start
                },
            },
        }

        response = client.post(
            "/api/validation/preflight",
            headers=auth_headers,
            json=request_body,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["passed"] is False

        # Should have failing checks
        error_checks = [c for c in data["checks"] if c["severity"] == "error" and not c["passed"]]
        assert len(error_checks) > 0


# =============================================================================
# Task 20.7.9: Parquet file support
# =============================================================================


class TestParquetFileSupport:
    """Tests for Parquet file handling in population endpoints."""

    def test_preview_works_with_parquet_file(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        sample_parquet_population: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Preview endpoint works with Parquet files."""
        # Copy parquet file to populations directory
        target_file = populations_dir / "parquet-test.parquet"
        target_file.write_bytes(sample_parquet_population.read_bytes())

        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        response = client.get("/api/populations/parquet-test/preview", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "parquet-test"
        assert data["total_rows"] == 4
        assert len(data["columns"]) == 5

    def test_profile_works_with_parquet_file(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        populations_dir: Path,
        sample_parquet_population: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Profile endpoint works with Parquet files."""
        target_file = populations_dir / "parquet-test.parquet"
        target_file.write_bytes(sample_parquet_population.read_bytes())

        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(populations_dir.parent))

        response = client.get("/api/populations/parquet-test/profile", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "parquet-test"
        assert len(data["columns"]) == 5

    def test_upload_accepts_parquet_file(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        uploaded_dir: Path,
        sample_parquet_population: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1, #3: Upload endpoint accepts Parquet files."""
        monkeypatch.setenv("REFORMLAB_UPLOADED_POPULATIONS_DIR", str(uploaded_dir))

        files = {
            "file": (
                "test-pop.parquet",
                sample_parquet_population.read_bytes(),
                "application/octet-stream",
            )
        }

        response = client.post(
            "/api/populations/upload",
            headers=auth_headers,
            files=files,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["valid"] is True


# =============================================================================
# Story 26.5: Quick Test Population
# =============================================================================


class TestQuickTestPopulation:
    """Tests for Quick Test Population — Story 26.5."""

    def test_list_populations_includes_quick_test_population(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-1: GET /api/populations includes Quick Test Population with correct metadata — Story 26.5."""
        # Use the real data directory which includes quick-test-population
        from pathlib import Path

        repo_root = Path(__file__).parent.parent.parent
        data_dir = repo_root / "data" / "populations"
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(data_dir.parent))

        # Recreate client to pick up new data directory
        from reformlab.server.app import create_app
        app = create_app()
        client = TestClient(app)

        # Authenticate
        response = client.post("/api/auth/login", json={"password": "test-password-123"})
        assert response.status_code == 200
        token = response.json()["token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/populations", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "populations" in data
        populations = data["populations"]

        # Find Quick Test Population
        quick_test = next((p for p in populations if p["id"] == "quick-test-population"), None)
        assert quick_test is not None, "Quick Test Population should be in the list"
        assert quick_test["name"] == "Quick Test Population"
        assert quick_test["households"] == 100
        assert quick_test["trust_status"] == "demo-only"
        assert quick_test["origin"] == "built-in"  # Folder-based populations
        assert quick_test["canonical_origin"] == "synthetic-public"
        assert quick_test["access_mode"] == "bundled"

    def test_quick_test_population_preview_works(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-5: Quick Test Population preview endpoint works — Story 26.5."""
        from pathlib import Path
        repo_root = Path(__file__).parent.parent.parent
        data_dir = repo_root / "data" / "populations"
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(data_dir.parent))

        # Recreate client to pick up new data directory
        from reformlab.server.app import create_app
        app = create_app()
        client = TestClient(app)

        # Authenticate
        response = client.post("/api/auth/login", json={"password": "test-password-123"})
        assert response.status_code == 200
        token = response.json()["token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/populations/quick-test-population/preview", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "quick-test-population"
        assert data["total_rows"] == 100
        assert len(data["columns"]) == 7  # household_id, person_id, age, income, energy_*

    def test_quick_test_population_profile_works(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """AC-5: Quick Test Population profile endpoint works — Story 26.5."""
        from pathlib import Path
        repo_root = Path(__file__).parent.parent.parent
        data_dir = repo_root / "data" / "populations"
        monkeypatch.setenv("REFORMLAB_DATA_DIR", str(data_dir.parent))

        # Recreate client to pick up new data directory
        from reformlab.server.app import create_app
        app = create_app()
        client = TestClient(app)

        # Authenticate
        response = client.post("/api/auth/login", json={"password": "test-password-123"})
        assert response.status_code == 200
        token = response.json()["token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/populations/quick-test-population/profile", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "quick-test-population"
        assert len(data["columns"]) == 7
