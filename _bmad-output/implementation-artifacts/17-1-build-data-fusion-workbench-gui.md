# Story 17.1: Build Data Fusion Workbench GUI

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a non-coding policy analyst,
I want a web-based Data Fusion Workbench where I can browse institutional data sources, select datasets, choose merge methods with plain-language explanations, generate a synthetic population, and validate it against known marginals,
so that I can build a credible population for policy simulation without writing code or understanding statistical internals.

## Acceptance Criteria

1. **AC-1: Data source browsing** — Given the Data Fusion Workbench screen, when the analyst opens it, then available data sources are listed with metadata (name, description, variables, record count, source URL) grouped by provider (INSEE, Eurostat, ADEME, SDES).

2. **AC-2: Variable overlap display** — Given the source browser, when the analyst selects two or more data sources, then the GUI shows overlapping and unique variables between selected sources, and prompts merge method selection.

3. **AC-3: Merge method explanation** — Given merge method selection, when the analyst chooses a method (uniform, IPF, conditional sampling), then a plain-language explanation of the method's assumptions and trade-offs is displayed alongside configurable parameters.

4. **AC-4: Population generation with progress** — Given a configured merge, when the analyst clicks "Generate Population", then the population generation pipeline runs and the GUI shows progress (current step, percentage, ETA).

5. **AC-5: Population preview and validation** — Given a generated population, when previewed, then the GUI displays summary statistics (record count, variable distributions, key demographics) and validation results against known marginals with pass/fail indicators.

6. **AC-6: Iterative regeneration** — Given the workbench, when the analyst adjusts merge parameters and regenerates, then the new population reflects the changed configuration without requiring page reload.

## Tasks / Subtasks

- [ ] Task 1: Implement FastAPI endpoints for data fusion operations (AC: 1, 2, 3, 4, 5)
  - [ ] 1.1: Create `src/reformlab/server/routes/data_fusion.py` with router
  - [ ] 1.2: Add `GET /api/data-sources` endpoint — list all available datasets from all 4 provider catalogs with metadata (name, description, column count, source URL)
  - [ ] 1.3: Add `GET /api/data-sources/{provider}/{dataset_id}` endpoint — return dataset detail including column schema (name, type, description)
  - [ ] 1.4: Add `GET /api/merge-methods` endpoint — return available merge methods with plain-language descriptions, assumption statements, and parameter specifications
  - [ ] 1.5: Add `POST /api/data-fusion/generate` endpoint — accept source selections + merge config, execute `PopulationPipeline`, return generation result with summary stats, assumption chain, step log, and validation results
  - [ ] 1.6: Add Pydantic v2 request/response models to `src/reformlab/server/models.py` for all new endpoints
  - [ ] 1.7: Register data fusion router in `src/reformlab/server/app.py`
  - [ ] 1.8: Write backend tests in `tests/server/test_data_fusion.py`

- [ ] Task 2: Define frontend TypeScript types and API client layer (AC: 1, 2, 3, 4, 5)
  - [ ] 2.1: Add TypeScript interfaces to `frontend/src/api/types.ts`: `DataSourceItem`, `DataSourceDetail`, `VariableInfo`, `MergeMethodInfo`, `MergeMethodParam`, `GenerationRequest`, `GenerationResult`, `PopulationSummary`, `ValidationResultResponse`, `MarginalResultResponse`
  - [ ] 2.2: Create `frontend/src/api/data-fusion.ts` with API functions: `listDataSources()`, `getDataSourceDetail()`, `listMergeMethods()`, `generatePopulation()`
  - [ ] 2.3: Add `useDataSources()` and `useMergeMethods()` hooks to `frontend/src/hooks/useApi.ts` following existing mock-data-fallback pattern
  - [ ] 2.4: Add mock data for data sources and merge methods in `frontend/src/data/mock-data.ts`

- [ ] Task 3: Build Data Source Browser component (AC: 1, 2)
  - [ ] 3.1: Create `frontend/src/components/simulation/DataSourceBrowser.tsx` — card grid of data sources grouped by provider, with search/filter, multi-select checkboxes, metadata display (name, description, variable count, record count, source URL)
  - [ ] 3.2: Create `frontend/src/components/simulation/VariableOverlapView.tsx` — given 2+ selected sources, display table of overlapping variables (shared columns) and unique variables per source, with column type badges
  - [ ] 3.3: Add unit tests for DataSourceBrowser and VariableOverlapView

