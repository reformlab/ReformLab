# Story 25.2: Redesign Policies stage browser/composition layout with types, categories, and duplicate policy instances

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want **to work in the redesigned Policies stage with a 50/50 desktop layout, type/category badges, and the ability to add the same policy template multiple times**,
so that **I can build policy sets with multiple variants of the same policy (e.g., carbon tax at different rates) while seeing clear visual indicators of policy types and categories**.

## Acceptance Criteria

1. **Given** the Policies stage on desktop, **when** rendered, **then** the policy browser and composition panel occupy a balanced 50/50 workbench layout using `grid-cols-2`.
2. **Given** the Policies stage on phone width, **when** rendered, **then** browser and composition panels stack vertically without horizontal overflow (single column on mobile).
3. **Given** a policy card in the template browser, **when** displayed, **then** it shows type badge (Tax/Subsidy/Transfer with correct color), category badge (neutral slate color), formula-help affordance (CircleHelp icon), and live-availability status when available.
4. **Given** a policy card in the composition panel, **when** displayed, **then** it shows type badge, category badge, and formula-help affordance (matching the browser card).
5. **Given** the same template is added twice, **when** the analyst edits one instance, **then** the other instance keeps its own parameters unchanged (each instance is independently editable).
6. **Given** a template card is clicked, **when** the template is already in the composition, **then** a new instance is added (the template can be added multiple times with unique IDs).
7. **Given** the Policies stage renders, **when** visible copy is inspected, **then** the stage says "Policies" and "Policy Set" rather than "Portfolio" in all user-facing text (headers, dialogs, button labels).
8. **Given** a composite template like feebate is added, **when** it enters the composition panel, **then** it creates separate Tax and Subsidy policies that can be edited independently (this is deferred to Story 25.3 — in this story, feebate templates add as a single policy entry per existing behavior).

## Tasks / Subtasks

- [ ] **Verify 50/50 layout implementation** (AC: 1, 2)
  - [ ] Confirm `PoliciesStageScreen` uses `grid-cols-1 lg:grid-cols-2` for 50/50 split
  - [ ] Test desktop breakpoint at 1024px (`lg:` breakpoint)
  - [ ] Test mobile stacking without horizontal overflow
  - [ ] Verify both panels have equal height allocation with `min-h-0` for scroll

- [ ] **Add category badges to composition panel** (AC: 4)
  - [ ] Add `category_id` to `CompositionEntry` interface or pass category lookup map
  - [ ] Update `PortfolioCompositionPanel` to accept `categories` prop
  - [ ] Render category badge next to type badge in policy card header
  - [ ] Add CircleHelp icon with formula-help popover in composition cards (reuse from browser)
  - [ ] Style category badge with neutral slate color (`bg-slate-100 text-slate-800`)

- [ ] **Implement duplicate policy instances** (AC: 5, 6)
  - [ ] Remove the `selectedTemplateIds` Set-based selection pattern (toggles prevent duplicates)
  - [ ] Change template browser from "toggle selection" to "add instance" action
  - [ ] Add unique instance ID to each composition entry (e.g., `${templateId}-${instanceId}`)
  - [ ] Update `key` prop in composition panel to use unique instance ID
  - [ ] Update `handleRemove` to remove by index (already implemented, no change needed)
  - [ ] Update template browser card to show "Add" action rather than checkbox selection state
  - [ ] Remove `aria-pressed` and selected state styling from template browser cards

- [ ] **Update Policies stage terminology** (AC: 7)
  - [ ] Rename "Portfolio" to "Policies" in stage headers and visible copy
  - [ ] Update dialog titles: "Save Portfolio" → "Save Policy Set", "Load Portfolio" → "Load Policy Set"
  - [ ] Update button labels and tooltips to use "policy" and "policy set"
  - [ ] Update internal comments to reference "policy set" concept
  - [ ] Keep backend API routes as `/api/portfolios` (no backend changes in this story)

- [ ] **Add category badge to template browser** (verify Story 25.1) (AC: 3)
  - [ ] Verify category badge displays with neutral slate color
  - [ ] Verify CircleHelp icon appears next to category badge
  - [ ] Verify popover shows formula_explanation and description
  - [ ] Verify category badge is hidden when template has no category

