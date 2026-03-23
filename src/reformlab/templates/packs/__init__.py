# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Template pack discovery and loading utilities.

This module provides functions to discover and load prebuilt scenario templates
from template packs shipped with ReformLab.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from reformlab.templates.loader import load_scenario_template

if TYPE_CHECKING:
    from reformlab.templates.schema import BaselineScenario

# Root directory for template packs
_PACKS_DIR = Path(__file__).parent


def list_carbon_tax_templates() -> list[str]:
    """List available carbon tax template variant names.

    Returns:
        List of variant names (without .yaml extension) that can be passed
        to load_carbon_tax_template().

    Example:
        >>> variants = list_carbon_tax_templates()
        >>> print(variants)
        ['carbon-tax-flat-lump-sum-dividend', 'carbon-tax-flat-no-redistribution', ...]
    """
    carbon_tax_dir = _PACKS_DIR / "carbon_tax"
    if not carbon_tax_dir.exists():
        return []

    variants = []
    for yaml_file in sorted(carbon_tax_dir.glob("*.yaml")):
        variants.append(yaml_file.stem)
    return variants


def load_carbon_tax_template(variant_name: str) -> BaselineScenario:
    """Load a carbon tax template by variant name.

    Args:
        variant_name: The variant name (e.g., "carbon-tax-flat-lump-sum-dividend").
            Use list_carbon_tax_templates() to see available variants.

    Returns:
        BaselineScenario loaded from the template YAML file.

    Raises:
        FileNotFoundError: If the variant does not exist.
        ScenarioError: If the template file is invalid.

    Example:
        >>> template = load_carbon_tax_template("carbon-tax-flat-lump-sum-dividend")
        >>> print(template.name)
        'Carbon Tax - Flat Rate with Lump-Sum Dividend'
    """
    carbon_tax_dir = _PACKS_DIR / "carbon_tax"
    template_path = carbon_tax_dir / f"{variant_name}.yaml"

    if not template_path.exists():
        available = list_carbon_tax_templates()
        raise FileNotFoundError(
            f"Carbon tax template '{variant_name}' not found. "
            f"Available variants: {available}"
        )

    scenario = load_scenario_template(template_path)

    # Type narrowing - carbon tax templates are always BaselineScenario
    from reformlab.templates.schema import BaselineScenario

    if not isinstance(scenario, BaselineScenario):
        raise TypeError(
            f"Expected BaselineScenario, got {type(scenario).__name__}. "
            "Carbon tax pack templates must be baseline scenarios."
        )

    return scenario


def get_carbon_tax_pack_dir() -> Path:
    """Return the path to the carbon tax template pack directory.

    Returns:
        Path to the carbon_tax pack directory.
    """
    return _PACKS_DIR / "carbon_tax"


# ---------------------------------------------------------------------------
# Subsidy template pack
# ---------------------------------------------------------------------------


def list_subsidy_templates() -> list[str]:
    """List available subsidy template variant names.

    Returns:
        List of variant names (without .yaml extension) that can be passed
        to load_subsidy_template().

    Example:
        >>> variants = list_subsidy_templates()
        >>> print(variants)
        ['subsidy-energy-retrofit']
    """
    subsidy_dir = _PACKS_DIR / "subsidy"
    if not subsidy_dir.exists():
        return []

    variants = []
    for yaml_file in sorted(subsidy_dir.glob("*.yaml")):
        variants.append(yaml_file.stem)
    return variants


def load_subsidy_template(variant_name: str) -> BaselineScenario:
    """Load a subsidy template by variant name.

    Args:
        variant_name: The variant name (e.g., "subsidy-energy-retrofit").
            Use list_subsidy_templates() to see available variants.

    Returns:
        BaselineScenario loaded from the template YAML file.

    Raises:
        FileNotFoundError: If the variant does not exist.
        ScenarioError: If the template file is invalid.

    Example:
        >>> template = load_subsidy_template("subsidy-energy-retrofit")
        >>> print(template.name)
        'Subsidy - Home Energy Retrofit'
    """
    subsidy_dir = _PACKS_DIR / "subsidy"
    template_path = subsidy_dir / f"{variant_name}.yaml"

    if not template_path.exists():
        available = list_subsidy_templates()
        raise FileNotFoundError(
            f"Subsidy template '{variant_name}' not found. "
            f"Available variants: {available}"
        )

    scenario = load_scenario_template(template_path)

    from reformlab.templates.schema import BaselineScenario

    if not isinstance(scenario, BaselineScenario):
        raise TypeError(
            f"Expected BaselineScenario, got {type(scenario).__name__}. "
            "Subsidy pack templates must be baseline scenarios."
        )

    return scenario


