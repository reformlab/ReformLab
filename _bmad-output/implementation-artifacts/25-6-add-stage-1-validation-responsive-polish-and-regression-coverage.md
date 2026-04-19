# Story 25.6: Add Stage 1 validation, responsive polish, and regression coverage

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want **closed-loop validation and regression coverage for the revised Stage 1 model**,
so that **I receive clear actionable feedback on policy configuration errors, see warnings about missing population data before execution, and trust that the redesigned Policies stage works reliably across all workflows and device sizes**.

## Acceptance Criteria

1. **Given** a policy is missing type, category, or required parameters, **when** validation runs, **then** the policy set is not marked ready and the failing field is identified. Validity indicator shows warning state, and a specific error message identifies which field is missing (e.g., "Policy 1 is missing required parameters: rate, threshold").
2. **Given** two instances of the same template, **when** validation runs, **then** duplicates are allowed and any real conflicts are shown as inline warnings. Duplicate policies are considered valid unless they have conflicting parameter assignments for the same entity/parameter combination.
3. **Given** selected policies require `vehicle_co2` and the selected population lacks that column, **when** Stage 1 renders, **then** a non-blocking warning explains the missing data. Warning text: "Some policies require population columns that may not be available in the selected population: vehicle_co2. Validate data compatibility in Stage 2 (Population) before running." Warning does not block save or load operations.
4. **Given** Stage 1 renders, **when** visible copy is inspected, **then** the stage uses "Policies" and "Policy Set" terminology rather than "Portfolio". Check: stage heading, toolbar labels, dialog titles, button labels, toast messages, and summary panels.
5. **Given** the Stage 1 regression suite, **when** it runs, **then** it covers from-template creation, from-scratch creation, editable groups, policy set save/load, and responsive layout. All existing Story 25.1-25.5 tests pass, plus new tests for validation error messages, population column warnings, terminology consistency, and responsive 50/50 desktop/stacked mobile layouts.

## Tasks / Subtasks

- [ ] **Add per-policy validation with field-level error messages** (AC: 1)
  - [ ] Add `validationErrors: PolicyValidationError[]` state to `PoliciesStageScreen` to track missing fields per policy
  - [ ] Define `PolicyValidationError` interface: `{ policyIndex: number; policyName: string; missingFields: string[]; invalidFields: string[] }`
  - [ ] Create `validateCompositionEntry()` function that checks each policy for:
    - Missing `policy_type` (for from-scratch policies)
    - Missing `category_id` (for from-scratch policies)
    - Empty `parameters` object (no parameters set)
    - Invalid `rateSchedule` (no years defined, or years outside horizon)
  - [ ] Update `isPortfolioValid` computation to include `validationErrors.length === 0` check
  - [ ] Render validation error summary in conflict display area when errors exist
  - [ ] Show per-policy error badges on policy cards in composition panel
  - [ ] Test: missing type → error shown, validity indicator warning
  - [ ] Test: missing category → error shown, validity indicator warning
  - [ ] Test: empty parameters → error shown, validity indicator warning
  - [ ] Test: invalid rate schedule → error shown, validity indicator warning

- [ ] **Clarify duplicate policy validation behavior** (AC: 2)
  - [ ] Document existing conflict detection behavior for duplicate templates
  - [ ] Verify duplicate instances are allowed (no automatic blocking)
  - [ ] Verify real conflicts (same parameter on same entity) show as inline warnings via existing `ConflictList` component
  - [ ] Add test: two instances of same template with different parameters → valid, no conflict warning
  - [ ] Add test: two instances of same template with conflicting parameters → conflict warning shown
  - [ ] Add test: duplicate policies with "error" strategy → conflicts block save
  - [ ] Add test: duplicate policies with "sum" strategy → conflicts allowed, save succeeds

