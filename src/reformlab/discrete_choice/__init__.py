"""Discrete choice subsystem for household decision modeling.

Implements population expansion and cost matrix computation for
evaluating household alternatives via the ComputationAdapter. The
DiscreteChoiceStep implements the OrchestratorStep protocol and
integrates with the orchestrator pipeline without modifying existing
interfaces.

Story 14-1: DiscreteChoiceStep with population expansion pattern.

Public API:
- DiscreteChoiceStep: OrchestratorStep for discrete choice evaluation
- DecisionDomain: Protocol for decision domains (vehicle, heating, etc.)
- Alternative, ChoiceSet, CostMatrix, ExpansionResult: Core value types
- expand_population: Population expansion function
- reshape_to_cost_matrix: Cost matrix reshape function
- DiscreteChoiceError, ExpansionError, ReshapeError: Error hierarchy
- State keys: DISCRETE_CHOICE_COST_MATRIX_KEY, etc.
"""

from __future__ import annotations

from reformlab.discrete_choice.domain import DecisionDomain
from reformlab.discrete_choice.errors import (
    DiscreteChoiceError,
    ExpansionError,
    ReshapeError,
)
from reformlab.discrete_choice.expansion import (
    TRACKING_COL_ALTERNATIVE_ID,
    TRACKING_COL_ORIGINAL_INDEX,
    expand_population,
)
from reformlab.discrete_choice.reshape import reshape_to_cost_matrix
from reformlab.discrete_choice.step import (
    DISCRETE_CHOICE_COST_MATRIX_KEY,
    DISCRETE_CHOICE_EXPANSION_KEY,
    DISCRETE_CHOICE_METADATA_KEY,
    DiscreteChoiceStep,
)
from reformlab.discrete_choice.types import (
    Alternative,
    ChoiceSet,
    CostMatrix,
    ExpansionResult,
)

__all__ = [
    "Alternative",
    "ChoiceSet",
    "CostMatrix",
    "DecisionDomain",
    "DISCRETE_CHOICE_COST_MATRIX_KEY",
    "DISCRETE_CHOICE_EXPANSION_KEY",
    "DISCRETE_CHOICE_METADATA_KEY",
    "DiscreteChoiceError",
    "DiscreteChoiceStep",
    "expand_population",
    "ExpansionError",
    "ExpansionResult",
    "reshape_to_cost_matrix",
    "ReshapeError",
    "TRACKING_COL_ALTERNATIVE_ID",
    "TRACKING_COL_ORIGINAL_INDEX",
]
