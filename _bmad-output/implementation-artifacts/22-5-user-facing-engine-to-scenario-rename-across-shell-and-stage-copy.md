# Story 22.5: User facing Engine to Scenario rename across shell and stage copy

Status: complete

## Story

As a policy analyst working in the ReformLab workspace,
I want the third stage to be labeled "Scenario" everywhere I see it in the UI,
so that the workspace language aligns with the scenario-centered model and is more intuitive.

## Acceptance Criteria

1. **[AC-1]** Given the shell, top bar, nav rail, screen headings, validation copy, and related aria labels, when inspected by a user, then the stage is labeled `Scenario` rather than `Engine`.
2. **[AC-2]** Given internal implementation details, when reviewed, then these internal `engine` identifiers remain unchanged: `StageKey = "engine"`, `activeStage = "engine"` state values, help lookup key `"engine"`, URL hash `#engine`, `engineConfig` type/properties, file names (EngineStageScreen.tsx), component names, folder name (engine/).
3. **[AC-3]** Given saved scenarios and local persistence state, when loaded after this change, then they remain compatible (no data migration needed).
4. **[AC-4]** Given existing tests and snapshots, when updated, then they validate the `Scenario` wording in user-facing assertions.

## Tasks / Subtasks

- [x] **Task 1: Update STAGES label in workspace.ts** (AC: 1)
  - [x] Change STAGES array entry from `{ key: "engine", label: "Engine", ... }` to `{ key: "engine", label: "Scenario", ... }`
  - [x] Verify this is the single source of truth for stage labels (no other "Engine" user-facing label definitions)

- [x] **Task 2: Update screen heading in EngineStageScreen** (AC: 1)
  - [x] Change heading from "Engine Configuration" to "Scenario Configuration" (line 192)
  - [x] Update JSDoc comment referencing "Engine Configuration" if present

