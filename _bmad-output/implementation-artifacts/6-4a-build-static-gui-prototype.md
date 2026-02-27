# Story 6.4a: Build Static GUI Prototype — Configuration and Simulation Flows

Status: in-progress

## Story

As a **policy analyst (Sophie)**,
I want **a clickable GUI prototype built with the target stack (React + Shadcn/ui + Tailwind v4) that lets me navigate the full configuration flow (population selection → policy template → parameter editing → assumptions review) and the simulation flow (run → results → comparison)**,
so that **screen layout and navigation can be validated and adjusted before backend integration begins, and the prototype screens are directly reusable in the final wired application**.

## Acceptance Criteria

From backlog (BKL-604a), aligned with FR32 (no-code GUI for scenario operations).

1. **AC-1: Full configuration flow navigable**
   - Given the prototype opened in a browser, when the analyst navigates the configuration flow, then clickable screens cover: population selection → policy template selection → parameter editing → assumptions review.
   - Each step in the flow is reachable via the ModelConfigStepper component (non-blocking — steps are always accessible, not wizard-locked).
   - Template fast-path: selecting a pre-built template pre-fills all configuration steps with sensible defaults.

2. **AC-2: Full simulation flow navigable**
   - Given the prototype, when the analyst navigates the simulation flow, then clickable screens cover: run trigger → progress indicator → results display → scenario comparison.
   - The run flow shows a RunProgressBar with simulated progress (no real backend needed).
   - Results display shows mock distributional bar charts (income decile impact) using Recharts with static data.
   - Comparison view shows at least side-by-side mode with two mock scenarios.

3. **AC-3: Three-column workspace layout implemented**
   - Given the prototype at viewport >= 1440px, then the three-column layout is visible: left panel (parameters/config, 280-320px), main content (flexible), right panel (context/metadata, 280-360px).
   - Side panels collapse to 48px icon rails at viewports < 1440px.
   - Panels are resizable via draggable dividers (ResizablePanel from Shadcn/ui).
   - Panel collapse/expand persists within the session.

4. **AC-4: Target stack used — screens are reusable**
   - Given the prototype source code, when inspected, then it uses: React 19 + TypeScript, Vite, Shadcn/ui components, Tailwind CSS v4, Recharts for charts.
   - Components follow Shadcn/ui patterns (cva variant pattern, Tailwind-only styling).
   - Custom domain components (ParameterRow, ScenarioCard, RunProgressBar, ComparisonView, ModelConfigStepper) are implemented as reusable React components in `frontend/src/components/simulation/`.
   - Shadcn/ui base components live in `frontend/src/components/ui/`.

5. **AC-5: Visual design matches UX specification**
   - The prototype follows the "Dense Terminal" design direction: hard 1px borders between panels, no shadows on static elements, `bg-white` for content areas, `bg-slate-50` for panel chrome.
   - Typography uses Inter for UI text and IBM Plex Mono for numeric data values.
   - Color tokens match the UX spec: emerald (validated), amber (warning), stone (unreviewed), red (error), blue (selection/editing), violet (lineage), sky (reform/delta).
   - Chart colors follow the defined palette: baseline=slate-500, reform-a=blue-500, reform-b=violet-500.

6. **AC-6: Product owner can review and adjust**
   - Given the prototype, when reviewed by the product owner, then screen layout, navigation flow, and component placement can be adjusted by modifying React components — no separate design tool needed.
   - The prototype runs with `npm run dev` (Vite dev server) and hot-reloads on changes.

## Dependencies

- **No hard backend dependencies** — this is BKL-604a with "Depends On: —" in the backlog. The prototype uses mock/static data only.
- **Follow-on story:**
  - Story 6-4b (BKL-604b): Wire GUI prototype to FastAPI backend — depends on this story AND BKL-601 (Python API).
  - Story 6-1 (BKL-601): Stable Python API — required for 6-4b but NOT for this story.

## Tasks / Subtasks

