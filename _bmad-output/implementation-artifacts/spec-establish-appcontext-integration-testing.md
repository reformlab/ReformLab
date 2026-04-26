---
title: 'Establish AppContext Integration Testing'
type: 'feature'
created: '2026-04-22'
status: 'done'
baseline_commit: 'dbad85b7d78bfd9fbc51e5fcf9f63be32b5cdaf0'
context:
  - '{project-root}/_bmad-output/project-context.md'
  - '{project-root}/_bmad-output/implementation-artifacts/retrospectives/epic-26-retro-20260422.md'
  - '{project-root}/_bmad-output/implementation-artifacts/26-6-add-deterministic-scenario-name-suggestions-from-policy-set-and-population-context.md'
---

<frozen-after-approval reason="human-owned intent - do not modify unless human renegotiates">

## Intent

**Problem:** Epic 26 left AppContext naming behavior under-tested: auto-update, manual edit freeze, loaded scenario preservation, and demo scenario protection are claimed in Story 26.6 but only the pure naming utility has direct coverage. The current provider flow is stateful enough that component mocks and broad workflow tests can miss regressions.

**Approach:** Add a focused AppProvider integration test harness that renders the real provider with a tiny consumer component, mocked API modules, and isolated storage. Use those tests to lock the lifecycle behavior; if the loaded-scenario preservation test fails, apply the smallest AppContext fix that preserves loaded names without changing unrelated workflow routing.

## Boundaries & Constraints

**Always:** Test the real `AppProvider` and `useAppState()` together; mock HTTP-facing API modules and `/api/health`; isolate `localStorage`, `sessionStorage`, and `window.location.hash` in every test; keep the test file provider-scoped rather than rendering the full `App` shell.

**Ask First:** Any schema change to `WorkspaceScenario`; any new persisted storage key beyond the existing manual-name key; any UX change where loaded saved scenarios permanently opt out of future automatic naming.

**Never:** Do not add real backend/network dependency; do not expand the existing five-stage workflow regression file for this narrow provider behavior; do not replace `generateScenarioSuggestion()` unit tests with provider tests.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|---------------|----------------------------|----------------|
| Auto-name active draft | Authenticated provider with a non-demo active scenario that has not been manually renamed; policy set and primary population are selected | Scenario name updates to the deterministic policy-set plus population suggestion using the current em-dash format | Failing API mocks should fall back to existing mock data without making the assertion flaky |
| Manual edit freeze | Same scenario, then `updateScenarioField("name", "Custom label")`, then policy set or population changes | `"Custom label"` remains and `MANUALLY_EDITED_NAMES_KEY` contains the scenario id | If storage write fails, React state still preserves the name for the session |
| Loaded scenario preservation | `SCENARIO_STORAGE_KEY` contains a saved non-demo scenario with an existing name and `HAS_LAUNCHED_KEY` is true | Initial provider restore keeps the existing name through selector sync and API refresh effects | Corrupt saved scenario JSON should keep existing fallback behavior, not be handled in this story |
| Demo scenario protection | First-launch or reset-to-demo state with `DEMO_SCENARIO_ID` | Demo name remains unchanged after policy set or population context changes | No manual-name entry should be created for the demo id |

</frozen-after-approval>

## Code Map

- `frontend/src/contexts/AppContext.tsx` -- Owns `activeScenario`, manual-name tracking, saved scenario restore, reset-to-demo, create/clone actions, and the auto-name effect.
- `frontend/src/hooks/useScenarioPersistence.ts` -- Exports storage keys and manual-name persistence helpers needed for test setup and assertions.
- `frontend/src/utils/naming.ts` -- Pure deterministic naming utility already unit-tested; provider tests should assert integration with it, not duplicate all utility cases.
- `frontend/src/utils/__tests__/naming.test.ts` -- Existing unit coverage for slugging, em-dash suggestions, and clone naming.
- `frontend/src/__tests__/workflows/five-stage-regression.test.tsx` -- Broad App-level regression coverage; useful pattern for API mocks but too heavy for the missing AppContext lifecycle tests.
- `frontend/src/test/setup.ts` -- Current global test setup; provider test may need local `fetch` and browser API stubs rather than global changes.

