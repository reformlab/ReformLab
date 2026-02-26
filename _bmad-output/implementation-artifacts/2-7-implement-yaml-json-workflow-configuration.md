# Story 2.7: Implement YAML/JSON Workflow Configuration

Status: backlog

## Story

As a **policy analyst**,
I want **a versioned YAML/JSON workflow configuration that can be validated and executed through a stable runner contract**,
so that **I can run policy workflows reproducibly from configuration files without editing Python code**.

## Acceptance Criteria

Scope note: BKL-207 in this sprint covers workflow-configuration contract design, loader/validator behavior, round-trip stability, and runner wiring for currently available data + template capabilities. Implementing dynamic multi-year orchestrator internals (Epic 3), indicator engine internals (Epic 4), manifest persistence internals (Epic 5), and GUI flows (Epic 6) is explicitly out of scope.

1. **AC-1: Workflow configuration schema is explicit, versioned, and architecture-aligned**
   - Given a workflow config file (`.yaml` or `.json`), when validated, then required top-level sections are enforced: `schema_version`, `inputs`, `scenario`, `execution`, and `outputs`.
   - JSON Schema is shipped in-repo for the workflow format and supports both YAML and JSON payloads.
   - `schema_version` is required and validated with semantic-version guardrails (NFR21 compatibility behavior).

2. **AC-2: Loader returns typed config objects with actionable field-level diagnostics**
   - Given a valid config file, when loaded, then a typed `WorkflowConfig` object is returned.
   - Given an invalid field or missing required key, when validated, then `WorkflowConfigError` identifies the exact field and, when parser metadata exists, the source line.
   - Typical config validation remains fast enough to satisfy NFR4 expectations (sub-second for standard analyst workflow files).

3. **AC-3: YAML/JSON round-trip behavior is deterministic**
   - Given a valid config, when processed by `load -> dump -> load`, then semantic content remains unchanged.
   - Given equivalent YAML and JSON config payloads, when loaded, then they resolve to the same canonical typed object.
   - Serialization uses deterministic key ordering and stable formatting for version control diffs.

4. **AC-4: Configuration-driven workflow runner executes supported steps and fails clearly on unavailable subsystems**
   - Given a valid workflow config referencing shipped template assets and local input data, when executed via workflow runner, then the supported path (input load + scenario/template resolution + template execution dispatch) completes and returns a typed result envelope.
   - Execution order in `execution.steps` is explicit and validated; unsupported steps (for not-yet-built subsystems) fail fast with actionable diagnostics naming the missing subsystem.
   - Workflow execution remains fully offline/local (NFR13), with no network calls introduced by configuration handling.

5. **AC-5: Version-controlled examples are CI-validated**
   - At least two shipped workflow examples (YAML and JSON) are included and documented.
   - CI validates all shipped workflow examples against schema.
   - CI includes at least one smoke workflow run from example config to prevent drift (NFR19, NFR20).

## Tasks / Subtasks

