# Story 25.1: Add API-driven categories endpoint and formula-help metadata

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want **to see policy categories and formula explanations fetched from the API**,
so that **I can understand what data each policy operates on and how formulas are calculated**.

## Acceptance Criteria

1. **Given** the categories API, **when** called, **then** it returns the defined categories with id, label, columns, compatible_types, formula_explanation, and description.
2. **Given** the Policies stage, **when** rendered, **then** templates are grouped by category with category headers.
3. **Given** a category filter chip, **when** selected, **then** only templates matching that category are shown.
4. **Given** a policy card, **when** the category help icon is clicked, **then** a popover appears showing the formula explanation and description.
5. **Given** a template without a matching category, **when** the browser renders, **then** it appears in a fallback "Other" group rather than being hidden.

## Tasks / Subtasks

- [ ] **Backend - Add Category API endpoint** (AC: 1)
  - [ ] Add `CategoryItem` Pydantic model to `src/reformlab/server/models.py`
  - [ ] Create `_CATEGORY_DEFINITIONS` constant with initial categories
  - [ ] Add `GET /api/categories` route in `src/reformlab/server/routes/categories.py`
  - [ ] Register categories router in `src/reformlab/server/app.py`
  - [ ] Add `category_id` field to `TemplateListItem` model
  - [ ] Update `_template_to_list_item()` to populate `category_id` from template metadata
- [ ] **Frontend API wrapper** (AC: 1)
  - [ ] Add `Category` type to `frontend/src/api/types.ts`
  - [ ] Create `frontend/src/api/categories.ts` with `listCategories()` function
  - [ ] Add `GET /api/categories` API call using `apiFetch` client
- [ ] **Policy browser update** (AC: 2, 3, 5)
  - [ ] Fetch categories on mount in `PoliciesStageScreen` or `PortfolioTemplateBrowser`
  - [ ] Group templates by category (add category_id to TemplateListItem type)
  - [ ] Add category filter chips alongside type filter
  - [ ] Implement "Other" fallback group for templates without matching categories
  - [ ] Update template card to show category badge with neutral color
- [ ] **Formula help popover** (AC: 4)
  - [ ] Add CircleHelp icon from lucide-react next to category badge
  - [ ] Implement Popover component from Shadcn UI (or use existing)
  - [ ] Show `formula_explanation` and `description` in popover content
  - [ ] Style popover with proper spacing and typography
- [ ] **Testing** (AC: 1, 2, 3, 4, 5)
  - [ ] Backend tests for `GET /api/categories` response shape and content
  - [ ] Backend tests for category_id population in template listings
  - [ ] Frontend tests for category fetching and error handling
  - [ ] Frontend tests for template grouping by category
  - [ ] Frontend tests for filter behavior (category chips)
  - [ ] Frontend tests for popover render and interaction
  - [ ] Regression tests for existing template selection flows

## Dev Notes

### Architecture Patterns and Constraints

**Backend - Server Layer:**
- Location: `src/reformlab/server/`
- Pydantic v2 models in `models.py` — use `BaseModel` for all request/response types
- Route modules in `routes/` — each gets an `APIRouter()` with a single router prefix
- Error responses follow the `{"what": str, "why": str, "fix": str}` pattern via `HTTPException(detail={...})`
- All route modules use `from __future__ import annotations` at the top
- New routes must be registered in `src/reformlab/server/app.py`

**Frontend - API Layer:**
- Location: `frontend/src/api/`
- Types in `types.ts` — TypeScript interfaces matching backend Pydantic models
- API functions in domain files (e.g., `templates.ts`, `categories.ts`)
- Use `apiFetch<T>()` from `client.ts` for all HTTP calls
- Pattern: `export async function listCategories(): Promise<Category[]> { ... }`

**Frontend - Component Layer:**
- Location: `frontend/src/components/`
- Shadcn UI components available: Badge, Button, Card, Popover, ScrollArea, Select, etc.
- **IMPORTANT: Dialog/Sheet components are stubs** — `dialog.tsx` only exports `Dialog` (fixed inset div)
- For Popover: use existing Shadcn Popover from `@/components/ui/popover`
- Icons from lucide-react: `CircleHelp` for formula help affordance

**Testing - Backend:**
- Location: `tests/server/`
- Use FastAPI `TestClient` from `fastapi.testclient`
- Fixtures in `tests/server/conftest.py` — use `client` and `auth_headers` fixtures
- Test structure: class-based groups (e.g., `TestListCategories`)
- Assertions: plain `assert` statements
- Auth: include `headers=auth_headers` in requests

**Testing - Frontend:**
- Location: `frontend/src/components/**/__tests__/`
- Use Vitest + Testing Library
- Mock API calls with `vi.mock("@/api/categories")` or similar
- For Recharts components, may need ResizeObserver polyfill

### Source Tree Components to Touch

**Backend files to create/modify:**
1. `src/reformlab/server/models.py` — Add `CategoryItem` model
2. `src/reformlab/server/routes/categories.py` — NEW file for category routes
3. `src/reformlab/server/routes/templates.py` — Update to include category_id
4. `src/reformlab/server/app.py` — Register categories router

