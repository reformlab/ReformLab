# Story 25.3: Implement create-from-scratch policy flow with compatible category picker and default parameter groups

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want **to create policies from scratch by selecting a policy type and compatible category, receiving a policy with default parameter groups pre-populated**,
so that **I can quickly build custom policies without starting from a template that may not match my intended use case**.

## Acceptance Criteria

1. **Given** the Policies stage, **when** the analyst clicks "+ Add Policy", **then** two paths are offered: "From template" (existing flow) and "From scratch" (new flow).
2. **Given** the from-scratch flow, **when** a policy type is selected (Tax / Subsidy / Transfer), **then** only categories whose `compatible_types` includes the selected type are shown.
3. **Given** a type and category selection, **when** confirmed, **then** a new policy appears in the composition panel with the correct type badge (amber/emerald/blue), category badge, and default parameter groups for the selected type.
4. **Given** a Tax policy created from scratch, **when** expanded, **then** it shows four default parameter groups: Mechanism, Eligibility, Schedule, and Redistribution.
5. **Given** a Subsidy policy created from scratch, **when** expanded, **then** it shows three default parameter groups: Mechanism, Eligibility, and Schedule (no Redistribution group).
6. **Given** a Transfer policy created from scratch, **when** expanded, **then** it shows three default parameter groups: Mechanism, Eligibility, and Schedule (no Redistribution group).
7. **Given** the new policy, **when** the analyst edits its parameters and saves the policy set, **then** the from-scratch policy persists and reloads correctly with all edits intact.

## Tasks / Subtasks

- [ ] **Add from-scratch policy type selection dialog** (AC: 1, 2)
  - [ ] Create `CreateFromScratchDialog.tsx` component with three-step flow (type → category → confirm)
  - [ ] Implement step 1: Three large clickable cards for Tax (amber), Subsidy (emerald), Transfer (blue) with one-line descriptions
  - [ ] Implement step 2: Category grid filtered by `compatible_types` from categories API
  - [ ] Implement step 3: Confirmation showing selected type badge + category badge + auto-generated name `"{Type} — {Category}"`
  - [ ] Add keyboard navigation (Enter/Space to select, Escape to cancel)
  - [ ] Add visible step indicator (1/2/3 dots with labels)

- [ ] **Backend: Add blank policy scaffold endpoint** (AC: 3, 4, 5, 6)
  - [ ] Add `CreateBlankPolicyRequest` model to `src/reformlab/server/models.py` with fields: `policy_type: str`, `category_id: str`
  - [ ] Add `POST /api/templates/from-scratch` route in `src/reformlab/server/routes/templates.py`
  - [ ] Implement blank policy generation with placeholder parameters (rate = 0, threshold = 0, etc.)
  - [ ] Return policy structure with default parameter groups based on type (Mechanism, Eligibility, Schedule, + Redistribution for Tax only)
  - [ ] Validate that `category_id` exists in categories registry
  - [ ] Validate that `policy_type` is one of the closed set (tax, subsidy, transfer)
  - [ ] Validate that category's `compatible_types` includes the requested policy_type

- [ ] **Frontend API wrapper for from-scratch endpoint** (AC: 3)
  - [ ] Add `CreateBlankPolicyRequest` interface to `frontend/src/api/types.ts`
  - [ ] Add `createBlankPolicy(request: CreateBlankPolicyRequest)` function to `frontend/src/api/templates.ts`
  - [ ] Add return type for blank policy structure with default groups

- [ ] **Integrate from-scratch dialog into Policies stage** (AC: 1, 3, 7)
  - [ ] Update `PoliciesStageScreen.tsx` to show choice dialog on "+ Add Policy" click
  - [ ] Add "From template" path: closes dialog, triggers existing template browser click
  - [ ] Add "From scratch" path: opens `CreateFromScratchDialog`
  - [ ] On from-scratch confirmation, call `createBlankPolicy()` API
  - [ ] Add resulting policy to composition with unique instanceId (using existing instanceCounterRef)
  - [ ] Auto-generate policy name from type label + category label (e.g., "Tax — Carbon Emissions")
  - [ ] Close dialog and scroll to new policy in composition panel

