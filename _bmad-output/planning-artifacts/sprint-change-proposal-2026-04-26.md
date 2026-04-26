---
title: Sprint Change Proposal — Workspace UX Stabilization, Deferred-Work Sweep, and Investment-Decisions Architecture
date: 2026-04-26
author: Lucas Vivier (with bmad-correct-course)
project: ReformLab
status: draft (rev 2 — after user audit ask + deferred-work sweep)
related_epics:
  - EPIC-25 (Stage 1 Policies Redesign — done)
  - EPIC-26 (Five-Stage Workspace Migration — story 26.7 in review)
proposed_epics:
  - EPIC-27 (Workspace UX Stabilization)
  - EPIC-28 (Investment Decisions — Technology-Set as a First-Class Concept)
  - EPIC-29 (OpenFisca Variable Coverage and Live-Output Recovery)
trigger:
  - User-reported defects on Policies, Population, Investment Decisions, nav rail, and help popovers
  - User-requested broader frontend audit for readability, redundancy, and consistency
  - Inventory of `_bmad-output/implementation-artifacts/deferred-work.md` and related artifacts
  - User instruction: technology-set architecture work goes in its own epic, not a spike
user_decisions_recorded:
  - 1. Demo no longer pre-selects population — confirmed
  - 2. Toast policy — silence passive autoload failures, keep toasts for explicit user actions (confirmed; saved as feedback memory)
  - 3. Technology-set work — promoted from spike to dedicated EPIC-28 (confirmed)
---

# Sprint Change Proposal — 2026-04-26 (rev 2)

## Section 1 — Issue Summary

After Epics 25 and 26 closed, hands-on use of the workspace surfaced three layers of problems:

1. **Concrete defects and IA gaps** on Policies, Population, Investment Decisions, the nav rail, and the help popover (issues 1–11 in rev 1).
2. **Polish-grade readability and redundancy** issues across all stages, identified by a follow-up frontend audit (run via three parallel review agents covering editorial / IA, code-level redundancy, and Stage 4–5).
3. **Deferred work that already has owners** in `_bmad-output/implementation-artifacts/deferred-work.md`, in story-26.7 review patches, in code-review antipatterns docs, and in source TODOs.

In addition, the user has explicitly asked to:
- Make the technology-set / population-coupling conversation for Investment Decisions a real epic, not a spike.
- Roll the deferred-work backlog into the new epics so it stops drifting.

---

## Section 2 — Impact Analysis

### Epic Impact

| Epic | Status | Impact |
|------|--------|--------|
| EPIC-25 | done | Issues live in EPIC-25 surfaces but do not invalidate ACs; handled in EPIC-27. |
| EPIC-26 | story 26.7 in review | Outstanding 26.7 review patches are folded into EPIC-27 story 27.0 (close-out). Subsequent issues are EPIC-27 work. |
| **EPIC-27 (new)** Workspace UX Stabilization | proposed | Bundles all UX defects, audit polish items, and Stage 4–5 fixes. |
| **EPIC-28 (new)** Investment Decisions — Technology-Set as a First-Class Concept | proposed | Adapter contract, EngineConfig schema, population schema, choice-result writeback, wizard UI for technology selection. Architecture-grade work. |
| **EPIC-29 (new)** OpenFisca Variable Coverage and Live-Output Recovery | proposed | Restores the eight French-named output variables that the 2026-04-26 hotfix narrowed in `_DEFAULT_LIVE_OUTPUT_VARIABLES`; sweeps test fixtures off generic names. Pure backend. Independent from EPIC-27/28. |

### Story Impact

- 26.7 outstanding review patches → folded into a small EPIC-27 close-out story (27.0).
- 9 base UX stories under EPIC-27 from rev 1.
- **+5 audit-driven stories** added to EPIC-27 (rev 2), covering Stage 4–5 polish and cross-cutting code consolidation.
- **+1 frontend cleanup story** under EPIC-27 absorbing the four deferred-work items that touch frontend (circular-import risk, error-badge variant, AC-3 prose collapse, auto-name effect dep).
- **+5 backend stories** under EPIC-29 covering custom variables, mapping renames, and test-fixture sweeps.
- EPIC-28 sized as 5 stories (architecture, schema, adapter, UI, regression).

