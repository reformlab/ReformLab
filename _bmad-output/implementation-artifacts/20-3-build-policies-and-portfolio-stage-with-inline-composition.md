# Story 20.3: Build Policies & Portfolio stage with inline composition

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want to browse policy templates, compose a portfolio inline with parameter editing and conflict resolution, and save/load/clone portfolios independently of my scenario,
so that I can rapidly build and iterate on reusable policy bundles without confusing them with scenario operations.

## Acceptance Criteria

1. **AC-1: Inline template browsing and portfolio composition** — Given Stage 1 (Policies & Portfolio) is open, when the user views the screen, then the template browser and portfolio composition panel are visible simultaneously on a single page (no multi-step wizard), allowing the user to add templates, edit parameters, and configure rate schedules without navigating between steps.
2. **AC-2: Single-policy portfolio support** — Given the user adds exactly one policy template, when the composition is viewed, then it is treated as a valid portfolio of one (no "minimum 2 policies" constraint) and can be saved, used for execution, and linked to a scenario.
3. **AC-3: Inline conflict detection and resolution** — Given a portfolio with two or more policies, when policies share overlapping parameters, then conflicts are detected automatically (on composition change, debounced), displayed as inline amber warnings, and resolvable via a resolution strategy selector without leaving Stage 1.
4. **AC-4: Portfolio operations independent of scenario** — Given portfolio save/load/clone actions, when the user performs any of these, then they operate on the portfolio entity only (via `/api/portfolios` endpoints), not on the scenario. Saving a portfolio does not save the scenario. Cloning a portfolio does not clone the scenario. The portfolio name is stored on `activeScenario.portfolioName` as a reference, not a deep copy.
5. **AC-5: Scenario integration** — Given the user saves or loads a portfolio, when the operation completes, then `activeScenario.portfolioName` is updated to reflect the active portfolio, and the nav rail Policies stage shows a completion checkmark. Clearing the composition sets `activeScenario.portfolioName` to `null`.
6. **AC-6: Portfolio validity indicator** — Given the user has composed a portfolio, when the portfolio is valid (all required parameters filled, ranges valid, conflicts resolved or strategy chosen), then a green checkmark is shown. When invalid, validation errors are surfaced inline.

## Tasks / Subtasks

