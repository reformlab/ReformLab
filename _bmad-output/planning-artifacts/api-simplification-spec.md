# API Unification Spec — Typed Policy as Runtime Source of Truth

**Date:** 2026-03-19
**Status:** Draft
**Scope:** Computation layer, public API, scenario types, adapter interface, governance boundaries, notebooks

---

## Problem Statement

The codebase has two parallel worlds that were built sequentially across epics and never properly unified:

1. **Template/domain world**: typed, frozen dataclasses such as `CarbonTaxParameters`, `BaselineScenario`, `ReformScenario`, `PolicyType`.
2. **Execution world**: low-level dict payloads such as `PolicyConfig(policy: dict[str, Any])` and `ScenarioConfig(policy: dict[str, Any])`.

The public API currently bridges them with manual translation. In practice, the rich `PolicyParameters` object the user creates is not the runtime source of truth. The public examples collapse it into a partial dict, usually just `rate_schedule`, which means policy fields such as `exemptions`, `thresholds`, `covered_categories`, `redistribution_type`, `income_weights`, and custom subclass fields are either discarded or only preserved for metadata.

This creates three problems:

- The public API is misleading: it encourages typed policy objects while execution still behaves like an untyped dict pipeline.
- Adapters cannot reliably consume the full policy model.
- The same policy is represented differently in domain code, runtime execution, manifests, notebooks, and server boundaries.

The objective of this spec is to make typed policy objects the runtime source of truth without breaking the places that still legitimately need dict snapshots at serialization boundaries.

---

## Design Principles

### 1. Runtime model and wire format are different concerns

The runtime computation layer should use typed domain objects. YAML, JSON, manifests, server payloads, and reproducibility artifacts should continue to use plain dictionaries and primitive discriminators.

This is not a contradiction. It is the correct boundary:

- **In memory / runtime:** `PolicyParameters`, `BaselineScenario`, `ReformScenario`, `PopulationData`
- **At boundaries:** `dict[str, Any]`, string `policy_type`, JSON-compatible snapshots

### 2. Typed policy must reach the adapter unchanged

`PolicyParameters` should flow from scenario definition into computation without being reduced to an ad hoc dict first.

### 3. Public API simplification must be additive before it is subtractive

The direct-scenario API should be introduced first without removing the existing `RunConfig` / `ScenarioConfig` path. Existing imports, examples, tests, and server integrations should continue to work during a transition period.

### 4. Governance contracts remain valid

Run manifests, reproducibility tools, workflow metadata, and server payloads remain dict-based. The conversion from typed objects to dict snapshots happens at clearly defined boundaries.

### 5. Reform scenarios require explicit resolution

`ReformScenario` is not self-contained. It references a baseline via `baseline_ref` and must be resolved before execution. Any direct public API that accepts `ReformScenario` must define how baseline resolution happens.

---

## Core Architectural Decisions

### Decision A — `computation.PolicyConfig.policy` becomes `PolicyParameters`

In `src/reformlab/computation/types.py`, change:

```python
@dataclass(frozen=True)
class PolicyConfig:
    policy: dict[str, Any]
    name: str = ""
    description: str = ""
```

to:

```python
@dataclass(frozen=True)
class PolicyConfig:
    policy: PolicyParameters
    name: str = ""
    description: str = ""
```

This is the key runtime change. From this point on, the computation layer and adapters receive typed policy objects.

### Decision B — `OrchestratorRunner` and manifests stay dict-based

`OrchestratorRunner` currently captures policy for metadata/manifest purposes. That capture should remain a dict snapshot, not a `PolicyParameters` object.

The runner is a workflow/governance boundary, not a domain-model container. It should continue to store:

```python
policy: dict[str, Any] | None = None
```

The runtime `ComputationStep` receives typed policy through `computation.PolicyConfig`, while the workflow request and manifest payload continue to carry serialized policy snapshots.

### Decision C — `policy_type` is derived on in-memory domain objects, but retained in wire formats

