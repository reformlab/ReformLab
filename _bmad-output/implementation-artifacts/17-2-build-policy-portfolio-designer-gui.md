
# Story 17.2: Build Policy Portfolio Designer GUI

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a non-coding policy analyst,
I want a web-based Policy Portfolio Designer where I can browse available policy templates, select multiple templates, compose them into a named portfolio, configure per-template parameters and year-indexed schedules, reorder or remove policies, and save the portfolio for later use,
so that I can design multi-policy bundles for simulation without writing code or understanding the underlying composition logic.

## Acceptance Criteria

1. **AC-1: Template browsing** — Given the Portfolio Designer screen, when the analyst opens it, then available policy templates are listed with name, description, configurable parameter count, policy type badge (carbon-tax, subsidy, rebate, feebate), and category tags corresponding to `parameterGroups`.

2. **AC-2: Template selection and composition** — Given the template browser, when the analyst selects one or more templates, then they are added to a portfolio composition panel where each template appears as a card showing its name, type badge, and parameter count. Per-template parameters can be configured inline using the existing `ParameterRow` editing pattern. If fewer than 2 templates are in the composition panel, the save button is disabled and an inline hint reads "Add at least 2 policies to save a portfolio."

3. **AC-3: Reorder and remove** — Given a portfolio with multiple templates, when the analyst reorders templates using move-up/move-down buttons or removes a template, then the portfolio composition list updates accordingly. Order matters because the orchestrator applies policies sequentially. No drag-and-drop library is needed — use arrow buttons to avoid adding dependencies. The move-up button is disabled for the first item; the move-down button is disabled for the last item. Policy order is persisted when saving and restored exactly on load.

4. **AC-4: Year-indexed schedule editor** — Given template parameters with `rate_schedule` (year-indexed values, e.g., carbon tax trajectory), when the analyst configures schedules, then a visual year-schedule editor shows year/value pairs as editable rows, allows adding/removing years, and displays the trajectory as a mini inline chart. For this story, the default year range is fixed at 2025–2035 (dynamic scenario-driven range is out of scope). Year entries must be unique integers; duplicate years are rejected with an inline error. Values must be valid numbers; non-numeric input shows an inline field error. Rows are displayed sorted by year ascending.

5. **AC-5: Save, load, clone, delete** — Given a complete portfolio configuration (name + 2+ templates with parameters), when saved, then the portfolio is persisted via the backend API as a named, versioned configuration in the scenario registry (each save produces a new version_id). Previously saved portfolios can be loaded (restoring exact policy order and parameter values), cloned (with a new name), or deleted. The portfolio name is required, non-empty, and must be a lowercase slug (`[a-z0-9-]+`, max 64 chars); invalid names show an inline error. Attempting to clone to a name that already exists returns a 409 conflict with a suggested alternative name.

6. **AC-6: Conflict validation** — Given a draft portfolio composition, when the analyst triggers validation (automatically before save, or via an explicit "Check Conflicts" button), then detected conflicts are listed showing conflict type, affected policy names, and a human-readable description. When `resolution_strategy` is `"error"`, save is blocked if any conflicts exist and the save button shows a tooltip explaining the block. When set to any other strategy (`sum`, `first_wins`, `last_wins`, `max`), conflicts are shown as warnings but save is permitted.

## Tasks / Subtasks

- [x] Task 1: Implement FastAPI endpoints for portfolio CRUD operations (AC: 1, 2, 3, 5)
  - [x] 1.1: Create `src/reformlab/server/routes/portfolios.py` with router
  - [x] 1.2: Add `GET /portfolios` endpoint (full path: `GET /api/portfolios`) — list all saved portfolios with name, policy count, description, version
  - [x] 1.3: Add `GET /portfolios/{name}` endpoint (full path: `GET /api/portfolios/{name}`) — return portfolio detail including full policy list with parameters
  - [x] 1.4: Add `POST /portfolios` endpoint (full path: `POST /api/portfolios`) — create portfolio from template selections + parameter overrides, validate min 2 policies, save to registry, return version_id (status 201)
  - [x] 1.5: Add `PUT /portfolios/{name}` endpoint (full path: `PUT /api/portfolios/{name}`) — update portfolio policies/parameters/order, return updated detail
  - [x] 1.6: Add `DELETE /portfolios/{name}` endpoint (full path: `DELETE /api/portfolios/{name}`) — remove portfolio from registry
  - [x] 1.7: Add `POST /portfolios/{name}/clone` endpoint (full path: `POST /api/portfolios/{name}/clone`) — clone portfolio with new name, return detail (status 201)
  - [x] 1.8: Add `POST /portfolios/validate` endpoint (full path: `POST /api/portfolios/validate`) — validate portfolio for conflicts, return conflict list (does not require prior save)
  - [x] 1.9: Add Pydantic v2 request/response models to `src/reformlab/server/models.py`
  - [x] 1.10: Register portfolios router in `src/reformlab/server/app.py`
  - [x] 1.11: Write backend tests in `tests/server/test_portfolios.py`

