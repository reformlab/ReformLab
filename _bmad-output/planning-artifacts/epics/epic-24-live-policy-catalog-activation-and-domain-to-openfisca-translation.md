# Epic 24: Live Policy Catalog Activation and Domain-to-OpenFisca Translation

**User outcome:** Analyst can discover and execute already-modeled subsidy and related policy packs from the catalog/API, with policy definitions remaining in the domain layer and live OpenFisca translation happening behind the scenes.

**Status:** backlog

**Builds on:** EPIC-2 (scenario templates and registry), EPIC-12 (policy portfolio model), EPIC-13 (additional policy templates and extensibility), EPIC-20 (workspace alignment), EPIC-23 (live runtime foundation)

**PRD Refs:** FR7, FR43-FR46, FR-RUNTIME-6, FR-RUNTIME-7

**Primary source documents:**
- `_bmad-output/planning-artifacts/prd.md`
- `_bmad-output/planning-artifacts/architecture.md`
- `_bmad-output/planning-artifacts/ux-design-specification.md` (Revision 4.1, dated 2026-04-01)
- `_bmad-output/planning-artifacts/sprint-change-proposal-2026-04-01.md`

| ID | Type | Pri | SP | Title | Status | PRD Refs |
|------|------|-----|----|-------|--------|----------|
| BKL-2401 | Story | P0 | 5 | Publish canonical catalog and API exposure for already-modeled hidden policy packs | backlog | FR7, FR-RUNTIME-7 |
| BKL-2402 | Story | P0 | 8 | Implement domain-layer live translation for subsidy-style policies without adapter-interface changes | backlog | FR46, FR-RUNTIME-6 |
| BKL-2403 | Story | P0 | 5 | Enable portfolio execution for surfaced subsidy and related live policy packs | backlog | FR43-FR45, FR46 |
| BKL-2404 | Story | P0 | 5 | Surface live-capable policy packs in workspace catalog flows without runtime-specific UX | backlog | FR7, FR43, FR44, FR-RUNTIME-7 |
| BKL-2405 | Story | P1 | 5 | Add regression coverage and examples for the expanded live policy catalog | backlog | FR44-FR46, FR-RUNTIME-6, FR-RUNTIME-7 |

## Epic-Level Acceptance Criteria

- Existing modeled policy packs that were previously hidden are exposed through the canonical catalog and API with clear availability metadata.
- Live translation for subsidy-style policies is implemented in the domain/policy layer and does not add subsidy logic to `ComputationAdapter` or the precomputed adapter.
- At least one surfaced subsidy-family pack executes successfully through the live runtime while preserving the normalized result contract from EPIC-23.
- Surfaced packs participate in portfolio validation, execution, and comparison flows without introducing runtime-specific UI branching.
- The first policy-expansion slice explicitly excludes housing and family-benefit reforms.

## Implementation Intent

- Reuse the existing pack and template registry utilities from EPIC-13 instead of creating a second catalog representation.
- Add a dedicated domain-to-live translation layer for subsidy-style policies so future policy expansion does not leak into adapter contracts.
- Surface only packs that are genuinely executable or intentionally marked unavailable; avoid exposing placeholders that the live runtime cannot honor.
- Keep catalog UX focused on policy discovery and configuration, not runtime education or engine toggles.
- Availability metadata should be stable and explicit enough to drive catalog rendering, validation, and save/load compatibility without hidden frontend logic.

## Scope Notes

- This epic assumes EPIC-23 has already established the live runtime default and normalized output contract.
- Housing and family-benefit reforms remain out of scope for this first expansion slice even if OpenFisca has related concepts.
- Existing hidden packs may include subsidy, rebate, feebate, vehicle-malus, and energy-poverty-aid variants; only the live-capable subset should be surfaced as executable.

---

## Story 24.1: Publish canonical catalog and API exposure for already-modeled hidden policy packs

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 23.4

Inventory the policy packs that already exist in the domain/template layer and expose them through the canonical product catalog and API. This story is about truthful discoverability: what exists, what is executable now, and what remains intentionally hidden.

**Implementation Notes:**

- Build catalog metadata from the existing template-pack registry utilities rather than hardcoding a second list in the frontend or API layer.
- Mark availability and execution readiness explicitly so hidden-but-supported packs can be surfaced without misleading users about runtime support.
- Expose `runtime_availability` (`live_ready` or `live_unavailable`) and `availability_reason` in the canonical catalog contract.
- Preserve deterministic identifiers so catalog items remain stable across API, workspace, and saved scenario references.

**Test Notes:**

- Add catalog listing tests covering visible, hidden, and newly surfaced packs.
- Add API contract tests for availability metadata and stable identifiers.
- Add regression tests ensuring existing visible packs keep their current identifiers and grouping.

### Acceptance Criteria

- Given the canonical catalog or API, when inspected, then existing modeled hidden packs appear with stable identifiers plus `runtime_availability` and `availability_reason` metadata.
- Given a pack that is not yet executable on the live path, when surfaced, then its status is explicit rather than silently failing at run time.
- Given existing visible packs, when the catalog is updated, then their identifiers and grouping remain stable.
- Given saved scenarios or portfolios that reference previously visible packs, when loaded, then they remain compatible after the catalog expansion.

---

## Story 24.2: Implement domain-layer live translation for subsidy-style policies without adapter-interface changes

**Status:** backlog
**Priority:** P0
**Estimate:** 8

**Dependencies:** Story 23.3, Story 24.1

Add the translation boundary that turns domain-authored subsidy-style policies into live OpenFisca execution inputs. This story must preserve the adapter contract: the adapter remains generic, while domain logic decides how subsidy-family policies are translated.

**Implementation Notes:**

