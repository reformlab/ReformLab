#!/bin/bash
# test_overnight_build.sh — Unit tests for overnight-build.sh
#
# Runs in an isolated temp directory with mock commands (claude, npx, git, python).
# Each test function sets up its own scenario and asserts expected behavior.
#
# Usage: bash tests/test_overnight_build.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_UNDER_TEST="${SCRIPT_DIR}/overnight-build.sh"

TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
FAILURES=()

# Colors (disabled if not a terminal).
if [[ -t 1 ]]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; NC=''
fi

pass() {
  TESTS_PASSED=$((TESTS_PASSED + 1))
  echo -e "  ${GREEN}PASS${NC}: $1"
}

fail() {
  TESTS_FAILED=$((TESTS_FAILED + 1))
  FAILURES+=("$1: $2")
  echo -e "  ${RED}FAIL${NC}: $1 — $2"
}

assert_eq() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    pass "$label"
  else
    fail "$label" "expected '${expected}', got '${actual}'"
  fi
}

assert_contains() {
  local label="$1" needle="$2" haystack="$3"
  if echo "$haystack" | grep -qF "$needle"; then
    pass "$label"
  else
    fail "$label" "output does not contain '${needle}'"
  fi
}

assert_not_contains() {
  local label="$1" needle="$2" haystack="$3"
  if echo "$haystack" | grep -qF -- "$needle"; then
    fail "$label" "output should not contain '${needle}'"
  else
    pass "$label"
  fi
}

assert_file_exists() {
  local label="$1" path="$2"
  if [[ -f "$path" ]]; then
    pass "$label"
  else
    fail "$label" "file does not exist: ${path}"
  fi
}

assert_exit_code() {
  local label="$1" expected="$2" actual="$3"
  if [[ "$expected" == "$actual" ]]; then
    pass "$label"
  else
    fail "$label" "expected exit code ${expected}, got ${actual}"
  fi
}

# ---------------------------------------------------------------------------
# Test environment setup
# ---------------------------------------------------------------------------

WORK_DIR=""
SAVED_PATH="$PATH"

setup_test_env() {
  # Restore PATH to avoid stacking mock dirs from prior tests.
  export PATH="$SAVED_PATH"

  WORK_DIR="$(mktemp -d)"
  export WORK_DIR
  mkdir -p "${WORK_DIR}/_bmad-output/implementation-artifacts"
  mkdir -p "${WORK_DIR}/_bmad-output/planning-artifacts"
  mkdir -p "${WORK_DIR}/src"
  mkdir -p "${WORK_DIR}/tests"
  mkdir -p "${WORK_DIR}/bin"

  # Copy the script under test.
  cp "$SCRIPT_UNDER_TEST" "${WORK_DIR}/overnight-build.sh"
  chmod +x "${WORK_DIR}/overnight-build.sh"

  # Initialize a real git repo so git operations work.
  (cd "$WORK_DIR" && git init -q && git add -A && git commit -m "init" -q --allow-empty)

  # Create mock commands in bin/ and prepend to PATH.
  # Default mocks: succeed silently.
  create_mock "claude" 'echo "mock-claude: $*"'
  create_mock "npx" 'echo "mock-npx: $*"'
  # python mock: default to passing tests
  create_mock "python" '
if [[ "$1" == "-m" && "$2" == "pytest" ]]; then
  echo "mock-pytest: all tests passed"
  exit 0
fi
echo "mock-python: $*"
'

  export PATH="${WORK_DIR}/bin:${PATH}"
}

create_mock() {
  local name="$1"
  local body="$2"
  cat > "${WORK_DIR}/bin/${name}" <<MOCK_EOF
#!/bin/bash
${body}
MOCK_EOF
  chmod +x "${WORK_DIR}/bin/${name}"
}

teardown_test_env() {
  export PATH="$SAVED_PATH"
  if [[ -n "$WORK_DIR" && -d "$WORK_DIR" ]]; then
    rm -rf "$WORK_DIR"
  fi
  WORK_DIR=""
}

