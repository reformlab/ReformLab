"""Tests for PortfolioComputationStep - multi-policy portfolio execution.

Story 12.3 / FR44: Extend orchestrator to execute policy portfolios.

Tests cover:
- AC1: Multi-policy portfolio execution
- AC2: 10-year portfolio panel output
- AC3: No changes to ComputationAdapter or orchestrator core
- AC4: Backward compatibility with single-policy scenarios
- AC5: Validation and error handling
- AC6: Deterministic execution
- AC7: Portfolio metadata in YearState
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import ComputationResult, PopulationData
from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig
from reformlab.orchestrator.computation_step import (
    COMPUTATION_METADATA_KEY,
    COMPUTATION_RESULT_KEY,
    ComputationStep,
)
from reformlab.orchestrator.panel import PanelOutput
from reformlab.orchestrator.portfolio_step import (
    PORTFOLIO_METADATA_KEY,
    PORTFOLIO_RESULTS_KEY,
    PortfolioComputationStep,
    PortfolioComputationStepError,
    _to_computation_policy,
)
from reformlab.orchestrator.runner import Orchestrator
from reformlab.orchestrator.step import OrchestratorStep
from reformlab.orchestrator.types import OrchestratorConfig, YearState
from reformlab.templates.portfolios.portfolio import (
    PolicyConfig as PortfolioPolicyConfig,
)
from reformlab.templates.portfolios.portfolio import (
    PolicyPortfolio,
)
from reformlab.templates.schema import (
    CarbonTaxParameters,
    PolicyType,
    SubsidyParameters,
)


@pytest.fixture
def year_state() -> YearState:
    """Empty year state for portfolio tests."""
    return YearState(year=2025, data={}, seed=42, metadata={})


# ============================================================================
# AC3: Protocol compliance — no changes to orchestrator core
# ============================================================================


class TestPortfolioStepProtocol:
    """AC3: PortfolioComputationStep satisfies OrchestratorStep protocol."""

    def test_satisfies_orchestrator_step_protocol(
        self, portfolio_computation_step: PortfolioComputationStep
    ) -> None:
        """Given PortfolioComputationStep, then isinstance check passes."""
        assert isinstance(portfolio_computation_step, OrchestratorStep)

    def test_name_property_returns_default(
        self, portfolio_computation_step: PortfolioComputationStep
    ) -> None:
        """Given default step, then name is 'portfolio_computation'."""
        assert portfolio_computation_step.name == "portfolio_computation"

    def test_custom_name(
        self,
        portfolio_mock_adapter: MockAdapter,
        portfolio_population: PopulationData,
        sample_portfolio: PolicyPortfolio,
    ) -> None:
        """Given custom name, then name property returns it."""
        step = PortfolioComputationStep(
            adapter=portfolio_mock_adapter,
            population=portfolio_population,
            portfolio=sample_portfolio,
            name="custom_portfolio",
        )
        assert step.name == "custom_portfolio"

    def test_depends_on_defaults_to_empty(
        self, portfolio_computation_step: PortfolioComputationStep
    ) -> None:
        """Given default step, depends_on is empty tuple."""
        assert portfolio_computation_step.depends_on == ()

    def test_execute_returns_year_state(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given step, execute returns YearState."""
        result = portfolio_computation_step.execute(2025, year_state)
        assert isinstance(result, YearState)


# ============================================================================
# AC1: Multi-policy portfolio execution
# ============================================================================


