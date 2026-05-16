# Story 27.15: UX-spec amendments

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a product team maintaining design documentation,
I want the UX specification to reflect the interaction changes implemented in Epic 27,
so that the written source of truth matches the implemented product and future developers understand the intended behavior.

## Background

Epic 27 implemented UX stabilization work across Stories 27.6, 27.7, 27.8, and 27.12. This story updates the UX specification to document those changes:

1. **Story 27.6:** Four-state nav rail model — already added to spec (lines 1365-1369) in that story's AC-7; remaining gap is prose explanation of when each state applies
2. **Story 27.7:** Clickable Investment Decisions wizard step labels — not yet documented
3. **Story 27.8:** Population stage restructure from three peer tabs to two-step flow (Source → Inspect) — not yet documented
4. **Story 27.12:** Stage 5 polish (breadcrumb context, semantic palette, unit labels, run-id width, NaN guards, stale reset) — not yet documented

These changes are already implemented and tested. This story is documentation-only—no code changes.

## Acceptance Criteria

1. **AC-1 (Nav rail four-state model):** Given the UX spec section "Application Shell & Navigation" around line 1365, verify the four-state model is present (already added in Story 27.6) and add prose explaining when each state applies:
   - Active: current stage, user is here
   - Complete: stage was finished successfully
   - Incomplete: stage was touched but not finished (user navigated away without completing)
   - Not started: stage has not been touched yet
   - The visual treatments (bg-blue-500, bg-emerald-500, border treatments) are already documented at lines 1365-1369

2. **AC-2 (Investment Decisions clickable wizard):** Given the Stage 3 section around line 2160-2168, when updated, then it documents that wizard step labels (Enable, Model, Parameters, Review) are clickable for backward navigation, with:
   - Visited and current steps are clickable, styled `text-emerald-600 cursor-pointer` (visited) or `text-blue-600 font-medium` (current)
   - Unreached steps are visibly disabled (`text-slate-400 cursor-not-allowed`, `aria-disabled="true"`)
   - State is preserved when navigating back then forward
   - Proper ARIA attributes (`role="button"`, `aria-current="step"` for current)

3. **AC-3 (Population two-step IA):** Given the Population Information Architecture section starting at line 1605, when updated, then it reflects the two-step model:
   - Sub-step 1: "Source" — contains Population Library (default) and Build New (DataFusionWorkbench)
   - Sub-step 2: "Inspect" — contains PopulationExplorer, gated behind population selection
   - Nav rail shows exactly two sub-steps when Population is active
   - Inspect is disabled when no population is selected, with tooltip "Select or build a population first"
   - URL hash patterns: `#population`, `#population/source`, `#population/inspect`

4. **AC-4 (Nav rail activeFor update - Population):** Given the nav rail STAGES constant around line 2175-2200, when updated, then it documents the updated Population `activeFor` array:
   - Population: `activeFor: ["population", "source", "inspect", "data-fusion"]` (note: "source" and "inspect" added; "data-fusion" retained for Build New button legacy support)
   - Legacy hash patterns are documented as migrated on app load

5. **AC-5 (Nav rail activeFor update - Results):** Given the nav rail STAGES constant around line 2198-2201, when updated, then it documents the updated Results `activeFor` array to include sub-views added in Story 27.12:
   - Results: `activeFor: ["results", "runner", "comparison", "decisions", "manifest", "overview"]` (verify "overview" key against actual implementation in `frontend/src/components/layout/workspace.ts`)

6. **AC-6 (Stage 5 breadcrumb):** Given the Stage 5 section starting at line 1841, when updated, then it documents the breadcrumb header:
   - Persistent breadcrumb at top of Stage 5 surface: `Results > {sub-view name}`
   - Lightweight styling (`text-sm`, `text-slate-500`)
   - Shows for all sub-views: Overview, Runner, Comparison, Decisions, Manifest

7. **AC-7 (Stage 5 semantic palette):** Given the Stage 5 section, when updated, then it documents the semantic color tokens:
   - Baseline run: `--chart-baseline` (darker, visually distinct)
   - Reform runs: `--chart-reform-a` through `--chart-reform-d` (existing tokens)
   - Rainbow palette replaced with semantic baseline/reform distinction

8. **AC-8 (Stage 5 unit labels):** Given the Stage 5 Comparison section, when updated, then it documents:
   - Fiscal and Welfare tab column headers include unit labels (e.g., "Revenue (€)")
   - Large numeric values use `formatLargeNumber()` helper (e.g., `€1.2M` instead of `1234567`)

