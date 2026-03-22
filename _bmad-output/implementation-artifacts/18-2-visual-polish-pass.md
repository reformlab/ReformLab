
# Story 18.2: Visual Polish Pass (Rounded Corners, Shadows, Header, Login)

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want the workspace to have rounded corners on containers, subtle depth through shadows, a branded header, and a polished login screen,
so that the application feels cohesive and professional rather than a flat prototype stitched together.

## Acceptance Criteria

1. **AC-1: Rounded corners on all containers** — Given all Card, section, and panel containers across all 9 screens, when rendered, then they use `rounded-lg` corners instead of sharp edges. Buttons and inputs already use `rounded-md` from shadcn defaults — verify but do not change.

2. **AC-2: Subtle shadows for depth** — Given primary content containers (cards, sections, the login card), when rendered, then they use subtle shadows (`shadow-sm`) for visual depth. Layout-level panels (left/right sidebars, workspace frame) do NOT get shadows — only content containers within them. Modals/dialogs keep existing `shadow-lg`.

3. **AC-3: Branded workspace header** — Given the main workspace header (currently `border border-slate-200 bg-white p-3` at `App.tsx:~250`), when rendered, then it displays a gradient background (e.g., `bg-gradient-to-r from-white to-indigo-50`), the "ReformLab" title uses `text-xl font-bold`, and there is a subtle brand accent (indigo tint on subtitle or a small icon).

4. **AC-4: Polished login screen** — Given the PasswordPrompt screen, when rendered, then the login card uses `rounded-xl shadow-lg`, includes a brand heading ("ReformLab") above the form, and the submit button uses a primary color fill (`bg-blue-600 text-white`).

5. **AC-5: Consistent border treatment** — Given all `border border-slate-200` section containers, when rounded corners are applied, then borders remain and are softened with the radius. No need to switch to `ring-1` — keep existing border approach for consistency.

6. **AC-6: No visual regressions** — Given all existing screens, when rendered at 1280px+ viewport, then no layouts are broken, no content is clipped by border radius, and all existing tests pass.

## Tasks / Subtasks

- [ ] Task 1: Update `Card` component base styling (AC: 1, 2)
  - [ ] 1.1: In `frontend/src/components/ui/card.tsx` line 6, add `rounded-lg shadow-sm` to the Card base class: `"border border-slate-200 bg-white"` → `"rounded-lg border border-slate-200 bg-white shadow-sm"`
  - [ ] 1.2: In `card.tsx` line 13, update CardHeader: add `rounded-t-lg` so header background doesn't clip rounded corners
  - [ ] 1.3: In `card.tsx` line 41, update CardFooter: add `rounded-b-lg` so footer background doesn't clip rounded corners
  - [ ] 1.4: Verify Card usage renders correctly (ScenarioCard, SummaryStatCard, and any other Card-based components)

- [ ] Task 2: Add rounded corners to inline section containers across screens (AC: 1, 2)
  - [ ] 2.1: In `App.tsx`, update right panel sections (~lines 487-520): add `rounded-lg` to each `border border-slate-200 bg-white p-3` section
  - [ ] 2.2: In `App.tsx`, update the "Run Simulation" section (~line 332): add `rounded-lg shadow-sm`
  - [ ] 2.3: In `ComparisonDashboardScreen.tsx`: add `rounded-lg` to all ~13 `border border-slate-200` containers
  - [ ] 2.4: In `PortfolioDesignerScreen.tsx`: add `rounded-lg` to section containers
  - [ ] 2.5: In `SimulationRunnerScreen.tsx`: add `rounded-lg` to section containers
  - [ ] 2.6: In `DataFusionWorkbench.tsx`: add `rounded-lg` to section containers
  - [ ] 2.7: In `PopulationSelectionScreen.tsx`: add `rounded-lg` to section containers
  - [ ] 2.8: In `ParameterEditingScreen.tsx`: add `rounded-lg` to section containers
  - [ ] 2.9: In `TemplateSelectionScreen.tsx`: add `rounded-lg` to section containers (excluding modals — already have rounding)
  - [ ] 2.10: In `AssumptionsReviewScreen.tsx`: add `rounded-lg` to section containers
  - [ ] 2.11: In `PopulationValidationPanel.tsx`, `ResultDetailView.tsx`: add `rounded-lg` to ~6 containers each
  - [ ] 2.12: In `ReviewStep.tsx`: normalize existing mixed `rounded` to consistent `rounded-lg`
  - [ ] 2.13: In `MultiRunChart.tsx`: add `rounded-lg` to any section containers
  - [ ] 2.14: In `RunProgressBar.tsx`, `DistributionalChart.tsx`: add `rounded-lg` if they have section containers

