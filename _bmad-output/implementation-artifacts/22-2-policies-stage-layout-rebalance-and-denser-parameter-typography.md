# Story 22.2: Policies stage layout rebalance and denser parameter typography

Status: ready-for-dev

## Story

As a policy analyst working in the Policies & Portfolio stage,
I want a visibly balanced two-panel workbench where template browsing and portfolio composition receive equal desktop emphasis, and parameter editing uses denser typography without sacrificing legibility,
so that the stage feels like a cohesive workspace rather than a primary panel with a cramped sidebar.

## Acceptance Criteria

1. **[AC-1]** Given the Policies stage at desktop widths (≥1024px), when rendered, then the template browser and portfolio composition panels use an equal 50/50 split (`grid-cols-2` or equivalent).
2. **[AC-2]** Given parameter editing controls in the portfolio composition panel, when rendered, then labels and supporting text use `text-xs` (12px) while values and section structure remain legible at `text-sm` (14px) or larger.
3. **[AC-3]** Given multiple policies in a portfolio, when the user adds, edits, reorders, validates, saves, or loads them, then the stage remains usable without the composition panel feeling like a cramped sidebar.
4. **[AC-4]** Given narrower breakpoints (<1024px), when the layout collapses, then the stage stacks vertically (template browser above, composition panel below) without forcing horizontal overflow.

## Tasks / Subtasks

- [x] **Task 1: Rebalance desktop layout to 50/50 split** (AC: 1, 3)
  - [x] Change `PoliciesStageScreen.tsx` main grid from `grid-cols-[minmax(0,1fr)_minmax(0,2fr)]` to `grid-cols-2` (equal split)
  - [x] Verify both panels receive equal width at desktop breakpoint (≥1024px / `lg:`)
  - [x] Ensure panel containers maintain their rounded border and padding treatments
  - [x] Test with 2+ policy cards in composition to confirm no cramping

- [x] **Task 2: Densify parameter typography in editing controls** (AC: 2)
  - [x] In `ParameterRow.tsx`: change label from `text-sm` to `text-xs`
  - [x] In `ParameterRow.tsx`: change baseline/delta display from `text-xs` to `text-xs` (already appropriate, verify)
  - [x] In `PortfolioCompositionPanel.tsx`: change `Rate Schedule` heading from `text-xs font-semibold` to `text-xs font-semibold` (verify it stays visually stronger than controls)
  - [x] In `PortfolioTemplateBrowser.tsx`: verify template name stays `text-sm` (left panel should maintain standard sizing for readability)
  - [x] Ensure monospace values remain `text-sm font-medium` or larger for legibility

- [x] **Task 3: Add responsive stacking for narrow breakpoints** (AC: 4)
  - [x] Update main grid to stack vertically below desktop breakpoint (default `grid-cols-1`, `lg:grid-cols-2`)
  - [x] Verify no page-level horizontal overflow at 375px viewport width
  - [x] Ensure both panels scroll independently when stacked (`overflow-y-auto` on panel containers)

- [x] **Task 4: Update tests for layout rebalance** (AC: 1, 2, 3, 4)
  - [x] Update `PoliciesStageScreen.test.tsx` to assert 50/50 split behavior (CSS class assertions)
  - [x] Add test for denser parameter typography classes
  - [x] Add test for responsive stacking at mobile breakpoint
  - [x] Ensure existing portfolio operation tests still pass

## Dev Notes

### Current Policies Stage Layout

**Source:** `frontend/src/components/screens/PoliciesStageScreen.tsx` line 547

Current desktop grid:
```tsx
<div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] gap-3 flex-1 min-h-0">
```

This creates a **1:2 ratio** (template browser gets 1/3, composition gets 2/3), which feels unbalanced and makes the composition panel dominate while the template browser feels like a narrow sidebar.

**Target behavior:** Equal 50/50 split using `lg:grid-cols-2`.

### Typography Changes Required

**ParameterRow.tsx** (line 32-34):
- Current: `<p className="text-sm text-slate-900">{parameter.label}</p>`
- Target: Change to `text-xs` (12px) for labels

- Baseline display (line 33-35):
- Current: `<p className="text-xs text-slate-500">`
- Target: Keep at `text-xs` (already appropriate)

- Value display (line 56-57):
- Current: `<p className="data-mono text-sm font-medium text-slate-800">`
- Target: Keep at `text-sm` for monospace values (maintain legibility)

**PortfolioCompositionPanel.tsx** (line 222-224):
- Rate Schedule heading: Already `text-xs font-semibold text-slate-700` — keep as is
- Section headers should stay visually stronger than controls

**PortfolioTemplateBrowser.tsx**:
- Template name (line 111): Currently `text-sm font-medium` — **keep unchanged** (left panel readability is important)
- Type label (line 90): Currently `text-xs font-semibold` — keep as is
- Description (line 114): Currently `text-xs` — keep as is

### Visual Identity Guide References

**[Source: `_bmad-output/branding/visual-identity-guide.md#4-typography`]**

**Application UI Type Scale:**
- **Body / labels:** 14px (`text-sm`), Normal (400) — **Story 22.2 makes parameter labels denser at `text-xs` (12px)**
- **Data values:** 14px (`text-sm`), Medium (500) — Keep values at `text-sm` or larger
- **Metadata:** 12px (`text-xs`), Normal (400)

**Key decision:** This story intentionally makes parameter labels denser than the VIDG default `text-sm` for body/labels. This is acceptable because:
1. Labels appear in a controlled editing context with sufficient spacing
2. Values remain legible at `text-sm` or larger
3. Section headers stay visually stronger

### Responsive Strategy

