# Story 27.13: AppContext naming-state hardening

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a frontend developer maintaining scenario state,
I want the AppContext naming logic to handle create-from-scratch, clone, direct-field-mutation, and empty-populationIds restore correctly,
so that auto-name suggestions and the manual-edit freeze rule work in the four edge cases the 26.7 review flagged but did not fix.

## Background

**Current State Issues (from Story 26.7 Review):**

1. **`selectedPortfolioName` not reset on `createScenario`/`cloneScenario`**: When creating a new scenario or cloning, the global `selectedPortfolioName` state retains its previous value. This causes the auto-name effect to use stale UI state instead of deriving from the new scenario's `portfolioName` field.

2. **Loaded-name guard not invalidated on direct field mutation**: The auto-name guard at `AppContext.tsx:517-554` checks `manuallyEditedScenarioNames.has(activeScenario.id)` to prevent overwriting manual edits. However, when `portfolioName` or `populationIds` are mutated directly via `updateScenarioField()`, the guard doesn't recompute — it only rechecks on `activeScenario.id` changes in the deps.

3. **Empty `populationIds` invalidates loaded-name guard**: When a scenario is restored with `populationIds: []` (empty array), the default-selection effect at `AppContext.tsx:465-469` later sets `selectedPopulationId` to `populations[0].id`. This triggers the auto-name effect, which overwrites the restored scenario's name even though the user never explicitly chose that population.

4. **Auto-name effect dep self-retrigger**: The auto-name effect depends on `activeScenario.name` implicitly (through the equality check at line 540). When the effect updates the name, this would theoretically retrigger the effect, though React's batching prevents infinite loops. This creates unnecessary dependency complexity.

**Why This Matters:**

These edge cases break the deterministic naming contract introduced in Story 22.3 and Story 27.9. Users expect:
- Fresh scenarios to get names derived from their actual configuration, not previous UI state
- Manually edited names to stay frozen across scenario mutations
- Restored scenarios to preserve their names even if their population selection was empty
- Effects to be idempotent and converge without unnecessary re-renders

## Acceptance Criteria

1. **AC-1 (reset on create):** Given the analyst calls `createNewScenario()`, when a new scenario is created, then `selectedPortfolioName` is reset to `null` so stale UI state from a previous scenario doesn't seed the auto-name suggestion.
   - Rationale: `createNewScenario()` generates the name via `generateScenarioSuggestion(selectedPortfolioName, ...)` before the scenario's `portfolioName` field is set. If `selectedPortfolioName` carries over from a previous scenario, the new scenario gets a misleading name.
   - Current behavior: `selectedPortfolioName` persists across `createNewScenario()` calls (line 597-635).

2. **AC-2 (reset on clone):** Given the analyst calls `cloneCurrentScenario()`, when a clone is created, then `selectedPortfolioName` is reset to `null` and the clone uses the existing clone-naming pattern (e.g., "Original (copy)"), not a fresh auto-suggestion.
   - Rationale: Cloned scenarios should preserve their naming pattern; they don't need auto-suggestions since they already have a derived name.
   - Current behavior: `cloneCurrentScenario()` (line 637-661) doesn't reset `selectedPortfolioName`.

3. **AC-3 (guard invalidation on direct mutation):** Given the loaded-scenario name guard at `AppContext.tsx:517-528`, when `activeScenario.portfolioName` or `activeScenario.populationIds` is mutated via `updateScenarioField()`, then the auto-name effect recomputes the suggestion and the guard check runs again.
   - Rationale: `updateScenarioField()` allows direct mutation of scenario fields. If `portfolioName` changes from "My Portfolio" to null, or `populationIds` changes, the name suggestion should update (unless manually edited).
   - Current behavior: The effect only watches `activeScenario?.id` for guard validity (line 548), not the scenario fields that actually affect naming.

4. **AC-4 (empty populationIds restore):** Given a restored scenario with `populationIds: []`, when the default-selection effect (line 465-469) later sets `selectedPopulationId`, then the auto-name effect distinguishes "no selection yet" from "explicit selection" and doesn't auto-rename a freshly restored named scenario.
   - Rationale: Empty `populationIds` means "user hasn't picked a population yet." The default-selection effect is for UI convenience, not an explicit user choice. Auto-renaming on this implicit choice overwrites the restored scenario's curated name.
   - Current behavior: The effect treats `selectedPopulationId` changes the same whether from explicit user action or default selection, causing unwanted renames.

