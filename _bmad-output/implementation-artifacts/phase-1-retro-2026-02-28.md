# Phase 1 Retrospective — ReformLab

**Date:** 2026-02-28
**Scope:** All 7 Epics (Epics 1-7), Full Phase 1 Implementation
**Facilitator:** Bob (Scrum Master)
**Participants:** Alice (Product Owner), Charlie (Senior Dev), Dana (QA Engineer), Elena (Junior Dev), Lucas (Project Lead)
**Mode:** YOLO — honest reckoning, all gaps surfaced at once

---

## 1. Delivery Metrics

| Metric | Value |
|--------|-------|
| Epics completed | 7/7 (all marked done in sprint-status.yaml) |
| Stories marked done | 46/46 in sprint-status.yaml |
| Python source files | 70 production files |
| Test files | 97 test files |
| Tests passing | 1,360 (excl. 2 notebook output failures) |
| Test coverage | 87.25% (above 80% threshold) |
| Frontend components | 25+ React components |
| Frontend tests | 3 passing (Vitest) |
| Notebooks | 2 (quickstart + advanced) |
| Backend test execution time | ~14s for full suite |
| Architecture subsystems | 8 (computation, data, templates, orchestrator, vintage, indicators, governance, interfaces) |

---

## 2. What Went Well

### 2.1 Architecture survived contact with reality
The layered design — Computation Adapter → Data Layer → Scenario Templates → Dynamic Orchestrator → Indicators → Governance → Interfaces — was implemented almost exactly as specified. No epic required rethinking the fundamental architecture. Key decisions that proved sound:
- **Adapter pattern** for computation backends
- **Frozen dataclasses** as the universal immutable type
- **Protocol-based structural typing** for extensibility
- **PyArrow as canonical data type** (no pandas/polars in production)

### 2.2 Test discipline was exceptional
Every story enforced "all existing tests must continue to pass." The regression safety net held across 46 stories. Test count grew monotonically:
- Epic 1: 37 → 210
- Epic 2: 210 → ~627
- Epic 3: 627 → 891
- Epic 4: 891 → ~1,100
- Epics 5-7: ~1,100 → 1,374

Red-green-refactor was the norm. Golden file tests, round-trip tests, and error message assertion tests were used consistently. Coverage reached 87.25% with proper exclusions.

### 2.3 Story files as contracts enabled multi-agent development
Claude Opus 4.5/4.6, Claude Sonnet 4.5, and GPT-5 Codex all implemented stories. The detailed dev notes, anti-patterns, cross-story dependency documentation, and "Previous Story Intelligence" sections let different agents produce consistent code. This is a genuine process innovation worth preserving.

### 2.4 Pattern reuse was the core accelerator
Error handling (`summary/reason/fix`), frozen dataclasses, YAML loaders, Protocol+decorator patterns — each was established once and reused across all subsequent stories. By Epic 3, stories were completing on first pass with zero debugging required across all 7 stories.

### 2.5 Scope discipline was strong throughout
Every story included explicit "Out of Scope Guardrails." No epic suffered from scope creep. Deferred items were consistently documented with rationale. The "Previous Story Learnings" feed-forward mechanism ensured each story built on prior insights.

### 2.6 Planning investment paid off massively
The PRD, architecture, and backlog were so detailed that most stories completed on first pass. Epics 3, 4, and 7 had virtually zero debugging. Spec quality directly predicted implementation smoothness. This is the single biggest success of Phase 1.

---

## 3. What Didn't Go Well — The Honest Reckoning

### GAP 1: Dev Agent Records are inconsistently filled
**Severity: HIGH (process/governance)**

Of 46 stories, approximately 15-18 have completely empty Dev Agent Records — template placeholders (`{{agent_model_name_version}}`) where there should be agent model, debug logs, completion notes, and file lists.

**Affected stories include:** 2-2, 4-1, 4-4, 4-5, 5-2, 5-3, 5-4, 5-5, 6-1, 6-6, 7-3, and parts of others.

**Impact:** No audit trail for what agent built those stories, what challenges were encountered, or what decisions were made. For a project that values "assumption transparency," this is a significant process gap.

