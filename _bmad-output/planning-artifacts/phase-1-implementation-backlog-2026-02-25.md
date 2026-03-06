---
title: Phase 1 Implementation Backlog
project: ReformLab
date: 2026-02-25
source_documents:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
status: ready
---

# Phase 1 Implementation Backlog (OpenFisca-First)

## Scope Baseline

This backlog is derived from:

- PRD Phase 1 must-have capabilities and FR1-FR35, NFR1-NFR21.
- Architecture active blueprint and delivery sequence (OpenFisca adapter -> templates -> dynamic/vintage -> indicators/governance -> interfaces).

Out of scope in Phase 1:

- Endogenous market-clearing.
- Physical system feedback loops.
- Full behavioral equilibrium.
- Public-facing election app.

## Backlog Conventions

- Priority: `P0` (must ship in Phase 1), `P1` (ship if capacity allows after P0 complete).
- Size: story points (`SP`) using a rough Fibonacci scale (1, 2, 3, 5, 8, 13).
- Item types: `Story`, `Task`, `Spike`.
- A story is "done" only when acceptance criteria pass and tests are in CI.

## Phase 1 Epics

All epic definitions, story tables, and acceptance criteria live in [epics.md](epics.md).

Phase 1 covers EPIC-1 through EPIC-7. EPIC-8 and EPIC-9 were added post-Phase-1.

## Story Dependency Graph

Story dependencies within each epic (read left to right):

```text
EPIC-1: BKL-108 ──────────────────────────────────────
         BKL-101 → BKL-102 → BKL-104
         BKL-101 → BKL-103 → BKL-105
         BKL-101 → BKL-106
         BKL-101 → BKL-107

EPIC-2: BKL-103 → BKL-201 → BKL-202
                   BKL-201 → BKL-203
                   BKL-201 → BKL-204 → BKL-205
                                BKL-204 → BKL-206
                   BKL-201 → BKL-207

EPIC-3: BKL-202, BKL-203 → BKL-301 → BKL-302 → BKL-303 → BKL-304
                             BKL-301 → BKL-306
         BKL-301, BKL-101 → BKL-305
                             BKL-304 → BKL-307

EPIC-4: BKL-306 → BKL-401 → BKL-402 → BKL-405
                   BKL-401 → BKL-403 → BKL-405
                   BKL-401 → BKL-404 → BKL-405
                                        BKL-405 → BKL-406

EPIC-5: BKL-204 → BKL-501 → BKL-502 → BKL-506
                   BKL-501, BKL-301 → BKL-503 → BKL-505
                   BKL-501 → BKL-504

EPIC-6: BKL-301, BKL-405, BKL-501 → BKL-601 → BKL-602
                                      BKL-601 → BKL-603
                                      BKL-601, BKL-604a → BKL-604b → BKL-606
                              BKL-405, BKL-604b → BKL-605

EPIC-7: BKL-301, BKL-401 → BKL-701 → BKL-702
         BKL-101 → BKL-703
         BKL-602, BKL-603, BKL-501 → BKL-704 → BKL-705
```

## Suggested Phase 1 Delivery Plan (6 Sprints)

1. Sprint 1: BKL-108, BKL-101 to BKL-105, BKL-201, BKL-703.
2. Sprint 2: BKL-202 to BKL-205, BKL-207, BKL-301, BKL-302.
3. Sprint 3: BKL-303 to BKL-307, BKL-501, BKL-502.
4. Sprint 4: BKL-401 to BKL-405, BKL-503, BKL-504, BKL-601.
5. Sprint 5: BKL-602, BKL-603, BKL-604, BKL-605, BKL-701, BKL-702.
6. Sprint 6: BKL-505, BKL-704, BKL-705, plus remaining P1 pull-ins if capacity exists.

## Phase 1 Exit Criteria (Backlog Gate)

Phase 1 is complete when all are true:

1. All `P0` stories are done.
2. 10-year deterministic run with vintage tracking passes regression tests.
3. Core indicators and comparison outputs are available via API and GUI.
4. Full manifest + lineage is emitted for every run.
5. Performance and reproducibility NFR checks pass for benchmark fixtures.
6. At least one external pilot user runs the workflow and confirms credibility.

## Open Questions To Resolve During Grooming

1. Which asset class is first for vintage tracking: vehicles or heating systems?
2. Should OpenFisca API orchestration (`BKL-106`) remain Phase 1 `P1` or move to Phase 2?
3. What minimum GUI scope is acceptable if Sprint 5 overruns?
4. Which external pilot partner is the go/no-go reference user?
