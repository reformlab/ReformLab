# ReformLab Runtime Map

This reference captures the observed `bmad-assist` setup in `/Users/lucas/Workspace/reformlab` as investigated on 2026-03-26.

## Key Files

- Project config: `bmad-assist.yaml`
- Project-local state: `.bmad-assist/state.yaml`
- Per-run timeline: `.bmad-assist/runs/run-*.yaml`
- Human-readable run logs: `.bmad-assist/logs/epic-*.log`
- Prompt snapshots: `.bmad-assist/prompts/run-*/prompt-*.md`
- Story status ledger: `_bmad-output/implementation-artifacts/sprint-status.yaml`
- Story structure source: `_bmad-output/planning-artifacts/epics.md`
- Generated story files: `_bmad-output/implementation-artifacts/*.md`
- Validation outputs: `_bmad-output/implementation-artifacts/story-validations/`
- Code review outputs: `_bmad-output/implementation-artifacts/code-reviews/`
- Benchmark/eval records: `_bmad-output/implementation-artifacts/benchmarks/`

## Observed Local Configuration

`bmad-assist.yaml` points `paths.project_knowledge` at `_bmad-output/planning-artifacts`.

That means runtime discovery starts from generated planning artifacts, not from `docs/`.

Observed phase loop in this project:

1. `create_story`
2. `validate_story`
3. `validate_story_synthesis`
4. `dev_story`
5. `code_review`
6. `code_review_synthesis`

Observed major per-phase model choices:

- `create_story`: `claude-subprocess / sonnet` with display name `glm-4.7`
- `dev_story`: `claude-subprocess / sonnet` with display name `glm-4.7`
- `validate_story`: parallel reviewers `claude-subprocess / sonnet` and `codex / gpt-5.3-codex`
- `validate_story_synthesis`: `claude-subprocess / sonnet` with display name `glm-4.7`
- `code_review`: parallel reviewers `claude-subprocess / sonnet` and `codex / gpt-5.3-codex`
- `code_review_synthesis`: `claude-subprocess / sonnet` with display name `glm-4.7`

## What Each Artifact Tells You

### `epics.md`

Defines epic and story structure.

In ReformLab, this is a consolidated file with:

- frontmatter
- epic index table
- convention sections
- detailed epic sections

Important observed behavior:

- this file is not in the strict “Story X.Y” format everywhere
- `bmad-assist` logs show fallback parsing for non-standard sections

Example observed log message:

- “Non-standard story format ... Using fallback parser (sequential numbering)”

### `sprint-status.yaml`

This is the practical status authority when present.

It records:

- epic status entries such as `epic-20: in-progress`
- story status keys such as `20-4-build-population-library-and-data-explorer-stage: in-progress`

Observed current state during investigation:

- `epic-20: in-progress`
- `20-1`, `20-2`, `20-3`: `done`
- `20-4`: `in-progress`
- `20-5` through `20-8`: `backlog`

### `.bmad-assist/state.yaml`

Tracks the live loop position and crash-resume state.

Observed state during investigation:

- `current_epic: 20`
- `current_story: '20.4'`
- `current_phase: validate_story_synthesis`

This file tells you where the loop thinks it is now.

### `.bmad-assist/runs/run-*.yaml`

This is the structured per-run timeline.

Observed fields:

- `cli_args`
- `current_phase`
- `epic`
- `phase_events`

`phase_events` show start/completion timestamps, provider, model, status, duration, and guard metadata.

Use this when you need an exact phase-by-phase timeline.

### `.bmad-assist/logs/epic-*.log`

This is the easiest file for human debugging.

It shows:

- workflow cache refresh
- epic/story loading
- parser warnings
- provider invocations
- timing
- sprint sync
- git auto-commits
- errors and tracebacks

Observed example:

- one Epic 20 log failed with “Epic 20 not found or has no stories” after fallback parsing loaded only one epic
- later Epic 20 logs succeeded and started from `20.1`

### `.bmad-assist/prompts/run-*/prompt-*.md`

These are saved compiled prompts for each phase.

Observed naming pattern:

- `prompt-20-2-01-create_story-20260325T083318Z.md`
- `prompt-20-2-04-dev_story-20260325T091112Z.md`

The file includes metadata comments:

- epic
- story
- phase
- timestamp

These are useful when you want to know exactly what context the provider received.

### `_bmad-output/implementation-artifacts/benchmarks/*.yaml`

These are evaluation records for individual phase executions.

Observed fields include:

- workflow id
- story epic/story number
- evaluator provider/model
- execution duration
- environment metadata including `bmad_assist_version`

Use these for analysis and benchmarking, not for controlling the next story.

## Practical Runtime Hierarchy

When answering “what is `bmad-assist` doing?” in this repo, use this order:

1. `bmad-assist.yaml` for path/model rules
2. `epics.md` for story topology
3. `sprint-status.yaml` for statuses
4. `.bmad-assist/state.yaml` for current pointer
5. `.bmad-assist/runs/*.yaml` and `.bmad-assist/logs/*.log` for execution history
6. `.bmad-assist/prompts/run-*/` for exact compiled prompt payloads

## Known Project-Specific Nuance

ReformLab’s consolidated `epics.md` contains index and convention sections before detailed epics. The parser can log fallback behavior on this file. When explaining story loading problems, mention that the issue is local formatting compatibility, not a generic `bmad-assist` rule.
