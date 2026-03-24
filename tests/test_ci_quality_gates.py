# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Static checks for CI quality-gate configuration (Story 7-3)."""

from __future__ import annotations

import tomllib
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW_PATH = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


def _load_ci_workflow() -> dict[str, object]:
    content = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(content)
    if isinstance(data, dict):
        return data
    return {}


def _check_job_run_commands() -> list[str]:
    workflow = _load_ci_workflow()
    jobs = workflow.get("jobs")
    if not isinstance(jobs, dict):
        return []
    check_job = jobs.get("check")
    if not isinstance(check_job, dict):
        return []
    steps = check_job.get("steps")
    if not isinstance(steps, list):
        return []

    commands: list[str] = []
    for step in steps:
        if isinstance(step, dict):
            run = step.get("run")
            if isinstance(run, str):
                commands.append(run)
    return commands


def _load_pyproject() -> dict[str, object]:
    content = PYPROJECT_PATH.read_text(encoding="utf-8")
    data = tomllib.loads(content)
    if isinstance(data, dict):
        return data
    return {}


def test_ci_workflow_has_required_quality_gate_commands() -> None:
    """CI check job enforces lint, type, tests with coverage, and notebooks."""
    commands = _check_job_run_commands()

    assert "uv run ruff check src tests" in commands
    assert "uv run mypy src" in commands
    assert "uv run pytest --cov=src/reformlab --cov-report=term-missing tests/" in commands
    assert "uv run python demos/guides/01_data_foundation.py" in commands
    assert "uv run python demos/guides/07_custom_templates.py" in commands


def test_pyproject_coverage_threshold_is_configured() -> None:
    """Coverage config enforces Phase 1 fail-under threshold with source scoping."""
    pyproject = _load_pyproject()
    tool = pyproject.get("tool")
    assert isinstance(tool, dict)

    coverage = tool.get("coverage")
    assert isinstance(coverage, dict)

    run_config = coverage.get("run")
    assert isinstance(run_config, dict)
    assert run_config.get("source") == ["src/reformlab"]
    assert run_config.get("branch") is True

    report_config = coverage.get("report")
    assert isinstance(report_config, dict)
    assert report_config.get("fail_under") == 80
    assert report_config.get("show_missing") is True


def test_pyproject_dev_dependencies_include_pytest_cov() -> None:
    """pytest-cov is available in dev dependencies for local/CI parity."""
    pyproject = _load_pyproject()
    project = pyproject.get("project")
    assert isinstance(project, dict)

    optional_dependencies = project.get("optional-dependencies")
    assert isinstance(optional_dependencies, dict)
    dev_dependencies = optional_dependencies.get("dev")
    assert isinstance(dev_dependencies, list)

    assert any(
        isinstance(dependency, str) and dependency.startswith("pytest-cov")
        for dependency in dev_dependencies
    )