class TestPortfolioStepExecution:
    """AC1: All policies in portfolio are applied per year."""

    def test_all_policies_computed(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        portfolio_mock_adapter: MockAdapter,
        year_state: YearState,
    ) -> None:
        """Given 3-policy portfolio, adapter.compute() called 3 times."""
        portfolio_computation_step.execute(2025, year_state)
        assert len(portfolio_mock_adapter.call_log) == 3

    def test_merged_result_under_computation_result_key(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio execution, merged result stored under COMPUTATION_RESULT_KEY."""
        result = portfolio_computation_step.execute(2025, year_state)
        assert COMPUTATION_RESULT_KEY in result.data
        comp_result = result.data[COMPUTATION_RESULT_KEY]
        assert isinstance(comp_result, ComputationResult)

    def test_merged_table_has_all_policy_columns(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given 3-policy portfolio, merged table has columns from all policies."""
        result = portfolio_computation_step.execute(2025, year_state)
        merged = result.data[COMPUTATION_RESULT_KEY].output_fields
        cols = merged.column_names
        # First policy (carbon_tax): keeps original names
        assert "household_id" in cols
        assert "tax_burden" in cols
        assert "emissions" in cols
        # Second policy (subsidy): prefixed
        assert "subsidy_subsidy_amount" in cols
        # Third policy (feebate): prefixed
        assert "feebate_net_impact" in cols

    def test_household_id_present_in_merged(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio execution, merged result contains household_id."""
        result = portfolio_computation_step.execute(2025, year_state)
        merged = result.data[COMPUTATION_RESULT_KEY].output_fields
        assert "household_id" in merged.column_names

    def test_merged_row_count_matches_input(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio with 3-row population, merged has 3 rows."""
        result = portfolio_computation_step.execute(2025, year_state)
        merged = result.data[COMPUTATION_RESULT_KEY].output_fields
        assert merged.num_rows == 3


# ============================================================================
# AC2: Merged output for panel compatibility
# ============================================================================


class TestPortfolioStepMergedOutput:
    """AC2: Merged table has columns from all policies with correct prefixing."""

    def test_column_order_is_deterministic(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio, column order is household_id first, then by policy order."""
        result = portfolio_computation_step.execute(2025, year_state)
        merged = result.data[COMPUTATION_RESULT_KEY].output_fields
        assert merged.column_names[0] == "household_id"
        # Carbon tax columns come before subsidy columns, which come before feebate
        tax_idx = merged.column_names.index("tax_burden")
        subsidy_idx = merged.column_names.index("subsidy_subsidy_amount")
        feebate_idx = merged.column_names.index("feebate_net_impact")
        assert tax_idx < subsidy_idx < feebate_idx

    def test_duplicate_policy_types_get_indexed_prefix(
        self,
        portfolio_mock_adapter: MockAdapter,
        portfolio_population: PopulationData,
        year_state: YearState,
    ) -> None:
        """Given two carbon_tax policies, all get {type}_{index}_ prefix."""
        portfolio = PolicyPortfolio(
            name="duplicate-types",
            policies=(
                PortfolioPolicyConfig(
                    policy_type=PolicyType.CARBON_TAX,
                    policy=CarbonTaxParameters(rate_schedule={2025: 44.6}),
                    name="carbon_tax_a",
                ),
                PortfolioPolicyConfig(
                    policy_type=PolicyType.CARBON_TAX,
                    policy=CarbonTaxParameters(rate_schedule={2025: 55.0}),
                    name="carbon_tax_b",
                ),
            ),
        )
        step = PortfolioComputationStep(
            adapter=portfolio_mock_adapter,
            population=portfolio_population,
            portfolio=portfolio,
        )
        result = step.execute(2025, year_state)
        merged = result.data[COMPUTATION_RESULT_KEY].output_fields
        cols = merged.column_names
        # Both should have indexed prefixes
        assert "carbon_tax_0_tax_burden" in cols
        assert "carbon_tax_1_tax_burden" in cols


# ============================================================================
# AC7: Portfolio metadata in YearState
# ============================================================================


class TestPortfolioStepMetadata:
    """AC7: Portfolio metadata in YearState.metadata."""

    def test_portfolio_metadata_key_present(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio execution, PORTFOLIO_METADATA_KEY in metadata."""
        result = portfolio_computation_step.execute(2025, year_state)
        assert PORTFOLIO_METADATA_KEY in result.metadata

    def test_portfolio_metadata_contains_name(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio, metadata contains portfolio name."""
        result = portfolio_computation_step.execute(2025, year_state)
        meta = result.metadata[PORTFOLIO_METADATA_KEY]
        assert meta["portfolio_name"] == "test-3-policy"

    def test_portfolio_metadata_contains_policy_count(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given 3-policy portfolio, metadata has policy_count=3."""
        result = portfolio_computation_step.execute(2025, year_state)
        meta = result.metadata[PORTFOLIO_METADATA_KEY]
        assert meta["policy_count"] == 3

    def test_portfolio_metadata_contains_execution_records(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio, metadata has per-policy execution records."""
        result = portfolio_computation_step.execute(2025, year_state)
        records = result.metadata[PORTFOLIO_METADATA_KEY]["execution_records"]
        assert len(records) == 3
        first = records[0]
        assert first["policy_index"] == 0
        assert first["policy_type"] == "carbon_tax"
        assert first["policy_name"] == "carbon_tax_baseline"
        assert first["adapter_version"] == "mock-portfolio-1.0.0"
        assert first["row_count"] == 3

    def test_portfolio_metadata_contains_execution_order(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio, metadata has execution order list."""
        result = portfolio_computation_step.execute(2025, year_state)
        order = result.metadata[PORTFOLIO_METADATA_KEY]["execution_order"]
        assert order == ["carbon_tax_baseline", "subsidy_green", "feebate_auto"]


class TestPortfolioStepMetadataComputationKey:
    """AC3: COMPUTATION_METADATA_KEY present for runner.py backward compat."""

    def test_computation_metadata_key_present(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio execution, COMPUTATION_METADATA_KEY is in metadata."""
        result = portfolio_computation_step.execute(2025, year_state)
        assert COMPUTATION_METADATA_KEY in result.metadata

    def test_computation_metadata_has_adapter_version(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio, computation metadata has adapter_version."""
        result = portfolio_computation_step.execute(2025, year_state)
        meta = result.metadata[COMPUTATION_METADATA_KEY]
        assert meta["adapter_version"] == "mock-portfolio-1.0.0"


# ============================================================================
# AC6: Deterministic execution
# ============================================================================


class TestPortfolioStepDeterminism:
    """AC6: Identical inputs produce identical outputs."""

    def test_two_runs_produce_identical_outputs(
        self,
        portfolio_population: PopulationData,
        three_policy_portfolio: PolicyPortfolio,
        year_state: YearState,
    ) -> None:
        """Given identical inputs, two runs produce identical YearState."""
        adapter = MockAdapter(
            version_string="mock-det-1.0.0",
            compute_fn=lambda pop, pol, per: pa.table({
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "value": pa.array([10.0, 20.0, 30.0]),
            }),
        )
        step1 = PortfolioComputationStep(
            adapter=adapter,
            population=portfolio_population,
            portfolio=three_policy_portfolio,
        )
        step2 = PortfolioComputationStep(
            adapter=adapter,
            population=portfolio_population,
            portfolio=three_policy_portfolio,
        )

        adapter.call_log.clear()
        result1 = step1.execute(2025, year_state)
        adapter.call_log.clear()
        result2 = step2.execute(2025, year_state)

        # Data comparison
        comp1 = result1.data[COMPUTATION_RESULT_KEY]
        comp2 = result2.data[COMPUTATION_RESULT_KEY]
        assert comp1.output_fields.equals(comp2.output_fields)
        assert comp1.adapter_version == comp2.adapter_version
        assert comp1.period == comp2.period

        # Metadata comparison
        meta1 = result1.metadata[PORTFOLIO_METADATA_KEY]
        meta2 = result2.metadata[PORTFOLIO_METADATA_KEY]
        assert meta1 == meta2


# ============================================================================
# AC5: Validation and error handling
# ============================================================================


class TestPortfolioStepErrorHandling:
    """AC5: Validation and error handling."""

    def test_adapter_failure_raises_portfolio_error(
        self,
        portfolio_population: PopulationData,
        year_state: YearState,
    ) -> None:
        """Given adapter failure at policy[1], PortfolioComputationStepError raised."""
        call_count = 0

        def failing_at_second(
            pop: PopulationData, policy: ComputationPolicyConfig, period: int
        ) -> pa.Table:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("Adapter crashed on subsidy")
            return pa.table({
                "household_id": pa.array([1, 2, 3], type=pa.int64()),
                "value": pa.array([1.0, 2.0, 3.0]),
            })

        adapter = MockAdapter(
            version_string="mock-fail-1.0.0",
            compute_fn=failing_at_second,
        )
        portfolio = PolicyPortfolio(
            name="failing-portfolio",
            policies=(
                PortfolioPolicyConfig(
                    policy_type=PolicyType.CARBON_TAX,
                    policy=CarbonTaxParameters(rate_schedule={2025: 44.6}),
                    name="carbon_tax_ok",
                ),
                PortfolioPolicyConfig(
                    policy_type=PolicyType.SUBSIDY,
                    policy=SubsidyParameters(rate_schedule={2025: 100.0}),
                    name="subsidy_fail",
                ),
            ),
        )
        step = PortfolioComputationStep(
            adapter=adapter,
            population=portfolio_population,
            portfolio=portfolio,
        )

        with pytest.raises(PortfolioComputationStepError) as exc_info:
            step.execute(2025, year_state)

        error = exc_info.value
        assert error.policy_index == 1
        assert error.policy_name == "subsidy_fail"
        assert error.policy_type == "subsidy"
        assert error.year == 2025
        assert error.adapter_version == "mock-fail-1.0.0"
        assert error.original_error is not None
        assert isinstance(error.original_error, RuntimeError)

    def test_error_message_format(
        self,
        portfolio_population: PopulationData,
        year_state: YearState,
    ) -> None:
        """Given adapter failure, error message has structured format."""
        call_count = 0

        def failing_fn(
            pop: PopulationData, policy: ComputationPolicyConfig, period: int
        ) -> pa.Table:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Bad input")
            return pa.table({
                "household_id": pa.array([1], type=pa.int64()),
                "v": pa.array([1.0]),
            })

        adapter = MockAdapter(version_string="v1", compute_fn=failing_fn)
        portfolio = PolicyPortfolio(
            name="err-fmt",
            policies=(
                PortfolioPolicyConfig(
                    policy_type=PolicyType.CARBON_TAX,
                    policy=CarbonTaxParameters(rate_schedule={2025: 10.0}),
                    name="ct",
                ),
                PortfolioPolicyConfig(
                    policy_type=PolicyType.SUBSIDY,
                    policy=SubsidyParameters(rate_schedule={2025: 20.0}),
                    name="sub",
                ),
            ),
        )
        step = PortfolioComputationStep(
            adapter=adapter, population=portfolio_population, portfolio=portfolio
        )

        with pytest.raises(PortfolioComputationStepError, match=r"policy\[1\].*'sub'"):
            step.execute(2030, year_state)


class TestPortfolioStepErrorHandlingVersionFallback:
    """AC5: Adapter with failing version() uses fallback."""

    def test_version_fallback(
        self,
        portfolio_population: PopulationData,
        three_policy_portfolio: PolicyPortfolio,
        year_state: YearState,
    ) -> None:
        """Given adapter with failing version(), uses '<version-unavailable>'."""

        class VersionFailingAdapter:
            def version(self) -> str:
                raise RuntimeError("No version")

            def compute(
                self,
                population: PopulationData,
                policy: ComputationPolicyConfig,
                period: int,
            ) -> ComputationResult:
                return ComputationResult(
                    output_fields=pa.table({
                        "household_id": pa.array([1, 2, 3], type=pa.int64()),
                        "value": pa.array([1.0, 2.0, 3.0]),
                    }),
                    adapter_version="unused",
                    period=period,
                )

        step = PortfolioComputationStep(
            adapter=VersionFailingAdapter(),  # type: ignore[arg-type]
            population=portfolio_population,
            portfolio=three_policy_portfolio,
        )
        result = step.execute(2025, year_state)
        meta = result.metadata[COMPUTATION_METADATA_KEY]
        assert meta["adapter_version"] == "<version-unavailable>"


# ============================================================================
# AC4: Backward compatibility with single-policy scenarios
# ============================================================================


class TestPortfolioStepBackwardCompat:
    """AC4: Existing ComputationStep unchanged, works alongside portfolio."""

    def test_existing_computation_step_unchanged(
        self,
        year_state: YearState,
    ) -> None:
        """Given single-policy ComputationStep, works as before."""
        output = pa.table({"tax": pa.array([100.0, 200.0])})
        adapter = MockAdapter(version_string="mock-1.0.0", default_output=output)
        population = PopulationData(
            tables={"individu": pa.table({"id": [1, 2]})},
        )
        policy = ComputationPolicyConfig(
            policy={"rate": 44.6}, name="single-policy"
        )
        step = ComputationStep(
            adapter=adapter, population=population, policy=policy
        )
        result = step.execute(2025, year_state)
        assert COMPUTATION_RESULT_KEY in result.data
        assert result.data[COMPUTATION_RESULT_KEY].output_fields.equals(output)

    def test_portfolio_step_in_pipeline_with_carry_forward(
        self,
        portfolio_computation_step: PortfolioComputationStep,
    ) -> None:
        """Given pipeline with PortfolioComputationStep + callable, runs OK."""
        from reformlab.orchestrator.carry_forward import (
            CarryForwardConfig,
            CarryForwardStep,
        )

        carry_config = CarryForwardConfig(rules=())
        carry_step = CarryForwardStep(config=carry_config)
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            step_pipeline=(portfolio_computation_step, carry_step),
        )
        orchestrator = Orchestrator(config)
        result = orchestrator.run()
        assert result.success


# ============================================================================
# AC1, AC4: Full orchestrator pipeline integration
# ============================================================================


class TestPortfolioStepInPipeline:
    """AC1, AC4: Full orchestrator run with portfolio step over multiple years."""

    def test_multi_year_pipeline(
        self,
        portfolio_computation_step: PortfolioComputationStep,
    ) -> None:
        """Given 3-year run with portfolio step, each year has portfolio results."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            step_pipeline=(portfolio_computation_step,),
            seed=42,
        )
        orchestrator = Orchestrator(config)
        result = orchestrator.run()

        assert result.success
        assert len(result.yearly_states) == 3
        for year in (2025, 2026, 2027):
            state = result.yearly_states[year]
            assert COMPUTATION_RESULT_KEY in state.data
            assert PORTFOLIO_METADATA_KEY in state.metadata


# ============================================================================
# AC2: Panel integration
# ============================================================================


class TestPortfolioStepPanelIntegration:
    """AC2: PanelOutput.from_orchestrator_result() works with portfolio results."""

    def test_panel_from_portfolio_run(
        self,
        portfolio_computation_step: PortfolioComputationStep,
    ) -> None:
        """Given portfolio run over 3 years, panel has all columns across years."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2027,
            step_pipeline=(portfolio_computation_step,),
            seed=42,
        )
        orchestrator = Orchestrator(config)
        result = orchestrator.run()
        assert result.success

        panel = PanelOutput.from_orchestrator_result(result)
        assert panel.table.num_rows == 9  # 3 households * 3 years
        assert "household_id" in panel.table.column_names
        assert "year" in panel.table.column_names
        # Policy columns present
        assert "tax_burden" in panel.table.column_names

    def test_panel_export_csv(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        tmp_path: "Path",  # noqa: F821
    ) -> None:
        """Given portfolio panel, CSV export works."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            step_pipeline=(portfolio_computation_step,),
        )
        result = Orchestrator(config).run()
        panel = PanelOutput.from_orchestrator_result(result)
        csv_path = panel.to_csv(tmp_path / "panel.csv")
        assert csv_path.exists()

    def test_panel_export_parquet(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        tmp_path: "Path",  # noqa: F821
    ) -> None:
        """Given portfolio panel, Parquet export works."""
        config = OrchestratorConfig(
            start_year=2025,
            end_year=2025,
            step_pipeline=(portfolio_computation_step,),
        )
        result = Orchestrator(config).run()
        panel = PanelOutput.from_orchestrator_result(result)
        pq_path = panel.to_parquet(tmp_path / "panel.parquet")
        assert pq_path.exists()


# ============================================================================
# AC1: Bridge function
# ============================================================================


class TestPolicyConfigBridge:
    """AC1: _to_computation_policy() converts portfolio→computation PolicyConfig."""

    def test_basic_conversion(self) -> None:
        """Given portfolio PolicyConfig, bridge produces computation PolicyConfig."""
        portfolio_policy = PortfolioPolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(
                rate_schedule={2025: 44.6, 2026: 50.0},
                exemptions=({"category": "agriculture", "rate": 0.5},),
            ),
            name="test-ct",
        )
        comp_policy = _to_computation_policy(portfolio_policy)
        assert comp_policy.name == "test-ct"
        assert comp_policy.description == "carbon_tax policy"
        assert comp_policy.policy["rate_schedule"] == {2025: 44.6, 2026: 50.0}
        assert len(comp_policy.policy["exemptions"]) == 1

    def test_name_fallback_to_policy_type(self) -> None:
        """Given portfolio PolicyConfig with no name, uses policy_type.value."""
        portfolio_policy = PortfolioPolicyConfig(
            policy_type=PolicyType.SUBSIDY,
            policy=SubsidyParameters(rate_schedule={2025: 100.0}),
        )
        comp_policy = _to_computation_policy(portfolio_policy)
        assert comp_policy.name == "subsidy"

    def test_fields_preserved(self) -> None:
        """Given rich PolicyParameters, all fields preserved in dict."""
        portfolio_policy = PortfolioPolicyConfig(
            policy_type=PolicyType.CARBON_TAX,
            policy=CarbonTaxParameters(
                rate_schedule={2025: 44.6},
                redistribution_type="lump_sum",
                income_weights={"decile_1": 1.5},
            ),
            name="rich-ct",
        )
        comp_policy = _to_computation_policy(portfolio_policy)
        assert comp_policy.policy["redistribution_type"] == "lump_sum"
        assert comp_policy.policy["income_weights"] == {"decile_1": 1.5}


# ============================================================================
# AC1: Per-policy results
# ============================================================================


class TestPerPolicyResults:
    """AC1: Individual ComputationResult per policy stored in state.data."""

    def test_portfolio_results_stored(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio execution, PORTFOLIO_RESULTS_KEY has individual results."""
        result = portfolio_computation_step.execute(2025, year_state)
        assert PORTFOLIO_RESULTS_KEY in result.data
        per_policy = result.data[PORTFOLIO_RESULTS_KEY]
        assert len(per_policy) == 3
        assert all(isinstance(r, ComputationResult) for r in per_policy)

    def test_per_policy_results_accessible_by_index(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio results, each policy's result is accessible by index."""
        result = portfolio_computation_step.execute(2025, year_state)
        per_policy = result.data[PORTFOLIO_RESULTS_KEY]
        # First policy (carbon_tax) should have tax_burden column
        assert "tax_burden" in per_policy[0].output_fields.column_names
        # Second policy (subsidy) should have subsidy_amount column
        assert "subsidy_amount" in per_policy[1].output_fields.column_names
        # Third policy (feebate) should have net_impact column
        assert "net_impact" in per_policy[2].output_fields.column_names


# ============================================================================
# Stable key constants
# ============================================================================


class TestPortfolioStepKeys:
    """Stable string constants for portfolio keys."""

    def test_portfolio_metadata_key_is_stable(self) -> None:
        assert PORTFOLIO_METADATA_KEY == "portfolio_metadata"

    def test_portfolio_results_key_is_stable(self) -> None:
        assert PORTFOLIO_RESULTS_KEY == "portfolio_results"


# ============================================================================
# Merge validation: household_id consistency (Code Review Synthesis)
# ============================================================================


class TestPortfolioStepMergeValidation:
    """Merge validates household_id uniqueness and set consistency."""

    def test_mismatched_household_ids_raises_error(
        self,
        portfolio_population: PopulationData,
        year_state: YearState,
    ) -> None:
        """Given policies returning different household_id sets, error is raised."""
        call_count = 0

        def mismatched_fn(
            pop: PopulationData, policy: ComputationPolicyConfig, period: int
        ) -> pa.Table:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return pa.table({
                    "household_id": pa.array([1, 2, 3], type=pa.int64()),
                    "val": pa.array([1.0, 2.0, 3.0]),
                })
            return pa.table({
                "household_id": pa.array([2, 3, 4], type=pa.int64()),
                "val": pa.array([4.0, 5.0, 6.0]),
            })

        adapter = MockAdapter(version_string="v1", compute_fn=mismatched_fn)
        portfolio = PolicyPortfolio(
            name="mismatch",
            policies=(
                PortfolioPolicyConfig(
                    policy_type=PolicyType.CARBON_TAX,
                    policy=CarbonTaxParameters(rate_schedule={2025: 10.0}),
                    name="ct",
                ),
                PortfolioPolicyConfig(
                    policy_type=PolicyType.SUBSIDY,
                    policy=SubsidyParameters(rate_schedule={2025: 20.0}),
                    name="sub",
                ),
            ),
        )
        step = PortfolioComputationStep(
            adapter=adapter, population=portfolio_population, portfolio=portfolio
        )
        with pytest.raises(
            PortfolioComputationStepError, match="household_id set differs"
        ):
            step.execute(2025, year_state)

    def test_duplicate_household_ids_raises_error(
        self,
        portfolio_population: PopulationData,
        year_state: YearState,
    ) -> None:
        """Given a policy with duplicate household_ids, error is raised."""

        def duplicate_fn(
            pop: PopulationData, policy: ComputationPolicyConfig, period: int
        ) -> pa.Table:
            return pa.table({
                "household_id": pa.array([1, 1, 2], type=pa.int64()),
                "val": pa.array([1.0, 2.0, 3.0]),
            })

        adapter = MockAdapter(version_string="v1", compute_fn=duplicate_fn)
        portfolio = PolicyPortfolio(
            name="dups",
            policies=(
                PortfolioPolicyConfig(
                    policy_type=PolicyType.CARBON_TAX,
                    policy=CarbonTaxParameters(rate_schedule={2025: 10.0}),
                    name="ct",
                ),
                PortfolioPolicyConfig(
                    policy_type=PolicyType.SUBSIDY,
                    policy=SubsidyParameters(rate_schedule={2025: 20.0}),
                    name="sub",
                ),
            ),
        )
        step = PortfolioComputationStep(
            adapter=adapter, population=portfolio_population, portfolio=portfolio
        )
        with pytest.raises(
            PortfolioComputationStepError, match="duplicate household_id"
        ):
            step.execute(2025, year_state)

    def test_per_policy_results_stored_as_tuple(
        self,
        portfolio_computation_step: PortfolioComputationStep,
        year_state: YearState,
    ) -> None:
        """Given portfolio execution, per-policy results stored as immutable tuple."""
        result = portfolio_computation_step.execute(2025, year_state)
        per_policy = result.data[PORTFOLIO_RESULTS_KEY]
        assert isinstance(per_policy, tuple)
