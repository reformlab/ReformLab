# Story 19.6: Add Guided Product Tour (driver.js)

Status: done

## Story

As a **first-time visitor landing on the domain model page**,
I want a "Take the tour" button that launches a step-by-step guided walkthrough highlighting each core domain object in sequence with explanatory tooltips,
so that I understand the full data pipeline without needing to read the entire page or figure out the diagram on my own.

## Acceptance Criteria

1. **Tour trigger button:** Given the domain model page (`domain-model.mdx`), when visited, then a "Take the tour" button is visible above the interactive diagram. Clicking it starts the guided tour.
2. **Six-step highlight sequence:** Given the tour is active, when each step is displayed, then the corresponding SVG node group in the `DomainModelDiagram` component is highlighted with an overlay, and a tooltip shows the object's name, a 1–2 sentence description, and the step number in "Step X of 6" format.
3. **Tour navigation controls:** Given the tour is active, when a step is displayed, then the user can navigate via "Next" / "Previous" buttons, and the final step shows a "Done" button that closes the tour.
4. **Keyboard navigation:** Given the tour is active, when the user presses the right arrow key, then the tour advances to the next step; left arrow goes to the previous step; Escape dismisses the tour.
5. **Dismissible without errors:** Given the tour is active at any step, when the user clicks the overlay backdrop, presses Escape, or clicks the close (×) button, then the tour closes and the page returns to its normal interactive state (diagram click-to-select still works, no console errors).
6. **Light and dark mode:** Given the tour overlay and tooltips, when rendered in Starlight light or dark mode, then the overlay, popover background, and text colors adapt using `--sl-color-*` CSS custom properties — no hard-coded palette is visible in either theme.
7. **Build succeeds:** Given all changes in this story, when `npm run build` is run in `docs/`, then it completes with zero errors.
8. **TypeScript clean:** Given all changes, when `npm run check` is run in `docs/`, then it completes with zero errors.

## Tasks / Subtasks

- [x] Task 1: Install driver.js (AC: 7, 8)
  - [x] Run `npm install driver.js@^1.0.0` in `docs/`
  - [x] Verify `npm ls driver.js` shows `1.x.x`
  - [x] Verify `npm ls astro` still shows `5.7.10` (no accidental upgrade)
  - [x] Verify `npm run build` and `npm run check` pass with zero errors

- [x] Task 2: Create DomainModelTour component (AC: 2, 3, 4, 6)
  - [x] Create `docs/src/components/DomainModelTour.tsx`
  - [x] Import and configure `driver()` from `driver.js` with 6 tour steps targeting existing SVG node groups
  - [x] Import `driver.js/dist/driver.css` for base overlay/popover styles
  - [x] Create `docs/src/components/DomainModelTour.module.css` for Starlight theme overrides
  - [x] Override driver.js CSS custom properties to use `--sl-color-*` variables for light/dark mode
  - [x] Expose a `startTour()` trigger from the component (button click)
  - [x] Configure `showProgress: true`, `progressText: 'Step {{current}} of {{total}}'`, `showButtons: ['next', 'previous', 'close']`, and `allowKeyboardControl: true`

- [x] Task 3: Integrate tour into domain-model.mdx (AC: 1, 5)
  - [x] Import `DomainModelTour` in `domain-model.mdx`
  - [x] Add `<DomainModelTour client:load />` above the `<DomainModelDiagram client:load />` component
  - [x] Ensure the "Take the tour" button renders above the diagram
  - [ ] Verify tour dismiss returns to normal page state (diagram still interactive) — requires manual browser check

- [x] Task 4: Verify build and visual quality (AC: 5, 6, 7, 8)
  - [x] Run `npm run build` in `docs/` — zero errors
  - [x] Run `npm run check` in `docs/` — zero errors
  - [ ] Visual check: tour highlights each of 6 nodes in sequence — requires manual browser check
  - [ ] Visual check: light mode — overlay and tooltips use correct Starlight colors — requires manual browser check
  - [ ] Visual check: dark mode — overlay and tooltips use correct Starlight colors — requires manual browser check
  - [ ] Visual check: after dismiss, diagram click-to-select works normally — requires manual browser check

