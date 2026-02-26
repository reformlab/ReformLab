#!/bin/bash
# overnight-build.sh — Full BMAD cycle: Create Story → Dev Story → Code Review
# Claude handles creation & development, Codex handles reviews
# Run: chmod +x overnight-build.sh && ./overnight-build.sh

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${PROJECT_DIR}/logs/overnight-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$LOG_DIR"

CODEX="npx @openai/codex"

# Common context paths for all prompts
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

# All stories grouped by epic, in order
# Format: "epic_number:story_id"
STORIES=(
  # Epic 1 — remaining
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

CURRENT_EPIC=""
EPIC_FIRST_COMMIT=""
STORY_COUNT=0
TOTAL=${#STORIES[@]}

echo "============================================"
echo "  OVERNIGHT BUILD — ${TOTAL} stories"
echo "  Claude: Create Story + Dev Story"
echo "  Codex:  Story Validation + Code Review"
echo "  Logs: ${LOG_DIR}"
echo "  Started: $(date)"
echo "============================================"

# Capture the starting commit for diffing
STARTING_COMMIT="$(git rev-parse HEAD)"

for entry in "${STORIES[@]}"; do
  EPIC="${entry%%:*}"
  STORY="${entry#*:}"
  STORY_COUNT=$((STORY_COUNT + 1))

  # Track epic transitions — run Codex code review at epic boundary
  if [[ "$EPIC" != "$CURRENT_EPIC" ]]; then
    if [[ -n "$CURRENT_EPIC" ]]; then
      echo ""
      echo ">>> Epic ${CURRENT_EPIC} complete. Codex code review..."

      # Codex review: diff everything since the epic started
      $CODEX review --uncommitted "
Review all code implemented for Epic ${CURRENT_EPIC} of the ReformLab project.
Check against the story acceptance criteria in _bmad-output/implementation-artifacts/.
Verify: code quality, test coverage, architecture compliance with _bmad-output/planning-artifacts/architecture.md.
Flag any bugs, security issues, missing tests, or deviations from the PRD.
" 2>&1 | tee "${LOG_DIR}/epic-${CURRENT_EPIC}-codex-review.log"

      echo ">>> Epic ${CURRENT_EPIC} Codex review done."
    fi
    CURRENT_EPIC="$EPIC"
    EPIC_FIRST_COMMIT="$(git rev-parse HEAD)"
    echo ""
    echo "============================================"
    echo "  STARTING EPIC ${EPIC}"
    echo "============================================"
  fi

  echo ""
  echo "--- [${STORY_COUNT}/${TOTAL}] Story: ${STORY} ---"

  # Step 1: Claude creates the story
  echo "--- Step 1/3: Create Story (Claude) ---"
  claude -p --dangerously-skip-permissions "
/bmad-bmm-create-story
Create story ${STORY} for Epic ${EPIC}.
Story files location: _bmad-output/implementation-artifacts/
${CONTEXT}
Update sprint-status.yaml to reflect story status changes.
" 2>&1 | tee "${LOG_DIR}/${STORY}-1-create.log"

  # Step 2: Codex validates the story file
  echo "--- Step 2/3: Validate Story (Codex) ---"
  $CODEX exec "
Review the story file at _bmad-output/implementation-artifacts/${STORY}.md
Check that it has:
- Clear acceptance criteria
- Technical tasks that align with the architecture in _bmad-output/planning-artifacts/architecture.md
- Consistent scope (not too big, not too small)
- Dependencies on prior stories are noted
If there are issues, fix the story file directly.
" 2>&1 | tee "${LOG_DIR}/${STORY}-2-validate.log"

  # Step 3: Claude implements the story
  echo "--- Step 3/3: Dev Story (Claude) ---"
  claude -p --dangerously-skip-permissions "
/bmad-bmm-dev-story
Implement story ${STORY} for Epic ${EPIC}.
Story file: _bmad-output/implementation-artifacts/${STORY}.md
${CONTEXT}
Build on existing code in src/. Run tests after implementation.
Update sprint-status.yaml to reflect story status changes.
" 2>&1 | tee "${LOG_DIR}/${STORY}-3-dev.log"

  echo "--- Story ${STORY} done ---"
done

# Final epic review with Codex
if [[ -n "$CURRENT_EPIC" ]]; then
  echo ""
  echo ">>> Final epic (${CURRENT_EPIC}) Codex code review..."
  $CODEX review --uncommitted "
Review all code implemented for Epic ${CURRENT_EPIC} of the ReformLab project.
Check against the story acceptance criteria in _bmad-output/implementation-artifacts/.
Verify: code quality, test coverage, architecture compliance with _bmad-output/planning-artifacts/architecture.md.
Flag any bugs, security issues, missing tests, or deviations from the PRD.
" 2>&1 | tee "${LOG_DIR}/epic-${CURRENT_EPIC}-codex-review.log"
fi

# Final full-project review with Codex
echo ""
echo ">>> Full project Codex review..."
$CODEX review --uncommitted "
Full project review for ReformLab.
Architecture: _bmad-output/planning-artifacts/architecture.md
PRD: _bmad-output/planning-artifacts/prd.md
Check: overall code quality, consistency across epics, test coverage, security, architecture compliance.
Produce a summary of issues found ranked by severity.
" 2>&1 | tee "${LOG_DIR}/final-codex-review.log"

echo ""
echo "============================================"
echo "  OVERNIGHT BUILD COMPLETE"
echo "  Finished: $(date)"
echo "  Logs: ${LOG_DIR}"
echo "============================================"

# Final sprint status via Claude
echo ""
echo ">>> Final sprint status check..."
claude -p --dangerously-skip-permissions "
/bmad-bmm-sprint-status
Summarize the current sprint status.
Sprint status: _bmad-output/implementation-artifacts/sprint-status.yaml
" 2>&1 | tee "${LOG_DIR}/final-sprint-status.log"
