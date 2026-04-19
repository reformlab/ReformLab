<!-- VALIDATION_SYNTHESIS_START -->
## Synthesis Summary

**12 issues verified** (4 critical, 4 high, 3 medium, 1 low) and **4 false positives dismissed** from 2 validator reports. **16 changes** applied to story file including: explicit parameter-to-group mapping strategy, backward compatibility migration logic with precedence rules, group name validation specification, last group protection added to AC-5, Select-only move interaction (no dnd-kit), FE/BE naming transform documentation, explicit backend test scenarios, visual distinction moved to AC-1, order semantics clarified in AC-8, and improved edit mode state documentation.

## Validations Quality

**Validator A (Quality Competition Engine):** Score 65% | Identified critical architectural gaps (persistence contract, index-based state, parameter invariants) and provided comprehensive enhancement recommendations. Strong technical depth but some issues were partially addressed in existing story content.

**Validator B (Quality Competition Engine):** Score 77.5% | Correctly identified parameter-to-group mapping as critical gap and flagged story sizing concerns (dismissed). Provided practical enhancement suggestions with clear examples.

**Overall:** Both validators provided valuable insights. Cross-validator consensus confirmed parameter-to-group mapping and backward compatibility as critical gaps. Some issues were false positives due to incomplete cross-referencing with existing story content.

## Issues Verified (by severity)

### Critical

- **Parameter-to-group mapping strategy missing** | **Source:** Validator B | **Fix:** Added DEFAULT_PARAM_ASSIGNMENTS constant to Key Design Decisions section with explicit parameter mappings for Mechanism, Eligibility, Schedule, and Redistribution groups. Updated Task 3.2 and Known Issues #2 to reference this strategy.

- **Backward compatibility for old portfolios not specified** | **Source:** Validator B | **Fix:** Added explicit migration logic to Task 9 with deterministic precedence: editable_parameter_groups (highest) → parameter_groups (converted) → default groups. Updated Known Issues #4 with full migration spec. Updated Integration section to clarify relationship between legacy and new fields.

- **Group name validation not specified in AC** | **Source:** Validator A | **Fix:** Updated AC-2 to specify behavior for empty names (reject with error, revert) and duplicate names (reject with error, revert). Enhanced Known Issues #8 with detailed validation rules including whitespace-only handling and error messages.

- **Select vs drag-and-drop ambiguity in Task 7** | **Source:** Validator A, B | **Fix:** Locked Task 7 to Select-only approach by removing "Or use drag handle with @dnd-kit library" option. Removed drag-and-drop references from parameter move implementation.

### High

- **FE/BE naming transform not documented** | **Source:** Validator A | **Fix:** Added new "FE/BE Naming Transform" section to Key Design Decisions documenting camelCase-to-snake_case mapping (parameterIds → parameter_ids, editableParameterGroups → editable_parameter_groups) and noting API layer handles this automatically.

- **Order semantics in AC-8 ambiguous** | **Source:** Validator A | **Fix:** Updated AC-8 to clarify that "order" means array sequence of groups (add/delete modify order; explicit reordering not supported in this story).

- **Last group protection missing from AC-5** | **Source:** Validator A, B | **Fix:** Updated AC-5 to specify that delete is disabled when only one group remains (regardless of parameter count), with tooltip "Cannot delete the last group". Updated Known Issues #9 to reference AC-5.

- **Backend test specifications missing** | **Source:** Validator B | **Fix:** Added explicit backend test scenarios to Testing section: test_portfolio_save_with_editable_groups, test_portfolio_load_without_editable_groups_migrates, test_portfolio_item_editable_groups_structure. Also added frontend test for delete last group.

### Medium

- **Visual distinction specification in wrong place** | **Source:** Validator B | **Fix:** Moved visual distinction requirements from Task 1 to AC-1, specifying blue border (border-blue-500) and "Editing" badge in header.

- **Parameter membership invariant not explicit** | **Source:** Validator A | **Fix:** Documented in Known Issues #5 that editGroupsIndex is only for visual state determination; all group operations use stable groupId identifiers. Added clarification that this design is safe after reorder/remove.

### Low

- **Group ID generation pattern inconsistent** | **Source:** Validator A, B | **Fix:** Noted existing guidance in Known Issues #1 provides better pattern (Date.now() + random or counter). No change needed as story already acknowledges this.

## Issues Dismissed

