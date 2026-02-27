# Story 6.1: Implement Stable Python API

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **researcher or policy analyst using Python/Jupyter**,
I want **a stable, documented Python API that exposes run orchestration, scenario management, and result access**,
so that **I can run complete analysis workflows programmatically without depending on internal implementation details**.

## Acceptance Criteria

From backlog (BKL-601), aligned with FR30 (Python API for run orchestration) and NFR16 (sensible `__repr__` for notebook display).

1. **AC-1: API supports full run lifecycle**
   - Given a scenario configuration (YAML path or dict), when `run_scenario(config, ...)` is called, then a complete orchestration cycle executes and returns results.
   - The API handles: scenario loading, population data loading, orchestrator configuration, multi-year execution, and result packaging.
   - Invalid configurations raise clear errors before execution begins.

2. **AC-2: Scenario creation and management via API**
   - Given the Python API, when a user calls `create_scenario(..., name=..., register=True)`, then a scenario object is created and optionally saved in the registry.
   - Given a registered scenario, when `clone_scenario(name, version_id=None, new_name=...)` is called, then a new scenario object is created from the original using registry semantics.
   - Baseline and reform scenarios can be linked for comparison workflows.

3. **AC-3: Result access with notebook-friendly display**
   - Given a completed run, when `SimulationResult` is displayed in Jupyter, then a sensible `__repr__` shows run summary (years, scenarios, key indicators).
   - Result objects provide accessor methods: `.yearly_states`, `.panel_output`, `.manifest`, `.indicators(...)`.
   - CSV/Parquet export actions are explicitly deferred to Story 6-5 (BKL-605) to keep this story focused on stable run orchestration API.

4. **AC-4: Clear error messages for invalid configurations**
   - Given an invalid scenario configuration (missing required fields, invalid parameter values), when passed to the API, then a clear `ConfigurationError` is raised identifying the exact issue.
   - Errors include: field path, expected type/value, actual value.
   - No raw exceptions or tracebacks leak to API users.

5. **AC-5: API objects integrate with existing subsystems**
   - The API layer delegates to existing subsystems: `templates/` for scenario loading, `orchestrator/` for execution, `governance/` for manifest capture, `indicators/` for analysis.
   - No duplication of existing logic in the API layer.
   - API is a thin facade over existing capabilities.

6. **AC-6: Public API exported from package root**
   - `from reformlab import run_scenario, create_scenario, clone_scenario, SimulationResult` works.
   - `reformlab.__all__` lists all public API symbols.
   - Internal modules remain importable but are clearly documented as internal.

## Dependencies

- **Backlog-declared blockers for BKL-601 (all DONE per sprint-status.yaml checked 2026-02-27):**
  - Story 3-1 (BKL-301): Yearly loop orchestrator foundation
  - Story 4-5 (BKL-405): Scenario comparison tables
  - Story 5-1 (BKL-501): Run manifest schema

- **Additional implementation dependencies (DONE):**
  - Story 2-7 (BKL-207): YAML/JSON workflow configuration with schema validation
  - Story 3-7 (BKL-307): Panel output dataset

- **Status note:**
  - EPIC-5 is currently `in-progress` overall because Story 5-6 is `ready-for-dev`; this is non-blocking for Story 6-1.

- **Follow-on stories:**
  - Story 6-2 (BKL-602): Quickstart notebook using this API
  - Story 6-3 (BKL-603): Advanced notebook using this API
  - Story 6-4b (BKL-604b): FastAPI backend wrapping this API

## Tasks / Subtasks

- [ ] Task 0: Review existing interfaces and identify reusable components (AC: dependency check)
  - [ ] 0.1 Review `templates/workflow.py` for `WorkflowConfig`, `WorkflowResult` patterns
  - [ ] 0.2 Review `templates/registry.py` for scenario registration patterns
  - [ ] 0.3 Review `orchestrator/runner.py` for `OrchestratorRunner.run()` contract
  - [ ] 0.4 Review `orchestrator/panel.py` for `PanelOutput` structure
  - [ ] 0.5 Review `governance/manifest.py` for `RunManifest` structure
  - [ ] 0.6 Review `indicators/__init__.py` for indicator computation patterns
  - [ ] 0.7 Confirm blocker dependencies for BKL-601 are DONE and record non-blocking upstream stories still in progress

