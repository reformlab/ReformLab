"""Tests for VintageTransitionStep execution."""

import pytest

from reformlab.orchestrator.types import YearState
from reformlab.vintage.config import VintageConfig, VintageTransitionRule
from reformlab.vintage.errors import VintageTransitionError
from reformlab.vintage.transition import VintageTransitionStep
from reformlab.vintage.types import VintageCohort, VintageState


class TestVintageTransitionStep:
    """Tests for VintageTransitionStep behavior."""

    @pytest.fixture
    def basic_config(self) -> VintageConfig:
        """Basic configuration with fixed entry and max age retirement."""
        return VintageConfig(
            asset_class="vehicle",
            rules=(
                VintageTransitionRule(
                    rule_type="fixed_entry",
                    parameters={"count": 100},
                ),
                VintageTransitionRule(
                    rule_type="max_age_retirement",
                    parameters={"max_age": 3},
                ),
            ),
        )

    @pytest.fixture
    def proportional_config(self) -> VintageConfig:
        """Configuration with proportional entry."""
        return VintageConfig(
            asset_class="vehicle",
            rules=(
                VintageTransitionRule(
                    rule_type="proportional_entry",
                    parameters={"rate": 0.1},  # 10% of fleet
                ),
                VintageTransitionRule(
                    rule_type="max_age_retirement",
                    parameters={"max_age": 5},
                ),
            ),
        )

    def test_protocol_compliance(self, basic_config: VintageConfig) -> None:
        """Step satisfies OrchestratorStep protocol."""
        step = VintageTransitionStep(basic_config)
        assert hasattr(step, "name")
        assert hasattr(step, "execute")
        assert step.name == "vintage_transition"

    def test_custom_name(self, basic_config: VintageConfig) -> None:
        """Step accepts custom name."""
        step = VintageTransitionStep(basic_config, name="my_vintage_step")
        assert step.name == "my_vintage_step"

    def test_depends_on(self, basic_config: VintageConfig) -> None:
        """Step accepts depends_on parameter."""
        step = VintageTransitionStep(basic_config, depends_on=("step_a", "step_b"))
        assert step.depends_on == ("step_a", "step_b")

    def test_execute_empty_state_creates_entry(
        self, basic_config: VintageConfig
    ) -> None:
        """Execute on empty state creates entry cohort."""
        step = VintageTransitionStep(basic_config)
        state = YearState(year=2024, data={})

        result = step.execute(2024, state)

        vintage = result.data["vintage_vehicle"]
        assert isinstance(vintage, VintageState)
        assert vintage.total_count == 100
        assert vintage.cohort_by_age(0) is not None
        assert vintage.cohort_by_age(0).count == 100  # type: ignore[union-attr]

    def test_execute_ages_cohorts(self, basic_config: VintageConfig) -> None:
        """Execute ages existing cohorts by one year."""
        step = VintageTransitionStep(basic_config)
        initial_vintage = VintageState(
            asset_class="vehicle",
            cohorts=(
                VintageCohort(age=0, count=50),
                VintageCohort(age=1, count=40),
            ),
        )
        state = YearState(year=2024, data={"vintage_vehicle": initial_vintage})

        result = step.execute(2024, state)

        vintage = result.data["vintage_vehicle"]
        # Original age=0 became age=1, original age=1 became age=2
        # Plus new entry cohort at age=0
        assert vintage.cohort_by_age(0) is not None
        assert vintage.cohort_by_age(0).count == 100  # type: ignore[union-attr]  # new entry
        assert vintage.cohort_by_age(1) is not None
        assert vintage.cohort_by_age(1).count == 50  # type: ignore[union-attr]  # was age=0
        assert vintage.cohort_by_age(2) is not None
        assert vintage.cohort_by_age(2).count == 40  # type: ignore[union-attr]  # was age=1

    def test_execute_retires_old_cohorts(self, basic_config: VintageConfig) -> None:
        """Execute removes cohorts above max age."""
        step = VintageTransitionStep(basic_config)  # max_age=3
        initial_vintage = VintageState(
            asset_class="vehicle",
            cohorts=(
                VintageCohort(age=2, count=30),  # becomes 3, survives
                VintageCohort(age=3, count=20),  # becomes 4, retired
            ),
        )
        state = YearState(year=2024, data={"vintage_vehicle": initial_vintage})

        result = step.execute(2024, state)

        vintage = result.data["vintage_vehicle"]
        assert vintage.cohort_by_age(3) is not None  # was age=2
        assert vintage.cohort_by_age(4) is None  # retired

    def test_execute_proportional_entry(
        self, proportional_config: VintageConfig
    ) -> None:
        """Execute with proportional entry adds cohorts based on fleet size."""
        step = VintageTransitionStep(proportional_config)
        initial_vintage = VintageState(
            asset_class="vehicle",
            cohorts=(VintageCohort(age=0, count=1000),),
        )
        state = YearState(year=2024, data={"vintage_vehicle": initial_vintage})

        result = step.execute(2024, state)

        vintage = result.data["vintage_vehicle"]
        # After aging: age=1 has 1000
        # Entry: 10% of 1000 = 100 at age=0
        assert vintage.cohort_by_age(0) is not None
        assert vintage.cohort_by_age(0).count == 100  # type: ignore[union-attr]

    def test_execute_preserves_other_state_data(
        self, basic_config: VintageConfig
    ) -> None:
        """Execute preserves other data in YearState."""
        step = VintageTransitionStep(basic_config)
        state = YearState(
            year=2024,
            data={"other_key": "preserved_value"},
        )

        result = step.execute(2024, state)

        assert result.data["other_key"] == "preserved_value"
        assert "vintage_vehicle" in result.data

    def test_execute_deterministic(self, basic_config: VintageConfig) -> None:
        """Execute produces identical results for identical inputs."""
        step = VintageTransitionStep(basic_config)
        initial_vintage = VintageState(
            asset_class="vehicle",
            cohorts=(
                VintageCohort(age=0, count=100),
                VintageCohort(age=1, count=90),
                VintageCohort(age=2, count=80),
            ),
        )
        state = YearState(year=2024, data={"vintage_vehicle": initial_vintage})

        result1 = step.execute(2024, state)
        result2 = step.execute(2024, state)

        # Full state equality
        assert result1.data == result2.data
        assert result1.year == result2.year

        # Vintage state equality
        v1 = result1.data["vintage_vehicle"]
        v2 = result2.data["vintage_vehicle"]
        assert v1.cohorts == v2.cohorts
        assert v1.total_count == v2.total_count

    def test_execute_immutable_input(self, basic_config: VintageConfig) -> None:
        """Execute does not modify input state."""
        step = VintageTransitionStep(basic_config)
        initial_vintage = VintageState(
            asset_class="vehicle",
            cohorts=(VintageCohort(age=0, count=100),),
        )
        state = YearState(year=2024, data={"vintage_vehicle": initial_vintage})
        original_data = dict(state.data)

        step.execute(2024, state)

        # Original state unchanged
        assert state.data == original_data

    def test_execute_uses_initial_state_from_config(self) -> None:
        """Execute uses initial_state from config when no state exists."""
        initial = VintageState(
            asset_class="vehicle",
            cohorts=(VintageCohort(age=5, count=500),),
        )
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
            initial_state=initial,
        )
        step = VintageTransitionStep(config)
        state = YearState(year=2024, data={})

        result = step.execute(2024, state)

        vintage = result.data["vintage_vehicle"]
        # Initial cohort aged from 5 to 6
        assert vintage.cohort_by_age(6) is not None
        assert vintage.cohort_by_age(6).count == 500  # type: ignore[union-attr]
        # Plus new entry cohort
        assert vintage.cohort_by_age(0) is not None
        assert vintage.cohort_by_age(0).count == 100  # type: ignore[union-attr]

    def test_execute_invalid_state_type_raises(
        self, basic_config: VintageConfig
    ) -> None:
        """Execute raises error when state data has wrong type."""
        step = VintageTransitionStep(basic_config)
        state = YearState(
            year=2024,
            data={"vintage_vehicle": {"invalid": "dict"}},
        )

        with pytest.raises(VintageTransitionError, match="expected VintageState"):
            step.execute(2024, state)

    def test_execute_asset_class_mismatch_raises(
        self, basic_config: VintageConfig
    ) -> None:
        """Execute raises error when state has mismatched asset class."""
        step = VintageTransitionStep(basic_config)  # vehicle
        wrong_vintage = VintageState(asset_class="different_class")
        state = YearState(year=2024, data={"vintage_vehicle": wrong_vintage})

        with pytest.raises(VintageTransitionError, match="Asset class mismatch"):
            step.execute(2024, state)

    def test_multi_year_transition(self, basic_config: VintageConfig) -> None:
        """Multi-year transitions produce expected fleet evolution."""
        step = VintageTransitionStep(basic_config)  # max_age=3, entry=100

        # Year 1: empty -> entry cohort
        state = YearState(year=2024, data={})
        state = step.execute(2024, state)
        vintage = state.data["vintage_vehicle"]
        assert vintage.total_count == 100

        # Year 2: age cohorts, add entry
        state = step.execute(2025, state)
        vintage = state.data["vintage_vehicle"]
        # age=0: 100 new, age=1: 100 from previous
        assert vintage.total_count == 200

        # Year 3
        state = step.execute(2026, state)
        vintage = state.data["vintage_vehicle"]
        # age=0: 100 new, age=1: 100, age=2: 100
        assert vintage.total_count == 300

        # Year 4
        state = step.execute(2027, state)
        vintage = state.data["vintage_vehicle"]
        # age=0: 100 new, age=1: 100, age=2: 100, age=3: 100
        assert vintage.total_count == 400

        # Year 5: first cohort retires (age 4 > max_age 3)
        state = step.execute(2028, state)
        vintage = state.data["vintage_vehicle"]
        # age=0: 100 new, age=1: 100, age=2: 100, age=3: 100
        # (age=4 retired)
        assert vintage.total_count == 400  # Steady state

    def test_cohort_ordering_deterministic(self, basic_config: VintageConfig) -> None:
        """Cohorts are always ordered by age after transition."""
        step = VintageTransitionStep(basic_config)
        # Start with unordered cohorts
        initial_vintage = VintageState(
            asset_class="vehicle",
            cohorts=(
                VintageCohort(age=2, count=80),
                VintageCohort(age=0, count=100),
                VintageCohort(age=1, count=90),
            ),
        )
        state = YearState(year=2024, data={"vintage_vehicle": initial_vintage})

        result = step.execute(2024, state)

        vintage = result.data["vintage_vehicle"]
        ages = [c.age for c in vintage.cohorts]
        assert ages == sorted(ages)
