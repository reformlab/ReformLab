# Epic 23: Live OpenFisca Runtime and Executable Population Alignment

**User outcome:** Analyst runs the web product against the actual selected population through live OpenFisca by default, keeps existing indicator/result behavior, and uses precomputed outputs only for explicit replay or demo flows.

**Status:** backlog

**Builds on:** EPIC-1 (computation adapter and data layer), EPIC-9 (OpenFisca adapter hardening), EPIC-17 (GUI showcase product), EPIC-20 (workspace alignment), EPIC-22 (Scenario-stage fit)

**PRD Refs:** FR2, FR3, FR4, FR5, FR11, FR18, FR25-FR28, FR32, FR32a, FR32c, FR-RUNTIME-1, FR-RUNTIME-2, FR-RUNTIME-3, FR-RUNTIME-4, FR-RUNTIME-5

**Primary source documents:**
- `_bmad-output/planning-artifacts/prd.md`
- `_bmad-output/planning-artifacts/architecture.md`
- `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, dated 2026-04-01)
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-01.md`

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-2301 | Story | P0 | 5 | Define explicit runtime-mode contract and default-live execution semantics | backlog | FR25-FR28, FR32c, FR-RUNTIME-1, FR-RUNTIME-4 |
| BKL-2302 | Story | P0 | 5 | Make bundled and uploaded populations executable through a unified population resolver | backlog | FR5, FR32a, FR-RUNTIME-2, FR-RUNTIME-3 |
| BKL-2303 | Story | P0 | 8 | Normalize live OpenFisca results into the stable app-facing output schema | backlog | FR3, FR4, FR11, FR18, FR-RUNTIME-5 |
| BKL-2304 | Story | P0 | 8 | Switch web runs to live OpenFisca by default and isolate replay mode to explicit paths | backlog | FR2, FR27, FR32, FR-RUNTIME-1, FR-RUNTIME-4 |
| BKL-2305 | Story | P0 | 5 | Extend preflight, manifests, and result metadata with runtime and population provenance | backlog | FR4, FR25-FR28, FR32c, FR-RUNTIME-2 |
| BKL-2306 | Story | P1 | 5 | Add regression coverage and operator docs for live default runs and replay smoke flows | backlog | FR18, FR25, FR32, FR-RUNTIME-3, FR-RUNTIME-5 |

## Epic-Level Acceptance Criteria

- Web-initiated runs execute through live OpenFisca by default without requiring a new frontend runtime selector.
- The selected primary population, whether bundled, uploaded, or generated, is the actual computational input used by the run path.
- Live outputs are normalized into the existing app-facing result schema so indicator, comparison, and export flows continue to work.
- Precomputed execution remains available only via explicit replay or demo-oriented paths and is never the implicit default.
- Preflight checks, run metadata, and manifests record runtime mode, population provenance, and compatibility warnings clearly.
- Existing Scenario-stage ownership from EPIC-20 and EPIC-22 is extended rather than duplicated.

## Implementation Intent

- Reuse the existing typed direct-execution path and OpenFisca API adapter behavior where possible instead of introducing a parallel runtime stack.
- Treat runtime selection as an API and workflow contract concern first; keep the first slice free of any new user-facing engine selector.
- Resolve the known gap where uploaded/generated populations are discoverable in the workspace but not reliably executable by the run endpoint.
- Introduce a thin normalization layer between live OpenFisca output and app-facing results so downstream surfaces stay stable while the runtime changes.

## Scope Notes

- This epic does not redesign the five-stage workspace proposed in the 2026-04-01 sprint change; it assumes those stage-boundary corrections remain owned by EPIC-20 and EPIC-22.
- Replay mode is retained only for explicit demo/manual use; it must not regain status as the default runtime through fallback behavior.
- If EPIC-20 Story 20.5 or Story 20.7 need contract extensions for inherited population context or execution metadata, those changes should extend the existing contracts rather than fork them.
- `runtime_mode` (`live` or explicit `replay`) must remain separate from `simulation_mode` (`annual` or `horizon_step`) so the two concepts cannot collapse into one overloaded field.

---

## Story 23.1: Define explicit runtime-mode contract and default-live execution semantics

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** None

Define the durable execution contract used by Scenario, run requests, run metadata, and manifests. The contract must make live execution the default for web runs, keep replay as an explicit non-default path, and avoid introducing a frontend runtime selector in the first slice.

**Implementation Notes:**

