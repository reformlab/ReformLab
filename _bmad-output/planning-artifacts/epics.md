---
title: ReformLab - Epics and Stories
project: ReformLab
description: Consolidated active epics and stories
date: 2026-04-15
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-01.md
source_documents:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-01.md
---

# Epics and Stories

Consolidated source of truth for the active backlog.
Epics 1-22 remain archived in git history rather than being reintroduced here.

## Epic Index

Epics 1-22 are complete (see git history for details).

| Epic | Title | Phase | Status | Stories |
|------|-------|-------|--------|---------|
| EPIC-23 | Live OpenFisca Runtime and Executable Population Alignment | 3 | in-progress | 6 |
| EPIC-24 | Live Policy Catalog Activation and Domain-to-OpenFisca Translation | 3 | backlog | 5 |

## Conventions

- **Priority:** `P0` (must ship), `P1` (ship if capacity allows after P0)
- **Size:** Story points (`SP`) on Fibonacci scale (1, 2, 3, 5, 8, 13)
- **Types:** `Story`, `Task`, `Spike`
- **Done:** Acceptance criteria pass and tests are in CI
- **Story files:** `_bmad-output/implementation-artifacts/{epic}-{story-slug}.md`

## Requirements Inventory

### Functional Requirements

- FR2: System can optionally execute OpenFisca runs through a version-pinned API adapter.
- FR3: Analyst can map OpenFisca variables to project schema fields through configuration.
- FR4: System validates mapping/schema contracts with clear field-level errors.
- FR5: Analyst can load synthetic populations and external environmental datasets.
- FR7: Analyst can load prebuilt environmental policy templates, including carbon tax, subsidy, rebate, and feebate.
- FR11: Analyst can compose tax-benefit baseline outputs with environmental template logic in one workflow.
- FR18: System outputs year-by-year panel results for each scenario.
- FR25: System automatically generates immutable run manifests including versions, hashes, parameters, and assumptions.
- FR26: Analyst can inspect assumptions and mappings used in any run.
- FR27: System emits warnings for unsupported run configurations.
- FR28: Results are pinned to scenario version, data version, and OpenFisca adapter/version.
- FR32: User can use a stage-based no-code GUI to create, inspect, clone, and run scenarios.
- FR32a: The primary population for a scenario is selected in the Population stage and inherited by later stages without mandatory reselection.
- FR32c: The Scenario stage configures execution settings, annual horizon, optional sensitivity population, and final validation before run.
- FR43: Analyst can compose multiple individual policy templates into a named policy portfolio.
- FR44: System executes a simulation with a policy portfolio, applying all bundled policies together.
- FR45: Analyst can compare results across different policy portfolios side-by-side.
- FR46: Analyst can define custom policy templates that participate in portfolios alongside built-in templates.
- FR-RUNTIME-1: Web runs use live OpenFisca as the default execution path; precomputed replay is not the default runtime.
- FR-RUNTIME-2: The selected population is a real execution input for live runs, not only a display or metadata choice.
- FR-RUNTIME-3: Bundled, uploaded, and generated populations are executable through the same live runtime contract.
- FR-RUNTIME-4: Precomputed mode remains available only for explicit demo or manual replay flows.
- FR-RUNTIME-5: Live runs return a stable app-facing result schema so existing indicators, result views, and comparison flows continue to work.
- FR-RUNTIME-6: Policy/domain definitions remain the source of truth for policy catalog entries, and live OpenFisca translation happens downstream of that layer.
- FR-RUNTIME-7: Existing hidden policy packs that are already supported by backend/domain logic are surfaced through the catalog/API where appropriate.

### NonFunctional Requirements