- **Story size - too large for single sprint** | **Raised by:** Validator B | **Dismissal Reason:** Story scope is reasonable for implementation. 8 ACs with clear subtasks touching 9 files is manageable. The breakdown shows well-defined feature areas (UI, state, persistence, tests) that can be implemented incrementally.

- **Index-based editing model is unsafe** | **Raised by:** Validator A | **Dismissal Reason:** editGroupsIndex is only used to determine which card is in edit mode (visual state), not for targeting operations. All group operations use stable groupId identifiers. Added clarification to Known Issues #5.

- **CompositionEntry vs portfolio types confusion** | **Raised by:** Validator B | **Dismissal Reason:** Story correctly distinguishes between component state (CompositionEntry.editableParameterGroups) and API contract (PortfolioPolicyRequest.editable_parameter_groups). Task 3 adds component field, Task 9 extends API types. This is proper architecture.

- **Parameter value type contract incompatible** | **Raised by:** Validator A | **Dismissal Reason:** Record<string, number> is correct for numeric policy parameters. This is by design - policy parameters are numeric values. No type mismatch issue exists.

## Deep Verify Integration

Deep Verify did not produce findings for this story.

## Changes Applied

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - AC-1
**Change:** Added explicit visual distinction requirements (blue border, "Editing" badge, specific controls)
**Before:**
```
1. **Given** a policy card in the composition panel, **when** the analyst clicks the "Edit groups" icon action, **then** edit-groups mode activates for that policy card, showing group editing controls while keeping parameter value editing available.
```
**After:**
```
1. **Given** a policy card in the composition panel, **when** the analyst clicks the "Edit groups" icon action, **then** edit-groups mode activates for that policy card, showing group editing controls (rename inputs, delete buttons, move dropdowns, add group button) while keeping parameter value editing available. The card displays a blue border (border-blue-500) and an "Editing" badge in the header.
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - AC-2
**Change:** Added group name validation rules (empty names rejected, duplicates rejected)
**Before:**
```
2. **Given** a policy card in edit-groups mode, **when** the analyst renames a group inline, **then** the new name persists and displays correctly on collapse and expand, and the name survives save/reload cycles.
```
**After:**
```
2. **Given** a policy card in edit-groups mode, **when** the analyst renames a group inline, **then** the new name persists and displays correctly on collapse and expand, and the name survives save/reload cycles. Empty names (after trimming whitespace) are rejected with an error message and reverted to the previous value. Duplicate group names within the same policy are rejected with an error message and reverted.
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - AC-5
**Change:** Added last group protection to delete behavior
**Before:**
```
5. **Given** a non-empty group (has one or more parameters), **when** delete is attempted, **then** the delete action is disabled with a tooltip or disabled action label explaining "Remove all parameters before deleting this group" (or similar), and the parameters remain intact.
```
**After:**
```
5. **Given** a non-empty group (has one or more parameters), **when** delete is attempted, **then** the delete action is disabled with a tooltip "Remove all parameters before deleting this group" and the parameters remain intact. Additionally, when only one group remains in the policy (regardless of parameter count), the delete action is disabled with a tooltip "Cannot delete the last group" and the group remains intact.
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - AC-8
**Change:** Clarified order semantics
**Before:**
```
8. **Given** a policy with edited groups is saved and reloaded, **then** the group names, order, and parameter memberships are restored correctly.
```
**After:**
```
8. **Given** a policy with edited groups is saved and reloaded, **then** the group names, order, and parameter memberships are restored correctly. Order is defined as the array sequence of groups (add/delete operations modify order; explicit reordering is not supported in this story).
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Task 1
**Change:** Removed visual distinction from task (now in AC-1)
**Before:**
```
- [ ] **Add "Edit groups" icon action to policy card header** (AC: 1)
  - [ ] Add Settings/Gear icon button from lucide-react to card header action buttons (before Move up or after Remove)
  - [ ] Icon button should have accessible label: "Edit parameter groups" and tooltip: "Customize parameter groups"
  - [ ] Clicking the button toggles edit-groups mode for that specific policy card (not global)
  - [ ] Edit-groups mode should have visual indicator: subtle blue border around card or "Editing" badge
  - [ ] Other policy cards should remain unaffected (mode is per-card, not global)
```
**After:**
```
- [ ] **Add "Edit groups" icon action to policy card header** (AC: 1)
  - [ ] Add Settings/Gear icon button from lucide-react to card header action buttons (before Move up or after Remove)
  - [ ] Icon button should have accessible label: "Edit parameter groups" and tooltip: "Customize parameter groups"
  - [ ] Clicking the button toggles edit-groups mode for that specific policy card (not global)
  - [ ] Other policy cards should remain unaffected (mode is per-card, not global)
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Task 3
**Change:** Added DEFAULT_PARAM_ASSIGNMENTS reference to parameter initialization
**Before:**
```
  - [ ] For from-scratch policies: convert `parameter_groups: string[]` to editable structure on mount (generate IDs)
  - [ ] For template-based policies: initialize editable groups from template's `parameter_groups` or default groups if not specified