- [ ] Task 1: Create SimulationResult dataclass (AC: #3)
  - [ ] 1.1 Create `src/reformlab/interfaces/api.py`
  - [ ] 1.2 Define `SimulationResult` frozen dataclass with fields:
        - `success: bool`
        - `scenario_id: str`
        - `yearly_states: dict[int, YearState]`
        - `panel_output: PanelOutput | None`
        - `manifest: RunManifest`
        - `metadata: dict[str, Any]`
  - [ ] 1.3 Implement `__repr__()` for notebook display showing:
        - Scenario ID and success status
        - Year range (start_year - end_year)
        - Row count in panel output
        - Manifest ID
  - [ ] 1.4 Implement accessor methods:
        - `.indicators(indicator_type: str, **kwargs) -> IndicatorResult`

- [ ] Task 2: Create configuration types (AC: #1, #4)
  - [ ] 2.1 Define `ScenarioConfig` frozen dataclass:
        - `template_name: str`
        - `parameters: dict[str, Any]`
        - `population_path: Path | None`
        - `start_year: int`
        - `end_year: int`
        - `seed: int | None`
        - `baseline_id: str | None` (for reform scenarios)
  - [ ] 2.2 Define `RunConfig` frozen dataclass:
        - `scenario: ScenarioConfig | Path | dict[str, Any]` (YAML path or config object)
        - `output_dir: Path | None`
        - `seed: int | None`
  - [ ] 2.3 Define `ConfigurationError` in `interfaces/errors.py`:
        - `field_path: str`
        - `expected: str`
        - `actual: Any`
        - Clear error message format

- [ ] Task 3: Implement run_scenario function (AC: #1, #5)
  - [ ] 3.1 Signature: `run_scenario(config: RunConfig | Path | dict, adapter: ComputationAdapter | None = None) -> SimulationResult`
  - [ ] 3.2 If config is `Path`, load YAML and validate against schema
  - [ ] 3.3 If config is `dict`, convert to `RunConfig`
  - [ ] 3.4 Validate configuration completeness before execution
  - [ ] 3.5 Delegate to existing subsystems:
        - Load and validate config via `templates/workflow.py` and template utilities
        - Execute through `run_workflow(..., runner=OrchestratorRunner(...))` or equivalent `OrchestratorRunner.run()` handoff
        - Capture manifest via governance layer
        - Package results as `SimulationResult`
  - [ ] 3.6 Wrap all subsystem errors in user-friendly `ConfigurationError` or `SimulationError`

- [ ] Task 4: Implement scenario management functions (AC: #2)
  - [ ] 4.1 Implement `create_scenario(scenario: BaselineScenario | ReformScenario, name: str, register: bool = False) -> str | BaselineScenario | ReformScenario`
  - [ ] 4.2 Implement `clone_scenario(name: str, version_id: str | None = None, new_name: str | None = None) -> BaselineScenario | ReformScenario`
  - [ ] 4.3 Implement `list_scenarios() -> list[str]` for registered scenarios
  - [ ] 4.4 Implement `get_scenario(name: str, version_id: str | None = None) -> BaselineScenario | ReformScenario`
  - [ ] 4.5 Delegate to existing `templates/registry.py` for persistence

- [ ] Task 5: Export public API from package root (AC: #6)
  - [ ] 5.1 Update `src/reformlab/__init__.py` with public exports:
        - `run_scenario`
        - `create_scenario`
        - `clone_scenario`
        - `list_scenarios`
        - `get_scenario`
        - `SimulationResult`
        - `ScenarioConfig`
        - `RunConfig`
        - `ConfigurationError`
        - `SimulationError`
  - [ ] 5.2 Define `__all__` list with all public symbols
  - [ ] 5.3 Add module docstring documenting public API

- [ ] Task 6: Create tests (AC: #1-6)
  - [ ] 6.1 Create `tests/interfaces/test_api.py`
  - [ ] 6.2 Test `SimulationResult` dataclass (immutability, repr, accessors)
  - [ ] 6.3 Test `run_scenario()` with valid YAML config (MockAdapter)
  - [ ] 6.4 Test `run_scenario()` with valid dict config
  - [ ] 6.5 Test `run_scenario()` with invalid config (ConfigurationError raised)
  - [ ] 6.6 Test `create_scenario()` and `clone_scenario()`
  - [ ] 6.7 Test `SimulationResult.indicators()` integration with indicator subsystem
  - [ ] 6.8 Test API error translation (`ConfigurationError`/`SimulationError`) with no bare `ValueError` leaks
  - [ ] 6.9 Test public imports from `reformlab` package root
  - [ ] 6.10 Run `ruff check src/reformlab/interfaces tests/interfaces`
  - [ ] 6.11 Run `mypy src/reformlab/interfaces`
  - [ ] 6.12 Run targeted tests (`pytest tests/interfaces -v`)

## Dev Notes

### Architecture Compliance

This story implements **FR30** (Python API for run orchestration) and **NFR16** (sensible `__repr__` for notebooks) from the PRD.

**Key architectural constraints:**

- **API is a thin facade** - The API layer orchestrates existing subsystems; it does NOT duplicate computation, template, or orchestrator logic. [Source: architecture.md#Layered-Architecture]
- **Frozen dataclasses are the default** - `SimulationResult`, `ScenarioConfig`, `RunConfig` must all be `@dataclass(frozen=True)`. [Source: _bmad-output/project-context.md#Python-Language-Rules]
- **PyArrow is canonical** - `panel_output` wraps PyArrow data (`PanelOutput.table: pa.Table`), not pandas. [Source: _bmad-output/project-context.md#Critical-Implementation-Rules]
- **Subsystem-specific exceptions** - Define `ConfigurationError`, `SimulationError` in `interfaces/errors.py`. Never raise bare `ValueError`. [Source: _bmad-output/project-context.md#Python-Language-Rules]
- **No OpenFisca imports outside adapters** - The API layer must never import OpenFisca directly. Use `ComputationAdapter` protocol. [Source: _bmad-output/project-context.md#Critical-Don't-Miss-Rules]

### Existing Code to Reuse

**From `templates/workflow.py`:**
```python
@dataclass(frozen=True)
class WorkflowConfig:
    """Complete workflow configuration."""
    name: str
    version: str
    data_sources: DataSourceConfig
    scenarios: tuple[ScenarioRef, ...]
    run_config: RunConfig

def run_workflow(
    config: WorkflowConfig,
    *,
    runner: Any | None = None,
) -> WorkflowResult: ...
```

**From `templates/registry.py`:**
```python
class ScenarioRegistry:
    """Versioned scenario storage with immutable IDs."""
    def save(
        self,
        scenario: BaselineScenario | ReformScenario,
        name: str,
        change_description: str = "",
    ) -> str: ...
    def get(
        self,
        name: str,
        version_id: str | None = None,
    ) -> BaselineScenario | ReformScenario: ...
    def clone(
        self,
        name: str,
        version_id: str | None = None,
        new_name: str | None = None,
    ) -> BaselineScenario | ReformScenario: ...
```

**From `orchestrator/runner.py`:**
```python
class OrchestratorRunner:
    """High-level runner coordinating orchestrator with governance."""
    def run(self, request: dict[str, Any]) -> WorkflowResult: ...
```

**From `orchestrator/panel.py`:**
```python
@dataclass
class PanelOutput:
    """Stacked yearly panel output."""
    table: pa.Table
    metadata: dict[str, Any]
```

**From `governance/manifest.py`:**
```python
@dataclass(frozen=True)
class RunManifest:
    """Immutable run manifest with integrity hash."""
    manifest_id: str
    created_at: str
    engine_version: str
    openfisca_version: str
    adapter_version: str
    ...
```

### Implementation Pattern

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.computation.adapter import ComputationAdapter
    from reformlab.governance.manifest import RunManifest
    from reformlab.indicators.types import IndicatorResult
    from reformlab.orchestrator.panel import PanelOutput
    from reformlab.orchestrator.types import YearState


@dataclass(frozen=True)
class SimulationResult:
    """Result of a simulation run with notebook-friendly display."""

    success: bool
    scenario_id: str
    yearly_states: dict[int, YearState]
    panel_output: PanelOutput | None
    manifest: RunManifest
    metadata: dict[str, Any]

    def __repr__(self) -> str:
        years = sorted(self.yearly_states.keys())
        year_range = f"{years[0]}-{years[-1]}" if years else "none"
        rows = self.panel_output.table.num_rows if self.panel_output else 0
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"SimulationResult({status}, scenario={self.scenario_id!r}, "
            f"years={year_range}, rows={rows}, manifest={self.manifest.manifest_id!r})"
        )

    def indicators(
        self,
        indicator_type: str,
        **kwargs: Any,
    ) -> IndicatorResult:
        """Compute indicators from panel output."""
        from reformlab.interfaces.errors import SimulationError
        if self.panel_output is None:
            msg = "No panel output available"
            raise SimulationError(msg)
        return _compute_indicator(self.panel_output, indicator_type, **kwargs)


def run_scenario(
    config: RunConfig | Path | dict[str, Any],
    adapter: ComputationAdapter | None = None,
) -> SimulationResult:
    """Run a complete simulation scenario.

    Args:
        config: Scenario configuration as RunConfig, YAML path, or dict.
        adapter: Optional computation adapter. Tests typically inject MockAdapter.

    Returns:
        SimulationResult with yearly states, panel output, and manifest.

    Raises:
        ConfigurationError: If configuration is invalid.
        SimulationError: If simulation fails during execution.
    """
    # 1. Normalize config to RunConfig
    run_config = _normalize_config(config)

    # 2. Validate before execution
    _validate_config(run_config)

    # 3. Load scenario template
    scenario = _load_scenario(run_config.scenario)

    # 4. Setup adapter
    if adapter is None:
        from reformlab.computation.openfisca_adapter import OpenFiscaAdapter

        adapter = OpenFiscaAdapter(...)

    # 5. Execute via orchestrator
    result = _execute_orchestration(scenario, run_config, adapter)

    # 6. Package and return
    return result
```

### Module Structure

```
src/reformlab/interfaces/
├── __init__.py           # Re-export public API
├── api.py                # Core API functions and types
└── errors.py             # ConfigurationError, SimulationError

src/reformlab/
├── __init__.py           # Package root exports (UPDATE)
└── ...

tests/interfaces/
├── __init__.py
├── conftest.py           # API test fixtures
└── test_api.py           # API tests
```

### Scope Guardrails

- **In scope:**
  - `SimulationResult` dataclass with `__repr__` and indicator accessors
  - `ScenarioConfig`, `RunConfig` dataclasses
  - `run_scenario()` function
  - `create_scenario()`, `clone_scenario()`, `list_scenarios()`, `get_scenario()`
  - `ConfigurationError`, `SimulationError` exception types
  - Package root exports
  - Unit and integration tests with MockAdapter

- **Out of scope:**
  - FastAPI HTTP endpoints (Story 6-4b)
  - Notebook examples (Stories 6-2, 6-3)
  - GUI integration (Story 6-4b)
  - CSV/Parquet export actions and convenience APIs (Story 6-5 / BKL-605)
  - Async/concurrent execution
  - Caching or memoization
  - Result persistence infrastructure

### Testing Standards

- Mirror source structure: `tests/interfaces/test_api.py`
- Class-based test grouping: `TestSimulationResult`, `TestRunScenario`, `TestScenarioManagement`
- Use `tmp_path` fixture for file operations
- Use `MockAdapter` from `computation/mock_adapter.py`
- Test both success and error paths
- Test `__repr__` output format for notebook display
- Integration test: full run cycle via API with MockAdapter

### Previous Story Intelligence

This is the first story in EPIC-6, but builds on all previous epics:

**From EPIC-1 (Computation):**
- `MockAdapter` is the standard test double for API tests
- `ComputationAdapter` protocol defines the adapter interface

**From EPIC-2 (Templates):**
- `ScenarioTemplate` defines scenario structure
- `ScenarioRegistry` handles versioned scenario storage
- `WorkflowConfig` pattern for configuration

**From EPIC-3 (Orchestrator):**
- `OrchestratorRunner` handles execution with governance
- `YearState` carries state between years
- `PanelOutput` provides stacked yearly results

**From EPIC-4 (Indicators):**
- Indicator functions compute from panel output
- `compute_distributional_indicators`, `compute_welfare_indicators`, etc.

**From EPIC-5 (Governance):**
- `RunManifest` captures run provenance
- Every run produces a manifest automatically

### References

- [Source: prd.md#Functional-Requirements] - FR30 Python API for run orchestration
- [Source: prd.md#Non-Functional-Requirements] - NFR16 sensible `__repr__` for notebooks
- [Source: backlog BKL-601] - Story acceptance criteria
- [Source: architecture.md#Layered-Architecture] - API is facade over subsystems
- [Source: ux-design-specification.md#Journey-3-Marco] - Researcher Python API workflow
- [Source: templates/workflow.py] - WorkflowConfig pattern
- [Source: templates/registry.py] - ScenarioRegistry pattern
- [Source: orchestrator/runner.py] - OrchestratorRunner.run() contract
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] - Frozen dataclasses, PyArrow canonical

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
