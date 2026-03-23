# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for the yearly loop orchestrator runner."""

from __future__ import annotations

from dataclasses import replace

import pytest

from reformlab.orchestrator import (
    Orchestrator,
    OrchestratorConfig,
    OrchestratorError,
    OrchestratorResult,
    YearState,
)
from tests.orchestrator.conftest import (
    add_year_marker,
    failing_step,
    increment_population,
)

# ============================================================================
# Test: Basic orchestrator execution (AC-1)
# ============================================================================


class TestOrchestratorBasicExecution:
    """Tests for basic orchestrator execution (AC-1)."""

    def test_execute_10_year_loop(self, simple_config: OrchestratorConfig):
        """10-year loop completes successfully (AC-1)."""
        orchestrator = Orchestrator(simple_config)
        result = orchestrator.run()

        assert result.success is True
        assert len(result.yearly_states) == 10
        assert 2025 in result.yearly_states
        assert 2034 in result.yearly_states

    def test_years_execute_in_strict_order(self, simple_config: OrchestratorConfig):
        """Years execute in strict order (AC-1)."""
        orchestrator = Orchestrator(simple_config)
        result = orchestrator.run()

        years = sorted(result.yearly_states.keys())
        expected_years = list(range(2025, 2035))
        assert years == expected_years

    def test_each_year_receives_previous_year_state(
        self, config_with_steps: OrchestratorConfig
    ):
        """Each year receives output state from previous year (AC-1)."""
        orchestrator = Orchestrator(config_with_steps)
        result = orchestrator.run()

        # Population should increase by 100 each year
        assert result.yearly_states[2025].data["population"] == 1100
        assert result.yearly_states[2026].data["population"] == 1200
        assert result.yearly_states[2027].data["population"] == 1300
        assert result.yearly_states[2028].data["population"] == 1400
        assert result.yearly_states[2029].data["population"] == 1500

    def test_step_pipeline_executes_for_each_year(
        self, config_with_steps: OrchestratorConfig
    ):
        """Step pipeline executes for each year (AC-1)."""
        orchestrator = Orchestrator(config_with_steps)
        result = orchestrator.run()

        # Each year should have its marker in metadata
        for year in range(2025, 2030):
            state = result.yearly_states[year]
            assert f"marker_{year}" in state.metadata
            assert state.metadata[f"marker_{year}"] is True


# ============================================================================
# Test: Empty step pipeline (AC-2)
# ============================================================================


class TestEmptyPipeline:
    """Tests for empty step pipeline handling (AC-2)."""

    def test_empty_pipeline_completes_without_error(
        self, empty_pipeline_config: OrchestratorConfig
    ):
        """Empty pipeline completes without error (AC-2)."""
        orchestrator = Orchestrator(empty_pipeline_config)
        result = orchestrator.run()

        assert result.success is True
        assert result.errors == []

    def test_empty_pipeline_logs_years(
        self, empty_pipeline_config: OrchestratorConfig, caplog
    ):
        """Empty pipeline logs each year iteration (AC-2)."""
        import logging

        with caplog.at_level(logging.DEBUG):
            orchestrator = Orchestrator(empty_pipeline_config)
            result = orchestrator.run()

        assert result.success is True
        messages = [record.message.lower() for record in caplog.records]
        for year in range(
            empty_pipeline_config.start_year,
            empty_pipeline_config.end_year + 1,
        ):
            assert any(f"year {year}" in message for message in messages)

    def test_empty_pipeline_preserves_state(
        self, empty_pipeline_config: OrchestratorConfig
    ):
        """Empty pipeline preserves initial state through years."""
        config = replace(
            empty_pipeline_config,
            initial_state={"test_value": 42},
        )
        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        # All years should have the initial value preserved
        for year, state in result.yearly_states.items():
            assert state.data.get("test_value") == 42


# ============================================================================
# Test: Step failure handling (AC-3)
# ============================================================================