5. **AC-5 (effect dep optimization):** Given the auto-name effect at `AppContext.tsx:517-554`, when it updates the scenario name, then the effect uses functional `setActiveScenario((prev) => ...)` so `activeScenario.name` doesn't need to be in the dep array.
   - Rationale: The effect currently reads `activeScenario.name` for the equality check (line 540). When it updates the name, React's state update queuing prevents infinite loops, but the dependency is implicit and confusing. Using functional state setters makes the convergence explicit.
   - Current behavior: The effect doesn't depend on `activeScenario.name` directly (it's not in deps), but the read at line 540 creates a "lurking" dependency.

6. **AC-6 (integration tests):** Given `frontend/src/contexts/__tests__/AppContext.integration.test.tsx` is created, when this story is complete, then all four edge cases have integration test coverage and existing tests pass.

## Tasks / Subtasks

- [ ] Task 1: Reset `selectedPortfolioName` on create/clone (AC: #1, #2)
  - [ ] Subtask 1.1: In `AppContext.tsx`, update `createNewScenario()` (line 597-635) to call `setSelectedPortfolioName(null)` after setting the new scenario
  - [ ] Subtask 1.2: In `AppContext.tsx`, update `cloneCurrentScenario()` (line 637-661) to call `setSelectedPortfolioName(null)` after cloning
  - [ ] Subtask 1.3: Follow the existing pattern from `resetToDemo()` (line 582) and `loadFullDemo()` (line 592) which reset selectors
  - [ ] Subtask 1.4: Verify the reset happens before `navigateTo()` to avoid hash-change race conditions

- [ ] Task 2: Invalidate guard on direct field mutation (AC: #3)
  - [ ] Subtask 2.1: Review the auto-name effect guard at lines 517-528
  - [ ] Subtask 2.2: Add `activeScenario?.portfolioName` and `activeScenario?.populationIds` to the effect's dependency array (line 545-554)
  - [ ] Subtask 2.3: OR: Refactor the guard to check scenario fields directly instead of relying on `manuallyEditedScenarioNames` set
  - [ ] Subtask 2.4: Add effect cleanup to handle scenario ID changes (clear any pending name updates)

- [ ] Task 3: Handle empty populationIds restore (AC: #4)
  - [ ] Subtask 3.1: Add a `restoredFromStorage: boolean` flag to the effect's closure (tracked via ref)
  - [ ] Subtask 3.2: Set the flag to `true` in the initialization effect (line 329-361) when restoring from `loadScenario()`
  - [ ] Subtask 3.3: In the auto-name effect, skip the rename if `restoredFromStorage` is true AND the scenario has a non-default name
  - [ ] Subtask 3.4: Clear the flag after the first effect run (or after a timeout) so subsequent explicit population changes trigger renames
  - [ ] Subtask 3.5: Alternative: Add a `nameManuallySet` boolean field to `WorkspaceScenario` type

- [ ] Task 4: Tighten auto-name effect deps (AC: #5)
  - [ ] Subtask 4.1: Review the effect's dependency array (line 545-554) and the name read at line 540
  - [ ] Subtask 4.2: Refactor the effect to use functional state update: `setActiveScenario((prev) => prev ? { ...prev, name: suggestedName } : null)`
  - [ ] Subtask 4.3: Remove `activeScenario?.name` from any implicit dependencies (ensure it's not needed in deps)
  - [ ] Subtask 4.4: Verify the effect converges in one render using React DevTools Profiler or similar

- [ ] Task 5: Create integration test suite (AC: #6)
  - [ ] Subtask 5.1: Create `frontend/src/contexts/__tests__/AppContext.integration.test.tsx`
  - [ ] Subtask 5.2: Add test for AC-1: `createNewScenario()` resets `selectedPortfolioName` and generates correct name
  - [ ] Subtask 5.3: Add test for AC-2: `cloneCurrentScenario()` resets `selectedPortfolioName` and uses clone naming
  - [ ] Subtask 5.4: Add test for AC-3: `updateScenarioField("portfolioName", ...)` triggers guard re-evaluation
  - [ ] Subtask 5.5: Add test for AC-4: Restored scenario with empty `populationIds` keeps its name after default selection
  - [ ] Subtask 5.6: Use `renderHook` from `@testing-library/react` for hook testing pattern
  - [ ] Subtask 5.7: Mock the `useScenarioPersistence` functions to avoid localStorage in tests

- [ ] Task 6: Quality gates
  - [ ] Subtask 6.1: Run `npm test` — all tests pass including new integration tests
  - [ ] Subtask 6.2: Run `npm run typecheck` — no TypeScript errors
  - [ ] Subtask 6.3: Run `npm run lint` — no new lint errors
  - [ ] Subtask 6.4: Manual verification: create/clone scenarios and verify naming behavior

## Dev Notes

### Edge Case Details

The four edge cases deferred from Story 26.7 represent gaps in the AppContext naming state machine:

1. **Stale `selectedPortfolioName` on create/clone**:
   - `selectedPortfolioName` is transient UI state for the "Save Portfolio" dialog
   - `activeScenario.portfolioName` is the durable scenario field
   - When `createNewScenario()` generates a name, it calls `generateScenarioSuggestion(selectedPortfolioName, ...)` at line 599-605
   - If `selectedPortfolioName` still holds "Carbon Tax Portfolio" from the previous scenario, the new scenario gets "Carbon Tax Portfolio (FR Synthetic 2024)" instead of a fresh suggestion
   - Solution: Reset `selectedPortfolioName` to null in both `createNewScenario()` and `cloneCurrentScenario()`

2. **Guard not invalidated on direct mutation**:
   - The `manuallyEditedScenarioNames` Set tracks scenarios whose names were edited by the user
   - This guard prevents auto-renaming user-curated names
   - However, `updateScenarioField()` can change `portfolioName` or `populationIds` directly, which should trigger a re-evaluation
   - Current effect only watches `activeScenario?.id` for guard validity (line 548)
   - Solution: Add scenario fields to effect deps, or refactor guard to be field-aware

3. **Empty `populationIds` restore behavior**:
   - `loadSavedScenario()` at line 567-577 restores a scenario and syncs selectors
   - If the scenario has `populationIds: []`, line 574 doesn't call `setSelectedPopulationId`
   - Later, the default-selection effect (line 465-469) sets `selectedPopulationId` to `populations[0].id`
   - This change triggers the auto-name effect, overwriting the restored scenario's name
   - The key distinction: default selection is implicit, not an explicit user choice
   - Solution: Track "just restored" state and skip auto-rename for the first render after restore

4. **Effect dependency optimization**:
   - The effect reads `activeScenario.name` at line 540 for equality check
   - It updates `name` via `setActiveScenario()` at lines 541-543
   - React's state batching prevents infinite loops, but the dependency is implicit
   - Using functional state updater `setActiveScenario((prev) => ...)` makes convergence explicit
   - This removes the need to read `activeScenario.name` in the effect body

### Implementation Strategy

**Phase 1: Selector Reset (AC-1, AC-2)**
- Simple, low-risk changes following existing patterns
- `resetToDemo()` and `loadFullDemo()` already demonstrate the pattern
- Add `setSelectedPortfolioName(null)` to both functions
- Test with integration tests that verify selector state

**Phase 2: Guard Invalidation (AC-3)**
- More complex — requires understanding effect dependency semantics
- Two approaches:
  1. Add `activeScenario?.portfolioName` and `activeScenario?.populationIds` to deps
  2. Refactor guard to check scenario fields directly
- Approach 1 is simpler but may cause more effect runs
- Approach 2 requires careful state management to avoid double-triggers

**Phase 3: Restore Protection (AC-4)**
- Most subtle edge case — requires new state tracking
- Use a ref to track `isRestoring` flag
- Set flag in `loadSavedScenario()` before calling `setActiveScenario()`
- Check flag in auto-name effect; skip rename if flag is set
- Clear flag after effect runs (use `useRef` + `useEffect`)

**Phase 4: Effect Optimization (AC-5)**
- Refactor to use functional state update
- Remove implicit dependency on `activeScenario.name`
- Verify convergence with React DevTools

**Phase 5: Integration Tests (AC-6)**
- Create new test file since none exists
- Use `renderHook` pattern for AppContext testing
- Mock all API hooks and localStorage
- Test each edge case independently
- Verify no regressions in existing behavior

### Dependencies and Coordination

- **Story 27.6 (nav-rail "not started" state)**: Also touches the restore path. Story 27.6 adds `stageTouched` tracking and affects how scenarios are marked as "complete." Ensure both stories don't conflict on the initialization effect.
- **Story 27.9 (policy-set auto-name)**: Enhanced `generateScenarioSuggestion()` and `generatePortfolioSuggestion()`. Story 27.13 doesn't change these utilities — it focuses on when and how they're called.
- **Story 27.11 (portfolio dialog consolidation)**: Merged the three dialog hooks. This doesn't affect AppContext naming directly, but verify `selectedPortfolioName` is still the correct selector to reset.

### Testing Strategy

**Unit-level** (in `naming.test.ts`):
- Not needed for this story — naming utilities are already tested
- Focus on integration-level effects

**Integration-level** (new `AppContext.integration.test.tsx`):
1. Test `createNewScenario()` selector reset:
   - Set `selectedPortfolioName` to "Test Portfolio"
   - Call `createNewScenario()`
   - Assert `selectedPortfolioName` is null
   - Assert new scenario name doesn't include "Test Portfolio"

2. Test `cloneCurrentScenario()` selector reset:
   - Create scenario with portfolio
   - Set `selectedPortfolioName`
   - Call `cloneCurrentScenario()`
   - Assert selector reset and clone naming pattern

3. Test direct mutation guard invalidation:
   - Create scenario with portfolio "Portfolio A"
   - Manually edit name to "Custom Name"
   - Call `updateScenarioField("portfolioName", "Portfolio B")`
   - Assert name updates to new suggestion (or stays "Custom Name" if that's the spec)

4. Test empty populationIds restore:
   - Create scenario with name "My Scenario" and `populationIds: []`
   - Save to localStorage (mock)
   - Restore scenario
   - Trigger default population selection
   - Assert name stays "My Scenario"

**Regression tests**:
- Run all existing AppContext tests
- Run scenario persistence tests
- Run naming utility tests

### Code Locations

**Key files to modify:**
- `frontend/src/contexts/AppContext.tsx`:
  - Lines 597-635: `createNewScenario()`
  - Lines 637-661: `cloneCurrentScenario()`
  - Lines 517-554: Auto-name effect
  - Lines 465-469: Default population selection effect
  - Lines 329-361: Initialization effect

**Key files to create:**
- `frontend/src/contexts/__tests__/AppContext.integration.test.tsx`

**Related files (read-only context):**
- `frontend/src/utils/naming.ts`: `generateScenarioSuggestion()`, `generateScenarioCloneName()`
- `frontend/src/hooks/useScenarioPersistence.ts`: `loadScenario()`, `getManuallyEditedNames()`
- `frontend/src/data/demo-scenario.ts`: `DEMO_SCENARIO_ID`

### Project Structure Notes

- Files touched: `frontend/src/contexts/AppContext.tsx`
- Files created: `frontend/src/contexts/__tests__/AppContext.integration.test.tsx`
- No breaking changes to public API
- No new dependencies

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.13]
- [Source: _bmad-output/implementation-artifacts/27-0-close-out-26-7-review-patches-and-retro-epic-26.md] (deferred items lines 38-40)
- [Source: frontend/src/contexts/AppContext.tsx] (lines 517-554, 597-661)
- [Source: frontend/src/utils/naming.ts] (naming utilities)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via create-story workflow)

### Debug Log References

None — this is a new story creation.

### Completion Notes List

- Story file created with comprehensive developer context
- Enhanced from basic AC list with:
  - Detailed background explaining each edge case
  - Technical rationale for each acceptance criterion
  - Implementation strategy broken into phases
  - Testing strategy with specific test scenarios
  - Code locations and line number references
  - Coordination notes with related stories
- Ready for dev-story workflow to begin implementation

### File List

Modified:
- `_bmad-output/implementation-artifacts/27-13-appcontext-naming-state-hardening.md`

To be modified during implementation:
- `frontend/src/contexts/AppContext.tsx`
- `frontend/src/contexts/__tests__/AppContext.integration.test.tsx` (new)
