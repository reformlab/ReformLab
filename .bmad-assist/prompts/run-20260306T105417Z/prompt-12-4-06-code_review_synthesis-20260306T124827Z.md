<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 12 -->
<!-- Story: 4 -->
<!-- Phase: code-review-synthesis -->
<!-- Timestamp: 20260306T124827Z -->
<compiled-workflow>
<mission><![CDATA[

Master Code Review Synthesis: Story 12.4

You are synthesizing 2 independent code review findings.

Your mission:
1. VERIFY each issue raised by reviewers
   - Cross-reference with project_context.md (ground truth)
   - Cross-reference with git diff and source files
   - Identify false positives (issues that aren't real problems)
   - Confirm valid issues with evidence

2. PRIORITIZE real issues by severity
   - Critical: Security vulnerabilities, data corruption risks
   - High: Bugs, logic errors, missing error handling
   - Medium: Code quality issues, performance concerns
   - Low: Style issues, minor improvements

3. SYNTHESIZE findings
   - Merge duplicate issues from different reviewers
   - Note reviewer consensus (if 3+ agree, high confidence)
   - Highlight unique insights from individual reviewers

4. APPLY source code fixes
   - You have WRITE PERMISSION to modify SOURCE CODE files
   - CRITICAL: Before using Edit tool, ALWAYS Read the target file first
   - Use EXACT content from Read tool output as old_string, NOT content from this prompt
   - If Read output is truncated, use offset/limit parameters to locate the target section
   - Apply fixes for verified issues
   - Do NOT modify the story file (only Dev Agent Record if needed)
   - Document what you changed and why

Output format:
## Synthesis Summary
## Issues Verified (by severity)
## Issues Dismissed (false positives with reasoning)
## Source Code Fixes Applied

]]></mission>
<context>
<file id="e58fb4dd" path="docs/project-context.md" label="PROJECT CONTEXT"><![CDATA[

---
project_name: 'ReformLab'
user_name: 'Lucas'
date: '2026-02-27'
status: 'complete'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
rule_count: 38
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python 3.13+** — `target-version = "py313"` (ruff), `python_version = "3.13"` (mypy strict)
- **uv** — package manager, **hatchling** — build backend
- **pyarrow >= 18.0.0** — canonical data type (`pa.Table`), CSV/Parquet I/O
- **pyyaml >= 6.0.2** — YAML template/config loading
- **jsonschema >= 4.23.0** — JSON Schema validation for templates
- **openfisca-core >= 44.0.0** — optional dependency (`[openfisca]` extra); never import outside adapter modules
- **pytest >= 8.3.3, ruff >= 0.15.0, mypy >= 1.19.0** — dev tooling
- **Planned frontend:** React 18+ / TypeScript / Vite / Shadcn/ui / Tailwind v4
- **Planned backend API:** FastAPI + uvicorn
- **Planned deployment:** Kamal 2 on Hetzner CX22

### Version Constraints

- mypy runs in **strict mode** with explicit `ignore_missing_imports` overrides for openfisca, pyarrow, jsonschema, yaml
- OpenFisca is optional — core library must function without it installed

## Critical Implementation Rules

### Python Language Rules

- **Every file starts with** `from __future__ import annotations` — no exceptions
- **Use `if TYPE_CHECKING:` guards** for imports that are only needed for annotations or would create circular dependencies; do the runtime import locally where needed
- **Frozen dataclasses are the default** — all domain types use `@dataclass(frozen=True)`; mutate via `dataclasses.replace()`, never by assignment
- **Protocols, not ABCs** — interfaces are `Protocol` + `@runtime_checkable`; no abstract base classes; structural (duck) typing only
- **Subsystem-specific exceptions** — each module defines its own error hierarchy; never raise bare `Exception` or `ValueError` for domain errors
- **Metadata bags** use `dict[str, Any]` with **stable string-constant keys** defined at module level (e.g., `STEP_EXECUTION_LOG_KEY`)
- **Union syntax** — use `X | None` not `Optional[X]`; use `dict[str, int]` not `Dict[str, int]` (modern generics, no `typing` aliases)
- **`tuple[...]` for immutable sequences** — function parameters and return types that are ordered-and-fixed use `tuple`, not `list`

### Architecture & Framework Rules

- **Adapter isolation is absolute** — only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca; all other code uses the `ComputationAdapter` protocol
- **Step pipeline contract** — steps implement `OrchestratorStep` protocol (`name` + `execute(year, state) -> YearState`); bare callables accepted via `adapt_callable()`; registration via `StepRegistry` with topological sort on `depends_on`
- **Template packs are YAML** — live in `src/reformlab/templates/packs/{policy_type}/`; validated against JSON Schemas in `templates/schema/`; each policy type has its own subpackage with `compute.py` + `compare.py`
- **Data flows through PyArrow** — `PopulationData` (dict of `pa.Table` by entity) → adapter → `ComputationResult` (`pa.Table`) → `YearState.data` → `PanelOutput` (stacked table) → indicators
- **`YearState` is the state token** — passed between steps and years; immutable (frozen dataclass); updated via `replace()`
- **Orchestrator is the core product** — never build custom policy engines, formula compilers, or entity graph engines; OpenFisca handles computation, this project handles orchestration

### Testing Rules

- **Mirror source structure** — `tests/{subsystem}/` matches `src/reformlab/{subsystem}/`; each has `__init__.py` and `conftest.py`
- **Class-based test grouping** — group tests by feature or acceptance criterion (e.g., `TestOrchestratorBasicExecution`); reference story/AC IDs in comments and docstrings
- **Fixtures in conftest.py** — subsystem-specific fixtures per `conftest.py`; build PyArrow tables inline, use `tmp_path` for I/O, golden YAML files in `tests/fixtures/`
- **Direct assertions** — use plain `assert`; no custom assertion helpers; use `pytest.raises(ExceptionClass, match=...)` for errors
- **Test helpers are explicit** — import shared callables from conftest directly (`from tests.orchestrator.conftest import ...`); no hidden magic
- **Golden file tests** — YAML fixtures in `tests/fixtures/templates/`; test load → validate → round-trip cycle
- **MockAdapter for unit tests** — never use real OpenFisca in orchestrator/template/indicator unit tests; `MockAdapter` is the standard test double

### Code Quality & Style Rules

- **ruff** enforces `E`, `F`, `I`, `W` rule sets; `src = ["src"]`; target Python 3.13
- **mypy strict** — all code must pass `mypy --strict`; new modules need `ignore_missing_imports` overrides in `pyproject.toml` only for third-party libs without stubs
- **File naming** — `snake_case.py` throughout; no PascalCase or kebab-case files
- **Class naming** — PascalCase for classes (`OrchestratorStep`, `CarbonTaxParameters`); no suffixes like `Impl` or `Base`
- **Module-level docstrings** — every module has a docstring explaining its role, referencing relevant story/FR
- **Section separators** — use `# ====...====` comment blocks to separate major sections within longer modules (see `step.py`)
- **No wildcard imports** — always import specific names; `from reformlab.orchestrator import Orchestrator, OrchestratorConfig`
- **Logging** — use `logging.getLogger(__name__)`; structured key=value format for parseable log lines (e.g., `year=%d seed=%s event=year_start`)

### Development Workflow Rules

- **Package manager is uv** — use `uv pip install`, `uv run pytest`, etc.; not `pip` directly
- **Test command** — `uv run pytest tests/` (or specific subsystem path)
- **Lint command** — `uv run ruff check src/ tests/` and `uv run mypy src/`
- **Source layout** — `src/reformlab/` is the installable package; `tests/` is separate; `pythonpath = ["src"]` in pytest config
- **Build system** — hatchling with `packages = ["src/reformlab"]`
- **No auto-formatting on save assumed** — agents must produce ruff-compliant code; run `ruff check --fix` if needed

### Critical Don't-Miss Rules

- **Never import OpenFisca outside adapter modules** — this is the single most important architectural boundary; violation couples the entire codebase to one backend
- **All domain types are frozen** — never add a mutable dataclass; if you need mutation, use `dataclasses.replace()` and return a new instance
- **Determinism is non-negotiable** — every run must be reproducible; seeds are explicit, logged in manifests, derived deterministically (`master_seed XOR year`)
- **Data contracts fail loudly** — contract validation at ingestion boundaries is field-level and blocking; never silently coerce or drop data
- **Assumption transparency** — every run produces a manifest (JSON); assumptions, versions, seeds, data hashes are all recorded
- **PyArrow is the canonical data type** — do not use pandas DataFrames in core logic; `pa.Table` is the standard; pandas only at display/export boundaries if needed
- **No custom formula compiler** — environmental policy logic is Python code in template `compute.py` modules, not YAML formula strings or DSLs
- **France/Europe first** — initial scenarios use French policy parameters (EUR, INSEE deciles, French carbon tax rates); European data sources (Eurostat, EU-SILC)

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-02-27


]]></file>
<file id="4f02ed14" path="_bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md" label="STORY FILE"><![CDATA[

# Story 12.4: Extend Scenario Registry with Portfolio Versioning

Status: ready-for-dev
Dependencies: Story 12.1 (PolicyPortfolio model), Story 12.2 (conflict detection/resolution)

## Story

As a **policy analyst**,
I want to save, version, and retrieve policy portfolios through the same scenario registry used for individual scenarios,
so that I can track portfolio evolution over time and distinguish portfolios from individual scenarios when browsing the registry.

## Acceptance Criteria

### AC1: Portfolio save and retrieval by version ID
Given a `PolicyPortfolio` saved to the registry, when retrieved by version ID, then the returned portfolio is identical to what was saved, including all constituent policies (policy types, parameters, names, resolution strategy, description).

### AC2: New version on content change
Given a portfolio, when a constituent policy is modified and the portfolio is re-saved, then a new version ID is assigned. The previous version remains accessible by its version ID.

### AC3: Type-distinguishable listing
Given the registry, when queried, then portfolios and individual scenarios are both listable and distinguishable by type. The developer can determine whether a registry entry is a `BaselineScenario`, `ReformScenario`, or `PolicyPortfolio`.

### AC4: Content-addressable versioning
Given a portfolio saved to the registry, when the same portfolio (identical content) is saved again, then the registry returns the existing version ID (idempotent save). The version ID is deterministic — same content always produces the same 12-character hex ID.

### AC5: Round-trip fidelity
Given a portfolio saved and then retrieved from the registry, when compared to the original, then all fields are identical: `name`, `policies` (including each `PolicyConfig`'s `policy_type`, `policy`, `name`), `version`, `description`, `resolution_strategy`. Frozen dataclass equality (`==`) holds.

### AC6: Version history and lineage
Given multiple saves of a portfolio (with modifications between saves), when `list_versions()` is called, then all versions are returned as `ScenarioVersion` objects in chronological order. Each entry contains: `version_id` (12-char hex), `timestamp` (UTC datetime), `change_description` (user-provided string), and `parent_version` (previous version ID or `None` for first version).

### AC7: Error handling
Given an invalid portfolio name (empty, path traversal), when `save()` is called, then a `RegistryError` is raised with actionable fields (`summary`, `reason`, `fix`). Given a non-existent portfolio name or version ID, when `get()` is called, then `ScenarioNotFoundError` or `VersionNotFoundError` is raised with available alternatives listed. Given an attempt to save a portfolio under an existing scenario name (or vice versa), then a `RegistryError` is raised indicating the entry type mismatch. Given a portfolio entry, when `migrate()` is called, then a `RegistryError` is raised indicating migration is not supported for portfolios.

## Tasks / Subtasks

### Task 1: Add portfolio serialization support to registry (AC: 1, 4, 5)

- [ ] 1.1 Create `_portfolio_to_dict_for_registry(portfolio: PolicyPortfolio) -> dict[str, Any]` in `registry.py`. Use existing `portfolio_to_dict()` from `portfolios.composition` as the base, but: (a) replace the `$schema` value with a stable relative path (e.g., `"portfolio.schema.json"`) — `portfolio_to_dict()` emits a machine-specific absolute path via `Path(__file__)` which would break cross-machine version ID determinism; (b) add a `"_registry_type": "portfolio"` marker field to distinguish from scenarios in the metadata/version YAML files
- [ ] 1.2 Create `_generate_portfolio_version_id(portfolio: PolicyPortfolio) -> str` using SHA-256 of `yaml.dump(content, sort_keys=True)` with 12-char hex prefix — same pattern as `_generate_version_id()` for scenarios
- [ ] 1.3 Create `_dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio` to reconstruct a `PolicyPortfolio` from registry YAML dict. Reuse `dict_to_portfolio()` from `portfolios.composition` after stripping the `_registry_type` marker

### Task 2: Extend `ScenarioRegistry.save()` to accept portfolios (AC: 1, 2, 4)

- [ ] 2.1 Widen `save()` signature to accept `BaselineScenario | ReformScenario | PolicyPortfolio`
- [ ] 2.2 Detect portfolio type with `isinstance(scenario, PolicyPortfolio)` and route to portfolio-specific version ID generation and serialization
- [ ] 2.3 Store portfolio YAML version files in the same directory structure: `{registry_path}/{name}/versions/{version_id}.yaml`
- [ ] 2.4 Store a `"_registry_type"` field in `metadata.yaml` with value `"baseline"`, `"reform"`, or `"portfolio"` based on artifact type. Determine scenario subtype via `isinstance(scenario, ReformScenario)` → `"reform"`, else `"baseline"`. For backward compat, legacy entries without this field infer type from the latest version content (presence of `baseline_ref` → `"reform"`, absence → `"baseline"`)
- [ ] 2.5 Portfolio save follows identical metadata update pattern: parent_version tracking, timestamp, change_description
- [ ] 2.6 Idempotent save: if content-addressable version ID already exists with identical content, return existing version ID without creating a new entry
- [ ] 2.7 Type-consistency guard: if metadata already exists for the given name, compare the stored `_registry_type` against the incoming artifact type. Reject mismatches (e.g., saving a portfolio under an existing scenario name) with `RegistryError(summary="Entry type mismatch", reason=..., fix="Use a different name or save as the correct type")`

### Task 3: Extend `ScenarioRegistry.get()` to return portfolios (AC: 1, 5)

- [ ] 3.1 Widen `get()` return type to `BaselineScenario | ReformScenario | PolicyPortfolio`
- [ ] 3.2 Check `_registry_type` in metadata to determine whether to call `_dict_to_scenario()` or `_dict_to_portfolio()` for deserialization
- [ ] 3.3 Portfolio integrity check: regenerate version ID from loaded content and compare to file name (same pattern as `_ensure_version_integrity()` for scenarios)

### Task 4: Add type-distinguishable listing (AC: 3)

- [ ] 4.1 Add `get_entry_type(name: str) -> str` method returning `"baseline"`, `"reform"`, or `"portfolio"` by reading `_registry_type` from metadata.yaml. For legacy entries without the `_registry_type` field, infer type by loading the latest version file and checking for `baseline_ref` (present → `"reform"`, absent → `"baseline"`). Persist the inferred type back to metadata for future reads
- [ ] 4.2 Update `RegistryEntry` to include an `entry_type: str` field (default `"scenario"` for backward compat of callers constructing `RegistryEntry` directly). Registry-populated entries use `"baseline"`, `"reform"`, or `"portfolio"` from metadata `_registry_type`
- [ ] 4.3 Update `get_entry()` to populate the new `entry_type` field from metadata
- [ ] 4.4 Add `list_portfolios() -> list[str]` convenience method that filters `list_scenarios()` by `_registry_type == "portfolio"`
- [ ] 4.5 Keep `list_scenarios()` returning ALL entries (both scenarios and portfolios) for backward compatibility. Document that it returns all registry entries regardless of type

### Task 5: Extend supporting methods for portfolios (AC: 6, 7)

- [ ] 5.1 `list_versions(name)` — works for portfolios unchanged (metadata structure is identical)
- [ ] 5.2 `exists(name, version_id)` — works for portfolios unchanged
- [ ] 5.3 `clone(name, version_id, new_name)` — extend to support portfolios: detect type, call `replace(portfolio, name=clone_name)` for `PolicyPortfolio`
- [ ] 5.4 `set_validated()` / `is_validated()` — work for portfolios unchanged (metadata-level operations)
- [ ] 5.5 `_ensure_version_integrity()` — create portfolio-aware variant that uses `_generate_portfolio_version_id()` for content hash verification
- [ ] 5.6 `migrate()` — add an early guard: if the entry is a portfolio (`_registry_type == "portfolio"` in metadata), raise `RegistryError(summary="Migration not supported for portfolios", ...)`. Portfolio migration is out of scope (see Scope Boundaries). `get_baseline()` and `list_reforms()` are naturally safe — they use `isinstance` checks that reject non-scenario types

### Task 6: Extend `_save_scenario_file()` and `_load_scenario_file()` (AC: 1, 5)

- [ ] 6.1 Rename or generalize `_save_scenario_file()` to handle both scenarios and portfolios. Use atomic write pattern (temp file + `os.replace()`) — same as existing implementation
- [ ] 6.2 Rename or generalize `_load_scenario_file()` to detect `_registry_type` in loaded YAML and dispatch to correct deserialization
- [ ] 6.3 Portfolio YAML uses `yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)` — same serialization options as scenarios (note: `sort_keys=False` for version files, `sort_keys=True` for version ID generation — matching existing scenario pattern)

### Task 7: Update `__init__.py` exports (AC: all)

- [ ] 7.1 If `RegistryEntry` gains `entry_type` field, no new exports needed (existing exports cover it)
- [ ] 7.2 Add `list_portfolios` to `ScenarioRegistry` (new method, no separate export needed — it's a method on the class)
- [ ] 7.3 Update module docstring in `registry.py` to mention portfolio support

### Task 8: Write tests in `tests/templates/test_registry_portfolios.py` (AC: all)

- [ ] 8.1 Create new test file with module docstring referencing Story 12.4
- [ ] 8.2 **TestPortfolioRegistrySaveAndGet** (AC1, AC5): Save a 2-policy portfolio, retrieve by version ID, assert frozen dataclass equality (`==`). Verify all fields: name, policies (each PolicyConfig), version, description, resolution_strategy
- [ ] 8.3 **TestPortfolioRegistryVersioning** (AC2, AC4): Save portfolio, modify a policy, re-save. Assert different version IDs. Assert both versions retrievable. Assert idempotent save (same content = same version ID)
- [ ] 8.4 **TestPortfolioRegistryListing** (AC3): Save both a scenario and a portfolio. Call `list_scenarios()` — both present. Call `list_portfolios()` — only portfolio. Call `get_entry()` — `entry_type` distinguishes them
- [ ] 8.5 **TestPortfolioRegistryVersionHistory** (AC6): Save 3 versions of a portfolio. `list_versions()` returns 3 entries in chronological order with correct parent_version links and change descriptions
- [ ] 8.6 **TestPortfolioRegistryClone** (AC1): Clone a portfolio, assert new name, identical policies
- [ ] 8.7 **TestPortfolioRegistryErrors** (AC7): Invalid name raises `RegistryError`. Non-existent portfolio raises `ScenarioNotFoundError`. Non-existent version raises `VersionNotFoundError`. Saving a portfolio under an existing scenario name raises `RegistryError` (type mismatch). Calling `migrate()` on a portfolio entry raises `RegistryError`
- [ ] 8.8 **TestPortfolioRegistryIntegrity** (AC4): Content integrity check passes on load. Tampered version file detected
- [ ] 8.9 **TestPortfolioRegistryRoundTrip** (AC5): Save → get round-trip preserves full PolicyPortfolio equality including nested PolicyConfig objects with CarbonTaxParameters, SubsidyParameters, FeebateParameters
- [ ] 8.10 **TestPortfolioRegistryValidatedFlag** (AC6): `set_validated()` / `is_validated()` work for portfolio entries
- [ ] 8.11 **TestPortfolioRegistryBackwardCompat** (AC3): Registry with pre-existing scenario entries (no `_registry_type` field) still works correctly. Default type is inferred as scenario

### Task 9: Run quality checks (AC: all)

- [ ] 9.1 Run `uv run pytest tests/templates/test_registry_portfolios.py -v` — all tests pass
- [ ] 9.2 Run `uv run pytest tests/templates/test_registry.py -v` — all existing registry tests pass (no regressions)
- [ ] 9.3 Run `uv run pytest tests/templates/portfolios/ -v` — all portfolio tests pass
- [ ] 9.4 Run `uv run ruff check src/reformlab/templates/registry.py tests/templates/test_registry_portfolios.py`
- [ ] 9.5 Run `uv run mypy src/reformlab/templates/registry.py` — passes strict mode
- [ ] 9.6 Run full test suite: `uv run pytest tests/ -v`

## Dev Notes

### Architecture Decisions

**Design: Extend ScenarioRegistry, don't create a separate PortfolioRegistry**

The acceptance criteria require "portfolios and individual scenarios are both listable and distinguishable by type" from the same registry. This means extending `ScenarioRegistry` to handle `PolicyPortfolio` alongside `BaselineScenario` and `ReformScenario`, not creating a parallel registry class.

Key reasons:
1. Registry directory structure and metadata pattern are generic — they work for any versioned, content-addressable artifact
2. Users expect a single registry to browse all policy artifacts
3. Avoids duplicating file I/O, metadata parsing, version history, integrity checks

**Design: `_registry_type` marker for type discrimination**

The version YAML files need a way to indicate whether they contain a scenario or a portfolio. Options considered:

- **Option A: Detect from content structure** (e.g., presence of `policies` key vs `policy_type` key) — fragile, relies on structural inference
- **Option B: `_registry_type` field in metadata.yaml** — clean, explicit, backward compatible (absent = scenario)

**Chosen: Option B** — `_registry_type` stored in `metadata.yaml` with values `"baseline"`, `"reform"`, or `"portfolio"`. This is set once when the first version is saved and checked on every `get()`. Backward compatibility: entries without `_registry_type` infer type from the latest version content (`baseline_ref` present → `"reform"`, absent → `"baseline"`).

The `_registry_type` marker is ALSO stored in each version YAML file (as part of the serialized dict) to enable standalone version file identification without requiring metadata.yaml lookup.

**Design: Reuse existing serialization from `portfolios.composition`**

`portfolio_to_dict()` and `dict_to_portfolio()` from `src/reformlab/templates/portfolios/composition.py` already handle full portfolio serialization/deserialization. The registry layer wraps these with:
1. `_registry_type` marker injection/stripping
2. Content-addressable version ID generation
3. Atomic file I/O

This avoids duplicating the complex policy parameter serialization logic (which handles CarbonTax, Subsidy, Rebate, Feebate with type-specific fields).

**Design: `RegistryEntry.entry_type` field**

The `RegistryEntry` frozen dataclass gains an `entry_type: str` field with default `"scenario"` for backward compatibility. Values: `"baseline"`, `"reform"`, `"portfolio"`. This makes type discrimination available through the standard entry API without requiring separate queries.

Note: This is a **backward-compatible addition** — the new field has a default value, so existing code constructing `RegistryEntry` won't break.

### Key Interfaces to Follow

**Existing `ScenarioRegistry` API** [Source: src/reformlab/templates/registry.py]:
```python
class ScenarioRegistry:
    def save(self, scenario, name, change_description="") -> str  # version_id
    def get(self, name, version_id=None) -> BaselineScenario | ReformScenario
    def list_scenarios(self) -> list[str]
    def list_versions(self, name) -> list[ScenarioVersion]
    def exists(self, name, version_id=None) -> bool
    def get_entry(self, name) -> RegistryEntry
    def clone(self, name, version_id=None, new_name=None) -> scenario
    def set_validated(self, name, version_id=None, *, validated=True) -> None
    def is_validated(self, name, version_id=None) -> bool
```

**Version ID generation pattern** [Source: src/reformlab/templates/registry.py:231-246]:
```python
def _generate_version_id(scenario):
    content = _scenario_to_dict_for_registry(scenario)
    yaml_str = yaml.dump(content, sort_keys=True)
    hash_bytes = hashlib.sha256(yaml_str.encode("utf-8")).hexdigest()[:12]
    return hash_bytes
```

Portfolio version ID generation MUST use the same pattern: convert to dict, `yaml.dump(content, sort_keys=True)`, SHA-256, 12-char prefix. The dict MUST include `_registry_type: "portfolio"` to ensure portfolio and scenario version IDs never collide even if content is superficially similar. The `$schema` field MUST be normalized to a stable relative path (e.g., `"portfolio.schema.json"`) before hashing — `portfolio_to_dict()` emits a machine-specific absolute path via `Path(__file__)` that would break cross-machine determinism.

**Atomic file save pattern** [Source: src/reformlab/templates/registry.py:1013-1038]:
```python
def _save_scenario_file(self, scenario, path):
    data = _scenario_to_dict_for_registry(scenario)
    fd, tmp_path = tempfile.mkstemp(suffix=".yaml", prefix=".tmp_", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
        os.replace(tmp_path, path)
    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
```

**Portfolio serialization** [Source: src/reformlab/templates/portfolios/composition.py:54-80]:
```python
def portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]:
    # Returns: {"$schema": ..., "name": ..., "version": ..., "description": ...,
    #           "policies": [...], "resolution_strategy": ...}
```

**Portfolio deserialization** [Source: src/reformlab/templates/portfolios/composition.py:145-255]:
```python
def dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio:
    # Reconstructs PolicyPortfolio from dict, including per-policy type handling
```

**RegistryEntry dataclass** [Source: src/reformlab/templates/registry.py:138-145]:
```python
@dataclass(frozen=True)
class RegistryEntry:
    name: str
    created: datetime
    latest_version: str
    versions: tuple[ScenarioVersion, ...]
```

The new `entry_type` field must be added with a default to maintain backward compatibility:
```python
@dataclass(frozen=True)
class RegistryEntry:
    name: str
    created: datetime
    latest_version: str
    versions: tuple[ScenarioVersion, ...]
    entry_type: str = "scenario"  # "baseline", "reform", "portfolio"
```

### Existing Error Pattern

All registry errors use structured kwargs [Source: src/reformlab/templates/registry.py:44-74]:
```python
class RegistryError(Exception):
    def __init__(self, *, summary, reason, fix, scenario_name="", version_id=""):
```

Portfolio errors should use the same pattern. The `scenario_name` parameter is slightly misnamed for portfolios but changing it would break backward compatibility — use it as the entry name regardless of type.

### Scope Boundaries

**IN SCOPE:**
- Extend `ScenarioRegistry` to save/get/list/clone `PolicyPortfolio` objects
- Content-addressable versioning for portfolios
- Type discrimination (`entry_type` field on `RegistryEntry`, `list_portfolios()` method)
- Version history tracking (same metadata pattern)
- Integrity checking for portfolio version files
- Round-trip fidelity for all portfolio fields
- Backward compatibility with existing scenario-only registries

**OUT OF SCOPE (deferred to future stories):**
- Portfolio-aware `from_workflow_config()` factory — Story 12.5 or later
- `WorkflowConfig` integration with portfolio references — Story 12.5 or later
- Multi-portfolio comparison — Story 12.5
- Portfolio migration (version upgrades) — future story
- Portfolio-specific `get_baseline()` / `list_reforms()` (portfolios don't have baseline_ref) — N/A

### Project Structure Notes

**Modified files:**
```
src/reformlab/templates/registry.py           ← Main changes: save/get/list/clone portfolio support
```

**New files:**
```
tests/templates/test_registry_portfolios.py   ← All portfolio registry tests
```

**Files NOT to modify:**
```
src/reformlab/templates/portfolios/portfolio.py     ← No changes needed
src/reformlab/templates/portfolios/composition.py   ← No changes needed (reuse existing serialization)
src/reformlab/templates/portfolios/__init__.py       ← No changes needed
src/reformlab/templates/__init__.py                  ← No new exports needed (RegistryEntry already exported)
src/reformlab/orchestrator/                          ← No changes (Story 12.3 already done)
```

### Code Conventions to Follow

- `from __future__ import annotations` at top of every file
- `if TYPE_CHECKING:` guards for type-only imports
- Frozen dataclasses for all domain types; mutate via `dataclasses.replace()`
- Structured error messages with `summary`, `reason`, `fix` kwargs
- `logging.getLogger(__name__)` for logger
- Section separators `# ====...====` for major sections in longer modules
- All domain types are frozen — `RegistryEntry` uses `@dataclass(frozen=True)`
- `yaml.safe_dump` for file output, `yaml.safe_load` for file input
- Deterministic serialization: `sort_keys=True` for version ID generation, `sort_keys=False` for file storage

### Test Patterns to Follow

**From existing registry tests** [Source: tests/templates/test_registry.py]:
- Use `tmp_path` for temporary registry directory
- Create registry with `ScenarioRegistry(tmp_path)` then `registry.initialize()`
- Build test scenarios inline using `BaselineScenario(...)` or `ReformScenario(...)`
- Assert round-trip equality with `==` on frozen dataclasses
- Test error cases with `pytest.raises(ErrorClass)` and check structured error fields

For portfolio tests, build portfolios inline using `PolicyPortfolio(name=..., policies=(...))` with `PolicyConfig` wrapping `CarbonTaxParameters`, `SubsidyParameters`, etc.

### Performance Considerations

Portfolio serialization/deserialization is slightly more complex than scenarios (nested policies), but registry operations are inherently I/O-bound and typically handle single entries. No optimization needed.

### References

- [Source: docs/epics.md#BKL-1204] — Story acceptance criteria
- [Source: docs/prd.md#FR43] — "Analyst can compose multiple individual policy templates into a named policy portfolio"
- [Source: src/reformlab/templates/registry.py] — Existing ScenarioRegistry implementation (1223 lines)
- [Source: src/reformlab/templates/registry.py:128-145] — `ScenarioVersion` and `RegistryEntry` dataclasses
- [Source: src/reformlab/templates/registry.py:231-246] — `_generate_version_id()` pattern
- [Source: src/reformlab/templates/registry.py:290-396] — `save()` method with idempotent save logic
- [Source: src/reformlab/templates/registry.py:398-465] — `get()` method with version resolution
- [Source: src/reformlab/templates/registry.py:467-481] — `list_scenarios()` method
- [Source: src/reformlab/templates/registry.py:574-608] — `clone()` method
- [Source: src/reformlab/templates/registry.py:1013-1038] — Atomic file save pattern
- [Source: src/reformlab/templates/registry.py:1040-1045] — `_load_scenario_file()` pattern
- [Source: src/reformlab/templates/registry.py:1069-1222] — `_dict_to_scenario()` and `_dict_to_policy()` deserialization
- [Source: src/reformlab/templates/portfolios/composition.py:54-80] — `portfolio_to_dict()` serialization
- [Source: src/reformlab/templates/portfolios/composition.py:145-255] — `dict_to_portfolio()` deserialization
- [Source: src/reformlab/templates/portfolios/composition.py:760-771] — `dump_portfolio()` YAML output
- [Source: src/reformlab/templates/portfolios/portfolio.py] — `PolicyPortfolio` and `PolicyConfig` frozen dataclasses
- [Source: src/reformlab/templates/portfolios/exceptions.py] — `PortfolioError` hierarchy
- [Source: docs/project-context.md#Architecture] — Adapter isolation, frozen dataclasses, deterministic serialization
- [Source: docs/project-context.md#Testing] — Mirror source structure, class-based grouping, direct assertions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

### Change Log

### File List


]]></file>
<file id="5f010a98" path="bmad-assist.example.yaml" label="CONFIG FILE"><![CDATA[

# bmad-assist configuration for ReformLab
# Strategy: GLM-5 creates/devs/synth/retro, Gemini+GLM-5+Codex validate/review

project_name: ReformLab
user_name: Lucas
communication_language: English
document_output_language: English
user_skill_level: intermediate

timeouts:
  default: 600
  retries: 2
  create_story: 900
  dev_story: 3600

providers:
  master:
    provider: opencode
    model: zai-coding-plan/glm-5

  helper:
    provider: claude-subprocess
    model: sonnet

# Per-phase model assignment
# GLM-5 creates/devs/synth/retro, Gemini+GLM-5+Codex validate/review
phase_models:
  # --- Creative phases: GLM-5 ---
  create_story:
    provider: opencode
    model: zai-coding-plan/glm-5
  dev_story:
    provider: opencode
    model: zai-coding-plan/glm-5


[... TRUNCATED at line 35 due to token budget ...]

]]></file>
<file id="cf8fe244" path="data/populations/demo-quickstart-100.csv" label="FILE"><![CDATA[

"household_id","income","carbon_emissions"
0,15418.280395373651,2.103133555242056
1,14341.823812306122,2.15152077652919
2,16296.33911912492,2.1284878520100574
3,16606.126442056637,2.4453648958053034
4,19613.295798287058,2.2932305747657615
5,18437.015772145955,2.5063350670893842
6,19990.705000528666,2.5478793922261485
7,18815.561982532137,2.1582422814672477
8,21389.456514286816,3.0705521203970805
9,21061.21886642946,2.928549922755728
10,25200.432348506583,3.744356177429086
11,24357.59342894897,3.6388473134706185
12,26635.12342497006,3.1467517155100984
13,23318.926459688297,3.1136308505790504
14,28641.416545250704,3.6915933097496385
15,24529.854853345914,3.2981158419118186
16,28249.009837032798,3.8582211367220873
17,27022.340916126708,3.391950120692449
18,28269.903717834608,3.2444265166765094
19,30166.704113315784,3.917121058892082
20,33653.54770844158,3.7517284447516213
21,31451.085471997394,4.106791169617447
22,32444.551869735333,3.6730498745610682
23,32830.48991538197,3.6158344856903115
24,31264.333061084057,3.6443141174486766
25,32023.556298111773,3.7921307660217174
26,37530.34957900034,5.171099881350255
27,37948.64377165638,4.511510259972174
28,40465.07389967056,5.6300261836019825
29,36853.47556207065,5.131357948310567
30,35672.72790745819,4.381272269181671
31,38047.33116964099,4.6233895693450515
32,43520.994974957954,6.072835754879046
33,40992.99771072067,5.160875475419836
34,41107.49805085283,4.5208175824927626
35,45572.39217440385,6.638615373933117
36,46554.828554122825,6.744383593670154
37,41436.398563552866,5.943485087977523
38,43325.13930840031,4.94930040796173
39,46254.88942323709,6.050294958245874
40,43660.37319475648,5.5022682865091035
41,47763.252983291946,5.378485050559915
42,50850.48258749005,6.04560665466166
43,46431.93641877851,6.640869313200955
44,53126.92039705312,6.445771268901275
45,47388.7389669324,5.778651234949906
46,50737.9847655279,7.029246618691654
47,48193.073791843264,6.118572342150392
48,50235.20037845683,5.587046044150384
49,49685.36244930487,6.828284878041161
50,54131.490757153115,6.6295676638185475
51,60401.7518904548,7.817500869008542
52,57129.793586034684,7.952645949072752
53,60386.653770996214,7.893215799766208
54,56693.71776985135,7.534942581300183
55,55395.53952561154,7.133774848376923
56,58082.52255288216,6.394897191213631
57,59436.21426831723,7.201531960260531
58,57048.818452678715,6.266970689216178
59,63209.53252835679,6.983835506133089
60,58566.95720047725,8.035317992011741
61,69912.6795321286,7.775818671731642
62,70542.69521811882,8.666252359465451
63,70345.53948592053,8.742727387804626
64,68989.4526257474,7.459076494033737
65,63602.858259569395,8.08983639873962
66,62789.85431745309,7.445222608691948
67,65575.8792896725,8.46438609374848
68,75427.55604233114,9.223003993296173
69,74793.47473740608,9.658635272013779
70,70733.70220384098,8.687658551154808
71,65058.77439789069,7.395642166294236
72,68838.38347711174,8.775062268572087
73,79211.84686510301,8.655000353071289
74,78968.9457665635,11.071967409150954
75,71101.54545099384,10.257324698954791
76,78998.49117979167,9.40090981001655
77,83131.11299232746,11.141767405343035
78,77631.23952803995,10.55871906168401
79,71745.39525458138,8.398823473388214
80,79158.29240654699,10.857890893166042
81,72655.72303766107,8.74321651978858
82,88027.78579889434,9.672146067794417
83,87912.94780785406,11.781115886066518
84,83393.16159479303,10.498670529255607
85,75439.95819498046,9.265645091323362
86,91174.97135428018,12.972307846101652
87,86056.7742422748,10.976137909634085
88,85737.80724754134,11.509008935265015
89,83018.1026549714,11.619208917310864
90,85476.26159422444,10.099408967663203
91,87691.701341754,11.693369715978633
92,88318.5843577224,10.635118595117566
93,92431.28644704573,11.14221182927651
94,91565.9203947812,12.172114806069144
95,83217.07165170436,10.914088009333218
96,86171.49110862415,11.863596570730193
97,83367.96839988876,9.33969535420166
98,98473.31875356482,13.791671112055347
99,94526.32574670669,12.61481333873273


]]></file>
<file id="ed28383a" path="scripts/check_ai_usage.py" label="SOURCE CODE"><![CDATA[

#!/usr/bin/env python3
"""One-shot local usage snapshot for Claude Code, Codex, and Gemini CLI."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def run_command(args: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return 127, "", "not installed"
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def summarize_cli_error(raw: str, fallback: str) -> str:
    text = (raw or "").strip()
    if not text:
        return fallback

    if "Unexpected token '??='" in text:
        return "Node runtime in this shell is too old for this CLI (`??=` syntax). Use Node 22."

    if "Missing optional dependency @openai/codex-" in text:
        match = re.search(r"Missing optional dependency (@openai/codex-[^.\s]+)", text)
        dep = match.group(1) if match else "@openai/codex-<platform>"
        return f"Codex optional binary mismatch ({dep}). Reinstall under Node 22: npm install -g @openai/codex@latest"

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if any(token in line for token in ("Error:", "SyntaxError:", "TypeError:", "ReferenceError:")):
            return line[:220]
    return lines[0][:220]


def format_epoch(value: Any) -> str:
    try:
        if value is None:
            return "n/a"
        dt = datetime.fromtimestamp(int(value), tz=timezone.utc).astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return "n/a"


def parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def fmt_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return "n/a"


def newest_file(root: Path, pattern: str) -> Path | None:
    if not root.exists():
        return None
    files = list(root.rglob(pattern))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def newest_files(root: Path, pattern: str, limit: int = 30) -> list[Path]:
    if not root.exists():
        return []
    files = list(root.rglob(pattern))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def check_claude() -> list[str]:
    lines = ["[Claude Code]"]
    code, stdout, stderr = run_command(["claude", "auth", "status", "--json"])
    if code == 127:
        lines.append("- CLI: not installed")
    elif code != 0:
        err = summarize_cli_error(stderr or stdout, "auth status failed")
        lines.append(f"- CLI auth check failed: {err}")
    else:
        try:
            data = json.loads(stdout)
            logged = "yes" if data.get("loggedIn") else "no"
            subscription = data.get("subscriptionType", "n/a")
            org_name = data.get("orgName", "n/a")
            lines.append(f"- Logged in: {logged}")
            lines.append(f"- Subscription: {subscription}")
            lines.append(f"- Org: {org_name}")
        except json.JSONDecodeError:
            lines.append("- CLI auth output could not be parsed")

    candidate_files = newest_files(Path.home() / ".claude" / "projects", "*.jsonl", limit=40)
    if not candidate_files:
        lines.append("- Local usage event: not found")
    else:
        latest_usage: dict[str, Any] | None = None
        latest_model = "n/a"
        latest_ts: datetime | None = None
        latest_ts_raw = "n/a"
        for latest_jsonl in candidate_files:
            try:
                with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
                    for raw in handle:
                        raw = raw.strip()
                        if not raw:
                            continue
                        try:
                            item = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        message = item.get("message")
                        if not isinstance(message, dict):
                            continue
                        usage = message.get("usage")
                        if not isinstance(usage, dict):
                            continue
                        ts_raw = item.get("timestamp")
                        ts = parse_iso(ts_raw)
                        if latest_ts is None or (ts and ts >= latest_ts):
                            latest_ts = ts or latest_ts
                            latest_ts_raw = ts_raw if isinstance(ts_raw, str) else "n/a"
                            latest_usage = usage
                            latest_model = str(message.get("model", "n/a"))
            except OSError:
                continue

        if not latest_usage:
            lines.append("- Local usage event: not found")
        else:
            in_tokens = (
                int(latest_usage.get("input_tokens", 0))
                + int(latest_usage.get("cache_creation_input_tokens", 0))
                + int(latest_usage.get("cache_read_input_tokens", 0))
            )
            out_tokens = int(latest_usage.get("output_tokens", 0))
            lines.append(f"- Latest local model: {latest_model}")
            lines.append(f"- Latest local tokens (in/out): {fmt_int(in_tokens)}/{fmt_int(out_tokens)}")
            lines.append(f"- Latest local event time: {latest_ts_raw}")

    lines.append("- Dashboard: https://console.anthropic.com/settings/usage")
    return lines


def check_codex() -> list[str]:
    lines = ["[GPT-Codex]"]
    code, stdout, stderr = run_command(["codex", "login", "status"])
    if code == 127:
        lines.append("- CLI: not installed")
    elif code != 0:
        err = summarize_cli_error(stderr or stdout, "login status failed")
        lines.append(f"- CLI auth check failed: {err}")
    else:
        status_text = stdout or stderr or "available"
        lines.append(f"- Login status: {status_text}")

    latest_jsonl = newest_file(Path.home() / ".codex" / "sessions", "*.jsonl")
    if latest_jsonl is None:
        lines.append("- Local rate-limit snapshot: not found")
    else:
        latest_rate: dict[str, Any] | None = None
        latest_usage: dict[str, Any] | None = None
        latest_ts = "n/a"
        try:
            with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
                for raw in handle:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        item = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if item.get("type") != "event_msg":
                        continue
                    payload = item.get("payload")
                    if not isinstance(payload, dict) or payload.get("type") != "token_count":
                        continue
                    rate = payload.get("rate_limits")
                    info = payload.get("info") or {}
                    usage = info.get("total_token_usage")
                    if isinstance(rate, dict):
                        latest_rate = rate
                        latest_usage = usage if isinstance(usage, dict) else None
                        latest_ts = str(item.get("timestamp", "n/a"))
        except OSError:
            latest_rate = None

        if not latest_rate:
            lines.append("- Local rate-limit snapshot: not found")
        else:
            primary = latest_rate.get("primary", {})
            secondary = latest_rate.get("secondary", {})
            lines.append(
                f"- Primary window used: {primary.get('used_percent', 'n/a')}% (resets {format_epoch(primary.get('resets_at'))})"
            )
            lines.append(
                f"- Secondary window used: {secondary.get('used_percent', 'n/a')}% (resets {format_epoch(secondary.get('resets_at'))})"
            )
            if latest_usage:
                total = latest_usage.get("total_tokens")
                lines.append(f"- Latest local total tokens: {fmt_int(total)}")
            lines.append(f"- Snapshot time: {latest_ts}")

    lines.append("- API dashboard: https://platform.openai.com/usage")
    lines.append("- ChatGPT plan dashboard: https://chatgpt.com/")
    return lines


def check_gemini() -> list[str]:
    lines = ["[Gemini CLI]"]
    code, stdout, stderr = run_command(["gemini", "--version"])
    if code == 127:
        lines.append("- CLI: not installed")
    elif code != 0:
        err = summarize_cli_error(stderr or stdout, "version check failed")
        lines.append(f"- CLI check failed: {err}")
    else:
        lines.append(f"- CLI version: {stdout}")

    has_env_auth = any(
        os.getenv(key)
        for key in ("GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_GENAI_USE_GCA")
    )
    has_oauth = (Path.home() / ".gemini" / "oauth_creds.json").exists()
    lines.append(f"- Auth configured: {'yes' if (has_env_auth or has_oauth) else 'no'}")

    prompt_count = 0
    latest_prompt_ts: datetime | None = None
    latest_prompt_raw = "n/a"
    tmp_root = Path.home() / ".gemini" / "tmp"
    if tmp_root.exists():
        for log_file in tmp_root.rglob("logs.json"):
            try:
                with log_file.open("r", encoding="utf-8", errors="ignore") as handle:
                    data = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, list):
                continue
            for row in data:
                if not isinstance(row, dict) or row.get("type") != "user":
                    continue
                prompt_count += 1
                ts_raw = row.get("timestamp")
                ts = parse_iso(ts_raw)
                if ts and (latest_prompt_ts is None or ts >= latest_prompt_ts):
                    latest_prompt_ts = ts
                    latest_prompt_raw = str(ts_raw)
    lines.append(f"- Local prompts recorded: {prompt_count}")
    lines.append(f"- Latest local prompt time: {latest_prompt_raw}")
    lines.append("- Dashboard: https://aistudio.google.com/")
    return lines


def open_dashboards() -> None:
    urls = [
        "https://console.anthropic.com/settings/usage",
        "https://platform.openai.com/usage",
        "https://chatgpt.com/",
        "https://aistudio.google.com/",
    ]
    opener = None
    if sys.platform == "darwin":
        opener = "open"
    elif sys.platform.startswith("linux"):
        opener = "xdg-open"
    if not opener:
        return
    for url in urls:
        subprocess.run([opener, url], check=False, capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check local usage snapshots for Claude/Codex/Gemini.")
    parser.add_argument(
        "--open-dashboards",
        action="store_true",
        help="Open provider usage dashboards in your browser.",
    )
    args = parser.parse_args()

    print("AI usage snapshot (local + dashboard links)")
    print(f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print("Note: provider billing dashboards remain the source of truth.\n")

    for section in (check_claude(), check_codex(), check_gemini()):
        for line in section:
            print(line)
        print()

    if args.open_dashboards:
        open_dashboards()
        print("Opened dashboards in browser.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


]]></file>
<file id="90dfc412" path="[ANTIPATTERNS - DO NOT REPEAT]" label="VIRTUAL CONTENT"><![CDATA[

# Epic 12 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 12-1 (2026-03-05)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Immutability breach - `list_policies()` returns direct reference to mutable `rate_schedule` dict, allowing external mutation of internal state. | Changed line 116 to return `dict(config.policy.rate_schedule)` instead of direct reference |
| high | Package integration gap - Portfolio types not exported from `reformlab.templates` | Added PolicyConfig, PolicyPortfolio, and portfolio exceptions to imports and __all__ list |
| high | Schema too permissive - No `additionalProperties: false` at root/policy levels, typos silently accepted | Added `additionalProperties: false` to root, policy item, and policy.parameters objects |
| high | Test data format mismatch - Test uses `redistribution_type` but loader expects `redistribution: {type: ...}` | Updated test to use canonical nested format |
| high | Unused imports - `yaml` imported but not used in test file, **Source**: Reviewer A | Removed unused `yaml` import |
| medium | Lint violations - Unused `PolicyType` import and unused `lines` variable | Removed unused imports |
| medium | Story traceability incomplete - Tasks marked incomplete despite implementation | Deferred (not applying - outside scope of code fixes) |

## Story 12-3 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `_merge_policy_results()` uses `inner` join, silently dropping households not present in all policy outputs — violates "Data contracts fail loudly" rule | Added household_id set consistency validation before merge; changed join to `left outer`; raise `PortfolioComputationStepError` on mismatch |
| critical | No uniqueness check on `household_id` before join — duplicate keys cause cartesian row explosion | Added duplicate household_id detection per policy result; raise `PortfolioComputationStepError` with count details |
| high | Mutable `list` stored in `YearState.data[PORTFOLIO_RESULTS_KEY]` undermines immutability semantics | Changed to `tuple(policy_results)` |
| medium | Repeated `append_column` calls create unnecessary intermediate PyArrow tables | Build columns/names arrays then construct table via `pa.table(dict(...))` in single operation; simplified first-policy path to use `renamed_table` directly |
| medium | Type hint `"PolicyConfig"` with `# noqa: F821` for undefined name in conftest | Imported `ComputationPolicyConfig` from `reformlab.computation.types` and used it directly |


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

**Adversarial Code Review Report**

**Story:** [/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md)

## Review Summary

| Category | Issues Found |
|---|---:|
| Git vs Story Discrepancies | 1 |
| AC Implementation Gaps | 4 |
| Task Completion Lies | 0 |
| SOLID / Abstraction Violations | 2 |
| Hidden Bugs | 5 |
| Performance Footguns | 1 |
| Security Vulnerabilities | 0 |
| **Total Issues** | **8** |

## Findings (Ordered by Severity)

1. **CRITICAL: `save()`/`get()` call undefined methods (`_save_entry_file`, `_load_entry_file`)**
Evidence: [registry.py:452](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:452), [registry.py:498](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:498), [registry.py:588](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:588), only `_save_scenario_file`/`_load_scenario_file` exist at [registry.py:1208](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:1208), [registry.py:1235](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:1235).  
Impact: Runtime `AttributeError`; AC1/AC2/AC4/AC5/AC6 effectively blocked.

2. **CRITICAL: `get()` does not implement required type-based portfolio deserialization path**
Evidence: `get()` never reads `_registry_type` or dispatches to portfolio deserializer in [registry.py:527](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:527)-[594](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:594); helper exists but is unused at [registry.py:231](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:231).  
Impact: AC1/AC5 contract not met even conceptually (Task 3.2 missing in implementation).

3. **IMPORTANT: Required Story 12.4 test file is missing**
Evidence: Story requires new file at [12-4 story:261](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md:261)-[264](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md:264) and detailed tests at [12-4 story:88](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md:88)-[109](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md:109); missing path: [/Users/lucas/Workspace/reformlab/tests/templates/test_registry_portfolios.py](/Users/lucas/Workspace/reformlab/tests/templates/test_registry_portfolios.py).  
Impact: AC coverage for portfolio registry behavior is absent.

4. **IMPORTANT: Existing registry tests do not cover portfolio registry behavior**
Evidence: [test_registry.py:1](/Users/lucas/Workspace/reformlab/tests/templates/test_registry.py:1)-[37](/Users/lucas/Workspace/reformlab/tests/templates/test_registry.py:37) imports only scenario types, no `PolicyPortfolio`-level cases.  
Impact: Regressions in Story 12.4 path are not guarded.

5. **IMPORTANT: `list_portfolios()` suppresses `RegistryError` and hides corruption**
Evidence: broad swallow at [registry.py:747](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:747)-[752](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:752).  
Impact: Violates fail-loud data-contract principle; corrupted entries disappear silently.

6. **IMPORTANT: Type inference/metadata load path can return wrong type or throw non-Registry exceptions**
Evidence: `_infer_registry_type()` defaults to `"baseline"` on missing latest version/file at [registry.py:272](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:272)-[278](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:278); `_load_metadata()` returns raw `safe_load` without dict validation at [registry.py:1258](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:1258)-[1262](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:1262), then `.get()` is assumed at [registry.py:726](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:726).  
Impact: Misclassification and non-actionable crashes (`AttributeError`/`yaml` errors) instead of structured `RegistryError`.

7. **MINOR: Task 4.5 documentation requirement not met**
Evidence: story requires documenting that `list_scenarios()` returns all entries at [12-4 story:65](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md:65); method doc still says “List all scenario names” at [registry.py:596](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:596)-[600](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:600).  
Impact: API contract confusion for callers.

8. **MINOR: Partial refactor left dead code/unintegrated helpers**
Evidence: `_dict_to_portfolio_from_registry()` defined at [registry.py:231](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:231) but not integrated into retrieval flow; legacy `_save_scenario_file`/`_load_scenario_file` remain at [registry.py:1208](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:1208), [registry.py:1235](/Users/lucas/Workspace/reformlab/src/reformlab/templates/registry.py:1235) while new call sites target different names.  
Impact: Maintenance debt and high regression risk.

## Evidence Score

| Severity | Source | Score |
|---|---|---:|
| CRITICAL | Missing `_save_entry_file` / `_load_entry_file` integration | +3.0 |
| CRITICAL | Missing `_registry_type`-based dispatch in `get()` | +3.0 |
| IMPORTANT | Missing `test_registry_portfolios.py` | +1.0 |
| IMPORTANT | No portfolio coverage in existing registry tests | +1.0 |
| IMPORTANT | `list_portfolios()` swallows `RegistryError` | +1.0 |
| IMPORTANT | Unsafe metadata/type inference error handling | +1.0 |
| MINOR | `list_scenarios()` doc mismatch with story | +0.3 |
| MINOR | Dead code from incomplete refactor | +0.3 |
| CLEAN PASS | Security vulnerabilities not identified in reviewed scope | -0.5 |

**Evidence Score:** `10.1`  
**Verdict:** `REJECT`

## Suggested Fixes

1. Implement `_save_entry_file()` and `_load_entry_file()` and wire them to scenario/portfolio serialization-deserialization.
2. In `get()`, explicitly branch on metadata `_registry_type` (or version marker) and call `_dict_to_scenario()` vs `_dict_to_portfolio_from_registry()`.
3. Add the missing test module [/Users/lucas/Workspace/reformlab/tests/templates/test_registry_portfolios.py](/Users/lucas/Workspace/reformlab/tests/templates/test_registry_portfolios.py) with AC1–AC7 coverage from story Task 8.
4. Remove silent error swallowing in `list_portfolios()`; surface corruption with actionable `RegistryError`.
5. Harden `_load_metadata()` and `_infer_registry_type()` with strict type validation and structured error wrapping.
6. Align `list_scenarios()` docstring to “all registry entries”.
7. Remove or rename dead legacy helpers to match the actual call graph.

**Review Actions**
- Issues Found: 8
- Issues Fixed: 0 (read-only validation scope)
- Action Items Created: 0

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

**🔥 ADVERSARIAL CODE REVIEW COMPLETE, User!**

**Story:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md

---

## 📊 Review Summary

| Category | Issues Found |
|----------|--------------|
| Git vs Story Discrepancies | 1 |
| AC Implementation Gaps | 7 |
| Task Completion Lies | 2 |
| SOLID Violations | 2 |
| Hidden Bugs | 2 |
| Performance Footguns | 0 |
| Security Vulnerabilities | 0 |
| **Total Issues** | **8** |

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟠 IMPORTANT | Grossly Inaccurate Project Structure Notes in Story File. The "Project Structure Notes" section in the STORY FILE (ID: 4f02ed14) is critically incomplete and misleading. It fails to list numerous new and modified files essential to the implementation of this story, and directly contradicts itself by listing files as "NOT to modify" (e.g., src/reformlab/templates/portfolios/portfolio.py, src/reformlab/templates/portfolios/composition.py, src/reformlab/templates/__init__.py) that are demonstrably new or heavily modified in the git-diff. This indicates a significant breakdown in planning, documentation, or task definition. | git-diff (ID: dc422a86) vs STORY FILE (ID: 4f02ed14) "Project Structure Notes" | +1 |
| 🔴 CRITICAL | Missing `_load_entry_file` implementation and `_load_scenario_file` generalization. `ScenarioRegistry.get()` in `src/reformlab/templates/registry.py` calls an undeclared method `self._load_entry_file()`. Furthermore, the existing `_load_scenario_file()` method, which `Task 6.2` specified to "Rename or generalize ... to detect `_registry_type` ... and dispatch", remains unchanged and exclusively calls `_dict_to_scenario()`. This means `PolicyPortfolio` objects cannot be correctly deserialized and retrieved by `get()`. | `src/reformlab/templates/registry.py`, `get()` and `_load_scenario_file` methods. | +3 |
| 🔴 CRITICAL | Missing `_save_entry_file` implementation and `_save_scenario_file` generalization. `ScenarioRegistry.save()` in `src/reformlab/templates/registry.py` calls an undeclared method `self._save_entry_file()`. The existing `_save_scenario_file()` was not generalized as instructed by `Task 6.1` to handle both scenarios and portfolios. This means `PolicyPortfolio` objects cannot be correctly serialized and saved to the registry. | `src/reformlab/templates/registry.py`, `save()` and `_save_scenario_file` methods. | +3 |
| 🟠 IMPORTANT | Single Responsibility Principle Violation in `_merge_policy_results`. The `_merge_policy_results` function (lines 104-192) in `src/reformlab/orchestrator/portfolio_step.py` has multiple responsibilities: validating `household_id` presence, uniqueness, and set consistency across policies; determining column prefixing strategy based on duplicate policy types; constructing renamed tables; and performing the final join operation. This violates the Single Responsibility Principle. | `src/reformlab/orchestrator/portfolio_step.py`:104-192 | +1 |
| 🟠 IMPORTANT | Single Responsibility Principle Violation in `composition.py`. The `composition.py` module handles portfolio serialization, deserialization, conflict validation, and conflict resolution. While related, these are distinct concerns. `validate_compatibility` further combines multiple types of conflict detection. This high coupling makes the module complex and harder to maintain or test in isolation. | `src/reformlab/templates/portfolios/composition.py` entire file. | +1 |
| 🟠 IMPORTANT | Hardcoded `_DEFAULT_REGISTRY_PATH` not robust for testing/deployment. The `_get_default_registry_path()` function at line 147 in `src/reformlab/templates/registry.py` provides a fallback to `~/.reformlab/registry/` if `REFORMLAB_REGISTRY_PATH` is not set. While convenient, this hardcoded default can make automated testing more difficult (as tests might create unwanted files in the user's home directory or require specific environment setup). It also implies a fixed deployment structure that might not be flexible enough for different environments. It violates the principle of configurable deployment. | `src/reformlab/templates/registry.py`:147 | +1 |
| 🟠 IMPORTANT | Mismatched return types/behavior in `save()` and `get()` due to missing helpers. The type hints for `save()` and `get()` methods in `src/reformlab/templates/registry.py` indicate they can handle and return `PolicyPortfolio` objects. However, due to the critical absence of `_save_entry_file` and `_load_entry_file` (Findings 2 and 3), these methods will either fail or only handle `BaselineScenario | ReformScenario` objects, making the type hints misleading and violating the contract implied by the type signature for `PolicyPortfolio`. | `src/reformlab/templates/registry.py`, `save()` and `get()` method signatures and internal calls. | +1 |
| 🟡 MINOR | Over-exporting in `__init__.py`. The `__init__.py` file in `src/reformlab/templates/` exports `PortfolioError`, `PortfolioSerializationError`, and `PortfolioValidationError` as top-level imports. While this might be a convenience, typically only the base exception (`PortfolioError`) or the most commonly used ones are exposed at the top level to avoid cluttering the namespace. Directly exporting all specific exceptions can lead to a less organized API. | `src/reformlab/templates/__init__.py` | +0.3 |

### Evidence Score: 11.3

| Score | Verdict |
|-------|---------|
| **11.3** | **REJECT** |

---

## 🏛️ Architectural Sins

- **[6/10] Single Responsibility:** The `_merge_policy_results` function (lines 104-192) in `src/reformlab/orchestrator/portfolio_step.py` has multiple responsibilities: validating `household_id` presence, uniqueness, and set consistency across policies; determining column prefixing strategy based on duplicate policy types; constructing renamed tables; and performing the final join operation. This violates the Single Responsibility Principle.
  - 📍 `src/reformlab/orchestrator/portfolio_step.py`:104-192
  - 💡 Fix: Refactor `_merge_policy_results` into smaller, more focused functions, each with a single responsibility (e.g., `_validate_household_ids`, `_determine_column_prefixes`, `_build_renamed_table`, `_join_tables`).

- **[6/10] Single Responsibility:** The `composition.py` module handles portfolio serialization, deserialization, conflict validation, and conflict resolution. While related, these are distinct concerns. `validate_compatibility` further combines multiple types of conflict detection. This high coupling makes the module complex and harder to maintain or test in isolation.
  - 📍 `src/reformlab/templates/portfolios/composition.py`
  - 💡 Fix: Consider splitting `composition.py` into separate modules like `serialization.py`, `validation.py`, and `resolution.py` within the `portfolios` package.

✅ No significant architectural violations detected.

---

## 🐍 Pythonic Crimes &amp; Readability

- **Style/API Design:** The `__init__.py` file in `src/reformlab/templates/` exports `PortfolioError`, `PortfolioSerializationError`, and `PortfolioValidationError` as top-level imports. While this might be a convenience, typically only the base exception (`PortfolioError`) or the most commonly used ones are exposed at the top level to avoid cluttering the namespace. Directly exporting all specific exceptions can lead to a less organized API.
  - 📍 `src/reformlab/templates/__init__.py`

- **Type Safety:** The type hints for `save()` and `get()` methods in `src/reformlab/templates/registry.py` indicate they can handle and return `PolicyPortfolio` objects. However, due to the critical absence of `_save_entry_file` and `_load_entry_file` (Findings 2 and 3), these methods will either fail or only handle `BaselineScenario | ReformScenario` objects, making the type hints misleading and violating the contract implied by the type signature for `PolicyPortfolio`.
  - 📍 `src/reformlab/templates/registry.py`

---

## ⚡ Performance &amp; Scalability

✅ No significant performance issues detected.

---

## 🐛 Correctness &amp; Safety

- **🐛 Bug:** Missing `_load_entry_file` implementation and `_load_scenario_file` generalization. `ScenarioRegistry.get()` in `src/reformlab/templates/registry.py` calls an undeclared method `self._load_entry_file()`. Furthermore, the existing `_load_scenario_file()` method, which `Task 6.2` specified to "Rename or generalize ... to detect `_registry_type` ... and dispatch", remains unchanged and exclusively calls `_dict_to_scenario()`. This means `PolicyPortfolio` objects cannot be correctly deserialized and retrieved by `get()`.
  - 📍 `src/reformlab/templates/registry.py`
  - 🔄 Reproduction: Attempt to call `registry.get()` for a `PolicyPortfolio` entry. This will result in an `AttributeError` for `_load_entry_file` or incorrect deserialization by `_dict_to_scenario`.

- **🐛 Bug:** Missing `_save_entry_file` implementation and `_save_scenario_file` generalization. `ScenarioRegistry.save()` in `src/reformlab/templates/registry.py` calls an undeclared method `self._save_entry_file()`. The existing `_save_scenario_file()` was not generalized as instructed by `Task 6.1` to handle both scenarios and portfolios. This means `PolicyPortfolio` objects cannot be correctly serialized and saved to the registry.
  - 📍 `src/reformlab/templates/registry.py`
  - 🔄 Reproduction: Attempt to call `registry.save()` with a `PolicyPortfolio` object. This will result in an `AttributeError` for `_save_entry_file`.

---

## 🔧 Maintainability Issues

- **💣 Tech Debt:** Hardcoded `_DEFAULT_REGISTRY_PATH` not robust for testing/deployment. The `_get_default_registry_path()` function at line 147 in `src/reformlab/templates/registry.py` provides a fallback to `~/.reformlab/registry/` if `REFORMLAB_REGISTRY_PATH` is not set. While convenient, this hardcoded default can make automated testing more difficult (as tests might create unwanted files in the user's home directory or require specific environment setup). It also implies a fixed deployment structure that might not be flexible enough for different environments. It violates the principle of configurable deployment.
  - 📍 `src/reformlab/templates/registry.py`:147
  - 💥 Explosion radius: Affects deployment flexibility and test isolation for the entire registry system.

---

## 🛠️ Suggested Fixes

### 1. Fix Missing `_save_entry_file` and `_load_entry_file`

**File:** `src/reformlab/templates/registry.py`
**Issue:** The `save()` and `get()` methods call internal helper methods (`self._save_entry_file` and `self._load_entry_file`) that are not defined. The existing `_save_scenario_file` and `_load_scenario_file` were also not generalized as instructed, leading to critical runtime errors and preventing portfolio functionality.

**Corrected code:**
```python
# Assuming the intention was to have a common dispatching method
# Add these methods to the ScenarioRegistry class:

    def _save_entry_file(
        self,
        artifact: BaselineScenario | ReformScenario | PolicyPortfolio,
        path: Path,
    ) -> None:
        """Save a scenario or portfolio to a YAML file atomically.
        Uses atomic write pattern (temp file + replace) for single-machine safety.
        """
        if isinstance(artifact, PolicyPortfolio):
            data = _portfolio_to_dict_for_registry(artifact)
        else:
            data = _scenario_to_dict_for_registry(artifact)

        # Write to temp file first, then replace
        fd, tmp_path = tempfile.mkstemp(
            suffix=".yaml",
            prefix=".tmp_",
            dir=path.parent,
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            os.replace(tmp_path, path)
        except Exception:
            # Clean up temp file on error
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    def _load_entry_file(self, path: Path) -> BaselineScenario | ReformScenario | PolicyPortfolio:
        """Load a scenario or portfolio from a YAML file."""
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Determine type from content to dispatch to correct deserializer
        # Prioritize _registry_type from the file itself if present
        # Fallback to inferring if not (for backward compatibility)
        if isinstance(data, dict) and data.get("_registry_type") == "portfolio":
            return _dict_to_portfolio_from_registry(data)
        else:
            # For scenarios, the _registry_type might not be present in the version file itself,
            # but is expected in metadata.yaml. Here we rely on _dict_to_scenario's robustness
            # or could infer from schema_ref if necessary, but metadata is canonical.
            # _dict_to_scenario can handle dict with baseline_ref.
            return self._dict_to_scenario(data)

# Original _save_scenario_file and _load_scenario_file can be removed or made private helpers for _save_entry_file/_load_entry_file if they are still strictly needed by _dict_to_scenario/policy.
# However, the diff shows _save_scenario_file and _load_scenario_file are methods of ScenarioRegistry.
# If these are now handled by _save_entry_file and _load_entry_file, then _save_scenario_file and _load_scenario_file can be removed.
```

### 2. Refactor `_merge_policy_results` for Single Responsibility

**File:** `src/reformlab/orchestrator/portfolio_step.py`
**Issue:** The `_merge_policy_results` function is overly complex and violates the Single Responsibility Principle.

**Diff:**
```diff
--- a/src/reformlab/orchestrator/portfolio_step.py
+++ b/src/reformlab/orchestrator/portfolio_step.py
@@ -101,6 +101,55 @@
         return pa.table({"household_id": pa.array([], type=pa.int64())})
 
     # Validate household_id column presence, uniqueness, and set consistency
+    _validate_household_id_integrity(results, portfolio)
+
+    # Detect duplicate policy types to decide prefixing strategy
+    type_counts: dict[str, int] = {}
+    for policy_cfg in portfolio.policies:
+        ptype = policy_cfg.policy_type.value
+        type_counts[ptype] = type_counts.get(ptype, 0) + 1
+
+    has_duplicate_types = any(count > 1 for count in type_counts.values())
+
+    # Build merged table starting from household_id of first result
+    merged = results[0].output_fields.select(["household_id"])
+
+    for i, (result, policy_cfg) in enumerate(
+        zip(results, portfolio.policies, strict=True)
+    ):
+        table = result.output_fields
+        ptype = policy_cfg.policy_type.value
+        non_id_cols = [c for c in table.column_names if c != "household_id"]
+
+        # Determine prefix
+        if i == 0 and not has_duplicate_types:
+            # First policy keeps original names when no type duplicates
+            prefix = ""
+        elif has_duplicate_types:
+            prefix = f"{ptype}_{i}_"
+        else:
+            prefix = f"{ptype}_"
+
+        # Build renamed table in a single construction
+        col_arrays = [table.column("household_id")]
+        col_names = ["household_id"]
+        for col_name in non_id_cols:
+            new_name = f"{prefix}{col_name}" if prefix else col_name
+            col_arrays.append(table.column(col_name))
+            col_names.append(new_name)
+        renamed_table = pa.table(
+            dict(zip(col_names, col_arrays, strict=True))
+        )
+
+        # Join on household_id
+        if i == 0:
+            merged = renamed_table
+        else:
+            # Left outer preserves all households from the base table.
+            # Mismatched sets are already caught above, so this is
+            # effectively an equi-join with guaranteed full overlap.
+            merged = merged.join(
+                renamed_table,
+                keys="household_id",
+                join_type="left outer",
+            )
+
+    return merged
+
+
+def _validate_household_id_integrity(
+    results: list[ComputationResult],
+    portfolio: PolicyPortfolio,
+) -> None:
+    """Validate household_id column presence, uniqueness, and set consistency."""
     reference_ids: set[Any] | None = None
     for i, result in enumerate(results):
         table = result.output_fields
         policy_cfg = portfolio.policies[i]
         policy_name = policy_cfg.name or policy_cfg.policy_type.value
-
         if "household_id" not in table.column_names:
             raise PortfolioComputationStepError(
                 f"Policy[{i}] '{policy_name}' "
                 f"output_fields missing required 'household_id' column",
                 year=result.period,
                 adapter_version=result.adapter_version,
                 policy_index=i,
                 policy_name=policy_name,
                 policy_type=policy_cfg.policy_type.value,
             )
-
         hh_ids = table.column("household_id").to_pylist()
         hh_id_set = set(hh_ids)
-
         # Check for duplicate household_ids within a single policy result
         if len(hh_ids) != len(hh_id_set):
             raise PortfolioComputationStepError(
                 f"Policy[{i}] '{policy_name}' output_fields contains "
                 f"duplicate household_id values ({len(hh_ids)} rows, "
                 f"{len(hh_id_set)} unique)",
                 year=result.period,
                 adapter_version=result.adapter_version,
                 policy_index=i,
                 policy_name=policy_name,
                 policy_type=policy_cfg.policy_type.value,
             )
-
         # Check household_id set consistency across policies
         if reference_ids is None:
             reference_ids = hh_id_set
         elif hh_id_set != reference_ids:
             missing = reference_ids - hh_id_set
             extra = hh_id_set - reference_ids
             raise PortfolioComputationStepError(
                 f"Policy[{i}] '{policy_name}' household_id set differs "
                 f"from policy[0]: missing={missing}, extra={extra}",
                 year=result.period,
                 adapter_version=result.adapter_version,
                 policy_index=i,
                 policy_name=policy_name,
                 policy_type=policy_cfg.policy_type.value,
             )
-
-    # Detect duplicate policy types to decide prefixing strategy
-    type_counts: dict[str, int] = {}
-    for policy_cfg in portfolio.policies:
-        ptype = policy_cfg.policy_type.value
-        type_counts[ptype] = type_counts.get(ptype, 0) + 1
-
-    has_duplicate_types = any(count > 1 for count in type_counts.values())
-
-    # Build merged table starting from household_id of first result
-    merged = results[0].output_fields.select(["household_id"])
-
-    for i, (result, policy_cfg) in enumerate(
-        zip(results, portfolio.policies, strict=True)
-    ):
-        table = result.output_fields
-        ptype = policy_cfg.policy_type.value
-        non_id_cols = [c for c in table.column_names if c != "household_id"]
-
-        # Determine prefix
-        if i == 0 and not has_duplicate_types:
-            # First policy keeps original names when no type duplicates
-            prefix = ""
-        elif has_duplicate_types:
-            prefix = f"{ptype}_{i}_"
-        else:
-            prefix = f"{ptype}_"
-
-        # Build renamed table in a single construction
-        col_arrays = [table.column("household_id")]
-        col_names = ["household_id"]
-        for col_name in non_id_cols:
-            new_name = f"{prefix}{col_name}" if prefix else col_name
-            col_arrays.append(table.column(col_name))
-            col_names.append(new_name)
-        renamed_table = pa.table(
-            dict(zip(col_names, col_arrays, strict=True))
-        )
-
-        # Join on household_id
-        if i == 0:
-            merged = renamed_table
-        else:
-            # Left outer preserves all households from the base table.
-            # Mismatched sets are already caught above, so this is
-            # effectively an equi-join with guaranteed full overlap.
-            merged = merged.join(
-                renamed_table,
-                keys="household_id",
-                join_type="left outer",
-            )
-
-    return merged
```

### 3. Refactor `composition.py` for Single Responsibility (Conceptual)

**File:** `src/reformlab/templates/portfolios/composition.py`
**Issue:** The `composition.py` module has too many responsibilities (serialization, deserialization, validation, resolution). This is a conceptual architectural issue.

**Corrected code:** (Conceptual change, requires multiple file moves and new files. This would be a MAJOR REWORK for this module).
```
# Move to src/reformlab/templates/portfolios/serialization.py
def portfolio_to_dict(...)
def _policy_parameters_to_dict(...)
def dict_to_portfolio(...)
def _dict_to_policy_parameters(...)
def dump_portfolio(...)
def load_portfolio(...)

# Move to src/reformlab/templates/portfolios/validation.py
def validate_compatibility(...)

# Move to src/reformlab/templates/portfolios/resolution.py
def resolve_conflicts(...)
def _apply_sum_strategy(...)
def _apply_first_wins_strategy(...)
def _apply_last_wins_strategy(...)
def _apply_max_strategy(...)
```

### 4. Make `_DEFAULT_REGISTRY_PATH` configurable

**File:** `src/reformlab/templates/registry.py`
**Issue:** The default registry path is hardcoded, limiting flexibility.

**Diff:**
```diff
--- a/src/reformlab/templates/registry.py
+++ b/src/reformlab/templates/registry.py
@@ -144,7 +144,7 @@
     return normalized
 
 
-_DEFAULT_REGISTRY_PATH = Path.home() / ".reformlab" / "registry"
+DEFAULT_REGISTRY_SUBDIR = Path(".reformlab") / "registry"
 
 
 def _get_default_registry_path() -> Path:
@@ -152,7 +152,7 @@
     """
     env_path = os.environ.get("REFORMLAB_REGISTRY_PATH")
     if env_path:
         return Path(env_path)
-    return _DEFAULT_REGISTRY_PATH
+    return Path.home() / DEFAULT_REGISTRY_SUBDIR
 
 
 def _scenario_to_dict_for_registry(
```
And then in `ScenarioRegistry.__init__`:
```diff
--- a/src/reformlab/templates/registry.py
+++ b/src/reformlab/templates/registry.py
@@ -250,6 +250,9 @@
         """
         if registry_path is None:
             self._path = _get_default_registry_path()
+        elif isinstance(registry_path, str) and registry_path == "tmp":
+            # Special case for testing: use a temporary directory
+            self._path = Path(tempfile.mkdtemp(prefix="reformlab_registry_"))
         else:
             self._path = Path(registry_path)
```

### 5. Correct `__init__.py` Over-exporting

**File:** `src/reformlab/templates/__init__.py`
**Issue:** Over-exporting specific exception classes.

**Diff:**
```diff
--- a/src/reformlab/templates/__init__.py
+++ b/src/reformlab/templates/__init__.py
@@ -73,9 +73,7 @@
 from reformlab.templates.portfolios import (
     Conflict,
     ConflictType,
-    PolicyConfig,
     PolicyPortfolio,
-    PortfolioError,
     PortfolioSerializationError,
     PortfolioValidationError,
     ResolutionStrategy,
@@ -89,9 +87,8 @@
 )
 
 __all__ = [
-    # Portfolio types
-    "PolicyConfig",
+    # Base Portfolio types
     "PolicyPortfolio",
-    "PortfolioError",
+    "Conflict", # Conflict details
     "PortfolioSerializationError",
     "PortfolioValidationError",
     "Conflict",
```

**Story:** /Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md
**Evidence Score:** 11.3 → **REJECT**

**Review Actions:**
- Issues Found: 8
- Issues Fixed: 0
- Action Items Created: 0

🚫 Code requires significant rework. Review action items carefully.

]]></file>
<file id="dc422a86" path="[git-diff]" label="VIRTUAL CONTENT"><![CDATA[

<!-- GIT_DIFF_START -->
 .gitignore                                         |   3 +
 bmad-assist.example.yaml                           | 109 +++
 bmad-assist.legacy.yaml                            | 108 +++
 bmad-assist.yaml                                   | 109 +++
 data/populations/demo-quickstart-100.csv           | 101 +++
 scripts/check_ai_usage.py                          | 317 ++++++++
 src/reformlab/orchestrator/__init__.py             |  15 +
 src/reformlab/orchestrator/portfolio_step.py       | 498 ++++++++++++
 src/reformlab/population/assumptions.py            |   8 +-
 src/reformlab/population/pipeline.py               |   2 +-
 src/reformlab/templates/__init__.py                |  27 +
 src/reformlab/templates/portfolios/__init__.py     |  40 +
 src/reformlab/templates/portfolios/composition.py  | 824 ++++++++++++++++++++
 src/reformlab/templates/portfolios/enums.py        |  27 +
 src/reformlab/templates/portfolios/exceptions.py   |  51 ++
 src/reformlab/templates/portfolios/portfolio.py    | 168 ++++
 src/reformlab/templates/registry.py                | 285 +++++--
 .../templates/schema/portfolio.schema.json         | 135 ++++
 tests/orchestrator/conftest.py                     | 128 +++
 tests/orchestrator/test_portfolio_step.py          | 867 +++++++++++++++++++++
 tests/population/conftest.py                       |   1 +
 tests/population/test_assumptions.py               |  15 -
 tests/templates/portfolios/__init__.py             |   1 +
 tests/templates/portfolios/conftest.py             |  55 ++
 tests/templates/portfolios/test_composition.py     | 599 ++++++++++++++
 tests/templates/portfolios/test_conflicts.py       | 671 ++++++++++++++++
 tests/templates/portfolios/test_portfolio.py       | 418 ++++++++++
 27 files changed, 5514 insertions(+), 68 deletions(-)

diff --git a/scripts/check_ai_usage.py b/scripts/check_ai_usage.py
new file mode 100755
index 0000000..1e18c43
--- /dev/null
+++ b/scripts/check_ai_usage.py
@@ -0,0 +1,317 @@
+#!/usr/bin/env python3
+"""One-shot local usage snapshot for Claude Code, Codex, and Gemini CLI."""
+
+from __future__ import annotations
+
+import argparse
+import json
+import os
+import re
+import subprocess
+import sys
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Any
+
+
+def run_command(args: list[str]) -> tuple[int, str, str]:
+    try:
+        proc = subprocess.run(args, capture_output=True, text=True, check=False)
+    except FileNotFoundError:
+        return 127, "", "not installed"
+    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
+
+
+def summarize_cli_error(raw: str, fallback: str) -> str:
+    text = (raw or "").strip()
+    if not text:
+        return fallback
+
+    if "Unexpected token '??='" in text:
+        return "Node runtime in this shell is too old for this CLI (`??=` syntax). Use Node 22."
+
+    if "Missing optional dependency @openai/codex-" in text:
+        match = re.search(r"Missing optional dependency (@openai/codex-[^.\s]+)", text)
+        dep = match.group(1) if match else "@openai/codex-<platform>"
+        return f"Codex optional binary mismatch ({dep}). Reinstall under Node 22: npm install -g @openai/codex@latest"
+
+    lines = [line.strip() for line in text.splitlines() if line.strip()]
+    for line in lines:
+        if any(token in line for token in ("Error:", "SyntaxError:", "TypeError:", "ReferenceError:")):
+            return line[:220]
+    return lines[0][:220]
+
+
+def format_epoch(value: Any) -> str:
+    try:
+        if value is None:
+            return "n/a"
+        dt = datetime.fromtimestamp(int(value), tz=timezone.utc).astimezone()
+        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
+    except Exception:
+        return "n/a"
+
+
+def parse_iso(value: Any) -> datetime | None:
+    if not isinstance(value, str):
+        return None
+    try:
+        if value.endswith("Z"):
+            value = value[:-1] + "+00:00"
+        return datetime.fromisoformat(value)
+    except ValueError:
+        return None
+
+
+def fmt_int(value: Any) -> str:
+    try:
+        return f"{int(value):,}"
+    except Exception:
+        return "n/a"
+
+
+def newest_file(root: Path, pattern: str) -> Path | None:
+    if not root.exists():
+        return None
+    files = list(root.rglob(pattern))
+    if not files:
+        return None
+    return max(files, key=lambda p: p.stat().st_mtime)
+
+
+def newest_files(root: Path, pattern: str, limit: int = 30) -> list[Path]:
+    if not root.exists():
+        return []
+    files = list(root.rglob(pattern))
+    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
+    return files[:limit]
+
+
+def check_claude() -> list[str]:
+    lines = ["[Claude Code]"]
+    code, stdout, stderr = run_command(["claude", "auth", "status", "--json"])
+    if code == 127:
+        lines.append("- CLI: not installed")
+    elif code != 0:
+        err = summarize_cli_error(stderr or stdout, "auth status failed")
+        lines.append(f"- CLI auth check failed: {err}")
+    else:
+        try:
+            data = json.loads(stdout)
+            logged = "yes" if data.get("loggedIn") else "no"
+            subscription = data.get("subscriptionType", "n/a")
+            org_name = data.get("orgName", "n/a")
+            lines.append(f"- Logged in: {logged}")
+            lines.append(f"- Subscription: {subscription}")
+            lines.append(f"- Org: {org_name}")
+        except json.JSONDecodeError:
+            lines.append("- CLI auth output could not be parsed")
+
+    candidate_files = newest_files(Path.home() / ".claude" / "projects", "*.jsonl", limit=40)
+    if not candidate_files:
+        lines.append("- Local usage event: not found")
+    else:
+        latest_usage: dict[str, Any] | None = None
+        latest_model = "n/a"
+        latest_ts: datetime | None = None
+        latest_ts_raw = "n/a"
+        for latest_jsonl in candidate_files:
+            try:
+                with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
+                    for raw in handle:
+                        raw = raw.strip()
+                        if not raw:
+                            continue
+                        try:
+                            item = json.loads(raw)
+                        except json.JSONDecodeError:
+                            continue
+                        message = item.get("message")
+                        if not isinstance(message, dict):
+                            continue
+                        usage = message.get("usage")
+                        if not isinstance(usage, dict):
+                            continue
+                        ts_raw = item.get("timestamp")
+                        ts = parse_iso(ts_raw)
+                        if latest_ts is None or (ts and ts >= latest_ts):
+                            latest_ts = ts or latest_ts
+                            latest_ts_raw = ts_raw if isinstance(ts_raw, str) else "n/a"
+                            latest_usage = usage
+                            latest_model = str(message.get("model", "n/a"))
+            except OSError:
+                continue
+
+        if not latest_usage:
+            lines.append("- Local usage event: not found")
+        else:
+            in_tokens = (
+                int(latest_usage.get("input_tokens", 0))
+                + int(latest_usage.get("cache_creation_input_tokens", 0))
+                + int(latest_usage.get("cache_read_input_tokens", 0))
+            )
+            out_tokens = int(latest_usage.get("output_tokens", 0))
+            lines.append(f"- Latest local model: {latest_model}")
+            lines.append(f"- Latest local tokens (in/out): {fmt_int(in_tokens)}/{fmt_int(out_tokens)}")
+            lines.append(f"- Latest local event time: {latest_ts_raw}")
+
+    lines.append("- Dashboard: https://console.anthropic.com/settings/usage")
+    return lines
+
+
+def check_codex() -> list[str]:
+    lines = ["[GPT-Codex]"]
+    code, stdout, stderr = run_command(["codex", "login", "status"])
+    if code == 127:
+        lines.append("- CLI: not installed")
+    elif code != 0:
+        err = summarize_cli_error(stderr or stdout, "login status failed")
+        lines.append(f"- CLI auth check failed: {err}")
+    else:
+        status_text = stdout or stderr or "available"
+        lines.append(f"- Login status: {status_text}")
+
+    latest_jsonl = newest_file(Path.home() / ".codex" / "sessions", "*.jsonl")
+    if latest_jsonl is None:
+        lines.append("- Local rate-limit snapshot: not found")
+    else:
+        latest_rate: dict[str, Any] | None = None
+        latest_usage: dict[str, Any] | None = None
+        latest_ts = "n/a"
+        try:
+            with latest_jsonl.open("r", encoding="utf-8", errors="ignore") as handle:
+                for raw in handle:
+                    raw = raw.strip()
+                    if not raw:
+                        continue
+                    try:
+                        item = json.loads(raw)
+                    except json.JSONDecodeError:
+                        continue
+                    if item.get("type") != "event_msg":
+                        continue
+                    payload = item.get("payload")
+                    if not isinstance(payload, dict) or payload.get("type") != "token_count":
+                        continue
+                    rate = payload.get("rate_limits")
+                    info = payload.get("info") or {}
+                    usage = info.get("total_token_usage")
+                    if isinstance(rate, dict):
+                        latest_rate = rate
+                        latest_usage = usage if isinstance(usage, dict) else None
+                        latest_ts = str(item.get("timestamp", "n/a"))
+        except OSError:
+            latest_rate = None
+
+        if not latest_rate:
+            lines.append("- Local rate-limit snapshot: not found")
+        else:
+            primary = latest_rate.get("primary", {})
+            secondary = latest_rate.get("secondary", {})
+            lines.append(
+                f"- Primary window used: {primary.get('used_percent', 'n/a')}% (resets {format_epoch(primary.get('resets_at'))})"
+            )
+            lines.append(
+                f"- Secondary window used: {secondary.get('used_percent', 'n/a')}% (resets {format_epoch(secondary.get('resets_at'))})"
+            )
+            if latest_usage:
+                total = latest_usage.get("total_tokens")
+                lines.append(f"- Latest local total tokens: {fmt_int(total)}")
+            lines.append(f"- Snapshot time: {latest_ts}")
+
+    lines.append("- API dashboard: https://platform.openai.com/usage")
+    lines.append("- ChatGPT plan dashboard: https://chatgpt.com/")
+    return lines
+
+
+def check_gemini() -> list[str]:
+    lines = ["[Gemini CLI]"]
+    code, stdout, stderr = run_command(["gemini", "--version"])
+    if code == 127:
+        lines.append("- CLI: not installed")
+    elif code != 0:
+        err = summarize_cli_error(stderr or stdout, "version check failed")
+        lines.append(f"- CLI check failed: {err}")
+    else:
+        lines.append(f"- CLI version: {stdout}")
+
+    has_env_auth = any(
+        os.getenv(key)
+        for key in ("GEMINI_API_KEY", "GOOGLE_GENAI_USE_VERTEXAI", "GOOGLE_GENAI_USE_GCA")
+    )
+    has_oauth = (Path.home() / ".gemini" / "oauth_creds.json").exists()
+    lines.append(f"- Auth configured: {'yes' if (has_env_auth or has_oauth) else 'no'}")
+
+    prompt_count = 0
+    latest_prompt_ts: datetime | None = None
+    latest_prompt_raw = "n/a"
+    tmp_root = Path.home() / ".gemini" / "tmp"
+    if tmp_root.exists():
+        for log_file in tmp_root.rglob("logs.json"):
+            try:
+                with log_file.open("r", encoding="utf-8", errors="ignore") as handle:
+                    data = json.load(handle)
+            except (OSError, json.JSONDecodeError):
+                continue
+            if not isinstance(data, list):
+                continue
+            for row in data:
+                if not isinstance(row, dict) or row.get("type") != "user":
+                    continue
+                prompt_count += 1
+                ts_raw = row.get("timestamp")
+                ts = parse_iso(ts_raw)
+                if ts and (latest_prompt_ts is None or ts >= latest_prompt_ts):
+                    latest_prompt_ts = ts
+                    latest_prompt_raw = str(ts_raw)
+    lines.append(f"- Local prompts recorded: {prompt_count}")
+    lines.append(f"- Latest local prompt time: {latest_prompt_raw}")
+    lines.append("- Dashboard: https://aistudio.google.com/")
+    return lines
+
+
+def open_dashboards() -> None:
+    urls = [
+        "https://console.anthropic.com/settings/usage",
+        "https://platform.openai.com/usage",
+        "https://chatgpt.com/",
+        "https://aistudio.google.com/",
+    ]
+    opener = None
+    if sys.platform == "darwin":
+        opener = "open"
+    elif sys.platform.startswith("linux"):
+        opener = "xdg-open"
+    if not opener:
+        return
+    for url in urls:
+        subprocess.run([opener, url], check=False, capture_output=True)
+
+
+def main() -> int:
+    parser = argparse.ArgumentParser(description="Check local usage snapshots for Claude/Codex/Gemini.")
+    parser.add_argument(
+        "--open-dashboards",
+        action="store_true",
+        help="Open provider usage dashboards in your browser.",
+    )
+    args = parser.parse_args()
+
+    print("AI usage snapshot (local + dashboard links)")
+    print(f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')}")
+    print("Note: provider billing dashboards remain the source of truth.\n")
+
+    for section in (check_claude(), check_codex(), check_gemini()):
+        for line in section:
+            print(line)
+        print()
+
+    if args.open_dashboards:
+        open_dashboards()
+        print("Opened dashboards in browser.")
+
+    return 0
+
+
+if __name__ == "__main__":
+    raise SystemExit(main())
diff --git a/src/reformlab/orchestrator/__init__.py b/src/reformlab/orchestrator/__init__.py
index 53a49b2..5e445da 100644
--- a/src/reformlab/orchestrator/__init__.py
+++ b/src/reformlab/orchestrator/__init__.py
@@ -32,6 +32,10 @@ Public API:
 - PanelOutput: Household-by-year panel dataset from orchestrator run (Story 3-7)
 - compare_panels: Helper to compare baseline and reform panels (Story 3-7)
 - PANEL_VERSION: Panel format version for metadata (Story 3-7)
+- PortfolioComputationStep: Portfolio execution step (Story 12-3)
+- PortfolioComputationStepError: Error during portfolio step execution (Story 12-3)
+- PORTFOLIO_METADATA_KEY: Stable key for portfolio metadata (Story 12-3)
+- PORTFOLIO_RESULTS_KEY: Stable key for per-policy results (Story 12-3)
 """
 
 from reformlab.orchestrator.carry_forward import (
@@ -49,6 +53,12 @@ from reformlab.orchestrator.computation_step import (
 )
 from reformlab.orchestrator.errors import OrchestratorError
 from reformlab.orchestrator.panel import PANEL_VERSION, PanelOutput, compare_panels
+from reformlab.orchestrator.portfolio_step import (
+    PORTFOLIO_METADATA_KEY,
+    PORTFOLIO_RESULTS_KEY,
+    PortfolioComputationStep,
+    PortfolioComputationStepError,
+)
 from reformlab.orchestrator.runner import (
     SEED_LOG_KEY,
     STEP_EXECUTION_LOG_KEY,
@@ -113,4 +123,9 @@ __all__ = [
     "PanelOutput",
     "compare_panels",
     "PANEL_VERSION",
+    # Portfolio step (Story 12-3)
+    "PortfolioComputationStep",
+    "PortfolioComputationStepError",
+    "PORTFOLIO_METADATA_KEY",
+    "PORTFOLIO_RESULTS_KEY",
 ]
diff --git a/src/reformlab/orchestrator/portfolio_step.py b/src/reformlab/orchestrator/portfolio_step.py
new file mode 100644
index 0000000..2739217
--- /dev/null
+++ b/src/reformlab/orchestrator/portfolio_step.py
@@ -0,0 +1,498 @@
+"""Portfolio computation step for executing multi-policy portfolios.
+
+This module provides:
+- PortfolioComputationStep: OrchestratorStep for portfolio execution
+- PortfolioComputationStepError: Error during portfolio computation
+- PORTFOLIO_METADATA_KEY: Stable key for portfolio metadata in YearState.metadata
+- PORTFOLIO_RESULTS_KEY: Stable key for per-policy results in YearState.data
+
+Story 12.3 / FR44: Extend orchestrator to execute policy portfolios.
+"""
+
+from __future__ import annotations
+
+import logging
+from dataclasses import asdict, replace
+from typing import TYPE_CHECKING, Any
+
+import pyarrow as pa
+
+from reformlab.orchestrator.computation_step import (
+    COMPUTATION_METADATA_KEY,
+    COMPUTATION_RESULT_KEY,
+)
+
+if TYPE_CHECKING:
+    from reformlab.computation.adapter import ComputationAdapter
+    from reformlab.computation.types import (
+        ComputationResult,
+        PopulationData,
+    )
+    from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig
+    from reformlab.orchestrator.types import YearState
+    from reformlab.templates.portfolios.portfolio import (
+        PolicyConfig as PortfolioPolicyConfig,
+    )
+    from reformlab.templates.portfolios.portfolio import PolicyPortfolio
+    from reformlab.templates.schema import PolicyType
+
+logger = logging.getLogger(__name__)
+
+
+# ============================================================================
+# Stable keys for portfolio data in YearState
+# ============================================================================
+
+PORTFOLIO_METADATA_KEY = "portfolio_metadata"
+PORTFOLIO_RESULTS_KEY = "portfolio_results"
+
+
+# ============================================================================
+# Error class
+# ============================================================================
+
+
+class PortfolioComputationStepError(Exception):
+    """Error during portfolio computation step execution.
+
+    Includes policy context (index, name, type), adapter version, year,
+    and original error for debugging and governance tracking.
+    """
+
+    def __init__(
+        self,
+        message: str,
+        *,
+        year: int,
+        adapter_version: str,
+        policy_index: int,
+        policy_name: str,
+        policy_type: str,
+        original_error: Exception | None = None,
+    ) -> None:
+        self.year = year
+        self.adapter_version = adapter_version
+        self.policy_index = policy_index
+        self.policy_name = policy_name
+        self.policy_type = policy_type
+        self.original_error = original_error
+        super().__init__(message)
+
+
+# ============================================================================
+# Bridge function
+# ============================================================================
+
+
+def _to_computation_policy(
+    policy_config: PortfolioPolicyConfig,
+) -> ComputationPolicyConfig:
+    """Convert a portfolio PolicyConfig to a computation PolicyConfig.
+
+    The portfolio layer uses typed PolicyParameters (frozen dataclass),
+    while the computation layer uses generic dict[str, Any].
+    """
+    from reformlab.computation.types import PolicyConfig as ComputationPolicyConfig
+
+    return ComputationPolicyConfig(
+        policy=asdict(policy_config.policy),
+        name=policy_config.name or policy_config.policy_type.value,
+        description=f"{policy_config.policy_type.value} policy",
+    )
+
+
+# ============================================================================
+# Result merging
+# ============================================================================
+
+
+def _merge_policy_results(
+    results: list[ComputationResult],
+    portfolio: PolicyPortfolio,
+) -> pa.Table:
+    """Merge output tables from multiple policies into a single table.
+
+    Strategy: join all output tables on ``household_id``. The first result
+    keeps column names as-is. Subsequent results prefix columns with

[... Git diff truncated due to size - see full diff with git command ...]

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-06</var>
<var name="description">Master synthesizes code review findings and applies fixes to source code</var>
<var name="document_output_language">English</var>
<var name="epic_num">12</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/code-review-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/code-review-synthesis/instructions.xml</var>
<var name="name">code-review-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" file_id="e58fb4dd" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: e58fb4dd</var>
<var name="project_knowledge">docs</var>
<var name="project_name">reformlab</var>
<var name="reviewer_count">2</var>
<var name="session_id">89942c5f-2094-45f1-815a-de7c26308b79</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="4f02ed14">embedded in prompt, file id: 4f02ed14</var>
<var name="story_id">12.4</var>
<var name="story_key">12-4-extend-scenario-registry-with-portfolio-versioning</var>
<var name="story_num">4</var>
<var name="story_title">extend-scenario-registry-with-portfolio-versioning</var>
<var name="template">False</var>
<var name="timestamp">20260306_1348</var>
<var name="user_name">User</var>
<var name="user_skill_level">expert</var>
<var name="validator_count"></var>
</variables>
<instructions><workflow>
  <critical>Communicate all responses in English and generate all documents in English</critical>
  <critical>You are the MASTER SYNTHESIS agent for CODE REVIEW findings.</critical>
  <critical>You have WRITE PERMISSION to modify SOURCE CODE files and story Dev Agent Record section.</critical>
  <critical>DO NOT modify story context (AC, Dev Notes content) - only Dev Agent Record (task checkboxes, completion notes, file list).</critical>
  <critical>All context (project_context.md, story file, anonymized reviews) is EMBEDDED below - do NOT attempt to read files.</critical>

  <step n="1" goal="Analyze reviewer findings">
    <action>Read all anonymized reviewer outputs (Reviewer A, B, C, D, etc.)</action>
    <action>For each issue raised:
      - Cross-reference with embedded project_context.md and story file
      - Cross-reference with source code snippets provided in reviews
      - Determine if issue is valid or false positive
      - Note reviewer consensus (if 3+ reviewers agree, high confidence issue)
    </action>
    <action>Issues with low reviewer agreement (1-2 reviewers) require extra scrutiny</action>
    <action>Group related findings that address the same underlying problem</action>
  </step>

  <step n="1.5" goal="Review Deep Verify code analysis" conditional="[Deep Verify Findings] section present">
    <critical>Deep Verify analyzed the actual source code files for this story.
      DV findings are based on static analysis patterns and may identify issues reviewers missed.</critical>

    <action>Review each DV finding:
      - CRITICAL findings: Security vulnerabilities, race conditions, resource leaks - must address
      - ERROR findings: Bugs, missing error handling, boundary issues - should address
      - WARNING findings: Code quality concerns - consider addressing
    </action>

    <action>Cross-reference DV findings with reviewer findings:
      - DV + Reviewers agree: High confidence issue, prioritize in fix order
      - Only DV flags: Verify in source code - DV has precise line numbers
      - Only reviewers flag: May be design/logic issues DV can't detect
    </action>

    <action>DV findings may include evidence with:
      - Code quotes (exact text from source)
      - Line numbers (precise location, when available)
      - Pattern IDs (known antipattern reference)
      Use this evidence when applying fixes.</action>

    <action>DV patterns reference:
      - CC-*: Concurrency issues (race conditions, deadlocks)
      - SEC-*: Security vulnerabilities
      - DB-*: Database/storage issues
      - DT-*: Data transformation issues
      - GEN-*: General code quality (null handling, resource cleanup)
    </action>
  </step>

  <step n="2" goal="Verify issues and identify false positives">
    <action>For each issue, verify against embedded code context:
      - Does the issue actually exist in the current code?
      - Is the suggested fix appropriate for the codebase patterns?
      - Would the fix introduce new issues or regressions?
    </action>
    <action>Document false positives with clear reasoning:
      - Why the reviewer was wrong
      - What evidence contradicts the finding
      - Reference specific code or project_context.md patterns
    </action>
  </step>

  <step n="3" goal="Prioritize by severity">
    <action>For verified issues, assign severity:
      - Critical: Security vulnerabilities, data corruption, crashes
      - High: Bugs that break functionality, performance issues
      - Medium: Code quality issues, missing error handling
      - Low: Style issues, minor improvements, documentation
    </action>
    <action>Order fixes by severity - Critical first, then High, Medium, Low</action>
    <action>For disputed issues (reviewers disagree), note for manual resolution</action>
  </step>

  <step n="4" goal="Apply fixes to source code">
    <critical>This is SOURCE CODE modification, not story file modification</critical>
    <critical>Use Edit tool for all code changes - preserve surrounding code</critical>
    <critical>After applying each fix group, run: pytest -q --tb=line --no-header</critical>
    <critical>NEVER proceed to next fix if tests are broken - either revert or adjust</critical>

    <action>For each verified issue (starting with Critical):
      1. Identify the source file(s) from reviewer findings
      2. Apply fix using Edit tool - change ONLY the identified issue
      3. Preserve code style, indentation, and surrounding context
      4. Log the change for synthesis report
    </action>

    <action>After each logical fix group (related changes):
      - Run: pytest -q --tb=line --no-header
      - If tests pass, continue to next fix
      - If tests fail:
        a. Analyze which fix caused the failure
        b. Either revert the problematic fix OR adjust implementation
        c. Run tests again to confirm green state
        d. Log partial fix failure in synthesis report
    </action>

    <action>Atomic commit guidance (for user reference):
      - Commit message format: fix(component): brief description (synthesis-12.4)
      - Group fixes by severity and affected component
      - Never commit unrelated changes together
      - User may batch or split commits as preferred
    </action>
  </step>

  <step n="5" goal="Refactor if needed">
    <critical>Only refactor code directly related to applied fixes</critical>
    <critical>Maximum scope: files already modified in Step 4</critical>

    <action>Review applied fixes for duplication patterns:
      - Same fix applied 2+ times across files = candidate for refactor
      - Only if duplication is in files already modified
    </action>

    <action>If refactoring:
      - Extract common logic to shared function/module
      - Update all call sites in modified files
      - Run tests after refactoring: pytest -q --tb=line --no-header
      - Log refactoring in synthesis report
    </action>

    <action>Do NOT refactor:
      - Unrelated code that "could be improved"
      - Files not touched in Step 4
      - Patterns that work but are just "not ideal"
    </action>

    <action>If broader refactoring needed:
      - Note it in synthesis report as "Suggested future improvement"
      - Do not apply - leave for dedicated refactoring story
    </action>
  </step>

  <step n="6" goal="Generate synthesis report">
    <critical>When updating story file, use atomic write pattern (temp file + rename).</critical>
    <action>Update story file Dev Agent Record section ONLY:
      - Mark completed tasks with [x] if fixes address them
      - Append to "Completion Notes List" subsection summarizing changes applied
      - Update file list with all modified files
    </action>

    <critical>Your synthesis report MUST be wrapped in HTML comment markers for extraction:</critical>
    <action>Produce structured output in this exact format (including the markers):</action>
    <output-format>
&lt;!-- CODE_REVIEW_SYNTHESIS_START --&gt;
## Synthesis Summary
[Brief overview: X issues verified, Y false positives dismissed, Z fixes applied to source files]

## Validations Quality
[For each reviewer: ID (A, B, C...), score (1-10), brief assessment]
[Note: Reviewers are anonymized - do not attempt to identify providers]

## Issues Verified (by severity)

### Critical
[Issues that required immediate fixes - list with evidence and fixes applied]
[Format: "- **Issue**: Description | **Source**: Reviewer(s) | **File**: path | **Fix**: What was changed"]
[If none: "No critical issues identified."]

### High
[Bugs and significant problems - same format]

### Medium
[Code quality issues - same format]

### Low
[Minor improvements - same format, note any deferred items]

## Issues Dismissed
[False positives with reasoning for each dismissal]
[Format: "- **Claimed Issue**: Description | **Raised by**: Reviewer(s) | **Dismissal Reason**: Why this is incorrect"]
[If none: "No false positives identified."]

## Changes Applied
[Complete list of modifications made to source files]
[Format for each change:
  **File**: [path/to/file.py]
  **Change**: [Brief description]
  **Before**:
  ```
  [2-3 lines of original code]
  ```
  **After**:
  ```
  [2-3 lines of updated code]
  ```
]
[If no changes: "No source code changes required."]

## Deep Verify Integration
[If DV findings were present, document how they were handled]

### DV Findings Fixed
[List DV findings that resulted in code changes]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **File**: {path} | **Fix**: {What was changed}"]

### DV Findings Dismissed
[List DV findings determined to be false positives]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Reason**: {Why this is not an issue}"]

### DV-Reviewer Overlap
[Note findings flagged by both DV and reviewers - highest confidence fixes]
[If no DV findings: "Deep Verify did not produce findings for this story."]

## Files Modified
[Simple list of all files that were modified]
- path/to/file1.py
- path/to/file2.py
[If none: "No files modified."]

## Suggested Future Improvements
[Broader refactorings or improvements identified in Step 5 but not applied]
[Format: "- **Scope**: Description | **Rationale**: Why deferred | **Effort**: Estimated complexity"]
[If none: "No future improvements identified."]

## Test Results
[Final test run output summary]
- Tests passed: X
- Tests failed: 0 (required for completion)
&lt;!-- CODE_REVIEW_SYNTHESIS_END --&gt;
    </output-format>

  </step>

  <step n="6.5" goal="Write Senior Developer Review section to story file for dev_story rework detection">
    <critical>This section enables dev_story to detect that a code review has occurred and extract action items.</critical>
    <critical>APPEND this section to the story file - do NOT replace existing content.</critical>

    <action>Determine the evidence verdict from the [Evidence Score] section:
      - REJECT: Evidence score exceeds reject threshold
      - PASS: Evidence score is below accept threshold
      - UNCERTAIN: Evidence score is between thresholds
    </action>

    <action>Map evidence verdict to review outcome:
      - PASS → "Approved"
      - REJECT → "Changes Requested"
      - UNCERTAIN → "Approved with Reservations"
    </action>

    <action>Append to story file "## Senior Developer Review (AI)" section:
      ```
      ## Senior Developer Review (AI)

      ### Review: {current_date}
      - **Reviewer:** AI Code Review Synthesis
      - **Evidence Score:** {evidence_score} → {evidence_verdict}
      - **Issues Found:** {total_verified_issues}
      - **Issues Fixed:** {fixes_applied_count}
      - **Action Items Created:** {remaining_unfixed_count}
      ```
    </action>

    <critical>When evidence verdict is REJECT, you MUST create Review Follow-ups tasks.
      If "Action Items Created" count is &gt; 0, there MUST be exactly that many [ ] [AI-Review] tasks.
      Do NOT skip this step. Do NOT claim all issues are fixed if you reported deferred items above.</critical>

    <action>Find the "## Tasks / Subtasks" section in the story file</action>
    <action>Append a "#### Review Follow-ups (AI)" subsection with checkbox tasks:
      ```
      #### Review Follow-ups (AI)
      - [ ] [AI-Review] {severity}: {brief description of unfixed issue} ({file path})
      ```
      One line per unfixed/deferred issue, prefixed with [AI-Review] tag.
      Order by severity: Critical first, then High, Medium, Low.
    </action>

    <critical>ATDD DEFECT CHECK: Search test directories (tests/**) for test.fixme() calls in test files related to this story.
      If ANY test.fixme() calls remain in story-related test files, this is a DEFECT — the dev_story agent failed to activate ATDD RED-phase tests.
      Create an additional [AI-Review] task:
      - [ ] [AI-Review] HIGH: Activate ATDD tests — convert all test.fixme() to test() and ensure they pass ({test file paths})
      Do NOT dismiss test.fixme() as "intentional TDD methodology". After dev_story completes, ALL test.fixme() tests for the story MUST be converted to test().</critical>
  </step>

  </workflow></instructions>
<output-template></output-template>
</compiled-workflow>