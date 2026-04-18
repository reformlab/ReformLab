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
