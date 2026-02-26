#!/bin/bash
# overnight-build.sh - Single-epic BMAD cycle for stories not yet done.
# Claude handles create/dev, Codex validates story files and reviews the epic.
# Usage:
#   ./overnight-build.sh <epic-number>
#   TARGET_EPIC=<epic-number> ./overnight-build.sh
# If no epic is provided, the script auto-selects the first in-progress epic
# from sprint-status.yaml.
#
# Options (env vars):
#   DRY_RUN=1              Print what would run without executing
#   SKIP_TESTS=1           Skip the pytest gate after dev
#   SKIP_CODEX_REVIEW=1    Skip the final Codex epic review

set -uo pipefail
# Note: -e is intentionally omitted. We handle errors per-story so one
# failure doesn't kill the entire overnight run.

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

SPRINT_STATUS_FILE="_bmad-output/implementation-artifacts/sprint-status.yaml"
DRY_RUN="${DRY_RUN:-0}"
SKIP_TESTS="${SKIP_TESTS:-0}"
SKIP_CODEX_REVIEW="${SKIP_CODEX_REVIEW:-0}"

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "ERROR: Required command not found: $cmd"
    exit 1
  fi
}

# Flat-key YAML parser. Handles only simple "key: value" lines.
# Limitations: no nested structures, no multi-line values, no quoted strings.
# Strips inline comments (anything after " #").
get_status_value() {
  local key="$1"
  awk -F': *' -v wanted_key="$key" '
    {
      found_key = $1
      found_value = $2
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", found_key)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", found_value)
      sub(/[[:space:]]+#.*/, "", found_value)
      if (found_key == wanted_key) {
        print found_value
        exit
      }
    }
  ' "$SPRINT_STATUS_FILE"
}

detect_default_epic() {
  awk -F': *' '
    {
      found_key = $1
      found_value = $2
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", found_key)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", found_value)
      sub(/[[:space:]]+#.*/, "", found_value)
      if (found_key ~ /^epic-[0-9]+$/ && found_value == "in-progress") {
        sub(/^epic-/, "", found_key)
        print found_key
        exit
      }
    }
  ' "$SPRINT_STATUS_FILE"
}

# Auto-commit all changes with a conventional message.
# Usage: git_checkpoint "story-id" "phase description"
git_checkpoint() {
  local story="$1"
  local phase="$2"
  if [[ -z "$(git status --porcelain)" ]]; then
    echo "  (no changes to commit)"
    return 0
  fi
  git add -A
  git commit -m "overnight-build: ${story} — ${phase}" --no-gpg-sign --quiet
  echo "  Committed: overnight-build: ${story} — ${phase}"
}

# Verify sprint-status.yaml has a sane value for a story key.
# Returns 0 if value is a known status, 1 otherwise.
verify_story_status() {
  local story="$1"
  local expected_statuses="backlog ready-for-dev in-progress review done"
  local current
  current="$(get_status_value "$story")"
  for s in $expected_statuses; do
    if [[ "$current" == "$s" ]]; then
      return 0
    fi
  done
  echo "WARNING: Story ${story} has unexpected status '${current}' in sprint-status.yaml"
  return 1
}

# Run pytest and return its exit code. Logs output.
run_test_gate() {
  local story="$1"
  local log_file="$2"

  if [[ "$SKIP_TESTS" == "1" ]]; then
    echo "  (test gate skipped via SKIP_TESTS=1)"
    return 0
  fi

  echo "  Running pytest..."
  local rc=0
  python -m pytest tests/ --tb=short -q 2>&1 | tee "$log_file" || rc=$?
  if [[ $rc -ne 0 ]]; then
    echo "  FAIL: Tests failed after implementing ${story} (exit code ${rc})"
  else
    echo "  PASS: All tests passed"
  fi
  return $rc
}

if [[ ! -f "$SPRINT_STATUS_FILE" ]]; then
  echo "ERROR: Missing sprint status file: $SPRINT_STATUS_FILE"
  exit 1
fi

require_command claude
require_command npx
require_command git

TARGET_EPIC="${1:-${TARGET_EPIC:-}}"
if [[ -z "$TARGET_EPIC" ]]; then
  TARGET_EPIC="$(detect_default_epic || true)"
