# Story 27.10: Consolidate frontend formatters

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst viewing results across the application,
I want all numeric, currency, date, timestamp, and status values to display consistently regardless of which component I'm viewing,
so that the UI feels coherent and trustworthy, and future formatting changes can be made in one place.

## Acceptance Criteria

1. **AC-1 (centralized formatters module):** Given the new `frontend/src/utils/formatters.ts` module, when imported, then it exports: `formatNumber(value, options?)`, `formatCurrency(value, options?)`, `formatPercent(value, options?)`, `formatDate(value)`, `formatTimestamp(value)`, and `formatLargeNumber(value)`.
2. **AC-2 (number formatting):** Given any component needs to format a number for display, when it calls `formatNumber(1234.56)`, then it returns "1,235" (thousands separator, 0 decimals by default, configurable via options).
3. **AC-3 (currency formatting):** Given any component needs to display a currency value in EUR, when it calls `formatCurrency(1234.56)`, then it returns "€1,235" (€ prefix, thousands separator, 0 decimals by default).
4. **AC-4 (date formatting):** Given any component needs to display a date, when it calls `formatDate("2026-05-13")`, then it returns "May 13, 2026" (consistent format across all date displays).
5. **AC-5 (timestamp formatting):** Given any component needs to display a timestamp with time, when it calls `formatTimestamp("2026-05-13T14:48:00Z")`, then it returns "May 13, 2026, 02:48 PM" (consistent format across all timestamp displays).
6. **AC-6 (compact/large number formatting):** Given a component needs to display large numbers compactly, when it calls `formatLargeNumber(2100000000)`, then it returns "2.1B" (B/M/k suffixes, 1 decimal place).
7. **AC-7 (percentage formatting):** Given a component needs to display a percentage, when it calls `formatPercent(0.44)`, then it returns "44%" (multiplies by 100, appends %, 0 decimals by default).
8. **AC-8 (status variant consolidation):** Given the duplicate `statusVariant()` functions at `ResultsListPanel.tsx`, `ResultDetailView.tsx`, and `comparison-helpers.ts`, when consolidated, then a single `statusVariant(status)` lives in `formatters.ts` and the divergent return for `failed` is reconciled to `"warning"` (the most common variant).
9. **AC-9 (all inline formatting migrated):** Given the new formatters are available, when the codebase is searched for `.toLocaleString()`, then all inline number/currency/date/timestamp formatting has been replaced with calls to the centralized formatters, EXCEPT where locale-specific behavior is intentionally different.
10. **AC-10 (comprehensive tests):** Given the formatter utilities, when the test suite runs, then all formatters have unit tests covering edge cases (null/undefined, NaN, Infinity, negative values, zero, very large numbers).
11. **AC-11 (no visual regressions):** Given the formatting changes are applied, when the application renders, then all numeric, currency, date, and status displays appear visually identical to before (formatting consolidation only, no format changes).
12. **AC-12 (policy label consolidation):** Given the duplicate `policyLabel()` helpers at `ResultsListPanel.tsx:40-44` and `ResultDetailView.tsx:49-53`, when consolidated, then a single helper lives in `frontend/src/utils/run-labels.ts` and the divergent fallback is reconciled to `"Portfolio run"`.

## Tasks / Subtasks