- [ ] **Add non-blocking population column warnings** (AC: 3)
  - [ ] Define required columns per policy type/category (e.g., `vehicle_co2` for vehicle-related policies)
  - [ ] Add `populationColumnWarnings: string[]` state to track missing columns
  - [ ] Create `checkPopulationColumnCompatibility()` function that:
    - Gets selected population from `activeScenario.populationIds`
    - Looks up population metadata from `populations` prop or via API
    - Checks if population has required columns for selected policies
    - Returns list of missing columns
  - [ ] Render warning banner in Stage 1 when `populationColumnWarnings.length > 0`
  - [ ] Use non-blocking warning style (amber/yellow, not red error)
  - [ ] Ensure warning does not block save/load operations
  - [ ] Test: vehicle policy selected + population missing `vehicle_co2` → warning shown
  - [ ] Test: no population selected → no warning (graceful degradation)
  - [ ] Test: population has all required columns → no warning

- [ ] **Complete Stage 1 terminology audit** (AC: 4)
  - [ ] Audit `PoliciesStageScreen.tsx` for remaining "Portfolio" references in visible copy
  - [ ] Audit `usePortfolioSaveDialog.ts`, `usePortfolioLoadDialog.ts`, `usePortfolioCloneDialog.ts` toast messages
  - [ ] Audit `PortfolioTemplateBrowser.tsx`, `PortfolioCompositionPanel.tsx` visible labels
  - [ ] Update any remaining "Portfolio" → "Policy Set" in user-facing text
  - [ ] Keep backend API routes and TypeScript types unchanged (already done in 25.5)
  - [ ] Add terminology assertions to regression tests
  - [ ] Test: search codebase for "Portfolio" in visible UI strings (exclude backend/types)
  - [ ] Test: verify "Policies" stage name, "Policy Set Composition" header, toast messages use correct terminology

- [ ] **Add responsive layout validation** (AC: 5)
  - [ ] Add `describe("Responsive layout")` test suite in `PoliciesStageScreen.test.tsx`
  - [ ] Test desktop viewport (1024px): verify 50/50 grid layout (both columns visible)
  - [ ] Test mobile viewport (375px): verify stacked layout (browser above composition)
  - [ ] Test toolbar wrapping on small widths (buttons wrap without overflow)
  - [ ] Test template browser scroll on mobile (horizontal overflow handled)
  - [ ] Test composition panel scroll on mobile (vertical overflow handled)
  - [ ] Verify no horizontal scroll on page body at any width
  - [ ] Verify dialog modals work on mobile (fit within viewport)

- [ ] **Add comprehensive regression test suite** (AC: 5)
  - [ ] Create `frontend/src/components/screens/__tests__/PoliciesStageScreen.regression.test.tsx`
  - [ ] Test from-template creation: add template → verify composition updated → verify validity
  - [ ] Test from-scratch creation: open dialog → select type → select category → verify policy created
  - [ ] Test editable groups: rename group → add group → delete empty group → move parameter
  - [ ] Test policy set save: open dialog → verify suggestion → save → verify persisted
  - [ ] Test policy set load: open dialog → select set → verify composition populated
  - [ ] Test policy set clone: open dialog → verify clone name → clone → verify independent copy
  - [ ] Test clear action: click clear → verify composition empty → verify reference reset
  - [ ] Test validation errors: create policy without parameters → verify error shown → verify not ready
  - [ ] Test population warnings: select policy requiring missing column → verify warning shown
  - [ ] Test terminology: render stage → verify "Policies" and "Policy Set" used (not "Portfolio")
  - [ ] Run all existing Story 25.1-25.5 tests and verify no regressions

- [ ] **Backend: Enhance validation endpoint with field-level errors** (optional, AC: 1)
  - [ ] Verify `POST /api/portfolios/validate` returns sufficient detail for field-level errors
  - [ ] If needed, extend `ValidatePortfolioResponse` to include `validation_errors: FieldError[]`
  - [ ] Add backend tests for enhanced validation response
  - [ ] Document: Frontend validation is primary; backend validation is safety net

## Dev Notes

### Architecture Patterns and Constraints

