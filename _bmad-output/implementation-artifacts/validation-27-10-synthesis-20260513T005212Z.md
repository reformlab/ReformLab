<!-- VALIDATION_SYNTHESIS_START -->
## Synthesis Summary

17 issues verified, 4 false positives dismissed, 12 changes applied to story file. The most critical fixes corrected factual errors in the "Current State" section that would have caused a visual regression (changing failed badge color from red to yellow), and removed orphaned tasks that had no acceptance criteria coverage.

## Validations Quality

**Validator A (Score: 7.3 - REJECT):**
- Identified structural issues (story size violates INVEST "Small", AC-Task mapping broken)
- Found interface mismatch between AC-5 and Implementation Spec
- Raised valid concerns about performance and test migration
- Had several factual errors about the actual codebase (claimed ResultDetailView returns "default" for failed, but actual code returns "destructive")

**Validator B (Score: 17.9 - REJECT):**
- Excellent verification with actual source code inspection
- Identified critical factual errors in "Current State" section that would have caused developer confusion
- Found the 4th statusVariant in ExecutionMatrix.tsx with type incompatibility
- Found 11 missing files from migration target list (26 files vs 15 listed)
- Identified policyLabel type mismatch (camelCase vs snake_case API types)
- Found two wrong file paths (RunSummaryPanel in engine/, ExecutionMatrix in comparison/)

**Overall validation quality: 8/10** - Validator B's findings were particularly valuable and prevented a significant visual regression. Both validators correctly identified the orphaned tasks issue.

## Issues Verified (by severity)

### Critical

- **statusVariant "Current State" contains factual errors**: Story claimed ResultDetailView returns "default" for failed and comparison-helpers returns "warning", but actual code returns "destructive" in both files. | **Source**: Validator B | **Fix**: Corrected "Current State" section to show actual return values

- **AC-8 proposes wrong reconciliation direction**: Story says "reconcile to 'warning'" but all three files return "destructive" for failed. The only real divergence is in the default case (warning vs default). This conflicts with AC-11 (no visual regressions). | **Source**: Validator B | **Fix**: Changed AC-8 and Implementation Specification to preserve `failed → "destructive"` and reconcile default case to `"warning"`

- **4th statusVariant in ExecutionMatrix.tsx undocumented**: Uses uppercase ExecutionStatus enum values, incompatible with proposed lowercase-string helper. | **Source**: Validator B | **Fix**: Added ExecutionMatrix to "Status Badge Mappings" with note about type incompatibility

- **Tasks 4 and 5 orphaned (no AC coverage)**: Loading-state component references "AC: #4" but AC-4 is formatDate; Canonical icons references "AC: #5" but AC-5 is formatTimestamp. | **Source**: Both validators | **Fix**: Removed Tasks 4 and 5 entirely along with related new files from Project Structure Notes

### High

- **policyLabel interface type mismatch**: Story specifies camelCase but API types use snake_case. Also loses "Scenario" vs "Scenario run" distinction. | **Source**: Validator B | **Fix**: Updated policyLabel interface to use snake_case matching API types

- **11 files missing from migration target list**: Grep finds 26 files with toLocaleString(), story only lists 15. | **Source**: Validator B | **Fix**: Added comprehensive list using grep output

- **Two wrong file paths**: RunSummaryPanel is in `engine/` not `screens/`, ExecutionMatrix is in `comparison/` not `simulation/`. | **Source**: Validator B | **Fix**: Corrected paths throughout story

- **Task AC reference numbers wrong**: Tasks reference AC: #2, #3, #7 but should reference AC: #9, #8, #12. | **Source**: Validator B | **Fix**: Corrected AC reference numbers in task labels

- **comparison/index.ts barrel export missing**: Re-exports statusVariant, needs update when moving. | **Source**: Validator B | **Fix**: Added comparison/index.ts to modified files list

### Medium

- **formatTimestamp interface not clear in AC-5**: Shows single-param usage but spec has two params. | **Source**: Validator A | **Fix**: Updated AC-5 to clarify optional style parameter

