# Epic 24 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 24-3 (2026-04-18)

| Severity | Issue | Fix |
|----------|-------|-----|
| medium | Layer violation — `result_normalizer.py` imports `LIVE_READY_TYPES` from `server.routes.templates` | Replaced `from reformlab.server.routes.templates import LIVE_READY_TYPES` with locally-defined `_KNOWN_POLICY_TYPES` list containing all known policy type names sorted longest-first |
| dismissed | AC-4 violated — replay mode not bypassed in runtime availability check | FALSE POSITIVE: Already fixed at `validation.py:733` — `if request.runtime_mode == "replay":` early return exists |
| dismissed | Column prefix parsing breaks for underscore-containing policy types (vehicle_malus, energy_poverty_aid) | FALSE POSITIVE: Already fixed — code uses longest-match approach against known policy types, correctly handling multi-word types |
| dismissed | Silent bypass for None policy_type in validation | FALSE POSITIVE: Already fixed at `validation.py:784-790` — None policy_type is now flagged as error |
| dismissed | Route enforces live-ready at portfolio create/update, blocking replay portfolios | FALSE POSITIVE: Already fixed — runtime availability check removed from create/update path, enforced only at execution time via preflight validation |
| dismissed | DIP violation — route imports private `_CUSTOM_PARAMETERS_TO_POLICY_TYPE` | FALSE POSITIVE: Already fixed — code now uses public `list_custom_registrations()` API |
| dismissed | Error masking — `except Exception` in policy-type resolution | FALSE POSITIVE: Already fixed — code catches specific `TemplateError` exception |
| dismissed | Lying tests — translation tests don't assert translator invocation or original_error | FALSE POSITIVE: Tests DO verify `original_error` attribute (line 944-945) and there IS a success path test (`test_valid_subsidy_policy_translates_successfully` at line 947) |
| dismissed | Frontend regression — carbon_tax label/color removed from PortfolioTemplateBrowser | FALSE POSITIVE: Mock data consistently uses `"carbon-tax"` (hyphenated) format; `"carbon_tax"` (underscore) was a duplicate key never matched by actual data |
| dismissed | Destructive test fixture uses real registry path | FALSE POSITIVE: Valid design concern but LOW impact — fixture only targets specific test names and only runs during test execution, never in production |
| dismissed | Translator imports from template layer (architectural boundary violation) | FALSE POSITIVE: Deliberate Story 24.2 design decision — imports are lazy (inside function bodies) and the computation layer needs to validate domain-specific policy parameters |
| dismissed | Unused import `TemplateError` | FALSE POSITIVE: FALSE POSITIVE — `TemplateError` IS used on line 125 in the `except TemplateError:` clause |
| dismissed | Inconsistent error handling in portfolio_step.py — catches all Exceptions | FALSE POSITIVE: Intentional — adapter failures can be any exception type; wrapping them in `PortfolioComputationStepError` provides consistent error context |
| dismissed | Repeated imports in hot paths (infer_policy_type, apply_output_mapping_to_name) | FALSE POSITIVE: Valid observation but negligible performance impact — these are called per-policy (not per-row) and Python caches module imports after first load |
| dismissed | Passthrough types hardcoded in translator | FALSE POSITIVE: Design observation — unknown types get an explicit error via the translator lookup; future types require explicit registration which is intentional |
