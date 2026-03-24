"""Epic 4 Demo -- Indicators and Scenario Comparison.

Turns raw panel outputs into decision-ready indicators:
  1. Distributional indicators -- income-decile breakdown
  2. Geographic indicators -- region-level aggregation
  3. Welfare indicators -- baseline vs reform winners/losers
  4. Fiscal indicators -- revenue, cost, balance tracking
  5. Scenario comparison tables -- side-by-side with delta columns
  6. Custom derived indicator formulas -- safe expression DSL
"""
from __future__ import annotations

from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR
while REPO_ROOT != REPO_ROOT.parent and not (REPO_ROOT / "src").exists():
    REPO_ROOT = REPO_ROOT.parent

SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DATA_DIR = REPO_ROOT / "notebooks" / "guides" / "data"
OUTPUT_DIR = DATA_DIR / "epic4_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

import pyarrow as pa

from reformlab.orchestrator.panel import PanelOutput
from reformlab.indicators import (
    # Main computation functions
    compute_distributional_indicators,
    compute_geographic_indicators,
    compute_welfare_indicators,
    compute_fiscal_indicators,
    compare_scenarios,
    apply_custom_formula,
    apply_custom_formulas,
    # Config types
    DistributionalConfig,
    GeographicConfig,
    WelfareConfig,
    FiscalConfig,
    ComparisonConfig,
    CustomFormulaConfig,
    # Result types
    IndicatorResult,
    ComparisonResult,
    ScenarioInput,
    # Exception
    FormulaValidationError,
)
from reformlab.visualization import show

print(f"Repo root:         {REPO_ROOT}")
print(f"Script directory:  {SCRIPT_DIR}")
print(f"Output directory:  {OUTPUT_DIR}")


# ---------------------------------------------------------------------------
# Setup: Building Demo Panel Data
# ---------------------------------------------------------------------------
# Indicators consume PanelOutput tables -- the household-by-year tables
# produced by the orchestrator in Epic 3.
#
# For this demo we build two panels directly:
# - Baseline -- a carbon tax at EUR 44.60/tCO2 with no redistribution
# - Reform -- same carbon tax but with a progressive lump-sum dividend
#   that benefits lower-income households
#
# Each panel has 100 households across 3 years (2026-2028), with income,
# region, tax, subsidy, and disposable income fields.
# ---------------------------------------------------------------------------

import random

random.seed(42)  # Deterministic demo data

NUM_HOUSEHOLDS = 100
YEARS = [2026, 2027, 2028]
REGIONS = ["11", "24", "27", "28", "32", "44", "52", "53", "75", "76", "84", "93", "94"]
REGION_NAMES = {
    "11": "Île-de-France", "24": "Centre-Val de Loire", "27": "Bourgogne-Franche-Comté",
    "28": "Normandie", "32": "Hauts-de-France", "44": "Grand Est",
    "52": "Pays de la Loire", "53": "Bretagne", "75": "Nouvelle-Aquitaine",
    "76": "Occitanie", "84": "Auvergne-Rhône-Alpes", "93": "Provence-Alpes-Côte d'Azur",
    "94": "Corse",
}

# Assign each household a fixed income and region
hh_incomes = [15000.0 + i * 850.0 + random.gauss(0, 2000) for i in range(NUM_HOUSEHOLDS)]
hh_regions = [random.choice(REGIONS) for _ in range(NUM_HOUSEHOLDS)]


