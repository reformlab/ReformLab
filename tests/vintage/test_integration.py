"""Integration tests for VintageTransitionStep with orchestrator."""

import pytest

from reformlab.orchestrator.carry_forward import (
    CarryForwardConfig,
    CarryForwardRule,
    CarryForwardStep,
)
from reformlab.orchestrator.runner import Orchestrator
from reformlab.orchestrator.step import StepRegistry, is_protocol_step
from reformlab.orchestrator.types import OrchestratorConfig, YearState
from reformlab.vintage.config import VintageConfig, VintageTransitionRule
from reformlab.vintage.transition import VintageTransitionStep
from reformlab.vintage.types import VintageCohort, VintageState


class TestVintageStepRegistration:
    """Tests for VintageTransitionStep registry integration."""

    @pytest.fixture
    def vintage_step(self) -> VintageTransitionStep:
        """Fixture providing a configured vintage step."""
        config = VintageConfig(
            asset_class="vehicle",
            rules=(
                VintageTransitionRule(
                    rule_type="fixed_entry",
                    parameters={"count": 100},
                ),
                VintageTransitionRule(
                    rule_type="max_age_retirement",
                    parameters={"max_age": 15},
                ),
            ),
        )
        return VintageTransitionStep(config)

    def test_is_protocol_step(self, vintage_step: VintageTransitionStep) -> None:
        """VintageTransitionStep satisfies OrchestratorStep protocol."""
        assert is_protocol_step(vintage_step)

    def test_registry_registration(self, vintage_step: VintageTransitionStep) -> None:
        """Step can be registered in StepRegistry."""
        registry = StepRegistry()
        registry.register(vintage_step)

        assert len(registry) == 1
        assert registry.get("vintage_transition") is vintage_step

    def test_registry_build_pipeline(self, vintage_step: VintageTransitionStep) -> None:
        """Step can be built into pipeline."""
        registry = StepRegistry()
        registry.register(vintage_step)

        pipeline = registry.build_pipeline()

        assert len(pipeline) == 1
        assert pipeline[0] is vintage_step


class TestVintageCarryForwardPipelineOrder:
    """Tests for pipeline ordering with vintage and carry-forward steps."""

    @pytest.fixture
    def vintage_step(self) -> VintageTransitionStep:
        """Vintage step for pipeline tests."""
        config = VintageConfig(
            asset_class="vehicle",
            rules=(
                VintageTransitionRule(
                    rule_type="fixed_entry",
                    parameters={"count": 100},
                ),
                VintageTransitionRule(
                    rule_type="max_age_retirement",
                    parameters={"max_age": 15},
                ),
            ),
        )
        return VintageTransitionStep(config)

    @pytest.fixture
    def carry_forward_step(self) -> CarryForwardStep:
        """Carry-forward step for pipeline tests."""
        config = CarryForwardConfig(
            rules=(
                CarryForwardRule(
                    variable="income",
                    rule_type="scale",
                    period_semantics="annual_growth",
                    value=1.02,
                ),
            )
        )
        return CarryForwardStep(config)

    def test_vintage_before_carry_forward_no_dependency(
        self,
        vintage_step: VintageTransitionStep,
        carry_forward_step: CarryForwardStep,
    ) -> None:
        """Vintage registered before carry-forward runs first (no explicit deps)."""
        registry = StepRegistry()
        registry.register(vintage_step)  # First
        registry.register(carry_forward_step)  # Second

        pipeline = registry.build_pipeline()

        # Registration order preserved when no dependencies
        assert pipeline[0].name == "vintage_transition"
        assert pipeline[1].name == "carry_forward"

    def test_carry_forward_depends_on_vintage(
        self,
        vintage_step: VintageTransitionStep,
    ) -> None:
        """Carry-forward can declare dependency on vintage."""
        cf_config = CarryForwardConfig(
            rules=(
                CarryForwardRule(
                    variable="income",
                    rule_type="static",
                    period_semantics="preserved",
                ),
            )
        )
        carry_forward_step = CarryForwardStep(
            cf_config,
            depends_on=("vintage_transition",),
        )

        registry = StepRegistry()
        # Register in reverse order
        registry.register(carry_forward_step)  # Second, but depends on vintage
        registry.register(vintage_step)  # First

        pipeline = registry.build_pipeline()

        # Dependency order enforced
        step_names = [s.name for s in pipeline]
        assert step_names.index("vintage_transition") < step_names.index(
            "carry_forward"
        )


