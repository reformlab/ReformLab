# Story 20.8: Add End-to-End Regression Coverage and Sync Product Docs to the New IA

Status: ready-for-dev
**Epic**: EPIC-20 (Phase 3 Canonical Scenario Model)
**Story Type**: Testing + Documentation
**Points**: 3
**Dependencies**: Stories 20.1–20.7 (all stage-based workspace implementations)

---

## Story

As a policy analyst using the ReformLab workspace,
I want comprehensive end-to-end tests that verify the critical user flows work end-to-end (first launch → demo run, portfolio editing → validation → run, population inspection → run, comparison with scenario lineage),
and I want all product documentation to describe the current four-stage workspace model (not the older screen-by-screen model),
so that I can trust the product works as advertised and new users see accurate documentation.

---

## Acceptance Criteria

### AC-1: End-to-End Regression Tests Cover Critical User Flows

**Given** the test suite runs,
**When** the end-to-end regression tests execute,
**Then** all critical user flows are tested and passing:
1. First launch → demo scenario loads → navigate to runner → run completes
2. Edit portfolio → navigate to engine → validation passes → run completes
3. Select population → inspect in explorer → navigate to engine → run completes
4. Upload population → validate schema → add to library → run completes
5. Compare completed runs → scenario lineage preserved in comparison view

Each flow test should:
- Start from a clean localStorage state
- Use real API calls (not mocks) where endpoints exist
- Verify hash navigation completes successfully
- Assert final state matches expected outcome
- Run in under 60 seconds per flow (keep e2e tests fast)

### AC-2: Product Documentation Synchronized to Four-Stage Workspace Model

**Given** a user reads the product documentation,
**When** they view workspace and screen descriptions,
**Then** all references describe the current four-stage model (Policies & Portfolio, Population, Engine, Run / Results / Compare) and do NOT reference the older screen-by-screen model:
- `README.md` describes the four-stage workspace
- `docs/` content (if any) matches current UX
- Any "screens" terminology maps to the correct stage
- First-launch onboarding is documented with demo scenario behavior

### AC-3: Tests Extensible for EPIC-21 Evidence Flows

**Given** EPIC-21 Story 21.8 will extend regression coverage,
**When** evidence-specific flows are added (synthetic ingestion, trust labels, calibration/validation separation),
**Then** the test fixtures and assertions are structured so 21.8 can add evidence scenarios without duplicating the workspace flow coverage built here:
- Test fixtures export reusable helpers (setupDemoScenario, navigateToStage, waitForRunCompletion)
- Flow tests accept optional configuration parameters
- Assertion helpers can be extended for evidence metadata validation

---

## Tasks / Subtasks

### 20.8.1: Create E2E Test Infrastructure and Shared Fixtures (AC: #1, #3)

**Subtasks**:
- [ ] Create `frontend/src/__tests__/e2e/` directory for end-to-end workflow tests
- [ ] Create `frontend/src/__tests__/e2e/helpers.ts` with reusable test helpers:
  - `cleanLocalStorage()` — clears all ReformLab keys
  - `waitForNavigation(stage: StageKey, subView?: string)` — waits for hash to match
  - `waitForElement(selector: string)` — waits for DOM element to appear
  - `setupDemoScenario()` — configures demo scenario from scratch (or skips if already loaded)
  - `waitForRunCompletion(runId: string)` — polls for completed status
  - `assertScenarioLineage(runId: string, expectedFields: object)` — verifies ResultDetailResponse includes expected scenario metadata
- [ ] Create `frontend/src/__tests__/e2e/fixtures.ts` with test data fixtures:
  - `demoScenarioConfig` — matches `DEMO_SCENARIO` from demo-scenario.ts
  - `testPortfolioConfig` — minimal 2-policy portfolio for editing flow
  - `testPopulationId` — reference to built-in test population
  - `testUploadFile` — minimal CSV fixture for upload flow (household_id, income, region)
- [ ] Export fixtures and helpers so Story 21.8 can reuse them without duplication
- [ ] Add `vi.unmock("@/api/indicators")` and `vi.unmock("@/api/populations")` in e2e tests to use real API calls

