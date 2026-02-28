# Story 6.4b: Wire GUI Prototype to FastAPI Backend

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **policy analyst (Sophie)**,
I want **the static GUI prototype wired to a FastAPI backend so that scenario creation, simulation runs, and comparison views use real data from the Python API instead of mock data**,
so that **I can operate the full analysis workflow — from template selection through parameter editing to scenario comparison — without writing code**.

## Acceptance Criteria

From backlog (BKL-604b), aligned with FR32 (no-code GUI for scenario operations). Depends on BKL-601 (Python API, done) and BKL-604a (static GUI prototype, done).

1. **AC-1: Scenario creation from template without code editing**
   - Given the wired GUI, when an analyst selects a policy template, edits parameters, and clicks "Create Scenario", then a scenario is created via the backend API using `create_scenario()`.
   - The created scenario appears in the scenario list (left panel) with correct metadata.
   - Template fast-path: selecting a pre-built template pre-fills parameters with defaults from the template pack.

2. **AC-2: Baseline cloning and reform creation**
   - Given the wired GUI, when an analyst clones a baseline scenario and modifies parameters, then a reform scenario is created and linked to the baseline via `clone_scenario()`.
   - The reform scenario shows the linked baseline reference.
   - Parameter deltas between baseline and reform are visible in the ParameterRow components.

3. **AC-3: Simulation execution with real results**
   - Given a configured scenario, when the analyst clicks "Run Simulation", then the backend executes `run_scenario()` and returns real computation results.
   - RunProgressBar shows real progress (year-by-year updates).
   - Results view displays actual distributional indicators from the `SimulationResult`.
   - DistributionalChart renders real decile data from `result.indicators("distributional")`.

4. **AC-4: Scenario comparison with real indicator data**
   - Given two completed runs in the GUI, when comparison is invoked, then side-by-side indicator tables display real data from the backend.
   - ComparisonView shows actual welfare, fiscal, and distributional indicators.
   - Delta columns compute correctly from real scenario results.

5. **AC-5: Export actions wired to backend**
   - Given completed scenario results, when the analyst clicks export (CSV or Parquet), then the backend calls `result.export_csv()` or `result.export_parquet()` and serves the file for download.
   - Export uses the API from Story 6-5 (BKL-605, done).

6. **AC-6: Error handling surfaces actionable messages**
   - Given an API error (configuration, simulation, or validation), when surfaced in the GUI, then the error follows the "[What failed] — [Why] — [How to fix]" format from Story 6-6.
   - Errors appear as toast notifications or inline messages — never raw stack traces.

7. **AC-7: Shared-password authentication**
   - Given the MVP deployment, when a user first accesses the GUI, then a password prompt appears.
   - The password is validated against the backend's shared-password middleware.
   - Session token stored in browser session; subsequent API calls include the token.

## Dependencies

Dependency gate: if any hard dependency below is not `done`, set this story to `blocked`.

- **Hard dependency: Story 6-1 (BKL-601) — DONE**
  - Provides `run_scenario()`, `create_scenario()`, `clone_scenario()`, `list_scenarios()`, `get_scenario()`, `SimulationResult`, `ScenarioConfig`, `RunConfig`.

- **Hard dependency: Story 6-4a (BKL-604a) — DONE**
  - Provides static GUI prototype with all screens, components, and mock data in `frontend/`.

- **Hard dependency: Story 6-5 (BKL-605) — DONE**
  - Provides `result.export_csv()`, `result.export_parquet()`, indicator/comparison export methods.

- **Soft dependency: Story 6-6 (BKL-606) — DONE**
  - Provides improved error UX format. AC-6 can use existing error types; 6-6 enhances them.

- **Soft dependency: Story 5-6 (BKL-506) — REVIEW**
  - Warning system for unvalidated templates. GUI can display warnings from `SimulationResult.metadata["warnings"]` if available.

## Tasks / Subtasks

