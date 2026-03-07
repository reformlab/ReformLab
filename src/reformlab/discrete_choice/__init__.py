"""Discrete choice subsystem for household decision modeling.

Implements population expansion, cost matrix computation, and
conditional logit choice modeling for evaluating household alternatives.
DiscreteChoiceStep and LogitChoiceStep implement the OrchestratorStep
protocol and integrate with the orchestrator pipeline.

Story 14-1: DiscreteChoiceStep with population expansion pattern.
Story 14-2: Conditional logit model with seed-controlled draws.
Story 14-3: Vehicle investment decision domain and state update step.
Story 14-4: Heating system investment decision domain and state update step.
Story 14-5: Eligibility filtering for performance optimization.
"""

from __future__ import annotations

from reformlab.discrete_choice.domain import DecisionDomain
from reformlab.discrete_choice.domain_utils import (
    apply_choices_to_population,
    create_vintage_entries,
    infer_pa_type,
)
from reformlab.discrete_choice.eligibility import (
    DISCRETE_CHOICE_ELIGIBILITY_KEY,
    EligibilityFilter,
    EligibilityInfo,
    EligibilityMergeStep,
    EligibilityRule,
    evaluate_eligibility,
    filter_population_by_eligibility,
)
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
from reformlab.discrete_choice.heating import (
    HeatingDomainConfig,
    HeatingInvestmentDomain,
    HeatingStateUpdateStep,
    default_heating_domain_config,
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
    default_vehicle_domain_config,
)

__all__ = [
    "Alternative",
    "ChoiceResult",
    "ChoiceSet",
    "apply_choices_to_population",
    "compute_probabilities",
    "compute_utilities",
    "CostMatrix",
    "create_vintage_entries",
    "DecisionDomain",
    "default_heating_domain_config",
    "default_vehicle_domain_config",
    "DISCRETE_CHOICE_COST_MATRIX_KEY",
    "DISCRETE_CHOICE_ELIGIBILITY_KEY",
    "DISCRETE_CHOICE_EXPANSION_KEY",
    "DISCRETE_CHOICE_METADATA_KEY",
    "DISCRETE_CHOICE_RESULT_KEY",
    "DiscreteChoiceError",
    "DiscreteChoiceStep",
    "draw_choices",
    "EligibilityFilter",
    "EligibilityInfo",
    "EligibilityMergeStep",
    "EligibilityRule",
    "evaluate_eligibility",
    "expand_population",
    "ExpansionError",
    "ExpansionResult",
    "filter_population_by_eligibility",
    "HeatingDomainConfig",
    "HeatingInvestmentDomain",
    "HeatingStateUpdateStep",
    "infer_pa_type",
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
]