### GAP 2: Story file status doesn't match sprint-status.yaml
**Severity: MEDIUM (tracking)**

Multiple story files have `Status: ready-for-dev` or `Status: review` in their headers while sprint-status.yaml says `done`. Stories 7-1, 7-3, 7-5 show `ready-for-dev` in the file header but `done` in sprint-status. sprint-status.yaml became the de facto source of truth, but story files contain stale status.

### GAP 3: Three governance stories may be unimplemented (5-2, 5-4, 5-5)
**Severity: CRITICAL (functional gap)**

Stories 5-2 (Capture Assumptions/Mappings/Parameters), 5-4 (Hash Input/Output Artifacts), and 5-5 (Reproducibility Check Harness) have empty Dev Agent Records and `ready-for-dev` status in their files, yet sprint-status.yaml marks them as `done`.

**What this means for the product:**
- `RunManifest` schema exists (Story 5-1 ✅) but assumptions, mappings, and parameters may not be captured at runtime
- `data_hashes` and `output_hashes` fields exist on the manifest but may not be populated
- No automated reproducibility verification harness may exist
- NFR6 (reproducibility) and NFR7 (cross-machine consistency) are architecturally defined but may not be enforced by code

**Note:** Code exists at `governance/capture.py`, `governance/hashing.py`, `governance/reproducibility.py` — a codebase audit is needed to verify if these files implement the story ACs or are incomplete stubs.

### GAP 4: Notebooks have committed outputs (2 test failures)
**Severity: LOW (easily fixable)**

Both `quickstart.ipynb` and `advanced.ipynb` have committed cell outputs (`execution_count: 1`). Two tests fail:
- `test_advanced_notebook_outputs_are_cleared`
- `test_quickstart_notebook_outputs_are_cleared`

### GAP 5: Frontend has minimal test coverage
**Severity: MEDIUM**

25+ React components but only 3 Vitest tests. No component unit tests. No integration tests. Manual visual review was the validation method. The GUI prototype (6-4a) is functional but fragile.

### GAP 6: Security was consistently an afterthought in early epics
**Severity: LOW (improved over time)**

In Epic 1, security hardening was caught in code review rather than during initial implementation in 5 of 8 stories: Parquet thrift limits, path traversal protection, hash error wrapping, YAML safe loading, range rule validation. By Epic 4, security was proactively addressed (whitelist-only formula parsing). The trend improved, but early code has bolted-on security.

### GAP 7: GPT-5 Codex produced no working code on Story 6-4a
**Severity: HIGH (process/quality)**

The first implementation pass of the GUI prototype delivered essentially zero working frontend code. The AI code review caught all 5 HIGH findings. A second pass resolved everything. Lesson: AI agent verification is critical — an agent claimed "done" when nothing was delivered.

### GAP 8: Notebook cell ordering bugs survived CI
**Severity: LOW**

Story 7-4 (pilot) discovered that both notebooks had cells in wrong order — variable usage before variable definition. These passed `pytest --nbmake` but broke when run sequentially. Fixed via manual cell reordering.

### GAP 9: Process discipline declined from Epic 5 onward
**Severity: MEDIUM (systemic)**

Epics 1-4 have generally complete Dev Agent Records, code reviews with specific findings, and accurate status tracking. From Epic 5 onward, records are frequently empty, code reviews are absent from artifacts, and status tracking diverges. Possible "process fatigue" in the second half.

---

## 4. Epic-by-Epic Assessment

### Epic 1: Computation Adapter and Data Layer
- **Stories:** 8/8 done
- **Quality:** Strong. All stories have Dev Agent Records. Code reviews caught security gaps.
- **Technical debt:** Minor (pytest<9.0 ceiling, metadata mutability deferred, ApiMappingError/MappingError split)
- **Key pattern established:** Protocol-based adapter, frozen dataclasses, structured errors

### Epic 2: Scenario Templates and Registry
- **Stories:** 7/7 done
- **Quality:** Good. Story 2-2 has empty Dev Agent Record. Pattern reuse from Epic 1 was highly effective.
- **Technical debt:** DecileResults in carbon_tax (should be shared), registry linear scan, large __init__.py API surface
- **Key pattern established:** Template-as-data, content-addressable versioning, schema migration

