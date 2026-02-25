# Sprint Change Proposal — Backlog Readiness Corrections

**Project:** Microsimulation
**Author:** Lucas
**Date:** 2026-02-25
**Trigger:** Implementation Readiness Assessment — NEEDS WORK (12 issues, 4 categories)
**Change Scope:** Minor — Direct backlog adjustments, no scope or timeline change
**Status:** Approved and Applied

---

## Section 1: Issue Summary

### Problem Statement

The implementation readiness assessment run on 2026-02-25 evaluated the Phase 1 backlog against the PRD, Architecture, and UX artifacts. It returned **NEEDS WORK** with 12 findings across requirements traceability, UX alignment, epic/story quality, and delivery structure.

### Context

The backlog was generated as a first-pass translation of PRD requirements into epics and stories. It captured scope and dependencies well but skipped the refinement pass that adds story-level acceptance criteria, user-outcome framing, and a greenfield setup story. One functional requirement (FR31) was also missed in the mapping.

### Evidence

- Implementation Readiness Report (2026-02-25): 12 findings, 4 categories
- FR31 coverage gap: YAML/JSON workflow configuration has no backlog story despite being a core PRD promise
- Epic-level-only acceptance criteria: no story-level Given/When/Then ACs
- EPIC-7 framed as internal milestone, not user-value epic
- No greenfield setup story for Sprint 1 scaffold

### Assessment

No strategic, scope, or architectural changes are needed. This is a **planning quality pass** before Sprint 1 execution begins.

---

## Section 2: Impact Analysis

### Epic Impact

| Epic | Impact | Nature |
|------|--------|--------|
| EPIC-1 | Minor | Add greenfield setup story; add story-level ACs |
| EPIC-2 | Minor | Add FR31 story; add story-level ACs |
| EPIC-3 | Minor | Add story-level ACs |
| EPIC-4 | Minor | Add story-level ACs |
| EPIC-5 | Minor | Add story-level ACs |
| EPIC-6 | Minor | Add story-level ACs |
| EPIC-7 | Moderate | Reframe as user-value epic; add story-level ACs |

### Artifact Impact

| Artifact | Impact |
|----------|--------|
| PRD | None — PRD is complete and consistent |
| Architecture | None — architecture is aligned |
| UX Design Spec | Noted as lightweight but treated as separate improvement track |
| Backlog | Primary target — all edits apply here |

### Technical Impact

- No code changes (greenfield, nothing implemented yet)
- No dependency changes
- No priority shifts
- Two new backlog items (BKL-108, BKL-207) add ~8 SP to total Phase 1

---

## Section 3: Recommended Approach

### Selected Path: Direct Adjustment

Modify and add stories within the existing backlog structure.

### Rationale

- No implementation work has started — zero rollback risk
- PRD scope is unchanged — no MVP review needed
- All issues are additive (new stories, reframed text, added ACs)
- Effort: Low (backlog document edits only)
- Risk: Low (no dependency changes, no priority shifts)
- Timeline impact: None — this is pre-Sprint 1 cleanup

---

## Section 4: Detailed Change Proposals

### PROPOSAL 1: Add FR31 Story to EPIC-2

**Finding:** Critical — FR31 (YAML/JSON workflow configuration) has no backlog story.

**Artifact:** phase-1-implementation-backlog-2026-02-25.md — EPIC-2 table

**ADD row after BKL-206:**

```
| BKL-207 | Story | P0 | 5 | Implement YAML/JSON workflow configuration with schema validation | BKL-201 | FR31, NFR4, NFR20 |
```

**APPEND to EPIC-2 acceptance criteria:**

```
- Analyst can define and run a complete scenario workflow from a YAML configuration file without code changes.
- YAML schema is validated on load with field-level error messages.
- YAML configuration files are version-controlled and round-trip stable.
- CI tests validate shipped YAML examples against schema.
```

**Rationale:** FR31 is a core PRD promise tied to Sophie's journey (YAML policy-as-code) and underpins NFR20 (YAML examples tested in CI). Without it, analyst-friendly version-control workflow has no implementation path.

**Sprint plan impact:** Add BKL-207 to Sprint 2.

---

### PROPOSAL 2: Add Greenfield Setup Story to EPIC-1

**Finding:** Major — No project scaffold/tooling/CI story exists for Sprint 1.

**Artifact:** phase-1-implementation-backlog-2026-02-25.md — EPIC-1 table

**ADD row after BKL-107:**

```
| BKL-108 | Task | P0 | 3 | Set up project scaffold, dev environment, and CI smoke pipeline | - | NFR18, NFR19 |
```