- NFR1: Full population simulation should remain performant enough for interactive analyst workflows.
- NFR3: Populations up to the supported laptop-scale threshold should fail with clear preflight warnings rather than opaque runtime crashes.
- NFR6: Identical inputs produce bit-identical outputs across runs on the same machine.
- NFR9: Run manifests are generated automatically with zero manual effort from the user.
- NFR10: No implicit temporal assumptions; period semantics must remain explicit.
- NFR13: Core workflows remain offline-capable with no required external network dependency.
- NFR14: CSV and Parquet files remain supported for relevant data input and output operations.
- NFR15: OpenFisca integration supports version-pinned orchestration and compatible import contracts.
- NFR18: Regression coverage protects adapters, orchestration, template logic, and execution flows.
- NFR21: Any app-facing contract changes preserve compatibility intentionally and are versioned clearly.
- NFR-RUNTIME-1: Live-runtime adoption must preserve current indicator and result-surface behavior for existing workflows.
- NFR-RUNTIME-2: Runtime-mode behavior must be explicit and interpretable in manifests, API responses, and validation surfaces.
- NFR-RUNTIME-3: The first delivery slice prioritizes runtime and data-path correctness before expanding policy breadth.

### Additional Requirements

- The architecture keeps ReformLab as an orchestration platform; computation logic stays behind the `ComputationAdapter` boundary and no non-computation module should import OpenFisca directly.
- The canonical analysis object remains the `Scenario`; simulation configuration, population inputs, and result lineage must stay attached to that durable object.
- `simulation_mode` and `runtime_mode` are distinct contracts. `simulation_mode` belongs to `Scenario` and controls execution semantics such as `annual` versus `horizon_step`. `runtime_mode` belongs to run requests, persisted run metadata, and manifests, and distinguishes `live` from explicit `replay`.
- Population selection remains part of scenario state, but Stage 2 owns the primary population choice and later stages consume inherited context.
- Backend contracts, manifests, and validation surfaces must distinguish runtime modes so demo replay and live execution remain interpretable.
- The normalized app-facing result contract must expose at least: run/scenario identifiers, runtime mode, simulation mode, executed population reference, normalized yearly or endpoint outputs, and the metadata required by existing indicator/comparison/export consumers.
- Subsidy and similar policy logic must be implemented in the policy/domain layer and translated into live OpenFisca execution; it must not be embedded into the `ComputationAdapter` interface or the precomputed adapter.
- Surfaced catalog entries must expose stable identifiers plus availability metadata sufficient for UX and validation surfaces: `runtime_availability` (`live_ready` or `live_unavailable`) and `availability_reason` when unavailable.
- Existing completed foundations in EPIC-1, EPIC-9, EPIC-13, EPIC-17, and EPIC-20 should be reused rather than recreated.
- The first expansion slice should not start with housing reforms or family-benefit reforms.

### UX Design Requirements

- UX-DR1: The first slice must not introduce a frontend engine selector; live OpenFisca is the default web behavior unless the user explicitly enters demo/manual replay flows.
- UX-DR2: Scenario setup must show the inherited primary population context clearly and avoid duplicate primary-population reselection.
- UX-DR3: Validation and run summary surfaces must make it clear whether a run uses live execution or explicit replay mode.
- UX-DR4: Catalog and policy-editing surfaces must expose newly surfaced policy packs without requiring users to understand backend adapter distinctions.
- UX-DR5: Existing results and indicator screens should continue to render without requiring users to learn a new output mental model.

### FR Coverage Map

- FR2: EPIC-23 - make live OpenFisca the default execution path for web runs.
- FR3: EPIC-23 - preserve and validate input/output mapping contracts on the live path.
- FR4: EPIC-23 - block invalid schema and mapping combinations before live execution.
- FR5: EPIC-23 - make bundled, uploaded, and generated populations executable through the same runtime contract.
- FR7: EPIC-24 - surface existing built-in packs that are already modeled in the domain layer.
- FR11: EPIC-23 - preserve the combined OpenFisca-plus-environment workflow under live execution.
- FR18: EPIC-23 - keep year-by-year outputs available through a stable normalized result schema.
- FR25: EPIC-23 - capture runtime mode, population provenance, and normalized-output lineage in manifests.
- FR26: EPIC-23 - keep assumptions, mappings, and runtime provenance inspectable after live runs.
- FR27: EPIC-23 - warn clearly when a request falls outside supported live or replay behavior.
- FR28: EPIC-23 - pin results to scenario, data, and adapter/runtime versions.
- FR32: EPIC-23 - preserve the no-code scenario run flow while changing the backend default path.
- FR32a: EPIC-23 - ensure the selected primary population is the real execution input.
- FR32c: EPIC-23 - keep Scenario as the execution and validation owner without adding a runtime selector.
- FR43: EPIC-24 - allow surfaced packs to participate in named portfolios.
- FR44: EPIC-24 - execute surfaced policy bundles together through the live runtime.
- FR45: EPIC-24 - preserve comparison behavior across expanded live-executable portfolios.
- FR46: EPIC-24 - keep policy/domain templates as the authoring source for live-executable packs.
- FR-RUNTIME-1: EPIC-23 - switch web runs to live OpenFisca by default.
- FR-RUNTIME-2: EPIC-23 - treat selected population data as computational input, not metadata only.
- FR-RUNTIME-3: EPIC-23 - execute bundled, uploaded, and generated populations through the same live path.
- FR-RUNTIME-4: EPIC-23 - confine precomputed execution to explicit replay/demo flows.
- FR-RUNTIME-5: EPIC-23 - normalize live outputs into the stable app-facing schema.
- FR-RUNTIME-6: EPIC-24 - keep domain-layer policy definitions authoritative and translate downstream.
- FR-RUNTIME-7: EPIC-24 - expose hidden supported packs through catalog and API where appropriate.

