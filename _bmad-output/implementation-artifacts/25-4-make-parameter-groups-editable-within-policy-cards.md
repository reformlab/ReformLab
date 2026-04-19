# Story 25.4: Make parameter groups editable within policy cards

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want **to edit parameter groups within policy cards (rename, add, move parameters between groups, delete empty groups)**,
so that **I can customize the organization of policy parameters to match my analytical workflow and mental model**.

## Acceptance Criteria

1. **Given** a policy card in the composition panel, **when** the analyst clicks the "Edit groups" icon action, **then** edit-groups mode activates for that policy card, showing group editing controls while keeping parameter value editing available.
2. **Given** a policy card in edit-groups mode, **when** the analyst renames a group inline, **then** the new name persists and displays correctly on collapse and expand, and the name survives save/reload cycles.
3. **Given** a policy card in edit-groups mode, **when** the analyst adds a new empty group, **then** an empty group appears in the group list with a default name (e.g., "New Group") that can be renamed and can receive moved parameters.
4. **Given** an empty parameter group (no parameters), **when** the analyst clicks delete, **then** the group is removed from the policy card.
5. **Given** a non-empty group (has one or more parameters), **when** delete is attempted, **then** the delete action is disabled with a tooltip or disabled action label explaining "Remove all parameters before deleting this group" (or similar), and the parameters remain intact.
6. **Given** a policy card in edit-groups mode, **when** the analyst moves a parameter from one group to another, **then** the parameter appears in the target group and disappears from the source group, and this organization persists through collapse/expand, save, and reload.
7. **Given** the policy card is collapsed while in edit-groups mode, **when** expanded again, **then** edit-groups mode remains active and all group edits are preserved.
8. **Given** a policy with edited groups is saved and reloaded, **then** the group names, order, and parameter memberships are restored correctly.

## Tasks / Subtasks

- [ ] **Add "Edit groups" icon action to policy card header** (AC: 1)
  - [ ] Add Settings/Gear icon button from lucide-react to card header action buttons (before Move up or after Remove)
  - [ ] Icon button should have accessible label: "Edit parameter groups" and tooltip: "Customize parameter groups"
  - [ ] Clicking the button toggles edit-groups mode for that specific policy card (not global)
  - [ ] Edit-groups mode should have visual indicator: subtle blue border around card or "Editing" badge
  - [ ] Other policy cards should remain unaffected (mode is per-card, not global)

