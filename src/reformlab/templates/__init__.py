"""Scenario template schema and loader for ReformLab.

This module provides:
- Schema dataclasses for defining scenario templates
- YAML loader/serializer for scenario template files
- Reform-as-delta resolution for reform scenarios
- JSON Schema for IDE validation support
- Template pack discovery and loading utilities
- Scenario registry with immutable versioning
- Schema migration utilities for version compatibility
- Workflow configuration schema and execution handoff
"""

from reformlab.templates.exceptions import ScenarioError, TemplateError
from reformlab.templates.loader import (
    SCHEMA_VERSION,
    dump_scenario_template,
    get_schema_path,
    load_scenario_template,
    validate_schema_version,
)
from reformlab.templates.migration import (
    CompatibilityStatus,
    MigrationChange,
    MigrationReport,
    SchemaVersion,
    check_compatibility,
    migrate_scenario_dict,
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
from reformlab.templates.portfolios import (
    Conflict,
    ConflictType,
    PolicyConfig,
    PolicyPortfolio,
    PortfolioError,
    PortfolioSerializationError,
    PortfolioValidationError,
    ResolutionStrategy,
    dump_portfolio,
    load_portfolio,
    resolve_conflicts,
    validate_compatibility,
)
from reformlab.templates.reform import resolve_reform_definition
from reformlab.templates.registry import (
    RegistryEntry,
    RegistryError,
    ScenarioNotFoundError,
    ScenarioRegistry,
    ScenarioVersion,
    VersionNotFoundError,
)
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    ReformScenario,
    ScenarioTemplate,
    SubsidyParameters,
    YearSchedule,
    infer_policy_type,
)
from reformlab.templates.workflow import (
    WORKFLOW_SCHEMA_VERSION,
    DataSourceConfig,
    OutputConfig,
    OutputFormat,
    OutputType,
    RunConfig,
    ScenarioRef,
    WorkflowConfig,
    WorkflowError,
    WorkflowResult,
    dump_workflow_config,
    get_workflow_schema_path,
    load_workflow_config,
    prepare_workflow_request,
    run_workflow,
    validate_workflow_config,
    validate_workflow_with_schema,
    workflow_to_json,
    workflow_to_yaml,
)

__all__ = [
    # Portfolio types
    "PolicyConfig",
    "PolicyPortfolio",
    "PortfolioError",
    "PortfolioSerializationError",
    "PortfolioValidationError",
    "Conflict",
    "ConflictType",
    "ResolutionStrategy",
    "validate_compatibility",
    "resolve_conflicts",
    "dump_portfolio",
    "load_portfolio",
    # Migration types and functions
    "CompatibilityStatus",
    "MigrationChange",
    "MigrationReport",
    "SchemaVersion",
    "check_compatibility",
    "migrate_scenario_dict",
    # Registry types
    "RegistryEntry",
    "RegistryError",
    "ScenarioNotFoundError",
    "ScenarioRegistry",
    "ScenarioVersion",
    "VersionNotFoundError",
    # Schema types
    "BaselineScenario",
    "CarbonTaxParameters",
    "FeebateParameters",
    "PolicyParameters",
    "PolicyType",
    "RebateParameters",
    "ReformScenario",
    "ScenarioTemplate",
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
    # Inference
    "infer_policy_type",
    # Exceptions
    "ScenarioError",
    "TemplateError",
    # Constants
    "SCHEMA_VERSION",
    # Workflow types and functions
    "DataSourceConfig",
    "OutputConfig",
    "OutputFormat",
    "OutputType",
    "RunConfig",
    "ScenarioRef",
    "WorkflowConfig",
    "WorkflowError",
    "WorkflowResult",
    "WORKFLOW_SCHEMA_VERSION",
    "dump_workflow_config",
    "get_workflow_schema_path",
    "load_workflow_config",
    "prepare_workflow_request",
    "run_workflow",
    "validate_workflow_config",
    "validate_workflow_with_schema",
    "workflow_to_json",
    "workflow_to_yaml",
]