write_sprint_status() {
  local content="$1"
  cat > "${WORK_DIR}/_bmad-output/implementation-artifacts/sprint-status.yaml" <<< "$content"
  # Commit so the file is tracked.
  (cd "$WORK_DIR" && git add -A && git commit -m "add sprint status" -q)
}

# Run the script in the test work dir.
# Returns: sets RUN_OUTPUT and RUN_EXIT_CODE
run_script() {
  RUN_EXIT_CODE=0
  RUN_OUTPUT="$(cd "$WORK_DIR" && DRY_RUN=1 bash ./overnight-build.sh "$@" 2>&1)" || RUN_EXIT_CODE=$?
}

# Run the script without dry-run (for git checkpoint tests, etc.).
run_script_live() {
  RUN_EXIT_CODE=0
  RUN_OUTPUT="$(cd "$WORK_DIR" && bash ./overnight-build.sh "$@" 2>&1)" || RUN_EXIT_CODE=$?
}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

test_missing_sprint_status_file() {
  echo ">> test_missing_sprint_status_file"
  setup_test_env
  rm -f "${WORK_DIR}/_bmad-output/implementation-artifacts/sprint-status.yaml"
  run_script 1
  assert_exit_code "exits 1 when sprint-status.yaml missing" "1" "$RUN_EXIT_CODE"
  assert_contains "error message mentions missing file" "Missing sprint status file" "$RUN_OUTPUT"
  teardown_test_env
}

test_invalid_epic_number() {
  echo ">> test_invalid_epic_number"
  setup_test_env
  write_sprint_status "epic-1: in-progress"
  run_script "abc"
  assert_exit_code "exits 1 for non-numeric epic" "1" "$RUN_EXIT_CODE"
  assert_contains "error says epic must be numeric" "Epic must be numeric" "$RUN_OUTPUT"
  teardown_test_env
}

test_no_stories_for_epic() {
  echo ">> test_no_stories_for_epic"
  setup_test_env
  write_sprint_status "epic-99: in-progress"
  run_script 99
  assert_exit_code "exits 1 when no stories for epic" "1" "$RUN_EXIT_CODE"
  assert_contains "error mentions no stories" "No stories configured" "$RUN_OUTPUT"
  teardown_test_env
}

test_auto_detect_epic() {
  echo ">> test_auto_detect_epic"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: backlog
1-6-add-direct-openfisca-api-orchestration-mode: backlog
1-7-create-compatibility-matrix: backlog
1-8-set-up-project-scaffold: backlog
YAML
)"
  run_script
  assert_exit_code "auto-detect succeeds" "0" "$RUN_EXIT_CODE"
  assert_contains "detects epic 1" "Epic 1" "$RUN_OUTPUT"
  teardown_test_env
}

test_skips_done_stories() {
  echo ">> test_skips_done_stories"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: done
1-6-add-direct-openfisca-api-orchestration-mode: done
1-7-create-compatibility-matrix: backlog
1-8-set-up-project-scaffold: backlog
YAML
)"
  run_script 1
  assert_exit_code "succeeds" "0" "$RUN_EXIT_CODE"
  assert_contains "reports done stories" "Already done: 2" "$RUN_OUTPUT"
  assert_contains "reports pending stories" "Pending stories: 2" "$RUN_OUTPUT"
  assert_not_contains "does not process done story" "[dry-run] Would run: claude -p /bmad-bmm-dev-story for 1-5" "$RUN_OUTPUT"
  assert_contains "processes pending story" "1-7-create-compatibility-matrix" "$RUN_OUTPUT"
  teardown_test_env
}

test_all_done_exits_cleanly() {
  echo ">> test_all_done_exits_cleanly"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: done
1-6-add-direct-openfisca-api-orchestration-mode: done
1-7-create-compatibility-matrix: done
1-8-set-up-project-scaffold: done
YAML
)"
  run_script 1
  assert_exit_code "exits 0 when all done" "0" "$RUN_EXIT_CODE"
  assert_contains "nothing to run message" "Nothing to run" "$RUN_OUTPUT"
  teardown_test_env
}

