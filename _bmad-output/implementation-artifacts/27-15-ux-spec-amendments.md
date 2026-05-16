# Story 27.15: UX-spec amendments

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a product team maintaining design documentation,
I want the UX specification to reflect the interaction changes implemented in Epic 27,
so that the written source of truth matches the implemented product and future developers understand the intended behavior.

## Background

Epic 27 implemented several UX refinements that were not yet reflected in the UX specification document (`_bmad-output/planning-artifacts/ux-design-specification.md`). This story updates the spec to document:

1. **Story 27.6:** Four-state nav rail model (Active, Complete, Incomplete, Not started)
2. **Story 27.7:** Clickable Investment Decisions wizard step labels
3. **Story 27.8:** Population stage restructure from three peer tabs to two-step flow (Source → Inspect)
4. **Story 27.12:** Stage 5 polish (breadcrumb context, semantic palette, unit labels, run-id width, NaN guards, stale reset)

These changes are already implemented and tested. This story is documentation-only—no code changes.

## Acceptance Criteria

1. **AC-1 (Nav rail four-state model):** Given the UX spec section "Application Shell & Navigation" around line 1365, when updated, then it documents the four-stage indicator states (Active, Complete, Incomplete, Not started) with the exact visual treatments:
   - Active: `bg-blue-500 text-white`
   - Complete: `bg-emerald-500 text-white` with check icon
   - Incomplete: `border-2 border-slate-300 bg-white text-slate-500` (stage has been touched but not finished)
   - Not started: `border border-dashed border-slate-200 bg-transparent text-slate-400` with smaller dot (stage has not been touched)

2. **AC-2 (Investment Decisions clickable wizard):** Given the Stage 3 section around line 2160-2168, when updated, then it documents that wizard step labels (Enable, Model, Parameters, Review) are clickable for backward navigation, with:
   - Visited and current steps are clickable
   - Unreached steps are visibly disabled (`aria-disabled="true"`)
   - State is preserved when navigating back then forward
   - Proper ARIA attributes (`role="button"`, `aria-current="step"` for current)

3. **AC-3 (Population two-step IA):** Given the Population Information Architecture section starting at line 1605, when updated, then it reflects the two-step model:
   - Sub-step 1: "Source" — contains Population Library (default) and Build New (DataFusionWorkbench)
   - Sub-step 2: "Inspect" — contains PopulationExplorer, gated behind population selection
   - Nav rail shows exactly two sub-steps when Population is active
   - Inspect is disabled when no population is selected, with tooltip "Select or build a population first"
   - URL hash patterns: `#population`, `#population/source`, `#population/inspect`

4. **AC-4 (Nav rail activeFor update):** Given the nav rail STAGES constant around line 2175-2200, when updated, then it documents the updated `activeFor` arrays:
   - Population: `activeFor: ["population", "source", "inspect", "data-fusion"]` (note: "source" and "inspect" added; "data-fusion" retained for Build New button legacy support)
   - Legacy hash patterns are documented as migrated on app load

5. **AC-5 (Stage 5 breadcrumb):** Given the Stage 5 section starting at line 1841, when updated, then it documents the breadcrumb header:
   - Persistent breadcrumb at top of Stage 5 surface: `Results > {sub-view name}`
   - Lightweight styling (`text-sm`, `text-slate-500`)
   - Shows for all sub-views: Overview, Runner, Comparison, Decisions, Manifest

6. **AC-6 (Stage 5 semantic palette):** Given the Stage 5 section, when updated, then it documents the semantic color tokens:
   - Baseline run: `--chart-baseline` (darker, visually distinct)
   - Reform runs: `--chart-reform-a` through `--chart-reform-d` (existing tokens)
   - Rainbow palette replaced with semantic baseline/reform distinction

7. **AC-7 (Stage 5 unit labels):** Given the Stage 5 Comparison section, when updated, then it documents:
   - Fiscal and Welfare tab column headers include unit labels (e.g., "Revenue (€)")
   - Large numeric values use `formatLargeNumber()` helper (e.g., `€1.2M` instead of `1234567`)

8. **AC-8 (Stage 5 run-id display):** Given the Stage 5 section, when updated, then it documents:
   - Run IDs display at least 12 characters in monospace font
   - Copy-to-clipboard button adjacent to run-id displays
   - Full ID available via tooltip and clipboard

9. **AC-9 (Stage 5 NaN/Infinity guards):** Given the Stage 5 section, when updated, then it documents that all numeric displays fall back to `"—"` for NaN or Infinity values (not rendered as raw `NaN` or `Infinity`).

