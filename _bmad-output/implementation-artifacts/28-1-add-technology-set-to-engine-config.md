# Story 28.1: Add `technology_set` to `EngineConfig`; expose API and persistence

Status: ready-for-dev

## Story

As an analyst configuring an investment-decisions scenario,
I want a typed `technology_set` on the engine configuration that names which technologies are in scope per domain, with a stable version and a fully-embedded snapshot for reproducibility,
so that future stories (population schema, choice writeback, wizard UI, multi-period regression) have a canonical contract to consume.

## Acceptance Criteria

1. Given the new types in `frontend/src/types/workspace.ts`, when imported, then the module exports `DecisionDomainKey`, `TechnologyAlternative`, `DomainTechnologySet`, and `TechnologySet` matching the spike's Section 2.1 shapes; `EngineConfig.technologySet?: TechnologySet | null` is added without breaking any existing consumer.
2. Given the new Python value object at `src/reformlab/discrete_choice/technology_set.py`, when imported, then it exports `DomainTechnologySet` and `TechnologySet` as frozen dataclasses, with a `to_choice_set(domain: str) -> ChoiceSet` method that materialises the existing `ChoiceSet` from existing `Alternative` instances. No mutation of `ChoiceSet` is introduced.
3. Given the new API endpoint `GET /api/discrete-choice/technology-sets/default?domain=heating`, when called with `domain=heating`, then the response is a `DomainTechnologySet` JSON shape representing the canonical French set (5 heating alternatives, including `keep_current` as `referenceAlternativeId`); `domain=vehicle` returns the canonical vehicle set (6 alternatives). Unknown domain → 4xx.
4. Given a scenario edit where the user populates `engineConfig.technologySet`, when the scenario is persisted to localStorage and reloaded, then the technology set is restored byte-for-byte (round-trip serialisation tested).
5. Given a scenario with `investmentDecisionsEnabled === false`, when persisted, then `technologySet` may be `null` or absent; the orchestrator must short-circuit (no validation, no writeback, no manifest snapshot of the set).
6. Given a contract test posting a `TechnologySet` JSON shape to `POST /api/runs`, when the run completes, then the manifest's `technology_set` field round-trips the same shape (this asserts TS-Python schema parity per the spike's risk 10.2).
7. Given an old scenario loaded from localStorage without a `technologySet` field, when restored with `investmentDecisionsEnabled === true`, then the migration in `useScenarioPersistence` falls back to the legacy `default_heating_domain_config` + `default_vehicle_domain_config` and emits a manifest warning when the run executes.

## Tasks / Subtasks

- [ ] Frontend types (AC: #1)
  - [ ] Add `DecisionDomainKey`, `TechnologyAlternative`, `DomainTechnologySet`, `TechnologySet` to `frontend/src/types/workspace.ts`
  - [ ] Extend `EngineConfig` with `technologySet?: TechnologySet | null`
  - [ ] Update any TypeScript consumer that constructs `EngineConfig` (search for `EngineConfig` instantiation; many will not need to change because the field is optional)
- [ ] Backend value object (AC: #2)
  - [ ] New file `src/reformlab/discrete_choice/technology_set.py` with the two frozen dataclasses and the `to_choice_set` method
  - [ ] Re-export from `src/reformlab/discrete_choice/__init__.py` if there's a public API there
- [ ] Canonical-set API endpoint (AC: #3)
  - [ ] Add a new route `GET /api/discrete-choice/technology-sets/default` in `src/reformlab/server/routes/`
  - [ ] Backed by a fixture file or in-code constant exposing the canonical `fr-default-2026-04-26` set: 5 heating alternatives (including `keep_current`) and 6 vehicle alternatives
  - [ ] Reference alternative ids: `keep_current` for heating, `keep_current` for vehicle (or domain-specific equivalents)
  - [ ] Backend tests for both domains plus unknown-domain 4xx
- [ ] Persistence (AC: #4, #7)
  - [ ] Update `useScenarioPersistence` (`frontend/src/hooks/useScenarioPersistence.ts`) to serialise/deserialise `technologySet`
  - [ ] Add a migration path: scenarios with `investmentDecisionsEnabled === true` but no `technologySet` keep working (legacy default-config fallback)
  - [ ] Round-trip test: serialise → reload → assert byte-equal
- [ ] Short-circuit when disabled (AC: #5)
  - [ ] Verify the orchestrator (`src/reformlab/orchestrator/runner.py`) does not invoke any technology-set validation when `investmentDecisionsEnabled === false`
  - [ ] Add a backend test asserting a run with `investmentDecisionsEnabled === false` succeeds even when `technology_set` is omitted
- [ ] Contract roundtrip test (AC: #6)
  - [ ] New test `tests/server/test_technology_set_roundtrip.py`: post a TechnologySet JSON, run an orchestrator, read the manifest, assert schema equivalence
  - [ ] This test enforces the TS↔Python parity called out in spike risk 10.2
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/`
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- **No `ComputationAdapter` change** in this story (or in EPIC-28 at all). The spike's Section 5 confirms the adapter is invariant.
- **No OpenFisca change** in this story.
- The canonical-set API intentionally returns the **fully-resolved** snapshot, not a reference. This is the same pattern `RunManifest.policy` uses (snapshot, not reference) and it is mandatory for reproducibility.
- The version string format `fr-default-{date}` is human traceability only. The snapshot is the source of truth. Bumping the version without changing the snapshot is meaningless.
- Story 28.4 (wizard) consumes the canonical-set API; do not block 28.4 on UX wireframes — the API contract is sufficient.

### Project Structure Notes

- New files: `src/reformlab/discrete_choice/technology_set.py`, `src/reformlab/server/routes/technology_sets.py` (or co-located), `tests/server/test_technology_set_roundtrip.py`, `tests/discrete_choice/test_technology_set.py`
- Modified: `frontend/src/types/workspace.ts`, `frontend/src/hooks/useScenarioPersistence.ts`, possibly `src/reformlab/discrete_choice/__init__.py`
- No deletions

### References

- [Source: _bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md#Section-2]
- [Source: _bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md#Section-9] (sized story breakdown)
- [Source: src/reformlab/discrete_choice/types.py] (existing Alternative, ChoiceSet)
- [Source: src/reformlab/governance/manifest.py:154] (manifest extension target — covered by 28.3, but 28.1 must keep the contract compatible)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