test_dry_run_does_not_execute() {
  echo ">> test_dry_run_does_not_execute"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: backlog
1-6-add-direct-openfisca-api-orchestration-mode: backlog
1-7-create-compatibility-matrix: backlog
1-8-set-up-project-scaffold: backlog
YAML
)"
  run_script 1
  assert_exit_code "dry run succeeds" "0" "$RUN_EXIT_CODE"
  assert_contains "shows dry-run marker" "DRY RUN MODE" "$RUN_OUTPUT"
  assert_contains "dry-run for create" "[dry-run] Would run: claude" "$RUN_OUTPUT"
  assert_contains "dry-run for codex" "[dry-run] Would run: codex" "$RUN_OUTPUT"
  assert_contains "dry-run for pytest" "[dry-run] Would run: pytest" "$RUN_OUTPUT"
  assert_not_contains "mock claude not actually called" "mock-claude" "$RUN_OUTPUT"
  teardown_test_env
}

test_skips_create_for_non_backlog() {
  echo ">> test_skips_create_for_non_backlog"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: done
1-6-add-direct-openfisca-api-orchestration-mode: done
1-7-create-compatibility-matrix: ready-for-dev
1-8-set-up-project-scaffold: backlog
YAML
)"
  # Create the story file for 1-7 so the "missing file" fallback doesn't trigger.
  echo "# Story" > "${WORK_DIR}/_bmad-output/implementation-artifacts/1-7-create-compatibility-matrix.md"
  (cd "$WORK_DIR" && git add -A && git commit -m "add story file" -q)

  run_script 1
  assert_exit_code "succeeds" "0" "$RUN_EXIT_CODE"
  assert_contains "skips create for ready-for-dev" "Step 1/4: Skipped (status is ready-for-dev)" "$RUN_OUTPUT"
  # 1-8 is backlog so create should run.
  assert_contains "runs create for backlog" "[dry-run] Would run: claude -p /bmad-bmm-create-story for 1-8" "$RUN_OUTPUT"
  teardown_test_env
}

test_git_checkpoint_creates_commits() {
  echo ">> test_git_checkpoint_creates_commits"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: done
1-6-add-direct-openfisca-api-orchestration-mode: done
1-7-create-compatibility-matrix: ready-for-dev
1-8-set-up-project-scaffold: done
YAML
)"
  # Create the story file so create step is skipped.
  echo "# Story 1-7" > "${WORK_DIR}/_bmad-output/implementation-artifacts/1-7-create-compatibility-matrix.md"
  (cd "$WORK_DIR" && git add -A && git commit -m "story file" -q)

  # Make claude mock produce a file change so git_checkpoint has something to commit.
  create_mock "claude" 'echo "implemented" >> src/changes.py; echo "mock-claude: $*"'

  local before_count
  before_count="$(cd "$WORK_DIR" && git rev-list --count HEAD)"

  run_script_live 1

  local after_count
  after_count="$(cd "$WORK_DIR" && git rev-list --count HEAD)"

  # Should have at least one new commit from git_checkpoint.
  if [[ "$after_count" -gt "$before_count" ]]; then
    pass "git checkpoint created new commits"
  else
    fail "git checkpoint created new commits" "commit count before=${before_count} after=${after_count}"
  fi

  # Check that commit messages follow the convention.
  local last_msg
  last_msg="$(cd "$WORK_DIR" && git log --oneline -1)"
  assert_contains "commit message has overnight-build prefix" "overnight-build:" "$last_msg"
  teardown_test_env
}

test_test_gate_failure_marks_story_failed() {
  echo ">> test_test_gate_failure_marks_story_failed"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: done
1-6-add-direct-openfisca-api-orchestration-mode: done
1-7-create-compatibility-matrix: done
1-8-set-up-project-scaffold: ready-for-dev
YAML
)"
  echo "# Story 1-8" > "${WORK_DIR}/_bmad-output/implementation-artifacts/1-8-set-up-project-scaffold.md"
  (cd "$WORK_DIR" && git add -A && git commit -m "story file" -q)

  # Make pytest fail.
  create_mock "python" '
