# Story 27.1: Allow single-policy portfolio runs

Status: ready-for-dev

## Story

As a policy analyst evaluating one isolated policy,
I want to assess a portfolio composed of a single policy without being blocked by a 2-policy minimum,
so that I can run a baseline-vs-one-reform analysis without inventing a second placeholder policy.

## Acceptance Criteria

1. Given a portfolio with exactly one policy, when `POST /api/portfolios` is called, then the portfolio is built successfully and the response status is 200.
2. Given a portfolio with exactly one policy, when `POST /api/portfolios/validate` is called, then the response status is 200 and `valid: true`.
3. Given a portfolio with zero policies, when build or validate is called, then the response status is 4xx with `detail.what: "Insufficient policies"`, `detail.why: "Portfolio requires at least 1 policy, got 0"`, and `detail.fix: "Add at least 1 policy to the portfolio"`.
4. Given a single-policy portfolio is run via `POST /api/runs`, when execution completes, then the run produces normal results without invoking pairwise conflict detection (since `composition.py:535+` pair loops are no-op for one policy).
5. Given the frontend is checked, when the composition has one policy, then no symmetric `< 2` guard prevents Save, Run, or any other primary action.
6. Given the existing pairwise conflict detection at `src/reformlab/templates/portfolios/composition.py:535+`, when run with 1 policy, then no spurious conflicts are emitted.

## Tasks / Subtasks

- [ ] Backend rule update (AC: #1, #2, #3)
  - [ ] Change `if len(policies) < 2:` to `if len(policies) < 1:` at `src/reformlab/server/routes/portfolios.py:305`
  - [ ] Update copy at `:310-311`: `why: "Portfolio requires at least 1 policy, got {len(policies)}"`, `fix: "Add at least 1 policy to the portfolio"`
  - [ ] Same rule change at `src/reformlab/server/routes/portfolios.py:415`
  - [ ] Update copy at `:420-421`: `why: "Validation requires at least 1 policy, got {len(body.policies)}"`, `fix: "Add at least 1 policy before validating"`
- [ ] Backend tests (AC: #1, #2, #3, #6)
  - [ ] Add test for single-policy build returning 200
  - [ ] Add test for single-policy validate returning 200 + `valid: true`
  - [ ] Add test for empty-policy build returning 4xx with new message
  - [ ] Add test asserting `validate_compatibility()` returns no conflicts for 1 policy
- [ ] Frontend audit (AC: #5)
  - [ ] Search frontend for any symmetric `< 2` / `>= 2` guards on composition length
  - [ ] Remove any guard that blocks Save/Run/Validate when composition has 1 policy
  - [ ] If a guard is purely informational (e.g., "conflict strategy only applies with 2+"), keep it but allow the action
- [ ] Run quality gates
  - [ ] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/server/test_portfolios.py`
  - [ ] `npm test`, `npm run typecheck`, `npm run lint`

## Dev Notes

- The 2-policy minimum was a UX constraint, not a technical one. `PolicyPortfolio.__post_init__` accepts ≥1 policy. `PortfolioComputationStep` validates ≥1. `validate_compatibility()` pairwise loop is naturally no-op for 1 policy.
- Git context: commit `b4f158e8` (2026-04-19) introduced the `< 2` rule; this story reverses it.

### Project Structure Notes

- Files touched: `src/reformlab/server/routes/portfolios.py`, `tests/server/test_portfolios.py` (or wherever portfolio route tests live)
- No frontend changes expected unless the audit finds a guard

### References

- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md#Story-27.1]
- [Source: src/reformlab/server/routes/portfolios.py:305-313, :415-423]
- [Source: src/reformlab/templates/portfolios/composition.py:535] (pairwise conflict detection)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
