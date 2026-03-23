# Epic 19 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 19-1 (2026-03-23)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | AC7 conflates PR-verifiable build with post-merge deployment requiring external admin setup, making pass/fail ambiguous | Rewrote AC7 to clearly scope PR acceptance to build/upload success; explicit note that full deploy is a post-merge out-of-band step, not a story blocker. |
| high | AC10 is a compound criterion (4 independent assertions) allowing ambiguous partial-done | Replaced AC10 with 4 labeled atomic sub-criteria (10a–10d) — each independently verifiable; exact task labels now embedded in AC10c eliminating Dev Notes duplication. |

## Story 19-3 (2026-03-23)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | OpenFisca as hard requirement | Rewrote intro sentence from "with Python 3.13+ and OpenFisca France" to "with Python 3.13+; OpenFisca France is the default computation backend and ships with the standard install" — preserves usability guidance while accurately reflecting the optional-by-adapter architecture |
| high | `custom.css` contradiction | Updated "Files NOT to Modify" entry for custom.css to note that fallback CSS edits are permitted if `<details>` renders unstyled — eliminates direct contradiction with the Risks table |
| medium | "Orchestrator is core engine" naming collision | Changed "The orchestrator is ReformLab's core engine" to "The orchestrator is ReformLab's coordination layer" — avoids using "engine" for two separate domain concepts on the same page |
| medium | Domain object set change undocumented | Added "Domain Object Set Rationale" section explaining the intentional change from epics.md definition (Simulation replaced by Orchestrator + Indicators added), with traceability note |
| medium | Markdown table in `<details>` not in testing checklist | Added explicit verification item to Testing Strategy for the Indicators `<details>` table rendering as HTML table |
| medium | `<Steps>` fallback contradicts AC 1 | Updated Risks table entry to say "raise a blocker — do not substitute `<ol>` without explicitly revising AC 1" instead of permitting a silent fallback |

## Story 19-5 (2026-03-23)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `npm install @astrojs/react` missing `@^4.4` version pin | Install command updated to `npm install @astrojs/react@^4.4 react@^19.0.0 react-dom@^19.0.0` with post-install verification steps added |
| high | AC 3 ("works correctly", "no flash of wrong theme") not objectively testable | Rewritten to specify `--sl-color-*` usage and "updates without page reload and no intermediate hard-coded palette is visible" |
| high | Detail panel dismiss behavior (click-outside, click-same-node) only in Dev Notes, not in ACs | Promoted to AC 2 body |
| high | AC 2 references "existing intro paragraph" without canonical source lock | AC 2 now references the Node Content Data table in Dev Notes |
| high | No accessibility requirements anywhere in story | Added AC 7 covering Tab navigation, Enter/Space activation, Escape dismiss, `role="button"`, visible focus, `aria-label` |
| medium | Edge count stated as "6 edges" but Edge Definitions lists 5 | Changed to "6 nodes and 5 edges" |
| medium | CSS styling approach contradiction — story says "co-locate" but shows descendant selectors incompatible with inline styles | Files NOT to Modify note updated to explicitly recommend CSS Modules; CSS example updated with camelCase module class names and import pattern; `DomainModelDiagram.module.css` added to Files to Create |
| medium | SVG coordinates listed as required field but no values provided | Added concrete coordinate reference block (viewBox, node x/y, edge endpoints) |
| medium | Task 3 "optional enhancement" for anchor scrolling creates scope ambiguity | Task updated to clarify the "Learn more" link is a standard `href="#id"` hash link — no JS auto-scroll needed |
| medium | `.astro/types.d.ts` may not exist in clean CI checkout before `npm run check` | Added note to tsconfig section |
| low | `useStarlightTheme` hook defaults to `'dark'` incorrectly for light-preference users | Fallback now uses `window.matchMedia('(prefers-color-scheme: dark)').matches` |
| dismissed | INVEST "Negotiable" violation — story is over-prescriptive (SVG approach, integration order, `client:load`) | FALSE POSITIVE: The prescribed guidance is appropriate for a docs-only component with no external library. Prescriptive dev notes reduce implementation variance without constraining outcomes. Not an INVEST violation in this context. |
| dismissed | INVEST "Independent" violation — hidden coupling to Story 19.3 heading anchors | FALSE POSITIVE: Story 19.3 is complete and the anchor IDs (`#population`, etc.) are generated from heading text that won't change. This is a stable, well-documented dependency, not a blocking one. |
| dismissed | Missing no-JS fallback requirement | FALSE POSITIVE: The story explicitly chooses `client:load` for above-fold UX. Requiring a static fallback for a docs site interactive diagram would add scope without meaningful benefit. Excessive for this story size. |
| dismissed | Missing mobile/narrow viewport AC | FALSE POSITIVE: Story explicitly states "primary viewport for docs is desktop (1280px+)" and calls mobile stacking a stretch goal. This is a deliberate scope boundary, not a gap. Out of scope for 19.5. |
| dismissed | Canonicalize Node Detail Content — node descriptions not "frozen" in ACs | FALSE POSITIVE: The Node Content Data section already provides exact canonical text for all 6 nodes. AC 2 now references that table directly. No further canonicalization needed. |