For Python domain objects:

- `ScenarioTemplate`, `BaselineScenario`, `ReformScenario`, and portfolio-layer `PolicyConfig` should derive `policy_type` from `policy`
- `policy_type` remains a readable attribute on constructed objects

For wire formats and persistence:

- YAML, JSON, registry files, server payloads, and manifests still carry `policy_type` as a string discriminator
- deserialization uses that discriminator to decide which `PolicyParameters` subclass to construct

### Decision D — public population input should use `PopulationData`, not raw `pa.Table`

The computation protocol already uses `PopulationData`, which supports multi-entity datasets. The simplified API should align with that existing abstraction rather than regress to `pa.Table`.

Public convenience helpers should normalize paths into `PopulationData`.

### Decision E — direct scenario execution is additive and overload-based

`run_scenario()` should gain support for domain scenarios directly, while preserving the existing config-based path during migration.

Target public shapes:

```python
result = run_scenario(run_config, adapter=adapter)
```

and

```python
population = load_population(path)
result = run_scenario(scenario, population=population, adapter=adapter, seed=42)
```

The old form remains supported through a transition period with deprecation warnings on public examples and docs before eventual removal.

---

## What Changes and What Does Not

### Changes

- The runtime computation layer becomes typed end to end.
- Public users can execute typed scenarios directly.
- Adapters consume the same policy objects users create.
- `policy_type` stops being manually passed around inside Python domain object construction.

### Does not change

- Server request/response payloads remain JSON-compatible.
- Scenario YAML and registry formats still use `policy_type` as a discriminator.
- Run manifests remain JSON-compatible dict snapshots.
- Reproducibility tooling continues to replay from manifest policy snapshots.
- The workflow runner remains generic and dict-oriented at its boundary.

---

## Revised Implementation Plan

### Phase 1: Type the computation layer only

**Objective:** make typed policy the runtime contract inside computation and orchestration without changing external wire formats.

Changes:

- Update `src/reformlab/computation/types.py` so `PolicyConfig.policy` is `PolicyParameters`
- Update `src/reformlab/computation/types.pyi`
- Update `src/reformlab/computation/adapter.py` and all `.pyi` adapter stubs
- Update `src/reformlab/computation/mock_adapter.py`
- Update all adapter implementations
- Update `src/reformlab/orchestrator/computation_step.py`
- Update `src/reformlab/orchestrator/portfolio_step.py` so portfolio execution passes typed policy into computation instead of `asdict(...)`
- Update `src/reformlab/interfaces/api.py::_execute_orchestration()` to construct `PolicyConfig(policy=typed_policy_obj, ...)`

Boundary behavior retained:

- workflow request payload still carries `policy` as dict
- `OrchestratorRunner.policy` remains dict-based
- manifest `policy` remains dict-based
- reproducibility continues to operate on dict snapshots

Required new utility:

- a single shared serializer for `PolicyParameters -> dict[str, Any]`
- a manifest-safe normalization step that converts non-JSON-friendly structures and numeric keys at the boundary only

This phase should not remove `_normalize_policy()` until its responsibility has been replaced by a typed-policy serializer at the manifest/request boundary.

### Phase 2: Add a direct-scenario public API without removing the old one

**Objective:** eliminate the manual bridge in user-facing code while keeping backward compatibility.

`run_scenario()` should support both:

```python
run_scenario(config, adapter=adapter, ...)
```

and

```python
run_scenario(
    scenario,
    population=population,
    adapter=adapter,
    seed=42,
    steps=(...),
    initial_state={...},
    skip_memory_check=False,
)
```

Direct-scenario execution must preserve existing runtime hooks:

- `steps`
- `initial_state`
- `skip_memory_check`
- adapter injection

Compatibility requirements:

- `RunConfig` and `ScenarioConfig` remain exported in `reformlab.__init__`
- existing config-based callers continue to work
- documentation and examples move to the direct-scenario form first
- deprecation warnings are introduced only after the direct path is stable

