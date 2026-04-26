# Story 29.2: Resolve generic-name placeholders (irpp, revenu_net, revenu_brut, taxe_carbone)

Status: ready-for-dev

## Story

As a backend developer maintaining the live OpenFisca path,
I want the four generic-name placeholders (`irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone`) renamed to real OpenFisca-France targets, dropped, or implemented as custom variables,
so that the live path's output mapping resolves cleanly against `openfisca_france` 44.2.2 instead of relying on names that don't exist in core.

## Acceptance Criteria

1. Given `irpp` in `_DEFAULT_OUTPUT_MAPPING`, when this story is complete, then it is renamed to `impot_revenu_restant_a_payer` (already used in `tests/computation/test_openfisca_integration.py`) and resolves at runtime.
2. Given `revenu_net` in the mapping, when this story is complete, then it is dropped — `revenu_disponible` already covers the net-income concept and is already in `_DEFAULT_LIVE_OUTPUT_VARIABLES`.
3. Given `revenu_brut`, when this story is complete, then either (a) it is dropped if `revenu_disponible` is sufficient for downstream indicators, or (b) it is implemented as a custom variable in the EPIC-29 extension, or (c) it is composed from existing OpenFisca core variables — pick one based on indicator usage analysis.
4. Given `taxe_carbone`, when this story is complete, then it is implemented as a custom variable in the EPIC-29 extension (it does not exist in OpenFisca core).
5. Given the renaming/dropping/implementation decisions, when summarised, then a short ADR section in this story's Dev Notes records each decision and its rationale.
6. Given the test suite, when this story is complete, then `_DEFAULT_OUTPUT_MAPPING` resolves entirely against either OpenFisca core variables OR the custom extension; no name remains unresolved.

## Tasks / Subtasks

- [ ] Indicator usage audit (AC: #3)
  - [ ] Search the indicator modules and any UI consumers for references to `revenu_brut` (frontend doesn't read internal names; check the analyst-facing column outputs)
  - [ ] If no consumer requires gross income separately from disposable income, drop `revenu_brut`
  - [ ] If a consumer requires it, decide between custom variable or composition formula
- [ ] Rename `irpp` → `impot_revenu_restant_a_payer` (AC: #1)
  - [ ] Update `_DEFAULT_OUTPUT_MAPPING` in `result_normalizer.py`
  - [ ] Verify `tests/computation/test_openfisca_integration.py` already uses the canonical name (audit said it does)
- [ ] Drop `revenu_net` (AC: #2)
  - [ ] Remove from `_DEFAULT_OUTPUT_MAPPING`
  - [ ] Verify no consumer expects this output column; if any does, update them to use `revenu_disponible`
- [ ] Resolve `revenu_brut` (AC: #3)
  - [ ] Apply the decision from the audit task above
- [ ] Implement `taxe_carbone` as custom variable (AC: #4)
  - [ ] Define in the EPIC-29 extension created in Story 29.1 (entity=household, value_type=float, definition_period=year)
  - [ ] Formula composes carbon emissions × carbon price parameter
- [ ] Document decisions (AC: #5)
  - [ ] Append an ADR section to this story file under "Decision Record" (or to a dedicated ADR doc) recording each choice
- [ ] Tests (AC: #6)
  - [ ] Unit test for `taxe_carbone` (3+ cases)
  - [ ] Integration test: live run produces values for the four newly-resolved names without error
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/computation/`

## Dev Notes

- This story depends on 29.1 (the extension module must exist).
- After this story lands, the `_DEFAULT_OUTPUT_MAPPING` should resolve fully without exceptions. Story 29.3 then adds the resolved names back to `_DEFAULT_LIVE_OUTPUT_VARIABLES`.
- `taxe_carbone` may already be partially implemented in policy templates; check before duplicating logic.

### Project Structure Notes

- Modified: `src/reformlab/computation/result_normalizer.py`, the EPIC-29 extension module
- Possibly modified: indicator modules if they reference dropped names
- Tests: `tests/computation/test_result_normalizer.py`, integration tests

### References

- [Source: _bmad-output/implementation-artifacts/deferred-work.md:19-25]
- [Source: src/reformlab/computation/result_normalizer.py] (current mapping)
- [Source: tests/computation/test_openfisca_integration.py] (canonical name `impot_revenu_restant_a_payer`)
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-29.2]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
