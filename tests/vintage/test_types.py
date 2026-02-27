"""Tests for vintage domain types."""

import pytest

from reformlab.vintage.types import VintageCohort, VintageState, VintageSummary


class TestVintageCohort:
    """Tests for VintageCohort dataclass."""

    def test_valid_cohort(self) -> None:
        """Valid cohort creation."""
        cohort = VintageCohort(age=5, count=100)
        assert cohort.age == 5
        assert cohort.count == 100
        assert cohort.attributes == {}

    def test_cohort_with_attributes(self) -> None:
        """Cohort with optional attributes."""
        attrs = {"fuel_type": "electric", "region": "ile-de-france"}
        cohort = VintageCohort(age=0, count=50, attributes=attrs)
        assert cohort.attributes == attrs

    def test_negative_age_raises(self) -> None:
        """Negative age raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            VintageCohort(age=-1, count=10)

    def test_negative_count_raises(self) -> None:
        """Negative count raises ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            VintageCohort(age=0, count=-5)

    def test_zero_age_allowed(self) -> None:
        """Zero age is valid (new cohort)."""
        cohort = VintageCohort(age=0, count=100)
        assert cohort.age == 0

    def test_zero_count_allowed(self) -> None:
        """Zero count is valid (empty cohort)."""
        cohort = VintageCohort(age=5, count=0)
        assert cohort.count == 0

    def test_immutable(self) -> None:
        """Cohort is immutable (frozen dataclass)."""
        cohort = VintageCohort(age=5, count=100)
        with pytest.raises(Exception):  # FrozenInstanceError
            cohort.age = 6  # type: ignore[misc]


class TestVintageState:
    """Tests for VintageState dataclass."""

    def test_empty_state(self) -> None:
        """Empty state with no cohorts."""
        state = VintageState(asset_class="vehicle")
        assert state.asset_class == "vehicle"
        assert state.cohorts == ()
        assert state.total_count == 0

    def test_state_with_cohorts(self) -> None:
        """State with multiple cohorts."""
        cohorts = (
            VintageCohort(age=0, count=100),
            VintageCohort(age=1, count=90),
            VintageCohort(age=2, count=80),
        )
        state = VintageState(asset_class="vehicle", cohorts=cohorts)
        assert len(state.cohorts) == 3
        assert state.total_count == 270

    def test_age_distribution(self) -> None:
        """Age distribution property."""
        cohorts = (
            VintageCohort(age=0, count=100),
            VintageCohort(age=5, count=50),
        )
        state = VintageState(asset_class="vehicle", cohorts=cohorts)
        assert state.age_distribution == {0: 100, 5: 50}

    def test_cohort_by_age_found(self) -> None:
        """cohort_by_age returns cohort when found."""
        cohorts = (
            VintageCohort(age=0, count=100),
            VintageCohort(age=5, count=50),
        )
        state = VintageState(asset_class="vehicle", cohorts=cohorts)
        cohort = state.cohort_by_age(5)
        assert cohort is not None
        assert cohort.count == 50

    def test_cohort_by_age_not_found(self) -> None:
        """cohort_by_age returns None when not found."""
        state = VintageState(
            asset_class="vehicle",
            cohorts=(VintageCohort(age=0, count=100),),
        )
        assert state.cohort_by_age(99) is None

    def test_empty_asset_class_raises(self) -> None:
        """Empty asset class raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            VintageState(asset_class="")

    def test_whitespace_asset_class_raises(self) -> None:
        """Whitespace-only asset class raises ValueError."""
        with pytest.raises(ValueError, match="non-empty"):
            VintageState(asset_class="   ")

    def test_cohorts_normalized_to_tuple(self) -> None:
        """Cohorts list is normalized to tuple."""
        cohorts = [VintageCohort(age=0, count=100)]
        state = VintageState(asset_class="vehicle", cohorts=cohorts)  # type: ignore[arg-type]
        assert isinstance(state.cohorts, tuple)


class TestVintageSummary:
    """Tests for VintageSummary dataclass."""

    def test_from_empty_state(self) -> None:
        """Summary from empty state."""
        state = VintageState(asset_class="vehicle")
        summary = VintageSummary.from_state(state)
        assert summary.asset_class == "vehicle"
        assert summary.total_count == 0
        assert summary.cohort_count == 0
        assert summary.mean_age == 0.0
        assert summary.max_age == 0

    def test_from_state_with_cohorts(self) -> None:
        """Summary from state with cohorts."""
        cohorts = (
            VintageCohort(age=0, count=100),  # 100 * 0 = 0
            VintageCohort(age=5, count=100),  # 100 * 5 = 500
            VintageCohort(age=10, count=100),  # 100 * 10 = 1000
        )
        state = VintageState(asset_class="vehicle", cohorts=cohorts)
        summary = VintageSummary.from_state(state)

        assert summary.total_count == 300
        assert summary.cohort_count == 3
        assert summary.max_age == 10
        # Mean age: (0 + 500 + 1000) / 300 = 1500 / 300 = 5.0
        assert summary.mean_age == 5.0

    def test_summary_age_distribution_copied(self) -> None:
        """Summary age distribution is a copy."""
        cohorts = (VintageCohort(age=0, count=100),)
        state = VintageState(asset_class="vehicle", cohorts=cohorts)
        summary = VintageSummary.from_state(state)
        assert summary.age_distribution == {0: 100}

    def test_summary_metadata_copied(self) -> None:
        """Summary copies metadata from state."""
        state = VintageState(
            asset_class="vehicle",
            metadata={"source": "test"},
        )
        summary = VintageSummary.from_state(state)
        assert summary.metadata == {"source": "test"}
