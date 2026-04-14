# Requirements Inventory

## Functional Requirements

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

## NonFunctional Requirements

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

## Additional Requirements

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

## UX Design Requirements

- UX-DR1: The first slice must not introduce a frontend engine selector; live OpenFisca is the default web behavior unless the user explicitly enters demo/manual replay flows.
- UX-DR2: Scenario setup must show the inherited primary population context clearly and avoid duplicate primary-population reselection.
- UX-DR3: Validation and run summary surfaces must make it clear whether a run uses live execution or explicit replay mode.
- UX-DR4: Catalog and policy-editing surfaces must expose newly surfaced policy packs without requiring users to understand backend adapter distinctions.
- UX-DR5: Existing results and indicator screens should continue to render without requiring users to learn a new output mental model.

## FR Coverage Map

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
