# Epic 18: UX Polish & Aesthetic Overhaul

Status: planned

## Epic Summary

Cross-cutting UX improvements to transform the ReformLab frontend from a functional prototype into a polished, cohesive product. Addresses navigation coherence, visual refinement, component deduplication, information hierarchy, and aesthetic warmth identified during a comprehensive UX audit of all 9 screens built across Epics 6–17.

## Motivation

The frontend was built screen-by-screen across independent epics. Each screen works well in isolation, but the overall experience feels like 5 separate apps stitched together. There is no persistent sense of workflow progress, visual design is austere (no rounded corners, no shadows, no brand presence), and several components are duplicated across screens. This epic consolidates these issues into a coherent improvement pass.

## Stories

| ID | Story | SP | Priority |
|----|-------|----|----------|
| 18.1 | Implement workflow navigation rail | 5 | P0 |
| 18.2 | Visual polish pass (rounded corners, shadows, header, login) | 3 | P0 |
| 18.3 | Extract shared components (WorkbenchStepper, ErrorAlert, SelectionGrid) | 3 | P0 |
| 18.4 | Restructure results view with tabs and hierarchy | 5 | P0 |
| 18.5 | Consolidate configuration flow and split dense screens | 5 | P1 |
| 18.6 | Standardize form inputs and add loading skeletons | 3 | P1 |
| 18.7 | Repurpose right panel as contextual help | 5 | P1 |
| 18.8 | Chart polish and color palette refinement | 3 | P1 |

## Dependencies

- No backend changes required — all stories are frontend-only
- All existing tests must continue to pass after each story
- Stories 18.1–18.4 can be done in any order; 18.5–18.8 depend on 18.3 (shared components available)

## Exit Criteria

- All 9 screens use shared components (no duplicated WorkbenchStepper, no inline error displays)
- Persistent navigation rail visible in all view modes
- All containers have rounded corners and appropriate elevation
- Results view has clear information hierarchy with tabs
- All form inputs use shadcn Input component (no raw `<input>` elements)
- Visual regression: no broken layouts at 1280px+ viewport
