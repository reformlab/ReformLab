# Story 27.4: Unify template vs from-scratch policy card visuals

Status: ready-for-dev

## Story

As an analyst composing a policy set,
I want template-instantiated policies and from-scratch policies to look and behave identically in the composition panel,
so that the source of a policy is not visible in its UI treatment and editing affordances are consistent.

## Acceptance Criteria

1. Given two policies side by side (one from-template, one from-scratch), when displayed in the composition panel, then their card structure, controls, and editing affordances are visually identical.
2. Given a template-instantiated policy, when added to the composition, then `editableParameterGroups` is populated using the same scaffolding logic that from-scratch policies use, so the unified renderer has data.
3. Given a template policy, when "Edit groups" is clicked, then group rename, add, move, delete-empty, and block-delete-non-empty work with the same UI and behaviour as Story 25.4 specified for from-scratch policies.
4. Given group edits on a template policy, when the policy set is saved and reloaded, then group names, order, and parameter membership persist (extends Story 25.5 reload coverage).
5. Given the unified `<PolicyCard>` component (extracted in this story), when used by both the from-template and from-scratch flows, then no source-specific branching exists in the renderer (only data differs).
6. Given the existing template-add tests and the existing from-scratch-add tests, when run, then both cover the unified card with identical assertions.

## Tasks / Subtasks