```
**After:**
```
  - [ ] For from-scratch policies: convert `parameter_groups: string[]` to editable structure on mount (generate IDs, assign parameters using DEFAULT_PARAM_ASSIGNMENTS)
  - [ ] For template-based policies: initialize editable groups from template's `parameter_groups` or default groups if not specified, using DEFAULT_PARAM_ASSIGNMENTS to populate parameterIds
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Task 7
**Change:** Locked to Select-only, removed drag-and-drop option
**Before:**
```
- [ ] **Implement parameter move between groups** (AC: 6)
  - [ ] In edit-groups mode, each parameter should have a move affordance
  - [ ] Use Select dropdown to move parameter to another group (shows all group names)
  - [ ] Or use drag handle with @dnd-kit library (if already in project) for drag-and-drop
  - [ ] On move: remove param from source group, add to target group
  - [ ] Add callback `onMoveParameter(policyIndex: number, paramId: string, fromGroupId: string, toGroupId: string)` to parent
```
**After:**
```
- [ ] **Implement parameter move between groups** (AC: 6)
  - [ ] In edit-groups mode, each parameter should have a move affordance
  - [ ] Use Select dropdown to move parameter to another group (shows all group names)
  - [ ] On move: remove param from source group, add to target group
  - [ ] Add callback `onMoveParameter(policyIndex: number, paramId: string, fromGroupId: string, toGroupId: string)` to parent
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Task 9
**Change:** Added explicit migration logic with precedence rules
**Before:**
```
- [ ] **Persist editable parameter groups in portfolio save/load** (AC: 8)
  - [ ] Update `createPortfolio()` API call to include `editable_parameter_groups` for each policy
  - [ ] Backend: Extend `PortfolioPolicyRequest` to accept `editable_parameter_groups` (optional field)
  - [ ] Backend: Store editable parameter groups in portfolio persistence layer
  - [ ] Update `usePortfolioLoadDialog.ts` to restore `editableParameterGroups` from loaded portfolio data
  - [ ] Ensure round-trip: save → reload → verify all group edits preserved
```
**After:**
```
- [ ] **Persist editable parameter groups in portfolio save/load** (AC: 8)
  - [ ] Update `createPortfolio()` API call to include `editable_parameter_groups` for each policy
  - [ ] Backend: Extend `PortfolioPolicyRequest` to accept `editable_parameter_groups` (optional field)
  - [ ] Backend: Store editable parameter groups in portfolio persistence layer
  - [ ] Update `usePortfolioLoadDialog.ts` to restore `editableParameterGroups` from loaded portfolio data
  - [ ] Implement migration logic: on portfolio load, if `editable_parameter_groups` exists use it; else if `parameter_groups` exists convert to editable structure; else use default groups
  - [ ] Ensure round-trip: save → reload → verify all group edits preserved
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Task 9 (Backend models)
**Change:** Added snake_case note and migration reference
**Before:**
```
- [ ] **Backend: Extend portfolio models for editable parameter groups** (AC: 8)
  - [ ] Add `editable_parameter_groups: list[dict[str, Any]] | None = None` to `PortfolioPolicyRequest`
  - [ ] Add `editable_parameter_groups: list[dict[str, Any]] | None = None` to `PortfolioPolicyItem`
  - [ ] Structure each editable group as: `{"id": str, "name": str, "parameter_ids": list[str]}`
  - [ ] Ensure backward compatibility: policies without editable groups use default groups from template
```
**After:**
```
- [ ] **Backend: Extend portfolio models for editable parameter groups** (AC: 8)
  - [ ] Add `editable_parameter_groups: list[dict[str, Any]] | None = None` to `PortfolioPolicyRequest`
  - [ ] Add `editable_parameter_groups: list[dict[str, Any]] | None = None` to `PortfolioPolicyItem`
  - [ ] Structure each editable group as: `{"id": str, "name": str, "parameter_ids": list[str]}` (note: snake_case for backend)
  - [ ] Ensure backward compatibility: policies without editable groups use default groups from template or migrate from `parameter_groups`
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Testing section
**Change:** Added explicit backend test scenarios and additional frontend test
**Before:**
```
- [ ] **Testing** (AC: 1, 2, 3, 4, 5, 6, 7, 8)
  - [ ] Frontend tests for edit-groups mode toggle (enter and exit)
  - [ ] Frontend tests for group rename (save on blur/Enter, revert on Escape)
  - [ ] Frontend tests for add new empty group
  - [ ] Frontend tests for delete empty group (success) and delete non-empty group (blocked with explanation)
  - [ ] Frontend tests for parameter move between groups via dropdown
  - [ ] Frontend tests for edit-groups mode persistence across collapse/expand
  - [ ] Persistence tests: save policy with edited groups, reload, verify all edits preserved
  - [ ] Accessibility tests: keyboard navigation, screen reader announcements, focus management
  - [ ] Regression tests: verify normal parameter editing still works when not in edit-groups mode