### Artifact Conflicts

- **PRD**: no conflict for EPIC-27, EPIC-29. EPIC-28 introduces FR additions: (a) technology-set as a scenario input, (b) population can carry incumbent-technology columns, (c) decisions produce population state transitions for multi-period runs. PM should review and either add explicit FRs or extend FR43/FR46 wording.
- **Architecture**: EPIC-28 changes the `ComputationAdapter` contract surface, `PopulationData` schema, and the orchestrator's multi-period contract — **architect agent must own**.
- **UX Spec (Revision 4.1)**: needs additions for "not started" nav state, Population IA reconciliation, clickable wizard steps, sub-view breadcrumbs in Stage 5, semantic comparison palette, and (for EPIC-28) a technology-selection step in the wizard.
- **`epics.md`**: append EPIC-27, EPIC-28, EPIC-29 entries; mark EPIC-26 done after story 26.7 closes.
- **`sprint-status.yaml`**: add EPIC-27 stories with status `backlog`; EPIC-28 and EPIC-29 entries with status `backlog`.
- **`deferred-work.md`**: every item is now owned by a story below; close out the file with a "migrated to EPIC-27/29" header once stories are created.

### Technical Impact

- **Backend (EPIC-27)**: tiny — single-policy rule fix. (~10 LOC in portfolios.py + tests.)
- **Backend (EPIC-29)**: medium — implementing four custom French variables and renaming/dropping four others, plus a test-fixture sweep. No adapter changes.
- **Backend (EPIC-28)**: significant — adapter contract, population schema migration, choice-result writeback into the population frame, multi-period state transitions. Requires architect spike before stories can be sized concretely.
- **Frontend (EPIC-27)**: medium — many small changes; biggest items are the unified PolicyCard renderer (story 27.4), draft autosave (27.5), nav-rail "not started" state (27.6), Population IA refactor (27.8), formatter consolidation (27.10), and dialog-hooks consolidation (27.11).
- **Frontend (EPIC-28)**: a wizard step + EngineConfig fields; relatively contained once backend lands.
- **CI / determinism / manifests**: EPIC-29 changes manifest contents (richer output set); EPIC-28 changes population provenance and adds technology-set into manifests. Both require manifest version bumps and migration tests.

---

## Section 3 — Recommended Approach

**Selected path:** **Hybrid (Direct Adjustment + three new epics)**

- **Direct adjustment** to land 26.7 review patches and close EPIC-26.
- **Three new epics**, each with focused scope:
  - **EPIC-27** — UX stabilization. One sprint. Mostly bug + small-feature stories. Unblocks day-to-day analyst use.
  - **EPIC-28** — Investment Decisions architecture. Multi-sprint. Architect-owned. Should not block EPIC-27 or EPIC-29.
  - **EPIC-29** — Backend variable coverage. Backend-only. Can run in parallel with EPIC-27.

**Why not other paths:**
- **Rollback** is unwarranted — EPIC-25/26 are correct in intent.
- **MVP review** is unwarranted — no FR/NFR is invalidated.
- **Single mega-epic** would mix architecture-grade work (EPIC-28) with polish (EPIC-27) and pure backend (EPIC-29), making it impossible to ship anything.

**Effort estimate:**
- EPIC-27: ~32 SP across 15 stories. One sprint with focus; two with normal cadence.
- EPIC-28: ~21 SP across 5 stories *after* an architect spike (the spike itself is 3 SP).
- EPIC-29: ~16 SP across 5 stories.

**Risk:** Low for EPIC-27/29 (localised changes). Medium-to-high for EPIC-28 (multi-period state transitions in the orchestrator are touchy).

---

## Section 4 — Detailed Change Proposals

### 4.0 Close out story 26.7

Apply the seven Review:Patch / Review:Decision items from `spec-fix-passive-policy-set-autoload-for-non-portfolio-references.md` lines 78–89:

- `usePortfolioLoadDialog.ts:135-141` — drop `loadedPortfolioRef.current = activeScenarioPortfolioName` in the membership-fail branch (skip-marker leak).
- `PoliciesStageScreen.tsx:555` — wrap `portfolios.map((p) => p.name)` in `useMemo([portfolios])`.
- `PoliciesStageScreen.test.tsx` — add `portfoliosLoading: true → false` rerender test, deferred-autoload test, and `toHaveBeenCalledTimes(1)` assertion on the explicit-failure regression.

The four "Decision" items become EPIC-27 follow-up story 27.13 (AppContext naming-state hardening). After this, mark EPIC-26 done, run epic-26 retrospective addendum.

---

### 4.1 EPIC-27 — Workspace UX Stabilization

**User outcome:** the analyst sees an honest "not started" workspace, can read help popovers, can run a single-policy assessment, gets useful information without expanding cards, never loses unsaved policy-set work, navigates Population and Investment Decisions in the way the UX spec already documents in prose, sees consistent units and labels in Run/Results/Compare, and benefits from a modest code consolidation that makes future polish cheaper.

**Status:** backlog
**PRD refs:** FR43 (clarification: ≥1 policy), UX-DR7, UX-DR9, UX-DR10, UX-DR11, UX-DR12, UX-DR13, UX-DR15
**Builds on:** EPIC-25, EPIC-26
**Toast policy (durable rule):** passive / autoload / restore failures are silent; explicit user-initiated actions (Save, Load click, Run) keep their toasts. Saved to memory as `feedback_error_toasts_user_initiated_only.md`.

#### Story list

| ID | Type | Pri | SP | Title |
|----|------|-----|----|-------|
| 27.0 | Bug | P0 | 2 | Close out story-26.7 review patches and retro EPIC-26 |
| 27.1 | Bug | P0 | 1 | Allow single-policy portfolio runs (drop ≥2 minimum) |
| 27.2 | Bug | P0 | 1 | Fix Popover transparent background (define `--popover` token) |
| 27.3 | Story | P0 | 5 | Show actual parameter values inline in policy cards (collapsed list + click-to-preview) |
| 27.4 | Story | P0 | 3 | Unify template vs from-scratch policy-card visuals (one renderer, "Edit groups" available for both) |
| 27.5 | Story | P0 | 3 | Auto-save policy-set composition draft to localStorage with restore prompt |
| 27.6 | Story | P0 | 3 | Add explicit "not started" nav-rail state and stop demo from pre-satisfying stages |
| 27.7 | Story | P0 | 3 | Make Investment Decisions wizard step labels clickable for back-navigation |
| 27.8 | Story | P1 | 3 | Restructure Population stage as Library-or-Build → Explorer with proper gating |
| 27.9 | Story | P1 | 2 | Improve policy-set auto-name suggestion (semantic ordering, type hints, sensible fallback) |
| 27.10 | Story | P1 | 3 | Consolidate frontend formatters (numbers, currency, dates, timestamps, status variants) |
| 27.11 | Story | P1 | 3 | Consolidate portfolio dialog hooks (save/load/clone) and unify policy types |
| 27.12 | Story | P1 | 3 | Stage 5 polish — sub-view breadcrumb, baseline/reform palette, units on Fiscal/Welfare, run-id width, NaN guards, stale-comparison reset |
| 27.13 | Story | P1 | 2 | AppContext naming-state hardening (deferred review-decisions) |
| 27.14 | Story | P1 | 2 | Frontend cleanup sweep absorbing `deferred-work.md` items (circular-import, error-badge variant, prose-collapse, auto-name dep) |
| 27.15 | Story | P2 | 2 | UX-spec amendments: not-started state, Population IA, clickable wizard steps, Stage 5 breadcrumb |

**Total:** ~38 SP. P0 ≈ 21 SP; P1 ≈ 15 SP; P2 ≈ 2 SP.

#### Story 27.0 — Close out 26.7 review patches

