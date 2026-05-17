# Epic 28 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 28-1 (2026-05-17)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | TS↔Python `referenceAlternativeId` nullability mismatch - frontend allows `null`, backend requires `str` | Changed Pydantic model to `str \| None = None` |
| critical | Short-circuit only checks `is False`, doesn't handle `None` or missing values | Changed to `if not investment_decisions_enabled:` |
| high | Type duplication between `workspace.ts` and `technology-sets.ts` violates DRY | Removed duplicate types, added import from workspace.ts |
| high | TechnologySet.domains is mutable dict despite frozen dataclass | Used MappingProxyType to enforce immutability |
| medium | Type guard `hasTechnologySet` doesn't validate structure | Added structural validation for version, domains, and required fields |
| dismissed | API error response reveals internal details (security vulnerability) | FALSE POSITIVE: The error message uses the project's standard `{what, why, fix}` pattern and only reveals domain names that are already public API contract (heating/vehicle). This is consistent with existing API patterns throughout the codebase (e.g., categories.py). Not a security issue. |
| dismissed | Redundant `domain` field in DomainTechnologySet | FALSE POSITIVE: The `domain` field is intentional and necessary for API responses - each domain object needs to be self-describing. The `to_api_dict()` method relies on it. This is a standard pattern for nested data structures, not redundancy. --- |
