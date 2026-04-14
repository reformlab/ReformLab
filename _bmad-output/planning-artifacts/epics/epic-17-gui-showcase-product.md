# Epic 17: GUI Showcase Product

**User outcome:** Non-coding analyst can operate the complete Phase 2 workflow through a web GUI: build populations from real data, design policy portfolios, run simulations, browse persistent results, and compare across portfolios.

**Status:** backlog

**Builds on:** All Phase 2 epics (EPIC-11 through EPIC-16), EPIC-6 (Phase 1 GUI prototype and FastAPI backend)

**PRD Refs:** FR32, FR37, FR39, FR43, FR45

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-1701 | Story | P0 | 8 | Build Data Fusion Workbench GUI | backlog | FR37, FR39 |
| BKL-1702 | Story | P0 | 5 | Build Policy Portfolio Designer GUI | backlog | FR43 |
| BKL-1703 | Story | P0 | 5 | Build Simulation Runner with progress and persistent results | backlog | FR32, FR45 |
| BKL-1704 | Story | P0 | 8 | Build Comparison Dashboard with multi-portfolio side-by-side | backlog | FR32, FR45 |
| BKL-1705 | Story | P0 | 5 | Build Behavioral Decision Viewer | backlog | FR45 |
| BKL-1706 | Task | P0 | 5 | Implement FastAPI endpoints for Phase 2 GUI operations | backlog | FR32 |
| BKL-1707 | Task | P0 | 3 | Implement persistent result storage and retrieval | backlog | FR45 |
| BKL-1708 | Story | P0 | 5 | Build end-to-end GUI workflow tests | backlog | FR32 |

## Epic-Level Acceptance Criteria

- Analyst can build a population from real data sources through the GUI without writing code.
- Analyst can choose merge methods with plain-language explanations in the GUI.
- Analyst can compose and run a policy portfolio through the GUI.
- Completed simulation results persist across browser sessions — no need to re-run.
- Analyst can compare multiple portfolio results side-by-side.
- GUI displays behavioral decision outcomes (discrete choice results) per household group.
- All GUI operations map to API endpoints tested independently.
- Frontend tests cover core workflows (data fusion, portfolio creation, simulation, comparison).

---

## Story 17.1: Build Data Fusion Workbench GUI

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**PRD Refs:** FR37, FR39

### Acceptance Criteria

- Given the Data Fusion Workbench screen, when the analyst opens it, then available data sources are listed with metadata (name, description, variables, record count, source URL).
- Given the source browser, when the analyst selects two or more data sources, then the GUI shows overlapping and unique variables and prompts merge method selection.
- Given merge method selection, when the analyst chooses a method (e.g., statistical matching, calibration weighting), then a plain-language explanation of the method's assumptions and trade-offs is displayed.
- Given a configured merge, when the analyst clicks "Generate Population", then the population generation pipeline runs and the GUI shows progress.
- Given a generated population, when previewed, then the GUI displays summary statistics (record count, variable distributions, key demographics) and validation results against known marginals.
- Given the workbench, when the analyst adjusts merge parameters and regenerates, then the new population reflects the changed configuration.

---

## Story 17.2: Build Policy Portfolio Designer GUI

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**PRD Refs:** FR43

### Acceptance Criteria

- Given the Portfolio Designer screen, when the analyst opens it, then available policy templates are listed with descriptions, configurable parameters, and category tags.
- Given the template browser, when the analyst selects templates, then they are added to a portfolio composition panel where parameters can be configured per template.
- Given a portfolio with multiple templates, when the analyst reorders or removes templates, then the portfolio updates accordingly.
- Given template parameters, when the analyst configures year-indexed schedules (e.g., carbon tax trajectory), then a visual timeline editor allows setting values per year.
- Given a complete portfolio configuration, when saved, then the portfolio is persisted as a named configuration that can be loaded, cloned, or edited later.

---

## Story 17.3: Build Simulation Runner with progress and persistent results

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 17.7
**PRD Refs:** FR32, FR45

### Acceptance Criteria

- Given a configured population and policy portfolio, when the analyst clicks "Run Simulation", then the simulation starts and a progress indicator shows current year, estimated remaining time, and completion percentage.
- Given a running simulation, when it completes, then results are automatically saved to persistent storage with a unique run ID, timestamp, and configuration summary.
- Given persistent results, when the analyst returns to the application (even after closing the browser), then all previously completed runs are listed and browsable.
- Given a completed run in the results list, when the analyst clicks it, then the full result detail view opens with indicators, panel data summary, and run manifest.

---