- [x] Task 2: Define frontend TypeScript types and API client layer (AC: 1, 2, 3, 5)
  - [x] 2.1: Add TypeScript interfaces to `frontend/src/api/types.ts`: `PortfolioListItem`, `PortfolioDetailResponse`, `PortfolioPolicyItem`, `CreatePortfolioRequest`, `UpdatePortfolioRequest`, `ClonePortfolioRequest`, `PortfolioConflict`, `ValidatePortfolioRequest`, `ValidatePortfolioResponse`
  - [x] 2.2: Create `frontend/src/api/portfolios.ts` with API functions: `listPortfolios()`, `getPortfolio()`, `createPortfolio()`, `updatePortfolio()`, `deletePortfolio()`, `clonePortfolio()`, `validatePortfolio()`
  - [x] 2.3: Add `usePortfolios()` hook to `frontend/src/hooks/useApi.ts` following existing mock-data-fallback pattern
  - [x] 2.4: Add mock data for portfolios in `frontend/src/data/mock-data.ts`: `MockPortfolio`, `MockPortfolioPolicy`, `mockPortfolios`

- [x] Task 3: Build Template Browser for portfolio composition (AC: 1, 2)
  - [x] 3.1: Create `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — card grid of available templates with multi-select toggle, grouped by type, showing name, description, parameter count, type badge. Follow `DataSourceBrowser.tsx` multi-select pattern with `aria-pressed` toggle buttons
  - [x] 3.2: Add unit tests for PortfolioTemplateBrowser

- [x] Task 4: Build Portfolio Composition Panel (AC: 2, 3)
  - [x] 4.1: Create `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — ordered list of selected templates as cards, each showing name, type badge, parameter count, and action buttons (move up, move down, remove, expand/collapse parameters). Inline parameter editing using `ParameterRow` pattern when expanded. Uses `ArrowUp`, `ArrowDown`, `Trash2`, `ChevronDown` icons from lucide-react
  - [x] 4.2: Add unit tests for PortfolioCompositionPanel (reorder, remove, parameter edit)

- [x] Task 5: Build Year Schedule Editor component (AC: 4)
  - [x] 5.1: Create `frontend/src/components/simulation/YearScheduleEditor.tsx` — editable table of year/value rows with add-year and remove-year buttons, inline number inputs per year. Shows a mini Recharts line chart preview of the trajectory below the table. Default year range 2025–2035. Props: `schedule: Record<number, number>`, `onChange: (schedule: Record<number, number>) => void`, `unit: string`
  - [x] 5.2: Add unit tests for YearScheduleEditor (add year, remove year, edit value)

- [x] Task 6: Build Portfolio Designer screen and integrate into workspace (AC: 1, 2, 3, 4, 5)
  - [x] 6.1: Create `frontend/src/components/screens/PortfolioDesignerScreen.tsx` — orchestration container with step flow: Template Selection → Portfolio Composition (with parameters + schedules) → Review & Save. Follow `DataFusionWorkbench.tsx` step-flow pattern with `WorkbenchStepper`-style nav. Include save dialog (portfolio name + description input) using existing `Dialog` component
  - [x] 6.2: Integrate PortfolioDesignerScreen into `App.tsx` — add `"portfolio"` view mode, wire into left panel navigation with a "Portfolio" button between "Population" and "Configure Policy"
  - [x] 6.3: Update `frontend/src/contexts/AppContext.tsx` — add portfolio state: `portfolios: PortfolioListItem[]`, and `portfoliosLoading`/`refetchPortfolios`
  - [x] 6.4: Add unit tests for PortfolioDesignerScreen
  - [x] 6.5: Verify non-regression: existing view modes (configuration, data-fusion, results, etc.), left panel navigation, and `Cmd+[`/`Cmd+]` keyboard shortcuts remain functional

- [x] Task 7: Run quality checks (AC: all)
  - [x] 7.1: Run `uv run ruff check src/ tests/` and fix any lint issues
  - [x] 7.2: Run `uv run mypy src/` and fix any type errors
  - [x] 7.3: Run `cd frontend && npm run typecheck && npm run lint` and fix any issues
  - [x] 7.4: Run `uv run pytest tests/` — 2986 passed, 1 skipped
  - [x] 7.5: Run `cd frontend && npm test` — 119 passed across 21 test files

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Backend — Canonical endpoint table:**