## Epic List

### Epic 23: Live OpenFisca Runtime and Executable Population Alignment
Analyst can run the web workflow against a real selected population through live OpenFisca by default, while existing indicators, results, and replay use cases continue to work.
**FRs covered:** FR2, FR3, FR4, FR5, FR11, FR18, FR25, FR26, FR27, FR28, FR32, FR32a, FR32c, FR-RUNTIME-1, FR-RUNTIME-2, FR-RUNTIME-3, FR-RUNTIME-4, FR-RUNTIME-5

### Epic 24: Live Policy Catalog Activation and Domain-to-OpenFisca Translation
Analyst can discover, configure, and execute already-modeled subsidy and related policy packs from the product catalog/API, with policy logic defined in the domain layer and translated into live OpenFisca execution.
**FRs covered:** FR7, FR43, FR44, FR45, FR46, FR-RUNTIME-6, FR-RUNTIME-7

---

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

# Epic 24: Live Policy Catalog Activation and Domain-to-OpenFisca Translation

**User outcome:** Analyst can discover and execute already-modeled subsidy and related policy packs from the catalog/API, with policy definitions remaining in the domain layer and live OpenFisca translation happening behind the scenes.

**Status:** backlog

**Builds on:** EPIC-2 (scenario templates and registry), EPIC-12 (policy portfolio model), EPIC-13 (additional policy templates and extensibility), EPIC-20 (workspace alignment), EPIC-23 (live runtime foundation)

**PRD Refs:** FR7, FR43-FR46, FR-RUNTIME-6, FR-RUNTIME-7

**Primary source documents:**
- `_bmad-output/planning-artifacts/prd.md`
- `_bmad-output/planning-artifacts/architecture.md`
- `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, dated 2026-04-01)
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-01.md`

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-2401 | Story | P0 | 5 | Publish canonical catalog and API exposure for already-modeled hidden policy packs | backlog | FR7, FR-RUNTIME-7 |
| BKL-2402 | Story | P0 | 8 | Implement domain-layer live translation for subsidy-style policies without adapter-interface changes | backlog | FR46, FR-RUNTIME-6 |
| BKL-2403 | Story | P0 | 5 | Enable portfolio execution for surfaced subsidy and related live policy packs | backlog | FR43-FR45, FR46 |
| BKL-2404 | Story | P0 | 5 | Surface live-capable policy packs in workspace catalog flows without runtime-specific UX | backlog | FR7, FR43, FR44, FR-RUNTIME-7 |
| BKL-2405 | Story | P1 | 5 | Add regression coverage and examples for the expanded live policy catalog | backlog | FR44-FR46, FR-RUNTIME-6, FR-RUNTIME-7 |

## Epic-Level Acceptance Criteria

- Existing modeled policy packs that were previously hidden are exposed through the canonical catalog and API with clear availability metadata.
- Live translation for subsidy-style policies is implemented in the domain/policy layer and does not add subsidy logic to `ComputationAdapter` or the precomputed adapter.
- At least one surfaced subsidy-family pack executes successfully through the live runtime while preserving the normalized result contract from EPIC-23.
- Surfaced packs participate in portfolio validation, execution, and comparison flows without introducing runtime-specific UI branching.
- The first policy-expansion slice explicitly excludes housing and family-benefit reforms.

