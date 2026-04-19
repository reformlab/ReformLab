# Story 25.1: Add API-driven categories endpoint and formula-help metadata

Status: complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst**,
I want **to see policy categories and formula explanations fetched from the API**,
so that **I can understand what data each policy operates on and how formulas are calculated**.

## Acceptance Criteria

1. **Given** the categories API, **when** called, **then** it returns the defined categories with id, label, columns, compatible_types, formula_explanation, and description.
2. **Given** the Policies stage, **when** rendered, **then** templates are grouped by category with category headers.
3. **Given** a category filter chip, **when** selected, **then** only templates matching that category are shown.
4. **Given** a policy card with a category, **when** the category help icon is clicked, **then** a popover appears showing the formula explanation and description. If the template has no category or the category has no help text, the help icon is hidden.
5. **Given** a template without a matching category, **when** the browser renders, **then** it appears in a fallback "Other" group positioned last (after all named categories).
6. **Given** the categories API fails to load, **when** the Policies stage renders, **then** templates are shown ungrouped (flat list) and a non-blocking warning indicates categories could not be loaded.
7. **Given** a popover is open, **when** the user presses Escape or clicks outside, **then** the popover closes.
8. **Given** both category and type filters are active, **when** filtering, **then** templates matching BOTH criteria are shown (AND logic).

## Tasks / Subtasks

- [x] **Backend - Add Category API endpoint** (AC: 1)
  - [x] Add `CategoryItem` Pydantic model to `src/reformlab/server/models.py`
  - [x] Create `_CATEGORY_DEFINITIONS` constant with initial categories
  - [x] Add `GET /api/categories` route in `src/reformlab/server/routes/categories.py`
  - [x] Register categories router in `src/reformlab/server/app.py`
  - [x] Add `category_id: str | None` field to `TemplateListItem` model
  - [x] Update `_template_to_list_item()` to populate `category_id` via hardcoded type-to-category mapping (do not read template YAML metadata in this story)
- [x] **Frontend API wrapper** (AC: 1)
  - [x] Add `Category` type to `frontend/src/api/types.ts`
  - [x] Add `category_id?: string` to `TemplateListItem` interface in `frontend/src/api/types.ts`
  - [x] Add `category_id?: string` to `Template` interface in `frontend/src/data/mock-data.ts`
  - [x] Update `mapTemplate()` in `frontend/src/hooks/useApi.ts` to pass `category_id` through (add `category_id: item.category_id,` to the return object)
  - [x] Create `frontend/src/api/categories.ts` with `listCategories()` function
  - [x] Add `GET /api/categories` API call using `apiFetch` client
- [x] **Policy browser update** (AC: 2, 3, 5)
  - [x] Fetch categories in `PoliciesStageScreen` on mount; pass categories as props to `PortfolioTemplateBrowser` (same pattern as templates prop)
  - [x] Group templates by category (add category_id to TemplateListItem type)
  - [x] Add category filter chips alongside type filter
  - [x] Implement "Other" fallback group for templates without matching categories
  - [x] Update template card to show category badge with neutral color
- [x] **Formula help popover** (AC: 4)
  - [x] Add CircleHelp icon from lucide-react next to category badge
  - [x] Install full Radix Popover via `npx shadcn-ui@latest add popover` (popover.tsx is currently a stub like Dialog/Sheet)
  - [x] Implement PopoverTrigger, PopoverContent with formula_explanation and description
  - [x] Style popover with proper spacing and typography
- [x] **Testing** (AC: 1, 2, 3, 4, 5, 6, 7, 8)
  - [x] Backend tests for `GET /api/categories` response shape and content
  - [x] Backend tests for category_id population in template listings
  - [x] Frontend tests for category fetching and error handling
  - [x] Frontend tests for template grouping by category
  - [x] Frontend tests for filter behavior (category chips)
  - [x] Frontend tests for popover render and interaction
  - [x] Regression tests for existing template selection flows (select/unselect, composition persistence, type badge display continuity, no-category fallback visibility)

## Dev Notes

### Architecture Patterns and Constraints