- [ ] **Add edit-groups mode state management** (AC: 1, 7)
  - [ ] Add `editGroupsIndex: number | null` state to `PoliciesStageScreen` to track which card is in edit-groups mode
  - [ ] Add `onToggleEditGroups(index: number)` callback to PortfolioCompositionPanel props
  - [ ] Pass `editGroupsIndex` and `onToggleEditGroups` from PoliciesStageScreen to PortfolioCompositionPanel
  - [ ] In PortfolioCompositionPanel, use `editGroupsIndex === index` to determine if current card is in edit-groups mode
  - [ ] Ensure edit-groups mode persists across collapse/expand (don't reset when toggling expansion)

- [ ] **Extend CompositionEntry with editable parameter groups structure** (AC: 2, 3, 6)
  - [ ] Extend `CompositionEntry` interface with `editableParameterGroups?: EditableParameterGroup[]` field
  - [ ] Define `EditableParameterGroup` interface with:
    - `id: string` — unique group identifier (e.g., `group-${Date.now()}`)
    - `name: string` — display name (e.g., "Mechanism", "Eligibility", "Custom Group")
    - `parameterIds: string[]` — list of parameter IDs in this group
  - [ ] For from-scratch policies: convert `parameter_groups: string[]` to editable structure on mount (generate IDs)
  - [ ] For template-based policies: initialize editable groups from template's `parameter_groups` or default groups if not specified
  - [ ] Backend: Add `editable_parameter_groups` field to `PortfolioPolicyRequest` and `PortfolioPolicyItem` (optional for backward compatibility)

- [ ] **Implement group rename inline editing** (AC: 2)
  - [ ] In edit-groups mode, group names should be editable text inputs
  - [ ] Use Input component with transparent background, borderless, appearing as text until focused
  - [ ] On focus: show blue outline, editable text
  - [ ] On blur or Enter: save new name
  - [ ] On Escape: revert to original name
  - [ ] Add callback `onGroupRename(index: number, groupId: string, newName: string)` to parent

- [ ] **Implement add new empty group** (AC: 3)
  - [ ] Add "+ Add group" button at bottom of parameter groups list in edit-groups mode
  - [ ] Button should be secondary style (outline) with small size
  - [ ] Clicking creates new group with:
    - `id: \`group-${Date.now()}\``
    - `name: "New Group"`
    - `parameterIds: []`
  - [ ] New group appears immediately and can be renamed
  - [ ] Add callback `onAddGroup(index: number)` to parent

- [ ] **Implement delete empty group** (AC: 4, 5)
  - [ ] Add trash/delete icon button next to each group name in edit-groups mode
  - [ ] Delete button is disabled if `parameterIds.length > 0`
  - [ ] When disabled, show tooltip: "Remove all parameters before deleting this group"
  - [ ] When enabled, clicking removes group from the list
  - [ ] Add callback `onDeleteGroup(index: number, groupId: string)` to parent

- [ ] **Implement parameter move between groups** (AC: 6)
  - [ ] In edit-groups mode, each parameter should have a move affordance
  - [ ] Use Select dropdown to move parameter to another group (shows all group names)
  - [ ] Or use drag handle with @dnd-kit library (if already in project) for drag-and-drop
  - [ ] On move: remove param from source group, add to target group
  - [ ] Add callback `onMoveParameter(policyIndex: number, paramId: string, fromGroupId: string, toGroupId: string)` to parent

- [ ] **Update parameter groups display in edit-groups mode** (AC: 1, 6)
  - [ ] Modify the existing parameter groups display (Story 25.3 code) to support edit mode
  - [ ] In normal mode: show groups as static display (current Story 25.3 behavior)
  - [ ] In edit-groups mode: show groups with edit controls (rename input, delete button, move dropdown for params)
  - [ ] Keep parameter value editing available in both modes
  - [ ] Ensure the primary parameter summary in collapsed header still shows correctly

- [ ] **Persist editable parameter groups in portfolio save/load** (AC: 8)
  - [ ] Update `createPortfolio()` API call to include `editable_parameter_groups` for each policy
  - [ ] Backend: Extend `PortfolioPolicyRequest` to accept `editable_parameter_groups` (optional field)
  - [ ] Backend: Store editable parameter groups in portfolio persistence layer
  - [ ] Update `usePortfolioLoadDialog.ts` to restore `editableParameterGroups` from loaded portfolio data
  - [ ] Ensure round-trip: save → reload → verify all group edits preserved

- [ ] **Backend: Extend portfolio models for editable parameter groups** (AC: 8)
  - [ ] Add `editable_parameter_groups: list[dict[str, Any]] | None = None` to `PortfolioPolicyRequest`
  - [ ] Add `editable_parameter_groups: list[dict[str, Any]] | None = None` to `PortfolioPolicyItem`
  - [ ] Structure each editable group as: `{"id": str, "name": str, "parameter_ids": list[str]}`
  - [ ] Ensure backward compatibility: policies without editable groups use default groups from template

- [ ] **Frontend types: Add editable parameter group interfaces** (AC: 2, 3, 6)
  - [ ] Add `EditableParameterGroup` interface to `frontend/src/api/types.ts`:
    ```typescript
    export interface EditableParameterGroup {
      id: string;
      name: string;
      parameterIds: string[];
    }
    ```
  - [ ] Extend `CompositionEntry` with `editableParameterGroups?: EditableParameterGroup[]`
  - [ ] Extend `PortfolioPolicyRequest` with `editable_parameter_groups?: EditableParameterGroup[]`
  - [ ] Extend `PortfolioPolicyItem` with `editable_parameter_groups?: EditableParameterGroup[]`

- [ ] **UI polish and accessibility** (AC: 1)
  - [ ] Ensure "Edit groups" button has proper focus indicator and keyboard navigation
  - [ ] Add aria-label to all edit mode controls (rename input, delete button, move dropdown)
  - [ ] Ensure color contrast meets WCAG AA for disabled delete state
  - [ ] Add visual transition when entering/exiting edit-groups mode
  - [ ] Test keyboard-only navigation through edit groups controls

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
- Persists the editable structure as `editable_parameter_groups` in addition to or replacing the simple string array

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

2. **Parameter-to-group mapping:** When initializing editable groups from templates, need to determine which parameters belong in which groups. Template schemas may not specify this explicitly — need a sensible default (all parameters in first group, or by parameter name pattern).

3. **From-scratch policy parameters:** From-scratch policies have placeholder parameters (`rate`, `unit`, `threshold`, `ceiling`) but no explicit parameter schema. Need to assign these to appropriate default groups:
   - Mechanism: `rate`, `unit`
   - Eligibility: `threshold`, `ceiling`
   - Schedule: (empty, uses year schedule editor)
   - Redistribution (Tax only): `divisible`, `recipients`

4. **Backward compatibility:** Portfolios saved before Story 25.4 won't have `editable_parameter_groups`. Need to migrate on load: if missing, generate editable groups from `parameter_groups` string array or template defaults.

5. **Edit mode state confusion:** Ensure edit mode doesn't get confused when multiple policy cards exist. Each card has independent edit mode state tracked by `editGroupsIndex`.

6. **Parameter move dropdown rendering:** In edit mode, showing a Select dropdown for every parameter may clutter the UI. Consider a more compact affordance (e.g., small move icon that opens a popover with group options).

7. **Save button disabled during edit:** Should save be disabled while a policy is in edit-groups mode? Probably not — edits are auto-saved to local state, portfolio save includes current editable groups.

8. **Group name validation:** Prevent empty group names or duplicate group names within a policy. Add validation on blur: if name is empty or duplicate, revert to previous value with error message.

9. **Last group cannot be deleted:** Prevent deletion of the last remaining group (need at least one group). Add check: `groups.length > 1` before allowing delete.

10. **Revert changes:** How does analyst undo group edits? For now, manual undo (re-edit). Future story could add "Reset to template defaults" button.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Completion Notes List

**Ultimate context engine analysis completed - comprehensive developer guide created.**

### File List

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

**References:**
- UX spec: `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, Stage 1 — Policies section, Editable Parameter Groups)
- Epics: `_bmad-output/planning-artifacts/epics.md` (Epic 25, Story 25.4)
- Story 25.1: `_bmad-output/implementation-artifacts/25-1-add-api-driven-categories-endpoint-and-formula-help-metadata.md` (categories API)
- Story 25.2: `_bmad-output/implementation-artifacts/25-2-redesign-policies-stage-browser-composition-layout-with-types-categories-and-duplicate-policy-instances.md` (duplicate instances)
- Story 25.3: `_bmad-output/implementation-artifacts/25-3-implement-create-from-scratch-policy-flow-with-compatible-category-picker-and-default-parameter-groups.md` (default parameter groups)