**Dev Notes**:
- E2E tests use Vitest + `@testing-library/react` (same as other tests)
- Tests are still "frontend e2e" — they use `TestClient` or real server during CI
- No Playwright/Cypress needed: app is localhost-only, user flows are fully testable via React Testing Library
- Helpers must be synchronous where possible; async helpers use `await` with timeouts
- Fixtures should be minimal to keep tests fast

### 20.8.2: Test First Launch → Demo Scenario → Run Flow (AC: #1)

**Subtasks**:
- [ ] Create `frontend/src/__tests__/e2e/first-launch-flow.test.tsx`
- [ ] Test: "first launch loads demo scenario and navigates to runner"
  - Start with `cleanLocalStorage()`
  - Render `<App />` (bypass auth or use test auth)
  - Assert demo scenario is set as `activeScenario`
  - Assert hash is `#results/runner`
  - Assert "Run Simulation" button is present and enabled
- [ ] Test: "demo scenario run completes successfully"
  - Click "Run Simulation" button
  - Wait for run completion (check for success toast or results panel)
  - Assert results are displayed (charts render, run ID is set)
  - Assert `lastRunId` is non-null in AppContext
- [ ] Test: "returning user restores scenario from localStorage"
  - Set up a scenario in localStorage
  - Render `<App />`
  - Assert restored scenario matches saved state
  - Assert last active stage is restored

**Dev Notes**:
- Use `createDemoScenario()` from demo-scenario.ts for expected values
- Test file should document the first-launch decision tree from Story 20.2
- Tests must clear localStorage in `beforeEach` to avoid state leakage

### 20.8.3: Test Portfolio Editing → Validation → Run Flow (AC: #1)

**Subtasks**:
- [ ] Create `frontend/src/__tests__/e2e/portfolio-workflow.test.tsx`
- [ ] Test: "edit portfolio and navigate to engine"
  - Start with demo scenario loaded
  - Navigate to Stage 1 (Policies)
  - Edit portfolio (add policy or modify parameter)
  - Save scenario
  - Navigate to Stage 3 (Engine)
  - Assert validation passes (portfolio-selected check)
- [ ] Test: "run completes with updated portfolio"
  - Click "Run Simulation" from Engine stage
  - Wait for completion
  - Assert results reflect the edited portfolio
  - Assert run metadata includes portfolio_name
- [ ] Test: "validation blocks run with empty portfolio"
  - Create new scenario (no portfolio)
  - Navigate to Engine
  - Assert validation fails with "portfolio-selected" error
  - Assert "Run Simulation" is disabled
  - Assert tooltip shows error message

**Dev Notes**:
- Portfolio editing can be done via UI interaction or direct `updateScenarioField` call
- For faster tests, prefer direct state manipulation where UI is not the focus
- Validation gate checks are tested in component unit tests; e2e focuses on flow integration

### 20.8.4: Test Population Selection → Inspection → Run Flow (AC: #1)

**Subtasks**:
- [ ] Create `frontend/src/__tests__/e2e/population-workflow.test.tsx`
- [ ] Test: "select population and navigate to explorer"
  - Start with demo scenario loaded
  - Navigate to Stage 2 (Population)
  - Click "Select" on a population card
  - Assert `activeScenario.populationIds` includes selected ID
  - Assert nav rail shows completion checkmark
  - Click "Explore" to open explorer
  - Assert explorer tabs render (Table, Profile, Summary)
- [ ] Test: "run completes with selected population"
  - From explorer, navigate to Stage 3 (Engine)
  - Assert population dropdown shows selected population
  - Click "Run Simulation"
  - Wait for completion
  - Assert run metadata includes population_id
- [ ] Test: "upload and inspect new population"
  - Navigate to Population stage
  - Click "Upload" button
  - Simulate file drop with test CSV fixture
  - Assert validation report shows matched/unrecognized columns
  - Confirm upload
  - Assert uploaded population appears in library with `[Uploaded]` tag
  - Run simulation with uploaded population

**Dev Notes**:
- Test CSV fixture: `household_id,income,region\n1,50000,North\n2,60000,South\n`
- Population preview/profile API calls are mocked in Story 20.4; this story uses real endpoints from Story 20.7
- Upload flow uses real `POST /api/populations/upload` endpoint (Story 20.7)

