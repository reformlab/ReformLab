# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Vehicle malus custom variable for OpenFisca-France.

Story 29.1: Implements malus_ecologique as a custom OpenFisca variable
extending the base TaxBenefitSystem.

Calculates malus (penalty) for households with vehicle emissions above
the threshold: max(0, emissions - threshold) * rate_per_gkm.

First-slice implementation: Uses reformlab_malus_emissions input variable
injected via PopulationData. If not provided, malus is 0.
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


def _malus_ecologique_formula(
    menage: Any,
    period: Any,
    parameters: Any,
) -> Any:
    """Calculate vehicle malus for each household."""
    import numpy as np

    # Try to get vehicle emissions from input variable
    # This needs to be injected via PopulationData as reformlab_malus_emissions
    try:
        emissions = menage("reformlab_malus_emissions", period)
    except Exception:
        # If emissions not available, no malus applies
        return np.zeros(menage.count, dtype=float)

    # Emission threshold (gCO2/km)
    threshold = 118.0

    # Malus rate per gCO2/km above threshold (EUR)
    rate = 50.0

    # Calculate malus: max(0, emissions - threshold) * rate
    excess = emissions - threshold
    excess_clamped = np.maximum(excess, 0)
    malus = excess_clamped * rate

    return malus


# ============================================================================
# Variable class
# ============================================================================


class malus_ecologique(Variable):  # type: ignore[misc]
    """Malus écologique pour les véhicules à forte émission.

    Story 29.1: Custom variable extending OpenFisca-France.
    Calculates penalty based on vehicle CO2 emissions above threshold.

    Formula: max(0, emissions - threshold) * rate
    - threshold: 118 gCO2/km
    - rate: 50 EUR per gCO2/km above threshold

    Uses reformlab_malus_emissions input variable if available,
    otherwise returns 0 (no malus).
    """

    value_type = float
    entity = "menage"  # Will be replaced with actual entity during registration
    definition_period = periods.YEAR if periods else "year"
    label = "Malus écologique pour véhicule"
    formula = _malus_ecologique_formula


__all__ = [
    "malus_ecologique",
]