- [ ] Task 1: Define workflow config domain model and schema (AC: #1, #3)
  - [ ] 1.1 Create typed workflow config models in `src/reformlab/interfaces/workflow_config.py`
  - [ ] 1.2 Add workflow JSON Schema at `src/reformlab/interfaces/schema/workflow-config.schema.json`
  - [ ] 1.3 Add schema-version compatibility helpers (major/minor guardrails) for workflow configs

- [ ] Task 2: Implement YAML/JSON loader and validator with structured errors (AC: #1, #2)
  - [ ] 2.1 Create `src/reformlab/interfaces/workflow_loader.py` supporting `.yaml`, `.yml`, and `.json`
  - [ ] 2.2 Add `WorkflowConfigError` to `src/reformlab/interfaces/exceptions.py` using structured `summary - reason - fix` style
  - [ ] 2.3 Surface field-path and source-line diagnostics where available

- [ ] Task 3: Implement deterministic serialization and canonicalization (AC: #3)
  - [ ] 3.1 Add `dump_workflow_config()` for stable YAML/JSON output
  - [ ] 3.2 Normalize ordering/canonical forms for deterministic diffs and equality checks
  - [ ] 3.3 Add parity checks ensuring YAML and JSON resolve identically

- [ ] Task 4: Add configuration-driven runner contract for supported current capabilities (AC: #4)
  - [ ] 4.1 Create `src/reformlab/interfaces/workflow_runner.py` to execute config-declared steps against existing modules
  - [ ] 4.2 Integrate current capabilities only: local input loading + scenario/template loading + template execution dispatch
  - [ ] 4.3 Validate step sequence and fail fast for unavailable subsystems (`orchestrator`, `indicators`, `governance`) with explicit errors

- [ ] Task 5: Add examples, tests, and CI checks (AC: #5)
  - [ ] 5.1 Add workflow examples under `examples/workflows/` (`.yaml` and `.json`)
  - [ ] 5.2 Add tests: `tests/interfaces/test_workflow_loader.py`, `tests/interfaces/test_workflow_serialization.py`, `tests/interfaces/test_workflow_runner.py`
  - [ ] 5.3 Add CI validation test that schema-checks all workflow examples and executes one smoke config end-to-end for supported steps

## Dev Notes

### Architecture Alignment

From `architecture.md`, this story belongs to the **Interfaces** layer while consuming the existing **Templates** and **Data** layer contracts. The implementation must preserve layered boundaries:
- No direct OpenFisca internal coupling from workflow config parser/runner.
- No YAML formula execution; policy logic remains Python implementation in template modules.
- Configuration defines intent and wiring; subsystem internals remain owned by their respective epics.

### Existing Code Patterns to Reuse

- Reuse structured validation/error style from `src/reformlab/templates/exceptions.py` and computation ingestion errors.
- Reuse scenario loading from `src/reformlab/templates/loader.py`.
- Reuse local dataset loading/hash patterns from `src/reformlab/data/pipeline.py` for offline-safe input handling.

### Project Structure Notes

**Target module location:** `src/reformlab/interfaces/`

**Likely files to add:**
- `src/reformlab/interfaces/workflow_config.py`
- `src/reformlab/interfaces/workflow_loader.py`
- `src/reformlab/interfaces/workflow_runner.py`
- `src/reformlab/interfaces/exceptions.py`
- `src/reformlab/interfaces/schema/workflow-config.schema.json`
- `examples/workflows/*.yaml`
- `examples/workflows/*.json`
- `tests/interfaces/test_workflow_loader.py`
- `tests/interfaces/test_workflow_serialization.py`
- `tests/interfaces/test_workflow_runner.py`

### Cross-Story Dependencies

- **Depends on Story 2.1 / BKL-201 (required gate):** Scenario template schema + loader contracts are foundational.
- **Depends on Story 2.2 / BKL-202 and Story 2.3 / BKL-203 (required for meaningful runnable examples):** Provides concrete template assets for config-driven execution.
- **Depends on Story 1.4 / BKL-104 (required for input-loading path):** Reuse dataset ingestion and metadata patterns.
- **Related upstream dependency:** Story 1.3 / BKL-103 mapping conventions inform config input mapping references.
- **Related downstream stories (do not implement here):**
  - Story 2.4 / BKL-204 and 2.5 / BKL-205 can extend config references to immutable scenario IDs and clone/link flows.
  - Epic 3 stories (`3-1` onward) provide full dynamic orchestration execution behind configured step names.
  - Epic 4 and Epic 5 consume workflow outputs for indicators and manifests.

### Out of Scope Guardrails

- No implementation of dynamic yearly orchestrator internals (Epic 3).
- No indicator computation internals (Epic 4).
- No manifest generation internals (Epic 5).
- No GUI/notebook UX implementation details (Epic 6).
- No network-dependent configuration resolution; local/offline file-based workflows only.

### Testing Standards

- Use `pytest` with fixture-based config samples (valid + invalid).
- Validate deterministic behavior for load/dump/load across YAML and JSON.
- Validate field-level + line-aware diagnostics for malformed configs.
- Include at least one smoke run test using shipped workflow example and currently implemented template capabilities.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Layered Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Starter & Tooling Decisions]
- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-207]
- [Source: _bmad-output/planning-artifacts/prd.md#FR31, NFR4, NFR20, NFR21]
- [Source: src/reformlab/templates/loader.py]
- [Source: src/reformlab/data/pipeline.py]