- [ ] Task 3: Polish workspace header (AC: 3)
  - [ ] 3.1: In `App.tsx` (~line 250), update the header div: replace `border border-slate-200 bg-white p-3` with `rounded-lg border border-slate-200 bg-gradient-to-r from-white to-indigo-50 p-3 shadow-sm`
  - [ ] 3.2: Update "ReformLab" heading from `text-lg font-semibold` to `text-xl font-bold`
  - [ ] 3.3: Add brand accent: update subtitle `text-slate-600` → `text-indigo-600/70` or similar muted indigo tint

- [ ] Task 4: Polish PasswordPrompt login screen (AC: 4)
  - [ ] 4.1: In `PasswordPrompt.tsx` (~line 30), update the login card: `border border-slate-200 bg-white p-6` → `rounded-xl border border-slate-200 bg-white p-8 shadow-lg`
  - [ ] 4.2: Add a brand heading above the form: "ReformLab" in `text-2xl font-bold` with subtitle "Environmental Policy Analysis" in muted text
  - [ ] 4.3: Ensure submit button uses filled primary style (check if already using shadcn Button default variant which may already be blue)
  - [ ] 4.4: Verify centered layout on the page (already uses `min-h-screen flex items-center justify-center` pattern — confirm)

- [ ] Task 5: Workspace frame rounding (AC: 1)
  - [ ] 5.1: In `WorkspaceLayout.tsx` (~line 25), add `rounded-lg overflow-hidden` to the main workspace container: `"h-[calc(100vh-5.5rem)] border border-slate-200 bg-white"` → `"h-[calc(100vh-5.5rem)] rounded-lg border border-slate-200 bg-white overflow-hidden"`
  - [ ] 5.2: Do NOT add shadows to LeftPanel/RightPanel — they are navigation chrome. Only their internal content sections get rounding.

- [ ] Task 6: Verification (AC: 6)
  - [ ] 6.1: Run `npm run typecheck` in `frontend/` — 0 errors
  - [ ] 6.2: Run `npm run lint` in `frontend/` — 0 errors (pre-existing fast-refresh warnings OK)
  - [ ] 6.3: Run `npm test` in `frontend/` — all tests pass (259+ existing)
  - [ ] 6.4: Visually verify at 1280px viewport that no layouts overflow or break

## Dev Notes

### Visual Polish Strategy

This story applies "selective softening" to the Dense Terminal (Direction B) base established across Epics 6–17. The UX audit found the result too austere — this pass adds warmth without sacrificing data density.

**Rounding hierarchy:**
- `rounded-lg` — standard for all content containers, cards, sections
- `rounded-xl` — premium feel on the login card (larger, standalone element)
- `rounded-full` — already used on WorkflowNavRail step indicators — do NOT change
- `rounded-md` — shadcn default for buttons/inputs — do NOT change
- Panel chrome (LeftPanel, RightPanel `border-r`/`border-l` separators) — keep sharp

**Shadow hierarchy:**
- `shadow-sm` — content cards and section containers (subtle depth)
- `shadow-lg` — login card, modals, popovers (already applied to modals)
- No shadow — layout chrome (sidebars, workspace frame, nav rail)
- Do NOT add shadows to: table rows, list items, inline badges, nav items

**Header gradient:** Keep subtle. The workspace is a precision instrument — the gradient should whisper, not shout. `from-white to-indigo-50` is appropriate. Avoid saturated dark gradients (the draft had `from-blue-600 to-violet-600` — this is too aggressive for a data workspace; keep header text dark for readability).

### Efficient Approach — Highest-Leverage Change First

**Task 1 (Card component)** is the highest-leverage change. Many screens use the shadcn Card component, so adding `rounded-lg shadow-sm` there automatically polishes ScenarioCard, SummaryStatCard, and other Card-based layouts.

After Task 1, the remaining work is find-and-update on raw `border border-slate-200 bg-white p-3` patterns that don't use Card.

**Search pattern for raw containers:**
```
border border-slate-200 bg-white p-3
border border-slate-200 bg-slate-50 p-3
border border-slate-200 bg-white p-4
border border-slate-200 bg-white p-6
```