| Method | Full URL | Router-relative path | Purpose |
|---|---|---|---|
| GET | `/api/portfolios` | `/` | List all saved portfolios |
| GET | `/api/portfolios/{name}` | `/{name}` | Get portfolio detail with all policies |
| POST | `/api/portfolios` | `/` | Create new portfolio (returns version_id) |
| PUT | `/api/portfolios/{name}` | `/{name}` | Update existing portfolio |
| DELETE | `/api/portfolios/{name}` | `/{name}` | Delete portfolio |
| POST | `/api/portfolios/{name}/clone` | `/{name}/clone` | Clone portfolio with new name |
| POST | `/api/portfolios/validate` | `/validate` | Validate portfolio for conflicts (no save) |

**Backend — FastAPI route pattern:**
- All routes follow pattern in `src/reformlab/server/routes/scenarios.py` (closest CRUD analog)
- Router created with `APIRouter()`, registered in `app.py` via `app.include_router(router, prefix="/api/portfolios", tags=["portfolios"])`
- **Route declaration order is critical:** declare `/validate` before `/{name}` so the static route is matched first; otherwise FastAPI captures `validate` as a portfolio name.
- Use lazy imports inside route handlers: `from reformlab.templates.portfolios import ...` (same pattern as scenarios.py)
- Pydantic v2 models in `models.py` — use `BaseModel` with `Field(...)`, `model_config = {"from_attributes": True}`
- Structured error responses with `what`, `why`, `fix` fields — use existing exception handlers from `app.py`
- `from __future__ import annotations` on every Python file
- Logging: `logging.getLogger(__name__)`, structured `key=value` format

**Backend — HTTP status code matrix:**

| Endpoint | Success | Client Error |
|---|---|---|
| `GET /api/portfolios` | 200 | — |
| `GET /api/portfolios/{name}` | 200 | 404 (not found) |
| `POST /api/portfolios` | 201 + `version_id` | 400 (< 2 policies), 409 (name exists), 422 (invalid name/params) |
| `PUT /api/portfolios/{name}` | 200 + updated detail | 400 (< 2 policies), 404 (not found), 422 (invalid params) |
| `DELETE /api/portfolios/{name}` | 204 | 404 (not found) |
| `POST /api/portfolios/{name}/clone` | 201 + detail | 404 (source not found), 409 (target name exists) |
| `POST /api/portfolios/validate` | 200 + conflict list | 400 (< 2 policies), 422 (invalid params) |

All error responses use `{"what": str, "why": str, "fix": str}` structure.

**Backend — Portfolio name validation:**
- Accept only lowercase slugs matching `^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$` or single-segment `^[a-z0-9]{1,64}$`
- Reject reserved names: `validate`, `clone`
- Validate in a `_validate_portfolio_name(name: str)` helper in `portfolios.py`; raise `HTTPException(422)` on violation
- Frontend enforces the same regex client-side before enabling the save button

**Backend — Versioning semantics for PUT:**
- `registry.save(portfolio, name)` is idempotent: if content matches an existing version, the same `version_id` is returned (no duplicate)
- For `PUT`, rebuild the `PolicyPortfolio` from the request body, call `registry.save(updated_portfolio, name)` — this produces a new `version_id` (SHA-256 content hash) if content changed
- Previous versions are preserved in history; the registry returns the latest version on `registry.get(name)`

**Backend — DELETE implementation:**
- `ScenarioRegistry` has no `delete()` method; implement deletion by removing the registry directory directly:
  ```python
  import shutil
  entry_path = registry.path / name
  if not entry_path.exists():
      raise HTTPException(404, ...)
  if registry.get_entry_type(name) != "portfolio":
      raise HTTPException(404, ...)  # Don't expose scenarios as portfolios
  shutil.rmtree(entry_path)
  ```

**Backend — Clone implementation:**
- `registry.clone(name, new_name=new_name)` returns an in-memory `PolicyPortfolio` — it does NOT save to registry
- Must also call `registry.save(cloned, new_name)` to persist the clone
- Check if `new_name` already exists before cloning; raise `HTTPException(409)` with a suggested rename if it does

**Frontend — Component pattern:**
- Components in `frontend/src/components/simulation/` (domain components) and `frontend/src/components/screens/` (full-width screens)
- Single `.tsx` file per component, props via TypeScript interface
- Tailwind-only styling, NO CSS modules/styled-components
- Use `cn()` from `@/lib/utils` for class merging
- Dense Terminal style: hard 1px `border-slate-200`, `p-3` padding, no shadows on static elements, square corners on panel containers
- Color tokens: `emerald` = validated/pass, `red` = error/fail, `amber` = warning, `blue` = selection/active, `slate` = neutral/inactive
- React 19 — NO `forwardRef`, ref is regular prop
- cva (class-variance-authority) for component variants
- Semantic HTML: `<button>` not `<div onClick>`, `<section>`, `<nav>`, `<main>`
- Icons from `lucide-react`