fi
if [[ -z "$TARGET_EPIC" ]]; then
  echo "ERROR: Could not determine target epic."
  echo "Pass it explicitly: ./overnight-build.sh <epic-number>"
  exit 1
fi
if [[ ! "$TARGET_EPIC" =~ ^[0-9]+$ ]]; then
  echo "ERROR: Epic must be numeric (received: $TARGET_EPIC)"
  exit 1
fi

LOG_DIR="${PROJECT_DIR}/logs/overnight-epic-${TARGET_EPIC}-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$LOG_DIR"

CODEX=(npx @openai/codex)

# Common context paths for all prompts.
CONTEXT="
Architecture: _bmad-output/planning-artifacts/architecture.md
PRD: _bmad-output/planning-artifacts/prd.md
Backlog: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md
Sprint status: _bmad-output/implementation-artifacts/sprint-status.yaml
Sprint change proposal: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-25.md
UX Design: _bmad-output/planning-artifacts/ux-design-specification.md
Existing code: src/
Tests: tests/
"

# All stories grouped by epic, in order.
# Format: "epic_number:story_id"
STORIES=(
  # Epic 1
  "1:1-5-add-data-quality-checks"
  "1:1-6-add-direct-openfisca-api-orchestration-mode"
  "1:1-7-create-compatibility-matrix"
  "1:1-8-set-up-project-scaffold"
  # Epic 2
  "2:2-1-define-scenario-template-schema"
  "2:2-2-implement-carbon-tax-template-pack"
  "2:2-3-implement-subsidy-rebate-feebate-template-pack"
  "2:2-4-build-scenario-registry"
  "2:2-5-implement-scenario-cloning"
  "2:2-6-add-schema-migration-helper"
  "2:2-7-implement-yaml-json-workflow-configuration"
  # Epic 3
  "3:3-1-implement-yearly-loop-orchestrator"
  "3:3-2-define-orchestrator-step-interface"
  "3:3-3-implement-carry-forward-step"
  "3:3-4-implement-vintage-transition-step"
  "3:3-5-integrate-computationadapter-calls"
  "3:3-6-log-seed-controls"
  "3:3-7-produce-scenario-year-panel-output"
  # Epic 4
  "4:4-1-implement-distributional-indicators"
  "4:4-2-implement-geographic-aggregation-indicators"
  "4:4-3-implement-welfare-indicators"
  "4:4-4-implement-fiscal-indicators"
  "4:4-5-implement-scenario-comparison-tables"
  "4:4-6-implement-custom-derived-indicator-formulas"
  # Epic 5
  "5:5-1-define-immutable-run-manifest-schema"
  "5:5-2-capture-assumptions-mappings-parameters"
  "5:5-3-implement-run-lineage-graph"
  "5:5-4-hash-input-output-artifacts"
  "5:5-5-add-reproducibility-check-harness"
  "5:5-6-add-warning-system-for-unvalidated-templates"
  # Epic 6
  "6:6-1-implement-stable-python-api"
  "6:6-2-build-quickstart-notebook"
  "6:6-3-build-advanced-notebook"
  "6:6-4-implement-early-no-code-gui"
  "6:6-5-add-export-actions"
  "6:6-6-improve-operational-error-ux"
  # Epic 7
  "7:7-1-verify-simulation-outputs-against-benchmarks"
  "7:7-2-warn-before-exceeding-memory-limits"
  "7:7-3-enforce-ci-quality-gates"
  "7:7-4-external-pilot-run-carbon-tax-workflow"
  "7:7-5-define-phase-1-exit-checklist"
)

EPIC_STORIES=()
DONE_STORIES=()
PENDING_STORIES=()

for entry in "${STORIES[@]}"; do
  epic="${entry%%:*}"
  story="${entry#*:}"
  if [[ "$epic" != "$TARGET_EPIC" ]]; then
    continue
  fi

  EPIC_STORIES+=("$story")
  status="$(get_status_value "$story")"
  if [[ -z "$status" ]]; then
    status="unknown"
  fi

  if [[ "$status" == "done" ]]; then
    DONE_STORIES+=("$story")
  else
    PENDING_STORIES+=("$story")
  fi