### 20.8.5: Test Comparison Flow with Scenario Lineage (AC: #1)

**Subtasks**:
- [ ] Create `frontend/src/__tests__/e2e/comparison-workflow.test.tsx`
- [ ] Test: "compare two runs with scenario lineage preserved"
  - Run baseline scenario (demo)
  - Clone scenario and modify a parameter
  - Run reform scenario
  - Navigate to Stage 4 (Results)
  - Select both runs for comparison
  - Assert comparison view shows side-by-side results
  - Assert each run shows scenario name, portfolio, population in header
- [ ] Test: "export includes scenario lineage"
  - From comparison view, export results
  - Assert exported CSV includes lineage columns (scenario_id, scenario_name, portfolio_name, population_id)
  - Or for Parquet export, verify metadata schema includes lineage fields
- [ ] Test: "cross-population comparison warning"
  - Run same scenario against two different populations
  - Compare the two runs
  - Assert warning appears: "Comparing runs from different populations"
  - Assert comparison proceeds despite warning

**Dev Notes**:
- Lineage fields tested: `scenario_id`, `scenario_name`, `portfolio_name`, `population_id`, `engineConfig.startYear`, `engineConfig.endYear`
- Comparison export uses `/api/comparison` endpoint; check response includes run metadata
- Warning message matches Story 20.6 specification

### 20.8.6: Update README.md to Describe Four-Stage Workspace (AC: #2)

**Subtasks**:
- [ ] Read `README.md` and identify sections that reference older screen model
- [ ] Update "Quick Start" section to describe first-launch demo scenario flow
- [ ] Update "Features" section to list four stages by name:
  - Stage 1: Policies & Portfolio
  - Stage 2: Population (Library, Data Explorer, Upload)
  - Stage 3: Engine (Configuration, Validation)
  - Stage 4: Run / Results / Compare (Matrix, Results, Comparison)
- [ ] Update any "screens" language to "stages" with correct stage names
- [ ] Ensure CLI examples and notebook workflows remain accurate
- [ ] Update screenshots/diagrams if any show old UI (or add placeholder note for future update)

**Dev Notes**:
- README is the primary onboarding document for new users
- Keep technical accuracy: CLI, Python API, and notebook sections don't need major changes
- Focus on GUI description sections to align with current UX

### 20.8.7: Review and Update Other Documentation (AC: #2)

**Subtasks**:
- [ ] Scan `docs/` directory for any workspace/screen descriptions
- [ ] Update content to use four-stage terminology
- [ ] Check CONTRIBUTING.md for outdated development workflow descriptions
- [ ] Check docs generated from planning artifacts (PRD, UX, Architecture) — these are authoritative, no changes needed
- [ ] Create or update `docs/workspace-guide.md` if stage-specific documentation is needed
- [ ] Ensure all doc links are valid (no broken internal references)

**Dev Notes**:
- Planning artifacts (`_bmad-output/planning-artifacts/`) are source of truth — don't modify them
- Focus on user-facing docs: README, CONTRIBUTING, and any guides in `docs/`
- If a doc describes a feature not yet implemented, add a TODO comment for the relevant story

### 20.8.8: Run Quality Gates and Verify All Tests Pass (AC: #1)

**Subtasks**:
- [ ] Run `npm test` — verify all e2e tests pass
- [ ] Run `npm run typecheck` — verify 0 errors
- [ ] Run `npm run lint` — verify 0 new errors
- [ ] Run `uv run pytest tests/` — verify backend tests still pass
- [ ] Run `uv run ruff check src/ tests/` — verify 0 errors
- [ ] Run `uv run mypy src/` — verify type check passes
- [ ] Document test runtimes: each e2e flow should complete in < 60s
- [ ] Update STORY file with actual test count and runtime metrics

**Dev Notes**:
- E2E tests should not significantly increase CI runtime
- If a test is slow, consider splitting or using more targeted assertions
- Quality gate commands are defined in MEMORY.md

---

## Dev Notes

### Architecture Patterns and Constraints