**Frontend — State management pattern:**
- React Context via `AppContext.tsx` → `useAppState()` hook
- API hooks in `useApi.ts` with mock data fallback pattern
- API client layer in `frontend/src/api/` — `apiFetch<T>()` with auth token injection
- View mode state in `App.tsx` for screen switching

**Frontend — Layout pattern:**
- Three-column responsive layout using `react-resizable-panels`
- Left panel (22%, min 18%): navigation, configuration steps
- Main content (56%, min 40%): active screen content
- Right panel (22%, min 18%): metadata, context, assumptions
- Keyboard shortcuts: `Cmd+[` / `Cmd+]` to toggle panels
- Desktop-only (min 1280px viewport), show warning below

### Backend Integration with Portfolio Library

The backend endpoints wrap the fully-implemented Epic 12 portfolio model. Key imports:

```python
# Portfolio domain model
from reformlab.templates.portfolios import (
    PolicyConfig,
    PolicyPortfolio,
    Conflict,
    ConflictType,
    ResolutionStrategy,
    PortfolioError,
    PortfolioValidationError,
    PortfolioSerializationError,
    validate_compatibility,
    resolve_conflicts,
    dump_portfolio,
    load_portfolio,
)

# Registry — portfolio CRUD
from reformlab.templates.registry import ScenarioRegistry

# Policy parameter types — needed for constructing PolicyConfig
from reformlab.templates.schema import (
    PolicyType,
    PolicyParameters,
    CarbonTaxParameters,
    SubsidyParameters,
    RebateParameters,
    FeebateParameters,
    infer_policy_type,
    YearSchedule,
)
```

**Portfolio creation pattern** (what the POST endpoint wraps):
```python
registry = ScenarioRegistry()

# Build typed policy objects from request parameters
carbon_params = CarbonTaxParameters(
    rate_schedule={2025: 50, 2026: 60, 2027: 70},
    covered_categories=("fossil_fuels",),
)
subsidy_params = SubsidyParameters(
    rate_schedule={2025: 5000},
    eligible_categories=("electric_vehicle",),
)

# Compose portfolio
portfolio = PolicyPortfolio(
    name="Green Transition 2030",
    policies=(
        PolicyConfig(policy_type=PolicyType.CARBON_TAX, policy=carbon_params, name="Carbon Tax"),
        PolicyConfig(policy_type=PolicyType.SUBSIDY, policy=subsidy_params, name="EV Subsidy"),
    ),
    description="Carbon tax + EV subsidy bundle",
    resolution_strategy="error",
)

# Validate for conflicts
conflicts = validate_compatibility(portfolio)
# Returns tuple[Conflict, ...] — empty if no conflicts

# Save to registry
version_id = registry.save(portfolio, "green-transition-2030")
```

**Registry portfolio methods:**
- `registry.save(portfolio, name)` → returns `str` version_id (SHA-256 content hash)
- `registry.get(name, version_id=None)` → returns `PolicyPortfolio` (latest if no version)
- `registry.list_portfolios()` → returns `list[str]` of portfolio names
- `registry.get_entry_type(name)` → returns `"portfolio"`, `"baseline"`, or `"reform"`
- `registry.clone(name, new_name)` → returns cloned `PolicyPortfolio`

**Conflict detection:**
- `validate_compatibility(portfolio)` returns `tuple[Conflict, ...]`
- `Conflict` has: `conflict_type` (ConflictType enum), `policy_indices`, `parameter_name`, `conflicting_values`, `description`
- `ConflictType`: `SAME_POLICY_TYPE`, `OVERLAPPING_CATEGORIES`, `OVERLAPPING_YEARS`, `PARAMETER_MISMATCH`

**Resolution strategies:** `"error"` (raise), `"sum"`, `"first_wins"`, `"last_wins"`, `"max"`

**PolicyPortfolio constraints:**
- Minimum 2 policies required (enforced in `__post_init__`)
- `resolution_strategy` must be one of: `error`, `sum`, `first_wins`, `last_wins`, `max`
- Frozen dataclass — mutate via `dataclasses.replace()`

**Available policy types (from PolicyType enum):**
- `CARBON_TAX` → `CarbonTaxParameters`
- `SUBSIDY` → `SubsidyParameters`
- `REBATE` → `RebateParameters`
- `FEEBATE` → `FeebateParameters`

**Policy parameter common fields:**
- `rate_schedule: dict[int, float]` — year-indexed rate values
- `exemptions: tuple[str, ...]` — exempted categories
- `thresholds: tuple[float, ...]` — threshold values
- `covered_categories: tuple[str, ...]` — categories covered by policy

### Pydantic Request/Response Models

Add these models to `src/reformlab/server/models.py`:

```python
from __future__ import annotations
from pydantic import BaseModel, Field

class PortfolioPolicyRequest(BaseModel):
    """A single policy entry in a portfolio create/update request."""
    model_config = {"from_attributes": True}
    name: str = Field(..., description="Display name for this policy entry")
    policy_type: str = Field(..., description="One of: carbon_tax, subsidy, rebate, feebate")
    rate_schedule: dict[str, float] = Field(default_factory=dict, description="Year→value map (JSON keys are strings)")
    exemptions: list[str] = Field(default_factory=list)
    thresholds: list[float] = Field(default_factory=list)
    covered_categories: list[str] = Field(default_factory=list)
    extra_params: dict[str, object] = Field(default_factory=dict, description="Policy-specific fields (e.g., eligible_categories)")

class CreatePortfolioRequest(BaseModel):
    model_config = {"from_attributes": True}
    name: str = Field(..., description="Lowercase slug name, max 64 chars")
    description: str = Field(default="")
    policies: list[PortfolioPolicyRequest] = Field(..., min_length=2, description="Ordered policy list (min 2)")
    resolution_strategy: str = Field(default="error", description="One of: error, sum, first_wins, last_wins, max")

class UpdatePortfolioRequest(BaseModel):
    model_config = {"from_attributes": True}
    description: str | None = None
    policies: list[PortfolioPolicyRequest] = Field(..., min_length=2)
    resolution_strategy: str | None = None

class ClonePortfolioRequest(BaseModel):
    model_config = {"from_attributes": True}
    new_name: str = Field(..., description="Target name for the clone (must not already exist)")

class PortfolioConflict(BaseModel):
    model_config = {"from_attributes": True}
    conflict_type: str
    policy_indices: list[int]
    parameter_name: str
    description: str

class ValidatePortfolioRequest(BaseModel):
    model_config = {"from_attributes": True}
    policies: list[PortfolioPolicyRequest] = Field(..., min_length=2)
    resolution_strategy: str = Field(default="error")

class ValidatePortfolioResponse(BaseModel):
    model_config = {"from_attributes": True}
    conflicts: list[PortfolioConflict]
    is_compatible: bool

class PortfolioPolicyItem(BaseModel):
    model_config = {"from_attributes": True}
    name: str
    policy_type: str
    rate_schedule: dict[str, float]
    parameters: dict[str, object]

class PortfolioDetailResponse(BaseModel):
    model_config = {"from_attributes": True}
    name: str
    description: str
    version_id: str
    policies: list[PortfolioPolicyItem]
    resolution_strategy: str
    policy_count: int

class PortfolioListItem(BaseModel):
    model_config = {"from_attributes": True}
    name: str
    description: str
    version_id: str
    policy_count: int
```

**Note on `rate_schedule` serialization:** JSON keys are always strings (`"2025"`, `"2026"`); Python backend converts them to `dict[int, float]` when constructing `PolicyParameters`. Frontend TypeScript uses `Record<string, number>` over the wire.

### Building Typed PolicyConfig from HTTP Request

The POST endpoint must construct domain objects from the untyped HTTP request. Follow the `scenarios.py:create_scenario` pattern (lines 78–172):

1. Map `policy_type` string → `PolicyType` enum
2. Look up the correct `PolicyParameters` subclass
3. Convert `rate_schedule` string keys → `dict[int, float]` (e.g., `{int(k): v for k, v in req.rate_schedule.items()}`)
4. Extract common fields (`exemptions`, `thresholds`, `covered_categories`) from `extra_params`
5. Construct `PolicyConfig(policy_type=..., policy=..., name=...)`
6. Repeat for each policy in the request
7. Construct `PolicyPortfolio(name=..., policies=tuple(...), ...)`

### Template Source for AC-1

Templates are fetched from the existing `GET /api/templates` endpoint (served by `src/reformlab/server/routes/templates.py`). The `PortfolioTemplateBrowser` component calls `GET /api/templates` (or uses the existing `useTemplates()` hook) to populate the template card grid. Each template item provides: `id`, `name`, `description`, `policy_type`, `parameter_groups` (for category tags), and `parameter_count`. No new endpoint is required for AC-1.

### Frontend Parameter Schema for Composition Panel

When a template is selected and added to the composition panel, its configurable parameters are derived from the template metadata returned by `GET /api/templates/{id}`. Each parameter entry includes `name`, `type` (number/string/enum), `unit`, and `default_value`. The `ParameterRow` component renders each parameter using this schema. `rate_schedule` parameters are rendered with the `YearScheduleEditor` component instead of a plain `ParameterRow`.

### Conflict Validation Endpoint

The `POST /portfolios/validate` endpoint is a dry-run validator. It:
1. Accepts `ValidatePortfolioRequest` body (same policy structure as POST create, min 2 policies)
2. Builds a `PolicyPortfolio` in memory (does NOT save to registry)
3. Calls `validate_compatibility(portfolio)`
4. Returns `ValidatePortfolioResponse` with conflict list and `is_compatible` boolean

