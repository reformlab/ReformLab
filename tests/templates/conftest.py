# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture()
def valid_carbon_tax_yaml(tmp_path: Path) -> Path:
    """A valid carbon tax scenario template YAML file."""
    content = textwrap.dedent("""\
        $schema: "./schema/scenario-template.schema.json"
        version: "1.0"

        name: "French Carbon Tax 2026"
        description: "Baseline carbon tax scenario for French households"
        policy_type: carbon_tax

        year_schedule:
          start_year: 2026
          end_year: 2036

        policy:
          rate_schedule:
            2026: 44.60
            2027: 50.00
            2028: 55.00
            2029: 60.00
            2030: 65.00
            2031: 70.00
            2032: 75.00
            2033: 80.00
            2034: 85.00
            2035: 90.00
            2036: 100.00
          exemptions:
            - category: "heating_oil_essential"
              rate_reduction: 0.5
            - category: "agricultural_fuel"
              rate_reduction: 1.0
          covered_categories:
            - "transport_fuel"
            - "heating_fuel"
            - "natural_gas"
    """)
    p = tmp_path / "carbon-tax-baseline.yaml"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def valid_reform_yaml(tmp_path: Path) -> Path:
    """A valid reform scenario template YAML file."""
    content = textwrap.dedent("""\
        $schema: "./schema/scenario-template.schema.json"
        version: "1.0"

        name: "Progressive Carbon Dividend Reform"
        description: "Carbon tax with progressive redistribution"
        policy_type: carbon_tax

        baseline_ref: "french-carbon-tax-2026"

        policy:
          redistribution:
            type: "progressive_dividend"
            income_weights:
              decile_1: 1.5
              decile_2: 1.3
              decile_3: 1.1
              decile_4: 1.0
              decile_5: 1.0
              decile_6: 0.9
              decile_7: 0.8
              decile_8: 0.7
              decile_9: 0.5
              decile_10: 0.2
    """)
    p = tmp_path / "reform-progressive-dividend.yaml"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def short_year_schedule_yaml(tmp_path: Path) -> Path:
    """A YAML file with year schedule shorter than 10 years."""
    content = textwrap.dedent("""\
        $schema: "./schema/scenario-template.schema.json"
        version: "1.0"

        name: "Short Schedule"
        description: "Only 5 years"
        policy_type: carbon_tax

        year_schedule:
          start_year: 2026
          end_year: 2030

        policy:
          rate_schedule:
            2026: 44.60
            2027: 50.00
            2028: 55.00
            2029: 60.00
            2030: 65.00
    """)
    p = tmp_path / "short-schedule.yaml"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def invalid_policy_type_yaml(tmp_path: Path) -> Path:
    """A YAML file with invalid policy type."""
    content = textwrap.dedent("""\
        $schema: "./schema/scenario-template.schema.json"
        version: "1.0"

        name: "Invalid Type"
        policy_type: unknown_policy

        year_schedule:
          start_year: 2026
          end_year: 2036

        policy: {}
    """)
    p = tmp_path / "invalid-policy-type.yaml"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def missing_required_field_yaml(tmp_path: Path) -> Path:
    """A YAML file missing required fields."""
    content = textwrap.dedent("""\
        $schema: "./schema/scenario-template.schema.json"
        version: "1.0"

        name: "Missing Policy Type"

        year_schedule:
          start_year: 2026
          end_year: 2036

        policy: {}
    """)
    p = tmp_path / "missing-field.yaml"
    p.write_text(content, encoding="utf-8")
    return p


@pytest.fixture()
def sample_year_schedule_dict() -> dict[str, Any]:
    """Sample year schedule as dict for testing."""
    return {
        "start_year": 2026,
        "end_year": 2036,
    }


@pytest.fixture()
def sample_carbon_tax_params_dict() -> dict[str, Any]:
    """Sample carbon tax parameters as dict for testing."""
    return {
        "rate_schedule": {
            2026: 44.60,
            2027: 50.00,
            2028: 55.00,
            2029: 60.00,
            2030: 65.00,
            2031: 70.00,
            2032: 75.00,
            2033: 80.00,
            2034: 85.00,
            2035: 90.00,
            2036: 100.00,
        },
        "exemptions": [
            {"category": "heating_oil_essential", "rate_reduction": 0.5},
            {"category": "agricultural_fuel", "rate_reduction": 1.0},
        ],
        "covered_categories": ["transport_fuel", "heating_fuel", "natural_gas"],
    }