## Dev Notes

### Library Choice: driver.js (NOT shepherd.js)

**driver.js v1.4.0** is the chosen library. Rationale:
- **~5 KB gzipped**, zero dependencies (shepherd.js is ~25-30 KB + Floating UI dependency)
- **MIT license** (shepherd.js is AGPL-3.0 — requires paid license for commercial use)
- Built-in progress indicator, prev/next/done buttons, keyboard navigation
- SVG element highlighting via `getBoundingClientRect()` — works with inline SVG child elements
- Simple `useEffect` + `driver()` pattern in React — no context provider or wrapper library needed

### Install Command

```bash
cd docs
npm install driver.js@^1.0.0
```

**Post-install verification:**
- `npm ls driver.js` — must show `1.x.x` (record exact resolved version in completion notes)
- `npm ls astro` — must still show `5.7.10`
- `npm ls zod` — must still show `3.25.76` (existing override)

### Component Architecture

**File:** `docs/src/components/DomainModelTour.tsx`

The tour is a **separate component** from `DomainModelDiagram`. It renders only a "Take the tour" button and manages the driver.js instance lifecycle. It does NOT wrap or modify the diagram component.

**React integration pattern:**

```tsx
import { useCallback, useRef, useEffect } from 'react';
import { driver, type DriveStep } from 'driver.js';
import 'driver.js/dist/driver.css';
import styles from './DomainModelTour.module.css';

const tourSteps: DriveStep[] = [
  {
    element: '[aria-label="Population — click to learn more"]',
    popover: {
      title: 'Population',
      description: 'A dataset of representative households — income, housing, vehicles, energy use, and demographics. This is one of two inputs to the simulation pipeline.',
      side: 'right', // left-edge node; prevent popover clipping at narrow viewports
    },
  },
  {
    element: '[aria-label="Policy — click to learn more"]',
    popover: {
      title: 'Policy',
      description: 'The reform being evaluated — tax rates, exemptions, thresholds, and redistribution rules. Policies are composed into portfolios for comparison.',
      side: 'right', // left-edge node; prevent popover clipping at narrow viewports
    },
  },
  {
    element: '[aria-label="Orchestrator — click to learn more"]',
    popover: {
      title: 'Orchestrator',
      description: 'The core of ReformLab. It runs your simulation year by year, feeding households through computation, behavioral response, and state transition steps.',
    },
  },
  {
    element: '[aria-label="Engine — click to learn more"]',
    popover: {
      title: 'Engine',
      description: 'The computation backend that calculates household-level taxes and benefits. Default: OpenFisca France. Swappable via the adapter protocol.',
    },
  },
  {
    element: '[aria-label="Results — click to learn more"]',
    popover: {
      title: 'Results',
      description: 'Raw simulation output — a household-by-year panel dataset with every computed variable. Stored as Parquet, cached in memory.',
    },
  },
  {
    element: '[aria-label="Indicators — click to learn more"]',
    popover: {
      title: 'Indicators',
      description: 'Analytics computed from results — distributional, fiscal, geographic, and welfare metrics. The final output users interact with.',
    },
  },
];

export default function DomainModelTour() {
  const driverRef = useRef<ReturnType<typeof driver> | null>(null);

  useEffect(() => {
    return () => {
      // Clean up on unmount
      driverRef.current?.destroy();
    };
  }, []);

  const startTour = useCallback(() => {
    driverRef.current?.destroy(); // destroy any prior instance before creating a new one
    const driverInstance = driver({
      showProgress: true,
      progressText: 'Step {{current}} of {{total}}',
      showButtons: ['next', 'previous', 'close'],
      allowKeyboardControl: true,
      steps: tourSteps,
      popoverClass: 'reformlab-tour-popover',
    });
    driverRef.current = driverInstance;
    driverInstance.drive();
  }, []);

  return (
    <button
      type="button"
      className={styles.tourButton}
      onClick={startTour}
    >
      Take the tour
    </button>
  );
}
```

### CSS Selector Strategy for SVG Nodes

