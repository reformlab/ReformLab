# Story 27.3: Show actual parameter values inline in policy cards

Status: ready-for-dev

## Story

As an analyst scanning a policy composition,
I want each policy card to surface its actual parameter values (rates, thresholds, schedules) without me having to expand it,
so that I can recognise and compare policies at a glance instead of reading uppercase parameter-group names that carry no information.

## Acceptance Criteria

1. Given a collapsed policy card with a populated rate schedule, when displayed, then the card shows headline parameter values per group (e.g., `Rate schedule → €45/tCO₂ in 2025`) instead of the generic chip `6 PARAMS` and the bare uppercase group names like `RATE_SCHEDULE`, `EXEMPTIONS`, etc.
2. Given a parameter group with no customised values, when displayed, then the default value is shown (no fake placeholder values like `rate: 0` or `unit: EUR` unless those are real defaults).
3. Given the analyst clicks a group chip on a collapsed card, when actioned, then the card expands and scrolls to that group with the relevant parameters visually highlighted.
4. Given the existing hardcoded placeholder block at `frontend/src/components/simulation/PortfolioCompositionPanel.tsx:471-513`, when this story is complete, then no hardcoded placeholder parameter values remain — all displayed values are derived from `entry.parameters` (or the equivalent live source).
5. Given a from-scratch policy whose parameter groups are empty by design, when displayed, then the card communicates "Parameters not yet set" per group rather than fake values.
6. Given the click-to-preview affordance, when group chip clicks are tested, then the card's expand state, scroll target, and highlight state are asserted in unit tests.

## Tasks / Subtasks