- Introduce translator components or functions owned by the policy/domain layer that convert subsidy-style definitions into the live runtime request shape.
- Invoke translation between domain policy-set resolution and live run-request assembly so the adapter still receives a generic computation input rather than subsidy-aware instructions.
- Keep `ComputationAdapter` unchanged and avoid embedding subsidy semantics into the precomputed adapter.
- Start with subsidy-family policies already represented in the domain model and explicitly exclude housing and family-benefit reforms.

**Test Notes:**

- Add unit tests for domain-to-live translation of subsidy-style policy parameters.
- Add contract tests proving the adapter interface remains unchanged while translated payloads execute successfully.
- Add negative-path tests for unsupported subsidy variants or missing translation fields.

### Acceptance Criteria

- Given a subsidy-style policy defined in the domain layer, when prepared for execution, then it is translated into live OpenFisca inputs by domain-owned translation logic.
- Given the live execution path, when translation completes, then the adapter receives the same generic request shape it would for any other live run rather than a subsidy-specific adapter extension.
- Given the translation implementation, when reviewed, then no subsidy-specific behavior is added to `ComputationAdapter` or the precomputed adapter.
- Given an unsupported subsidy-domain feature, when translation is attempted, then the failure is explicit and actionable.
- Given the excluded housing or family-benefit domains, when requested in this slice, then they are not silently treated as supported.

---

## Story 24.3: Enable portfolio execution for surfaced subsidy and related live policy packs

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 24.1, Story 24.2

Move from discoverability to execution. Surfaced live-capable packs must work inside the existing portfolio model, including compatibility validation, runtime execution, and comparison against baseline or other portfolios.

**Implementation Notes:**

- Reuse existing portfolio composition and conflict-resolution rules from EPIC-12 and EPIC-13 where they already fit the surfaced pack types.
- Ensure translated subsidy-family policies and already-supported related packs can execute together through the live runtime foundation from EPIC-23.
- Preserve the normalized output contract so comparison and indicator flows remain untouched downstream.

**Test Notes:**

- Add portfolio integration tests covering mixed portfolios with carbon tax plus surfaced subsidy-family packs.
- Add compatibility-rule regression tests for conflict detection and resolution.
- Add execution tests proving normalized outputs remain valid after portfolio runs with surfaced packs.

### Acceptance Criteria

- Given a portfolio containing surfaced live-capable packs, when validated, then compatibility checks behave consistently with existing portfolio rules.
- Given a portfolio containing a surfaced subsidy-family pack, when executed, then it runs through the live runtime and produces normalized results.
- Given baseline-versus-portfolio comparison, when computed, then existing comparison surfaces continue to work without pack-specific branching.
- Given a pack marked unavailable for live execution, when added to a portfolio run, then the system blocks or warns before execution rather than failing deep in the runtime.

---

## Story 24.4: Surface live-capable policy packs in workspace catalog flows without runtime-specific UX

**Status:** backlog
**Priority:** P0
**Estimate:** 5

**Dependencies:** Story 24.1, Story 24.3

Expose the newly surfaced packs across the workspace where analysts actually choose and configure policies. The UX should communicate availability and category clearly, but it should not force users to understand runtime internals or choose an engine.

**Implementation Notes:**

- Reuse existing template-browser and composition-panel patterns from EPIC-20 and EPIC-22.
- Display policy type, readiness, and any availability constraints through catalog metadata rather than runtime-selector UI.
- Keep the default editing and portfolio-assembly experience consistent across old and newly surfaced packs.

**Test Notes:**

- Add frontend tests confirming surfaced packs appear in template browsers and composition panels with the correct labels.
- Add UX regression tests ensuring no runtime selector or adapter-specific jargon appears in the first-slice policy flows.
- Add persistence tests for scenarios and portfolios using newly surfaced packs.

### Acceptance Criteria

- Given the policy browser and composition flows, when rendered, then newly surfaced live-capable packs are available alongside existing packs.
- Given a surfaced pack with a readiness caveat, when shown to the user, then the caveat is visible without exposing backend runtime mechanics.
- Given the first-slice policy workflows, when reviewed, then no runtime or engine selector is introduced.
- Given a scenario or portfolio using a surfaced pack, when saved and reloaded, then the pack reference remains stable.

---

## Story 24.5: Add regression coverage and examples for the expanded live policy catalog

**Status:** backlog
**Priority:** P1
**Estimate:** 5

**Dependencies:** Story 24.3, Story 24.4

Close the policy-expansion epic by proving that the newly surfaced packs behave coherently across catalog, portfolio, execution, and comparison flows. Capture that behavior in regression tests and lightweight examples for future pack additions.

**Implementation Notes:**

- Extend the existing catalog, portfolio, and run regression suites rather than creating one-off tests per pack.
- Add lightweight examples that demonstrate surfaced subsidy-family execution through the live runtime and normalized results.
- Document the current supported live policy catalog so future additions have a clear baseline.

**Test Notes:**

- Add end-to-end or integration coverage for selecting a surfaced pack, running it live, and comparing results.
- Add regression tests for portfolio save/load and scenario persistence with surfaced pack identifiers.
- Add example smoke tests for any shipped sample configurations that demonstrate surfaced packs.

### Acceptance Criteria

- Given the automated test suite, when it runs, then it covers catalog exposure, portfolio validation, live execution, and comparison for surfaced packs.
- Given shipped examples or smoke configs, when executed, then they demonstrate at least one surfaced subsidy-family pack running through the live path successfully.
- Given the supported policy catalog documentation, when reviewed, then it matches the packs actually exposed and executable in the product.
- Given future pack expansion work, when planned, then the added tests and examples provide a reusable baseline rather than a one-off demo.