def build_panel(label: str, subsidy_multiplier: float = 0.0) -> PanelOutput:
    """Build a demo panel with carbon tax and optional progressive subsidy."""
    household_ids, year_col = [], []
    incomes, carbon_taxes, subsidies, disposable_incomes = [], [], [], []
    region_codes = []

    for year in YEARS:
        year_offset = (year - 2026)
        for hh_id in range(NUM_HOUSEHOLDS):
            income = hh_incomes[hh_id] * (1 + 0.02 * year_offset)  # 2% annual growth
            # Carbon tax: regressive -- roughly flat per household (EUR 150-300)
            carbon_tax = 180.0 + random.gauss(0, 30) + 10 * year_offset
            # Progressive subsidy: inversely proportional to income
            if subsidy_multiplier > 0:
                median_income = 55000.0
                subsidy = max(0.0, subsidy_multiplier * (median_income - income) / median_income * 250.0)
            else:
                subsidy = 0.0

            household_ids.append(hh_id)
            year_col.append(year)
            incomes.append(round(income, 2))
            region_codes.append(hh_regions[hh_id])
            carbon_taxes.append(round(max(carbon_tax, 50.0), 2))  # Floor at EUR 50
            subsidies.append(round(subsidy, 2))
            disposable_incomes.append(round(income - carbon_tax + subsidy, 2))

    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "year": pa.array(year_col, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "region_code": pa.array(region_codes, type=pa.utf8()),
            "carbon_tax": pa.array(carbon_taxes, type=pa.float64()),
            "subsidy": pa.array(subsidies, type=pa.float64()),
            "disposable_income": pa.array(disposable_incomes, type=pa.float64()),
        }
    )
    return PanelOutput(
        table=table,
        metadata={"label": label, "start_year": 2026, "end_year": 2028, "seed": 42},
    )


baseline_panel = build_panel("baseline", subsidy_multiplier=0.0)
reform_panel = build_panel("reform", subsidy_multiplier=1.5)

print(f"Baseline panel: {baseline_panel.shape[0]} rows, {baseline_panel.shape[1]} columns")
print(f"Reform panel:   {reform_panel.shape[0]} rows, {reform_panel.shape[1]} columns")
print(f"\nColumns: {baseline_panel.table.column_names}")
print(f"Years:   {sorted(set(baseline_panel.table.column('year').to_pylist()))}")
print(f"Regions: {sorted(set(baseline_panel.table.column('region_code').to_pylist()))}")
print("\nBaseline sample (first 8 rows):")
show(baseline_panel.table, n=8)


# ---------------------------------------------------------------------------
# 1. Distributional Indicators by Income Decile
# ---------------------------------------------------------------------------
# The most fundamental policy question: who bears the burden?
#
# Distributional indicators assign each household to an income decile
# (1 = lowest 10%, 10 = highest 10%) and compute statistics (count, mean,
# median, sum, min, max) for every numeric field within each decile.
#
# This reveals whether a policy is progressive (heavier on the rich)
# or regressive (heavier on the poor).
# ---------------------------------------------------------------------------

# Default config: aggregate across all years, group by decile only
dist_result = compute_distributional_indicators(baseline_panel)

print(f"Indicators computed: {len(dist_result.indicators)}")
print(f"Excluded (null income): {dist_result.excluded_count}")
print(f"Warnings: {dist_result.warnings}")
print(f"\nMetadata keys: {sorted(dist_result.metadata.keys())}")

# Show the long-form table -- one row per (field, decile, metric)
dist_table = dist_result.to_table()
print(f"\nLong-form table shape: {dist_table.num_rows} rows x {dist_table.num_columns} cols")
print(f"Columns: {dist_table.column_names}")

# Show carbon_tax mean by decile -- the key regressivity indicator
print("\nCarbon tax mean by decile (is the tax regressive?):")
for i in range(dist_table.num_rows):
    if (
        dist_table.column("field_name")[i].as_py() == "carbon_tax"
        and dist_table.column("metric")[i].as_py() == "mean"
    ):
        decile = dist_table.column("decile")[i].as_py()
        value = dist_table.column("value")[i].as_py()
        bar = "#" * int(value / 10)
        print(f"  Decile {decile:2d}: EUR {value:8.2f}  {bar}")

# Year-by-year mode: see how the distribution evolves over time
dist_by_year = compute_distributional_indicators(
    baseline_panel,
    DistributionalConfig(by_year=True),
)