**Project Context:**
- **Python 3.13+** backend with FastAPI, Pydantic v2, PyArrow
- **React 19 / TypeScript** frontend with Vite 7, Tailwind v4, Shadcn/ui
- **Testing:** Vitest + Testing Library (frontend), pytest (backend)
- **Quality gates:** `npm run typecheck`, `npm run lint`, `npm test`, `uv run pytest tests/`

**Frontend - Component Layer:**
- Location: `frontend/src/components/screens/PoliciesStageScreen.tsx`
- Shadcn UI components: Badge, Button, Input, Separator, Alert (for warnings)
- Icons: `AlertTriangle`, `CheckCircle2`, `Info` for validation states

**Frontend - State Management:**
- `PoliciesStageScreen` owns composition state and validation state
- `AppContext` owns scenario state (via `activeScenario`)
- Validation is computed from composition state (using `useMemo` or derived state)
- Use immutable state updates: `setValidationErrors(prev => ...)` pattern

**Frontend - Validation Infrastructure:**
- Existing: `portfolioValidation.ts` with `validatePortfolioName()` function
- Existing: `validatePortfolio()` API call to `POST /api/portfolios/validate`
- Existing: Conflict detection via `usePortfolioSaveDialog` integration
- New: Add per-policy validation function for field-level errors

**Testing - Frontend:**
- Location: `frontend/src/components/screens/__tests__/`
- Use Vitest + Testing Library
- Mock API calls with `vi.mock("@/api/portfolios")` for validation tests
- Responsive tests use `window.innerWidth = 1024` pattern or CSS media query mocks

### Key Design Decisions

**Validation State Design:**

```typescript
// New validation error interface
interface PolicyValidationError {
  policyIndex: number;
  policyName: string;
  missingFields: string[];  // e.g., ["policy_type", "category_id"]
  invalidFields: string[];  // e.g., ["rateSchedule"]
}

// In PoliciesStageScreen component
const [validationErrors, setValidationErrors] = useState<PolicyValidationError[]>([]);

// Compose overall validity from conflicts AND validation errors
const isPortfolioValid = useMemo(() => {
  const hasPolicies = composition.length >= 1;
  const hasConflicts = composition.length >= 2 && conflicts.length > 0 && resolutionStrategy === "error";
  const hasValidationErrors = validationErrors.length > 0;
  return hasPolicies && !hasConflicts && !hasValidationErrors;
}, [composition, conflicts, resolutionStrategy, validationErrors]);
```

**Per-Policy Validation Function:**

```typescript
function validateCompositionEntry(
  entry: CompositionEntry,
  templates: Template[],
): PolicyValidationError | null {
  const missingFields: string[] = [];
  const invalidFields: string[] = [];

  // Check from-scratch policy fields
  if (!entry.templateId) {
    if (!entry.policy_type) missingFields.push("policy_type");
    if (!entry.category_id) missingFields.push("category_id");
  }

  // Check parameters
  if (Object.keys(entry.parameters).length === 0) {
    missingFields.push("parameters");
  }

  // Check rate schedule
  const yearCount = Object.keys(entry.rateSchedule).length;
  if (yearCount === 0) {
    invalidFields.push("rateSchedule (no years defined)");
  }

  if (missingFields.length === 0 && invalidFields.length === 0) {
    return null;
  }

  return {
    policyIndex: 0, // Set by caller
    policyName: entry.name,
    missingFields,
    invalidFields,
  };
}
```

**Population Column Warning Design:**