## Implementation Intent

- Reuse the existing pack and template registry utilities from EPIC-13 instead of creating a second catalog representation.
- Add a dedicated domain-to-live translation layer for subsidy-style policies so future policy expansion does not leak into adapter contracts.
- Surface only packs that are genuinely executable or intentionally marked unavailable; avoid exposing placeholders that the live runtime cannot honor.
- Keep catalog UX focused on policy discovery and configuration, not runtime education or engine toggles.
- Availability metadata should be stable and explicit enough to drive catalog rendering, validation, and save/load compatibility without hidden frontend logic.

## Scope Notes

- This epic assumes EPIC-23 has already established the live runtime default and normalized output contract.
- Housing and family-benefit reforms remain out of scope for this first expansion slice even if OpenFisca has related concepts.
- Existing hidden packs may include subsidy, rebate, feebate, vehicle-malus, and energy-poverty-aid variants; only the live-capable subset should be surfaced as executable.

---

## Story 24.1: Publish canonical catalog and API exposure for already-modeled hidden policy packs

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 23.4

Inventory the policy packs that already exist in the domain/template layer and expose them through the canonical product catalog and API. This story is about truthful discoverability: what exists, what is executable now, and what remains intentionally hidden.

**Implementation Notes:**

- Build catalog metadata from the existing template-pack registry utilities rather than hardcoding a second list in the frontend or API layer.
- Mark availability and execution readiness explicitly so hidden-but-supported packs can be surfaced without misleading users about runtime support.
- Expose `runtime_availability` (`live_ready` or `live_unavailable`) and `availability_reason` in the canonical catalog contract.
- Preserve deterministic identifiers so catalog items remain stable across API, workspace, and saved scenario references.

**Test Notes:**

- Add catalog listing tests covering visible, hidden, and newly surfaced packs.
- Add API contract tests for availability metadata and stable identifiers.
- Add regression tests ensuring existing visible packs keep their current identifiers and grouping.

### Acceptance Criteria

- Given the canonical catalog or API, when inspected, then existing modeled hidden packs appear with stable identifiers plus `runtime_availability` and `availability_reason` metadata.
- Given a pack that is not yet executable on the live path, when surfaced, then its status is explicit rather than silently failing at run time.
- Given existing visible packs, when the catalog is updated, then their identifiers and grouping remain stable.
- Given saved scenarios or portfolios that reference previously visible packs, when loaded, then they remain compatible after the catalog expansion.

---

## Story 24.2: Implement domain-layer live translation for subsidy-style policies without adapter-interface changes

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 23.3, Story 24.1

Add the translation boundary that turns domain-authored subsidy-style policies into live OpenFisca execution inputs. This story must preserve the adapter contract: the adapter remains generic, while domain logic decides how subsidy-family policies are translated.

**Implementation Notes:**

- Introduce translator components or functions owned by the policy/domain layer that convert subsidy-style definitions into the live runtime request shape.
- Invoke translation between domain policy-set resolution and live run-request assembly so the adapter still receives a generic computation input rather than subsidy-aware instructions.
- Keep `ComputationAdapter` unchanged and avoid embedding subsidy semantics into the precomputed adapter.
- Start with subsidy-family policies already represented in the domain model and explicitly exclude housing and family-benefit reforms.

**Test Notes:**

- Add unit tests for domain-to-live translation of subsidy-style policy parameters.
- Add contract tests proving the adapter interface remains unchanged while translated payloads execute successfully.
- Add negative-path tests for unsupported subsidy variants or missing translation fields.

### Acceptance Criteria

- Given a subsidy-style policy defined in the domain layer, when prepared for execution, then it is translated into live OpenFisca inputs by domain-owned translation logic.
- Given the live execution path, when translation completes, then the adapter receives the same generic request shape it would for any other live run rather than a subsidy-specific adapter extension.
- Given the translation implementation, when reviewed, then no subsidy-specific behavior is added to `ComputationAdapter` or the precomputed adapter.
- Given an unsupported subsidy-domain feature, when translation is attempted, then the failure is explicit and actionable.
- Given the excluded housing or family-benefit domains, when requested in this slice, then they are not silently treated as supported.

