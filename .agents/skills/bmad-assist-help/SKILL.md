---
name: bmad-assist-help
description: Explain how bmad-assist works in this project by inspecting the local bmad-assist config, sprint status, epics, state, runs, prompts, logs, and relevant source code. Use when the user asks how bmad-assist behaves, how it reads epics and stories, why a run resumed or failed, what files are authoritative, or to investigate bmad-assist execution in the current repo.
---

# bmad-assist Help

Use this skill for project-grounded questions about `bmad-assist`, not generic BMAD routing.

## What This Skill Must Do

Answer from the local repo first. Do not give abstract explanations if the answer depends on current project files.

Always inspect these files before answering any non-trivial question:

- `bmad-assist.yaml`
- `.bmad-assist/state.yaml`
- latest `.bmad-assist/runs/*.yaml`
- latest `.bmad-assist/logs/*.log`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/planning-artifacts/epics.md`

Then use the references:

- `references/reformlab-runtime-map.md`
- `references/bmad-assist-code-paths.md`

If the user asks about a specific failure, resume issue, or skipped story, also inspect the matching prompt snapshot under `.bmad-assist/prompts/run-*/`.

## Answering Model

Explain `bmad-assist` using this source-of-truth split:

1. Story structure comes from epic docs:
   - consolidated `epics.md`
   - or sharded `epics/` files
2. Story status comes from `sprint-status.yaml` when present.
3. Active loop position comes from `.bmad-assist/state.yaml`.
4. What happened during a run comes from:
   - `.bmad-assist/runs/*.yaml`
   - `.bmad-assist/logs/*.log`
   - `.bmad-assist/prompts/run-*/`
5. Generated outputs live under `_bmad-output/implementation-artifacts/`.

Be explicit about which file answers which part of the question.

## Required Checks

### When user asks "how does it read epics/stories?"

Inspect:

- `_bmad-output/planning-artifacts/epics.md`
- `src/bmad_assist/bmad/parser.py`
- `src/bmad_assist/bmad/state_reader.py`
- `src/bmad_assist/sprint/generator.py`
- `src/bmad_assist/compiler/workflows/create_story.py`

Explain:

- how epic files are discovered
- standard story header parsing vs fallback parsing
- how story numbers are assigned
- how sprint-status keys map back to `epic.story`
- what happens if epic formatting is non-standard

### When user asks "what is the next story / why did it resume there?"

Inspect:

- `.bmad-assist/state.yaml`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- latest `.bmad-assist/runs/*.yaml`
- `src/bmad_assist/cli.py`
- `src/bmad_assist/cli_start_point.py`
- `src/bmad_assist/core/loop/story_transitions.py`
- `src/bmad_assist/core/loop/sprint_sync.py`

Explain:

- current epic/story/phase from state
- why completed stories are skipped
- how `--epic` / `--story` override works
- how sprint-status can advance resume state

### When user asks "what do the logs/prompts/runs mean?"

Inspect:

- `.bmad-assist/logs/*.log`
- `.bmad-assist/runs/*.yaml`
- `.bmad-assist/prompts/run-*/`
- `src/bmad_assist/core/loop/run_tracking.py`
- `src/bmad_assist/core/io.py`

Explain:

- per-run YAML timeline
- per-phase prompt snapshots
- human-readable epic log files
- benchmark/evaluation artifacts

## ReformLab-Specific Grounding

This project uses:

- `paths.project_knowledge: _bmad-output/planning-artifacts` in `bmad-assist.yaml`
- consolidated `_bmad-output/planning-artifacts/epics.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- project-local `.bmad-assist/` for state, prompts, run logs, cache, and epic log files

Do not assume vanilla `docs/epics.md` unless the local files actually point there.

## Response Rules

- Prefer concrete paths, file names, and function names.
- If behavior is project-specific, say so.
- If behavior is inferred from code rather than directly logged, label it as an inference.
- If current files and code disagree, say which side is authoritative at runtime.
- Keep answers practical: “where to look”, “what drives it”, “why it happened”.