10. **AC-10 (Stage 5 stale-comparison reset):** Given the Stage 5 Comparison section, when updated, then it documents that when `activeScenario.id` changes, `selectedRunIds` and `comparisonData` are reset (no stale comparison from previous scenario).

11. **AC-11 (Stage 5 failed-runs summary):** Given the Stage 5 Comparison section, when updated, then it documents that when some selected runs are in `failed` status, a summary line reads "{N} runs completed, {M} failed (excluded from comparison)".

12. **AC-12 (Stage 5 skeleton loading):** Given the Stage 5 Results Overview section, when updated, then it documents that the Detail tab renders a skeleton placeholder immediately (within ~16ms) before API call resolves.

## Tasks / Subtasks

- [ ] Task 1: Update nav rail four-state model documentation (AC: #1)
  - [ ] Subtask 1.1: In `_bmad-output/planning-artifacts/ux-design-specification.md` at line 1365-1369, verify "Story 27.6: four-state model" comment is present and complete
  - [ ] Subtask 1.2: Ensure all four states are documented with exact visual treatments
  - [ ] Subtask 1.3: Add prose explaining when each state applies (touched vs untouched, complete vs incomplete)

- [ ] Task 2: Update Investment Decisions wizard documentation (AC: #2)
  - [ ] Subtask 2.1: In Stage 3 section around line 2160-2168, add subsection "Clickable Step Labels"
  - [ ] Subtask 2.2: Document that step labels are `<button>` elements with `onClick` handlers calling `goToStep()`
  - [ ] Subtask 2.3: Document disabled state for unreached steps with `aria-disabled="true"`
  - [ ] Subtask 2.4: Document state preservation when navigating back then forward
  - [ ] Subtask 2.5: Document ARIA attributes: `role="button"`, `aria-current="step"` for current step

- [ ] Task 3: Update Population stage IA documentation (AC: #3, #4)
  - [ ] Subtask 3.1: In Population Information Architecture section (line 1605-1700), update the IA diagram to show two-step structure
  - [ ] Subtask 3.2: Add prose explaining the two-step flow: "pick or build a population (Source), then inspect it (Inspect)"
  - [ ] Subtask 3.3: Document that Inspect is disabled when no population is selected, with tooltip text
  - [ ] Subtask 3.4: Document URL hash patterns: `#population` (Source), `#population/source`, `#population/inspect`
  - [ ] Subtask 3.5: In nav rail STAGES constant (line 2183-2185), update `activeFor` to include `"source"` and `"inspect"`
  - [ ] Subtask 3.6: Add note about legacy hash migration: `"" → "source"`, `"data-fusion" → "source"`, `"population-explorer" → "inspect"`

- [ ] Task 4: Update Stage 5 documentation (AC: #5-12)
  - [ ] Subtask 4.1: In Stage 5 section (line 1841-1900), add "Breadcrumb Context" subsection with `Results > {sub-view}` pattern
  - [ ] Subtask 4.2: Add "Semantic Comparison Palette" subsection documenting `--chart-baseline` vs `--chart-reform-a..d`
  - [ ] Subtask 4.3: Add "Unit Labels" subsection documenting Fiscal/Welfare column headers with `formatLargeNumber()` usage
  - [ ] Subtask 4.4: Add "Run Identifiers" subsection documenting 12-char minimum, monospace font, copy button
  - [ ] Subtask 4.5: Add "Numeric Display Guards" subsection documenting NaN/Infinity fallback to `"—"`
  - [ ] Subtask 4.6: Add "Stale Comparison Reset" subsection documenting scenario-change behavior
  - [ ] Subtask 4.7: Add "Failed Runs Summary" subsection documenting "{N} completed, {M} failed" message
  - [ ] Subtask 4.8: Add "Skeleton Loading" subsection documenting Detail-tab immediate skeleton render

- [ ] Task 5: Verification (AC: all)
  - [ ] Subtask 5.1: Read through updated UX spec sections to confirm clarity and completeness
  - [ ] Subtask 5.2: Cross-reference each AC with corresponding story file (27.6, 27.7, 27.8, 27.12) to verify accuracy
  - [ ] Subtask 5.3: No code changes required—this is documentation-only

## Dev Notes

### Context

Epic 27 implemented UX stabilization work across Stories 27.6, 27.7, 27.8, and 27.12. These stories are complete with passing tests, but the UX specification document was not updated to reflect the changes. This story corrects that documentation gap.

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

Claude Opus 4.6 (via create-story workflow)

### Debug Log References

None — documentation-only story.

### Completion Notes List

<!-- Populated after implementation is complete -->

### File List

<!-- Populated after implementation is complete -->