- [ ] Task 4: Build Merge Method Selector component (AC: 3)
  - [ ] 4.1: Create `frontend/src/components/simulation/MergeMethodSelector.tsx` — radio/card selection of available merge methods, each with icon, name, plain-language assumption statement, and when-appropriate guidance
  - [ ] 4.2: Create `frontend/src/components/simulation/MergeParametersPanel.tsx` — method-specific parameter inputs: seed (all methods), IPF constraints (dimension + targets), conditional strata columns; using existing ParameterRow pattern
  - [ ] 4.3: Add unit tests for MergeMethodSelector and MergeParametersPanel

- [ ] Task 5: Build Population Preview and Validation components (AC: 4, 5)
  - [ ] 5.1: Create `frontend/src/components/simulation/PopulationGenerationProgress.tsx` — progress bar (reuse RunProgressBar pattern) with current step label, percentage, ETA, cancel-ability
  - [ ] 5.2: Create `frontend/src/components/simulation/PopulationPreview.tsx` — tabbed view (Summary | Distributions | Assumptions) showing record count, column list, key demographic stats, assumption chain from pipeline
  - [ ] 5.3: Create `frontend/src/components/simulation/PopulationDistributionChart.tsx` — Recharts bar chart showing distribution of key variables (income deciles, heating types, vehicle types) using existing DistributionalChart pattern
  - [ ] 5.4: Create `frontend/src/components/simulation/PopulationValidationPanel.tsx` — per-marginal pass/fail badges, deviation values, expected vs. observed comparison, overall validation status
  - [ ] 5.5: Add unit tests for PopulationPreview and PopulationValidationPanel

- [ ] Task 6: Build Data Fusion Workbench screen and integrate into workspace (AC: 1, 2, 3, 4, 5, 6)
  - [ ] 6.1: Create `frontend/src/components/screens/DataFusionWorkbench.tsx` — orchestration container with step flow: source selection → variable review → method selection → generation → preview; back/next navigation; state management for selected sources, merge method, generation result
  - [ ] 6.2: Integrate DataFusionWorkbench into `App.tsx` — add `"data-fusion"` view mode, wire into ModelConfigStepper as first step ("Population"), update left panel navigation
  - [ ] 6.3: Update `frontend/src/contexts/AppContext.tsx` — add data fusion state (selected sources, merge method, generation result, population preview), expose through context
  - [ ] 6.4: Add unit tests for DataFusionWorkbench screen component
  - [ ] 6.5: Verify full end-to-end flow: open workbench → select sources → review variables → choose method → generate → preview → regenerate with different parameters

- [ ] Task 7: Run quality checks (AC: all)
  - [ ] 7.1: Run `uv run ruff check src/ tests/` and fix any lint issues
  - [ ] 7.2: Run `uv run mypy src/` and fix any type errors
  - [ ] 7.3: Run `cd frontend && npm run typecheck && npm run lint` and fix any issues
  - [ ] 7.4: Run `uv run pytest tests/server/` to verify backend tests pass
  - [ ] 7.5: Run `cd frontend && npm test` to verify frontend tests pass

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Backend — FastAPI route pattern:**
- All routes follow pattern in `src/reformlab/server/routes/templates.py` and `scenarios.py`
- Router created with `APIRouter()`, registered in `app.py` via `app.include_router(router, prefix="/api/data-fusion", tags=["data-fusion"])`
- Pydantic v2 models in `models.py` — use `BaseModel` with `Field(...)`, `model_config = {"from_attributes": True}`
- Structured error responses with `what`, `why`, `fix` fields — use existing exception handlers from `app.py`
- `from __future__ import annotations` on every Python file
- Logging: `logging.getLogger(__name__)`, structured `key=value` format

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

### Source Tree Components to Touch

**New files:**
```
src/reformlab/server/routes/data_fusion.py        ← New API routes
tests/server/test_data_fusion.py                  ← Backend tests
frontend/src/api/data-fusion.ts                   ← API client functions
frontend/src/components/simulation/DataSourceBrowser.tsx
frontend/src/components/simulation/VariableOverlapView.tsx
frontend/src/components/simulation/MergeMethodSelector.tsx
frontend/src/components/simulation/MergeParametersPanel.tsx
frontend/src/components/simulation/PopulationGenerationProgress.tsx
frontend/src/components/simulation/PopulationPreview.tsx
frontend/src/components/simulation/PopulationDistributionChart.tsx
frontend/src/components/simulation/PopulationValidationPanel.tsx
frontend/src/components/screens/DataFusionWorkbench.tsx
```

**Modified files:**
```
src/reformlab/server/models.py                    ← Add Pydantic models
src/reformlab/server/app.py                       ← Register new router
frontend/src/api/types.ts                         ← Add TypeScript interfaces
frontend/src/data/mock-data.ts                    ← Add mock data
frontend/src/hooks/useApi.ts                      ← Add hooks
frontend/src/contexts/AppContext.tsx               ← Add data fusion state
frontend/src/App.tsx                              ← Add view mode, wire workbench
```

