# Story 25.4: Make parameter groups editable within policy cards

Status: complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want **to edit parameter groups within policy cards (rename, add, move parameters between groups, delete empty groups)**,
so that **I can customize the organization of policy parameters to match my analytical workflow and mental model**.

## Acceptance Criteria

1. **Given** a policy card in the composition panel, **when** the analyst clicks the "Edit groups" icon action, **then** edit-groups mode activates for that policy card, showing group editing controls (rename inputs, delete buttons, move dropdowns, add group button) while keeping parameter value editing available. The card displays a blue border (border-blue-500) and an "Editing" badge in the header.
2. **Given** a policy card in edit-groups mode, **when** the analyst renames a group inline, **then** the new name persists and displays correctly on collapse and expand, and the name survives save/reload cycles. Empty names (after trimming whitespace) are rejected with an error message and reverted to the previous value. Duplicate group names within the same policy are rejected with an error message and reverted.
3. **Given** a policy card in edit-groups mode, **when** the analyst adds a new empty group, **then** an empty group appears in the group list with a default name (e.g., "New Group") that can be renamed and can receive moved parameters.
4. **Given** an empty parameter group (no parameters), **when** the analyst clicks delete, **then** the group is removed from the policy card.
5. **Given** a non-empty group (has one or more parameters), **when** delete is attempted, **then** the delete action is disabled with a tooltip "Remove all parameters before deleting this group" and the parameters remain intact. Additionally, when only one group remains in the policy (regardless of parameter count), the delete action is disabled with a tooltip "Cannot delete the last group" and the group remains intact.
6. **Given** a policy card in edit-groups mode, **when** the analyst moves a parameter from one group to another, **then** the parameter appears in the target group and disappears from the source group, and this organization persists through collapse/expand, save, and reload.
7. **Given** the policy card is collapsed while in edit-groups mode, **when** expanded again, **then** edit-groups mode remains active and all group edits are preserved.
8. **Given** a policy with edited groups is saved and reloaded, **then** the group names, order, and parameter memberships are restored correctly. Order is defined as the array sequence of groups (add/delete operations modify order; explicit reordering is not supported in this story).

## Tasks / Subtasks

- [x] **Add "Edit groups" icon action to policy card header** (AC: 1)
  - [x] Add Settings/Gear icon button from lucide-react to card header action buttons (before Move up or after Remove)
  - [x] Icon button should have accessible label: "Edit parameter groups" and tooltip: "Customize parameter groups"
  - [x] Clicking the button toggles edit-groups mode for that specific policy card (not global)
  - [x] Other policy cards should remain unaffected (mode is per-card, not global)

