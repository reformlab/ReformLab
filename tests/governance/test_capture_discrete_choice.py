"""Tests for capture_discrete_choice_parameters function.

Story 14-6: Extend Panel Output and Manifests with Decision Records.
AC-5: Manifest taste parameter capture.
"""

from __future__ import annotations

from typing import Any

import pyarrow as pa

from reformlab.discrete_choice.decision_record import (
    DECISION_LOG_KEY,
    DecisionRecord,
)
from reformlab.governance.capture import capture_discrete_choice_parameters
from reformlab.orchestrator.types import YearState

# ============================================================================
# Test helpers
# ============================================================================


def _make_record(
    domain_name: str,
    beta_cost: float = -0.01,
    seed: int | None = 42,
    eligibility: dict[str, int] | None = None,
    alt_ids: tuple[str, ...] = ("ev", "ice"),
) -> DecisionRecord:
    """Build a minimal DecisionRecord for capture tests."""
    n = 2
    taste: dict[str, float] = {}
    if beta_cost != 0.0:
        taste["beta_cost"] = beta_cost
    return DecisionRecord(
        domain_name=domain_name,
        chosen=pa.array(["ev"] * n, type=pa.string()),
        probabilities=pa.table({aid: [0.5] * n for aid in alt_ids}),
        utilities=pa.table({aid: [-1.0] * n for aid in alt_ids}),
        alternative_ids=alt_ids,
        seed=seed,
        taste_parameters=taste,
        eligibility_summary=eligibility,
    )


def _make_yearly_states(
    years_with_records: dict[int, list[DecisionRecord]],
    years_without: list[int] | None = None,
) -> dict[int, Any]:
    """Build yearly states dict for capture function."""
    states: dict[int, Any] = {}
    for year, records in years_with_records.items():
        states[year] = YearState(
            year=year,
            data={DECISION_LOG_KEY: tuple(records)},
            seed=42,
            metadata={},
        )
    for year in (years_without or []):
        states[year] = YearState(
            year=year, data={}, seed=42, metadata={}
        )
    return states


# ============================================================================
# TestCaptureDiscreteChoiceParameters — AC-5
# ============================================================================


class TestCaptureDiscreteChoiceParameters:
    """AC-5: Extract taste parameters from decision log."""

    def test_single_domain(self) -> None:
        """Extracts parameters from a single domain."""
        record = _make_record("vehicle", beta_cost=-0.01, seed=42)
        states = _make_yearly_states({2025: [record]})

        result = capture_discrete_choice_parameters(states)

        assert len(result) == 1
        entry = result[0]
        assert entry["domain_name"] == "vehicle"
        assert entry["beta_cost"] == -0.01
        assert entry["choice_seed"] == 42
        assert entry["alternative_ids"] == ["ev", "ice"]

    def test_two_domains_sorted_by_name(self) -> None:
        """Extracts from two domains, sorted by domain_name."""
        vehicle = _make_record("vehicle", beta_cost=-0.01, seed=42)
        heating = _make_record("heating", beta_cost=-0.02, seed=99)
        states = _make_yearly_states({2025: [vehicle, heating]})

        result = capture_discrete_choice_parameters(states)

        assert len(result) == 2
        assert result[0]["domain_name"] == "heating"
        assert result[1]["domain_name"] == "vehicle"

    def test_empty_when_no_decision_log(self) -> None:
        """Returns empty list when no decision log exists."""
        states = _make_yearly_states({}, years_without=[2025, 2026])

        result = capture_discrete_choice_parameters(states)

        assert result == []

    def test_uses_first_year_only(self) -> None:
        """Captures from first year containing decision log."""
        rec_2025 = _make_record("vehicle", beta_cost=-0.01, seed=42)
        rec_2026 = _make_record("vehicle", beta_cost=-0.99, seed=999)
        states = _make_yearly_states({
            2025: [rec_2025],
            2026: [rec_2026],
        })

        result = capture_discrete_choice_parameters(states)

        assert len(result) == 1
        assert result[0]["beta_cost"] == -0.01
        assert result[0]["choice_seed"] == 42

    def test_includes_eligibility_summary(self) -> None:
        """Includes eligibility_summary when present."""
        record = _make_record(
            "vehicle",
            eligibility={"n_total": 100, "n_eligible": 30, "n_ineligible": 70},
        )
        states = _make_yearly_states({2025: [record]})

        result = capture_discrete_choice_parameters(states)

        assert result[0]["eligibility_summary"] == {
            "n_total": 100,
            "n_eligible": 30,
            "n_ineligible": 70,
        }

    def test_no_eligibility_when_none(self) -> None:
        """No eligibility_summary key when it's None."""
        record = _make_record("vehicle", eligibility=None)
        states = _make_yearly_states({2025: [record]})

        result = capture_discrete_choice_parameters(states)

        assert "eligibility_summary" not in result[0]

    def test_no_seed_when_none(self) -> None:
        """No choice_seed key when seed is None."""
        record = _make_record("vehicle", seed=None)
        states = _make_yearly_states({2025: [record]})

        result = capture_discrete_choice_parameters(states)

        assert "choice_seed" not in result[0]

    def test_skips_years_without_decision_log(self) -> None:
        """Skips years that don't have decision log to find first with log."""
        record = _make_record("vehicle")
        states = _make_yearly_states(
            {2026: [record]},
            years_without=[2025],
        )

        result = capture_discrete_choice_parameters(states)

        assert len(result) == 1
        assert result[0]["domain_name"] == "vehicle"