- [ ] Task 0: Scaffold frontend project (AC: #4, #6)
  - [ ] 0.1 Initialize Vite + React 19 + TypeScript project in `frontend/`
  - [ ] 0.2 Install and configure Tailwind CSS v4 with `@tailwindcss/vite` plugin
  - [ ] 0.3 Initialize Shadcn/ui (`npx shadcn-ui@latest init`) and add base components: Button, Input, Select, Slider, Switch, Dialog, Popover, Tooltip, Card, Table, Tabs, Badge, Collapsible, Separator, ScrollArea, ResizablePanel, Sheet
  - [ ] 0.4 Install Recharts for chart components
  - [ ] 0.5 Configure design tokens: custom color palette (emerald, amber, stone, red, blue, violet, sky), chart CSS variables, typography (Inter + IBM Plex Mono)
  - [ ] 0.6 Verify `npm run dev` starts and hot-reloads

- [ ] Task 1: Build three-column workspace layout shell (AC: #3)
  - [ ] 1.1 Create `WorkspaceLayout` component using Shadcn/ui ResizablePanel (left 280-320px, main flexible, right 280-360px)
  - [ ] 1.2 Implement panel collapse to 48px icon rails at < 1440px viewport
  - [ ] 1.3 Add panel toggle buttons and keyboard shortcuts (Cmd+[ left, Cmd+] right)
  - [ ] 1.4 Add session-persisted panel state (localStorage)
  - [ ] 1.5 Style per UX spec: hard 1px `border-slate-200` between panels, `bg-slate-50` for panel chrome, `bg-white` for content areas, square corners on panel containers

- [ ] Task 2: Build custom domain components (AC: #4, #5)
  - [ ] 2.1 `ParameterRow` — dense inline parameter editing: label, current value (mono), baseline value (muted), delta indicator (sky badge), hover/editing/modified states
  - [ ] 2.2 `ScenarioCard` — compact scenario card: name, status badge (draft/ready/running/completed/failed), delta summary, last run timestamp, actions (Run/Clone/Compare/Delete), baseline vs reform variants
  - [ ] 2.3 `RunProgressBar` — progress bar with percentage, ETA, current step label ("Computing year 2027..."), cancel button, animated states
  - [ ] 2.4 `ModelConfigStepper` — horizontal step bar: Population → Data Sources → Policy → Validation, with step status icons, clickable navigation, non-blocking
  - [ ] 2.5 `ComparisonView` — main content component with Tabs for side-by-side/overlay/delta modes, scenario selector (max 5), color-coded per scenario

- [ ] Task 3: Build configuration flow screens (AC: #1)
  - [ ] 3.1 Population selection screen — list of pre-built synthetic populations, selection card with metadata (source, household count, year)
  - [ ] 3.2 Policy template selection screen — grid of template cards (Carbon Tax variants, Subsidy, Rebate, Feebate), each with description and parameter count
  - [ ] 3.3 Parameter editing screen — left panel filled with ParameterRow components grouped by domain (tax rates, thresholds, subsidies), using mock parameter data
  - [ ] 3.4 Assumptions review screen — summary panel showing all configuration choices: population source, template, parameters, with validation status indicators
  - [ ] 3.5 Wire all screens through ModelConfigStepper navigation

- [ ] Task 4: Build simulation flow screens (AC: #2)
  - [ ] 4.1 Run trigger — prominent "Run Simulation" primary button, pre-run summary showing what will be computed
  - [ ] 4.2 Progress view — RunProgressBar with simulated animated progress (setTimeout-based), step labels cycling through years
  - [ ] 4.3 Results view — distributional bar chart (Recharts) showing income decile impacts with mock data, summary statistics cards (Gini, fiscal cost, affected population %)
  - [ ] 4.4 Comparison view — ComparisonView with side-by-side mode showing baseline vs one reform with mock indicator data
  - [ ] 4.5 Scenario workspace — left panel with ScenarioCard components (one baseline + one reform), main content toggling between single results and comparison

- [ ] Task 5: Polish and verify (AC: #5, #6)
  - [ ] 5.1 Verify all color tokens match UX spec semantic palette
  - [ ] 5.2 Verify typography: Inter for UI, IBM Plex Mono for data values
  - [ ] 5.3 Verify Dense Terminal style: no shadows on static elements, tight padding (p-3), hard borders
  - [ ] 5.4 Verify responsive collapse at 1440px breakpoint
  - [ ] 5.5 Test `npm run dev` works with hot reload
  - [ ] 5.6 Run TypeScript type check (`npx tsc --noEmit`)
  - [ ] 5.7 Run lint check (ESLint)
- [ ] Review Follow-ups (AI)
  - [ ] [AI-Review][HIGH] Implement AC-1 configuration flow screens and non-blocking `ModelConfigStepper` (`population -> template -> parameter editing -> assumptions`) in reusable React components. [Story AC refs: lines 15-18]
  - [ ] [AI-Review][HIGH] Implement AC-2 simulation flow (`run trigger -> progress -> results -> comparison`) including `RunProgressBar`, Recharts distribution chart, and side-by-side comparison view. [Story AC refs: lines 20-24]
  - [ ] [AI-Review][HIGH] Implement AC-3 workspace shell with three resizable panels, `<1440px` collapse to 48px rails, and session-persisted panel state. [Story AC refs: lines 26-30]
  - [ ] [AI-Review][HIGH] Complete AC-4 stack scaffold and component structure (`package.json`, `vite.config.ts`, `src/main.tsx`, `src/App.tsx`, `src/components/ui/`, `src/components/simulation/`). Current `frontend/` has only `Dockerfile`, `nginx.conf`, and `src/data/mock-data.ts`. [Story refs: lines 32-37, 126-160]
  - [ ] [AI-Review][HIGH] Restore runnable dev workflow for AC-6 by creating npm/Vite project metadata and scripts so `npm run dev` works with hot reload. [Story refs: lines 44-47]
  - [ ] [AI-Review][MEDIUM] Fix repository hygiene: `.gitignore` `data/` rule currently ignores `frontend/src/data/mock-data.ts`, preventing required mock-data assets from being versioned. [`.gitignore`: line 59]
  - [ ] [AI-Review][MEDIUM] Update Dev Agent Record with implementation evidence (debug log refs, completion notes, file list) once code work starts; record is currently empty and non-auditable. [Story refs: lines 322-326]
  - [ ] [AI-Review][MEDIUM] Align story claims with git reality: there are no tracked frontend source changes for this story yet; only unrelated working-tree changes were detected (`_bmad-output/implementation-artifacts/sprint-status.yaml`, `.vite` cache, and untracked story 6-1 draft).

## Dev Notes

### Architecture Compliance

This story implements **FR32** (no-code GUI for scenario operations) as a static prototype. Per the architecture document's Deployment & GUI Architecture section (2026-02-27):

- **Monorepo structure**: Frontend lives in `frontend/` alongside the Python `src/` backend
- **Frontend stack** (from architecture and UX spec): React 19+ / TypeScript / Vite / Shadcn/ui / Tailwind CSS v4 / Recharts / React Flow (not needed for this story)
- **No backend dependency**: This story is purely frontend — mock data only, no FastAPI calls
- **Screens must be reusable**: The whole point of using the target stack is that prototype screens become production screens in story 6-4b

### Critical Implementation Rules

**From project-context.md and UX spec:**

- **Tailwind-only styling** — no CSS modules, no styled-components, no inline styles. Single pattern for consistent AI generation.
- **Component props use TypeScript interfaces** with JSDoc descriptions
- **cva (class variance authority)** pattern for component variants, following Shadcn/ui conventions
- **Semantic HTML first** — `<button>` not `<div onClick>`, `<nav>`, `<main>`, `<aside>` for layout regions
- **No mobile layouts** — desktop-only (min 1280px). Show warning below 1280px.
- **No `forwardRef`** — React 19 accepts `ref` as a prop directly
- **`@import "tailwindcss"`** in CSS, not `@tailwind` directives (Tailwind v4 change)
- **`@tailwindcss/vite`** plugin, not PostCSS (Tailwind v4 change)

### Frontend Project Structure

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── vite.config.ts              ← Vite + Tailwind v4 + React plugin
├── src/
│   ├── main.tsx                ← React 19 createRoot entry
│   ├── App.tsx                 ← Root component with workspace layout
│   ├── index.css               ← @import "tailwindcss" + design tokens + font imports
│   ├── components/
│   │   ├── ui/                 ← Shadcn/ui base components (Button, Card, etc.)
│   │   ├── simulation/         ← Domain components
│   │   │   ├── ParameterRow.tsx
│   │   │   ├── ScenarioCard.tsx
│   │   │   ├── RunProgressBar.tsx
│   │   │   ├── ModelConfigStepper.tsx
│   │   │   ├── ComparisonView.tsx
│   │   │   ├── DistributionalChart.tsx  ← Recharts wrapper
│   │   │   └── SummaryStatCard.tsx
│   │   └── layout/
│   │       ├── WorkspaceLayout.tsx      ← Three-column shell
│   │       ├── LeftPanel.tsx
│   │       ├── MainContent.tsx
│   │       └── RightPanel.tsx
│   ├── data/
│   │   └── mock-data.ts        ← Static mock data for all screens
│   └── lib/
│       └── utils.ts            ← Shadcn/ui cn() utility
├── Dockerfile                  ← Already exists (nginx serving build)
└── nginx.conf                  ← Already exists
```

### Design Tokens Configuration

**Tailwind v4 uses CSS `@theme` blocks instead of JS config:**

```css
/* In index.css */
@import "tailwindcss";

@theme {
  --color-validated: var(--color-emerald-500);
  --color-warning: var(--color-amber-500);
  --color-unreviewed: var(--color-stone-400);
  --color-error: var(--color-red-500);
  --color-selection: var(--color-blue-500);
  --color-lineage: var(--color-violet-500);
  --color-reform: var(--color-sky-500);
}

/* Chart colors as CSS custom properties */
:root {
  --chart-baseline: theme(colors.slate.500);
  --chart-reform-a: theme(colors.blue.500);
  --chart-reform-b: theme(colors.violet.500);
  --chart-reform-c: theme(colors.emerald.500);
  --chart-reform-d: theme(colors.amber.500);
}
```

**Fonts (load via Google Fonts or local):**
- Inter: UI text (Shadcn/ui default, already included)
- IBM Plex Mono: All numeric data values, parameter values, IDs

### Mock Data Shape

All screens use static mock data — no API calls. The mock data should represent realistic ReformLab domain concepts:

```typescript
// mock-data.ts
export const mockPopulations = [
  { id: "fr-synthetic-2024", name: "France Synthetic 2024", households: 100_000, source: "INSEE marginals", year: 2024 },
  { id: "fr-synthetic-2023", name: "France Synthetic 2023", households: 100_000, source: "INSEE marginals", year: 2023 },
];

export const mockTemplates = [
  { id: "carbon-tax-flat", name: "Carbon Tax — Flat Rate", type: "carbon-tax", parameterCount: 8, description: "Flat carbon tax rate applied uniformly" },
  { id: "carbon-tax-progressive", name: "Carbon Tax — Progressive", type: "carbon-tax", parameterCount: 12, description: "Progressive rate by income decile" },
  { id: "carbon-tax-dividend", name: "Carbon Tax — With Dividend", type: "carbon-tax", parameterCount: 10, description: "Flat tax with equal per-capita dividend" },
  { id: "subsidy-energy", name: "Energy Efficiency Subsidy", type: "subsidy", parameterCount: 6, description: "Means-tested energy efficiency subsidy" },
  { id: "feebate-vehicle", name: "Vehicle Feebate", type: "feebate", parameterCount: 9, description: "Fee on high-emission, rebate on low-emission vehicles" },
];

export const mockParameters = [
  { id: "tax_rate", label: "Carbon tax rate", value: 44, baseline: 44, unit: "EUR/tCO2", group: "Tax Rates", type: "slider", min: 0, max: 200 },
  { id: "dividend_per_capita", label: "Dividend per capita", value: 120, baseline: 0, unit: "EUR/year", group: "Redistribution", type: "number" },
  // ... more parameters
];

export const mockDecileData = [
  { decile: "D1", baseline: -120, reform: -80, delta: 40 },
  { decile: "D2", baseline: -180, reform: -150, delta: 30 },
  // ... through D10
];

export const mockScenarios = [
  { id: "baseline", name: "Baseline (No Policy)", status: "completed", isBaseline: true, parameterChanges: 0 },
  { id: "reform-a", name: "Carbon Tax + Dividend", status: "completed", isBaseline: false, parameterChanges: 3, linkedBaseline: "baseline" },
];
```

### Scope Guardrails

- **In scope:**
  - Vite + React 19 + TS project scaffold in `frontend/`
  - Shadcn/ui initialization with all needed base components
  - Tailwind v4 with custom design tokens
  - Three-column responsive workspace layout
  - Custom domain components (ParameterRow, ScenarioCard, RunProgressBar, ModelConfigStepper, ComparisonView)
  - Configuration flow: 4 screens navigable via stepper
  - Simulation flow: run → progress → results → comparison with mock data
  - Recharts distributional bar chart with mock data
  - Dense Terminal visual style per UX spec

- **Out of scope (deferred to 6-4b or later):**
  - FastAPI backend or any real API calls
  - Real data loading or computation
  - React Flow / lineage DAG visualization (Phase 1b per UX spec)
  - WaterfallChart component (Phase 1b)
  - Export functionality
  - Command palette (Cmd+K) — Phase 2
  - Lens overlays — Phase 2
  - State management library (React Context is sufficient for prototype)
  - Authentication / password prompt
  - Docker build or deployment — just dev server
  - Unit tests for components (manual visual review is the validation method)

### Latest Technical Stack (February 2026)

| Package | Version | Install |
|---------|---------|---------|
| React | 19.x | `react react-dom` |
| Vite | 7.x | `npm create vite@latest -- --template react-ts` |
| TypeScript | 5.x | Included with Vite template |
| Tailwind CSS | 4.x | `tailwindcss @tailwindcss/vite` |
| Shadcn/ui | latest | `npx shadcn-ui@latest init` |
| Recharts | 3.x | `recharts` |
| React Hook Form | 7.x | Not needed for this story (no real forms) |
| Zod | 4.x | Not needed for this story (no schema validation) |

**Critical Tailwind v4 differences from v3:**
- `@import "tailwindcss"` instead of `@tailwind` directives
- `@tailwindcss/vite` plugin instead of PostCSS
- Theme configured via CSS `@theme` blocks, not `tailwind.config.js`
- Auto-discovers template files (no `content` array needed)
- Class renames: `bg-gradient-to-*` → `bg-linear-to-*`, `flex-shrink-0` → `shrink-0`

**Critical React 19 differences from React 18:**
- `forwardRef` no longer needed — `ref` is a regular prop
- Use `ReactDOM.createRoot()` (not `ReactDOM.render()`)
- String refs removed — use callback refs or `createRef()`

### Previous Story Intelligence

This is the first story in EPIC-6 (Interfaces). No previous story in this epic.

**From EPIC-5 (most recent work):**
- The project uses frozen dataclasses, Protocol interfaces, and PyArrow throughout the Python backend
- All backend modules have comprehensive test suites with class-based test grouping
- The governance module captures run manifests with seeds, parameters, data hashes — this data will eventually flow to the GUI's lineage and run context panels (but not in this story)

**From git history (last 5 commits):**
- All recent work was in EPIC-5 (governance/reproducibility) — Python backend only
- No frontend code has been written yet — `frontend/` only contains `Dockerfile` and `nginx.conf`
- The project is mature on the backend side with computation, data, templates, orchestrator, vintage, indicators, and governance all implemented

### Project Structure Notes

- The `frontend/` directory already exists with `Dockerfile` and `nginx.conf` — do NOT overwrite these
- The Python backend is in `src/reformlab/` — this story does NOT touch any Python code
- The `frontend/` directory is part of the monorepo but is a separate npm project with its own `package.json`

### References

- [Source: architecture.md#Deployment-&-GUI-Architecture] — Monorepo structure, frontend stack, deployment topology
- [Source: architecture.md#Frontend-Stack] — React 18+/TS, Vite, Shadcn/ui + Radix, Tailwind v4, Recharts, React Flow
- [Source: ux-design-specification.md#Design-System-Foundation] — Shadcn/ui choice, implementation approach, customization strategy
- [Source: ux-design-specification.md#Visual-Design-Foundation] — Color system, typography, spacing, Dense Terminal direction
- [Source: ux-design-specification.md#Component-Strategy] — Custom component specs (ParameterRow, ScenarioCard, RunProgressBar, etc.)
- [Source: ux-design-specification.md#User-Journey-Flows] — Configuration flow, onboarding flow, scenario workspace flow
- [Source: ux-design-specification.md#Defining-Interaction] — Core loop, experience mechanics
- [Source: ux-design-specification.md#UX-Consistency-Patterns] — Action hierarchy, feedback patterns, error handling, navigation
- [Source: ux-design-specification.md#Responsive-Design-&-Accessibility] — Desktop-only, viewport breakpoints, accessibility strategy
- [Source: backlog BKL-604a] — Story acceptance criteria
- [Source: prd.md#Functional-Requirements] — FR32 no-code GUI

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

- `_bmad-output/implementation-artifacts/6-4a-build-static-gui-prototype.md` (updated by code review)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (story status sync target)
- `frontend/src/data/mock-data.ts` (reviewed; currently git-ignored)

## Senior Developer Review (AI)

### Reviewer

Lucas

### Date

2026-02-27

### Outcome

Changes Requested

### Summary

Story implementation has not started in tracked frontend source. Core acceptance criteria AC-1 through AC-4 and AC-6 are not implemented yet. Story status has been set to `in-progress` and review follow-up action items were added.

### Findings

1. **HIGH** - AC-1 configuration flow is missing (`ModelConfigStepper` and clickable configuration screens are not present in source). [Story AC refs: lines 15-18]
2. **HIGH** - AC-2 simulation flow is missing (`RunProgressBar`, results chart, and comparison UI are not present in source). [Story AC refs: lines 20-24]
3. **HIGH** - AC-3 layout requirements are missing (no workspace layout or resizable panel implementation in `frontend/src`). [Story AC refs: lines 26-30]
4. **HIGH** - AC-4 target stack/reusable component structure is missing (expected React/Vite/Tailwind/Shadcn component tree not present). [Story refs: lines 32-37, 126-160]
5. **HIGH** - AC-6 dev workflow is currently not runnable (no `package.json`/Vite scripts in `frontend/`, so `npm run dev` cannot be executed). [Story refs: lines 44-47]
6. **MEDIUM** - `frontend/src/data/mock-data.ts` is git-ignored by the global `data/` ignore rule, so story assets are not tracked. [`.gitignore`: line 59]
7. **MEDIUM** - Dev Agent Record has no implementation traceability (debug logs, completion notes, and file list were empty before review). [Story refs: lines 322-326]
8. **MEDIUM** - Git vs story discrepancy: no tracked frontend source changes were found for this story in the working tree.

### Validation Evidence

- `git status --porcelain --untracked-files=all` showed no tracked frontend source work for Story 6.4a.
- `find frontend/src -type f` found only `frontend/src/data/mock-data.ts`.
- `ls -la frontend` showed only Docker/runtime artifacts plus `src/`, with no npm/Vite scaffold files.
- `rg` for required UI components (`ModelConfigStepper`, `RunProgressBar`, `ComparisonView`, `WorkspaceLayout`, `ParameterRow`, `ScenarioCard`) returned no matches in non-generated frontend source.

## Change Log

- 2026-02-27: Senior Developer Review (AI) completed for Story 6.4a; outcome set to Changes Requested, status moved to in-progress, and follow-up action items added.