### Epic 3: Step-Pluggable Dynamic Orchestrator
- **Stories:** 7/7 done
- **Quality:** Excellent. Zero debugging across all stories. Cleanest epic in Phase 1.
- **Technical debt:** Shallow state copy, no dynamic step loading, custom callable trust boundary
- **Key pattern established:** Step Protocol+decorator+adapter, deterministic seed propagation

### Epic 4: Indicators and Scenario Comparison
- **Stories:** 6/6 done
- **Quality:** Good. 3 stories have empty Dev Agent Records (4-1, 4-4, 4-5). Pattern reuse was dominant accelerator.
- **Technical debt:** Approximate median, deferred cross-field formulas, growing IndicatorResult union type
- **Key pattern established:** Vectorized PyArrow operations, recursive descent formula parser

### Epic 5: Governance and Reproducibility
- **Stories:** 6 marked done, but 3 may be incomplete (5-2, 5-4, 5-5)
- **Quality:** LOWEST of all epics. Critical verification needed.
- **Technical debt:** Potentially missing runtime capture, hashing, and reproducibility verification
- **Key pattern established:** RunManifest schema, warning capture system (5-6)

### Epic 6: Interfaces
- **Stories:** 7 marked done, but 6-2, 6-3, 6-4b appear not started
- **Quality:** Mixed. 6-4a had a failed first pass. 6-5 was the cleanest story.
- **Technical debt:** No frontend component tests, no backend wiring for GUI, notebooks may not follow full story process
- **Key pattern established:** Thin facade delegation, FastAPI backend design (planned)

### Epic 7: Trusted Outputs and Validation
- **Stories:** 5/5 done
- **Quality:** Good. Story files have status mismatches but code/tests exist.
- **Technical debt:** Hardcoded memory heuristics, liberal benchmark tolerances, cross-machine reproducibility untested
- **Key pattern established:** Benchmark suite, pilot validation, exit checklist

---

## 5. Technical Debt Registry

| ID | Item | Source | Severity | Blocking? |
|----|------|--------|----------|-----------|
| TD-01 | pytest<9.0 ceiling from openfisca-core | Epic 1 | Low | No |
| TD-02 | DecileResults in carbon_tax, not shared module | Epic 2 | Low | No |
| TD-03 | Registry linear scan O(n*v) | Epic 2 | Low | No |
| TD-04 | templates/__init__.py large API surface | Epic 2 | Low | No |
| TD-05 | Shallow state copy in orchestrator | Epic 3 | Medium | No |
| TD-06 | Custom callable trust boundary (no sandbox) | Epic 3 | Medium | No |
| TD-07 | Single asset class (vehicle) for vintage | Epic 3 | Low | No |
| TD-08 | Approximate median in indicators | Epic 4 | Low | No |
| TD-09 | Growing IndicatorResult union type | Epic 4 | Medium | No |
| TD-10 | Governance runtime capture gaps (5-2, 5-4, 5-5) | Epic 5 | CRITICAL | YES |
| TD-11 | Empty Dev Agent Records (~15-18 stories) | Process | High | No |
| TD-12 | Status mismatch between files and sprint-status | Process | Medium | No |
| TD-13 | Frontend: 3 tests for 25+ components | Epic 6 | Medium | No |
| TD-14 | GUI backend wiring (6-4b) not started | Epic 6 | High | Phase 2 |
| TD-15 | Notebook committed outputs (2 test failures) | Epic 7 | Low | No |
| TD-16 | Hardcoded memory estimation heuristic | Epic 7 | Low | No |
| TD-17 | Cross-machine reproducibility untested | Epic 7 | Medium | No |

---

## 6. Action Items

### Critical (Before Phase 2 starts)

