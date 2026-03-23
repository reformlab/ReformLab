# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Test fixtures for the orchestrator module."""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig
from reformlab.computation.types import PopulationData
from reformlab.orchestrator.portfolio_step import PortfolioComputationStep
from reformlab.orchestrator.types import OrchestratorConfig, YearState
from reformlab.templates.portfolios.portfolio import (
    PolicyConfig as PortfolioPolicyConfig,
)
from reformlab.templates.portfolios.portfolio import (
    PolicyPortfolio,
)
from reformlab.templates.schema import (
    CarbonTaxParameters,
    FeebateParameters,
    PolicyType,
    SubsidyParameters,
)


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


# ============================================================================
# Portfolio fixtures (Story 12-3)
# ============================================================================


def _portfolio_compute_fn(
    population: PopulationData, policy: ComputationPolicyConfig, period: int
) -> pa.Table:
    """Return policy-type-specific columns based on policy name."""
    hh_ids = [1, 2, 3]
    if "carbon_tax" in policy.name:
        return pa.table({
            "household_id": pa.array(hh_ids, type=pa.int64()),
            "tax_burden": pa.array([100.0, 200.0, 300.0]),
            "emissions": pa.array([2.5, 5.0, 7.5]),
        })
    if "subsidy" in policy.name:
        return pa.table({
            "household_id": pa.array(hh_ids, type=pa.int64()),
            "subsidy_amount": pa.array([50.0, 75.0, 100.0]),
        })
    if "feebate" in policy.name:
        return pa.table({
            "household_id": pa.array(hh_ids, type=pa.int64()),
            "net_impact": pa.array([-20.0, 10.0, 30.0]),
        })
    # Fallback
    return pa.table({
        "household_id": pa.array(hh_ids, type=pa.int64()),
        "value": pa.array([1.0, 2.0, 3.0]),
    })


@pytest.fixture
def portfolio_population() -> PopulationData:
    """Population data for portfolio tests."""
    table = pa.table({
        "person_id": pa.array([1, 2, 3]),
        "salary": pa.array([30000.0, 45000.0, 60000.0]),
    })
    return PopulationData(tables={"individu": table}, metadata={"source": "test"})


@pytest.fixture
def portfolio_mock_adapter() -> MockAdapter:
    """MockAdapter that returns different columns per policy type."""
    return MockAdapter(
        version_string="mock-portfolio-1.0.0",
        compute_fn=_portfolio_compute_fn,
    )


@pytest.fixture
def sample_portfolio() -> PolicyPortfolio:
    """2-policy portfolio: carbon tax + subsidy."""
    return PolicyPortfolio(
        name="test-2-policy",
        policies=(
            PortfolioPolicyConfig(
                policy_type=PolicyType.CARBON_TAX,
                policy=CarbonTaxParameters(rate_schedule={2025: 44.6, 2026: 50.0}),
                name="carbon_tax_baseline",
            ),
            PortfolioPolicyConfig(
                policy_type=PolicyType.SUBSIDY,
                policy=SubsidyParameters(rate_schedule={2025: 100.0, 2026: 120.0}),
                name="subsidy_green",
            ),
        ),
    )


@pytest.fixture
def three_policy_portfolio() -> PolicyPortfolio:
    """3-policy portfolio: carbon tax + subsidy + feebate."""
    return PolicyPortfolio(
        name="test-3-policy",
        policies=(
            PortfolioPolicyConfig(
                policy_type=PolicyType.CARBON_TAX,
                policy=CarbonTaxParameters(rate_schedule={2025: 44.6}),
                name="carbon_tax_baseline",
            ),
            PortfolioPolicyConfig(
                policy_type=PolicyType.SUBSIDY,
                policy=SubsidyParameters(rate_schedule={2025: 100.0}),
                name="subsidy_green",
            ),
            PortfolioPolicyConfig(
                policy_type=PolicyType.FEEBATE,
                policy=FeebateParameters(rate_schedule={2025: 0.05}),
                name="feebate_auto",
            ),
        ),
    )


@pytest.fixture
def portfolio_computation_step(
    portfolio_mock_adapter: MockAdapter,
    portfolio_population: PopulationData,
    three_policy_portfolio: PolicyPortfolio,
) -> PortfolioComputationStep:
    """PortfolioComputationStep with MockAdapter and 3-policy portfolio."""
    return PortfolioComputationStep(
        adapter=portfolio_mock_adapter,
        population=portfolio_population,
        portfolio=three_policy_portfolio,
    )