- [ ] **Composition panel: display default parameter groups** (AC: 4, 5, 6)
  - [ ] Update `PortfolioCompositionPanel` to render parameter groups when expanded
  - [ ] Display groups in order: Mechanism, Eligibility, Schedule, Redistribution (Tax only)
  - [ ] Show placeholder parameters with sensible defaults (rate = 0, threshold = 0, ceiling = 0)
  - [ ] Each group should be collapsible (expand/collapse chevron)
  - [ ] Groups should show parameter count badge (e.g., "3 params")

- [ ] **Persistence and reload** (AC: 7)
  - [ ] Ensure from-scratch policies save correctly via `createPortfolio()` API
  - [ ] Ensure from-scratch policies load correctly via `getPortfolio()` API
  - [ ] Verify parameter edits persist after save/load cycle
  - [ ] Verify instanceId uniqueness is preserved across reloads

- [ ] **Testing** (AC: 1, 2, 3, 4, 5, 6, 7)
  - [ ] Backend tests for blank policy generation with valid/invalid type and category combinations
  - [ ] Backend tests for compatible_types validation (tax with carbon_emissions OK, tax with income reject if not compatible)
  - [ ] Frontend tests for from-scratch dialog: type selection → category filtering → confirmation
  - [ ] Frontend tests for blank policy creation and addition to composition
  - [ ] Frontend tests for default parameter groups display (Tax has 4 groups, Subsidy/Transfer have 3)
  - [ ] Frontend tests for policy name generation (type + category format)
  - [ ] Persistence tests: save from-scratch policy, reload, verify edits intact
  - [ ] Regression tests: verify existing from-template flow still works unchanged

## Dev Notes

### Architecture Patterns and Constraints

**Backend - Server Layer:**
- Location: `src/reformlab/server/routes/`
- Pydantic v2 models in `models.py` — use `BaseModel` for all request/response types
- Error responses follow the `{"what": str, "why": str, "fix": str}` pattern via `HTTPException(detail={...})`
- All route modules use `from __future__ import annotations` at the top
- Auth: `POST /api/templates/from-scratch` requires authentication (use same auth pattern as other template routes)

**Frontend - Component Layer:**
- Location: `frontend/src/components/`
- Shadcn UI components available: Badge, Button, Card, Dialog (stub), Popover, ScrollArea, Select, Separator, etc.
- **IMPORTANT: Dialog/Sheet components are stubs** — `dialog.tsx` only exports `Dialog` (fixed inset div), no `DialogContent`/`DialogHeader`/`DialogTitle`
- For modal dialogs, use inline fixed-overlay pattern (see `TemplateSelectionScreen.tsx`, `ScenarioEntryDialog.tsx` for examples)
- Icons from lucide-react: use existing icons for type selection (may use custom colors)

**Frontend - API Layer:**
- Location: `frontend/src/api/`
- Types in `types.ts` — TypeScript interfaces matching backend Pydantic models
- API functions in domain files (e.g., `templates.ts`, `categories.ts`)
- Use `apiFetch<T>()` from `client.ts` for all HTTP calls

**Testing - Backend:**
- Location: `tests/server/`
- Use FastAPI `TestClient` from `fastapi.testclient`
- Fixtures in `tests/server/conftest.py` — use `client` and `auth_headers` fixtures
- Test structure: class-based groups (e.g., `TestCreateBlankPolicy`)
- Assertions: plain `assert` statements

**Testing - Frontend:**
- Location: `frontend/src/components/**/__tests__/`
- Use Vitest + Testing Library
- Mock API calls with `vi.mock("@/api/templates")` or similar
- Test component render with different states

### Key Design Decisions

**Policy Type System (Closed Set):**

Per UX spec Revision 4.1, there are exactly three fundamental policy types:

| Type | Badge Color | Description | Parameter Groups |
|------|-------------|-------------|------------------|
| Tax | Amber (`bg-amber-100 text-amber-800`) | Charges on emissions, consumption, or activities | Mechanism, Eligibility, Schedule, **Redistribution** |
| Subsidy | Emerald (`bg-emerald-100 text-emerald-800`) | Payments to encourage behavior | Mechanism, Eligibility, Schedule |
| Transfer | Blue (`bg-blue-100 text-blue-800`) | Means-tested social payments | Mechanism, Eligibility, Schedule |

**Note:** Rebate = Subsidy. Feebate = composite Tax + Subsidy (not a fundamental type).

**From-Scratch Dialog Flow:**

The dialog uses a three-step inline overlay pattern (not Shadcn Dialog stub):

1. **Step 1 — Type Selection:**
   - Three large cards (approx 200px wide) with:
     - Icon or large first letter
     - Type name (Tax / Subsidy / Transfer)
     - One-line description
     - Colored border matching type badge color (amber/emerald/blue)
   - Selection highlights card with thicker colored border + checkmark
   - Next button reveals Step 2

2. **Step 2 — Category Selection:**
   - Grid of category cards (2 columns on desktop, 1 on mobile)
   - Each card shows: category label, description
   - Only categories with `compatible_types` including selected type are shown
   - Filter using: `categories.filter(c => c.compatible_types.includes(selectedType))`
   - Selection highlights card
   - Back button returns to Step 1
   - Next button reveals Step 3

3. **Step 3 — Confirmation:**
   - Summary showing:
     - Selected type badge (colored)
     - Selected category badge (neutral slate)
     - Auto-generated name: `"{Type} — {Category}"` (e.g., "Tax — Carbon Emissions")
   - Cancel button returns to Policies stage
   - Create Policy button calls API and adds to composition

**Policy Name Generation:**

Use the following pattern:
```
const name = `${typeLabel} — ${categoryLabel}`;
```

Examples:
- "Tax — Carbon Emissions"
- "Subsidy — Energy Consumption"
- "Transfer — Income"

**Default Parameter Groups:**

Per UX spec table, default groups by type:

| Policy Type | Default Parameter Groups |
|-------------|-------------------------|
| Tax | Mechanism, Eligibility, Schedule, Redistribution |
| Subsidy | Mechanism, Eligibility, Schedule |
| Transfer | Mechanism, Eligibility, Schedule |

Each group should have placeholder parameters with sensible defaults:
- **Mechanism**: `rate: 0` (number), `unit: "EUR"` (string)
- **Eligibility**: `threshold: 0` (number), `ceiling: null` (nullable)
- **Schedule**: `{}` (empty year-indexed schedule)
- **Redistribution** (Tax only): `divisible: true` (boolean), `recipients: "all"` (string)

**Backend Blank Policy Structure:**

The `POST /api/templates/from-scratch` endpoint should return:

```json
{
  "name": "Tax — Carbon Emissions",
  "policy_type": "tax",
  "category_id": "carbon_emissions",
  "parameters": {
    "rate": 0,
    "unit": "EUR",
    "threshold": 0,
    "ceiling": null
  },
  "parameter_groups": ["Mechanism", "Eligibility", "Schedule", "Redistribution"],
  "rate_schedule": {}
}
```

**Integration with Existing CompositionEntry:**

The from-scratch policy becomes a `CompositionEntry` in the composition panel:

```typescript
const newEntry: CompositionEntry = {
  instanceId: `blank-${Date.now()}`, // or use instanceCounterRef
  templateId: "", // Empty for from-scratch policies
  name: response.name, // Auto-generated from type + category
  parameters: response.parameters,
  rateSchedule: response.rate_schedule,
};
```

**Type Badge Mappings (from existing code):**

The following constants are already defined and should be reused:

```typescript
// TYPE_LABELS from PortfolioTemplateBrowser.tsx
const TYPE_LABELS: Record<string, string> = {
  "carbon-tax": "Carbon Tax",
  "carbon_tax": "Carbon Tax",
  "subsidy": "Subsidy",
  "rebate": "Rebate",
  "feebate": "Feebate",
  "vehicle_malus": "Vehicle Malus",
  "energy_poverty_aid": "Energy Poverty Aid",
};

// TYPE_COLORS from PortfolioTemplateBrowser.tsx
const TYPE_COLORS: Record<string, string> = {
  "carbon-tax": "bg-amber-100 text-amber-800",
  "carbon_tax": "bg-amber-100 text-amber-800",
  "subsidy": "bg-emerald-100 text-emerald-800",
  "rebate": "bg-blue-100 text-blue-800",
  "feebate": "bg-violet-100 text-violet-800",
  "vehicle_malus": "bg-rose-100 text-rose-800",
  "energy_poverty_aid": "bg-cyan-100 text-cyan-800",
};
```

For the from-scratch flow, add:
```typescript
// Add to TYPE_COLORS
"tax": "bg-amber-100 text-amber-800",
"transfer": "bg-blue-100 text-blue-800",
```

### Source Tree Components to Touch

**Backend files to create/modify:**
1. `src/reformlab/server/models.py` — Add `CreateBlankPolicyRequest` model, `BlankPolicyResponse` model
2. `src/reformlab/server/routes/templates.py` — Add `POST /api/templates/from-scratch` endpoint
3. `tests/server/test_templates.py` — Add tests for blank policy creation (or create `tests/server/test_from_scratch.py`)

**Frontend files to create/modify:**
1. `frontend/src/api/types.ts` — Add `CreateBlankPolicyRequest`, `BlankPolicyResponse` interfaces
2. `frontend/src/api/templates.ts` — Add `createBlankPolicy()` function
3. `frontend/src/components/simulation/CreateFromScratchDialog.tsx` — NEW (three-step from-scratch flow)
4. `frontend/src/components/screens/PoliciesStageScreen.tsx` — Add "+ Add Policy" choice dialog, integrate from-scratch flow
5. `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — Update to display parameter groups for from-scratch policies
6. `frontend/src/components/simulation/__tests__/CreateFromScratchDialog.test.tsx` — NEW (dialog flow tests)
7. `frontend/src/components/screens/__tests__/PoliciesStageScreen.fromScratch.test.tsx` — NEW (integration tests)

### Integration with Story 25.1 and 25.2

**Story 25.1 provided:**
- `Category` interface with `compatible_types: string[]` field
- `listCategories()` API function
- Categories fetched in `PoliciesStageScreen` on mount

**Story 25.2 provided:**
- Duplicate instance support with `instanceCounterRef` (use `useRef`)
- `CompositionEntry` interface with `instanceId` field
- `addTemplateInstance` pattern for adding unique instances to composition

**Story 25.3 uses:**
- Categories for filtering in Step 2
- `instanceCounterRef.current++` for generating unique instanceIds
- Same composition panel for displaying from-scratch policies

### Category Compatibility Filtering

Use the `compatible_types` field from categories API:

```typescript
const compatibleCategories = categories.filter(cat =>
  cat.compatible_types.includes(selectedType.toLowerCase())
);
```

Example categories from Story 25.1:
```json
{
  "id": "carbon_emissions",
  "label": "Carbon Emissions",
  "compatible_types": ["tax", "subsidy", "transfer"]
},
{
  "id": "vehicle_emissions",
  "label": "Vehicle Emissions",
  "compatible_types": ["tax"]
},
{
  "id": "income",
  "label": "Income",
  "compatible_types": ["transfer"]
}
```

### Out of Scope

The following are explicitly out of scope for Story 25.3:
- **Editable parameter groups** — deferred to Story 25.4 (groups are fixed in this story)
- **Parameter editing within from-scratch dialog** — policy is created with defaults, then edited in composition panel
- **Policy set persistence independence** — deferred to Story 25.5
- **Custom parameter definitions** — only placeholder defaults (rate = 0, threshold = 0)
- **Template YAML metadata for from-scratch policies** — from-scratch policies are not templates

### Testing Standards Summary

**Backend:**
```bash
uv run pytest tests/server/test_templates.py::TestCreateBlankPolicy -v
```
- Test valid type + compatible category combinations
- Test invalid type (not in closed set)
- Test incompatible category (category.compatible_types excludes type)
- Test response shape and default parameter groups

**Frontend:**
```bash
npm test -- CreateFromScratchDialog
npm test -- PoliciesStageScreen.fromScratch
```
- Test dialog state progression (type → category → confirm)
- Test category filtering by type
- Test blank policy creation and addition to composition
- Test default parameter groups (Tax has 4, others have 3)
- Test policy name generation

**Quality gates:**
```bash
# Backend
uv run ruff check src/reformlab/server/routes/templates.py
uv run mypy src/reformlab/server/routes/templates.py