```typescript
// Required columns mapping (can be extended)
const POLICY_CATEGORY_REQUIRED_COLUMNS: Record<string, string[]> = {
  "vehicle_emissions": ["vehicle_co2", "vehicle_distance"],
  "housing": ["housing_floor_area", "housing_energy_rating"],
  "energy_consumption": ["energy_consumption_kwh"],
  // Add more mappings as needed
};

function checkPopulationColumnCompatibility(
  composition: CompositionEntry[],
  populationId: string | null,
  populations: Population[],
): string[] {
  if (!populationId) return [];

  const population = populations.find(p => p.id === populationId);
  if (!population) return [];

  const missingColumns: string[] = [];

  for (const entry of composition) {
    if (!entry.category_id) continue;

    const required = POLICY_CATEGORY_REQUIRED_COLUMNS[entry.category_id];
    if (!required) continue;

    for (const col of required) {
      // Assume population has columns metadata (extend Population type if needed)
      if (!(population as any).columns?.includes(col)) {
        missingColumns.push(col);
      }
    }
  }

  return [...new Set(missingColumns)]; // Deduplicate
}
```

**Validation Error Display:**

Add to conflict display area in `PoliciesStageScreen`:

```tsx
{/* Validation errors display */}
{validationErrors.length > 0 ? (
  <div className="rounded-lg border border-red-200 bg-red-50/50 p-3">
    <p className="text-xs font-semibold text-red-700 mb-1">
      Policy validation errors
    </p>
    <ul className="text-xs text-red-600 space-y-0.5">
      {validationErrors.map((err) => (
        <li key={err.policyIndex}>
          <strong>{err.policyName}</strong>:{" "}
          {err.missingFields.length > 0 && `Missing: ${err.missingFields.join(", ")}. `}
          {err.invalidFields.length > 0 && `Invalid: ${err.invalidFields.join(", ")}.`}
        </li>
      ))}
    </ul>
  </div>
) : null}
```

**Population Column Warning Display:**

Add warning banner below toolbar in `PoliciesStageScreen`:

```tsx
{/* Population column compatibility warning */}
{populationColumnWarnings.length > 0 ? (
  <div className="rounded-lg border border-amber-200 bg-amber-50/50 p-3 flex items-start gap-2">
    <Info className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
    <div className="text-xs text-amber-700">
      <p className="font-semibold mb-1">Population data compatibility warning</p>
      <p>
        Some policies require population columns that may not be available in the selected population:{" "}
        <strong>{populationColumnWarnings.join(", ")}</strong>.
      </p>
      <p className="mt-1">
        Validate data compatibility in Stage 2 (Population) before running.
      </p>
    </div>
  </div>
) : null}
```

**Terminology Audit Checklist:**

- [ ] Stage heading: "Policies" (already correct)
- [ ] Composition panel header: "Policy Set Composition" (already correct)
- [ ] Toolbar buttons: "Save", "Load", "Clone" (already correct)
- [ ] Dialog titles: "Save Policy Set", "Load Policy Set", "Clone..." (verify)
- [ ] Toast messages: "Policy set saved", "Policy set loaded" (verify)
- [ ] Empty state: "Unsaved policy set" (already correct)
- [ ] RunSummaryPanel: "Policy Set" label (already done in 25.5)
- [ ] Nav rail: "Policies" stage label (verify)

**Responsive Test Pattern:**

```typescript
describe("PoliciesStageScreen — responsive layout", () => {
  it("should render 50/50 layout on desktop", () => {
    // Set desktop viewport
    window.innerWidth = 1024;
    render(<PoliciesStageScreen />);

    // Verify both columns visible
    expect(screen.getByText("Policy Templates")).toBeInTheDocument();
    expect(screen.getByText("Policy Set Composition")).toBeInTheDocument();

    // Verify grid layout (check for lg:grid-cols-2 class effect)
    const gridContainer = screen.getByText("Policy Templates").closest(".grid");
    expect(gridContainer).toHaveClass("lg:grid-cols-2");
  });

  it("should stack layout on mobile", () => {
    // Set mobile viewport
    window.innerWidth = 375;
    render(<PoliciesStageScreen />);

    // Verify both sections still present
    expect(screen.getByText("Policy Templates")).toBeInTheDocument();
    expect(screen.getByText("Policy Set Composition")).toBeInTheDocument();

    // Verify stacking (grid-cols-1 on mobile)
    const gridContainer = screen.getByText("Policy Templates").closest(".grid");
    expect(gridContainer).toHaveClass("grid-cols-1");
  });
});
```

