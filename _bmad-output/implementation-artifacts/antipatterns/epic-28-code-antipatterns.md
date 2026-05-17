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

## Story 28-4 (2026-05-17)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Missing `Collapsible` wrapper breaks expand/collapse functionality | Added `<Collapsible>` wrapper around domain section content with `open` and `onOpenChange` props |
| critical | Template string syntax error - literal `{domainLabel}` won't interpolate | Changed to use `DOMAIN_LABELS[mismatch.domain]` for proper interpolation |
| critical | `canGoNext` null check doesn't catch `undefined` - legacy scenarios bypass gate | Changed strict `!== null` to loose `!= null` to catch both null and undefined |
| high | Dead imports (`useEffect`, `Separator`, `DomainTechnologySet`) | Removed unused imports from source file |
| high | `populationId` hardcoded `null` - population incumbent features non-functional | Updated comment to clearly indicate TODO status; removed unused prop from interface |
| high | `handleToggleAlternative` dead code with empty body | Removed stub function; alternatives always included per simplified AC-3 implementation |
| medium | Orphan-ASC validation is stub (always returns empty array) | Updated comment to clearly indicate stub status and requirements for implementation (needs tasteParameters schema extension) |
| medium | Placeholder tests with zero assertions | Removed unused variables and `as any` types; documented as deferred work |
| low | "Add to my set" only adds first unmatched value | Documented as known limitation; banner shows first unmatched value only |
| low | Review step missing Technology Set summary | Deferred as UX enhancement (not blocking) |
| dismissed | Task 3/4/5 marked incomplete but story says "ready-for-dev" | FALSE POSITIVE: Story status reflects planning phase, not implementation completion. Task checkboxes track implementation progress. |
| dismissed | Alternative reordering not implemented | FALSE POSITIVE: Story file shows this as optional - simplified implementation without reordering is acceptable for MVP. |
| dismissed | Household count hardcoded to 0 | FALSE POSITIVE: Population profile API doesn't provide per-value household counts. Requires backend API extension (out of scope). |
| dismissed | canRemove check allows removing reference | FALSE POSITIVE: FALSE POSITIVE. The check `!isReference` correctly prevents reference removal. |
| dismissed | SOLID violations | FALSE POSITIVE: Architectural concerns reflecting design tradeoffs, not bugs. |
| dismissed | Unnecessary re-renders | FALSE POSITIVE: Performance concern is theoretical; incumbents don't change during wizard interaction. |
| dismissed | Lying tests - wrong call signature | FALSE POSITIVE: Test helper accepts optional second parameter via default values. |
| dismissed | Story 28.3 Alternative ID mismatch | FALSE POSITIVE: FALSE POSITIVE. Story file explicitly documents this with mitigation strategy. |
