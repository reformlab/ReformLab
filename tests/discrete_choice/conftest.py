# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Test fixtures for the discrete choice subsystem.

Provides mock adapter, sample population, sample choice set, and mock
decision domain for testing expansion, reshape, and step execution.
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import PolicyConfig, PopulationData
from reformlab.discrete_choice.expansion import (
    TRACKING_COL_ALTERNATIVE_ID,
    TRACKING_COL_ORIGINAL_INDEX,
)
from reformlab.discrete_choice.types import Alternative, ChoiceSet, CostMatrix, TasteParameters

# ============================================================================
# Mock Decision Domain
# ============================================================================


class MockDomain:
    """Test decision domain with 3 alternatives overriding one column.

    Satisfies the DecisionDomain protocol via structural typing.
    """

    @property
    def name(self) -> str:
        return "test_domain"

    @property
    def alternatives(self) -> tuple[Alternative, ...]:
        return (
            Alternative(id="option_a", name="Option A", attributes={"fuel_cost": 0.10}),
            Alternative(id="option_b", name="Option B", attributes={"fuel_cost": 0.20}),
            Alternative(id="option_c", name="Option C", attributes={"fuel_cost": 0.30}),
        )

    @property
    def cost_column(self) -> str:
        return "total_cost"

    def apply_alternative(
        self, table: pa.Table, alternative: Alternative
    ) -> pa.Table:
        """Override fuel_cost column with alternative-specific value."""
        for col_name, col_value in alternative.attributes.items():
            if col_name in table.column_names:
                idx = table.column_names.index(col_name)
                new_col = pa.array(
                    [col_value] * table.num_rows, type=table.column(idx).type
                )
                table = table.set_column(idx, col_name, new_col)
            else:
                new_col = pa.array([col_value] * table.num_rows, type=pa.float64())
                table = table.append_column(col_name, new_col)
        return table


class NoOverrideDomain:
    """Test domain where alternatives have no attribute overrides."""

    @property
    def name(self) -> str:
        return "no_override_domain"

    @property
    def alternatives(self) -> tuple[Alternative, ...]:
        return (
            Alternative(id="keep_a", name="Keep A", attributes={}),
            Alternative(id="keep_b", name="Keep B", attributes={}),
        )

    @property
    def cost_column(self) -> str:
        return "total_cost"

    def apply_alternative(
        self, table: pa.Table, alternative: Alternative
    ) -> pa.Table:
        """No overrides — return table as-is."""
        return table


class SingleAlternativeDomain:
    """Test domain with a single alternative (M=1)."""

    @property
    def name(self) -> str:
        return "single_alt_domain"

    @property
    def alternatives(self) -> tuple[Alternative, ...]:
        return (Alternative(id="only", name="Only Option", attributes={"fuel_cost": 0.15}),)

    @property
    def cost_column(self) -> str:
        return "total_cost"

    def apply_alternative(
        self, table: pa.Table, alternative: Alternative
    ) -> pa.Table:
        for col_name, col_value in alternative.attributes.items():
            if col_name in table.column_names:
                idx = table.column_names.index(col_name)
                new_col = pa.array(
                    [col_value] * table.num_rows, type=table.column(idx).type
                )
                table = table.set_column(idx, col_name, new_col)
            else:
                new_col = pa.array([col_value] * table.num_rows, type=pa.float64())
                table = table.append_column(col_name, new_col)
        return table


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_domain() -> MockDomain:
    """Mock decision domain with 3 alternatives."""
    return MockDomain()


@pytest.fixture
def no_override_domain() -> NoOverrideDomain:
    """Domain with no attribute overrides."""
    return NoOverrideDomain()


@pytest.fixture
def single_alt_domain() -> SingleAlternativeDomain:
    """Domain with single alternative."""
    return SingleAlternativeDomain()


@pytest.fixture
def sample_population() -> PopulationData:
    """Sample population with 3 households and one entity table."""
    table = pa.table({
        "household_id": pa.array([0, 1, 2], type=pa.int64()),
        "income": pa.array([30000.0, 45000.0, 60000.0]),
        "fuel_cost": pa.array([0.15, 0.18, 0.12]),
    })
    return PopulationData(
        tables={"menage": table},
        metadata={"source": "test"},
    )