Internal approach:

- add normalization logic that converts either public shape into one internal execution request
- do not duplicate orchestration logic for the two paths

### Phase 3: Population handling aligned to `PopulationData`

**Objective:** simplify the public API without narrowing the runtime model.

Introduce a public helper:

```python
def load_population(path: Path) -> PopulationData:
    ...
```

Recommended direct API:

```python
def run_scenario(
    scenario: BaselineScenario | ReformScenario,
    adapter: ComputationAdapter | None = None,
    *,
    population: PopulationData | Path | None = None,
    seed: int | None = None,
    steps: tuple[PipelineStep, ...] | None = None,
    initial_state: dict[str, Any] | None = None,
    skip_memory_check: bool = False,
    baseline: BaselineScenario | None = None,
) -> SimulationResult:
    ...
```

Rules:

- if `population` is a `Path`, normalize via `load_population()`
- if `population` is a `PopulationData`, pass through unchanged
- if `population` is omitted for direct execution, raise a clear configuration error unless an existing scenario path supplies one

This preserves multi-entity support and avoids introducing a second population abstraction just for notebooks.

### Phase 4: Explicit reform resolution for direct execution

**Objective:** make `ReformScenario` support real rather than implied.

Direct execution of `ReformScenario` must follow one of these paths:

1. `baseline=` is explicitly provided by the caller
2. baseline is loaded from registry using `baseline_ref`

Resolution flow:

- if scenario is `BaselineScenario`, execute directly
- if scenario is `ReformScenario` and `baseline` is provided, resolve via `resolve_reform_definition()`
- if scenario is `ReformScenario` and `baseline` is omitted, attempt registry lookup from `baseline_ref`
- if lookup fails, raise a structured `ConfigurationError` explaining how to provide the missing baseline

This phase may ship after baseline direct-execution support. `BaselineScenario` support should not wait on reform-resolution work.

### Phase 5: Remove `policy_type` redundancy in Python constructors

**Objective:** keep `policy_type` readable but stop manually threading it through Python domain construction.

Target changes:

- `ScenarioTemplate`, `BaselineScenario`, `ReformScenario`: derive `policy_type` in `__post_init__`
- portfolio-layer `templates.portfolios.PolicyConfig`: derive `policy_type` from `policy`

Keep:

- `scenario.policy_type` and `config.policy_type` reads
- `policy_type` in server payloads
- `policy_type` in registry and YAML files
- loader/registry logic that uses `policy_type` to choose the correct parameters class

Transition note:

To reduce churn, constructors may temporarily accept `policy_type: ... | None = None` and ignore/deprecate explicit values before fully switching to `field(init=False)`. The goal is to remove redundancy without forcing an unnecessarily disruptive single-step change.

### Phase 6: Adapter cleanup and public examples

**Objective:** make the simplified public path visible and honest.

Changes:

- replace `create_quickstart_adapter()` as the primary documented example with a visible adapter class such as `SimpleCarbonTaxAdapter`
- retain `create_quickstart_adapter()` as a compatibility shim during migration
- add `load_population()` to public exports
- rewrite notebooks and examples to use:
  - typed policy objects
  - `BaselineScenario`
  - `load_population()`
  - direct `run_scenario(...)`

Documentation scope must include at least:

- `notebooks/quickstart.ipynb`
- `notebooks/advanced.ipynb`
- `notebooks/guides/02_scenario_templates.ipynb`
- `notebooks/guides/11_replication_workflow.ipynb`
- public examples and docstrings in `src/reformlab/interfaces/api.py`
- top-level examples and exports in `src/reformlab/__init__.py` and `src/reformlab/interfaces/__init__.py`

---

## Serialization and Governance Boundaries

### Manifest policy snapshot

Run manifests still require:

```python
policy: dict[str, Any]
```

The typed runtime policy must be converted to a serialized snapshot at manifest creation time, not earlier.

Preferred approach:

- introduce a shared serializer, reused by:
  - API manifest packaging
  - workflow metadata capture
  - registry and YAML serialization where appropriate
- preserve the existing JSON-compatibility guarantees
- normalize numeric dict keys to strings only in the serialized snapshot, not in the in-memory domain object

### Reproducibility

Reproducibility tools currently replay from manifest policy snapshots. That remains valid.

No change to the contract:

- manifests store dict snapshots
- reruns consume dict snapshots
- adapters for rerun workflows can reconstruct typed policy if needed, but reproducibility artifacts remain stable

### Workflow runner

`OrchestratorRunner` remains a dict-boundary component. It should not become dependent on `PolicyParameters`.

Its responsibilities are:

- execute step pipelines
- capture metadata
- package governance fields

It is not the correct place to carry typed domain models.

---

## Adapter Impact

### Simple adapters

Notebook/demo adapters should read typed policy directly:

```python
rate = policy.policy.rate_schedule[period]
```

### OpenFisca adapters

The OpenFisca adapters are not a mechanical type update. They currently assume dict iteration and key injection behavior. They must be explicitly adapted to translate from `PolicyParameters` to the engine-specific parameter structure.

That translation belongs inside the adapter, not in the public API.

### Mock adapter

`MockAdapter` continues to work. Tests that ignore policy still ignore policy. Tests that inspect policy need updating to expect typed policy rather than dict payloads.

---

## Migration and Compatibility

### Public API transition

Stage 1:

- ship direct `run_scenario(scenario, population=..., ...)`
- keep `run_scenario(config, ...)`
- keep `RunConfig`, `ScenarioConfig`, and `create_quickstart_adapter` exports

Stage 2:

- update all docs and notebooks to the new form
- add deprecation guidance in docstrings and examples

Stage 3:

- optionally deprecate config-based public entry points after downstream migration

### Constructor transition

Stage 1:

- infer `policy_type` when omitted

Stage 2:

- deprecate explicit `policy_type=` in Python object construction

Stage 3:

- remove constructor parameter if desired

This staged path avoids a single large churn event across notebooks, tests, server routes, and registry code.

---

## Test and Implementation Surface

This spec affects more than the obvious files.

### Required code updates

- computation runtime types and stubs
- adapter implementations and stubs
- public API normalization code
- portfolio execution bridge
- server route construction code
- scenario loader and registry serialization
- governance manifest packaging
- reproducibility helpers
- top-level exports

### Required test updates

- tests constructing `PolicyConfig(policy=dict(...))`
- tests asserting dict-based adapter inputs
- tests passing explicit `policy_type=...`
- notebook execution tests
- public API tests for both old and new `run_scenario()` signatures
- reform-resolution tests for direct `ReformScenario` execution

Each phase should include its own test updates. This should not be treated as one giant cleanup at the end.

---

## Recommended Execution Order

```text
Phase 1: typed computation runtime
    ->
Phase 2: additive direct-scenario API
    ->
Phase 3: population normalization via PopulationData
    ->
Phase 4: reform-resolution support
    ->
Phase 5: policy_type constructor cleanup
    ->
Phase 6: adapters/docs/notebooks migration
```

Notes:

- Phase 1 is the foundation for everything else.
- Phase 2 should land before broad documentation changes.
- Phase 4 should not block direct baseline execution.
- Phase 5 should happen after the runtime and API shape are stable.

---

## Non-Goals

- redesigning manifest schema away from dict snapshots
- removing YAML/JSON `policy_type` discriminators
- rewriting the workflow runner into a domain-model layer
- narrowing population support to single-table datasets
- removing backward compatibility in the same change that introduces the new API

---

## Final Outcome

When this spec is complete:

- users define one typed policy object and that same object drives computation
- adapters receive full policy information instead of partial dict fragments
- public examples no longer teach a lossy bridge
- manifests and reproducibility still work because dict serialization happens at the boundary
- reform execution works through an explicit baseline-resolution path
- the API is simpler for users without being naive about the surrounding system
