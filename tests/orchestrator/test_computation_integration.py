# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Integration tests for ComputationStep within orchestrator pipeline.

Story 3-5: Integrate ComputationAdapter calls into orchestrator yearly loop.

Tests cover:
- AC-3: Mock adapter enables full pipeline testing
- AC-4: Partial results preserved on adapter failure
- Full pipeline with MockAdapter + VintageTransitionStep + CarryForwardStep
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import ComputationResult, PolicyConfig, PopulationData
from reformlab.orchestrator.carry_forward import (
    CarryForwardConfig,
    CarryForwardRule,
    CarryForwardStep,
)
from reformlab.orchestrator.computation_step import (
    COMPUTATION_METADATA_KEY,
    COMPUTATION_RESULT_KEY,
    ComputationStep,
)
from reformlab.orchestrator.runner import Orchestrator
from reformlab.orchestrator.step import StepRegistry
from reformlab.orchestrator.types import OrchestratorConfig
from reformlab.vintage.config import VintageConfig, VintageTransitionRule
from reformlab.vintage.transition import VintageTransitionStep


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
def vintage_step() -> VintageTransitionStep:
    """VintageTransitionStep for testing pipeline integration."""
    config = VintageConfig(
        asset_class="vehicle",
        rules=(
            VintageTransitionRule(
                rule_type="fixed_entry",
                parameters={"count": 10},
            ),
            VintageTransitionRule(
                rule_type="max_age_retirement",
                parameters={"max_age": 20},
            ),
        ),
    )
    return VintageTransitionStep(config=config)


@pytest.fixture
def carry_forward_step() -> CarryForwardStep:
    """CarryForwardStep for testing pipeline integration."""
    config = CarryForwardConfig(
        rules=(
            CarryForwardRule(
                variable="inflation_factor",
                rule_type="scale",
                period_semantics="annual_growth_factor",
                value=1.02,
            ),
        ),
    )
    return CarryForwardStep(config=config)


class TestMockAdapterPipelineIntegration:
    """AC-3: Mock adapter enables full pipeline testing."""

    def test_orchestrator_runs_with_mock_adapter_only(
        self,
        computation_step: ComputationStep,
        mock_adapter: MockAdapter,
    ) -> None:
        """Given MockAdapter, when orchestrator runs, then pipeline completes."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={},
            seed=42,
            step_pipeline=(computation_step,),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is True
        assert len(result.yearly_states) == 3
        assert len(mock_adapter.call_log) == 3

    def test_computation_results_stored_per_year(
        self,
        computation_step: ComputationStep,
        mock_adapter: MockAdapter,
    ) -> None:
        """Given multi-year run, then computation results stored for each year."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={},
            seed=42,
            step_pipeline=(computation_step,),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        for year in [2025, 2026, 2027]:
            state = result.yearly_states[year]
            assert COMPUTATION_RESULT_KEY in state.data
            comp_result = state.data[COMPUTATION_RESULT_KEY]
            assert isinstance(comp_result, ComputationResult)
            assert comp_result.period == year

    def test_full_pipeline_with_all_step_types(
        self,
        computation_step: ComputationStep,
        vintage_step: VintageTransitionStep,
        carry_forward_step: CarryForwardStep,
        mock_adapter: MockAdapter,
    ) -> None:
        """Given full pipeline with computation + vintage + carry_forward,
        then orchestrator completes successfully using mock results."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={"inflation_factor": 1.0},
            seed=42,
            step_pipeline=(computation_step, vintage_step, carry_forward_step),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is True
        assert len(result.yearly_states) == 3

        # Verify computation results present
        for year in [2025, 2026, 2027]:
            state = result.yearly_states[year]
            assert COMPUTATION_RESULT_KEY in state.data
            assert COMPUTATION_METADATA_KEY in state.metadata

        # Verify vintage transition applied
        final_state = result.yearly_states[2027]
        assert "vintage_vehicle" in final_state.data

        # Verify carry forward applied
        # 1.0 * 1.02 * 1.02 * 1.02 ≈ 1.061208
        assert final_state.data["inflation_factor"] == pytest.approx(1.061208, rel=1e-5)


class TestPipelineOrdering:
    """Test step pipeline ordering behavior."""

    def test_computation_runs_before_transition_steps(
        self,
        computation_step: ComputationStep,
        vintage_step: VintageTransitionStep,
        carry_forward_step: CarryForwardStep,
        mock_adapter: MockAdapter,
    ) -> None:
        """Given pipeline, computation runs before transition steps."""
        # Register steps in order
        registry = StepRegistry()
        registry.register(computation_step)
        registry.register(vintage_step)
        registry.register(carry_forward_step)

        pipeline = registry.build_pipeline()

        # Computation should be first in pipeline
        assert len(pipeline) == 3
        assert pipeline[0].name == "computation"

    def test_pipeline_ordering_with_explicit_dependencies(
        self,
        mock_adapter: MockAdapter,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given steps with explicit dependencies, then topological order is correct."""
        computation = ComputationStep(
            adapter=mock_adapter,
            population=sample_population,
            policy=sample_policy,
        )

        # Create vintage step that depends on computation
        vintage_config = VintageConfig(
            asset_class="vehicle",
            rules=(
                VintageTransitionRule(
                    rule_type="fixed_entry",
                    parameters={"count": 5},
                ),
                VintageTransitionRule(
                    rule_type="max_age_retirement",
                    parameters={"max_age": 20},
                ),
            ),
        )
        vintage = VintageTransitionStep(
            config=vintage_config,
            depends_on=("computation",),
        )

        # Create carry_forward that depends on vintage_transition
        cf_config = CarryForwardConfig(rules=())
        carry_forward = CarryForwardStep(
            config=cf_config,
            depends_on=("vintage_transition",),
        )

        registry = StepRegistry()
        # Register in reverse order to test topological sort
        registry.register(carry_forward)
        registry.register(vintage)
        registry.register(computation)

        pipeline = registry.build_pipeline()

        # Despite reverse registration, dependencies enforce order
        assert [s.name for s in pipeline] == [
            "computation",
            "vintage_transition",
            "carry_forward",
        ]


