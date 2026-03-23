# Story 19.5: Build Interactive Domain Model (React/MDX Component)

Status: done

## Story

As a **visitor exploring the documentation site**,
I want the domain model page to feature a clickable interactive diagram showing the 6 core objects and their relationships,
so that I can discover what each concept does by clicking on it rather than scrolling through a wall of text.

## Acceptance Criteria

1. **Interactive diagram replaces Mermaid:** Given the domain model page (`domain-model.mdx`), when visited, then the static Mermaid code block diagram is replaced by a clickable React component rendered inside MDX showing the 6 core objects (Population, Policy, Orchestrator, Engine, Results, Indicators) and their directed relationships.
2. **Click reveals detail:** Given an object node in the interactive diagram, when clicked, then a detail panel displays the object's canonical description and key properties (from the Node Content Data table in Dev Notes); clicking the selected node again, or clicking anywhere outside the diagram area, dismisses the panel.
3. **Light and dark mode:** Given the interactive component, when rendered in Starlight, then node fills, edge strokes, and panel backgrounds use `--sl-color-*` CSS custom properties; when Starlight's theme toggle is activated, the diagram updates without a page reload and no intermediate hard-coded palette is visible.
4. **Existing content preserved:** Given the domain model page, when the interactive component is added, then all existing section content (headings, prose, `<details>` code blocks) remains intact below the diagram. The diagram is a navigation aid, not a replacement for page content.
5. **Build succeeds:** Given all changes in this story, when `npm run build` is run in `docs/`, then it completes with zero errors.
6. **TypeScript clean:** Given all changes, when `npm run check` is run in `docs/`, then it completes with zero errors.
7. **Keyboard accessible:** Given the interactive diagram, when navigated with a keyboard, then each node is reachable via Tab, selectable via Enter or Space (showing the detail panel), and the Escape key dismisses the open panel. Each node element has `role="button"`, a visible focus outline, and an `aria-label` describing its name.

## Tasks / Subtasks

- [x] Task 1: Add React integration to docs site (AC: 5, 6)
  - [x] Install `@astrojs/react`, `react`, `react-dom`, `@types/react`, `@types/react-dom`
  - [x] Add `react()` integration to `astro.config.mjs` (after `mermaid()`, before `starlight()`)
  - [x] Update `tsconfig.json` with JSX compiler options
  - [x] Verify `npm run build` and `npm run check` still pass with zero errors
- [x] Task 2: Build DomainModelDiagram React component (AC: 1, 2, 3)
  - [x] Create `docs/src/components/DomainModelDiagram.tsx`
  - [x] Implement SVG-based node layout for 6 objects with directed edge arrows
  - [x] Implement click handler that highlights selected node and shows detail panel
  - [x] Implement detail panel with object description and key properties
  - [x] Style with CSS custom properties from Starlight (`--sl-color-*`) for light/dark mode
  - [x] Add `useStarlightTheme` hook (MutationObserver on `data-theme`) if any fill/stroke must be set programmatically
- [x] Task 3: Integrate component into domain-model.mdx (AC: 1, 4)
  - [x] Replace Mermaid code block with `<DomainModelDiagram client:load />` import
  - [x] Keep all existing section content (headings, prose, `<details>` blocks) below the diagram
  - [x] The detail panel "Learn more" link is a standard `href="#section-id"` hash link — no auto-scroll JS needed (anchor navigation is handled by the browser)
- [x] Task 4: Verify build and visual quality (AC: 5, 6)
  - [x] Run `npm run build` in `docs/` — zero errors
  - [x] Run `npm run check` in `docs/` — zero errors

## Dev Notes

### React Integration Setup

**React is NOT yet installed in docs.** This is the first React component in the docs site. You must install the integration first.

**Version constraints (CRITICAL — from Story 19.1):**
- Docs site is pinned to **Astro 5.7.10** and **Starlight ^0.37**. Do NOT upgrade to Astro 6.x (requires Node 22+).
- Use `@astrojs/react` **^4.4** (not 5.x which requires Astro 6 + Node 22).
- Use **React 19** (`react@^19.0.0`, `react-dom@^19.0.0`) — compatible with `@astrojs/react` 4.x.