class TestStepFailureHandling:
    """Tests for step failure handling (AC-3)."""

    def test_step_failure_halts_execution(
        self, config_with_failing_step: OrchestratorConfig
    ):
        """Step failure halts execution immediately (AC-3)."""
        orchestrator = Orchestrator(config_with_failing_step)
        result = orchestrator.run()

        assert result.success is False
        assert result.failed_year == 2028

    def test_step_failure_includes_step_name(
        self, config_with_failing_step: OrchestratorConfig
    ):
        """Step failure includes step name (AC-3)."""
        orchestrator = Orchestrator(config_with_failing_step)
        result = orchestrator.run()

        assert result.failed_step == "fail_at_year_2028"

    def test_step_failure_preserves_partial_results(
        self, config_with_failing_step: OrchestratorConfig
    ):
        """Step failure preserves partial results (AC-3)."""
        orchestrator = Orchestrator(config_with_failing_step)
        result = orchestrator.run()

        # Years before failure should be captured
        assert 2025 in result.yearly_states
        assert 2026 in result.yearly_states
        assert 2027 in result.yearly_states
        # Year of failure and after should not be in results
        assert 2028 not in result.yearly_states
        assert 2029 not in result.yearly_states

    def test_step_failure_error_includes_context(
        self, config_with_failing_step: OrchestratorConfig
    ):
        """Step failure error includes context (AC-3)."""
        orchestrator = Orchestrator(config_with_failing_step)
        result = orchestrator.run()

        assert len(result.errors) >= 1
        error_msg = result.errors[0]
        assert "2028" in error_msg or "fail_at_year_2028" in error_msg
        assert "completed years: [2025, 2026, 2027]" in error_msg

    def test_step_failure_with_immediate_fail(self):
        """Step that fails immediately captures correct context."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2030,
            initial_state={},
            seed=None,
            step_pipeline=(failing_step,),
        )
        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is False
        assert result.failed_year == 2025
        assert result.failed_step == "failing_step"
        assert len(result.yearly_states) == 0

    def test_step_return_type_violation_surfaces_as_orchestrator_error(self):
        """A step returning non-YearState fails with clear context."""

        def bad_return_step(year: int, state: YearState) -> YearState:
            return {"year": year}  # type: ignore[return-value]

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=None,
            step_pipeline=(bad_return_step,),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is False
        assert result.failed_year == 2025
        assert result.failed_step == "bad_return_step"
        assert "expected YearState" in result.errors[0]


# ============================================================================
# Test: Deterministic execution (AC-4)
# ============================================================================


class TestDeterministicExecution:
    """Tests for deterministic execution (AC-4)."""

    def test_identical_inputs_produce_identical_outputs(
        self, config_with_steps: OrchestratorConfig
    ):
        """Identical inputs produce identical outputs (AC-4)."""
        orchestrator1 = Orchestrator(config_with_steps)
        result1 = orchestrator1.run()

        orchestrator2 = Orchestrator(config_with_steps)
        result2 = orchestrator2.run()

        # Results should be identical
        assert result1.success == result2.success
        assert len(result1.yearly_states) == len(result2.yearly_states)

        for year in result1.yearly_states:
            state1 = result1.yearly_states[year]
            state2 = result2.yearly_states[year]
            assert state1.year == state2.year
            assert state1.data == state2.data
            assert state1.seed == state2.seed

    def test_seed_propagation_is_deterministic(self, simple_config: OrchestratorConfig):
        """Seed propagation produces deterministic year seeds (AC-4)."""
        orchestrator = Orchestrator(simple_config)
        result = orchestrator.run()

        # Each year should have a unique but deterministic seed
        seeds = [
            result.yearly_states[year].seed for year in sorted(result.yearly_states)
        ]
        assert all(seed is not None for seed in seeds)
        # Seeds should all be different (derived from master seed XOR year)
        assert len(set(seeds)) == len(seeds)

    def test_no_seed_produces_none_year_seeds(
        self, empty_pipeline_config: OrchestratorConfig
    ):
        """No master seed produces None year seeds."""
        orchestrator = Orchestrator(empty_pipeline_config)
        result = orchestrator.run()

        for year, state in result.yearly_states.items():
            assert state.seed is None

    def test_seed_derivation_is_reproducible(self, simple_config: OrchestratorConfig):
        """Same master seed produces same year seeds on multiple runs."""
        orchestrator1 = Orchestrator(simple_config)
        result1 = orchestrator1.run()

        orchestrator2 = Orchestrator(simple_config)
        result2 = orchestrator2.run()

        for year in result1.yearly_states:
            assert result1.yearly_states[year].seed == result2.yearly_states[year].seed


# ============================================================================
# Test: State carry-forward
# ============================================================================


class TestStateCarryForward:
    """Tests for state carry-forward between years."""

    def test_initial_state_is_used(self, simple_config: OrchestratorConfig):
        """Initial state data is available to first year."""
        orchestrator = Orchestrator(simple_config)
        result = orchestrator.run()

        # First year should have access to initial state
        first_year = min(result.yearly_states.keys())
        assert result.yearly_states[first_year].data.get("population") is not None

    def test_state_modifications_carry_forward(self):
        """State modifications carry forward between years."""

        def append_to_history(year: int, state: YearState) -> YearState:
            new_data = dict(state.data)
            history = list(new_data.get("history", []))
            history.append(year)
            new_data["history"] = history
            return replace(state, data=new_data)

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={"history": []},
            seed=None,
            step_pipeline=(append_to_history,),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.yearly_states[2025].data["history"] == [2025]
        assert result.yearly_states[2026].data["history"] == [2025, 2026]
        assert result.yearly_states[2027].data["history"] == [2025, 2026, 2027]

    def test_metadata_from_previous_year_available(
        self, config_with_steps: OrchestratorConfig
    ):
        """Metadata includes reference to previous year."""
        orchestrator = Orchestrator(config_with_steps)
        result = orchestrator.run()

        # First year should reference year before start
        assert result.yearly_states[2025].metadata.get("previous_year") == 2024
        # Subsequent years should reference their predecessor
        assert result.yearly_states[2026].metadata.get("previous_year") == 2025


# ============================================================================
# Test: OrchestratorResult
# ============================================================================


class TestOrchestratorResult:
    """Tests for OrchestratorResult dataclass."""

    def test_successful_result_structure(self, config_with_steps: OrchestratorConfig):
        """Successful result has expected structure."""
        orchestrator = Orchestrator(config_with_steps)
        result = orchestrator.run()

        assert isinstance(result, OrchestratorResult)
        assert result.success is True
        assert isinstance(result.yearly_states, dict)
        assert result.errors == []
        assert result.failed_year is None
        assert result.failed_step is None
        assert isinstance(result.metadata, dict)

    def test_failed_result_structure(
        self, config_with_failing_step: OrchestratorConfig
    ):
        """Failed result has expected structure."""
        orchestrator = Orchestrator(config_with_failing_step)
        result = orchestrator.run()

        assert isinstance(result, OrchestratorResult)
        assert result.success is False
        assert isinstance(result.yearly_states, dict)
        assert len(result.errors) >= 1
        assert result.failed_year is not None
        assert result.failed_step is not None

    def test_result_metadata_contains_run_info(self, simple_config: OrchestratorConfig):
        """Result metadata contains run information."""
        orchestrator = Orchestrator(simple_config)
        result = orchestrator.run()

        assert "start_year" in result.metadata
        assert "end_year" in result.metadata
        assert "seed" in result.metadata
        assert result.metadata["start_year"] == 2025
        assert result.metadata["end_year"] == 2034
        assert result.metadata["seed"] == 42


# ============================================================================
# Test: YearState
# ============================================================================


class TestYearState:
    """Tests for YearState dataclass."""

    def test_year_state_is_frozen(self):
        """YearState is immutable (frozen dataclass)."""
        state = YearState(year=2025, data={"a": 1})

        with pytest.raises(Exception):  # FrozenInstanceError
            state.year = 2026  # type: ignore[misc]

    def test_year_state_defaults(self):
        """YearState has expected defaults."""
        state = YearState(year=2025)

        assert state.year == 2025
        assert state.data == {}
        assert state.seed is None
        assert state.metadata == {}

    def test_year_state_with_all_fields(self):
        """YearState can be created with all fields."""
        state = YearState(
            year=2025,
            data={"population": 1000},
            seed=42,
            metadata={"source": "test"},
        )

        assert state.year == 2025
        assert state.data == {"population": 1000}
        assert state.seed == 42
        assert state.metadata == {"source": "test"}


# ============================================================================
# Test: OrchestratorConfig
# ============================================================================


class TestOrchestratorConfig:
    """Tests for OrchestratorConfig dataclass."""

    def test_config_is_frozen(self):
        """OrchestratorConfig is immutable (frozen dataclass)."""
        config = OrchestratorConfig(start_year=2025, end_year=2030)

        with pytest.raises(Exception):  # FrozenInstanceError
            config.start_year = 2020  # type: ignore[misc]

    def test_config_defaults(self):
        """OrchestratorConfig has expected defaults."""
        config = OrchestratorConfig(start_year=2025, end_year=2030)

        assert config.start_year == 2025
        assert config.end_year == 2030
        assert config.initial_state == {}
        assert config.seed is None
        assert config.step_pipeline == ()

    def test_config_with_all_fields(self):
        """OrchestratorConfig can be created with all fields."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2030,
            initial_state={"test": 1},
            seed=42,
            step_pipeline=(increment_population,),
        )

        assert config.start_year == 2025
        assert config.end_year == 2030
        assert config.initial_state == {"test": 1}
        assert config.seed == 42
        assert len(config.step_pipeline) == 1

    def test_config_rejects_invalid_year_bounds(self):
        """OrchestratorConfig rejects end_year < start_year."""
        with pytest.raises(ValueError, match="end_year"):
            OrchestratorConfig(start_year=2030, end_year=2029)

    def test_config_rejects_non_callable_steps(self):
        """OrchestratorConfig rejects non-callable step entries."""
        with pytest.raises(TypeError, match="not callable"):
            OrchestratorConfig(
                start_year=2025,
                end_year=2025,
                step_pipeline=(42,),  # type: ignore[arg-type]
            )


