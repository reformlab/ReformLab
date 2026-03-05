# Story 12.1: Define PolicyPortfolio dataclass and composition logic

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst,
I want to compose multiple individual policy templates into a named policy portfolio,
so that I can run simulations with bundled policies applied together and compare comprehensive policy packages.

## Acceptance Criteria

1. **AC1: Frozen dataclass composition** — Given 2+ individual `PolicyConfig` objects, when composed into a `PolicyPortfolio`, then the portfolio is a named, frozen dataclass containing all policies.
   
2. **AC2: Policy inspection** — Given a portfolio, when inspected, then it lists all constituent policies with their types and parameter summaries.

3. **AC3: YAML round-trip** — Given a portfolio, when serialized to YAML and reloaded, then the round-trip produces an identical object (save and reload produces identical object).

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
  - [ ] 2.2 Decide if `PolicyConfig` is an alias or a new dataclass
  - [ ] 2.3 If new dataclass, define with: `policy_type: PolicyType`, `policy: PolicyParameters`, optional `name: str`
  - [ ] 2.4 Add helper method to extract policy type and parameter summary
  - [ ] 2.5 Ensure `PolicyConfig` integrates with existing `BaselineScenario` and `ReformScenario`

- [ ] **Task 3: Implement portfolio inspection methods** (AC: #2)
  - [ ] 3.1 Add `list_policies() -> list[dict[str, Any]]` method
  - [ ] 3.2 Each policy dict includes: name, type, rate_schedule summary, key parameters
  - [ ] 3.3 Add `get_policy_by_type(policy_type: PolicyType) -> PolicyConfig | None`
  - [ ] 3.4 Add `has_policy_type(policy_type: PolicyType) -> bool`
  - [ ] 3.5 Ensure methods work with frozen dataclass (no mutation, return new values)

- [ ] **Task 4: Implement YAML serialization** (AC: #3)
  - [ ] 4.1 Create `composition.py` module in `portfolios/` directory
  - [ ] 4.2 Implement `portfolio_to_dict(portfolio: PolicyPortfolio) -> dict[str, Any]`
  - [ ] 4.3 Implement `dict_to_portfolio(data: dict[str, Any]) -> PolicyPortfolio`
  - [ ] 4.4 Add `dump_portfolio(portfolio: PolicyPortfolio, path: Path) -> None`
  - [ ] 4.5 Add `load_portfolio(path: Path) -> PolicyPortfolio`
  - [ ] 4.6 Define YAML schema with `version` field for future migrations
  - [ ] 4.7 Include `$schema` reference for IDE validation support

- [ ] **Task 5: Add validation and error handling** (AC: #1, #2, #3)
  - [ ] 5.1 Validate portfolio has at least 2 policies on construction
  - [ ] 5.2 Validate all policy configs have consistent year schedules (or decide if this is Story 12.2)
  - [ ] 5.3 Create `PortfolioError` exception in `exceptions.py`
  - [ ] 5.4 Add clear error messages for invalid portfolios (missing policies, duplicate policies, etc.)
  - [ ] 5.5 Validate YAML structure on load with field-level error messages

- [ ] **Task 6: Write comprehensive tests** (AC: #1, #2, #3)
  - [ ] 6.1 Create `tests/templates/portfolios/` directory
  - [ ] 6.2 Create `conftest.py` with portfolio fixtures
  - [ ] 6.3 Create `test_portfolio.py` for dataclass tests
  - [ ] 6.4 Create `test_composition.py` for YAML serialization tests
  - [ ] 6.5 Test frozen dataclass immutability
  - [ ] 6.6 Test inspection methods return correct summaries
  - [ ] 6.7 Test YAML round-trip produces identical objects
  - [ ] 6.8 Test error cases: <2 policies, invalid YAML, missing fields
  - [ ] 6.9 Achieve high test coverage (>90%)

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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reformlab.templates.schema import PolicyParameters

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

**Design decision needed:** Is `PolicyConfig`:
1. An alias for `PolicyParameters`? (simplest)
2. A new wrapper containing `PolicyParameters` + metadata? (more flexible)
3. A reference to `ScenarioTemplate`? (reuses existing structure)

**Recommendation:** Start with option 2 — a lightweight wrapper that allows naming individual policies within a portfolio and extracting summaries. This gives flexibility for future portfolio-specific metadata without modifying existing scenario templates.

### YAML Serialization Pattern

**Follow existing loader patterns** [Source: src/reformlab/templates/loader.py]:
- Schema version field: `version: "1.0"`
- `$schema` reference for IDE validation
- `load_portfolio(path: Path) -> PolicyPortfolio`
- `dump_portfolio(portfolio: PolicyPortfolio, path: Path) -> None`
- Clear `ScenarioError` or `PortfolioError` on validation failures

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
│   └── exceptions.py    ← PortfolioError (or add to existing exceptions.py)
```

**Update exports** in:
- `src/reformlab/templates/portfolios/__init__.py`
- `src/reformlab/templates/__init__.py` (add portfolio types to `__all__`)

### Integration with Existing Code

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
