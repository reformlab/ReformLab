# Story 22.3: Deterministic portfolio and scenario auto naming

Status: ready-for-dev

## Story

As a policy analyst working in the ReformLab workspace,
I want portfolio and scenario names to be auto-suggested from their current context (portfolio composition, population selection)
so that I don't have to invent names from scratch every time I save,
but I can still override the suggestions with custom names when I want them.

## Acceptance Criteria

1. **[AC-1]** Given the portfolio save flow is opened without a manual name already entered, when the save dialog renders, then the name input field is pre-filled with a deterministic suggestion derived from the current composition (not with an empty field).
2. **[AC-2]** Given a portfolio with 1 selected template, when the save dialog opens, then the suggested name uses the template name (e.g., "Carbon Tax — Flat Rate" becomes "carbon-tax-flat-rate" or similar slugified form).
3. **[AC-3]** Given a portfolio with 2 selected templates, when the save dialog opens, then the suggested name joins both template short names with ` + ` (e.g., "carbon-tax + subsidy").
4. **[AC-4]** Given a portfolio with 3+ selected templates, when the save dialog opens, then the suggested name uses "[first short policy name] + [N] more" pattern (e.g., "carbon-tax + 2 more").
5. **[AC-5]** Given a portfolio save dialog with an auto-suggested name, when the user manually edits the name field, then subsequent changes to composition during the same save flow do NOT overwrite the manual edit.
6. **[AC-6]** Given a new scenario is created (via "New Scenario" action), when the scenario object is initialized, then its initial name is suggested from the current portfolio and population context rather than defaulting to "New Scenario".
7. **[AC-7]** Given a scenario name that was auto-suggested, when the user manually edits it via `updateScenarioField("name", ...)`, then future context changes (portfolio changes, population changes) do NOT overwrite the manual edit.
8. **[AC-8]** Given cloning is invoked (portfolio clone or scenario clone), when the clone dialog completes or clone object is created, then the clone's name follows a deterministic and distinguishable convention from the original (e.g., original + "-copy" or similar).

## Tasks / Subtasks

- [ ] **Task 1: Create `generatePortfolioSuggestion()` utility function** (AC: 2, 3, 4)
  - [ ] Create new utility file `frontend/src/utils/naming.ts` with deterministic naming functions
  - [ ] Implement `generatePortfolioSuggestion()` that takes `templates[]` and `composition[]` and returns a string
  - [ ] Implement single-policy logic: use template name, slugified (kebab-case)
  - [ ] Implement two-policy logic: join short names with ` + `
  - [ ] Implement 3+ policy logic: "[first] + [N-1] more"
  - [ ] Add fallback to "Untitled Portfolio" for empty composition
  - [ ] Export function for use in components

- [ ] **Task 2: Add portfolio name suggestion to PoliciesStageScreen save dialog** (AC: 1, 2, 3, 4, 5)
  - [ ] Import `generatePortfolioSuggestion()` in `PoliciesStageScreen.tsx`
  - [ ] Add local state `portfolioNameManuallyEdited` to track whether user has manually edited the name
  - [ ] Add `useEffect` that updates `portfolioSaveName` when `composition` changes, ONLY if `!portfolioNameManuallyEdited`
  - [ ] Set `portfolioNameManuallyEdited = true` when user types in the name input field
  - [ ] Reset `portfolioNameManuallyEdited = false` when dialog closes (so re-opening gets fresh suggestion)
  - [ ] Verify that manual edits are preserved even when composition changes during the same dialog session

- [ ] **Task 3: Add scenario name suggestion to `createNewScenario()` in AppContext** (AC: 6)
  - [ ] Create `generateScenarioSuggestion()` utility in `frontend/src/utils/naming.ts`
  - [ ] Function should accept: `activeScenario.portfolioName`, `selectedPopulationId`, `populations[]`, `portfolios[]`
  - [ ] Suggested name pattern: if portfolio is set, use portfolio name as base; if population is set, append population short name
  - [ ] Example patterns: "Carbon Tax (FR 2024)", "My Portfolio (FR Synthetic 2024)"
  - [ ] Fallback: "Untitled Scenario" (better than "New Scenario")
  - [ ] Update `createNewScenario()` in `AppContext.tsx` to use `generateScenarioSuggestion()` for initial `name` field
  - [ ] Import `populations` and `selectedPopulationId` into the suggestion logic