by_year_table = dist_by_year.to_table()
print(f"Year-by-year table: {by_year_table.num_rows} rows")

# Show carbon tax mean for decile 1 (poorest) across years
print("\nCarbon tax burden on decile 1 (poorest 10%) over time:")
for i in range(by_year_table.num_rows):
    if (
        by_year_table.column("field_name")[i].as_py() == "carbon_tax"
        and by_year_table.column("metric")[i].as_py() == "mean"
        and by_year_table.column("decile")[i].as_py() == 1
    ):
        year = by_year_table.column("year")[i].as_py()
        value = by_year_table.column("value")[i].as_py()
        print(f"  {year}: EUR {value:.2f}")


# ---------------------------------------------------------------------------
# 2. Geographic Aggregation Indicators
# ---------------------------------------------------------------------------
# Policy impacts vary across regions -- a carbon tax hits rural areas with
# longer commutes differently from dense urban centres.
#
# Geographic indicators group households by region code and compute the
# same statistics. An optional reference table validates region codes:
# unknown codes are bucketed into "_UNMATCHED" so nothing is silently dropped.
# ---------------------------------------------------------------------------

# Build a reference table of valid French region codes
ref_table = pa.table(
    {
        "region_code": pa.array(list(REGION_NAMES.keys()), type=pa.utf8()),
        "region_name": pa.array(list(REGION_NAMES.values()), type=pa.utf8()),
    }
)

geo_result = compute_geographic_indicators(
    baseline_panel,
    GeographicConfig(reference_table=ref_table),
)

print(f"Indicators computed: {len(geo_result.indicators)}")
print(f"Excluded (null region): {geo_result.excluded_count}")
print(f"Unmatched regions: {geo_result.unmatched_count}")

# Show mean carbon tax by region
geo_table = geo_result.to_table()
print(f"\nCarbon tax mean by region:")
region_means = []
for i in range(geo_table.num_rows):
    if (
        geo_table.column("field_name")[i].as_py() == "carbon_tax"
        and geo_table.column("metric")[i].as_py() == "mean"
    ):
        region = geo_table.column("region")[i].as_py()
        value = geo_table.column("value")[i].as_py()
        name = REGION_NAMES.get(region, region)
        region_means.append((name, value))

for name, value in sorted(region_means, key=lambda x: -x[1]):
    bar = "#" * int(value / 10)
    print(f"  {name:35s} EUR {value:8.2f}  {bar}")

# Year-by-year geographic breakdown
geo_by_year = compute_geographic_indicators(
    baseline_panel,
    GeographicConfig(reference_table=ref_table, by_year=True),
)

geo_year_table = geo_by_year.to_table()
print(f"Year-by-year geographic table: {geo_year_table.num_rows} rows")

# Show Ile-de-France carbon tax mean over time
print("\nÎle-de-France (region 11) carbon tax mean over time:")
for i in range(geo_year_table.num_rows):
    if (
        geo_year_table.column("field_name")[i].as_py() == "carbon_tax"
        and geo_year_table.column("metric")[i].as_py() == "mean"
        and geo_year_table.column("region")[i].as_py() == "11"
    ):
        year = geo_year_table.column("year")[i].as_py()
        value = geo_year_table.column("value")[i].as_py()
        print(f"  {year}: EUR {value:.2f}")


# ---------------------------------------------------------------------------
# 3. Welfare Indicators (Baseline vs Reform)
# ---------------------------------------------------------------------------
# The core policy design question: who wins and who loses under the reform?
#
# Welfare indicators join baseline and reform panels on (household_id, year),
# compute net_change = reform - baseline for a welfare field (e.g.,
# disposable income), and classify each household as a winner, loser,
# or neutral.
#
# Results are grouped by income decile (default) or region.
# ---------------------------------------------------------------------------

# Default: group by income decile, aggregate across years
welfare_result = compute_welfare_indicators(
    baseline_panel,
    reform_panel,
    WelfareConfig(welfare_field="disposable_income", threshold=100.0),
)

