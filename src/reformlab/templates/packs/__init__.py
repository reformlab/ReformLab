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


__all__ = [
    "get_carbon_tax_pack_dir",
    "list_carbon_tax_templates",
    "load_carbon_tax_template",
]
