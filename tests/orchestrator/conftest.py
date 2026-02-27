"""Test fixtures for the orchestrator module."""

from __future__ import annotations

import pytest

from reformlab.orchestrator.types import OrchestratorConfig, YearState


@pytest.fixture
def simple_config() -> OrchestratorConfig:
    """Return a simple orchestrator config with no steps."""
    return OrchestratorConfig(
        start_year=2025,
        end_year=2034,
        initial_state={"population": 1000},
        seed=42,
        step_pipeline=(),
    )


@pytest.fixture
def empty_pipeline_config() -> OrchestratorConfig:
    """Return config with explicitly empty pipeline."""
    return OrchestratorConfig(
        start_year=2025,
        end_year=2027,
        initial_state={},
        seed=None,
        step_pipeline=(),
    )


def increment_population(year: int, state: YearState) -> YearState:
    """Test step that increments population by year offset."""
    from dataclasses import replace

    new_data = dict(state.data)
    new_data["population"] = new_data.get("population", 0) + 100
    return replace(state, data=new_data)


def add_year_marker(year: int, state: YearState) -> YearState:
    """Test step that adds a year marker to metadata."""
    from dataclasses import replace

    new_metadata = dict(state.metadata)
    new_metadata[f"marker_{year}"] = True
    return replace(state, metadata=new_metadata)


def failing_step(year: int, state: YearState) -> YearState:
    """Test step that always fails."""
    raise ValueError(f"Intentional failure at year {year}")


def fail_at_year_2028(year: int, state: YearState) -> YearState:
    """Test step that fails only at year 2028."""
    if year == 2028:
        raise RuntimeError("Failing at year 2028 as expected")
    return state


@pytest.fixture
def config_with_steps() -> OrchestratorConfig:
    """Return config with two test steps."""
    return OrchestratorConfig(
        start_year=2025,
        end_year=2029,
        initial_state={"population": 1000},
        seed=12345,
        step_pipeline=(increment_population, add_year_marker),
    )


@pytest.fixture
def config_with_failing_step() -> OrchestratorConfig:
    """Return config with a step that fails at year 2028."""
    return OrchestratorConfig(
        start_year=2025,
        end_year=2030,
        initial_state={"population": 1000},
        seed=None,
        step_pipeline=(increment_population, fail_at_year_2028),
    )