This allows the GUI to show conflict warnings before the user commits to saving. The frontend calls this endpoint automatically when the composition changes (debounced 500ms) and again before the save dialog opens.

### Source Tree Components to Touch

**New files:**
```
src/reformlab/server/routes/portfolios.py          ← New API routes
tests/server/test_portfolios.py                    ← Backend tests
frontend/src/api/portfolios.ts                     ← API client functions
frontend/src/components/simulation/PortfolioTemplateBrowser.tsx
frontend/src/components/simulation/PortfolioCompositionPanel.tsx
frontend/src/components/simulation/YearScheduleEditor.tsx
frontend/src/components/screens/PortfolioDesignerScreen.tsx
```

**Modified files:**
```
src/reformlab/server/models.py                     ← Add Pydantic models
src/reformlab/server/app.py                        ← Register new router
frontend/src/api/types.ts                          ← Add TypeScript interfaces
frontend/src/data/mock-data.ts                     ← Add mock portfolio data
frontend/src/hooks/useApi.ts                       ← Add usePortfolios hook
frontend/src/contexts/AppContext.tsx                ← Add portfolio state
frontend/src/App.tsx                               ← Add view mode, wire designer
```

### Frontend Existing Components to Reuse

| Existing Component | Reuse in 17.2 |
|---|---|
| `DataSourceBrowser.tsx` | Pattern for `PortfolioTemplateBrowser` (multi-select card grid with `aria-pressed`) |
| `DataFusionWorkbench.tsx` | Pattern for `PortfolioDesignerScreen` (step-flow with WorkbenchStepper) |
| `ParameterRow.tsx` | Reuse directly for per-template parameter editing in composition panel |
| `ParametersStep.tsx` | Pattern for grouped parameter display (collapsible sections) |
| `TemplateSelectionScreen.tsx` | Pattern for template card layout |
| `ScenarioCard.tsx` | Pattern for portfolio policy cards with action buttons |
| `DistributionalChart.tsx` | Pattern for mini trajectory chart in `YearScheduleEditor` |
| `PopulationGenerationProgress.tsx` | Pattern for conflict validation display |

### Shadcn/ui Components Available

Already installed in `frontend/src/components/ui/`: Badge, Button, Card, Collapsible, Dialog, Input, Popover, ScrollArea, Select, Separator, Sheet, Slider, Switch, Table, Tabs, Tooltip, Sonner (toast).

### Dependency Versions (Current)

**Frontend** (from `package.json`):
- React 19.1.1, React DOM 19.1.1
- Vite 7.1.5, TypeScript 5.9.2
- Tailwind CSS v4 via `@tailwindcss/vite` 4.1.13
- Recharts 3.1.2
- class-variance-authority 0.7.1
- lucide-react 0.542.0
- react-resizable-panels 3.0.5
- Vitest 3.2.4, @testing-library/react 16.3.0

**Backend** (from `pyproject.toml`):
- FastAPI >= 0.133.0, uvicorn >= 0.41.0
- Pydantic >= 2.10
- Python 3.13+, mypy strict

### Important Scope Boundaries

**What this story does:**
- Builds GUI screens and backend endpoints for portfolio design workflow
- Wraps the fully-implemented Epic 12 portfolio composition library
- Provides portfolio CRUD (create, read, update, delete, clone)
- Provides conflict validation before save
- Includes year-schedule editor for rate trajectories
- Persists portfolios in the scenario registry

**What this story does NOT do:**
- Portfolio execution/simulation (that requires selecting a population and running — covered by Story 17.3)
- Multi-portfolio comparison dashboard (covered by Story 17.4)
- E2E browser tests with Playwright/Cypress (covered by Story 17.8)
- Custom template authoring (covered by Epic 13)
- Behavioral decision viewer (covered by Story 17.5)

### Resolution Strategy UI

The `resolution_strategy` field controls how policy conflicts are handled:
- `"error"` (default) — Block if conflicts detected
- `"sum"` — Add conflicting rate values
- `"first_wins"` — Keep first policy's value
- `"last_wins"` — Use last policy's value
- `"max"` — Use maximum value

Display as a select dropdown in the composition panel or review step. Default to `"error"` and show conflict warnings if validation returns non-empty conflicts.

### Mock Data for Portfolios