print(f"Indicators computed: {len(welfare_result.indicators)}")
print(f"Excluded (null income): {welfare_result.excluded_count}")
print(f"Unmatched households: {welfare_result.unmatched_count}")

# Show winner/loser breakdown by decile
print("\nWinner/Loser analysis by income decile (threshold: EUR 100):")
print(f"{'Decile':>8s}  {'Winners':>8s}  {'Losers':>8s}  {'Neutral':>8s}  {'Net Change':>12s}")
print("-" * 55)

welfare_table = welfare_result.to_table()
# Collect per-decile summary
decile_data: dict[int, dict[str, float]] = {}
for i in range(welfare_table.num_rows):
    decile = welfare_table.column("decile")[i].as_py()
    metric = welfare_table.column("metric")[i].as_py()
    value = welfare_table.column("value")[i].as_py()
    decile_data.setdefault(decile, {})[metric] = value

for decile in sorted(decile_data):
    d = decile_data[decile]
    print(
        f"{decile:8d}  {d.get('winner_count', 0):8.0f}  {d.get('loser_count', 0):8.0f}  "
        f"{d.get('neutral_count', 0):8.0f}  EUR {d.get('net_change', 0):9.2f}"
    )

# Group by region instead of decile
welfare_by_region = compute_welfare_indicators(
    baseline_panel,
    reform_panel,
    WelfareConfig(
        welfare_field="disposable_income",
        threshold=100.0,
        group_by_decile=False,
        group_by_region=True,
    ),
)

welfare_region_table = welfare_by_region.to_table()
print("Winner/Loser analysis by region:")
print(f"{'Region':>35s}  {'Winners':>8s}  {'Losers':>8s}  {'Net EUR':>12s}")
print("-" * 72)

region_welfare: dict[str, dict[str, float]] = {}
for i in range(welfare_region_table.num_rows):
    region = welfare_region_table.column("region")[i].as_py()
    metric = welfare_region_table.column("metric")[i].as_py()
    value = welfare_region_table.column("value")[i].as_py()
    region_welfare.setdefault(region, {})[metric] = value

for region in sorted(region_welfare, key=lambda r: -region_welfare[r].get("net_change", 0)):
    d = region_welfare[region]
    name = REGION_NAMES.get(region, region)
    print(
        f"{name:>35s}  {d.get('winner_count', 0):8.0f}  {d.get('loser_count', 0):8.0f}  "
        f"EUR {d.get('net_change', 0):9.2f}"
    )


# ---------------------------------------------------------------------------
# 4. Fiscal Indicators (Revenue, Cost, Balance)
# ---------------------------------------------------------------------------
# For budget analysis: how much does the policy collect, how much does it
# spend, and what's the balance?
#
# Fiscal indicators sum configured revenue and cost fields across all
# households, optionally year-by-year with running cumulative totals.
# ---------------------------------------------------------------------------

# Fiscal indicators for the reform panel (has both carbon_tax revenue and subsidy cost)
fiscal_result = compute_fiscal_indicators(
    reform_panel,
    FiscalConfig(
        revenue_fields=["carbon_tax"],
        cost_fields=["subsidy"],
        by_year=True,
        cumulative=True,
    ),
)

print(f"Indicators computed: {len(fiscal_result.indicators)}")
print(f"Warnings: {fiscal_result.warnings}")

fiscal_table = fiscal_result.to_table()
print(f"\nFiscal table: {fiscal_table.num_rows} rows")
print("\nYear-by-year fiscal summary:")

# Parse the long-form table into a readable summary
year_fiscal: dict[int, dict[str, float]] = {}
for i in range(fiscal_table.num_rows):
    year = fiscal_table.column("year")[i].as_py()
    metric = fiscal_table.column("metric")[i].as_py()
    value = fiscal_table.column("value")[i].as_py()
    year_fiscal.setdefault(year, {})[metric] = value