- **Locale preservation guidance missing**: AC-9 has exception clause but no guidance on identifying intentional differences. | **Source**: Validator A | **Fix**: Added Dev Notes section on locale exception identification

- **ResultDetailView formatTs includes seconds**: Migration risk if default "short" format used. | **Source**: Validator B | **Fix**: Added note in migration targets to use "full" style

- **statusVariant placement ambiguous**: AC-8 says formatters.ts, Tasks say status-variants.ts. | **Source**: Validator B | **Fix**: Clarified status-variants.ts as canonical location per Tasks

### Low

- **Story size concern**: Touching 25-30 files is large but work is mechanical. | **Source**: Validator A | **Fix**: None - keeping as-is, work is parallelizable and component-level commits minimize conflict risk

- **Performance considerations missing**: No requirements for Intl formatter memoization. | **Source**: Validator A | **Fix**: None - defer to implementation; formatters are simple utilities

## Issues Dismissed

- **Claimed Issue**: "can land in parallel with most P0/P1 stories" contradicts touching 25-30 files | **Raised by**: Validator A | **Dismissal Reason**: Changes are mechanical and isolated to formatting. Component-level commits make conflict resolution straightforward.

- **Claimed Issue**: Verbose Dev Notes repeat implementation specifications | **Raised by**: Validator A | **Dismissal Reason**: Duplication provides context without scrolling. Story file not token-constrained for this workflow.

- **Claimed Issue**: Test migration strategy missing | **Raised by**: Validator A | **Dismissal Reason**: AC-10 requires unit tests; AC-11 implies snapshot test updates. Additional guidance not required.

- **Claimed Issue**: Task AC references misnumbered | **Raised by**: Validator B | **Dismissal Reason**: Already addressed as part of High-priority fix.

## Deep Verify Integration

Deep Verify did not produce findings for this story.

### DV-Validator Overlap

N/A - No Deep Verify findings were present.

