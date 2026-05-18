# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Subsidy-related custom variables for OpenFisca-France.

Story 29.1: Implements montant_subvention and eligible_subvention
as custom OpenFisca variables extending the base TaxBenefitSystem.

These variables provide subsidy eligibility and amount calculations
for households based on income thresholds.

Note: OpenFisca uses snake_case for class names (e.g., montant_subvention),
not PascalCase. This is required for the variable key to be correctly
registered in the TaxBenefitSystem.

Formula functions are defined as standalone functions (not methods) to match
OpenFisca's pattern. This allows OpenFisca to inspect __code__.co_argcount.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy import of OpenFisca Variable class
# Only import when this module is loaded by extension loader
try:
    from openfisca_core import periods
    from openfisca_core.variables import Variable
except ImportError:
    # OpenFisca not available - define placeholder
    Variable = object  # type: ignore
    periods = None  # type: ignore


# ============================================================================
# Formula functions (standalone, not methods)
# ============================================================================


def _montant_subvention_formula(
    menage: Any,
    period: Any,
    parameters: Any,
) -> Any:
    """Calculate subsidy amount for each household."""
    import numpy as np

    # Get household disposable income
    try:
        income = menage("revenu_disponible", period)
    except Exception:
        # If revenu_disponible not available, use zero (no subsidy)
        income = np.zeros(menage.count, dtype=float)

    # Income cap for eligibility (EUR)
    income_cap = 20000.0

    # Subsidy amount for eligible households (EUR)
    subsidy_amount = 150.0

    # Calculate eligibility: income < cap
    is_eligible = income < income_cap

    # Return subsidy amount for eligible households, 0 otherwise
    return np.where(is_eligible, subsidy_amount, 0.0)


def _eligible_subvention_formula(
    menage: Any,
    period: Any,
    parameters: Any,
) -> Any:
    """Determine subsidy eligibility for each household."""
    import numpy as np

    # Get household disposable income
    try:
        income = menage("revenu_disponible", period)
    except Exception:
        # If revenu_disponible not available, no one is eligible
        return np.zeros(menage.count, dtype=bool)

    # Income cap for eligibility (EUR)
    income_cap = 20000.0

    # Eligible if income < cap
    return income < income_cap


# ============================================================================
# Variable classes
# ============================================================================


class montant_subvention(Variable):  # type: ignore[misc]
    """Montant de la subvention pour les ménages éligibles.

    Story 29.1: Custom variable extending OpenFisca-France.
    Provides subsidy amount based on income eligibility.

    First-slice implementation: Fixed amount (150 EUR) for households
    with disposable income below 20000 EUR.
    """

    value_type = float
    entity = "menage"  # Will be replaced with actual entity during registration
    definition_period = periods.YEAR if periods else "year"
    label = "Montant de la subvention"
    formula = _montant_subvention_formula


class eligible_subvention(Variable):  # type: ignore[misc]
    """Éligibilité à la subvention pour les ménages.

    Story 29.1: Custom variable extending OpenFisca-France.
    Returns True if household meets income eligibility criteria.

    First-slice implementation: Income cap only (20000 EUR).
    Future enhancement: Add category eligibility.
    """

    value_type = bool
    entity = "menage"  # Will be replaced with actual entity during registration
    definition_period = periods.YEAR if periods else "year"
    label = "Éligibilité à la subvention"
    formula = _eligible_subvention_formula


__all__ = [
    "montant_subvention",
    "eligible_subvention",
]
