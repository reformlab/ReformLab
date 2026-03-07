"""Tests for eligibility filtering for discrete choice performance optimization.

Tests EligibilityRule, EligibilityFilter, EligibilityInfo types,
evaluate_eligibility and filter_population_by_eligibility functions,
EligibilityMergeStep, DiscreteChoiceStep with eligibility integration,
and full pipeline integration.

Story 14-5: Implement Eligibility Filtering for Performance Optimization (FR48).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pyarrow as pa
import pytest

from reformlab.computation.mock_adapter import MockAdapter
from reformlab.computation.types import PolicyConfig, PopulationData
from reformlab.discrete_choice.eligibility import (
    DISCRETE_CHOICE_ELIGIBILITY_KEY,
    EligibilityFilter,
    EligibilityInfo,
    EligibilityMergeStep,
    EligibilityRule,
    evaluate_eligibility,
    filter_population_by_eligibility,
)
from reformlab.discrete_choice.errors import DiscreteChoiceError
from reformlab.discrete_choice.expansion import (
    TRACKING_COL_ALTERNATIVE_ID,
    TRACKING_COL_ORIGINAL_INDEX,
)
from reformlab.discrete_choice.logit import DISCRETE_CHOICE_RESULT_KEY, LogitChoiceStep
from reformlab.discrete_choice.step import (
    DISCRETE_CHOICE_METADATA_KEY,
    DiscreteChoiceStep,
)
from reformlab.discrete_choice.types import (
    Alternative,
    ChoiceResult,
    TasteParameters,
)
from reformlab.orchestrator.step import StepRegistry, is_protocol_step
from reformlab.orchestrator.types import YearState

# ============================================================================
# Helpers
# ============================================================================


def _make_population(
    n: int,
    *,
    incomes: list[float] | None = None,
    ages: list[int] | None = None,
    entity_key: str = "menage",
) -> PopulationData:
    """Build a test PopulationData with household_id, income, fuel_cost, and optionally age."""
    if incomes is None:
        incomes = [30000.0 + i * 10000.0 for i in range(n)]
    cols: dict[str, pa.Array] = {
        "household_id": pa.array(list(range(n)), type=pa.int64()),
        "income": pa.array(incomes),
        "fuel_cost": pa.array([0.15] * n),
    }
    if ages is not None:
        cols["age"] = pa.array(ages, type=pa.int64())
    return PopulationData(
        tables={entity_key: pa.table(cols)},
        metadata={"source": "test"},
    )


def _make_state(
    population: PopulationData,
    *,
    seed: int = 42,
    extra_data: dict | None = None,
) -> YearState:
    """Build a YearState with population data."""
    data: dict = {"population_data": population}
    if extra_data:
        data.update(extra_data)
    return YearState(year=2025, data=data, seed=seed)


def _make_choice_result(
    n: int,
    alt_ids: tuple[str, ...],
    *,
    chosen: list[str] | None = None,
    seed: int = 42,
) -> ChoiceResult:
    """Build a test ChoiceResult with uniform probabilities."""
    m = len(alt_ids)
    if chosen is None:
        chosen = [alt_ids[i % m] for i in range(n)]
    prob = 1.0 / m
    probs = {aid: pa.array([prob] * n) for aid in alt_ids}
    utils = {aid: pa.array([0.5] * n) for aid in alt_ids}
    return ChoiceResult(
        chosen=pa.array(chosen),
        probabilities=pa.table(probs),
        utilities=pa.table(utils),
        alternative_ids=alt_ids,
        seed=seed,
    )


def _discrete_choice_compute_fn(
    population: PopulationData,
    policy: PolicyConfig,
    period: int,
) -> pa.Table:
    """Compute function that returns tracking columns + total_cost."""
    entity_key = sorted(population.tables.keys())[0]
    table = population.tables[entity_key]
    income = table.column("income").to_pylist()
    fuel_cost = table.column("fuel_cost").to_pylist()
    total_cost = [i * f for i, f in zip(income, fuel_cost)]
    result_cols: dict[str, pa.Array] = {
        "total_cost": pa.array(total_cost),
    }
    if TRACKING_COL_ALTERNATIVE_ID in table.column_names:
        result_cols[TRACKING_COL_ALTERNATIVE_ID] = table.column(
            TRACKING_COL_ALTERNATIVE_ID
        )
    if TRACKING_COL_ORIGINAL_INDEX in table.column_names:
        result_cols[TRACKING_COL_ORIGINAL_INDEX] = table.column(
            TRACKING_COL_ORIGINAL_INDEX
        )
    return pa.table(result_cols)


class _MockDomain:
    """Test domain with 3 alternatives."""

    @property
    def name(self) -> str:
        return "test_domain"

    @property
    def alternatives(self) -> tuple[Alternative, ...]:
        return (
            Alternative(id="keep_current", name="Keep Current", attributes={}),
            Alternative(id="option_a", name="Option A", attributes={"fuel_cost": 0.10}),
            Alternative(id="option_b", name="Option B", attributes={"fuel_cost": 0.30}),
        )

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
# TestEligibilityRule (Task 7.1, AC-1)
# ============================================================================


class TestEligibilityRule:
    """Tests for EligibilityRule frozen dataclass."""

    def test_construction_valid_operators(self) -> None:
        """AC-1: all valid operators are accepted."""
        for op in ("gt", "ge", "lt", "le", "eq", "ne"):
            rule = EligibilityRule(column="income", operator=op, threshold=30000)
            assert rule.operator == op

    def test_construction_with_description(self) -> None:
        """AC-1: description field."""
        rule = EligibilityRule(
            column="age", operator="gt", threshold=10, description="Old vehicles"
        )
        assert rule.description == "Old vehicles"

    def test_default_description_empty(self) -> None:
        """AC-1: default description is empty string."""
        rule = EligibilityRule(column="income", operator="gt", threshold=0)
        assert rule.description == ""

    def test_invalid_operator_raises(self) -> None:
        """AC-1: invalid operator raises DiscreteChoiceError at construction."""
        with pytest.raises(DiscreteChoiceError, match="Invalid eligibility operator"):
            EligibilityRule(column="income", operator="between", threshold=0)

    def test_frozen(self) -> None:
        """AC-1: EligibilityRule is frozen."""
        rule = EligibilityRule(column="income", operator="gt", threshold=0)
        with pytest.raises(FrozenInstanceError):
            rule.column = "age"  # type: ignore[misc]

    def test_threshold_types(self) -> None:
        """AC-1: threshold supports int, float, str."""
        r_int = EligibilityRule(column="age", operator="gt", threshold=10)
        assert r_int.threshold == 10
        r_float = EligibilityRule(column="income", operator="ge", threshold=30000.5)
        assert r_float.threshold == 30000.5
        r_str = EligibilityRule(column="type", operator="eq", threshold="gas")
        assert r_str.threshold == "gas"


# ============================================================================
# TestEligibilityFilter (Task 7.2, AC-1)
# ============================================================================


class TestEligibilityFilter:
    """Tests for EligibilityFilter frozen dataclass."""

    def test_construction_defaults(self) -> None:
        """AC-1: default values."""
        ef = EligibilityFilter(rules=())
        assert ef.logic == "all"
        assert ef.default_choice == "keep_current"
        assert ef.entity_key == "menage"
        assert ef.description == ""

    def test_construction_with_rules(self) -> None:
        """AC-1: filter with rules."""
        rule = EligibilityRule(column="income", operator="gt", threshold=30000)
        ef = EligibilityFilter(rules=(rule,), logic="any", description="Test filter")
        assert len(ef.rules) == 1
        assert ef.logic == "any"
        assert ef.description == "Test filter"

    def test_invalid_logic_raises(self) -> None:
        """AC-1: invalid logic raises DiscreteChoiceError."""
        with pytest.raises(DiscreteChoiceError, match="Invalid eligibility logic"):
            EligibilityFilter(rules=(), logic="xor")

    def test_valid_logic_values(self) -> None:
        """AC-1: both 'all' and 'any' are valid."""
        EligibilityFilter(rules=(), logic="all")
        EligibilityFilter(rules=(), logic="any")

    def test_frozen(self) -> None:
        """AC-1: EligibilityFilter is frozen."""
        ef = EligibilityFilter(rules=())
        with pytest.raises(FrozenInstanceError):
            ef.logic = "any"  # type: ignore[misc]


# ============================================================================
# TestEligibilityInfo (Task 7.3, AC-9)
# ============================================================================


class TestEligibilityInfo:
    """Tests for EligibilityInfo frozen dataclass."""

    def test_construction(self) -> None:
        """AC-9: EligibilityInfo stores all fields."""
        rule = EligibilityRule(column="income", operator="gt", threshold=30000)
        info = EligibilityInfo(
            n_total=100,
            n_eligible=30,
            eligible_indices=(0, 5, 10),
            default_choice="keep_current",
            filter_description="Income > 30k",
            alternative_ids=("keep_current", "option_a"),
            filter_rules=(rule,),
        )
        assert info.n_total == 100
        assert info.n_eligible == 30
        assert info.eligible_indices == (0, 5, 10)
        assert info.default_choice == "keep_current"
        assert info.filter_description == "Income > 30k"
        assert info.alternative_ids == ("keep_current", "option_a")
        assert info.filter_rules == (rule,)

    def test_frozen(self) -> None:
        """AC-9: EligibilityInfo is frozen."""
        info = EligibilityInfo(
            n_total=10,
            n_eligible=5,
            eligible_indices=(0, 1, 2, 3, 4),
            default_choice="keep_current",
            filter_description="",
            alternative_ids=("a",),
            filter_rules=(),
        )
        with pytest.raises(FrozenInstanceError):
            info.n_total = 20  # type: ignore[misc]


# ============================================================================
# TestEvaluateEligibility (Task 7.4, AC-2)
# ============================================================================


class TestEvaluateEligibility:
    """Tests for evaluate_eligibility function."""

    def _make_table(self) -> pa.Table:
        """5-row table with income and age columns."""
        return pa.table({
            "income": pa.array([20000.0, 30000.0, 40000.0, 50000.0, 60000.0]),
            "age": pa.array([5, 10, 15, 20, 25], type=pa.int64()),
        })

    def test_single_rule_gt(self) -> None:
        """AC-2: greater than threshold."""
        table = self._make_table()
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="income", operator="gt", threshold=30000.0),)
        )
        mask = evaluate_eligibility(table, ef)
        assert mask.to_pylist() == [False, False, True, True, True]

    def test_single_rule_ge(self) -> None:
        """AC-2: greater than or equal."""
        table = self._make_table()
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="income", operator="ge", threshold=30000.0),)
        )
        mask = evaluate_eligibility(table, ef)
        assert mask.to_pylist() == [False, True, True, True, True]

    def test_single_rule_lt(self) -> None:
        """AC-2: less than."""
        table = self._make_table()
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="income", operator="lt", threshold=40000.0),)
        )
        mask = evaluate_eligibility(table, ef)
        assert mask.to_pylist() == [True, True, False, False, False]

    def test_single_rule_le(self) -> None:
        """AC-2: less than or equal."""
        table = self._make_table()
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="income", operator="le", threshold=40000.0),)
        )
        mask = evaluate_eligibility(table, ef)
        assert mask.to_pylist() == [True, True, True, False, False]

    def test_single_rule_eq(self) -> None:
        """AC-2: equal."""
        table = self._make_table()
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="age", operator="eq", threshold=15),)
        )
        mask = evaluate_eligibility(table, ef)
        assert mask.to_pylist() == [False, False, True, False, False]

    def test_single_rule_ne(self) -> None:
        """AC-2: not equal."""
        table = self._make_table()
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="age", operator="ne", threshold=15),)
        )
        mask = evaluate_eligibility(table, ef)
        assert mask.to_pylist() == [True, True, False, True, True]

    def test_multiple_rules_and_logic(self) -> None:
        """AC-2: multiple rules with AND logic."""
        table = self._make_table()
        ef = EligibilityFilter(
            rules=(
                EligibilityRule(column="income", operator="ge", threshold=30000.0),
                EligibilityRule(column="age", operator="gt", threshold=10),
            ),
            logic="all",
        )
        mask = evaluate_eligibility(table, ef)
        # income >= 30k: [F, T, T, T, T], age > 10: [F, F, T, T, T] → AND: [F, F, T, T, T]
        assert mask.to_pylist() == [False, False, True, True, True]

    def test_multiple_rules_or_logic(self) -> None:
        """AC-2: multiple rules with OR logic."""
        table = self._make_table()
        ef = EligibilityFilter(
            rules=(
                EligibilityRule(column="income", operator="lt", threshold=25000.0),
                EligibilityRule(column="age", operator="ge", threshold=25),
            ),
            logic="any",
        )
        mask = evaluate_eligibility(table, ef)
        # income < 25k: [T, F, F, F, F], age >= 25: [F, F, F, F, T] → OR: [T, F, F, F, T]
        assert mask.to_pylist() == [True, False, False, False, True]

    def test_missing_column_raises(self) -> None:
        """AC-2: missing column raises DiscreteChoiceError."""
        table = self._make_table()
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="nonexistent", operator="gt", threshold=0),)
        )
        with pytest.raises(DiscreteChoiceError, match="nonexistent.*not found"):
            evaluate_eligibility(table, ef)

    def test_empty_rules_all_eligible(self) -> None:
        """AC-2: empty rules → all households eligible."""
        table = self._make_table()
        ef = EligibilityFilter(rules=())
        mask = evaluate_eligibility(table, ef)
        assert mask.to_pylist() == [True, True, True, True, True]

    def test_all_true_result(self) -> None:
        """AC-2: all households match rule."""
        table = self._make_table()
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="income", operator="gt", threshold=0.0),)
        )
        mask = evaluate_eligibility(table, ef)
        assert all(mask.to_pylist())

    def test_all_false_result(self) -> None:
        """AC-2: no households match rule."""
        table = self._make_table()
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="income", operator="gt", threshold=100000.0),)
        )
        mask = evaluate_eligibility(table, ef)
        assert not any(mask.to_pylist())

    def test_string_threshold(self) -> None:
        """AC-2: string threshold with eq operator."""
        table = pa.table({"type": pa.array(["gas", "electric", "gas", "heat_pump", "gas"])})
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="type", operator="eq", threshold="gas"),)
        )
        mask = evaluate_eligibility(table, ef)
        assert mask.to_pylist() == [True, False, True, False, True]


# ============================================================================
# TestFilterPopulation (Task 7.5, AC-3)
# ============================================================================


class TestFilterPopulation:
    """Tests for filter_population_by_eligibility function."""

    def test_correct_filtering(self) -> None:
        """AC-3: filters entity table to eligible rows only."""
        pop = _make_population(5, incomes=[10.0, 20.0, 30.0, 40.0, 50.0])
        mask = pa.chunked_array([pa.array([True, False, True, False, True])])
        filtered, indices = filter_population_by_eligibility(pop, mask, "menage")
        assert filtered.tables["menage"].num_rows == 3
        assert indices == (0, 2, 4)
        # Check actual values
        filtered_incomes = filtered.tables["menage"].column("income").to_pylist()
        assert filtered_incomes == [10.0, 30.0, 50.0]

    def test_eligible_indices(self) -> None:
        """AC-3: eligible_indices match mask positions."""
        pop = _make_population(4, incomes=[10.0, 20.0, 30.0, 40.0])
        mask = pa.chunked_array([pa.array([False, True, True, False])])
        _, indices = filter_population_by_eligibility(pop, mask, "menage")
        assert indices == (1, 2)

    def test_entity_key_not_found_raises(self) -> None:
        """AC-3: missing entity_key raises DiscreteChoiceError."""
        pop = _make_population(3)
        mask = pa.chunked_array([pa.array([True, True, True])])
        with pytest.raises(DiscreteChoiceError, match="Entity key.*not found"):
            filter_population_by_eligibility(pop, mask, "nonexistent")

    def test_input_not_modified(self) -> None:
        """AC-3: input population is not modified."""
        pop = _make_population(3, incomes=[10.0, 20.0, 30.0])
        original_rows = pop.tables["menage"].num_rows
        mask = pa.chunked_array([pa.array([True, False, True])])
        filter_population_by_eligibility(pop, mask, "menage")
        assert pop.tables["menage"].num_rows == original_rows

    def test_empty_eligible(self) -> None:
        """AC-10: N'=0 (all ineligible)."""
        pop = _make_population(3)
        mask = pa.chunked_array([pa.array([False, False, False])])
        filtered, indices = filter_population_by_eligibility(pop, mask, "menage")
        assert filtered.tables["menage"].num_rows == 0
        assert indices == ()

    def test_all_eligible(self) -> None:
        """AC-10: N'=N (all eligible)."""
        pop = _make_population(3)
        mask = pa.chunked_array([pa.array([True, True, True])])
        filtered, indices = filter_population_by_eligibility(pop, mask, "menage")
        assert filtered.tables["menage"].num_rows == 3
        assert indices == (0, 1, 2)

    def test_only_entity_key_table_in_filtered(self) -> None:
        """AC-3: filtered population contains only entity_key table."""
        table_menage = pa.table({
            "household_id": pa.array([0, 1], type=pa.int64()),
            "income": pa.array([30000.0, 50000.0]),
            "fuel_cost": pa.array([0.15, 0.20]),
        })
        table_individu = pa.table({
            "person_id": pa.array([0, 1, 2], type=pa.int64()),
        })
        pop = PopulationData(
            tables={"menage": table_menage, "individu": table_individu},
            metadata={"source": "test"},
        )
        mask = pa.chunked_array([pa.array([True, False])])
        filtered, _ = filter_population_by_eligibility(pop, mask, "menage")
        assert "menage" in filtered.tables
        assert "individu" not in filtered.tables

    def test_metadata_preserved(self) -> None:
        """AC-3: metadata is preserved in filtered population."""
        pop = _make_population(2)
        mask = pa.chunked_array([pa.array([True, True])])
        filtered, _ = filter_population_by_eligibility(pop, mask, "menage")
        assert filtered.metadata == pop.metadata


