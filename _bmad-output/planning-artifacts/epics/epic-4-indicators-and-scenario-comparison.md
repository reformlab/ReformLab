# Epic 4: Indicators and Scenario Comparison

**User outcome:** Analyst can compute and compare distributional, welfare, and fiscal indicators across scenarios.

**Status:** done

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-401 | Story | P0 | 5 | Implement distributional indicators by income decile | done | FR19 |
| BKL-402 | Story | P0 | 3 | Implement geographic aggregation indicators | done | FR20 |
| BKL-403 | Story | P0 | 5 | Implement welfare indicators (winners/losers, net changes) | done | FR21 |
| BKL-404 | Story | P0 | 5 | Implement fiscal indicators (annual and cumulative) | done | FR22 |
| BKL-405 | Story | P0 | 5 | Implement scenario comparison tables across runs | done | FR24, FR33 |
| BKL-406 | Story | P1 | 5 | Implement custom derived indicator formulas | done | FR23 |

## Epic-Level Acceptance Criteria

- Indicators are generated per scenario and per year.
- Comparison outputs support side-by-side baseline/reform analysis.
- Export format is machine-readable CSV/Parquet.

## Story-Level Acceptance Criteria

**BKL-401: Implement distributional indicators by income decile**

- Given a completed scenario run with household-level results, when distributional analysis is invoked, then indicators are computed for each of the 10 income deciles.
- Given a population with missing income data for some households, when analysis runs, then those households are flagged and excluded with a count warning.

**BKL-402: Implement geographic aggregation indicators**

- Given household results with region codes, when geographic aggregation is invoked, then indicators are grouped by region.
- Given a region code not in the reference table, when aggregated, then results include an "unmatched" category with count.

**BKL-403: Implement welfare indicators (winners/losers, net changes)**

- Given baseline and reform scenario results, when welfare indicators are computed, then winner count, loser count, and net gain/loss per decile are returned.
- Given a scenario where all households are neutral (zero net change), when computed, then winner and loser counts are both zero.

**BKL-404: Implement fiscal indicators (annual and cumulative)**

- Given a multi-year scenario run, when fiscal indicators are computed, then annual revenue, cost, and balance are returned per year.
- Given a 10-year run, when cumulative fiscal indicators are requested, then they sum correctly across all years.

**BKL-405: Implement scenario comparison tables across runs**

- Given two completed scenario runs (baseline and reform), when comparison is invoked, then a side-by-side table is produced with all indicator types.
- Given comparison output, when exported to CSV/Parquet, then the file is readable with correct column headers and types.

**BKL-406: Implement custom derived indicator formulas**

- Given a user-defined formula referencing existing indicator fields, when the formula is registered and invoked, then it produces a new derived indicator column with correct values.
- Given an invalid formula (e.g., referencing a nonexistent field), when registered, then a clear error identifies the problem before computation begins.

---