- **Test Framework**: Vitest + React Testing Library + @testing-library/user-event
- **Test Location**: `frontend/src/__tests__/e2e/` for workflow tests; component tests remain in `__tests__/` directories alongside components
- **E2E Definition**: "Frontend e2e" tests use real API endpoints where available but run in a test environment (not a browser automation tool like Playwright)
- **Test Helpers**: Reusable helpers in `frontend/src/__tests__/e2e/helpers/` to avoid duplication across flows
- **Test Fixtures**: Minimal fixtures in `frontend/src/__tests__/e2e/fixtures.ts` for consistent test data
- **Auth Handling**: E2E tests use test auth bypass or valid test credentials; see `App.test.tsx` for auth mock pattern
- **Hash Routing**: Tests use `window.location.hash` for navigation; helpers wait for hashchange events
- **localStorage Isolation**: Each test cleans localStorage in `beforeEach` to avoid state leakage

### Documentation Patterns

- **README.md**: Primary user-facing document; must describe current workspace model accurately
- **Four-Stage Model**: Always use stage names: Policies & Portfolio, Population, Engine, Run / Results / Compare
- **Screen vs Stage**: Older docs may say "screen"; update to "stage" or refer to specific component names
- **Planning Artifacts**: `_bmad-output/planning-artifacts/` are authoritative; don't modify PRD/UX/Architecture docs
- **Code Comments**: Update outdated comments that reference old screen names or workflows

### Testing Standards Summary

- **E2E Test Structure**: Arrange-Act-Assert pattern; each test is independent
- **Test Speed**: Keep e2e tests fast — prefer direct state manipulation over slow UI interactions where possible
- **API Calls**: Use real API endpoints (unmock `@/api/*`) to test integration
- **Assertions**: Assert key state changes and UI outcomes; avoid over-asserting implementation details
- **Error Messages**: Clear failure messages that indicate which flow and step failed
- **Fixtures**: Minimal and reusable; export for EPIC-21 extension

### EPIC-21 Coordination

- **Test Extensibility**: Fixtures and helpers are designed for reuse in Story 21.8 (evidence-specific flows)
- **Evidence Tests**: Story 21.8 will add flows for: synthetic ingestion, trust labels, calibration/validation separation
- **No Duplication**: Structure test files so 21.8 extends helpers rather than copying flow logic
- **Evidence Metadata**: Assertion helpers include optional parameter for evidence field validation

### Source Tree Components

| File | Modification |
|------|--------------|
| `frontend/src/__tests__/e2e/` | NEW: end-to-end workflow test directory |
| `frontend/src/__tests__/e2e/helpers.ts` | NEW: reusable test helpers (navigation, waiting, assertions) |
| `frontend/src/__tests__/e2e/fixtures.ts` | NEW: test data fixtures |
| `frontend/src/__tests__/e2e/first-launch-flow.test.tsx` | NEW: first launch and demo scenario tests |
| `frontend/src/__tests__/e2e/portfolio-workflow.test.tsx` | NEW: portfolio editing and validation tests |
| `frontend/src/__tests__/e2e/population-workflow.test.tsx` | NEW: population selection and upload tests |
| `frontend/src/__tests__/e2e/comparison-workflow.test.tsx` | NEW: comparison and lineage tests |
| `README.md` | Update: describe four-stage workspace model |
| `CONTRIBUTING.md` | Review and update if outdated |
| `docs/workspace-guide.md` | OPTIONAL: create if stage-specific guide needed |

### Project Structure Notes

- E2E tests live in `frontend/src/__tests__/e2e/` to be co-located with the frontend codebase
- Helpers are exported for reuse in EPIC-21 Story 21.8
- Documentation updates focus on user-facing docs, not planning artifacts
- Test runtimes should be documented for CI pipeline planning

### Detected Conflicts or Variances

- **No conflicts expected**: This story is pure testing and documentation; no implementation changes
- **Backend API Dependencies**: E2E tests use endpoints from Stories 20.1–20.7; ensure those stories are complete first
- **Test Data Race**: If tests run in parallel, ensure test fixtures use unique IDs (e.g., timestamp-based)
- **Documentation Drift**: README may have been updated during previous stories; review and sync with current state