- [ ] **Task 4: Implement manual edit detection for scenario names** (AC: 7)
  - [ ] Add `nameManuallyEdited` flag to `WorkspaceScenario` (or track separately in AppContext)
  - [ ] Since `WorkspaceScenario` is frozen dataclass, track this in a `Set<string>` in AppContext (scenario IDs with manually edited names)
  - [ ] Add `useEffect` in AppContext that updates `activeScenario.name` ONLY if:
    - `activeScenario.id` is NOT in the `manuallyEditedNames` set
    - AND `portfolioName` or `populationIds` changes
  - [ ] When user calls `updateScenarioField("name", newValue)`, add `activeScenario.id` to `manuallyEditedNames` set
  - [ ] Persist the `manuallyEditedNames` set to localStorage (use a new key: `reformlab-manually-edited-names`)

- [ ] **Task 5: Apply deterministic naming to portfolio clone dialog** (AC: 8)
  - [ ] Update `PoliciesStageScreen.tsx` clone dialog default name
  - [ ] Current: `${activePortfolioName}-copy` (already deterministic — keep this pattern)
  - [ ] Verify the pattern is consistent and distinguishable from the original

- [ ] **Task 6: Apply deterministic naming to scenario clone in AppContext** (AC: 8)
  - [ ] Current pattern in `cloneCurrentScenario()`: `${activeScenario.name} (copy)` — verify this is used
  - [ ] Ensure clone gets a new entry in `manuallyEditedNames` immediately (cloned name is "manual" by definition)

- [ ] **Task 7: Add tests for naming utility functions** (AC: 2, 3, 4, 6)
  - [ ] Create `frontend/src/utils/__tests__/naming.test.ts`
  - [ ] Test `generatePortfolioSuggestion()` with 0 templates → "Untitled Portfolio"
  - [ ] Test `generatePortfolioSuggestion()` with 1 template → slugified template name
  - [ ] Test `generatePortfolioSuggestion()` with 2 templates → "name1 + name2"
  - [ ] Test `generatePortfolioSuggestion()` with 3+ templates → "first + N more"
  - [ ] Test `generateScenarioSuggestion()` with portfolio + population
  - [ ] Test `generateScenarioSuggestion()` with portfolio only
  - [ ] Test `generateScenarioSuggestion()` with no context → "Untitled Scenario"

- [ ] **Task 8: Add integration tests for portfolio save dialog** (AC: 1, 5)
  - [ ] Add test to `PoliciesStageScreen.test.tsx`
  - [ ] Test: opening save dialog pre-fills name with suggestion
  - [ ] Test: composition changes update suggested name if user hasn't edited
  - [ ] Test: manual edit is preserved when composition changes
  - [ ] Test: re-opening dialog after close gets fresh suggestion

- [ ] **Task 9: Add integration tests for scenario naming** (AC: 6, 7)
  - [ ] Create or update `AppContext.test.tsx` for scenario naming tests
  - [ ] Test: `createNewScenario()` produces suggested name, not "New Scenario"
  - [ ] Test: scenario name updates when portfolio changes (if not manually edited)
  - [ ] Test: manual edit via `updateScenarioField("name", ...)` prevents auto-updates
  - [ ] Test: clone produces deterministic "(copy)" suffix

## Dev Notes

### Current Implementation Analysis

**Portfolio Save Dialog (`PoliciesStageScreen.tsx`, lines ~477-543):**
- Current `portfolioSaveName` state is initialized to empty string `""`
- Save dialog opens with empty name field
- No auto-suggestion logic exists
- Validation enforces `portfolioSaveName` is non-empty before save

**Scenario Creation (`AppContext.tsx`, lines ~333-352):**
- `createNewScenario()` initializes with hardcoded `name: "New Scenario"`
- No context-aware naming exists
- Population and portfolio context are available but not used for naming

**Scenario Clone (`AppContext.tsx`, lines ~354-363):**
- Current pattern: `${activeScenario.name} (copy)` — already follows deterministic convention
- No changes needed here except to verify consistency

**Portfolio Clone (`PoliciesStageScreen.tsx`, lines ~696-744):**
- Current default: `${activePortfolioName}-copy` — already follows deterministic convention
- No changes needed here except to verify consistency

### Naming Algorithm Specifications

**Portfolio Name Rules:**
```
1 policy:        slugify(template.name)
2 policies:       slugify(template1.name) + " + " + slugify(template2.name)
3+ policies:      slugify(firstTemplate.name) + " + " + (count - 1) + " more"
empty:           "Untitled Portfolio"
```