if [[ "$1" == "-m" && "$2" == "pytest" ]]; then
  echo "FAILED test_something"
  exit 1
fi
echo "mock-python: $*"
'

  run_script_live 1

  assert_exit_code "exits 1 when tests fail" "1" "$RUN_EXIT_CODE"
  assert_contains "reports test gate failure" "FAILED the test gate" "$RUN_OUTPUT"
  assert_contains "story in failed list" "FAILED:" "$RUN_OUTPUT"
  teardown_test_env
}

test_continues_after_story_failure() {
  echo ">> test_continues_after_story_failure"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: done
1-6-add-direct-openfisca-api-orchestration-mode: done
1-7-create-compatibility-matrix: ready-for-dev
1-8-set-up-project-scaffold: ready-for-dev
YAML
)"
  echo "# Story 1-7" > "${WORK_DIR}/_bmad-output/implementation-artifacts/1-7-create-compatibility-matrix.md"
  echo "# Story 1-8" > "${WORK_DIR}/_bmad-output/implementation-artifacts/1-8-set-up-project-scaffold.md"
  (cd "$WORK_DIR" && git add -A && git commit -m "story files" -q)

  # Track which stories pytest is called for using a counter file.
  create_mock "python" '
if [[ "$1" == "-m" && "$2" == "pytest" ]]; then
  COUNTER_FILE="${WORK_DIR:-/tmp}/.pytest_call_count"
  if [[ ! -f "$COUNTER_FILE" ]]; then
    echo "1" > "$COUNTER_FILE"
    echo "FAILED first story"
    exit 1
  else
    count=$(cat "$COUNTER_FILE")
    echo $((count + 1)) > "$COUNTER_FILE"
    echo "PASSED second story"
    exit 0
  fi
fi
'
  run_script_live 1

  # Even though first story fails, second story should still be attempted.
  assert_contains "processes first story" "1-7-create-compatibility-matrix" "$RUN_OUTPUT"
  assert_contains "processes second story" "1-8-set-up-project-scaffold" "$RUN_OUTPUT"
  assert_contains "reports failure" "FAILED" "$RUN_OUTPUT"
  # The script should have processed both.
  assert_contains "shows succeeded count" "Succeeded: 1 / 2" "$RUN_OUTPUT"
  teardown_test_env
}

test_stash_and_restore_dirty_worktree() {
  echo ">> test_stash_and_restore_dirty_worktree"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: done
1-6-add-direct-openfisca-api-orchestration-mode: done
1-7-create-compatibility-matrix: done
1-8-set-up-project-scaffold: done
YAML
)"

  # Create a dirty file.
  echo "dirty content" > "${WORK_DIR}/dirty-file.txt"

  run_script_live 1

  assert_exit_code "succeeds" "0" "$RUN_EXIT_CODE"
  assert_contains "warns about dirty tree" "Stashing pre-existing changes" "$RUN_OUTPUT"
  # After the run, the dirty file should be restored.
  if [[ -f "${WORK_DIR}/dirty-file.txt" ]]; then
    pass "dirty file restored after stash pop"
  else
    fail "dirty file restored after stash pop" "file not found"
  fi
  teardown_test_env
}

test_skip_tests_env_var() {
  echo ">> test_skip_tests_env_var"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: done
1-6-add-direct-openfisca-api-orchestration-mode: done
1-7-create-compatibility-matrix: done
1-8-set-up-project-scaffold: ready-for-dev
YAML
)"
  echo "# Story 1-8" > "${WORK_DIR}/_bmad-output/implementation-artifacts/1-8-set-up-project-scaffold.md"
  (cd "$WORK_DIR" && git add -A && git commit -m "story file" -q)

  # Make pytest fail — but SKIP_TESTS should bypass it.
  create_mock "python" 'exit 1'

  RUN_EXIT_CODE=0
  RUN_OUTPUT="$(cd "$WORK_DIR" && SKIP_TESTS=1 bash ./overnight-build.sh 1 2>&1)" || RUN_EXIT_CODE=$?

  assert_exit_code "succeeds with SKIP_TESTS=1" "0" "$RUN_EXIT_CODE"
  assert_contains "test gate skipped" "test gate skipped" "$RUN_OUTPUT"
  teardown_test_env
}