**Install command (version pins required — do NOT omit):**

```bash
cd docs
npm install @astrojs/react@^4.4 react@^19.0.0 react-dom@^19.0.0
npm install -D @types/react @types/react-dom
```

**Do NOT use `npx astro add react`** — it may attempt to upgrade Astro. Install manually.

**Post-install verification:** Run `npm ls @astrojs/react` — must show `4.x.x`. Run `npm ls astro` — must still show `5.7.10`. Run `npm ls zod` — must show only `3.25.76` (existing override).

**`astro.config.mjs` update:**

```js
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import mermaid from 'astro-mermaid';
import react from '@astrojs/react';

export default defineConfig({
  site: 'https://docs.reform-lab.eu',
  server: { port: 4322 },
  integrations: [
    mermaid(),
    react(),
    starlight({
      // ... existing config unchanged
    }),
  ],
});
```

Place `react()` after `mermaid()` and before `starlight()` in the integrations array.

**`tsconfig.json` update:**

```json
{
  "extends": "astro/tsconfigs/strict",
  "include": [".astro/types.d.ts", "**/*"],
  "exclude": ["dist"],
  "compilerOptions": {
    "jsx": "react-jsx",
    "jsxImportSource": "react"
  }
}
```

**Note:** `.astro/types.d.ts` is generated by `astro build` / `astro dev` / `astro sync`. In CI on a clean checkout, run `npm run build` before `npm run check` to ensure this file exists.

### Component Architecture

**File:** `docs/src/components/DomainModelDiagram.tsx`

**Design: Inline SVG with React state — no external library.**

The diagram has only 6 nodes and 5 edges. This is too simple to warrant a library like React Flow, D3, or Recharts. Use an inline SVG with:
- Rectangles (rounded) for each domain object
- Directed arrows (SVG `<line>` + `<marker>`) for relationships
- React `useState` for selected node
- CSS custom properties for theming

**Layout (matches existing Mermaid LR flow):**

```
            ┌──────────────┐
            │  Population   │───┐
            └──────────────┘   │    ┌──────────────┐    ┌──────────┐    ┌──────────┐
                               ├──→ │ Orchestrator  │──→ │  Engine  │──→ │ Results  │──→ ┌──────────────┐
            ┌──────────────┐   │    └──────────────┘    └──────────┘    └──────────┘    │  Indicators  │
            │    Policy     │───┘                                                        └──────────────┘
            └──────────────┘
```

Two inputs (Population, Policy) converge into Orchestrator, then linear flow to Engine → Results → Indicators.

**Node data (embed in component):**

Each node needs:
- `id` — matches the heading anchor on the page (e.g., `"population"`)
- `label` — display name (e.g., `"Population"`)
- `description` — 1-2 sentence summary (reuse from existing page prose)
- `properties` — 2-4 key properties (bullet points)
- `x`, `y` — SVG coordinates (top-left corner of the node rectangle)

**Suggested SVG coordinate system:**

```
viewBox: "0 0 920 220"
Node dimensions: width=130, height=44, rx=8 (rounded corners)

Node positions (x, y = top-left corner):
  population:   x=20,  y=30
  policy:       x=20,  y=150
  orchestrator: x=230, y=90
  engine:       x=430, y=90
  results:      x=600, y=90
  indicators:   x=770, y=90

Arrowhead marker: refX=10, refY=5, markerWidth=10, markerHeight=10
  path d="M 0 0 L 10 5 L 0 10 z"

Edge line endpoints (from right/left midpoints of node rects):
  population → orchestrator:   from (150, 52)  to (230, 112)  [angled down-right]
  policy → orchestrator:       from (150, 172) to (230, 112)  [angled up-right]
  orchestrator → engine:       from (360, 112) to (430, 112)  [horizontal]
  engine → results:            from (560, 112) to (600, 112)  [horizontal]
  results → indicators:        from (730, 112) to (770, 112)  [horizontal]
```

