# ReformLab Workflow Examples

This directory contains example workflow configurations for ReformLab policy analysis.

## Workflow Files

### `carbon_tax_analysis.yaml`
**Single Scenario Analysis**

A basic workflow that analyzes the distributional impact of a flat carbon tax policy. Demonstrates:
- Loading a baseline scenario from the registry
- Configuring a 10-year projection
- Generating distributional indicators grouped by income decile

### `scenario_comparison.yaml`
**Baseline vs Reform Comparison**

Compares a baseline carbon tax with a progressive redistribution reform. Demonstrates:
- Loading multiple scenarios with different roles (baseline, reform)
- Generating side-by-side comparison tables
- Multiple output configurations

### `batch_sensitivity.json`
**Multi-Scenario Batch Analysis**

A JSON-format workflow for sensitivity analysis across multiple carbon tax rate trajectories. Demonstrates:
- JSON format support with deterministic key ordering
- Multiple scenarios for batch processing
- Parquet output format for large datasets
- Cross-scenario comparison outputs

## Schema Validation

All workflow files can reference the JSON Schema for IDE validation support:

```yaml
$schema: "./schema/workflow.schema.json"
```

The schema is located at `src/reformlab/templates/schema/workflow.schema.json`.

## Running Workflows

```python
from reformlab.templates import load_workflow_config, run_workflow

# Load and validate a workflow
config = load_workflow_config("examples/workflows/carbon_tax_analysis.yaml")

# Execute the workflow (requires orchestrator backend from EPIC-3)
result = run_workflow(config, runner=my_runner)
```

## Workflow Configuration Reference

### Required Fields
- `name`: Workflow identifier (string)
- `version`: Schema version for compatibility (e.g., "1.0")
- `scenarios`: List of scenario references

### Optional Fields
- `description`: Human-readable description
- `data_sources`: Data source configuration
  - `population`: Registry reference for population data
  - `emission_factors`: Registry reference for emission factors
- `run_config`: Orchestrator settings
  - `projection_years`: Number of years to project (default: 10)
  - `start_year`: Starting year (default: 2025)
  - `output_format`: Default output format (csv, parquet, json, yaml)
- `outputs`: List of output configurations
  - `type`: Output type (distributional_indicators, comparison_table, panel_export, summary_report)
  - `by`: Grouping dimensions
  - `format`: Output format
  - `path`: Output file path