## Changes Applied

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - AC-5 (line 19)
**Change**: Clarified optional style parameter in AC-5
**Before**:
```
5. **AC-5 (timestamp formatting):** Given any component needs to display a timestamp with time, when it calls `formatTimestamp("2026-05-13T14:48:00Z")`, then it returns "May 13, 2026, 02:48 PM" (consistent format across all timestamp displays).
```
**After**:
```
5. **AC-5 (timestamp formatting):** Given any component needs to display a timestamp with time, when it calls `formatTimestamp("2026-05-13T14:48:00Z")` (style defaults to "short"), then it returns "May 13, 2026, 02:48 PM" (consistent format across all timestamp displays; style: "full" includes seconds).
```

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - AC-8 (line 22)
**Change**: Corrected reconciliation direction to preserve failed→destructive
**Before**:
```
8. **AC-8 (status variant consolidation):** ...divergent return for `failed` is reconciled to `"warning"` (the most common variant).
```
**After**:
```
8. **AC-8 (status variant consolidation):** ...preserves the consistent return for `failed` as `"destructive"` while reconciling the divergent default case to `"warning"`.
```

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - Current State (lines 84-91)
**Change**: Fixed factual errors about statusVariant return values, added 4th function
**Before**:
```
**Status Badge Mappings (3 duplicate functions):**
- `ResultsListPanel.tsx:19-23`: completed→success, failed→destructive, default→warning
- `ResultDetailView.tsx:55-59`: completed→success, failed→default (divergent!)
- `comparison-helpers.ts:50-56`: completed→success, failed→warning
```
**After**:
```
**Status Badge Mappings (4 duplicate functions):**
- `ResultsListPanel.tsx:19-23`: completed→success, failed→destructive, default→warning
- `ResultDetailView.tsx:55-59`: completed→success, failed→destructive, default→default (divergent!)
- `comparison-helpers.ts:50-56`: completed→success, failed→destructive, default→warning
- `ExecutionMatrix.tsx:43-54`: COMPLETED→success, FAILED→destructive, uses uppercase ExecutionStatus enum (type-incompatible with lowercase string version; keep separate or add case normalization)
```

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - Implementation Specifications (lines 147-154)
**Change**: Updated statusVariant spec to preserve destructive for failed
**Before**:
```
**statusVariant(status: string): BadgeVariant**
// Reconciled mapping (failed → "warning" as most common):
// "failed" → "warning" (not "destructive", not "default")
```
**After**:
```
**statusVariant(status: string): BadgeVariant**
// Preserves existing behavior (all three files return "destructive" for failed):
// "failed" → "destructive" (consistent across all 3 files)
// default → "warning" (reconciled from ResultDetailView's "default")
```

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - Implementation Specifications (lines 157-161)
**Change**: Fixed policyLabel interface to use snake_case
**Before**:
```
**policyLabel(run: { scenarioName?: string; portfolioName?: string }): string**
// return run.scenarioName || run.portfolioName || "Portfolio run"
```
**After**:
```
**policyLabel(run: { portfolio_name?: string | null; template_name?: string | null; run_kind?: string }): string**
// return run.portfolio_name || run.template_name || (run.run_kind === "portfolio" ? "Portfolio run" : "Scenario run")
```

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - Tasks/Subtasks (lines 35-51)
**Change**: Removed orphaned Tasks 4 and 5, corrected AC references, added ExecutionMatrix note
**Before**:
```
- [ ] Sweep `.toLocaleString()` call sites (AC: #2)
- [ ] Consolidate `statusVariant` (AC: #3)
- [ ] Loading-state component (AC: #4) [...]
- [ ] Canonical icons (AC: #5) [...]
- [ ] Consolidate `policyLabel` (AC: #7)
```
**After**:
```
- [ ] Sweep `.toLocaleString()` call sites (AC: #9)
- [ ] Consolidate `statusVariant` (AC: #8)
  - [ ] NOTE: ExecutionMatrix.tsx uses uppercase ExecutionStatus and is NOT consolidated
- [ ] Consolidate `policyLabel` (AC: #12)
```

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - Dev Notes (after line 63)
**Change**: Added locale exception identification and formatTimestamp migration notes
**Before**:
```
- The audit at `...sprint-change-proposal-2026-04-26.md` Section 4.1 lists the consolidation targets.
```
**After**:
```
- The audit at `...sprint-change-proposal-2026-04-26.md` Section 4.1 lists the consolidation targets.

### Locale Exception Identification
Before replacing any `.toLocaleString()` call, verify:
1. Check if the call has explicit locale parameter
2. Check if the call has custom format options
3. If either present, preserve the call and add TODO comment

### formatTimestamp Migration Note
`ResultDetailView.tsx` uses `formatTs` which includes seconds. When migrating, use `formatTimestamp(value, "full")` to preserve this behavior.
```

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - Target Files for Migration (lines 165-196)
**Change**: Expanded list with all 26 files from grep, corrected paths
**Before**:
```
**Number formatting (.toLocaleString, .toFixed):**
- `ResultsOverviewScreen.tsx`, `PopulationProfiler.tsx` [... 15 files ...]
**Date/timestamp formatting:**
- `ResultsListPanel.tsx` - formatTimestamp
- `ResultDetailView.tsx` - formatTs
- `PopulationLibraryScreen.tsx` - toLocaleDateString
- `ExecutionMatrix.tsx` - toLocaleString
```
**After**:
```
**Number formatting (.toLocaleString, .toFixed):**
- `ResultsOverviewScreen.tsx`, `PopulationProfiler.tsx` [... 26 files total ...]
- Added: `engine/EngineStageScreen.tsx`, `comparison/RunSelector.tsx`, `simulation/DataSourceBrowser.tsx`, `simulation/YearDetailPanel.tsx`, `simulation/TransitionChart.tsx`, `simulation/PopulationPreview.tsx`, `simulation/PopulationDistributionChart.tsx`, `screens/PopulationSelectionScreen.tsx`, `comparison/WelfareTab.tsx`, `comparison/FiscalTab.tsx`, `comparison/DetailPanel.tsx`
**Date/timestamp formatting:**
- `ResultsListPanel.tsx` - formatTimestamp (short style, no seconds)
- `ResultDetailView.tsx` - formatTs (use "full" style to preserve seconds)
- `PopulationLibraryScreen.tsx` - toLocaleDateString
- `comparison/ExecutionMatrix.tsx` - toLocaleString
**Status badge variants (note: ExecutionMatrix uses uppercase ExecutionStatus, keep separate):**
- `ResultsListPanel.tsx:19-23`
- `ResultDetailView.tsx:55-59`
- `comparison-helpers.ts:50-56`
- `comparison/ExecutionMatrix.tsx:43-54` (type-incompatible, do not consolidate)
```

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - Project Structure Notes (lines 224-235)
**Change**: Removed orphaned files, added comparison/index.ts
**Before**:
```
**New files:**
- [...], `frontend/src/components/ui/data-loading.tsx`, `frontend/src/lib/icons.ts`, [...]
**Modified files:**
- ~25–30 component files for .toLocaleString() sweep
- 3 files for statusVariant consolidation
- 2 files for policyLabel consolidation
- Loading state pattern replacements
- Icon import updates
```
**After**:
```
**New files:**
- `frontend/src/utils/formatters.ts`
- `frontend/src/utils/run-labels.ts`
- `frontend/src/lib/status-variants.ts`
- `frontend/src/utils/__tests__/formatters.test.ts`
- `frontend/src/utils/__tests__/run-labels.test.ts`
**Modified files:**
- 26 component files for .toLocaleString() sweep (see Target Files list above)
- 3 files for statusVariant consolidation
- 2 files for policyLabel consolidation
- `frontend/src/components/comparison/index.ts` - update barrel export for statusVariant
```

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - References section (line 247)
**Change**: Added ExecutionMatrix reference
**Before**:
```
- [Source: frontend/src/components/comparison/comparison-helpers.ts:50-56] - statusVariant
- [Source: frontend/src/components/simulation/MultiRunChart.tsx:120-130] - formatValue
```
**After**:
```
- [Source: frontend/src/components/comparison/comparison-helpers.ts:50-56] - statusVariant
- [Source: frontend/src/components/comparison/ExecutionMatrix.tsx:43-54] - statusVariant (uppercase ExecutionStatus, not consolidated)
- [Source: frontend/src/components/simulation/MultiRunChart.tsx:120-130] - formatValue
```

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - Completion Notes List (lines 263-276)
**Change**: Updated to reflect verified findings
**Before**:
```
- Identified 15-20 components with inline .toLocaleString() calls
- Found 3 duplicate statusVariant() functions with divergent "failed" handling
- Reconciled divergent statusVariant and policyLabel implementations
```
**After**:
```
- Identified 26 components with inline .toLocaleString() calls (via grep)
- Found 3 duplicate statusVariant() functions with consistent "failed" handling (all return "destructive"), divergent default case
- Found 4th statusVariant in ExecutionMatrix.tsx using uppercase ExecutionStatus (type-incompatible)
- Reconciled statusVariant (preserve failed→destructive, reconcile default→warning)
- Reconciled policyLabel (use snake_case API field names, preserve run_kind-aware fallback)
```

**Location**: _bmad-output/implementation-artifacts/27-10-consolidate-frontend-formatters.md - File List (lines 286-293)
**Change**: Removed orphaned files
**Before**:
```
**New files to create:**
- `frontend/src/utils/formatters.ts`
- `frontend/src/utils/run-labels.ts`
- `frontend/src/lib/status-variants.ts` (or include in formatters.ts)
- `frontend/src/components/ui/data-loading.tsx`
- `frontend/src/lib/icons.ts`
- `frontend/src/utils/__tests__/formatters.test.ts`
- `frontend/src/utils/__tests__/run-labels.test.ts`
```
**After**:
```
**New files to create:**
- `frontend/src/utils/formatters.ts`
- `frontend/src/utils/run-labels.ts`
- `frontend/src/lib/status-variants.ts`
- `frontend/src/utils/__tests__/formatters.test.ts`
- `frontend/src/utils/__tests__/run-labels.test.ts`
```

<!-- VALIDATION_SYNTHESIS_END -->
