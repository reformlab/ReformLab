# Story 26.7 Validation Synthesis Report

**Date:** 2026-04-22
**Story:** 26.7 - Add Five-Stage Migration, Demo, Restore, and Cross-Stage Regression Coverage
**Validators:** 2 (Quality Competition Engine)

---

<!-- VALIDATION_SYNTHESIS_START -->
## Synthesis Summary

**Issues Verified:** 14 issues (1 Critical, 8 High, 5 Medium)
**False Positives Dismissed:** 2 issues
**Changes Applied:** 11 modifications to story file

Both validators identified critical testability issues with AC-6 (using "covers" without measurable criteria) and significant ambiguities in AC-1, AC-2, and AC-4. The conflicting test file name directive was also correctly flagged. Story has been updated with specific, measurable acceptance criteria, concrete test count targets, edge case examples, mobile coverage, and performance/browser compatibility guidance.

## Validations Quality

| Validator | Quality Score | Comments |
|-----------|---------------|----------|
| Validator A | 8.4/10 | Thorough analysis with excellent architectural alignment assessment. Correctly identified AC-6 as fundamentally untestable. |
| Validator B | 7.7/10 | Good catch on missing mobile coverage and conflicting file names. AC-6 and warning brittleness appropriately flagged. |

**Overall Validation Quality:** 8.0/10 - Both validators provided valuable, actionable feedback. Consensus on critical issues (AC-6 testability, conflicting file names) increases confidence.

## Issues Verified (by Severity)

### Critical

- **Issue: AC-6 is fundamentally untestable** | **Source:** Validator A, Validator B | **Fix:** Replaced with specific test count targets (minimum 8+ tests per area) for all 9 coverage domains (five-stage nav, demo flow, restore migration, skip routing, cross-stage validation, Stage 5 sub-views, Quick Test Population, scenario naming, mobile stage-switcher). Each area now has measurable completion criteria.

### High

- **Issue: AC-1 "valid Stage 1-4 selections" is undefined** | **Source:** Validator A, Validator B | **Fix:** Added 5 sub-criteria (a-e) specifying exact requirements: policy set selected, DEMO_POPULATION_ID selected, Stage 3 disabled, Scenario has valid mode/horizon, analyst can run without validation errors.

- **Issue: AC-4 "non-blocking warnings" format undefined** | **Source:** Validator A, Validator B | **Fix:** Added 5 sub-criteria (a-e) specifying: warnings have same semantic meaning across stages, format includes category/role/severity and column list, appear in amber banner, are non-blocking, and Scenario shows hard blockers.

- **Issue: AC-2 "without losing scenario context" incomplete** | **Source:** Validator A, Validator B | **Fix:** Added 7 sub-criteria (a-g) specifying exact context elements to preserve: policy set, population ID, decisions enabled/disabled state, scenario settings (startYear, endYear, seed, discountRate, simulationMode), Stage 5 sub-view, stage key migration, hash redirection.

- **Issue: Conflicting test file names** | **Source:** Validator A, Validator B | **Fix:** Standardized to `five-stage-regression.test.tsx` throughout (Task 1.1 updated, Implementation Strategy already correct).

- **Issue: Missing edge case examples for hash+localStorage conflict** | **Source:** Validator A, Validator B | **Fix:** Added 4 specific conflict scenarios with expected behaviors: (1) empty hash + "engine" localStorage, (2) #engine hash + "scenario" localStorage, (3) #engine hash + empty localStorage, (4) #scenario hash + "engine" localStorage.

- **Issue: Missing mobile stage-switcher coverage** | **Source:** Validator B | **Fix:** Added new task section "Add mobile stage-switcher regression test" with 4 subtasks: compact nav shows all stages, stage switching works, sub-view navigation works, active stage highlighted.

- **Issue: Warning test over-constrained ("identical warnings")** | **Source:** Validator B | **Fix:** Changed from "Verify warnings are identical" to "Verify warnings have the same semantic meaning and non-blocking behavior (check category/role/severity, not exact string match)".