def get_subsidy_pack_dir() -> Path:
    """Return the path to the subsidy template pack directory.

    Returns:
        Path to the subsidy pack directory.
    """
    return _PACKS_DIR / "subsidy"


# ---------------------------------------------------------------------------
# Rebate template pack
# ---------------------------------------------------------------------------


def list_rebate_templates() -> list[str]:
    """List available rebate template variant names.

    Returns:
        List of variant names (without .yaml extension) that can be passed
        to load_rebate_template().

    Example:
        >>> variants = list_rebate_templates()
        >>> print(variants)
        ['rebate-progressive-income']
    """
    rebate_dir = _PACKS_DIR / "rebate"
    if not rebate_dir.exists():
        return []

    variants = []
    for yaml_file in sorted(rebate_dir.glob("*.yaml")):
        variants.append(yaml_file.stem)
    return variants


def load_rebate_template(variant_name: str) -> BaselineScenario:
    """Load a rebate template by variant name.

    Args:
        variant_name: The variant name (e.g., "rebate-progressive-income").
            Use list_rebate_templates() to see available variants.

    Returns:
        BaselineScenario loaded from the template YAML file.

    Raises:
        FileNotFoundError: If the variant does not exist.
        ScenarioError: If the template file is invalid.

    Example:
        >>> template = load_rebate_template("rebate-progressive-income")
        >>> print(template.name)
        'Rebate - Progressive Income Dividend'
    """
    rebate_dir = _PACKS_DIR / "rebate"
    template_path = rebate_dir / f"{variant_name}.yaml"

    if not template_path.exists():
        available = list_rebate_templates()
        raise FileNotFoundError(
            f"Rebate template '{variant_name}' not found. "
            f"Available variants: {available}"
        )

    scenario = load_scenario_template(template_path)

    from reformlab.templates.schema import BaselineScenario

    if not isinstance(scenario, BaselineScenario):
        raise TypeError(
            f"Expected BaselineScenario, got {type(scenario).__name__}. "
            "Rebate pack templates must be baseline scenarios."
        )

    return scenario


def get_rebate_pack_dir() -> Path:
    """Return the path to the rebate template pack directory.

    Returns:
        Path to the rebate pack directory.
    """
    return _PACKS_DIR / "rebate"


# ---------------------------------------------------------------------------
# Feebate template pack
# ---------------------------------------------------------------------------


def list_feebate_templates() -> list[str]:
    """List available feebate template variant names.

    Returns:
        List of variant names (without .yaml extension) that can be passed
        to load_feebate_template().

    Example:
        >>> variants = list_feebate_templates()
        >>> print(variants)
        ['feebate-vehicle-emissions']
    """
    feebate_dir = _PACKS_DIR / "feebate"
    if not feebate_dir.exists():
        return []

    variants = []
    for yaml_file in sorted(feebate_dir.glob("*.yaml")):
        variants.append(yaml_file.stem)
    return variants


def load_feebate_template(variant_name: str) -> BaselineScenario:
    """Load a feebate template by variant name.

    Args:
        variant_name: The variant name (e.g., "feebate-vehicle-emissions").
            Use list_feebate_templates() to see available variants.

    Returns:
        BaselineScenario loaded from the template YAML file.

    Raises:
        FileNotFoundError: If the variant does not exist.
        ScenarioError: If the template file is invalid.

    Example:
        >>> template = load_feebate_template("feebate-vehicle-emissions")
        >>> print(template.name)
        'Feebate - Vehicle Emissions'
    """
    feebate_dir = _PACKS_DIR / "feebate"
    template_path = feebate_dir / f"{variant_name}.yaml"

    if not template_path.exists():
        available = list_feebate_templates()
        raise FileNotFoundError(
            f"Feebate template '{variant_name}' not found. "
            f"Available variants: {available}"
        )

    scenario = load_scenario_template(template_path)

    from reformlab.templates.schema import BaselineScenario

    if not isinstance(scenario, BaselineScenario):
        raise TypeError(
            f"Expected BaselineScenario, got {type(scenario).__name__}. "
            "Feebate pack templates must be baseline scenarios."
        )

    return scenario


def get_feebate_pack_dir() -> Path:
    """Return the path to the feebate template pack directory.

    Returns:
        Path to the feebate pack directory.
    """
    return _PACKS_DIR / "feebate"


# ---------------------------------------------------------------------------
# Vehicle malus template pack
# ---------------------------------------------------------------------------


def list_vehicle_malus_templates() -> list[str]:
    """List available vehicle malus template variant names.

    Returns:
        List of variant names (without .yaml extension) that can be passed
        to load_vehicle_malus_template().
    """
    vehicle_malus_dir = _PACKS_DIR / "vehicle_malus"
    if not vehicle_malus_dir.exists():
        return []

    variants = []
    for yaml_file in sorted(vehicle_malus_dir.glob("*.yaml")):
        variants.append(yaml_file.stem)
    return variants