**Frontend files to create/modify:**
1. `frontend/src/api/types.ts` — Add `Category` interface, extend `TemplateListItem`
2. `frontend/src/api/categories.ts` — NEW file for category API functions
3. `frontend/src/components/screens/PoliciesStageScreen.tsx` — Fetch and use categories
4. `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — Group by category, add filter chips
5. `frontend/src/components/simulation/TemplateCard.tsx` — Add category badge and help icon (may exist)

**Test files to create:**
1. `tests/server/test_categories.py` — NEW file for category endpoint tests
2. `frontend/src/components/screens/__tests__/PoliciesStageScreen.categories.test.tsx` — NEW file for category UI tests

### Category Schema Definition

From UX spec Revision 4.1, the category schema is:

```json
[
  {
    "id": "carbon_emissions",
    "label": "Carbon Emissions",
    "columns": ["emissions_co2"],
    "compatible_types": ["tax", "subsidy", "transfer"],
    "formula_explanation": "emissions_co2 × tax_rate",
    "description": "Applies to household CO₂ emissions (tonnes/year)"
  },
  {
    "id": "energy_consumption",
    "label": "Energy Consumption",
    "columns": ["energy_kwh", "energy_cost"],
    "compatible_types": ["tax", "subsidy", "transfer"],
    "formula_explanation": "energy_kwh × rate_per_kwh",
    "description": "Applies to household energy consumption"
  },
  {
    "id": "vehicle_emissions",
    "label": "Vehicle Emissions",
    "columns": ["vehicle_co2", "vehicle_type"],
    "compatible_types": ["tax", "subsidy"],
    "formula_explanation": "vehicle_co2 × malus_rate",
    "description": "Applies to vehicle emission levels"
  },
  {
    "id": "housing",
    "label": "Housing",
    "columns": ["housing_type", "housing_efficiency"],
    "compatible_types": ["subsidy", "transfer"],
    "formula_explanation": "renovation_cost × subsidy_rate",
    "description": "Applies to housing characteristics and efficiency"
  },
  {
    "id": "income",
    "label": "Income",
    "columns": ["disposable_income", "decile"],
    "compatible_types": ["transfer"],
    "formula_explanation": "max(0, ceiling − disposable_income)",
    "description": "Applies to household income for means-tested transfers"
  }
]
```

### Policy Type Badges (Context for Category Badge Colors)

Per UX spec Revision 4.1:
- **Tax**: Amber (`bg-amber-100 text-amber-800`)
- **Subsidy**: Emerald (`bg-emerald-100 text-emerald-800`)
- **Transfer**: Blue (`bg-blue-100 text-blue-800`)

**Category badge** should use a neutral color (slate) to distinguish from the type badge:
- Category badge: `bg-slate-100 text-slate-800` or similar neutral variant

### Template-Category Mapping Strategy

For Story 25.1, templates need a `category_id` field. Options:
1. **Quick approach**: Map template `type` to a default category (e.g., `carbon_tax` → `carbon_emissions`)
2. **Proper approach**: Add category metadata to template YAML and read it during load

Since this is the first story introducing categories, use a hardcoded mapping function that:
- Maps known template types to categories (e.g., `carbon_tax` → `carbon_emissions`)
- Falls back to `None` for unknown types (these go to "Other" group)

Future stories (25.2-25.3) will add proper category metadata to templates.

### Integration with Existing Patterns

**Existing template listing flow:**
- `GET /api/templates` → returns `TemplateListItem[]`
- `_template_to_list_item()` in `routes/templates.py` converts domain templates
- `listTemplates()` in `frontend/src/api/templates.ts` fetches and returns templates

**Changes needed:**
- Add `category_id: str | None` to `TemplateListItem` model (backend)
- Add `category_id?: string` to `TemplateListItem` interface (frontend)
- Populate `category_id` in `_template_to_list_item()` using a mapping function

### Testing Standards Summary

**Backend:**
```bash
uv run pytest tests/server/test_categories.py -v
```
- Use `client` and `auth_headers` fixtures from `conftest.py`
- Test response shape, field types, and content
- Test error cases (none for simple GET)

**Frontend:**
```bash
npm test -- categories
```
- Mock API responses with `vi.mock()`
- Test component render with category data
- Test filter chip interactions
- Test popover trigger and content display

**Quality gates:**
```bash
# Backend
uv run ruff check src/reformlab/server/
uv run mypy src/reformlab/server/

# Frontend
npm run typecheck
npm run lint
```

### Known Issues / Gotchas

1. **Dialog/Sheet stubs**: Do not use Shadcn Dialog or Sheet for modals — they're stubs. Use inline fixed-overlay pattern (see `TemplateSelectionScreen.tsx`, `ScenarioEntryDialog.tsx`) or Popover (which is available).

2. **Popover availability**: Verify `@/components/ui/popover` exists and exports Popover, PopoverTrigger, PopoverContent. If not, may need to add via Shadcn CLI.

3. **Template metadata**: Current templates may not have category metadata. Use a mapping function for Story 25.1; proper metadata comes in later stories.

4. **Group by category**: The existing template browser may group by `parameter_groups`. Switch this to group by `category_id` instead.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Completion Notes List

- Comprehensive developer guide created with all necessary context
- Backend and frontend patterns documented
- Testing patterns and fixtures identified
- Category schema fully specified from UX spec
- Integration points with existing template listing flow identified
- Ready-for-dev status set

### File List

**Backend (4 files):**
- `src/reformlab/server/models.py` — add CategoryItem model
- `src/reformlab/server/routes/categories.py` — NEW
- `src/reformlab/server/routes/templates.py` — update for category_id
- `src/reformlab/server/app.py` — register categories router

**Frontend (5 files):**
- `frontend/src/api/types.ts` — add Category interface
- `frontend/src/api/categories.ts` — NEW
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — fetch categories
- `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — grouping + filters
- `frontend/src/components/simulation/TemplateCard.tsx` — category badge + popover (if exists)

**Tests (2 files):**
- `tests/server/test_categories.py` — NEW
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.categories.test.tsx` — NEW

**References:**
- UX spec: `_bmad-output/planning-artifacts/ux-design-specification.md` (lines 1400-1599 for Stage 1 details)
- Architecture: `_bmad-output/planning-artifacts/architecture.md` (server section, API layer)
- Epics: `_bmad-output/planning-artifacts/epics.md` (Epic 25, Story 25.1)
