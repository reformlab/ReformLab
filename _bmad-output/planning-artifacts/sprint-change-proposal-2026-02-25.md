# Sprint Change Proposal — Strategic Pivot to OpenFisca-Based Platform

**Project:** Microsimulation
**Author:** Lucas
**Date:** 2026-02-25
**Change Scope:** Major — Architectural pivot affecting PRD, Architecture, and Backlog
**Status:** Approved and Applied

---

## Section 1: Issue Summary

### Problem Statement

The original architecture planned a custom microsimulation engine — parallel NumPy entity graph, AST-based formula compiler, sequential rule execution model, and custom policy engine — that would replicate capabilities OpenFisca already provides for tax-benefit calculations. Building this custom engine would consume months of development effort without adding differentiated value over OpenFisca.

### Context

This issue was identified during planning, before any implementation began. The architecture document already contained a "Strategic Direction Update (2026-02-24)" moving toward OpenFisca-first, but the document body still carried ~720 lines of legacy custom engine design, and the PRD and backlog still referenced custom engine concepts (formula language, entity graph internals, AST parsing).

### Evidence

- OpenFisca is mature and actively maintained for tax-benefit policy rules
- PolicyEngine demonstrates that behavioral responses can be layered on top of OpenFisca (proven pattern for Phase 2)
- No code has been written — this is the optimal time for a strategic pivot
- The product's core value is the dynamic orchestrator with vintage tracking, not a computation engine
- No existing open-source tool offers multi-year environmental policy projection with vintage tracking

---

## Section 2: Impact Analysis

### Epic Impact

| Epic | Impact | Details |
|---|---|---|
| EPIC-1 | **Simplify + Rename** | Renamed to "Computation Adapter and Data Layer." Adapter interface pattern replaces custom data contracts. Open-data ingestion added. SP reduced from 37 to 30. |
| EPIC-2 | Minor | Scenario templates unchanged. No structural impact. |
| EPIC-3 | **Elevate + Redesign** | Renamed to "Step-Pluggable Dynamic Orchestrator and Vintage Tracking." Now the product core. Step interface and registration added. ComputationAdapter integration explicit. SP increased from 37 to 39. |
| EPIC-4 | None | Indicators unchanged. |
| EPIC-5 | Minor | Manifests now track OpenFisca version + adapter version. No story changes. |
| EPIC-6 | None | Interfaces unchanged. |
| EPIC-7 | None | Quality gates unchanged. |

### Artifact Conflicts

| Artifact | Impact Level | Changes Required |
|---|---|---|
| **Architecture** | **Critical** | Delete ~720 lines of legacy engine design. Expand active blueprint with adapter pattern, step-pluggable orchestrator, subsystem redesign, Phase 2+ extension paths. |
| **PRD** | **Moderate** | Strengthen strategic direction update. Update API surface (remove entity graph/formula references). Update testing strategy. Update innovation areas (elevate orchestrator, add system dynamics bridge vision). |
| **Backlog** | **Moderate** | Rename EPIC-1 and EPIC-3. Rewrite EPIC-1 stories (adapter focus). Rewrite EPIC-3 stories (step-pluggable design). Update sprint plan for new story IDs. |
| **UX Design** | None | Partial document (steps 1-2 only), no engine dependencies. |

### Technical Impact

- **Removed complexity:** Custom formula compiler, AST parsing, entity graph internals, EntityArrays class, cross-entity resolution, formula whitelist, policy engine
- **Added design:** ComputationAdapter interface, step-pluggable orchestrator pipeline, open-data ingestion layer
- **Testing shift:** From YAML formula tests to adapter contract tests, orchestrator determinism tests, vintage transition regression tests
- **Phase 2 path:** Behavioral responses become a new orchestrator step (proven PolicyEngine pattern), not a custom engine feature

---

## Section 3: Recommended Approach

### Selected Path: Direct Adjustment

Modify existing epics and stories within the current plan structure. No code exists to roll back. No MVP scope change needed.

### Rationale

