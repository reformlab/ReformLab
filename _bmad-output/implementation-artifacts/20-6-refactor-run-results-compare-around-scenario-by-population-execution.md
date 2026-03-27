# Story 20.6: Refactor Run / Results / Compare Around Scenario-by-Population Execution

**Status**: `in-progress`
**Epic**: EPIC-20 (Phase 3 Canonical Scenario Model)
**Story Type**: Refactoring
**Points**: 13
**Dependencies**: Story 20.5 (cross-stage validation gate)

---

## Story

Refactor Stage 4 (Run / Results / Compare) to reflect the durable scenario model introduced in Stories 20.1–20.5. The current Stage 4 components use a legacy props-based pattern that doesn't leverage `WorkspaceScenario` for state management. This refactoring must:

1. Present simulation results as a **scenario-by-population execution matrix**, making it explicit which scenarios have been executed against which populations
2. Preserve **scenario lineage** through comparison and export views, ensuring results remain traceable to their source scenario configuration
3. Implement **pluggable comparison dimensions** infrastructure to support EPIC-21 (Evidence Governance) where comparisons will span exogenous assumptions, calibration targets, and validation benchmarks

This story completes the Stage 4 modernization to use the canonical scenario model throughout the application.

---

## Acceptance Criteria

### AC-1: Results Presented as Scenario-by-Population Matrix

**Given** a user has multiple scenarios defined in their workspace
**When** they navigate to Stage 4 (Run / Results / Compare)
**Then** they see a matrix view showing:
- Rows: Scenarios (by name/portfolio)
- Columns: Populations (by name/source)
- Cells: Execution status (ExecutionStatus enum: NOT_EXECUTED, QUEUED, RUNNING, COMPLETED, FAILED) with quick access to results
- When multiple runs exist for same scenario-population: display latest completed run with optional run history drawer

**And** selecting a completed cell loads the corresponding results with full scenario context preserved.

### AC-2: Scenario Lineage Preserved Through Comparison/Export Views

**Given** a user has executed scenarios against one or more populations
**When** they view results or create comparisons
**Then** all result metadata includes:
- Scenario ID and name
- Portfolio composition snapshot (policy names + parameters as portfolio_snapshot field)
- Population selection and version (population_id + population_version fields)
- Engine configuration (logit model, discount rate from engine_config field)
- Execution timestamp and seed

**And** export actions embed lineage:
- CSV export: Add lineage columns (scenario_id, scenario_name, portfolio_name, population_id, logit_model, discount_rate, executed_at) at start
- Parquet export: Add lineage metadata to file schema
- Replication package: Create scenario.yaml alongside manifest.json with full scenario configuration

### AC-3: Comparison Infrastructure Supports Pluggable Comparison Dimensions

**Given** the comparison system architecture
**When** EPIC-21 adds new evidence asset types (exogenous time series, calibration targets)
**Then** the comparison model can be extended with new dimensions without modifying core comparison logic:
- `ComparisonDimension` registry pattern for extensible dimensions
- Extension boundary: only registry file additions allowed; core comparison logic files must remain unchanged
- Type-safe dimension configuration
- Default and custom dimension providers

**And** the comparison UI supports dynamic dimension rendering based on available dimensions.

---

## Tasks

### 20.6.1: Design Scenario-by-Population Execution Matrix UI

**Subtasks**:
- [x] Define `ExecutionStatus` enum: NOT_EXECUTED, QUEUED, RUNNING, COMPLETED, FAILED
- [x] Define `ExecutionMatrixCell` type: { scenarioId, populationId, status: ExecutionStatus, runId?, error?, startedAt?, finishedAt? }
- [x] Implement `ExecutionMatrix` component with sticky first column (scenario) and horizontal scroll for populations
- [x] Define cell click behavior: completed => open ResultsOverviewScreen, pending => open SimulationRunnerScreen
- [x] Add cell context menu using Shadcn DropdownMenu with actions: view, clone, delete, export, retry
- [x] Add loading skeleton for matrix initialization
- [x] Implement three empty states:
  - No scenarios: "Create a scenario first" with link to Stage 1
  - No populations: "Select populations in Stage 2" with link to Stage 2
  - No executions: "Run simulations to see results" with Run button
- [x] Add responsive behavior: < 1200px single column with horizontal scroll, >= 1200px sticky first column

