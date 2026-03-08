"""Unit tests for ResultStore panel and manifest persistence — Story 17.7.

Covers:
- save_panel() + load_panel() round-trip (Parquet content intact)
- save_manifest() + load_manifest() round-trip (JSON content intact)
- has_panel() returns True/False correctly
- load_from_disk() returns SimulationResult with correct panel data
- load_panel() raises ResultNotFound when file missing
- load_panel() raises ResultStoreError when file is corrupt
- load_from_disk() returns None when panel.parquet is corrupt
- Atomic write safety (.tmp file cleaned up)
"""

from __future__ import annotations

from pathlib import Path

import pyarrow as pa
import pytest

from reformlab.orchestrator.panel import PanelOutput
from reformlab.server.result_store import (
    ResultMetadata,
    ResultNotFound,
    ResultStore,
    ResultStoreError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_panel(seed: int = 0) -> PanelOutput:
    """Minimal PanelOutput for persistence tests."""
    n = 50
    incomes = [10000.0 + i * 500.0 + seed * 100.0 for i in range(n)]
    table = pa.table(
        {
            "household_id": pa.array(list(range(n)), type=pa.int64()),
            "year": pa.array([2025] * n, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "tax_burden": pa.array([inc * 0.1 for inc in incomes], type=pa.float64()),
        }
    )
    return PanelOutput(
        table=table,
        metadata={
            "start_year": 2025,
            "end_year": 2025,
            "seed": seed,
            "partial": False,
        },
    )


def _make_metadata(run_id: str = "test-run") -> ResultMetadata:
    return ResultMetadata(
        run_id=run_id,
        timestamp="2026-03-08T00:00:00+00:00",
        run_kind="scenario",
        start_year=2025,
        end_year=2025,
        population_id=None,
        seed=42,
        row_count=50,
        manifest_id="manifest-persist-test",
        scenario_id="sc-persist",
        adapter_version="1.0.0",
        started_at="2026-03-08T00:00:00+00:00",
        finished_at="2026-03-08T00:00:03+00:00",
        status="completed",
        template_name="carbon_tax",
        portfolio_name=None,
        policy_type="carbon_tax",
    )


def _make_manifest_json() -> str:
    """Return a valid canonical RunManifest JSON string."""
    from reformlab.governance.manifest import RunManifest

    manifest = RunManifest(
        manifest_id="manifest-persist-test",
        created_at="2026-03-08T00:00:00+00:00",
        engine_version="0.1.0",
        openfisca_version="44.0.0",
        adapter_version="1.0.0",
        scenario_version="1.0.0",
    )
    return manifest.to_json()


# ---------------------------------------------------------------------------
# save_panel + load_panel round-trip
# ---------------------------------------------------------------------------


class TestSavePanelLoadPanel:
    """save_panel() + load_panel() round-trip."""

    def test_round_trip_row_count(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        panel = _make_panel()
        store.save_panel("r1", panel)
        loaded = store.load_panel("r1")
        assert loaded.table.num_rows == panel.table.num_rows

    def test_round_trip_column_names(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        panel = _make_panel()
        store.save_panel("r1", panel)
        loaded = store.load_panel("r1")
        assert set(loaded.table.column_names) == set(panel.table.column_names)

    def test_round_trip_data_values(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        panel = _make_panel(seed=7)
        store.save_panel("r1", panel)
        loaded = store.load_panel("r1")
        orig_incomes = panel.table.column("income").to_pylist()
        loaded_incomes = loaded.table.column("income").to_pylist()
        assert orig_incomes == loaded_incomes

    def test_round_trip_panel_metadata(self, tmp_path: Path) -> None:
        """PanelOutput.metadata survives Parquet round-trip via schema metadata."""
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        panel = _make_panel(seed=3)
        store.save_panel("r1", panel)
        loaded = store.load_panel("r1")
        assert loaded.metadata.get("start_year") == 2025
        assert loaded.metadata.get("seed") == 3
        assert loaded.metadata.get("partial") is False

    def test_parquet_file_written_to_disk(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r2", _make_metadata("r2"))
        store.save_panel("r2", _make_panel())
        assert (tmp_path / "r2" / "panel.parquet").exists()


# ---------------------------------------------------------------------------
# save_manifest + load_manifest round-trip
# ---------------------------------------------------------------------------


class TestSaveManifestLoadManifest:
    """save_manifest() + load_manifest() round-trip."""

    def test_round_trip_manifest_id(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        manifest_json = _make_manifest_json()
        store.save_manifest("r1", manifest_json)
        loaded = store.load_manifest("r1")
        assert loaded.manifest_id == "manifest-persist-test"

    def test_round_trip_adapter_version(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_manifest("r1", _make_manifest_json())
        loaded = store.load_manifest("r1")
        assert loaded.adapter_version == "1.0.0"

    def test_manifest_file_written_to_disk(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_manifest("r1", _make_manifest_json())
        assert (tmp_path / "r1" / "manifest.json").exists()


# ---------------------------------------------------------------------------
# has_panel
# ---------------------------------------------------------------------------


class TestHasPanel:
    """has_panel() returns True/False correctly."""

    def test_returns_false_before_save(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        assert not store.has_panel("r1")

    def test_returns_true_after_save(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_panel("r1", _make_panel())
        assert store.has_panel("r1")

    def test_returns_false_for_unknown_run(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        assert not store.has_panel("does-not-exist")


# ---------------------------------------------------------------------------
# load_panel errors
# ---------------------------------------------------------------------------


class TestLoadPanelErrors:
    """load_panel() raises correct exceptions on missing/corrupt files."""

    def test_raises_result_not_found_when_missing(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        with pytest.raises(ResultNotFound):
            store.load_panel("r1")

    def test_raises_result_store_error_when_corrupt(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        # Write invalid bytes into panel.parquet
        panel_path = tmp_path / "r1" / "panel.parquet"
        panel_path.write_bytes(b"not a valid parquet file")
        with pytest.raises(ResultStoreError):
            store.load_panel("r1")


# ---------------------------------------------------------------------------
# load_from_disk
# ---------------------------------------------------------------------------


class TestLoadFromDisk:
    """load_from_disk() returns SimulationResult or None."""

    def test_returns_sim_result_with_panel(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_panel("r1", _make_panel())
        store.save_manifest("r1", _make_manifest_json())
        result = store.load_from_disk("r1")
        assert result is not None
        assert result.panel_output is not None

    def test_returns_none_when_no_panel(self, tmp_path: Path) -> None:
        """No panel.parquet → None (e.g., failed run)."""
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        result = store.load_from_disk("r1")
        assert result is None

    def test_returns_none_when_panel_corrupt(self, tmp_path: Path) -> None:
        """Corrupt panel.parquet → None (does not propagate exception)."""
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        (tmp_path / "r1" / "panel.parquet").write_bytes(b"garbage bytes")
        result = store.load_from_disk("r1")
        assert result is None

    def test_panel_data_intact_in_result(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        panel = _make_panel(seed=5)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_panel("r1", panel)
        result = store.load_from_disk("r1")
        assert result is not None
        assert result.panel_output is not None
        assert result.panel_output.table.num_rows == panel.table.num_rows

    def test_panel_metadata_intact_in_result(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        panel = _make_panel(seed=9)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_panel("r1", panel)
        result = store.load_from_disk("r1")
        assert result is not None
        assert result.panel_output is not None
        assert result.panel_output.metadata.get("seed") == 9

    def test_success_flag_true(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_panel("r1", _make_panel())
        result = store.load_from_disk("r1")
        assert result is not None
        assert result.success is True

    def test_yearly_states_empty(self, tmp_path: Path) -> None:
        """yearly_states is {} for disk-loaded results (not persisted)."""
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_panel("r1", _make_panel())
        result = store.load_from_disk("r1")
        assert result is not None
        assert result.yearly_states == {}

    def test_manifest_loaded_when_present(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_panel("r1", _make_panel())
        store.save_manifest("r1", _make_manifest_json())
        result = store.load_from_disk("r1")
        assert result is not None
        assert result.manifest.manifest_id == "manifest-persist-test"

    def test_falls_back_to_minimal_manifest_when_missing(self, tmp_path: Path) -> None:
        """Missing manifest.json → minimal manifest fallback, no crash."""
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_panel("r1", _make_panel())
        # No manifest saved
        result = store.load_from_disk("r1")
        assert result is not None
        assert result.manifest is not None  # minimal manifest used


# ---------------------------------------------------------------------------
# Atomic write safety
# ---------------------------------------------------------------------------


class TestAtomicWriteSafety:
    """Verify .tmp files are not left behind after successful writes."""

    def test_no_tmp_file_after_panel_save(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_panel("r1", _make_panel())
        assert not (tmp_path / "r1" / ".panel.parquet.tmp").exists()
        assert (tmp_path / "r1" / "panel.parquet").exists()

    def test_no_tmp_file_after_manifest_save(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("r1", _make_metadata("r1"))
        store.save_manifest("r1", _make_manifest_json())
        assert not (tmp_path / "r1" / ".manifest.json.tmp").exists()
        assert (tmp_path / "r1" / "manifest.json").exists()
