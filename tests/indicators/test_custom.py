# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Lucas Vivier
"""Tests for custom derived indicator formulas.

Story 4.6: Implement Custom Derived Indicator Formulas
"""

from __future__ import annotations

import pyarrow as pa
import pytest

from reformlab.indicators.custom import (
    CustomFormulaConfig,
    FormulaValidationError,
    apply_custom_formula,
    apply_custom_formulas,
)
from reformlab.indicators.types import (
    DecileIndicators,
    FiscalIndicators,
    IndicatorResult,
    RegionIndicators,
)

# Fixtures


@pytest.fixture
def simple_decile_indicators() -> IndicatorResult:
    """Create simple decile indicator result for testing."""
    indicators = [
        DecileIndicators(
            field_name="income",
            decile=1,
            year=2020,
            count=100,
            mean=1000.0,
            median=950.0,
            sum=100000.0,
            min=500.0,
            max=1500.0,
        ),
        DecileIndicators(
            field_name="income",
            decile=2,
            year=2020,
            count=100,
            mean=2000.0,
            median=1950.0,
            sum=200000.0,
            min=1500.0,
            max=2500.0,
        ),
    ]
    return IndicatorResult(
        indicators=indicators,
        metadata={"income_field": "income"},
    )


@pytest.fixture
def fiscal_indicators() -> IndicatorResult:
    """Create fiscal indicator result for testing."""
    indicators = [
        FiscalIndicators(
            field_name="fiscal_summary",
            year=2020,
            revenue=500000.0,
            cost=300000.0,
            balance=200000.0,
        ),
        FiscalIndicators(
            field_name="fiscal_summary",
            year=2021,
            revenue=600000.0,
            cost=350000.0,
            balance=250000.0,
        ),
    ]
    return IndicatorResult(
        indicators=indicators,
        metadata={"revenue_fields": ["tax"], "cost_fields": ["rebate"]},
    )


@pytest.fixture
def region_indicators() -> IndicatorResult:
    """Create region indicator result for testing."""
    indicators = [
        RegionIndicators(
            field_name="emissions",
            region="11",
            year=2020,
            count=1000,
            mean=5.5,
            median=5.0,
            sum=5500.0,
            min=0.0,
            max=15.0,
        ),
        RegionIndicators(
            field_name="emissions",
            region="24",
            year=2020,
            count=500,
            mean=4.2,
            median=4.0,
            sum=2100.0,
            min=0.0,
            max=12.0,
        ),
    ]
    return IndicatorResult(
        indicators=indicators,
        metadata={"region_field": "region_code"},
    )


# Test AC-1: Define custom indicator formula schema


def test_custom_formula_config_creation():
    """Test CustomFormulaConfig dataclass creation."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="normalized",
        expression="mean / 1000",
        description="Normalize income to thousands",
    )
    assert formula.source_field == "income"
    assert formula.output_metric == "normalized"
    assert formula.expression == "mean / 1000"
    assert formula.description == "Normalize income to thousands"


def test_custom_formula_config_default_description():
    """Test CustomFormulaConfig with default description."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="normalized",
        expression="mean / 1000",
    )
    assert formula.description == ""


# Test AC-2: Preserve IndicatorResult table contract


def test_apply_formula_preserves_original_indicators(simple_decile_indicators):
    """Test that apply_custom_formula preserves original indicator values."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="mean_per_household",
        expression="mean",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)

    # Original indicators unchanged
    assert len(result.indicators) == len(simple_decile_indicators.indicators)
    assert result.indicators == simple_decile_indicators.indicators

    # Table includes derived metric
    table = result.to_table()
    assert "metric" in table.column_names
    assert "value" in table.column_names

    metrics = table["metric"].to_pylist()
    assert "mean_per_household" in metrics


def test_apply_formula_table_schema_compatible(simple_decile_indicators):
    """Test that derived result maintains compatible table schema."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="custom",
        expression="sum + mean",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    # Check schema compatibility
    expected_cols = ["field_name", "decile", "year", "metric", "value"]
    assert table.column_names == expected_cols


# Test AC-3: Support arithmetic operations


