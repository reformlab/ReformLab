# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""OpenFisca-France extension loader for ReformLab custom variables.

This module provides the load_extension() function that registers
ReformLab's custom variables with an OpenFisca-France TaxBenefitSystem.

Story 29.1: Extension loading with idempotency, error handling, and
version tracking for reproducibility.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)

EXTENSION_NAME = "reformlab-openfisca-extend-fr"
EXTENSION_VERSION = "1.0.0"

# Custom variable names for manifest tracking
CUSTOM_VARIABLES = (
    "montant_subvention",
    "eligible_subvention",
    "malus_ecologique",
    "aide_energie",
)


def _get_menage_entity(tbs: Any) -> Any:
    """Get the menage (household) entity from the TaxBenefitSystem.

    Args:
        tbs: OpenFisca-France TaxBenefitSystem instance.

    Returns:
        The menage GroupEntity instance.

    Raises:
        RuntimeError: If menage entity not found.
    """
    for entity in tbs.entities:
        if entity.key == "menage":
            return entity

    raise RuntimeError(
        f"Menage entity not found in {tbs}. "
        "This may indicate an incompatible OpenFisca-France version."
    )


def _create_variable_with_entity(
    base_class: type,
    entity: Any,
) -> type:
    """Create a variable class with the entity reference set.

    OpenFisca requires the entity attribute to be an actual Entity instance,
    not a string. This function creates a new class with the entity injected.

    Args:
        base_class: The base Variable class with entity as a placeholder.
        entity: The Entity instance to inject.

    Returns:
        A new Variable class with entity set to the Entity instance.
    """
    class_name = base_class.__name__
    base_dict = dict(base_class.__dict__)

    # Remove unwanted attributes
    for key in ("__dict__", "__weakref__", "__module__", "__doc__"):
        base_dict.pop(key, None)

    # Set the entity to the actual Entity instance
    base_dict["entity"] = entity

    # Create new class dynamically
    return type(class_name, (base_class,), base_dict)


def load_extension(tbs: Any) -> None:
    """Load ReformLab custom variables into the TaxBenefitSystem.

    Registers the four custom variables (subsidy, vehicle malus,
    energy aid) with the provided TaxBenefitSystem instance.

    Idempotent: safe to call multiple times — checks if variables
    are already registered before adding them.

    Args:
        tbs: OpenFisca-France TaxBenefitSystem instance to extend.

    Raises:
        ImportError: If OpenFisca-France is not installed.
        RuntimeError: If variable registration fails.

    Example:
        >>> from openfisca_france import CountryTaxBenefitSystem
        >>> from reformlab.computation.openfisca_extension import load_extension
        >>> tbs = CountryTaxBenefitSystem()
        >>> load_extension(tbs)
        >>> assert "montant_subvention" in tbs.variables
    """
    # Get the menage entity for injecting into variable classes
    menage_entity = _get_menage_entity(tbs)

    # Import our custom variable classes (with placeholder entity strings)
    from reformlab.computation.openfisca_extension.energy_variables import (
        aide_energie,
    )
    from reformlab.computation.openfisca_extension.subsidy_variables import (
        eligible_subvention,
        montant_subvention,
    )
    from reformlab.computation.openfisca_extension.vehicle_variables import (
        malus_ecologique,
    )

    # Create variable classes with actual entity reference
    variables_to_add = [
        _create_variable_with_entity(montant_subvention, menage_entity),
        _create_variable_with_entity(eligible_subvention, menage_entity),
        _create_variable_with_entity(malus_ecologique, menage_entity),
        _create_variable_with_entity(aide_energie, menage_entity),
    ]

    for var_class in variables_to_add:
        var_name = var_class.__name__
        # OpenFisca uses the class name as the variable key
        # Since we're using snake_case class names, this gives us the correct key
        var_key = var_name

        if var_key in tbs.variables:
            logger.debug(
                "extension=%s variable=%s event=already_registered skip=true",
                EXTENSION_NAME,
                var_key,
            )
            continue

        try:
            tbs.add_variable(var_class)
            logger.debug(
                "extension=%s variable=%s event=registered success=true",
                EXTENSION_NAME,
                var_key,
            )
        except Exception as exc:
            msg = (
                f"Failed to register variable '{var_key}' "
                f"with {EXTENSION_NAME} extension"
            )
            raise RuntimeError(msg) from exc

    logger.info(
        "extension=%s version=%s event=load_complete variables=%s",
        EXTENSION_NAME,
        EXTENSION_VERSION,
        CUSTOM_VARIABLES,
    )
