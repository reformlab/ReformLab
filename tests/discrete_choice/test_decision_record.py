# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for DecisionRecord type and DecisionRecordStep.

Story 14-6: Extend Panel Output and Manifests with Decision Records.
AC-1: DecisionRecord type.
AC-2: DecisionRecordStep.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pyarrow as pa
import pytest

from reformlab.discrete_choice.decision_record import (
    DECISION_LOG_KEY,
    DecisionRecord,
    DecisionRecordStep,
)
from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.logit import DISCRETE_CHOICE_RESULT_KEY
from reformlab.discrete_choice.step import DISCRETE_CHOICE_METADATA_KEY
from reformlab.discrete_choice.types import ChoiceResult
from reformlab.orchestrator.step import StepRegistry, is_protocol_step
from reformlab.orchestrator.types import YearState

# ============================================================================
# Test helpers
# ============================================================================

def _make_choice_result(
    n: int,
    alt_ids: tuple[str, ...] = ("ev", "ice", "keep"),
    chosen: list[str] | None = None,
    seed: int = 42,
) -> ChoiceResult:
    """Build a ChoiceResult for testing."""
    if chosen is None:
        chosen = [alt_ids[0]] * n

    m = len(alt_ids)
    uniform_prob = 1.0 / m
    prob_data = {aid: [uniform_prob] * n for aid in alt_ids}
    util_data = {aid: [float(-idx - 1)] * n for idx, aid in enumerate(alt_ids)}

    return ChoiceResult(
        chosen=pa.array(chosen, type=pa.string()),
        probabilities=pa.table(prob_data),
        utilities=pa.table(util_data),
        alternative_ids=alt_ids,
        seed=seed,
    )


def _make_metadata(
    domain_name: str = "vehicle",
    beta_cost: float = -0.01,
    choice_seed: int = 42,
    eligibility: bool = False,
) -> dict[str, object]:
    """Build discrete choice metadata dict for testing."""
    meta: dict[str, object] = {
        "domain_name": domain_name,
        "beta_cost": beta_cost,
        "choice_seed": choice_seed,
    }
    if eligibility:
        meta["eligibility_n_total"] = 100
        meta["eligibility_n_eligible"] = 30
        meta["eligibility_n_ineligible"] = 70
    return meta


def _make_state(
    choice_result: ChoiceResult | None = None,
    metadata: dict[str, object] | None = None,
    existing_log: tuple[DecisionRecord, ...] | None = None,
    seed: int = 42,
) -> YearState:
    """Build a YearState for testing DecisionRecordStep."""
    data: dict[str, object] = {}
    if choice_result is not None:
        data[DISCRETE_CHOICE_RESULT_KEY] = choice_result
    if metadata is not None:
        data[DISCRETE_CHOICE_METADATA_KEY] = metadata
    if existing_log is not None:
        data[DECISION_LOG_KEY] = existing_log
    return YearState(year=2025, data=data, seed=seed, metadata={})


# ============================================================================
# TestDecisionRecord — AC-1
# ============================================================================