- Add an explicit runtime-mode field to the backend and shared frontend/API contracts, with a live default and an explicit replay-only mode.
- Keep `runtime_mode` separate from `simulation_mode`; replay versus live is not a substitute for annual versus horizon-step simulation behavior.
- Record runtime mode in run metadata and manifest packaging so later evidence and comparison flows can distinguish live runs from replay runs.
- Keep the default user journey unchanged: standard Scenario execution chooses the live mode automatically unless the user enters a dedicated replay/demo flow.

**Test Notes:**

- Add contract tests for request/response serialization of runtime mode.
- Add manifest packaging tests asserting runtime mode is recorded for live and replay paths.
- Add migration tests for previously saved scenarios or run metadata that predate the runtime-mode field.

### Acceptance Criteria

- Given a standard web run request, when no special replay path is invoked, then the runtime contract resolves to live OpenFisca execution by default.
- Given an explicit replay or demo path, when invoked, then the runtime contract records replay mode rather than inheriting the live default implicitly.
- Given a scenario configured for `annual` or `horizon_step` simulation, when runtime mode is serialized, then the simulation-mode value remains unchanged and separately addressable from runtime mode.
- Given run metadata or manifests, when inspected, then runtime mode is visible and unambiguous.
- Given the Scenario-stage UX, when reviewed for this story, then no new frontend runtime selector is introduced.

---

## Story 23.2: Make bundled, uploaded, and generated populations executable through a unified population resolver

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 23.1

Close the current gap between population selection and execution. The same population identifiers used in the workspace must resolve to executable datasets for bundled populations, uploaded populations, and generated outputs without separate code paths leaking into user behavior.

**Implementation Notes:**

- Replace data-directory-only population lookup with a resolver that understands bundled, uploaded, and generated population sources already exposed by the workspace APIs.
- Keep the population identifier stable from Population stage selection through Scenario execution and run persistence.
- Fail early with actionable errors when a selected population exists in catalog metadata but is not executable as a dataset.

**Test Notes:**

- Add resolver unit tests for bundled, uploaded, generated, and missing population IDs.
- Add run-route integration tests showing that uploaded and generated populations can be executed, not just listed.
- Add negative-path tests for deleted, unreadable, or schema-incompatible population files.

### Acceptance Criteria

- Given a bundled population selected in the workspace, when a run starts, then that dataset is loaded as the actual execution input.
- Given an uploaded population selected in the workspace, when a run starts, then the uploaded dataset is resolved and executed through the same run path.
- Given a generated population selected in the workspace, when a run starts, then the generated dataset is resolved and executed through the same run path.
- Given a population ID that cannot be resolved to an executable dataset, when the run is requested, then execution is blocked with a precise population-resolution error.
- Given completed run metadata, when reviewed, then it points back to the resolved population identifier and source class used for execution.

---

## Story 23.3: Normalize live OpenFisca results into the stable app-facing output schema

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 23.1, Story 23.2

Introduce the normalization boundary that allows live OpenFisca execution to feed the existing app without breaking indicators, comparison views, or result persistence. This story owns the stable app-facing schema, not new policy breadth.

**Implementation Notes:**

- Define the canonical normalized output shape expected by result storage, indicator computation, and comparison surfaces.
- The canonical normalized output shape includes, at minimum: run identifier, scenario identifier, runtime mode, simulation mode, executed population reference, normalized result payload, and the metadata consumed by indicator/comparison/export flows.
- Map live OpenFisca outputs and metadata into that shape using existing mapping and ingestion primitives where possible.
- Keep replay-mode outputs flowing through the same normalized schema so downstream consumers do not branch on runtime mode.

**Test Notes:**

- Add schema-level tests for normalized output fields, types, and required metadata.
- Add regression tests showing existing indicator and comparison code accepts normalized live results without special casing.
- Add compatibility tests covering both live and replay outputs against the same normalized contract.

### Acceptance Criteria

- Given a successful live OpenFisca run, when results are packaged for the app, then they conform to the stable normalized output schema used by existing result consumers.
- Given a normalized result payload, when inspected, then it includes run/scenario identifiers, runtime mode, simulation mode, and executed population provenance alongside the normalized result data required by existing consumers.
- Given an existing indicator or comparison flow, when it consumes normalized live results, then it behaves without requiring a runtime-specific code path.
- Given a mapping or schema mismatch during normalization, when detected, then the error identifies the offending field or mapping boundary clearly.
- Given replay-mode results, when packaged, then they also conform to the same normalized output schema.