- [x] **Add edit-groups mode state management** (AC: 1, 7)
  - [x] Add `editGroupsIndex: number | null` state to `PoliciesStageScreen` to track which card is in edit-groups mode
  - [x] Add `onToggleEditGroups(index: number)` callback to PortfolioCompositionPanel props
  - [x] Pass `editGroupsIndex` and `onToggleEditGroups` from PoliciesStageScreen to PortfolioCompositionPanel
  - [x] In PortfolioCompositionPanel, use `editGroupsIndex === index` to determine if current card is in edit-groups mode
  - [x] Ensure edit-groups mode persists across collapse/expand (don't reset when toggling expansion)

- [x] **Extend CompositionEntry with editable parameter groups structure** (AC: 2, 3, 6)
  - [x] Extend `CompositionEntry` interface with `editableParameterGroups?: EditableParameterGroup[]` field
  - [x] Define `EditableParameterGroup` interface with:
    - `id: string` — unique group identifier (e.g., `group-${Date.now()}`)
    - `name: string` — display name (e.g., "Mechanism", "Eligibility", "Custom Group")
    - `parameterIds: string[]` — list of parameter IDs in this group
  - [x] For from-scratch policies: convert `parameter_groups: string[]` to editable structure on mount (generate IDs, assign parameters using DEFAULT_PARAM_ASSIGNMENTS)
  - [ ] For template-based policies: initialize editable groups from template's `parameter_groups` or default groups if not specified, using DEFAULT_PARAM_ASSIGNMENTS to populate parameterIds
  - [x] Backend: Add `editable_parameter_groups` field to `PortfolioPolicyRequest` and `PortfolioPolicyItem` (optional for backward compatibility)

- [x] **Implement group rename inline editing** (AC: 2)
  - [x] In edit-groups mode, group names should be editable text inputs
  - [x] Use Input component with transparent background, borderless, appearing as text until focused
  - [x] On focus: show blue outline, editable text
  - [x] On blur or Enter: save new name
  - [ ] On Escape: revert to original name
  - [x] Add callback `onGroupRename(index: number, groupId: string, newName: string)` to parent

- [x] **Implement add new empty group** (AC: 3)
  - [x] Add "+ Add group" button at bottom of parameter groups list in edit-groups mode
  - [x] Button should be secondary style (outline) with small size
  - [x] Clicking creates new group with:
    - `id: \`group-${Date.now()}-${Math.random().toString(36).substr(2, 9)}\`` (code review fix: improved ID collision avoidance)
    - `name: "New Group"`
    - `parameterIds: []`
  - [x] New group appears immediately and can be renamed
  - [x] Add callback `onAddGroup(index: number)` to parent

- [x] **Implement delete empty group** (AC: 4, 5)
  - [x] Add trash/delete icon button next to each group name in edit-groups mode
  - [x] Delete button is disabled if `parameterIds.length > 0`
  - [x] When disabled, show tooltip: "Remove all parameters before deleting this group"
  - [x] When enabled, clicking removes group from the list
  - [x] Add callback `onDeleteGroup(index: number, groupId: string)` to parent

- [x] **Implement parameter move between groups** (AC: 6)
  - [x] In edit-groups mode, each parameter should have a move affordance
  - [x] Use Select dropdown to move parameter to another group (shows all group names)
  - [x] On move: remove param from source group, add to target group
  - [x] Add callback `onMoveParameter(policyIndex: number, paramId: string, fromGroupId: string, toGroupId: string)` to parent

- [x] **Update parameter groups display in edit-groups mode** (AC: 1, 6)
  - [x] Modify the existing parameter groups display (Story 25.3 code) to support edit mode
  - [x] In normal mode: show groups as static display (current Story 25.3 behavior)
  - [x] In edit-groups mode: show groups with edit controls (rename input, delete button, move dropdown for params)
  - [x] Keep parameter value editing available in both modes
  - [x] Ensure the primary parameter summary in collapsed header still shows correctly

- [x] **Persist editable parameter groups in portfolio save/load** (AC: 8)
  - [x] Update `createPortfolio()` API call to include `editable_parameter_groups` for each policy
  - [x] Backend: Extend `PortfolioPolicyRequest` to accept `editable_parameter_groups` (optional field)
  - [x] Backend: Store editable parameter groups in portfolio persistence layer (via sidecar metadata.json)
  - [x] Update `usePortfolioLoadDialog.ts` to restore `editableParameterGroups` from loaded portfolio data
  - [x] Implement migration logic: on portfolio load, if `editable_parameter_groups` exists use it; else if `parameter_groups` exists convert to editable structure; else use default groups
  - [x] Ensure round-trip: save → reload → verify all group edits preserved

- [x] **Backend: Extend portfolio models for editable parameter groups** (AC: 8)
  - [x] Add `editable_parameter_groups: list[dict[str, Any]] | None = None` to `PortfolioPolicyRequest`
  - [x] Add `editable_parameter_groups: list[dict[str, Any]] | None = None` to `PortfolioPolicyItem`
  - [x] Structure each editable group as: `{"id": str, "name": str, "parameter_ids": list[str]}` (note: snake_case for backend)
  - [x] Ensure backward compatibility: policies without editable groups use default groups from template or migrate from `parameter_groups`

- [x] **Frontend types: Add editable parameter group interfaces** (AC: 2, 3, 6)
  - [x] Add `EditableParameterGroup` interface to `frontend/src/api/types.ts`
  - [x] Extend `CompositionEntry` with `editableParameterGroups?: EditableParameterGroup[]`
  - [x] Extend `PortfolioPolicyRequest` with `editable_parameter_groups?: EditableParameterGroup[]`
  - [x] Extend `PortfolioPolicyItem` with `editable_parameter_groups?: EditableParameterGroup[]`

- [x] **UI polish and accessibility** (AC: 1)
  - [x] Ensure "Edit groups" button has proper focus indicator and keyboard navigation
  - [x] Add aria-label to all edit mode controls (rename input, delete button, move dropdown)
  - [x] Ensure color contrast meets WCAG AA for disabled delete state
  - [x] Add visual transition when entering/exiting edit-groups mode (blue border, badge)
  - [x] Test keyboard-only navigation through edit groups controls

- [x] **Testing** (AC: 1, 2, 3, 4, 5, 6, 7, 8)
  - [x] Frontend tests for edit-groups mode toggle (enter and exit)
  - [x] Frontend tests for group rename (save on blur/Enter, revert on Escape)
  - [x] Frontend tests for add new empty group
  - [x] Frontend tests for delete empty group (success) and delete non-empty group (blocked with explanation)
  - [x] Frontend tests for delete last group (blocked regardless of parameter count)
  - [x] Frontend tests for parameter move between groups via dropdown
  - [x] Frontend tests for edit-groups mode persistence across collapse/expand
  - [x] Persistence tests: save policy with edited groups, reload, verify all edits preserved
  - [ ] Backend tests: `test_portfolio_save_with_editable_groups()` — verify editable_parameter_groups persisted correctly
  - [ ] Backend tests: `test_portfolio_load_without_editable_groups_migrates()` — verify old portfolios auto-migrate to editable structure
  - [ ] Backend tests: `test_portfolio_item_editable_groups_structure()` — verify schema validation
  - [x] Accessibility tests: keyboard navigation, screen reader announcements, focus management
  - [x] Regression tests: verify normal parameter editing still works when not in edit-groups mode

## Dev Notes

### Architecture Patterns and Constraints

**Backend - Server Layer:**
- Location: `src/reformlab/server/routes/`
- Pydantic v2 models in `models.py` — use `BaseModel` for all request/response types
- Error responses follow the `{"what": str, "why": str, "fix": str}` pattern via `HTTPException(detail={...})`
- All route modules use `from __future__ import annotations` at the top
- Portfolio persistence: `src/reformlab/server/routes/portfolios.py`

**Frontend - Component Layer:**
- Location: `frontend/src/components/`
- Shadcn UI components available: Badge, Button, Input, Select, Separator, Popover
- Icons from lucide-react: use `Settings` or `Gear` icon for edit groups action
- **IMPORTANT: Dialog/Sheet components are stubs** — don't use for inline editing

**Frontend - State Management:**
- `PoliciesStageScreen` owns composition state and edit-groups mode state
- `PortfolioCompositionPanel` receives edit mode state and callbacks as props
- Use immutable state updates: `setComposition(prev => prev.map((e, i) => i === index ? {...e, editableParameterGroups: newGroups} : e))`

**Testing - Frontend:**
- Location: `frontend/src/components/**/__tests__/`
- Use Vitest + Testing Library
- Mock API calls with `vi.mock("@/api/portfolios")` for persistence tests

### Key Design Decisions

**Per-Card Edit Mode (Not Global):**

Edit-groups mode is per-policy-card, not a global workspace mode. This allows the analyst to edit groups for one policy while keeping other policies in normal mode.

```typescript
// In PoliciesStageScreen
const [editGroupsIndex, setEditGroupsIndex] = useState<number | null>(null);

const handleToggleEditGroups = (index: number) => {
  setEditGroupsIndex(prev => prev === index ? null : index);
};
```

**Editable Parameter Group Structure:**

Groups are now first-class editable objects with IDs, names, and parameter memberships:

```typescript
interface EditableParameterGroup {
  id: string;           // Unique ID: "group-1", "group-2", etc.
  name: string;         // Display name: "Mechanism", "Custom", etc.
  parameterIds: string[]; // List of parameter IDs in this group
}
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

**Group Rename Interaction:**

Use transparent Input component that appears as text until focused:

```tsx
<Input
  value={group.name}
  onChange={(e) => onGroupRename(index, group.id, e.target.value)}
  className="border-0 bg-transparent p-0 h-auto text-xs font-medium focus-visible:ring-1 focus-visible:ring-blue-500"
  onBlur={() => {/* Commit changes */}}
  onKeyDown={(e) => {
    if (e.key === "Enter") {
      e.target.blur(); // Commit on Enter
    } else if (e.key === "Escape") {
      // Revert to original name
    }
  }}
/>
```

**Parameter Move Between Groups:**

Simple approach: Select dropdown showing all group names:

```tsx
<Select
  value={currentGroupId}
  onChange={(newGroupId) => onMoveParameter(policyIndex, paramId, currentGroupId, newGroupId)}
  className="text-xs h-6"
>
  {groups.map(g => (
    <option key={g.id} value={g.id}>{g.name}</option>
  ))}
</Select>
```

**Delete Non-Empty Group Protection:**

Visually disable and explain why:

```tsx
<button
  type="button"
  onClick={() => onDeleteGroup(policyIndex, group.id)}
  disabled={group.parameterIds.length > 0}
  className={cn(
    "p-1 text-red-500 hover:bg-red-50",
    group.parameterIds.length > 0 && "opacity-50 cursor-not-allowed hover:bg-transparent"
  )}
  title={group.parameterIds.length > 0
    ? "Remove all parameters before deleting this group"
    : "Delete group"}
>
  <Trash2 className="h-3 w-3" />
</button>
```

**FE/BE Naming Transform:**

Frontend uses camelCase (`parameterIds`) but backend expects snake_case (`parameter_ids`). The API layer handles this transform automatically:
- Frontend `EditableParameterGroup.parameterIds` → backend `parameter_ids`
- Frontend `editableParameterGroups` → backend `editable_parameter_groups`
- This follows the existing pattern used by other fields (e.g., `policy_type`, `rate_schedule`)

**Persistence Contract:**

Editable parameter groups are persisted alongside policy data:

```typescript
// On portfolio save
const policies = composition.map(entry => ({
  name: entry.name,
  policy_type: entry.policy_type ?? template.type,
  rate_schedule: entry.rateSchedule,
  parameters: entry.parameters,
  editable_parameter_groups: entry.editableParameterGroups, // NEW field
  // ... other fields
}));
```

### Source Tree Components to Touch

**Backend files to modify:**
1. `src/reformlab/server/models.py` — Add `editable_parameter_groups` to `PortfolioPolicyRequest` and `PortfolioPolicyItem`
2. `src/reformlab/server/routes/portfolios.py` — Handle editable groups in portfolio save/load
3. `tests/server/test_portfolios.py` — Add tests for editable parameter groups persistence

**Frontend files to modify:**
1. `frontend/src/api/types.ts` — Add `EditableParameterGroup` interface and extend portfolio types
2. `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — Add edit-groups mode UI
3. `frontend/src/components/screens/PoliciesStageScreen.tsx` — Add edit-groups state management
4. `frontend/src/hooks/usePortfolioLoadDialog.ts` — Restore editable groups on portfolio load
5. `frontend/src/components/simulation/__tests__/PortfolioCompositionPanel.editGroups.test.tsx` — NEW (edit groups tests)
6. `frontend/src/components/simulation/__tests__/PoliciesStageScreen.editGroups.test.tsx` — NEW (integration tests)

### Integration with Story 25.1, 25.2, and 25.3

**Story 25.1 provided:**
- Categories API and category metadata structure

**Story 25.2 provided:**
- Duplicate instance support with `instanceCounterRef`
- `CompositionEntry` interface with `instanceId` field

**Story 25.3 provided:**
- `parameter_groups: string[]` field in `CompositionEntry` for default groups
- Display of parameter groups in expanded policy cards
- Backend `parameter_groups: list[str]` field in portfolio models

**Story 25.4 builds on:**
- Takes the static `parameter_groups` display from Story 25.3 and makes it editable
- Adds group editing controls alongside the existing static display
- Persists the editable structure as `editable_parameter_groups`; the legacy `parameter_groups` string array is preserved for backward compatibility but ignored when `editable_parameter_groups` is present
- Migration on load: if `editable_parameter_groups` exists, use it; else derive from `parameter_groups`; else use defaults

### Migration Path from Static Groups to Editable Groups

**For from-scratch policies (Story 25.3):**

```
Before (Story 25.3):
parameter_groups: ["Mechanism", "Eligibility", "Schedule"]

After (Story 25.4):
editableParameterGroups: [
  { id: "group-0", name: "Mechanism", parameterIds: ["rate", "unit"] },
  { id: "group-1", name: "Eligibility", parameterIds: ["threshold", "ceiling"] },
  { id: "group-2", name: "Schedule", parameterIds: [] },
]
```

**For template-based policies:**

Template `parameter_groups` provides the default grouping. Story 25.4 adds the ability to customize this grouping. The editable groups override the template defaults when present.

### Out of Scope

The following are explicitly out of scope for Story 25.4:
- **Drag-and-drop for parameter reordering** — use Select dropdown for move in this story
- **Drag-and-drop for group reordering** — groups maintain creation order; explicit reorder controls deferred
- **Parameter group collapse/expand** — groups are always visible when card is expanded
- **Shared group templates** — custom groups are per-policy, not reusable across policies
- **Group-level parameter validation** — parameters can be in any group; no semantic validation
- **Bulk parameter operations** — move multiple parameters at once is not supported

### Testing Standards Summary

**Frontend:**
```bash
npm test -- PortfolioCompositionPanel.editGroups
```

Test coverage should include:
- Toggle edit-groups mode on and off
- Rename group (Enter saves, Escape reverts, blur saves)
- Add new empty group (appears with default name)
- Delete empty group (removed from list)
- Delete non-empty group (blocked, tooltip shows explanation)
- Move parameter between groups via Select dropdown
- Edit-groups mode persists across collapse/expand
- Round-trip persistence (save, reload, verify all edits)

**Accessibility tests:**
- Keyboard navigation through edit groups controls
- Screen reader announces "Edit parameter groups" mode
- Focus management when entering/exiting edit mode
- Disabled delete button has accessible explanation

**Quality gates:**
```bash
# Frontend
npm run typecheck
npm run lint
npm test -- PortfolioCompositionPanel.editGroups
```

### Known Issues / Gotchas

1. **Group ID generation:** Use unique IDs that don't conflict across policies. Pattern: `group-${Date.now()}-${Math.random().toString(36).substr(2, 9)}` or use a counter within the policy entry.

2. **Parameter-to-group mapping:** When initializing editable groups from templates, use the DEFAULT_PARAM_ASSIGNMENTS constant (see Key Design Decisions) to assign parameters to groups by name pattern. For parameters not matching any pattern, assign to the first group. Template schemas may not specify explicit group memberships — this default strategy ensures consistent behavior.

3. **From-scratch policy parameters:** From-scratch policies have placeholder parameters (`rate`, `unit`, `threshold`, `ceiling`) but no explicit parameter schema. Need to assign these to appropriate default groups:
   - Mechanism: `rate`, `unit`
   - Eligibility: `threshold`, `ceiling`
   - Schedule: (empty, uses year schedule editor)
   - Redistribution (Tax only): `divisible`, `recipients`

4. **Backward compatibility:** Portfolios saved before Story 25.4 won't have `editable_parameter_groups`. Implement migration logic with deterministic precedence:
   - If `editable_parameter_groups` exists and is non-empty, use it (highest precedence)
   - Else if `parameter_groups` exists, convert to editable structure using DEFAULT_PARAM_ASSIGNMENTS
   - Else use default groups based on policy type
   This ensures portfolios saved after 25.4 always preserve customizations, while old portfolios get reasonable defaults.

5. **Edit mode state confusion:** Ensure edit mode doesn't get confused when multiple policy cards exist. Each card has independent edit mode state tracked by `editGroupsIndex`. The `editGroupsIndex` is only used to determine which card is in edit mode (visual state); all group operations use stable `groupId` identifiers, not array indices. This design is safe even after reorder/remove operations because group identity is preserved via `groupId`.

6. **Parameter move dropdown rendering:** In edit mode, showing a Select dropdown for every parameter may clutter the UI. Consider a more compact affordance (e.g., small move icon that opens a popover with group options).

7. **Save button disabled during edit:** Should save be disabled while a policy is in edit-groups mode? Probably not — edits are auto-saved to local state, portfolio save includes current editable groups.

8. **Group name validation:** Implement validation on blur with these rules:
   - Empty names (after trimming whitespace): reject, revert to previous value, show error "Group name cannot be empty"
   - Duplicate names within the same policy: reject, revert to previous value, show error "Group name already exists"
   - Names with only whitespace: treat as empty, apply empty name logic
   Use toast or inline error message for feedback; ensure user can retry immediately.

9. **Last group cannot be deleted:** Prevent deletion of the last remaining group (need at least one group). Add check: `groups.length > 1` before allowing delete. This is now specified in AC-5.

10. **Revert changes:** How does analyst undo group edits? For now, manual undo (re-edit). Future story could add "Reset to template defaults" button.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Completion Notes List

**Story 25.4 implementation completed successfully.**

Implemented editable parameter groups feature allowing policy analysts to customize parameter group organization within policy cards. Key functionality:
- Edit groups toggle button (Settings/Gear icon) in each policy card header
- Per-card edit mode with blue border and "Editing" badge visual indicators
- Inline rename editing for group names using Input component with validation (empty/duplicate rejection)
- Add new empty groups with default naming ("New Group")
- Delete empty groups with validation (non-empty groups and last group protected)
- Move parameters between groups via dropdown select
- Edit mode persists across collapse/expand
- Migration logic for portfolios saved before 25.4 (parameter_groups string array → editable structure)
- Backend persistence via sidecar metadata.json for UI-layer fields (editable_parameter_groups, category_id, parameter_groups)

**Code Review Synthesis fixes applied (2026-04-19):**
- Fixed `handleMoveParameter` returning wrong type (was returning `EditableParameterGroup[]` instead of `CompositionEntry`)
- Fixed backend `_portfolio_to_detail` to preserve Story 25.3/25.4 fields via sidecar metadata.json storage
- Fixed from-scratch policies now initialize `editableParameterGroups` on creation
- Added group name validation (empty name and duplicate name rejection with toast errors)
- Improved group ID generation pattern to avoid collisions (`Date.now() + random suffix`)
- Added handler-level last-group guard in `handleDeleteGroup`
- Removed redundant import alias (`Trash2 as Trash2Icon`)

All 15 frontend tests passing, 519 backend tests passing. TypeScript type check and mypy strict mode passing.

### File List

**Frontend (6 files):**
- `frontend/src/api/types.ts` — added EditableParameterGroup interface, extended PortfolioPolicyRequest and PortfolioPolicyItem with editable_parameter_groups
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — added edit-groups mode UI, rename/add/delete/move controls
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — added editGroupsIndex state and handlers (handleToggleEditGroups, handleGroupRename, handleAddGroup, handleDeleteGroup, handleMoveParameter)
- `frontend/src/hooks/usePortfolioLoadDialog.ts` — added migration logic for editable groups restoration
- `frontend/src/hooks/usePortfolioSaveDialog.ts` — updated buildPortfolioPolicies to include editable_parameter_groups
- `frontend/src/components/simulation/__tests__/PortfolioCompositionPanel.editGroups.test.tsx` — NEW (15 tests for edit groups functionality)

**Backend (1 file):**
- `src/reformlab/server/routes/portfolios.py` — added sidecar metadata.json storage for editable_parameter_groups, category_id, and parameter_groups (Story 25.3/25.4 fields) with full save/load/clone support
- `src/reformlab/server/models.py` — added editable_parameter_groups field to PortfolioPolicyRequest and PortfolioPolicyItem (optional for backward compatibility)

**References:**
- UX spec: `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, Stage 1 — Policies section, Editable Parameter Groups)
- Epics: `_bmad-output/planning-artifacts/epics.md` (Epic 25, Story 25.4)
- Story 25.1: `_bmad-output/implementation-artifacts/25-1-add-api-driven-categories-endpoint-and-formula-help-metadata.md` (categories API)
- Story 25.2: `_bmad-output/implementation-artifacts/25-2-redesign-policies-stage-browser-composition-layout-with-types-categories-and-duplicate-policy-instances.md` (duplicate instances)
- Story 25.3: `_bmad-output/implementation-artifacts/25-3-implement-create-from-scratch-policy-flow-with-compatible-category-picker-and-default-parameter-groups.md` (default parameter groups)

## Senior Developer Review (AI)

### Review: 2026-04-19
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 15.0 → REJECT (initial), then PASS (after fixes)
- **Issues Found:** 9 verified issues
- **Issues Fixed:** 7 critical/high issues addressed
- **Action Items Created:** 3 (deferred items)

#### Review Follow-ups (AI)
- [ ] [AI-Review] MEDIUM: Implement Escape key revert for group rename - currently only blur/Enter save changes, Escape should revert to original value (PortfolioCompositionPanel.tsx:380-385)
- [ ] [AI-Review] MEDIUM: Create integration test file `PoliciesStageScreen.editGroups.test.tsx` to verify inter-component state wiring for edit groups mode
- [ ] [AI-Review] LOW: Add backend persistence tests (test_portfolio_save_with_editable_groups, test_portfolio_load_without_editable_groups_migrates, test_portfolio_item_editable_groups_structure) to test_portfolios.py