- [ ] Extract `<PolicyCard>` component (AC: #1, #5)
  - [ ] In `PortfolioCompositionPanel.tsx:324-773`, identify the rendering logic and split it into a new component `frontend/src/components/simulation/PolicyCard.tsx`
  - [ ] The component takes a single `entry: CompositionEntry` and emits the same callbacks the panel emits today (onParameterChange, onGroupRename, onAddGroup, onDeleteGroup, onMoveParameter, onRemove)
  - [ ] Move all card-specific state (isExpanded, isHighlighted) into the PolicyCard component
  - [ ] Move the helper functions (formatParameterValue, resolveParameterValue, summarizeParameterGroup, summarizeRateSchedule) into the new file or a shared utils file
- [ ] Populate `editableParameterGroups` for template policies (AC: #2, #3)
  - [ ] Find the template-add code path in `PoliciesStageScreen.tsx:166-180` (`addTemplateInstance` function)
  - [ ] On add, scaffold `editableParameterGroups` from the template's parameter schema using the same factory used for from-scratch policies (lines 194-206 in `handleCreateBlankPolicy`)
  - [ ] The scaffolding should map parameters to groups based on their `group` field in the schema
  - [ ] Use deterministic group IDs: `group-0`, `group-1`, etc. to match from-scratch behavior
- [ ] Lift "Edit groups" affordance for both sources (AC: #3)
  - [ ] Remove the source-specific branch at `PortfolioCompositionPanel.tsx:485` that checks `entry.editableParameterGroups && entry.editableParameterGroups.length > 0`
  - [ ] Show the gear icon whenever `editableParameterGroups` is present (regardless of policy source)
  - [ ] Ensure all edit-group callbacks work identically for both template and from-scratch policies
- [ ] Persistence + reload coverage (AC: #4)
  - [ ] Add or extend tests in `frontend/src/components/screens/__tests__/PoliciesStageScreen.policySets.test.tsx` covering: template policy → group rename → save → reload → name persisted
  - [ ] Same flow for: template policy → group add → save → reload
  - [ ] Verify the portfolio save/load round-trip preserves `editableParameterGroups` for template policies
- [ ] Side-by-side test (AC: #1, #6)
  - [ ] Add test in `frontend/src/components/simulation/__tests__/PortfolioCompositionPanel.test.tsx`
  - [ ] Render test: one template policy + one from-scratch policy → assert identical DOM structure for card frame, group section, controls
  - [ ] Verify className matching for badges, borders, and spacing
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- **Sequencing:** This story depends on Story 27.3 (live parameter values in cards) so the unified renderer has informative content. Story 27.3 was completed on 2026-04-29.
- **Cross-checks:** This work does NOT change the underlying API contract for portfolios. `instanceId`, `templateId`, `parameters`, `rateSchedule`, and `editableParameterGroups` all already exist in `CompositionEntry`. We're only making the UI consistent.
- **Story 27.11** will later unify the type system itself (`CompositionEntry` ↔ `PortfolioPolicyItem`), which makes this renderer extraction even cleaner.
- **Key insight:** The main visual difference is that template-based policies show a parameter count badge (`template.parameterCount`) while from-scratch policies do not. Once both use `editableParameterGroups`, this can be unified to `editableParameterGroups.flatMap(g => g.parameterIds).length`.

### Current State Analysis

**Template-based policy creation** (`PoliciesStageScreen.tsx:166-180`):
```tsx
const addTemplateInstance = useCallback((templateId: string) => {
  const t = templates.find((tmpl) => tmpl.id === templateId);
  if (!t) return;

  const id = instanceCounterRef.current++;
  const newInstance: CompositionEntry = {
    instanceId: `${templateId}-ins${id}`,
    templateId,
    name: t?.name ?? templateId,
    parameters: {},
    rateSchedule: {},
    // ❌ NO editableParameterGroups scaffolded here
  };

  setComposition((prev) => [...prev, newInstance]);
}, [templates]);
```

**From-scratch policy creation** (`PoliciesStageScreen.tsx:182-235`):
```tsx
const handleCreateBlankPolicy = useCallback(async (
  policyType: "tax" | "subsidy" | "transfer",
  categoryId: string,
) => {
  const response = await createBlankPolicy({
    policy_type: policyType,
    category_id: categoryId,
  });

  // ✅ editableParameterGroups ARE scaffolded here
  const editableParameterGroups = response.parameter_groups.map((groupName: string, idx: number) => ({
    id: `group-${idx}`,
    name: groupName,
    parameterIds: DEFAULT_PARAM_ASSIGNMENTS[groupName] ?? [],
  }));

  const newInstance: CompositionEntry = {
    instanceId: `blank-${id}`,
    templateId: "", // Empty for from-scratch
    name: response.name,
    parameters: response.parameters as Record<string, number>,
    rateSchedule: response.rate_schedule,
    policy_type: response.policy_type,
    category_id: response.category_id,
    parameter_groups: response.parameter_groups,
    editableParameterGroups, // ✅ Present
  };

  setComposition((prev) => [...prev, newInstance]);
}, []);
```

**Visual discrepancy in card rendering** (`PortfolioCompositionPanel.tsx:369-374`):
```tsx
{/* Story 25.3: Parameter count badge - only show for template-based policies */}
{template && (
  <Badge variant="default" className="text-xs shrink-0">
    {template.parameterCount} params
  </Badge>
)}
```
- Template-based: Shows badge (e.g., "8 params")
- From-scratch: No badge (because `templateId: ""` means no template match)

**Edit groups button** (`PortfolioCompositionPanel.tsx:485-500`):
```tsx
{onToggleEditGroups && entry.editableParameterGroups && entry.editableParameterGroups.length > 0 && (
  <button
    type="button"
    onClick={() => onToggleEditGroups(index)}
    className={...}
    aria-label="Edit parameter groups"
    title="Customize parameter groups"
  >
    <Settings className="h-3 w-3" />
  </button>
)}
```
- From-scratch: Has `editableParameterGroups` → shows gear icon
- Template-based: No `editableParameterGroups` → no gear icon

### Implementation Strategy

**1. Scaffold editableParameterGroups for template policies:**

In `addTemplateInstance`, after creating the base instance:
```tsx
// Get parameter schemas for this template
const schemas = parameterSchemas[templateId] ?? [];

// Group parameters by their 'group' field
const groupsMap = new Map<string, string[]>();
for (const schema of schemas) {
  const groupName = schema.group || "Other";
  if (!groupsMap.has(groupName)) {
    groupsMap.set(groupName, []);
  }
  groupsMap.get(groupName)!.push(schema.id);
}

// Convert to editableParameterGroups format
const editableParameterGroups = Array.from(groupsMap.entries()).map(([name, parameterIds], idx) => ({
  id: `group-${idx}`,
  name,
  parameterIds,
}));

const newInstance: CompositionEntry = {
  // ... existing fields
  editableParameterGroups,
};
```

**2. Update parameter count badge to use editableParameterGroups:**

Replace the template-only badge with:
```tsx
{entry.editableParameterGroups && (
  <Badge variant="default" className="text-xs shrink-0">
    {entry.editableParameterGroups.reduce((sum, g) => sum + g.parameterIds.length, 0)} params
  </Badge>
)}
```

**3. PolicyCard component extraction:**

Create `frontend/src/components/simulation/PolicyCard.tsx`:
```tsx
export interface PolicyCardProps {
  entry: CompositionEntry;
  template?: Template;
  schemas: Parameter[];
  index: number;
  isFirst: boolean;
  isLast: boolean;
  categories?: Category[] | null;
  editGroupsIndex: number | null;
  validationError?: PolicyValidationError;
  onToggleEditGroups?: (index: number) => void;
  onGroupRename?: (policyIndex: number, groupId: string, newName: string) => void;
  onAddGroup?: (policyIndex: number) => void;
  onDeleteGroup?: (policyIndex: number, groupId: string) => void;
  onMoveParameter?: (policyIndex: number, paramId: string, fromGroupId: string, toGroupId: string) => void;
  onRemove: (index: number) => void;
  onReorder: (fromIndex: number, toIndex: number) => void;
  onParameterChange: (index: number, paramId: string, value: number) => void;
  onRateScheduleChange: (index: number, schedule: Record<string, number>) => void;
}

export function PolicyCard({ entry, template, schemas, ...props }: PolicyCardProps) {
  // Move card-specific state here
  const [isExpanded, setIsExpanded] = useState(false);
  const [highlightedGroupId, setHighlightedGroupId] = useState<string | null>(null);

  // Move helper functions here or import from utils

  // Return the card JSX (lines 324-773 from PortfolioCompositionPanel.tsx)
}
```

### Data Structures

**CompositionEntry interface** (PortfolioCompositionPanel.tsx:38-54):
```tsx
export interface CompositionEntry {
  templateId: string;
  name: string;
  parameters: Record<string, number>;
  rateSchedule: Record<string, number>;
  instanceId?: string;
  policy_type?: string;
  category_id?: string;
  parameter_groups?: string[];
  editableParameterGroups?: EditableParameterGroup[];
}
```

**EditableParameterGroup** (types.ts:323-327):
```tsx
export interface EditableParameterGroup {
  id: string;
  name: string;
  parameterIds: string[];
}
```

**Parameter schema** (mock-data.ts:28-38):
```tsx
export interface Parameter {
  id: string;
  label: string;
  value: number;
  baseline: number;
  unit: string;
  group: string; // ← Used for grouping parameters
  type: "slider" | "number";
  min?: number;
  max?: number;
}
```

### Project Structure Notes

**New file:**
- `frontend/src/components/simulation/PolicyCard.tsx` — Extracted card component

**Modified files:**
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — Use PolicyCard component
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — Scaffold editableParameterGroups in addTemplateInstance
- `frontend/src/components/simulation/__tests__/PortfolioCompositionPanel.test.tsx` — Add side-by-side visual consistency test
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.policySets.test.tsx` — Add persistence tests for template policy groups

**No backend changes** — This is purely frontend UI unification

### References

- [Source: _bmad-output/planning-artifacts/epics.md] — Story 27.4 description
- [Source: frontend/src/components/simulation/PortfolioCompositionPanel.tsx:324-773] — Card rendering logic to extract
- [Source: frontend/src/components/simulation/PortfolioCompositionPanel.tsx:485-500] — Edit groups button (source-specific)
- [Source: frontend/src/components/simulation/PortfolioCompositionPanel.tsx:369-374] — Parameter count badge (template-only)
- [Source: frontend/src/components/screens/PoliciesStageScreen.tsx:166-180] — Template add function (needs editableParameterGroups)
- [Source: frontend/src/components/screens/PoliciesStageScreen.tsx:194-206] — From-scratch editableParameterGroups scaffolding (reference)
- [Source: Story 25.4 completion notes] — Editable parameter groups implementation
- [Source: Story 27.3 completion notes] — Shows inline parameter values were recently implemented

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (glm-4.7)

### Debug Log References

### Completion Notes List

<!-- Populated after implementation is complete -->

### File List

<!-- Populated after implementation is complete -->
