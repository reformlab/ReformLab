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
]