See Section 4.0. Outputs: 26.7 marked done, sprint-status.yaml updated, epic-26 retrospective addendum recorded.

#### Story 27.1 — Allow single-policy portfolio runs

**Files:** [src/reformlab/server/routes/portfolios.py:305-313](src/reformlab/server/routes/portfolios.py#L305-L313), [:415-423](src/reformlab/server/routes/portfolios.py#L415-L423). Drop `< 2` to `< 1`; update copy. Backend test for single-policy build + validate. Verify no symmetric ≥2 guard in frontend.

**AC:** single-policy composition runs end-to-end; empty composition returns 4xx with new message; `composition.py:535+` pairwise loops are no-op for 1 policy (no spurious conflicts).

#### Story 27.2 — Fix Popover transparent background

**Files:** define `--popover` and `--popover-foreground` in `_bmad-output/branding/theme.css` (Tailwind v4 `@theme`); verify resolution in `frontend/src/components/ui/popover.tsx:23` and all consumers.

**AC:** formula-help popover renders opaque, readable background.

#### Story 27.3 — Show actual parameter values in policy cards

**Files:** [frontend/src/components/simulation/PortfolioCompositionPanel.tsx:471-513](frontend/src/components/simulation/PortfolioCompositionPanel.tsx#L471-L513). Replace hardcoded placeholders with live `entry.parameters` values, grouped by parameter-group membership. Collapsed cards show headline values per group (e.g., `Rate schedule → €45/tCO₂ (2025)`) instead of `6 PARAMS`. Group chips become click-to-scroll-to-group.

**AC:** card shows real values per group when collapsed; clicking a chip expands and scrolls to that group; defaults shown when nothing customised; no fake placeholders survive.

#### Story 27.4 — Unify template vs from-scratch policy-card visuals

**Files:** [frontend/src/components/simulation/PortfolioCompositionPanel.tsx:155-531](frontend/src/components/simulation/PortfolioCompositionPanel.tsx#L155-L531). Extract `<PolicyCard>` rendering from `editableParameterGroups` for both sources; lift "Edit groups" affordance for both; ensure template-add path populates `editableParameterGroups`.

**AC:** template and from-scratch cards visually identical; "Edit groups" works the same on both; group edits persist for both (extends 25.4/25.5 reload coverage).

#### Story 27.5 — Auto-save composition draft

New hook `frontend/src/hooks/usePolicySetDraftAutosave.ts`. Debounced 750 ms write to localStorage; on Policies-stage mount, surface a non-blocking banner "You have unsaved changes from {time}. Restore | Discard"; clear draft on explicit Save; optional `beforeunload` warning.

**AC:** edits survive a tab close → reopen via Restore banner; Save clears draft; Discard reverts to loaded state.

#### Story 27.6 — Honest nav-rail state

**Files:** [frontend/src/components/layout/WorkflowNavRail.tsx:43-73, :143-149](frontend/src/components/layout/WorkflowNavRail.tsx#L43); add a fourth state `not-started`, distinct from `incomplete`. [frontend/src/data/demo-scenario.ts:32-55](frontend/src/data/demo-scenario.ts#L32-L55) — remove `populationIds: [DEMO_POPULATION_ID]`; set `investmentDecisionsEnabled: null` (was `false`). [frontend/src/types/workspace.ts](frontend/src/types/workspace.ts) — extend `EngineConfig.investmentDecisionsEnabled` to `boolean | null`. Update UX spec status table.

**AC:** brand-new workspace shows no green stages; selecting a population turns Population green only; explicit "Skip" on Investment Decisions turns Stage 3 green; legacy `false` migrates to explicit-skip.

#### Story 27.7 — Clickable wizard steps

**Files:** [frontend/src/components/engine/InvestmentDecisionsWizard.tsx:152-199](frontend/src/components/engine/InvestmentDecisionsWizard.tsx#L152-L199). Wrap each step indicator in a `<button onClick={() => goToStep(step)} disabled={!visited}>`. Free backward navigation; forward jumps disabled until reached.

**AC:** clicking "Model" from Review navigates back; unreached steps are visibly disabled.

#### Story 27.8 — Population stage information architecture

**Files:** [frontend/src/types/workspace.ts:33-37](frontend/src/types/workspace.ts#L33-L37) — collapse `POPULATION_SUB_STEPS` to a sequenced model: `source` (Library or Build inside the screen) → `inspect` (Explorer, gated by selected population). [frontend/src/components/screens/PopulationStageScreen.tsx:282-318](frontend/src/components/screens/PopulationStageScreen.tsx#L282-L318) — gate Explorer until `selectedPopulationId` is set; tooltip on the disabled tab. [frontend/src/components/layout/WorkflowNavRail.tsx:228-294](frontend/src/components/layout/WorkflowNavRail.tsx#L228-L294) — show two sub-steps. Reconcile UX spec prose vs implementation.

**AC:** Explorer disabled until a population exists; choosing Build → Generate-and-Use selects the population and unlocks Explorer; legacy `population-explorer` sub-view migrates correctly.

#### Story 27.9 — Better policy-set auto-name suggestions

**Files:** [frontend/src/utils/naming.ts:84-125](frontend/src/utils/naming.ts#L84-L125). Replace `slug-plus-N-more` with a semantic algorithm: sort by type (tax → subsidy → transfer), take first 2-3 categories, fall back to type counts only when categories overlap. Manual-edit freeze rule (Story 25.5) still holds.

#### Story 27.10 — Consolidate formatters

Extract `frontend/src/utils/formatters.ts` exporting `formatNumber`, `formatCurrency`, `formatPercent`, `formatRunTimestamp(style: "short" | "full")`, `formatDate`. Replace ≥42 `.toLocaleString()` call sites and three duplicate `statusVariant()` functions ([ResultsListPanel.tsx:19-23](frontend/src/components/simulation/ResultsListPanel.tsx#L19-L23), [ResultDetailView.tsx:55-59](frontend/src/components/simulation/ResultDetailView.tsx#L55-L59), [comparison-helpers.ts:50-56](frontend/src/components/comparison/comparison-helpers.ts#L50-L56)). Standardise icons and loading states (Skeleton vs spinner vs text).

**AC:** all numeric/currency/timestamp/status values pass through the new helpers; no inline `.toLocaleString` in components after the sweep; existing tests pass.

#### Story 27.11 — Consolidate dialog hooks and policy types

Merge `usePortfolioSaveDialog`, `usePortfolioLoadDialog`, `usePortfolioCloneDialog` into a single `usePortfolioDialog({ mode: "save" | "load" | "clone" })`. Unify `CompositionEntry` and `PortfolioPolicyItem` types — keep `PortfolioPolicy` as the canonical shape and `CompositionEntry extends PortfolioPolicy`. Remove deprecated `useScenarioPersistence` hook export.

**AC:** all three dialogs work identically; ~250 LOC removed; type unification surfaces no regressions in PoliciesStageScreen tests.

#### Story 27.12 — Stage 5 polish

Six sub-tasks bundled because each is small:
- Add a sub-view breadcrumb header in [App.tsx:162-221](frontend/src/App.tsx#L162-L221) showing `Results > Overview / Runner / Comparison / Decisions / Manifest`.
- Use a semantic baseline/reform palette in [ComparisonDashboardScreen.tsx](frontend/src/components/screens/ComparisonDashboardScreen.tsx) (darker baseline, accent reforms; reuse the existing `--chart-baseline` / `--chart-reform-*` tokens from CLAUDE memory).
- Add unit labels and `formatLargeNumber()` to Fiscal and Welfare tables.
- Widen run-id displays from 8 chars to ≥12 chars in `ResultsListPanel`, `RunSelector`, `RunManifestViewer`; add copy-to-clipboard.
- Guard NaN/Infinity in `CrossMetricPanel`, `MultiRunChart`.
- Reset `selectedRunIds` and `comparisonData` in `ComparisonDashboardScreen` when `activeScenario.id` changes.
- Show "N runs completed, M failed" summary in Comparison so users understand why some runs are excluded.
- Add immediate skeleton on the Detail tab so it doesn't appear to hang.

**AC:** each sub-task has a focused test; visual regression on the comparison palette is approved by the user before merge.

#### Story 27.13 — AppContext naming hardening

Carries the four "Decision" items from `spec-fix-passive-policy-set-autoload-for-non-portfolio-references.md` lines 82–85: reset `selectedPortfolioName` on `createScenario`/`cloneScenario`; invalidate loaded-name guard on direct field mutation; handle empty `populationIds` correctly during restore; tighten the auto-name effect dep array.

**AC:** integration tests cover create-then-edit, clone-then-edit, restore-with-empty-populations, and direct-mutation flows.

#### Story 27.14 — Frontend cleanup sweep absorbing `deferred-work.md`

- Move `CompositionEntry` from `PortfolioCompositionPanel` to `api/types.ts` (circular-import risk). [deferred-work.md:3](_bmad-output/implementation-artifacts/deferred-work.md#L3)
- Replace `variant="default"` + `bg-red-500` in [PortfolioCompositionPanel.tsx:786](frontend/src/components/simulation/PortfolioCompositionPanel.tsx#L786) with a real `destructive` variant.
- Collapse the AC-3 warning text in [PoliciesStageScreen.tsx:760-776](frontend/src/components/screens/PoliciesStageScreen.tsx#L760-L776) to a single `<p>` if/when strict-match grading is required (otherwise leave with a comment).
- Tighten the auto-name effect dep array in [AppContext.tsx:550-560](frontend/src/contexts/AppContext.tsx#L550-L560) (functional setter or name-ref) so `activeScenarioName` doesn't need to be a dep.

#### Story 27.15 — UX-spec amendments

Update [_bmad-output/planning-artifacts/ux-design-specification.md](_bmad-output/planning-artifacts/ux-design-specification.md) to reflect: not-started nav-rail state, Population IA reconciliation (Library/Build → Inspect), clickable wizard steps, Stage 5 sub-view breadcrumb, semantic comparison palette, popover background tokens.

---

### 4.2 EPIC-28 — Investment Decisions: Technology-Set as a First-Class Concept

**User outcome:** the analyst can declare which technologies are in scope for an investment decision, the population carries an incumbent technology per household, the discrete-choice step writes chosen technologies back into the population, and multi-period runs reflect technology transitions.

**Status:** backlog (gated on architect spike — see Story 28.0)
**PRD refs:** likely new FRs around technology-set, population-state transitions, and multi-period semantics. PM owns the FR additions before sizing 28.2–28.5.
**Builds on:** EPIC-23 (live runtime), EPIC-26 (Investment Decisions stage), and the existing `src/reformlab/discrete_choice/` module (`Alternative`, `ChoiceSet`, `DiscreteChoiceStep`).

#### Story list

| ID | Type | Pri | SP | Title |
|----|------|-----|----|-------|
| 28.0 | Spike | P0 | 3 | Architect spike — technology-set contract and population state-transition model |
| 28.1 | Story | P0 | 5 | Add `technology_set` to `EngineConfig`; expose API and persistence |
| 28.2 | Story | P0 | 5 | Extend `PopulationData` schema with optional incumbent-technology columns; migration + manifest provenance |
| 28.3 | Story | P0 | 5 | Wire `DiscreteChoiceStep` outputs back into the population frame as state transitions; orchestrator multi-period contract |
| 28.4 | Story | P0 | 3 | Investment Decisions wizard — Technology step (between Enable and Model); reactive defaults from population |
| 28.5 | Story | P1 | 3 | Regression and analyst-journey coverage for multi-period decisions runs |

#### Story 28.0 — Architect spike

Deliverable: `_bmad-output/planning-artifacts/spike-investment-decisions-technology-set.md` answering:
- What does `EngineConfig.technology_set` look like (per-domain list of alternative ids, taste-overrides, default?)?
- What's the population schema delta — one column per domain (`incumbent_heating`, `incumbent_vehicle`) or a single keyed map?
- How does `DiscreteChoiceStep` write back? In-place mutation? Returns a new population frame? How does the orchestrator chain it across periods?
- Manifest impact — what new provenance fields must record the technology-set version?
- Backward compatibility — populations without incumbent columns must still run scenarios that don't enable decisions.
- Adapter contract — does the `ComputationAdapter` interface change, or does the change live entirely above it?

Owner: architect agent. Output: ADR + sized stories 28.1–28.5.

#### Stories 28.1–28.5

Sized concretely after 28.0 lands. Sketch:
- 28.1 — `technology_set: TechnologySet | None` in `EngineConfig`; FastAPI endpoint to list alternatives by domain; persistence and manifest fields.
- 28.2 — population schema accepts optional `incumbent_*` columns; PyArrow validation; backward-compat path for populations without columns; manifest provenance for the technology version.
- 28.3 — `DiscreteChoiceStep` writes a transition record (household_id, period, from_tech, to_tech) and emits an updated population; orchestrator threads the updated population to subsequent periods.
- 28.4 — wizard step UI: pick domain, pick alternatives, default from population's incumbent column; surface "no incumbent column" warning instead of a silent assumption.
- 28.5 — analyst-journey test through a multi-period heating scenario showing transition counts in results; manifest version bump tested.

---

### 4.3 EPIC-29 — OpenFisca Variable Coverage and Live-Output Recovery

**User outcome:** the live OpenFisca path produces the full set of policy-relevant outputs (subsidies, malus, energy aid, French income variables) instead of the four currently-resolvable variables, and the test suite stops encoding the generic-name placeholders that blew up production on 2026-04-26.

**Status:** backlog
**PRD refs:** indirect support for FR43, FR46 (richer policy outputs) and NFR9 (manifest fidelity).
**Builds on:** EPIC-23 (live OpenFisca default) and the 2026-04-26 hotfix that narrowed `_DEFAULT_LIVE_OUTPUT_VARIABLES`.
**Driving artifact:** [_bmad-output/implementation-artifacts/deferred-work.md:19-25](_bmad-output/implementation-artifacts/deferred-work.md#L19-L25)

#### Story list

| ID | Type | Pri | SP | Title |
|----|------|-----|----|-------|
| 29.1 | Story | P0 | 5 | Implement custom OpenFisca variables `subsidy_amount`, `subsidy_eligible`, `vehicle_malus`, `energy_poverty_aid` in a registered TaxBenefitSystem extension |
| 29.2 | Story | P0 | 3 | Resolve generic-name placeholders: `irpp` → `impot_revenu_restant_a_payer`, `revenu_net` → drop, `revenu_brut` → custom or composition, `taxe_carbone` → custom |
| 29.3 | Story | P0 | 2 | Restore the resolved names in `_DEFAULT_LIVE_OUTPUT_VARIABLES` ([result_normalizer.py:71-76](src/reformlab/computation/result_normalizer.py#L71-L76)) |
| 29.4 | Story | P1 | 3 | Sweep test fixtures off the generic names ([test_result_normalizer.py:148-149](tests/computation/test_result_normalizer.py#L148-L149); test_normalization_regression.py; test_openfisca_api_adapter.py; [test_panel.py:518](tests/orchestrator/test_panel.py#L518)) |
| 29.5 | Story | P1 | 3 | Add regression tests for `pa.concat_tables()` schema-mismatch paths in [src/reformlab/orchestrator/panel.py](src/reformlab/orchestrator/panel.py) (deferred from 2026-04-19) |

**Note:** Story 24.2's incompleteness is the parent of 29.1–29.3. Tag those stories with `parent: epic-24-followup` so the trail is visible. Confirm with PM whether `cheque_energie` (already in core) covers the energy-poverty-aid case before implementing a custom variable.

---

## Section 5 — Implementation Handoff

**Scope classification:** **Major** (now). With three new epics and one of them touching the adapter contract, this proposal is no longer "moderate". PM and architect must approve EPIC-28 scope before stories beyond 28.0 are written.

**Handoff plan:**

| Item | Recipient | Deliverable |
|------|-----------|-------------|
| 26.7 close-out (story 27.0) | Developer agent (`bmad-dev`) | Land seven review patches; mark 26.7 done; epic-26 retro addendum |
| EPIC-27 stories 27.1–27.15 | Story-creator (`bmad-create-story`) then dev agent | Story files; implementation P0 first; quality-gate per CLAUDE memory |
| EPIC-28 spike 28.0 | Architect agent (`bmad-architect`) | Spike doc + sized stories 28.1–28.5; PM review for FR additions |
| EPIC-28 stories 28.1–28.5 | Architect (oversight) + dev agent | Adapter / schema / orchestrator / wizard / regression coverage |
| EPIC-29 stories 29.1–29.5 | Dev agent + analyst review on `cheque_energie` decision | Custom OpenFisca variables, fixture sweep, schema-mismatch tests |
| `epics.md`, `sprint-status.yaml`, `deferred-work.md` close-out | Tech writer (`bmad-tech-writer`) | Append EPIC-27/28/29; mark deferred items "migrated to {story-id}" |
| UX spec amendments (story 27.15) | Tech writer + UX designer (`bmad-ux-designer`) | Specifications update for not-started nav, Population IA, clickable wizard, Stage 5 breadcrumb, popover tokens |
| FR additions for EPIC-28 | Product manager (`bmad-pm`) | New FRs in PRD around technology-set, population state transitions, multi-period semantics |

**Success criteria:**

- **EPIC-27 done:** no spurious toasts, single-policy runs work, popovers readable, policy cards informative, autosave in place, nav rail honest, Stages 4–5 polished, code consolidated. All quality gates green.
- **EPIC-28 done:** an analyst configures a heating scenario over 5 years with EV/heat-pump/gas alternatives, sees transition counts in results, and the manifest captures the technology-set version. Backward compat verified for scenarios that don't enable decisions.
- **EPIC-29 done:** live OpenFisca runs produce all policy-relevant outputs; no test fixture references generic names; `_DEFAULT_LIVE_OUTPUT_VARIABLES` is back to its full intended set.

---

## Section 6 — Decisions Recorded

The three rev-1 questions have been answered:

1. **Demo no longer pre-selects population.** First launch lands on Policies with everything cleanly "not started". The Quick Test Population stays available but the user must select it. Implemented in story 27.6.
2. **Toast policy.** Passive autoload / restore failures are silent. Explicit user-initiated actions keep their toasts. Saved to memory as `feedback_error_toasts_user_initiated_only.md`.
3. **Technology-set work** is its own dedicated EPIC-28, not a spike — gated on an architect spike (story 28.0) before 28.1–28.5 are sized.

---

## Section 7 — Sources Folded Into This Proposal

- User reports (2026-04-26, three messages with screenshots)
- `_bmad-output/implementation-artifacts/spec-fix-passive-policy-set-autoload-for-non-portfolio-references.md` (review section, lines 78–89)
- `_bmad-output/implementation-artifacts/spec-establish-appcontext-integration-testing.md` (status: done; informs 27.13)
- `_bmad-output/implementation-artifacts/deferred-work.md` (every item assigned to 27.14, 29.1–29.5)
- `_bmad-output/implementation-artifacts/retrospectives/epic-26-retro-20260422.md` ("AppContext integration testing remains underdeveloped" → 27.13)
- `_bmad-output/implementation-artifacts/antipatterns/epic-26-code-antipatterns.md` (informs 27.10/27.11 cleanup)
- Frontend audit run today via three parallel review agents (editorial/IA, code-redundancy, Stage 4–5 coverage)
- `src/reformlab/discrete_choice/` module read for EPIC-28 sizing
- `_bmad-output/planning-artifacts/{prd.md, architecture.md, ux-design-specification.md, epics.md}`

Once approved, story files for EPIC-27 (15 stories) will be drafted in priority order, EPIC-28 begins with the architect spike (28.0), and EPIC-29 stories can run in parallel.