- [ ] **Testing** (AC: 1, 2, 3, 4, 5, 6, 7, 8)
  - [ ] Layout tests: verify 50/50 grid on desktop, single column on mobile
  - [ ] Duplicate instance tests: add same template twice, verify independent editing
  - [ ] Category badge tests in composition panel
  - [ ] Terminology tests: verify "Policies" and "Policy Set" in visible copy
  - [ ] Regression tests: verify existing template add/edit/remove still works
  - [ ] Responsive tests: verify no horizontal overflow on mobile widths

## Dev Notes

### Architecture Patterns and Constraints

**Frontend - Component Layer:**
- Location: `frontend/src/components/`
- **Layout pattern**: Use `grid-cols-1 lg:grid-cols-2` for 50/50 desktop, stacked mobile
- **Responsive breakpoint**: Tailwind `lg:` at 1024px
- **Scroll handling**: `min-h-0` on grid children enables proper scrolling within flex/grid containers
- **Shadcn UI components available**: Badge, Button, Card, Popover, ScrollArea, Select, etc.
- **Icons from lucide-react**: `CircleHelp` for formula help affordance

**Testing - Frontend:**
- Location: `frontend/src/components/**/__tests__/`
- Use Vitest + Testing Library
- Test responsive behavior with `@testing-library/react` render
- Mock API calls with `vi.mock()` where needed
- Test layout with viewport size changes if needed

### Key Design Decisions

**Duplicate Policy Instances:**
- The current implementation uses a `selectedTemplateIds: string[]` array with Set-like behavior (toggles prevent duplicates)
- To support duplicates, change from "selection toggle" to "add instance" action
- Each composition entry gets a unique instance ID: `${templateId}-${Date.now()}` or a counter
- Template browser cards no longer show selected state (remove `aria-pressed`, checkbox, selected styling)
- Instead, each card has an "Add" button/action that adds a new instance

**Category Badges in Composition Panel:**
- `PortfolioCompositionPanel` currently shows type badges but not category badges
- Add `categories?: Category[]` prop to `PortfolioCompositionPanel`
- Look up category by `template.category_id` and display badge next to type badge
- Reuse the same Popover component from `PortfolioTemplateBrowser` for formula help

**Terminology Updates:**
- Stage name remains "Policies" (already correct in `PoliciesStageScreen`)
- Dialog titles: "Save Portfolio" → "Save Policy Set"
- Button labels: "Save portfolio" → "Save policy set"
- Internal state can keep `portfolioName` for backend compatibility (no backend changes in this story)

**Layout Verification:**
- The 50/50 layout is already implemented in `PoliciesStageScreen` (lines 330-345)
- Verify: `<div className="grid grid-cols-1 lg:grid-cols-2 gap-3 flex-1 min-h-0">`
- Each panel has `overflow-y-auto min-w-0` for proper scrolling

### Source Tree Components to Touch

**Frontend files to modify:**
1. `frontend/src/components/screens/PoliciesStageScreen.tsx` — terminology updates, duplicate instance logic
2. `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — remove selection state, change to "add" action
3. `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — add category badges, formula help popover
4. `frontend/src/components/simulation/PortfolioCompositionPanel.test.tsx` — add tests for category badges
5. `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` — add tests for duplicate instances

**Files to verify (no changes expected if already correct):**
1. `frontend/src/components/ui/popover.tsx` — already installed full Radix Popover in Story 25.1
2. `frontend/src/api/categories.ts` — already implemented in Story 25.1
3. `frontend/src/api/types.ts` — Category type already defined

### Integration with Story 25.1

Story 25.1 added:
- `GET /api/categories` endpoint
- `Category` type in `types.ts`
- Category badges and formula help popovers in template browser
- Category grouping and filter chips

Story 25.2 builds on this by:
- Adding category badges to composition panel cards (not just browser)
- Changing browser from selection-toggle to add-instance action
- Terminology updates from "Portfolio" to "Policy Set"

### Duplicate Instance Implementation Strategy

**Current state (Story 25.1):**
```typescript
const [selectedTemplateIds, setSelectedTemplateIds] = useState<string[]>([]);

const toggleTemplate = useCallback((id: string) => {
  setSelectedTemplateIds((prev) =>
    prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
  );
}, []);
```

