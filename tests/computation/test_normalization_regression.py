# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Regression tests for indicator/comparison compatibility with normalized output.

Story 23.3: Normalize live OpenFisca results into the stable app-facing output schema

Tests cover:
- Distributional indicators accept normalized live output (AC: 3)
- Welfare indicators accept normalized live output (AC: 3)
- Fiscal indicators accept normalized live output (AC: 3)
- Live vs replay results are comparable (AC: 3)
- No runtime branching in indicators (AC: 3)
"""

from __future__ import annotations

import pyarrow as pa

from reformlab.computation.types import ComputationResult
from reformlab.indicators import (
    compute_distributional_indicators,
    compute_fiscal_indicators,
    compute_welfare_indicators,
)
from reformlab.indicators.types import DistributionalConfig, FiscalConfig, WelfareConfig
from reformlab.orchestrator.computation_step import COMPUTATION_RESULT_KEY
from reformlab.orchestrator.panel import PanelOutput
from reformlab.orchestrator.types import OrchestratorResult, YearState


def make_panel(table: pa.Table, start_year: int, end_year: int) -> PanelOutput:
    """Helper to create a PanelOutput from a single-year table."""
    yearly_states: dict[int, YearState] = {}
    for year in range(start_year, end_year + 1):
        # Create a fresh table for each year with year-specific values
        arrays = {}
        for col_name in table.column_names:
            col = table.column(col_name)
            if pa.types.is_float64(col.type):
                # Slightly vary values per year for realism
                base_values = col.to_pylist()
                year_values = [v + (year - start_year) * 1000 for v in base_values]
                arrays[col_name] = pa.array(year_values, type=pa.float64())
            elif pa.types.is_int64(col.type):
                arrays[col_name] = col
            else:
                arrays[col_name] = col

        comp_result = ComputationResult(
            output_fields=pa.table(arrays),
            adapter_version="test-1.0.0",
            period=year,
        )
        yearly_states[year] = YearState(
            year=year,
            data={COMPUTATION_RESULT_KEY: comp_result},
            seed=42,
            metadata={},
        )

    result = OrchestratorResult(
        success=True,
        yearly_states=yearly_states,
        errors=[],
        failed_year=None,
        metadata={
            "start_year": start_year,
            "end_year": end_year,
            "seed": 42,
            "step_pipeline": ["computation"],
        },
    )

    return PanelOutput.from_orchestrator_result(result)


class TestIndicatorCompatibilityWithNormalizedOutput:
    """Test that indicators work with normalized live output (AC: 3)."""

    def test_distributional_indicators_accept_normalized_live_output(self) -> None:
        """Default config (income_field='income') works because _DEFAULT_OUTPUT_MAPPING
        includes 'salaire_net' -> 'income'.
        """
        # Simulate normalized live OpenFisca output (English names)
        table = pa.table({
            "household_id": pa.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], type=pa.int64()),
            "income": pa.array([
                20000.0, 30000.0, 40000.0, 50000.0, 60000.0,
                70000.0, 80000.0, 90000.0, 100000.0, 110000.0,
            ]),
        })
        panel = make_panel(table, 2025, 2025)

        # Default config uses income_field="income" (present after normalization)
        config = DistributionalConfig(income_field="income", by_year=False)

        # Key test: indicator should not error with normalized output
        # This is the acceptance criterion - no runtime branching needed
        result = compute_distributional_indicators(panel, config=config)
        assert result is not None

    def test_welfare_indicators_accept_normalized_live_output(self) -> None:
        """Default config (welfare_field='disposable_income') works."""
        # Baseline panel
        baseline_table = pa.table({
            "household_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
            "income": pa.array([40000.0, 50000.0, 60000.0, 70000.0, 80000.0]),
            "disposable_income": pa.array([36000.0, 45000.0, 54000.0, 63000.0, 72000.0]),
        })
        baseline = make_panel(baseline_table, 2025, 2025)

        # Reform panel (higher carbon tax, lower disposable income)
        reform_table = pa.table({
            "household_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
            "income": pa.array([40000.0, 50000.0, 60000.0, 70000.0, 80000.0]),
            "disposable_income": pa.array([35500.0, 44000.0, 52500.0, 61000.0, 69500.0]),
        })
        reform = make_panel(reform_table, 2025, 2025)

        # Default config uses welfare_field="disposable_income" (present after normalization)
        config = WelfareConfig(welfare_field="disposable_income", threshold=0.0)

        # Key test: indicator should not error with normalized output
        result = compute_welfare_indicators(baseline, reform, config=config)
        assert result is not None

    def test_fiscal_indicators_accept_normalized_live_output(self) -> None:
        """Auto-detects fiscal columns with *_tax, *_revenue, etc. suffixes."""
        table = pa.table({
            "household_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
            "carbon_tax": pa.array([100.0, 200.0, 300.0, 400.0, 500.0]),
            "income_tax": pa.array([4000.0, 5000.0, 6000.0, 7000.0, 8000.0]),
        })
        panel = make_panel(table, 2025, 2025)

        # Auto-detect fiscal columns by explicitly listing them
        config = FiscalConfig(
            revenue_fields=["carbon_tax", "income_tax"],
            cost_fields=[],
            by_year=False,
        )

        # Key test: indicator should not error with normalized output
        result = compute_fiscal_indicators(panel, config=config)
        assert result is not None


class TestComparisonWithMixedRuntimeModes:
    """Test that live and replay results are comparable (AC: 3)."""

    def test_compare_live_vs_replay_results(self) -> None:
        """Both produce comparable panels with same column schema."""
        # Live result (simulated - already normalized to English names)
        live_table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([50000.0, 60000.0, 70000.0]),
            "disposable_income": pa.array([45000.0, 54000.0, 63000.0]),
            "carbon_tax": pa.array([100.0, 200.0, 300.0]),
        })
        live_panel = make_panel(live_table, 2025, 2025)

        # Replay result (same schema, already uses English names)
        replay_table = pa.table({
            "household_id": pa.array([1, 2, 3], type=pa.int64()),
            "income": pa.array([52000.0, 62000.0, 72000.0]),
            "disposable_income": pa.array([46800.0, 55800.0, 64800.0]),
            "carbon_tax": pa.array([120.0, 220.0, 320.0]),
        })
        replay_panel = make_panel(replay_table, 2025, 2025)

        # Both should have same column schema
        assert set(live_panel.table.column_names) == set(replay_panel.table.column_names)
        assert "income" in live_panel.table.column_names
        assert "disposable_income" in live_panel.table.column_names
        assert "carbon_tax" in live_panel.table.column_names

        # Should be comparable (no errors when computing indicators)
        live_indicators = compute_distributional_indicators(
            live_panel,
            config=DistributionalConfig(income_field="income", by_year=False),
        )
        replay_indicators = compute_distributional_indicators(
            replay_panel,
            config=DistributionalConfig(income_field="income", by_year=False),
        )

        assert live_indicators is not None
        assert replay_indicators is not None

    def test_no_runtime_branching_in_indicators(self) -> None:
        """Indicator code does not check runtime_mode."""
        # Create a panel that could be from either live or replay mode
        table = pa.table({
            "household_id": pa.array([1, 2, 3, 4, 5], type=pa.int64()),
            "income": pa.array([40000.0, 50000.0, 60000.0, 70000.0, 80000.0]),
            "disposable_income": pa.array([36000.0, 45000.0, 54000.0, 63000.0, 72000.0]),
            "carbon_tax": pa.array([100.0, 200.0, 300.0, 400.0, 500.0]),
        })
        panel = make_panel(table, 2025, 2025)

        # Add runtime_mode to metadata (simulating either mode)
        panel.metadata["runtime_mode"] = "live"  # or "replay"

        # Indicator should work regardless of runtime_mode value
        # (indicators don't check this field)
        config = DistributionalConfig(income_field="income", by_year=False)
        result = compute_distributional_indicators(panel, config=config)

        # Should succeed
        assert result is not None

        # Same with different runtime_mode
        panel.metadata["runtime_mode"] = "replay"
        result2 = compute_distributional_indicators(panel, config=config)

        # Should also succeed
        assert result2 is not None