**APPEND to EPIC-1 acceptance criteria:**

```
- Repository has pyproject.toml with dependency pinning, ruff linting, mypy type checking, and pytest configured.
- CI pipeline runs lint + unit tests on every push.
- Development environment is reproducible via uv from pyproject.toml.
- Project directory structure matches architecture subsystem layout.
```

**Rationale:** Every other story depends on a working project scaffold, CI, and tooling baseline. Without this, Sprint 1 starts with implicit setup work that bloats BKL-101.

**Sprint plan impact:** BKL-108 becomes the first item in Sprint 1 (before BKL-101).

---

### PROPOSAL 3: Reframe EPIC-7 as User-Value Epic

**Finding:** Critical — EPIC-7 is an internal delivery milestone, not a user-outcome epic.

**Artifact:** phase-1-implementation-backlog-2026-02-25.md — EPIC-7 section

**OLD:**
```
### EPIC-7 Quality Gates, Benchmarks, and Pilot Readiness
```

**NEW:**
```
### EPIC-7 Trusted Outputs and External Pilot Validation
```

**OLD story titles:**
```
| BKL-701 | Story | P0 | 5 | Build performance benchmark suite (100k households) | ...
| BKL-702 | Task | P0 | 3 | Add memory-limit guardrails and warning checks | ...
| BKL-704 | Story | P0 | 5 | Build external pilot package (example datasets, templates, docs) | ...
| BKL-705 | Task | P0 | 3 | Define Phase 1 exit checklist and pilot sign-off form | ...
```

**NEW story titles:**
```
| BKL-701 | Story | P0 | 5 | Analyst can verify simulation outputs against published benchmarks (100k households) | ...
| BKL-702 | Task | P0 | 3 | System warns analyst before exceeding memory limits on large populations | ...
| BKL-704 | Story | P0 | 5 | External pilot user can run complete carbon-tax workflow from shipped package | ...
| BKL-705 | Task | P0 | 3 | Define Phase 1 exit checklist and pilot sign-off criteria | ...
```

*Note: BKL-703 (CI quality gates) stays as-is — CI enforcement is inherently developer-facing.*

**OLD acceptance criteria:**
```
- Benchmark suite reports pass/fail against Phase 1 NFR targets.
- CI blocks merges on failing tests or coverage gates.
- Pilot package is runnable by at least one external user.
```

**NEW acceptance criteria:**
```
- Analyst can run benchmark suite and see pass/fail against Phase 1 NFR targets for their environment.
- CI blocks merges on failing tests or coverage gates.
- At least one external pilot user runs the carbon-tax workflow end-to-end and confirms result credibility.
- Pilot package includes example datasets, templates, and documentation sufficient for independent execution.
```

**Rationale:** Stories and acceptance criteria now express user outcomes rather than internal build tasks.

---

### PROPOSAL 4: Add Story-Level Acceptance Criteria to All P0 Stories

**Finding:** Critical — Acceptance criteria exist only at epic level, not at story level.

**Artifact:** phase-1-implementation-backlog-2026-02-25.md — After each epic's table.

**Format per story:**
```
**BKL-{id}: {title}**
- Given {precondition}, when {action}, then {expected outcome}.
- Given {error condition}, when {action}, then {error handling}.
```

**Scope:** Every P0 story gets 2-4 story-level acceptance criteria in Given/When/Then format, derived from epic-level ACs, decomposed to individual story scope, and augmented with error-path coverage.

**Implementation note:** This is the largest edit by volume. The full AC set should be generated as a dedicated pass after the structural changes (Proposals 1-3, 5-6) are applied to the backlog.

**Rationale:** Story-level ACs are essential for unambiguous Definition of Done during sprint execution.

---

### PROPOSAL 5: Add User-Outcome Statements to All Epics

**Finding:** Major — Epic framing is capability-centric, not user-outcome-centric.

**Artifact:** phase-1-implementation-backlog-2026-02-25.md — Each epic header section.

**ADD one line after each epic header:**

