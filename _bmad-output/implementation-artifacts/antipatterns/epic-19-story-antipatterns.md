# Epic 19 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 19-1 (2026-03-23)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | AC7 conflates PR-verifiable build with post-merge deployment requiring external admin setup, making pass/fail ambiguous | Rewrote AC7 to clearly scope PR acceptance to build/upload success; explicit note that full deploy is a post-merge out-of-band step, not a story blocker. |
| high | AC10 is a compound criterion (4 independent assertions) allowing ambiguous partial-done | Replaced AC10 with 4 labeled atomic sub-criteria (10a–10d) — each independently verifiable; exact task labels now embedded in AC10c eliminating Dev Notes duplication. |

## Story 19-3 (2026-03-23)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | OpenFisca as hard requirement | Rewrote intro sentence from "with Python 3.13+ and OpenFisca France" to "with Python 3.13+; OpenFisca France is the default computation backend and ships with the standard install" — preserves usability guidance while accurately reflecting the optional-by-adapter architecture |
| high | `custom.css` contradiction | Updated "Files NOT to Modify" entry for custom.css to note that fallback CSS edits are permitted if `<details>` renders unstyled — eliminates direct contradiction with the Risks table |
| medium | "Orchestrator is core engine" naming collision | Changed "The orchestrator is ReformLab's core engine" to "The orchestrator is ReformLab's coordination layer" — avoids using "engine" for two separate domain concepts on the same page |
| medium | Domain object set change undocumented | Added "Domain Object Set Rationale" section explaining the intentional change from epics.md definition (Simulation replaced by Orchestrator + Indicators added), with traceability note |
| medium | Markdown table in `<details>` not in testing checklist | Added explicit verification item to Testing Strategy for the Indicators `<details>` table rendering as HTML table |
| medium | `<Steps>` fallback contradicts AC 1 | Updated Risks table entry to say "raise a blocker — do not substitute `<ol>` without explicitly revising AC 1" instead of permitting a silent fallback |
