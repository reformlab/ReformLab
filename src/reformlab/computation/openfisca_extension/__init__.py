# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""OpenFisca-France custom variable extension for ReformLab.

This module extends OpenFisca-France with custom variables needed for
ReformLab's subsidy, vehicle malus, and energy poverty aid scenarios.

Story 29.1: Custom variables (montant_subvention, eligible_subvention,
malus_ecologique, aide_energie) are registered here to extend the base
TaxBenefitSystem.

All imports are lazy since openfisca-core is an optional dependency.
"""

from __future__ import annotations

# Extension loader entrypoint — called by OpenFiscaApiAdapter
from reformlab.computation.openfisca_extension.extension import (
    EXTENSION_NAME,
    EXTENSION_VERSION,
    load_extension,
)

__all__ = [
    "EXTENSION_NAME",
    "EXTENSION_VERSION",
    "load_extension",
]