print(f"{'Year':>6s}  {'Revenue':>12s}  {'Cost':>12s}  {'Balance':>12s}  {'Cum.Balance':>12s}")
print("-" * 62)
for year in sorted(year_fiscal):
    d = year_fiscal[year]
    print(
        f"{year:6d}  EUR {d.get('revenue', 0):9.0f}  EUR {d.get('cost', 0):9.0f}  "
        f"EUR {d.get('balance', 0):9.0f}  EUR {d.get('cumulative_balance', 0):9.0f}"
    )

# Compare fiscal position: baseline (no subsidy) vs reform (with subsidy)
fiscal_baseline = compute_fiscal_indicators(
    baseline_panel,
    FiscalConfig(
        revenue_fields=["carbon_tax"],
        cost_fields=["subsidy"],
        by_year=True,
        cumulative=True,
    ),
)

print("Baseline fiscal (no redistribution):")
base_fiscal_table = fiscal_baseline.to_table()
for i in range(base_fiscal_table.num_rows):
    if base_fiscal_table.column("metric")[i].as_py() == "balance":
        year = base_fiscal_table.column("year")[i].as_py()
        value = base_fiscal_table.column("value")[i].as_py()
        print(f"  {year}: EUR {value:,.0f} (all revenue, no cost)")

print("\nReform fiscal (with progressive dividend):")
for i in range(fiscal_table.num_rows):
    if fiscal_table.column("metric")[i].as_py() == "balance":
        year = fiscal_table.column("year")[i].as_py()
        value = fiscal_table.column("value")[i].as_py()
        print(f"  {year}: EUR {value:,.0f} (revenue minus subsidy cost)")


# ---------------------------------------------------------------------------
# 5. Scenario Comparison Tables
# ---------------------------------------------------------------------------
# When you have indicators from multiple scenarios, you want to put them
# side by side and see the deltas.
#
# compare_scenarios does exactly that:
# - Takes 2+ ScenarioInput wrappers (label + IndicatorResult)
# - Joins them on their natural keys (field_name, decile/region, year, metric)
# - Adds delta_* columns (absolute change from baseline) and pct_delta_*
#   columns (percentage change)
# - Exports to CSV or Parquet
# ---------------------------------------------------------------------------

# Compute distributional indicators for both scenarios
dist_baseline = compute_distributional_indicators(baseline_panel)
dist_reform = compute_distributional_indicators(reform_panel)

# Compare them side-by-side
comparison = compare_scenarios(
    [
        ScenarioInput(label="baseline", indicators=dist_baseline),
        ScenarioInput(label="reform", indicators=dist_reform),
    ],
    ComparisonConfig(baseline_label="baseline", include_deltas=True, include_pct_deltas=True),
)

print(f"Comparison table shape: {comparison.table.num_rows} rows x {comparison.table.num_columns} cols")
print(f"Columns: {comparison.table.column_names}")
print(f"Warnings: {comparison.warnings}")
print(f"\nMetadata:")
print(f"  Schema: {comparison.metadata.get('indicator_schema')}")
print(f"  Labels: {comparison.metadata.get('scenario_labels')}")
print(f"  Join keys: {comparison.metadata.get('join_keys')}")

# Show subsidy mean by decile -- the reform redistributes, so this should differ
print("\nSubsidy mean by decile -- baseline vs reform:")
ct = comparison.table
for i in range(ct.num_rows):
    if (
        ct.column("field_name")[i].as_py() == "subsidy"
        and ct.column("metric")[i].as_py() == "mean"
    ):
        decile = ct.column("decile")[i].as_py()
        base_val = ct.column("baseline")[i].as_py()
        reform_val = ct.column("reform")[i].as_py()
        delta = ct.column("delta_reform")[i].as_py()
        print(
            f"  Decile {decile:2d}: baseline={base_val:8.2f}  reform={reform_val:8.2f}  "
            f"delta={delta:+9.2f}"
        )

