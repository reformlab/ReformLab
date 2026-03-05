# Story 12.1: Define PolicyPortfolio dataclass and composition logic

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want to compose multiple individual policy templates into a named policy portfolio,
so that I can run simulations with bundled policies applied together and compare comprehensive policy packages.

## Acceptance Criteria

1. **AC1: Frozen dataclass composition** — Given 2+ individual `PolicyConfig` objects, when composed into a `PolicyPortfolio`, then the portfolio is a named, frozen dataclass containing all policies in the order provided.
   
2. **AC2: Policy inspection** — Given a portfolio, when inspected, then it lists all constituent policies with their types and parameter summaries in deterministic order.

3. **AC3: YAML round-trip** — Given a portfolio, when serialized to YAML and reloaded, then the round-trip produces an identical object using dataclass equality, with preserved policy order and default field values.

4. **AC4: Validation error handling** — Given invalid portfolio inputs (fewer than 2 policies, invalid YAML structure, missing required fields), when construction or loading is attempted, then clear `PortfolioError` exceptions are raised with field-level error messages.

5. **AC5: Deterministic serialization** — Given two identical portfolios, when serialized to YAML, then the output is byte-for-byte identical (canonical ordering, stable key order, deterministic formatting).

## Tasks / Subtasks

- [ ] **Task 1: Define PolicyPortfolio frozen dataclass** (AC: #1)
  - [ ] 1.1 Create `src/reformlab/templates/portfolios/` directory structure
  - [ ] 1.2 Create `__init__.py` with module docstring
  - [ ] 1.3 Create `portfolio.py` with `PolicyPortfolio` frozen dataclass
  - [ ] 1.4 Define fields: `name: str`, `policies: tuple[PolicyConfig, ...]`, `version: str`, `description: str`
  - [ ] 1.5 Add `__post_init__` validation (at least 2 policies required)
  - [ ] 1.6 Add property methods: `policy_types`, `policy_count`, `policy_summaries`
  - [ ] 1.7 Add `__repr__` for notebook-friendly display

- [ ] **Task 2: Define PolicyConfig wrapper type** (AC: #1, #2)
  - [ ] 2.1 Analyze existing `PolicyParameters` and `ScenarioTemplate` structures
  - [ ] 2.2 Create `PolicyConfig` as a new frozen dataclass (NOT an alias)
  - [ ] 2.3 Define fields: `policy_type: PolicyType`, `policy: PolicyParameters`, `name: str = ""`
  - [ ] 2.4 Add `get_summary() -> dict[str, Any]` method to extract policy type and parameter summary
  - [ ] 2.5 Add `__post_init__` to validate `policy` matches declared `policy_type`
  - [ ] 2.6 Ensure `PolicyConfig` integrates with existing `BaselineScenario` and `ReformScenario`

- [ ] **Task 3: Implement portfolio inspection methods** (AC: #2)
  - [ ] 3.1 Add `list_policies() -> list[dict[str, Any]]` method
  - [ ] 3.2 Each policy dict includes: name, type, rate_schedule summary, key parameters
  - [ ] 3.3 Add `get_policy_by_type(policy_type: PolicyType) -> PolicyConfig | None`
  - [ ] 3.4 Add `has_policy_type(policy_type: PolicyType) -> bool`
  - [ ] 3.5 Ensure methods work with frozen dataclass (no mutation, return new values)

- [ ] **Task 4: Implement YAML serialization** (AC: #3, #5)
  - [ ] 4.1 Create `composition.py` module in `portfolios/` directory
  - [ ] 4.2 Implement `portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]` with deterministic key ordering
  - [ ] 4.3 Implement `dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio`
  - [ ] 4.4 Add `dump_portfolio(portfolio: PolicyPortfolio, path: Path) -> None` with canonical YAML formatting
  - [ ] 4.5 Add `load_portfolio(path: Path) -> PolicyPortfolio` with jsonschema validation
  - [ ] 4.6 Create schema file at `src/reformlab/templates/schema/portfolio.schema.json` with `version` field
  - [ ] 4.7 Include `$schema` reference in dumped YAML files for IDE validation support

- [ ] **Task 5: Add validation and error handling** (AC: #1, #2, #3, #4)
  - [ ] 5.1 Validate portfolio has at least 2 policies on construction
  - [ ] 5.2 OUT OF SCOPE: Cross-policy year schedule compatibility validation (deferred to future story)
  - [ ] 5.3 Create `PortfolioError` exception in `exceptions.py` with subclasses for validation vs serialization errors
  - [ ] 5.4 Add clear error messages for invalid portfolios (missing policies, missing required fields)
  - [ ] 5.5 Validate YAML structure on load with field-level error messages using `jsonschema` library
  - [ ] 5.6 Create schema file at `src/reformlab/templates/schema/portfolio.schema.json`

- [ ] **Task 6: Write comprehensive tests** (AC: #1, #2, #3, #4, #5)
  - [ ] 6.1 Create `tests/templates/portfolios/` directory
  - [ ] 6.2 Create `conftest.py` with portfolio fixtures
  - [ ] 6.3 Create `test_portfolio.py` for dataclass tests
  - [ ] 6.4 Create `test_composition.py` for YAML serialization tests
  - [ ] 6.5 Test frozen dataclass immutability
  - [ ] 6.6 Test inspection methods return correct summaries in deterministic order
  - [ ] 6.7 Test YAML round-trip produces identical objects using dataclass equality
  - [ ] 6.8 Test error cases: <2 policies raises PortfolioError, invalid YAML structure, missing required fields
  - [ ] 6.9 Test deterministic serialization: identical portfolios produce byte-identical YAML
  - [ ] 6.10 Run `uv run pytest tests/templates/portfolios/ --cov=src/reformlab/templates/portfolios --cov-report=term-missing` to verify >90% coverage

- [ ] **Task 7: Update module exports** (AC: #1, #2, #3)
  - [ ] 7.1 Update `src/reformlab/templates/portfolios/__init__.py` exports
  - [ ] 7.2 Update `src/reformlab/templates/__init__.py` to export portfolio types
  - [ ] 7.3 Ensure imports follow `from __future__ import annotations` pattern
  - [ ] 7.4 Use `TYPE_CHECKING` guards for type-only imports

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Frozen dataclass is NON-NEGOTIABLE** — All domain types in ReformLab use `@dataclass(frozen=True)`. This is a core architectural decision [Source: project-context.md#architecture-framework-rules].

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from reformlab.templates.schema import PolicyParameters, PolicyType

@dataclass(frozen=True)
class PolicyConfig:
    """Wrapper for policy parameters with metadata for portfolio composition."""
    policy_type: PolicyType
    policy: PolicyParameters
    name: str = ""
    
    def get_summary(self) -> dict[str, Any]:
        """Extract policy type and key parameter summary."""
        return {
            "name": self.name,
            "type": self.policy_type.value,
            "rate_schedule_years": sorted(self.policy.rate_schedule.keys()),
        }

@dataclass(frozen=True)
class PolicyPortfolio:
    """Named, versioned collection of policy configurations."""
    name: str
    policies: tuple[PolicyConfig, ...]  # tuple for immutability
    version: str = "1.0"
    description: str = ""
```

**Use `tuple` not `list`** — Function parameters and return types that are ordered-and-fixed use `tuple`, not `list` [Source: project-context.md#python-language-rules].

**No ABCs, use Protocols** — Interfaces are `Protocol` + `@runtime_checkable`, not abstract base classes [Source: project-context.md#python-language-rules].

### Existing Schema Analysis

**Current `PolicyParameters` hierarchy** [Source: src/reformlab/templates/schema.py]:
```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class PolicyParameters:
    """Base class for policy-specific parameters."""
    rate_schedule: dict[int, float]
    exemptions: tuple[dict[str, Any], ...] = ()
    thresholds: tuple[dict[str, Any], ...] = ()
    covered_categories: tuple[str, ...] = ()

@dataclass(frozen=True)
class CarbonTaxParameters(PolicyParameters):
    redistribution_type: str = ""
    income_weights: dict[str, float] = field(default_factory=dict)

# Similar: SubsidyParameters, RebateParameters, FeebateParameters
```

**Current `ScenarioTemplate` structure** [Source: src/reformlab/templates/schema.py:192-213]:
```python
@dataclass(frozen=True)
class ScenarioTemplate:
    """Base scenario template shape."""
    name: str
    year_schedule: YearSchedule
    policy: PolicyParameters
    policy_type: PolicyType | None = None  # Inferred if None
    description: str = ""
    version: str = "1.0"
    schema_ref: str = ""
```

**Design decision: `PolicyConfig` is a new frozen dataclass wrapper** — Option 2 from the list below is required. This allows naming individual policies within a portfolio and extracting summaries without modifying existing scenario templates. Aliases are NOT acceptable.

**Previous design options considered:**
1. An alias for `PolicyParameters`? (REJECTED - insufficient for portfolio needs)
2. A new wrapper containing `PolicyParameters` + metadata? (REQUIRED - provides needed flexibility)
3. A reference to `ScenarioTemplate`? (REJECTED - creates unnecessary coupling)

### YAML Serialization Pattern

**Follow existing loader patterns** [Source: src/reformlab/templates/loader.py]:
- Schema version field: `version: "1.0"`
- `$schema` reference for IDE validation
- `load_portfolio(path: Path) -> PolicyPortfolio`
- `dump_portfolio(portfolio: PolicyPortfolio, path: Path) -> None`
- Clear `ScenarioError` or `PortfolioError` on validation failures

**Deterministic serialization requirements** [Source: project-context.md#critical-dont-miss-rules]:
- Use `jsonschema` library for YAML validation on load (consistent with project stack)
- Sort dictionary keys alphabetically in output
- Use canonical YAML formatting (consistent indentation, no trailing spaces)
- Preserve policy order from tuple (do not reorder)
- Round-trip equality must include order preservation

**Example YAML structure** (proposed):
```yaml
$schema: "../schema/portfolio.schema.json"
version: "1.0"

name: "Green Transition 2030"
description: >
  Comprehensive climate policy package combining carbon pricing,
  vehicle incentives, and home renovation subsidies.

policies:
  - name: "Carbon Tax Component"
    policy_type: carbon_tax
    policy:
      rate_schedule:
        2026: 44.60
        2027: 50.00
        # ... (full policy parameters)
      redistribution_type: lump_sum
      
  - name: "EV Bonus"
    policy_type: subsidy
    policy:
      rate_schedule:
        2026: 5000.0
        2027: 5000.0
        # ... (full policy parameters)
      eligible_categories:
        - electric_vehicle
```

### Testing Standards

**Mirror source structure** [Source: project-context.md#testing-rules]:
```
tests/templates/portfolios/
├── __init__.py
├── conftest.py          ← fixtures: sample portfolios, policy configs
├── test_portfolio.py    ← dataclass construction, inspection methods
└── test_composition.py  ← YAML serialization, round-trip, validation
```

**Class-based test grouping** [Source: project-context.md]:
```python
class TestPolicyPortfolioConstruction:
    """Tests for portfolio creation and validation (AC #1)."""
    
class TestPolicyPortfolioInspection:
    """Tests for policy listing and summaries (AC #2)."""
    
class TestPolicyPortfolioYAML:
    """Tests for YAML serialization round-trip (AC #3)."""
```

**Direct assertions, no helpers** [Source: project-context.md]:
```python
def test_portfolio_requires_two_policies(self) -> None:
    """Portfolio with <2 policies raises clear error."""
    with pytest.raises(PortfolioError, match="at least 2 policies"):
        PolicyPortfolio(
            name="invalid",
            policies=(policy_1,),  # Only 1 policy
        )
```

### File Structure

**New directory** [Source: architecture.md#phase-2-architecture-extensions]:
```
src/reformlab/templates/
├── portfolios/
│   ├── __init__.py
│   ├── portfolio.py     ← PolicyPortfolio frozen dataclass
│   ├── composition.py   ← YAML serialization, validation
│   └── exceptions.py    ← PortfolioError hierarchy
```

**Exception taxonomy** — Create exception hierarchy consistent with project patterns:
```python
class PortfolioError(Exception):
    """Base exception for portfolio-related errors."""
    pass

class PortfolioValidationError(PortfolioError):
    """Raised when portfolio structure or policy configuration is invalid."""
    pass

class PortfolioSerializationError(PortfolioError):
    """Raised when YAML serialization or deserialization fails."""
    pass
```

**Update exports** in:
- `src/reformlab/templates/portfolios/__init__.py`
- `src/reformlab/templates/__init__.py` (add portfolio types to `__all__`)

### Integration with Existing Code

**Scope boundaries** — This story focuses on data structure and serialization ONLY:
- ✅ IN SCOPE: PolicyPortfolio frozen dataclass, PolicyConfig wrapper, YAML serialization, basic validation
- ❌ OUT OF SCOPE: Cross-policy year schedule compatibility checks (future story)
- ❌ OUT OF SCOPE: Orchestrator integration (Story 12.3)
- ❌ OUT OF SCOPE: Conflict resolution or policy compatibility logic

**Scenario Registry compatibility** — Portfolios will eventually be stored in the scenario registry alongside individual scenarios [Source: architecture.md#extension-policy-portfolio-layer]. Design `PolicyPortfolio` to be registry-friendly:
- Include `version` field for versioning
- Include `name` field for registry lookup
- Follow same immutability patterns as `BaselineScenario` and `ReformScenario`

**Orchestrator integration** — The orchestrator will receive a portfolio instead of a single policy [Source: architecture.md#extension-policy-portfolio-layer]. This is Story 12.3, not this story. Design `PolicyPortfolio` to expose the policies list in a way that's easy for the orchestrator to iterate.

### Project Structure Notes

- **Alignment with unified project structure:** New `portfolios/` subdirectory follows existing template subsystem pattern (similar to `carbon_tax/`, `subsidy/`, etc.)
- **Naming convention:** `portfolio.py` and `composition.py` follow `snake_case.py` convention
- **Module docstrings:** Every module needs a docstring explaining its role [Source: project-context.md#code-quality-style-rules]

### Critical Don't-Miss Rules

1. **Every file starts with `from __future__ import annotations`** — no exceptions [Source: project-context.md#python-language-rules]
2. **Use `if TYPE_CHECKING:` guards** for imports only needed for annotations [Source: project-context.md#python-language-rules]
3. **All domain types are frozen** — never add a mutable dataclass [Source: project-context.md#critical-dont-miss-rules]
4. **Determinism is non-negotiable** — portfolio construction and serialization must be deterministic [Source: project-context.md#critical-dont-miss-rules]
5. **No wildcard imports** — always import specific names [Source: project-context.md#code-quality-style-rules]

### References

**Architecture:**
- [Source: architecture.md#phase-2-architecture-extensions] — Policy Portfolio Layer design
- [Source: architecture.md#extension-policy-portfolio-layer] — Portfolio composition and orchestrator integration

**PRD:**
- [Source: prd.md#phase-2-policy-portfolios] — FR43-FR46 functional requirements
- [Source: prd.md#product-scope-post-mvp-features] — Phase 2 feature table

**Existing Code:**
- [Source: src/reformlab/templates/schema.py] — Existing `PolicyParameters`, `ScenarioTemplate` structures
- [Source: src/reformlab/templates/loader.py] — YAML serialization patterns
- [Source: src/reformlab/templates/registry.py] — Registry patterns for versioned artifacts

**Testing:**
- [Source: tests/templates/test_loader.py] — Example test patterns for YAML serialization
- [Source: tests/templates/test_registry.py] — Example test patterns for versioned artifacts

**Project Context:**
- [Source: project-context.md#architecture-framework-rules] — Frozen dataclasses, Protocols, step pipeline
- [Source: project-context.md#testing-rules] — Test structure, fixtures, assertions
- [Source: project-context.md#code-quality-style-rules] — ruff, mypy, naming conventions

## Dev Agent Record

### Agent Model Used

(To be filled during implementation)

### Debug Log References

(To be filled during implementation)

### Completion Notes List

(To be filled during implementation)

### File List

(To be filled during implementation)