# ============================================================================
# TestEligibilityMergeStep (Task 7.6, AC-5)
# ============================================================================


class TestEligibilityMergeStep:
    """Tests for EligibilityMergeStep."""

    def test_protocol_compliance(self) -> None:
        """AC-5: EligibilityMergeStep satisfies OrchestratorStep protocol."""
        step = EligibilityMergeStep()
        assert is_protocol_step(step)

    def test_step_registry(self) -> None:
        """AC-5: EligibilityMergeStep registers in StepRegistry."""
        registry = StepRegistry()
        # Need logit_choice step first for dependency
        from reformlab.orchestrator.step import adapt_callable

        logit = adapt_callable(lambda y, s: s, name="logit_choice")
        registry.register(logit)
        step = EligibilityMergeStep()
        registry.register(step)
        pipeline = registry.build_pipeline()
        assert len(pipeline) == 2
        assert pipeline[1].name == "eligibility_merge"

    def test_defaults(self) -> None:
        """AC-5: default name, depends_on, description."""
        step = EligibilityMergeStep()
        assert step.name == "eligibility_merge"
        assert step.depends_on == ("logit_choice",)
        assert "eligibility" in step.description.lower()

    def test_pass_through_no_eligibility_info(self) -> None:
        """AC-5: returns state unchanged when no EligibilityInfo in state."""
        step = EligibilityMergeStep()
        state = YearState(year=2025, data={"some_key": "some_value"}, seed=42)
        result = step.execute(2025, state)
        assert result is state  # exact same object

    def test_merge_correct_chosen(self) -> None:
        """AC-5: eligible get logit choice, ineligible get default_choice."""
        alt_ids = ("keep_current", "option_a", "option_b")
        # 5 total households, indices 1 and 3 are eligible
        # N' = 2 choices from logit
        cr = ChoiceResult(
            chosen=pa.array(["option_a", "option_b"]),
            probabilities=pa.table({
                "keep_current": pa.array([0.2, 0.1]),
                "option_a": pa.array([0.5, 0.3]),
                "option_b": pa.array([0.3, 0.6]),
            }),
            utilities=pa.table({
                "keep_current": pa.array([-1.0, -2.0]),
                "option_a": pa.array([-0.5, -1.5]),
                "option_b": pa.array([-0.8, -0.3]),
            }),
            alternative_ids=alt_ids,
            seed=42,
        )
        info = EligibilityInfo(
            n_total=5,
            n_eligible=2,
            eligible_indices=(1, 3),
            default_choice="keep_current",
            filter_description="Test",
            alternative_ids=alt_ids,
            filter_rules=(),
        )
        state = YearState(
            year=2025,
            data={
                DISCRETE_CHOICE_RESULT_KEY: cr,
                DISCRETE_CHOICE_ELIGIBILITY_KEY: info,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
            seed=42,
        )
        step = EligibilityMergeStep()
        result = step.execute(2025, state)

        merged_cr = result.data[DISCRETE_CHOICE_RESULT_KEY]
        assert isinstance(merged_cr, ChoiceResult)
        chosen = merged_cr.chosen.to_pylist()
        assert len(chosen) == 5
        # Indices 0, 2, 4 = ineligible → "keep_current"
        # Index 1 → "option_a", Index 3 → "option_b"
        assert chosen == ["keep_current", "option_a", "keep_current", "option_b", "keep_current"]

    def test_merge_probabilities(self) -> None:
        """AC-5: ineligible have 1.0 for default, 0.0 for others."""
        alt_ids = ("keep_current", "option_a")
        cr = ChoiceResult(
            chosen=pa.array(["option_a"]),
            probabilities=pa.table({
                "keep_current": pa.array([0.3]),
                "option_a": pa.array([0.7]),
            }),
            utilities=pa.table({
                "keep_current": pa.array([-1.0]),
                "option_a": pa.array([-0.5]),
            }),
            alternative_ids=alt_ids,
            seed=42,
        )
        info = EligibilityInfo(
            n_total=3,
            n_eligible=1,
            eligible_indices=(1,),
            default_choice="keep_current",
            filter_description="",
            alternative_ids=alt_ids,
            filter_rules=(),
        )
        state = YearState(
            year=2025,
            data={
                DISCRETE_CHOICE_RESULT_KEY: cr,
                DISCRETE_CHOICE_ELIGIBILITY_KEY: info,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
            seed=42,
        )
        step = EligibilityMergeStep()
        result = step.execute(2025, state)
        merged = result.data[DISCRETE_CHOICE_RESULT_KEY]

        # Index 0: ineligible
        assert merged.probabilities.column("keep_current")[0].as_py() == 1.0
        assert merged.probabilities.column("option_a")[0].as_py() == 0.0
        # Index 1: eligible (from logit)
        assert merged.probabilities.column("keep_current")[1].as_py() == 0.3
        assert merged.probabilities.column("option_a")[1].as_py() == 0.7
        # Index 2: ineligible
        assert merged.probabilities.column("keep_current")[2].as_py() == 1.0
        assert merged.probabilities.column("option_a")[2].as_py() == 0.0

    def test_merge_utilities(self) -> None:
        """AC-5: ineligible have utility 0.0 for all alternatives."""
        alt_ids = ("keep_current", "option_a")
        cr = ChoiceResult(
            chosen=pa.array(["option_a"]),
            probabilities=pa.table({
                "keep_current": pa.array([0.3]),
                "option_a": pa.array([0.7]),
            }),
            utilities=pa.table({
                "keep_current": pa.array([-1.0]),
                "option_a": pa.array([-0.5]),
            }),
            alternative_ids=alt_ids,
            seed=42,
        )
        info = EligibilityInfo(
            n_total=2,
            n_eligible=1,
            eligible_indices=(0,),
            default_choice="keep_current",
            filter_description="",
            alternative_ids=alt_ids,
            filter_rules=(),
        )
        state = YearState(
            year=2025,
            data={
                DISCRETE_CHOICE_RESULT_KEY: cr,
                DISCRETE_CHOICE_ELIGIBILITY_KEY: info,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
            seed=42,
        )
        step = EligibilityMergeStep()
        result = step.execute(2025, state)
        merged = result.data[DISCRETE_CHOICE_RESULT_KEY]

        # Index 0: eligible
        assert merged.utilities.column("keep_current")[0].as_py() == -1.0
        assert merged.utilities.column("option_a")[0].as_py() == -0.5
        # Index 1: ineligible → utility 0.0
        assert merged.utilities.column("keep_current")[1].as_py() == 0.0
        assert merged.utilities.column("option_a")[1].as_py() == 0.0

    def test_all_eligible_merge(self) -> None:
        """AC-10: all eligible → 1:1 mapping, identical to no filtering."""
        alt_ids = ("keep_current", "option_a")
        cr = _make_choice_result(3, alt_ids, chosen=["option_a", "keep_current", "option_a"])
        info = EligibilityInfo(
            n_total=3,
            n_eligible=3,
            eligible_indices=(0, 1, 2),
            default_choice="keep_current",
            filter_description="",
            alternative_ids=alt_ids,
            filter_rules=(),
        )
        state = YearState(
            year=2025,
            data={
                DISCRETE_CHOICE_RESULT_KEY: cr,
                DISCRETE_CHOICE_ELIGIBILITY_KEY: info,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
            seed=42,
        )
        step = EligibilityMergeStep()
        result = step.execute(2025, state)
        merged = result.data[DISCRETE_CHOICE_RESULT_KEY]
        assert merged.chosen.to_pylist() == ["option_a", "keep_current", "option_a"]

    def test_all_ineligible_merge(self) -> None:
        """AC-10: all ineligible → all get default_choice."""
        alt_ids = ("keep_current", "option_a")
        # N'=0, empty choice result
        cr = ChoiceResult(
            chosen=pa.array([], type=pa.string()),
            probabilities=pa.table({
                "keep_current": pa.array([], type=pa.float64()),
                "option_a": pa.array([], type=pa.float64()),
            }),
            utilities=pa.table({
                "keep_current": pa.array([], type=pa.float64()),
                "option_a": pa.array([], type=pa.float64()),
            }),
            alternative_ids=alt_ids,
            seed=42,
        )
        info = EligibilityInfo(
            n_total=3,
            n_eligible=0,
            eligible_indices=(),
            default_choice="keep_current",
            filter_description="",
            alternative_ids=alt_ids,
            filter_rules=(),
        )
        state = YearState(
            year=2025,
            data={
                DISCRETE_CHOICE_RESULT_KEY: cr,
                DISCRETE_CHOICE_ELIGIBILITY_KEY: info,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
            seed=42,
        )
        step = EligibilityMergeStep()
        result = step.execute(2025, state)
        merged = result.data[DISCRETE_CHOICE_RESULT_KEY]
        assert merged.chosen.to_pylist() == ["keep_current"] * 3
        # All probabilities for default = 1.0
        assert merged.probabilities.column("keep_current").to_pylist() == [1.0, 1.0, 1.0]
        assert merged.probabilities.column("option_a").to_pylist() == [0.0, 0.0, 0.0]

    def test_eligibility_info_consumed(self) -> None:
        """AC-5: EligibilityInfo is removed from state after merge."""
        alt_ids = ("keep_current", "option_a")
        cr = _make_choice_result(1, alt_ids, chosen=["option_a"])
        info = EligibilityInfo(
            n_total=1,
            n_eligible=1,
            eligible_indices=(0,),
            default_choice="keep_current",
            filter_description="",
            alternative_ids=alt_ids,
            filter_rules=(),
        )
        state = YearState(
            year=2025,
            data={
                DISCRETE_CHOICE_RESULT_KEY: cr,
                DISCRETE_CHOICE_ELIGIBILITY_KEY: info,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
            seed=42,
        )
        step = EligibilityMergeStep()
        result = step.execute(2025, state)
        assert DISCRETE_CHOICE_ELIGIBILITY_KEY not in result.data

    def test_state_immutability(self) -> None:
        """AC-5: original state is not modified."""
        alt_ids = ("keep_current", "option_a")
        cr = _make_choice_result(1, alt_ids, chosen=["option_a"])
        info = EligibilityInfo(
            n_total=2,
            n_eligible=1,
            eligible_indices=(0,),
            default_choice="keep_current",
            filter_description="",
            alternative_ids=alt_ids,
            filter_rules=(),
        )
        state = YearState(
            year=2025,
            data={
                DISCRETE_CHOICE_RESULT_KEY: cr,
                DISCRETE_CHOICE_ELIGIBILITY_KEY: info,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
            seed=42,
        )
        step = EligibilityMergeStep()
        step.execute(2025, state)
        # Original state still has eligibility info
        assert DISCRETE_CHOICE_ELIGIBILITY_KEY in state.data

    def test_metadata_extension(self) -> None:
        """AC-5: metadata extended with eligibility_merge_n_defaulted."""
        alt_ids = ("keep_current", "option_a")
        cr = _make_choice_result(2, alt_ids, chosen=["option_a", "option_a"])
        info = EligibilityInfo(
            n_total=5,
            n_eligible=2,
            eligible_indices=(1, 3),
            default_choice="keep_current",
            filter_description="",
            alternative_ids=alt_ids,
            filter_rules=(),
        )
        state = YearState(
            year=2025,
            data={
                DISCRETE_CHOICE_RESULT_KEY: cr,
                DISCRETE_CHOICE_ELIGIBILITY_KEY: info,
                DISCRETE_CHOICE_METADATA_KEY: {"existing_key": "preserved"},
            },
            seed=42,
        )
        step = EligibilityMergeStep()
        result = step.execute(2025, state)
        meta = result.data[DISCRETE_CHOICE_METADATA_KEY]
        assert meta["eligibility_merge_n_defaulted"] == 3
        assert meta["existing_key"] == "preserved"

    def test_invalid_default_choice_raises(self) -> None:
        """AC-5: default_choice not in alternative_ids raises error."""
        alt_ids = ("option_a", "option_b")
        cr = _make_choice_result(1, alt_ids, chosen=["option_a"])
        info = EligibilityInfo(
            n_total=2,
            n_eligible=1,
            eligible_indices=(0,),
            default_choice="nonexistent",
            filter_description="",
            alternative_ids=alt_ids,
            filter_rules=(),
        )
        state = YearState(
            year=2025,
            data={
                DISCRETE_CHOICE_RESULT_KEY: cr,
                DISCRETE_CHOICE_ELIGIBILITY_KEY: info,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
            seed=42,
        )
        step = EligibilityMergeStep()
        with pytest.raises(DiscreteChoiceError, match="not a valid alternative"):
            step.execute(2025, state)

    def test_choice_result_validation_passes(self) -> None:
        """AC-5: merged ChoiceResult passes __post_init__ validation."""
        alt_ids = ("keep_current", "option_a")
        cr = ChoiceResult(
            chosen=pa.array(["option_a"]),
            probabilities=pa.table({
                "keep_current": pa.array([0.4]),
                "option_a": pa.array([0.6]),
            }),
            utilities=pa.table({
                "keep_current": pa.array([-1.0]),
                "option_a": pa.array([-0.5]),
            }),
            alternative_ids=alt_ids,
            seed=42,
        )
        info = EligibilityInfo(
            n_total=3,
            n_eligible=1,
            eligible_indices=(1,),
            default_choice="keep_current",
            filter_description="",
            alternative_ids=alt_ids,
            filter_rules=(),
        )
        state = YearState(
            year=2025,
            data={
                DISCRETE_CHOICE_RESULT_KEY: cr,
                DISCRETE_CHOICE_ELIGIBILITY_KEY: info,
                DISCRETE_CHOICE_METADATA_KEY: {},
            },
            seed=42,
        )
        step = EligibilityMergeStep()
        result = step.execute(2025, state)
        merged = result.data[DISCRETE_CHOICE_RESULT_KEY]
        # ChoiceResult __post_init__ validates probability sums
        # If we got here, validation passed
        assert merged.probabilities.num_rows == 3
        for i in range(3):
            row_sum = sum(
                merged.probabilities.column(aid)[i].as_py() for aid in alt_ids
            )
            assert abs(row_sum - 1.0) < 1e-10


# ============================================================================
# TestDiscreteChoiceStepWithEligibility (Task 7.7, AC-4)
# ============================================================================


class TestDiscreteChoiceStepWithEligibility:
    """Tests for DiscreteChoiceStep with eligibility filtering."""

    def test_step_with_filter_expands_only_eligible(self) -> None:
        """AC-4/AC-6: only eligible households are expanded."""
        # 5 households, income: 10k, 20k, 30k, 40k, 50k
        # Rule: income > 25000 → 3 eligible (indices 2, 3, 4)
        pop = _make_population(5, incomes=[10000.0, 20000.0, 30000.0, 40000.0, 50000.0])
        domain = _MockDomain()
        adapter = MockAdapter(
            version_string="test-1.0",
            compute_fn=_discrete_choice_compute_fn,
        )
        policy = PolicyConfig(policy={}, name="test")
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="income", operator="gt", threshold=25000.0),),
            default_choice="keep_current",
            description="Income > 25k",
        )
        step = DiscreteChoiceStep(
            adapter=adapter,
            domain=domain,
            policy=policy,
            eligibility_filter=ef,
        )
        state = _make_state(pop)
        result = step.execute(2025, state)

        # Cost matrix should have 3 rows (not 5)
        cost_matrix = result.data["discrete_choice_cost_matrix"]
        assert cost_matrix.n_households == 3
        # Adapter called with 3 × 3 = 9 rows (not 15)
        assert adapter.call_log[0]["population_row_count"] == 9

    def test_step_without_filter_expands_all(self) -> None:
        """AC-4: backward compatibility — no filter → full expansion."""
        pop = _make_population(3)
        domain = _MockDomain()
        adapter = MockAdapter(
            version_string="test-1.0",
            compute_fn=_discrete_choice_compute_fn,
        )
        policy = PolicyConfig(policy={}, name="test")
        step = DiscreteChoiceStep(
            adapter=adapter,
            domain=domain,
            policy=policy,
        )
        state = _make_state(pop)
        result = step.execute(2025, state)

        cost_matrix = result.data["discrete_choice_cost_matrix"]
        assert cost_matrix.n_households == 3
        # Adapter called with 3 × 3 = 9 rows
        assert adapter.call_log[0]["population_row_count"] == 9

    def test_eligibility_info_stored_in_state(self) -> None:
        """AC-4: EligibilityInfo stored in state when filter applied."""
        pop = _make_population(4, incomes=[10000.0, 20000.0, 30000.0, 40000.0])
        domain = _MockDomain()
        adapter = MockAdapter(
            version_string="test-1.0",
            compute_fn=_discrete_choice_compute_fn,
        )
        policy = PolicyConfig(policy={}, name="test")
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="income", operator="ge", threshold=30000.0),),
        )
        step = DiscreteChoiceStep(
            adapter=adapter,
            domain=domain,
            policy=policy,
            eligibility_filter=ef,
        )
        state = _make_state(pop)
        result = step.execute(2025, state)

        assert DISCRETE_CHOICE_ELIGIBILITY_KEY in result.data
        info = result.data[DISCRETE_CHOICE_ELIGIBILITY_KEY]
        assert isinstance(info, EligibilityInfo)
        assert info.n_total == 4
        assert info.n_eligible == 2
        assert info.eligible_indices == (2, 3)

    def test_no_eligibility_info_when_no_filter(self) -> None:
        """AC-4: no EligibilityInfo stored without filter."""
        pop = _make_population(2)
        domain = _MockDomain()
        adapter = MockAdapter(
            version_string="test-1.0",
            compute_fn=_discrete_choice_compute_fn,
        )
        policy = PolicyConfig(policy={}, name="test")
        step = DiscreteChoiceStep(
            adapter=adapter,
            domain=domain,
            policy=policy,
        )
        state = _make_state(pop)
        result = step.execute(2025, state)
        assert DISCRETE_CHOICE_ELIGIBILITY_KEY not in result.data

    def test_metadata_has_eligibility_counts(self) -> None:
        """AC-8: metadata contains eligibility counts."""
        pop = _make_population(5, incomes=[10000.0, 20000.0, 30000.0, 40000.0, 50000.0])
        domain = _MockDomain()
        adapter = MockAdapter(
            version_string="test-1.0",
            compute_fn=_discrete_choice_compute_fn,
        )
        policy = PolicyConfig(policy={}, name="test")
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="income", operator="gt", threshold=25000.0),),
            description="Income > 25k",
        )
        step = DiscreteChoiceStep(
            adapter=adapter,
            domain=domain,
            policy=policy,
            eligibility_filter=ef,
        )
        state = _make_state(pop)
        result = step.execute(2025, state)

        meta = result.data[DISCRETE_CHOICE_METADATA_KEY]
        assert meta["eligibility_n_total"] == 5
        assert meta["eligibility_n_eligible"] == 3
        assert meta["eligibility_n_ineligible"] == 2
        assert meta["eligibility_filter_description"] == "Income > 25k"