@pytest.fixture
def empty_population() -> PopulationData:
    """Empty population with 0 households."""
    table = pa.table({
        "household_id": pa.array([], type=pa.int64()),
        "income": pa.array([], type=pa.float64()),
        "fuel_cost": pa.array([], type=pa.float64()),
    })
    return PopulationData(
        tables={"menage": table},
        metadata={"source": "test_empty"},
    )


@pytest.fixture
def single_household_population() -> PopulationData:
    """Population with a single household (N=1)."""
    table = pa.table({
        "household_id": pa.array([0], type=pa.int64()),
        "income": pa.array([50000.0]),
        "fuel_cost": pa.array([0.20]),
    })
    return PopulationData(
        tables={"menage": table},
        metadata={"source": "test_single"},
    )


@pytest.fixture
def multi_entity_population() -> PopulationData:
    """Population with two entity tables."""
    menage_table = pa.table({
        "household_id": pa.array([0, 1], type=pa.int64()),
        "income": pa.array([30000.0, 50000.0]),
        "fuel_cost": pa.array([0.15, 0.20]),
    })
    individu_table = pa.table({
        "person_id": pa.array([0, 1, 2], type=pa.int64()),
        "age": pa.array([35, 42, 28], type=pa.int32()),
    })
    return PopulationData(
        tables={"menage": menage_table, "individu": individu_table},
        metadata={"source": "test_multi"},
    )


@pytest.fixture
def sample_choice_set() -> ChoiceSet:
    """Choice set with 3 alternatives."""
    return ChoiceSet(
        alternatives=(
            Alternative(id="option_a", name="Option A", attributes={"fuel_cost": 0.10}),
            Alternative(id="option_b", name="Option B", attributes={"fuel_cost": 0.20}),
            Alternative(id="option_c", name="Option C", attributes={"fuel_cost": 0.30}),
        )
    )


def _discrete_choice_compute_fn(
    population: PopulationData,
    policy: PolicyConfig,
    period: int,
) -> pa.Table:
    """Compute function that returns tracking columns + total_cost.

    Computes total_cost = income * fuel_cost for each expanded row,
    preserving tracking columns for reshape.
    """
    # Get the first entity table
    entity_key = sorted(population.tables.keys())[0]
    table = population.tables[entity_key]

    # Pass through tracking columns + compute cost
    income = table.column("income").to_pylist()
    fuel_cost = table.column("fuel_cost").to_pylist()
    total_cost = [i * f for i, f in zip(income, fuel_cost)]

    result_cols: dict[str, pa.Array] = {
        "total_cost": pa.array(total_cost),
    }

    # Include tracking columns if present
    if TRACKING_COL_ALTERNATIVE_ID in table.column_names:
        result_cols[TRACKING_COL_ALTERNATIVE_ID] = table.column(
            TRACKING_COL_ALTERNATIVE_ID
        )
    if TRACKING_COL_ORIGINAL_INDEX in table.column_names:
        result_cols[TRACKING_COL_ORIGINAL_INDEX] = table.column(
            TRACKING_COL_ORIGINAL_INDEX
        )

    return pa.table(result_cols)


@pytest.fixture
def mock_adapter() -> MockAdapter:
    """MockAdapter that computes total_cost and preserves tracking columns."""
    return MockAdapter(
        version_string="mock-dc-1.0.0",
        compute_fn=_discrete_choice_compute_fn,
    )


@pytest.fixture
def sample_policy() -> PolicyConfig:
    """Simple policy config for discrete choice tests."""
    return PolicyConfig(
        policy={"carbon_tax_rate": 44.6},
        name="test_policy",
        description="Test policy for discrete choice",
    )


# ============================================================================
# Story 14-2: Logit model fixtures
# ============================================================================


@pytest.fixture
def sample_taste_parameters() -> TasteParameters:
    """Default taste parameters for logit tests."""
    return TasteParameters(beta_cost=-0.01)


@pytest.fixture
def sample_cost_matrix() -> CostMatrix:
    """3×3 cost matrix for logit tests."""
    return CostMatrix(
        table=pa.table({
            "option_a": pa.array([100.0, 200.0, 300.0]),
            "option_b": pa.array([200.0, 100.0, 200.0]),
            "option_c": pa.array([300.0, 300.0, 100.0]),
        }),
        alternative_ids=("option_a", "option_b", "option_c"),
    )
