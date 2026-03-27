# Story 20.6: Refactor Run / Results / Compare Around Scenario-by-Population Execution

**Status**: `ready-for-dev`
**Epic**: EPIC-20 (Phase 3 Canonical Scenario Model)
**Story Type**: Refactoring
**Points**: 8
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
- Cells: Execution status (not executed, running, completed, failed) with quick access to results

**And** selecting a completed cell loads the corresponding results with full scenario context preserved.

### AC-2: Scenario Lineage Preserved Through Comparison/Export Views

**Given** a user has executed scenarios against one or more populations
**When** they view results or create comparisons
**Then** all result metadata includes:
- Scenario ID and name
- Portfolio composition (policy templates + parameters)
- Population selection and version
- Engine configuration (logit model, discount rate)
- Execution timestamp and seed

**And** export actions (panel data, manifest, replication package) embed this lineage in the output artifacts.

### AC-3: Comparison Infrastructure Supports Pluggable Comparison Dimensions

**Given** the comparison system architecture
**When** EPIC-21 adds new evidence asset types (exogenous time series, calibration targets)
**Then** the comparison model can be extended with new dimensions without modifying core comparison logic:
- `comparisonDimension` registry pattern for extensible dimensions
- Type-safe dimension configuration
- Default and custom dimension providers

**And** the comparison UI supports dynamic dimension rendering based on available dimensions.

---

## Tasks

### 20.6.1: Design Scenario-by-Population Execution Matrix UI

**Subtasks**:
- [ ] Define matrix data structure: `ExecutionMatrixCell { scenarioId, populationId, status, runId? }`
- [ ] Design cell state representation (not executed, running, completed, failed)
- [ ] Define cell interaction patterns (click to view, right-click for actions)
- [ ] Design matrix layout for responsive behavior (scrollable populations, sticky scenarios)
- [ ] Add loading skeleton for matrix initialization
- [ ] Design empty states (no scenarios, no populations, no executions)

**Dev Notes**:
- Matrix should populate from `ResultStore.list_results()` cross-referenced with workspace scenarios
- Status polling needed for "running" cells (via SimulationRunner progress updates)
- Consider Shadcn/ui `Table` component with sticky columns for scenario names

### 20.6.2: Refactor SimulationRunnerScreen to Use WorkspaceScenario

**Subtasks**:
- [ ] Remove legacy props: `selectedPopulationId`, `selectedPortfolioName`, `selectedTemplateName`
- [ ] Add `activeScenario: WorkspaceScenario` prop from AppContext
- [ ] Update `runScenario()` call to include full scenario context in request metadata
- [ ] Store execution records with `scenarioId` and `populationId` keys for matrix lookup
- [ ] Update progress tracking to publish matrix cell updates via AppContext
- [ ] Add error handling that preserves scenario context for retry flows
- [ ] Update tests to use `WorkspaceScenario` fixtures

**Dev Notes**:
- Current SimulationRunnerScreen has three internal sub-views (configure, progress, post-run) — preserve this UX
- Execution request should embed `scenarioId` in metadata for ResultStore lineage tracking
- See `frontend/src/components/screens/SimulationRunnerScreen.tsx` for current implementation

### 20.6.3: Refactor ResultsOverviewScreen to Preserve Scenario Lineage

**Subtasks**:
- [ ] Remove legacy props: `decileData`, `runResult`, `reformLabel`, `onNavigateBack`
- [ ] Add `activeScenario: WorkspaceScenario` and `runId: string` props
- [ ] Load result data via `useIndicators(runId)` with scenario context
- [ ] Display scenario metadata header (portfolio, population, engine config, timestamp)
- [ ] Update export actions to embed lineage in downloaded artifacts
- [ ] Add "Clone Scenario" action that pre-populates Stage 2 from result's scenario
- [ ] Update tests to verify lineage preservation

**Dev Notes**:
- Metadata header should match ScenarioEntryDialog summary format for consistency
- Export actions: panel data (add scenario column), manifest (already has lineage), replication package (scenario config as YAML)
- See `frontend/src/components/screens/ResultsOverviewScreen.tsx` for current implementation

### 20.6.4: Refactor ComparisonDashboardScreen for Scenario Lineage

**Subtasks**:
- [ ] Remove legacy run selection state; integrate with matrix cell selection
- [ ] Update comparison request to include scenario IDs for all selected runs
- [ ] Display scenario context for each comparison participant (mini scenario cards)
- [ ] Add scenario filtering to matrix (show only scenarios matching comparison criteria)
- [ ] Update comparison export to include scenario lineage in output
- [ ] Add warning when comparing runs from different populations (dimension mismatch)
- [ ] Update tests for scenario-aware comparison flows