# ============================================================================
# TestFullPipelineIntegration (Task 7.8, AC-7)
# ============================================================================


class TestFullPipelineIntegration:
    """Integration test: DiscreteChoiceStep → LogitChoiceStep → EligibilityMergeStep."""

    def test_pipeline_with_eligibility(self) -> None:
        """AC-7: full pipeline — ineligible households get keep_current unchanged."""
        # 5 households, income: 10k, 20k, 30k, 40k, 50k
        # Eligible: income > 25000 → indices 2, 3, 4
        pop = _make_population(5, incomes=[10000.0, 20000.0, 30000.0, 40000.0, 50000.0])
        domain = _MockDomain()
        adapter = MockAdapter(
            version_string="test-1.0",
            compute_fn=_discrete_choice_compute_fn,
        )
        policy = PolicyConfig(policy={}, name="test")
        taste = TasteParameters(beta_cost=-0.01)

        ef = EligibilityFilter(
            rules=(EligibilityRule(column="income", operator="gt", threshold=25000.0),),
            default_choice="keep_current",
            description="Income > 25k",
        )

        dc_step = DiscreteChoiceStep(
            adapter=adapter,
            domain=domain,
            policy=policy,
            eligibility_filter=ef,
            name="discrete_choice",
        )
        logit_step = LogitChoiceStep(
            taste_parameters=taste,
            name="logit_choice",
            depends_on=("discrete_choice",),
        )
        merge_step = EligibilityMergeStep(
            name="eligibility_merge",
            depends_on=("logit_choice",),
        )

        state = _make_state(pop)

        # Execute pipeline
        state = dc_step.execute(2025, state)
        state = logit_step.execute(2025, state)
        state = merge_step.execute(2025, state)

        # Check merged ChoiceResult
        cr = state.data[DISCRETE_CHOICE_RESULT_KEY]
        chosen = cr.chosen.to_pylist()
        assert len(chosen) == 5

        # Indices 0, 1 are ineligible → must be "keep_current"
        assert chosen[0] == "keep_current"
        assert chosen[1] == "keep_current"

        # Indices 2, 3, 4 are eligible → can be any alternative
        for idx in (2, 3, 4):
            assert chosen[idx] in ("keep_current", "option_a", "option_b")

        # Probability validation: all rows sum to 1.0
        for i in range(5):
            row_sum = sum(
                cr.probabilities.column(aid)[i].as_py()
                for aid in cr.alternative_ids
            )
            assert abs(row_sum - 1.0) < 1e-10

        # EligibilityInfo should be consumed
        assert DISCRETE_CHOICE_ELIGIBILITY_KEY not in state.data