test_log_directory_created() {
  echo ">> test_log_directory_created"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: backlog
1-6-add-direct-openfisca-api-orchestration-mode: done
1-7-create-compatibility-matrix: done
1-8-set-up-project-scaffold: done
YAML
)"

  run_script 1

  # Check that a log directory was created.
  local log_count
  log_count="$(find "${WORK_DIR}/logs" -maxdepth 1 -name "overnight-epic-1-*" -type d | wc -l | tr -d ' ')"
  if [[ "$log_count" -ge 1 ]]; then
    pass "log directory created"
  else
    fail "log directory created" "no log directory found in ${WORK_DIR}/logs"
  fi
  teardown_test_env
}

test_verify_story_status_warns_on_bad_status() {
  echo ">> test_verify_story_status_warns_on_bad_status"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: done
1-6-add-direct-openfisca-api-orchestration-mode: done
1-7-create-compatibility-matrix: done
1-8-set-up-project-scaffold: garbage-status
YAML
)"
  echo "# Story 1-8" > "${WORK_DIR}/_bmad-output/implementation-artifacts/1-8-set-up-project-scaffold.md"
  (cd "$WORK_DIR" && git add -A && git commit -m "story file" -q)

  run_script_live 1

  assert_contains "warns on bad status" "unexpected status" "$RUN_OUTPUT"
  teardown_test_env
}

test_codex_review_uses_diff_range() {
  echo ">> test_codex_review_uses_diff_range"
  setup_test_env
  write_sprint_status "$(cat <<'YAML'
epic-1: in-progress
1-5-add-data-quality-checks: done
1-6-add-direct-openfisca-api-orchestration-mode: done
1-7-create-compatibility-matrix: done
1-8-set-up-project-scaffold: ready-for-dev
YAML
)"
  echo "# Story 1-8" > "${WORK_DIR}/_bmad-output/implementation-artifacts/1-8-set-up-project-scaffold.md"
  (cd "$WORK_DIR" && git add -A && git commit -m "story file" -q)

  # Capture what npx (codex) receives.
  create_mock "npx" 'echo "mock-npx-args: $*"'

  run_script_live 1

  # The final codex review should use --diff, not --uncommitted.
  assert_contains "codex review uses --diff" "review --diff" "$RUN_OUTPUT"
  assert_not_contains "codex review does not use --uncommitted" "--uncommitted" "$RUN_OUTPUT"
  teardown_test_env
}

# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

echo ""
echo "================================================="
echo "  overnight-build.sh test suite"
echo "================================================="
echo ""

test_missing_sprint_status_file
test_invalid_epic_number
test_no_stories_for_epic
test_auto_detect_epic
test_skips_done_stories
test_all_done_exits_cleanly
test_dry_run_does_not_execute
test_skips_create_for_non_backlog
test_git_checkpoint_creates_commits
test_test_gate_failure_marks_story_failed
test_continues_after_story_failure
test_stash_and_restore_dirty_worktree
test_skip_tests_env_var
test_log_directory_created
test_verify_story_status_warns_on_bad_status
test_codex_review_uses_diff_range

echo ""
echo "================================================="
echo "  Results: ${TESTS_PASSED} passed, ${TESTS_FAILED} failed"
echo "================================================="

if [[ ${#FAILURES[@]} -gt 0 ]]; then
  echo ""
  echo "Failures:"
  for f in "${FAILURES[@]}"; do
    echo "  - $f"
  done
fi

echo ""
exit "$TESTS_FAILED"