```
**After:**
```
- [ ] **Testing** (AC: 1, 2, 3, 4, 5, 6, 7, 8)
  - [ ] Frontend tests for edit-groups mode toggle (enter and exit)
  - [ ] Frontend tests for group rename (save on blur/Enter, revert on Escape)
  - [ ] Frontend tests for add new empty group
  - [ ] Frontend tests for delete empty group (success) and delete non-empty group (blocked with explanation)
  - [ ] Frontend tests for delete last group (blocked regardless of parameter count)
  - [ ] Frontend tests for parameter move between groups via dropdown
  - [ ] Frontend tests for edit-groups mode persistence across collapse/expand
  - [ ] Persistence tests: save policy with edited groups, reload, verify all edits preserved
  - [ ] Backend tests: `test_portfolio_save_with_editable_groups()` — verify editable_parameter_groups persisted correctly
  - [ ] Backend tests: `test_portfolio_load_without_editable_groups_migrates()` — verify old portfolios auto-migrate to editable structure
  - [ ] Backend tests: `test_portfolio_item_editable_groups_structure()` — verify schema validation
  - [ ] Accessibility tests: keyboard navigation, screen reader announcements, focus management
  - [ ] Regression tests: verify normal parameter editing still works when not in edit-groups mode
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Key Design Decisions - Parameter Group Initialization
**Change:** Added DEFAULT_PARAM_ASSIGNMENTS constant
**Before:**
```
**Parameter Group Initialization:**

For from-scratch policies (Story 25.3), convert the simple `parameter_groups: string[]` array to editable groups on mount:

```typescript
const initializeEditableGroups = (entry: CompositionEntry): EditableParameterGroup[] => {
  if (entry.editableParameterGroups) {
    return entry.editableParameterGroups;
  }

  // Convert from Story 25.3 parameter_groups string[] to editable structure
  if (entry.parameter_groups) {
    return entry.parameter_groups.map((name, idx) => ({
      id: `group-${idx}`,
      name,
      parameterIds: [], // Parameters assigned to groups via template schema
    }));
  }

  // Default groups for template-based policies
  return [
    { id: "group-0", name: "Mechanism", parameterIds: ["rate", "unit"] },
    { id: "group-1", name: "Eligibility", parameterIds: ["threshold", "ceiling"] },
    { id: "group-2", name: "Schedule", parameterIds: [] },
  ];
};
```
```
**After:**
```
**Parameter Group Initialization:**

For from-scratch policies (Story 25.3), convert the simple `parameter_groups: string[]` array to editable groups on mount:

```typescript
// Default parameter-to-group assignments for from-scratch policies
const DEFAULT_PARAM_ASSIGNMENTS: Record<string, string[]> = {
  "Mechanism": ["rate", "unit"],
  "Eligibility": ["threshold", "ceiling", "income_cap"],
  "Schedule": [], // Uses year schedule editor
  "Redistribution": ["divisible", "recipients", "income_weights"],
};