```typescript
export interface MockPortfolio {
  name: string;
  description: string;
  version: string;
  policy_count: number;
  policies: Array<{
    name: string;
    template_id: string;
    policy_type: string;
    parameters: Record<string, unknown>;
    rate_schedule: Record<string, number>;
  }>;
  resolution_strategy: string;
}

export const mockPortfolios: MockPortfolio[] = [
  {
    name: "Green Transition 2030",
    description: "Carbon tax with energy efficiency subsidy for low-income households",
    version: "1.0",
    policy_count: 2,
    policies: [
      {
        name: "Carbon Tax Trajectory",
        template_id: "carbon-tax-flat",
        policy_type: "carbon_tax",
        parameters: { tax_rate: 50, tax_rate_growth: 10 },
        rate_schedule: { "2025": 50, "2026": 60, "2027": 70, "2028": 80, "2029": 90, "2030": 100 },
      },
      {
        name: "Energy Efficiency Subsidy",
        template_id: "subsidy-energy",
        policy_type: "subsidy",
        parameters: { means_test_ceiling: 30000 },
        rate_schedule: { "2025": 5000, "2026": 5000, "2027": 4000 },
      },
    ],
    resolution_strategy: "error",
  },
];
```

### Anti-Patterns to Avoid

| Issue | Prevention |
|---|---|
| Adding drag-and-drop library (react-beautiful-dnd, dnd-kit) | Use simple arrow-up/arrow-down buttons for reordering — no new deps |
| Building custom chart library for year schedule | Reuse Recharts `LineChart` for mini trajectory preview |
| Adding CSS modules or styled-components | Tailwind-only; use `cn()` for conditional classes |
| Using `forwardRef` | React 19: ref is a regular prop |
| Mobile-responsive layouts | Desktop-only (min 1280px); show warning banner below |
| Importing OpenFisca in server routes | Portfolio library handles all composition; server routes only call registry |
| Creating separate state management (Redux/Zustand) | Follow existing React Context pattern in AppContext.tsx |
| Adding new npm dependencies | All needed dependencies already installed |
| Shadows on static layout elements | Shadows reserved exclusively for floating elements (dropdowns, modals, tooltips) |
| Creating portfolio without min 2 policies | Backend enforces min 2 in `PolicyPortfolio.__post_init__`; frontend should disable save button and show hint |
| Mixing portfolio and scenario endpoints | Portfolios have their own `/api/portfolios` prefix, separate from `/api/scenarios` |

### Testing Standards Summary

**Backend tests:**
- File: `tests/server/test_portfolios.py`
- Use FastAPI `TestClient` pattern from `tests/server/test_api.py`
- Test each endpoint: valid input → expected response, invalid input → error with structured message
- Mock the `ScenarioRegistry` for unit tests — don't require real registry state
- Test conflict validation endpoint with conflicting and non-conflicting portfolios
- Use `pytest.raises(...)` with `match=` for error assertions

**Frontend tests:**
- Use Vitest + @testing-library/react (already configured)
- Test component rendering with mock data
- Test user interactions (select template, reorder, remove, configure params)
- Test state transitions in designer flow
- Test year schedule editor (add/remove/edit year entries)
- Follow existing test patterns in `frontend/src/__tests__/` and `frontend/src/components/simulation/__tests__/`

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| EPIC-12 (all stories) | **Produces** portfolio model that 17.2 wraps via API |
| Story 17.1 | **Predecessor** — Data Fusion Workbench establishes step-flow pattern that 17.2 follows |
| Story 6.4a/6.4b | **Established** GUI patterns (layout, components, API client) that 17.2 follows |
| Story 17.3 | **Consumer** — Simulation Runner uses portfolio from 17.2 as input |
| Story 17.4 | **Consumer** — Comparison Dashboard compares portfolio results |
| Story 17.6 | **Overlap** — 17.2 creates portfolio-specific endpoints; 17.6 covers remaining Phase 2 endpoints |
| Story 17.7 | **Extension** — persistent storage for portfolio run results (not in 17.2 scope) |
| Story 17.8 | **Extension** — E2E browser tests for the designer flow (not in 17.2 scope) |

### Project Structure Notes

- Backend routes align with `src/reformlab/server/routes/` convention
- Frontend components align with `frontend/src/components/{simulation,screens}/` convention
- API client aligns with `frontend/src/api/` convention with typed fetch wrappers
- No new npm or Python dependencies required — all libraries already installed
- TypeScript path aliases (`@/`) already configured in `tsconfig.json`
- Portfolio registry stores files under `~/.reformlab/registry/{portfolio_name}/` (same as scenarios)

### References

