# Story 13.1: Define custom template authoring API and registration

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a policy analyst or developer,
I want to define custom policy templates in Python and register them with the template system,
so that my custom policies participate in scenarios, portfolios, and orchestrator runs alongside built-in templates.

## Acceptance Criteria

1. **AC1: Custom PolicyParameters registration** — Given a Python class subclassing `PolicyParameters` (frozen dataclass), when registered with the template system via `register_policy_type()`, then `infer_policy_type()` resolves the custom class to its declared `PolicyType` and the class is usable in `BaselineScenario`, `ReformScenario`, `PolicyConfig`, and `PolicyPortfolio`.

2. **AC2: Custom PolicyType extension** — Given a custom policy type string not in the built-in `PolicyType` enum, when registered, then the system accepts it as a valid policy type for scenarios, portfolios, YAML loading, and orchestrator execution.

3. **AC3: Validation on registration** — Given a custom template with a missing required field (e.g., `rate_schedule` not present on the class), when registered, then a clear `TemplateError` identifies the missing field or signature mismatch. Given a duplicate policy type registration, then a clear error prevents accidental overwriting.

4. **AC4: YAML loading of custom templates** — Given a registered custom template, when used in a YAML scenario configuration with the custom `policy_type` string, then the YAML loader parses the policy fields and constructs the correct custom `PolicyParameters` subclass, and the scenario loads and executes like a built-in template.

5. **AC5: Portfolio participation** — Given a registered custom template, when wrapped in a `PolicyConfig` and added to a `PolicyPortfolio` alongside built-in templates, then portfolio validation, conflict detection, and orchestrator execution all work correctly.

## Tasks / Subtasks