def test_arithmetic_addition(simple_decile_indicators):
    """Test addition operator."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="sum_plus_mean",
        expression="sum + mean",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    # Filter to derived metric
    mask = pa.compute.equal(table["metric"], "sum_plus_mean")
    derived = table.filter(mask)

    # Verify calculation: decile 1: 100000 + 1000 = 101000
    decile_1_mask = pa.compute.equal(derived["decile"], 1)
    decile_1 = derived.filter(decile_1_mask)
    assert decile_1.num_rows == 1
    assert decile_1["value"][0].as_py() == pytest.approx(101000.0)


def test_arithmetic_subtraction(simple_decile_indicators):
    """Test subtraction operator."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="sum_minus_mean",
        expression="sum - mean",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "sum_minus_mean")
    derived = table.filter(mask)

    # Verify: decile 1: 100000 - 1000 = 99000
    decile_1_mask = pa.compute.equal(derived["decile"], 1)
    decile_1 = derived.filter(decile_1_mask)
    assert decile_1["value"][0].as_py() == pytest.approx(99000.0)


def test_arithmetic_multiplication(simple_decile_indicators):
    """Test multiplication operator."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="mean_times_two",
        expression="mean * 2",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "mean_times_two")
    derived = table.filter(mask)

    # Verify: decile 1: 1000 * 2 = 2000
    decile_1_mask = pa.compute.equal(derived["decile"], 1)
    decile_1 = derived.filter(decile_1_mask)
    assert decile_1["value"][0].as_py() == pytest.approx(2000.0)


def test_arithmetic_division(simple_decile_indicators):
    """Test division operator."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="mean_over_count",
        expression="sum / count",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "mean_over_count")
    derived = table.filter(mask)

    # Verify: decile 1: 100000 / 100 = 1000
    decile_1_mask = pa.compute.equal(derived["decile"], 1)
    decile_1 = derived.filter(decile_1_mask)
    assert decile_1["value"][0].as_py() == pytest.approx(1000.0)


def test_division_by_zero_produces_null(simple_decile_indicators):
    """Test that division by zero produces null values, not errors."""
    # Create indicator with zero count
    indicators = [
        DecileIndicators(
            field_name="income",
            decile=1,
            year=2020,
            count=0,  # Zero count
            mean=0.0,
            median=0.0,
            sum=0.0,
            min=0.0,
            max=0.0,
        ),
    ]
    result = IndicatorResult(indicators=indicators, metadata={})

    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="mean_over_count",
        expression="sum / count",
    )

    # Should not raise an error
    result_with_formula = apply_custom_formula(result, formula)
    table = result_with_formula.to_table()

    mask = pa.compute.equal(table["metric"], "mean_over_count")
    derived = table.filter(mask)

    # Should have null value
    assert derived.num_rows == 1
    assert derived["value"][0].as_py() is None


def test_operator_precedence(simple_decile_indicators):
    """Test operator precedence: multiplication before addition."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="precedence_test",
        expression="mean + count * 2",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "precedence_test")
    derived = table.filter(mask)

    # Verify: decile 1: 1000 + (100 * 2) = 1200 (not (1000 + 100) * 2 = 2200)
    decile_1_mask = pa.compute.equal(derived["decile"], 1)
    decile_1 = derived.filter(decile_1_mask)
    assert decile_1["value"][0].as_py() == pytest.approx(1200.0)


def test_parentheses_override_precedence(simple_decile_indicators):
    """Test that parentheses override operator precedence."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="paren_test",
        expression="(mean + count) * 2",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "paren_test")
    derived = table.filter(mask)

    # Verify: decile 1: (1000 + 100) * 2 = 2200
    decile_1_mask = pa.compute.equal(derived["decile"], 1)
    decile_1 = derived.filter(decile_1_mask)
    assert decile_1["value"][0].as_py() == pytest.approx(2200.0)


# Test AC-4: Support metric references