# Frontend
npm run typecheck
npm run lint
```

### Known Issues / Gotchas

1. **Dialog/Sheet stubs**: Do not use Shadcn Dialog directly — it's a stub. Use inline fixed-overlay pattern with `position: fixed; inset: 0; z-index: 50` div for modal background and centered content div.

2. **Type normalization**: The frontend may use "Tax" (capitalized) while backend uses "tax" (lowercase). Normalize to lowercase for API calls:
   ```typescript
   const policyType = selectedType.toLowerCase(); // "tax" | "subsidy" | "transfer"
   ```

3. **instanceId generation**: Use the existing `instanceCounterRef.current++` pattern from Story 25.2 to ensure uniqueness:
   ```typescript
   const instanceId = `blank-${instanceCounterRef.current++}`;
   ```

4. **Empty templateId**: From-scratch policies have no template, so `templateId` should be empty string `""` or a special prefix like `"blank:"`. Empty string is simpler for existing composition panel logic.

5. **Category lookup failures**: If categories API fails or returns null, the from-scratch flow should be disabled with a helpful message: "Categories not loaded — cannot create from scratch. Try again later."

6. **Composite template expansion**: The epic story mentions "composite templates such as feebate should add multiple policies" — this is explicitly out of scope for Story 25.3. From-scratch always creates a single policy entry.

7. **Parameter group collapse/expand**: If the composition panel doesn't already support collapsible parameter groups, add expand/collapse chevrons per group (not per policy). This may be deferred to Story 25.4 if not needed for AC 4-6.

8. **Type badge consistency**: Ensure from-scratch policies use the same TYPE_COLORS and TYPE_LABELS mappings as template-sourced policies. Add "tax" and "transfer" keys if not present.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Completion Notes List

### File List

**Backend (3 files):**
- `src/reformlab/server/models.py` — add CreateBlankPolicyRequest, BlankPolicyResponse
- `src/reformlab/server/routes/templates.py` — add POST /api/templates/from-scratch endpoint
- `tests/server/test_templates.py` or `tests/server/test_from_scratch.py` — tests for blank policy creation

**Frontend (7 files):**
- `frontend/src/api/types.ts` — add CreateBlankPolicyRequest, BlankPolicyResponse interfaces
- `frontend/src/api/templates.ts` — add createBlankPolicy() function
- `frontend/src/components/simulation/CreateFromScratchDialog.tsx` — NEW (three-step from-scratch wizard)
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — add "+ Add Policy" choice, integrate from-scratch
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — display parameter groups for from-scratch
- `frontend/src/components/simulation/__tests__/CreateFromScratchDialog.test.tsx` — NEW (dialog tests)
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.fromScratch.test.tsx` — NEW (integration tests)

**References:**
- UX spec: `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, Stage 1 — Policies section, Create-from-Scratch Flow)
- Epics: `_bmad-output/planning-artifacts/epics.md` (Epic 25, Story 25.3)
- Story 25.1: `_bmad-output/implementation-artifacts/25-1-add-api-driven-categories-endpoint-and-formula-help-metadata.md` (categories API)
- Story 25.2: `_bmad-output/implementation-artifacts/25-2-redesign-policies-stage-browser-composition-layout-with-types-categories-and-duplicate-policy-instances.md` (duplicate instances, instanceCounterRef)