- [ ] **Task 1: Extend PolicyType to support custom types** (AC: #2)
  - [ ] 1.1 Refactor `PolicyType` from `Enum` to a system that supports runtime-registered custom values (options: use a string-based type registry alongside the enum, or convert `PolicyType` to a string-backed extensible type)
  - [ ] 1.2 Ensure backward compatibility — existing `PolicyType.CARBON_TAX`, `.SUBSIDY`, `.REBATE`, `.FEEBATE` continue to work identically
  - [ ] 1.3 Add `register_policy_type(type_name: str) -> PolicyType` function to `schema.py` that creates and registers a new policy type value
  - [ ] 1.4 Add validation: `type_name` must be non-empty, lowercase, snake_case
  - [ ] 1.5 Add duplicate detection: registering an existing type_name raises `TemplateError`
  - [ ] 1.6 Ensure custom `PolicyType` values work with `PolicyType(value_string)` lookup

- [ ] **Task 2: Implement custom PolicyParameters registration** (AC: #1, #3)
  - [ ] 2.1 Add `register_custom_template(policy_type: PolicyType | str, parameters_class: type[PolicyParameters])` function to `schema.py`
  - [ ] 2.2 Validate that `parameters_class` is a frozen dataclass subclass of `PolicyParameters`
  - [ ] 2.3 Validate that `parameters_class` has a `rate_schedule` field (inherited from base)
  - [ ] 2.4 Register the mapping in `_PARAMETERS_TO_POLICY_TYPE` dict
  - [ ] 2.5 Ensure `infer_policy_type()` resolves custom classes correctly (isinstance check order: custom classes checked before base `PolicyParameters`)
  - [ ] 2.6 Add duplicate detection: re-registering same class or conflicting type raises `TemplateError`

- [ ] **Task 3: Extend YAML loader for custom policy types** (AC: #4)
  - [ ] 3.1 Modify `_validate_policy_type()` in `loader.py` to accept registered custom policy types (not just `_VALID_POLICY_TYPES` frozenset)
  - [ ] 3.2 Add a custom policy parser registry: `register_policy_parser(policy_type: str, parser: Callable[[Path, dict], PolicyParameters])`
  - [ ] 3.3 Modify `_parse_policy()` to dispatch to registered custom parsers for non-built-in types
  - [ ] 3.4 Provide a default parser for custom types that constructs the registered `PolicyParameters` subclass from the raw dict (using `_parse_generic_custom_policy()`)
  - [ ] 3.5 Modify `_policy_to_dict()` to handle custom `PolicyParameters` subclasses via `dataclasses.asdict()` fallback for unknown types
  - [ ] 3.6 Update `_VALID_POLICY_TYPES` to be dynamic (check registered types, not just frozenset)

- [ ] **Task 4: Extend portfolio composition for custom types** (AC: #5)
  - [ ] 4.1 Modify `dict_to_portfolio()` in `composition.py` to accept registered custom `policy_type` strings via `PolicyType(value)` lookup
  - [ ] 4.2 Modify `_dict_to_policy_parameters()` to dispatch to custom parsers or use the default generic parser for custom types
  - [ ] 4.3 Modify `_policy_parameters_to_dict()` to serialize custom `PolicyParameters` subclasses using `dataclasses.fields()` introspection
  - [ ] 4.4 Ensure `validate_compatibility()` works with custom types (no hardcoded built-in type assumptions)

- [ ] **Task 5: Extend orchestrator integration** (AC: #5)
  - [ ] 5.1 Verify `_validate_policy_type()` in `portfolio_step.py` works with custom `PolicyType` values (it uses `isinstance(policy_type, PolicyTypeEnum)` — must support extended types)
  - [ ] 5.2 Verify `_to_computation_policy()` works with custom `PolicyParameters` subclasses (it uses `asdict()` — should work by default)
  - [ ] 5.3 Add integration test: custom template in portfolio through orchestrator yearly loop

- [ ] **Task 6: Update module exports and public API** (AC: #1, #2)
  - [ ] 6.1 Export `register_policy_type`, `register_custom_template` from `src/reformlab/templates/schema.py`
  - [ ] 6.2 Export new functions from `src/reformlab/templates/__init__.py` and add to `__all__`
  - [ ] 6.3 If a custom parser registration function is added to `loader.py`, export it similarly
  - [ ] 6.4 Add module-level docstring updates explaining extensibility

- [ ] **Task 7: Write comprehensive tests** (AC: #1, #2, #3, #4, #5)
  - [ ] 7.1 Create `tests/templates/test_custom_templates.py`
  - [ ] 7.2 Test registration of a custom `PolicyParameters` subclass with a new policy type
  - [ ] 7.3 Test `infer_policy_type()` resolves custom classes correctly
  - [ ] 7.4 Test error on registering with missing required fields
  - [ ] 7.5 Test error on duplicate registration
  - [ ] 7.6 Test YAML loading of a custom template (write a fixture YAML, load it, verify correct class)
  - [ ] 7.7 Test YAML round-trip: dump custom template → reload → verify identical
  - [ ] 7.8 Test custom template in `PolicyConfig` and `PolicyPortfolio` construction
  - [ ] 7.9 Test portfolio `validate_compatibility()` with custom types
  - [ ] 7.10 Test portfolio YAML round-trip with custom types
  - [ ] 7.11 Test custom template through `PortfolioComputationStep` with `MockAdapter`
  - [ ] 7.12 Test `BaselineScenario` and `ReformScenario` with custom policy type
  - [ ] 7.13 Ensure all tests use `autouse` fixture or setup/teardown to clean up registered custom types between tests (registration is global state)
  - [ ] 7.14 Run `uv run ruff check src/ tests/` and `uv run mypy src/`
  - [ ] 7.15 Run `uv run pytest tests/ -x` to verify no regressions

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**Frozen dataclasses are NON-NEGOTIABLE:**
```python
from __future__ import annotations
from dataclasses import dataclass
from reformlab.templates.schema import PolicyParameters

@dataclass(frozen=True)
class VehicleMalusParameters(PolicyParameters):
    """Vehicle malus (penalty) for high-emission vehicles."""
    emission_threshold: float = 120.0  # gCO2/km
    malus_rate: float = 50.0  # EUR per gCO2/km above threshold
```

**Protocols, not ABCs** — No abstract base classes. `PolicyParameters` is a concrete frozen dataclass base, not an ABC. Custom templates subclass it following the same pattern as `CarbonTaxParameters`. [Source: docs/project-context.md#Python Language Rules]

**`from __future__ import annotations`** on every file. Use `if TYPE_CHECKING:` guards for type-only imports. [Source: docs/project-context.md#Python Language Rules]

**Subsystem-specific exceptions** — Use `TemplateError` from `src/reformlab/templates/exceptions.py` for registration errors. Never raise bare `Exception` or `ValueError`. [Source: docs/project-context.md#Python Language Rules]

### Existing Code Patterns to Follow

**Policy type inference pattern** — `_PARAMETERS_TO_POLICY_TYPE` dict in `schema.py:133-138` maps parameter classes to policy types. `infer_policy_type()` at `schema.py:141-157` uses `isinstance` checks for subclass safety. The registration API must add entries to this dict.

**Policy type resolution pattern** — `_resolve_policy_type()` at `schema.py:165-189` handles inference with optional explicit override. Custom types must flow through this unchanged.

**YAML loader dispatch pattern** — `_parse_policy()` at `loader.py:298-515` dispatches on `PolicyType` with an `if/elif` chain. The final `else` branch already returns a generic `PolicyParameters` for unknown types. Extend this to dispatch to registered custom parsers.

**YAML serializer pattern** — `_policy_to_dict()` at `loader.py:555-599` uses `isinstance` checks per built-in type. Add an `else` branch that uses `dataclasses.fields()` introspection for custom types.

**Portfolio composition pattern** — `_dict_to_policy_parameters()` at `composition.py:258-440` also dispatches on `PolicyType` with an `if/elif` chain ending in an error for unsupported types. Must be extended similarly to loader.

**Valid policy types validation** — `_VALID_POLICY_TYPES` at `loader.py:31` is a `frozenset` of built-in enum values. Must become dynamic to include registered custom types. Similarly, `_validate_policy_type()` at `loader.py:243-254` must accept custom types.

### Key Design Decisions

**1. PolicyType extensibility approach:**
The core challenge is that `PolicyType` is a Python `Enum`, which is not extensible at runtime. Options:
- **Option A (Recommended): Keep enum for built-ins, add parallel string-based registry.** `PolicyType` enum stays for backward compat. A new `_CUSTOM_POLICY_TYPES: dict[str, PolicyType-like]` stores custom types. Validation and lookup functions check both. This minimizes blast radius.
- **Option B: Convert PolicyType to a string-backed class** with predefined constants. More elegant but larger refactor with more regression risk.
- **Option C: Use `aenum` or similar** for extensible enums. Adds a dependency.

Recommendation: Option A. Create a lightweight `CustomPolicyType` wrapper or use string values for custom types, with a unified lookup function. The `PolicyType` enum stays as-is for built-in types. All code that does `PolicyType(value_string)` must be updated to use a unified `get_policy_type(value_string)` function that checks both the enum and the custom registry.

**2. Registration is process-global state:**
Custom registrations live in module-level dicts (`_PARAMETERS_TO_POLICY_TYPE`, `_CUSTOM_POLICY_TYPES`). Tests MUST clean up registrations after each test. Provide a `_reset_custom_registrations()` helper for test teardown (prefixed with underscore for internal use).

**3. YAML parsing for custom types:**
Two strategies:
- **Default generic parser:** Uses `dataclasses.fields()` to introspect the registered class and construct it from YAML dict keys. Handles `rate_schedule` conversion (string keys → int) automatically since it's inherited from `PolicyParameters`.
- **Custom parser override:** Allow registering a callable `(Path, dict[str, Any]) -> PolicyParameters` for types that need special parsing logic (e.g., nested structures like carbon tax's `redistribution` sub-dict).

### Source File Touchpoints

| File | Change Type | Purpose |
|------|-------------|---------|
| `src/reformlab/templates/schema.py` | **MODIFY** | Add `register_policy_type()`, `register_custom_template()`, `get_policy_type()`, `_reset_custom_registrations()` |
| `src/reformlab/templates/loader.py` | **MODIFY** | Extend `_validate_policy_type()`, `_parse_policy()`, `_policy_to_dict()` for custom types; add custom parser registry |
| `src/reformlab/templates/portfolios/composition.py` | **MODIFY** | Extend `_dict_to_policy_parameters()`, `_policy_parameters_to_dict()` for custom types |
| `src/reformlab/templates/portfolios/portfolio.py` | **VERIFY** | Confirm `PolicyConfig.__post_init__` works with custom types (uses `infer_policy_type()` — should work after registration) |
| `src/reformlab/templates/__init__.py` | **MODIFY** | Export new registration functions |
| `src/reformlab/orchestrator/portfolio_step.py` | **VERIFY** | Confirm `_validate_policy_type()` works with custom types |
| `tests/templates/test_custom_templates.py` | **CREATE** | Comprehensive test suite for custom template registration and usage |

### Project Structure Notes

- All template code lives under `src/reformlab/templates/`
- Tests mirror at `tests/templates/`
- No new directories needed — custom template registration is a feature of the existing template subsystem, not a new subsystem
- JSON Schema files at `src/reformlab/templates/schema/` — the `scenario-template.schema.json` has a hardcoded `policy_type` enum; consider whether to update it or document that custom types aren't validated by JSON Schema (IDE-level validation only)

### Cross-Story Dependencies

- **Depends on:** EPIC-2 (template schema — done), EPIC-10 (policy_type inference — done), EPIC-12 (portfolios — done)
- **Blocks:** Story 13.2 (vehicle malus template — will use registration API), Story 13.3 (energy poverty aid), Story 13.4 (portfolio validation + notebook)
- Stories 13.2 and 13.3 will be the first real consumers of this API

### Out of Scope Guardrails

- **Do NOT** create a plugin discovery mechanism (e.g., entry points, auto-scanning directories). Registration is explicit Python calls.
- **Do NOT** modify the `ComputationAdapter` protocol. Custom templates use the same adapter interface.
- **Do NOT** build a custom template CLI or GUI. This is a Python API story.
- **Do NOT** add new dependencies. Use stdlib `dataclasses` introspection for generic YAML parsing.
- **Do NOT** modify the orchestrator core loop (`runner.py`). Custom templates flow through the existing `PortfolioComputationStep` → `ComputationAdapter` pipeline.
- **Do NOT** create compute.py/compare.py modules for custom templates in this story. That is the template author's responsibility and demonstrated in Stories 13.2/13.3.

### Testing Standards

- **Mirror source structure:** Tests in `tests/templates/test_custom_templates.py`
- **Class-based grouping:** `TestCustomPolicyTypeRegistration`, `TestCustomParametersRegistration`, `TestCustomTemplateYAMLLoading`, `TestCustomTemplateInPortfolio`, `TestCustomTemplateOrchestrator`
- **Fixtures in conftest:** Use existing `tests/templates/conftest.py` fixtures; add custom template fixtures
- **Direct assertions:** Plain `assert`, `pytest.raises(TemplateError, match=...)` for errors
- **Global state cleanup:** Use `autouse` fixture or `yield` to clean up `_PARAMETERS_TO_POLICY_TYPE` and custom type registries after each test
- **MockAdapter for unit tests:** Use `MockAdapter` from existing test infrastructure for orchestrator integration tests
- **Coverage target:** >90% for new code in registration, parsing, and validation paths

### References

- [Source: `src/reformlab/templates/schema.py` — PolicyType enum, PolicyParameters base, infer_policy_type(), _PARAMETERS_TO_POLICY_TYPE dict]
- [Source: `src/reformlab/templates/loader.py` — _parse_policy(), _policy_to_dict(), _validate_policy_type(), _VALID_POLICY_TYPES]
- [Source: `src/reformlab/templates/portfolios/composition.py` — _dict_to_policy_parameters(), validate_compatibility()]
- [Source: `src/reformlab/templates/portfolios/portfolio.py` — PolicyConfig, PolicyPortfolio]
- [Source: `src/reformlab/orchestrator/portfolio_step.py` — PortfolioComputationStep, _validate_policy_type(), _to_computation_policy()]
- [Source: `src/reformlab/templates/__init__.py` — Public API exports]
- [Source: `docs/project-context.md` — Frozen dataclasses, Protocol pattern, exception hierarchy, coding standards]
- [Source: `docs/epics.md#Epic 13` — Story acceptance criteria and scope notes]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All 5 source files that need modification identified with exact line references
- Design decision documented: PolicyType extensibility via parallel string registry (Option A)
- Global state management pattern documented for test isolation
- Cross-story dependency chain mapped: 13.1 → 13.2/13.3 → 13.4

### File List