9. **AC-9 (Stage 5 run-id display):** Given the Stage 5 section, when updated, then it documents:
   - Run IDs display at least 12 characters in monospace font
   - Copy-to-clipboard button adjacent to run-id displays
   - Full ID available via tooltip and clipboard

10. **AC-10 (Stage 5 NaN/Infinity guards):** Given the Stage 5 section, when updated, then it documents that all numeric displays fall back to `"—"` for NaN or Infinity values (not rendered as raw `NaN` or `Infinity`).

11. **AC-11 (Stage 5 stale-comparison reset):** Given the Stage 5 Comparison section, when updated, then it documents that when `activeScenario.id` changes, `selectedRunIds` and `comparisonData` are reset (no stale comparison from previous scenario).

12. **AC-12 (Stage 5 failed-runs summary):** Given the Stage 5 Comparison section, when updated, then it documents that when some selected runs are in `failed` status, a summary line reads "{N} runs completed, {M} failed (excluded from comparison)".

13. **AC-13 (Stage 5 skeleton loading):** Given the Stage 5 Results Overview section, when updated, then it documents that the Detail tab renders a skeleton placeholder immediately (before the API call resolves, using a skeleton template).

14. **AC-14 (Stage 5 IA diagram update):** Given the Stage 5 IA diagram around line 1847-1874, when updated, then it reflects the actual sub-view structure implemented in Story 27.12:
   - Overview (formerly Results View)
   - Runner (formerly Run Queue)
   - Comparison
   - Decisions
   - Manifest (formerly Run Manifest Viewer)
   - Retain detail about what each sub-view contains

## Tasks / Subtasks

