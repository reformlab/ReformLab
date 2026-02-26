"""Scenario template schema and loader for ReformLab.

This module provides:
- Schema dataclasses for defining scenario templates
- YAML loader/serializer for scenario template files
- Reform-as-delta resolution for reform scenarios
- JSON Schema for IDE validation support
- Template pack discovery and loading utilities
"""

from reformlab.templates.exceptions import ScenarioError
from reformlab.templates.loader import (
    SCHEMA_VERSION,
    dump_scenario_template,
    get_schema_path,
    load_scenario_template,
    validate_schema_version,
)
from reformlab.templates.packs import (
    get_carbon_tax_pack_dir,
    get_feebate_pack_dir,
    get_rebate_pack_dir,
    get_subsidy_pack_dir,
    list_carbon_tax_templates,
    list_feebate_templates,
    list_rebate_templates,
    list_subsidy_templates,
    load_carbon_tax_template,
    load_feebate_template,
    load_rebate_template,
    load_subsidy_template,
)
from reformlab.templates.reform import resolve_reform_definition
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    ReformScenario,
    SubsidyParameters,
    YearSchedule,
)

__all__ = [
    # Schema types
    "BaselineScenario",
    "CarbonTaxParameters",
    "FeebateParameters",
    "PolicyParameters",
    "PolicyType",
    "RebateParameters",
    "ReformScenario",
    "SubsidyParameters",
    "YearSchedule",
    # Loader functions
    "dump_scenario_template",
    "get_schema_path",
    "load_scenario_template",
    "resolve_reform_definition",
    "validate_schema_version",
    # Pack utilities - Carbon tax
    "get_carbon_tax_pack_dir",
    "list_carbon_tax_templates",
    "load_carbon_tax_template",
    # Pack utilities - Subsidy
    "get_subsidy_pack_dir",
    "list_subsidy_templates",
    "load_subsidy_template",
    # Pack utilities - Rebate
    "get_rebate_pack_dir",
    "list_rebate_templates",
    "load_rebate_template",
    # Pack utilities - Feebate
    "get_feebate_pack_dir",
    "list_feebate_templates",
    "load_feebate_template",
    # Exceptions
    "ScenarioError",
    # Constants
    "SCHEMA_VERSION",
]
