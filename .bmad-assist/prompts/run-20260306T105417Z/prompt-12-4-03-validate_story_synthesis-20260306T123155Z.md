<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 12 -->
<!-- Story: 4 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260306T123155Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 12.4

You are synthesizing 2 independent validator reviews.

Your mission:
1. VERIFY each issue raised by validators
   - Cross-reference with story content
   - Identify false positives (issues that aren't real problems)
   - Confirm valid issues with evidence

2. PRIORITIZE real issues by severity
   - Critical: Blocks implementation or causes major problems
   - High: Significant gaps or ambiguities
   - Medium: Improvements that would help
   - Low: Nice-to-have suggestions

3. SYNTHESIZE findings
   - Merge duplicate issues from different validators
   - Note validator consensus (if 3+ agree, high confidence)
   - Highlight unique insights from individual validators

4. APPLY changes to story file
   - You have WRITE PERMISSION to modify the story
   - CRITICAL: Before using Edit tool, ALWAYS Read the target file first
   - Use EXACT content from Read tool output as old_string, NOT content from this prompt
   - If Read output is truncated, use offset/limit parameters to locate the target section
   - Apply fixes for verified issues
   - Document what you changed and why

Output format:
## Synthesis Summary
## Issues Verified (by severity)
## Issues Dismissed (false positives with reasoning)
## Changes Applied

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
Given an invalid portfolio name (empty, path traversal), when `save()` is called, then a `RegistryError` is raised with actionable fields (`summary`, `reason`, `fix`). Given a non-existent portfolio name or version ID, when `get()` is called, then `ScenarioNotFoundError` or `VersionNotFoundError` is raised with available alternatives listed.

## Tasks / Subtasks

### Task 1: Add portfolio serialization support to registry (AC: 1, 4, 5)

- [ ] 1.1 Create `_portfolio_to_dict_for_registry(portfolio: PolicyPortfolio) -> dict[str, Any]` in `registry.py`. Use existing `portfolio_to_dict()` from `portfolios.composition` as the base, but add a `"_registry_type": "portfolio"` marker field to distinguish from scenarios in the metadata/version YAML files
- [ ] 1.2 Create `_generate_portfolio_version_id(portfolio: PolicyPortfolio) -> str` using SHA-256 of `yaml.dump(content, sort_keys=True)` with 12-char hex prefix — same pattern as `_generate_version_id()` for scenarios
- [ ] 1.3 Create `_dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio` to reconstruct a `PolicyPortfolio` from registry YAML dict. Reuse `dict_to_portfolio()` from `portfolios.composition` after stripping the `_registry_type` marker

### Task 2: Extend `ScenarioRegistry.save()` to accept portfolios (AC: 1, 2, 4)

- [ ] 2.1 Widen `save()` signature to accept `BaselineScenario | ReformScenario | PolicyPortfolio`
- [ ] 2.2 Detect portfolio type with `isinstance(scenario, PolicyPortfolio)` and route to portfolio-specific version ID generation and serialization
- [ ] 2.3 Store portfolio YAML version files in the same directory structure: `{registry_path}/{name}/versions/{version_id}.yaml`
- [ ] 2.4 Store a `"_registry_type": "portfolio"` field in `metadata.yaml` to distinguish from scenarios. Default to `"scenario"` for backward compat when the field is absent
- [ ] 2.5 Portfolio save follows identical metadata update pattern: parent_version tracking, timestamp, change_description
- [ ] 2.6 Idempotent save: if content-addressable version ID already exists with identical content, return existing version ID without creating a new entry

### Task 3: Extend `ScenarioRegistry.get()` to return portfolios (AC: 1, 5)

- [ ] 3.1 Widen `get()` return type to `BaselineScenario | ReformScenario | PolicyPortfolio`
- [ ] 3.2 Check `_registry_type` in metadata to determine whether to call `_dict_to_scenario()` or `_dict_to_portfolio()` for deserialization
- [ ] 3.3 Portfolio integrity check: regenerate version ID from loaded content and compare to file name (same pattern as `_ensure_version_integrity()` for scenarios)

### Task 4: Add type-distinguishable listing (AC: 3)

- [ ] 4.1 Add `get_entry_type(name: str) -> str` method returning `"baseline"`, `"reform"`, or `"portfolio"` by reading `_registry_type` from metadata.yaml (defaulting to examining version content for legacy entries without the marker)
- [ ] 4.2 Update `RegistryEntry` to include an `entry_type: str` field (default `"scenario"` for backward compat). Use `"portfolio"` for portfolios, `"baseline"` or `"reform"` for scenarios
- [ ] 4.3 Update `get_entry()` to populate the new `entry_type` field from metadata
- [ ] 4.4 Add `list_portfolios() -> list[str]` convenience method that filters `list_scenarios()` by `_registry_type == "portfolio"`
- [ ] 4.5 Keep `list_scenarios()` returning ALL entries (both scenarios and portfolios) for backward compatibility. Document that it returns all registry entries regardless of type

### Task 5: Extend supporting methods for portfolios (AC: 6, 7)

- [ ] 5.1 `list_versions(name)` — works for portfolios unchanged (metadata structure is identical)
- [ ] 5.2 `exists(name, version_id)` — works for portfolios unchanged
- [ ] 5.3 `clone(name, version_id, new_name)` — extend to support portfolios: detect type, call `replace(portfolio, name=clone_name)` for `PolicyPortfolio`
- [ ] 5.4 `set_validated()` / `is_validated()` — work for portfolios unchanged (metadata-level operations)
- [ ] 5.5 `_ensure_version_integrity()` — create portfolio-aware variant that uses `_generate_portfolio_version_id()` for content hash verification

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
- [ ] 8.7 **TestPortfolioRegistryErrors** (AC7): Invalid name raises `RegistryError`. Non-existent portfolio raises `ScenarioNotFoundError`. Non-existent version raises `VersionNotFoundError`
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

**Chosen: Option B** — `_registry_type` stored in `metadata.yaml` with values `"scenario"` or `"portfolio"`. This is set once when the first version is saved and checked on every `get()`. Backward compatibility: entries without `_registry_type` default to `"scenario"`.

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

Portfolio version ID generation MUST use the same pattern: convert to dict, `yaml.dump(content, sort_keys=True)`, SHA-256, 12-char prefix. The dict MUST include `_registry_type: "portfolio"` to ensure portfolio and scenario version IDs never collide even if content is superficially similar.

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
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

<!-- report_header -->

**Story:** 12.4 - extend-scenario-registry-with-portfolio-versioning
**Story File:** _bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md
**Validated:** 2026-03-06
**Validator:** Quality Competition Engine

---

<!-- executive_summary -->

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 0 | 0 |
| ⚡ Enhancements | 0 | 0 |
| ✨ Optimizations | 0 | 0 |
| 🤖 LLM Optimizations | 2 | 0 |

**Overall Assessment:** The story is exceptionally well-structured, comprehensive, and detailed. It demonstrates a deep understanding of existing project patterns and maintains strict backward compatibility. Minor LLM optimization opportunities were identified for token efficiency and instruction clarity, but these do not detract from the high quality of the story's content.

---

<!-- evidence_score_summary -->

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🟡 MINOR | Redundant Source Citations in Dev Notes | LLM Optimization Analysis | +0.3 |
| 🟡 MINOR | Elevate crucial `_registry_type` storage detail | LLM Optimization Analysis | +0.3 |
| 🟢 CLEAN PASS | 11 | | -5.5 |

### Evidence Score: -4.9

| Score | Verdict |
|-------|---------|
| **-4.9** | **EXCELLENT** |

---

<!-- story_quality_gate -->

## 🎯 Ruthless Story Validation 12.4

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | Pass | 0/10 | Explicit dependencies on 12.1 and 12.2 are stated. Assuming these are complete, the story is independent. |
| **N**egotiable | Pass | 0/10 | While prescriptive in parts, this is necessary to maintain consistency with existing registry patterns and ensure backward compatibility. It focuses on the 'what' and 'how' for integration into an established system. |
| **V**aluable | Pass | 0/10 | Clear business value in managing and tracking policy portfolios for policy analysts, aligning with the project's Phase 2 goals. |
| **E**stimable | Pass | 0/10 | Detailed tasks and references to existing patterns make the story estimable. |
| **S**mall | Pass | 0/10 | The scope of modifying an existing class with new serialization/deserialization logic, several method updates, and comprehensive testing seems appropriately sized for a sprint. |
| **T**estable | Pass | 0/10 | Acceptance criteria are specific, measurable, and cover various scenarios including error handling and versioning. |

### INVEST Violations

✅ No significant INVEST violations detected.

### Acceptance Criteria Issues

✅ Acceptance criteria are well-defined and testable.

### Hidden Risks and Dependencies

✅ No hidden dependencies or blockers identified.

### Estimation Reality-Check

**Assessment:** Realistic

The story's detailed breakdown, clear task descriptions, and explicit references to existing patterns and code provide a solid foundation for accurate estimation.

### Technical Alignment

**Status:** Strong Alignment

✅ Story aligns with architecture.md patterns.

### Evidence Score: -4.9 → EXCELLENT

---

<!-- critical_issues_section -->

## 🚨 Critical Issues (Must Fix)

These are essential requirements, security concerns, or blocking issues that could cause implementation disasters.

✅ No critical issues found - the original story covered essential requirements.

---

<!-- enhancements_section -->

## ⚡ Enhancement Opportunities (Should Add)

Additional guidance that would significantly help the developer avoid mistakes.

✅ No significant enhancement opportunities identified.

---

<!-- optimizations_section -->

## ✨ Optimizations (Nice to Have)

Performance hints, development tips, and additional context for complex scenarios.

✅ No additional optimizations identified.

---

<!-- llm_optimizations_section -->

## 🤖 LLM Optimization Improvements

Token efficiency and clarity improvements for better dev agent processing.

### 1. Redundant Source Citations in Dev Notes

**Issue:** Mild redundancy in source citations within the "Dev Notes" section.
**Token Impact:** Low to Medium.

**Current:**
```
**Existing ScenarioRegistry API** [Source: src/reformlab/templates/registry.py]
...
**Version ID generation pattern** [Source: src/reformlab/templates/registry.py:231-246]
... (many more similar repetitions)
```

**Optimized:**
```
(Suggestion for a global declaration at the start of Dev Notes):
"Unless otherwise specified, all `registry` references below pertain to `src/reformlab/templates/registry.py`."
(Then, subsequent references could be shorter, e.g., "Existing ScenarioRegistry API" or "Version ID generation pattern (lines 231-246)").
```

**Rationale:** While precise, repeated full path citations can slightly increase token usage. A global declaration could maintain clarity with fewer tokens, especially if the LLM is already grounded in the main context files.

### 2. Elevate crucial `_registry_type` storage detail

**Issue:** Important instruction regarding the storage of `_registry_type` in both `metadata.yaml` and each version YAML file is embedded within a paragraph in "Dev Notes" rather than being an explicit task or sub-task.
**Token Impact:** Low, primarily structural clarity.

**Current:**
```
(Within "Design: _registry_type` marker" in Dev Notes)
"The `_registry_type` marker is ALSO stored in each version YAML file (as part of the serialized dict) to enable standalone version file identification without requiring metadata.yaml lookup."
```

**Optimized:**
```
(As a new sub-task within Task 1, or explicitly reiterated in Task 6.3):
"1.1.1 Ensure `_registry_type: "portfolio"` is included in the serialized dictionary for each version YAML file, in addition to `metadata.yaml`."
```

**Rationale:** Elevating this instruction to a specific task ensures it's not overlooked, as it's critical for standalone version file identification. This improves the LLM agent's direct actionability.

---

<!-- changes_applied_section -->

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

<!-- competition_results -->

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 100% |
| Architecture Alignment | 100% |
| Previous Story Integration | 100% |
| LLM Optimization Score | 90% |
| **Overall Quality Score** | **98%** |

### Disaster Prevention Assessment

-   **Reinvention Prevention:** No significant risks identified. The story effectively leverages existing code and patterns.
-   **Technical Specification:** No significant risks identified. Specifications are robust and consistent with project standards.
-   **File Structure:** No significant risks identified. Adheres to defined file and naming conventions.
-   **Regression:** No significant risks identified. Strong emphasis on backward compatibility and comprehensive testing reduces regression potential.
-   **Implementation:** No significant risks identified. Detailed tasks, clear scope boundaries, and specific ACs prevent vague or incorrect implementations.

### Competition Outcome

✅ **Original create-story produced high-quality output** with minimal gaps identified.

---

**Report Generated:** 2026-03-06
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 12-4-extend-scenario-registry-with-portfolio-versioning - extend-scenario-registry-with-portfolio-versioning  
**Story File:** _bmad-output/implementation-artifacts/12-4-extend-scenario-registry-with-portfolio-versioning.md  
**Validated:** 2026-03-06  
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 4 | 0 |
| ⚡ Enhancements | 7 | 0 |
| ✨ Optimizations | 3 | 0 |
| 🤖 LLM Optimizations | 4 | 0 |

**Overall Assessment:** REJECT — the story is directionally strong but has critical design contradictions and determinism/regression gaps that can cause incorrect implementation and backward-compatibility breakage.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Type-discrimination model is contradictory (`_registry_type: scenario/portfolio` vs required `baseline/reform/portfolio`) | Story Tasks 2.4, 4.1, 4.2 | +3 |
| 🔴 CRITICAL | No guard against mixed artifact types under same registry name (scenario then portfolio) | Missing requirement in Tasks 2/3 + current `ScenarioRegistry.save()` behavior | +3 |
| 🔴 CRITICAL | Version hash determinism risk via machine-specific `$schema` path from `portfolio_to_dict()` | Task 1.1 + `portfolios/composition.py` | +3 |
| 🔴 CRITICAL | Regression safety not specified for `migrate()`, `get_baseline()`, `list_reforms()` with portfolio entries | Current `registry.py` API surface vs story scope | +3 |
| 🟠 IMPORTANT | AC1 and AC5 overlap heavily, reducing test signal and estimation clarity | AC section | +1 |
| 🟠 IMPORTANT | Legacy-entry type inference is under-specified and can diverge across implementations | Task 4.1 | +1 |
| 🟠 IMPORTANT | No explicit rule for metadata/version-file type-marker mismatch handling | Tasks 2/3/6 | +1 |
| 🟠 IMPORTANT | Scope likely underestimated for a 5-point story given API + compatibility + regression matrix | Epic estimate vs task breadth | +1 |
| 🟠 IMPORTANT | Over-prescriptive method-renaming tasks add churn with limited user value | Task 6 | +1 |
| 🟡 MINOR | Reference anchors include brittle file-length/line assumptions | Dev Notes references | +0.3 |
| 🟡 MINOR | Story contains repetitive guidance that dilutes critical requirements | Dev Notes repetition | +0.3 |
| 🟢 CLEAN PASS | Valuable business outcome is explicit and aligned with FR43 | INVEST-V | -0.5 |

### Evidence Score: 16.1

| Score | Verdict |
|-------|---------|
| **16.1** | **REJECT** |

---

## 🎯 Ruthless Story Validation 12.4

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | PARTIAL FAIL | 7/10 | Hidden coupling to existing registry methods (`migrate`, baseline/reform helpers) is not specified. |
| **N**egotiable | PARTIAL FAIL | 6/10 | Story is overly prescriptive in method names/renames instead of outcomes. |
| **V**aluable | PASS | 1/10 | Clear analyst value and direct alignment with FR43. |
| **E**stimable | FAIL | 8/10 | Type-model contradictions and missing compatibility contracts make effort unpredictable. |
| **S**mall | FAIL | 7/10 | Scope spans core API, serialization, lineage, compatibility, and regression hardening. |
| **T**estable | PARTIAL FAIL | 6/10 | Core tests are listed, but key edge/regression behaviors are missing from ACs. |

### INVEST Violations

- **[7/10] Independent:** Story omits required behavior for existing registry methods when portfolio types are introduced.
- **[6/10] Negotiable:** Private method renaming/generalization is mandated where behavioral outcomes would suffice.
- **[8/10] Estimable:** Contradictory type markers create multiple implementation paths with different risk.
- **[7/10] Small:** Combined API expansion + backward compatibility + integrity + tests is larger than one focused story.
- **[6/10] Testable:** Missing acceptance criteria for mixed-type name collisions and marker inconsistency handling.

### Acceptance Criteria Issues

- **Conflicting specification:** AC3 requires distinction among `BaselineScenario`, `ReformScenario`, `PolicyPortfolio`, but tasking stores `_registry_type` as only `"scenario"` or `"portfolio"`.  
Quote: “Store a `"_registry_type": "portfolio"`... Default to `"scenario"`...” and “returning `"baseline"`, `"reform"`, or `"portfolio"`...”  
Recommendation: define a single canonical type model (`baseline|reform|portfolio`) and require it consistently in metadata + version files.

- **Redundant criteria:** AC1 and AC5 both assert full round-trip equality.  
Quote: AC1 “returned portfolio is identical...” and AC5 “all fields are identical... equality holds.”  
Recommendation: merge or differentiate (e.g., AC1 retrieval by explicit version ID; AC5 fidelity across legacy/marker migration path).

- **Incomplete determinism criterion:** AC4 does not constrain non-semantic/environmental fields in hash input.  
Quote: “same content always produces the same 12-character hex ID.”  
Recommendation: explicitly exclude or normalize `$schema` and other environment-dependent fields before hashing.

- **Error-handling gap:** AC7 covers missing names/versions but not corrupted type metadata or type conflicts.  
Quote: AC7 only mentions invalid name and non-existent IDs.  
Recommendation: add AC for marker mismatch, mixed-type entry rejection, and integrity failure messaging.

- **Lineage ambiguity:** AC6 defines chronological history but does not require lineage correctness under idempotent re-save and cross-type saves.  
Recommendation: add explicit expected `parent_version` behavior for idempotent save and rejected-type-change cases.

### Hidden Risks and Dependencies

- **API regression dependency:** Existing methods (`migrate`, `get_baseline`, `list_reforms`) assume scenario-only semantics.  
Impact: runtime/type regressions after widening `get()` and `save()`.  
Mitigation: define explicit portfolio behavior (unsupported with structured error, or supported path) and add regression tests.

- **Serialization dependency:** `portfolio_to_dict()` currently emits filesystem-based `$schema` path.  
Impact: cross-machine hash drift and false version churn.  
Mitigation: normalize to stable schema identifier before hash generation.

- **Legacy metadata dependency:** Existing entries lack `_registry_type`.  
Impact: inconsistent type inference if logic is not deterministic and documented.  
Mitigation: define deterministic inference order and test fixtures for legacy scenarios.

- **Name collision dependency:** Registry key currently accepts any artifact per name without type lock.  
Impact: mixed-type lineage corruption.  
Mitigation: enforce immutable entry type per registry name and raise `RegistryError` on mismatch.

### Estimation Reality-Check

**Assessment:** underestimated

Current scope combines artifact-type model redesign, save/get/integrity plumbing, metadata evolution, backward compatibility, and new test suite plus regression coverage. This is likely larger than a single 5-point story unless split into: (1) core portfolio persistence and (2) compatibility/regression hardening.

### Technical Alignment

**Status:** PARTIAL MISALIGNMENT

- **Determinism conflict:** Story does not protect content hash from environment-specific serialization fields.  
Architecture Reference: `project-context.md` critical rule “Determinism is non-negotiable.”  
Recommendation: define canonical hash payload contract explicitly.

- **Registry immutability risk:** Mixed-type saves under one entry name are not prohibited.  
Architecture Reference: `docs/architecture.md` registry immutability/content-addressability principles.  
Recommendation: enforce immutable entry type and lineage invariants.

- **Backward compatibility gap:** Existing registry API methods are not fully accounted for in scope/tests.  
Architecture Reference: layered architecture and stable interfaces in templates registry.  
Recommendation: add explicit “no regression” AC covering existing scenario-only workflows.

### Evidence Score: 16.1 → REJECT

---

## 🚨 Critical Issues (Must Fix)

### 1. Contradictory Entry-Type Model

**Impact:** AC3 may be implemented incorrectly, producing unreliable type discrimination.  
**Source:** AC3, Task 2.4, Task 4.1, Task 4.2

**Problem:** Story mixes two incompatible representations: metadata marker values (`scenario|portfolio`) and API requirement values (`baseline|reform|portfolio`).

**Recommended Fix:** Define one canonical stored type model and one API projection model, with explicit mapping rules and backward-compat fallback.

### 2. Missing Type-Consistency Invariant per Registry Name

**Impact:** A single registry key can accumulate heterogeneous artifacts, corrupting lineage and retrieval semantics.  
**Source:** Save/get tasks + existing `ScenarioRegistry.save()` behavior

**Problem:** No requirement states whether saving a portfolio under an existing scenario key is allowed or rejected.

**Recommended Fix:** Add a must-fail rule: once an entry type is established, subsequent saves with a different type raise `RegistryError` with actionable fix.

### 3. Deterministic Version ID Contract Is Underspecified

**Impact:** Same logical portfolio can hash differently across machines/environments.  
**Source:** Task 1.1 + current `portfolio_to_dict()` behavior

**Problem:** Reusing `portfolio_to_dict()` directly can include machine-dependent `$schema` path in hash payload.

**Recommended Fix:** Canonicalize hash input (stable field set, stable schema identifier, normalized key ordering) and test cross-path determinism.

### 4. Regression Contract Missing for Existing Registry APIs

**Impact:** Introducing portfolio types can break scenario-focused methods at runtime.  
**Source:** Story scope vs existing methods `migrate`, `get_baseline`, `list_reforms`

**Problem:** Story does not define expected behavior for these methods when called on portfolio entries.

**Recommended Fix:** Add explicit ACs and tests for portfolio interaction with these methods (supported behavior or structured rejection).

---

## ⚡ Enhancement Opportunities (Should Add)

### 5. Add Marker-Consistency Rules

**Benefit:** Prevent silent corruption and debugging ambiguity.  
**Source:** Tasks 2/3/6

**Current Gap:** No rule for metadata `_registry_type` disagreeing with version file marker.

**Suggested Addition:** Require `RegistryError` on mismatch, with remediation message pointing to repair/recreate metadata.

### 6. Clarify Legacy Inference Algorithm

**Benefit:** Deterministic migration path for existing registries.  
**Source:** Task 4.1

**Current Gap:** “examine version content” is vague.

**Suggested Addition:** Specify exact fields and precedence used to infer baseline vs reform for legacy entries.

### 7. Expand AC7 for Corruption Cases

**Benefit:** Better operability under real-world failures.  
**Source:** AC7

**Current Gap:** Corrupted metadata/version structures are unaddressed.

**Suggested Addition:** Add errors for malformed metadata, missing latest version, and invalid type marker values.

### 8. Add No-Regression AC for Existing Scenario Workflows

**Benefit:** Protect current users from portfolio-related changes.  
**Source:** Existing `tests/templates/test_registry.py`

**Current Gap:** No explicit acceptance criterion for preserving scenario behavior.

**Suggested Addition:** Add AC and task line requiring all existing registry tests to pass unchanged.

### 9. Define Clone Semantics More Precisely

**Benefit:** Avoid confusion between registry key and object `name`.  
**Source:** Task 5.3

**Current Gap:** Clone task mentions replacing `name` but not key/object-name interplay.

**Suggested Addition:** Document expected behavior for object `name` vs `save(name=...)` key in clone workflows.

### 10. Tighten AC6 Timestamp Contract

**Benefit:** Stronger lineage reliability.  
**Source:** AC6

**Current Gap:** UTC is stated but monotonic ordering and timezone-aware parsing are implicit.

**Suggested Addition:** Require timezone-aware timestamps and deterministic chronological sorting behavior on load.

### 11. Add Compatibility Note for Public API Typing

**Benefit:** Safer developer experience in strict mypy mode.  
**Source:** Task 2.1 / 3.1

**Current Gap:** Return type widening implications for callers are not documented.

**Suggested Addition:** Define type aliases/overloads (or dedicated getters) to avoid widespread `isinstance` churn.

---

## ✨ Optimizations (Nice to Have)

### 12. Reduce Refactor Churn in Task 6

**Value:** Faster delivery with lower risk.  
**Suggestion:** Prefer minimal internal changes (wrapper dispatch) over renaming private methods unless required by acceptance behavior.

### 13. Split Into Two Stories

**Value:** Better estimation and clearer done criteria.  
**Suggestion:** Story A for core portfolio save/get/versioning; Story B for backward compatibility hardening and legacy inference.

### 14. Replace Brittle Line-Number References

**Value:** More durable implementation guidance.  
**Suggestion:** Reference symbols/functions rather than approximate file lengths and line ranges.

---

## 🤖 LLM Optimization Improvements

### 15. Unify Type Model Language

**Issue:** Ambiguity  
**Token Impact:** High

**Current:**
```text
Store "_registry_type": "portfolio" (default "scenario")...
get_entry_type returns "baseline", "reform", or "portfolio"...
```

**Optimized:**
```text
Canonical stored type = one of {"baseline","reform","portfolio"} for all new entries.
Legacy entries without marker: infer once from latest version content, persist inferred type to metadata.
```

**Rationale:** Eliminates contradictory interpretation paths.

### 16. Collapse Duplicate Fidelity Criteria

**Issue:** Redundancy  
**Token Impact:** Medium

**Current:**
```text
AC1: retrieved portfolio is identical...
AC5: all fields are identical, equality holds...
```

**Optimized:**
```text
Single AC: Retrieval by explicit version ID preserves full dataclass equality for all portfolio fields.
```

**Rationale:** Improves estimation and test mapping.

### 17. Convert Task 6 to Outcome-Based Requirement

**Issue:** Over-prescriptive implementation detail  
**Token Impact:** Medium

**Current:**
```text
Rename/generalize _save_scenario_file and _load_scenario_file...
```

**Optimized:**
```text
Registry file IO supports both scenarios and portfolios with atomic writes and deterministic deserialization dispatch.
```

**Rationale:** Keeps flexibility while preserving correctness.

### 18. Promote Critical Edge Cases into ACs

**Issue:** Critical behavior buried in tasks/notes  
**Token Impact:** Medium

**Current:**
```text
Mixed concerns scattered across tasks and dev notes.
```

**Optimized:**
```text
AC: Saving an artifact type different from existing entry type must fail with RegistryError.
AC: Metadata/type-marker mismatch must fail with integrity error.
AC: Version hash excludes environment-dependent fields.
```

**Rationale:** Makes blockers visible and testable at story gate.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 74% |
| Architecture Alignment | 68% |
| Previous Story Integration | 71% |
| LLM Optimization Score | 62% |
| **Overall Quality Score** | **69%** |

### Disaster Prevention Assessment

- **Reinvention Prevention:** PARTIAL PASS — reuse intent is present, but type model ambiguity can force ad-hoc rewrites.
- **Technical Specification Disasters:** FAIL — determinism and type invariants are insufficiently specified.
- **File Structure Disasters:** PASS — file targets are mostly correct and aligned with current module layout.
- **Regression Disasters:** FAIL — existing registry method compatibility is under-defined.
- **Implementation Disasters:** FAIL — contradictions can permit “passing” implementation that violates AC3/AC4 intent.

### Competition Outcome

🏆 **Validator identified 18 improvements** that materially increase implementation safety, determinism, and backward compatibility.

---

**Report Generated:** 2026-03-06  
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-06</var>
<var name="description">Master synthesizes validator findings and applies changes to story file</var>
<var name="document_output_language">English</var>
<var name="epic_num">12</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/validate-story-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/validate-story-synthesis/instructions.xml</var>
<var name="name">validate-story-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" file_id="e58fb4dd" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: e58fb4dd</var>
<var name="project_knowledge">docs</var>
<var name="project_name">reformlab</var>
<var name="session_id">83e2a066-a821-4e37-94b1-c3b97e052763</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="4f02ed14">embedded in prompt, file id: 4f02ed14</var>
<var name="story_id">12.4</var>
<var name="story_key">12-4-extend-scenario-registry-with-portfolio-versioning</var>
<var name="story_num">4</var>
<var name="story_title">extend-scenario-registry-with-portfolio-versioning</var>
<var name="template">False</var>
<var name="timestamp">20260306_1331</var>
<var name="user_name">User</var>
<var name="user_skill_level">expert</var>
<var name="validator_count">2</var>
</variables>
<instructions><workflow>
  <critical>Communicate all responses in English and generate all documents in English</critical>

  <critical>You are the MASTER SYNTHESIS agent. Your role is to evaluate validator findings
    and produce a definitive synthesis with applied fixes.</critical>
  <critical>You have WRITE PERMISSION to modify the story file being validated.</critical>
  <critical>All context (project_context.md, story file, anonymized validations) is EMBEDDED below - do NOT attempt to read files.</critical>
  <critical>Apply changes to story file directly using atomic write pattern (temp file + rename).</critical>

  <step n="1" goal="Analyze validator findings">
    <action>Read all anonymized validator outputs (Validator A, B, C, D, etc.)</action>
    <action>For each issue raised:
      - Cross-reference with story content and project_context.md
      - Determine if issue is valid or false positive
      - Note validator consensus (if 3+ validators agree, high confidence issue)
    </action>
    <action>Issues with low validator agreement (1-2 validators) require extra scrutiny</action>
  </step>

  <step n="1.5" goal="Review Deep Verify technical findings" conditional="[Deep Verify Findings] section present">
    <critical>Deep Verify provides automated technical analysis that complements validator reviews.
      DV findings focus on: patterns, boundary cases, assumptions, temporal issues, security, and worst-case scenarios.</critical>

    <action>Review each DV finding:
      - CRITICAL findings: Must be addressed - these indicate serious technical issues
      - ERROR findings: Should be addressed unless clearly false positive
      - WARNING findings: Consider addressing, document if dismissed
    </action>

    <action>Cross-reference DV findings with validator findings:
      - If validators AND DV flag same issue: High confidence, prioritize fix
      - If only DV flags issue: Verify technically valid, may be edge case validators missed
      - If only validators flag issue: Normal processing per step 1
    </action>

    <action>For each DV finding, determine:
      - Is this a genuine issue in the story specification?
      - Does the story need to address this edge case/scenario?
      - Is this already covered but DV missed it? (false positive)
    </action>

    <action>DV findings with patterns (CC-*, SEC-*, DB-*, DT-*, GEN-*) reference known antipatterns.
      Treat pattern-matched findings as higher confidence.</action>
  </step>

  <step n="2" goal="Verify and prioritize issues">
    <action>For verified issues, assign severity:
      - Critical: Blocks implementation or causes major problems
      - High: Significant gaps or ambiguities that need attention
      - Medium: Improvements that would help quality
      - Low: Nice-to-have suggestions
    </action>
    <action>Document false positives with clear reasoning for dismissal:
      - Why the validator was wrong
      - What evidence contradicts the finding
      - Reference specific story content or project_context.md
    </action>
  </step>

  <step n="3" goal="Apply changes to story file">
    <action>For each verified issue (starting with Critical, then High), apply fix directly to story file</action>
    <action>Changes should be natural improvements:
      - DO NOT add review metadata or synthesis comments to story
      - DO NOT reference the synthesis or validation process
      - Preserve story structure, formatting, and style
      - Make changes look like they were always there
    </action>
    <action>For each change, log in synthesis output:
      - File path modified
      - Section/line reference (e.g., "AC4", "Task 2.3")
      - Brief description of change
      - Before snippet (2-3 lines context)
      - After snippet (2-3 lines context)
    </action>
    <action>Use atomic write pattern for story modifications to prevent corruption</action>
  </step>

  <step n="4" goal="Generate synthesis report">
    <critical>Your synthesis report MUST be wrapped in HTML comment markers for extraction:</critical>
    <action>Produce structured output in this exact format (including the markers):</action>
    <output-format>
&lt;!-- VALIDATION_SYNTHESIS_START --&gt;
## Synthesis Summary
[Brief overview: X issues verified, Y false positives dismissed, Z changes applied to story file]

## Validations Quality
[For each validator: name, score, comments]
[Summary of validation quality - 1-10 scale]

## Issues Verified (by severity)

### Critical
[Issues that block implementation - list with evidence and fixes applied]
[Format: "- **Issue**: Description | **Source**: Validator(s) | **Fix**: What was changed"]

### High
[Significant gaps requiring attention]

### Medium
[Quality improvements]

### Low
[Nice-to-have suggestions - may be deferred]

## Issues Dismissed
[False positives with reasoning for each dismissal]
[Format: "- **Claimed Issue**: Description | **Raised by**: Validator(s) | **Dismissal Reason**: Why this is incorrect"]

## Deep Verify Integration
[If DV findings were present, document how they were handled]

### DV Findings Addressed
[List DV findings that resulted in story changes]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Action**: {What was changed}"]

### DV Findings Dismissed
[List DV findings determined to be false positives or not applicable]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Reason**: {Why dismissed}"]

### DV-Validator Overlap
[Note any findings flagged by both DV and validators - these are high confidence]
[If no DV findings: "Deep Verify did not produce findings for this story."]

## Changes Applied
[Complete list of modifications made to story file]
[Format for each change:
  **Location**: [File path] - [Section/line]
  **Change**: [Brief description]
  **Before**:
  ```
  [2-3 lines of original content]
  ```
  **After**:
  ```
  [2-3 lines of updated content]
  ```
]
&lt;!-- VALIDATION_SYNTHESIS_END --&gt;
    </output-format>

  </step>

  <step n="5" goal="Final verification">
    <action>Verify all Critical and High issues have been addressed</action>
    <action>Confirm story file changes are coherent and preserve structure</action>
    <action>Ensure synthesis report is complete with all sections populated</action>
  </step>
</workflow></instructions>
<output-template></output-template>
</compiled-workflow>