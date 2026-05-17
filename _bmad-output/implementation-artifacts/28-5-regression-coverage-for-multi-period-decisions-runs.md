# Story 28.5: Regression and analyst-journey coverage for multi-period decisions runs

Status: ready-for-dev

## Story

As a developer closing out EPIC-28,
I want a multi-year integration test that exercises the full technology-set → incumbent column → choice writeback → transition record → manifest snapshot loop, plus the backward-compatibility checklist from the spike,
so that the multi-period chaining invariant (`incumbent_t == chosen_{t-1}`), the manifest reproducibility property, and the no-decisions backward compat are pinned in CI before EPIC-28 ships.

## Acceptance Criteria

1. Given a 5-year heating scenario over a 1k-household fixture with mixed initial incumbents (heat_pump / gas_boiler / wood_stove), when run end-to-end, then for every (household, year>1) the panel column `incumbent_heating_t == heating_chosen_{t-1}` (multi-period chaining invariant). The test pins this for all 1k households across all 4 transition years.
2. Given the same 5-year scenario, when run twice with the same master seed, then the two manifests are byte-for-byte identical (NFR6/NFR7 reproducibility).
3. Given a fixture mapping `(year → expected aggregate transition counts per (from, to) pair)`, when the scenario completes, then the actual transition counts match the fixture exactly.
4. Given a scenario with `investmentDecisionsEnabled === false`, when run on the same population, then the panel output is bit-identical to a baseline panel snapshot (no investment-decisions side effects). This validates the spike's Appendix B item 1.
5. Given a scenario with `investmentDecisionsEnabled === true` and `technologySet === null` (legacy fallback), when run, then the run completes with the legacy `default_heating_domain_config` + `default_vehicle_domain_config`, and the manifest records a "legacy fallback used" warning.
6. Given a population without `incumbent_<domain>` columns and `investmentDecisionsEnabled === true`, when run, then the run completes, all households start at the reference alternative, and the manifest records the missing-column warning (Story 28.2 AC #8).
7. Given a population with `incumbent_<domain>` containing values not in the technology set, when run, then the run aborts with `PopulationSchemaError` listing the unknown ids and household counts (Story 28.2 AC #3).
8. Given the existing manifest fixtures from earlier epics, when this story lands, then they all still load via `RunManifest.from_dict` after the new optional `technology_set` field is added (Story 28.3 AC #5; spike Appendix B item 5).
9. Given the existing 100k-household full population, when the test runs as a nightly job (not on every PR), then the same invariants hold; the per-PR test uses the 1k fixture.
10. Given an analyst-journey test in `frontend/src/__tests__/workflows/`, when run, then it walks: select population → enable decisions → open Technology step → use default French set → advance to Model → advance to Review → run → see transition counts in results → open manifest → verify `technology_set` snapshot present.

## Tasks / Subtasks

- [ ] Build 1k-household fixture (AC: #1, #2, #3)
  - [ ] Create or reuse a 1k-household fixture with mixed initial `incumbent_heating` values
  - [ ] Document the seed and the expected aggregate transition counts in a fixture file
- [ ] Multi-period chaining test (AC: #1)
  - [ ] New test `tests/orchestrator/test_multi_period_decisions.py`
  - [ ] Run a 5-year heating-only scenario with `EngineConfigCompiler` from Story 28.3
  - [ ] Assert the chaining invariant for every (household, year>1)
- [ ] Manifest reproducibility test (AC: #2)
  - [ ] Run twice with same seed; assert manifest equality (excluding timestamps; use a canonical-form helper if needed)
- [ ] Transition-counts fixture test (AC: #3)
  - [ ] Compare aggregate (from, to) transition counts to the fixture
- [ ] No-decisions backward-compat snapshot (AC: #4)
  - [ ] Run a scenario with decisions disabled; compare panel to a baseline snapshot
  - [ ] If a baseline snapshot doesn't exist yet, generate one in this story and commit it
- [ ] Legacy-fallback test (AC: #5)
  - [ ] Run a scenario with `investmentDecisionsEnabled === true` and `technologySet === null`
  - [ ] Assert legacy defaults applied; assert manifest warning present
- [ ] Missing-incumbent-column test (AC: #6)
  - [ ] Population without incumbent columns; assert all households start at reference alternative; assert manifest warning
- [ ] Unknown-incumbent fail-loud test (AC: #7)
  - [ ] Population with incumbent values not in the technology set; assert `PopulationSchemaError` raised
- [ ] Existing-manifest load test (AC: #8)
  - [ ] Iterate over existing manifest fixtures in `tests/governance/fixtures/` (or wherever they live); assert each loads via `RunManifest.from_dict`
- [ ] Nightly full-population variant (AC: #9)
  - [ ] Mark the 100k variant with a pytest marker (e.g., `@pytest.mark.nightly`)
  - [ ] Configure CI to run nightly tests separately from per-PR tests
- [ ] Analyst-journey test (AC: #10)
  - [ ] New file `frontend/src/__tests__/workflows/investment-decisions-journey.test.tsx`
  - [ ] Walks through the full happy path; mocks API endpoints; asserts manifest panel includes transition counts
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/`
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- This is the closing story for EPIC-28. It pins the highest-risk invariants the spike flagged in Section 10.
- The 1k-household fixture is intentional — the 100k full population is too slow for per-PR CI. The spike Section 9 mentions this tradeoff explicitly.
- AC #2 (manifest equality) excludes timestamps and run ids — use the existing canonical-form helper if one exists, otherwise add one.
- AC #4 (no-decisions snapshot) is the strongest backward-compat guarantee. If the snapshot diverges in a future story, that's a real regression and must be investigated, not auto-updated.
- Coordinate with Story 27.10 (formatter consolidation) for any test that asserts on formatted strings — use the new helpers.

### Project Structure Notes

- New files: `tests/orchestrator/test_multi_period_decisions.py`, possibly `tests/governance/test_manifest_backward_compat.py`, `frontend/src/__tests__/workflows/investment-decisions-journey.test.tsx`, fixture files
- Modified: pytest CI config to add a `nightly` marker if not already present
- No production code changes (all behaviour comes from 28.1–28.4)

### References

- [Source: _bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md#Section-9] (sized stories)
- [Source: _bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md#Section-10] (risks pinned by this story)
- [Source: _bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md#Appendix-B] (backward-compat checklist)
- [Source: Stories 28.1, 28.2, 28.3, 28.4]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
