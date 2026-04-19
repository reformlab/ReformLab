# Story 25.5: Make policy sets first-class reusable artifacts independent from scenarios

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want **to save, load, clone, and reuse policy sets independently from scenarios, with deterministic name suggestions that freeze after manual edit**,
so that **I can build reusable policy compositions once and apply them across multiple scenarios without duplicating work**.

## Acceptance Criteria

1. **Given** the Policies stage, **when** the analyst saves the current composition, **then** a policy set is persisted independently from the scenario. The save succeeds, a version_id is returned, and the policy set appears in the saved policy sets list with the correct name, description, and policy count.
2. **Given** the current composition contains a Tax on Carbon Emissions and Subsidy on Energy Consumption, **when** the save dialog opens, **then** the suggested name reflects those policy types/categories (e.g., "carbon-tax-plus-energy-subsidy" or similar deterministic pattern derived from the composition).
3. **Given** the analyst manually edits the suggested policy set name, **when** the composition changes later (adding/removing policies), **then** the manual name is not overwritten. The save dialog continues to show the manually edited name, not a new suggestion based on the updated composition.
4. **Given** a saved policy set, **when** loaded into a different scenario, **then** the composition panel populates with the set's policies, categories, groups (including editable groups from Story 25.4), and parameters. All editable parameter groups are restored correctly.
5. **Given** a scenario, **when** inspected programmatically or via the scenario detail view, **then** it references a policy set by name (string identifier) rather than embedding the full policy composition as the only source of truth. The scenario's `portfolioName` field contains the policy set name.
6. **Given** old localStorage state with `portfolioName` from before Story 25.5, **when** the app initializes, **then** it migrates to the new policy set reference model without losing the existing composition. The migration preserves the portfolio name as a reference to the independent policy set.

## Tasks / Subtasks

- [ ] **Add clone action to Stage 1 toolbar** (AC: 1, 4)
  - [ ] Add "Clone" button to PoliciesStageScreen toolbar next to Load button
  - [ ] Button should be disabled when no policy set is currently loaded (`activePortfolioName` is null)
  - [ ] Clicking Clone opens the clone dialog (reuse `usePortfolioCloneDialog`)
  - [ ] Clone creates a new independent policy set with "-copy" suffix
  - [ ] Update UX copy: button label "Clone", tooltip "Clone active policy set"

- [ ] **Implement name suggestion freeze after manual edit** (AC: 2, 3)
  - [ ] Add `saveDialogNameManuallyEdited` state to track whether user has edited the name
  - [ ] Initialize suggestion on dialog open using `generatePortfolioSuggestion(templates, composition)`
  - [ ] Set `saveDialogNameManuallyEdited = false` on dialog open
  - [ ] On `handleSaveNameChange`, set `saveDialogNameManuallyEdited = true` (user has manually edited)
  - [ ] Only update `portfolioSaveName` from suggestion when `!saveDialogNameManuallyEdited`
  - [ ] Ensure subsequent dialog opens recalculate suggestion if name wasn't manually edited
  - [ ] Test: add policy → open dialog → see suggestion → close → add another policy → open dialog → verify suggestion updated
  - [ ] Test: add policy → open dialog → edit name manually → close → add another policy → open dialog → verify manual name preserved

- [ ] **Migrate Stage 1 terminology from "Portfolio" to "Policy Set"** (AC: 1)
  - [ ] Update PoliciesStageScreen visible copy: "Portfolio" → "Policy Set"
  - [ ] Update toolbar labels: "Saved Policy Sets" (was "Saved Portfolios")
  - [ ] Update dialog titles: "Save Policy Set", "Load Policy Set", "Clone Policy Set"
  - [ ] Update validation messages: "Policy set name is required" (was "Portfolio name")
  - [ ] Update toast messages: "Policy set 'xxx' saved", "Loaded policy set 'xxx'"
  - [ ] Update placeholder text: "my-policy-set" (was "my-portfolio")
  - [ ] Update empty states: "Add at least 1 policy template to compose a policy set"
  - [ ] Update action tooltips: "Save policy set", "Load policy set", "Clone active policy set"
  - [ ] Update RunSummaryPanel: "Policy Set" label (was "Portfolio")
  - [ ] Update ValidationGate references where appropriate
  - [ ] Keep backend API routes as `/api/portfolios` (internal implementation detail)
  - [ ] Keep TypeScript interface names unchanged (`PortfolioListItem`, etc.) for code stability