# ============================================================================
# Test: OrchestratorError
# ============================================================================


class TestOrchestratorError:
    """Tests for OrchestratorError exception."""

    def test_error_message_format(self):
        """OrchestratorError formats message correctly."""
        error = OrchestratorError(
            summary="Step failed",
            reason="test error",
            year=2028,
            step_name="test_step",
        )

        message = str(error)
        assert "Step failed" in message
        assert "test error" in message
        assert "2028" in message
        assert "test_step" in message

    def test_error_to_dict(self):
        """OrchestratorError serializes to dict."""
        error = OrchestratorError(
            summary="Step failed",
            reason="test error",
            year=2028,
            step_name="test_step",
            partial_states={2025: YearState(year=2025)},
        )

        d = error.to_dict()
        assert d["summary"] == "Step failed"
        assert d["reason"] == "test error"
        assert d["year"] == 2028
        assert d["step_name"] == "test_step"
        assert d["completed_years"] == [2025]

    def test_error_with_original_exception(self):
        """OrchestratorError captures original exception."""
        original = ValueError("original error")
        error = OrchestratorError(
            summary="Wrapped",
            reason="test",
            original_error=original,
        )

        assert error.original_error is original


# ============================================================================
# Test: Protocol step execution (AC-1 Story 3-2)
# ============================================================================


