# Epic 20 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 20-1 (2026-03-24)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `WorkspaceScenario.status` is a closed union but EPIC-21 note says not to use one — direct self-contradiction in the same file | Replaced status with `ScenarioStatus = string` type alias with known values documented in a comment; updated the EPIC-21 note to reference the new type. |
| critical | Stage label "Run / Results / Compare" (AC-1, story title) vs "Run / Results" (STAGES constant) — would cause rail label mismatch and brittle test failures | Normalized `STAGES` constant to `"Run / Results / Compare"`. Added import directive in Task 4.1 so WorkflowNavRail uses the single source from `workspace.ts`. |
| critical | `mock-data.ts` Files to Modify says "Deprecate/remove old `Scenario` interface" but Task 8.3 says keep backward-compatible state — contradictory migration path | Changed `mock-data.ts` row to explicitly keep the interface, add a `@deprecated` comment only, and prohibit deletion until 20.3–20.6. |
| critical | `analyst-journey.test.tsx` task 6.5 hard-targets gradient-header "Simulation" button which is removed in Task 5.1 — guaranteed test failure | Expanded Task 9.3 with subtasks 9.3a and 9.3b specifying exactly how the comparison navigation flow must be rewritten using hash changes instead of button clicks. |
| critical | `isValidStage()` used in routing sketch but never defined; empty-hash fallback behavior unspecified | Added `isValidStage` and `isValidSubView` as exported functions in the type definitions block; updated routing sketch to use them with explicit fallback to `"policies"` for empty/invalid input. |
| high | Task 8.3 "where possible" migration boundary — no definition of what must migrate now vs later | Rewrote Task 8.3 to explicitly prohibit replacing existing field reads in this story; `activeScenario` is added alongside, not replacing, existing state. |
| high | `ScenarioCard` removal (Task 4.5) deletes `onSelect`/`onRun`/`onCompare` UX flows with no replacement specified | Added explicit note to Task 4.5 to keep all AppContext scenario actions (`startRun`, `cloneScenario`, `deleteScenario`) in place; removal deferred to 20.3–20.4. |
| high | `ContextualHelpPanel` not in Files to Modify — will silently show wrong help content after ViewMode is replaced | Added `ContextualHelpPanel.tsx` and `help-content.ts` to Files to Modify with specific change descriptions. |
| high | Task 2.4 "update all setViewMode call sites" with no enumeration — dev will miss calls | Task 2.4 now contains an exhaustive list of all `setViewMode` calls, `openComparison`/`backFromComparison`/`openDecisions`/`backFromDecisions` functions to delete, and `previousViewMode` state to remove. |
| high | `WorkflowNavRailProps` prop interface change (setViewMode → navigateTo) underdescribed | Task 4.6 now specifies exact prop replacement (`activeStage: StageKey` + `navigateTo: (stage: StageKey) => void`) and that props are received (not consumed via hook) for testability. |
| high | `WorkspaceLayout` height calc `h-[calc(100vh-Xrem)]` not updated for 48px TopBar insertion | Added note to `WorkspaceLayout.tsx` row in Files to Modify. |
| low | AC-3 "clear ownership boundaries" not objectively testable | Rewrote AC-3 with concrete field-level requirements (WorkspaceScenario references portfolio by name, population by ID array; no single interface owns fields from two object classes). |
| low | Stub screen strategy ambiguous ("re-exports existing content or simple placeholder") | Tasks 6.1 and 6.2 now unambiguously specify thin wrappers rendering existing screens directly (not placeholders). |
| low | No AC for default hash behavior or stage-4 screen regression preservation | Added AC-4 (empty/invalid hash fallback) and AC-5 (stage-4 screens preserved). |
| dismissed | Story scope is too large — should be split into 3 stories | FALSE POSITIVE: Story is already written, approved, and has downstream dependencies (20.2–20.7). Scope splitting at synthesis stage requires sprint re-planning beyond this workflow's authority. The story has a clear delivery boundary (shell + types) and all tasks are coherent. Noted as a risk but not actionable here. |
| dismissed | Backend quality gates (10.4–10.5) in a frontend-only story are "noisy blocking overhead" | FALSE POSITIVE: This is a project convention — all stories run full quality gates regardless of scope. Not a story defect. |
| dismissed | INVEST violations N/E/S/T scores (negotiable, estimable, small, testable) | FALSE POSITIVE: INVEST scoring is useful for backlog refinement before story creation, not for post-hoc rejection of authored stories with defined deliverables. The actionable defects within these INVEST scores (missing ACs, ambiguous tasks) were extracted and addressed individually above. |
| dismissed | `handleStartRun` async-progress flow is "ambiguous" for hash routing | FALSE POSITIVE: The ViewMode mapping table already shows `"run"/"progress"` → `"results"/"runner"`, and Task 2.4 now explicitly maps all three `handleStartRun` calls. The `SimulationRunnerScreen` using `runLoading` prop for internal progress state is an implementation detail not requiring story-level specification. |

## Story 20-3 (2026-03-25)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | AC-6 validity contradiction with Task 5.3 | AC-6 rewritten with concrete boolean rule (`composition.length >= 1 && (no conflicts OR strategy !== "error")`). Task 5.3 indicator condition fixed (was `&& conflicts.length === 0 &&` which produced false-amber for zero-conflict portfolios with "error" strategy). |
| critical | WorkflowNavRail.test.tsx regression | Task 8.3 updated to include `portfolio-workflow.test.tsx`; Task 8.4 added with explicit test update instructions — replace `portfolios` prop assertion with `activeScenario.portfolioName` assertion in completion and summary tests. |
| high | PortfolioCompositionPanel "reused as-is" contradicts Task 2.2 | Component Reuse table row changed to `⚠️ Requires small prop addition`; Task 2.2 updated to reference the `minimumPolicies={1}` prop; `PortfolioCompositionPanel.tsx` added to Files to Modify; removed from Files NOT Modified. |
| high | Task 4.1 self-contradiction | Removed the ambiguous `\|\| composition.length > 0` clause. Task now states the single clear decision: `activeScenario?.portfolioName !== null` with rationale. |
| high | Delete action in wireframe but absent from Tasks | Task 6.5 added covering `Trash2` button, `deletePortfolio()` call, `refetchPortfolios()`, and delink-from-scenario logic when deleting the active portfolio. |
| high | loadedRef ordering risk in save handler | Task 3.2 expanded to explicitly require `loadedRef.current = portfolioName` BEFORE `updateScenarioField(...)`, with explanation of why ordering matters. |
| high | AC-2 overstates execution support | "used for execution" removed from AC-2; parenthetical note added that portfolio execution is wired in Story 20.6. |
| medium | `savedPortfolios` naming inconsistency | Task 6.2 updated to use `portfolios` (the actual AppContext field name). |
| medium | `validatePortfolioName`/`NAME_RE` not shared | `portfolioValidation.ts` added to Files to Create; `PortfolioDesignerScreen` is the extraction source; both Save and Clone dialogs will import from the shared utility. |
| medium | AC-4 independence test assertion too vague | Task 8.2 test bullet tightened to assert no `/api/scenarios` calls and no `saveCurrentScenario`/`cloneCurrentScenario` invocations. |