**Backend - Server Layer:**
- Location: `src/reformlab/server/`
- Pydantic v2 models in `models.py` — use `BaseModel` for all request/response types
- Route modules in `routes/` — each gets an `APIRouter()` with a single router prefix
- Error responses follow the `{"what": str, "why": str, "fix": str}` pattern via `HTTPException(detail={...})`
- All route modules use `from __future__ import annotations` at the top
- New routes must be registered in `src/reformlab/server/app.py`
- Auth: `GET /api/categories` requires authentication (use same auth pattern as `/api/templates`)

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
3. `frontend/src/data/mock-data.ts` — Add `category_id?: string` to `Template` interface
4. `frontend/src/hooks/useApi.ts` — Update `mapTemplate()` to pass `category_id` through
5. `frontend/src/components/screens/PoliciesStageScreen.tsx` — Fetch and use categories
6. `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — Group by category, add filter chips, add category badge and help icon inline

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
- Maps known template types to categories (see mapping table below)
- Falls back to `None` for unknown types (these go to "Other" group)

Future stories (25.2-25.3) will add proper category metadata to templates.

**Explicit type-to-category mapping for 25.1:**

```python
# In routes/templates.py
TYPE_TO_CATEGORY: dict[str, str | None] = {
    "carbon-tax": "carbon_emissions",
    "carbon_tax": "carbon_emissions",  # API uses underscore format
    "vehicle_malus": "vehicle_emissions",
    "energy_poverty_aid": "income",
    # subsidy, rebate, feebate → None intentionally (may apply to multiple categories)
    # These will appear in "Other" group until proper metadata is added in 25.2-25.3
}
```

### Integration with Existing Patterns

**Existing template listing flow:**
- `GET /api/templates` → returns `TemplateListItem[]`
- `_template_to_list_item()` in `routes/templates.py` converts domain templates
- `listTemplates()` in `frontend/src/api/templates.ts` fetches and returns templates

**Changes needed:**
- Add `category_id: str | None` to `TemplateListItem` model (backend)
- Add `category_id?: string` to `TemplateListItem` interface (frontend)
- Populate `category_id` in `_template_to_list_item()` using a mapping function

### Out of Scope

The following are explicitly out of scope for Story 25.1 and will be addressed in later stories:
- **Template YAML metadata for categories**: Adding `category_id` fields to template pack YAML files (Stories 25.2-25.3)
- **Admin interfaces for category management**: CRUD operations for category definitions (future stories)
- **Dynamic category assignment**: User-selectable categories per template (future stories)

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

1. **Dialog/Sheet/Popover stubs**: Do not use Shadcn Dialog, Sheet, or Popover components directly — they're stubs. `dialog.tsx` and `popover.tsx` only export bare `<div>` wrappers with no floating behavior. For Popover in AC4, install the full Radix implementation: `npx shadcn-ui@latest add popover`. This overwrites the stub with `PopoverTrigger`/`PopoverContent` exports.

3. **Template metadata**: Current templates may not have category metadata. Use a mapping function for Story 25.1; proper metadata comes in later stories.

4. **Group by category**: The existing template browser groups by `type` (see `PortfolioTemplateBrowser.tsx` line 56: `const key = t.type`). Replace the `byType` grouping with `byCategory` grouping keyed by `t.category_id ?? "other"`. Keep `type` as a secondary filter/badge only.

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Completion Notes List

- Comprehensive developer guide created with all necessary context
- Backend and frontend patterns documented
- Testing patterns and fixtures identified
- Category schema fully specified from UX spec
- Integration points with existing template listing flow identified
- **All 8 acceptance criteria implemented and tested**
- **Backend: CategoryItem Pydantic model, categories API endpoint, category_id in TemplateListItem, type-to-category mapping**
- **Frontend: Category type, categories API wrapper, category_id in Template/listItem/useApi, PoliciesStageScreen category fetch, PortfolioTemplateBrowser grouping/filters/badges/popover**
- **Full Radix Popover installed and integrated (PopoverTrigger, PopoverContent)**
- **"Other" fallback group implemented for templates without matching categories**
- **AC-6: Non-blocking warning when categories API fails - templates shown ungrouped**
- **AC-8: Category and type filters use AND logic**
- **All tests passing: 8 backend tests, 14 frontend category tests, 51 PoliciesStageScreen tests**
- **No regressions in existing functionality**

### File List

**Backend (4 files):**
- `src/reformlab/server/models.py` — add CategoryItem model, category_id to TemplateListItem
- `src/reformlab/server/routes/categories.py` — NEW (categories API endpoint)
- `src/reformlab/server/routes/templates.py` — update for category_id mapping
- `src/reformlab/server/app.py` — register categories router

**Frontend (7 files):**
- `frontend/src/api/types.ts` — add Category interface, category_id to TemplateListItem
- `frontend/src/api/categories.ts` — NEW (categories API wrapper)
- `frontend/src/data/mock-data.ts` — add category_id to Template interface
- `frontend/src/hooks/useApi.ts` — update mapTemplate to pass category_id
- `frontend/src/components/screens/PoliciesStageScreen.tsx` — fetch categories on mount
- `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — grouping, filters, badges, popover
- `frontend/src/components/ui/popover.tsx` — installed full Radix Popover implementation

**Tests (2 files):**
- `tests/server/test_categories.py` — NEW (8 tests)
- `frontend/src/components/screens/__tests__/PoliciesStageScreen.categories.test.tsx` — NEW (14 tests)
- `frontend/src/components/simulation/__tests__/PortfolioTemplateBrowser.test.tsx` — updated for categories prop

**References:**
- UX spec: `_bmad-output/planning-artifacts/ux-design-specification.md` (Stage 1 — Policies section, API-Driven Categories)
- Architecture: `_bmad-output/planning-artifacts/architecture.md` (server section, API layer)
- Epics: `_bmad-output/planning-artifacts/epics.md` (Epic 25, Story 25.1)


## Change Log

- **Date: 2026-04-19**
- **Status:** Complete - All acceptance criteria implemented and tested
- **Summary:** Added API-driven categories endpoint and formula help metadata
- **Files Modified/Created:**
  - Backend: models.py, routes/categories.py (NEW), routes/templates.py, app.py
  - Frontend: types.ts, categories.ts (NEW), mock-data.ts, useApi.ts, PoliciesStageScreen.tsx, PortfolioTemplateBrowser.tsx, popover.tsx
  - Tests: test_categories.py (NEW), PoliciesStageScreen.categories.test.tsx (NEW), PortfolioTemplateBrowser.test.tsx (updated)
- **Tests:** 8 backend tests + 14 frontend category tests + 51 PoliciesStageScreen tests = **73 tests passing**
- **Acceptance Criteria:** All 8 AC satisfied
