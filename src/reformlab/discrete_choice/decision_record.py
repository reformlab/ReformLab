"""Decision record types and step for discrete choice audit trail.

Captures per-domain choice snapshots (chosen alternatives, probabilities,
utilities, taste parameters) into the decision log before the next domain's
DiscreteChoiceStep overwrites shared state keys. This solves the multi-domain
metadata overwrite problem where sequential domain execution (vehicle → heating)
loses earlier domain results.

Types:
- DecisionRecord: Frozen dataclass capturing one domain's choice snapshot
- DecisionRecordStep: OrchestratorStep that snapshots ChoiceResult into log

Story 14-6: Extend Panel Output and Manifests with Decision Records (FR50/FR51).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.logit import DISCRETE_CHOICE_RESULT_KEY
from reformlab.discrete_choice.step import DISCRETE_CHOICE_METADATA_KEY

if TYPE_CHECKING:
    import pyarrow as pa

    from reformlab.orchestrator.types import YearState

logger = logging.getLogger(__name__)

# ============================================================================
# Constants
# ============================================================================

DECISION_LOG_KEY = "discrete_choice_decision_log"

# ============================================================================
# DecisionRecord type — AC-1
# ============================================================================


@dataclass(frozen=True)
class DecisionRecord:
    """Snapshot of one domain's discrete choice results for audit trail.

    Captures the chosen alternatives, full probability and utility tables,
    taste parameters, and eligibility summary for a single decision domain
    within one year. Stored as a tuple in YearState.data[DECISION_LOG_KEY].

    Fields:
        domain_name: Domain identifier (e.g., "vehicle", "heating").
        chosen: N-element string array of chosen alternative IDs.
        probabilities: N×M table, one column per alternative.
        utilities: N×M table, one column per alternative.
        alternative_ids: Ordered tuple of alternative IDs.
        seed: RNG seed used for this domain's choice draw, or None.
        taste_parameters: Taste coefficients (e.g., {"beta_cost": -0.01}).
            Treat as logically immutable after construction.
        eligibility_summary: Eligibility counts or None if no filtering.
            Treat as logically immutable after construction.
    """

    domain_name: str
    chosen: pa.Array
    probabilities: pa.Table
    utilities: pa.Table
    alternative_ids: tuple[str, ...]
    seed: int | None
    taste_parameters: dict[str, float]
    eligibility_summary: dict[str, int] | None


# ============================================================================
# DecisionRecordStep — AC-2
# ============================================================================


class DecisionRecordStep:
    """Orchestrator step that snapshots ChoiceResult into the decision log.

    Reads the current ChoiceResult and domain metadata from state, creates
    a DecisionRecord, and appends it to the decision log tuple. Safe to
    always include in a pipeline — passes through when no ChoiceResult exists.

    Implements the OrchestratorStep protocol.

    Story 14-6, AC-2.
    """

    __slots__ = ("_name", "_depends_on", "_description")

    def __init__(
        self,
        name: str = "decision_record",
        depends_on: tuple[str, ...] = ("vehicle_state_update",),
        description: str | None = None,
    ) -> None:
        self._name = name
        self._depends_on = depends_on
        self._description = (
            description
            or "Snapshot discrete choice result into decision log"
        )

    @property
    def name(self) -> str:
        """Unique identifier for this step."""
        return self._name

    @property
    def depends_on(self) -> tuple[str, ...]:
        """Names of steps this step depends on."""
        return self._depends_on

    @property
    def description(self) -> str:
        """Human-readable description of the step."""
        return self._description

    def execute(self, year: int, state: YearState) -> YearState:
        """Snapshot current ChoiceResult and metadata into decision log.

        If no ChoiceResult exists in state, returns state unchanged
        (pass-through). This makes it safe to always include in a pipeline.

        Args:
            year: Current simulation year.
            state: Current year state.

        Returns:
            New YearState with DecisionRecord appended to decision log.

        Raises:
            DiscreteChoiceError: If metadata is not a dict or existing log
                is not a tuple.
        """
        from reformlab.discrete_choice.types import ChoiceResult as _ChoiceResult

        # Pass-through if no ChoiceResult in state
        choice_result = state.data.get(DISCRETE_CHOICE_RESULT_KEY)
        if not isinstance(choice_result, _ChoiceResult):
            return state

        # Read metadata
        metadata: Any = state.data.get(DISCRETE_CHOICE_METADATA_KEY, {})
        if not isinstance(metadata, dict):
            raise DiscreteChoiceError(
                f"Expected dict for key '{DISCRETE_CHOICE_METADATA_KEY}', "
                f"got {type(metadata).__name__}",
                year=year,
                step_name=self._name,
            )

        domain_name: str = metadata.get("domain_name", "unknown")

        # Extract taste parameters
        taste_params: dict[str, float] = {}
        beta = metadata.get("beta_cost")
        if isinstance(beta, (int, float)):
            taste_params["beta_cost"] = float(beta)

        # Extract eligibility summary if present
        eligibility_summary: dict[str, int] | None = None
        n_total = metadata.get("eligibility_n_total")
        if isinstance(n_total, int):
            eligibility_summary = {
                "n_total": n_total,
                "n_eligible": metadata.get("eligibility_n_eligible", n_total),
                "n_ineligible": metadata.get("eligibility_n_ineligible", 0),
            }

        record = DecisionRecord(
            domain_name=domain_name,
            chosen=choice_result.chosen,
            probabilities=choice_result.probabilities,
            utilities=choice_result.utilities,
            alternative_ids=choice_result.alternative_ids,
            seed=choice_result.seed,
            taste_parameters=taste_params,
            eligibility_summary=eligibility_summary,
        )

        # Append to existing log
        existing_log = state.data.get(DECISION_LOG_KEY, ())
        if not isinstance(existing_log, tuple):
            raise DiscreteChoiceError(
                f"Expected tuple for key '{DECISION_LOG_KEY}', "
                f"got {type(existing_log).__name__}",
                year=year,
                step_name=self._name,
            )
        new_log = (*existing_log, record)

        new_data = dict(state.data)
        new_data[DECISION_LOG_KEY] = new_log

        logger.info(
            "year=%d step_name=%s domain_name=%s n_households=%d "
            "n_alternatives=%d event=decision_recorded",
            year,
            self._name,
            domain_name,
            len(choice_result.chosen),
            len(choice_result.alternative_ids),
        )

        return replace(state, data=new_data)