| Epic | User-Outcome Statement |
|------|----------------------|
| EPIC-1 | **User outcome:** Analyst can connect OpenFisca outputs and open datasets to the framework with validated data contracts. |
| EPIC-2 | **User outcome:** Analyst can define, version, and reuse environmental policy scenarios without writing code. |
| EPIC-3 | **User outcome:** Analyst can run multi-year projections with vintage tracking and get year-by-year panel results. |
| EPIC-4 | **User outcome:** Analyst can compute and compare distributional, welfare, and fiscal indicators across scenarios. |
| EPIC-5 | **User outcome:** Analyst can trust and reproduce any simulation run through immutable manifests and lineage tracking. |
| EPIC-6 | **User outcome:** User can operate the full analysis workflow from Python API, notebooks, or a no-code GUI. |
| EPIC-7 | **User outcome:** External pilot user can validate simulation credibility against published benchmarks and run the carbon-tax workflow independently. |

**Rationale:** User-outcome statements make each epic independently demonstrable and stakeholder-reviewable without changing scope.

---

### PROPOSAL 6: Update Sprint Delivery Plan

**Finding:** Derived from Proposals 1 and 2 — new stories need sprint assignments.

**Artifact:** phase-1-implementation-backlog-2026-02-25.md — "Suggested Phase 1 Delivery Plan" section.

**OLD:**
```
1. Sprint 1: BKL-101 to BKL-105, BKL-201, BKL-703.
2. Sprint 2: BKL-202 to BKL-205, BKL-301, BKL-302.
```

**NEW:**
```
1. Sprint 1: BKL-108, BKL-101 to BKL-105, BKL-201, BKL-703.
2. Sprint 2: BKL-202 to BKL-205, BKL-207, BKL-301, BKL-302.
```

**Rationale:** BKL-108 (project scaffold) goes first in Sprint 1. BKL-207 (FR31 YAML workflow config) slots into Sprint 2 alongside scenario template stories.

---

## Section 5: Issues Not Addressed (With Justification)

### SKIPPED: "UX specification needs implementation-ready fidelity" (Critical #4)

Expanding the UX spec into wireframes, task flows, and error-path behaviors is a separate UX design workstream. The backlog already includes BKL-604 (no-code GUI) which will drive UX detail when Sprint 5 begins. Fleshing out the full UX spec now — before EPIC-1 through EPIC-4 are built — would produce speculative designs disconnected from the actual API surface. Recommend running the UX design workflow before Sprint 5.

### SKIPPED: "UX-to-architecture traceability not explicit" (Major)

The architecture's subsystem layout already maps cleanly to UX surfaces. An explicit traceability table would be useful documentation but doesn't change any implementation decision. Can be added as part of the UX expansion pass before Sprint 5.

### SKIPPED: "Epic independence evidence is implicit" (Major)

Addressed by Proposal 5 (user-outcome statements per epic). Once each epic has an explicit user outcome, independence is demonstrable. A separate independence matrix would be redundant.

### SKIPPED: "Mixed Story/Task usage could dilute value tracking" (Minor)

The current Story/Task distinction is reasonable and standard. Tasks are correctly typed as technical enablement work. No change needed.

### SKIPPED: "FR-to-AC links not at story level" (Minor)

Addressed by Proposal 4 (story-level acceptance criteria). The PRD refs column already provides FR traceability per story.

### SKIPPED: "Standardized story templates would improve grooming velocity" (Minor)

Process improvement suggestion, not a backlog defect. Can be adopted as a convention during Sprint 1 grooming.

---

## Section 6: Implementation Handoff

### Change Scope Classification: Minor

All changes are direct backlog edits executable before Sprint 1 begins.

### Action Items

| # | Action | Owner | Priority |
|---|--------|-------|----------|
| 1 | Add BKL-108 (greenfield setup) to EPIC-1 and Sprint 1 | Dev | Immediate |
| 2 | Add BKL-207 (FR31 YAML config) to EPIC-2 and Sprint 2 | Dev | Immediate |
| 3 | Reframe EPIC-7 title and story titles per Proposal 3 | Dev | Immediate |
| 4 | Add user-outcome statements to all 7 epics per Proposal 5 | Dev | Immediate |
| 5 | Update Sprint 1 and Sprint 2 assignments per Proposal 6 | Dev | Immediate |
| 6 | Add story-level ACs for all P0 stories per Proposal 4 | Dev | Before each sprint starts |
| 7 | Expand UX spec to implementation-ready fidelity | Dev (UX workflow) | Before Sprint 5 |

### Success Criteria

- All P0 stories have story-level acceptance criteria in Given/When/Then format
- FR31 has explicit backlog coverage with testable ACs
- Every epic has a user-outcome statement
- EPIC-7 stories are framed as user outcomes
- Greenfield setup story exists and is first in Sprint 1
- Re-run of implementation readiness assessment returns READY status

---

**Proposal Date:** 2026-02-25
**Proposer:** Correct Course Workflow (BMAD)
