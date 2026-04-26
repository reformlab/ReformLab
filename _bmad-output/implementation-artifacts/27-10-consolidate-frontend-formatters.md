# Story 27.10: Consolidate frontend formatters

Status: ready-for-dev

## Story

As a frontend developer maintaining the UI,
I want a single source of truth for number, currency, percent, date, timestamp, and status-variant formatting,
so that all screens render consistent values and locale handling, and future polish only needs to change one place.

## Acceptance Criteria

1. Given the new `frontend/src/utils/formatters.ts` module, when imported, then it exports: `formatNumber(value, precision?)`, `formatCurrency(value, currency?)`, `formatPercent(value, precision?)`, `formatDate(ts, style?)`, `formatRunTimestamp(ts, style?: "short" | "full")`, and `formatLargeNumber(value)`.
2. Given the audit-identified ≥42 inline `.toLocaleString()` call sites across components like `YearDetailPanel`, `TransitionChart`, `ResultDetailView`, `ResultsListPanel`, `DataSourceBrowser`, `PopulationDistributionChart`, `PopulationGenerationProgress`, `PopulationPreview`, `ResultsOverviewScreen`, `PopulationLibraryScreen`, `ScenarioStageScreen`, `PopulationSelectionScreen`, `PopulationDataTable`, `PopulationExplorer`, `PopulationProfiler`, `PopulationQuickPreview`, `PopulationComparisonView`, `PopulationSummaryView`, `RunSelector`, `DetailPanel`, `FiscalTab`, `WelfareTab`, `ExecutionMatrix`, `PopulationUploadZone`, `WorkflowNavRail`, `RunSummaryPanel`, `RunManifestViewer`, when this story is complete, then each call site uses the appropriate helper from `formatters.ts`.
3. Given the three duplicate `statusVariant()` functions at `ResultsListPanel.tsx:19-23`, `ResultDetailView.tsx:55-59`, and `comparison-helpers.ts:50-56`, when consolidated, then a single `statusVariant(status)` lives in `frontend/src/lib/status-variants.ts` and the divergent return for `failed` (`"default"` vs `"warning"`) is reconciled to one canonical value.
4. Given the loading-state inconsistency (Skeleton vs spinner vs `"Loading..."` text), when consolidated, then a `<DataLoading variant="skeleton" | "text" | "spinner" />` component exists and replaces the ad-hoc patterns at the audit-identified sites.
5. Given the icon inconsistency (`CircleHelp` vs `HelpCircle`, `Trash2` vs `X` vs `XCircle` for delete), when consolidated, then a `frontend/src/lib/icons.ts` exports canonical names (`HelpIcon`, `DeleteIcon`, `DismissIcon`) and call sites import from there.
6. Given the existing test suite, when this story is complete, then all tests pass and any tests that previously relied on locale-specific or per-component formatting still pass (snapshot tests may need updating).
7. Given the duplicate `policyLabel()` helpers at `ResultsListPanel.tsx:40-44` and `ResultDetailView.tsx:49-53`, when consolidated, then a single helper lives in `frontend/src/utils/run-labels.ts` and the divergent fallback (`"Portfolio run"` vs `"Portfolio"`) is reconciled.

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

### Project Structure Notes

- New files: `frontend/src/utils/formatters.ts`, `frontend/src/lib/status-variants.ts`, `frontend/src/components/ui/data-loading.tsx`, `frontend/src/lib/icons.ts`, `frontend/src/utils/run-labels.ts`, plus matching tests
- Modified: ~25–30 component files (sweep of `.toLocaleString` and the three duplicate utilities)
- This story may produce a large diff; commit per-utility to keep PRs reviewable

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.10]
- [Source: Audit findings (Stage 4-5 + cross-cutting code redundancy report)]
- [Source: frontend/src/components/simulation/ResultsListPanel.tsx:19-23, :40-44]
- [Source: frontend/src/components/simulation/ResultDetailView.tsx:55-59, :49-53]
- [Source: frontend/src/components/comparison/comparison-helpers.ts:50-56]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
