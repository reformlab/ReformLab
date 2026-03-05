

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

