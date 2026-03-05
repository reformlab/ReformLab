<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 12 -->
<!-- Story: 2 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260305T195937Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 12.2

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
<file id="b5c6fe32" path="_bmad-output/project-context.md" label="PROJECT CONTEXT"><![CDATA[

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
<file id="38e1067d" path="_bmad-output/implementation-artifacts/12-2-implement-portfolio-compatibility-validation-and-conflict-resolution.md" label="STORY FILE"><![CDATA[



# Story 12.2: Implement portfolio compatibility validation and conflict resolution

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want to detect and resolve conflicts when multiple policies in a portfolio affect the same household attributes,
so that I can ensure coherent policy combinations and prevent unintended interactions during simulation runs.

## Acceptance Criteria

1. **AC1: Conflict detection for same policy type** — Given two policies of the same type in a portfolio (e.g., two carbon taxes), when validated, then a conflict is detected and reported with the exact policy names and conflicting parameters.

2. **AC2: Non-conflicting portfolio validation** — Given a portfolio with non-conflicting policies (e.g., carbon tax + vehicle subsidy), when validated, then validation passes with no conflicts reported.

3. **AC3: Resolution strategy application** — Given a conflict and an explicit resolution strategy ("sum", "first_wins", "last_wins", "max"), when the portfolio is validated or executed, then the conflict is resolved according to the strategy and the resolution is recorded in portfolio metadata.

4. **AC4: Execution blocking for unresolved conflicts** — Given an unresolvable conflict with resolution strategy "error" (default), when the portfolio is executed, then it fails before computation with a clear error listing all conflicting policies, parameters, and suggested resolution strategies.

5. **AC5: Deterministic conflict resolution** — Given identical portfolios and resolution strategies, when validated/executed multiple times, then conflict detection and resolution produce identical results (deterministic ordering, stable output).

## Tasks / Subtasks

- [ ] **Task 1: Define conflict detection data structures** (AC: #1, #5)
  - [ ] 1.1 Create `Conflict` frozen dataclass in `composition.py` with fields: `conflict_type`, `policy_indices`, `parameter_name`, `conflicting_values`, `description`
  - [ ] 1.2 Create `ConflictType` enum: `SAME_POLICY_TYPE`, `OVERLAPPING_CATEGORIES`, `OVERLAPPING_YEARS`, `PARAMETER_MISMATCH`
  - [ ] 1.3 Add `__repr__` for readable conflict descriptions
  - [ ] 1.4 Ensure frozen dataclass pattern with `from __future__ import annotations`

- [ ] **Task 2: Add resolution strategy field to PolicyPortfolio** (AC: #3, #5)
  - [ ] 2.1 Add `resolution_strategy: str = "error"` field to `PolicyPortfolio` dataclass
  - [ ] 2.2 Create `ResolutionStrategy` enum in `composition.py`: `ERROR`, `SUM`, `FIRST_WINS`, `LAST_WINS`, `MAX`
  - [ ] 2.3 Validate resolution_strategy in `__post_init__` (must be valid enum value)
  - [ ] 2.4 Update YAML serialization in `composition.py` to include resolution_strategy field
  - [ ] 2.5 Update portfolio.schema.json to include resolution_strategy field with enum validation
  - [ ] 2.6 Ensure round-trip preserves resolution_strategy value

- [ ] **Task 3: Implement conflict detection logic** (AC: #1, #2, #5)
  - [ ] 3.1 Create `validate_compatibility(portfolio: PolicyPortfolio) -> tuple[Conflict, ...]` function
  - [ ] 3.2 Detect `SAME_POLICY_TYPE` conflicts: two policies with same PolicyType
  - [ ] 3.3 Detect `OVERLAPPING_CATEGORIES` conflicts: overlapping covered_categories or eligible_categories
  - [ ] 3.4 Detect `OVERLAPPING_YEARS` conflicts: overlapping years in rate_schedule dictionaries
  - [ ] 3.5 Detect `PARAMETER_MISMATCH` conflicts: same category affected by different parameters
  - [ ] 3.6 Ensure deterministic conflict ordering (sorted by policy indices, then parameter name)
  - [ ] 3.7 Return empty tuple for non-conflicting portfolios

- [ ] **Task 4: Implement conflict resolution logic** (AC: #3, #4, #5)
  - [ ] 4.1 Create `resolve_conflicts(portfolio: PolicyPortfolio, conflicts: tuple[Conflict, ...]) -> PolicyPortfolio` function
  - [ ] 4.2 Implement "error" strategy: raise `PortfolioValidationError` if any conflicts exist
  - [ ] 4.3 Implement "sum" strategy: add rate values for overlapping years
  - [ ] 4.4 Implement "first_wins" strategy: use first policy's values for conflicts
  - [ ] 4.5 Implement "last_wins" strategy: use last policy's values for conflicts
  - [ ] 4.6 Implement "max" strategy: use maximum rate for overlapping years
  - [ ] 4.7 Return new PolicyPortfolio with resolved policies (frozen dataclass → create new instance)
  - [ ] 4.8 Record resolution metadata in description or new metadata field
  - [ ] 4.9 Ensure deterministic resolution (stable ordering, identical results for identical inputs)

- [ ] **Task 5: Integrate validation into portfolio loading** (AC: #4)
  - [ ] 5.1 Update `load_portfolio()` to call `validate_compatibility()` after loading
  - [ ] 5.2 Add optional parameter `validate: bool = True` to `load_portfolio()`
  - [ ] 5.3 If conflicts exist and resolution_strategy is "error", raise `PortfolioValidationError` with conflict details
  - [ ] 5.4 If conflicts exist and resolution_strategy is not "error", log warning with conflict summary
  - [ ] 5.5 Include suggested resolution strategies in error messages

- [ ] **Task 6: Write comprehensive tests** (AC: #1, #2, #3, #4, #5)
  - [ ] 6.1 Create `tests/templates/portfolios/test_conflicts.py` for conflict detection tests
  - [ ] 6.2 Test `SAME_POLICY_TYPE` conflict detection with two carbon taxes
  - [ ] 6.3 Test `OVERLAPPING_CATEGORIES` conflict detection with overlapping covered_categories
  - [ ] 6.4 Test `OVERLAPPING_YEARS` conflict detection with overlapping rate_schedule years
  - [ ] 6.5 Test non-conflicting portfolio (carbon tax + subsidy) passes validation
  - [ ] 6.6 Test "error" strategy raises exception with clear conflict details
  - [ ] 6.7 Test "sum" strategy adds rates for overlapping years
  - [ ] 6.8 Test "first_wins" strategy uses first policy values
  - [ ] 6.9 Test "last_wins" strategy uses last policy values
  - [ ] 6.10 Test "max" strategy uses maximum rate
  - [ ] 6.11 Test deterministic conflict ordering (sorted by indices, then parameter)
  - [ ] 6.12 Test deterministic resolution (identical results for identical inputs)
  - [ ] 6.13 Test YAML round-trip preserves resolution_strategy
  - [ ] 6.14 Test error messages include suggested resolution strategies
  - [ ] 6.15 Run `uv run pytest tests/templates/portfolios/ --cov=src/reformlab/templates/portfolios --cov-report=term-missing` to verify >90% coverage

- [ ] **Task 7: Update module exports and documentation** (AC: #1, #2, #3, #4)
  - [ ] 7.1 Export `Conflict`, `ConflictType`, `ResolutionStrategy` from `portfolios/__init__.py`
  - [ ] 7.2 Export `validate_compatibility`, `resolve_conflicts` from `portfolios/__init__.py`
  - [ ] 7.3 Update `templates/__init__.py` to export conflict types
  - [ ] 7.4 Add module docstring to `composition.py` explaining conflict detection and resolution
  - [ ] 7.5 Add inline code comments explaining resolution strategy semantics

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Frozen dataclass is NON-NEGOTIABLE** — `Conflict` and all new types must use `@dataclass(frozen=True)`. Resolution functions return NEW PolicyPortfolio instances, never mutate existing ones [Source: project-context.md#architecture-framework-rules].

```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.templates.portfolios.portfolio import PolicyPortfolio

class ConflictType(Enum):
    """Types of conflicts that can occur in a portfolio."""
    SAME_POLICY_TYPE = "same_policy_type"
    OVERLAPPING_CATEGORIES = "overlapping_categories"
    OVERLAPPING_YEARS = "overlapping_years"
    PARAMETER_MISMATCH = "parameter_mismatch"

class ResolutionStrategy(Enum):
    """Strategies for resolving portfolio conflicts."""
    ERROR = "error"
    SUM = "sum"
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    MAX = "max"

@dataclass(frozen=True)
class Conflict:
    """Represents a detected conflict between policies in a portfolio."""
    conflict_type: ConflictType
    policy_indices: tuple[int, ...]  # Indices of conflicting policies
    parameter_name: str  # e.g., "rate_schedule", "covered_categories"
    conflicting_values: tuple[Any, ...]  # The actual conflicting values
    description: str  # Human-readable description
```

**Use `tuple` not `list`** — All ordered collections in conflict detection use `tuple` for immutability [Source: project-context.md#python-language-rules].

**Determinism is NON-NEGOTIABLE** — Conflict detection and resolution must be deterministic:
- Conflicts sorted by policy indices (ascending), then parameter name (alphabetical)
- Resolution produces identical results for identical inputs
- No random or unordered iteration (use sorted() where needed)

### Existing Code Integration

**PolicyPortfolio structure** [Source: src/reformlab/templates/portfolios/portfolio.py]:
```python
@dataclass(frozen=True)
class PolicyPortfolio:
    name: str
    policies: tuple[PolicyConfig, ...]
    version: str = "1.0"
    description: str = ""
    # NEW FIELD: resolution_strategy: str = "error"
```

**PolicyConfig structure** [Source: src/reformlab/templates/portfolios/portfolio.py]:
```python
@dataclass(frozen=True)
class PolicyConfig:
    policy_type: PolicyType
    policy: PolicyParameters
    name: str = ""
```

**PolicyParameters hierarchy** [Source: src/reformlab/templates/schema.py]:
- All policies: `rate_schedule`, `exemptions`, `thresholds`, `covered_categories`
- CarbonTaxParameters: `redistribution_type`, `income_weights`
- SubsidyParameters: `eligible_categories`, `income_caps`
- RebateParameters: `rebate_type`, `income_weights`
- FeebateParameters: `pivot_point`, `fee_rate`, `rebate_rate`

### Conflict Detection Logic

**SAME_POLICY_TYPE conflicts:**
- Detect when two policies have identical `PolicyType` values
- Example: Two `PolicyType.CARBON_TAX` policies
- Conflicting parameter: `"policy_type"`
- Conflicting values: tuple of the two policy names or indices

**OVERLAPPING_CATEGORIES conflicts:**
- Detect overlapping `covered_categories` or `eligible_categories`
- Example: Carbon tax covers ["transport", "heating"] and subsidy covers ["heating", "electricity"]
- Overlap: "heating"
- Conflicting parameter: `"covered_categories"` or `"eligible_categories"`

**OVERLAPPING_YEARS conflicts:**
- Detect overlapping years in `rate_schedule` dictionaries
- Example: Policy A has rates for 2026-2028, Policy B has rates for 2027-2029
- Overlap: 2027, 2028
- Conflicting parameter: `"rate_schedule"`

**PARAMETER_MISMATCH conflicts:**
- Detect when same category has different parameter values
- Example: Two policies affect "transport" but with different income_caps
- Conflicting parameter: specific parameter name (e.g., `"income_caps"`)

### Resolution Strategy Semantics

**"error" (default):**
- Raise `PortfolioValidationError` if ANY conflicts exist
- Error message includes: conflict type, policy names, parameter name, conflicting values
- Suggested resolution strategies in error message: "Consider using resolution_strategy: 'sum', 'first_wins', 'last_wins', or 'max'"

**"sum":**
- For `OVERLAPPING_YEARS` conflicts: add rate values for overlapping years
- Example: Policy A rate 2027 = 50, Policy B rate 2027 = 30 → resolved rate = 80
- Only applies to numeric rate values
- For other conflict types: treat as "error" (cannot sum non-numeric values)

**"first_wins":**
- Use first policy's values for all conflicts
- Example: Policy A (index 0) vs Policy B (index 1) → use Policy A's values
- Preserves first policy's rate_schedule, categories, parameters

**"last_wins":**
- Use last policy's values for all conflicts
- Example: Policy A (index 0) vs Policy B (index 1) → use Policy B's values
- Preserves last policy's rate_schedule, categories, parameters

**"max":**
- For `OVERLAPPING_YEARS` conflicts: use maximum rate for overlapping years
- Example: Policy A rate 2027 = 50, Policy B rate 2027 = 30 → resolved rate = 50
- Only applies to numeric rate values
- For other conflict types: treat as "error" (cannot take max of non-numeric values)

### Resolution Implementation Pattern

**Creating new PolicyPortfolio with resolved policies:**
```python
def resolve_conflicts(
    portfolio: PolicyPortfolio, 
    conflicts: tuple[Conflict, ...]
) -> PolicyPortfolio:
    """Resolve conflicts and return new portfolio with resolved policies."""
    if portfolio.resolution_strategy == "error":
        if conflicts:
            raise PortfolioValidationError(
                summary="Unresolved portfolio conflicts",
                reason=f"{len(conflicts)} conflicts detected",
                fix="Set resolution_strategy to 'sum', 'first_wins', 'last_wins', or 'max'",
                invalid_fields=tuple(f"policies[{c.policy_indices[0]}]" for c in conflicts),
            )
        return portfolio  # No conflicts, return as-is
    
    # Apply resolution strategy
    resolved_policies = _apply_resolution_strategy(
        portfolio.policies, 
        conflicts, 
        portfolio.resolution_strategy
    )
    
    # Create new portfolio with resolved policies
    return PolicyPortfolio(
        name=portfolio.name,
        policies=resolved_policies,
        version=portfolio.version,
        description=f"{portfolio.description}\n\nResolved {len(conflicts)} conflicts using '{portfolio.resolution_strategy}' strategy.".strip(),
        resolution_strategy=portfolio.resolution_strategy,
    )
```

### Testing Standards

**Mirror source structure** [Source: project-context.md#testing-rules]:
```
tests/templates/portfolios/
├── conftest.py              ← existing (fixtures for policies, portfolios)
├── test_portfolio.py        ← existing (dataclass tests)
├── test_composition.py      ← existing (YAML tests) - UPDATE for resolution_strategy
└── test_conflicts.py        ← NEW (conflict detection and resolution)
```

**Class-based test grouping** [Source: project-context.md]:
```python
class TestConflictDetection:
    """Tests for conflict detection logic (AC #1, #2, #5)."""
    
class TestConflictResolution:
    """Tests for conflict resolution strategies (AC #3, #4, #5)."""
    
class TestConflictYAMLIntegration:
    """Tests for YAML serialization with resolution_strategy (AC #3, #5)."""
```

**Direct assertions, no helpers** [Source: project-context.md]:
```python
def test_sum_strategy_adds_rates(self) -> None:
    """Sum strategy adds rates for overlapping years."""
    portfolio = PolicyPortfolio(
        name="Test",
        policies=(policy_a, policy_b),
        resolution_strategy="sum",
    )
    conflicts = validate_compatibility(portfolio)
    resolved = resolve_conflicts(portfolio, conflicts)
    # Direct assertion on resolved rates
    assert resolved.policies[0].policy.rate_schedule[2027] == 80  # 50 + 30
```

### File Structure

**Updated directory** [Source: architecture.md#extension-policy-portfolio-layer]:
```
src/reformlab/templates/
├── portfolios/
│   ├── __init__.py
│   ├── portfolio.py     ← PolicyPortfolio (ADD resolution_strategy field)
│   ├── composition.py   ← ADD: Conflict, ConflictType, ResolutionStrategy,
│   │                    ←      validate_compatibility(), resolve_conflicts()
│   └── exceptions.py    ← existing (PortfolioError hierarchy)
└── schema/
    └── portfolio.schema.json  ← UPDATE: add resolution_strategy field
```

**Exception taxonomy** — Use existing `PortfolioValidationError` for conflict errors:
```python
# In composition.py
if conflicts and portfolio.resolution_strategy == "error":
    conflict_details = "\n".join(
        f"  - {c.description}" for c in conflicts
    )
    raise PortfolioValidationError(
        summary="Portfolio has unresolved conflicts",
        reason=f"{len(conflicts)} conflicts detected:\n{conflict_details}",
        fix="Set resolution_strategy to 'sum', 'first_wins', 'last_wins', or 'max' "
            "to automatically resolve conflicts",
        invalid_fields=tuple(f"policies[{i}]" for c in conflicts for i in c.policy_indices),
    )
```

### Integration with Existing Code

**Scope boundaries** — This story focuses on conflict detection and resolution ONLY:
- ✅ IN SCOPE: Conflict detection, resolution strategies, metadata recording, validation integration
- ❌ OUT OF SCOPE: Orchestrator execution (Story 12.3), scenario registry integration (Story 12.4), multi-portfolio comparison (Story 12.5)

**YAML schema compatibility** — Portfolio YAML files from Story 12.1 must remain valid:
- `resolution_strategy` field is optional (defaults to "error")
- Existing portfolios without resolution_strategy work as before (fail on conflicts)
- Schema version remains "1.0" (additive change, not breaking)

**Load-time validation** — Conflicts detected at load time, not construction time:
- `PolicyPortfolio.__post_init__` does NOT validate conflicts (deferred to load_portfolio)
- `load_portfolio(path, validate=True)` calls `validate_compatibility()` after loading
- `load_portfolio(path, validate=False)` skips conflict detection (for testing/special cases)

### Error Message Examples

**Conflict detection error (strategy="error"):**
```
PortfolioValidationError: Portfolio has unresolved conflicts
  Reason: 2 conflicts detected:
    - SAME_POLICY_TYPE conflict between policies[0] and policies[1]: both are carbon_tax
    - OVERLAPPING_YEARS conflict in rate_schedule: years 2027-2028 overlap
  Fix: Set resolution_strategy to 'sum', 'first_wins', 'last_wins', or 'max' to automatically resolve conflicts
  Invalid fields: policies[0], policies[1]
```

**Resolution warning (strategy!="error"):**
```
WARNING: Portfolio 'Green Transition 2030' has 2 conflicts resolved using 'sum' strategy:
  - SAME_POLICY_TYPE: policies[0] and policies[1] (carbon_tax)
  - OVERLAPPING_YEARS: rate_schedule years 2027-2028
```

### Project Structure Notes

- **Alignment with unified project structure:** Conflict logic added to existing `composition.py` module (not new file)
- **Naming convention:** `Conflict`, `ConflictType`, `ResolutionStrategy` follow PascalCase enum/class naming
- **Module docstrings:** Update `composition.py` docstring to explain conflict detection and resolution
- **Frozen dataclass pattern:** `Conflict` is frozen, resolution returns new `PolicyPortfolio` instances

### Critical Don't-Miss Rules

1. **Every file starts with `from __future__ import annotations`** — no exceptions [Source: project-context.md#python-language-rules]
2. **Use `if TYPE_CHECKING:` guards** for imports only needed for annotations [Source: project-context.md#python-language-rules]
3. **All domain types are frozen** — `Conflict` must be frozen, resolution returns new `PolicyPortfolio` [Source: project-context.md#critical-dont-miss-rules]
4. **Determinism is non-negotiable** — conflict ordering and resolution must be deterministic [Source: project-context.md#critical-dont-miss-rules]
5. **No wildcard imports** — always import specific names [Source: project-context.md#code-quality-style-rules]
6. **Resolution creates new objects** — never mutate frozen dataclasses, use `PolicyPortfolio(...)` to create new instance

### References

**Architecture:**
- [Source: architecture.md#extension-policy-portfolio-layer] — Policy Portfolio Layer design, composition.py responsibilities
- [Source: architecture.md#phase-2-architecture-extensions] — Phase 2 subsystem overview

**PRD:**
- [Source: prd.md#phase-2-policy-portfolios] — FR43: compose policies, FR44: execute portfolio

**Existing Code:**
- [Source: src/reformlab/templates/portfolios/portfolio.py] — PolicyPortfolio and PolicyConfig definitions
- [Source: src/reformlab/templates/portfolios/composition.py] — YAML serialization (extend for conflicts)
- [Source: src/reformlab/templates/schema.py] — PolicyParameters hierarchy and attributes
- [Source: src/reformlab/templates/portfolios/exceptions.py] — PortfolioValidationError

**Previous Story:**
- [Source: _bmad-output/implementation-artifacts/12-1-define-policyportfolio-dataclass-and-composition-logic.md] — Story 12.1 implementation patterns, frozen dataclass approach, testing standards

**Testing:**
- [Source: tests/templates/portfolios/test_composition.py] — Example YAML round-trip tests
- [Source: tests/templates/portfolios/conftest.py] — Existing fixtures for policies

**Project Context:**
- [Source: project-context.md#architecture-framework-rules] — Frozen dataclasses, Protocols, determinism
- [Source: project-context.md#testing-rules] — Test structure, fixtures, assertions
- [Source: project-context.md#code-quality-style-rules] — ruff, mypy, naming conventions

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

Story 12.1 completed successfully on 2026-03-05. Code review synthesis applied fixes for immutability, package integration, and schema validation.

### Completion Notes List

Ultimate context engine analysis completed - comprehensive developer guide created with detailed conflict detection logic, resolution strategy semantics, and integration patterns.

### File List

**Source code files to create/modify:**
- src/reformlab/templates/portfolios/portfolio.py (add resolution_strategy field)
- src/reformlab/templates/portfolios/composition.py (add Conflict, ConflictType, ResolutionStrategy, validate_compatibility, resolve_conflicts)
- src/reformlab/templates/schema/portfolio.schema.json (add resolution_strategy field)
- src/reformlab/templates/portfolios/__init__.py (export new types)
- src/reformlab/templates/__init__.py (export conflict types)

**Test files to create:**
- tests/templates/portfolios/test_conflicts.py (new file)
- tests/templates/portfolios/test_composition.py (update for resolution_strategy)



]]></file>
<file id="986a4896" path="src/reformlab/templates/__init__.py" label="SOURCE CODE"><![CDATA[

"""Scenario template schema and loader for ReformLab.

This module provides:
- Schema dataclasses for defining scenario templates
- YAML loader/serializer for scenario template files
- Reform-as-delta resolution for reform scenarios
- JSON Schema for IDE validation support
- Template pack discovery and loading utilities
- Scenario registry with immutable versioning
- Schema migration utilities for version compatibility
- Workflow configuration schema and execution handoff
"""

from reformlab.templates.exceptions import ScenarioError, TemplateError
from reformlab.templates.loader import (
    SCHEMA_VERSION,
    dump_scenario_template,
    get_schema_path,
    load_scenario_template,
    validate_schema_version,
)
from reformlab.templates.migration import (
    CompatibilityStatus,
    MigrationChange,
    MigrationReport,
    SchemaVersion,
    check_compatibility,
    migrate_scenario_dict,
)
from reformlab.templates.packs import (
    get_carbon_tax_pack_dir,
    get_feebate_pack_dir,
    get_rebate_pack_dir,
    get_subsidy_pack_dir,
    list_carbon_tax_templates,
    list_feebate_templates,
    list_rebate_templates,
    list_subsidy_templates,
    load_carbon_tax_template,
    load_feebate_template,
    load_rebate_template,
    load_subsidy_template,
)
from reformlab.templates.reform import resolve_reform_definition
from reformlab.templates.registry import (
    RegistryEntry,
    RegistryError,
    ScenarioNotFoundError,
    ScenarioRegistry,
    ScenarioVersion,
    VersionNotFoundError,
)
from reformlab.templates.schema import (
    BaselineScenario,
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    ReformScenario,
    ScenarioTemplate,
    SubsidyParameters,
    YearSchedule,
    infer_policy_type,
)
from reformlab.templates.portfolios import (
    PolicyConfig,
    PolicyPortfolio,
    PortfolioError,
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.workflow import (
    WORKFLOW_SCHEMA_VERSION,
    DataSourceConfig,
    OutputConfig,
    OutputFormat,
    OutputType,
    RunConfig,
    ScenarioRef,
    WorkflowConfig,
    WorkflowError,
    WorkflowResult,
    dump_workflow_config,
    get_workflow_schema_path,
    load_workflow_config,
    prepare_workflow_request,
    run_workflow,
    validate_workflow_config,
    validate_workflow_with_schema,
    workflow_to_json,
    workflow_to_yaml,
)

__all__ = [
    # Portfolio types
    "PolicyConfig",
    "PolicyPortfolio",
    "PortfolioError",
    "PortfolioSerializationError",
    "PortfolioValidationError",
    # Migration types and functions
    "CompatibilityStatus",
    "MigrationChange",
    "MigrationReport",
    "SchemaVersion",
    "check_compatibility",
    "migrate_scenario_dict",
    # Registry types
    "RegistryEntry",
    "RegistryError",
    "ScenarioNotFoundError",
    "ScenarioRegistry",
    "ScenarioVersion",
    "VersionNotFoundError",
    # Schema types
    "BaselineScenario",
    "CarbonTaxParameters",
    "FeebateParameters",
    "PolicyParameters",
    "PolicyType",
    "RebateParameters",
    "ReformScenario",
    "ScenarioTemplate",
    "SubsidyParameters",
    "YearSchedule",
    # Loader functions
    "dump_scenario_template",
    "get_schema_path",
    "load_scenario_template",
    "resolve_reform_definition",
    "validate_schema_version",
    # Pack utilities - Carbon tax
    "get_carbon_tax_pack_dir",
    "list_carbon_tax_templates",
    "load_carbon_tax_template",
    # Pack utilities - Subsidy
    "get_subsidy_pack_dir",
    "list_subsidy_templates",
    "load_subsidy_template",
    # Pack utilities - Rebate
    "get_rebate_pack_dir",
    "list_rebate_templates",
    "load_rebate_template",
    # Pack utilities - Feebate
    "get_feebate_pack_dir",
    "list_feebate_templates",
    "load_feebate_template",
    # Inference
    "infer_policy_type",
    # Exceptions
    "ScenarioError",
    "TemplateError",
    # Constants
    "SCHEMA_VERSION",
    # Workflow types and functions
    "DataSourceConfig",
    "OutputConfig",
    "OutputFormat",
    "OutputType",
    "RunConfig",
    "ScenarioRef",
    "WorkflowConfig",
    "WorkflowError",
    "WorkflowResult",
    "WORKFLOW_SCHEMA_VERSION",
    "dump_workflow_config",
    "get_workflow_schema_path",
    "load_workflow_config",
    "prepare_workflow_request",
    "run_workflow",
    "validate_workflow_config",
    "validate_workflow_with_schema",
    "workflow_to_json",
    "workflow_to_yaml",
]


]]></file>
<file id="499cc132" path="src/reformlab/templates/portfolios/__init__.py" label="SOURCE CODE"><![CDATA[

"""Policy portfolio composition and serialization.

This module provides the PolicyPortfolio frozen dataclass for composing
multiple individual policy templates into named, versioned policy packages.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
"""

from __future__ import annotations

from reformlab.templates.portfolios.exceptions import (
    PortfolioError,
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio

__all__ = [
    "PolicyConfig",
    "PolicyPortfolio",
    "PortfolioError",
    "PortfolioValidationError",
    "PortfolioSerializationError",
]


]]></file>
<file id="15cb27f1" path="src/reformlab/templates/portfolios/composition.py" label="SOURCE CODE"><![CDATA[

"""Portfolio YAML serialization and deserialization.

Story 12.1: Define PolicyPortfolio dataclass and composition logic
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from reformlab.templates.portfolios.exceptions import (
    PortfolioSerializationError,
    PortfolioValidationError,
)
from reformlab.templates.portfolios.portfolio import PolicyConfig, PolicyPortfolio
from reformlab.templates.schema import (
    CarbonTaxParameters,
    FeebateParameters,
    PolicyParameters,
    PolicyType,
    RebateParameters,
    SubsidyParameters,
)

logger = logging.getLogger(__name__)

_SCHEMA_VERSION = "1.0"
_SCHEMA_DIR = Path(__file__).parent.parent / "schema"


def get_portfolio_schema_path() -> Path:
    """Return path to portfolio JSON Schema."""
    return _SCHEMA_DIR / "portfolio.schema.json"


def _load_schema() -> dict[str, Any]:
    """Load portfolio JSON Schema from disk."""
    schema_path = get_portfolio_schema_path()
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]:
    """Convert PolicyPortfolio to dictionary with deterministic ordering.

    Keys are sorted alphabetically for canonical output.

    Args:
        portfolio: The portfolio to convert

    Returns:
        Dictionary with canonical key ordering
    """
    data: dict[str, Any] = {}

    data["$schema"] = "./schema/portfolio.schema.json"
    data["version"] = portfolio.version
    data["name"] = portfolio.name

    if portfolio.description:
        data["description"] = portfolio.description

    policies_list = []
    for config in portfolio.policies:
        policy_dict: dict[str, Any] = {}
        if config.name:
            policy_dict["name"] = config.name
        policy_dict["policy_type"] = config.policy_type.value
        policy_dict["policy"] = _policy_params_to_dict(config.policy)
        policies_list.append(policy_dict)

    data["policies"] = policies_list

    return data


def _policy_params_to_dict(params: PolicyParameters) -> dict[str, Any]:
    """Convert PolicyParameters to dictionary for YAML serialization."""
    result: dict[str, Any] = {}

    if params.rate_schedule:
        result["rate_schedule"] = params.rate_schedule

    if params.exemptions:
        result["exemptions"] = list(params.exemptions)

    if params.thresholds:
        result["thresholds"] = list(params.thresholds)

    if params.covered_categories:
        result["covered_categories"] = list(params.covered_categories)

    if isinstance(params, CarbonTaxParameters):
        if params.redistribution_type or params.income_weights:
            redistribution: dict[str, Any] = {}
            if params.redistribution_type:
                redistribution["type"] = params.redistribution_type
            if params.income_weights:
                redistribution["income_weights"] = params.income_weights
            result["redistribution"] = redistribution
    elif isinstance(params, SubsidyParameters):
        if params.eligible_categories:
            result["eligible_categories"] = list(params.eligible_categories)
        if params.income_caps:
            result["income_caps"] = params.income_caps
    elif isinstance(params, RebateParameters):
        if params.rebate_type:
            result["rebate_type"] = params.rebate_type
        if params.income_weights:
            result["income_weights"] = params.income_weights
    elif isinstance(params, FeebateParameters):
        if params._pivot_point_set or params.pivot_point != 0.0:
            result["pivot_point"] = params.pivot_point
        if params._fee_rate_set or params.fee_rate != 0.0:
            result["fee_rate"] = params.fee_rate
        if params._rebate_rate_set or params.rebate_rate != 0.0:
            result["rebate_rate"] = params.rebate_rate

    return result


def dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio:
    """Convert dictionary to PolicyPortfolio.

    Args:
        data: Dictionary with portfolio data

    Returns:
        PolicyPortfolio instance

    Raises:
        PortfolioValidationError: If data is invalid
    """
    try:
        schema = _load_schema()
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"Schema validation error: {e.message}",
            fix="Ensure portfolio YAML follows the schema structure",
            invalid_fields=(e.json_path,),
        ) from None
    except jsonschema.SchemaError as e:
        logger.error("Schema error: %s", e)
        raise PortfolioValidationError(
            summary="Portfolio validation failed",
            reason=f"Invalid schema: {e}",
            fix="Check portfolio.schema.json file",
        ) from None

    name = str(data["name"])
    version = str(data.get("version", _SCHEMA_VERSION))
    description = str(data.get("description", ""))

    policies_list = []
    for idx, policy_data in enumerate(data["policies"]):
        policy_name = str(policy_data.get("name", ""))
        policy_type_str = str(policy_data["policy_type"])
        policy_type = PolicyType(policy_type_str)
        policy_params_data = policy_data["policy"]

        policy_params = _dict_to_policy_params(policy_type, policy_params_data)
        config = PolicyConfig(
            policy_type=policy_type,
            policy=policy_params,
            name=policy_name,
        )
        policies_list.append(config)

    portfolio = PolicyPortfolio(
        name=name,
        policies=tuple(policies_list),
        version=version,
        description=description,
    )

    return portfolio


def _dict_to_policy_params(policy_type: PolicyType, raw: dict[str, Any]) -> PolicyParameters:
    """Parse policy parameters from dict based on policy type."""
    rate_schedule: dict[int, float] = {}
    if "rate_schedule" in raw:
        raw_rate = raw["rate_schedule"]
        if not isinstance(raw_rate, dict):
            raise PortfolioValidationError(
                summary="Policy validation failed",
                reason="policy.rate_schedule must be a mapping",
                fix="Set rate_schedule as a YAML object with numeric values",
                invalid_fields=("policy.rate_schedule",),
            )
        try:
            for k, v in raw_rate.items():
                rate_schedule[int(k)] = float(v)
        except (TypeError, ValueError):
            raise PortfolioValidationError(
                summary="Policy validation failed",
                reason="policy.rate_schedule contains non-numeric year or value",
                fix="Use integer-like years and numeric rate values in rate_schedule",
                invalid_fields=("policy.rate_schedule",),
            ) from None

    exemptions = tuple(raw.get("exemptions", []))
    thresholds = tuple(raw.get("thresholds", []))
    covered_categories = tuple(raw.get("covered_categories", []))

    if policy_type == PolicyType.CARBON_TAX:
        redistribution_type = ""
        income_weights: dict[str, float] = {}
        if "redistribution" in raw:
            redist = raw["redistribution"]
            if not isinstance(redist, dict):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.redistribution must be a mapping",
                    fix="Set redistribution as a YAML object with type/income_weights",
                    invalid_fields=("policy.redistribution",),
                )
            if "type" in redist:
                redistribution_type = str(redist["type"])
            if "income_weights" in redist:
                raw_weights = redist["income_weights"]
                if not isinstance(raw_weights, dict):
                    raise PortfolioValidationError(
                        summary="Policy validation failed",
                        reason="policy.redistribution.income_weights must be a mapping",
                        fix="Set income_weights as decile -> numeric weight pairs",
                        invalid_fields=("policy.redistribution.income_weights",),
                    )
                try:
                    for k, v in raw_weights.items():
                        income_weights[str(k)] = float(v)
                except (TypeError, ValueError):
                    raise PortfolioValidationError(
                        summary="Policy validation failed",
                        reason="policy.redistribution.income_weights has non-numeric values",
                        fix="Use numeric values for all redistribution income_weights",
                        invalid_fields=("policy.redistribution.income_weights",),
                    ) from None
        return CarbonTaxParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            redistribution_type=redistribution_type,
            income_weights=income_weights,
        )
    elif policy_type == PolicyType.SUBSIDY:
        eligible_categories = tuple(raw.get("eligible_categories", []))
        income_caps: dict[int, float] = {}
        if "income_caps" in raw:
            raw_caps = raw["income_caps"]
            if not isinstance(raw_caps, dict):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_caps must be a mapping",
                    fix="Set income_caps as a YAML object with numeric values",
                    invalid_fields=("policy.income_caps",),
                )
            try:
                for k, v in raw_caps.items():
                    income_caps[int(k)] = float(v)
            except (TypeError, ValueError):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_caps contains non-numeric year or value",
                    fix="Use integer-like years and numeric values in income_caps",
                    invalid_fields=("policy.income_caps",),
                ) from None
        return SubsidyParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            eligible_categories=eligible_categories,
            income_caps=income_caps,
        )
    elif policy_type == PolicyType.REBATE:
        rebate_type = str(raw.get("rebate_type", ""))
        rebate_weights: dict[str, float] = {}
        if "income_weights" in raw:
            raw_weights = raw["income_weights"]
            if not isinstance(raw_weights, dict):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_weights must be a mapping",
                    fix="Set income_weights as decile -> numeric weight pairs",
                    invalid_fields=("policy.income_weights",),
                )
            try:
                for k, v in raw_weights.items():
                    rebate_weights[str(k)] = float(v)
            except (TypeError, ValueError):
                raise PortfolioValidationError(
                    summary="Policy validation failed",
                    reason="policy.income_weights has non-numeric values",
                    fix="Use numeric values for all income_weights",
                    invalid_fields=("policy.income_weights",),
                ) from None
        return RebateParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            rebate_type=rebate_type,
            income_weights=rebate_weights,
        )
    elif policy_type == PolicyType.FEEBATE:
        pivot_point_set = "pivot_point" in raw
        fee_rate_set = "fee_rate" in raw
        rebate_rate_set = "rebate_rate" in raw
        try:
            pivot_point = float(raw.get("pivot_point", 0.0))
            fee_rate = float(raw.get("fee_rate", 0.0))
            rebate_rate = float(raw.get("rebate_rate", 0.0))
        except (TypeError, ValueError):
            raise PortfolioValidationError(
                summary="Policy validation failed",
                reason="feebate numeric fields must be numbers",
                fix="Use numeric values for pivot_point, fee_rate, and rebate_rate",
                invalid_fields=("policy",),
            ) from None
        return FeebateParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
            pivot_point=pivot_point,
            fee_rate=fee_rate,
            rebate_rate=rebate_rate,
            _pivot_point_set=pivot_point_set,
            _fee_rate_set=fee_rate_set,
            _rebate_rate_set=rebate_rate_set,
        )
    else:
        return PolicyParameters(
            rate_schedule=rate_schedule,
            exemptions=exemptions,
            thresholds=thresholds,
            covered_categories=covered_categories,
        )


def dump_portfolio(portfolio: PolicyPortfolio, path: Path | str) -> None:
    """Serialize portfolio to YAML file with canonical formatting.

    Args:
        portfolio: The portfolio to serialize
        path: Output file path
    """
    file_path = Path(path)
    data = portfolio_to_dict(portfolio)

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=True)


def load_portfolio(path: Path | str) -> PolicyPortfolio:
    """Load portfolio from YAML file.

    Args:
        path: Path to YAML file

    Returns:
        PolicyPortfolio instance

    Raises:
        PortfolioSerializationError: If file not found or invalid YAML
        PortfolioValidationError: If data is invalid
    """
    file_path = Path(path)

    if not file_path.exists():
        raise PortfolioSerializationError(
            summary="Portfolio load failed",
            reason=f"file was not found: {file_path}",
            fix="Provide an existing .yaml or .yml portfolio file path",
            file_path=file_path,
        )

    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise PortfolioSerializationError(
            summary="Portfolio load failed",
            reason=f"invalid YAML syntax: {exc}",
            fix="Fix the YAML syntax errors in the portfolio file",
            file_path=file_path,
        ) from None

    if not isinstance(data, dict):
        raise PortfolioValidationError(
            summary="Portfolio load failed",
            reason="portfolio file must contain a YAML mapping (dict)",
            fix="Ensure the file has top-level keys: name, version, policies",
            file_path=file_path,
        )

    portfolio = dict_to_portfolio(data)
    return portfolio


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 12-2-implement-portfolio-compatibility-validation-and-conflict-resolution
**Story File:** _bmad-output/implementation-artifacts/12-2-implement-portfolio-compatibility-validation-and-conflict-resolution.md
**Validated:** 2026-03-05
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 1 | 0 |
| ⚡ Enhancements | 3 | 0 |
| ✨ Optimizations | 0 | 0 |
| 🤖 LLM Optimizations | 1 | 0 |

**Overall Assessment:** MAJOR REWORK

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Story scope is too large for a single sprint. | INVEST (Small) | +3 |
| 🟠 IMPORTANT | AC1: Clarify "conflicting parameters" for SAME_POLICY_TYPE. | Acceptance Criteria | +1 |
| 🟠 IMPORTANT | AC3: Clarify "recorded in portfolio metadata". | Acceptance Criteria | +1 |
| 🟠 IMPORTANT | Add performance considerations for large policy definitions. | Technical Specification Disasters | +1 |
| 🟡 MINOR | Reduce redundant architectural mandates in Dev Notes for LLM efficiency. | LLM Optimization | +0.3 |
| 🟢 CLEAN PASS | 3 | | -1.5 |

### Evidence Score: 4.8

| Score | Verdict |
|-------|---------|
| **4.8** | **MAJOR REWORK** |

---

## 🎯 Ruthless Story Validation 12.2

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | Pass | 1/10 | Minor explicit dependency on Story 12.1's dataclass definitions. |
| **N**egotiable | Pass | 4/10 | Highly prescriptive, but potentially justifiable for deterministic conflict resolution. |
| **V**aluable | Pass | 1/10 | Clear value proposition: ensures coherent policy combinations and prevents unintended interactions. |
| **E**stimable | Pass | 1/10 | Granular tasks and detailed dev notes make the story highly estimable. |
| **S**mall | Fail | 7/10 | The scope, including multiple conflict types, resolution strategies, and immutability requirements, is likely too large for a single sprint. |
| **T**estable | Pass | 1/10 | Acceptance criteria are specific and measurable, and testing plans are comprehensive. |

### INVEST Violations

- **[7/10] Small:** The story encompasses defining new data structures, modifying an existing one, implementing complex detection logic for four types of conflicts, implementing resolution logic for five strategies, integrating this into loading, and writing comprehensive tests. This is a substantial amount of work for a single sprint, particularly given the project's strict adherence to determinism and immutable data structures.

### Acceptance Criteria Issues

- **Ambiguous Detail:** Clarify "conflicting parameters" in AC1.
  - *Quote:* "AC1: Conflict detection for same policy type — Given two policies of the same type in a portfolio (e.g., two carbon taxes), when validated, then a conflict is detected and reported with the exact policy names and conflicting parameters."
  - *Recommendation:* Specify that for `SAME_POLICY_TYPE` conflicts, the primary conflicting parameter is the `policy_type` itself, and potentially refer to the entire policy objects as conflicting in terms of their presence in the same portfolio.
- **Ambiguous Term:** Clarify "recorded in portfolio metadata" in AC3.
  - *Quote:* "AC3: Resolution strategy application — ...then the conflict is resolved according to the strategy and the resolution is recorded in portfolio metadata."
  - *Recommendation:* Explicitly state if "portfolio metadata" refers to appending to the existing `description` field (as implied by the `resolve_conflicts` pattern in Dev Notes) or if a new, dedicated structured field for conflict resolution records should be added to the `PolicyPortfolio` dataclass.

### Hidden Risks and Dependencies

✅ No hidden dependencies or blockers identified. Explicit dependencies on Story 12.1, `jsonschema`, and `logging` are well-documented.

### Estimation Reality-Check

**Assessment:** Underestimated

The detailed tasks (defining new data structures, adding fields, implementing four types of conflict detection, five resolution strategies, integration, and comprehensive testing with deterministic behavior and immutability) represent a significant workload. It is highly likely this story will extend beyond a typical sprint duration.

### Technical Alignment

**Status:** Well-aligned

✅ Story aligns with architecture.md patterns. The story thoroughly references and adheres to key architectural mandates from `project-context.md` and `architecture.md`, including:
- Mandatory use of frozen dataclasses and returning new instances upon modification.
- Preference for tuples over lists for immutable collections.
- Emphasis on determinism in conflict ordering and resolution.
- Consistent file structure and naming conventions.
- Proper exception taxonomy and import practices (`from __future__ import annotations`, `TYPE_CHECKING` guards, no wildcard imports).

### Evidence Score: 4.8 → MAJOR REWORK

---

## 🚨 Critical Issues (Must Fix)

These are essential requirements, security concerns, or blocking issues that could cause implementation disasters.

### 1. Story Scope is Too Large

**Impact:** Project schedule delays, potential for bugs due to rushed implementation, increased cognitive load on the developer, and reduced quality.
**Source:** INVEST (Small)

**Problem:**
The story currently encompasses a broad range of functionality:
- Defining new data structures (`Conflict`, `ConflictType`, `ResolutionStrategy`).
- Modifying an existing core data structure (`PolicyPortfolio` with `resolution_strategy`).
- Implementing complex conflict detection logic for four distinct types (`SAME_POLICY_TYPE`, `OVERLAPPING_CATEGORIES`, `OVERLAPPING_YEARS`, `PARAMETER_MISMATCH`).
- Implementing resolution logic for five strategies (`ERROR`, `SUM`, `FIRST_WINS`, `LAST_WINS`, `MAX`).
- Integrating validation into the loading process.
- Writing comprehensive tests for all combinations of conflict types and resolution strategies, ensuring deterministic behavior and immutable object handling.
This volume of work is substantial and challenging to complete within a single sprint while maintaining the project's high-quality standards.

**Recommended Fix:**
Split the story into smaller, more manageable units. Consider options such as:
1.  **Story 12.2a: Define Portfolio Conflict Structures & Detection:** Focus on defining `Conflict`, `ConflictType`, `ResolutionStrategy`, modifying `PolicyPortfolio`, and implementing `validate_compatibility()` for all conflict types (AC1, AC2, AC5 for detection).
2.  **Story 12.2b: Implement Portfolio Conflict Resolution:** Focus on implementing `resolve_conflicts()` for all strategies (AC3, AC4, AC5 for resolution) and integrating the validation into `load_portfolio()`.
Alternatively, prioritize a subset of conflict types and resolution strategies for this story, deferring less critical ones to future iterations.

---

## ⚡ Enhancement Opportunities (Should Add)

Additional guidance that would significantly help the developer avoid mistakes.

### 1. Clarify AC1: "conflicting parameters"

**Benefit:** Removes ambiguity for the developer and ensures precise understanding of conflict definition.
**Source:** Acceptance Criteria

**Current Gap:** The phrase "conflicting parameters" in AC1 is vague, especially for `SAME_POLICY_TYPE` conflicts. While the Dev Notes clarify that for this conflict type it refers to the `policy_type` itself, this detail is not explicit in the Acceptance Criteria.

**Suggested Addition:** Update AC1 to be more specific. For example: "AC1: Conflict detection for same policy type — Given two policies of the same type in a portfolio (e.g., two carbon taxes), when validated, then a conflict is detected and reported indicating the duplicate `policy_type` and the names/indices of the conflicting policies."

### 2. Clarify AC3: "recorded in portfolio metadata"

**Benefit:** Ensures clarity on how resolution details are stored, preventing inconsistent implementations.
**Source:** Acceptance Criteria

**Current Gap:** AC3 states that resolution should be "recorded in portfolio metadata," but the provided implementation pattern in Dev Notes suggests appending to the `description` field. This uses "metadata" loosely and could lead to confusion or inconsistent structured vs. unstructured recording.

**Suggested Addition:** Update AC3 to explicitly state the intended mechanism. For example: "AC3: Resolution strategy application — ...then the conflict is resolved according to the strategy, and the resolution details are appended to the portfolio's `description` field." Or, if a more structured approach is desired, "AC3: Resolution strategy application — ...then the conflict is resolved according to the strategy, and the resolution details are stored in a new structured `resolution_log: tuple[ConflictResolutionEntry, ...]` field on the `PolicyPortfolio`."

### 3. Add Performance Considerations for Large Policy Definitions

**Benefit:** Proactively identifies and addresses potential performance bottlenecks for complex policy scenarios.
**Source:** Technical Specification Disasters

**Current Gap:** The story does not discuss performance implications if `covered_categories` lists or `rate_schedule` dictionaries within `PolicyParameters` become very large (e.g., thousands of entries). While the overall job execution has performance targets, the impact of these specific internal operations is not explicitly mentioned.

**Suggested Addition:** Add a note in "Dev Notes" or "Critical Don't-Miss Rules" regarding performance. For example: "While `PolicyPortfolio` operations are generally expected to be fast, consider the performance implications if individual `PolicyConfig` objects contain extremely large `rate_schedule` dictionaries or `covered_categories` tuples. For this story, assume typical policy sizes (tens to hundreds of entries). If future use cases involve thousands of entries, performance profiling and potential optimizations for conflict detection/resolution loops may be required."

---

## ✨ Optimizations (Nice to Have)

✅ No additional optimizations identified.

---

## 🤖 LLM Optimization Improvements

### 1. Reduce Repetitive Architectural Mandates in Dev Notes

**Issue:** Verbosity
**Token Impact:** Medium

**Current:**
```
**Frozen dataclass is NON-NEGOTIABLE** — `Conflict` and all new types must use `@dataclass(frozen=True)`. Resolution functions return NEW PolicyPortfolio instances, never mutate existing ones [Source: project-context.md#architecture-framework-rules].
...
**Use `tuple` not `list`** — All ordered collections in conflict detection use `tuple` for immutability [Source: project-context.md#python-language-rules].
...
**Determinism is NON-NEGOTIABLE** — Conflict detection and resolution must be deterministic:
- Conflicts sorted by policy indices (ascending), then parameter name (alphabetical)
- Resolution produces identical results for identical inputs
- No random or unordered iteration (use sorted() where needed)
```

**Optimized:**
```
**Architectural Mandates:**
- All new types (e.g., `Conflict`) must be `@dataclass(frozen=True)`. Resolution functions MUST return NEW `PolicyPortfolio` instances, never mutate existing ones. (Refer to `project-context.md#architecture-framework-rules` for details.)
- Use `tuple` for all ordered, immutable collections (e.g., `policy_indices`, `conflicting_values`). (Refer to `project-context.md#python-language-rules`.)
- **Determinism is NON-NEGOTIABLE:** Conflict detection and resolution MUST be deterministic. Conflicts must be sorted (by policy indices then parameter name). Resolution must produce identical results for identical inputs.
```

**Rationale:** The original story reiterates fundamental architectural rules with full explanations several times. For an LLM agent, relying on cross-references to the `project-context.md` for the full rationale and only stating the specific application of the rule in the story saves tokens and reduces redundancy, making the document more concise while retaining clarity.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 95% |
| Architecture Alignment | 100% |
| Previous Story Integration | 100% |
| LLM Optimization Score | 80% |
| **Overall Quality Score** | **95%** |

### Disaster Prevention Assessment

- **Reinvention Prevention:** Pass. No obvious reinvention risks.
- **Technical Specification Disasters:** Minor Risk. Performance implications for extremely large policy data structures could be an issue if not considered.
- **File Structure Disasters:** Pass. File structure and naming align with project conventions.
- **Regression Disasters:** Pass. Explicit handling of additive changes and comprehensive testing plan mitigate regression risks.
- **Implementation Disasters:** Pass. Implementation details are robust and scope is well-defined.

### Competition Outcome

🏆 **Validator identified 5 improvements** that enhance the story context.

---

**Report Generated:** 2026-03-05
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 12-2-implement-portfolio-compatibility-validation-and-conflict-resolution - implement-portfolio-compatibility-validation-and-conflict-resolution  
**Story File:** [12-2-implement-portfolio-compatibility-validation-and-conflict-resolution.md](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/12-2-implement-portfolio-compatibility-validation-and-conflict-resolution.md)  
**Validated:** 2026-03-05  
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 5 | 0 |
| ⚡ Enhancements | 6 | 0 |
| ✨ Optimizations | 3 | 0 |
| 🤖 LLM Optimizations | 4 | 0 |

**Overall Assessment:** REJECT. Story 12.2 has core requirement contradictions, execution-scope leakage into Story 12.3 territory, and missing conflict semantics that make implementation non-deterministic and high-regression risk.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Conflict rules can mark valid bundles as conflicts (e.g., overlapping years across different policy types) | Story 12.2 AC2 + Task 3.4 | +3 |
| 🔴 CRITICAL | `sum`/`max` strategies are undefined across heterogeneous policy units (tax vs subsidy) | Story 12.2 AC3 + Resolution semantics | +3 |
| 🔴 CRITICAL | AC4 requires execution-time failure while execution is explicitly out-of-scope for this story | Story 12.2 AC4 + Scope boundaries | +3 |
| 🔴 CRITICAL | No formal mapping from “household attributes affected” to detectable fields; detection logic is proxy-based and under-specified | Story statement + Task 3 | +3 |
| 🟠 IMPORTANT | Resolution metadata target is ambiguous (“description or new metadata field”) and not test-contractual | Task 4.8 | +1 |
| 🟠 IMPORTANT | Multi-policy (>2) conflict precedence/merge order is unspecified | Task 3/4 | +1 |
| 🟠 IMPORTANT | `load_portfolio(validate=False)` behavior and lifecycle contract are incomplete | Task 5.2 | +1 |
| 🟠 IMPORTANT | Hidden dependency on Story 12.1 stabilization (known failing tests noted) is not surfaced as gate | Story 12.1 Dev Record + Story 12.2 status | +1 |
| 🟡 MINOR | Task duplication/noise (schema update repeated, verbose repeats) reduces implementer signal clarity | Task list + Dev Notes | +0.3 |
| 🟢 CLEAN PASS | Clear business value and epic alignment are present | Story statement + Epics FR43/FR44 | -0.5 |

### Evidence Score: 14.8

| Score | Verdict |
|-------|---------|
| **14.8** | **REJECT** |

---

## 🎯 Ruthless Story Validation 12.2

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | FAIL | 8/10 | AC4 depends on execution behavior implemented in Story 12.3; story cannot be fully validated independently. |
| **N**egotiable | PARTIAL | 5/10 | Several implementation details are over-prescriptive while core semantics remain undefined. |
| **V**aluable | PASS | 1/10 | Clear analyst value and direct alignment with EPIC-12 outcomes. |
| **E**stimable | FAIL | 7/10 | Ambiguous conflict semantics and missing attribute mapping prevent reliable estimation. |
| **S**mall | PARTIAL | 6/10 | Scope bundles model changes, schema, loader behavior, conflict engine, resolution engine, and full test suite. |
| **T**estable | FAIL | 8/10 | Key ACs are not objectively testable due to ambiguity and cross-story execution dependency. |

### INVEST Violations

- **[8/10] Independent:** Execution-time AC in a composition-layer story introduces hard dependency on Story 12.3.
- **[7/10] Estimable:** Conflict detection target (“same household attribute”) is undefined operationally.
- **[8/10] Testable:** AC3/AC4 cannot be consistently tested without explicit merge contracts and execution boundary.
- **[6/10] Small:** Story likely exceeds a single sprint unit unless split into detection vs resolution vs integration.
- **[5/10] Negotiable:** File-level prescription is high, but expected outcomes are still ambiguous.

### Acceptance Criteria Issues

- **Conflicting Criteria:** AC2 says carbon tax + subsidy should pass, while Task 3.4 requires conflict on overlapping `rate_schedule` years.
  Quote: "Detect `OVERLAPPING_YEARS` conflicts: overlapping years in rate_schedule dictionaries"
  Recommendation: Limit year-overlap conflicts to same policy dimension/type or define a compatibility matrix by policy pair.

- **Ambiguous Semantics:** AC3 allows `"sum"` / `"max"` without defining unit compatibility.
  Quote: "explicit resolution strategy ('sum', ... 'max')"
  Recommendation: Define strategy applicability matrix per `ConflictType` and per policy-type pair.

- **Out-of-Scope AC:** AC4 requires execution blocking, but story notes execution/orchestrator are out of scope.
  Quote: "when the portfolio is executed, then it fails before computation"
  Recommendation: Move execution-blocking acceptance to Story 12.3; keep 12.2 to pre-execution validation contract.

- **Underspecified Conflict Definition:** Story promise is "same household attributes" but implementation checks metadata fields only.
  Quote: "affect the same household attributes"
  Recommendation: Add explicit attribute-impact mapping source (template metadata or compare module contract).

- **Metadata Recording Not Testable:** AC3 requires recording resolution in metadata with no required structure.
  Quote: "recorded in portfolio metadata"
  Recommendation: Add explicit schema field (e.g., `resolution_log`) with deterministic format.

- **Determinism Incomplete:** AC5 asks deterministic output but does not define tie-breakers for equal indices/fields or 3+ policy conflicts.
  Quote: "deterministic ordering, stable output"
  Recommendation: Specify total ordering rules and multi-way merge precedence.

### Hidden Risks and Dependencies

- **Sequential Dependency:** Story 12.2 implicitly depends on Story 12.3 for execution-time behavior.
  Impact: Incomplete delivery despite “ready-for-dev” status.
  Mitigation: Split ACs by layer and reassign execution ACs to Story 12.3.

- **Baseline Stability Dependency:** Story 12.1 has unresolved test mismatches in its own record.
  Impact: 12.2 work may build on unstable interfaces/error contracts.
  Mitigation: Add explicit prerequisite gate: 12.1 tests green and API frozen.

- **Data Contract Dependency:** No formal policy-effect metadata exists for “same attribute” detection.
  Impact: Heuristic conflict engine causes false positives/negatives.
  Mitigation: Add required effect-surface contract to `PolicyConfig` or template metadata.

- **Schema Evolution Dependency:** Adding `resolution_strategy` with strict schema controls requires migration guidance.
  Impact: Existing portfolio files/tooling may diverge unexpectedly.
  Mitigation: Add backward-compat tests and migration notes in story ACs.

- **Observability Dependency:** Warning logging is required but format unspecified.
  Impact: Inconsistent logs, hard-to-debug conflicts.
  Mitigation: Require structured key=value logging fields in AC/tests.

### Estimation Reality-Check

**Assessment:** underestimated

The story combines domain modeling, conflict DSL semantics, deterministic merge rules, YAML/schema compatibility, loader behavior changes, and comprehensive tests. With undefined merge contracts, a 5-point estimate is optimistic unless split into two stories:
1) deterministic conflict detection contract,
2) resolution + loader integration.

### Technical Alignment

**Status:** Partial alignment with architecture; key semantic misalignments present.

- **Boundary Leakage:** Execution failure behavior belongs to orchestrator execution flow (Story 12.3), not only composition layer.
  Architecture Reference: [epics.md Story 12.3 dependencies](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/epics.md)
  Recommendation: Keep 12.2 as pre-exec composition validation API and return typed validation results.

- **Policy Compatibility Semantics Missing:** Architecture says composition validates compatibility, but story omits compatibility matrix/contract.
  Architecture Reference: [architecture.md - Policy Portfolio Layer](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/architecture.md)
  Recommendation: Add explicit compatibility spec per policy-type pair and parameter domain.

- **Determinism Risk:** Project context requires deterministic behavior; story lacks full deterministic tie-break contract.
  Architecture Reference: [project-context.md](/Users/lucas/Workspace/reformlab/_bmad-output/project-context.md)
  Recommendation: Add deterministic ordering AC for pair generation, field ordering, and metadata serialization.

### Evidence Score: 14.8 → REJECT

---

## 🚨 Critical Issues (Must Fix)

### 1. False-positive conflict model blocks valid portfolios

**Impact:** Legitimate policy bundles can be rejected.  
**Source:** Story 12.2 AC2, Task 3.4

**Problem:** Overlapping year keys across different policy types are treated as conflicts, which contradicts the non-conflicting carbon-tax+subsidy example.

**Recommended Fix:** Define conflict detection by policy-type compatibility and parameter dimension, not by raw `rate_schedule` key overlap alone.

### 2. Resolution strategies lack unit-safe semantics

**Impact:** Corrupt or nonsensical merged policies.  
**Source:** AC3 + Resolution Strategy Semantics

**Problem:** `sum`/`max` are allowed without defining when numeric values are commensurate.

**Recommended Fix:** Add a strategy applicability matrix: `(conflict_type, policy_type_pair, parameter_name) -> allowed strategies`.

### 3. AC4 is not implementable in this story’s scope

**Impact:** Story cannot be completed/tested independently.  
**Source:** AC4 + Scope boundaries

**Problem:** “Fails before computation when executed” requires orchestration runtime path outside this story.

**Recommended Fix:** Move execution blocking to Story 12.3 ACs; in 12.2 require `validate_compatibility` to produce blocking `PortfolioValidationError` contract.

### 4. “Same household attribute” is not operationalized

**Impact:** Ambiguous implementation and inconsistent behavior across developers.  
**Source:** Story statement + Task 3

**Problem:** No explicit source of truth maps policy parameters to affected household attributes.

**Recommended Fix:** Add required `affected_attributes` metadata on templates/policies and validate conflicts against that contract.

### 5. Resolution result persistence contract is undefined

**Impact:** Non-deterministic metadata, broken auditability, AC3 unverifiable.  
**Source:** Task 4.8

**Problem:** Story suggests “description or new metadata field” with no schema/test obligations.

**Recommended Fix:** Add a mandatory `resolution_log` schema field with deterministic structure and ordering; test round-trip and byte-stability.

---

## ⚡ Enhancement Opportunities (Should Add)

### 6. Add explicit compatibility matrix
**Benefit:** Removes ambiguity for detection/resolution behavior.  
**Source:** AC1-AC3  
**Current Gap:** No policy-pair rules.  
**Suggested Addition:** Add table for `carbon_tax/subsidy/rebate/feebate` compatibility by parameter.

### 7. Define multi-way conflict behavior
**Benefit:** Prevents divergent merges with 3+ policies.  
**Source:** Task 3/4  
**Current Gap:** Pairwise examples only.  
**Suggested Addition:** Specify grouping and precedence for conflict sets of cardinality >2.

### 8. Make error payload deterministic
**Benefit:** Stable tests and debuggability.  
**Source:** AC4  
**Current Gap:** “clear error” is subjective.  
**Suggested Addition:** Require fixed fields: `conflict_type`, `policy_names`, `parameter`, `strategy_suggestions`, sorted ordering.

### 9. Add backward compatibility AC for old YAML
**Benefit:** Safe adoption.  
**Source:** Task 2.4/2.5  
**Current Gap:** No explicit test for portfolios missing `resolution_strategy`.  
**Suggested Addition:** AC: old YAML loads with default `"error"` unchanged.

### 10. Add `validate=False` behavior test contract
**Benefit:** Prevents accidental eager validation regressions.  
**Source:** Task 5.2  
**Current Gap:** Parameter exists but behavior not test-specified.  
**Suggested Addition:** AC for skipped conflict detection and no warning/error emission.

### 11. Require structured warning logs
**Benefit:** Operational traceability and project-style compliance.  
**Source:** Task 5.4 + project context logging rule  
**Current Gap:** Warning format unspecified.  
**Suggested Addition:** Enforce `event=portfolio_conflicts strategy=... conflict_count=...`.

---

## ✨ Optimizations (Nice to Have)

### 12. Bound conflict detection complexity
**Value:** Better scaling with large portfolios.  
**Suggestion:** State expected complexity and deterministic iteration strategy upfront.

### 13. Reuse compiled JSON Schema validator
**Value:** Faster repeated loads/tests.  
**Suggestion:** Cache validator object in module scope.

### 14. Normalize policy names for diagnostics
**Value:** Cleaner errors and stable messages.  
**Suggestion:** If `name==""`, emit deterministic fallback `policy[{index}]`.

---

## 🤖 LLM Optimization Improvements

### 15. Clarify scope boundary sentence
**Issue:** Contradictory scope  
**Token Impact:** High (prevents wrong implementation branch)

**Current:**
```text
Given ... when the portfolio is executed, then it fails before computation ...
```

**Optimized:**
```text
In Story 12.2, unresolved conflicts must raise PortfolioValidationError during compatibility validation (pre-execution). Runtime enforcement is validated in Story 12.3.
```

**Rationale:** Removes cross-story ambiguity and makes AC testable now.

### 16. Replace vague conflict prose with decision table
**Issue:** Ambiguity  
**Token Impact:** High

**Current:**
```text
Detect ... overlapping categories/years/parameter mismatch
```

**Optimized:**
```text
Add table: [conflict_type, detection_rule, allowed_strategies, output_action].
```

**Rationale:** Compresses semantics into executable spec.

### 17. Eliminate duplicate schema tasks
**Issue:** Redundant instructions  
**Token Impact:** Medium

**Current:**
```text
Create schema file ... (Task 4.6) and Create schema file ... (Task 5.6)
```

**Optimized:**
```text
Single task: update/create portfolio.schema.json once; reference in serialization and validation tasks.
```

**Rationale:** Avoids duplicate implementation paths.

### 18. Promote deterministic ordering to explicit algorithm
**Issue:** Missing critical signal  
**Token Impact:** Medium

**Current:**
```text
Ensure deterministic conflict ordering...
```

**Optimized:**
```text
Sort key = (min(policy_indices), max(policy_indices), conflict_type.value, parameter_name, normalized_value_hash).
```

**Rationale:** Reduces interpretation drift across developers/agents.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 69% |
| Architecture Alignment | 71% |
| Previous Story Integration | 58% |
| LLM Optimization Score | 62% |
| **Overall Quality Score** | **65%** |

### Disaster Prevention Assessment

- **Reinvention Prevention:** AT RISK - no compatibility matrix, high chance of ad-hoc bespoke conflict logic.
- **Technical Specification:** FAIL - merge semantics and execution boundary are under-specified.
- **File Structure:** PASS - target modules/paths are mostly consistent with architecture.
- **Regression Risk:** HIGH - likely false-positive conflicts and behavior drift across loaders/execution.
- **Implementation Quality:** FAIL - ACs allow divergent “correct” implementations.

### Competition Outcome

🏆 **Validator identified 18 improvements** that materially strengthen story clarity, testability, and implementation safety.

---

**Report Generated:** 2026-03-05  
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-05</var>
<var name="description">Master synthesizes validator findings and applies changes to story file</var>
<var name="document_output_language">English</var>
<var name="epic_num">12</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/validate-story-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/validate-story-synthesis/instructions.xml</var>
<var name="name">validate-story-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" file_id="b5c6fe32" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: b5c6fe32</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>
<var name="session_id">d8c79f07-2f5c-43b3-a9e2-912b29cfd8cf</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="38e1067d">embedded in prompt, file id: 38e1067d</var>
<var name="story_id">12.2</var>
<var name="story_key">12-2-implement-portfolio-compatibility-validation-and-conflict-resolution</var>
<var name="story_num">2</var>
<var name="story_title">implement-portfolio-compatibility-validation-and-conflict-resolution</var>
<var name="template">False</var>
<var name="timestamp">20260305_2059</var>
<var name="user_name">Lucas</var>
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