**New state (Story 25.2):**
```typescript
// Remove selectedTemplateIds state entirely
// Template browser calls onAddTemplate(templateId) directly
// Composition manages unique instance IDs internally

const addTemplateInstance = useCallback((templateId: string) => {
  const t = templates.find((tmpl) => tmpl.id === templateId);
  if (!t) return;

  const newInstance: CompositionEntry = {
    instanceId: `${templateId}-${Date.now()}`, // Unique ID
    templateId,
    name: t?.name ?? templateId,
    parameters: {},
    rateSchedule: {},
  };

  setComposition((prev) => [...prev, newInstance]);
}, [templates]);
```

**Template browser change:**
```typescript
// Remove aria-pressed, selected state, checkbox
// Add "Add" button or make entire card an "add" action
<button onClick={() => onAddTemplate(template.id)}>
  Add to policies
</button>
```

**Composition panel change:**
```typescript
// Use instanceId as key instead of index
{composition.map((entry, index) => (
  <div key={entry.instanceId || `${entry.templateId}-${index}`}>
```

### Out of Scope

The following are explicitly out of scope for Story 25.2:
- **Composite template expansion** (e.g., feebate → Tax + Subsidy) — deferred to Story 25.3
- **Backend changes** — all terminology changes are frontend-only; `/api/portfolios` endpoints unchanged
- **Policy set persistence independence** — deferred to Story 25.5
- **Editable parameter groups** — deferred to Story 25.4
- **From-scratch policy creation** — deferred to Story 25.3

### Testing Standards Summary

**Frontend:**
```bash
npm test -- PoliciesStageScreen
npm test -- PortfolioTemplateBrowser
npm test -- PortfolioCompositionPanel
```

**Test structure:**
- Use Vitest + Testing Library
- Mock templates and categories
- Test layout with different viewport sizes if needed
- Test duplicate instance behavior (add twice, edit independently)

**Quality gates:**
```bash
npm run typecheck
npm run lint
npm test
```

### Known Issues / Gotchas

1. **Unique instance IDs**: Use `Date.now()` or a counter to ensure uniqueness. Do not use array index as the sole identifier (reordering breaks identity).

2. **CompositionEntry interface**: Currently has `templateId`, `name`, `parameters`, `rateSchedule`. Add `instanceId?: string` for uniqueness.

3. **Template browser selected state**: The current implementation shows selected state with `aria-pressed` and a checkbox. Remove these for duplicate support. The browser becomes a catalog, not a selection list.

4. **Category badge in composition panel**: The composition panel currently only shows type badges. Add category badge lookup and rendering similar to the browser.

5. **Popover reusability**: The Popover component from Story 25.1 can be imported and reused in `PortfolioCompositionPanel`. No new installation needed.

6. **Terminology scope**: Only update user-facing copy. Keep internal state names (`portfolioName`, `portfolios`) for backend compatibility. Story 25.5 will handle backend renaming.

7. **50/50 layout**: Already implemented in `PoliciesStageScreen`. This story requires verification, not new implementation. Test at desktop width (≥1024px) and mobile width (<1024px).

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Completion Notes List

- Story created with comprehensive developer context
- All acceptance criteria mapped to implementation tasks
- Integration points with Story 25.1 identified
- Duplicate instance implementation strategy documented
- Out of scope items clearly listed to prevent scope creep
- Testing patterns and quality gates specified

### File List

**Frontend files to modify (5 files):**
1. `frontend/src/components/screens/PoliciesStageScreen.tsx` — terminology, duplicate instance logic, 50/50 layout verification
2. `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — remove selection state, add "add" action
3. `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — add category badges, formula help, instanceId support
4. `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` — add duplicate instance tests
5. `frontend/src/components/simulation/__tests__/PortfolioCompositionPanel.test.tsx` — add category badge tests

**References:**
- UX spec: `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, Stage 1 — Policies section)
- Epics: `_bmad-output/planning-artifacts/epics.md` (Epic 25, Story 25.2)
- Story 25.1: `_bmad-output/implementation-artifacts/25-1-add-api-driven-categories-endpoint-and-formula-help-metadata.md`
- Antipatterns: `[ANTIPATTERNS - DO NOT REPEAT]` section in workflow context
