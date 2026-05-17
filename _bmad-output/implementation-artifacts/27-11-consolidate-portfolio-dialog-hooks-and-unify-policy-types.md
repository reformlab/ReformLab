# Story 27.11: Consolidate portfolio dialog hooks and unify policy types

Status: done

## Story

As a frontend developer maintaining policy-set workflows,
I want the three portfolio dialog hooks (save, load, clone) merged into one, the divergent policy type formats normalized throughout the frontend, and deprecated exports cleaned up,
so that future changes to portfolio dialog behavior land in one file, the codebase doesn't scatter `.replace(/-/g, "_")` conversions, and type inconsistencies are eliminated.

## Background

**Current State Issues:**

1. **Three separate portfolio dialog hooks** with duplicated patterns:
   - `usePortfolioSaveDialog` - handles save/update flow (188 lines)
   - `usePortfolioLoadDialog` - handles load/autoload flow (189 lines)
   - `usePortfolioCloneDialog` - handles clone flow (93 lines)
   - All share: dialog state management, toast notifications, loading states, portfolio ref management

2. **Policy type format divergence** with scattered conversions:
   - `Template.type` uses kebab-case: `"carbon-tax"`, `"subsidy"`, `"feebate"`
   - `PortfolioPolicyItem.policy_type` uses snake_case: `"carbon_tax"`, `"subsidy"`
   - `CreateBlankPolicyRequest.policy_type` uses lowercase: `"tax"`, `"subsidy"`, `"transfer"`
   - Inline `.replace(/-/g, "_")` conversions in 5+ locations:
     - `usePortfolioSaveDialog.ts:46`
     - `usePortfolioLoadDialog.ts:66`
     - `PoliciesStageScreen.tsx:552`
     - `PortfolioDesignerScreen.tsx:209,267,318`
   - `TYPE_LABELS` and `TYPE_COLORS` have duplicate entries for both formats

3. **Deprecated exports** lingering from previous refactors:
   - `useScenarioPersistence.ts` has deprecated hook export (lines 232-255: the `ScenarioPersistence` interface and `useScenarioPersistence()` function)
   - `PortfolioDesignerScreen.tsx` is unreachable dead code (deprecated since Story 20.3, not referenced in routing) with inline `validatePortfolioName` duplicate (lines 93-104)

## Acceptance Criteria

1. **AC-1 (unified dialog hook):** Given the new `usePortfolioDialog` hook with `mode: "save" | "load" | "clone"`, when imported with any mode, then it returns the appropriate dialog state and handlers matching the previous three separate hooks.
2. **AC-2 (hook consolidation - PoliciesStageScreen):** Given `PoliciesStageScreen.tsx` uses the unified hook, when all three dialog flows are exercised, then behavior is identical to before with shorter wiring and a single source of error-handling logic. Specific test scenarios:
   - Save flow: open dialog → enter name → save → verify portfolio created with identical name and policies as before
   - Load flow: open dialog → select portfolio → load → verify composition updated identically
   - Clone flow: open dialog → enter name → clone → verify new portfolio created with identical policies
   - Error handling: API errors show toasts identically; autoload failures remain silent (no toast)
3. **AC-3 (policy type normalization utility):** Given a `normalizePolicyType()` utility function, when called with any policy type format, then it returns snake_case (canonical): `normalizePolicyType("carbon-tax")` → `"carbon_tax"`, `normalizePolicyType("carbon_tax")` → `"carbon_tax"`, `normalizePolicyType("tax")` → `"tax"`.
4. **AC-4 (policy type constants unified):** Given `typeConstants.ts`, when updated, then `TYPE_LABELS` and `TYPE_COLORS` use only snake_case keys and duplicate kebab-case entries are removed.
5. **AC-5 (inline conversions replaced):** Given the codebase, when searched for `.replace(/-/g, "_")` in portfolio-related code, then all occurrences are replaced with `normalizePolicyType()` calls.
6. **AC-6 (type unification - CompositionEntry):** Given `frontend/src/api/types.ts`, when updated, then:
   - `PortfolioPolicyItem` remains unchanged (backend API type)
   - `CompositionEntry` extends `PortfolioPolicyItem` with UI-only fields: `instanceId`, `templateId`, `editableParameterGroups`, `category_id`, `parameter_groups`
   - JSDoc on `CompositionEntry` explains it's the UI composition layer over `PortfolioPolicyItem`
   - The circular-import risk from `PortfolioCompositionPanel.tsx` is resolved (import path now one-way: api/types → PortfolioCompositionPanel)
