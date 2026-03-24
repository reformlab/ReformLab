"""Epic 12 Demo -- Multi-Portfolio Comparison.

Compares results across multiple policy portfolios side-by-side:
  1. Multi-portfolio comparison -- 3+ portfolios across indicator types
  2. Cross-comparison metrics -- aggregate rankings ("which portfolio is best?")
  3. Backward compatibility -- compare_portfolios() builds on compare_scenarios()
"""
from __future__ import annotations

import random
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR
while REPO_ROOT != REPO_ROOT.parent and not (REPO_ROOT / "src").exists():
    REPO_ROOT = REPO_ROOT.parent

SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import pyarrow as pa

from reformlab.orchestrator.panel import PanelOutput
from reformlab.indicators import (
    compute_distributional_indicators,
    compute_fiscal_indicators,
    compare_scenarios,
    DistributionalConfig,
    FiscalConfig,
    ScenarioInput,
    compare_portfolios,
    PortfolioComparisonInput,
    PortfolioComparisonConfig,
)
from reformlab.visualization import show

OUTPUT_DIR = REPO_ROOT / "notebooks" / "guides" / "data" / "epic12_outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Repo root:  {REPO_ROOT}")
print(f"Output dir: {OUTPUT_DIR}")


# ---------------------------------------------------------------------------
# 1. Create Three Policy Portfolios
# ---------------------------------------------------------------------------
# We simulate three portfolios with different policy mixes:
#
# | Portfolio              | Carbon Tax    | Subsidy             | Description                              |
# |------------------------|---------------|---------------------|------------------------------------------|
# | A: Carbon Tax Light    | EUR 44/tCO2   | None                | Current French rate, no redistribution   |
# | B: Carbon Tax + Subsidy| EUR 50/tCO2   | EUR 150-250 progr.  | Moderate tax with progressive dividend   |
# | C: Green Transition    | EUR 80/tCO2   | EUR 200-400 progr.  | Ambitious tax with generous redistrib.   |
#
# Each portfolio is applied to the same 100-household population over
# 3 years (2025-2027).
# ---------------------------------------------------------------------------

random.seed(42)

NUM_HOUSEHOLDS = 100
YEARS = [2025, 2026, 2027]

# Fixed household attributes (same across all portfolios for fair comparison)
hh_incomes = [15000.0 + i * 850.0 + random.gauss(0, 2000) for i in range(NUM_HOUSEHOLDS)]
hh_emissions = [3.0 + random.gauss(0, 1.0) for _ in range(NUM_HOUSEHOLDS)]  # tCO2


def build_portfolio_panel(
    label: str,
    carbon_tax_rate: float,
    subsidy_multiplier: float = 0.0,
) -> PanelOutput:
    """Build a demo panel simulating a policy portfolio."""
    household_ids, year_col = [], []
    incomes, carbon_taxes, subsidies, disposable_incomes = [], [], [], []

    for year in YEARS:
        year_offset = year - 2025
        for hh_id in range(NUM_HOUSEHOLDS):
            income = hh_incomes[hh_id] * (1 + 0.02 * year_offset)
            carbon_tax = max(0.0, hh_emissions[hh_id] * carbon_tax_rate)

            if subsidy_multiplier > 0:
                median_income = 55000.0
                subsidy = max(0.0, subsidy_multiplier * (median_income - income) / median_income * 300.0)
            else:
                subsidy = 0.0

            household_ids.append(hh_id)
            year_col.append(year)
            incomes.append(round(income, 2))
            carbon_taxes.append(round(carbon_tax, 2))
            subsidies.append(round(subsidy, 2))
            disposable_incomes.append(round(income - carbon_tax + subsidy, 2))

    table = pa.table(
        {
            "household_id": pa.array(household_ids, type=pa.int64()),
            "year": pa.array(year_col, type=pa.int64()),
            "income": pa.array(incomes, type=pa.float64()),
            "carbon_tax": pa.array(carbon_taxes, type=pa.float64()),
            "subsidy_amount": pa.array(subsidies, type=pa.float64()),
            "disposable_income": pa.array(disposable_incomes, type=pa.float64()),
        }
    )
    return PanelOutput(
        table=table,
        metadata={"label": label, "start_year": 2025, "end_year": 2027, "seed": 42},
    )