def load_vehicle_malus_template(variant_name: str) -> BaselineScenario:
    """Load a vehicle malus template by variant name.

    Args:
        variant_name: The variant name (e.g., "vehicle-malus-french-2026").
            Use list_vehicle_malus_templates() to see available variants.

    Returns:
        BaselineScenario loaded from the template YAML file.

    Raises:
        FileNotFoundError: If the variant does not exist.
        ScenarioError: If the template file is invalid.
    """
    # Ensure vehicle_malus custom type is registered before loading YAML
    import reformlab.templates.vehicle_malus  # noqa: F401

    vehicle_malus_dir = _PACKS_DIR / "vehicle_malus"
    template_path = vehicle_malus_dir / f"{variant_name}.yaml"

    if not template_path.exists():
        available = list_vehicle_malus_templates()
        raise FileNotFoundError(
            f"Vehicle malus template '{variant_name}' not found. "
            f"Available variants: {available}"
        )

    scenario = load_scenario_template(template_path)

    from reformlab.templates.schema import BaselineScenario

    if not isinstance(scenario, BaselineScenario):
        raise TypeError(
            f"Expected BaselineScenario, got {type(scenario).__name__}. "
            "Vehicle malus pack templates must be baseline scenarios."
        )

    return scenario


def get_vehicle_malus_pack_dir() -> Path:
    """Return the path to the vehicle malus template pack directory.

    Returns:
        Path to the vehicle_malus pack directory.
    """
    return _PACKS_DIR / "vehicle_malus"


# ---------------------------------------------------------------------------
# Energy poverty aid template pack
# ---------------------------------------------------------------------------


def list_energy_poverty_aid_templates() -> list[str]:
    """List available energy poverty aid template variant names.

    Returns:
        List of variant names (without .yaml extension) that can be passed
        to load_energy_poverty_aid_template().
    """
    energy_poverty_aid_dir = _PACKS_DIR / "energy_poverty_aid"
    if not energy_poverty_aid_dir.exists():
        return []

    variants = []
    for yaml_file in sorted(energy_poverty_aid_dir.glob("*.yaml")):
        variants.append(yaml_file.stem)
    return variants


def load_energy_poverty_aid_template(variant_name: str) -> BaselineScenario:
    """Load an energy poverty aid template by variant name.

    Args:
        variant_name: The variant name (e.g., "energy-poverty-cheque-energie").
            Use list_energy_poverty_aid_templates() to see available variants.

    Returns:
        BaselineScenario loaded from the template YAML file.

    Raises:
        FileNotFoundError: If the variant does not exist.
        ScenarioError: If the template file is invalid.
    """
    # Ensure energy_poverty_aid custom type is registered before loading YAML
    import reformlab.templates.energy_poverty_aid  # noqa: F401

    energy_poverty_aid_dir = _PACKS_DIR / "energy_poverty_aid"
    template_path = energy_poverty_aid_dir / f"{variant_name}.yaml"

    if not template_path.exists():
        available = list_energy_poverty_aid_templates()
        raise FileNotFoundError(
            f"Energy poverty aid template '{variant_name}' not found. "
            f"Available variants: {available}"
        )

    scenario = load_scenario_template(template_path)

    from reformlab.templates.schema import BaselineScenario

    if not isinstance(scenario, BaselineScenario):
        raise TypeError(
            f"Expected BaselineScenario, got {type(scenario).__name__}. "
            "Energy poverty aid pack templates must be baseline scenarios."
        )

    return scenario


def get_energy_poverty_aid_pack_dir() -> Path:
    """Return the path to the energy poverty aid template pack directory.

    Returns:
        Path to the energy_poverty_aid pack directory.
    """
    return _PACKS_DIR / "energy_poverty_aid"


__all__ = [
    # Carbon tax
    "get_carbon_tax_pack_dir",
    "list_carbon_tax_templates",
    "load_carbon_tax_template",
    # Subsidy
    "get_subsidy_pack_dir",
    "list_subsidy_templates",
    "load_subsidy_template",
    # Rebate
    "get_rebate_pack_dir",
    "list_rebate_templates",
    "load_rebate_template",
    # Feebate
    "get_feebate_pack_dir",
    "list_feebate_templates",
    "load_feebate_template",
    # Vehicle malus
    "get_vehicle_malus_pack_dir",
    "list_vehicle_malus_templates",
    "load_vehicle_malus_template",
    # Energy poverty aid
    "get_energy_poverty_aid_pack_dir",
    "list_energy_poverty_aid_templates",
    "load_energy_poverty_aid_template",
]
