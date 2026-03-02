"""Tests for ComputationStep - adapter invocation within orchestrator pipeline.

Story 3-5: Integrate ComputationAdapter calls into orchestrator yearly loop.

Tests cover:
- AC-1: ComputationStep invokes adapter per year
- AC-2: Step satisfies orchestrator plugin contract
- AC-4: Adapter errors include year and version context
- AC-5: Determinism and logging requirements
"""

from __future__ import annotations

import logging
from dataclasses import replace

import pyarrow as pa
import pytest

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData
from reformlab.orchestrator.computation_step import (
    COMPUTATION_METADATA_KEY,
    COMPUTATION_RESULT_KEY,
    ComputationStep,
    ComputationStepError,
)
from reformlab.orchestrator.step import OrchestratorStep
from reformlab.orchestrator.types import YearState


@pytest.fixture
def sample_population() -> PopulationData:
    """Sample population data for testing."""
    table = pa.table(
        {
            "person_id": pa.array([1, 2, 3]),
            "salary": pa.array([30000.0, 45000.0, 60000.0]),
        }
    )
    return PopulationData(tables={"individu": table}, metadata={"source": "test"})


@pytest.fixture
def sample_policy() -> PolicyConfig:
    """Sample policy configuration for testing."""
    return PolicyConfig(
        policy={"carbon_tax_rate": 44.6},
        name="carbon-tax-baseline",
    )


@pytest.fixture
def mock_adapter() -> MockAdapter:
    """MockAdapter with test output."""
    output = pa.table({"tax": pa.array([100.0, 150.0, 200.0])})
    return MockAdapter(version_string="mock-2.0.0", default_output=output)


@pytest.fixture
def computation_step(
    mock_adapter: MockAdapter,
    sample_population: PopulationData,
    sample_policy: PolicyConfig,
) -> ComputationStep:
    """ComputationStep configured for testing."""
    return ComputationStep(
        adapter=mock_adapter,
        population=sample_population,
        policy=sample_policy,
    )


@pytest.fixture
def year_state() -> YearState:
    """Empty year state for testing."""
    return YearState(year=2025, data={}, seed=42, metadata={})