- [ ] Task 1: Refactor PoliciesStageScreen to inline composition layout (AC: #1)
  - [ ] 1.1: Replace the thin wrapper in `PoliciesStageScreen.tsx` with a new single-page layout that renders `PortfolioTemplateBrowser` and `PortfolioCompositionPanel` side-by-side (template browser on the left, composition on the right). Use a responsive CSS grid: `grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]`.
  - [ ] 1.2: Move all portfolio composition state currently inside `PortfolioDesignerScreen` (selectedTemplateIds, composition, resolutionStrategy, conflicts, etc.) into `PoliciesStageScreen` so it can coordinate both panels and the toolbar.
  - [ ] 1.3: Add a top toolbar row within the stage screen containing: portfolio name display (if saved), Save button, Load button, Clone button, Clear button, and the conflict resolution strategy selector. All controls are always visible — no "review step" required.
  - [ ] 1.4: Remove the `WorkbenchStepper` usage from the policies stage flow. The stepper stays in the codebase (used by DataFusionWorkbench) but is no longer used in Stage 1.
  - [ ] 1.5: Keep `PortfolioDesignerScreen.tsx` in the codebase (it is a standalone component with tests) but add a `@deprecated` JSDoc tag. `PoliciesStageScreen` is the new canonical Stage 1 screen.
- [ ] Task 2: Allow single-policy portfolios (AC: #2)
  - [ ] 2.1: In `PoliciesStageScreen`, remove the `composition.length < 2` guard from the Save button's disabled state. The new constraint is `composition.length >= 1`.
  - [ ] 2.2: In the inline composition area, remove the "Add at least 2 policies" amber warning. Replace with "Add at least 1 policy template to compose a portfolio." when composition is empty.
  - [ ] 2.3: When calling `createPortfolio` API, single-policy payloads are valid — the backend already accepts `policies` arrays of length 1. No backend change needed.
  - [ ] 2.4: Update `validatePortfolio` call to skip validation when `composition.length < 2` (no conflicts possible with a single policy) — already handled by existing `runValidation` early return, but verify the condition is `< 2` not `< 1`.
- [ ] Task 3: Wire portfolio to activeScenario (AC: #4, #5)
  - [ ] 3.1: In `PoliciesStageScreen`, import `useAppState()` and destructure `activeScenario`, `updateScenarioField`, `portfolios`, `refetchPortfolios`.
  - [ ] 3.2: After successful portfolio save (`createPortfolio` succeeds), call `updateScenarioField("portfolioName", portfolioName)` to set the portfolio reference on the active scenario.
  - [ ] 3.3: After successful portfolio load (`getPortfolio` succeeds), call `updateScenarioField("portfolioName", portfolioName)` to update the active scenario reference.
  - [ ] 3.4: On "Clear" action (clear all composition), call `updateScenarioField("portfolioName", null)`.
  - [ ] 3.5: When the screen mounts with `activeScenario?.portfolioName !== null`, auto-load that portfolio into the composition panel by calling `getPortfolio(activeScenario.portfolioName)` and mapping the response to `CompositionEntry[]`. If the load fails (portfolio deleted or API down), show a toast warning and leave composition empty — do NOT crash. Guard with a `useEffect` that runs when `activeScenario?.portfolioName` changes but only when the composition is empty (avoid re-loading on every portfolio save).
  - [ ] 3.6: Also sync legacy state: after portfolio save/load, set `selectedPortfolioName` via `setSelectedPortfolioName(portfolioName)` from AppContext so that SimulationRunnerScreen (Stage 4) can reference the portfolio. On clear, set `setSelectedPortfolioName(null)`.
- [ ] Task 4: Update nav rail completion logic (AC: #5, #6)
  - [ ] 4.1: In `WorkflowNavRail.tsx`, change the `"policies"` completion check from `portfolios.length > 0` to `activeScenario?.portfolioName !== null || composition.length > 0`. Since `WorkflowNavRail` doesn't have access to composition state directly, use `activeScenario?.portfolioName !== null` as the proxy — this is set when a portfolio is saved (Task 3.2) and cleared on Clear (Task 3.4).
  - [ ] 4.2: Update the `"policies"` summary line from the portfolio count to the active portfolio name: `activeScenario?.portfolioName ?? null`.
- [ ] Task 5: Inline conflict detection with debounce (AC: #3)
  - [ ] 5.1: In `PoliciesStageScreen`, implement debounced validation: when `composition` or `resolutionStrategy` changes and `composition.length >= 2`, run `validatePortfolio` after a 500ms debounce. Use a `useRef` for the timeout ID and clear on unmount.
  - [ ] 5.2: Display conflicts inline between the toolbar and composition panel (above the composition list). Reuse the existing `ConflictList` component from `PortfolioDesignerScreen` — extract it to a shared file `frontend/src/components/simulation/ConflictList.tsx` or inline it in PoliciesStageScreen.
  - [ ] 5.3: Show a validity status indicator: green `CheckCircle2` icon in the toolbar when `composition.length >= 1 && conflicts.length === 0 && (composition.length < 2 || resolutionStrategy !== "error")`, amber `AlertTriangle` when conflicts exist.
- [ ] Task 6: Portfolio save/load/clone/clear actions (AC: #4)
  - [ ] 6.1: **Save:** Opens an inline save dialog (fixed-position overlay, same pattern as `ScenarioEntryDialog`). Fields: portfolio name (slug validation), description. On save: calls `createPortfolio`, then `refetchPortfolios()`, then `updateScenarioField("portfolioName", name)`. Close dialog on success.
  - [ ] 6.2: **Load:** Opens an inline overlay listing `savedPortfolios` (from AppContext `portfolios`). Each row shows portfolio name, policy count badge, description. Click loads the portfolio into the composition panel and sets `activeScenario.portfolioName`.
  - [ ] 6.3: **Clone:** Opens an inline overlay with a new-name input. Calls `clonePortfolio` API, then `refetchPortfolios()`. Does NOT change `activeScenario.portfolioName` (the clone is a new portfolio, not the active one).
  - [ ] 6.4: **Clear:** Resets composition to `[]`, selectedTemplateIds to `[]`, conflicts to `[]`, sets `activeScenario.portfolioName` to null and `selectedPortfolioName` to null. No confirmation dialog needed (the action is easily undone by re-loading from saved list).
- [ ] Task 7: Update help content (AC: #1)
  - [ ] 7.1: Update `"policies"` entry in `help-content.ts` to describe inline composition layout, single-policy portfolios, and conflict resolution.
  - [ ] 7.2: Replace `"portfolio"` entry tips (currently references the 3-step designer) with updated tips matching the new inline layout.
- [ ] Task 8: Add tests (AC: all)
  - [ ] 8.1: Create `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` with tests for:
    - Template browser and composition panel render simultaneously (AC-1)
    - Adding a single template enables Save button (AC-2)
    - Conflict detection triggers on composition change (AC-3)
    - Portfolio save updates `activeScenario.portfolioName` (AC-4, AC-5)
    - Portfolio load populates composition and updates scenario (AC-5)
    - Clear resets composition and nulls `activeScenario.portfolioName` (AC-4, AC-5)
    - Validity indicator shows green/amber appropriately (AC-6)
  - [ ] 8.2: Add a Story 20.3 section to `frontend/src/__tests__/workflows/analyst-journey.test.tsx` with:
    - Navigate to `#policies`, verify template browser and composition visible
    - Compose a portfolio (add template, save), verify nav rail shows completion
    - Portfolio operations don't trigger scenario save
  - [ ] 8.3: Verify existing tests still pass — no regressions in:
    - `PortfolioTemplateBrowser.test.tsx` (unchanged component)
    - `PortfolioCompositionPanel.test.tsx` (unchanged component)
    - `YearScheduleEditor.test.tsx` (unchanged component)
    - `PortfolioDesignerScreen` tests (component deprecated but not deleted)
- [ ] Task 9: Run quality gates (AC: all)
  - [ ] 9.1: `npm run typecheck` — 0 errors
  - [ ] 9.2: `npm run lint` — 0 errors (pre-existing fast-refresh warnings OK)
  - [ ] 9.3: `npm test` — all tests pass, 0 failures, 0 regressions
  - [ ] 9.4: `uv run ruff check src/ tests/` — 0 errors
  - [ ] 9.5: `uv run mypy src/` — passes

## Dev Notes

### Architecture Constraints

- **No backend changes in this story.** All portfolio API endpoints (`/api/portfolios`, `/api/portfolios/{name}`, `/api/portfolios/validate`, etc.) already exist and support single-policy portfolios. This is a frontend-only story.
- **No router library.** Continue using hash-based routing via `window.location.hash`. Stage 1 is `#policies`.
- **Dual state model persists.** `activeScenario.portfolioName` (new canonical) coexists with `selectedPortfolioName` (legacy). This story sets both on portfolio save/load/clear. Full migration to `activeScenario`-only is deferred to stories 20.5–20.6.
- **Dialog/Sheet stubs.** shadcn `Dialog` component only exports `Dialog` (no `DialogContent`/`DialogHeader`/`DialogTitle`). Use the inline fixed-overlay pattern established in `ScenarioEntryDialog.tsx` and `PortfolioDesignerScreen.tsx`.
- **Portfolio ≠ Scenario.** Portfolio save/load/clone call `/api/portfolios` endpoints. Scenario save/clone call `/api/scenarios` endpoints and are wired through `AppContext` actions (`saveCurrentScenario`, `cloneCurrentScenario`). These must remain separate.
- **Immutable scenario updates.** `WorkspaceScenario` is treated as immutable — update via `updateScenarioField()` which internally does `{ ...current, [field]: value }`.

### Key Design Decision: Inline Layout

The UX specification (§ Stage 1: POLICIES & PORTFOLIO, lines 1366–1396) explicitly requires:
- "Portfolio Composition (inline, not a separate screen)"
- "Policy parameters live with their policy — Expanding a policy card reveals parameter editors"
- "Single policy = portfolio of one — UI doesn't distinguish internally"

The current `PortfolioDesignerScreen` uses a 3-step `WorkbenchStepper` pattern (Select → Compose → Review). This story replaces that flow within `PoliciesStageScreen` with a single-page layout:

```
┌────────────────────────────────────────────────────┐
│ Toolbar: [name] [Save] [Load] [Clone] [Clear] ✓/⚠ │
│ Conflict Resolution: [strategy dropdown]           │
├──────────────────┬─────────────────────────────────┤
│ Template Browser │ Portfolio Composition            │
│ ┌──────────────┐ │ ┌─────────────────────────────┐ │
│ │ Search...    │ │ │ 1. Carbon Tax — Flat Rate    │ │
│ ├──────────────┤ │ │    [▶ expand] [↑] [↓] [✕]   │ │
│ │ CARBON TAX   │ │ ├─────────────────────────────┤ │
│ │ ☐ Flat Rate  │ │ │ 2. Energy Efficiency Subsidy│ │
│ │ ☑ Dividend   │ │ │    [▼ expand] [↑] [↓] [✕]   │ │
│ │              │ │ │   Rate Schedule: [table]     │ │
│ │ SUBSIDY      │ │ │   Parameters: [sliders]      │ │
│ │ ☐ Efficiency │ │ └─────────────────────────────┘ │
│ │              │ │                                  │
│ │ FEEBATE      │ │ ⚠ Conflict: tax_rate overlap    │
│ │ ☐ Vehicle    │ │   Policies #1, #2 • [strategy]  │
│ └──────────────┘ │                                  │
├──────────────────┴─────────────────────────────────┤
│ Saved Portfolios: [load] [clone] [delete]          │
└────────────────────────────────────────────────────┘
```

### Current Component Reuse Strategy

| Existing Component | Reuse in 20.3 | Changes Required |
|---|---|---|
| `PortfolioTemplateBrowser` | ✅ Reused as-is | None — props unchanged |
| `PortfolioCompositionPanel` | ✅ Reused as-is | None — props unchanged |
| `YearScheduleEditor` | ✅ Reused via PortfolioCompositionPanel | None |
| `ParameterRow` | ✅ Reused via PortfolioCompositionPanel | None |
| `ConflictList` (inline in PortfolioDesignerScreen) | ⚠️ Extract to shared file | Move to `simulation/ConflictList.tsx` |
| `PortfolioDesignerScreen` | ❌ Deprecated | Add `@deprecated` tag; keep for reference |
| `WorkbenchStepper` | ❌ Not used in Stage 1 | Still used by DataFusionWorkbench |

### State Management in PoliciesStageScreen

`PoliciesStageScreen` becomes the stateful coordinator for Stage 1. State owned locally:

| State | Type | Source |
|---|---|---|
| `selectedTemplateIds` | `string[]` | Local — user toggles in PortfolioTemplateBrowser |
| `composition` | `CompositionEntry[]` | Local — synced from template selection |
| `resolutionStrategy` | `ResolutionStrategy` | Local — dropdown selection |
| `conflicts` | `PortfolioConflict[]` | Local — from `validatePortfolio()` API |
| `validationLoading` | `boolean` | Local — during validation call |
| `activePortfolioName` | `string \| null` | Local — name of the currently loaded/saved portfolio |
| `saveDialogOpen` | `boolean` | Local — modal state |
| `loadDialogOpen` | `boolean` | Local — modal state |
| `cloneDialogOpen` | `string \| null` | Local — portfolio name being cloned |

State consumed from AppContext (via `useAppState()`):

| State | Usage |
|---|---|
| `templates` | Passed to PortfolioTemplateBrowser |
| `portfolios` | Listed in Load dialog and saved portfolios section |
| `refetchPortfolios` | Called after save/delete/clone |
| `activeScenario` | Read `portfolioName` for initial load |
| `updateScenarioField` | Write `portfolioName` on save/load/clear |
| `setSelectedPortfolioName` | Legacy sync for SimulationRunnerScreen |

### Portfolio Auto-Load on Mount

When `PoliciesStageScreen` mounts and `activeScenario?.portfolioName` is set (e.g., user navigated away and came back), the screen should auto-load that portfolio:

```tsx
useEffect(() => {
  if (!activeScenario?.portfolioName) return;
  if (composition.length > 0) return; // Don't overwrite existing work
  if (loadedRef.current === activeScenario.portfolioName) return; // Already loaded

  loadedRef.current = activeScenario.portfolioName;
  void loadPortfolioIntoComposition(activeScenario.portfolioName);
}, [activeScenario?.portfolioName]);
```

Use a `loadedRef` to prevent reload loops when the user saves (which updates `portfolioName` but shouldn't re-trigger the load).

### Interaction with Legacy State

| New State | Legacy State (synced alongside) | Why |
|---|---|---|
| `activeScenario.portfolioName` | `selectedPortfolioName` | `SimulationRunnerScreen` displays `selectedPortfolioName` in the runner header. Migration deferred to 20.6. |
| Template selection in composition | ⚠️ Do NOT sync to `selectedTemplateId` | `selectedTemplateId` is for single-template scenarios (legacy). Portfolio composition manages its own template list. |
| `activeScenario.policyType` | ⚠️ Do NOT change in this story | `policyType` is set by demo scenario or scenario entry dialog. Portfolio is multi-policy and doesn't map to a single `policyType`. |

### Nav Rail Completion After Portfolio Save

After portfolio is saved/loaded:
- **Policies** (`activeScenario.portfolioName !== null`): **Complete** ✅
- **Population** (unchanged): Depends on `selectedPopulationId`
- **Engine** (unchanged): Depends on `activeScenario !== null`
- **Results** (unchanged): Depends on `results.length > 0`

After clear:
- **Policies**: **Incomplete** (portfolioName is null)

### Error Handling Pattern

Follow the established pattern from `PortfolioDesignerScreen`:

```tsx
try {
  await createPortfolio({...});
  toast.success(`Portfolio '${name}' saved`);
} catch (err) {
  if (err instanceof ApiError) {
    toast.error(`${err.what} — ${err.why}`, { description: err.fix });
  } else if (err instanceof Error) {
    toast.error("Save failed", { description: err.message });
  }
}
```

### Debounced Validation Pattern

```tsx
const validationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

useEffect(() => {
  if (composition.length < 2) {
    setConflicts([]);
    return;
  }
  if (validationTimerRef.current) clearTimeout(validationTimerRef.current);
  validationTimerRef.current = setTimeout(() => {
    void runValidation();
  }, 500);
  return () => {
    if (validationTimerRef.current) clearTimeout(validationTimerRef.current);
  };
}, [composition, resolutionStrategy]);
```

### Files to Create

| File | Purpose |
|---|---|
| `frontend/src/components/simulation/ConflictList.tsx` | Extract `ConflictList` from PortfolioDesignerScreen into shared component (used by both PoliciesStageScreen and deprecated PortfolioDesignerScreen) |
| `frontend/src/components/screens/__tests__/PoliciesStageScreen.test.tsx` | Unit tests for the new inline composition layout |

### Files to Modify

| File | Changes |
|---|---|
| `frontend/src/components/screens/PoliciesStageScreen.tsx` | Replace thin wrapper with full inline composition screen: template browser + composition panel + toolbar + save/load/clone/clear dialogs + debounced validation + activeScenario integration |
| `frontend/src/components/screens/PortfolioDesignerScreen.tsx` | Add `@deprecated` JSDoc tag. Optionally update `ConflictList` import if extracted. No functional changes. |
| `frontend/src/components/layout/WorkflowNavRail.tsx` | Change `"policies"` completion from `portfolios.length > 0` to `activeScenario?.portfolioName !== null`. Update summary from portfolio count to active portfolio name. |
| `frontend/src/components/help/help-content.ts` | Update `"policies"` and `"portfolio"` help entries to describe the new inline layout. |
| `frontend/src/__tests__/workflows/analyst-journey.test.tsx` | Add Story 20.3 section with inline composition, portfolio save/scenario integration, and nav rail tests. |

### Files NOT Modified

| File | Why |
|---|---|
| `frontend/src/contexts/AppContext.tsx` | All needed actions exist: `updateScenarioField`, `setSelectedPortfolioName`, `refetchPortfolios`. No new state or actions required. |
| `frontend/src/api/portfolios.ts` | All API functions needed already exist: `createPortfolio`, `getPortfolio`, `deletePortfolio`, `clonePortfolio`, `validatePortfolio`. |
| `frontend/src/api/types.ts` | All types needed already exist: `PortfolioConflict`, `PortfolioListItem`, `CreatePortfolioRequest`, `ValidatePortfolioRequest`, `ValidatePortfolioResponse`. |
| `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` | Reused as-is — same props interface. |
| `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` | Reused as-is — same props interface. |
| `frontend/src/App.tsx` | Stage routing already renders `PoliciesStageScreen` for `activeStage === "policies"`. |

### Shadcn Components Used

From the available component library:
- `Button` — toolbar actions, dialog buttons
- `Input` — portfolio name, clone name inputs
- `Badge` — policy type badges in saved list and composition
- `Select` — resolution strategy dropdown
- `Separator` — visual separator between toolbar and content

Lucide icons used: `Save`, `FolderOpen`, `Copy`, `Trash2`, `X`, `CheckCircle2`, `AlertTriangle`, `Search`, `ArrowUp`, `ArrowDown`, `ChevronDown`, `ChevronRight`

### Project Structure Notes

- `PoliciesStageScreen.tsx` grows from 24 lines (thin wrapper) to ~400-500 lines (stateful coordinator). This is acceptable and consistent with `PortfolioDesignerScreen` (728 lines) and `DataFusionWorkbench` which are similar stateful screen components.
- New `ConflictList.tsx` in `components/simulation/` — consistent with other shared simulation sub-components in that directory.
- Test file at `components/screens/__tests__/PoliciesStageScreen.test.tsx` — mirrors source structure per convention.

### EPIC-21 Extensibility Note

Story 20.3 does not implement EPIC-21 features, but the portfolio composition design accommodates future extensions:
- `CompositionEntry.parameters` is `Record<string, number>` — flexible enough for new parameter types
- Conflict detection accepts any `PortfolioConflict` structure from the backend — new conflict types from EPIC-21 will render without frontend changes
- The validity indicator uses a simple `valid/invalid` binary — EPIC-21 can add `"warning"` states by extending the check

### Testing Patterns

**Mocking AppContext for PoliciesStageScreen tests:**
```tsx
vi.mock("@/contexts/AppContext", () => ({
  useAppState: vi.fn(),
}));
```

**Mocking portfolio API:**
```tsx
vi.mock("@/api/portfolios", () => ({
  createPortfolio: vi.fn(),
  getPortfolio: vi.fn(),
  deletePortfolio: vi.fn(),
  clonePortfolio: vi.fn(),
  validatePortfolio: vi.fn(),
}));
```

**Testing debounced validation:** Use `vi.useFakeTimers()` and `vi.advanceTimersByTime(500)` to trigger the debounced validation call.

### References

- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Stage 1: POLICIES & PORTFOLIO, lines 1364–1421]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Portfolio Composition inline requirement, line 1371]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Single policy = portfolio of one, line 1404]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — Conflict detection inline non-blocking, line 1403]
- [Source: `_bmad-output/planning-artifacts/prd.md` — FR43 Portfolio Composition, line 567]
- [Source: `_bmad-output/planning-artifacts/prd.md` — FR44 Portfolio Execution, line 568]
- [Source: `_bmad-output/planning-artifacts/prd.md` — FR32 No-Code GUI, line 547]
- [Source: `_bmad-output/planning-artifacts/epics.md` — Story 20.3 BKL-2003, lines 2054–2070]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Portfolio conflict resolution strategies, line 343]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Frontend Stage 1 surfaces, line 484]
- [Source: `frontend/src/types/workspace.ts` — WorkspaceScenario.portfolioName, line 47]
- [Source: `frontend/src/components/screens/PortfolioDesignerScreen.tsx` — Current 3-step designer, 728 lines]
- [Source: `frontend/src/components/screens/PoliciesStageScreen.tsx` — Current thin wrapper, 24 lines]
- [Source: `frontend/src/components/simulation/PortfolioTemplateBrowser.tsx` — Template browser, 159 lines]
- [Source: `frontend/src/components/simulation/PortfolioCompositionPanel.tsx` — Composition panel, 257 lines]
- [Source: `frontend/src/components/layout/WorkflowNavRail.tsx` — Completion logic, lines 39–57]
- [Source: `frontend/src/api/portfolios.ts` — Portfolio CRUD API, 76 lines]
- [Source: `frontend/src/api/types.ts` — Portfolio types, lines 268–336]
- [Source: `frontend/src/contexts/AppContext.tsx` — updateScenarioField, setSelectedPortfolioName]
- [Source: `frontend/src/components/scenario/ScenarioEntryDialog.tsx` — Fixed overlay dialog pattern]
- [Source: `_bmad-output/implementation-artifacts/20-2-add-pre-seeded-demo-scenario-onboarding-and-scenario-entry-flows.md` — Dialog/overlay pattern, legacy state sync pattern]
- [Source: `_bmad-output/implementation-artifacts/20-1-implement-canonical-scenario-model-and-stage-aware-routing-shell.md` — Stage routing, activeScenario, updateScenarioField]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