## Story 17.4: Build Comparison Dashboard with multi-portfolio side-by-side

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 17.3
**PRD Refs:** FR32, FR45

### Acceptance Criteria

- Given two or more completed simulation runs, when the analyst selects them for comparison, then a side-by-side dashboard displays key indicators (distributional, welfare, fiscal, environmental) for each run.
- Given the comparison view, when the analyst inspects distributional indicators, then charts show impact by income decile for each portfolio with clear visual differentiation.
- Given the comparison view, when the analyst hovers over or selects a specific indicator, then a detail panel shows the breakdown and methodology.
- Given the comparison dashboard, when the analyst toggles between absolute and relative views, then the charts and tables update to show the selected representation.
- Given the comparison dashboard, when populated with runs that include behavioral responses (discrete choice), then indicators reflect post-behavioral-response outcomes (not just static impacts).

---

## Story 17.5: Build Behavioral Decision Viewer

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 17.3
**PRD Refs:** FR45

### Acceptance Criteria

- Given a completed run with discrete choice results, when the analyst opens the Behavioral Decision Viewer, then aggregate decision outcomes are displayed per domain (vehicle fleet composition, heating system mix over time).
- Given the decision viewer, when the analyst selects a decision domain (e.g., vehicle), then year-by-year transition charts show the evolution of the fleet (e.g., EV adoption curve, diesel phase-out).
- Given the decision viewer, when the analyst filters by household group (e.g., income decile, location), then the decision outcomes update to show group-specific transition patterns.
- Given the decision viewer, when the analyst clicks on a specific year, then a detail panel shows choice probabilities and the distribution of chosen alternatives for that year.

---

## Story 17.6: Implement FastAPI endpoints for Phase 2 GUI operations

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**PRD Refs:** FR32

### Acceptance Criteria

- Given the Phase 2 backend capabilities, when the GUI needs them, then FastAPI endpoints exist for: population generation (start, status, result), portfolio CRUD (create, read, update, delete, list), simulation execution (start, progress, result), result listing and retrieval, and comparison queries.
- Given each API endpoint, when called with valid parameters, then it returns correctly typed JSON responses matching documented schemas.
- Given each API endpoint, when called with invalid parameters, then it returns appropriate error codes (400, 404, 422) with descriptive error messages.
- Given API endpoints, when tested independently (without the GUI), then all endpoints pass integration tests.

---

## Story 17.7: Implement persistent result storage and retrieval

**Status:** backlog
**Priority:** P0
**Estimate:** 3

**PRD Refs:** FR45

### Acceptance Criteria

- Given a completed simulation, when results are stored, then all outputs (indicators, panel summary, manifest, configuration) are persisted to disk in a structured directory per run.
- Given stored results, when listed via API, then the response includes: run ID, timestamp, population summary, portfolio name, and status.
- Given a stored result, when retrieved by run ID, then all artifacts are returned (indicators, panel data, manifest, configuration used).
- Given stored results, when the application restarts, then all previously stored results remain accessible.

---

## Story 17.8: Build end-to-end GUI workflow tests

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 17.4, Story 17.5
**PRD Refs:** FR32

### Acceptance Criteria

- Given the frontend test suite, when run, then it covers the core analyst workflow: open Data Fusion Workbench → configure and generate population → open Portfolio Designer → compose portfolio → run simulation → view results → compare two runs.
- Given the test suite, when run in CI, then all tests pass.
- Given the test suite, when a GUI component changes, then relevant tests fail and identify the broken workflow step.
- Given the test suite, when inspected, then it covers: data fusion (source selection, merge method, generation), portfolio design (template selection, parameter configuration, save), simulation (run, progress, completion), results (persistence, retrieval, browsing), and comparison (multi-run selection, side-by-side display).

## Scope Notes

- **Built last, shown first** — the GUI integrates all backend capabilities from EPIC-11 through EPIC-16.
- **Notebook demos from prior epics** directly inform GUI screen design — each notebook workflow maps to a GUI screen.
- **Tech stack:** React + TypeScript + Shadcn/ui + Tailwind v4 (same as Phase 1 prototype).
- **Key new GUI sections:**
  - **Data Fusion Workbench** — browse datasets, select sources, choose merge methods, preview population, validate against marginals
  - **Policy Portfolio Designer** — browse templates, compose portfolios, configure parameters per policy
  - **Simulation Runner** — run with configured population + portfolio, show progress
  - **Persistent Results** — completed simulations stored and browsable
  - **Comparison Dashboard** — side-by-side across portfolios with distributional/welfare/fiscal indicators
  - **Behavioral Decision Viewer** — explore household decisions from discrete choice model

---