## Tasks & Acceptance

**Execution:**
- [x] `frontend/src/contexts/__tests__/AppContext.integration.test.tsx` -- Add a focused provider harness with API mocks, an authenticated-session setup helper, a `ContextProbe` consumer, and the four matrix scenarios -- closes the infrastructure gap without coupling to full-page UI.
- [x] `frontend/src/contexts/AppContext.tsx` -- If the new loaded-scenario test fails, adjust restore/load behavior so an existing saved name is not overwritten during initial provider hydration -- addresses the actual integration bug while keeping manual edit and demo protections intact.
- [x] `frontend/src/hooks/useScenarioPersistence.ts` or existing test helpers -- No source change needed; reused exported storage keys directly in the provider test -- keeps integration tests isolated across runs.

**Acceptance Criteria:**
- Given a non-demo scenario has not been manually renamed, when policy set and primary population context change through `useAppState()`, then `activeScenario.name` becomes the deterministic suggestion.
- Given a non-demo scenario name was manually edited through `updateScenarioField("name", ...)`, when policy set or primary population context changes, then the manual name remains unchanged and the scenario id is persisted in the manual-name set.
- Given a saved scenario is restored from localStorage, when AppProvider completes initialization and mocked API refresh effects settle, then the restored name remains unchanged.
- Given the active scenario is the demo scenario, when policy set or population context changes, then the demo name remains unchanged and the demo id is not written to the manual-name set.

## Design Notes

The main recommendation is to test AppContext at the provider boundary: render `<AppProvider><ContextProbe /></AppProvider>` instead of `<App />`. The probe can expose buttons or callbacks for `setSelectedPortfolioName`, `setSelectedPopulationId`, `updateScenarioField`, `loadSavedScenario`, and `resetToDemo`, while the assertion reads `activeScenario` directly. This catches provider state interactions without inheriting unrelated nav rail, modal, and screen complexity.

There is a likely implementation risk in the current restore flow: `activeScenario.portfolioName` is restored, but `selectedPortfolioName` is not synchronized, while the auto-name effect generates from `selectedPortfolioName`. If the preservation test exposes this, prefer a minimal provider fix over broad UI changes: synchronize selected policy-set state on restore/load and prevent the initial hydration pass from renaming an existing saved scenario.

## Verification

**Commands:**
- `cd frontend && npm test -- src/contexts/__tests__/AppContext.integration.test.tsx` -- expected: new provider integration tests pass.
- `cd frontend && npm test -- src/utils/__tests__/naming.test.ts src/__tests__/workflows/five-stage-regression.test.tsx` -- expected: existing naming and broad Epic 26 regression coverage still passes.
- `cd frontend && npm run typecheck` -- expected: TypeScript accepts any AppContext/test changes.

## Suggested Review Order

**Restore Semantics**

- Preserve loaded names only while the restored context is unchanged.
  [`AppContext.tsx:300`](../../frontend/src/contexts/AppContext.tsx#L300)

- Synchronize restored policy set and primary population selectors.
  [`AppContext.tsx:332`](../../frontend/src/contexts/AppContext.tsx#L332)

- Keep default selector effects from overriding restored values.
  [`AppContext.tsx:463`](../../frontend/src/contexts/AppContext.tsx#L463)

**Auto-Naming Guard**

- Skip auto-name while the loaded scenario context still matches.
  [`AppContext.tsx:521`](../../frontend/src/contexts/AppContext.tsx#L521)

- Apply the same preservation rule when loading saved scenarios.
  [`AppContext.tsx:581`](../../frontend/src/contexts/AppContext.tsx#L581)

**Provider Coverage**

- Use a tiny real-context consumer instead of full app rendering.
  [`AppContext.integration.test.tsx:154`](../../frontend/src/contexts/__tests__/AppContext.integration.test.tsx#L154)

- Assert auto-update, manual freeze, loaded preservation, and demo protection.
  [`AppContext.integration.test.tsx:231`](../../frontend/src/contexts/__tests__/AppContext.integration.test.tsx#L231)