**Dev Notes**:
- Matrix should populate from `/api/results` endpoint (cross-reference scenario_id/population_id with workspace scenarios)
- For this story: matrix displays post-run executions only (running/cancel states deferred to future async execution story)
- Cell tooltip content: NOT_EXECUTED="Click to run simulation", RUNNING="Simulation in progress...", COMPLETED="Run {runId} completed at {timestamp}", FAILED="Run failed: {error}. Click to retry"
- Use Shadcn/ui `Table` component with sticky columns for scenario names

### 20.6.2: Refactor SimulationRunnerScreen to Use WorkspaceScenario

**Subtasks**:
- [x] Remove legacy props: `selectedPopulationId`, `selectedPortfolioName`, `selectedTemplateName`
- [x] Consume `activeScenario` from AppContext using `useAppState()` hook (not as prop)
- [x] Update `runScenario()` call to include full scenario context in request metadata
- [x] Store execution records with `scenarioId` and `populationId` keys for matrix lookup
- [x] Update progress tracking to publish matrix cell updates via AppContext:
  - On run start: updateCell(scenarioId, populationId, { status: RUNNING })
  - On complete: updateCell(scenarioId, populationId, { status: COMPLETED, runId, finishedAt })
  - On error: updateCell(scenarioId, populationId, { status: FAILED, error })
- [x] Add error handling that preserves scenario context for retry flows
- [x] Update tests to use `WorkspaceScenario` fixtures

**Dev Notes**:
- Current SimulationRunnerScreen has three internal sub-views (configure, progress, post-run) — preserve this UX
- Execution request should embed `scenarioId` in metadata for ResultStore lineage tracking
- See `frontend/src/components/screens/SimulationRunnerScreen.tsx` for current implementation

### 20.6.3: Refactor ResultsOverviewScreen to Preserve Scenario Lineage

**Subtasks**:
- [ ] Remove legacy props: `decileData`, `runResult`, `reformLabel`, `onNavigateBack`
- [ ] Add `activeScenario: WorkspaceScenario` and `runId: string` props
- [ ] Load result data via `useIndicators(runId)` with scenario context
- [ ] Display scenario metadata header matching ScenarioEntryDialog format:
  - Scenario name and portfolio name
  - Population name and version
  - Engine config (logit model, discount rate, year range)
  - Execution timestamp and seed
- [ ] Update export actions to embed lineage in downloaded artifacts:
  - CSV: Add lineage columns at start
  - Parquet: Add metadata to file schema
  - Replication: Create scenario.yaml alongside manifest
- [ ] Add "Clone Scenario" action that pre-populates Stage 2 from result's scenario
- [ ] Update tests to verify lineage preservation

**Dev Notes**:
- Metadata header should match ScenarioEntryDialog summary format for consistency
- Export filename convention: `reformlab-{scenario_name}-{timestamp}.csv`, `reformlab-{scenario_name}-{timestamp}.parquet`, `reformlab-{run_id}-manifest.json`, `reformlab-{scenario_name}-{timestamp}-replication.zip`
- See `frontend/src/components/screens/ResultsOverviewScreen.tsx` for current implementation

### 20.6.4: Refactor ComparisonDashboardScreen for Scenario Lineage

**Subtasks**:
- [ ] Remove legacy run selection state; integrate with matrix cell selection
- [ ] Update comparison request to include scenario IDs for all selected runs
- [ ] Display scenario context for each comparison participant (mini scenario cards):
  ```typescript
  interface ScenarioCardProps {
    scenario: ScenarioSummary;
    compact?: boolean;
  }
  // Shows: portfolio badge, scenario name, population, engine config year range
  ```
- [ ] Add scenario filtering to matrix (show only scenarios matching comparison criteria)
- [ ] Update comparison export to include scenario lineage in output
- [ ] Add cross-population comparison warning:
  - Display when selected runs have different population_id values
  - Warning text: "Comparing runs from different populations. Results may not be directly comparable."
  - Allow comparison to proceed (warning, not error)
- [ ] Update tests for scenario-aware comparison flows

**Dev Notes**:
- Comparison participants should show: scenario name, portfolio summary, population
- "Dimension mismatch" warning is precursor to AC-3 pluggable dimensions
- See `frontend/src/components/screens/ComparisonDashboardScreen.tsx` for current implementation

### 20.6.5: Implement Pluggable Comparison Dimensions Infrastructure

**Subtasks**:
- [ ] Define `ComparisonDimension<T = unknown>` protocol:
  ```typescript
  interface ComparisonDimension<T = unknown> {
    id: string;
    label: string;
    description: string;
    getValue(runResult: RunResponse): T | null;
    render?(value: T): React.ReactNode; // Optional custom renderer
  }
  ```
