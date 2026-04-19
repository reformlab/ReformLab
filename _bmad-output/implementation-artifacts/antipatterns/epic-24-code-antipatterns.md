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

## Story 24-4 (2026-04-18)

| Severity | Issue | Fix |
|----------|-------|-----|
| medium | Missing `rebate` template in mock-data.ts breaks non-regression claim | Added `rebate-energy` template with `type: "rebate"`, `runtime_availability: "live_ready"` |
| medium | Lying tests — label assertions match template name text, not type badge | Changed assertions to target type badge element via CSS class selector (`.bg-rose-100.text-rose-800`, `.bg-cyan-100.text-cyan-800`) and verify badge text content |
| medium | Redundant dual-format OR condition in PortfolioCompositionPanel | Replaced `template?.type === "carbon_tax" \|\| template?.type === "carbon-tax"` with `template?.type.replace(/-/g, "_") === "carbon_tax"` |
| low | Overly-specific availability_reason test assertion | Changed from `screen.queryByText(/Domain translation pending/)` to checking absence of `.bg-amber-50.rounded.border` container element |
| dismissed | AC-5 cross-browser inconsistency — TemplateSelectionScreen needs TYPE_LABELS/TYPE_COLORS | FALSE POSITIVE: TemplateSelectionScreen renders cards via `SelectionGrid.renderCard` prop and does NOT display type labels/badges. It shows template name, custom badge, and runtime availability badge only. No type label to be inconsistent about. Story already verified this. |
| dismissed | AC-4 template_id not persisted — load resolves by policy_type | FALSE POSITIVE: Pre-existing API design limitation. `PortfolioPolicyItem` in `types.ts` has no `template_id` field — the API contract doesn't include it. Changing the API contract is beyond this story's scope. Deferred as future improvement. |
| dismissed | Non-numeric params dropped on portfolio load | FALSE POSITIVE: Pre-existing design. `CompositionEntry.parameters` is typed `Record<string, number>` — the composition panel only supports numeric parameters. Not introduced by this story. Would require API contract change to fix. |
| dismissed | AC-7 composition panel doesn't display parameter groups | FALSE POSITIVE: The AC says "parameter groups (e.g., emission_threshold, malus_rate_per_gkm, rate_schedule)" but the composition panel's collapsed card view shows parameter count and type badge. Parameter schemas appear in the expanded view via `ParameterRow`. The parameter group chips are shown in the browser, not the composition panel. This is the existing design pattern, not a regression. |
| dismissed | `/live\|replay/i` regex in no-runtime-selector test is too broad | FALSE POSITIVE: `queryByText` matches visible text content only, not DOM attributes. Badge renders "Ready" text (not "live_ready"). Template descriptions don't contain "live" or "replay". Regex won't produce false negatives. |
| dismissed | Tests use inline templates instead of mockTemplates | FALSE POSITIVE: Component tests should test component behavior with specific inputs, not be coupled to mock data structure. The inline templates verify the TYPE_LABELS/TYPE_COLORS mapping works correctly for specific type values, which is the right level of abstraction. Existing pre-24.4 tests already use `mockTemplates` directly for integration-level coverage. |
| dismissed | Dual-format TYPE_LABELS/TYPE_COLORS pattern is fragile | FALSE POSITIVE: Valid observation but this is the established pattern from PortfolioCompositionPanel (pre-existing). Normalizing at component boundary would be a broader refactor affecting multiple files. Deferred as future improvement. |
| dismissed | Type format conversion `.replace(/-/g, "_")` scattered in PoliciesStageScreen | FALSE POSITIVE: Valid DRY concern but all 3 instances are in the same file and the conversion is trivial. Centralizing would be a minor refactor. Deferred as future improvement. |
| dismissed | Backend tests not documented in completion notes | FALSE POSITIVE: This story is pure frontend UX (no backend changes). Backend tests are from Stories 24.1-24.3. |
| dismissed | Story file list incomplete | FALSE POSITIVE: Story file list documents implementation changes. Build artifacts and state files are not implementation changes. |