> **Implementation decision required — verify before writing selectors:**
> Open a browser console on the running dev server and run:
> ```js
> document.querySelector('[aria-label="Population — click to learn more"]')
> ```
> - If it returns the `<g>` element → use `aria-label` attribute selectors as written below.
> - If it returns `null` (em dash encoding mismatch or label text changed) → add `data-tour-step="population"` etc. to each `<g>` in `DomainModelDiagram.tsx` and use `[data-tour-step="population"]` selectors instead. Modifying `DomainModelDiagram.tsx` is permitted for this fallback.

The existing `DomainModelDiagram` component renders each node as a `<g>` element with `aria-label` attributes:

```html
<g role="button" aria-label="Population — click to learn more" ...>
<g role="button" aria-label="Policy — click to learn more" ...>
<g role="button" aria-label="Orchestrator — click to learn more" ...>
<g role="button" aria-label="Engine — click to learn more" ...>
<g role="button" aria-label="Results — click to learn more" ...>
<g role="button" aria-label="Indicators — click to learn more" ...>
```

driver.js accepts any CSS selector for `element`. Use **attribute selectors** on `aria-label` to target each node group. This avoids adding `data-*` attributes to the diagram component.

**Important:** driver.js highlights elements using `getBoundingClientRect()`. For SVG `<g>` elements, `getBoundingClientRect()` returns the bounding box of all child shapes (rect + text). This works correctly with the existing diagram layout.

**Note on missing selectors:** driver.js v1.x silently skips steps whose target element is not found in the DOM at navigation time — it does not throw. Verify all 6 selectors resolve before shipping: `document.querySelectorAll('[aria-label$="click to learn more"]').length === 6`.

### Theming: Starlight Light/Dark Mode

**File:** `docs/src/components/DomainModelTour.module.css`

driver.js uses CSS custom properties for its overlay and popover styling. Override them to use Starlight's `--sl-color-*` variables:

```css
/* Override driver.js theming to use Starlight CSS custom properties */
:global(.driver-popover.reformlab-tour-popover) {
  background-color: var(--sl-color-bg);
  color: var(--sl-color-text);
}

:global(.driver-popover.reformlab-tour-popover .driver-popover-title) {
  color: var(--sl-color-text-accent);
  font-family: var(--sl-font);
}

:global(.driver-popover.reformlab-tour-popover .driver-popover-description) {
  color: var(--sl-color-text);
  font-family: var(--sl-font);
}

:global(.driver-popover.reformlab-tour-popover .driver-popover-progress-text) {
  color: var(--sl-color-gray-3);
}

:global(.driver-popover.reformlab-tour-popover .driver-popover-navigation-btns button) {
  background-color: var(--sl-color-accent);
  color: var(--sl-color-bg);
  border: none;
  border-radius: 4px;
  padding: 0.375rem 0.75rem;
  font-family: var(--sl-font);
  cursor: pointer;
}

:global(.driver-popover.reformlab-tour-popover .driver-popover-close-btn) {
  color: var(--sl-color-gray-3);
}

.tourButton {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid var(--sl-color-accent);
  border-radius: 6px;
  background: transparent;
  color: var(--sl-color-accent);
  font-family: var(--sl-font);
  font-size: 0.875rem;
  cursor: pointer;
  margin-bottom: 1rem;
  transition: background-color 0.15s, color 0.15s;
}

.tourButton:hover {
  background-color: var(--sl-color-accent);
  color: var(--sl-color-bg);
}
```

**Key pattern:** Use `:global()` selector from CSS Modules to target driver.js's generated DOM elements. The `popoverClass: 'reformlab-tour-popover'` option on the driver instance scopes overrides to this tour only.

### MDX Integration

In `domain-model.mdx`, add the tour component **above** the diagram:

```mdx
import DomainModelDiagram from '../../components/DomainModelDiagram';
import DomainModelTour from '../../components/DomainModelTour';

ReformLab is built around six core objects that work together to produce distributional impact analysis. Click any object to learn more, or take a guided tour.

<DomainModelTour client:load />

<DomainModelDiagram client:load />
```

**MDX rules (from Stories 19.2–19.4):**
- Import statements after frontmatter, before content
- Use `{/* */}` for JSX comments, not `<!-- -->`
- Blank lines required around JSX components for MDX paragraph parsing