---

## Story 24.3: Enable portfolio execution for surfaced subsidy and related live policy packs

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 24.1, Story 24.2

Move from discoverability to execution. Surfaced live-capable packs must work inside the existing portfolio model, including compatibility validation, runtime execution, and comparison against baseline or other portfolios.

**Implementation Notes:**

- Reuse existing portfolio composition and conflict-resolution rules from EPIC-12 and EPIC-13 where they already fit the surfaced pack types.
- Ensure translated subsidy-family policies and already-supported related packs can execute together through the live runtime foundation from EPIC-23.
- Preserve the normalized output contract so comparison and indicator flows remain untouched downstream.

**Test Notes:**

- Add portfolio integration tests covering mixed portfolios with carbon tax plus surfaced subsidy-family packs.
- Add compatibility-rule regression tests for conflict detection and resolution.
- Add execution tests proving normalized outputs remain valid after portfolio runs with surfaced packs.

### Acceptance Criteria

- Given a portfolio containing surfaced live-capable packs, when validated, then compatibility checks behave consistently with existing portfolio rules.
- Given a portfolio containing a surfaced subsidy-family pack, when executed, then it runs through the live runtime and produces normalized results.
- Given baseline-versus-portfolio comparison, when computed, then existing comparison surfaces continue to work without pack-specific branching.
- Given a pack marked unavailable for live execution, when added to a portfolio run, then the system blocks or warns before execution rather than failing deep in the runtime.

---

## Story 24.4: Surface live-capable policy packs in workspace catalog flows without runtime-specific UX

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 24.1, Story 24.3

Expose the newly surfaced packs across the workspace where analysts actually choose and configure policies. The UX should communicate availability and category clearly, but it should not force users to understand runtime internals or choose an engine.

**Implementation Notes:**

- Reuse existing template-browser and composition-panel patterns from EPIC-20 and EPIC-22.
- Display policy type, readiness, and any availability constraints through catalog metadata rather than runtime-selector UI.
- Keep the default editing and portfolio-assembly experience consistent across old and newly surfaced packs.

**Test Notes:**

- Add frontend tests confirming surfaced packs appear in template browsers and composition panels with the correct labels.
- Add UX regression tests ensuring no runtime selector or adapter-specific jargon appears in the first-slice policy flows.
- Add persistence tests for scenarios and portfolios using newly surfaced packs.

### Acceptance Criteria

- Given the policy browser and composition flows, when rendered, then newly surfaced live-capable packs are available alongside existing packs.
- Given a surfaced pack with a readiness caveat, when shown to the user, then the caveat is visible without exposing backend runtime mechanics.
- Given the first-slice policy workflows, when reviewed, then no runtime or engine selector is introduced.
- Given a scenario or portfolio using a surfaced pack, when saved and reloaded, then the pack reference remains stable.

---

## Story 24.5: Add regression coverage and examples for the expanded live policy catalog

**Status:** backlog
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 24.3, Story 24.4

Close the policy-expansion epic by proving that the newly surfaced packs behave coherently across catalog, portfolio, execution, and comparison flows. Capture that behavior in regression tests and lightweight examples for future pack additions.

**Implementation Notes:**

- Extend the existing catalog, portfolio, and run regression suites rather than creating one-off tests per pack.
- Add lightweight examples that demonstrate surfaced subsidy-family execution through the live runtime and normalized results.
- Document the current supported live policy catalog so future additions have a clear baseline.

**Test Notes:**

- Add end-to-end or integration coverage for selecting a surfaced pack, running it live, and comparing results.
- Add regression tests for portfolio save/load and scenario persistence with surfaced pack identifiers.
- Add example smoke tests for any shipped sample configurations that demonstrate surfaced packs.

### Acceptance Criteria

- Given the automated test suite, when it runs, then it covers catalog exposure, portfolio validation, live execution, and comparison for surfaced packs.
- Given shipped examples or smoke configs, when executed, then they demonstrate at least one surfaced subsidy-family pack running through the live path successfully.
- Given the supported policy catalog documentation, when reviewed, then it matches the packs actually exposed and executable in the product.
- Given future pack expansion work, when planned, then the added tests and examples provide a reusable baseline rather than a one-off demo.
