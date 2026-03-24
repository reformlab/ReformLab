# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Static checks for the Epic 13 custom templates demo script.

Story 13.4: Validate custom templates in portfolios and build demo.
Tests AC6: static validation (existence, public API, key API calls,
section coverage, portfolio comparison, YAML round-trip).
"""

from __future__ import annotations

from pathlib import Path

DEMO_PATH = Path(__file__).resolve().parents[2] / "demos" / "guides" / "07_custom_templates.py"
CI_WORKFLOW_PATH = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci.yml"


def _read_source() -> str:
    return DEMO_PATH.read_text(encoding="utf-8")


def test_epic13_demo_exists() -> None:
    """Demo script exists at expected path."""
    assert DEMO_PATH.exists()


def test_epic13_demo_uses_public_api_only() -> None:
    """Uses public API imports only — no computation internals or openfisca."""
    source = _read_source()
    assert "register_policy_type" in source
    assert "register_custom_template" in source
    assert "PolicyPortfolio" in source
    assert "validate_compatibility" in source
    assert "from openfisca import" not in source


def test_epic13_demo_covers_custom_template_lifecycle() -> None:
    """Contains key sections: Define a Custom Template, Register and Use,
    Portfolios with Custom Templates."""
    source = _read_source()
    assert "Define a Custom Template" in source
    assert "Register and Use" in source
    assert "Portfolios with Custom Templates" in source


def test_epic13_demo_covers_portfolio_comparison() -> None:
    """Contains portfolio comparison code."""
    source = _read_source()
    assert "Compare Portfolios" in source
    assert "run_vehicle_malus_batch" in source
    assert "compare_vehicle_malus_decile_impacts" in source


def test_epic13_demo_covers_yaml_round_trip() -> None:
    """Contains dump_portfolio and load_portfolio for YAML round-trip."""
    source = _read_source()
    assert "dump_portfolio" in source
    assert "load_portfolio" in source


def test_epic13_ci_includes_demo() -> None:
    """CI workflow includes execution of this demo."""
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "uv run python demos/guides/07_custom_templates.py" in ci_workflow