def test_metric_reference_resolution(simple_decile_indicators):
    """Test that metric references are correctly resolved."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="test",
        expression="mean",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "test")
    derived = table.filter(mask)

    # Should have same values as mean metric
    decile_1_mask = pa.compute.equal(derived["decile"], 1)
    decile_1 = derived.filter(decile_1_mask)
    assert decile_1["value"][0].as_py() == pytest.approx(1000.0)


def test_missing_metric_reference_raises_error(simple_decile_indicators):
    """Test that missing metric references raise clear error."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="test",
        expression="nonexistent_metric + mean",
    )

    with pytest.raises(FormulaValidationError) as excinfo:
        apply_custom_formula(simple_decile_indicators, formula)

    assert "nonexistent_metric" in str(excinfo.value)
    assert "Available metrics:" in str(excinfo.value)


def test_missing_source_field_raises_error(simple_decile_indicators):
    """Test that missing source_field raises clear error."""
    formula = CustomFormulaConfig(
        source_field="nonexistent_field",
        output_metric="test",
        expression="mean",
    )

    with pytest.raises(FormulaValidationError) as excinfo:
        apply_custom_formula(simple_decile_indicators, formula)

    assert "nonexistent_field" in str(excinfo.value)
    assert "Available fields:" in str(excinfo.value)


# Test AC-5: Support constants


def test_integer_constant(simple_decile_indicators):
    """Test integer constants in formulas."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="plus_100",
        expression="mean + 100",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "plus_100")
    derived = table.filter(mask)

    decile_1_mask = pa.compute.equal(derived["decile"], 1)
    decile_1 = derived.filter(decile_1_mask)
    assert decile_1["value"][0].as_py() == pytest.approx(1100.0)


def test_float_constant(simple_decile_indicators):
    """Test float constants in formulas."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="scaled",
        expression="mean * 0.85",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "scaled")
    derived = table.filter(mask)

    decile_1_mask = pa.compute.equal(derived["decile"], 1)
    decile_1 = derived.filter(decile_1_mask)
    assert decile_1["value"][0].as_py() == pytest.approx(850.0)


def test_negative_constant(simple_decile_indicators):
    """Test negative constants in formulas."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="offset",
        expression="mean + -500",
    )
    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "offset")
    derived = table.filter(mask)

    decile_1_mask = pa.compute.equal(derived["decile"], 1)
    decile_1 = derived.filter(decile_1_mask)
    assert decile_1["value"][0].as_py() == pytest.approx(500.0)


# Test AC-6: Chain multiple custom formulas


def test_chain_formulas_sequential(simple_decile_indicators):
    """Test chaining multiple formulas where later formulas reference earlier."""
    formulas = [
        CustomFormulaConfig(
            source_field="income",
            output_metric="doubled_mean",
            expression="mean * 2",
        ),
        CustomFormulaConfig(
            source_field="income",
            output_metric="doubled_plus_sum",
            expression="doubled_mean + sum",
        ),
    ]

    result = apply_custom_formulas(simple_decile_indicators, formulas)
    table = result.to_table()

    # Check first derived metric
    mask1 = pa.compute.equal(table["metric"], "doubled_mean")
    derived1 = table.filter(mask1)
    decile_1_mask = pa.compute.equal(derived1["decile"], 1)
    decile_1_first = derived1.filter(decile_1_mask)
    assert decile_1_first["value"][0].as_py() == pytest.approx(2000.0)

    # Check second derived metric (depends on first)
    mask2 = pa.compute.equal(table["metric"], "doubled_plus_sum")
    derived2 = table.filter(mask2)
    decile_1_mask2 = pa.compute.equal(derived2["decile"], 1)
    decile_1_second = derived2.filter(decile_1_mask2)
    # 2000 (doubled_mean) + 100000 (sum) = 102000
    assert decile_1_second["value"][0].as_py() == pytest.approx(102000.0)


def test_chain_formulas_all_tracked_in_metadata(simple_decile_indicators):
    """Test that all chained formulas are tracked in metadata."""
    formulas = [
        CustomFormulaConfig(
            source_field="income",
            output_metric="first",
            expression="mean",
        ),
        CustomFormulaConfig(
            source_field="income",
            output_metric="second",
            expression="sum",
        ),
    ]

    result = apply_custom_formulas(simple_decile_indicators, formulas)

    assert "custom_formulas" in result.metadata
    assert len(result.metadata["custom_formulas"]) == 2
    assert result.metadata["custom_formulas"][0]["output_metric"] == "first"
    assert result.metadata["custom_formulas"][1]["output_metric"] == "second"


# Test AC-7: Custom formula metadata tracking


def test_formula_metadata_tracking(simple_decile_indicators):
    """Test that formula definition is tracked in metadata."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="test_metric",
        expression="mean + sum",
        description="Test formula for governance",
    )

    result = apply_custom_formula(simple_decile_indicators, formula)

    assert "custom_formulas" in result.metadata
    assert len(result.metadata["custom_formulas"]) == 1

    tracked = result.metadata["custom_formulas"][0]
    assert tracked["source_field"] == "income"
    assert tracked["output_metric"] == "test_metric"
    assert tracked["expression"] == "mean + sum"
    assert tracked["description"] == "Test formula for governance"