### Medium

- **Issue: No performance expectations for test execution** | **Source:** Validator A | **Fix:** Added "Performance Targets" section to Testing Strategy: aim for under 2 seconds per test, under 60 seconds for full suite, use focused tests over broad E2E sweeps.

- **Issue: No browser compatibility specification** | **Source:** Validator A | **Fix:** Added "Browser Compatibility" section to Testing Strategy: must pass in Chromium-based browsers (Chrome, Edge), Safari/Firefox desirable but not blocking.

- **Issue: No mock data creation guidance** | **Source:** Validator A | **Fix:** Added mock fixture creation to Phase 1 with 4 specific fixture types needed: migration scenarios, Stage 3 states, validation warnings, Stage 5 routing states.

- **Issue: Restore semantics unclear (hash vs localStorage precedence)** | **Source:** Validator A, Validator B | **Fix:** Added "Restore Precedence" section to Architecture Context: URL hash subview > localStorage stage > default; empty hash uses localStorage; hash persisted to localStorage on save.

- **Issue: Mock data section lacks specific factory references** | **Source:** Validator A | **Fix:** Updated Mock Data section in Key Design Decisions to list specific factories from helpers.ts (setupResizeObserver, setupExportMocks, mockResultListItem, etc.).

### Low

- **Issue: Hardcoded test count "926+" is fragile** | **Source:** Validator B | **Fix:** Changed to "expect 50+ new tests added to existing suite" - more durable as it focuses on delta rather than absolute count.

## Issues Dismissed

- **Claimed Issue: Story is oversized and should be split** | **Raised by:** Validator A, Validator B | **Dismissal Reason:** Scope is appropriate for a regression testing story. All coverage areas are interconnected parts of the same five-stage workspace migration. Testing them together ensures integration compatibility. The 3 SP estimate is reasonable given existing test infrastructure and patterns.

- **Claimed Issue: Quick Test Population "near top" is imprecise** | **Raised by:** Validator B | **Dismissal Reason:** "Near top" is appropriate language for a population library with dynamic content and sorting. Forcing "first card" would be over-prescriptive and may not match the actual library behavior (populations may be sorted by trust, date, or other criteria).

## Deep Verify Integration

Deep Verify did not produce findings for this story. All issues were identified through manual validator review.

## Changes Applied

**Location:** `_bmad-output/implementation-artifacts/26-7-add-five-stage-migration-demo-restore-and-cross-stage-regression-coverage.md` - Acceptance Criteria section

**Change:** Rewrote all 6 ACs with specific, measurable criteria

**Before:**
```
1. Given first launch uses the demo scenario, when the workspace opens, then valid Stage 1-4 selections are present and the analyst can run immediately.
...
6. Given the regression suite runs, then it covers five-stage nav, skip routing, scenario validation, Quick Test Population, scenario naming, manifest access, demo flow, and restore flow.
```

**After:**
```
1. Given first launch uses the demo scenario, when the workspace opens, then:
   a. Stage 1 (Policies) has a policy set selected with at least one policy configured
   b. Stage 2 (Population) has the DEMO_POPULATION_ID selected as primary population
   c. Stage 3 (Investment Decisions) is in disabled state (investmentDecisionsEnabled: false)
   d. Stage 4 (Scenario) has valid simulation mode (annual) and horizon configured (startYear: 2025, endYear: 2030)
   e. The analyst can click "Run" and execution proceeds without validation errors
...
6. Given Story 26.7 implementation is complete, then the following test coverage exists:
   a. Five-stage nav routing: minimum 8 tests
   b. First-launch demo flow: minimum 6 tests
   [... 7 more specific coverage areas with minimum test counts]
```

---

**Location:** Same file - Task 1.1

**Change:** Fixed conflicting test file name

**Before:**
```
- [ ] Create `five-stage-happy-path.test.tsx` in `frontend/src/__tests__/workflows/`
```

