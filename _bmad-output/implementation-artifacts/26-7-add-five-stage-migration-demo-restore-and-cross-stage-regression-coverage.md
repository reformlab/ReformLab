# Story 26.7: Add Five-Stage Migration, Demo, Restore, and Cross-Stage Regression Coverage

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a QA engineer and product owner,
I want comprehensive regression coverage for the five-stage workspace migration, first-launch demo flow, returning-user restore, skip routing, and cross-stage validation,
so that we can confidently ship the workspace redesign without regressions.

## Acceptance Criteria

1. Given first launch uses the demo scenario, when the workspace opens, then valid Stage 1-4 selections are present and the analyst can run immediately.
2. Given a returning user has saved old four-stage state, when the app initializes, then state migrates to the five-stage model without losing scenario context.
3. Given investment decisions are disabled, when the analyst follows the natural flow, then Stage 3 can be skipped and Scenario validation can still pass.
4. Given policies require columns missing from the selected population, when Stage 1 and Stage 2 render, then both show non-blocking warnings.
5. Given Stage 5 sub-views are used, then run queue, results, comparison, and manifest viewer all keep Run / Results / Compare active in the nav rail.
6. Given the regression suite runs, then it covers five-stage nav, skip routing, scenario validation, Quick Test Population, scenario naming, manifest access, demo flow, and restore flow.

## Tasks / Subtasks