### Source Tree Components to Touch

**Frontend files to modify:**
1. `frontend/src/components/screens/PoliciesStageScreen.tsx` — Add validation state, population warnings, error display
2. `frontend/src/components/screens/__tests__/PoliciesStageScreen.regression.test.tsx` — NEW (comprehensive regression suite)
3. `frontend/src/components/screens/__tests__/PoliciesStageScreen.validation.test.tsx` — NEW (validation-specific tests)
4. `frontend/src/components/screens/__tests__/PoliciesStageScreen.responsive.test.tsx` — NEW (responsive layout tests)
5. `frontend/src/components/simulation/portfolioValidation.ts` — Add `validateCompositionEntry()` function

**Frontend files to audit (terminology):**
1. `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — Check for "Portfolio" references
2. `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — Check for "Portfolio" references
3. `frontend/src/hooks/usePortfolioSaveDialog.ts` — Audit toast messages (done in 25.5, verify)
4. `frontend/src/hooks/usePortfolioLoadDialog.ts` — Audit toast messages (done in 25.5, verify)
5. `frontend/src/hooks/usePortfolioCloneDialog.ts` — Audit toast messages (done in 25.5, verify)

**Backend files to verify (optional):**
1. `src/reformlab/server/routes/portfolios.py` — Verify validation endpoint returns sufficient detail
2. `tests/server/test_portfolios.py` — Add validation error tests if needed

### Integration with Story 25.1, 25.2, 25.3, 25.4, and 25.5

**Story 25.1 provided:**
- Categories API and category metadata
- Category badges and formula help in policy cards
- Categories must be validated for from-scratch policies

**Story 25.2 provided:**
- Duplicate instance support with `instanceCounterRef`
- Browser-composition synchronization
- 50/50 desktop layout implementation

**Story 25.3 provided:**
- From-scratch policy creation with `policy_type` and `category_id` fields
- Default parameter groups for from-scratch policies
- Choice dialog for template vs. from-scratch creation

**Story 25.4 provided:**
- Editable parameter groups with `EditableParameterGroup` interface
- Inline group editing (rename, add, delete, move parameters)

**Story 25.5 provided:**
- Policy set independence and scenario reference contract
- Clone action and naming freeze logic
- Terminology migration (Portfolio → Policy Set) in most UI

**Story 25.6 builds on:**
- Adds per-policy validation to catch missing from-scratch fields
- Adds population column warnings for cross-stage compatibility
- Completes terminology migration for consistency
- Adds regression coverage to ensure all 25.1-25.5 features continue working

### Out of Scope

The following are explicitly out of scope for Story 25.6:
- **Backend validation changes** — Frontend validation is primary; backend validation enhancements are optional
- **Population columns API** — Use existing population metadata; don't add new columns endpoint
- **Hard blocking on population warnings** — Warnings are non-blocking; blocking validation is deferred to Stage 4 (Scenario)
- **Comprehensive policy parameter validation** — Only check presence/absence, not parameter value ranges
- **Policy template schema validation** — Templates are assumed valid; validation focuses on user configuration
- **Cross-stage navigation on warnings** — Warning text mentions Stage 2 but doesn't auto-navigate
- **Accessibility audit** — Responsive tests focus on layout, not full WCAG compliance
- **Performance optimization** — Validation runs synchronously; debouncing exists for conflict detection

### Testing Standards Summary

**Frontend:**
```bash
npm test -- PoliciesStageScreen.regression
npm test -- PoliciesStageScreen.validation
npm test -- PoliciesStageScreen.responsive
```

Test coverage should include:
- Validation error detection (missing type, category, parameters, schedule)
- Validity indicator state (valid vs. invalid)
- Population column warnings (missing columns shown)
- Duplicate policy behavior (allowed, conflicts shown)
- Terminology consistency (Policies, Policy Set everywhere)
- Responsive layout (desktop 50/50, mobile stacked)
- Regression coverage (from-template, from-scratch, groups, save/load)