Add `rounded-lg` to each match. Add `shadow-sm` only to top-level content sections (not nested sub-containers within sections — those get rounding but not shadow to avoid shadow-on-shadow).

### Codebase Inventory — Containers to Update

**~96+ occurrences of `border border-slate-200`** across the codebase (from codebase analysis):

| File | ~Count | Notes |
|------|--------|-------|
| `components/ui/card.tsx` | 3 | **Foundation** — Card, CardHeader, CardFooter |
| `App.tsx` | 6 | Header, Run section, right panel sections |
| `screens/ComparisonDashboardScreen.tsx` | 13 | RunSelector, tabs, detail panels |
| `screens/PortfolioDesignerScreen.tsx` | 11 | Template grid, portfolio list, modals |
| `simulation/MultiRunChart.tsx` | 10 | Table cells, chart wrappers |
| `simulation/PopulationValidationPanel.tsx` | 6 | Validation results, summary cards |
| `simulation/ResultDetailView.tsx` | 6 | Result cards, detail sections |
| `screens/SimulationRunnerScreen.tsx` | ~5 | Config sections |
| `screens/DataFusionWorkbench.tsx` | ~5 | Source selection, method config |
| `auth/PasswordPrompt.tsx` | 1 | Login card |
| `layout/WorkspaceLayout.tsx` | 1 | Workspace frame |
| Others (PopulationSelection, Parameters, Template, Assumptions, ReviewStep) | ~15 | Various section containers |

### Files NOT to Modify

- `LeftPanel.tsx` / `RightPanel.tsx` — structural `border-r`/`border-l` separators stay sharp (panel chrome)
- `WorkflowNavRail.tsx` — already uses `rounded-full` on step indicators; just polished in Story 18.1
- `index.css` — body background gradient already exists; no global CSS changes needed
- Test files — no test changes expected (visual-only CSS class changes don't affect test selectors or assertions)
- Backend files — this is a frontend-only story

### What NOT to Do

- Do NOT add a `.panel` CSS utility class — keep Tailwind utility-first approach consistent with codebase
- Do NOT change Button or Input rounding — shadcn defaults (`rounded-md`) are already correct
- Do NOT use `ring-1` instead of `border` — keep existing border approach
- Do NOT add dark mode support — deferred to Phase 2 per UX spec
- Do NOT add brand logo SVG — use text only or lucide icon as placeholder
- Do NOT change spacing or padding — that's a different concern (not in scope for this story)

### Project Structure Notes

- Screen components: `frontend/src/components/screens/` (9 screens)
- Simulation domain components: `frontend/src/components/simulation/`
- Layout components: `frontend/src/components/layout/`
- Shadcn UI primitives: `frontend/src/components/ui/`
- Auth components: `frontend/src/components/auth/`
- No new files needed — pure styling pass on existing files
- Tailwind v4 via `@tailwindcss/vite` plugin; no `tailwind.config.ts` file (uses `@theme` in `index.css`)

### References

- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — "Design Direction Decision": Direction B (Dense Terminal) with selective softening from Direction A]
- [Source: `_bmad-output/planning-artifacts/ux-design-specification.md` — "Visual Design Foundation": shadows reserved for floating elements; `shadow-sm` on Shadcn Card override; `rounded-md` on interactive components]
- [Source: `_bmad-output/implementation-artifacts/epic-18-ux-polish-and-aesthetic-overhaul.md` — Epic exit criteria: "All containers have rounded corners and appropriate elevation"]
- [Source: `_bmad-output/implementation-artifacts/18-1-implement-workflow-navigation-rail.md` — Story 18.1 done: nav rail uses `rounded-full` indicators, 259 tests passing]
- [Source: `frontend/src/components/ui/card.tsx` — Card base: `border border-slate-200 bg-white` (no rounding, no shadow)]
- [Source: `frontend/src/components/auth/PasswordPrompt.tsx:30` — Login card: `border border-slate-200 bg-white p-6` (sharp corners)]
- [Source: `frontend/src/App.tsx:~250` — Header: `border border-slate-200 bg-white p-3` (sharp, no gradient)]

## Dev Agent Record

### Agent Model Used

*(to be filled by dev agent)*

### Debug Log References

*(to be filled by dev agent)*

### Completion Notes

*(to be filled by dev agent)*

### File List

*(to be filled by dev agent)*
