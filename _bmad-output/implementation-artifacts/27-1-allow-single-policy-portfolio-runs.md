# Story 27.1: Allow single-policy portfolio runs

Status: done

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

- [x] Backend rule update (AC: #1, #2, #3)
  - [x] Change `if len(policies) < 2:` to `if len(policies) < 1:` at `src/reformlab/server/routes/portfolios.py:305`
  - [x] Update copy at `:310-311`: `why: "Portfolio requires at least 1 policy, got {len(policies)}"`, `fix: "Add at least 1 policy to the portfolio"`
  - [x] Same rule change at `src/reformlab/server/routes/portfolios.py:415`
  - [x] Update copy at `:420-421`: `why: "Validation requires at least 1 policy, got {len(body.policies)}"`, `fix: "Add at least 1 policy before validating"`
- [x] Backend tests (AC: #1, #2, #3, #6)
  - [x] Add test for single-policy build returning 200
  - [x] Add test for single-policy validate returning 200 + `valid: true`
  - [x] Add test for empty-policy build returning 4xx with new message
  - [x] Add test asserting `validate_compatibility()` returns no conflicts for 1 policy
- [x] Frontend audit (AC: #5)
  - [x] Search frontend for any symmetric `< 2` / `>= 2` guards on composition length
  - [x] Remove any guard that blocks Save/Run/Validate when composition has 1 policy
  - [x] If a guard is purely informational (e.g., "conflict strategy only applies with 2+"), keep it but allow the action
- [x] Run quality gates
  - [x] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/server/test_portfolios.py`
  - [x] `npm test`, `npm run typecheck`, `npm run lint`

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

glm-4.7 (Claude Code)

### Debug Log References

None required - all changes completed on first attempt.

### Completion Notes List

1. **Backend rule update**: Changed `len(policies) < 2` to `len(policies) < 1` in two locations (line 305 for build, line 415 for validate). Updated error messages to reflect "at least 1 policy" requirement.

2. **Backend tests**:
   - Added `test_create_single_policy_succeeds` - verifies 201 status for single-policy portfolio creation
   - Added `test_validate_single_policy_succeeds` - verifies 200 status with `is_compatible: true` for single-policy validation
   - Updated `test_create_requires_min_1_policy` - now tests empty policy array (0 policies) returns 400 with new error message
   - Updated `test_validate_requires_min_1_policy` - now tests empty policy array returns 400 with new error message
   - Updated `test_update_requires_min_1_policy` - now tests empty policy array returns 400 with new error message
   - Added `test_validate_compatibility_single_policy_returns_no_conflicts` - verifies pairwise conflict detection returns empty tuple for single-policy portfolio

3. **Frontend audit**:
   - Found and fixed one blocking guard in `PortfolioDesignerScreen.tsx` (deprecated but still present): changed `disabled={composition.length < 2}` to `< 1` for the Review button
   - Verified `PoliciesStageScreen.tsx` (canonical screen) already correctly supports single-policy portfolios:
     - `isPortfolioValid` uses `composition.length >= 1` for minimum policy check
     - `hasConflicts` only checks conflicts when `composition.length >= 2`
     - `runValidation` skips validation API call for `< 2` policies (informational optimization, not blocking)

4. **Quality gates**:
   - All 77 tests passed (including 3 new single-policy tests)
   - mypy: Success (no issues found in 163 source files)
   - Frontend: 819 tests passed, typecheck passed
   - ruff errors are pre-existing (line length in unrelated files)

### File List

**Modified:**
- `src/reformlab/server/routes/portfolios.py` - Updated minimum policy count from 2 to 1
- `tests/server/test_portfolios.py` - Updated/added tests for single-policy portfolios
- `tests/templates/portfolios/test_composition.py` - Added test for `validate_compatibility()` with single policy
- `frontend/src/components/screens/PortfolioDesignerScreen.tsx` - Fixed Review button guard to allow single-policy navigation