**After:**
```
- [ ] Create `five-stage-regression.test.tsx` in `frontend/src/__tests__/workflows/`
```

---

**Location:** Same file - Task 2.8

**Change:** Added specific edge case scenarios

**Before:**
```
- [ ] Test hash+localStorage conflict scenario (hash empty, localStorage has "engine")
```

**After:**
```
- [ ] Test hash+localStorage conflict scenarios:
  - [ ] Scenario 1: hash empty + localStorage has "engine" → migrate to "scenario" and persist
  - [ ] Scenario 2: hash is #engine + localStorage has "scenario" → hash takes precedence, redirect to #scenario
  - [ ] Scenario 3: hash is #engine + localStorage is empty → migrate hash to #scenario and persist
  - [ ] Scenario 4: hash is #scenario + localStorage has "engine" → hash takes precedence, localStorage migrated on save
```

---

**Location:** Same file - Task 4.3

**Change:** Made warning test more flexible (semantic vs exact string match)

**Before:**
```
- [ ] Verify warnings are identical across both stages (same message, same non-blocking behavior)
```

**After:**
```
- [ ] Verify warnings have the same semantic meaning and non-blocking behavior across both stages (check category/role/severity, not exact string match)
```

---

**Location:** Same file - After Task 5.7

**Change:** Added mobile stage-switcher test task

**Before:**
```
- [ ] Verify invalid sub-view falls back to run queue without crashing

- [ ] Add Quick Test Population regression test (AC: #6)
```

**After:**
```
- [ ] Verify invalid sub-view falls back to run queue without crashing

- [ ] Add mobile stage-switcher regression test (AC: #6)
  - [ ] Test compact navigation mode shows all five stages in mobile viewport
  - [ ] Test stage switching works via mobile stage switcher dropdown
  - [ ] Test sub-view navigation works in mobile compact mode
  - [ ] Test active stage is correctly highlighted in mobile navigation

- [ ] Add Quick Test Population regression test (AC: #6)
```

---

**Location:** Same file - Testing Strategy section

**Change:** Added Performance Targets and Browser Compatibility sections

**Before:**
```
### Testing Strategy

**Unit Tests:**
...
**E2E Tests:**
- Use existing E2E patterns (full App rendering, mocked APIs)
```

**After:**
```
### Testing Strategy

**Unit Tests:**
...
**E2E Tests:**
- Use existing E2E patterns (full App rendering, mocked APIs)

**Performance Targets:**
- Individual test execution: aim for under 2 seconds per test
- Full regression suite: aim for under 60 seconds total
- Use focused integration tests over broad end-to-end sweeps to maintain speed

**Browser Compatibility:**
- Tests must pass in Chromium-based browsers (Chrome, Edge)
- Safari/Firefox support is desirable but not blocking for this story
- Follow project's existing browser support policy
```

---

**Location:** Same file - Phase 1 (Implementation Strategy)

**Change:** Added mock fixture creation task

**Before:**
```
**Phase 1: Create new regression test file**
1. Create `frontend/src/__tests__/workflows/five-stage-regression.test.tsx`
2. Import test helpers and fixtures from existing files
3. Mock all API modules (same pattern as analyst-journey.test.tsx)
4. Add `beforeAll` and `beforeEach` setup
```

**After:**
```
**Phase 1: Create new regression test file**
1. Create `frontend/src/__tests__/workflows/five-stage-regression.test.tsx`
2. Import test helpers and fixtures from existing files
3. Create or extend mock fixtures in `fixtures.ts` for five-stage scenarios:
   - Mock migration scenarios (four-stage state → five-stage state)
   - Mock Stage 3 disabled/enabled states
   - Mock cross-stage validation warning responses
   - Mock Stage 5 sub-view routing states
4. Mock all API modules (same pattern as analyst-journey.test.tsx)
5. Add `beforeAll` and `beforeEach` setup
```

---

**Location:** Same file - Hash Routing section (Architecture Context)

**Change:** Added Restore Precedence section