**Quality gates:**
```bash
# Frontend
npm run typecheck  # Must pass (0 errors)
npm run lint       # Must pass (0 errors)
npm test           # All new and existing tests must pass

# Backend (if changes made)
uv run pytest tests/server/test_portfolios.py
```

### Known Issues / Gotchas

1. **Validation timing:** Validation errors should update in real-time as composition changes, not just on save. Use `useEffect` or `useMemo` to recalculate on composition updates.

2. **Population metadata availability:** Population columns metadata may not exist in the current `Population` type. Use type assertion or extend the interface to add `columns?: string[]` field.

3. **Required columns mapping:** The `POLICY_CATEGORY_REQUIRED_COLUMNS` mapping is a starting point. It may need to be extended based on actual policy requirements. Consider making this data-driven from the categories API in the future.

4. **Non-blocking warning implementation:** Population warnings must NOT block save/load operations. Use a separate state variable from `validationErrors` and don't include it in `isPortfolioValid` computation.

5. **Terminology audit scope:** Focus on user-facing copy only. Don't change backend API routes, TypeScript interfaces, or test file names. The "portfolio" term is still correct in code-only contexts.

6. **Responsive test limitations:** Vitest doesn't have full browser rendering. Use `window.innerWidth` changes to test responsive behavior, but acknowledge that CSS media queries may not match exactly in jsdom.

7. **Regression test organization:** Before creating `PoliciesStageScreen.regression.test.tsx`, check existing test files from Stories 25.2-25.5. Extend existing test suites where possible to avoid duplicate test code.

8. **Validation error UX:** Show per-policy error badges on policy cards so users can quickly identify which policies have problems. Consider using red borders or background colors for invalid policy cards.

9. **Backend validation enhancement:** If extending `POST /api/portfolios/validate`, ensure the response format is backward compatible. Add new fields as optional to avoid breaking existing clients.

10. **From-scratch vs. from-template validation:** From-scratch policies require `policy_type` and `category_id`, but from-template policies don't (they derive these from the template). Validation logic must handle both cases correctly.

11. **Empty parameters edge case:** A policy with `parameters: {}` (empty object) should be flagged as invalid. However, a policy with default parameters set to 0 may be valid (depends on policy semantics). For Story 25.6, treat completely empty `parameters` as invalid.

12. **Rate schedule validation:** A policy with `rateSchedule: {}` (no years) should be flagged as invalid. A policy with years outside the scenario horizon should show a warning but may be valid (user might want to set rates for future years).

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

### Completion Notes List

### File List

**References:**
- Epics: `_bmad-output/planning-artifacts/epics.md` (Epic 25, Story 25.6)
- Story 25.1: `_bmad-output/implementation-artifacts/25-1-add-api-driven-categories-endpoint-and-formula-help-metadata.md` (categories API)
- Story 25.2: `_bmad-output/implementation-artifacts/25-2-redesign-policies-stage-browser-composition-layout-with-types-categories-and-duplicate-policy-instances.md` (duplicate instances, 50/50 layout)
- Story 25.3: `_bmad-output/implementation-artifacts/25-3-implement-create-from-scratch-policy-flow-with-compatible-category-picker-and-default-parameter-groups.md` (from-scratch policies)
- Story 25.4: `_bmad-output/implementation-artifacts/25-4-make-parameter-groups-editable-within-policy-cards.md` (editable groups)
- Story 25.5: `_bmad-output/implementation-artifacts/25-5-make-policy-sets-first-class-reusable-artifacts-independent-from-scenarios.md` (policy set independence, terminology migration)
- Antipatterns: `[ANTIPATTERNS - DO NOT REPEAT]` (Story 25-5 critical lessons)

---
**Story created with ultimate context engine analysis - comprehensive developer guide ready for implementation.**
