# Epic 24 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 24-2 (2026-04-18)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | OpenFisca variable names left as "Developer TODO" | Moved TODO section to "OpenFisca Variable Names" and restructured as a prerequisite research requirement. The story now clearly states that variable name research must be completed before implementing translation functions, listing the known variable names to research. |
| critical | PolicyType enum uses UPPERCASE (CARBON_TAX), not lowercase strings | Removed all references to modifying PolicyType enum. The story no longer proposes adding vehicle_malus/energy_poverty_aid as enum values, since they are CustomPolicyTypes. |
| critical | vehicle_malus and energy_poverty_aid are CustomPolicyTypes, not enum values | Updated dispatch logic to use string keys instead of PolicyType enum keys. The translation now correctly handles both PolicyType enum members and CustomPolicyType objects by using string-based dispatch. |
| critical | PolicyParameters base class has no policy_type attribute | Changed to use `infer_policy_type()` from schema.py instead of `getattr(policy, "policy_type", None)`. This function correctly handles both PolicyType enum and CustomPolicyType objects. |
| critical | Excluded types reference non-existent values (PolicyType.housing, PolicyType.family_benefit) | Removed references to non-existent PolicyType.housing/family_benefit. Updated AC#5 to handle unsupported policy types generically. |
| critical | Missing policy_type field prevents dispatch from working | Used `infer_policy_type()` function which does not require a policy_type attribute on PolicyParameters. |
| critical | Normalization mapping does not include subsidy-family outputs | Added explicit task to extend `_DEFAULT_OUTPUT_MAPPING` in result_normalizer.py with mappings for montant_subvention, eligible_subvention, malus_ecologique, and aide_energie. |
| critical | PolicyTranslator protocol is overengineered and doesn't match domain patterns | Removed PolicyTranslator protocol. Changed to simple translation functions that return the appropriate output for the adapter. |
| critical | Missing non-regression AC for existing policies | Added AC#8: "Given existing carbon_tax, rebate, and feebate policies, when executed after this story's implementation, then they continue to execute without errors or behavioral changes (non-regression)." |
| critical | Story assumes dict-based translation path exists in adapter | Added "Translation Implementation Note" explaining that the exact translation output format depends on adapter behavior research. Changed AC#2 to focus on "adapter receives input compatible with existing adapter contract" rather than dict-specific wording. |
| critical | Field name spelling mismatch (emission_threshold vs emission_threshold) | Verified VehicleMalusParameters uses correct field name `emission_threshold` and used it consistently in the story. |
| high | AC#2 "same generic request shape" is undefined | Rewrote AC#2 to: "Given the live execution path, when translation completes, then the adapter receives input compatible with the existing adapter contract for any live run." |
| high | "Domain-owned translation" vs "computation/translator.py" placement unclear | Added "Translation Boundary Clarification" section explaining that translation is "domain-owned" in terms of understanding domain types, while technically placed in computation/translator.py for organization. |
| high | Test expectations don't match actual adapter behavior | Updated integration tests to focus on "executes through live path" and "results include expected outputs" rather than checking what the adapter "receives". Tests now use actual API endpoints rather than mocking adapter input. |
| high | Clarify domain computation relationship | Added "Domain Computation Relationship" section explaining the two execution paths (replay using domain compute() vs live using OpenFisca with translation). |
| medium | Story is over-prescriptive with implementation snippets | Reduced code-level pseudocode, focused on outcome-level contracts. Removed overly detailed code blocks that prescribed exact implementation, replaced with clearer descriptions of required behavior. |
| dismissed | "OpenFisca API adapter uses SimulationBuilder, not dict" | FALSE POSITIVE: This is partially valid but the story now acknowledges this by requiring research into the correct adapter input format. The critical issue is that the adapter's current implementation may not support custom policy injection at all, which the story now addresses through the "Translation Implementation Note" requiring adapter behavior research before implementing translation. |
| dismissed | "PolicyTranslator protocol uses @runtime_checkable but this is for structural duck-typing" | FALSE POSITIVE: This was a minor style point. The protocol has been removed entirely, which addresses the issue more comprehensively than just removing @runtime_checkable. |
| dismissed | "openfisca_api_adapter.py vs openfisca_adapter.py file reference inconsistency" | FALSE POSITIVE: Both files exist in the codebase. The precomputed adapter (openfisca_adapter.py) is in scope of "must not modify", and the live adapter (openfisca_api_adapter.py) is also in scope of "must not modify". The story correctly references both files under "Files NOT to Modify". |
| dismissed | "PolicyTranslator protocol conflates protocol with callable wrapper" | FALSE POSITIVE: Addressed by removing the protocol entirely. The story now uses simple functions, which is cleaner and matches domain patterns better than a class-based protocol. |