class TestProtocolStepExecution:
    """Tests for OrchestratorStep protocol execution (Story 3-2 AC-1)."""

    def test_protocol_step_executes_in_pipeline(self):
        """A protocol step with name and execute runs in the orchestrator."""
        from dataclasses import dataclass

        @dataclass
        class CountingStep:
            name: str = "counting_step"

            def execute(self, year: int, state: YearState) -> YearState:
                new_data = dict(state.data)
                new_data["count"] = new_data.get("count", 0) + 1
                return replace(state, data=new_data)

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={"count": 0},
            seed=None,
            step_pipeline=(CountingStep(),),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is True
        assert result.yearly_states[2025].data["count"] == 1
        assert result.yearly_states[2026].data["count"] == 2
        assert result.yearly_states[2027].data["count"] == 3

    def test_protocol_step_name_in_error_context(self):
        """Protocol step failure includes step.name in error context."""
        from dataclasses import dataclass

        @dataclass
        class FailingProtocolStep:
            name: str = "my_failing_step"

            def execute(self, year: int, state: YearState) -> YearState:
                raise ValueError("Intentional failure")

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=None,
            step_pipeline=(FailingProtocolStep(),),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is False
        assert result.failed_step == "my_failing_step"

    def test_decorated_step_executes_in_pipeline(self):
        """Function decorated with @step runs in the orchestrator."""
        from reformlab.orchestrator.step import step

        @step(name="decorated_incrementer")
        def decorated_incrementer(year: int, state: YearState) -> YearState:
            new_data = dict(state.data)
            new_data["value"] = new_data.get("value", 0) + 10
            return replace(state, data=new_data)

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={"value": 100},
            seed=None,
            step_pipeline=(decorated_incrementer,),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is True
        assert result.yearly_states[2025].data["value"] == 110
        assert result.yearly_states[2026].data["value"] == 120
        assert result.yearly_states[2027].data["value"] == 130


