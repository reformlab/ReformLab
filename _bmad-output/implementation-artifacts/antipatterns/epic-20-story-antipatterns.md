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

## Story 20-6 (2026-03-27)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Cell state enum not defined (not executed, running, completed, failed referenced but no TypeScript enum) | Added `ExecutionStatus` enum definition with 5 states in types section and updated task 20.6.1 |
| critical | ComparisonDimension getValue() return type undefined - type safety violation | Added complete TypeScript interface with generic type parameter and optional render method |
| critical | WebSocket vs polling not specified - leaves critical infrastructure decision unresolved | Specified polling as default approach (2s interval, 10min timeout) with WebSocket deferred to future story |
| critical | ResultStore path incorrect - story points to `core/result_store.py` but actual is `server/result_store.py` | Corrected all ResultStore path references to `src/reformlab/server/result_store.py` |
| critical | RunMetadata type incorrect - story references `RunMetadata` in models.py but actual persistent type is `ResultMetadata` in result_store.py | Updated all references from `RunMetadata` to `ResultMetadata` |
| critical | AC-2 lineage contract incomplete - portfolio composition, population version, full engine config not defined in persistence schema | Extended AC-2 with explicit field specifications and added task to extend ResultMetadata with portfolio_snapshot |
| critical | Story scope too large for 8 SP - involves 3 screen refactors, 4 new components, backend changes, migration | Updated story points to 13 and added note in Dev Agent Record about scope assessment |
| critical | Matrix state synchronization mechanism undefined - "publish matrix cell updates via AppContext" with no specification | Added explicit AppContext extension specification with ExecutionMatrixState interface |
| critical | No async execution contract - story expects running/cancel states but backend run endpoint is synchronous | Reduced scope to post-run matrix only for this story, deferred async execution infrastructure |
| critical | Test path references non-existent directory | Changed from `tests/integration/frontend/` to `frontend/src/**/__tests__/` to match repo conventions |
| critical | Backend API contract not specified - unclear if scenario_id is required, how to handle legacy requests | Added explicit API contract specification in task 20.6.6 with transitional validation |
| critical | ResultStore migration strategy not specified | Added detailed migration specification with one-time migration script approach and rollback strategy |
| high | Dimension-based filtering UI not defined | Added DimensionFilter interface and filter bar component specification |
| high | Portfolio composition hash algorithm undefined | Added explicit hash algorithm using SHA-256 with sorted policies for order-independence |
| high | Cell context menu implementation not specified | Added CellContextMenuAction interface with action definitions (view, clone, delete, export, retry) |
| high | Export lineage embedding format not specified for CSV/Parquet | Added explicit format specifications for CSV (lineage columns), Parquet (metadata), and replication package (scenario.yaml) |
| high | Matrix refresh trigger events undefined | Added explicit refresh triggers: on mount, after runs, on window focus, periodic 30s for multi-user scenarios |
| high | Legacy run display format not specified | Added explicit UI specification for legacy runs with "Unknown Scenario (Legacy)" badge and behavior rules |
| high | Empty state designs not specified | Added three empty state specifications (no scenarios, no populations, no executions) with actions |
| high | Dimension registry contract lacks conflict rules, lifecycle | Added complete registry API specification with register, unregister, duplicate-id behavior |
| high | Multiple runs per scenario-population pair not handled | Added deterministic rule: "latest completed run" with optional run history drawer |
| medium | Scenario context error handling pattern undefined | Added ScenarioContextError interface with recoverable flag and snapshot for retry |
| medium | Matrix responsive behavior not specified | Added breakpoint specification (< 1200px horizontal scroll, >= 1200px sticky first column) |
| medium | Comparison scenario card design not specified | Added ScenarioCard component specification with compact/full variants |
| medium | "Different Populations" warning behavior undefined | Added validation warning specification with allowProceed flag |
| medium | Naming inconsistency (comparisonDimension vs ComparisonDimension) | Normalized to `ComparisonDimension` throughout story |
| medium | Scenario-by-population matrix layout contradicts UX spec | Aligned matrix specification with UX Stage 4 model from ux-design-specification.md |
| low | Export filename convention not specified | Added getExportFilename specification with pattern for each export type |
| low | Cell tooltip content not defined | Added CellTooltip specification with status-based content |
| low | Matrix filter persistence not specified | Added localStorage persistence specification with clear/reset behavior |
| low | Typo in test example ("perserves") | Corrected to "preserves" |
| dismissed | Backend API contract - RunRequest.scenario_id already exists in backend (no change needed) | FALSE POSITIVE: Valid concern - scenario_id exists but is optional; added specification for making it required with transitional validation |
| dismissed | WorkspaceScenario reference wrong location | FALSE POSITIVE: Partially valid - WorkspaceScenario is indeed defined in workspace.ts but also exported via types.ts for API consumers; kept types.ts reference for API layer consistency |
| dismissed | Matrix data-source instruction incorrectly suggests frontend can use ResultStore.list_results() directly | FALSE POSITIVE: Valid concern - clarified that matrix should populate via API endpoint (/api/results), not direct backend access |
| dismissed | Verbose "Architecture Constraints" repetition | FALSE POSITIVE: Content is concise and necessary; cross-reference with project context is appropriate for standalone story files |
| dismissed | INVEST criteria failures | FALSE POSITIVE: Story complexity is inherent to cross-cutting refactor; points adjusted to 13 SP which is more realistic |
| dismissed | Dependency risk - Story 20.5 has open AI-review follow-ups | FALSE POSITIVE: Valid risk but not a story defect; added dependency note to Dev Agent Record |
| dismissed | Backward compatibility break risk from strict validation | FALSE POSITIVE: Addressed by adding transitional validation with infer-from-legacy fallback instead of strict rejection |