- [x] **Task 3: Update help content for engine stage** (AC: 1)
  - [x] Change title from "Engine Configuration" to "Scenario Configuration" in help-content.ts
  - [x] Update "Getting Started" tip (line ~231): "Policies, Population, Engine, and Results" → "Policies, Population, Scenario, and Results"
  - [x] Update Save Scenario tip (line ~203): "portfolio + population + engine settings" → "portfolio + population + scenario settings"
  - [x] Keep the internal key "engine" unchanged (it's used for help content lookup)

- [x] **Task 4: Update component comments and validation messages** (AC: 1, 2)
  - [x] Change "Stage 3 (Engine)" comments to "Stage 3 (Scenario)" in ValidationGate.tsx
  - [x] Change "Stage 3 (Engine)" comments to "Stage 3 (Scenario)" in RunSummaryPanel.tsx
  - [x] Change JSDoc comment in EngineStageScreen.tsx from "Engine Configuration" to "Scenario Configuration"
  - [x] Change "Cross-stage validation check registry for the Engine preflight gate" to "...for the Scenario preflight gate" in validationChecks.ts (line 3)
  - [x] Change error message in validationChecks.ts (line 80): "No engine configuration." → "No scenario configuration."

- [x] **Task 5: Update test assertions** (AC: 4)
  - [x] Change EngineStageScreen.test.tsx assertion from "Engine Configuration" to "Scenario Configuration" (line 177)
  - [x] Change ContextualHelpPanel.test.tsx assertion from "Engine Configuration" to "Scenario Configuration" (line 26)
  - [x] Update describe block comments from "EngineStageScreen — Story 20.5" to keep existing format (no change to component name)

- [x] **Task 6: Verify compatibility and run tests** (AC: 3, 4)
  - [x] Run `npm test` to verify all component tests pass with new assertions
  - [x] Run grep to verify no user-facing "Engine" remains (excluding internal identifiers):
    ```bash
    grep -rn '\bEngine\b' frontend/src --include='*.tsx' --include='*.ts' | \
      grep -v 'engineConfig\|EngineConfig\|StageKey.*engine\|activeStage.*engine\|/#engine\|"engine".*:' | \
      grep -v '__tests__' | \
      # Review remaining matches for user-facing text
    ```
  - [x] Verify saved scenarios still load (no breaking changes to data structures)
  - [x] Run E2E tests to verify navigation still works with unchanged "engine" route key

- [x] **Task 7: Update E2E test comments** (AC: 2)
  - [x] Update section header comment in fixtures.ts (line 202): "// Engine configuration fixtures" → "// Scenario configuration fixtures"
  - [x] Update JSDoc descriptions in fixtures.ts (lines 206, 218, 230): "engine configuration" → "scenario configuration"
  - [x] Keep variable names unchanged (defaultEngineConfig, etc.) - internal identifiers only
  - [x] Update E2E test comments: "// Navigate to Engine stage" → "// Navigate to Scenario stage"
  - [x] Update E2E test comments: "// Navigate to engine and run" → "// Navigate to Scenario and run"

## Dev Notes

### Current Implementation Analysis

**Stage Label System:**
- The STAGES array in `frontend/src/types/workspace.ts` is the single source of truth for stage labels
- WorkflowNavRail, TopBar, and other navigation components derive labels from STAGES
- Only the `label` property needs to change; `key: "engine"` stays unchanged

**User-Facing "Engine" Locations Found:**
1. `frontend/src/types/workspace.ts` - STAGES array label: "Engine" → "Scenario"
2. `frontend/src/components/screens/EngineStageScreen.tsx` - Heading: "Engine Configuration" → "Scenario Configuration"
3. `frontend/src/components/help/help-content.ts` - Help entry title: "Engine Configuration" → "Scenario Configuration"
4. `frontend/src/components/help/help-content.ts` - Getting Started tip (line ~231): "Policies, Population, **Engine**, and Results" → "Policies, Population, **Scenario**, and Results"
5. `frontend/src/components/help/help-content.ts` - Save Scenario tip (line ~203): "**engine settings**" → "**scenario settings**"
6. `frontend/src/components/engine/validationChecks.ts` - Error message (line 80): "No **engine** configuration." → "No **scenario** configuration."

**Internal "engine" identifiers that MUST stay unchanged:**
- `StageKey = "engine"` type value
- `activeStage = "engine"` in routing and state
- `activeSubView` values (none for engine stage)
- File names: `EngineStageScreen.tsx`, `EngineStageScreen.test.tsx`
- Component names: `EngineStageScreen`
- Folder name: `frontend/src/components/engine/`
- URL hash fragment: `#engine` (if used in navigation)
- Internal keys in help-content.ts: `"engine"` key for help lookup

**Scope Boundaries:**
- IN SCOPE: User-visible text (labels, headings, help content, error messages, tips)
- IN SCOPE: Comments describing user-facing features
- OUT OF SCOPE: "computation engine" in documentation (refers to OpenFisca backend, not the stage)
- OUT OF SCOPE: File renames (too much churn for low value)
- OUT OF SCOPE: Route key changes (breaks URLs, no benefit)
- OUT OF SCOPE: Type name changes (breaks type contracts, no benefit)

### Testing Patterns

Per project context:
- Use Vitest for frontend tests
- Test file structure mirrors source
- Update assertions to match new "Scenario Configuration" text
- No data migration needed—stage key "engine" is unchanged

### Known Constraints and Gotchas

1. **Do NOT rename files** — `EngineStageScreen.tsx`, `EngineStageScreen.test.tsx`, and the `engine/` folder keep their names. The story explicitly allows internal `engine` identifiers.

2. **STAGES array is the source of truth** — Changing the label in `workspace.ts` automatically updates WorkflowNavRail and any other component that reads from STAGES. No changes needed to WorkflowNavRail.tsx itself.

3. **Help content internal key** — The key `"engine"` in `HELP_CONTENT` must remain unchanged because `getHelpEntry()` looks up help by stage key. Only change the `title` and any user-facing text in tips/concepts. Specific locations: Getting Started tip (line ~231), Save Scenario tip (line ~203).

4. **Test assertions** — Update specific text assertions:
   - EngineStageScreen.test.tsx line 177: `getByRole("heading", { name: /engine configuration/i })` → `/scenario configuration/i`
   - ContextualHelpPanel.test.tsx line 26: `getByText("Engine Configuration")` → "Scenario Configuration"

5. **E2E tests** — Only update comments. The internal navigation using `activeStage = "engine"` continues to work unchanged.

6. **Comments are low priority** — Component JSDoc comments mentioning "Engine" can be updated for consistency, but this is cosmetic and doesn't affect user experience.

7. **No persistence impact** — Since `StageKey = "engine"` is unchanged, saved scenarios and local state require no migration. The rename is display-layer only.

8. **Validation error message** — The error message in validationChecks.ts (line 80) is user-facing and must change from "No engine configuration." to "No scenario configuration."

9. **Grep verification required** — Use the grep command in Task 6 to verify no user-facing "Engine" instances remain. Expected false positives: engineConfig, EngineConfig, StageKey references, activeStage values, URL hashes, internal keys.

### Known False Positives (DO NOT CHANGE)

These contain "engine" but are NOT user-facing stage labels:
- `engineConfig` / `EngineConfig` - TypeScript type for scenario configuration
- `StageKey = "engine"` - Internal route key used in hash navigation
- `activeStage = "engine"` - State value for routing
- `"engine"` as object key in STAGES array (internal lookup key)
- `/#engine` in URL hash fragments (internal routing)
- `computation engine` in docs - refers to OpenFisca backend, not UI stage

### Component Naming Context

The component file `EngineStageScreen.tsx` was created in Story 20.5 when the stage was called "Engine".
File renames are explicitly out of scope for Story 22.5 to avoid unnecessary churn.
The component JSDoc should be updated to reflect the new user-facing name ("Scenario Configuration").

### References

- **Epic 22 definition:** `_bmad-output/planning-artifacts/epics.md#Epic-22`
- **UX Revision 3 spec:** `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md` — Change 6 (Engine to Scenario rename)
- **Story 22.1:** `_bmad-output/implementation-artifacts/22-1-shell-branding-external-links-and-scenario-entry-relocation.md` — Previous story for pattern reference
- **workspace.ts source:** `frontend/src/types/workspace.ts` — STAGES array (line ~122)
- **EngineStageScreen source:** `frontend/src/components/screens/EngineStageScreen.tsx`
- **help-content.ts source:** `frontend/src/components/help/help-content.ts`

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (via create-story workflow)

### Implementation Plan

**Phase 1: Core label change (Task 1)**
- Update STAGES array in workspace.ts from "Engine" to "Scenario"
- This automatically updates nav rail, top bar, and any component reading from STAGES

**Phase 2: Screen component update (Task 2)**
- Change heading in EngineStageScreen.tsx from "Engine Configuration" to "Scenario Configuration"

**Phase 3: Help content update (Task 3)**
- Update help-content.ts title from "Engine Configuration" to "Scenario Configuration"
- Update Getting Started tip: "Policies, Population, Engine, and Results" → "Policies, Population, Scenario, and Results"
- Update Save Scenario tip: "engine settings" → "scenario settings"
- Keep internal "engine" key unchanged for lookup compatibility

**Phase 4: Comment consistency and validation message (Task 4)**
- Update component JSDoc comments: ValidationGate, RunSummaryPanel, EngineStageScreen, validationChecks
- Update user-facing error message in validationChecks.ts: "No engine configuration." → "No scenario configuration."

**Phase 5: Test updates (Task 5)**
- Update text assertions in EngineStageScreen.test.tsx and ContextualHelpPanel.test.tsx

**Phase 6: Verification (Task 6)**
- Run all tests, verify compatibility
- Run grep command to verify no user-facing "Engine" remains (excluding internal identifiers)

**Phase 7: E2E comments (Task 7)**
- Update descriptive comments in E2E tests and fixtures

### Debug Log References

Analysis completed from source files:
- `frontend/src/types/workspace.ts` — STAGES array definition
- `frontend/src/components/screens/EngineStageScreen.tsx` — "Engine Configuration" heading
- `frontend/src/components/help/help-content.ts` — Help content with "Engine Configuration" title, Getting Started tip, Save Scenario tip
- `frontend/src/components/engine/validationChecks.ts` — User-facing error message "No engine configuration."
- `frontend/src/components/screens/__tests__/EngineStageScreen.test.tsx` — Test assertions
- `frontend/src/components/help/__tests__/ContextualHelpPanel.test.tsx` — Help content test assertions
- `frontend/src/components/engine/ValidationGate.tsx` — Component comments
- `frontend/src/components/engine/RunSummaryPanel.tsx` — Component comments
- `frontend/src/components/engine/validationChecks.ts` — Validation registry comments
- `frontend/src/__tests__/e2e/fixtures.ts` — Test fixtures with "Engine" comments
- E2E tests with "Engine" references in comments

### Completion Notes List

- Story 22.5 is a pure text rename with no structural code changes
- All user-facing "Engine" text changes to "Scenario" (labels, headings, help content, error messages, tips)
- All internal "engine" identifiers (route keys, file names, type names) remain unchanged
- Validation error message updated: "No engine configuration." → "No scenario configuration."
- No data migration required—stage key "engine" is preserved
- Tests updated to assert "Scenario Configuration" instead of "Engine Configuration"
- Grep verification step added to ensure no user-facing "Engine" remains
- **Additional files updated during implementation:**
  - `WorkflowNavRail.tsx` — JSDoc comment updated for workflow description
  - `DimensionRegistry.tsx` — Label and description updated for engine dimension (user-facing display text)
- **Story created:** 2026-03-30
- **Story completed:** 2026-03-30
- **Epic:** 22 (UX Revision 3 Workspace Fit and Mobile Demo Viability)

### File List

**Files modified (user-facing text changes):**
- `frontend/src/types/workspace.ts` — STAGES array label: "Engine" → "Scenario"
- `frontend/src/components/screens/EngineStageScreen.tsx` — Heading and JSDoc: "Engine Configuration" → "Scenario Configuration"
- `frontend/src/components/help/help-content.ts` — Help title and tips updated
- `frontend/src/components/engine/validationChecks.ts` — Error message and JSDoc updated
- `frontend/src/components/layout/WorkflowNavRail.tsx` — JSDoc comment updated
- `frontend/src/components/comparison/DimensionRegistry.tsx` — Label and description updated
- `frontend/src/components/screens/__tests__/EngineStageScreen.test.tsx` — Test assertion updated
- `frontend/src/components/help/__tests__/ContextualHelpPanel.test.tsx` — Test assertion updated

**Files modified (comment consistency):**
- `frontend/src/components/engine/ValidationGate.tsx` — JSDoc comment updated
- `frontend/src/components/engine/RunSummaryPanel.tsx` — JSDoc comment updated
- `frontend/src/__tests__/e2e/fixtures.ts` — Fixture comments updated
- `frontend/src/__tests__/e2e/portfolio-workflow.test.tsx` — Descriptive comments updated
- `frontend/src/__tests__/e2e/population-workflow.test.tsx` — Descriptive comments updated

**Files NOT modified (internal identifiers stay as "engine"):**
- Route keys, type names, file names, folder names all remain unchanged
- `StageKey = "engine"` type value preserved
- URL hash fragments (#engine) preserved
- Component class/function names preserved

---
**Story Status:** complete
**Created:** 2026-03-30
**Completed:** 2026-03-30