class TestDecisionRecord:
    """AC-1: DecisionRecord frozen dataclass with all required fields."""

    def test_construction_all_fields(self) -> None:
        """DecisionRecord can be constructed with all fields."""
        alt_ids = ("ev", "ice", "keep")
        n = 3
        record = DecisionRecord(
            domain_name="vehicle",
            chosen=pa.array(["ev", "ice", "keep"], type=pa.string()),
            probabilities=pa.table({aid: [0.33] * n for aid in alt_ids}),
            utilities=pa.table({aid: [-1.0] * n for aid in alt_ids}),
            alternative_ids=alt_ids,
            seed=42,
            taste_parameters={"beta_cost": -0.01},
            eligibility_summary={"n_total": 100, "n_eligible": 30, "n_ineligible": 70},
        )

        assert record.domain_name == "vehicle"
        assert len(record.chosen) == 3
        assert record.probabilities.num_rows == 3
        assert record.utilities.num_rows == 3
        assert record.alternative_ids == ("ev", "ice", "keep")
        assert record.seed == 42
        assert record.taste_parameters == {"beta_cost": -0.01}
        assert record.eligibility_summary == {
            "n_total": 100,
            "n_eligible": 30,
            "n_ineligible": 70,
        }

    def test_frozen(self) -> None:
        """DecisionRecord is immutable."""
        record = DecisionRecord(
            domain_name="vehicle",
            chosen=pa.array(["ev"], type=pa.string()),
            probabilities=pa.table({"ev": [1.0]}),
            utilities=pa.table({"ev": [-1.0]}),
            alternative_ids=("ev",),
            seed=42,
            taste_parameters={},
            eligibility_summary=None,
        )
        with pytest.raises(FrozenInstanceError):
            record.domain_name = "heating"  # type: ignore[misc]

    def test_optional_fields(self) -> None:
        """DecisionRecord handles None seed and None eligibility_summary."""
        record = DecisionRecord(
            domain_name="heating",
            chosen=pa.array([], type=pa.string()),
            probabilities=pa.table({"hp": pa.array([], type=pa.float64())}),
            utilities=pa.table({"hp": pa.array([], type=pa.float64())}),
            alternative_ids=("hp",),
            seed=None,
            taste_parameters={},
            eligibility_summary=None,
        )
        assert record.seed is None
        assert record.eligibility_summary is None

    def test_empty_population(self) -> None:
        """DecisionRecord supports N=0 (empty population)."""
        record = DecisionRecord(
            domain_name="vehicle",
            chosen=pa.array([], type=pa.string()),
            probabilities=pa.table({"ev": pa.array([], type=pa.float64())}),
            utilities=pa.table({"ev": pa.array([], type=pa.float64())}),
            alternative_ids=("ev",),
            seed=42,
            taste_parameters={"beta_cost": -0.01},
            eligibility_summary=None,
        )
        assert len(record.chosen) == 0
        assert record.probabilities.num_rows == 0


# ============================================================================
# TestDecisionRecordStep — AC-2
# ============================================================================


