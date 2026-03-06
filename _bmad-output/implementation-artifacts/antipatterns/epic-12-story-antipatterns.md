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

## Story 12-2 (2026-03-05)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | AC4 execution-time language contradicts scope boundaries | Changed AC4 from "when the portfolio is executed, then it fails before computation" to "when the portfolio is loaded with validation enabled, then `load_portfolio()` raises `PortfolioValidationError`". Also updated scope boundaries section to clarify validation-time vs execution-time behavior. |
| high | AC1 "conflicting parameters" is ambiguous for SAME_POLICY_TYPE | Changed AC1 from "reported with the exact policy names and conflicting parameters" to "reported with the exact policy names/indices and the duplicate `policy_type` as the conflicting parameter". |
| high | Task 4.8/AC3 "metadata" recording is ambiguous | Changed AC3 from "recorded in portfolio metadata" to "appended to the portfolio's `description` field with a deterministic format". Changed Task 4.8 from "Record resolution metadata in description or new metadata field" to "Record resolution metadata by appending to description field: 'Resolved {count} conflicts using '{strategy}' strategy.'" |
| medium | Story scope may be large | Acknowledged in synthesis but determined manageable due to granular tasks and comprehensive Dev Notes. Added performance considerations section to address scaling concerns. |
| medium | "Same household attribute" not fully operationalized | Added clarification in Story section: "This story uses metadata-based proxies (rate_schedule years, covered_categories, policy_type) to detect potential conflicts. These proxies identify overlapping policy effects without requiring explicit household-attribute mapping." |
| medium | Multi-way (3+ policy) conflict behavior undefined | Added new section "Multi-policy conflicts (3+ policies)" in Dev Notes explaining pairwise conflict generation and resolution application across all conflicts. |
| medium | Error payload determinism could be more explicit | Added new section "Error Message Determinism" specifying structured error fields, sorting rules, and byte-identical guarantees for testability. |
| medium | Backward compatibility for portfolios without resolution_strategy | Added new AC6: "Given a portfolio YAML file without a `resolution_strategy` field (from Story 12.1), when loaded, then it defaults to 'error' strategy and behaves identically to portfolios created in Story 12.1." Added test task 6.15. |
| medium | validate=False behavior needs test | Added test task 6.16: "Test validate=False parameter skips conflict detection and emits no warnings/errors." |
| medium | Warning log format should follow project standards | Updated Task 5.4 from "log warning with conflict summary" to "log warning with structured format: `event=portfolio_conflicts strategy=<strategy> conflict_count=<n> portfolio=<name>`". Added test task 6.17. |
| low | Performance considerations for large policy definitions | Added new section "Performance Considerations" with expected portfolio sizes, complexity analysis (O(n²)), and future optimization notes for 50+ policies or 1000+ rate_schedule entries. |

## Story 12-3 (2026-03-06)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | AC5 error contract missing `policy_name`**: AC5 explicitly requires "index, **name**, type" in failure context, but Task 1.4 error class only had `policy_index`, `policy_type` (no `policy_name`). Task 5.2 error format and Test 7.8 assertions also omitted it. | Added `policy_name` to Task 1.4, Task 5.2, and Test 7.8. |
| critical | Merge row-index fallback violates fail-loud data-contract rule**: Task 4.3 originally said "use row-index alignment as fallback" when `household_id` is missing. Verified against `project-context.md`: "Data contracts fail loudly — contract validation at ingestion boundaries is field-level and blocking; never silently coerce or drop data." The panel.py fallback (line 233-235) is designed for single-policy output display, NOT for cross-policy merging where silent row alignment risks merging different households. | Changed Task 4.3 to require `household_id` and raise `PortfolioComputationStepError` if missing. |
| high | Missing explicit dependency on Story 12.1/12.2**: Story consumed `PolicyPortfolio` and `PolicyConfig` from Story 12.1 and assumed conflict resolution from Story 12.2 but never declared these dependencies. | Added `Dependencies:` line after Status header. |
| high | Merged `ComputationResult` fields underspecified**: Task 3.8 only said "create a single `ComputationResult` with the merged output table" without specifying `adapter_version`, `period`, `metadata`, or `entity_tables`. Verified that `ComputationResult` has 5 required/optional fields. | Expanded Task 3.8 with explicit values for all `ComputationResult` fields. |
| medium | Task 2.3 "non-empty" vs >=2 inconsistency**: Task 2.3 said "non-empty" but `PolicyPortfolio.__post_init__` enforces `len(policies) < 2`. Defensive check should match the actual invariant. | Changed to "at least 2 entries" with reference to the >=2 invariant. |
| medium | Brittle line-number references**: References to "line 342-346" (runner.py) and "line 233-235" (panel.py) are fragile. | Replaced with behavior-based references (`_execute_step()`, `from_orchestrator_result()`). |