# ============================================================================
# TestPerformanceAssertion (Task 7.9, AC-6)
# ============================================================================


class TestPerformanceAssertion:
    """Performance scaling tests."""

    def test_adapter_receives_eligible_times_alternatives(self) -> None:
        """AC-6: adapter receives N'×M rows (not N×M)."""
        # 100 households, 30 eligible (income > 60000)
        incomes = [50000.0 + i * 500 for i in range(100)]
        # Income range: 50000 to 99500. Threshold 70000 → eligible = 60 (indices 40-99)
        # Let's make it exact: 30 eligible with income > threshold
        incomes = [float(i * 1000) for i in range(100)]  # 0, 1000, ..., 99000
        # Threshold 70000: eligible = indices 71..99 = 29, let's use >= 70000 → 30
        pop = _make_population(100, incomes=incomes)
        domain = _MockDomain()  # 3 alternatives
        adapter = MockAdapter(
            version_string="test-1.0",
            compute_fn=_discrete_choice_compute_fn,
        )
        policy = PolicyConfig(policy={}, name="test")
        ef = EligibilityFilter(
            rules=(EligibilityRule(column="income", operator="ge", threshold=70000.0),),
        )
        step = DiscreteChoiceStep(
            adapter=adapter,
            domain=domain,
            policy=policy,
            eligibility_filter=ef,
        )
        state = _make_state(pop)
        result = step.execute(2025, state)

        # Eligible: income >= 70000 → indices 70..99 → 30 eligible
        info = result.data[DISCRETE_CHOICE_ELIGIBILITY_KEY]
        assert info.n_eligible == 30
        assert info.n_total == 100

        # Adapter should receive 30 × 3 = 90 rows (not 100 × 3 = 300)
        assert adapter.call_log[0]["population_row_count"] == 90

        # Cost matrix is 30 × 3
        cost_matrix = result.data["discrete_choice_cost_matrix"]
        assert cost_matrix.n_households == 30
        assert cost_matrix.n_alternatives == 3
