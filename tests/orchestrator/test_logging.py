"""Tests for structured logging and execution trace metadata (Story 3-6).

This module tests:
- AC-1: Year seed is logged at year start with deterministic markers
- AC-2: Step execution order is logged exactly as executed
- AC-3: Adapter version is logged by ComputationStep
- AC-4: Year completion summary is logged only on successful year completion
- AC-5: Seed differences are observable across runs
- AC-6: Minimal structured trace is exposed in OrchestratorResult.metadata
"""

from __future__ import annotations

import logging

from reformlab.orchestrator import (
    Orchestrator,
    OrchestratorConfig,
    YearState,
)
from reformlab.orchestrator.runner import (
    SEED_LOG_KEY,
    STEP_EXECUTION_LOG_KEY,
)
from tests.orchestrator.conftest import (
    add_year_marker,
    increment_population,
)

# ============================================================================
# Test: AC-1 Year seed is logged at year start with deterministic markers
# ============================================================================


class TestYearStartLogging:
    """Tests for AC-1: year-start logging with stable markers."""

    def test_year_start_emits_info_log_with_markers(self, caplog):
        """Year-start INFO log includes year, seed, master_seed, event markers."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=42,
            step_pipeline=(),
        )

        with caplog.at_level(logging.INFO, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        # Find year_start log entry
        year_start_logs = [
            r for r in caplog.records if "event=year_start" in r.message
        ]
        assert len(year_start_logs) == 1

        log = year_start_logs[0]
        assert "year=2025" in log.message
        assert "seed=" in log.message
        assert "master_seed=42" in log.message
        assert "event=year_start" in log.message

    def test_year_start_logs_none_seed_when_no_master_seed(self, caplog):
        """Year-start log shows seed=None when no master seed configured."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=None,
            step_pipeline=(),
        )

        with caplog.at_level(logging.INFO, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        year_start_logs = [
            r for r in caplog.records if "event=year_start" in r.message
        ]
        assert len(year_start_logs) == 1
        assert "seed=None" in year_start_logs[0].message
        assert "master_seed=None" in year_start_logs[0].message

    def test_year_start_logs_one_entry_per_year(self, caplog):
        """Each year gets exactly one year_start log entry."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={},
            seed=42,
            step_pipeline=(),
        )

        with caplog.at_level(logging.INFO, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        year_start_logs = [
            r for r in caplog.records if "event=year_start" in r.message
        ]
        assert len(year_start_logs) == 3
        assert "year=2025" in year_start_logs[0].message
        assert "year=2026" in year_start_logs[1].message
        assert "year=2027" in year_start_logs[2].message


# ============================================================================
# Test: AC-2 Step execution order is logged exactly as executed
# ============================================================================


class TestStepExecutionLogging:
    """Tests for AC-2: step execution order logging."""

    def test_step_logs_include_step_index_and_total(self, caplog):
        """Step logs include step_index and step_total markers."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={"population": 1000},
            seed=42,
            step_pipeline=(increment_population, add_year_marker),
        )

        with caplog.at_level(logging.DEBUG, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        # Find step_start logs
        step_start_logs = [
            r for r in caplog.records if "event=step_start" in r.message
        ]
        assert len(step_start_logs) == 2

        # First step
        assert "step_index=1" in step_start_logs[0].message
        assert "step_total=2" in step_start_logs[0].message
        assert "step_name=increment_population" in step_start_logs[0].message

        # Second step
        assert "step_index=2" in step_start_logs[1].message
        assert "step_total=2" in step_start_logs[1].message
        assert "step_name=add_year_marker" in step_start_logs[1].message

    def test_step_logs_emit_start_and_end_events(self, caplog):
        """Step execution emits both step_start and step_end events."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={"population": 1000},
            seed=42,
            step_pipeline=(increment_population,),
        )

        with caplog.at_level(logging.DEBUG, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        step_start_logs = [
            r for r in caplog.records if "event=step_start" in r.message
        ]
        step_end_logs = [
            r for r in caplog.records if "event=step_end" in r.message
        ]

        assert len(step_start_logs) == 1
        assert len(step_end_logs) == 1

        # Both should reference the same step
        assert "step_name=increment_population" in step_start_logs[0].message
        assert "step_name=increment_population" in step_end_logs[0].message

    def test_step_logs_are_at_debug_level(self, caplog):
        """Step start/end logs are at DEBUG level."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=None,
            step_pipeline=(increment_population,),
        )

        with caplog.at_level(logging.DEBUG, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        step_logs = [
            r
            for r in caplog.records
            if "event=step_start" in r.message or "event=step_end" in r.message
        ]

        for log in step_logs:
            assert log.levelno == logging.DEBUG

    def test_empty_pipeline_emits_no_step_logs(self, caplog):
        """Empty pipeline produces no step_start or step_end logs."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=None,
            step_pipeline=(),
        )

        with caplog.at_level(logging.DEBUG, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        step_logs = [
            r
            for r in caplog.records
            if "event=step_start" in r.message or "event=step_end" in r.message
        ]
        assert len(step_logs) == 0


# ============================================================================
# Test: AC-4 Year completion summary is logged only on successful year completion
# ============================================================================


class TestYearCompleteLogging:
    """Tests for AC-4: year completion summary logging."""

    def test_year_complete_emits_info_log_with_markers(self, caplog):
        """Year-complete INFO log includes year, steps, seed, adapter_version."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={"population": 1000},
            seed=42,
            step_pipeline=(increment_population, add_year_marker),
        )

        with caplog.at_level(logging.INFO, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        year_complete_logs = [
            r for r in caplog.records if "event=year_complete" in r.message
        ]
        assert len(year_complete_logs) == 1

        log = year_complete_logs[0]
        assert "year=2025" in log.message
        assert "steps_executed=2" in log.message
        assert "seed=" in log.message
        assert "adapter_version=" in log.message  # n/a for non-computation steps
        assert "event=year_complete" in log.message

    def test_year_complete_shows_n_a_adapter_version_when_no_computation_step(
        self, caplog
    ):
        """Year-complete shows adapter_version=n/a when no computation step."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={"population": 1000},
            seed=42,
            step_pipeline=(increment_population,),
        )

        with caplog.at_level(logging.INFO, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        year_complete_logs = [
            r for r in caplog.records if "event=year_complete" in r.message
        ]
        assert "adapter_version=n/a" in year_complete_logs[0].message

    def test_empty_pipeline_shows_steps_executed_zero(self, caplog):
        """Empty pipeline shows steps_executed=0 in year_complete log."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=None,
            step_pipeline=(),
        )

        with caplog.at_level(logging.INFO, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        year_complete_logs = [
            r for r in caplog.records if "event=year_complete" in r.message
        ]
        assert len(year_complete_logs) == 1
        assert "steps_executed=0" in year_complete_logs[0].message


# ============================================================================
# Test: AC-5 Seed differences are observable across runs
# ============================================================================


class TestSeedDifferenceObservability:
    """Tests for AC-5: seed differences visible in logs."""

    def test_different_master_seeds_produce_different_year_seeds_in_logs(self, caplog):
        """Runs with different master seeds show different seed values in logs."""
        config_seed_42 = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=42,
            step_pipeline=(),
        )
        config_seed_100 = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=100,
            step_pipeline=(),
        )

        # Run with seed 42
        with caplog.at_level(logging.INFO, logger="reformlab.orchestrator.runner"):
            orchestrator1 = Orchestrator(config_seed_42)
            orchestrator1.run()

        year_start_logs_seed42 = [
            r for r in caplog.records if "event=year_start" in r.message
        ]

        caplog.clear()

        # Run with seed 100
        with caplog.at_level(logging.INFO, logger="reformlab.orchestrator.runner"):
            orchestrator2 = Orchestrator(config_seed_100)
            orchestrator2.run()

        year_start_logs_seed100 = [
            r for r in caplog.records if "event=year_start" in r.message
        ]

        # Master seeds should differ
        assert "master_seed=42" in year_start_logs_seed42[0].message
        assert "master_seed=100" in year_start_logs_seed100[0].message

        # Year seeds should also differ (derived from master seed)
        # Extract seed value from first run
        import re

        seed_pattern = r"seed=(\d+|None)"
        match1 = re.search(seed_pattern, year_start_logs_seed42[0].message)
        match2 = re.search(seed_pattern, year_start_logs_seed100[0].message)

        assert match1 is not None and match2 is not None
        assert match1.group(1) != match2.group(1)

    def test_searchable_markers_present_in_year_logs(self, caplog):
        """Required searchable markers (year=, seed=, step_name=) are present."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={"population": 1000},
            seed=42,
            step_pipeline=(increment_population,),
        )

        with caplog.at_level(logging.DEBUG, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        all_messages = " ".join(r.message for r in caplog.records)

        # Verify all required searchable markers appear
        assert "year=" in all_messages
        assert "seed=" in all_messages
        assert "step_name=" in all_messages


# ============================================================================
# Test: AC-6 Minimal structured trace is exposed in OrchestratorResult.metadata
# ============================================================================


class TestExecutionTraceMetadata:
    """Tests for AC-6: execution trace in OrchestratorResult.metadata."""

    def test_seed_log_contains_year_to_seed_mapping(self):
        """seed_log maps each executed year to its derived seed."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={},
            seed=42,
            step_pipeline=(),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert SEED_LOG_KEY in result.metadata
        seed_log = result.metadata[SEED_LOG_KEY]

        assert isinstance(seed_log, dict)
        assert 2025 in seed_log
        assert 2026 in seed_log
        assert 2027 in seed_log

        # All seeds should be integers (derived from master seed)
        assert all(isinstance(v, int) for v in seed_log.values())

    def test_seed_log_contains_none_when_no_master_seed(self):
        """seed_log maps years to None when no master seed configured."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={},
            seed=None,
            step_pipeline=(),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        seed_log = result.metadata[SEED_LOG_KEY]
        assert all(v is None for v in seed_log.values())

    def test_step_execution_log_contains_ordered_records(self):
        """step_execution_log contains ordered records for each step execution."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2026,
            initial_state={"population": 1000},
            seed=42,
            step_pipeline=(increment_population, add_year_marker),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert STEP_EXECUTION_LOG_KEY in result.metadata
        step_log = result.metadata[STEP_EXECUTION_LOG_KEY]

        assert isinstance(step_log, list)
        # 2 steps × 2 years = 4 records
        assert len(step_log) == 4

        # Check structure of first record
        first_record = step_log[0]
        assert "year" in first_record
        assert "step_index" in first_record
        assert "step_total" in first_record
        assert "step_name" in first_record
        assert "status" in first_record

        # Verify ordering (year 2025 first, then 2026)
        assert step_log[0]["year"] == 2025
        assert step_log[0]["step_index"] == 1
        assert step_log[1]["year"] == 2025
        assert step_log[1]["step_index"] == 2
        assert step_log[2]["year"] == 2026
        assert step_log[2]["step_index"] == 1

    def test_step_execution_log_records_status_completed(self):
        """Successful step executions record status='completed'."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=None,
            step_pipeline=(increment_population,),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        step_log = result.metadata[STEP_EXECUTION_LOG_KEY]
        assert all(record["status"] == "completed" for record in step_log)

    def test_step_execution_log_empty_for_empty_pipeline(self):
        """step_execution_log is empty when pipeline is empty."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={},
            seed=None,
            step_pipeline=(),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        step_log = result.metadata[STEP_EXECUTION_LOG_KEY]
        assert step_log == []

    def test_trace_metadata_included_on_failure_path(self):
        """Trace metadata is included even when orchestrator fails."""

        def fail_at_2026(year: int, state: YearState) -> YearState:
            if year == 2026:
                raise ValueError("Failing at 2026")
            return state

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={},
            seed=42,
            step_pipeline=(fail_at_2026,),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is False
        assert SEED_LOG_KEY in result.metadata
        assert STEP_EXECUTION_LOG_KEY in result.metadata

        # Only 2025 completed before failure
        seed_log = result.metadata[SEED_LOG_KEY]
        assert 2025 in seed_log
        assert 2026 not in seed_log  # Failed year not in seed_log

        # Only 2025's step should be in the log
        step_log = result.metadata[STEP_EXECUTION_LOG_KEY]
        assert len(step_log) == 1
        assert step_log[0]["year"] == 2025

    def test_seed_log_and_step_log_keys_are_stable(self):
        """The metadata keys for seed_log and step_execution_log are stable strings."""
        # These constants should be stable and not change
        assert SEED_LOG_KEY == "seed_log"
        assert STEP_EXECUTION_LOG_KEY == "step_execution_log"


# ============================================================================
# Test: Marker format consistency
# ============================================================================


class TestMarkerFormatConsistency:
    """Tests for consistent key=value marker format."""

    def test_all_markers_use_key_value_format(self, caplog):
        """All markers use consistent key=value format without spaces around =."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={"population": 1000},
            seed=42,
            step_pipeline=(increment_population, add_year_marker),
        )

        with caplog.at_level(logging.DEBUG, logger="reformlab.orchestrator.runner"):
            orchestrator = Orchestrator(config)
            orchestrator.run()

        # Check all logged messages with markers
        marker_logs = [
            r
            for r in caplog.records
            if any(
                m in r.message
                for m in ["year=", "seed=", "step_name=", "event=", "step_index="]
            )
        ]

        for log in marker_logs:
            # Verify no spaces around = in markers
            assert " = " not in log.message
            # Verify markers are followed by values (not just "key=")
            if "year=" in log.message:
                assert "year=20" in log.message  # Year starts with 20xx
            if "event=" in log.message:
                assert (
                    "event=year_start" in log.message
                    or "event=year_complete" in log.message
                    or "event=step_start" in log.message
                    or "event=step_end" in log.message
                )