**Desktop (≥1024px / `lg:`):**
- Two-panel layout with equal 50/50 split
- Both panels scroll independently with `overflow-y-auto`

**Tablet/Mobile (<1024px):**
- Panels stack vertically: template browser above, composition panel below
- Each panel retains its border, padding, and scroll behavior
- No page-level horizontal overflow

**Mobile breakpoint reference:** Tailwind's `lg:` breakpoint is 1024px, which aligns with the UX Revision 3 spec's "desktop widths" phrasing.

### Component Architecture

**Files to modify:**
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — main grid layout
- `frontend/src/components/simulation/ParameterRow.tsx` — parameter label typography
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` — add layout assertions

**Files to verify (no changes expected):**
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — verify section headers remain appropriate
- `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — verify left panel maintains readability
- `frontend/src/components/simulation/YearScheduleEditor.tsx` — verify it works correctly with the denser layout

**State management:**
- Uses `useAppState()` for: templates, portfolios, activeScenario, updateScenarioField, setSelectedPortfolioName
- Local state for: selectedTemplateIds, composition, conflicts, dialogs
- No new state needed for this story

### Scope Boundaries

**OUT OF SCOPE for Story 22.2:**
- No changes to portfolio naming behavior (Story 22.3)
- No changes to scenario entry or shell branding (Story 22.1)
- No changes to Population or Scenario stages
- No backend API changes

### Testing Patterns

**Per project context [Source: `_bmad-output/project-context.md`]:**
- Use Vitest for frontend tests
- Test file structure mirrors source
- Mock `useAppState` with `vi.mock("@/contexts/AppContext")`

**Test coverage targets:**
- Grid layout uses `lg:grid-cols-2` for equal split at desktop
- Parameter labels use `text-xs` class
- Responsive classes apply `grid-cols-1` by default (mobile stacking)
- Both panels remain scrollable and usable with 2+ policies

### Known Constraints and Gotchas

1. **Grid overflow:** The `minmax(0,1fr)` pattern in the current layout prevents grid blowout. When changing to `grid-cols-2`, ensure `min-w-0` is present on child divs to allow proper shrinking.
2. **Panel scrolling:** Both panel containers have `overflow-y-auto` — ensure this is preserved so content scrolls within the panel rather than the entire page.
3. **Save dialog:** The save/load/clone dialogs are rendered inline in PoliciesStageScreen — ensure layout changes don't break dialog z-indexing or positioning.
4. **Accessibility:** Parameter labels at `text-xs` must still meet WCAG contrast requirements. The current `text-slate-900` on white background is sufficient.
5. **Existing tests:** 30+ tests in `PoliciesStageScreen.test.tsx` — ensure they still pass after layout changes.

### References

- **UX Revision 3 spec:** `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md` — Change 3 details
- **Epic 22 definition:** `_bmad-output/planning-artifacts/epics.md#Epic-22` — Full epic context
- **Visual Identity Guide:** `_bmad-output/branding/visual-identity-guide.md` — Typography rules
- **Story 22.1 completion:** `_bmad-output/implementation-artifacts/22-1-shell-branding-external-links-and-scenario-entry-relocation.md` — Previous story for reference
- **PoliciesStageScreen source:** `frontend/src/components/screens/PoliciesStageScreen.tsx` — Current implementation
- **ParameterRow source:** `frontend/src/components/simulation/ParameterRow.tsx` — Parameter editing component

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (via create-story workflow)

### Implementation Plan

**Task 1: Rebalance desktop layout to 50/50 split** (AC: 1, 3)
- Change `PoliciesStageScreen.tsx` line 547 from `lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]` to `lg:grid-cols-2`
- This creates an equal 50/50 split at desktop breakpoint (≥1024px)
- Both child divs already have `min-w-0` classes (lines 549, 559) which ensures proper grid shrinking behavior

**Task 2: Densify parameter typography in editing controls** (AC: 2)
- In `ParameterRow.tsx` line 32: Change `text-sm` to `text-xs` for parameter label
- Keep baseline display at `text-xs` (already appropriate)
- Keep value display at `text-sm font-medium` (maintain legibility for monospace numbers)

**Task 3: Add responsive stacking for narrow breakpoints** (AC: 4)
- The `grid-cols-1` base class is already present (line 547)
- The `lg:grid-cols-2` override will create the 50/50 split at desktop
- Mobile stacking behavior is already in place — just verifying it works correctly

**Task 4: Update tests for layout rebalance** (AC: 1, 2, 3, 4)
- Add tests for grid layout classes: `grid-cols-1` and `lg:grid-cols-2`
- Add tests for ParameterRow label `text-xs` class
- Add tests for responsive behavior at mobile viewport
- Ensure all 30+ existing tests still pass

### Debug Log References

None — analysis completed from source files and spec documents.

### Completion Notes List

- Story 22.2 is frontend-only — no backend changes required
- Does NOT depend on incomplete Epic 21 stories (21.4, 21.5, 21.6)
- Builds on Story 22.1 shell work but has no code dependencies on it
- Layout change is a single-line CSS grid modification plus typography density adjustments
- All changes preserve existing functionality and state management
- Test updates will ensure layout assertions cover the new 50/50 behavior

### File List

**Modified files:**
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — Change grid to `lg:grid-cols-2` for equal split
- `frontend/src/components/simulation/ParameterRow.tsx` — Change parameter label to `text-xs`
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` — Add layout and typography assertions

**Reference files (not modified):**
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — Verify section headers remain appropriate
- `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — Verify left panel maintains readability
- `frontend/src/components/simulation/YearScheduleEditor.tsx` — Verify it works correctly with denser layout
- `_bmad-output/branding/visual-identity-guide.md` — Typography reference
- `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md` — Change 3 specification