| # | Action | Owner | Success Criteria |
|---|--------|-------|-----------------|
| 1 | **Audit stories 5-2, 5-4, 5-5 against codebase** — verify if governance/capture.py, governance/hashing.py, governance/reproducibility.py implement story ACs or are stubs | Lucas | Each story's ACs individually verified. Status corrected in both files and sprint-status.yaml |
| 2 | **Fix notebook output failures** — clear committed outputs from both notebooks | Dev agent | `pytest tests/notebooks` passes 14/14 |
| 3 | **Reconcile story file status with sprint-status.yaml** — every file header must match | Dev agent | Zero discrepancies |

### High Priority

| # | Action | Owner | Success Criteria |
|---|--------|-------|-----------------|
| 4 | **Implement 5-2, 5-4, 5-5 if confirmed missing** | Dev agent | RunManifest populated at runtime; hashing works; reproducibility harness verifies reruns |
| 5 | **Fill empty Dev Agent Records retroactively** — at minimum: agent model, file list, brief completion summary | Dev agent / Lucas | No `{{agent_model_name_version}}` placeholders remain |

### Medium Priority

| # | Action | Owner | Success Criteria |
|---|--------|-------|-----------------|
| 6 | **Add frontend component tests** | Dev agent | Frontend test count > 20 |
| 7 | **Create process health CI check** for Dev Agent Record completeness | Dev agent | CI warns on empty records |
| 8 | **Extract shared DecileResults to common module** | Dev agent | carbon_tax, subsidy, rebate, feebate all import from shared location |

---

## 7. Readiness Assessment

| Subsystem | Status | Confidence |
|-----------|--------|------------|
| Computation Adapter | SOLID | High |
| Data Layer | SOLID | High |
| Scenario Templates | SOLID | High |
| Dynamic Orchestrator | SOLID | High |
| Vintage Tracking | SOLID | High |
| Indicators | SOLID | High |
| Governance | GAPS | Low — needs audit |
| Python API | SOLID | High |
| Notebooks | MINOR GAPS | Medium — test failures |
| GUI Prototype | PARTIAL | Medium — static only, no backend |
| Frontend Tests | WEAK | Low |
| CI / Quality Gates | SOLID | High |
| Process Discipline | DECLINING | Low — strong Epics 1-4, weak 5-7 |

---

## 8. Key Lessons for Phase 2

1. **Planning quality predicts implementation smoothness.** The investment in PRD, architecture, and detailed story specs paid off massively. Continue this practice.

2. **Dev Agent Records must be enforced, not optional.** Add a CI check or pre-review gate that verifies records are populated before marking done.

3. **Governance stories are the hardest to implement.** Cross-subsystem wiring (capture, hashing, reproducibility) is inherently harder than intra-module work. These stories need extra attention and possibly pairing.

4. **AI code reviews on AI-generated work are an effective quality gate.** The GPT-5 Codex failure on 6-4a was caught by review. Maintain cross-agent review discipline.

5. **Process discipline requires active maintenance.** The decay from Epic 5 onward shows that process habits atrophy without reinforcement. Consider lightweight process checkpoints between epics.

6. **Security should be a first-pass concern.** Add security considerations to story templates as a standard section, not just a review finding category.

---

## 9. Phase 1 Summary

Phase 1 delivered an impressive body of working software: 70 production Python files, 1,360 passing tests at 87% coverage, a working GUI prototype, two notebooks, and a sound architecture. The planning-to-execution pipeline worked exceptionally well, and the multi-agent development model proved viable.

The critical gap is in the governance layer — the subsystem that transforms ReformLab from "a computation engine" into "a trustworthy analytical tool." Stories 5-2, 5-4, and 5-5 require immediate audit and, if missing, implementation. Without runtime capture, artifact hashing, and reproducibility verification, the project's core promise of transparent, reproducible analysis is incomplete.

Process discipline also needs renewal. The Dev Agent Record gaps and status tracking inconsistencies are manageable but must be addressed before Phase 2 to avoid accumulating more invisible debt.

---

**Retrospective Status:** COMPLETE
**Generated:** 2026-02-28
**Next Steps:**
1. Audit governance stories (5-2, 5-4, 5-5) against codebase
2. Fix notebook test failures
3. Reconcile all story statuses
4. Begin Phase 2 planning when critical items resolved