---

## References

- **Epic 20**: `_bmad-output/planning-artifacts/epics.md` (lines 2135-2150) — Story 20.8 specification
- **Story 20.2**: `_bmad-output/implementation-artifacts/20-2-add-pre-seeded-demo-scenario-onboarding-and-scenario-entry-flows.md` — First launch flow, demo scenario design, localStorage patterns
- **Story 20.3**: `_bmad-output/implementation-artifacts/20-3-build-policies-and-portfolio-stage-with-inline-composition.md` — Portfolio editing, save/clone flows
- **Story 20.4**: `_bmad-output/implementation-artifacts/20-4-build-population-library-and-data-explorer-stage.md` — Population selection, explorer, upload flows
- **Story 20.5**: `_bmad-output/implementation-artifacts/20-5-build-engine-stage-with-scenario-save-clone-and-cross-stage-validation-gate.md` — Validation gate, engine configuration
- **Story 20.6**: `_bmad-output/implementation-artifacts/20-6-refactor-run-results-compare-around-scenario-by-population-execution.md` — Scenario lineage, comparison infrastructure
- **Story 20.7**: `_bmad-output/implementation-artifacts/20-7-extend-backend-apis-for-population-explorer-and-execution-contract-validation.md` — Population API endpoints, validation contract
- **UX Spec**: `_bmad-output/planning-artifacts/ux-design-specification.md` — Critical success moments, user journey flows
- **Memory**: `MEMORY.md` — Quality check commands, testing patterns

---

## Dev Agent Record

**Created**: 2026-03-27
**Author**: Claude (Opus 4.6) via create-story workflow
**Context Enhancement**: Ultimate context engine analysis performed
**Ready for Dev**: Yes — all tasks defined with acceptance criteria, dev notes, and test specifications

**Dependencies Status**:
- Story 20.1 (canonical scenario model): **DONE**
- Story 20.2 (demo scenario onboarding): **DONE**
- Story 20.3 (Policies & Portfolio stage): **DONE**
- Story 20.4 (Population Library and Explorer): **DONE**
- Story 20.5 (Engine stage with validation): **DONE**
- Story 20.6 (Run / Results / Compare refactor): **DONE**
- Story 20.7 (Population APIs and validation): **DONE**

**Implementation Notes**:
- This is a testing and documentation story — no new implementation code
- E2E tests verify all previous Epic 20 stories work together as intended
- Documentation sync ensures users see accurate descriptions of the current workspace
- Tests are structured for extensibility: EPIC-21 Story 21.8 will add evidence-specific flows

**EPIC-21 Coordination**:
- Test fixtures and helpers are designed for reuse in Story 21.8
- Evidence flows (synthetic ingestion, trust labels, calibration/validation separation) will extend these tests
- Assertion helpers include optional parameters for evidence metadata validation

---

## File List

**Frontend Tests**:
- `frontend/src/__tests__/e2e/helpers.ts` — NEW: test helper functions
- `frontend/src/__tests__/e2e/fixtures.ts` — NEW: test data fixtures
- `frontend/src/__tests__/e2e/first-launch-flow.test.tsx` — NEW: first launch tests
- `frontend/src/__tests__/e2e/portfolio-workflow.test.tsx` — NEW: portfolio editing tests
- `frontend/src/__tests__/e2e/population-workflow.test.tsx` — NEW: population selection tests
- `frontend/src/__tests__/e2e/comparison-workflow.test.tsx` — NEW: comparison tests

**Documentation**:
- `README.md` — Update: describe four-stage workspace
- `CONTRIBUTING.md` — Review and update if needed
- `docs/workspace-guide.md` — OPTIONAL: create stage-specific guide

---

## Change Log

- 2026-03-27: Story created with comprehensive task breakdown for e2e testing and documentation sync

---

## Senior Developer Review (AI)

### Review: 2026-03-27
- **Reviewer:** TBS
- **Evidence Score:** TBS
- **Issues Found:** TBS
- **Issues Fixed:** TBS

<!-- REVIEW SYNTHESIS PLACEHOLDER -->
