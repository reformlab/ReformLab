# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for ResultStore — Story 17.3, AC-2, AC-3.

Verifies:
- save_metadata / get_metadata round-trip
- list_results sorted descending
- ResultNotFound raised for missing run_ids
- delete_result removes directory
- Corrupt entries skipped during list
- Failed-run metadata shape
"""

from __future__ import annotations

from pathlib import Path

import pytest

from reformlab.server.result_store import (
    ResultMetadata,
    ResultNotFound,
    ResultStore,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_metadata(
    run_id: str = "test-run-1",
    status: str = "completed",
    timestamp: str = "2026-03-07T22:00:00+00:00",
    row_count: int = 1000,
) -> ResultMetadata:
    return ResultMetadata(
        run_id=run_id,
        timestamp=timestamp,
        run_kind="scenario",
        start_year=2025,
        end_year=2030,
        population_id="fr-synthetic-2024",
        seed=42,
        row_count=row_count,
        manifest_id="manifest-abc",
        scenario_id="scenario-xyz",
        adapter_version="1.0.0",
        started_at="2026-03-07T22:00:00+00:00",
        finished_at="2026-03-07T22:00:05+00:00",
        status=status,
        template_name="Carbon Tax — Flat Rate",
        policy_type="carbon_tax",
        portfolio_name=None,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestResultStoreSaveAndGet:
    """save_metadata / get_metadata round-trip."""

    def test_save_and_get_roundtrip(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        meta = _make_metadata()
        store.save_metadata("test-run-1", meta)
        loaded = store.get_metadata("test-run-1")
        assert loaded.run_id == "test-run-1"
        assert loaded.status == "completed"
        assert loaded.row_count == 1000
        assert loaded.template_name == "Carbon Tax — Flat Rate"
        assert loaded.policy_type == "carbon_tax"
        assert loaded.portfolio_name is None

    def test_metadata_file_exists_after_save(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        meta = _make_metadata()
        store.save_metadata("my-run", meta)
        assert (tmp_path / "my-run" / "metadata.json").exists()

    def test_all_fields_preserved(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        meta = _make_metadata(run_id="abc", timestamp="2026-03-07T10:00:00Z")
        store.save_metadata("abc", meta)
        loaded = store.get_metadata("abc")
        assert loaded.start_year == 2025
        assert loaded.end_year == 2030
        assert loaded.population_id == "fr-synthetic-2024"
        assert loaded.seed == 42
        assert loaded.manifest_id == "manifest-abc"
        assert loaded.scenario_id == "scenario-xyz"
        assert loaded.adapter_version == "1.0.0"
        assert loaded.started_at == "2026-03-07T22:00:00+00:00"
        assert loaded.finished_at == "2026-03-07T22:00:05+00:00"

    def test_portfolio_run_metadata(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        meta = ResultMetadata(
            run_id="portfolio-run",
            timestamp="2026-03-07T20:00:00Z",
            run_kind="portfolio",
            start_year=2025,
            end_year=2035,
            population_id=None,
            seed=None,
            row_count=1100000,
            manifest_id="mf-001",
            scenario_id="sc-001",
            adapter_version="1.0.0",
            started_at="2026-03-07T20:00:00Z",
            finished_at="2026-03-07T20:01:00Z",
            status="completed",
            template_name=None,
            policy_type=None,
            portfolio_name="green-transition-2030",
        )
        store.save_metadata("portfolio-run", meta)
        loaded = store.get_metadata("portfolio-run")
        assert loaded.run_kind == "portfolio"
        assert loaded.portfolio_name == "green-transition-2030"
        assert loaded.template_name is None
        assert loaded.policy_type is None
        assert loaded.population_id is None
        assert loaded.seed is None


class TestResultStoreGetNotFound:
    """get_metadata raises ResultNotFound for missing runs."""

    def test_get_missing_run_raises(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        with pytest.raises(ResultNotFound):
            store.get_metadata("does-not-exist")

    def test_get_run_id_with_dir_but_no_file(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        (tmp_path / "orphan-run").mkdir()
        with pytest.raises(ResultNotFound):
            store.get_metadata("orphan-run")


class TestResultStoreList:
    """list_results returns entries sorted descending by timestamp."""

    def test_list_returns_all_entries(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("run-1", _make_metadata("run-1", timestamp="2026-03-07T10:00:00Z"))
        store.save_metadata("run-2", _make_metadata("run-2", timestamp="2026-03-07T11:00:00Z"))
        results = store.list_results()
        assert len(results) == 2

    def test_list_sorted_newest_first(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("run-old", _make_metadata("run-old", timestamp="2026-03-06T10:00:00Z"))
        store.save_metadata("run-new", _make_metadata("run-new", timestamp="2026-03-07T10:00:00Z"))
        results = store.list_results()
        assert results[0].run_id == "run-new"
        assert results[1].run_id == "run-old"

    def test_list_empty_store(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        assert store.list_results() == []

    def test_list_skips_corrupt_entry(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("good-run", _make_metadata("good-run"))

        # Create corrupt entry
        corrupt_dir = tmp_path / "corrupt-run"
        corrupt_dir.mkdir()
        (corrupt_dir / "metadata.json").write_text("not valid json", encoding="utf-8")

        results = store.list_results()
        # Corrupt entry is skipped; good entry is returned
        assert len(results) == 1
        assert results[0].run_id == "good-run"

    def test_list_skips_directory_without_metadata(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("real-run", _make_metadata("real-run"))
        (tmp_path / "empty-dir").mkdir()  # No metadata.json
        results = store.list_results()
        assert len(results) == 1

    def test_list_three_runs_sorted(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("a", _make_metadata("a", timestamp="2026-03-05T12:00:00Z"))
        store.save_metadata("b", _make_metadata("b", timestamp="2026-03-07T12:00:00Z"))
        store.save_metadata("c", _make_metadata("c", timestamp="2026-03-06T12:00:00Z"))
        results = store.list_results()
        assert [r.run_id for r in results] == ["b", "c", "a"]


class TestResultStoreDelete:
    """delete_result removes the run directory."""

    def test_delete_removes_run(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("run-to-delete", _make_metadata("run-to-delete"))
        assert (tmp_path / "run-to-delete").exists()
        store.delete_result("run-to-delete")
        assert not (tmp_path / "run-to-delete").exists()

    def test_delete_missing_run_raises(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        with pytest.raises(ResultNotFound):
            store.delete_result("does-not-exist")

    def test_deleted_run_not_in_list(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("keep", _make_metadata("keep"))
        store.save_metadata("delete-me", _make_metadata("delete-me"))
        store.delete_result("delete-me")
        results = store.list_results()
        assert len(results) == 1
        assert results[0].run_id == "keep"


class TestResultStoreFailedRun:
    """Failed-run metadata has correct shape (row_count=0, empty ids)."""

    def test_failed_run_fields(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        meta = ResultMetadata(
            run_id="failed-run",
            timestamp="2026-03-07T22:30:00Z",
            run_kind="scenario",
            start_year=2025,
            end_year=2030,
            population_id=None,
            seed=None,
            row_count=0,
            manifest_id="",
            scenario_id="",
            adapter_version="unknown",
            started_at="2026-03-07T22:30:00Z",
            finished_at="2026-03-07T22:30:01Z",
            status="failed",
            template_name="Carbon Tax — Flat Rate",
            policy_type="carbon_tax",
            portfolio_name=None,
        )
        store.save_metadata("failed-run", meta)
        loaded = store.get_metadata("failed-run")
        assert loaded.status == "failed"
        assert loaded.row_count == 0
        assert loaded.manifest_id == ""
        assert loaded.adapter_version == "unknown"

    def test_failed_run_appears_in_list(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata(
            "failed-run",
            _make_metadata("failed-run", status="failed", row_count=0),
        )
        results = store.list_results()
        assert len(results) == 1
        assert results[0].status == "failed"


class TestResultStoreAtomicWrite:
    """Verifies atomic write — tmp file is replaced atomically."""

    def test_no_tmp_file_after_save(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("atomic-run", _make_metadata("atomic-run"))
        tmp_path_file = tmp_path / "atomic-run" / ".metadata.json.tmp"
        assert not tmp_path_file.exists()

    def test_metadata_json_exists_after_save(self, tmp_path: Path) -> None:
        store = ResultStore(base_dir=tmp_path)
        store.save_metadata("atomic-run", _make_metadata("atomic-run"))
        assert (tmp_path / "atomic-run" / "metadata.json").exists()