- **Zero implementation debt:** No code has been written — changes are purely to planning artifacts
- **Net simplification:** EPIC-1 reduces in scope (SP 37 → 30), freeing capacity
- **Strategic clarity:** Product identity shifts from "custom engine" to "dynamic orchestrator platform"
- **Future-proofing:** Adapter pattern and pluggable steps enable Phase 2 behavioral responses and Phase 3 system dynamics bridge without architectural changes
- **Timeline impact:** Neutral to positive — EPIC-1 simplifies, EPIC-3 gains one story but is better scoped

### Effort and Risk

- **Effort:** Low — document updates only, no code changes
- **Risk:** Low — pivot simplifies the architecture and reduces total implementation scope
- **Timeline:** No sprint plan changes needed beyond story ID renumbering

---

## Section 4: Detailed Change Proposals

### Proposal 1: Architecture — Delete Legacy Engine (APPROVED)

Delete everything from "## Legacy Design Notes" (line 137) to end of file (~720 lines). Removes: entity graph, formula compiler, AST parsing, policy engine, EntityArrays, implementation patterns, anti-patterns, enforcement guidelines.

### Proposal 2: Architecture — Expand Active Blueprint (APPROVED)

Replace skeleton blueprint with comprehensive design: adapter interface pattern (`ComputationAdapter` protocol), step-pluggable orchestrator (yearly loop with registered step pipeline), redesigned subsystems, Phase 2+ extension points (behavioral responses, system dynamics bridge).

### Proposal 3: PRD — Update Developer Tool Requirements (APPROVED)

Update Python API surface (remove entity graph/formula references, add adapter and orchestrator configuration). Update testing strategy (remove YAML formula tests, add adapter contract tests, orchestrator determinism tests, vintage regression tests).

### Proposal 4: PRD — Update Innovation & Competitive Positioning (APPROVED)

Elevate dynamic orchestrator to #1 innovation area. Reframe OpenFisca positioning around adapter pattern. Add system dynamics bridge as #5 strategic vision (Phase 3).

### Proposal 5: Backlog — Simplify EPIC-1 (APPROVED)

Rename to "Computation Adapter and Data Layer." BKL-101 defines adapter interface. BKL-102 merges CSV/Parquet. BKL-104 becomes open-data ingestion pipeline. SP reduced from 37 to 30.

### Proposal 6: Backlog — Redesign EPIC-3 (APPROVED)

Rename to "Step-Pluggable Dynamic Orchestrator and Vintage Tracking." Add BKL-302 (step interface), BKL-305 (adapter integration). Carry-forward and vintage framed as orchestrator steps. SP 37 → 39.

### Proposal 7: Backlog — Update Sprint Plan (APPROVED)

Update epic names in summary. Add BKL-302 to Sprint 2. Update Sprint 3 story IDs (BKL-303 to BKL-307).

### Proposal 8: PRD — Strengthen Strategic Direction (APPROVED)

Rewrite strategic direction update as positive product identity statement: orchestrator as core, adapter pattern, open-data-first, no custom engine.

---

## Section 5: Implementation Handoff

### Change Scope Classification: Minor

All changes are to planning artifacts only. No code exists. No backlog reorganization beyond the changes documented above. The development team (Lucas, solo developer with AI assistance) can implement these document updates directly.

### Handoff Plan

| Action | Owner | Priority |
|---|---|---|
| Apply Architecture changes (Proposals 1-2) | Dev (Lucas) | Immediate |
| Apply PRD changes (Proposals 3-4, 8) | Dev (Lucas) | Immediate |
| Apply Backlog changes (Proposals 5-7) | Dev (Lucas) | Immediate |
| Validate updated documents for internal consistency | QA review | After updates |

### Success Criteria

- Architecture document contains zero references to custom entity graph, formula compiler, or policy engine
- PRD strategic direction explicitly names the dynamic orchestrator as the core product
- Backlog EPIC-1 stories center on adapter interface and open-data pipeline
- Backlog EPIC-3 stories center on step-pluggable orchestrator design
- All 8 approved proposals are applied to their respective documents
- Sprint plan reflects updated story IDs and epic names