done

if [[ ${#EPIC_STORIES[@]} -eq 0 ]]; then
  echo "ERROR: No stories configured for epic ${TARGET_EPIC} in overnight-build.sh"
  exit 1
fi

# Record the baseline commit so the final Codex review only sees
# changes made during this run (not pre-existing uncommitted work).
BASELINE_DIRTY=""
if [[ -n "$(git status --porcelain)" ]]; then
  BASELINE_DIRTY=1
  echo "WARNING: Working tree is not clean. Stashing pre-existing changes."
  git stash push -m "overnight-build: pre-existing changes" --quiet
  echo "  Stashed. Will restore after the run."
fi
BASELINE_COMMIT="$(git rev-parse HEAD)"

echo "============================================"
echo "  OVERNIGHT BUILD - Epic ${TARGET_EPIC}"
echo "  Claude: Create Story + Dev Story (fresh print sessions)"
echo "  Codex:  Story Validation + Epic Review"
echo "  Pending stories: ${#PENDING_STORIES[@]} / ${#EPIC_STORIES[@]}"
echo "  Already done: ${#DONE_STORIES[@]}"
echo "  Baseline commit: ${BASELINE_COMMIT:0:10}"
echo "  Logs: ${LOG_DIR}"
echo "  Started: $(date)"
[[ "$DRY_RUN" == "1" ]] && echo "  *** DRY RUN MODE ***"
echo "============================================"

if [[ ${#DONE_STORIES[@]} -gt 0 ]]; then
  printf 'Skipping done stories:\n- %s\n' "${DONE_STORIES[@]}"
fi

if [[ ${#PENDING_STORIES[@]} -eq 0 ]]; then
  echo ""
  echo "No pending stories for epic ${TARGET_EPIC}. Nothing to run."
  [[ "$BASELINE_DIRTY" == "1" ]] && git stash pop --quiet
  exit 0
fi

story_count=0
total=${#PENDING_STORIES[@]}
FAILED_STORIES=()
SUCCEEDED_STORIES=()

for story in "${PENDING_STORIES[@]}"; do
  story_count=$((story_count + 1))
  status="$(get_status_value "$story")"
  story_file="_bmad-output/implementation-artifacts/${story}.md"
  if [[ -z "$status" ]]; then
    status="unknown"
  fi

  echo ""
  echo "--- [${story_count}/${total}] Story: ${story} (status: ${status}) ---"

  story_failed=0

  # Step 1: Create story (only for backlog stories or missing files).
  if [[ "$status" == "backlog" || ! -f "$story_file" ]]; then
    echo "--- Step 1/4: Create Story (Claude) ---"
    if [[ "$DRY_RUN" == "1" ]]; then
      echo "  [dry-run] Would run: claude -p /bmad-bmm-create-story for ${story}"
    else
      if ! claude -p --no-session-persistence --dangerously-skip-permissions "
/bmad-bmm-create-story
Create story ${story} for Epic ${TARGET_EPIC}.
Story files location: _bmad-output/implementation-artifacts/
${CONTEXT}
Update sprint-status.yaml to reflect story status changes.
" 2>&1 | tee "${LOG_DIR}/${story}-1-create.log"; then
        echo "  WARN: Create story step exited non-zero for ${story}"
      fi
      git_checkpoint "$story" "create story"
      verify_story_status "$story" || true
    fi
  else
    echo "--- Step 1/4: Skipped (status is ${status}) ---"
  fi

  # Step 2: Validate story file (Codex).
  echo "--- Step 2/4: Validate Story (Codex) ---"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  [dry-run] Would run: codex exec for ${story}"
  else
    if ! "${CODEX[@]}" exec --sandbox workspace-write --ephemeral "
Review the story file at _bmad-output/implementation-artifacts/${story}.md
Check that it has:
- Clear acceptance criteria
- Technical tasks that align with the architecture in _bmad-output/planning-artifacts/architecture.md
- Consistent scope (not too big, not too small)
- Dependencies on prior stories are noted
If there are issues, fix the story file directly.
" 2>&1 | tee "${LOG_DIR}/${story}-2-validate.log"; then
      echo "  WARN: Codex validation exited non-zero for ${story}"
    fi
    git_checkpoint "$story" "validate story"
  fi

  # Step 3: Implement story (Claude).
  echo "--- Step 3/4: Dev Story (Claude) ---"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  [dry-run] Would run: claude -p /bmad-bmm-dev-story for ${story}"
  else
    if ! claude -p --no-session-persistence --dangerously-skip-permissions "
/bmad-bmm-dev-story
Implement story ${story} for Epic ${TARGET_EPIC}.
Story file: _bmad-output/implementation-artifacts/${story}.md
${CONTEXT}
Build on existing code in src/. Run tests after implementation.
Update sprint-status.yaml to reflect story status changes.
" 2>&1 | tee "${LOG_DIR}/${story}-3-dev.log"; then
      echo "  WARN: Dev story step exited non-zero for ${story}"
    fi
    verify_story_status "$story" || true
  fi

  # Step 4: Test gate — hard pytest check after dev.
  echo "--- Step 4/4: Test Gate ---"
  if [[ "$DRY_RUN" == "1" ]]; then
    echo "  [dry-run] Would run: pytest"
  else
    if ! run_test_gate "$story" "${LOG_DIR}/${story}-4-tests.log"; then
      story_failed=1
      echo "  Story ${story} FAILED the test gate."
    fi
    git_checkpoint "$story" "dev + tests"
  fi

  if [[ $story_failed -eq 1 ]]; then
    FAILED_STORIES+=("$story")
    echo "--- Story ${story} FAILED — continuing to next story ---"
  else
    SUCCEEDED_STORIES+=("$story")
    echo "--- Story ${story} complete ---"
  fi
done

# Epic-level Codex review — only reviews changes from this run.
echo ""
if [[ "$SKIP_CODEX_REVIEW" == "1" ]]; then
  echo ">>> Skipping Codex epic review (SKIP_CODEX_REVIEW=1)"
elif [[ "$DRY_RUN" == "1" ]]; then
  echo ">>> [dry-run] Would run: codex review for epic ${TARGET_EPIC}"
else
  echo ">>> Epic ${TARGET_EPIC} Codex code review (changes since ${BASELINE_COMMIT:0:10})..."
  "${CODEX[@]}" review --diff "${BASELINE_COMMIT}..HEAD" "
Review all code implemented for Epic ${TARGET_EPIC} of the ReformLab project.
Check against the story acceptance criteria in _bmad-output/implementation-artifacts/.
Verify: code quality, test coverage, architecture compliance with _bmad-output/planning-artifacts/architecture.md.
Flag any bugs, security issues, missing tests, or deviations from the PRD.
" 2>&1 | tee "${LOG_DIR}/epic-${TARGET_EPIC}-codex-review.log" || true
fi

# Restore stashed changes if we stashed at the start.
if [[ "$BASELINE_DIRTY" == "1" ]]; then
  echo ""
  echo ">>> Restoring pre-existing stashed changes..."
  git stash pop --quiet || echo "  WARN: Could not restore stash (may need manual resolution)"
fi

echo ""
echo "============================================"
echo "  OVERNIGHT BUILD COMPLETE"
echo "  Epic: ${TARGET_EPIC}"
echo "  Succeeded: ${#SUCCEEDED_STORIES[@]} / ${total}"
if [[ ${#FAILED_STORIES[@]} -gt 0 ]]; then
  echo "  FAILED: ${FAILED_STORIES[*]}"
fi
echo "  Finished: $(date)"
echo "  Logs: ${LOG_DIR}"
echo "============================================"

echo ""
echo ">>> Final sprint status check..."
if [[ "$DRY_RUN" == "1" ]]; then
  echo "  [dry-run] Would run: claude -p /bmad-bmm-sprint-status"
else
  claude -p --no-session-persistence --dangerously-skip-permissions "
/bmad-bmm-sprint-status
Summarize the current sprint status.
Sprint status: _bmad-output/implementation-artifacts/sprint-status.yaml
" 2>&1 | tee "${LOG_DIR}/final-sprint-status.log"
fi

# Exit with failure if any stories failed.
if [[ ${#FAILED_STORIES[@]} -gt 0 ]]; then
  exit 1
fi