class TestComputationStepProtocol:
    """AC-2: Step satisfies orchestrator plugin contract."""

    def test_satisfies_orchestrator_step_protocol(
        self, computation_step: ComputationStep
    ) -> None:
        """Given ComputationStep, then it satisfies OrchestratorStep protocol."""
        assert isinstance(computation_step, OrchestratorStep)

    def test_name_property_returns_computation(
        self, computation_step: ComputationStep
    ) -> None:
        """Given ComputationStep, then name property returns 'computation'."""
        assert computation_step.name == "computation"

    def test_custom_name_property(
        self,
        mock_adapter: MockAdapter,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given ComputationStep with custom name, then name property returns it."""
        step = ComputationStep(
            adapter=mock_adapter,
            population=sample_population,
            policy=sample_policy,
            name="custom_computation",
        )
        assert step.name == "custom_computation"

    def test_depends_on_defaults_to_empty(
        self, computation_step: ComputationStep
    ) -> None:
        """Given ComputationStep without depends_on, then it defaults to empty tuple."""
        assert computation_step.depends_on == ()

    def test_custom_depends_on(
        self,
        mock_adapter: MockAdapter,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given ComputationStep with depends_on, returns configured value."""
        step = ComputationStep(
            adapter=mock_adapter,
            population=sample_population,
            policy=sample_policy,
            depends_on=("data_load",),
        )
        assert step.depends_on == ("data_load",)

    def test_execute_signature(
        self, computation_step: ComputationStep, year_state: YearState
    ) -> None:
        """Given ComputationStep, execute accepts year and state, returns YearState."""
        result = computation_step.execute(2025, year_state)
        assert isinstance(result, YearState)


class TestComputationStepExecution:
    """AC-1: ComputationStep invokes adapter per year."""

    def test_calls_adapter_compute_with_correct_parameters(
        self,
        computation_step: ComputationStep,
        mock_adapter: MockAdapter,
        year_state: YearState,
    ) -> None:
        """Given ComputationStep, adapter.compute() receives correct params."""
        computation_step.execute(2025, year_state)

        assert len(mock_adapter.call_log) == 1
        call = mock_adapter.call_log[0]
        assert call["period"] == 2025
        assert call["policy_name"] == "carbon-tax-baseline"
        assert call["population_row_count"] == 3

    def test_stores_result_in_year_state_data(
        self, computation_step: ComputationStep, year_state: YearState
    ) -> None:
        """Given ComputationStep execution, ComputationResult stored in state.data."""
        result = computation_step.execute(2025, year_state)

        assert COMPUTATION_RESULT_KEY in result.data
        comp_result = result.data[COMPUTATION_RESULT_KEY]
        assert isinstance(comp_result, ComputationResult)
        assert comp_result.period == 2025
        assert comp_result.adapter_version == "mock-2.0.0"

    def test_stores_metadata_in_year_state_metadata(
        self, computation_step: ComputationStep, year_state: YearState
    ) -> None:
        """Given ComputationStep execution, metadata stored in state.metadata."""
        result = computation_step.execute(2025, year_state)

        assert COMPUTATION_METADATA_KEY in result.metadata
        meta = result.metadata[COMPUTATION_METADATA_KEY]
        assert meta["adapter_version"] == "mock-2.0.0"
        assert meta["computation_period"] == 2025
        assert meta["computation_row_count"] == 3

    def test_returns_immutable_new_state(
        self, computation_step: ComputationStep, year_state: YearState
    ) -> None:
        """Given ComputationStep execution, then returns new immutable state."""
        result = computation_step.execute(2025, year_state)

        assert result is not year_state
        assert result.data is not year_state.data
        assert result.metadata is not year_state.metadata
        # Original state unchanged
        assert COMPUTATION_RESULT_KEY not in year_state.data

    def test_preserves_existing_state_data(
        self, computation_step: ComputationStep, year_state: YearState
    ) -> None:
        """Given state with existing data, then existing data preserved."""
        state_with_data = replace(year_state, data={"existing_key": "existing_value"})
        result = computation_step.execute(2025, state_with_data)

        assert result.data["existing_key"] == "existing_value"
        assert COMPUTATION_RESULT_KEY in result.data

    def test_preserves_existing_metadata(
        self, computation_step: ComputationStep, year_state: YearState
    ) -> None:
        """Given state with existing metadata, then metadata preserved."""
        state_with_meta = replace(year_state, metadata={"existing_meta": True})
        result = computation_step.execute(2025, state_with_meta)

        assert result.metadata["existing_meta"] is True
        assert COMPUTATION_METADATA_KEY in result.metadata


class TestComputationStepDeterminism:
    """AC-5: Determinism requirements."""

    def test_identical_inputs_produce_identical_outputs(
        self,
        mock_adapter: MockAdapter,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
        year_state: YearState,
    ) -> None:
        """Given identical inputs, when step runs twice, then outputs are identical."""
        step1 = ComputationStep(
            adapter=mock_adapter,
            population=sample_population,
            policy=sample_policy,
        )
        step2 = ComputationStep(
            adapter=mock_adapter,
            population=sample_population,
            policy=sample_policy,
        )

        # Reset call log between runs
        mock_adapter.call_log.clear()
        result1 = step1.execute(2025, year_state)
        mock_adapter.call_log.clear()
        result2 = step2.execute(2025, year_state)

        # Compare computation results
        comp1 = result1.data[COMPUTATION_RESULT_KEY]
        comp2 = result2.data[COMPUTATION_RESULT_KEY]
        assert comp1.period == comp2.period
        assert comp1.adapter_version == comp2.adapter_version
        assert comp1.output_fields.equals(comp2.output_fields)

        # Compare metadata
        meta1 = result1.metadata[COMPUTATION_METADATA_KEY]
        meta2 = result2.metadata[COMPUTATION_METADATA_KEY]
        assert meta1 == meta2

    def test_adapter_version_logged_in_metadata(
        self, computation_step: ComputationStep, year_state: YearState
    ) -> None:
        """Given ComputationStep, adapter version is logged in metadata."""
        result = computation_step.execute(2025, year_state)
        meta = result.metadata[COMPUTATION_METADATA_KEY]
        assert meta["adapter_version"] == "mock-2.0.0"


class TestComputationStepErrorHandling:
    """AC-4: Adapter errors include year and version context."""

    def test_adapter_failure_produces_computation_step_error(
        self,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
        year_state: YearState,
    ) -> None:
        """Given adapter that fails, then ComputationStepError is raised."""

        class FailingAdapter:
            def version(self) -> str:
                return "failing-1.0.0"

            def compute(
                self,
                population: PopulationData,
                policy: PolicyConfig,
                period: int,
            ) -> ComputationResult:
                raise RuntimeError("Computation failed")

        step = ComputationStep(
            adapter=FailingAdapter(),  # type: ignore[arg-type]
            population=sample_population,
            policy=sample_policy,
        )

        with pytest.raises(ComputationStepError) as exc_info:
            step.execute(2025, year_state)

        error = exc_info.value
        assert error.year == 2025
        assert error.adapter_version == "failing-1.0.0"
        assert "Computation failed" in str(error)

    def test_error_preserves_original_exception(
        self,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
        year_state: YearState,
    ) -> None:
        """Given adapter failure, then original error is preserved in chain."""

        class FailingAdapter:
            def version(self) -> str:
                return "failing-1.0.0"

            def compute(
                self,
                population: PopulationData,
                policy: PolicyConfig,
                period: int,
            ) -> ComputationResult:
                raise ValueError("Original error message")

        step = ComputationStep(
            adapter=FailingAdapter(),  # type: ignore[arg-type]
            population=sample_population,
            policy=sample_policy,
        )

        with pytest.raises(ComputationStepError) as exc_info:
            step.execute(2025, year_state)

        error = exc_info.value
        assert error.original_error is not None
        assert isinstance(error.original_error, ValueError)
        assert "Original error message" in str(error.original_error)

    def test_error_includes_adapter_version_and_year(
        self,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
        year_state: YearState,
    ) -> None:
        """Given adapter failure, then error message includes version and year."""

        class FailingAdapter:
            def version(self) -> str:
                return "failing-2.5.0"

            def compute(
                self,
                population: PopulationData,
                policy: PolicyConfig,
                period: int,
            ) -> ComputationResult:
                raise RuntimeError("Backend error")

        step = ComputationStep(
            adapter=FailingAdapter(),  # type: ignore[arg-type]
            population=sample_population,
            policy=sample_policy,
        )

        with pytest.raises(ComputationStepError) as exc_info:
            step.execute(2028, year_state)

        error_msg = str(exc_info.value)
        assert "2028" in error_msg
        assert "failing-2.5.0" in error_msg

    def test_version_lookup_failure_falls_back_to_version_unavailable(
        self,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
        year_state: YearState,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Given version lookup failure, computation still succeeds with fallback."""

        class VersionFailingAdapter:
            def version(self) -> str:
                raise RuntimeError("Version lookup failed")

            def compute(
                self,
                population: PopulationData,
                policy: PolicyConfig,
                period: int,
            ) -> ComputationResult:
                return ComputationResult(
                    output_fields=pa.table({"value": pa.array([1.0])}),
                    adapter_version="unused",
                    period=period,
                )

        step = ComputationStep(
            adapter=VersionFailingAdapter(),  # type: ignore[arg-type]
            population=sample_population,
            policy=sample_policy,
        )

        with caplog.at_level(
            logging.INFO, logger="reformlab.orchestrator.computation_step"
        ):
            result = step.execute(2026, year_state)

        meta = result.metadata[COMPUTATION_METADATA_KEY]
        assert meta["adapter_version"] == "<version-unavailable>"
        assert any(
            "adapter_version=<version-unavailable>" in record.message
            for record in caplog.records
        )

    def test_logs_adapter_version_at_info_level(
        self,
        computation_step: ComputationStep,
        year_state: YearState,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Given successful execution, INFO log includes adapter version marker."""
        with caplog.at_level(
            logging.INFO, logger="reformlab.orchestrator.computation_step"
        ):
            computation_step.execute(2025, year_state)

        version_logs = [r for r in caplog.records if "adapter_version=" in r.message]
        assert len(version_logs) >= 1
        assert "year=2025" in version_logs[0].message
        assert "step_name=computation" in version_logs[0].message
        assert "adapter_version=mock-2.0.0" in version_logs[0].message

    def test_invalid_computation_result_is_wrapped_with_adapter_context(
        self,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
        year_state: YearState,
    ) -> None:
        """Given malformed adapter result, failure is wrapped with adapter context."""

        class MalformedResultAdapter:
            def version(self) -> str:
                return "malformed-1.0.0"

            def compute(
                self,
                population: PopulationData,
                policy: PolicyConfig,
                period: int,
            ) -> ComputationResult:
                return ComputationResult(
                    output_fields="not-a-table",  # type: ignore[arg-type]
                    adapter_version=self.version(),
                    period=period,
                )

        step = ComputationStep(
            adapter=MalformedResultAdapter(),  # type: ignore[arg-type]
            population=sample_population,
            policy=sample_policy,
        )

        with pytest.raises(ComputationStepError) as exc_info:
            step.execute(2027, year_state)

        error = exc_info.value
        assert error.year == 2027
        assert error.adapter_version == "malformed-1.0.0"
        assert "AttributeError" in str(error)


class TestComputationStepKeys:
    """Test stable state key constants."""

    def test_computation_result_key_is_stable(self) -> None:
        """Given COMPUTATION_RESULT_KEY, then it has expected stable value."""
        assert COMPUTATION_RESULT_KEY == "computation_result"

    def test_computation_metadata_key_is_stable(self) -> None:
        """Given COMPUTATION_METADATA_KEY, then it has expected stable value."""
        assert COMPUTATION_METADATA_KEY == "computation_metadata"