### Backend Integration with Population Library

The backend endpoints wrap the fully-implemented Epic 11 population generation library. Key imports:

```python
# Data source discovery — catalogs are dicts with dataset metadata
from reformlab.population import (
    INSEE_CATALOG, EUROSTAT_CATALOG, ADEME_CATALOG, SDES_CATALOG,
    INSEE_AVAILABLE_DATASETS, EUROSTAT_AVAILABLE_DATASETS,
    ADEME_AVAILABLE_DATASETS, SDES_AVAILABLE_DATASETS,
)

# Loader factories — create configured loaders per provider
from reformlab.population import (
    get_insee_loader, get_eurostat_loader, get_ademe_loader, get_sdes_loader,
    make_insee_config, make_eurostat_config, make_ademe_config, make_sdes_config,
    SourceCache,
)

# Merge methods — statistical fusion implementations
from reformlab.population import (
    UniformMergeMethod, IPFMergeMethod, ConditionalSamplingMethod,
    MergeConfig, IPFConstraint,
)

# Pipeline — composable builder
from reformlab.population import (
    PopulationPipeline, PipelineResult, PipelineStepLog,
)

# Validation — marginal distribution checks
from reformlab.population import (
    PopulationValidator, MarginalConstraint, ValidationResult,
)
```

**Pipeline usage pattern** (what the API endpoint wraps):
```python
cache = SourceCache()
pipeline = PopulationPipeline(description="User's population")
pipeline.add_source("income", get_insee_loader("filosofi_2021_commune", cache=cache),
                     make_insee_config("filosofi_2021_commune"))
pipeline.add_source("vehicles", get_sdes_loader("vehicle_fleet", cache=cache),
                     make_sdes_config("vehicle_fleet"))
pipeline.add_merge("merged", left="income", right="vehicles",
                   method=UniformMergeMethod(), config=MergeConfig(seed=42))
result = pipeline.execute()
# result.table (pa.Table), result.assumption_chain, result.step_log
```

**Available data source catalogs:**
- `INSEE_CATALOG`: `filosofi_2021_commune`, `filosofi_2021_iris_declared`, `filosofi_2021_iris_disposable`
- `EUROSTAT_CATALOG`: `ilc_di01` (income distribution), `nrg_d_hhq` (energy consumption)
- `ADEME_CATALOG`: `base_carbone` (emission factors)
- `SDES_CATALOG`: `vehicle_fleet` (fleet composition by fuel/age/region)

**Available merge methods:**
- `UniformMergeMethod` — no parameters beyond seed; assumes independence between sources
- `IPFMergeMethod(constraints, max_iterations=100, tolerance=1e-6)` — needs `IPFConstraint(dimension, targets)` list
- `ConditionalSamplingMethod(strata_columns)` — needs shared column names for stratification

### Merge Method Plain-Language Descriptions (for GUI display)

**Uniform Distribution:**
- **What it does:** Matches each household from one source to a randomly chosen household from another source, with equal probability.
- **Assumption:** Variables in the two sources are statistically independent — knowing a household's income tells you nothing about their vehicle type.
- **When appropriate:** Quick baseline when no better information is available about correlations between sources.
- **Trade-off:** Fast and simple, but may produce unrealistic combinations (e.g., low-income household paired with luxury vehicle).

**Iterative Proportional Fitting (IPF):**
- **What it does:** Adjusts matching weights so that the final population matches known aggregate statistics (marginals) from official sources.
- **Assumption:** The population matches known distribution totals — if INSEE says 10% of households are in decile 1, the result respects that.
- **When appropriate:** You have reliable census or administrative marginals to calibrate against.
- **Trade-off:** More accurate aggregates, but requires knowing the target marginals upfront; may not converge if constraints are contradictory.

**Conditional Sampling:**
- **What it does:** Groups households by a shared variable (e.g., income bracket), then matches randomly only within the same group.
- **Assumption:** Given the grouping variable, remaining variables are independent — within the same income bracket, vehicle and heating choices are uncorrelated.
- **When appropriate:** You know that some variable (like income or region) correlates with variables in both sources.
- **Trade-off:** Preserves known correlations through the grouping variable, but assumes independence within groups.

### Frontend Existing Components to Reuse