## Story 19-6 (2026-03-23)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `driver.js@^1.4.0` version pin unverified — if v1.4.0 does not exist in the npm registry, Task 1 fails immediately and the entire story is blocked | Changed pin to `^1.0.0` in Task 1 subtask, Install Command, and post-install verification; added risk table entry; noted to record resolved version in completion notes. |
| high | AC2 specifies "Step 3 of 6" format but `showProgress: true` renders "3 / 6" by default — no `progressText` override in sample config | Updated Task 2 config subtask to include `progressText: 'Step {{current}} of {{total}}'`; added same option to the `driver()` call in the component sample code. |
| high | AC2 says "one-sentence description" but all 6 provided step copy examples are two sentences — direct conflict between AC and the implementation contract | Changed AC2 to "1–2 sentence description" and "Step X of 6" format (non-prescriptive example removed); the well-crafted step descriptions are retained as-is. |
| medium | Selector verification is buried as a risk note; no up-front decision gate tells the dev agent to verify selectors before writing tour code — increases chance of silent misses | Added a `> **Implementation decision required**` block at the top of the CSS Selector Strategy section with a browser console smoke check and explicit branching decision. |
| low | `startTour()` creates a new driver instance without destroying any prior instance — ghost instances possible in edge cases / automated testing | Added `driverRef.current?.destroy();` guard at the start of `startTour()` in the sample code. |
| low | Population and Policy nodes are at x=20 (left edge of SVG) — auto-positioned popovers may clip against the viewport at narrow widths | Added `side: 'right'` to the `popover` config for both Population and Policy steps in the `tourSteps` sample. |
| dismissed | AC5 backdrop-click dismissal not guaranteed by explicit driver.js config | FALSE POSITIVE: driver.js v1.x defaults `allowClose: true`, which enables backdrop-click dismissal. The existing visual verification checklist ("Backdrop click: dismisses tour") already covers this. No explicit config override is needed for default behavior; adding `allowClose: true` to the config would be noise. The visual test checklist is the correct validation layer here. |
| dismissed | No pre-flight guard for missing selector elements causing "no console errors" violation | FALSE POSITIVE: driver.js v1.x silently skips steps whose element is not found — it does not throw or produce console errors. AC5's "no console errors" is not violated by a missing selector. A smoke check note was added to Dev Notes as documentation, which is sufficient. |
| dismissed | AC3 "Done" button label not deterministically guaranteed by config | FALSE POSITIVE: driver.js v1.x automatically replaces "Next" with "Done" (or equivalent finish label) on the final step when `showButtons: ['next', 'previous', 'close']` is configured. This is documented behavior, not an unspecified gap. No additional config is needed. |
| dismissed | AC4 arrow-key semantics not verified per-key — `allowKeyboardControl: true` insufficient | FALSE POSITIVE: `allowKeyboardControl: true` in driver.js v1.x enables right-arrow (next), left-arrow (previous), and Escape (close) by default — exactly the keys specified in AC4. These are the only keyboard controls the library exposes. The AC maps cleanly to the library's documented API. |
| dismissed | Overlay CSS override missing from theming sample | FALSE POSITIVE: driver.js uses `--driver-overlay-color` (a semi-transparent dark color) for the overlay, which works correctly in both Starlight light and dark themes without a Starlight variable mapping. AC6 says "no hard-coded palette visible" — the overlay uses its own CSS custom property, not a hard-coded value. No Starlight override is needed for the overlay. |
| dismissed | `data-tour-step` should be primary selector, not fallback | FALSE POSITIVE: The story's "Files NOT to Modify" constraint (DomainModelDiagram.tsx) reflects a deliberate decision to avoid cross-component coupling. The aria-label attributes were designed as the integration contract in Story 19.5. Making data-tour-step primary would require modifying DomainModelDiagram.tsx unconditionally, increasing story scope. The decision gate added to the selector strategy section addresses the risk without changing the primary approach. --- |
