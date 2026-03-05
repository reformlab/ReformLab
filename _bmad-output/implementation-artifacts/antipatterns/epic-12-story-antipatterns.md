# Epic 12 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 12-1 (2026-03-05)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Unlocked Core Type Contract (`PolicyConfig`) | Changed Task 2.2 from "Decide if `PolicyConfig` is an alias or a new dataclass" to "Create `PolicyConfig` as a new frozen dataclass (NOT an alias)". Removed design decision ambiguity. |
| critical | Missing Failure-Mode Acceptance Criteria | Added AC4 for validation error handling and AC5 for deterministic serialization. Now covers invalid inputs, error messages, and byte-identical output requirements. |
| critical | Scope Boundary Conflict with Story 12.2 | Changed Task 5.2 from ambiguous "or decide if this is Story 12.2" to explicit "OUT OF SCOPE: Cross-policy year schedule compatibility validation (deferred to future story)". Added dedicated scope boundaries section in Dev Notes. |
| critical | Determinism Not Operationalized | Added AC5 for deterministic serialization (byte-identical output). Updated AC3 to specify dataclass equality with order preservation. Added deterministic serialization requirements section to Dev Notes. |
| critical | Composition Logic Underspecified vs Architecture | Added explicit scope boundaries section clarifying what's IN SCOPE (data structure, serialization, basic validation) vs OUT OF SCOPE (compatibility checks, conflict resolution, orchestrator integration). Title is accurate for actual scope. |
| high | Explicit jsonschema usage for YAML validation | Updated Task 4.5 to "with jsonschema validation", Task 5.5 to "using `jsonschema` library", added deterministic serialization requirements section mentioning jsonschema. |
| high | Define Inspection Contract Precisely | Added concrete `get_summary()` method example in PolicyConfig code snippet with explicit return fields. |
| high | Explicit Schema Artifact Path | Added Task 5.6 to create schema file at `src/reformlab/templates/schema/portfolio.schema.json`, updated Task 4.6 to reference this path. |
| high | Clarify Exception Taxonomy | Added exception hierarchy example in File Structure section with `PortfolioError`, `PortfolioValidationError`, `PortfolioSerializationError` subclasses. |
| medium | Ensure `field` import in code snippets | Added `from dataclasses import dataclass, field` import to PolicyParameters hierarchy example. |
| medium | Add test coverage measurement scope/command | Changed Task 6.10 to explicit command: `uv run pytest tests/templates/portfolios/ --cov=src/reformlab/templates/portfolios --cov-report=term-missing`. |