- [ ] Add five-stage happy-path regression test (AC: #1, #6)
  - [ ] Create `five-stage-happy-path.test.tsx` in `frontend/src/__tests__/workflows/`
  - [ ] Test first-launch demo scenario loads with valid selections for all stages
  - [ ] Verify nav rail shows all five stages in correct order
  - [ ] Verify WorkflowNavRail completion indicators work for all stages
  - [ ] Verify hash routing works for all five stages (#policies, #population, #investment-decisions, #scenario, #results)
  - [ ] Verify navigateTo() function works for all stages
  - [ ] Verify demo scenario has name "Demo — Carbon Tax + Dividend" (em dash from Story 26.6)
  - [ ] Verify demo scenario uses `DEMO_TEMPLATE_ID` and `DEMO_POPULATION_ID`

- [ ] Add returning-user restore migration test (AC: #2, #6)
  - [ ] Test migration from "engine" stage to "scenario" stage (Story 26.1)
  - [ ] Test hash migration from #engine to #scenario
  - [ ] Test localStorage migration from `STORAGE_KEY="engine"` to `"scenario"`
  - [ ] Test returning user with full four-stage state migrates without data loss
  - [ ] Test returning user restores selected policy set, primary population, and scenario settings
  - [ ] Test returning user restores Investment Decisions enabled/disabled state
  - [ ] Test returning user restores Stage 5 sub-view (comparison, manifest, etc.)
  - [ ] Test hash+localStorage conflict scenario (hash empty, localStorage has "engine")

- [ ] Add skip routing regression test for Investment Decisions (AC: #3, #6)
  - [ ] Test Stage 3 nav rail shows "Disabled" when decisions disabled
  - [ ] Test Stage 3 shows enable toggle and Continue to Scenario action when disabled
  - [ ] Test clicking Continue to Scenario bypasses wizard and goes to Scenario stage
  - [ ] Test Scenario validation passes when decisions disabled (no decision blocker)
  - [ ] Test nav rail completion shows Stage 3 as complete when disabled
  - [ ] Test navigating directly to Scenario works even if Stage 3 is disabled

- [ ] Add cross-stage validation warning test (AC: #4, #6)
  - [ ] Test Stage 1 shows non-blocking warning when policy requires missing columns
  - [ ] Test Stage 2 shows non-blocking warning when selected population lacks required columns
  - [ ] Verify warnings are identical across both stages (same message, same non-blocking behavior)
  - [ ] Verify warnings don't block navigation or execution
  - [ ] Verify Scenario stage shows hard blockers for missing policy set or population (blocking validation)

- [ ] Add Stage 5 sub-views regression test (AC: #5, #6)
  - [ ] Test run queue sub-view (#results) keeps Run / Results / Compare active in nav rail
  - [ ] Test results sub-view keeps Run / Results / Compare active in nav rail
  - [ ] Test comparison sub-view (#results/comparison) keeps Run / Results / Compare active
  - [ ] Test decisions sub-view (#results/decisions) keeps Run / Results / Compare active
  - [ ] Test runner sub-view (#results/runner) keeps Run / Results / Compare active
  - [ ] Test manifest sub-view (#results/manifest) keeps Run / Results / Compare active (Story 26.4)
  - [ ] Verify invalid sub-view falls back to run queue without crashing

- [ ] Add Quick Test Population regression test (AC: #6)
  - [ ] Test Quick Test Population appears near top of Population Library
  - [ ] Test Quick Test Population is labeled as fast demo/smoke test and not for analysis
  - [ ] Test Quick Test Population can be selected as primary population
  - [ ] Test Quick Test Population is visually differentiated from analysis-grade populations

- [ ] Add scenario naming regression test (AC: #6)
  - [ ] Test new scenario uses em dash format: "Policy Set — Population" (Story 26.6)
  - [ ] Test policy set only → "Policy Set" (no suffix)
  - [ ] Test population only → "Untitled — Population"
  - [ ] Test manual edit freeze prevents auto-updates
  - [ ] Test clone naming preserves em dash and appends " (copy)"

- [ ] Update existing tests for five-stage model (AC: #6)
  - [ ] Update `analyst-journey.test.tsx` to include Investment Decisions stage
  - [ ] Update nav rail tests to expect five stages instead of four
  - [ ] Update stage completion tests for five-stage logic
  - [ ] Update localStorage migration tests to cover "engine" → "scenario" migration
  - [ ] Verify all existing tests still pass after five-stage migration

- [ ] Run full regression suite and verify all tests pass (AC: #6)
  - [ ] Run `npm test` in frontend directory
  - [ ] Verify all 926+ tests pass (current count from Story 26.6)
  - [ ] Verify no new test failures introduced
  - [ ] Document any pre-existing test failures (if any)

## Dev Notes

### Current State Analysis

**Five-Stage Migration Status (Stories 26.1-26.6):**
- Story 26.1: Nav rail migrated to five stages (Policies, Population, Investment Decisions, Scenario, Run/Results/Compare)
- Story 26.2: Investment Decisions extracted to dedicated Stage 3 with skip-when-disabled routing
- Story 26.3: Engine renamed to Scenario with inherited population context and runtime summary
- Story 26.4: Stage 5 completed with Run Manifest Viewer
- Story 26.5: Quick Test Population added to Population Library
- Story 26.6: Scenario naming updated to use em dash format ("Policy Set — Population")

**Migration Infrastructure Already in Place:**
- `StageKey` type includes all five stages: `"policies" | "population" | "investment-decisions" | "scenario" | "results"`
- `STAGES` constant in `workspace.ts` defines all five stages with `activeFor` arrays
- Hash migration from `#engine` to `#scenario` in `AppContext.tsx` (lines 225-235)
- localStorage migration from `"engine"` to `"scenario"` in `useScenarioPersistence.ts` (lines 86-96)

**Demo Scenario Configuration:**
- `DEMO_SCENARIO_ID = "demo-carbon-tax-dividend"`
- `DEMO_TEMPLATE_ID = "carbon-tax-dividend"`
- `DEMO_POPULATION_ID = "fr-synthetic-2024"`
- Demo name: `"Demo — Carbon Tax + Dividend"` (em dash format from Story 26.6)
- Demo scenario has `investmentDecisionsEnabled: false` (Stage 3 disabled by default)

**Quick Test Population:**
- `QUICK_TEST_POPULATION_ID = "quick-test-population"`
- 100 households, marked as "demo-only" trust status
- Labeled as fast demo/smoke test, not for substantive analysis

### Test Infrastructure Patterns

**Existing Workflow Tests:**
- `frontend/src/__tests__/workflows/analyst-journey.test.tsx` — Full App rendering with mocked APIs
- `frontend/src/__tests__/workflows/simulation-workflow.test.tsx` — Simulation Runner workflow
- `frontend/src/__tests__/workflows/portfolio-workflow.test.tsx` — Portfolio save/load/clone flows
- `frontend/src/__tests__/workflows/comparison-workflow.test.tsx` — Comparison workflow
- `frontend/src/__tests__/workflows/data-fusion-workflow.test.tsx` — Data Fusion workflow

**Test Helpers:**
- `frontend/src/__tests__/workflows/helpers.ts` — Common test helpers (setupResizeObserver, mocks, fixtures)
- `frontend/src/__tests__/e2e/fixtures.ts` — Test data fixtures (demoScenarioConfig, testPopulationId, etc.)
- `frontend/src/__tests__/e2e/helpers.ts` — E2E test helpers

**Test Patterns:**
- All API modules mocked with `vi.mock()` before imports
- Full `<AppProvider><App /></AppProvider>` tree rendered
- `beforeEach` clears `localStorage`, `sessionStorage`, and `window.location.hash`
- `waitFor()` used for async assertions after hash changes and navigation
- `within()` used to scope queries to specific regions (avoid false matches)

**localStorage Test Keys:**
- `HAS_LAUNCHED_KEY = "reformlab-has-launched"`
- `SCENARIO_STORAGE_KEY = "reformlab-active-scenario"`
- `STAGE_STORAGE_KEY = "reformlab-active-stage"`
- `SAVED_SCENARIOS_KEY = "reformlab-saved-scenarios"`
- `MANUALLY_EDITED_NAMES_KEY = "reformlab-manually-edited-names"`

### Architecture Context

**Five-Stage Flow:**
1. **Policies** (Stage 1) — Select policy set, configure parameters
2. **Population** (Stage 2) — Select primary population, view data, explore
3. **Investment Decisions** (Stage 3) — Optional decision behavior configuration
4. **Scenario** (Stage 4) — Simulation mode, horizon, validation, run trigger
5. **Run / Results / Compare** (Stage 5) — Run queue, results, comparison, manifest

**Skip Routing Logic (Story 26.2):**
- Stage 3 (Investment Decisions) is optional by default (`investmentDecisionsEnabled: false`)
- When disabled, nav rail shows "Disabled" summary
- Stage 3 is complete when disabled OR when enabled with model configured
- Scenario validation doesn't fail when decisions disabled

**Cross-Stage Validation (Story 26.3):**
- Stage 1 and Stage 2 show non-blocking warnings when policies require missing columns
- Stage 4 (Scenario) shows hard blockers for missing policy set or population
- Stage 4 is the final integration validation gate

**Hash Routing:**
- Format: `#{stage}` or `#{stage}/{subView}`
- Examples: `#policies`, `#population`, `#population/data-fusion`, `#results/comparison`, `#results/manifest`
- Migration: `#engine` → `#scenario`, `#engine/<subView>` → `#scenario/<subView>`
- Invalid hash defaults to `#policies`

### Implementation Strategy

**Phase 1: Create new regression test file**
1. Create `frontend/src/__tests__/workflows/five-stage-regression.test.tsx`
2. Import test helpers and fixtures from existing files
3. Mock all API modules (same pattern as analyst-journey.test.tsx)
4. Add `beforeAll` and `beforeEach` setup

**Phase 2: Implement five-stage happy-path test**
1. Test first-launch loads demo scenario
2. Verify all five stages in nav rail
3. Verify hash routing works for all stages
4. Verify demo scenario configuration (name, template, population)

**Phase 3: Implement migration test**
1. Test localStorage migration from "engine" to "scenario"
2. Test hash migration from #engine to #scenario
3. Test returning user with full four-stage state
4. Test hash+localStorage conflict scenario

**Phase 4: Implement skip routing test**
1. Test Stage 3 disabled state
2. Test Continue to Scenario bypass
3. Test Scenario validation with disabled decisions
4. Test nav rail completion logic

**Phase 5: Implement cross-stage validation test**
1. Test Stage 1 warning for missing columns
2. Test Stage 2 warning for missing columns
3. Verify warnings are non-blocking
4. Verify Scenario stage hard blockers

**Phase 6: Implement Stage 5 sub-views test**
1. Test all Stage 5 sub-views keep Run / Results / Compare active
2. Test invalid sub-view fallback
3. Test manifest viewer access (Story 26.4)

**Phase 7: Update existing tests**
1. Update analyst-journey.test.tsx for five stages
2. Update nav rail tests
3. Update completion tests
4. Verify all existing tests pass

**Phase 8: Run full regression suite**
1. Run `npm test` in frontend directory
2. Verify all tests pass
3. Document any pre-existing failures

### Key Design Decisions

**Test File Structure:**
- New file: `frontend/src/__tests__/workflows/five-stage-regression.test.tsx`
- Follow existing patterns from `analyst-journey.test.tsx`
- Use `describe()` blocks to group tests by AC
- Use `beforeEach` to reset state between tests

**Mock Data:**
- Use existing fixtures from `frontend/src/__tests__/e2e/fixtures.ts`
- Use `createDemoScenario()` for first-launch tests
- Create custom scenarios for migration tests

**Test Isolation:**
- Each test clears localStorage, sessionStorage, and hash
- Each test has independent mock setup
- No shared state between tests

**Assertion Patterns:**
- Use `waitFor()` for async assertions after hash changes
- Use `getByTestId()` for component-specific assertions
- Use `within()` to scope queries to specific regions
- Use `getAllByText()` when multiple matches are expected

### Project Structure Notes

**Files to Create:**
- `frontend/src/__tests__/workflows/five-stage-regression.test.tsx` — New regression test suite

**Files to Verify (no changes expected):**
- `frontend/src/contexts/AppContext.tsx` — Hash migration logic
- `frontend/src/hooks/useScenarioPersistence.ts` — localStorage migration logic
- `frontend/src/types/workspace.ts` — Stage definitions
- `frontend/src/components/layout/WorkflowNavRail.tsx` — Five-stage nav rail
- `frontend/src/__tests__/workflows/analyst-journey.test.tsx` — May need updates for five stages

**Files to Modify:**
- `frontend/src/__tests__/workflows/analyst-journey.test.tsx` — Update for five-stage model

### Testing Strategy

**Unit Tests:**
- No new unit tests needed (Story 26.7 is integration/regression focused)

**Integration Tests:**
- `five-stage-regression.test.tsx` — New integration test suite
- Update `analyst-journey.test.tsx` for five stages

**E2E Tests:**
- Use existing E2E patterns (full App rendering, mocked APIs)

**Regression Coverage:**
- Five-stage nav routing
- First-launch demo flow
- Returning-user restore with migration
- Skip routing for disabled Investment Decisions
- Cross-stage validation warnings
- Stage 5 sub-views
- Quick Test Population
- Scenario naming (em dash format)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-26.7] — Story requirements and acceptance criteria
- [Source: frontend/src/contexts/AppContext.tsx#L220-L245] — Hash routing with migration logic
- [Source: frontend/src/hooks/useScenarioPersistence.ts#L82-L97] — localStorage migration logic
- [Source: frontend/src/types/workspace.ts#L97-L103] — STAGES constant with five stages
- [Source: frontend/src/components/layout/WorkflowNavRail.tsx] — Five-stage nav rail implementation
- [Source: frontend/src/data/demo-scenario.ts] — Demo scenario configuration
- [Source: frontend/src/data/quick-test-population.ts] — Quick Test Population definition
- [Source: frontend/src/__tests__/workflows/analyst-journey.test.tsx] — Existing workflow test patterns
- [Source: frontend/src/__tests__/e2e/fixtures.ts] — Test data fixtures
- [Source: frontend/src/__tests__/workflows/helpers.ts] — Test helper functions

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (story creation)

### Debug Log References

None — story created with comprehensive context from existing codebase analysis.

### Completion Notes List

Story 26.7 created with comprehensive developer context:

**Context Sources Analyzed:**
- Epic 26 Story 26.7 requirements and acceptance criteria
- AppContext.tsx — Hash routing, migration logic, first launch, restore flow
- useScenarioPersistence.ts — localStorage migration, first-launch detection
- workspace.ts — Stage definitions, STAGES constant
- demo-scenario.ts — Demo scenario configuration
- quick-test-population.ts — Quick Test Population definition
- WorkflowNavRail.tsx — Five-stage nav rail, completion logic
- analyst-journey.test.tsx — Existing workflow test patterns
- useScenarioPersistence.test.tsx — Existing migration tests
- fixtures.ts and helpers.ts — Test infrastructure

**Key Findings:**
- Five-stage migration is complete (Stories 26.1-26.6)
- Hash and localStorage migration infrastructure already in place
- Demo scenario uses em dash format from Story 26.6
- Quick Test Population already added in Story 26.5
- Existing test patterns provide solid foundation for regression tests
- analyst-journey.test.tsx needs updates for five-stage model

**Implementation Scope:**
- Create new regression test file: `five-stage-regression.test.tsx`
- Add tests for five-stage happy path, migration, skip routing, cross-stage validation, Stage 5 sub-views
- Update existing `analyst-journey.test.tsx` for five stages
- Run full regression suite and verify all tests pass

**Testing Strategy:**
- Follow existing patterns from `analyst-journey.test.tsx`
- Use full App rendering with mocked APIs
- Clear localStorage/sessionStorage/hash in beforeEach
- Use waitFor() for async assertions
- Use within() for scoped queries
- Test happy paths, edge cases, and error conditions

**Expected Test Coverage:**
- Five-stage nav routing (all stages, all hash formats)
- First-launch demo flow
- Returning-user restore with migration
- Skip routing for disabled Investment Decisions
- Cross-stage validation warnings
- Stage 5 sub-views (all 6 sub-views)
- Quick Test Population visibility and selection
- Scenario naming (em dash format)
- Migration from "engine" to "scenario"

Status set to: ready-for-dev

### File List

- `_bmad-output/implementation-artifacts/26-7-add-five-stage-migration-demo-restore-and-cross-stage-regression-coverage.md`