| Existing Component | Reuse in 17.1 |
|---|---|
| `RunProgressBar.tsx` | Pattern for `PopulationGenerationProgress` |
| `DistributionalChart.tsx` | Pattern for `PopulationDistributionChart` (Recharts bar chart) |
| `SummaryStatCard.tsx` | Pattern for population summary cards |
| `ParameterRow.tsx` | Pattern for merge method parameter inputs |
| `ScenarioCard.tsx` | Pattern for data source cards with selection state |
| `ModelConfigStepper.tsx` | Wire "Population" as first step |
| `PopulationSelectionScreen.tsx` | Pattern for card-grid selection screens |

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
- Builds GUI screens and backend endpoints for the data fusion workflow
- Wraps the fully-implemented Epic 11 population generation library
- Provides synchronous population generation (pipeline executes and returns in single request)
- Displays results with charts and validation panels

**What this story does NOT do:**
- Async/background population generation with WebSocket progress (simplify to synchronous for now; async can be added in 17.6 if needed)
- Persistent population storage (covered by Story 17.7)
- E2E browser tests with Playwright/Cypress (covered by Story 17.8)
- Real network data downloads from INSEE/Eurostat APIs — backend uses fixture/cached data; network download is opt-in via the existing loader infrastructure

### Anti-Patterns to Avoid

| Issue | Prevention |
|---|---|
| Building custom chart library | Reuse Recharts + existing `DistributionalChart` pattern |
| Adding CSS modules or styled-components | Tailwind-only; use `cn()` for conditional classes |
| Using `forwardRef` | React 19: ref is a regular prop |
| Mobile-responsive layouts | Desktop-only (min 1280px); show warning banner below |
| Importing OpenFisca in server routes | Population library handles all computation; server routes only call pipeline |
| Creating separate state management (Redux/Zustand) | Follow existing React Context pattern in AppContext.tsx |
| Adding new npm dependencies without justification | All needed dependencies already installed |
| Shadows on static layout elements | Shadows reserved exclusively for floating elements (dropdowns, modals, tooltips) |

### Testing Standards Summary

**Backend tests:**
- File: `tests/server/test_data_fusion.py`
- Use FastAPI `TestClient` pattern from `tests/server/test_api.py`
- Test each endpoint: valid input → expected response, invalid input → error with structured message
- Mock the population pipeline for unit tests — don't require real data downloads
- Use `pytest.raises(...)` with `match=` for error assertions

**Frontend tests:**
- Use Vitest + @testing-library/react (already configured)
- Test component rendering with mock data
- Test user interactions (select source, choose method, click generate)
- Test state transitions in workbench flow
- Follow existing test patterns in `frontend/src/__tests__/`

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| EPIC-11 (all stories) | **Produces** population library that 17.1 wraps via API |
| Story 6.4a/6.4b | **Established** GUI patterns (layout, components, API client) that 17.1 follows |
| Story 17.2 | **Consumer** — Portfolio Designer follows after Data Fusion in ModelConfigStepper |
| Story 17.6 | **Overlap** — 17.1 creates the data-fusion-specific endpoints; 17.6 covers remaining Phase 2 endpoints |
| Story 17.7 | **Extension** — persistent storage for generated populations (not in 17.1 scope) |
| Story 17.8 | **Extension** — E2E browser tests for the workbench flow (not in 17.1 scope) |

### Project Structure Notes

- Backend routes align with `src/reformlab/server/routes/` convention
- Frontend components align with `frontend/src/components/{simulation,screens}/` convention
- API client aligns with `frontend/src/api/` convention with typed fetch wrappers
- No new npm or Python dependencies required — all libraries already installed
- TypeScript path aliases (`@/`) already configured in `tsconfig.json`

### References

- [Source: docs/epics.md#Epic 17, Story 17.1] — Acceptance criteria
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Data Fusion Workbench] — Screen design, layout, components
- [Source: _bmad-output/planning-artifacts/architecture.md] — Tech stack, layered architecture
- [Source: docs/project-context.md] — Coding conventions, testing rules
- [Source: src/reformlab/population/__init__.py] — Public API for population generation library
- [Source: src/reformlab/server/routes/templates.py] — Backend route pattern reference
- [Source: src/reformlab/server/routes/populations.py] — Existing populations endpoint
- [Source: src/reformlab/server/models.py] — Pydantic model pattern reference
- [Source: frontend/src/App.tsx] — Workspace orchestration, view modes
- [Source: frontend/src/contexts/AppContext.tsx] — State management pattern
- [Source: frontend/src/hooks/useApi.ts] — Data fetching hook pattern
- [Source: frontend/src/api/client.ts] — API client with error handling
- [Source: frontend/src/components/simulation/] — Existing domain components
- [Source: frontend/src/components/screens/PopulationSelectionScreen.tsx] — Screen component pattern
- [Source: frontend/package.json] — Frontend dependency versions

## Dev Agent Record

### Agent Model Used

(To be filled during implementation)

### Debug Log References

(To be filled during implementation)

### Completion Notes List

(To be filled during implementation)

### File List

(To be filled during implementation)
