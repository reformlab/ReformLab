"""Tests for OrchestratorRunner discrete choice parameter capture.

Story 14-6: Extend Panel Output and Manifests with Decision Records.
AC-5: Manifest taste parameter capture in runner.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pyarrow as pa

from reformlab.discrete_choice.decision_record import (
    DecisionRecordStep,
)
from reformlab.discrete_choice.logit import DISCRETE_CHOICE_RESULT_KEY
from reformlab.discrete_choice.step import DISCRETE_CHOICE_METADATA_KEY
from reformlab.discrete_choice.types import ChoiceResult
from reformlab.orchestrator.runner import OrchestratorRunner
from reformlab.orchestrator.types import YearState

# ============================================================================
# Helpers
# ============================================================================


def _make_choice_result(n: int = 3) -> ChoiceResult:
    """Build a minimal ChoiceResult."""
    alt_ids = ("ev", "ice")
    return ChoiceResult(
        chosen=pa.array(["ev"] * n, type=pa.string()),
        probabilities=pa.table({aid: [0.5] * n for aid in alt_ids}),
        utilities=pa.table({aid: [-1.0] * n for aid in alt_ids}),
        alternative_ids=alt_ids,
        seed=42,
    )


def _decision_record_step(year: int, state: YearState) -> YearState:
    """Simulate a pipeline that creates a decision record."""
    step = DecisionRecordStep(name="decision_record", depends_on=())
    return step.execute(year, state)


def _setup_choice_state(year: int, state: YearState) -> YearState:
    """Inject ChoiceResult and metadata into state for decision recording."""
    new_data = dict(state.data)
    new_data[DISCRETE_CHOICE_RESULT_KEY] = _make_choice_result()
    new_data[DISCRETE_CHOICE_METADATA_KEY] = {
        "domain_name": "vehicle",
        "beta_cost": -0.01,
        "choice_seed": 42,
    }
    return replace(state, data=new_data)


# ============================================================================
# TestRunnerDiscreteChoiceCapture — AC-5
# ============================================================================


class TestRunnerDiscreteChoiceCapture:
    """AC-5: discrete_choice_parameters appears in WorkflowResult metadata."""

    def test_discrete_choice_parameters_in_metadata(self) -> None:
        """Runner captures discrete choice parameters in workflow metadata."""
        runner = OrchestratorRunner(
            step_pipeline=(_setup_choice_state, _decision_record_step),
            seed=42,
        )

        request: dict[str, Any] = {
            "run_config": {
                "start_year": 2025,
                "projection_years": 1,
            },
        }

        result = runner.run(request)

        assert result.success
        assert "discrete_choice_parameters" in result.metadata
        dc_params = result.metadata["discrete_choice_parameters"]
        assert len(dc_params) == 1
        assert dc_params[0]["domain_name"] == "vehicle"
        assert dc_params[0]["beta_cost"] == -0.01

    def test_no_discrete_choice_parameters_when_absent(self) -> None:
        """Runner omits discrete_choice_parameters when no decision log."""
        runner = OrchestratorRunner(seed=42)

        request: dict[str, Any] = {
            "run_config": {
                "start_year": 2025,
                "projection_years": 1,
            },
        }

        result = runner.run(request)

        assert result.success
        assert "discrete_choice_parameters" not in result.metadata