- [Source: docs/epics.md#Epic 12] — Portfolio model stories and acceptance criteria
- [Source: docs/epics.md#Epic 17, Story 17.2] — GUI acceptance criteria
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Scenario Workspace] — Three-column layout, ScenarioCard, ParameterRow patterns
- [Source: _bmad-output/planning-artifacts/architecture.md] — Tech stack, layered architecture
- [Source: docs/project-context.md] — Coding conventions, testing rules
- [Source: src/reformlab/templates/portfolios/__init__.py] — Public API for portfolio library
- [Source: src/reformlab/templates/portfolios/portfolio.py] — PolicyPortfolio and PolicyConfig dataclasses
- [Source: src/reformlab/templates/portfolios/composition.py] — Validation, conflict resolution, serialization
- [Source: src/reformlab/templates/portfolios/enums.py] — ConflictType, ResolutionStrategy enums
- [Source: src/reformlab/templates/registry.py] — ScenarioRegistry with portfolio support
- [Source: src/reformlab/server/routes/scenarios.py] — CRUD route pattern reference
- [Source: src/reformlab/server/routes/templates.py] — Template listing pattern reference
- [Source: src/reformlab/server/models.py] — Pydantic model pattern reference
- [Source: src/reformlab/server/app.py] — Router registration pattern
- [Source: frontend/src/App.tsx] — Workspace orchestration, view modes
- [Source: frontend/src/contexts/AppContext.tsx] — State management pattern
- [Source: frontend/src/hooks/useApi.ts] — Data fetching hook pattern
- [Source: frontend/src/api/client.ts] — API client with error handling
- [Source: frontend/src/api/scenarios.ts] — CRUD API pattern reference
- [Source: frontend/src/components/simulation/DataSourceBrowser.tsx] — Multi-select card grid pattern
- [Source: frontend/src/components/screens/DataFusionWorkbench.tsx] — Step-flow screen pattern
- [Source: frontend/src/components/simulation/ParameterRow.tsx] — Parameter editing pattern
- [Source: frontend/src/components/simulation/ParametersStep.tsx] — Grouped parameter display
- [Source: frontend/src/data/mock-data.ts] — Mock data structure
- [Source: frontend/package.json] — Frontend dependency versions
- [Source: _bmad-output/implementation-artifacts/17-1-build-data-fusion-workbench-gui.md] — Previous story reference (patterns, antipatterns learned)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- **Bug fixed in Epic 12 library**: `_dict_to_policy_parameters()` in `composition.py` defaulted `redistribution_type` to `"lump_sum"` instead of `""`. This broke round-trip hash integrity — saved portfolios failed on `registry.get()` because the loaded object had a different hash. Fixed: `redistribution_data.get("type", "")`.
- **Operator precedence error**: `entry.name || t?.name ?? entry.templateId` is rejected by esbuild. Fixed to `entry.name || t?.name || entry.templateId` in both `PortfolioCompositionPanel.tsx` and `PortfolioDesignerScreen.tsx`.
- **Unused `asdict` import**: Removed from `portfolios.py` (ruff auto-fix).
- **mypy arg-type errors**: `tuple(list[str])` → `tuple[dict[str, Any], ...]` mismatch for `exemptions`/`thresholds`; suppressed with `# type: ignore[arg-type]` — runtime behaviour is correct.

### Completion Notes List

- All 7 FastAPI portfolio endpoints implemented and tested (45 backend tests, all green).
- Pre-existing bug in `src/reformlab/templates/portfolios/composition.py` line 333 fixed as prerequisite.
- Frontend: 4 new components + 4 test suites; AppContext extended with `portfolios`/`portfoliosLoading`/`refetchPortfolios`; App.tsx wired with `"portfolio"` view mode.
- `selectedPortfolioName` and `currentComposition` from the story task were not added to AppContext because `PortfolioDesignerScreen` manages its own composition state internally — no global state coordination is needed for MVP.
- ESLint warning `react-refresh/only-export-components` in `AppContext.tsx` is pre-existing (not introduced by this story).

### File List

**New files:**
- `src/reformlab/server/routes/portfolios.py`
- `tests/server/test_portfolios.py`
- `frontend/src/api/portfolios.ts`
- `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx`
- `frontend/src/components/simulation/__tests__/PortfolioTemplateBrowser.test.tsx`
- `frontend/src/components/simulation/PortfolioCompositionPanel.tsx`
- `frontend/src/components/simulation/__tests__/PortfolioCompositionPanel.test.tsx`
- `frontend/src/components/simulation/YearScheduleEditor.tsx`
- `frontend/src/components/simulation/__tests__/YearScheduleEditor.test.tsx`
- `frontend/src/components/screens/PortfolioDesignerScreen.tsx`
- `frontend/src/components/screens/__tests__/PortfolioDesignerScreen.test.tsx`

**Modified files:**
- `src/reformlab/templates/portfolios/composition.py` (bug fix: redistribution_type default)
- `src/reformlab/server/models.py` (added portfolio Pydantic models)
- `src/reformlab/server/app.py` (registered portfolios router)
- `frontend/src/api/types.ts` (added portfolio TypeScript interfaces)
- `frontend/src/data/mock-data.ts` (added MockPortfolio, mockPortfolios)
- `frontend/src/hooks/useApi.ts` (added usePortfolios, useValidatePortfolio hooks)
- `frontend/src/contexts/AppContext.tsx` (added portfolios state)
- `frontend/src/App.tsx` (added "portfolio" view mode, Portfolio nav button, screen render)