---

## Story 23.4: Switch web runs to live OpenFisca by default and isolate replay mode to explicit paths

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 23.1, Story 23.2, Story 23.3

Move the actual execution default in the product. The standard run route, Scenario flow, and server orchestration should use live OpenFisca by default, while replay behavior is available only through clearly separate demo/manual entry points.

**Implementation Notes:**

- Rewire the main web run route and Scenario execution plumbing to use the live runtime contract as the default.
- Keep explicit replay endpoints, demo helpers, or manual re-run utilities separate enough that logs and manifests cannot confuse them with live runs.
- Preserve current result-store and cache semantics so the runtime swap does not create a second persistence model.

**Test Notes:**

- Add server integration tests proving the default run route uses live execution when no replay path is requested.
- Add smoke tests for explicit replay paths to confirm they still work and remain opt-in.
- Add route-level tests confirming result persistence and cache hydration behave the same after the default switch.

### Acceptance Criteria

- Given a standard run triggered from the web product, when executed, then it uses live OpenFisca rather than the precomputed adapter path.
- Given a demo or manual replay action, when invoked explicitly, then replay execution remains available without changing the default path for normal runs.
- Given a successful live run, when stored and later reloaded, then existing result-store and cache behavior continues to work.
- Given runtime fallback conditions, when replay mode is not explicitly requested, then the system does not silently downgrade to the precomputed path.

---

## Story 23.5: Extend preflight, manifests, and result metadata with runtime and population provenance

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 23.1, Story 23.4

Make runtime-mode clarity a first-class trust feature. Before execution and after persistence, the product should tell the analyst what runtime ran, which population was executed, and whether any requested configuration is unsupported on the live path.

**Implementation Notes:**

- Extend the existing preflight registry to validate runtime support, selected-population executability, and normalization prerequisites.
- Record runtime mode, population provenance, and compatibility warnings in manifests, run metadata, and result summaries.
- Preserve the current error-message style so failures explain what happened, why, and how to fix it.

**Test Notes:**

- Add validation-registry tests for runtime support checks and population-executability checks.
- Add manifest/result-store tests asserting runtime and population provenance fields are persisted and reloaded.
- Add UI/API tests for warning visibility when replay-only or unsupported configurations are requested.

### Acceptance Criteria

- Given a run request that is unsupported on the live path or has no executable population resolution, when preflight runs, then execution is blocked with actionable runtime-specific guidance.
- Given a completed run, when its manifest or metadata is inspected, then runtime mode and executed population provenance are visible.
- Given a normalization prerequisite failure, when detected before run, then the validation output identifies the missing mapping or schema requirement.
- Given a supported live run with only non-blocking informational caveats, when preflight runs, then the analyst receives an explicit warning without any replay fallback implication.
- Given a supported live run, when preflight passes cleanly, then the analyst receives no false replay warnings.

---

## Story 23.6: Add regression coverage and operator docs for live default runs and replay smoke flows

**Status:** backlog
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 23.2, Story 23.3, Story 23.4, Story 23.5

Lock the change down with end-to-end coverage and concise operator guidance. This story closes the first slice by proving that live-default execution works with built-in and uploaded populations and that replay remains a deliberately narrow maintenance path.

**Implementation Notes:**

- Extend existing workspace, run-route, and results regression suites rather than creating a separate runtime-specific test silo.
- Document the supported live-default flow, the explicit replay path, and the operational checks needed when a run fails due to population or mapping issues.
- Keep docs aligned with the product reality that live OpenFisca is the default web runtime.

**Test Notes:**

- Add end-to-end coverage for built-in population live runs, uploaded population live runs, generated population live runs, and explicit replay smoke runs.
- Add regression assertions that existing indicator, comparison, and export flows still pass on normalized live results.
- Add doc-example or smoke tests for any operator-facing commands or documented replay utilities.

### Acceptance Criteria

- Given the automated regression suite, when it runs, then it covers live-default execution with bundled, uploaded, and generated populations plus an explicit replay smoke path.
- Given existing results and indicator workflows, when exercised by regression tests, then they pass on normalized live outputs.
- Given operator-facing documentation for runtime support, when reviewed, then it describes live as the default and replay as explicit/manual.
- Given this epic is complete, when a developer or operator investigates a failed run, then the docs and tests point to the relevant runtime, population, and mapping diagnostics.

---