class TestDecisionRecordStep:
    """AC-2: DecisionRecordStep implements OrchestratorStep protocol."""

    def test_protocol_compliance(self) -> None:
        """DecisionRecordStep implements the OrchestratorStep protocol."""
        step = DecisionRecordStep()
        assert is_protocol_step(step)

    def test_step_registry_registration(self) -> None:
        """DecisionRecordStep can be registered in StepRegistry."""
        registry = StepRegistry()
        step = DecisionRecordStep(
            name="decision_record_vehicle",
            depends_on=("vehicle_state_update",),
        )
        registry.register(step)
        assert registry.get("decision_record_vehicle") is step

    def test_default_name_and_depends_on(self) -> None:
        """Defaults: name='decision_record', depends_on=('vehicle_state_update',)."""
        step = DecisionRecordStep()
        assert step.name == "decision_record"
        assert step.depends_on == ("vehicle_state_update",)

    def test_custom_name_and_depends_on(self) -> None:
        """Custom name and depends_on are accepted."""
        step = DecisionRecordStep(
            name="decision_record_heating",
            depends_on=("heating_state_update",),
        )
        assert step.name == "decision_record_heating"
        assert step.depends_on == ("heating_state_update",)

    def test_pass_through_when_no_choice_result(self) -> None:
        """Step returns state unchanged when no ChoiceResult in state."""
        step = DecisionRecordStep()
        state = YearState(year=2025, data={}, seed=42, metadata={})
        result = step.execute(2025, state)
        assert result is state

    def test_creates_decision_record(self) -> None:
        """Step creates a DecisionRecord from ChoiceResult and metadata."""
        step = DecisionRecordStep()
        cr = _make_choice_result(3)
        meta = _make_metadata(domain_name="vehicle", beta_cost=-0.01, choice_seed=42)
        state = _make_state(choice_result=cr, metadata=meta)

        result = step.execute(2025, state)

        log = result.data[DECISION_LOG_KEY]
        assert isinstance(log, tuple)
        assert len(log) == 1
        record = log[0]
        assert isinstance(record, DecisionRecord)
        assert record.domain_name == "vehicle"
        assert record.taste_parameters == {"beta_cost": -0.01}
        assert record.seed == 42
        assert record.alternative_ids == ("ev", "ice", "keep")
        assert len(record.chosen) == 3

    def test_appends_to_existing_log(self) -> None:
        """Step appends to existing decision log tuple."""
        step = DecisionRecordStep()
        cr = _make_choice_result(3)

        # Create an existing record
        existing_record = DecisionRecord(
            domain_name="vehicle",
            chosen=pa.array(["ev"] * 3, type=pa.string()),
            probabilities=pa.table({"ev": [1.0] * 3}),
            utilities=pa.table({"ev": [-1.0] * 3}),
            alternative_ids=("ev",),
            seed=42,
            taste_parameters={"beta_cost": -0.01},
            eligibility_summary=None,
        )
        meta = _make_metadata(domain_name="heating", beta_cost=-0.02, choice_seed=99)
        state = _make_state(
            choice_result=cr,
            metadata=meta,
            existing_log=(existing_record,),
        )

        result = step.execute(2025, state)

        log = result.data[DECISION_LOG_KEY]
        assert len(log) == 2
        assert log[0].domain_name == "vehicle"
        assert log[1].domain_name == "heating"
        assert log[1].taste_parameters == {"beta_cost": -0.02}

    def test_creates_new_log_when_none_exists(self) -> None:
        """Step creates a new log tuple when none exists in state."""
        step = DecisionRecordStep()
        cr = _make_choice_result(2)
        meta = _make_metadata()
        state = _make_state(choice_result=cr, metadata=meta)

        result = step.execute(2025, state)

        log = result.data[DECISION_LOG_KEY]
        assert isinstance(log, tuple)
        assert len(log) == 1

    def test_extracts_taste_parameters(self) -> None:
        """Step extracts beta_cost from metadata."""
        step = DecisionRecordStep()
        cr = _make_choice_result(1)
        meta = _make_metadata(beta_cost=-0.05)
        state = _make_state(choice_result=cr, metadata=meta)

        result = step.execute(2025, state)

        record = result.data[DECISION_LOG_KEY][0]
        assert record.taste_parameters == {"beta_cost": -0.05}

    def test_missing_beta_cost_produces_empty_taste_params(self) -> None:
        """When beta_cost is not in metadata, taste_parameters is empty."""
        step = DecisionRecordStep()
        cr = _make_choice_result(1)
        meta: dict[str, object] = {"domain_name": "vehicle"}
        state = _make_state(choice_result=cr, metadata=meta)

        result = step.execute(2025, state)

        record = result.data[DECISION_LOG_KEY][0]
        assert record.taste_parameters == {}

    def test_extracts_eligibility_summary(self) -> None:
        """Step extracts eligibility summary from metadata when present."""
        step = DecisionRecordStep()
        cr = _make_choice_result(1)
        meta = _make_metadata(eligibility=True)
        state = _make_state(choice_result=cr, metadata=meta)

        result = step.execute(2025, state)

        record = result.data[DECISION_LOG_KEY][0]
        assert record.eligibility_summary == {
            "n_total": 100,
            "n_eligible": 30,
            "n_ineligible": 70,
        }

    def test_no_eligibility_summary_when_absent(self) -> None:
        """Step sets eligibility_summary=None when no eligibility metadata."""
        step = DecisionRecordStep()
        cr = _make_choice_result(1)
        meta = _make_metadata(eligibility=False)
        state = _make_state(choice_result=cr, metadata=meta)

        result = step.execute(2025, state)

        record = result.data[DECISION_LOG_KEY][0]
        assert record.eligibility_summary is None

    def test_state_immutability(self) -> None:
        """Original state is not mutated by step execution."""
        step = DecisionRecordStep()
        cr = _make_choice_result(2)
        meta = _make_metadata()
        state = _make_state(choice_result=cr, metadata=meta)
        original_data_keys = set(state.data.keys())

        step.execute(2025, state)

        assert set(state.data.keys()) == original_data_keys
        assert DECISION_LOG_KEY not in state.data

    def test_non_dict_metadata_raises_error(self) -> None:
        """Non-dict metadata raises DiscreteChoiceError."""
        step = DecisionRecordStep()
        cr = _make_choice_result(1)
        data: dict[str, object] = {
            DISCRETE_CHOICE_RESULT_KEY: cr,
            DISCRETE_CHOICE_METADATA_KEY: "not a dict",
        }
        state = YearState(year=2025, data=data, seed=42, metadata={})

        with pytest.raises(DiscreteChoiceError, match="dict"):
            step.execute(2025, state)

    def test_non_tuple_existing_log_raises_error(self) -> None:
        """Non-tuple existing decision log raises DiscreteChoiceError."""
        step = DecisionRecordStep()
        cr = _make_choice_result(1)
        meta = _make_metadata()
        data: dict[str, object] = {
            DISCRETE_CHOICE_RESULT_KEY: cr,
            DISCRETE_CHOICE_METADATA_KEY: meta,
            DECISION_LOG_KEY: [1, 2, 3],  # list, not tuple
        }
        state = YearState(year=2025, data=data, seed=42, metadata={})

        with pytest.raises(DiscreteChoiceError, match="tuple"):
            step.execute(2025, state)

    def test_missing_domain_name_defaults_to_unknown(self) -> None:
        """Missing domain_name in metadata defaults to 'unknown'."""
        step = DecisionRecordStep()
        cr = _make_choice_result(1)
        meta: dict[str, object] = {"beta_cost": -0.01}
        state = _make_state(choice_result=cr, metadata=meta)

        result = step.execute(2025, state)

        record = result.data[DECISION_LOG_KEY][0]
        assert record.domain_name == "unknown"