# ============================================================================
# Test: Mixed pipeline compatibility (AC-5 Story 3-2)
# ============================================================================


class TestMixedPipelineCompatibility:
    """Tests for mixed pipelines with protocol steps and bare callables (Story 3-2 AC-5)."""

    def test_mixed_pipeline_executes_successfully(self):
        """Mixed pipeline with protocol steps and bare callables runs successfully."""
        from dataclasses import dataclass

        @dataclass
        class ProtocolStep:
            name: str = "protocol_add"

            def execute(self, year: int, state: YearState) -> YearState:
                new_data = dict(state.data)
                new_data["from_protocol"] = new_data.get("from_protocol", 0) + 1
                return replace(state, data=new_data)

        def bare_callable(year: int, state: YearState) -> YearState:
            new_data = dict(state.data)
            new_data["from_bare"] = new_data.get("from_bare", 0) + 1
            return replace(state, data=new_data)

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={},
            seed=None,
            step_pipeline=(ProtocolStep(), bare_callable),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is True
        # Both step types should have executed
        assert result.yearly_states[2027].data["from_protocol"] == 3
        assert result.yearly_states[2027].data["from_bare"] == 3

    def test_mixed_pipeline_with_decorated_step(self):
        """Mixed pipeline with decorated step and bare callable works."""
        from reformlab.orchestrator.step import step

        @step(name="decorated_step")
        def decorated_step(year: int, state: YearState) -> YearState:
            new_data = dict(state.data)
            new_data["from_decorated"] = True
            return replace(state, data=new_data)

        def bare_callable(year: int, state: YearState) -> YearState:
            new_data = dict(state.data)
            new_data["from_bare"] = True
            return replace(state, data=new_data)

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=None,
            step_pipeline=(decorated_step, bare_callable),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is True
        assert result.yearly_states[2025].data["from_decorated"] is True
        assert result.yearly_states[2025].data["from_bare"] is True

    def test_step_execution_order_preserved_in_mixed_pipeline(self):
        """Steps execute in order regardless of type (protocol or callable)."""
        from dataclasses import dataclass

        execution_order: list[str] = []

        @dataclass
        class FirstProtocolStep:
            name: str = "first_protocol"

            def execute(self, year: int, state: YearState) -> YearState:
                execution_order.append("first_protocol")
                return state

        def second_bare(year: int, state: YearState) -> YearState:
            execution_order.append("second_bare")
            return state

        @dataclass
        class ThirdProtocolStep:
            name: str = "third_protocol"

            def execute(self, year: int, state: YearState) -> YearState:
                execution_order.append("third_protocol")
                return state

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            initial_state={},
            seed=None,
            step_pipeline=(FirstProtocolStep(), second_bare, ThirdProtocolStep()),
        )

        execution_order.clear()
        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is True
        assert execution_order == ["first_protocol", "second_bare", "third_protocol"]

    def test_bare_callable_from_story_3_1_still_works(self):
        """Existing bare YearStep callables from Story 3-1 remain compatible."""
        # Use the existing test fixtures
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={"population": 1000},
            seed=None,
            step_pipeline=(increment_population, add_year_marker),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        # Verify existing behavior unchanged
        assert result.success is True
        assert result.yearly_states[2027].data["population"] == 1300
        assert "marker_2027" in result.yearly_states[2027].metadata
