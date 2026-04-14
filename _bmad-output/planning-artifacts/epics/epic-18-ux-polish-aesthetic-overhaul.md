# Epic 18: UX Polish & Aesthetic Overhaul

**User outcome:** Non-coding analyst experiences a polished, cohesive product with persistent navigation, visual warmth, shared components, and clear information hierarchy — instead of separate screens stitched together.

**Status:** backlog

**Builds on:** EPIC-17 (GUI Showcase), EPIC-6 (Phase 1 GUI prototype)

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-1801 | Story | P0 | 5 | Implement workflow navigation rail | backlog | — |
| BKL-1802 | Story | P0 | 3 | Visual polish pass (rounded corners, shadows, header, login) | backlog | — |
| BKL-1803 | Story | P0 | 3 | Extract shared components (WorkbenchStepper, ErrorAlert, SelectionGrid) | backlog | — |
| BKL-1804 | Story | P0 | 5 | Restructure results view with tabs and hierarchy | backlog | — |
| BKL-1805 | Story | P1 | 5 | Consolidate configuration flow and split dense screens | backlog | — |
| BKL-1806 | Story | P1 | 3 | Standardize form inputs and add loading skeletons | backlog | — |
| BKL-1807 | Story | P1 | 5 | Repurpose right panel as contextual help | backlog | — |
| BKL-1808 | Story | P1 | 3 | Chart polish and color palette refinement | backlog | — |

## Epic-Level Acceptance Criteria

- All 9 screens use shared components (no duplicated WorkbenchStepper, no inline error displays).
- Persistent navigation rail visible in all view modes.
- All containers have rounded corners and appropriate elevation.
- Results view has clear information hierarchy with tabs.
- All form inputs use shadcn Input component (no raw `<input>` elements).
- Visual regression: no broken layouts at 1280px+ viewport.

---

## Story 18.1: Implement workflow navigation rail

**Status:** backlog
**Priority:** P0
**Estimate:** 5

### Acceptance Criteria

- Given the left panel, when the workspace loads, then the four navigation buttons are replaced by a vertical stepper showing workflow stages with numbered step indicators and connecting lines.
- Given a workflow stage, when the user has completed meaningful work in that stage, then the step indicator shows a checkmark icon instead of the stage number.
- Given each workflow stage in the nav rail, when there is relevant state, then a one-line summary is displayed below the stage label in muted text.
- Given the nav rail, when the analyst clicks any stage, then the main panel switches to that stage's view mode.
- Given the left panel, when scenarios exist, then ScenarioCards still appear below the navigation rail, separated by a visual divider.
- Given the left panel in collapsed state, when viewed, then the nav rail shows only the step indicator icons in a vertical column.

---

## Story 18.2: Visual polish pass (rounded corners, shadows, header, login)

**Status:** backlog
**Priority:** P0
**Estimate:** 3

### Acceptance Criteria

- Given all Card, section, and panel containers across all 9 screens, when rendered, then they use rounded corners.
- Given primary content containers, when rendered, then they use subtle shadows for depth.
- Given the main workspace header, when rendered, then it displays a gradient background with branding.
- Given the PasswordPrompt screen, when rendered, then the login card uses rounded corners, shadow, and brand mark.
- Given all existing screens, when rendered at 1280px+ viewport, then no layouts are broken.

---

## Story 18.3: Extract shared components (WorkbenchStepper, ErrorAlert, SelectionGrid)

**Status:** backlog
**Priority:** P0
**Estimate:** 3

### Acceptance Criteria

- Given WorkbenchStepper variants across screens, when refactored, then a single shared component is used everywhere.
- Given inline error displays, when refactored, then a shared ErrorAlert component is used.
- Given selection grid patterns, when refactored, then a shared SelectionGrid component is used.
- Given the refactored components, when all screens render, then no visual regressions occur.

---

## Story 18.4: Restructure results view with tabs and hierarchy

**Status:** backlog
**Priority:** P0
**Estimate:** 5

### Acceptance Criteria

- Given the results view, when a completed run is selected, then results are organized with tabs for different indicator categories.
- Given the results view, when browsing indicators, then information hierarchy distinguishes primary metrics from details.
- Given the results view, when switching between tabs, then content loads without full re-render.

---

## Story 18.5: Consolidate configuration flow and split dense screens

**Status:** backlog
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 18.3

### Acceptance Criteria

- Given dense configuration screens, when viewed, then content is split into logical sections or steps.
- Given the configuration flow, when navigating between sections, then state is preserved.

---

## Story 18.6: Standardize form inputs and add loading skeletons

**Status:** backlog
**Priority:** P1
**Estimate:** 3

**Dependencies:** Story 18.3

### Acceptance Criteria

- Given all form inputs, when rendered, then they use the shadcn Input component (no raw `<input>` elements).
- Given loading states, when data is being fetched, then skeleton placeholders are shown instead of blank areas.

---

## Story 18.7: Repurpose right panel as contextual help

**Status:** backlog
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 18.3

### Acceptance Criteria

- Given the right panel, when a workflow stage is active, then contextual help relevant to that stage is displayed.
- Given the right panel, when the user dismisses it, then it collapses and persists its state.

---

## Story 18.8: Chart polish and color palette refinement

**Status:** backlog
**Priority:** P1
**Estimate:** 3

**Dependencies:** Story 18.3

### Acceptance Criteria

- Given all chart components, when rendered, then they use a refined, consistent color palette.
- Given chart containers, when rendered within rounded parents, then they display correctly without clipping.

---