### Tour Step Order

The tour follows the data pipeline flow (left to right, matching the diagram layout):

1. **Population** — "A dataset of representative households..." (top-left input)
2. **Policy** — "The reform being evaluated..." (bottom-left input)
3. **Orchestrator** — "The core of ReformLab..." (center, convergence point)
4. **Engine** — "The computation backend..." (center-right)
5. **Results** — "Raw simulation output..." (right)
6. **Indicators** — "Analytics computed from results..." (far right, final output)

This mirrors the pipeline: inputs → processing → outputs.

### Files to Create

| File | Purpose |
|------|---------|
| `docs/src/components/DomainModelTour.tsx` | Tour trigger button + driver.js lifecycle management |
| `docs/src/components/DomainModelTour.module.css` | Starlight theme overrides for driver.js popover + tour button styles |

### Files to Modify

| File | Change |
|------|--------|
| `docs/src/content/docs/domain-model.mdx` | Import `DomainModelTour`, add `<DomainModelTour client:load />` above diagram, update intro text |
| `docs/package.json` | New `driver.js` dependency (via `npm install`, auto-updated) |
| `docs/package-lock.json` | Updated by `npm install` |

### Files NOT to Modify

- `docs/src/components/DomainModelDiagram.tsx` — the tour targets existing DOM elements via CSS selectors; no changes to the diagram component are needed (unless aria-label selectors don't work, in which case add `data-tour-step` attributes as a fallback)
- `docs/src/components/DomainModelDiagram.module.css` — tour styling is in its own CSS Module
- `docs/astro.config.mjs` — no config changes needed (React integration already set up in Story 19.5)
- `docs/tsconfig.json` — no changes needed
- `docs/src/styles/custom.css` — tour styles go in the component's CSS Module, not the global stylesheet

### Client Directive

Use **`client:load`** for the tour component. The button must be interactive immediately — it's the first CTA above the fold. `client:visible` would show a non-functional button until hydration completes.

### driver.js CSS Import

driver.js requires importing its base CSS: `import 'driver.js/dist/driver.css';`

This import goes in the React component file. Astro's build system will bundle it with the component's island. The CSS will only load on pages that use the tour component (island isolation).

### Testing Strategy

No automated tests for static docs. Quality gates:

1. `npm run build` in `docs/` — zero errors, all pages render
2. `npm run check` in `docs/` — zero TypeScript errors
3. `npm run preview` — visual verification:
   - Domain model page: "Take the tour" button visible above the diagram
   - Click "Take the tour": overlay appears, first step highlights Population node
   - Next button: advances through all 6 steps in pipeline order
   - Previous button: navigates back to prior step
   - Progress indicator: shows "Step X of 6" at each step
   - Close (×): dismisses tour at any step, returns to normal page state
   - Backdrop click: dismisses tour
   - Escape key: dismisses tour
   - After tour dismiss: diagram click-to-select still works, no console errors
   - Light mode: overlay semi-transparent dark, popover uses Starlight light colors
   - Dark mode: overlay semi-transparent dark, popover uses Starlight dark colors
   - Keyboard: right/left arrow keys navigate steps, Escape dismisses

### Risks

| Risk | Mitigation |
|------|------------|
| `driver.js` types missing or incomplete | driver.js ships its own TypeScript declarations (since v1.0). If `npm run check` flags type issues, add `// @ts-expect-error` with a comment, or create a minimal `driver.js.d.ts` declaration. |
| `driver.js@^1.0.0` resolves to unexpected major version | `^1.0.0` accepts any v1.x release. Run `npm view driver.js versions` to see available releases before installing. Record the exact resolved version in completion notes. |
| aria-label CSS selectors don't match | Test with `document.querySelector('[aria-label="Population — click to learn more"]')` in browser console first. If special characters (em dash) cause issues, fall back to `data-tour-step` attributes on the diagram component. |
| SVG `<g>` element `getBoundingClientRect()` returns wrong position after scroll | driver.js recalculates position on each step transition. The SVG uses `viewBox` with `width="100%"`, so `getBoundingClientRect()` reflects the rendered (scaled) position. Test by scrolling the page before starting the tour. |
| driver.js CSS conflicts with Starlight styles | Scope all overrides under the `.reformlab-tour-popover` class (set via `popoverClass` option). Use `:global()` in CSS Modules to target driver.js DOM. |
| `npm install driver.js` triggers Astro version bump | driver.js has zero dependencies, so no transitive dep risk. Still verify `npm ls astro` shows `5.7.10` after install. |
| Tour popover obscures SVG node it's highlighting | driver.js auto-positions popovers (top/bottom/left/right) based on available viewport space. Default behavior should work for the horizontal diagram layout. If a specific step needs manual positioning, use the `side` property on that step's `popover` config. |

### Previous Story Intelligence

**From Story 19.5 (done):**
- React integration is set up: `@astrojs/react@4.4.2`, `react@^19`, `react-dom@^19`, JSX config in tsconfig
- `DomainModelDiagram.tsx` already exists with 6 clickable nodes using `aria-label` attributes
- CSS Modules with `--sl-color-*` variables pattern established — follow the same approach for tour theming
- `client:load` directive is the standard for above-the-fold interactive components
- Component directory: `docs/src/components/`

**From Story 19.1 (done):**
- Astro 5.7.10, Starlight 0.37.x — DO NOT upgrade
- `overrides` in `package.json` for sitemap/zod conflicts
- `npm run build` and `npm run check` are the automated quality gates
- Port 4322, custom fonts (Inter via `--sl-font`, IBM Plex Mono via `--sl-font-mono`)

**From Stories 19.3–19.4 (done):**
- MDX import pattern: imports after frontmatter, blank lines around components
- `{/* */}` for JSX comments, never `<!-- -->`
- Anchor IDs: `#population`, `#policy`, `#orchestrator`, `#engine`, `#results`, `#indicators`

**Antipatterns to avoid (from Stories 19.1 and 19.3):**
- Do NOT create compound acceptance criteria — each AC is independently verifiable
- Do NOT conflate PR-verifiable gates with post-merge deployment steps
- Do NOT modify the diagram component unless strictly necessary (prefer targeting existing DOM)

### References

- [Epics: `_bmad-output/planning-artifacts/epics.md`] — Epic 19 Story 19.6 acceptance criteria
- [Story 19.5: `_bmad-output/implementation-artifacts/19-5-build-interactive-domain-model-react-mdx-component.md`] — React integration setup, diagram component, CSS Module theming pattern
- [DomainModelDiagram: `docs/src/components/DomainModelDiagram.tsx`] — target component with 6 aria-labeled node groups
- [driver.js docs: https://driverjs.com/docs/installation]
- [driver.js GitHub: https://github.com/kamranahmedse/driver.js]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None.

### Completion Notes List

- driver.js@1.4.0 installed; astro@5.7.10, zod@3.25.76 unchanged.
- Aria-label selectors confirmed present in `DomainModelDiagram.tsx` as `${node.label} — click to learn more` (em dash U+2014). Used Unicode escape `\u2014` in selector strings to avoid encoding issues.
- `DomainModelTour.tsx`: React component with `useRef` for driver instance lifecycle, `useEffect` cleanup on unmount, `useCallback` for `startTour`. Configures `showProgress`, `progressText`, `showButtons`, `allowKeyboardControl`, `popoverClass`.
- `DomainModelTour.module.css`: Starlight theme overrides scoped under `.reformlab-tour-popover` via `:global()` CSS Modules selector. Uses `--sl-color-*` variables throughout for light/dark mode support.
- `domain-model.mdx`: Added import and `<DomainModelTour client:load />` above diagram with blank line separators per MDX rules.
- `npm run check` — 0 errors, 0 warnings. `npm run build` — complete, 7 pages built, zero errors.
- Visual checks (tour sequence, light/dark mode colors, post-dismiss diagram interactivity) require manual browser verification via `npm run preview`.

### File List

- `docs/src/components/DomainModelTour.tsx` (created)
- `docs/src/components/DomainModelTour.module.css` (created)
- `docs/src/content/docs/domain-model.mdx` (modified)
- `docs/package.json` (modified — driver.js dependency added)
- `docs/package-lock.json` (modified — lockfile updated)