- [ ] Task 0: Add FastAPI + uvicorn dependencies to project (AC: #1-#7)
  - [ ] 0.1 Add `fastapi>=0.133.0`, `uvicorn[standard]>=0.41.0`, `python-multipart>=0.0.9` to `pyproject.toml` optional dependencies (`[server]` extra)
  - [ ] 0.2 Verify `uv sync --extra server` installs correctly
  - [ ] 0.3 Create `src/reformlab/server/` package with `__init__.py`
  - [ ] 0.4 Add missing frontend dependencies: `cd frontend && npm install sonner next-themes` (required by existing `components/ui/sonner.tsx`)

- [ ] Task 1: Implement FastAPI application and route structure (AC: #1, #2, #3, #4, #5, #7)
  - [ ] 1.1 Create `src/reformlab/server/app.py` — FastAPI app factory with CORS middleware (allow `localhost:5173` for dev)
  - [ ] 1.2 Create `src/reformlab/server/auth.py` — shared-password middleware reading `REFORMLAB_PASSWORD` env var, session token in cookie
  - [ ] 1.3 Create `src/reformlab/server/models.py` — Pydantic v2 request/response models mirroring Python API types (`ScenarioConfigRequest`, `RunRequest`, `SimulationResultResponse`, `IndicatorResponse`, `ExportRequest`)
  - [ ] 1.4 Create `src/reformlab/server/routes/scenarios.py` — scenario CRUD endpoints:
    - `GET /api/scenarios` → `list_scenarios()`
    - `GET /api/scenarios/{name}` → `get_scenario(name)`
    - `POST /api/scenarios` → `create_scenario()`
    - `POST /api/scenarios/{name}/clone` → `clone_scenario()`
  - [ ] 1.5 Create `src/reformlab/server/routes/runs.py` — simulation run endpoints:
    - `POST /api/runs` → `run_scenario()` (returns `SimulationResultResponse`)
    - `POST /api/runs/memory-check` → `check_memory_requirements()`
  - [ ] 1.6 Create `src/reformlab/server/routes/indicators.py` — indicator endpoints:
    - `POST /api/indicators/{type}` → `result.indicators(type)` (distributional, geographic, welfare, fiscal)
    - `POST /api/comparison` → scenario comparison
  - [ ] 1.7 Create `src/reformlab/server/routes/exports.py` — export endpoints:
    - `POST /api/exports/csv` → `result.export_csv()` → file download response
    - `POST /api/exports/parquet` → `result.export_parquet()` → file download response
  - [ ] 1.8 Create `src/reformlab/server/routes/templates.py` — template listing:
    - `GET /api/templates` → list available scenario templates with metadata
    - `GET /api/templates/{name}` → template details with default parameters
  - [ ] 1.9 Create `src/reformlab/server/routes/populations.py` — population data:
    - `GET /api/populations` → list available population datasets (scan `data/populations/` directory for CSV/Parquet files; no Python API function exists — implement as a file listing utility in the route handler)
  - [ ] 1.10 Wire error handlers: translate `ConfigurationError`, `SimulationError`, `ValidationErrors` to structured JSON responses with HTTP status codes
  - [ ] 1.11 Create `src/reformlab/server/dependencies.py` — FastAPI dependency injection for `ComputationAdapter` instance and result cache (in-memory LRU dict, max 10 entries)

- [ ] Task 2: Configure Vite proxy for development (AC: #3)
  - [ ] 2.1 Update `frontend/vite.config.ts` to proxy `/api/*` requests to `http://localhost:8000`
  - [ ] 2.2 Verify proxy works: `npm run dev` (frontend) + `uv run uvicorn reformlab.server.app:create_app --factory --reload --port 8000` (backend)

- [ ] Task 3: Create frontend API client layer (AC: #1-#6)
  - [ ] 3.1 Create `frontend/src/api/client.ts` — typed fetch wrapper with error handling, auth token injection, base URL configuration
  - [ ] 3.2 Create `frontend/src/api/scenarios.ts` — scenario API functions: `listScenarios()`, `getScenario()`, `createScenario()`, `cloneScenario()`
  - [ ] 3.3 Create `frontend/src/api/runs.ts` — run API functions: `runScenario()`, `checkMemory()`
  - [ ] 3.4 Create `frontend/src/api/indicators.ts` — indicator API functions: `getIndicators()`, `compareScenarios()`
  - [ ] 3.5 Create `frontend/src/api/exports.ts` — export API functions: `exportCsv()`, `exportParquet()` (trigger browser file download)
  - [ ] 3.6 Create `frontend/src/api/templates.ts` — template API functions: `listTemplates()`, `getTemplate()`
  - [ ] 3.7 Create `frontend/src/api/populations.ts` — population API functions: `listPopulations()`
  - [ ] 3.8 Create `frontend/src/api/types.ts` — TypeScript interfaces matching Pydantic response models

- [ ] Task 4: Wire frontend components to real API (AC: #1, #2, #3, #4)
  - [ ] 4.1 Replace mock population data in `PopulationSelectionScreen` with `listPopulations()` API call
  - [ ] 4.2 Replace mock template data in `TemplateSelectionScreen` with `listTemplates()` API call
  - [ ] 4.3 Replace mock parameter data in `ParameterEditingScreen` with template-specific parameters from `getTemplate()`
  - [ ] 4.4 Wire "Create Scenario" action to `createScenario()` API call
  - [ ] 4.5 Wire "Clone" action on ScenarioCard to `cloneScenario()` API call
  - [ ] 4.6 Wire "Run Simulation" button to `runScenario()` API call; update RunProgressBar with real progress
  - [ ] 4.7 Wire results view: fetch real indicators via `getIndicators("distributional")` and render in DistributionalChart
  - [ ] 4.8 Wire ComparisonView to fetch real comparison data via `compareScenarios()`
  - [ ] 4.9 Wire export buttons to `exportCsv()` / `exportParquet()` API calls
  - [ ] 4.10 Update scenario list (left panel) to load from `listScenarios()` on mount and refresh after mutations

- [ ] Task 5: Implement authentication flow (AC: #7)
  - [ ] 5.1 Create `frontend/src/components/auth/PasswordPrompt.tsx` — modal password input shown on first access
  - [ ] 5.2 Store auth token in `sessionStorage`; inject in API client headers
  - [ ] 5.3 Handle 401 responses by showing password prompt again
  - [ ] 5.4 Wire auth middleware in FastAPI to validate token on every `/api/*` request

- [ ] Task 6: Error handling and loading states (AC: #6)
  - [ ] 6.1 Add toast notification system (Sonner already in ui/) for API errors
  - [ ] 6.2 Parse structured error responses and display "[What] — [Why] — [Fix]" format in toasts
  - [ ] 6.3 Add loading spinners/skeleton states to screens during API calls
  - [ ] 6.4 Handle network errors gracefully (offline state, connection refused)

- [ ] Task 7: State management upgrade (AC: #1-#4)
  - [ ] 7.1 Replace `useState`-based state in `App.tsx` with React Context for shared API state (scenarios, templates, populations, active run)
  - [ ] 7.2 Implement data fetching hooks: `useScenarios()`, `useTemplates()`, `usePopulations()`, `useRunResult()`
  - [ ] 7.3 Refetch data after mutations (create, clone, run) — simple refetch-on-success pattern, no optimistic updates for MVP

- [ ] Task 8: Development workflow and testing (AC: #1-#7)
  - [ ] 8.1 Add `dev:backend` script to `package.json` or document `uv run uvicorn` command
  - [ ] 8.2 Add backend API tests in `tests/server/` — test route handlers with mock adapter
  - [ ] 8.3 Verify full flow: start backend → start frontend → create scenario → run → compare → export
  - [ ] 8.4 Run `npm run typecheck` and `npm run lint` on frontend
  - [ ] 8.5 Run `uv run ruff check src/reformlab/server/` and `uv run mypy src/reformlab/server/` on backend

## Dev Notes

### Architecture Compliance

This story implements **FR32** (no-code GUI for scenario operations) as a wired application. Per the architecture document's Deployment & GUI Architecture section:

- **Monorepo structure**: Backend FastAPI server in `src/reformlab/server/`, frontend React app in `frontend/`
- **FastAPI wraps the Python API**: The server is a thin HTTP facade over the existing `reformlab` Python API (Story 6-1). No business logic in route handlers.
- **Shared-password authentication**: Single password in env var, session token in cookie. No user accounts, no OAuth. [Source: architecture.md#Authentication-(MVP)]
- **File-based storage**: Scenario configs, run outputs, manifests are files on disk. No database. [Source: architecture.md#Data-Storage-(MVP)]

### Critical Implementation Rules

**Backend (FastAPI):**

- **Every file starts with** `from __future__ import annotations`
- **Frozen dataclasses for domain types** — Pydantic models for API request/response, frozen dataclasses for internal types
- **Subsystem-specific exceptions** — use existing `ConfigurationError`, `SimulationError`, `ValidationErrors` from `reformlab.interfaces.errors`
- **PyArrow is the canonical data type** — serialize `pa.Table` to JSON via `table.to_pydict()` for API responses; do not convert to pandas
- **Never import OpenFisca** in server code — use `ComputationAdapter` protocol via the Python API
- **Structured logging** — `logging.getLogger(__name__)` with `key=value` format
- **mypy strict** — all server code must pass `mypy --strict`
- **ruff compliance** — E, F, I, W rule sets

**Frontend (React/TypeScript):**

- **Tailwind-only styling** — no CSS modules, no styled-components, no inline styles
- **cva pattern** for component variants (following Shadcn/ui conventions)
- **No `forwardRef`** — React 19 accepts `ref` as a prop directly
- **`@import "tailwindcss"`** in CSS (Tailwind v4)
- **TypeScript strict mode** — all API response types explicitly typed
- **No external state management library** — React Context is sufficient for MVP
- **Semantic HTML** — `<button>` not `<div onClick>`, proper ARIA labels

### Python API Surface (from Story 6-1)

The FastAPI backend wraps these existing functions — do NOT reimplement any logic:

```python
# Core execution
run_scenario(
    config: RunConfig | ScenarioConfig | Path | dict[str, Any],
    adapter: ComputationAdapter | None = None,  # inject adapter for testing
    *,
    skip_memory_check: bool = False,
) -> SimulationResult
check_memory_requirements(config: RunConfig | ScenarioConfig, skip_check: bool = False) -> MemoryCheckResult

# Scenario management
create_scenario(scenario: Any, name: str, register: bool = False) -> str | Any
clone_scenario(name: str, version_id: str | None = None, new_name: str | None = None) -> Any
list_scenarios() -> list[str]
get_scenario(name: str, version_id: str | None = None) -> Any

# Result methods
SimulationResult.indicators(indicator_type: str, **kwargs: Any) -> IndicatorResult
SimulationResult.export_csv(path: str | Path) -> Path
SimulationResult.export_parquet(path: str | Path) -> Path

# Error types (keyword-only constructors)
ConfigurationError(*, field_path: str, expected: str, actual: Any, message: str | None = None, fix: str | None = None)
SimulationError(message: str, *, cause: Exception | None = None, fix: str | None = None, partial_states: dict[int, Any] | None = None)
ValidationErrors(issues: list[ValidationIssue])
```

### FastAPI Server Structure

```
src/reformlab/server/
├── __init__.py
├── app.py              ← FastAPI app factory, CORS, middleware registration
├── auth.py             ← Shared-password middleware, session token
├── models.py           ← Pydantic v2 request/response models
├── dependencies.py     ← FastAPI dependency injection (adapter, result cache)
├── routes/
│   ├── __init__.py
│   ├── scenarios.py    ← Scenario CRUD endpoints
│   ├── runs.py         ← Simulation execution endpoints
│   ├── indicators.py   ← Indicator computation endpoints
│   ├── exports.py      ← File export/download endpoints
│   ├── templates.py    ← Template listing endpoints
│   └── populations.py  ← Population dataset listing endpoints
```

### Frontend API Layer Structure

```
frontend/src/api/
├── client.ts           ← Typed fetch wrapper, auth token, error parsing
├── types.ts            ← TypeScript interfaces matching Pydantic models
├── scenarios.ts        ← Scenario CRUD API functions
├── runs.ts             ← Simulation run API functions
├── indicators.ts       ← Indicator API functions
├── exports.ts          ← Export download triggers
├── templates.ts        ← Template listing API functions
└── populations.ts      ← Population dataset listing API functions
```

### API Route Map

| Method | Path | Handler | Python API Function |
|--------|------|---------|-------------------|
| GET | `/api/scenarios` | `list_scenarios_route` | `list_scenarios()` |
| GET | `/api/scenarios/{name}` | `get_scenario_route` | `get_scenario(name)` |
| POST | `/api/scenarios` | `create_scenario_route` | `create_scenario()` |
| POST | `/api/scenarios/{name}/clone` | `clone_scenario_route` | `clone_scenario()` |
| POST | `/api/runs` | `run_scenario_route` | `run_scenario()` |
| POST | `/api/runs/memory-check` | `check_memory_route` | `check_memory_requirements()` |
| POST | `/api/indicators/{type}` | `get_indicators_route` | `result.indicators(type)` |
| POST | `/api/comparison` | `compare_route` | comparison via indicators |
| POST | `/api/exports/csv` | `export_csv_route` | `result.export_csv()` |
| POST | `/api/exports/parquet` | `export_parquet_route` | `result.export_parquet()` |
| GET | `/api/templates` | `list_templates_route` | Template registry scan |
| GET | `/api/templates/{name}` | `get_template_route` | Template details + defaults |
| GET | `/api/populations` | `list_populations_route` | Population data scan |
| POST | `/api/auth/login` | `login_route` | Password validation |

### Run Progress Strategy

The `run_scenario()` call can take several seconds for multi-year runs. Options for progress feedback:

**Option A (Recommended for MVP): Polling**
- `POST /api/runs` returns immediately with a `run_id`
- `GET /api/runs/{run_id}/status` returns progress (current year, total years, percentage)
- Frontend polls every 500ms until status is "completed" or "failed"
- Backend runs simulation in a background thread, stores progress in a dict keyed by `run_id`

**Option B: Server-Sent Events (SSE)**
- `POST /api/runs` returns a `StreamingResponse` with year-by-year progress events
- Frontend uses `EventSource` or `fetch` with `ReadableStream`
- More real-time but more complex

**Option C: Synchronous (simplest)**
- `POST /api/runs` blocks until complete, returns full result
- Frontend shows indeterminate progress bar
- Acceptable for MVP if runs complete in < 10 seconds

Choose based on expected run duration. For 100k households over 10 years, typical runs should be under 10 seconds — **Option C is acceptable for MVP**, upgrade to Option A if runs are slow.

### Result Caching Strategy

`SimulationResult` objects (containing PyArrow tables) are too large to serialize repeatedly. The backend should:

1. Run simulation → get `SimulationResult`
2. Store result in an in-memory dict keyed by `run_id` (or scenario name + version)
3. Subsequent indicator/export/comparison requests reference the cached result
4. Cache eviction: LRU with max 10 results, or manual cleanup

### Serialization Notes

- **PyArrow `pa.Table` → JSON**: Use `table.to_pydict()` which returns `dict[str, list]`, then serialize with standard JSON
- **`Path` objects**: Pydantic v2 auto-serializes `Path` to `str` in JSON mode
- **`datetime` objects**: Pydantic v2 auto-serializes to ISO 8601 strings
- **Frozen dataclasses → Pydantic**: Create mirror Pydantic models for API layer; convert from/to domain types in route handlers
- **Large responses**: For panel data (household × year), consider pagination or streaming

### Design Tokens and UX Patterns

The existing frontend uses these patterns — maintain consistency when adding new components:

- **Dense Terminal style**: Hard 1px borders, no shadows, tight padding (`p-3`), square corners
- **Color tokens**: emerald=validated, amber=warning, stone=unreviewed, red=error, blue=selection, violet=lineage, sky=reform/delta
- **Typography**: Inter for UI, IBM Plex Mono for numeric data values
- **Chart colors**: baseline=slate-500, reform-a=blue-500, reform-b=violet-500
- **Badge component**: Used for status indicators (6 variants: default, success, warning, destructive, info, violet)
- **Toast notifications**: Sonner component already available in `components/ui/sonner.tsx`

### Latest Technical Stack (February 2026)

| Package | Version | Notes |
|---------|---------|-------|
| FastAPI | >= 0.133.0 | Use `fastapi[standard]`; strict content-type validation default |
| Pydantic | v2.10+ | Use `model_validate()` not `parse_obj()`; `model_dump()` not `dict()` |
| uvicorn | >= 0.41.0 | Use `[standard]` extra; `--reload` for dev |
| python-multipart | >= 0.0.9 | Required by FastAPI for form data |
| React | 19.x | `use()` hook available but not required for MVP |
| Vite | 7.x | Proxy config in `server.proxy` in `vite.config.ts` |
| Tailwind CSS | 4.x | `@import "tailwindcss"`, `@theme` blocks, `@tailwindcss/vite` plugin |

**Critical FastAPI notes:**
- CORS middleware MUST be added before other middleware
- Use Pydantic v2 models (not v1 compatibility mode)
- `python-multipart` required even for JSON-only endpoints (FastAPI dependency)

### Scope Guardrails

**In scope:**
- FastAPI backend wrapping existing Python API
- Pydantic request/response models
- Frontend API client layer (typed fetch)
- Wiring all existing screens to real API data
- Shared-password authentication (single password, session token)
- Export actions (CSV/Parquet download)
- Error display (toast notifications)
- Loading states
- Vite proxy configuration for development
- Basic React Context for shared state

**Out of scope (deferred):**
- WebSocket or SSE for real-time progress (use polling or synchronous if needed)
- React Flow / lineage DAG visualization (Phase 1b per UX spec)
- WaterfallChart component (Phase 1b)
- Command palette (Cmd+K) — Phase 2
- Lens overlays — Phase 2
- OAuth or user accounts — Phase 3
- Docker/Kamal deployment configuration (separate ops task)
- Database migration — file-based storage is sufficient
- Unit tests for React components (manual visual verification)
- Parameter sweep / sensitivity analysis UI

### Project Structure Notes

- `src/reformlab/server/` is a NEW package — create it with `__init__.py`
- `frontend/src/api/` is a NEW directory — create it
- Do NOT modify any existing Python API code in `src/reformlab/interfaces/`
- Do NOT modify existing backend subsystems (computation, data, templates, orchestrator, etc.)
- The `frontend/Dockerfile` and `frontend/nginx.conf` already exist — do NOT overwrite them
- Existing mock data in `frontend/src/data/mock-data.ts` can be kept as fallback but should not be the primary data source

### References

- [Source: architecture.md#Deployment-&-GUI-Architecture] — Monorepo structure, frontend stack, deployment topology
- [Source: architecture.md#Frontend-Stack] — React 18+/TS, Vite, Shadcn/ui + Radix, Tailwind v4, Recharts
- [Source: architecture.md#Backend-Stack] — FastAPI, Python 3.13+, uvicorn
- [Source: architecture.md#Authentication-(MVP)] — Shared-password, session token, no user accounts
- [Source: architecture.md#Data-Storage-(MVP)] — File-based, Docker volume mount, no database
- [Source: ux-design-specification.md#Defining-Experience] — Mode 1 (configuration) + Mode 2 (execution), continuous workspace
- [Source: ux-design-specification.md#Effortless-Interactions] — One-click simulation, auto-comparison, export
- [Source: ux-design-specification.md#Visual-Design-Foundation] — Dense Terminal, color tokens, typography
- [Source: ux-design-specification.md#Component-Strategy] — ParameterRow, ScenarioCard, RunProgressBar, ComparisonView specs
- [Source: backlog BKL-604b] — Story acceptance criteria
- [Source: prd.md#FR32] — No-code GUI for scenario operations
- [Source: prd.md#FR33] — Export tables and indicators in CSV/Parquet
- [Source: project-context.md] — All critical implementation rules, testing conventions, code quality standards
- [Source: 6-4a story] — Previous story: frontend prototype structure, component inventory, design tokens
- [Source: 6-1 story] — Python API surface: functions, types, error hierarchy
- [Source: 6-5 story] — Export API: `export_csv()`, `export_parquet()` on results and indicators

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