# Three-way comparison: baseline, reform, and a "high ambition" variant
high_ambition_panel = build_panel("high_ambition", subsidy_multiplier=2.5)
dist_high = compute_distributional_indicators(high_ambition_panel)

comparison_3way = compare_scenarios(
    [
        ScenarioInput(label="baseline", indicators=dist_baseline),
        ScenarioInput(label="reform", indicators=dist_reform),
        ScenarioInput(label="high_ambition", indicators=dist_high),
    ],
)

print(f"3-way comparison: {comparison_3way.table.num_rows} rows x {comparison_3way.table.num_columns} cols")
print(f"Columns: {comparison_3way.table.column_names}")

# Export to CSV and Parquet
comparison.export_csv(OUTPUT_DIR / "distributional_comparison.csv")
comparison.export_parquet(OUTPUT_DIR / "distributional_comparison.parquet")
comparison_3way.export_csv(OUTPUT_DIR / "distributional_3way_comparison.csv")

print("\nExported comparison files to notebooks/data/epic4_outputs/")

# Fiscal comparison across scenarios
fiscal_high = compute_fiscal_indicators(
    high_ambition_panel,
    FiscalConfig(
        revenue_fields=["carbon_tax"],
        cost_fields=["subsidy"],
        by_year=True,
        cumulative=True,
    ),
)

fiscal_comparison = compare_scenarios(
    [
        ScenarioInput(label="baseline", indicators=fiscal_baseline),
        ScenarioInput(label="reform", indicators=fiscal_result),
        ScenarioInput(label="high_ambition", indicators=fiscal_high),
    ],
)

print("Fiscal comparison -- balance metric across scenarios:")
fct = fiscal_comparison.table
print(f"{'Year':>6s}  {'Baseline':>12s}  {'Reform':>12s}  {'High Ambition':>14s}")
print("-" * 52)
for i in range(fct.num_rows):
    if fct.column("metric")[i].as_py() == "balance":
        year = fct.column("year")[i].as_py()
        base = fct.column("baseline")[i].as_py()
        ref = fct.column("reform")[i].as_py()
        high = fct.column("high_ambition")[i].as_py()
        print(f"{year:6d}  EUR {base:9.0f}  EUR {ref:9.0f}  EUR {high:11.0f}")

fiscal_comparison.export_csv(OUTPUT_DIR / "fiscal_comparison.csv")
print("\nExported fiscal comparison to notebooks/data/epic4_outputs/")


# ---------------------------------------------------------------------------
# 6. Custom Derived Indicator Formulas
# ---------------------------------------------------------------------------
# Sometimes the built-in metrics aren't enough -- you need a custom
# calculation. For example:
# - "Surplus as % of revenue" -> balance / revenue * 100
# - "Average tax per household" -> sum / count
#
# apply_custom_formula parses a safe expression DSL (no eval, no code
# injection) that supports:
# - Arithmetic: +, -, *, /
# - Parentheses for grouping
# - Numeric constants
# - References to existing metric names
#
# Division by zero returns null (not an error). Formulas are tracked in
# result metadata for governance.
# ---------------------------------------------------------------------------

# Start with fiscal indicators -- they have revenue, cost, balance metrics
fiscal_for_custom = compute_fiscal_indicators(
    reform_panel,
    FiscalConfig(
        revenue_fields=["carbon_tax"],
        cost_fields=["subsidy"],
        by_year=True,
        cumulative=False,  # Keep it simple for formulas
    ),
)

# Apply a single custom formula: surplus percentage
surplus_formula = CustomFormulaConfig(
    source_field="fiscal_summary",
    output_metric="surplus_pct",
    expression="balance / revenue * 100",
    description="Net fiscal surplus as a percentage of total revenue",
)

with_surplus = apply_custom_formula(fiscal_for_custom, surplus_formula)

# The derived metric appears in the to_table() output
derived_table = with_surplus.to_table()
print("Fiscal indicators with custom surplus_pct metric:")
show(derived_table)

