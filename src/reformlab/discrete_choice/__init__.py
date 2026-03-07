"""Discrete choice subsystem for household decision modeling.

Implements population expansion, cost matrix computation, and
conditional logit choice modeling for evaluating household alternatives.
DiscreteChoiceStep and LogitChoiceStep implement the OrchestratorStep
protocol and integrate with the orchestrator pipeline.

Story 14-1: DiscreteChoiceStep with population expansion pattern.
Story 14-2: Conditional logit model with seed-controlled draws.
Story 14-3: Vehicle investment decision domain and state update step.

Public API:
- DiscreteChoiceStep: OrchestratorStep for discrete choice evaluation
- LogitChoiceStep: OrchestratorStep for logit probability + draws
- VehicleInvestmentDomain: Vehicle decision domain (DecisionDomain protocol)
- VehicleStateUpdateStep: OrchestratorStep for post-logit state updates
- VehicleDomainConfig: Configuration for vehicle domain
- default_vehicle_domain_config: Factory for French market defaults
- apply_choices_to_population: Per-household attribute application
- DecisionDomain: Protocol for decision domains (vehicle, heating, etc.)
- Alternative, ChoiceSet, CostMatrix, ExpansionResult: Core value types
- TasteParameters, ChoiceResult: Logit model types
- compute_utilities, compute_probabilities, draw_choices: Pure logit functions
- expand_population: Population expansion function
- reshape_to_cost_matrix: Cost matrix reshape function
- DiscreteChoiceError, ExpansionError, ReshapeError, LogitError: Error hierarchy
- State keys: DISCRETE_CHOICE_COST_MATRIX_KEY, DISCRETE_CHOICE_RESULT_KEY, etc.
"""

from __future__ import annotations

from reformlab.discrete_choice.domain import DecisionDomain
from reformlab.discrete_choice.errors import (
    DiscreteChoiceError,
    ExpansionError,
    LogitError,
    ReshapeError,
)
from reformlab.discrete_choice.expansion import (
    TRACKING_COL_ALTERNATIVE_ID,
    TRACKING_COL_ORIGINAL_INDEX,
    expand_population,
)
from reformlab.discrete_choice.logit import (
    DISCRETE_CHOICE_RESULT_KEY,
    LogitChoiceStep,
    compute_probabilities,
    compute_utilities,
    draw_choices,
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
    ChoiceResult,
    ChoiceSet,
    CostMatrix,
    ExpansionResult,
    TasteParameters,
)
from reformlab.discrete_choice.vehicle import (
    VehicleDomainConfig,
    VehicleInvestmentDomain,
    VehicleStateUpdateStep,
    apply_choices_to_population,
    default_vehicle_domain_config,
)

__all__ = [
    "Alternative",
    "ChoiceResult",
    "ChoiceSet",
    "compute_probabilities",
    "compute_utilities",
    "CostMatrix",
    "DecisionDomain",
    "DISCRETE_CHOICE_COST_MATRIX_KEY",
    "DISCRETE_CHOICE_EXPANSION_KEY",
    "DISCRETE_CHOICE_METADATA_KEY",
    "DISCRETE_CHOICE_RESULT_KEY",
    "DiscreteChoiceError",
    "DiscreteChoiceStep",
    "draw_choices",
    "expand_population",
    "ExpansionError",
    "ExpansionResult",
    "LogitChoiceStep",
    "LogitError",
    "reshape_to_cost_matrix",
    "ReshapeError",
    "TasteParameters",
    "TRACKING_COL_ALTERNATIVE_ID",
    "TRACKING_COL_ORIGINAL_INDEX",
    "VehicleDomainConfig",
    "VehicleInvestmentDomain",
    "VehicleStateUpdateStep",
    "apply_choices_to_population",
    "default_vehicle_domain_config",
]
