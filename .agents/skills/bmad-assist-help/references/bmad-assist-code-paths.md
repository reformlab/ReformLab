# bmad-assist Code Paths

Use this reference to explain how runtime behavior is implemented.

## Path Resolution

Primary file:

- `src/bmad_assist/core/paths.py`

Important behavior:

- `project_knowledge` comes from config if set, otherwise `docs/`
- `epics_dir` search order is:
  - explicit config override
  - `project_knowledge/epics`
  - `docs/epics`
  - auto-discovery
  - fallback to `planning_artifacts/epics`
- search dirs are deduplicated across:
  - `project_knowledge`
  - `planning_artifacts`
  - `docs/`

This matters in ReformLab because `project_knowledge` is `_bmad-output/planning-artifacts`.

## Loading Epics And Stories

Primary files:

- `src/bmad_assist/bmad/state_reader.py`
- `src/bmad_assist/bmad/parser.py`
- `src/bmad_assist/sprint/generator.py`

### Discovery

`read_project_state()`:

1. loads epic files from BMAD docs or configured knowledge path
2. flattens stories
3. applies default `backlog` to missing statuses
4. optionally overlays `sprint-status.yaml`
5. picks the first non-`done` story as current position

### Multi-epic vs sharded

`state_reader._load_epics()` supports:

- sharded `epics/`
- single consolidated `epics.md`

### Parsing story sections

`parser._parse_story_sections()` tries:

1. standard story headers first
2. fallback story parsing for non-standard sections

Standard parsing looks for explicit `Story X.Y` style headers.

Fallback parsing is heuristic and assigns sequential numbers inside the current epic.

Observed runtime warning in ReformLab comes from:

- `parser._parse_fallback_story_sections()`

That log is informational but also a signal that the file shape is not ideal for the parser.

### Sprint-status key mapping

`state_reader._parse_sprint_status_key()` converts keys like:

- `20-4-build-population-library-and-data-explorer-stage`

into:

- `20.4`

`sprint/generator.py` builds these keys from parsed stories using the title slug.

## Which File Controls Status?

Primary file:

- `src/bmad_assist/bmad/state_reader.py`

Key rule:

- story structure is loaded from epic docs
- if `use_sprint_status=True`, status values from `sprint-status.yaml` override embedded story statuses

This is the critical distinction to explain to users.

## CLI Start Point Logic

Primary files:

- `src/bmad_assist/cli.py`
- `src/bmad_assist/cli_start_point.py`

Important behavior:

- `_load_epic_data()` reads project state with `use_sprint_status=True`
- only non-`done` stories are kept in the active epic list
- `--epic` and `--story` resolve against full project state
- story status maps to starting phase:
  - `backlog` -> `create_story`
  - `ready-for-dev` -> `dev_story`
  - `in-progress` -> `dev_story`
  - `review` -> `code_review`

## Loop State

Primary files:

- `src/bmad_assist/core/state.py`
- `src/bmad_assist/core/loop/story_transitions.py`
- `src/bmad_assist/core/loop/runner.py`

Important behavior:

- `.bmad-assist/state.yaml` is the persistent loop pointer
- `current_epic`, `current_story`, `current_phase` drive resume
- `completed_stories` and `completed_epics` protect against reruns
- after story completion, the loop advances to the next incomplete story in order

## Resume And Sprint Repair

Primary file:

- `src/bmad_assist/core/loop/sprint_sync.py`

Important behavior:

- resume validation checks whether `state.yaml` is stale relative to `sprint-status.yaml`
- if sprint status shows work is already done, resume can auto-advance
- sprint sync callbacks update artifacts after phases

## Prompt And Run Tracking

Primary files:

- `src/bmad_assist/core/io.py`
- `src/bmad_assist/core/loop/run_tracking.py`

Important behavior:

- each run gets `.bmad-assist/prompts/run-{timestamp}/`
- each saved prompt is named:
  - `prompt-{epic}-{story}-{phase_seq}-{phase}-{timestamp}.md`
- prompt files include metadata comments for epic, story, phase, timestamp
- `.bmad-assist/runs/run-*.yaml` stores:
  - CLI args
  - current phase
  - phase event timeline
  - provider/model per phase

## What To Cite In Answers

For “how does it read epics?” cite:

- `state_reader.py`
- `parser.py`
- `sprint/generator.py`

For “why did it start at this story?” cite:

- `cli.py`
- `cli_start_point.py`
- `state.yaml`
- `sprint-status.yaml`

For “what happened in this run?” cite:

- `.bmad-assist/runs/*.yaml`
- `.bmad-assist/logs/*.log`
- `.bmad-assist/prompts/run-*/`