- [ ] Replace hardcoded placeholders (AC: #1, #2, #4)
  - [ ] At `PortfolioCompositionPanel.tsx:471-513`, remove the static `rate: 0`, `unit: EUR`, `threshold: 0`, `ceiling: null` hardcoded values
  - [ ] Derive headline values from `entry.parameters` keyed by parameter-group membership; if `entry.editableParameterGroups` exists, use it as the authoritative grouping source
  - [ ] If a parameter has no value and no default, display "—" rather than a fabricated zero
- [ ] Headline-value formatter (AC: #1)
  - [ ] Add a helper `summariseParameterGroup(group, parameters): string` that returns a one-line summary per group (e.g., `Rate schedule → €45/tCO₂ in 2025; €60/tCO₂ in 2030`)
  - [ ] For a rate schedule, prefer the first year's rate or "scheduled" label
  - [ ] For a threshold, show value+unit
  - [ ] For exemptions, show count of exempt categories
- [ ] Click-to-preview affordance (AC: #3, #6)
  - [ ] Wrap each group chip on the collapsed card in a `<button>` that triggers expand + scroll-to-group
  - [ ] Add a `data-group-id` on the expanded group container so the scroll/highlight target is unambiguous
  - [ ] Add a brief CSS highlight (`ring-2 ring-blue-300` for ~1s) on the targeted group
- [ ] Empty-state per group (AC: #5)
  - [ ] If a group has no parameters set, the headline reads "Not yet set" or equivalent; clicking still expands and scrolls
- [ ] Tests (AC: #6)
  - [ ] Render test: collapsed card shows real values for each group
  - [ ] Click test: clicking a group chip expands, scrolls, and highlights
  - [ ] Empty-state test: ungrouped/unset parameters show "—" or "Not yet set"
- [ ] Quality gates
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- The current renderer at `:471-513` predates EPIC-25's editable parameter groups; it uses static placeholders that look like data. This story replaces it with live derivation.
- Story 27.4 (unify template vs from-scratch) is the natural follow-up — once both card sources share a renderer, this story's improvements apply uniformly. Sequencing: 27.3 first (fix the renderer), then 27.4 (apply it to both sources).
- The screenshots in the user report show the issue: chips like `6 PARAMS`, `RATE_SCHEDULE`, `EXEMPTIONS` are label-only.

### Data Structures

**CompositionEntry** (PortfolioCompositionPanel.tsx:37-53):
```tsx
export interface CompositionEntry {
  templateId: string;
  name: string;
  parameters: Record<string, number>;  // ← Configured values
  rateSchedule: Record<string, number>;
  instanceId?: string;
  policy_type?: string;
  category_id?: string;
  parameter_groups?: string[];  // Legacy static groups
  editableParameterGroups?: EditableParameterGroup[];  // Story 25.4 groups
}
```

**EditableParameterGroup** (frontend/src/api/types.ts:323-327):
```tsx
export interface EditableParameterGroup {
  id: string;
  name: string;
  parameterIds: string[];
}
```

**Parameter schemas** (available via `parameterSchemas` prop):
```tsx
parameterSchemas?: Record<string, Parameter[]>;
// Usage: const schemas = parameterSchemas[entry.templateId] ?? [];
```

**Parameter type** (frontend/src/data/mock-data.ts:28-38):
```tsx
export interface Parameter {
  id: string;
  label: string;
  value: number;
  baseline: number;
  unit: string;  // ← Use for display formatting
  group: string;
  type: "slider" | "number";
  min?: number;
  max?: number;
}
```

### Existing Formatting Patterns

**Value formatting** (ParameterRow.tsx:16-21) - reuse for consistency:
```tsx
function formatValue(parameter: Parameter, value: number): string {
  if (parameter.unit === "%") {
    return `${Math.round(value * 100)}%`;
  }
  return `${value} ${parameter.unit}`;
}
```

**Rate schedule display** (YearScheduleEditor usage in panel):
- `entry.rateSchedule` is `Record<string, number>` where keys are year strings
- For headline summary, prefer first year: `Object.entries(entry.rateSchedule)[0]?.[1]`
- If empty, show "Not scheduled"

### Implementation Pattern

```tsx
// Helper to summarize a parameter group
function summarizeParameterGroup(
  group: EditableParameterGroup | string,
  entry: CompositionEntry,
  schemas: Parameter[]
): string {
  const groupIds = typeof group === 'string'
    ? schemas.filter(p => p.group === group).map(p => p.id)
    : group.parameterIds;

  if (groupIds.length === 0) return "Not yet set";

  const parts = groupIds.map(paramId => {
    const value = entry.parameters[paramId];
    const schema = schemas.find(s => s.id === paramId);

    if (value === undefined) return "—";
    if (!schema) return `${value}`;

    // Reuse ParameterRow formatting logic
    if (schema.unit === "%") {
      return `${Math.round(value * 100)}%`;
    }
    return `${value} ${schema.unit}`;
  });

  return parts.join("; ");
}
```

### Click-to-Preview Implementation

```tsx
// Add to PortfolioCompositionPanel state
const [highlightedGroupId, setHighlightedGroupId] = useState<string | null>(null);

// Handler for group chip click
const handleGroupChipClick = (groupId: string, index: number) => {
  // Expand the card
  setExpandedIndices(prev => new Set(prev).add(index));

  // Set highlight
  setHighlightedGroupId(groupId);

  // Scroll to group (next tick after DOM update)
  setTimeout(() => {
    const el = document.querySelector(`[data-group-id="${groupId}"]`);
    el?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Remove highlight after animation
    setTimeout(() => setHighlightedGroupId(null), 1000);
  }, 0);
};

// In render, add data attribute and highlight class
<div
  key={group.id}
  data-group-id={group.id}
  className={cn(
    "border border-slate-200 rounded p-2 bg-slate-50",
    highlightedGroupId === group.id && "ring-2 ring-blue-300 transition-all"
  )}
>
```

### Project Structure Notes

**Files to modify:**
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` - Main implementation
- `frontend/src/components/simulation/__tests__/PortfolioCompositionPanel.test.tsx` - Tests (or create new file)

**Optional new file:**
- `frontend/src/utils/policy-summary.ts` - Extract `summarizeParameterGroup` helper for reusability

**No backend changes** - This is purely frontend display logic

### Test Data Pattern

```tsx
// Mock composition with realistic parameter values
const mockComposition: CompositionEntry[] = [
  {
    templateId: "carbon-tax-flat",
    name: "Carbon Tax — Flat Rate",
    parameters: {
      tax_rate: 44,
      exemption_threshold: 15000,
      rate_schedule_2025: 44,
      rate_schedule_2026: 50,
    },
    rateSchedule: { "2025": 44, "2026": 50 },
    instanceId: "inst-1",
    editableParameterGroups: [
      { id: "mechanism", name: "Mechanism", parameterIds: ["tax_rate"] },
      { id: "eligibility", name: "Eligibility", parameterIds: ["exemption_threshold"] },
      { id: "schedule", name: "Schedule", parameterIds: ["rate_schedule_2025", "rate_schedule_2026"] },
    ],
  },
];
```

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.3]
- [Source: frontend/src/components/simulation/PortfolioCompositionPanel.tsx:186-352] - Card header structure
- [Source: frontend/src/components/simulation/PortfolioCompositionPanel.tsx:471-513] - Hardcoded placeholder block to replace
- [Source: frontend/src/components/simulation/ParameterRow.tsx:16-21] - Value formatting logic to reuse
- [Source: frontend/src/data/mock-data.ts:28-38] - Parameter interface definition
- [Source: frontend/src/api/types.ts:323-327] - EditableParameterGroup interface
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#1553] - "primary parameter summary in collapsed card header"
- [Source: User report 2026-04-26 (screenshots showing 6 PARAMS chips)]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
