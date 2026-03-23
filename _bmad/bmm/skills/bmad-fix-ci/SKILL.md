---
name: bmad-fix-ci
description: "Diagnose and fix GitHub CI failures locally. Use when the user says 'fix ci' or 'fix ci failures'."
---

# Fix CI

## Overview

This skill checks GitHub Actions CI status for the current branch, diagnoses failures from the logs, applies fixes iteratively, verifies locally, and commits the result. Act as a pragmatic developer focused on getting CI green with minimal targeted changes. Produces a local commit with all fixes applied — does not push.

**Supported failure types:** ruff lint, mypy typecheck, pytest, npm lint, npm typecheck, npm test. For unrecognized failures (infra issues, dependency problems, permissions), reports findings and halts for the user to decide.

**Iteration:** After fixing and verifying, if new failures surface, loops back to fix again (max 3 iterations, tracked explicitly). This catches cascading issues where fixing one error reveals another.

## On Activation

Load available config from `{project-root}/_bmad/config.yaml` and `{project-root}/_bmad/config.user.yaml` (root level and `bmm` section). If config is missing, let the user know `bmad-builder-setup` can configure the module at any time. Use sensible defaults for anything not configured.

Resolve: `{communication_language}`, `{user_name}`.

## Execution

### Step 0: Precondition Check

Verify `gh auth status` succeeds. If not, tell the user to run `gh auth login` and halt.

### Step 1: Check CI Status

Get the current branch and check for failed runs:

```bash
git branch --show-current
gh run list --branch <current-branch> --limit 5
```

If there are **no runs at all**, report: "No CI runs found for this branch. CI may not have triggered yet, or the branch may not have a workflow configured." and halt.

If there are runs but **none have failed**, report that CI is green and stop.

If there are failed runs, display the selected run's ID, name, timestamp, and workflow name. If multiple failed runs exist, confirm with the user: "Targeting run #<id> (<name> · <time ago>). Proceed or pick a different run?"

### Step 2: Fetch Failure Logs

First identify which jobs failed:

```bash
gh run view <run-id> --json jobs --jq '.jobs[] | select(.conclusion == "failure") | {name, conclusion}'
```

Then fetch logs only for the failed job(s):

```bash
gh run view <run-id> --log-failed
```

### Step 3: Diagnose

Set `iteration = 1` (track this explicitly — increment before each loop-back).

Classify each failure into one of these categories:

| Category | Signals | Local verification command |
|----------|---------|--------------------------|
| **Ruff lint** | ruff errors, lint violations | `uv run ruff check src/ tests/` |
| **Mypy typecheck** | type errors, mypy output | `uv run mypy src/` |
| **Pytest** | test failures, assertion errors | `uv run pytest tests/` |
| **NPM lint** | eslint errors, lint violations | `cd frontend && npm run lint` |
| **NPM typecheck** | TypeScript errors, tsc output | `cd frontend && npm run typecheck` |
| **NPM test** | vitest/jest failures | `cd frontend && npm test` |
| **Unknown** | infra, dependency, timeout, permissions | *Cannot auto-fix* |

If **all** failures are "Unknown": report to the user: (1) which jobs failed, (2) relevant log excerpt (max 20 lines), (3) your interpretation of the root cause, and (4) suggested next steps. Halt.

If there is a mix of known and unknown: fix the known ones, then clearly warn the user: "CI will still fail after pushing because [unknown failure summary] cannot be auto-resolved. Review and fix manually before pushing."

### Step 4: Fix

Apply fixes for each identified failure type. Prefer minimal targeted changes — do not refactor surrounding code:
- **Lint:** auto-fix with `uv run ruff check --fix src/ tests/` first; manual edits for what auto-fix can't resolve
- **Type errors:** fix type annotations, imports, missing types
- **Test failures:** prefer fixing the code unless the test itself is clearly wrong (e.g., hardcoded expected value that changed). If a test appears intentionally failing (xfail, skip markers, TODO comments), flag it to the user rather than modifying
- **Frontend equivalents:** similar approach with npm tooling

### Step 5: Verify Locally

Run the verification commands relevant to the failures you fixed. Backend and frontend checks are independent — run them in parallel when both are needed. All must pass before proceeding.

If fixes touch shared modules or types imported broadly, run the full suite rather than just targeted checks.

If verification reveals **new failures** not present in the original CI logs and `iteration < 3`, increment iteration and loop back to Step 3. If `iteration >= 3`, report: (1) what was fixed so far, (2) unresolved failures with log excerpts, (3) recommendation: "The partial fixes are staged. You can commit as-is and push to confirm what remains, or reset and fix manually."

### Step 6: Commit

Display `git diff --stat` so the user can review what changed. Then stage only the files you changed and commit:

```
fix(ci): <concise description of what was fixed>
```

If the commit fails due to a pre-commit hook, treat the hook failure as a new verification failure and loop back to Step 3 (incrementing the iteration counter). Do not use `--no-verify`.

Do **not** push. Report what was fixed and that the commit is ready to push.

Skill complete — no further automated action. The user may push when ready.