7. **AC-7 (deprecated exports removed):** Given `useScenarioPersistence.ts`, when this story is complete, then the deprecated hook export (lines 232-255 (the `ScenarioPersistence` interface and `useScenarioPersistence()` function, both `@deprecated`)) is removed and only the module-level functions remain.
8. **AC-8 (PortfolioDesignerScreen cleanup):** Given `PortfolioDesignerScreen.tsx` is confirmed unreachable (deprecated since Story 20.3, not referenced in routing), when deleted with its tests, then dead code is removed and no portfolio dialog functionality is lost.
9. **AC-9 (comprehensive tests):** Given the consolidated hook and policy type utilities, when tests run, then `usePortfolioDialog.test.ts` covers all three modes and `policyTypes.test.ts` covers normalization edge cases.
10. **AC-10 (LOC reduction):** Given before/after LOC measurement, when compared, then the consolidation achieves net reduction of ~100 lines (with ~250 lines removed from old hooks and ~150 lines added for new unified hook and tests) without losing functional coverage.

## Tasks / Subtasks

- [ ] Task 1: Create policy type normalization utilities (AC: #3, #4, #5)
  - [ ] Subtask 1.1: Create `frontend/src/utils/policyTypes.ts` with `normalizePolicyType()` function
  - [ ] Subtask 1.2: Add JSDoc explaining kebab-case ↔ snake_case conversion and canonical format choice (snake_case = backend format)
  - [ ] Subtask 1.3: Update `typeConstants.ts` to remove duplicate kebab-case keys from `TYPE_LABELS` and `TYPE_COLORS`
  - [ ] Subtask 1.4: Add `normalizePolicyType` unit tests covering: kebab-case input, snake_case input (no-op), lowercase fundamental types, edge cases (null/undefined/empty)
  - [ ] Subtask 1.5: Add tests for `TYPE_LABELS` and `TYPE_COLORS` ensuring all keys are snake_case

- [ ] Task 2: Replace inline policy type conversions (AC: #5)
  - [ ] Subtask 2.1: Update `usePortfolioSaveDialog.ts:46` to use `normalizePolicyType()`
  - [ ] Subtask 2.2: Update `usePortfolioLoadDialog.ts:66` to use `normalizePolicyType()`
  - [ ] Subtask 2.3: Update `PoliciesStageScreen.tsx:552` to use `normalizePolicyType()`
  - [ ] Subtask 2.4: Update `PortfolioDesignerScreen.tsx:209,267,318` to use `normalizePolicyType()`
  - [ ] Subtask 2.5: Update `PolicyCard.tsx:509` to use `normalizePolicyType()` in the type comparison
  - [ ] Subtask 2.6: Verify no other `.replace(/-/g, "_")` conversions remain in portfolio-related code (grep check)

- [ ] Task 3: Design unified hook signature (AC: #1, #2)
  - [ ] Subtask 3.1: Define `PortfolioDialogMode = "save" | "load" | "clone"` type
  - [ ] Subtask 3.2: Design discriminated union return types for mode-specific dialog state
  - [ ] Subtask 3.3: Document error-handling policy (passive autoload silent, explicit user actions toast)

- [ ] Task 4: Implement unified hook (AC: #1, #2)
  - [ ] Subtask 4.1: Create `frontend/src/hooks/usePortfolioDialog.ts`
  - [ ] Subtask 4.2: Extract common dialog state patterns (open/close, loading, toast)
  - [ ] Subtask 4.3: Implement save mode with all existing functionality (name suggestion, manual edit freeze, draft clearing)
  - [ ] Subtask 4.4: Implement load mode with all existing functionality (autoload, draft clearing, error handling)
  - [ ] Subtask 4.5: Implement clone mode with all existing functionality (name generation, validation)
  - [ ] Subtask 4.6: Add backward compatibility re-exports in old hook files

- [ ] Task 5: Migrate consumers to unified hook (AC: #2)
  - [ ] Subtask 5.1: Verify hook consumer scope BEFORE development: run `grep -rn "usePortfolio(Save|Load|Clone)Dialog" frontend/src --exclude-dir=__tests__` and document findings (expected: `PoliciesStageScreen.tsx` is primary consumer)
  - [ ] Subtask 5.2: Update `PoliciesStageScreen.tsx` to use `usePortfolioDialog` with mode parameter
  - [ ] Subtask 5.3: If additional consumers found in Subtask 5.1, update them to use the unified hook
  - [ ] Subtask 5.4: Verify all three dialog flows work identically via integration tests in `PoliciesStageScreen.test.tsx` (save→create, load→update, clone→duplicate)

- [ ] Task 6: Unify policy types in type system (AC: #6)
  - [ ] Subtask 6.1: In `frontend/src/api/types.ts`, ensure `PortfolioPolicyItem` is the canonical portfolio policy type
  - [ ] Subtask 6.2: Move `CompositionEntry` from `PortfolioCompositionPanel.tsx` to `frontend/src/api/types.ts`
  - [ ] Subtask 6.3: Define `CompositionEntry` as extending `PortfolioPolicyItem` with UI-only fields (instanceId, templateId, editableParameterGroups) and add JSDoc explaining it's the UI composition layer
  - [ ] Subtask 6.4: Update `portfolioValidation.ts` import of `CompositionEntry` from `PortfolioCompositionPanel` to `@/api/types`
  - [ ] Subtask 6.5: Update conversion logic in unified hook to set `instanceId`/`templateId` without field name translation

- [ ] Task 7: Remove deprecated exports and clean up (AC: #7, #8)
  - [ ] Subtask 7.1: In `useScenarioPersistence.ts`, remove deprecated hook export (lines 232-255: the `ScenarioPersistence` interface and `useScenarioPersistence()` function, both `@deprecated`)
  - [ ] Subtask 7.2: Audit remaining imports of deprecated export; update tests to use module-level functions
  - [ ] Subtask 7.3: Delete `PortfolioDesignerScreen.tsx` and `PortfolioDesignerScreen.test.tsx` (confirmed unreachable since Story 20.3: file header says `@deprecated … is no longer used in routing` and no routing references exist)

- [ ] Task 8: Consolidate and update tests (AC: #9)
  - [ ] Subtask 8.1: Create `frontend/src/hooks/__tests__/usePortfolioDialog.test.ts`
  - [ ] Subtask 8.2: Add tests for save mode: name suggestion, manual edit freeze, draft clearing, validation
  - [ ] Subtask 8.3: Add tests for load mode: autoload, draft clearing, error handling
  - [ ] Subtask 8.4: Add tests for clone mode: name generation, duplicate validation, error handling
  - [ ] Subtask 8.5: Verify `usePortfolioSaveDialog.nameFreeze.test.ts` continues to pass via the backward-compat wrapper (these tests import the old hook and must still work)
  - [ ] Subtask 8.6: Add type-system test verifying `CompositionEntry` relationship to `PortfolioPolicyItem`

- [ ] Task 9: Quality gates and LOC measurement (AC: #10)
  - [ ] Subtask 9.1: Run `npm test` - all tests must pass
  - [ ] Subtask 9.2: Run `npm run typecheck` - no type errors
  - [ ] Subtask 9.3: Run `npm run lint` - no new warnings
  - [ ] Subtask 9.4: Run portfolio workflow E2E tests to verify dialog behavior unchanged
  - [ ] Subtask 9.5: Measure before/after LOC for affected files; record in PR description

## Dev Notes

### Architecture Patterns

- **Hook consolidation**: Use discriminated unions for mode-specific return types to maintain type safety while allowing a single hook
- **Policy type canonical format**: Backend API uses snake_case (`carbon_tax`), frontend `Template` type uses kebab-case (`carbon-tax`). Normalize to snake_case as single source of truth
- **Error handling policy**: Per `feedback_error_toasts_user_initiated_only.md`, passive/autoload operations fail silently; explicit user-initiated actions show toasts
- **Backward compatibility**: Re-export pattern allows gradual migration without breaking existing imports during transition

### Policy Type Normalization Specification

**normalizePolicyType(type: string | null | undefined): string**
```typescript
/**
 * Normalize a policy type to the canonical snake_case format used by the backend API.
 *
 * Handles three formats in the codebase:
 * - Kebab-case (Template.type): "carbon-tax" → "carbon_tax"
 * - Snake_case (PortfolioPolicyItem.policy_type): "carbon_tax" → "carbon_tax" (no-op)
 * - Lowercase fundamental types (CreateBlankPolicyRequest): "tax" → "tax" (no-op)
 *
 * @example normalizePolicyType("carbon-tax") // "carbon_tax"
 * @example normalizePolicyType("carbon_tax") // "carbon_tax"
 * @example normalizePolicyType("tax") // "tax"
 * @example normalizePolicyType(null) // ""
 */
export function normalizePolicyType(type: string | null | undefined): string {
  if (!type) return "";
  // Convert kebab-case to snake_case, leave other formats unchanged
  return type.replace(/-/g, "_");
}
```

**typeConstants.ts updates:**
Remove duplicate kebab-case entries, keep only snake_case:
```typescript
// BEFORE (with duplicates):
export const TYPE_LABELS: Record<string, string> = {
  "carbon-tax": "Carbon Tax",  // REMOVE
  "carbon_tax": "Carbon Tax",  // KEEP
  "subsidy": "Subsidy",        // KEEP
  // ...
};

// AFTER (canonical snake_case only):
export const TYPE_LABELS: Record<string, string> = {
  "carbon_tax": "Carbon Tax",
  "subsidy": "Subsidy",
  "rebate": "Rebate",
  "feebate": "Feebate",
  "vehicle_malus": "Vehicle Malus",
  "energy_poverty_aid": "Energy Poverty Aid",
  "tax": "Tax",
  "transfer": "Transfer",
};
```

### Hook Consolidation Pattern

**Use discriminated unions for type-safe mode-specific returns:**
```typescript
type PortfolioDialogMode = "save" | "load" | "clone";

// INPUT discriminated union (mirrors output):
type PortfolioDialogParams =
  | {
      mode: "save";
      templates: Template[];
      composition: CompositionEntry[];
      resolutionStrategy: string;
      conflicts: PortfolioConflict[];
      loadedPortfolioRef: { current: string | null };
      setActivePortfolioName: (name: string | null) => void;
      updateScenarioPortfolioName: (name: string | null) => void;
      setSelectedPortfolioName: (name: string | null) => void;
      refetchPortfolios: () => Promise<void>;
      onSavedSuccessfully?: () => void;
      categories?: Category[] | null;
    }
  | {
      mode: "load";
      templates: Template[];
      activeScenarioPortfolioName: string | null | undefined;
      compositionLength: number;
      validStrategies: readonly string[];
      defaultResolutionStrategy: string;
      loadedPortfolioRef: { current: string | null };
      setComposition: (composition: CompositionEntry[]) => void;
      setResolutionStrategy: (strategy: string) => void;
      setActivePortfolioName: (name: string | null) => void;
      updateScenarioPortfolioName: (name: string | null) => void;
      setSelectedPortfolioName: (name: string | null) => void;
      setInstanceCounter?: (value: number) => void;
      onLoadedSuccessfully?: () => void;
    }
  | {
      mode: "clone";
      portfolios: PortfolioListItem[];
      refetchPortfolios: () => Promise<void>;
    };

// RETURN discriminated union:
interface SaveDialogState {
  mode: "save";
  saveDialogOpen: boolean;
  portfolioSaveName: string;
  portfolioSaveDesc: string;
  saveNameError: string | null;
  saving: boolean;
  openSaveDialog: () => void;
  closeSaveDialog: () => void;
  handleSaveNameChange: (name: string) => void;
  setPortfolioSaveDesc: (desc: string) => void;
  handleSave: () => Promise<void>;
}

interface LoadDialogState {
  mode: "load";
  loadDialogOpen: boolean;
  openLoadDialog: () => void;
  closeLoadDialog: () => void;
  handleLoad: (name: string) => Promise<boolean>;
}

interface CloneDialogState {
  mode: "clone";
  cloneDialogOpen: boolean;
  cloneDialogName: string | null;
  cloneNewName: string;
  cloneNameError: string | null;
  cloning: boolean;
  openCloneDialog: (name: string) => void;
  closeCloneDialog: () => void;
  handleCloneNameChange: (name: string) => void;
  handleClone: () => Promise<void>;
}

type PortfolioDialogState =
  | SaveDialogState
  | LoadDialogState
  | CloneDialogState;

export function usePortfolioDialog<T extends PortfolioDialogMode>(
  mode: T,
  params: Omit<PortfolioDialogParams & { mode: T }, "mode">,
): PortfolioDialogState {
  // Implementation returns discriminated union based on mode
}

// Usage in PoliciesStageScreen (three separate calls, NOT conditional):
const saveState = usePortfolioDialog("save", { templates, composition, ... });
const loadState = usePortfolioDialog("load", { templates, activeScenarioPortfolioName, ... });
const cloneState = usePortfolioDialog("clone", { portfolios, refetchPortfolios });
```

**Architecture Note:** Discriminated unions for mode-specific returns are an intentional exception to the project's protocol-driven pattern because: (1) mode-specific return types have EXCLUSIVE state (only one dialog open at a time), (2) type safety is more valuable than flexibility for this internal hook, and (3) external consumers don't implement these types (not a public API).

### Type Unification Strategy

**Move CompositionEntry to api/types.ts:**
```typescript
// In frontend/src/api/types.ts:

/** Portfolio policy item from backend API */
export interface PortfolioPolicyItem {
  name: string;
  policy_type: string;
  rate_schedule: Record<string, number>;
  parameters: Record<string, unknown>;
  // ... other fields
}

/** Composition entry extends portfolio policy with UI-only fields */
export interface CompositionEntry extends PortfolioPolicyItem {
  instanceId: string;
  templateId: string;
  editableParameterGroups?: EditableParameterGroup[];
  // Story 25.3: Optional from-scratch policy fields
  category_id?: string;
  parameter_groups?: string[];
}
```

This resolves the circular-import risk noted in `deferred-work.md` by moving `CompositionEntry` to a shared location.

**Circular Import Resolution:**

BEFORE (circular risk):
```
PortfolioCompositionPanel → defines CompositionEntry
PortfolioCompositionPanel → imports EditableParameterGroup from api/types
[If api/types tried to import CompositionEntry, would create cycle]
```

AFTER (clean one-way dependency):
```
api/types → exports CompositionEntry (moved)
api/types → exports EditableParameterGroup (existing)
PortfolioCompositionPanel → imports CompositionEntry from api/types
PortfolioCompositionPanel → imports EditableParameterGroup from api/types
portfolioValidation.ts → imports CompositionEntry from api/types (updated from PortfolioCompositionPanel)
Result: No circular dependency, clear layering (types.ts → components)
```

### Integration Points

- **PoliciesStageScreen**: Primary consumer of all three hooks; will switch to unified hook with mode parameter
- **AppContext**: May need updates if portfolio dialog state is referenced
- **useCompositionDraft**: Integration with draft clearing callbacks preserved (Story 27.5 dependency)
- **PolicyCard**: Verifies type display works with normalized policy types

### Backward Compatibility Strategy

Old hook files become thin wrapper functions for backward compatibility:
```typescript
// usePortfolioSaveDialog.ts (after refactoring)
import { usePortfolioDialog } from './usePortfolioDialog';

/** @deprecated Use `usePortfolioDialog({ mode: "save", ... })` directly. */
export function usePortfolioSaveDialog(params: Omit<SaveDialogParams, "mode">) {
  return usePortfolioDialog({ mode: "save", ...params });
}

// usePortfolioLoadDialog.ts (after refactoring)
import { usePortfolioDialog } from './usePortfolioDialog';

/** @deprecated Use `usePortfolioDialog({ mode: "load", ... })` directly. */
export function usePortfolioLoadDialog(params: Omit<LoadDialogParams, "mode">) {
  return usePortfolioDialog({ mode: "load", ...params });
}

// usePortfolioCloneDialog.ts (after refactoring)
import { usePortfolioDialog } from './usePortfolioDialog';

/** @deprecated Use `usePortfolioDialog({ mode: "clone", ... })` directly. */
export function usePortfolioCloneDialog(params: Omit<CloneDialogParams, "mode">) {
  return usePortfolioDialog({ mode: "clone", ...params });
}
```

Benefits:
1. Zero breaking changes for consumers during transition
2. Existing tests (e.g., `usePortfolioSaveDialog.nameFreeze.test.ts`) continue to pass
3. Gradual migration at importer's convenience
4. JSDoc `@deprecated` tags signal migration path
5. Future deprecation: remove old hooks in EPIC-28 or after 2 production releases

### Testing Strategy

1. **Unit tests for policy type normalization**:
   - All known format conversions (kebab-case, snake_case, lowercase)
   - Edge cases (null, undefined, empty string)
   - Idempotency (running twice produces same result)

2. **Hook tests per mode**:
   - Save mode: name suggestion with type/category context, manual edit freeze, draft clearing, validation errors
   - Load mode: autoload on mount with empty composition, draft clearing, error handling
   - Clone mode: name generation, duplicate name validation, success/error handling

3. **Integration tests**:
   - PoliciesStageScreen interaction tests verify dialog behavior
   - Type-system test (compile-time): `CompositionEntry` relationship to `PortfolioPolicyItem`

4. **E2E tests**:
   - Portfolio workflow tests verify save/load/clone still work end-to-end

### Edge Cases

1. **Empty or null policy types**: `normalizePolicyType` returns empty string; consuming code handles display
2. **Unknown policy types**: `TYPE_LABELS` and `TYPE_COLORS` should have fallback for unknown types (display raw value)
3. **Dialog state persistence**: Ensure dialog state doesn't leak between modes (only one dialog open at a time)
4. **Concurrent dialog operations**: Existing behavior preserved (opening one dialog closes any other)

### Migration Notes

- **Prior context**: Stories 27.4 and 27.5 are already completed. This story refactors the functionality they introduced — no blocking dependency, just implementation context for understanding the base code
- **Future cleanup**: Consider removing the old hook files entirely in a future breaking-change release after this has been in production for a while
- **PortfolioDesignerScreen**: If reachable from routing, it should also use the unified hook; otherwise delete it
- **Type import cleanup**: After moving `CompositionEntry` to `api/types.ts`, update imports throughout the codebase

### Toast Policy Reference

Per `feedback_error_toasts_user_initiated_only.md`:
- **Passive/autoload operations**: Fail silently (no toasts)
  - `usePortfolioLoadDialog` autoload effect
  - Draft restoration failures
- **Explicit user-initiated actions**: Show toasts
  - Save button clicks
  - Load button clicks
  - Clone button clicks
  - Dialog open actions

This consolidated hook must maintain this policy for all three modes.

### Project Structure Notes

**New files:**
- `frontend/src/utils/policyTypes.ts` - Policy type normalization utilities
- `frontend/src/utils/__tests__/policyTypes.test.ts` - Policy type utility tests
- `frontend/src/hooks/usePortfolioDialog.ts` - Unified portfolio dialog hook
- `frontend/src/hooks/__tests__/usePortfolioDialog.test.ts` - Consolidated hook tests

**Modified files:**
- `frontend/src/hooks/usePortfolioSaveDialog.ts` - Becomes thin wrapper function for backward compatibility (5-10 lines)
- `frontend/src/hooks/usePortfolioLoadDialog.ts` - Becomes thin wrapper function for backward compatibility (5-10 lines)
- `frontend/src/hooks/usePortfolioCloneDialog.ts` - Becomes thin wrapper function for backward compatibility (5-10 lines)
- `frontend/src/components/simulation/typeConstants.ts` - Remove duplicate kebab-case entries from TYPE_LABELS/TYPE_COLORS
- `frontend/src/components/screens/PoliciesStageScreen.tsx` - Use unified hook with mode parameter
- `frontend/src/api/types.ts` - Move CompositionEntry here; clarify relationship to PortfolioPolicyItem
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` - Remove CompositionEntry export (moved to api/types.ts)
- `frontend/src/hooks/useScenarioPersistence.ts` - Remove deprecated hook export (lines 232-255 (the `ScenarioPersistence` interface and `useScenarioPersistence()` function, both `@deprecated`))
- `frontend/src/components/screens/PortfolioDesignerScreen.tsx` - DELETE (confirmed unreachable)
- `frontend/src/components/simulation/PolicyCard.tsx` - Update type comparison at line 509 to use `normalizePolicyType()`

**Test files modified:**
- `frontend/src/hooks/__tests__/usePortfolioSaveDialog.nameFreeze.test.ts` - Verify continues to pass via backward-compat wrapper
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` - Update hook imports
- Any E2E tests that reference the three hooks by name

**Files to delete:**
- `frontend/src/components/screens/PortfolioDesignerScreen.tsx` (confirmed unreachable)
- `frontend/src/components/screens/__tests__/PortfolioDesignerScreen.test.tsx` (confirmed unreachable)

**Deprecated files (backward compatibility wrappers):**
After migration is complete, these files become thin wrapper functions:
- `frontend/src/hooks/usePortfolioSaveDialog.ts` (~5-10 lines: wrapper function with @deprecated JSDoc)
- `frontend/src/hooks/usePortfolioLoadDialog.ts` (~5-10 lines: wrapper function with @deprecated JSDoc)
- `frontend/src/hooks/usePortfolioCloneDialog.ts` (~5-10 lines: wrapper function with @deprecated JSDoc)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-27.11]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.11]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md] (circular-import risk, deprecated exports)
- [Source: frontend/src/hooks/usePortfolioSaveDialog.ts] - Save dialog hook (188 lines) to consolidate
- [Source: frontend/src/hooks/usePortfolioLoadDialog.ts] - Load dialog hook (189 lines) to consolidate
- [Source: frontend/src/hooks/usePortfolioCloneDialog.ts] - Clone dialog hook (93 lines) to consolidate
- [Source: frontend/src/components/simulation/typeConstants.ts] - Type labels/colors with duplicate entries for kebab-case and snake_case
- [Source: frontend/src/components/screens/PoliciesStageScreen.tsx] - Primary consumer of all three hooks
- [Source: frontend/src/api/types.ts] - PortfolioPolicyItem, future home of CompositionEntry
- [Source: frontend/src/components/simulation/PortfolioCompositionPanel.tsx] - Current location of CompositionEntry (circular-import risk)
- [Source: frontend/src/hooks/useScenarioPersistence.ts] - Deprecated hook export at lines 232-255 (the `ScenarioPersistence` interface and `useScenarioPersistence()` function, both `@deprecated`)
- [Source: frontend/src/components/screens/PortfolioDesignerScreen.tsx] - Dead code (deprecated since Story 20.3, unreachable) with inline validatePortfolioName duplicate at lines 93-104
- [Source: Story 27.4] - Unified policy card visuals (already completed; provides context for this refactoring)
- [Source: Story 27.5] - Auto-save draft (already completed; provides context for draft clearing integration)
- [Source: feedback_error_toasts_user_initiated_only.md] - Toast policy reference

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (via BMad create-story workflow)

### Debug Log References

### Completion Notes List

**Story context enhanced:**
- Added comprehensive background on three separate issues: hook duplication, policy type divergence, deprecated exports
- Documented 5+ locations with inline `.replace(/-/g, "_")` conversions that need normalization utility
- Specified discriminated union pattern for type-safe mode-specific hook returns
- Added detailed normalization function specification with JSDoc examples
- Documented TYPE_LABELS/TYPE_COLORS cleanup (remove duplicate kebab-case entries)
- Added toast policy reference for error handling (silent autoload, toasts for user actions)
- Included backward compatibility strategy via re-export pattern
- Added comprehensive testing strategy (unit, integration, E2E, type-system)

**Implementation specifications provided:**
- `normalizePolicyType()` utility function with exact signature and behavior
- `usePortfolioDialog` discriminated union return types for each mode
- `typeConstants.ts` before/after for duplicate key removal
- `CompositionEntry` move to `api/types.ts` to resolve circular-import risk
- Backward compatibility re-export pattern for gradual migration

**Task breakdown enhanced:**
- 9 comprehensive tasks with 45+ subtasks covering all aspects
- Hook consolidation (design, implementation, consumer migration)
- Policy type normalization (utility, constants, inline conversions)
- Type system unification (CompositionEntry move, relationship clarification)
- Deprecated export removal (useScenarioPersistence, PortfolioDesignerScreen)
- Test consolidation and LOC measurement

**AC Validation:**
- AC-1 ✓: Unified hook with mode parameter
- AC-2 ✓: PoliciesStageScreen migration with shorter wiring
- AC-3 ✓: normalizePolicyType utility specification
- AC-4 ✓: TYPE_LABELS/TYPE_COLORS cleanup
- AC-5 ✓: Replace inline conversions
- AC-6 ✓: CompositionEntry type unification
- AC-7 ✓: Remove deprecated hook export
- AC-8 ✓: PortfolioDesignerScreen cleanup decision tree
- AC-9 ✓: Comprehensive test coverage
- AC-10 ✓: LOC reduction measurement (target ~250 lines)

### File List

**New files to create:**
- `frontend/src/utils/policyTypes.ts` - Policy type normalization utilities
- `frontend/src/utils/__tests__/policyTypes.test.ts` - Policy type utility tests
- `frontend/src/hooks/usePortfolioDialog.ts` - Unified portfolio dialog hook
- `frontend/src/hooks/__tests__/usePortfolioDialog.test.ts` - Consolidated hook tests

**Files to modify:**
- `frontend/src/hooks/usePortfolioSaveDialog.ts` - Re-export for backward compatibility
- `frontend/src/hooks/usePortfolioLoadDialog.ts` - Re-export for backward compatibility
- `frontend/src/hooks/usePortfolioCloneDialog.ts` - Re-export for backward compatibility
- `frontend/src/components/simulation/typeConstants.ts` - Remove duplicate entries
- `frontend/src/components/screens/PoliciesStageScreen.tsx` - Use unified hook
- `frontend/src/api/types.ts` - Add CompositionEntry export
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` - Remove CompositionEntry export
- `frontend/src/hooks/useScenarioPersistence.ts` - Remove deprecated export
- `frontend/src/components/screens/PortfolioDesignerScreen.tsx` - Cleanup or delete
- `frontend/src/components/simulation/PolicyCard.tsx` - Verify normalization (no changes expected)
- Test files for affected components

**Estimated impact:**
- Lines removed: ~250 (hook consolidation + cleanup)
- Lines added: ~150 (new unified hook + tests + utilities)
- Net reduction: ~100 lines with improved maintainability