def test_apply_formula_does_not_mutate_input_metadata(simple_decile_indicators):
    """Test input metadata remains unchanged after applying custom formula."""
    original_metadata = dict(simple_decile_indicators.metadata)
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="test_metric",
        expression="mean + sum",
    )

    result = apply_custom_formula(simple_decile_indicators, formula)

    assert "custom_formulas" not in simple_decile_indicators.metadata
    assert simple_decile_indicators.metadata == original_metadata
    assert "custom_formulas" in result.metadata


# Test AC-8: Custom formula in comparison context


def test_derived_metrics_in_comparison(simple_decile_indicators):
    """Test that derived metrics flow through compare_scenarios()."""
    from reformlab.indicators.comparison import (
        ScenarioInput,
        compare_scenarios,
    )

    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="intensity",
        expression="sum / count",
    )

    result1 = apply_custom_formula(simple_decile_indicators, formula)

    # Create second scenario with different values
    indicators2 = [
        DecileIndicators(
            field_name="income",
            decile=1,
            year=2020,
            count=100,
            mean=1100.0,
            median=1050.0,
            sum=110000.0,
            min=600.0,
            max=1600.0,
        ),
        DecileIndicators(
            field_name="income",
            decile=2,
            year=2020,
            count=100,
            mean=2100.0,
            median=2050.0,
            sum=210000.0,
            min=1600.0,
            max=2600.0,
        ),
    ]
    result2_base = IndicatorResult(
        indicators=indicators2,
        metadata={"income_field": "income"},
    )
    result2 = apply_custom_formula(result2_base, formula)

    scenarios = [
        ScenarioInput(label="baseline", indicators=result1),
        ScenarioInput(label="reform", indicators=result2),
    ]

    comparison = compare_scenarios(scenarios)
    table = comparison.to_table()

    # Check that derived metric is included
    metrics = table["metric"].to_pylist()
    assert "intensity" in metrics

    # Check that delta is computed for derived metric
    assert "delta_reform" in table.column_names


# Test AC-9: Validation and safe evaluation


def test_empty_expression_raises_error(simple_decile_indicators):
    """Test that empty expressions raise clear error."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="test",
        expression="",
    )

    with pytest.raises(FormulaValidationError) as excinfo:
        apply_custom_formula(simple_decile_indicators, formula)

    assert "empty" in str(excinfo.value).lower()


def test_invalid_syntax_unbalanced_parentheses(simple_decile_indicators):
    """Test that unbalanced parentheses raise clear error."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="test",
        expression="(mean + sum",
    )

    with pytest.raises(FormulaValidationError) as excinfo:
        apply_custom_formula(simple_decile_indicators, formula)

    assert "Expected" in str(excinfo.value)