**Dev Notes**:
- Comparison participants should show: scenario name, portfolio summary, population
- "Dimension mismatch" warning is precursor to AC-3 pluggable dimensions
- See `frontend/src/components/screens/ComparisonDashboardScreen.tsx` for current implementation

### 20.6.5: Implement Pluggable Comparison Dimensions Infrastructure

**Subtasks**:
- [ ] Define `ComparisonDimension` protocol: `id, label, description, getValue(runResult)`
- [ ] Create `comparisonDimensions` registry with default dimensions:
  - `scenario`: scenario ID and name
  - `portfolio`: portfolio composition hash
  - `population`: population ID and version
  - `engine`: logit model and discount rate
- [ ] Add `registerDimension(dimension)` API for extensibility
- [ ] Update comparison UI to render dimension values dynamically
- [ ] Add dimension-based filtering to matrix and comparison views
- [ ] Document dimension extension pattern for EPIC-21 integration
- [ ] Add tests for default dimensions and custom dimension registration

**Dev Notes**:
- Registry pattern: `const dimensions = new Map<string, ComparisonDimension>()`
- Default dimensions provide baseline for AC-2 lineage display
- EPIC-21 will add: `exogenousAssumptions`, `calibrationTargets`, `validationBenchmarks`
- Dimension `getValue()` functions should extract from run metadata, not require panel data

### 20.6.6: Add ResultStore Lineage Persistence

**Subtasks**:
- [ ] Extend `RunMetadata` to include `scenarioId` and `populationId` fields
- [ ] Update `runScenario()` API to accept scenario context
- [ ] Update `ResultStore.save()` to persist lineage in `metadata.json`
- [ ] Update `ResultStore.load_from_disk()` to restore lineage
- [ ] Add validation: reject runs without valid scenario context
- [ ] Add migration for existing runs without lineage (mark as "legacy")
- [ ] Update ResultStore tests to verify lineage round-trip

**Dev Notes**:
- `RunMetadata` is in `src/reformlab/server/models.py`
- API endpoint is `POST /api/runs` in `src/reformlab/server/routes/runs.py`
- Legacy runs can be displayed in matrix with "unknown scenario" designation
- See Story 20.5 for ResultStore persistence patterns

### 20.6.7: Implement Execution Matrix Coordinator

**Subtasks**:
- [ ] Create `useExecutionMatrix()` hook to manage matrix state
- [ ] Implement matrix refresh from ResultStore on mount and after runs
- [ ] Add real-time status updates for running cells (via WebSocket or polling)
- [ ] Implement cell click handlers to navigate to results or runner
- [ ] Add cell context menu (view, clone, delete, export)
- [ ] Implement matrix filtering (by scenario, by population, by status)
- [ ] Add loading and error states for matrix operations
- [ ] Test matrix with various execution patterns (empty, partial, full)

**Dev Notes**:
- Matrix state should be: `Record<scenarioId, Record<populationId, ExecutionMatrixCell>>`
- Polling interval: 2 seconds for running cells; stop when all cells terminal
- Cell click: completed → ResultsOverviewScreen; not executed → SimulationRunnerScreen
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
- `frontend/src/components/comparison/ComparisonDimensionRegistry.ts` — NEW: dimension registry
- `frontend/src/components/comparison/ExecutionMatrix.tsx` — NEW: matrix UI component
- `frontend/src/contexts/AppContext.tsx` — extend with execution matrix state
- `frontend/src/api/types.ts` — add `ExecutionMatrixCell`, `ComparisonDimension` types

**Backend**:
- `src/reformlab/server/models.py` — extend `RunMetadata` with `scenarioId`, `populationId`
- `src/reformlab/server/routes/runs.py` — accept scenario context in run requests
- `src/reformlab/core/result_store.py` — persist and restore lineage metadata

### Test Patterns

**Frontend Tests** (`tests/integration/frontend/`):
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
def test_run_scenario_perserves_lineage(client, scenario_payload):
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
- **WorkspaceScenario Model**: `frontend/src/api/types.ts`
- **AppContext**: `frontend/src/contexts/AppContext.tsx`
- **ResultStore**: `src/reformlab/core/result_store.py`
- **UX Specification**: `_bmad-output/planning-artifacts/ux-design-specification.md`

---

## Dev Agent Record

**Created**: 2026-03-27
**Author**: Claude (Opus 4.6) via compiled-workflow
**Context Enhancement**: Ultimate context engine analysis performed
**Ready for Dev**: Yes — all tasks defined with acceptance criteria and dev notes