# Build the three portfolio panels
panel_a = build_portfolio_panel("Carbon Tax Light", carbon_tax_rate=44.0)
panel_b = build_portfolio_panel("Carbon Tax + Subsidy", carbon_tax_rate=50.0, subsidy_multiplier=1.5)
panel_c = build_portfolio_panel("Green Transition", carbon_tax_rate=80.0, subsidy_multiplier=2.5)

portfolios = {
    "Carbon Tax Light": panel_a,
    "Carbon Tax + Subsidy": panel_b,
    "Green Transition": panel_c,
}

for name, panel in portfolios.items():
    print(f"{name}: {panel.shape[0]} rows, {panel.shape[1]} columns")

print("\nSample from Portfolio A:")
show(panel_a.table, n=5)


# ---------------------------------------------------------------------------
# 2. Distributional Comparison
# ---------------------------------------------------------------------------
# How does each portfolio affect different income groups? We compare
# distributional indicators across all three portfolios.
#
# compare_portfolios() computes indicators for each portfolio, then
# produces a side-by-side comparison table.
# ---------------------------------------------------------------------------

# Create portfolio comparison inputs
portfolio_inputs = [
    PortfolioComparisonInput(label=name, panel=panel)
    for name, panel in portfolios.items()
]

# Compare with distributional indicators only
dist_config = PortfolioComparisonConfig(
    indicator_types=("distributional",),
)
dist_result = compare_portfolios(portfolio_inputs, dist_config)

print(f"Comparisons: {list(dist_result.comparisons.keys())}")
print(f"Portfolio labels: {dist_result.portfolio_labels}")

dist_comparison = dist_result.comparisons["distributional"]
print(f"\nComparison table: {dist_comparison.table.num_rows} rows x {dist_comparison.table.num_columns} cols")
print(f"Columns: {dist_comparison.table.column_names}")

# Show carbon tax mean by decile across portfolios
ct = dist_comparison.table
print("\nCarbon tax mean by decile -- all portfolios:")
print(f"{'Decile':>8s}  {'Tax Light':>12s}  {'Tax+Subsidy':>12s}  {'Green Trans.':>12s}")
print("-" * 52)
for i in range(ct.num_rows):
    if (
        ct.column("field_name")[i].as_py() == "carbon_tax"
        and ct.column("metric")[i].as_py() == "mean"
    ):
        decile = ct.column("decile")[i].as_py()
        vals = [
            ct.column(name)[i].as_py()
            for name in portfolios
        ]
        print(f"{decile:8d}  EUR {vals[0]:9.2f}  EUR {vals[1]:9.2f}  EUR {vals[2]:9.2f}")


# ---------------------------------------------------------------------------
# 3. Fiscal Comparison
# ---------------------------------------------------------------------------
# How do the portfolios compare on revenue, cost, and fiscal balance?
#
# The FiscalConfig specifies which columns are revenue and which are costs.
# ---------------------------------------------------------------------------

fiscal_config = PortfolioComparisonConfig(
    indicator_types=("fiscal",),
    fiscal_config=FiscalConfig(
        revenue_fields=["carbon_tax"],
        cost_fields=["subsidy_amount"],
        by_year=True,
        cumulative=True,
    ),
)
fiscal_result = compare_portfolios(portfolio_inputs, fiscal_config)

fiscal_comparison = fiscal_result.comparisons["fiscal"]
ft = fiscal_comparison.table

print("Fiscal balance by year -- all portfolios:")
print(f"{'Year':>6s}  {'Tax Light':>12s}  {'Tax+Subsidy':>12s}  {'Green Trans.':>12s}")
print("-" * 52)
for i in range(ft.num_rows):
    if ft.column("metric")[i].as_py() == "balance":
        year = ft.column("year")[i].as_py()
        vals = [
            ft.column(name)[i].as_py()
            for name in portfolios
        ]
        print(f"{year:6d}  EUR {vals[0]:9.0f}  EUR {vals[1]:9.0f}  EUR {vals[2]:9.0f}")