const initializeEditableGroups = (entry: CompositionEntry): EditableParameterGroup[] => {
  if (entry.editableParameterGroups) {
    return entry.editableParameterGroups;
  }

  // Convert from Story 25.3 parameter_groups string[] to editable structure
  if (entry.parameter_groups) {
    return entry.parameter_groups.map((name, idx) => ({
      id: `group-${idx}`,
      name,
      parameterIds: DEFAULT_PARAM_ASSIGNMENTS[name] ?? [],
    }));
  }

  // Default groups for template-based policies
  return [
    { id: "group-0", name: "Mechanism", parameterIds: ["rate", "unit"] },
    { id: "group-1", name: "Eligibility", parameterIds: ["threshold", "ceiling"] },
    { id: "group-2", name: "Schedule", parameterIds: [] },
  ];
};
```
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Key Design Decisions - before Persistence Contract
**Change:** Added new FE/BE Naming Transform section
**Before:**
```
**Persistence Contract:**

Editable parameter groups are persisted alongside policy data:
```
**After:**
```
**FE/BE Naming Transform:**

Frontend uses camelCase (`parameterIds`) but backend expects snake_case (`parameter_ids`). The API layer handles this transform automatically:
- Frontend `EditableParameterGroup.parameterIds` → backend `parameter_ids`
- Frontend `editableParameterGroups` → backend `editable_parameter_groups`
- This follows the existing pattern used by other fields (e.g., `policy_type`, `rate_schedule`)

**Persistence Contract:**

Editable parameter groups are persisted alongside policy data:
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Known Issues #2
**Change:** Updated to reference DEFAULT_PARAM_ASSIGNMENTS
**Before:**
```
2. **Parameter-to-group mapping:** When initializing editable groups from templates, need to determine which parameters belong in which groups. Template schemas may not specify this explicitly — need a sensible default (all parameters in first group, or by parameter name pattern).
```
**After:**
```
2. **Parameter-to-group mapping:** When initializing editable groups from templates, use the DEFAULT_PARAM_ASSIGNMENTS constant (see Key Design Decisions) to assign parameters to groups by name pattern. For parameters not matching any pattern, assign to the first group. Template schemas may not specify explicit group memberships — this default strategy ensures consistent behavior.
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Known Issues #4
**Change:** Added explicit migration precedence rules
**Before:**
```
4. **Backward compatibility:** Portfolios saved before Story 25.4 won't have `editable_parameter_groups`. Need to migrate on load: if missing, generate editable groups from `parameter_groups` string array or template defaults.
```
**After:**
```
4. **Backward compatibility:** Portfolios saved before Story 25.4 won't have `editable_parameter_groups`. Implement migration logic with deterministic precedence:
   - If `editable_parameter_groups` exists and is non-empty, use it (highest precedence)
   - Else if `parameter_groups` exists, convert to editable structure using DEFAULT_PARAM_ASSIGNMENTS
   - Else use default groups based on policy type
   This ensures portfolios saved after 25.4 always preserve customizations, while old portfolios get reasonable defaults.
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Known Issues #5
**Change:** Clarified editGroupsIndex usage and safety
**Before:**
```
5. **Edit mode state confusion:** Ensure edit mode doesn't get confused when multiple policy cards exist. Each card has independent edit mode state tracked by `editGroupsIndex`.
```
**After:**
```
5. **Edit mode state confusion:** Ensure edit mode doesn't get confused when multiple policy cards exist. Each card has independent edit mode state tracked by `editGroupsIndex`. The `editGroupsIndex` is only used to determine which card is in edit mode (visual state); all group operations use stable `groupId` identifiers, not array indices. This design is safe even after reorder/remove operations because group identity is preserved via `groupId`.
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Known Issues #8
**Change:** Added detailed validation rules with error messages
**Before:**
```
8. **Group name validation:** Prevent empty group names or duplicate group names within a policy. Add validation on blur: if name is empty or duplicate, revert to previous value with error message.
```
**After:**
```
8. **Group name validation:** Implement validation on blur with these rules:
   - Empty names (after trimming whitespace): reject, revert to previous value, show error "Group name cannot be empty"
   - Duplicate names within the same policy: reject, revert to previous value, show error "Group name already exists"
   - Names with only whitespace: treat as empty, apply empty name logic
   Use toast or inline error message for feedback; ensure user can retry immediately.
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Known Issues #9
**Change:** Added reference to AC-5
**Before:**
```
9. **Last group cannot be deleted:** Prevent deletion of the last remaining group (need at least one group). Add check: `groups.length > 1` before allowing delete.
```
**After:**
```
9. **Last group cannot be deleted:** Prevent deletion of the last remaining group (need at least one group). Add check: `groups.length > 1` before allowing delete. This is now specified in AC-5.
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Integration section
**Change:** Clarified editable_groups vs parameter_groups relationship
**Before:**
```
**Story 25.4 builds on:**
- Takes the static `parameter_groups` display from Story 25.3 and makes it editable
- Adds group editing controls alongside the existing static display
- Persists the editable structure as `editable_parameter_groups` in addition to or replacing the simple string array
```
**After:**
```
**Story 25.4 builds on:**
- Takes the static `parameter_groups` display from Story 25.3 and makes it editable
- Adds group editing controls alongside the existing static display
- Persists the editable structure as `editable_parameter_groups`; the legacy `parameter_groups` string array is preserved for backward compatibility but ignored when `editable_parameter_groups` is present
- Migration on load: if `editable_parameter_groups` exists, use it; else derive from `parameter_groups`; else use defaults
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Source Tree Components to Touch
**Change:** Added missing test file to frontend list
**Before:**
```
**Frontend files to modify:**
1. `frontend/src/api/types.ts` — Add `EditableParameterGroup` interface and extend portfolio types
2. `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — Add edit-groups mode UI
3. `frontend/src/components/screens/PoliciesStageScreen.tsx` — Add edit-groups state management
4. `frontend/src/hooks/usePortfolioLoadDialog.ts` — Restore editable groups on portfolio load
5. `frontend/src/components/simulation/__tests__/PortfolioCompositionPanel.editGroups.test.tsx` — NEW (edit groups tests)
```
**After:**
```
**Frontend files to modify:**
1. `frontend/src/api/types.ts` — Add `EditableParameterGroup` interface and extend portfolio types
2. `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — Add edit-groups mode UI
3. `frontend/src/components/screens/PoliciesStageScreen.tsx` — Add edit-groups state management
4. `frontend/src/hooks/usePortfolioLoadDialog.ts` — Restore editable groups on portfolio load
5. `frontend/src/components/simulation/__tests__/PortfolioCompositionPanel.editGroups.test.tsx` — NEW (edit groups tests)
6. `frontend/src/components/simulation/__tests__/PoliciesStageScreen.editGroups.test.tsx` — NEW (integration tests)
```