class TestPartialResultsOnFailure:
    """AC-4: Partial results (completed years) preserved on adapter failure."""

    def test_partial_results_preserved_on_year_t_plus_2_failure(
        self,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given adapter fails at year t+2, then completed years are preserved."""

        class FailingAtYear2027Adapter:
            """Adapter that fails at year 2027 (t+2 from 2025)."""

            def __init__(self) -> None:
                self.call_log: list[int] = []

            def version(self) -> str:
                return "failing-at-2027-v1.0"

            def compute(
                self,
                population: PopulationData,
                policy: PolicyConfig,
                period: int,
            ) -> ComputationResult:
                self.call_log.append(period)
                if period == 2027:
                    raise RuntimeError(f"Simulated failure at year {period}")
                return ComputationResult(
                    output_fields=pa.table({"result": pa.array([0.0])}),
                    adapter_version=self.version(),
                    period=period,
                )

        failing_adapter = FailingAtYear2027Adapter()
        computation_step = ComputationStep(
            adapter=failing_adapter,  # type: ignore[arg-type]
            population=sample_population,
            policy=sample_policy,
        )

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2029,
            initial_state={},
            seed=42,
            step_pipeline=(computation_step,),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        # Execution should fail
        assert result.success is False
        assert result.failed_year == 2027
        assert result.failed_step == "computation"

        # Years 2025, 2026 should be preserved
        assert 2025 in result.yearly_states
        assert 2026 in result.yearly_states
        assert 2027 not in result.yearly_states

        # Verify completed years have valid computation results
        for year in [2025, 2026]:
            state = result.yearly_states[year]
            assert COMPUTATION_RESULT_KEY in state.data
            comp_result = state.data[COMPUTATION_RESULT_KEY]
            assert comp_result.period == year

    def test_error_includes_adapter_context(
        self,
        sample_population: PopulationData,
        sample_policy: PolicyConfig,
    ) -> None:
        """Given adapter failure, then error includes version and year context."""

        class FailingAdapter:
            def version(self) -> str:
                return "failing-adapter-v3.2.1"

            def compute(
                self,
                population: PopulationData,
                policy: PolicyConfig,
                period: int,
            ) -> ComputationResult:
                raise ValueError("Backend computation error")

        computation_step = ComputationStep(
            adapter=FailingAdapter(),  # type: ignore[arg-type]
            population=sample_population,
            policy=sample_policy,
        )

        config = OrchestratorConfig(
            start_year=2025,
            end_year=2026,
            initial_state={},
            seed=None,
            step_pipeline=(computation_step,),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is False
        assert result.failed_year == 2025
        assert len(result.errors) == 1
        error_msg = result.errors[0]
        assert "2025" in error_msg
        assert "failing-adapter-v3.2.1" in error_msg


class TestMultiYearExecution:
    """Test multi-year execution with computation step."""

    def test_adapter_called_for_each_year(
        self,
        computation_step: ComputationStep,
        mock_adapter: MockAdapter,
    ) -> None:
        """Given multi-year projection, then adapter.compute() called for each year."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2030,
            initial_state={},
            seed=42,
            step_pipeline=(computation_step,),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success is True
        assert len(mock_adapter.call_log) == 6  # 2025-2030 inclusive

        # Verify correct periods passed
        periods = [call["period"] for call in mock_adapter.call_log]
        assert periods == [2025, 2026, 2027, 2028, 2029, 2030]

    def test_metadata_recorded_for_each_year(
        self,
        computation_step: ComputationStep,
        mock_adapter: MockAdapter,
    ) -> None:
        """Given multi-year projection, then metadata recorded for each year."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            initial_state={},
            seed=42,
            step_pipeline=(computation_step,),
        )

        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        for year in [2025, 2026, 2027]:
            state = result.yearly_states[year]
            meta = state.metadata[COMPUTATION_METADATA_KEY]
            assert meta["adapter_version"] == "mock-2.0.0"
            assert meta["computation_period"] == year
            assert meta["computation_row_count"] == 3  # 3 rows in fixture table
