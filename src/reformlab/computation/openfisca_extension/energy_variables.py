# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Energy poverty aid custom variable for OpenFisca-France.

Story 29.1: Implements aide_energie as a custom OpenFisca variable
extending the base TaxBenefitSystem.

PM Decision: aide_energie aliases to OpenFisca-France's existing
cheque_energie variable, which provides functionally equivalent
energy poverty aid calculations.

This approach leverages the existing OpenFisca-France implementation
rather than computing fresh, maintaining consistency with French
tax-benefit conventions.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Lazy import of OpenFisca Variable class
try:
    from openfisca_core import periods
    from openfisca_core.variables import Variable
except ImportError:
    Variable = object  # type: ignore
    periods = None  # type: ignore


# ============================================================================
# Formula function (standalone, not method)
# ============================================================================


def _aide_energie_formula(
    menage: Any,
    period: Any,
    parameters: Any,
) -> Any:
    """Get energy aid amount from existing cheque_energie."""
    import numpy as np

    # Delegate to OpenFisca-France's existing cheque_energie variable
    try:
        return menage("cheque_energie", period)
    except Exception as exc:
        # Log error but return zeros to avoid breaking the simulation
        household_count = len(menage.household_index)
        logger.warning(
            "event=cheque_energie_fallback error=%s households=%d",
            exc,
            household_count,
        )
        return np.zeros(household_count, dtype=float)


# ============================================================================
# Variable class
# ============================================================================


class aide_energie(Variable):  # type: ignore[misc]
    """Aide énergétique pour les ménages à faible revenu.

    Story 29.1: Custom variable extending OpenFisca-France.
    Aliases to OpenFisca-France's existing cheque_energie variable.

    PM Decision: Leverages existing OpenFisca-France implementation
    for cheque_energie rather than computing fresh, maintaining
    consistency with French tax-benefit conventions.

    The cheque_energie variable (value_type=float, entity=menage,
    definition_period=year) provides functionally equivalent
    energy poverty aid calculations.
    """

    value_type = float
    entity = "menage"  # Will be replaced with actual entity during registration
    definition_period = periods.YEAR if periods else "year"
    label = "Aide énergétique (chèque énergie)"
    formula = _aide_energie_formula


__all__ = [
    "aide_energie",
]