- [ ] Create dimension registry with API:
  - `register<T>(dimension: ComparisonDimension<T>): void`
  - `unregister(id: string): void`
  - `get(id: string): ComparisonDimension<unknown> | undefined`
  - Duplicate ID handling: throw error with message indicating conflict
- [ ] Implement default dimensions:
  - `scenario`: returns scenario_id and scenario_name
  - `portfolio`: returns SHA-256 hash of portfolio composition (sorted policies by name, hash: name + JSON.stringify(parameters) + resolutionStrategy)
  - `population`: returns population_id and population_version
  - `engine`: returns logit_model and discount_rate from engine_config
- [ ] Implement dimension-based filtering:
  - `DimensionFilter` interface: { dimensionId, operator: "equals" | "contains" | "in", values }
  - Filter bar component above matrix with active filters display
  - Filter logic: visibleCells = cells.filter(cell => filters.every(f => f.matches(cell)))
- [ ] Update comparison UI to render dimension values dynamically using dimension.render() or default toString()
- [ ] Document dimension extension pattern for EPIC-21 integration:
  - Story 21.2: originAccessMode, trustStatus dimensions
  - Story 21.3: calibrationTargets, validationBenchmarks dimensions
  - Story 21.6: exogenousTimeSeries, exogenousContext dimensions
- [ ] Add tests for default dimensions and custom dimension registration including duplicate ID rejection

**Dev Notes**:
- Registry pattern: `const dimensions = new Map<string, ComparisonDimension>()`
- Default dimensions provide baseline for AC-2 lineage display
- Dimension `getValue()` functions should extract from run metadata, not require panel data
- Use SHA-256 for portfolio hash (consistent with manifest hashing)

### 20.6.6: Add ResultStore Lineage Persistence

**Subtasks**:
- [ ] Extend `ResultMetadata` in `src/reformlab/server/result_store.py`:
  - Add `scenario_id: str | None` field
  - Add `population_id: str | None` field
  - Add `portfolio_snapshot: dict[str, Any] | None` field for full composition
- [ ] Update `RunRequest` in `src/reformlab/server/models.py`:
  - Change `scenario_id` from optional to required with transitional validation:
    - Phase 1: Accept optional scenario_id, infer from legacy payload if missing
    - Phase 2: Log deprecation warning for requests without scenario_id
    - Phase 3: Reject requests without scenario_id (after all callers migrated)
- [ ] Update `POST /api/runs` endpoint to accept and validate scenario context
- [ ] Update `ResultStore.save()` to persist lineage in `metadata.json`
- [ ] Update `ResultStore.load_from_disk()` to restore lineage with legacy handling
- [ ] Implement one-time migration for existing runs:
  - Scan all metadata.json files in result store directory
  - Identify legacy runs: scenario_id is null or empty string
  - Mark with scenario_id="legacy" and population_id="unknown"
  - Create migration.log with count_migrated, count_failed, errors[]
  - Rollback strategy: Delete migration.log, re-run migration
- [ ] Update ResultStore tests to verify lineage round-trip and legacy migration

**Dev Notes**:
- `ResultMetadata` is in `src/reformlab/server/result_store.py` (not models.py)
- API endpoint is `POST /api/runs` in `src/reformlab/server/routes/runs.py`
- Legacy runs display: scenario name = "Unknown Scenario (Legacy)" with amber Legacy badge
- See Story 20.5 for ResultStore persistence patterns

### 20.6.7: Implement Execution Matrix Coordinator

**Subtasks**:
- [ ] Create `useExecutionMatrix()` hook to manage matrix state
- [ ] Extend AppContext with ExecutionMatrixState:
  ```typescript
  interface ExecutionMatrixState {
    matrix: Record<string, Record<string, ExecutionMatrixCell>>;
    updateCell: (scenarioId: string, populationId: string, update: Partial<ExecutionMatrixCell>) => void;
    refreshMatrix: () => Promise<void>;
  }
  ```
- [ ] Implement matrix refresh triggers:
  - On component mount
  - After run completes (via AppContext updateCell callback)
  - On window focus (user returns to tab)
  - Periodic every 30s for multi-user scenarios
- [ ] Implement matrix filtering with localStorage persistence:
  - Filter key: "reformlab.matrix-filters"
  - Restore filters on mount
  - Clear on "Reset Filters" button
- [ ] Implement cell click handlers:
  - Completed cell: navigate to ResultsOverviewScreen with runId
  - Not executed cell: navigate to SimulationRunnerScreen
  - Failed cell: navigate to SimulationRunnerScreen with retry prompt