- [ ] **Enhance deterministic name suggestions from policy types and categories** (AC: 2)
  - [ ] Review `generatePortfolioSuggestion` in `naming.ts`
  - [ ] For 1 policy: use slugified policy name
  - [ ] For 2 policies: use "slug1-plus-slug2" pattern
  - [ ] For 3+ policies: use "first-slug-plus-(N-1)-more" pattern
  - [ ] Ensure suggestions pass `validatePortfolioName` validation
  - [ ] Consider incorporating category information for better names (e.g., "carbon-tax-energy-subsidy" instead of generic "plus-2-more")
  - [ ] Add unit tests for suggestion generation with various compositions

- [ ] **Verify scenario-reference contract for policy set independence** (AC: 5)
  - [ ] Verify `WorkspaceScenario.portfolioName: string | null` field exists in `types/workspace.ts`
  - [ ] Verify scenarios reference policy sets by name (string identifier), not by embedding composition
  - [ ] Verify `PoliciesStageScreen` sets `activeScenario.portfolioName` on save
  - [ ] Verify `usePortfolioLoadDialog` updates scenario reference on load
  - [ ] Add test: scenario created with policy set reference has correct `portfolioName`
  - [ ] Add test: loading policy set into scenario updates scenario's `portfolioName` field

- [ ] **Implement localStorage migration for legacy portfolio state** (AC: 6)
  - [ ] Review existing localStorage keys in `useScenarioPersistence.ts`
  - [ ] Check if `portfolioName` key already exists in persistence layer
  - [ ] If migration needed: add migration logic in `AppContext` initialization effect
  - [ ] Migration should: read old `portfolioName` value → preserve as policy set reference → clear old key if appropriate
  - [ ] Add migration test: create legacy state → initialize app → verify policy set reference preserved
  - [ ] Ensure idempotent migration (running twice doesn't break anything)

- [ ] **Add clear/start over action improvements** (AC: 1)
  - [ ] Verify existing "Clear" button in PoliciesStageScreen toolbar
  - [ ] Ensure clear action resets: composition array, conflicts array, activePortfolioName, instanceCounterRef
  - [ ] Ensure clear action updates scenario: `updateScenarioField("portfolioName", null)`
  - [ ] Ensure clear action updates AppContext: `setSelectedPortfolioName(null)`
  - [ ] Add test: clear action → verify composition empty, no active portfolio, scenario reference null

- [ ] **Backend: Verify policy set independence and aliases** (AC: 1)
  - [ ] Verify `/api/portfolios` routes work independently from scenario routes
  - [ ] Consider adding `/api/policy-sets` route aliases for clarity (optional, depends on scope decision)
  - [ ] If adding aliases: create new router pointing to existing route handlers
  - [ ] Verify metadata sidecar storage works for cloned policy sets
  - [ ] Add backend tests: clone preserves editable_parameter_groups and other Story 25.4 fields

- [ ] **Frontend types and interfaces** (AC: 4, 5)
  - [ ] Verify `PortfolioListItem`, `PortfolioDetailResponse`, `PortfolioPolicyItem` in `api/types.ts`
  - [ ] Verify `CompositionEntry` interface includes all Story 25.4 fields (editableParameterGroups, category_id, parameter_groups)
  - [ ] Verify `WorkspaceScenario` interface has `portfolioName: string | null` field
  - [ ] No changes needed to types if they already support independence (verify this)

- [ ] **Testing** (AC: 1, 2, 3, 4, 5, 6)
  - [ ] Frontend tests: save policy set → verify persisted independently
  - [ ] Frontend tests: deterministic name suggestions for 1, 2, 3+ policies
  - [ ] Frontend tests: manual name edit freezes suggestion (composition changes don't override)
  - [ ] Frontend tests: load policy set → verify composition panel populated correctly
  - [ ] Frontend tests: load policy set → verify editable groups restored (Story 25.4 integration)
  - [ ] Frontend tests: clone policy set → verify independent copy created
  - [ ] Frontend tests: clear action → verify composition and reference reset
  - [ ] Frontend tests: scenario has correct portfolioName after save/load/clone
  - [ ] Integration tests: policy set reused across multiple scenarios
  - [ ] Migration tests: legacy localStorage state migrates correctly
  - [ ] Backend tests: policy set CRUD operations work independently
  - [ ] Backend tests: clone preserves all policy set fields including metadata

## Dev Notes

### Architecture Patterns and Constraints

**Backend - Server Layer:**
- Location: `src/reformlab/server/routes/portfolios.py`
- Pydantic v2 models in `models.py` — use `BaseModel` for all request/response types
- Error responses follow the `{"what": str, "why": str, "fix": str}` pattern via `HTTPException(detail={...})`
- Portfolio persistence: registry at `registry.path / name /` with metadata sidecar at `metadata.json`
- **Policy sets are already independent** — the `/api/portfolios` routes implement full CRUD with persistence separate from scenarios

**Frontend - Component Layer:**
- Location: `frontend/src/components/`
- Shadcn UI components available: Badge, Button, Input, Select, Separator, Popover
- Icons from lucide-react: use `Save`, `FolderOpen`, `Copy`, `X` for toolbar actions

**Frontend - State Management:**
- `PoliciesStageScreen` owns composition state and policy set operations
- `AppContext` owns scenario state and `selectedPortfolioName`
- Scenarios reference policy sets by name: `WorkspaceScenario.portfolioName: string | null`
- Use immutable state updates: `setComposition(prev => ...)` pattern

**Testing - Frontend:**
- Location: `frontend/src/components/**/__tests__/`
- Use Vitest + Testing Library
- Mock API calls with `vi.mock("@/api/portfolios")` for persistence tests

**Testing - Backend:**
- Location: `tests/server/test_portfolios.py`
- Use FastAPI `TestClient` with auth headers fixture
- Use `_cleanup_test_portfolio` fixture to avoid 409 conflicts

### Key Design Decisions

**Terminology Migration (UI only, not backend):**

The term "Portfolio" is replaced with "Policy Set" in user-facing copy, but the backend API and TypeScript types keep "Portfolio" naming for backward compatibility:

```
User-facing: "Policy Set"
Backend API: /api/portfolios (unchanged)
TypeScript types: PortfolioListItem, PortfolioPolicyItem (unchanged)
Database/storage: portfolios/ (unchanged)
```

This approach minimizes breaking changes while improving UX clarity.

**Name Suggestion Freeze Logic:**

Track whether the user has manually edited the name with a boolean flag:

```typescript
// In usePortfolioSaveDialog.ts
const [saveDialogNameManuallyEdited, setSaveDialogNameManuallyEdited] = useState(false);

// Recalculate suggestion only when user hasn't manually edited
useEffect(() => {
  if (!saveDialogOpen || saveDialogNameManuallyEdited) return;
  const suggestion = generatePortfolioSuggestion(templates, composition);
  setPortfolioSaveName(suggestion);
}, [composition, templates, saveDialogOpen, saveDialogNameManuallyEdited]);

// Mark as manually edited on user input
const handleSaveNameChange = useCallback((name: string) => {
  setSaveDialogNameManuallyEdited(true);
  setPortfolioSaveName(name);
  setSaveNameError(validatePortfolioName(name));
}, []);
```

Reset the flag when the dialog closes so reopening the dialog recalculates the suggestion:

```typescript
const closeSaveDialog = useCallback(() => {
  setSaveDialogOpen(false);
  setSaveDialogNameManuallyEdited(false);
}, []);
```

**Scenario Reference Contract:**

Scenarios reference policy sets by name (string identifier), not by embedding the full composition:

```typescript
// In types/workspace.ts
export interface WorkspaceScenario {
  // ... other fields
  portfolioName: string | null;  // References PortfolioListItem.name
  // NOT: portfolioComposition: CompositionEntry[]  <-- This would embed the composition
}
```

This allows:
- Multiple scenarios to reference the same policy set
- Policy set updates to potentially affect all referencing scenarios (or not, depending on versioning strategy)
- Policy set lifecycle independent from scenario lifecycle

**Clone Action Integration:**

The clone action reuses the existing `usePortfolioCloneDialog` hook:

```typescript
// In PoliciesStageScreen toolbar
{activePortfolioName ? (
  <Button
    size="sm"
    variant="outline"
    onClick={() => openCloneDialog(activePortfolioName)}
    title="Clone active policy set"
  >
    <Copy className="mr-1.5 h-3 w-3" />
    Clone
  </Button>
) : null}
```

**Deterministic Name Suggestions:**

The existing `generatePortfolioSuggestion` function in `naming.ts` provides deterministic naming:

```typescript
// 0 policies: "untitled-portfolio"
// 1 policy: slugified template name
// 2 policies: "slug1-plus-slug2"
// 3+ policies: "first-slug-plus-(N-1)-more"
```

For Story 25.5, consider enhancing the suggestions to include category information for more descriptive names. This is optional depending on scope.

**Migration Path for Legacy State:**

Check if migration is needed by reviewing existing localStorage keys. The current implementation may already store `portfolioName` correctly, so migration may be a no-op. If migration is needed:

```typescript
// In AppContext initialization effect
const LEGACY_PORTFOLIO_KEY = "reformlab-legacy-portfolio-name";

useEffect(() => {
  if (!isAuthenticated) return;
  if (initializedRef.current) return;
  initializedRef.current = true;

  // Migration: read legacy key if present
  const legacyPortfolioName = localStorage.getItem(LEGACY_PORTFOLIO_KEY);
  if (legacyPortfolioName) {
    // Preserve as current policy set reference
    setSelectedPortfolioName(legacyPortfolioName);
    // Clear legacy key to prevent re-migration
    localStorage.removeItem(LEGACY_PORTFOLIO_KEY);
  }

  // ... rest of initialization logic
}, [isAuthenticated]);
```

**Clear Action Behavior:**

The clear action should completely reset the composition state:

```typescript
const handleClear = useCallback(() => {
  setComposition([]);
  setConflicts([]);
  setActivePortfolioName(null);
  loadedRef.current = null;
  updateScenarioField("portfolioName", null);
  setSelectedPortfolioName(null);
  instanceCounterRef.current = 0; // Reset counter on clear
}, [updateScenarioField, setSelectedPortfolioName]);
```

### Source Tree Components to Touch

**Frontend files to modify:**
1. `frontend/src/components/screens/PoliciesStageScreen.tsx` — Add clone button, update terminology, implement name freeze
2. `frontend/src/hooks/usePortfolioSaveDialog.ts` — Add name freeze logic
3. `frontend/src/components/engine/RunSummaryPanel.tsx` — Update "Portfolio" → "Policy Set" label
4. `frontend/src/contexts/AppContext.tsx` — Verify/migrate localStorage state
5. `frontend/src/utils/naming.ts` — Enhance `generatePortfolioSuggestion` if needed (optional)
6. `frontend/src/components/simulation/__tests__/PoliciesStageScreen.policySets.test.tsx` — NEW (policy set independence tests)

**Backend files to verify (may not need changes):**
1. `src/reformlab/server/routes/portfolios.py` — Verify independent CRUD works, add alias routes if needed
2. `src/reformlab/server/models.py` — Verify types support independence
3. `tests/server/test_portfolios.py` — Add clone preservation tests

**Test files to create/modify:**
1. `frontend/src/components/simulation/__tests__/PoliciesStageScreen.policySets.test.tsx` — NEW (comprehensive policy set tests)
2. `frontend/src/hooks/__tests__/usePortfolioSaveDialog.nameFreeze.test.ts` — NEW (name freeze tests)
3. `tests/server/test_portfolios.py` — Add clone metadata preservation tests

### Integration with Story 25.1, 25.2, 25.3, and 25.4

**Story 25.1 provided:**
- Categories API and category metadata structure
- Category badges and formula help in policy cards

**Story 25.2 provided:**
- Duplicate instance support with `instanceCounterRef`
- `CompositionEntry` interface with `instanceId` field
- Browser-composition synchronization via `useMemo`

**Story 25.3 provided:**
- From-scratch policy creation with `policy_type` and `category_id` fields
- Default parameter groups for from-scratch policies
- `parameter_groups: string[]` field in `CompositionEntry`

**Story 25.4 provided:**
- Editable parameter groups with `EditableParameterGroup` interface
- Inline group editing (rename, add, delete, move parameters)
- Metadata sidecar storage for UI-layer fields

**Story 25.5 builds on:**
- Takes the independent portfolio CRUD from backend and ensures frontend terminology matches
- Adds clone action to make policy set reuse more convenient
- Implements name suggestion freeze for better UX
- Verifies scenario-reference contract for independence
- Migrates any legacy state to the new model

### Out of Scope

The following are explicitly out of scope for Story 25.5:
- **Backend API route renaming** — `/api/portfolios` remains; UI terminology changes only
- **TypeScript interface renaming** — `PortfolioListItem`, etc. remain for code stability
- **Policy set versioning** — scenarios reference policy sets by name, not by version
- **Policy set deduplication** — no detection of duplicate policy sets with same composition
- **Policy set sharing between users** — no collaboration or sharing features
- **Policy set templates** — no predefined policy set templates beyond what users save
- **Bulk policy set operations** — no batch operations on multiple policy sets
- **Policy set search/filtering** — list remains simple; no advanced search

### Testing Standards Summary

**Frontend:**
```bash
npm test -- PoliciesStageScreen.policySets
```

Test coverage should include:
- Save policy set → verify persisted independently
- Deterministic name suggestions for 1, 2, 3+ policies
- Manual name edit freezes suggestion
- Load policy set → composition populated correctly
- Load policy set → editable groups restored (Story 25.4 integration)
- Clone policy set → independent copy created
- Clear action → composition and reference reset
- Scenario has correct portfolioName after operations
- Policy set reused across multiple scenarios

**Migration tests:**
```bash
npm test -- useScenarioPersistence
```

Test coverage should include:
- Legacy localStorage state migration
- Idempotent migration (running twice safe)

**Quality gates:**
```bash
# Frontend
npm run typecheck
npm run lint
npm test -- PoliciesStageScreen.policySets

# Backend
uv run pytest tests/server/test_portfolios.py
```

### Known Issues / Gotchas

1. **Terminology consistency:** Ensure all user-facing "Portfolio" text is changed to "Policy Set", but backend API and TypeScript types keep "Portfolio" naming. This inconsistency is intentional for backward compatibility.

2. **Name suggestion freeze scope:** The freeze is per-save-dialog-session, not permanent. If the user closes the save dialog and reopens it, the suggestion recalculates (unless they manually edit again). This is the correct behavior — we don't want to permanently freeze suggestions across sessions.

3. **Scenario reference lifetime:** Scenarios reference policy sets by name. If a policy set is deleted, scenarios referencing it will have a dangling reference. This is acceptable for now; future stories could add reference tracking or validation.

4. **Clone naming collision:** The existing `generatePortfolioCloneName` function handles collisions by appending "-2", "-3", etc. Verify this works correctly when cloning a policy set that was just created.

5. **Clear action and saved scenarios:** The clear action clears the current composition but doesn't delete saved policy sets. This is correct — clear is for "start over" not "delete saved work".

6. **Instance counter reset:** The clear action resets `instanceCounterRef` to 0. This is correct for starting fresh but could cause instance ID collisions if a policy set is loaded after clear. The `usePortfolioLoadDialog` hook should set the counter to avoid collisions (verify this).

7. **Metadata sidecar for clones:** Verify that cloning a policy set also copies the metadata sidecar file. The backend clone route should handle this, but verify the implementation.

8. **Deterministic suggestions with categories:** The current `generatePortfolioSuggestion` doesn't incorporate category information. If enhanced suggestions are desired (e.g., "carbon-tax-energy-subsidy" instead of "policy1-plus-policy2"), this requires updates to `naming.ts`.

9. **Migration necessity:** The current implementation may already store `portfolioName` correctly in localStorage. Review existing keys before implementing migration — it may be a no-op.

10. **Policy set independence verification:** Scenarios reference policy sets by name. This means if a policy set is updated, scenarios referencing it won't automatically see the updates until they reload the policy set. This is expected behavior but worth documenting.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

### Completion Notes List

### File List

**References:**
- UX spec: `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, Stage 1 — Policies section)
- Epics: `_bmad-output/planning-artifacts/epics.md` (Epic 25, Story 25.5)
- Story 25.1: `_bmad-output/implementation-artifacts/25-1-add-api-driven-categories-endpoint-and-formula-help-metadata.md` (categories API)
- Story 25.2: `_bmad-output/implementation-artifacts/25-2-redesign-policies-stage-browser-composition-layout-with-types-categories-and-duplicate-policy-instances.md` (duplicate instances)
- Story 25.3: `_bmad-output/implementation-artifacts/25-3-implement-create-from-scratch-policy-flow-with-compatible-category-picker-and-default-parameter-groups.md` (from-scratch policies)
- Story 25.4: `_bmad-output/implementation-artifacts/25-4-make-parameter-groups-editable-within-policy-cards.md` (editable parameter groups)