**Detail panel:**
- Appears below (or beside) the SVG when a node is clicked
- Shows: node label, description, properties list
- "Learn more" link scrolling to the corresponding `#section` anchor
- Click outside or click same node again to dismiss

### Dark/Light Mode Strategy

**Use CSS custom properties (CSS-only approach — preferred):**

Starlight sets `data-theme="light"` or `data-theme="dark"` on `<html>`. Style the component using Starlight's CSS variables:

| Purpose | Variable | Light | Dark |
|---------|----------|-------|------|
| Background | `var(--sl-color-bg)` | white | dark gray |
| Text | `var(--sl-color-text)` | dark | light |
| Node fill | `var(--sl-color-gray-6)` | light gray | dark gray |
| Node border | `var(--sl-color-gray-4)` | medium gray | medium gray |
| Accent/selected | `var(--sl-color-accent)` | brand accent | brand accent |
| Edge/arrow | `var(--sl-color-gray-3)` | gray | gray |

For SVG `fill` and `stroke` attributes (which cannot use CSS variables directly in all browsers), use CSS `fill: var(--sl-color-gray-6)` on SVG elements styled via CSS Module classes — SVG presentation attributes CAN be overridden by CSS.

Example (`DomainModelDiagram.module.css`):

```css
.domainNode rect {
  fill: var(--sl-color-gray-6);
  stroke: var(--sl-color-gray-4);
}
.domainNode.selected rect {
  fill: var(--sl-color-accent);
  stroke: var(--sl-color-accent);
}
.domainNode text {
  fill: var(--sl-color-text);
}
.domainEdge line {
  stroke: var(--sl-color-gray-3);
}
```

In the TSX file: `import styles from './DomainModelDiagram.module.css';` then `<g className={styles.domainNode}>` on each node group.

**If** CSS variables on SVG elements cause cross-browser issues, fall back to a `useStarlightTheme` hook using `MutationObserver` on the `data-theme` attribute:

```tsx
function useStarlightTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof document !== 'undefined') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      return (document.documentElement.dataset.theme as 'light' | 'dark') ?? (prefersDark ? 'dark' : 'light');
    }
    return 'dark';
  });
  useEffect(() => {
    const observer = new MutationObserver(() => {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme((document.documentElement.dataset.theme as 'light' | 'dark') ?? (prefersDark ? 'dark' : 'light'));
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => observer.disconnect();
  }, []);
  return theme;
}
```

**Prefer the CSS approach first.** Only add the hook if SVG fill/stroke doesn't respond to CSS vars in testing.

### Client Directive

Use **`client:load`** (not `client:visible`). The diagram is the first visual element on the page — it's above the fold and must be interactive immediately. `client:visible` would show a static placeholder first, then hydrate, which is worse UX for the hero element.

### MDX Integration Pattern

In `domain-model.mdx`, replace the Mermaid block:

```mdx
---
title: Domain Model
description: Core concepts and objects in the ReformLab domain model.
---

import DomainModelDiagram from '../../components/DomainModelDiagram';

ReformLab is built around six core objects that work together to produce distributional impact analysis. Click any object to learn more.

<DomainModelDiagram client:load />

---

## Population
{/* ... existing content unchanged ... */}
```

**Important MDX rules (from Stories 19.2–19.4):**
- Import statement goes after frontmatter, before content
- Use `{/* */}` for JSX comments, not `<!-- -->`
- Blank lines required around JSX components for MDX paragraph parsing

### Responsive Considerations

The SVG should use `viewBox` with a fixed coordinate system and `width="100%"` to scale responsively. At narrow viewports (< 640px), consider stacking nodes vertically instead of horizontally — but this is a stretch goal, not a requirement. The primary viewport for docs is desktop (1280px+).

### Files to Create

| File | Purpose |
|------|---------|
| `docs/src/components/DomainModelDiagram.tsx` | Interactive domain model React component |
| `docs/src/components/DomainModelDiagram.module.css` | CSS Module styles with `--sl-color-*` custom property references for light/dark theming |