- [ ] Implement cell context menu with actions:
  - View Results (disabled if no runId)
  - Clone Scenario (always enabled)
  - Delete Run (disabled if status is RUNNING)
  - Export (disabled if no runId)
  - Retry Run (disabled if status is not FAILED)
- [ ] Implement matrix filtering by scenario, population, and status
- [ ] Add loading and error states for matrix operations
- [ ] Test matrix with various execution patterns (empty, partial, full)

**Dev Notes**:
- Matrix state structure: `Record<scenarioId, Record<populationId, ExecutionMatrixCell>>`
- Polling not needed for this story (running states deferred to async execution story)
- Cell click behavior as specified above
- Hook pattern: similar to `usePopulationPreview` from Story 20.4

### 20.6.8: End-to-End Integration and Testing

**Subtasks**:
- [ ] Test full flow: create scenario → execute → view results → compare → export
- [ ] Test matrix with multiple scenarios and populations
- [ ] Test lineage preservation through export/import round-trip
- [ ] Test comparison dimension registration and rendering
- [ ] Test legacy run display in matrix
- [ ] Test error recovery (failed runs, retry, cleanup)
- [ ] Add E2E test coverage for matrix navigation patterns
- [ ] Verify performance with 10+ scenarios and 5+ populations

---

## Dev Notes

### Architecture Constraints

- **WorkspaceScenario Model**: All Stage 4 components must consume `activeScenario` from AppContext, not receive scenario fragments as props
- **Scenario Lineage**: Every execution must be traceable to its source scenario via `scenarioId` in ResultStore metadata
- **Backward Compatibility**: Existing runs without `scenarioId` must display gracefully (as "legacy" runs)
- **State Management**: Use AppContext for shared state; avoid prop drilling scenario context
- **Comparison Extensibility**: Dimension registry must support EPIC-21 additions without core logic changes

### File Modifications

**Frontend**:
- `frontend/src/components/screens/SimulationRunnerScreen.tsx` — refactor to WorkspaceScenario
- `frontend/src/components/screens/ResultsOverviewScreen.tsx` — refactor to WorkspaceScenario, add lineage display
- `frontend/src/components/screens/ComparisonDashboardScreen.tsx` — refactor to scenario-aware comparison
- `frontend/src/hooks/useExecutionMatrix.ts` — NEW: matrix state management
- `frontend/src/components/comparison/DimensionRegistry.ts` — NEW: dimension registry
- `frontend/src/components/comparison/ExecutionMatrix.tsx` — NEW: matrix UI component
- `frontend/src/contexts/AppContext.tsx` — extend with execution matrix state
- `frontend/src/api/types.ts` — add `ExecutionMatrixCell`, `ExecutionStatus`, `ComparisonDimension` types

**Backend**:
- `src/reformlab/server/models.py` — extend `RunRequest` to require scenario_id with transitional validation
- `src/reformlab/server/routes/runs.py` — accept scenario context in run requests
- `src/reformlab/server/result_store.py` — persist and restore lineage metadata

### Test Patterns

**Frontend Tests** (`frontend/src/**/__tests__/` and `frontend/src/__tests__/workflows/`):
```typescript
describe("ExecutionMatrix", () => {
  it("displays scenario-by-population matrix", () => {
    // Given: workspace with 2 scenarios, 3 populations
    // When: render matrix
    // Then: 2x3 grid with correct status cells
  });

  it("navigates to results on completed cell click", () => {
    // Given: matrix with completed cell
    // When: click cell
    // Then: navigate to ResultsOverviewScreen with correct runId
  });
});

describe("ComparisonDashboard", () => {
  it("displays scenario lineage for comparison participants", () => {
    // Given: two runs from different scenarios
    // When: create comparison
    // Then: both show scenario metadata cards
  });
});
```

**Backend Tests** (`tests/server/`):
```python
def test_run_scenario_preserves_lineage(client, scenario_payload):
    """Scenario ID and population ID must be stored in run metadata."""
    response = client.post("/api/runs", json=scenario_payload)
    run_id = response.json()["run_id"]
    metadata = result_store.load_metadata(run_id)
    assert metadata.scenario_id == scenario_payload["scenario_id"]
    assert metadata.population_id == scenario_payload["population_id"]
```

### EPIC-21 Coordination

The pluggable comparison dimensions infrastructure (AC-3) is designed to enable EPIC-21 Story 21.6 (exogenous assumptions) and beyond:

- **Story 21.2** will add `originAccessMode` and `trustStatus` dimensions
- **Story 21.3** will add `calibrationTargets` and `validationBenchmarks` dimensions
- **Story 21.6** will add `exogenousTimeSeries` and `exogenousContext` dimensions

The dimension registry pattern ensures these can be registered without modifying core comparison logic.

---

## References

- **Epic Definition**: `_bmad-output/planning-artifacts/epics.md` (lines 1970-2133)
- **Story 20.5**: `_bmad-output/implementation-artifacts/20-5-build-engine-stage-with-scenario-save-clone-and-cross-stage-validation-gate.md`
- **Current Stage 4**: `frontend/src/components/screens/SimulationRunnerScreen.tsx`, `ResultsOverviewScreen.tsx`, `ComparisonDashboardScreen.tsx`
- **WorkspaceScenario Model**: `frontend/src/types/workspace.ts` (exported via types.ts for API consumers)
- **AppContext**: `frontend/src/contexts/AppContext.tsx`
- **ResultStore**: `src/reformlab/server/result_store.py`
- **UX Specification**: `_bmad-output/planning-artifacts/ux-design-specification.md`

---

## Dev Agent Record

**Created**: 2026-03-27
**Author**: Claude (Opus 4.6) via compiled-workflow
**Context Enhancement**: Ultimate context engine analysis performed
**Ready for Dev**: Yes — all tasks defined with acceptance criteria, dev notes, and type specifications
**Scope Note**: Story scope adjusted to 13 SP based on validator feedback (original estimate 8 SP). Consider splitting into 2-3 stories if velocity constraints require.
**Dependency Note**: Story 20.5 has open AI-review follow-ups that should be reviewed before starting this story.

**Implementation Progress (2026-03-27)**:
- Task 20.6.1 COMPLETED: ExecutionStatus enum, ExecutionMatrixCell type, ExecutionMatrix component with sticky columns, cell context menu, loading skeleton, empty states, responsive behavior
- Task 20.6.2 COMPLETED: SimulationRunnerScreen refactored to use WorkspaceScenario from AppContext, removed legacy props, added matrix cell updates via updateExecutionCell
- Task 20.6.5 COMPLETED: DimensionRegistry with register/unregister/get API, default dimensions (scenario, portfolio, population, engine), dimension-based filtering with matchesFilter function
- Task 20.6.7 PARTIAL: Added ExecutionMatrixState to AppContext (executionMatrix, updateExecutionCell), useExecutionMatrix hook still pending

**Remaining Tasks**:
- Task 20.6.3: Refactor ResultsOverviewScreen to Preserve Scenario Lineage
- Task 20.6.4: Refactor ComparisonDashboardScreen for Scenario Lineage
- Task 20.6.6: Add ResultStore Lineage Persistence (backend)
- Task 20.6.8: End-to-End Integration and Testing

---

## File List

**Frontend**:
- `frontend/src/api/types.ts` — added ExecutionStatus, ExecutionMatrixCell, ScenarioSummary, ComparisonDimension, DimensionFilter types
- `frontend/src/components/comparison/ExecutionMatrix.tsx` — NEW: execution matrix UI component
- `frontend/src/components/comparison/DimensionRegistry.tsx` — NEW: dimension registry for pluggable comparison dimensions
- `frontend/src/components/comparison/__tests__/ExecutionMatrix.test.tsx` — NEW: ExecutionMatrix tests
- `frontend/src/components/comparison/__tests__/DimensionRegistry.test.ts` — NEW: DimensionRegistry tests
- `frontend/src/components/screens/SimulationRunnerScreen.tsx` — REFACTORED: now uses WorkspaceScenario from AppContext
- `frontend/src/components/screens/__tests__/SimulationRunnerScreen.test.tsx` — UPDATED: tests now use WorkspaceScenario fixtures
- `frontend/src/__tests__/workflows/simulation-workflow.test.tsx` — UPDATED: added AppProvider mock
- `frontend/src/contexts/AppContext.tsx` — EXTENDED: added executionMatrix state and updateExecutionCell method

---

## Change Log

- 2026-03-27: Started implementation — Task 20.6.1 (ExecutionMatrix UI) and Task 20.6.2 (SimulationRunnerScreen refactor) completed
- 2026-03-27: Implemented pluggable comparison dimensions infrastructure (Task 20.6.5)
- 2026-03-27: Added ExecutionMatrixState to AppContext (partial Task 20.6.7)
