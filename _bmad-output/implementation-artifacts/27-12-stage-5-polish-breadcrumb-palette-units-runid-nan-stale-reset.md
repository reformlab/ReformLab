# Story 27.12: Stage 5 polish — breadcrumb, palette, units, run-id width, NaN guards, stale-comparison reset

Status: ready-for-dev

## Story

As an analyst working in Stage 5 (Run / Results / Compare),
I want consistent units, semantic colours for baseline vs reform, clearer sub-view location, wider run identifiers, and protection against stale comparison state and NaN/Infinity displays,
so that I can read and trust the results panel without parsing inconsistencies.

## Acceptance Criteria

1. Given Stage 5 sub-views (Overview, Runner, Comparison, Decisions, Manifest), when the user is in any sub-view, then a persistent breadcrumb header at the top of the Stage 5 surface shows `Results > {sub-view name}`.
2. Given the Comparison view renders runs, when displayed, then the baseline run uses a darker semantic color (e.g., `--chart-baseline`) and reform runs use the existing `--chart-reform-a` through `--chart-reform-d` tokens; the rainbow palette is replaced.
3. Given the Fiscal and Welfare tabs in Comparison, when columns render, then column headers include unit labels (e.g., "Revenue (€)") and large numeric values use `formatLargeNumber()` from Story 27.10's formatters (`€1.2M` instead of bare `1234567`).
4. Given run-id displays in `ResultsListPanel`, `RunSelector`, and `RunManifestViewer`, when shown, then at least 12 characters of the run id are visible in a monospace font, and a copy-to-clipboard button is available adjacent.
5. Given any numeric display that could be NaN or Infinity (e.g., relative comparison with zero baseline) in `CrossMetricPanel`, `MultiRunChart`, and elsewhere, when computed, then the display falls back to `"—"` rather than rendering `NaN` or `Infinity`.
6. Given the Comparison dashboard maintains `selectedRunIds` and `comparisonData`, when `activeScenario.id` changes, then both are reset; the user does not see a comparison from a previous scenario.
7. Given the Comparison view's selected runs list, when some selected runs are in `failed` status, when displayed, then a summary line above the comparison reads "{N} runs completed, {M} failed (excluded from comparison)" instead of silently excluding the failed ones.
8. Given the Detail tab in Results Overview, when the analyst opens it for the first time, then a skeleton placeholder appears immediately (within ~16 ms) instead of an apparent hang while the API call resolves.

## Tasks / Subtasks

- [ ] Sub-view breadcrumb (AC: #1)
  - [ ] In `App.tsx:162-221` (or the Stage 5 wrapper), render a breadcrumb showing the active sub-view
  - [ ] Style it lightweight (text-sm, slate-500) so it doesn't compete with the screen title
- [ ] Semantic comparison palette (AC: #2)
  - [ ] In `ComparisonDashboardScreen.tsx`, replace `CHART_COLORS` rainbow with the semantic tokens (`--chart-baseline`, `--chart-reform-a..d`)
  - [ ] Ensure baseline is visually distinct (heavier weight or darker shade)
  - [ ] Apply consistently in `MultiRunChart`, table headers, and legend
- [ ] Units on Fiscal/Welfare (AC: #3)
  - [ ] In `FiscalTab.tsx` and `WelfareTab.tsx`, append unit labels to column headers
  - [ ] Replace bare `.toLocaleString()` with `formatLargeNumber()` from Story 27.10's helper (or use `formatCurrency` for monetary columns)
- [ ] Run-id width (AC: #4)
  - [ ] Update displays in `ResultsListPanel.tsx`, `RunSelector.tsx`, `RunManifestViewer.tsx` to show ≥12 chars
  - [ ] Add a small copy-to-clipboard button (existing icon set; reuse navigator.clipboard.writeText)
  - [ ] Ensure full ID is available via tooltip and clipboard for unambiguous reference
- [ ] NaN/Infinity guards (AC: #5)
  - [ ] In `CrossMetricPanel.tsx`, `MultiRunChart.tsx`, and any other numeric-render site found by grep for `formatLargeNumber\|toLocaleString` followed by potentially-undefined values, wrap with `Number.isFinite(value) ? format(value) : "—"`
- [ ] Stale-comparison reset (AC: #6)
  - [ ] In `ComparisonDashboardScreen.tsx:63-77`, add a `useEffect` that resets `selectedRunIds` and `comparisonData` when `activeScenario.id` changes
- [ ] Failed-runs summary (AC: #7)
  - [ ] In `ComparisonDashboardScreen.tsx`, when filtering selected runs by `status === "completed"`, also count failed runs and render the summary line
- [ ] Detail-tab skeleton (AC: #8)
  - [ ] In `ResultsOverviewScreen.tsx:126-146`, render the skeleton immediately when the Detail tab is opened, before the API call resolves
- [ ] Tests
  - [ ] Render tests for breadcrumb, palette, unit headers
  - [ ] Run-id copy-to-clipboard test
  - [ ] NaN guard test (provide NaN values; assert display shows `—`)
  - [ ] Stale-comparison reset test (change scenario; assert comparison cleared)
  - [ ] Failed-runs summary test
  - [ ] Detail-tab skeleton test (mock slow API; assert skeleton present immediately)
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- This story bundles eight small Stage 5 polish items. They are independent enough to land in parallel commits but small enough to fit in one story.
- Coordinate with Story 27.10 (formatter consolidation) — units and `formatLargeNumber` reuse those helpers.
- The chart tokens `--chart-baseline` and `--chart-reform-a..d` are already documented in CLAUDE memory; verify they're defined in the brand theme before using.

### Project Structure Notes

- Files touched: `App.tsx`, `ComparisonDashboardScreen.tsx`, `FiscalTab.tsx`, `WelfareTab.tsx`, `ResultsListPanel.tsx`, `RunSelector.tsx`, `RunManifestViewer.tsx`, `CrossMetricPanel.tsx`, `MultiRunChart.tsx`, `ResultsOverviewScreen.tsx`, matching tests
- No new files (uses helpers from Story 27.10)

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.12]
- [Source: Audit findings (Stage 4-5 audit report) findings #6, #7, #8, #9, #10, #11, #12, #13]
- [Source: CLAUDE memory] (chart color tokens)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