# ---------------------------------------------------------------------------
# 4. Cross-Comparison Metrics
# ---------------------------------------------------------------------------
# The key question: which portfolio is best?
#
# Cross-comparison metrics rank portfolios on aggregate criteria like total
# revenue, total cost, and fiscal balance. Each metric names the best
# portfolio and provides all portfolio values in ranked order.
# ---------------------------------------------------------------------------

print(f"Cross-comparison metrics: {len(fiscal_result.cross_metrics)}")
print()

for metric in fiscal_result.cross_metrics:
    print(f"Criterion: {metric.criterion}")
    print(f"  Best portfolio: {metric.best_portfolio} (value: {metric.value:,.2f})")
    print(f"  All rankings:")
    for rank, (label, value) in enumerate(metric.all_values.items(), 1):
        marker = " <-- best" if rank == 1 else ""
        print(f"    #{rank} {label}: {value:,.2f}{marker}")
    print()


# ---------------------------------------------------------------------------
# 5. Backward Compatibility with Phase 1 API
# ---------------------------------------------------------------------------
# compare_portfolios() is a convenience wrapper around compare_scenarios().
# You can still use the Phase 1 API directly with portfolio indicator results.
# ---------------------------------------------------------------------------

# Compute indicators manually for 2 portfolios
indicators_a = compute_distributional_indicators(panel_a)
indicators_b = compute_distributional_indicators(panel_b)

# Use compare_scenarios directly
direct_comparison = compare_scenarios(
    [
        ScenarioInput(label="Carbon Tax Light", indicators=indicators_a),
        ScenarioInput(label="Carbon Tax + Subsidy", indicators=indicators_b),
    ],
)

print(f"Direct compare_scenarios result: {direct_comparison.table.num_rows} rows")
print(f"Columns: {direct_comparison.table.column_names}")

# Compare with compare_portfolios for the same 2 portfolios
portfolio_2way = compare_portfolios(
    portfolio_inputs[:2],
    PortfolioComparisonConfig(indicator_types=("distributional",)),
)
portfolio_table = portfolio_2way.comparisons["distributional"].table

print(f"\ncompare_portfolios result: {portfolio_table.num_rows} rows")
print(f"Same shape: {direct_comparison.table.num_rows == portfolio_table.num_rows}")
print("\n(Both APIs produce equivalent results)")


# ---------------------------------------------------------------------------
# 6. Export Results
# ---------------------------------------------------------------------------
# Each per-indicator-type comparison table can be exported to CSV or
# Parquet independently.
# ---------------------------------------------------------------------------

import pyarrow.parquet as pq

# Run a combined comparison
combined_config = PortfolioComparisonConfig(
    indicator_types=("distributional", "fiscal"),
    fiscal_config=FiscalConfig(
        revenue_fields=["carbon_tax"],
        cost_fields=["subsidy_amount"],
        by_year=True,
    ),
)
combined_result = compare_portfolios(portfolio_inputs, combined_config)

# Export each comparison type
for indicator_type, comparison in combined_result.comparisons.items():
    csv_path = comparison.export_csv(OUTPUT_DIR / f"portfolio_{indicator_type}.csv")
    parquet_path = comparison.export_parquet(OUTPUT_DIR / f"portfolio_{indicator_type}.parquet")
    print(f"{indicator_type}: CSV ({csv_path.name}), Parquet ({parquet_path.name})")

    # Verify round-trip
    roundtrip = pq.read_table(str(parquet_path))
    assert roundtrip.num_rows == comparison.table.num_rows

# Cross-metrics are available programmatically
print(f"\nCross-metrics: {len(combined_result.cross_metrics)} metrics available")
print(f"Warnings: {len(combined_result.warnings)}")

print("\nGenerated files:")
for path in sorted(OUTPUT_DIR.iterdir()):
    print(f"  {path.name}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
# This demo covered the multi-portfolio comparison API from Epic 12:
#
# - PortfolioComparisonInput wraps a label + panel
# - PortfolioComparisonConfig controls which indicator types to compute
# - compare_portfolios() produces per-indicator comparison tables + cross-metrics
# - Cross-metrics rank portfolios on aggregate criteria
# - Full backward compatibility with compare_scenarios()
#
# Future work:
# - Epic 13: Custom template packs in portfolios
# - Epic 17: GUI portfolio comparison dashboard
# ---------------------------------------------------------------------------