# ============================================================================
# TestDecisionRecordStepMultiDomain — AC-2
# ============================================================================


class TestDecisionRecordStepMultiDomain:
    """AC-2: Two domains in sequence produce two records in log."""

    def test_two_domains_produce_two_records(self) -> None:
        """Sequential vehicle → heating produces two DecisionRecords."""
        vehicle_step = DecisionRecordStep(
            name="decision_record_vehicle",
            depends_on=("vehicle_state_update",),
        )
        heating_step = DecisionRecordStep(
            name="decision_record_heating",
            depends_on=("heating_state_update",),
        )

        # Vehicle domain
        vehicle_cr = _make_choice_result(3, alt_ids=("ev", "ice", "keep"), seed=42)
        vehicle_meta = _make_metadata(domain_name="vehicle", beta_cost=-0.01)
        state = _make_state(choice_result=vehicle_cr, metadata=vehicle_meta)

        state = vehicle_step.execute(2025, state)

        # Heating domain — overwrite ChoiceResult and metadata as pipeline would
        heating_cr = _make_choice_result(3, alt_ids=("hp", "gas", "keep_h"), seed=99)
        heating_meta = _make_metadata(domain_name="heating", beta_cost=-0.02)
        new_data = dict(state.data)
        new_data[DISCRETE_CHOICE_RESULT_KEY] = heating_cr
        new_data[DISCRETE_CHOICE_METADATA_KEY] = heating_meta
        state = YearState(year=2025, data=new_data, seed=42, metadata={})

        state = heating_step.execute(2025, state)

        log = state.data[DECISION_LOG_KEY]
        assert isinstance(log, tuple)
        assert len(log) == 2

        assert log[0].domain_name == "vehicle"
        assert log[0].taste_parameters == {"beta_cost": -0.01}
        assert log[0].alternative_ids == ("ev", "ice", "keep")

        assert log[1].domain_name == "heating"
        assert log[1].taste_parameters == {"beta_cost": -0.02}
        assert log[1].alternative_ids == ("hp", "gas", "keep_h")
