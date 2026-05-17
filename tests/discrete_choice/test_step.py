# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for DiscreteChoiceStep class.

Story 14-1, AC-1, AC-3, AC-5, AC-6, AC-7, AC-8, AC-9:
Protocol compliance, StepRegistry registration, full execute cycle,
state key storage, logging output.
"""

from __future__ import annotations

import logging

import pyarrow as pa
import pytest

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import PolicyConfig, PopulationData
from reformlab.discrete_choice.domain import DecisionDomain
from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.expansion import expand_population
from reformlab.discrete_choice.step import (
    DISCRETE_CHOICE_COST_MATRIX_KEY,
    DISCRETE_CHOICE_EXPANSION_KEY,
    DISCRETE_CHOICE_METADATA_KEY,
    DiscreteChoiceStep,
    _inject_fuel_price_from_exogenous_context,
)
from reformlab.discrete_choice.types import ChoiceSet, CostMatrix, ExpansionResult
from reformlab.orchestrator.step import StepRegistry, is_protocol_step
from reformlab.orchestrator.types import YearState
from tests.discrete_choice.conftest import MockDomain


class _FuelPriceConfig:
    fuel_price_series = "fuel_price_eur_litre"


class _FuelPriceDomain(MockDomain):
    @property
    def config(self) -> _FuelPriceConfig:
        return _FuelPriceConfig()


class _ExogenousContext:
    def __init__(self, value: float | Exception) -> None:
        self._value = value

    def get_value(self, series_id: str, year: int) -> float:
        if isinstance(self._value, Exception):
            raise self._value
        assert series_id == "fuel_price_eur_litre"
        assert year == 2025
        return self._value


class TestDiscreteChoiceStepProtocol:
    """AC-1: Protocol compliance and StepRegistry registration."""

    def test_is_protocol_step(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
    ) -> None:
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        assert is_protocol_step(step)

    def test_registry_registration(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
    ) -> None:
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        registry = StepRegistry()
        registry.register(step)
        assert registry.get("discrete_choice") is step

    def test_custom_name(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
    ) -> None:
        step = DiscreteChoiceStep(
            adapter=mock_adapter,
            domain=mock_domain,
            policy=sample_policy,
            name="vehicle_choice",
        )
        assert step.name == "vehicle_choice"

    def test_depends_on(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
    ) -> None:
        step = DiscreteChoiceStep(
            adapter=mock_adapter,
            domain=mock_domain,
            policy=sample_policy,
            depends_on=("computation",),
        )
        assert step.depends_on == ("computation",)

    def test_description(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
    ) -> None:
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        assert step.description  # Non-empty

    def test_domain_protocol_compliance(self, mock_domain: MockDomain) -> None:
        """AC-6: MockDomain satisfies DecisionDomain protocol."""
        assert isinstance(mock_domain, DecisionDomain)


class TestDiscreteChoiceStepExecution:
    """AC-3, AC-7, AC-8: Full execute cycle with state storage."""

    def _make_state(self, population: PopulationData) -> YearState:
        return YearState(
            year=2025,
            data={"population_data": population},
            seed=42,
        )

    def test_full_execute_cycle(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        sample_population: PopulationData,
    ) -> None:
        """End-to-end: expand → compute → reshape → store."""
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        state = self._make_state(sample_population)
        new_state = step.execute(2025, state)

        # State keys present
        assert DISCRETE_CHOICE_COST_MATRIX_KEY in new_state.data
        assert DISCRETE_CHOICE_EXPANSION_KEY in new_state.data
        assert DISCRETE_CHOICE_METADATA_KEY in new_state.data

        # Cost matrix is correct type
        cm = new_state.data[DISCRETE_CHOICE_COST_MATRIX_KEY]
        assert isinstance(cm, CostMatrix)
        assert cm.n_households == 3
        assert cm.n_alternatives == 3

        # Expansion result is correct type
        er = new_state.data[DISCRETE_CHOICE_EXPANSION_KEY]
        assert isinstance(er, ExpansionResult)

    def test_cost_matrix_values(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        sample_population: PopulationData,
    ) -> None:
        """Verify cost matrix has correct computed values.

        MockAdapter computes total_cost = income × fuel_cost.
        N=3, M=3 alternatives with fuel_cost=[0.10, 0.20, 0.30].
        """
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        state = self._make_state(sample_population)
        new_state = step.execute(2025, state)

        cm = new_state.data[DISCRETE_CHOICE_COST_MATRIX_KEY]

        # Option A (fuel_cost=0.10): [30000*0.10, 45000*0.10, 60000*0.10]
        assert cm.table.column("option_a").to_pylist() == pytest.approx(
            [3000.0, 4500.0, 6000.0]
        )
        # Option B (fuel_cost=0.20): [30000*0.20, 45000*0.20, 60000*0.20]
        assert cm.table.column("option_b").to_pylist() == pytest.approx(
            [6000.0, 9000.0, 12000.0]
        )
        # Option C (fuel_cost=0.30): [30000*0.30, 45000*0.30, 60000*0.30]
        assert cm.table.column("option_c").to_pylist() == pytest.approx(
            [9000.0, 13500.0, 18000.0]
        )

    def test_metadata_stored(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        sample_population: PopulationData,
    ) -> None:
        """AC-7: Metadata dict stored with domain name, N, M, etc."""
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        state = self._make_state(sample_population)
        new_state = step.execute(2025, state)

        meta = new_state.data[DISCRETE_CHOICE_METADATA_KEY]
        assert meta["domain_name"] == "test_domain"
        assert meta["n_households"] == 3
        assert meta["n_alternatives"] == 3
        assert meta["alternative_names"] == ["option_a", "option_b", "option_c"]
        assert meta["adapter_version"] == "mock-dc-1.0.0"

    def test_fuel_price_injection_adds_column_and_metadata(
        self,
        sample_population: PopulationData,
    ) -> None:
        """Configured exogenous fuel prices are injected into expanded rows."""
        domain = _FuelPriceDomain()
        choice_set = ChoiceSet(alternatives=domain.alternatives)
        expansion = expand_population(sample_population, choice_set, domain)

        injected, metadata = _inject_fuel_price_from_exogenous_context(
            expansion=expansion,
            domain=domain,
            state_data={"exogenous_context": _ExogenousContext(1.87)},
            year=2025,
            step_name="discrete_choice",
        )

        assert metadata == {
            "source": "exogenous:fuel_price_eur_litre",
            "value": 1.87,
            "unit": "EUR/litre",
        }
        for table in injected.population.tables.values():
            assert table.column("fuel_price").to_pylist() == pytest.approx(
                [1.87] * table.num_rows
            )

    def test_fuel_price_injection_failure_is_not_silent(
        self,
        mock_adapter: MockAdapter,
        sample_policy: PolicyConfig,
        sample_population: PopulationData,
    ) -> None:
        """Fuel price lookup failures abort the step with context."""
        step = DiscreteChoiceStep(
            adapter=mock_adapter,
            domain=_FuelPriceDomain(),
            policy=sample_policy,
        )
        state = YearState(
            year=2025,
            data={
                "population_data": sample_population,
                "exogenous_context": _ExogenousContext(KeyError("missing series")),
            },
            seed=42,
        )

        with pytest.raises(DiscreteChoiceError, match="Fuel price injection failed"):
            step.execute(2025, state)

        assert mock_adapter.call_log == []

    def test_single_batch_call(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        sample_population: PopulationData,
    ) -> None:
        """AC-3: Adapter called exactly once with N×M expanded population."""
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        state = self._make_state(sample_population)
        step.execute(2025, state)

        assert len(mock_adapter.call_log) == 1
        call = mock_adapter.call_log[0]
        assert call["population_row_count"] == 9  # 3 × 3

    def test_empty_population_skips_adapter(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        empty_population: PopulationData,
    ) -> None:
        """AC-3 exception: N=0 skips adapter, returns empty CostMatrix."""
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        state = self._make_state(empty_population)
        new_state = step.execute(2025, state)

        # Adapter not called
        assert len(mock_adapter.call_log) == 0

        # Empty CostMatrix with correct columns
        cm = new_state.data[DISCRETE_CHOICE_COST_MATRIX_KEY]
        assert cm.n_households == 0
        assert cm.n_alternatives == 3

    def test_determinism(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        sample_population: PopulationData,
    ) -> None:
        """AC-8: Identical inputs produce identical outputs."""
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        state = self._make_state(sample_population)

        s1 = step.execute(2025, state)
        # Reset call log for second run
        mock_adapter.call_log.clear()
        s2 = step.execute(2025, state)

        cm1 = s1.data[DISCRETE_CHOICE_COST_MATRIX_KEY]
        cm2 = s2.data[DISCRETE_CHOICE_COST_MATRIX_KEY]
        assert cm1.table.equals(cm2.table)

    def test_immutable_state_update(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        sample_population: PopulationData,
    ) -> None:
        """Step returns new YearState without modifying original."""
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        state = self._make_state(sample_population)
        new_state = step.execute(2025, state)

        # Original state unchanged
        assert DISCRETE_CHOICE_COST_MATRIX_KEY not in state.data
        # New state has results
        assert DISCRETE_CHOICE_COST_MATRIX_KEY in new_state.data

    def test_no_population_raises(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
    ) -> None:
        """DiscreteChoiceError when no PopulationData in state."""
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        state = YearState(year=2025, data={"some_key": "some_value"})

        with pytest.raises(DiscreteChoiceError, match="PopulationData not found"):
            step.execute(2025, state)

    def test_adapter_failure_wrapped(
        self,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        sample_population: PopulationData,
    ) -> None:
        """Adapter compute failure is wrapped in DiscreteChoiceError."""

        def failing_compute(
            population: PopulationData, policy: PolicyConfig, period: int
        ) -> pa.Table:
            raise RuntimeError("Backend unavailable")

        adapter = MockAdapter(
            version_string="mock-fail-1.0.0",
            compute_fn=failing_compute,
        )
        step = DiscreteChoiceStep(
            adapter=adapter, domain=mock_domain, policy=sample_policy
        )
        state = YearState(
            year=2025, data={"population_data": sample_population}
        )

        with pytest.raises(DiscreteChoiceError, match="Adapter computation failed"):
            step.execute(2025, state)


class TestDiscreteChoiceStepLogging:
    """AC-9: Structured key=value logging."""

    def test_step_start_log(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        sample_population: PopulationData,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        step = DiscreteChoiceStep(
            adapter=mock_adapter, domain=mock_domain, policy=sample_policy
        )
        state = YearState(
            year=2025, data={"population_data": sample_population}
        )

        with caplog.at_level(logging.INFO, logger="reformlab.discrete_choice.step"):
            step.execute(2025, state)

        # Check structured log messages
        info_messages = [r.message for r in caplog.records if r.levelno == logging.INFO]
        assert any("event=step_start" in m for m in info_messages)
        assert any("event=step_complete" in m for m in info_messages)
        assert any("n_households=3" in m for m in info_messages)
        assert any("n_alternatives=3" in m for m in info_messages)


class TestDiscreteChoiceStepTechnologySet:
    """Story 28.2 / AC-1, AC-8: Integration tests for technology_set parameter."""

    def test_step_with_technology_set_validates_incumbents(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Step with technology_set validates incumbent columns and logs warnings."""
        from reformlab.discrete_choice import DEFAULT_TECHNOLOGY_SET

        # Population without incumbent columns (but with required columns for adapter)
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2, 3],
                    "income": [30000.0, 45000.0, 60000.0],
                    "fuel_cost": [0.15, 0.18, 0.12],
                })
            },
            metadata={},
        )

        step = DiscreteChoiceStep(
            adapter=mock_adapter,
            domain=mock_domain,
            policy=sample_policy,
            technology_set=DEFAULT_TECHNOLOGY_SET,
        )
        state = YearState(year=2025, data={"population_data": population})

        with caplog.at_level(logging.WARNING, logger="reformlab.discrete_choice.step"):
            result = step.execute(2025, state)

        # Should log warnings for missing incumbent columns
        warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        assert any("incumbent_heating" in m for m in warning_messages)
        assert any("incumbent_vehicle" in m for m in warning_messages)
        assert any("event=population_validation" in m for m in warning_messages)

        # Step should still complete successfully
        assert DISCRETE_CHOICE_COST_MATRIX_KEY in result.data

    def test_step_without_technology_set_skips_validation(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        sample_population: PopulationData,
    ) -> None:
        """Step without technology_set skips validation (backward compatible)."""
        step = DiscreteChoiceStep(
            adapter=mock_adapter,
            domain=mock_domain,
            policy=sample_policy,
            technology_set=None,  # Explicitly None
        )
        state = YearState(year=2025, data={"population_data": sample_population})

        # Should not raise even if population has no incumbent columns
        result = step.execute(2025, state)
        assert DISCRETE_CHOICE_COST_MATRIX_KEY in result.data

    def test_step_with_incumbents_validates_successfully(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
    ) -> None:
        """Step with valid incumbent columns passes validation without warnings."""
        from reformlab.discrete_choice import DEFAULT_TECHNOLOGY_SET

        # Population with valid incumbent columns (plus required columns for adapter)
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2, 3],
                    "income": [30000.0, 45000.0, 60000.0],
                    "fuel_cost": [0.15, 0.18, 0.12],
                    "incumbent_heating": pa.array(
                        ["condensing_boiler", "heat_pump_air", "keep_current"],
                        type=pa.dictionary(pa.int32(), pa.utf8()),
                    ),
                    "incumbent_vehicle": pa.array(
                        ["diesel", "ev", "keep_current"],
                        type=pa.dictionary(pa.int32(), pa.utf8()),
                    ),
                })
            },
            metadata={},
        )

        step = DiscreteChoiceStep(
            adapter=mock_adapter,
            domain=mock_domain,
            policy=sample_policy,
            technology_set=DEFAULT_TECHNOLOGY_SET,
        )
        state = YearState(year=2025, data={"population_data": population})

        # Should complete without warnings
        result = step.execute(2025, state)
        assert DISCRETE_CHOICE_COST_MATRIX_KEY in result.data

    def test_step_with_unknown_incumbent_ids_raises(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
    ) -> None:
        """Step with unknown incumbent IDs raises DiscreteChoiceError."""
        from reformlab.discrete_choice import DEFAULT_TECHNOLOGY_SET

        # Population with unknown incumbent ID (plus required columns for adapter)
        population = PopulationData(
            tables={
                "menage": pa.table({
                    "household_id": [1, 2],
                    "income": [30000.0, 45000.0],
                    "fuel_cost": [0.15, 0.18],
                    "incumbent_heating": pa.array(
                        ["condensing_boiler", "unknown_tech"],
                        type=pa.dictionary(pa.int32(), pa.utf8()),
                    ),
                })
            },
            metadata={},
        )

        step = DiscreteChoiceStep(
            adapter=mock_adapter,
            domain=mock_domain,
            policy=sample_policy,
            technology_set=DEFAULT_TECHNOLOGY_SET,
        )
        state = YearState(year=2025, data={"population_data": population})

        # Should raise DiscreteChoiceError
        with pytest.raises(DiscreteChoiceError, match="unknown incumbent technology IDs"):
            step.execute(2025, state)

    def test_step_short_circuits_when_decisions_disabled(
        self,
        mock_adapter: MockAdapter,
        mock_domain: MockDomain,
        sample_policy: PolicyConfig,
        sample_population: PopulationData,
    ) -> None:
        """Step short-circuits when investment_decisions_enabled=false (Story 28.2 / AC-8)."""
        from reformlab.discrete_choice import DEFAULT_TECHNOLOGY_SET

        step = DiscreteChoiceStep(
            adapter=mock_adapter,
            domain=mock_domain,
            policy=sample_policy,
            technology_set=DEFAULT_TECHNOLOGY_SET,
        )
        state = YearState(
            year=2025,
            data={"population_data": sample_population},
            metadata={"investment_decisions_enabled": False},
        )

        result = step.execute(2025, state)

        # Should return state unchanged, no validation performed
        assert result == state
        assert DISCRETE_CHOICE_COST_MATRIX_KEY not in result.data