## Story 24-3 (2026-04-18)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `_to_computation_policy` signature change incompatible with actual implementation | Removed proposed signature change, instead use `dataclasses.replace()` to create translated config before calling existing function unchanged |
| critical | `_build_policy_config` cannot handle CustomTypePolicy - blocks main feature | Added complete CustomTypePolicy extension to portfolio routes section, including `get_policy_type()` fallback and parameter class registry lookup, added new task "Extend portfolio route to handle CustomTypePolicy policies (CRITICAL)" |
| high | AC4 ambiguity - "blocks or warns" without specifying behavior or layer | Changed AC4 to specify "blocks with 422 error before execution" and added runtime mode specificity (only applies to `runtime_mode=live`, bypassed for `runtime_mode=replay`) |
| high | AC3 "comparison surfaces continue to work" is vague and untestable | Rewrote AC3 to specify "comparison API endpoints return successful responses with normalized output columns for surfaced policy types" |
| high | Output column naming order undefined across AC5-AC7 | Added explicit column naming order specification to AC6 and Normalization section: "normalization first, then policy-type+index prefixing" with example (`subsidy_0_subsidy_amount`) |
| high | Missing CustomTypePolicy handling in portfolio routes is a fundamental blocker | Extended "Portfolio Route Runtime Availability Check" section with complete CustomTypePolicy support code, added new task for this work |
| medium | LIVE_READY_TYPES duplicated across multiple sections increases drift risk | Updated validation check to import `LIVE_READY_TYPES` from canonical source (`routes/templates.py`), removed duplicate definition |
| medium | AC5 output variables lack conditional specification | Updated AC5 to specify "for each policy type present" and added transformation example |
| medium | Missing integration test coverage for full orchestrator execution path | Added `TestPortfolioLiveExecution` class with full execution path tests |
| medium | Runtime availability validation lacks replay mode handling | Added `runtime_mode=replay` bypass specification to validation check docstring and added test case |
| low | Missing entry gate for Story 24.2 dependency | Added prerequisite note: "Story 24.2 must be merged and stable before starting this story" |
| low | AC7 lacks specific non-regression test | Added `test_duplicate_policy_type_prefixing_preserved` to non-regression test class |
| low | Task list doesn't reflect CustomTypePolicy work | Added new task "Extend portfolio route to handle CustomTypePolicy policies (CRITICAL)" with subtasks |
| low | Project structure notes incomplete | Updated to include CustomTypePolicy extension work |
| dismissed | Story scope too large (epic-sized) | FALSE POSITIVE: Story scope is appropriate - 7 tasks focused on single feature (portfolio execution for surfaced policies). Translation integration is necessary core work, not scope creep. |
| dismissed | Over-prescriptive pseudocode reduces negotiability | FALSE POSITIVE: Code examples are implementation guidance, not requirements. Developers can adapt patterns. The prescriptive detail helps prevent errors in complex integration points. |
| dismissed | INVEST criteria violations (Independent, Negotiable, Small, Testable) | FALSE POSITIVE: INVEST is a heuristic, not a strict checklist. Story has clear dependencies (Story 24.2), reasonable scope for translation integration work, and testable ACs after clarifications applied. |
| dismissed | PreflightRequest structure uncertain for validation check | FALSE POSITIVE: The `request.scenario.get("portfolioName")` pattern is consistent with existing validation checks in the codebase. No change needed. |

## Story 24-5 (2026-04-18)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | AC4 is non-testable and subjective | Rewrote AC4 to specify concrete deliverable artifacts (fixture module, example test class, smoke test) that enable future pack expansion |
| critical | AC1 "covers" is too vague and not estimable | Expanded AC1 into specific minimum test counts (at least 2 catalog tests, 2 portfolio tests, 2 execution tests, 2 comparison tests, 3 non-regression tests) |
| critical | Incorrect column name in example | Changed `assert "malus_amount"` to `assert "vehicle_malus"` with prefix handling to match normalized output contract |
| critical | Missing negative-path runtime availability tests | Added AC5 explicitly testing live_unavailable blocking (422) and replay mode bypass, plus new "Negative-Path Runtime Availability Tests" section in Dev Notes |
| high | Smoke test lacks executable contract | Added specific command `python examples/live_policy_catalog/surfaced_packs_smoke.py` with exit code 0 requirement to AC2 and task list |
| high | Fixture scope completely undefined | Replaced generic fixture task with specific fixtures (surfaced_subsidy_params, surfaced_vehicle_malus_params, surfaced_energy_poverty_aid_params, minimal_population, assert helper) |
| high | Documentation location ambiguous for Astro site | Added Astro Starlight format requirements with frontmatter, updated target path to `docs/src/content/docs/live-policy-catalog.mdx` |
| high | Frontend-backend contract task unclear ("type labels") | Clarified task to verify `type` field value (backend) and separated frontend mock verification task with specific file path |
| medium | No directory structure verification | Added new task "Verify and create required directory structure" as first task, checking tests/regression/, examples/live_policy_catalog/, and docs location |
| medium | Portfolio CRUD task duplicates existing tests | Clarified task to focus on surfaced pack specifics (CREATE operations for vehicle_malus, energy_poverty_aid) rather than generic CRUD already covered |
| low | No prerequisite gate in story header | Added "Prerequisites" section requiring Stories 24.3 and 24.4 to be `done` in sprint-status before starting |
| low | Missing test fixture reuse guidance | Added "Test Fixture Reuse" section with specific import patterns from existing conftest.py files |
| low | No guidance for optional OpenFisca dependency | Added "Test Execution Strategy" subsection to Non-Regression Requirements with pytest marks and MockAdapter guidance |
| dismissed | Subsidy `income_ceiling` field is incorrect | FALSE POSITIVE: Field name is correct per source code—`SubsidyParameters` uses `income_ceiling` as shown in translator validation logic (line 77 of translator.py: checks `if policy.income_ceiling <= 0`) |
| dismissed | Feebate "rebates, maluses" key fields are wrong | FALSE POSITIVE: Fields are valid per `FeebateParameters` schema; validator provided no contradictory evidence |
| dismissed | Story 24.3 status conflict across artifacts | FALSE POSITIVE: Sprint status file inconsistency is a process issue, not a story specification problem. Added prerequisite check to mitigate |
| dismissed | Reinvention risk—tests already exist | FALSE POSITIVE: Story explicitly mentions reusing existing fixtures and extending tests for surfaced pack specifics. Added fixture reuse guidance to reinforce this |
| dismissed | Scope too large (tests + fixtures + docs + smoke) | FALSE POSITIVE: Story is appropriately sized for Epic 24 closure work; all tasks are directly related to regression coverage. Implementation phases provide structure |