# Chain multiple formulas -- later formulas can reference earlier ones
formulas = [
    CustomFormulaConfig(
        source_field="fiscal_summary",
        output_metric="cost_ratio",
        expression="cost / revenue * 100",
        description="Cost as percentage of revenue",
    ),
    CustomFormulaConfig(
        source_field="fiscal_summary",
        output_metric="net_rate",
        expression="balance / revenue",
        description="Net fiscal rate (1 = all revenue retained, 0 = fully redistributed)",
    ),
]

enriched = apply_custom_formulas(fiscal_for_custom, formulas)

enriched_table = enriched.to_table()
print(f"Enriched table: {enriched_table.num_rows} rows (added {enriched_table.num_rows - fiscal_for_custom.to_table().num_rows} derived rows)")

# Show the derived metrics
print("\nDerived metrics by year:")
for i in range(enriched_table.num_rows):
    metric = enriched_table.column("metric")[i].as_py()
    if metric in ("cost_ratio", "net_rate"):
        year = enriched_table.column("year")[i].as_py()
        value = enriched_table.column("value")[i].as_py()
        print(f"  {year}  {metric:12s} = {value:.4f}")

# Metadata tracks all formulas applied
print(f"\nFormula metadata: {enriched.metadata.get('custom_formulas')}")

# Custom formulas on distributional indicators too
# Example: "average tax per household" from decile-level stats
dist_with_avg = apply_custom_formula(
    dist_baseline,
    CustomFormulaConfig(
        source_field="carbon_tax",
        output_metric="avg_tax",
        expression="sum / count",
        description="Average carbon tax per household in the decile",
    ),
)

avg_table = dist_with_avg.to_table()
print("Average carbon tax per household by decile (via custom formula):")
for i in range(avg_table.num_rows):
    if (
        avg_table.column("field_name")[i].as_py() == "carbon_tax"
        and avg_table.column("metric")[i].as_py() == "avg_tax"
    ):
        decile = avg_table.column("decile")[i].as_py()
        value = avg_table.column("value")[i].as_py()
        print(f"  Decile {decile:2d}: EUR {value:.2f}")

# What happens with invalid formulas?
# The parser catches syntax errors and gives helpful messages

bad_formulas = [
    ("", "Empty expression"),
    ("revenue + @invalid", "Unknown character"),
    ("(revenue + cost", "Unbalanced parentheses"),
    ("nonexistent_metric * 2", "Unknown metric reference"),
]

for expr, label in bad_formulas:
    try:
        apply_custom_formula(
            fiscal_for_custom,
            CustomFormulaConfig(
                source_field="fiscal_summary",
                output_metric="bad",
                expression=expr,
            ),
        )
    except (FormulaValidationError, ValueError) as e:
        print(f"  [{label}] {type(e).__name__}: {e}")
        if isinstance(e, FormulaValidationError) and e.suggestion:
            print(f"    Suggestion: {e.suggestion}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
# This EPIC 4 demo covers the full indicator and comparison layer:
#
# | Capability                   | In plain terms                                  |
# |------------------------------|------------------------------------------------|
# | Distributional indicators    | Income deciles + statistics for every field     |
# | Geographic indicators        | Region grouping with reference validation       |
# | Welfare indicators           | Winners/losers classification by decile/region  |
# | Fiscal indicators            | Revenue, cost, balance with cumulative tracking |
# | Scenario comparison tables   | Side-by-side with absolute and % deltas         |
# | Custom derived formulas      | Safe expression DSL for new metrics             |
# | Long-form output             | Stable to_table() for export / downstream use   |
# | Metadata + warnings          | Full transparency on computation details         |
# ---------------------------------------------------------------------------

print("Generated files in notebooks/data/epic4_outputs:")
for path in sorted(OUTPUT_DIR.iterdir()):
    print(f"  {path.relative_to(DATA_DIR)}")