- [ ] Create `formatters.ts` (AC: #1)
  - [ ] New file `frontend/src/utils/formatters.ts` with the six exported functions
  - [ ] Each function uses `Intl.NumberFormat` / `Intl.DateTimeFormat` with sensible defaults
  - [ ] `formatLargeNumber` matches the existing `MultiRunChart.tsx` behaviour (1.2M, 1.0B)
  - [ ] Document each function with a short docstring example
- [ ] Sweep `.toLocaleString()` call sites (AC: #2)
  - [ ] Use `grep -rn "\.toLocaleString" frontend/src/components` to enumerate sites
  - [ ] Replace each with the appropriate helper
  - [ ] Track sites in a checklist; commit per-component to keep diffs reviewable
- [ ] Consolidate `statusVariant` (AC: #3)
  - [ ] New file `frontend/src/lib/status-variants.ts` exporting one `statusVariant(status)` function
  - [ ] Reconcile failed → use `"warning"` (consistent with most call sites; ResultDetailView's `"default"` was likely a typo)
  - [ ] Update three call sites to import the shared function
- [ ] Loading-state component (AC: #4)
  - [ ] New file `frontend/src/components/ui/data-loading.tsx` with the three variants
  - [ ] Replace ad-hoc patterns at the audit-identified sites
- [ ] Canonical icons (AC: #5)
  - [ ] New file `frontend/src/lib/icons.ts` re-exporting `lucide-react` icons under canonical names
  - [ ] Update import statements at call sites
- [ ] Consolidate `policyLabel` (AC: #7)
  - [ ] New file `frontend/src/utils/run-labels.ts` with one `policyLabel(run)` function
  - [ ] Reconcile fallback to `"Portfolio run"`
- [ ] Update tests
  - [ ] Add unit tests for each new utility
  - [ ] Run the full test suite; update any snapshot tests as needed
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- Sequencing: this story can land in parallel with most P0/P1 stories. The formatter consolidation is purely mechanical and should not introduce behavior changes.
- For complex sites (e.g., chart axis tick formatters), if the inline call has a unique format string, prefer adding a new helper variant rather than forcing the site to compose multiple helpers.
- Do NOT introduce a generic "format anything" function. Keep helpers narrow and named.
- The audit at `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md` Section 4.1 lists the consolidation targets.

### Current State (Pre-Consolidation)

**Number Formatting Patterns:**
- `toLocaleString()` used in 15+ components for thousands separation
- `toFixed(0/1/2)` used for decimal control in 6+ components
- Custom `formatValue()` in MultiRunChart.tsx and CrossMetricPanel.tsx for compact numbers (B/M/k)
- Inline percentage: `${Math.round(value * 100)}%` in ParameterRow.tsx

**Currency Formatting:**
- Manual `€` prefix: `€${value.toLocaleString()}` in ResultsOverviewScreen.tsx
- Per-year suffix: `€${value.toLocaleString()}/yr`
- No `Intl.NumberFormat` currency options used

**Date/Timestamp Formatting:**
- Duplicate `formatTimestamp()` in ResultsListPanel.tsx (no seconds)
- Duplicate `formatTs()` in ResultDetailView.tsx (includes seconds)
- `toLocaleDateString()` in PopulationLibraryScreen.tsx
- `toLocaleString()` in ExecutionMatrix.tsx

**Status Badge Mappings (3 duplicate functions):**
- `ResultsListPanel.tsx:19-23`: completed→success, failed→destructive, default→warning
- `ResultDetailView.tsx:55-59`: completed→success, failed→default (divergent!)
- `comparison-helpers.ts:50-56`: completed→success, failed→warning

**Policy Label Helpers (2 duplicates):**
- `ResultsListPanel.tsx:40-44`: scenarioName || portfolioName || "Portfolio run"
- `ResultDetailView.tsx:49-53`: scenarioName || portfolioName || "Portfolio"

### Implementation Specifications

**formatNumber(value: number | null | undefined, options?: NumberFormatOptions): string**
```typescript
interface NumberFormatOptions {
  decimals?: number;  // Default: 0
  locale?: string;    // Default: undefined (user locale)
}
// Edge cases: null/undefined → "—", NaN → "NaN", Infinity → "∞"
// Use Intl.NumberFormat for locale-aware formatting
```

**formatCurrency(value: number | null | undefined, options?: CurrencyFormatOptions): string**
```typescript
interface CurrencyFormatOptions extends NumberFormatOptions {
  symbol?: string;     // Default: "€"
  perYear?: boolean;   // Default: false
}
// Returns: "€1,234" or "€1,234/yr" if perYear=true
```

**formatPercent(value: number | null | undefined, options?: PercentFormatOptions): string**
```typescript
interface PercentFormatOptions {
  decimals?: number;        // Default: 0
  multiplyBy100?: boolean;  // Default: true
}
// Returns: "44%" for input 0.44
```

**formatDate(value: string | Date | null | undefined): string**
```typescript
// Format: "May 13, 2026"
// Uses Intl.DateTimeFormat with { year: "numeric", month: "short", day: "2-digit" }
// Edge cases: null/undefined → "—", invalid Date → return original string
```

**formatTimestamp(value: string | Date | null | undefined, style?: "short" | "full"): string**
```typescript
// Short (default): "May 13, 2026, 02:48 PM" - NO seconds
// Full: "May 13, 2026, 02:48:00 PM" - WITH seconds
// Uses Intl.DateTimeFormat
```

**formatLargeNumber(value: number | null | undefined): string**
```typescript
// Matches MultiRunChart.tsx behavior exactly:
// ≥1e9 → "2.1B"  (1 decimal place)
// ≥1e6 → "1.5M"
// ≥1e3 → "2.5k"
// Otherwise → "999" (toFixed(0))
// Edge cases: abs < 1 → "0", preserve negative sign
```

**statusVariant(status: string): BadgeVariant**
```typescript
// Reconciled mapping (failed → "warning" as most common):
// "completed" → "success"
// "failed" → "warning" (not "destructive", not "default")
// "running" | "pending" | "queued" → "warning"
// default → "default"
// Return type: "success" | "destructive" | "warning" | "default"
```

**policyLabel(run: { scenarioName?: string; portfolioName?: string }): string**
```typescript
// Reconciled fallback to "Portfolio run":
// return run.scenarioName || run.portfolioName || "Portfolio run"
```

### Target Files for Migration

**Number formatting (.toLocaleString, .toFixed):**
- `ResultsOverviewScreen.tsx` - currency formatting
- `PopulationProfiler.tsx`, `PopulationSummaryView.tsx`, `PopulationComparisonView.tsx`
- `WorkflowNavRail.tsx`, `RunSummaryPanel.tsx`
- `PopulationDataTable.tsx`, `PopulationExplorer.tsx`
- `PopulationGenerationProgress.tsx`, `PopulationQuickPreview.tsx`
- `PopulationUploadZone.tsx`, `InvestmentDecisionsWizard.tsx`

**Currency formatting (€ prefix):**
- `ResultsOverviewScreen.tsx`

**Date/timestamp formatting:**
- `ResultsListPanel.tsx` - formatTimestamp
- `ResultDetailView.tsx` - formatTs
- `PopulationLibraryScreen.tsx` - toLocaleDateString
- `ExecutionMatrix.tsx` - toLocaleString

**Compact number formatting:**
- `MultiRunChart.tsx` - formatValue
- `CrossMetricPanel.tsx` - formatValue

**Percentage formatting:**
- `ParameterRow.tsx` - inline Math.round

**Status badge variants:**
- `ResultsListPanel.tsx:19-23`
- `ResultDetailView.tsx:55-59`
- `comparison-helpers.ts:50-56`

**Policy label helpers:**
- `ResultsListPanel.tsx:40-44`
- `ResultDetailView.tsx:49-53`

### Project Structure Notes

**New files:**
- `frontend/src/utils/formatters.ts` - All formatter utilities
- `frontend/src/utils/run-labels.ts` - policyLabel helper
- `frontend/src/lib/status-variants.ts` - statusVariant (or include in formatters.ts)
- `frontend/src/components/ui/data-loading.tsx` - Loading state component
- `frontend/src/lib/icons.ts` - Canonical icon exports
- `frontend/src/utils/__tests__/formatters.test.ts` - Formatter tests
- `frontend/src/utils/__tests__/run-labels.test.ts` - policyLabel tests

**Modified files:**
- ~25–30 component files for .toLocaleString() sweep
- 3 files for statusVariant consolidation
- 2 files for policyLabel consolidation
- Loading state pattern replacements
- Icon import updates

**Commit strategy:**
- Commit per-utility to keep PRs reviewable
- Example commits: "feat: add formatters.ts", "refactor: migrate ResultsListPanel to formatters", etc.

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.10]
- [Source: _bmad-output/planning-artifacts/epics.md#Story-27.10]
- [Source: frontend/src/components/simulation/ResultsListPanel.tsx:19-23, :40-44] - statusVariant, policyLabel, formatTimestamp
- [Source: frontend/src/components/simulation/ResultDetailView.tsx:55-59, :49-53] - statusVariant, policyLabel, formatTs
- [Source: frontend/src/components/comparison/comparison-helpers.ts:50-56] - statusVariant
- [Source: frontend/src/components/simulation/MultiRunChart.tsx:120-130] - formatValue (compact numbers)
- [Source: frontend/src/components/simulation/CrossMetricPanel.tsx] - formatValue (compact numbers)
- [Source: frontend/src/components/simulation/ParameterRow.tsx] - Inline percentage formatting
- [Source: frontend/src/components/screens/results/ResultsOverviewScreen.tsx] - Currency formatting

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (via BMad create-story workflow)

### Debug Log References

### Completion Notes List

**Analysis completed:**
- Explored entire frontend codebase for formatter usage patterns
- Identified 15-20 components with inline .toLocaleString() calls
- Found 3 duplicate statusVariant() functions with divergent "failed" handling
- Found 2 duplicate policyLabel() helpers with different fallbacks
- Mapped existing formatValue() implementation for compact numbers
- Identified all target files for migration

**Story context enhanced:**
- Added detailed implementation specifications for each formatter
- Documented edge cases and null/undefined handling
- Specified exact output formats for date/timestamp formatters
- Reconciled divergent statusVariant and policyLabel implementations
- Listed all target files for migration

**Ready for development:**
- All formatters fully specified with TypeScript interfaces
- Migration strategy documented
- Test strategy defined with edge cases
- No visual regressions expected (format consolidation only)

### File List

**New files to create:**
- `frontend/src/utils/formatters.ts`
- `frontend/src/utils/run-labels.ts`
- `frontend/src/lib/status-variants.ts` (or include in formatters.ts)
- `frontend/src/components/ui/data-loading.tsx`
- `frontend/src/lib/icons.ts`
- `frontend/src/utils/__tests__/formatters.test.ts`
- `frontend/src/utils/__tests__/run-labels.test.ts`

**Existing files to modify:**
- `frontend/src/components/simulation/ResultsListPanel.tsx`
- `frontend/src/components/simulation/ResultDetailView.tsx`
- `frontend/src/components/comparison/comparison-helpers.ts`
- `frontend/src/components/simulation/MultiRunChart.tsx`
- `frontend/src/components/simulation/CrossMetricPanel.tsx`
- `frontend/src/components/simulation/ParameterRow.tsx`
- `frontend/src/components/screens/results/ResultsOverviewScreen.tsx`
- `frontend/src/components/population/PopulationProfiler.tsx`
- `frontend/src/components/population/PopulationSummaryView.tsx`
- `frontend/src/components/population/PopulationComparisonView.tsx`
- `frontend/src/components/population/PopulationLibraryScreen.tsx`
- `frontend/src/components/population/PopulationDataTable.tsx`
- `frontend/src/components/population/PopulationExplorer.tsx`
- `frontend/src/components/population/PopulationUploadZone.tsx`
- `frontend/src/components/population/PopulationQuickPreview.tsx`
- `frontend/src/components/population/PopulationGenerationProgress.tsx`
- `frontend/src/components/screens/WorkflowNavRail.tsx`
- `frontend/src/components/screens/RunSummaryPanel.tsx`
- `frontend/src/components/simulation/ExecutionMatrix.tsx`
- `frontend/src/components/simulation/InvestmentDecisionsWizard.tsx`
- Additional components with .toLocaleString() patterns (per grep results)