---

**Location:** 25-4-make-parameter-groups-editable-within-policy-cards.md - Dev Agent Record - File List
**Change:** Updated descriptions to reflect migration logic
**Before:**
```
**Backend (3 files):**
- `src/reformlab/server/models.py` — add editable_parameter_groups to portfolio models
- `src/reformlab/server/routes/portfolios.py` — handle editable groups in save/load
- `tests/server/test_portfolios.py` — add persistence tests

**Frontend (6 files):**
- `frontend/src/api/types.ts` — add EditableParameterGroup interface, extend portfolio types
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — add edit-groups mode UI
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — add edit-groups state management
- `frontend/src/hooks/usePortfolioLoadDialog.ts` — restore editable groups on load
- `frontend/src/components/simulation/__tests__/PortfolioCompositionPanel.editGroups.test.tsx` — NEW (edit groups tests)
- `frontend/src/components/simulation/__tests__/PoliciesStageScreen.editGroups.test.tsx` — NEW (integration tests)
```
**After:**
```
**Backend (3 files):**
- `src/reformlab/server/models.py` — add editable_parameter_groups to portfolio models
- `src/reformlab/server/routes/portfolios.py` — handle editable groups in save/load with migration logic
- `tests/server/test_portfolios.py` — add persistence tests including migration scenarios

**Frontend (6 files):**
- `frontend/src/api/types.ts` — add EditableParameterGroup interface, extend portfolio types
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — add edit-groups mode UI
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — add edit-groups state management
- `frontend/src/hooks/usePortfolioLoadDialog.ts` — restore editable groups on portfolio load with migration
- `frontend/src/components/simulation/__tests__/PortfolioCompositionPanel.editGroups.test.tsx` — NEW (edit groups tests)
- `frontend/src/components/simulation/__tests__/PoliciesStageScreen.editGroups.test.tsx` — NEW (integration tests)
```
<!-- VALIDATION_SYNTHESIS_END -->