**slugify() function:**
- Convert to lowercase
- Replace spaces with hyphens
- Remove special characters (keep only alphanumeric, hyphens)
- Example: "Carbon Tax — Flat Rate" → "carbon-tax-flat-rate"

**Scenario Name Rules:**
```
has portfolio:   portfolio.displayName + (population ? " (" + population.shortName + ")" : "")
no portfolio:    population ? "Untitled (" + population.shortName + ")" : "Untitled Scenario"
```

**portfolio.displayName** logic:
- If portfolioName is set, use it (it's already slugified from save)
- Otherwise, generate suggestion on-the-fly

**population.shortName** logic:
- Remove "France " prefix if present
- Remove year suffix if present
- Example: "France Synthetic 2024" → "Synthetic 2024" or just "FR Synthetic"

### State Management Design

**Portfolio Name Tracking:**
- Local component state in `PoliciesStageScreen`:
  ```tsx
  const [portfolioNameManuallyEdited, setPortfolioNameManuallyEdited] = useState(false);
  ```
- Reset to `false` when dialog opens
- Set to `true` on input `onChange` event

**Scenario Name Tracking:**
- AppContext-level Set to track manually-edited scenario IDs:
  ```tsx
  const [manuallyEditedScenarioNames, setManuallyEditedScenarioNames] = useState<Set<string>>(new Set());
  ```
- Persist to localStorage as JSON array of IDs
- Check membership before applying auto-update

### Component Architecture

**Files to create:**
- `frontend/src/utils/naming.ts` — naming utility functions
- `frontend/src/utils/__tests__/naming.test.ts` — naming function tests

**Files to modify:**
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — portfolio save dialog
- `frontend/src/contexts/AppContext.tsx` — scenario creation and naming
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` — add integration tests

**New localStorage keys:**
- `reformlab-manually-edited-names` — JSON array of scenario IDs with manually edited names

### Testing Patterns

**Per project context:**
- Use Vitest for frontend tests
- Test file structure mirrors source
- Mock `useAppState` with `vi.mock("@/contexts/AppContext")`

**Test coverage for naming utilities:**
- Unit tests for all edge cases of `generatePortfolioSuggestion()`
- Unit tests for all edge cases of `generateScenarioSuggestion()`
- Test with empty inputs, single inputs, multiple inputs

**Test coverage for integration:**
- Portfolio save dialog opens with pre-filled name
- Composition changes update suggestion (if not edited)
- Manual edits block auto-updates
- Dialog re-open resets state
- Scenario creation uses suggestion
- Scenario name updates follow context changes (if not edited)
- Clone naming is deterministic

### Scope Boundaries

**OUT OF SCOPE for Story 22.3:**
- No changes to backend APIs or database schemas
- No automatic saving (names are suggestions only, user must still click Save)
- No retroactive renaming of already-saved portfolios or scenarios
- No AI-generated names or remote naming service
- No changes to Engine stage rename (that's Story 22.5)

**IN SCOPE:**
- Frontend-only deterministic naming utilities
- Portfolio save dialog pre-fill behavior
- Scenario creation initial name
- Manual edit detection and preservation
- Clone naming verification (existing patterns are already correct)

### Known Constraints and Gotchas

1. **Frozen dataclass constraint:** `WorkspaceScenario` is a frozen dataclass (`@dataclass(frozen=True)` equivalent in TypeScript via readonly assertion). We cannot add a `nameManuallyEdited` field directly to the type. Use a separate Set in AppContext to track this.

2. **Slugification consistency:** Portfolio names are slugified before saving to backend. The naming utility should produce the same format to avoid confusion between display names and save names.

3. **Population short names:** The `Population` type has `name` (e.g., "France Synthetic 2024"). For scenario naming, we need a "short name" function that extracts the essential part without overly long context.

4. **Template name availability:** `Template.name` is user-friendly (e.g., "Carbon Tax — Flat Rate"). For portfolio naming, we should slugify this for consistency with backend naming conventions.

5. **Validation compatibility:** The existing `validatePortfolioName()` function in `PortfolioCompositionPanel` expects specific patterns (lowercase, hyphens, alphanumeric). Our suggestions must be compatible with this validation.

6. **localStorage persistence:** The `manuallyEditedScenarioNames` set must be persisted to localStorage so manual edit tracking survives page reloads.

7. **Demo scenario compatibility:** The demo scenario (created in `createDemoScenario()`) should NOT be treated as "manually edited" so it can get auto-updates if portfolio/population context changes.

### References

- **UX Revision 3 spec:** `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md` — Change 4 (Portfolio Naming) and Change 6 (Scenario Naming)
- **Epic 22 definition:** `_bmad-output/planning-artifacts/epics.md#Epic-22` — Full epic context
- **Story 22.1 completion:** `_bmad-output/implementation-artifacts/22-1-shell-branding-external-links-and-scenario-entry-relocation.md` — Previous story for reference
- **PoliciesStageScreen source:** `frontend/src/components/screens/PoliciesStageScreen.tsx` — Current portfolio save dialog
- **AppContext source:** `frontend/src/contexts/AppContext.tsx` — Current scenario creation
- **Workspace types:** `frontend/src/types/workspace.ts` — `WorkspaceScenario` type definition
- **Mock data:** `frontend/src/data/mock-data.ts` — `Template` and `Population` types

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (via create-story workflow)

### Implementation Plan

**Phase 1: Naming Utilities (Task 1, Task 3)**
- Create `frontend/src/utils/naming.ts`
- Implement `slugify()` helper function
- Implement `generatePortfolioSuggestion()` with rules for 0, 1, 2, 3+ templates
- Implement `getPopulationShortName()` helper
- Implement `generateScenarioSuggestion()` with portfolio + population context
- Add unit tests in `frontend/src/utils/__tests__/naming.test.ts`

**Phase 2: Portfolio Save Dialog (Task 2)**
- Modify `PoliciesStageScreen.tsx`
- Add `portfolioNameManuallyEdited` state
- Add effect to update `portfolioSaveName` when composition changes (if not edited)
- Wire up `onChange` handler to set `portfolioNameManuallyEdited = true`
- Reset state when dialog closes
- Add integration tests

**Phase 3: Scenario Naming (Task 4, parts of Task 3)**
- Modify `AppContext.tsx`
- Create `manuallyEditedScenarioNames` Set with localStorage persistence
- Update `createNewScenario()` to use `generateScenarioSuggestion()`
- Add effect to auto-update scenario names when context changes (if not manually edited)
- Update `updateScenarioField()` to add scenario ID to manually edited set
- Add integration tests

**Phase 4: Clone Verification (Task 5, Task 6)**
- Verify existing clone patterns are correct
- Ensure clones get added to manually edited set
- Add tests for clone naming

### Debug Log References

Analysis completed from source files:
- `PoliciesStageScreen.tsx` — portfolio save dialog implementation
- `AppContext.tsx` — scenario creation and state management
- `workspace.ts` — type definitions
- `mock-data.ts` — Template and Population type shapes
- `ux-revision-3-implementation-spec.md` — requirements for Changes 4 and 6

### Completion Notes List

- Story 22.3 is frontend-only — no backend changes required
- Depends on Story 22.1 (shell context) for workflow integration but has no code dependencies on it
- Naming utilities are pure functions — easy to test and reason about
- Manual edit tracking uses a Set in AppContext + localStorage for persistence
- Clone naming patterns already exist and are deterministic — this story primarily verifies they remain consistent
- All changes preserve existing functionality:
  - Portfolio save still requires user to click Save button
  - Scenario names can still be manually edited
  - Validation rules for portfolio names remain unchanged
- Test coverage will include:
  - Unit tests for all naming utility functions
  - Integration tests for portfolio save dialog behavior
  - Integration tests for scenario creation and auto-naming
  - Tests for manual edit preservation
  - Tests for clone naming patterns

### File List

**New files to create:**
- `frontend/src/utils/naming.ts` — naming utility functions
- `frontend/src/utils/__tests__/naming.test.ts` — naming function tests

**Files to modify:**
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — portfolio save dialog auto-suggestion
- `frontend/src/contexts/AppContext.tsx` — scenario auto-naming and manual edit tracking
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` — add portfolio naming tests

**Files to verify (no changes expected):**
- `frontend/src/types/workspace.ts` — verify WorkspaceScenario type
- `frontend/src/data/mock-data.ts` — verify Template and Population types
- `frontend/src/utils/__tests__/` — verify test structure

---
**Story Status:** ready-for-dev
**Created:** 2026-03-30
**Epic:** 22 (UX Revision 3 Workspace Fit and Mobile Demo Viability)