### Files to Modify

| File | Change |
|------|--------|
| `docs/astro.config.mjs` | Add `react()` integration import and registration |
| `docs/tsconfig.json` | Add JSX compiler options |
| `docs/package.json` | New dependencies (via `npm install`, auto-updated) |
| `docs/package-lock.json` | Updated by `npm install` |
| `docs/src/content/docs/domain-model.mdx` | Replace Mermaid block with React component import + usage |

### Files NOT to Modify

- `docs/src/styles/custom.css` — component styles should use a CSS Module file (`DomainModelDiagram.module.css`) co-located with the component, not the global stylesheet. CSS Modules support descendant selectors (`.domain-node rect { ... }`) and CSS custom property references (`var(--sl-color-*)`). Do NOT use inline styles for theme-responsive rules (inline styles cannot do descendant selectors or `:hover`/`:focus`). Exception: if Starlight CSS variable overrides are needed for the diagram globally, add them to `custom.css`.
- Other MDX pages — out of scope
- `docs/src/content.config.ts` — no changes needed

### Node Content Data

Reuse descriptions from existing `domain-model.mdx` sections (condensed):

```typescript
const nodes = [
  {
    id: 'population',
    label: 'Population',
    description: 'A dataset of representative households — income, housing, vehicles, energy use, and demographics.',
    properties: ['PyArrow Tables by entity', 'INSEE / Eurostat / ADEME / SDES sources', 'Data fusion pipeline', 'Synthetic or custom'],
  },
  {
    id: 'policy',
    label: 'Policy',
    description: 'The reform being evaluated — tax rates, exemptions, thresholds, and redistribution rules.',
    properties: ['6 template types (carbon tax, subsidy, rebate, feebate, malus, poverty aid)', 'Year-indexed rate schedules', 'Portfolio composition (2+ policies)', 'Conflict detection'],
  },
  {
    id: 'orchestrator',
    label: 'Orchestrator',
    description: 'Runs your simulation year by year — feeding households through a pipeline of computation, behavioral response, and state transition steps.',
    properties: ['Pluggable step pipeline', 'Multi-year projection (10+ years)', 'Vintage tracking', 'Deterministic seeds'],
  },
  {
    id: 'engine',
    label: 'Engine',
    description: 'The computation backend that calculates household-level taxes and benefits. Default: OpenFisca France.',
    properties: ['ComputationAdapter protocol', 'Swappable backends', 'Version-pinned', 'Mock adapter for tests'],
  },
  {
    id: 'results',
    label: 'Results',
    description: 'Raw simulation output — a household-by-year panel dataset with every computed variable.',
    properties: ['Parquet storage on disk', 'In-memory LRU cache', 'Immutable run manifest', 'Reproducible via seeds + hashes'],
  },
  {
    id: 'indicators',
    label: 'Indicators',
    description: 'Analytics computed from results — distributional, fiscal, geographic, and welfare metrics.',
    properties: ['7 indicator types', 'Per-decile and per-region breakdowns', 'Winner/loser analysis', 'Cross-portfolio comparison'],
  },
];
```

### Edge Definitions

```typescript
const edges = [
  { from: 'population', to: 'orchestrator' },
  { from: 'policy', to: 'orchestrator' },
  { from: 'orchestrator', to: 'engine' },
  { from: 'engine', to: 'results' },
  { from: 'results', to: 'indicators' },
];
```

### Project Structure Notes