- [x] Task 1: Update nav rail four-state model documentation (AC: #1)
  - [x] Subtask 1.1: In `_bmad-output/planning-artifacts/ux-design-specification.md` at line 1365-1369, verify "Story 27.6: four-state model" comment is present and complete (verification step—content was added in Story 27.6)
  - [x] Subtask 1.2: Confirm visual treatments match implementation: Active (`bg-blue-500`), Complete (`bg-emerald-500` with check), Incomplete (`border-2 border-slate-300`), Not started (`border-dashed border-slate-200`) (verification step)
  - [x] Subtask 1.3: Add prose explaining when each state applies (current/touched/untouched, finished/unfinished)—this is the only new content to add

- [x] Task 2: Update Investment Decisions wizard documentation (AC: #2)
  - [x] Subtask 2.1: In Stage 3 section around line 2160-2168, add subsection "Clickable Step Labels"
  - [x] Subtask 2.2: Document that step labels are `<button>` elements with `onClick` handlers calling `goToStep()`
  - [x] Subtask 2.3: Document visual styling: visited steps (`text-emerald-600 cursor-pointer`), current step (`text-blue-600 font-medium`), unreached steps (`text-slate-400 cursor-not-allowed`)
  - [x] Subtask 2.4: Document disabled state for unreached steps with `aria-disabled="true"`
  - [x] Subtask 2.5: Document state preservation when navigating back then forward
  - [x] Subtask 2.6: Document ARIA attributes: `role="button"`, `aria-current="step"` for current step

- [x] Task 3: Update Population stage IA documentation (AC: #3, #4)
  - [x] Subtask 3.1: In Population Information Architecture section (line 1605-1700), replace the existing flat IA diagram with a reorganized two-step structure: place Library, Upload Flow, and Quick Preview under "Source"; place Full Data Explorer (the three tabs: Table, Profile, Summary) under "Inspect". Retain the Backend Support API table and Key Design Decisions sections below the IA.
  - [x] Subtask 3.2: Add prose explaining the two-step flow: "pick or build a population (Source), then inspect it (Inspect)"
  - [x] Subtask 3.3: Document that Inspect is disabled when no population is selected, with tooltip text
  - [x] Subtask 3.4: Document URL hash patterns: `#population` (Source), `#population/source`, `#population/inspect`
  - [x] Subtask 3.5: In nav rail STAGES constant (line 2183-2185), update Population `activeFor` to include `"source"` and `"inspect"`
  - [x] Subtask 3.6: Add note about legacy hash migration: `"" → "source"`, `"data-fusion" → "source"`, `"population-explorer" → "inspect"`
  - [x] Subtask 3.7: In nav rail STAGES constant (line 2198-2201), update Results `activeFor` to include `"manifest"` and verify `"overview"` key against `frontend/src/components/layout/workspace.ts`

- [x] Task 4: Update Stage 5 documentation (AC: #6-14)
  - [x] Subtask 4.0: Update the Stage 5 IA diagram (lines 1847-1874) to reflect actual sub-view structure: Overview (formerly Results View), Runner (formerly Run Queue), Comparison, Decisions, Manifest (formerly Run Manifest Viewer). Retain detail about what each sub-view contains.
  - [x] Subtask 4.1: In Stage 5 section (line 1841-1900), add "Breadcrumb Context" subsection with `Results > {sub-view}` pattern
  - [x] Subtask 4.2: Add "Semantic Comparison Palette" subsection documenting `--chart-baseline` vs `--chart-reform-a..d`
  - [x] Subtask 4.3: Add "Unit Labels" subsection documenting Fiscal/Welfare column headers with `formatLargeNumber()` usage
  - [x] Subtask 4.4: Add "Run Identifiers" subsection documenting 12-char minimum, monospace font, copy button
  - [x] Subtask 4.5: Add "Numeric Display Guards" subsection documenting NaN/Infinity fallback to `"—"`
  - [x] Subtask 4.6: Add "Stale Comparison Reset" subsection documenting scenario-change behavior
  - [x] Subtask 4.7: Add "Failed Runs Summary" subsection documenting "{N} completed, {M} failed" message
  - [x] Subtask 4.8: Add "Skeleton Loading" subsection documenting Detail-tab immediate skeleton render (before API call resolves)

- [x] Task 5: Verification (AC: all)
  - [x] Subtask 5.1: Verify each AC's content exists in the spec using search-based checks: AC-1 search for "Not started"; AC-2 search for "clickable" and "goToStep"; AC-3 search for "Source" and "Inspect" within Population IA; AC-4 search for "source" within Population activeFor; AC-5 search for "manifest" within Results activeFor; AC-6 search for "Results >" or "breadcrumb"; AC-7 search for "--chart-baseline"; AC-8 search for "(€)"; AC-9 search for "12 characters"; AC-10 search for '"—"' or fallback text; AC-11 search for "reset"; AC-12 search for "failed"; AC-13 search for "skeleton"; AC-14 verify Stage 5 IA shows Overview/Runner/Comparison/Decisions/Manifest
  - [x] Subtask 5.2: Cross-reference each AC with corresponding story file to verify accuracy: Story 27.6 (AC-1) read completion notes; Story 27.7 (AC-2) read InvestmentDecisionsWizard.tsx for visual styling; Story 27.8 (AC-3, AC-4) read workspace.ts for POPULATION_SUB_STEPS and STAGES.activeFor; Story 27.12 (AC-6 through AC-14) read each mentioned component to verify documented behaviors
  - [x] Subtask 5.3: No code changes required—this is documentation-only

## Dev Notes

### Context

Epic 27 implemented UX stabilization work across Stories 27.6, 27.7, 27.8, and 27.12. These stories are complete with passing tests. The UX specification needs updates to document the implemented interactions:

- **Story 27.6:** Already updated the spec for the four-state model (AC-7 in that story, visible at lines 1365-1369). Task 1 only needs to add prose explaining when each state applies—subtasks 1.1 and 1.2 are verification steps.
- **Story 27.7, 27.8, 27.12:** Have no spec updates yet—those sections need to be written from scratch based on the implementation.

**Important:** This story is documentation-only. All acceptance criteria refer to updating the UX specification markdown file, not changing implementation code.

### Files to Modify

**Single file:**
- `_bmad-output/planning-artifacts/ux-design-specification.md`

**Sections to update:**
1. Line ~1365-1369: "Stage indicator states" (Story 27.6)
2. Line ~1605-1700: Population Information Architecture (Story 27.8)
3. Line ~1841-1900: Stage 5 — Run / Results / Compare (Story 27.12)
4. Line ~2160-2168: Investment Decisions wizard (Story 27.7)
5. Line ~2175-2200: Nav rail STAGES constant `activeFor` arrays (Story 27.8)

**Important:** Line numbers in this story are approximations. The Population IA rewrite in Task 3 (~90 lines) will shift all downstream line references (Stage 5, Investment Decisions, STAGES constant) by a variable amount. Always locate sections using markdown section headers, not line numbers. After completing Task 3, use section headers to find remaining sections.

### Documentation Update Strategy

When updating the UX specification:

- **For prose descriptions:** Edit in-place to update or add content within existing paragraphs
- **For code examples or diagrams:** Replace the entire block with the updated version (don't patch)
- **For lists or constants:** Replace with the complete new version

**Specific guidance:**
- Population IA (Task 3.1): Replace the entire flat IA diagram with the reorganized two-step structure. Keep the Backend Support API table and Key Design Decisions sections—those don't change.
- STAGES constant (Task 3.5, 3.7): Replace the entire `activeFor` array with the new version
- Stage 5 IA (Task 4.0): Replace the entire IA diagram with the updated sub-view structure

### Implementation Source References

- **Story 27.6:** `_bmad-output/implementation-artifacts/27-6-add-not-started-nav-rail-state-and-stop-demo-presatisfying-stages.md`
- **Story 27.7:** `_bmad-output/implementation-artifacts/27-7-make-investment-decisions-wizard-step-labels-clickable.md`
- **Story 27.8:** `_bmad-output/implementation-artifacts/27-8-restructure-population-stage-as-library-or-build-then-explorer.md`
- **Story 27.12:** `_bmad-output/implementation-artifacts/27-12-stage-5-polish-breadcrumb-palette-units-runid-nan-stale-reset.md`

### Project Structure Notes

- No code changes required
- No test changes required
- This is pure documentation amendment

### References

- [Source: _bmad-output/planning-artifacts/ux-design-specification.md]
- [Source: _bmad-output/implementation-artifacts/27-6-add-not-started-nav-rail-state-and-stop-demo-presatisfying-stages.md]
- [Source: _bmad-output/implementation-artifacts/27-7-make-investment-decisions-wizard-step-labels-clickable.md]
- [Source: _bmad-output/implementation-artifacts/27-8-restructure-population-stage-as-library-or-build-then-explorer.md]
- [Source: _bmad-output/implementation-artifacts/27-12-stage-5-polish-breadcrumb-palette-units-runid-nan-stale-reset.md]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via dev-story workflow)

### Debug Log References

None — documentation-only story.

### Completion Notes List

- **AC-1 (Nav rail four-state model):** ✅ Added prose explaining when each state applies (Active/Complete/Incomplete/Not started) to the existing visual treatment documentation at lines 1365-1369.
- **AC-2 (Investment Decisions clickable wizard):** ✅ Added "Clickable Step Labels" subsection to Stage 3 (Investment Decisions) documenting button elements, visual styling, disabled state, state preservation, and ARIA attributes.
- **AC-3 (Population two-step IA):** ✅ Replaced flat Population IA diagram with two-step Source → Inspect structure. Source contains Library, Upload Flow, Quick Preview. Inspect contains Full Data Explorer (Table/Profile/Summary tabs).
- **AC-4 (Nav rail activeFor - Population):** ✅ Updated both STAGES constant occurrences in the spec. Population `activeFor` now includes "source" and "inspect". Retained "data-fusion" and "population-explorer" for legacy support.
- **AC-5 (Nav rail activeFor - Results):** ✅ Verified Results `activeFor` includes "runner", "comparison", "decisions". Note: "overview" is not a sub-view key (it's the default view with activeSubView === null). "manifest" is a tab within Detail, not a sub-view.
- **AC-6 (Stage 5 breadcrumb):** ✅ Added "Sub-View Breadcrumb" subsection documenting `Results > {sub-view name}` pattern with lightweight styling.
- **AC-7 (Stage 5 semantic palette):** ✅ Added "Semantic Comparison Palette" subsection documenting `--chart-baseline` for baseline and `--chart-reform-a..d` for reform runs.
- **AC-8 (Stage 5 unit labels):** ✅ Added "Unit Labels and Number Formatting" subsection documenting Fiscal/Welfare column headers with `formatLargeNumber()` usage.
- **AC-9 (Stage 5 run-id display):** ✅ Added "Run Identifiers" subsection documenting 12-char minimum, monospace font, copy button.
- **AC-10 (Stage 5 NaN/Infinity guards):** ✅ Added "Numeric Display Guards" subsection documenting em dash fallback for NaN/Infinity values.
- **AC-11 (Stage 5 stale-comparison reset):** ✅ Added "Stale Comparison Reset" subsection documenting activeScenario.id change behavior.
- **AC-12 (Stage 5 failed-runs summary):** ✅ Added "Failed Runs Summary" subsection documenting "{N} completed, {M} failed" message pattern.
- **AC-13 (Stage 5 skeleton loading):** ✅ Added "Skeleton Loading" subsection documenting Detail-tab immediate skeleton render.
- **AC-14 (Stage 5 IA diagram update):** ✅ Updated Stage 5 IA diagram to reflect actual sub-view structure: Overview (default), Runner, Comparison, Decisions, Manifest.

All updates were made to `_bmad-output/planning-artifacts/ux-design-specification.md` only. No code changes required.

### File List

- `_bmad-output/planning-artifacts/ux-design-specification.md` — Updated with Epic 27 UX amendments: four-state model prose, clickable wizard labels, Population two-step IA, Stage 5 polish documentation