class TestVintageOrchestratorExecution:
    """Tests for VintageTransitionStep execution via Orchestrator."""

    @pytest.fixture
    def vintage_config(self) -> VintageConfig:
        """Config for orchestrator tests."""
        return VintageConfig(
            asset_class="vehicle",
            rules=(
                VintageTransitionRule(
                    rule_type="fixed_entry",
                    parameters={"count": 1000},
                ),
                VintageTransitionRule(
                    rule_type="max_age_retirement",
                    parameters={"max_age": 20},
                ),
            ),
        )

    def test_orchestrator_executes_vintage_step(
        self, vintage_config: VintageConfig
    ) -> None:
        """Orchestrator executes vintage step and produces yearly states."""
        step = VintageTransitionStep(vintage_config)
        config = OrchestratorConfig(
            start_year=2024,
            end_year=2026,
            step_pipeline=(step,),
        )
        orchestrator = Orchestrator(config)

        result = orchestrator.run()

        assert result.success
        assert len(result.yearly_states) == 3  # 2024, 2025, 2026

        # Check each year has vintage data
        for year in range(2024, 2027):
            state = result.yearly_states[year]
            assert "vintage_vehicle" in state.data
            vintage = state.data["vintage_vehicle"]
            assert isinstance(vintage, VintageState)

    def test_orchestrator_vintage_evolves_over_years(
        self, vintage_config: VintageConfig
    ) -> None:
        """Vintage state evolves correctly over multiple years."""
        step = VintageTransitionStep(vintage_config)
        config = OrchestratorConfig(
            start_year=2024,
            end_year=2028,
            step_pipeline=(step,),
        )
        orchestrator = Orchestrator(config)

        result = orchestrator.run()

        assert result.success

        # Year 1: only entry cohort
        v2024 = result.yearly_states[2024].data["vintage_vehicle"]
        assert v2024.total_count == 1000

        # Year 5: 5 cohorts (ages 0-4)
        v2028 = result.yearly_states[2028].data["vintage_vehicle"]
        assert v2028.total_count == 5000

    def test_orchestrator_with_initial_state(
        self, vintage_config: VintageConfig
    ) -> None:
        """Orchestrator respects initial vintage state."""
        initial_vintage = VintageState(
            asset_class="vehicle",
            cohorts=(
                VintageCohort(age=10, count=5000),
                VintageCohort(age=15, count=3000),
            ),
        )

        step = VintageTransitionStep(vintage_config)
        config = OrchestratorConfig(
            start_year=2024,
            end_year=2024,
            initial_state={"vintage_vehicle": initial_vintage},
            step_pipeline=(step,),
        )
        orchestrator = Orchestrator(config)

        result = orchestrator.run()

        assert result.success
        vintage = result.yearly_states[2024].data["vintage_vehicle"]

        # Initial cohorts aged: 10->11, 15->16
        # Plus new entry: 1000 at age=0
        assert vintage.cohort_by_age(0) is not None
        assert vintage.cohort_by_age(0).count == 1000  # type: ignore[union-attr]
        assert vintage.cohort_by_age(11) is not None
        assert vintage.cohort_by_age(11).count == 5000  # type: ignore[union-attr]
        assert vintage.cohort_by_age(16) is not None
        assert vintage.cohort_by_age(16).count == 3000  # type: ignore[union-attr]


class TestVintageStateDownstreamVisibility:
    """Tests ensuring vintage state is accessible for downstream consumers."""

    def test_vintage_state_key_stable(self) -> None:
        """Vintage state uses stable key pattern for downstream access."""
        config = VintageConfig(
            asset_class="vehicle",
            rules=(
                VintageTransitionRule(
                    rule_type="fixed_entry",
                    parameters={"count": 100},
                ),
                VintageTransitionRule(
                    rule_type="max_age_retirement",
                    parameters={"max_age": 10},
                ),
            ),
        )
        step = VintageTransitionStep(config)
        state = YearState(year=2024, data={})

        result = step.execute(2024, state)

        # Key follows stable pattern: vintage_{asset_class}
        assert "vintage_vehicle" in result.data

    def test_vintage_state_has_required_downstream_attributes(self) -> None:
        """Vintage state provides attributes needed by downstream stories."""
        config = VintageConfig(
            asset_class="vehicle",
            rules=(
                VintageTransitionRule(
                    rule_type="fixed_entry",
                    parameters={"count": 100},
                ),
                VintageTransitionRule(
                    rule_type="max_age_retirement",
                    parameters={"max_age": 10},
                ),
            ),
        )
        step = VintageTransitionStep(config)
        initial_vintage = VintageState(
            asset_class="vehicle",
            cohorts=(
                VintageCohort(age=0, count=100),
                VintageCohort(age=5, count=50),
            ),
        )
        state = YearState(year=2024, data={"vintage_vehicle": initial_vintage})

        result = step.execute(2024, state)

        vintage = result.data["vintage_vehicle"]
        # These attributes are needed for Story 3-7 panel output and EPIC-4 indicators
        assert hasattr(vintage, "total_count")
        assert hasattr(vintage, "age_distribution")
        assert hasattr(vintage, "cohorts")
        assert hasattr(vintage, "asset_class")

    def test_vintage_state_can_produce_summary(self) -> None:
        """Vintage state can produce VintageSummary for indicators."""
        from reformlab.vintage.types import VintageSummary

        config = VintageConfig(
            asset_class="vehicle",
            rules=(
                VintageTransitionRule(
                    rule_type="fixed_entry",
                    parameters={"count": 100},
                ),
                VintageTransitionRule(
                    rule_type="max_age_retirement",
                    parameters={"max_age": 10},
                ),
            ),
        )
        step = VintageTransitionStep(config)
        state = YearState(year=2024, data={})

        result = step.execute(2024, state)

        vintage = result.data["vintage_vehicle"]
        summary = VintageSummary.from_state(vintage)

        assert summary.asset_class == "vehicle"
        assert summary.total_count == 100
        assert summary.mean_age == 0.0  # Only age=0 cohort