- **First React component in docs/** — establishes the pattern for Story 19.6 (guided tour with driver.js/shepherd.js)
- Component directory: `docs/src/components/` (new directory, follows Astro convention)
- Port 4322 for docs dev server (set in `astro.config.mjs`)
- Three surfaces: `reform-lab.eu` (sell) / `docs.reform-lab.eu` (use) / `app.reform-lab.eu` (try)

### Testing Strategy

No automated tests for static docs. Quality gates:

1. `npm run build` in `docs/` — zero errors, all pages render
2. `npm run check` in `docs/` — zero TypeScript errors
3. `npm run preview` — visual verification:
   - Domain model: interactive diagram renders (not Mermaid code block)
   - Domain model: clicking a node shows detail panel with description and properties
   - Domain model: clicking another node switches the detail panel
   - Domain model: clicking the selected node (or outside) dismisses the detail panel
   - Domain model: light mode → correct node colors, readable text
   - Domain model: dark mode → correct node colors, readable text
   - Domain model: toggle between light/dark → diagram updates without page reload
   - Domain model: all existing section content (headings, prose, `<details>`) intact below diagram
   - Domain model: SVG scales correctly at 1280px+ viewport
   - Sidebar navigation: all pages still accessible

### Risks

| Risk | Mitigation |
|------|------------|
| `@astrojs/react` version pulls in Astro 6 peer dep | Install `@astrojs/react@^4.4` explicitly. Verify `astro` version in `package-lock.json` stays at 5.7.x after install. |
| SVG `fill`/`stroke` ignores CSS custom variables in Safari | Test in Safari. If broken, fall back to `useStarlightTheme` hook + inline style props. Both approaches documented in Dev Notes. |
| React hydration mismatch (SSR vs client) | Use `client:load` which hydrates immediately. Avoid reading `document` during SSR — gate with `typeof document !== 'undefined'` checks. |
| Large bundle size from React | React 19 is ~40KB gzipped. Acceptable for one interactive page. This is an island — it doesn't affect other pages. |
| `npm ci` in CI fails with new deps | Ensure `package-lock.json` is committed (it is per Story 19.1). CI workflow uses `npm ci`. |
| Overrides conflict (`@astrojs/sitemap`, `zod`) | Story 19.1 already has `"overrides"` in `package.json` for sitemap 3.6.1 and zod 3.25.76. Verify these still resolve after adding React deps. |

### Previous Story Intelligence

**From Story 19.1 (done):**
- Astro 5.7.10, Starlight 0.37.x — DO NOT upgrade
- `overrides` in `package.json` for sitemap/zod conflicts
- `tsconfig.json` currently minimal (`extends: "astro/tsconfigs/strict"`)
- `npm run build` and `npm run check` are the automated quality gates
- Port 4322, custom fonts (Inter, IBM Plex Mono)

**From Story 19.3 (done):**
- Domain model has 6 objects (expanded from 5): Population, Policy, Orchestrator, Engine, Results, Indicators
- "Orchestrator" replaced "Simulation" intentionally; "Indicators" added explicitly
- Mermaid `flowchart LR` with Population+Policy converging into Orchestrator
- `<details>`/`<summary>` pattern for code sections — blank lines required
- Anchor IDs auto-generated: `#population`, `#policy`, `#orchestrator`, `#engine`, `#results`, `#indicators`
- `{/* */}` for JSX comments in MDX, never `<!-- -->`

**From Story 19.4 (done):**
- MDX `<details>` sections work well for progressive disclosure
- `npm run build` catches MDX syntax errors
- Mermaid node labels: use `\n` not `<br/>` in astro-mermaid

**Antipatterns to avoid (from Stories 19.1 and 19.3):**
- Do NOT create compound acceptance criteria (19.1 lesson) — each AC is independently verifiable
- Do NOT conflate PR-verifiable gates with post-merge deployment steps
- Do NOT make OpenFisca a hard requirement — it's optional via adapter

### References

- [Epics: `_bmad-output/planning-artifacts/epics.md`] — Epic 19 Story 19.5 acceptance criteria
- [Domain model page: `docs/src/content/docs/domain-model.mdx`] — current Mermaid diagram and 6-section content
- [Story 19.3: `_bmad-output/implementation-artifacts/19-3-create-getting-started-guide-and-domain-model.md`] — domain object definitions, MDX patterns
- [Story 19.1: `_bmad-output/implementation-artifacts/19-1-scaffold-starlight-site-with-brand-theming-and.md`] — version pins, site scaffold, Astro 5.x constraint
- [Story 19.4: `_bmad-output/implementation-artifacts/19-4-create-contributing-page-and-api-reference.md`] — MDX expandable sections pattern
- [Astro React integration docs: https://docs.astro.build/en/guides/integrations-guide/react/]
- [Starlight using components: https://starlight.astro.build/components/using-components/]
- [Starlight CSS & styling: https://starlight.astro.build/guides/css-and-tailwind/]
- [Astro client directives: https://docs.astro.build/en/reference/directives-reference/]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None.

### Completion Notes List

- Installed `@astrojs/react@4.4.2`, `react@^19.0.0`, `react-dom@^19.0.0`, `@types/react`, `@types/react-dom` — version pins held; `astro` stayed at `5.7.10`, `zod` at `3.25.76`
- Added `react()` integration to `astro.config.mjs` between `mermaid()` and `starlight()`
- Updated `tsconfig.json` with `jsx: "react-jsx"` and `jsxImportSource: "react"` compiler options
- Created `DomainModelDiagram.tsx`: inline SVG with 6 nodes, 5 directed edges, `useState` for selection, `role="button"` + `tabIndex` + keyboard handlers (Enter/Space/Escape) satisfying AC 7
- CSS Module (`DomainModelDiagram.module.css`) uses `--sl-color-*` variables exclusively — no hard-coded palette, light/dark toggle works without JS (AC 3)
- `useStarlightTheme` hook NOT needed — CSS custom properties on SVG elements work correctly via CSS Modules
- Replaced Mermaid block in `domain-model.mdx` with `import DomainModelDiagram` + `<DomainModelDiagram client:load />` — all existing sections preserved intact (AC 4)
- `npm run build`: 0 errors, component bundles as `DomainModelDiagram.PONpCjxg.js` (4.98 kB gzipped 2.43 kB) + CSS module (AC 5)
- `npm run check`: 0 errors, 0 warnings (AC 6)
- [Code Review Synthesis] Removed `role="img"` from SVG — ARIA anti-pattern that suppressed child `role="button"` semantics for AT (AC 7 fix)
- [Code Review Synthesis] Added `<title id="domain-diagram-title">` + `aria-labelledby` for accessible SVG naming without `role="img"`
- [Code Review Synthesis] Added document-level `mousedown` listener via `useEffect` + `useRef` for click-outside-dismiss (AC 2 fix)
- [Code Review Synthesis] Replaced `tagName === 'svg'` with `e.target === e.currentTarget` for type-safe SVG background click detection
- [Code Review Synthesis] Added `outline: none` on `.domainNode:focus` and `:focus-visible` rule to prevent double focus indicator
- [Code Review Synthesis] Added `aria-live="polite"` to detail panel for AT announcement on keyboard activation
- [Code Review Synthesis] Added `type="button"` to dismiss button for defensive form-context safety
- [Code Review Synthesis] `npm run build`: 0 errors; `npm run check`: 0 errors, 0 warnings — all quality gates pass after fixes

### File List

**Created:**
- `docs/src/components/DomainModelDiagram.tsx`
- `docs/src/components/DomainModelDiagram.module.css`

**Modified:**
- `docs/astro.config.mjs` — added `react()` integration
- `docs/tsconfig.json` — added JSX compiler options
- `docs/package.json` — new dependencies added via `npm install`
- `docs/package-lock.json` — updated by `npm install`
- `docs/src/content/docs/domain-model.mdx` — replaced Mermaid block with React component

## Senior Developer Review (AI)

### Review: 2026-03-23
- **Reviewer:** AI Code Review Synthesis
- **Evidence Score:** 3.5 → Changes Requested
- **Issues Found:** 7
- **Issues Fixed:** 6
- **Action Items Created:** 1

#### Review Follow-ups (AI)
- [ ] [AI-Review] LOW: Hardcoded `13px` font-size on SVG node labels — consider `0.8rem` or Starlight design token for user font-scale accessibility (`docs/src/components/DomainModelDiagram.module.css`)
