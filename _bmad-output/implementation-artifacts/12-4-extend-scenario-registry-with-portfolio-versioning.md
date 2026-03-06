# Story 12.4: Extend Scenario Registry with Portfolio Versioning

Status: done
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