def test_invalid_syntax_unknown_operator(simple_decile_indicators):
    """Test that unknown operators raise clear error."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="test",
        expression="mean % sum",
    )

    with pytest.raises(FormulaValidationError) as excinfo:
        apply_custom_formula(simple_decile_indicators, formula)

    assert "Invalid character" in str(excinfo.value)


def test_no_code_injection_possible(simple_decile_indicators):
    """Test that arbitrary code execution is not possible."""
    # Attempt to inject Python code
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="test",
        expression="__import__('os').system('echo pwned')",
    )

    # Should fail during parsing, not execute the code
    with pytest.raises(FormulaValidationError):
        apply_custom_formula(simple_decile_indicators, formula)


# Additional tests for edge cases and robustness


def test_nested_parentheses(simple_decile_indicators):
    """Test deeply nested parentheses."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="nested",
        expression="((mean + sum) * 2) / count",
    )

    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "nested")
    derived = table.filter(mask)

    decile_1_mask = pa.compute.equal(derived["decile"], 1)
    decile_1 = derived.filter(decile_1_mask)
    # ((1000 + 100000) * 2) / 100 = 2020
    assert decile_1["value"][0].as_py() == pytest.approx(2020.0)


def test_complex_expression(simple_decile_indicators):
    """Test complex expression with multiple operations."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="complex",
        expression="(sum - mean * count) / (max - min) + 42",
    )

    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "complex")
    derived = table.filter(mask)
    assert derived.num_rows > 0


def test_formula_on_fiscal_indicators(fiscal_indicators):
    """Test formulas on fiscal indicators."""
    formula = CustomFormulaConfig(
        source_field="fiscal_summary",
        output_metric="balance_pct",
        expression="balance / revenue * 100",
    )

    result = apply_custom_formula(fiscal_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "balance_pct")
    derived = table.filter(mask)

    year_2020_mask = pa.compute.equal(derived["year"], 2020)
    year_2020 = derived.filter(year_2020_mask)
    # 200000 / 500000 * 100 = 40.0
    assert year_2020["value"][0].as_py() == pytest.approx(40.0)


def test_formula_on_region_indicators(region_indicators):
    """Test formulas on region indicators."""
    formula = CustomFormulaConfig(
        source_field="emissions",
        output_metric="per_capita",
        expression="sum / count",
    )

    result = apply_custom_formula(region_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "per_capita")
    derived = table.filter(mask)

    region_11_mask = pa.compute.equal(derived["region"], "11")
    region_11 = derived.filter(region_11_mask)
    # 5500 / 1000 = 5.5
    assert region_11["value"][0].as_py() == pytest.approx(5.5)


def test_duplicate_metric_rows_raise_validation_error():
    """Test duplicate metric rows for same key raise FormulaValidationError."""
    result = IndicatorResult(
        indicators=[
            DecileIndicators(
                field_name="income",
                decile=1,
                year=2020,
                count=100,
                mean=1000.0,
                median=950.0,
                sum=100000.0,
                min=500.0,
                max=1500.0,
            ),
            DecileIndicators(
                field_name="income",
                decile=1,
                year=2020,
                count=120,
                mean=1200.0,
                median=1100.0,
                sum=144000.0,
                min=600.0,
                max=1800.0,
            ),
        ],
        metadata={"income_field": "income"},
    )
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="test",
        expression="mean",
    )

    with pytest.raises(FormulaValidationError) as excinfo:
        apply_custom_formula(result, formula)

    assert "Duplicate metric rows detected" in str(excinfo.value)


def test_empty_indicator_result():
    """Test formula application on empty indicator result."""
    result = IndicatorResult(indicators=[], metadata={})
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="test",
        expression="mean",
    )

    result_with_formula = apply_custom_formula(result, formula)

    # Should not raise error
    assert "custom_formulas" in result_with_formula.metadata
    table = result_with_formula.to_table()
    assert table.num_rows == 0


def test_whitespace_in_expression(simple_decile_indicators):
    """Test that whitespace in expressions is handled correctly."""
    formula = CustomFormulaConfig(
        source_field="income",
        output_metric="test",
        expression="  mean   +   sum  ",
    )

    result = apply_custom_formula(simple_decile_indicators, formula)
    table = result.to_table()

    mask = pa.compute.equal(table["metric"], "test")
    derived = table.filter(mask)
    assert derived.num_rows > 0


def test_formula_validation_error_attributes():
    """Test FormulaValidationError attributes."""
    error = FormulaValidationError(
        "Test error",
        position=10,
        suggestion="Try this instead",
    )

    assert str(error) == "Test error"
    assert error.position == 10
    assert error.suggestion == "Try this instead"