**Before:**
```
**Hash Routing:**
- Format: `#{stage}` or `#{stage}/{subView}`
- Examples: `#policies`, `#population`, `#population/data-fusion`, `#results/comparison`, `#results/manifest`
- Migration: `#engine` → `#scenario`, `#engine/<subView>` → `#scenario/<subView>`
- Invalid hash defaults to `#policies`
```

**After:**
```
**Hash Routing:**
- Format: `#{stage}` or `#{stage}/{subView}`
- Examples: `#policies`, `#population`, `#population/data-fusion`, `#results/comparison`, `#results/manifest`
- Migration: `#engine` → `#scenario`, `#engine/<subView>` → `#scenario/<subView>`
- Invalid hash defaults to `#policies`

**Restore Precedence (for returning users):**
- URL hash subview takes precedence over localStorage stage
- localStorage stage takes precedence over default
- When hash is empty, use localStorage stage value
- When localStorage is empty, use hash and persist to localStorage on save
```

---

**Location:** Same file - Mock Data section (Key Design Decisions)

**Change:** Added specific factory references

**Before:**
```
**Mock Data:**
- Use existing fixtures from `frontend/src/__tests__/e2e/fixtures.ts`
- Use `createDemoScenario()` for first-launch tests
- Create custom scenarios for migration tests
```

**After:**
```
**Mock Data:**
- Use existing factories from `frontend/src/__tests__/workflows/helpers.ts`:
  - `setupResizeObserver()` — Required by Recharts components
  - `setupExportMocks()` — Stub URL.createObjectURL for export tests
  - `mockResultListItem()` — Result list item fixtures
  - `mockResultDetailResponse()` — Complete result fixtures
  - `mockRunResponse()` — Run response fixtures
- Use existing fixtures from `frontend/src/__tests__/e2e/fixtures.ts`:
  - `demoScenarioConfig` — Demo scenario configuration
  - `createDemoScenario()` — Demo scenario factory
  - `testPopulationId` — Test population ID
- Create custom migration fixtures for four-stage → five-stage scenarios in fixtures.ts
```

---

**Location:** Same file - Task 9.2

**Change:** Made test count reference more durable

**Before:**
```
- [ ] Verify all 926+ tests pass (current count from Story 26.6)
```

**After:**
```
- [ ] Verify all tests pass (expect 50+ new tests added to existing suite)
```

---

**Location:** Same file - Regression Coverage section

**Change:** Added mobile stage-switcher to coverage list

**Before:**
```
**Regression Coverage:**
- Five-stage nav routing
- First-launch demo flow
- Returning-user restore with migration
- Skip routing for disabled Investment Decisions
- Cross-stage validation warnings
- Stage 5 sub-views
- Quick Test Population
- Scenario naming (em dash format)
```

**After:**
```
**Regression Coverage:**
- Five-stage nav routing
- First-launch demo flow
- Returning-user restore with migration
- Skip routing for disabled Investment Decisions
- Cross-stage validation warnings
- Stage 5 sub-views
- Quick Test Population
- Scenario naming (em dash format)
- Mobile stage-switcher navigation
```

<!-- VALIDATION_SYNTHESIS_END -->

---

## Summary

Story 26.7 has been significantly improved based on validator feedback. The primary issues were:

1. **AC-6 untestable** - Fixed by adding specific minimum test counts for each of 9 coverage domains
2. **Vague AC criteria** - Fixed by adding detailed sub-criteria to AC-1, AC-2, and AC-4
3. **Conflicting file names** - Fixed by standardizing on `five-stage-regression.test.tsx`
4. **Missing mobile coverage** - Fixed by adding dedicated mobile test task
5. **Missing edge case specifications** - Fixed by adding 4 specific conflict scenarios
6. **Missing implementation guidance** - Fixed by adding performance targets, browser compatibility, mock fixture tasks, and restore precedence rules

The story is now ready for development with clear, measurable acceptance criteria and comprehensive implementation guidance.
