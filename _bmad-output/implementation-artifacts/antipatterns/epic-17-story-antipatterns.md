# Epic 17 - Story Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during validation of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent story-writing mistakes (unclear AC, missing Notes, unrealistic scope).

## Story 17-1 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | API path contract conflict — tasks 1.2-1.4 specified `/api/data-sources` and `/api/merge-methods` as full URLs, but the router is mounted at prefix `/api/data-fusion`, making the actual full paths `/api/data-fusion/api/data-sources` (broken) | Tasks 1.2-1.4 paths changed to router-relative (`/sources`, `/sources/{provider}/{dataset_id}`, `/merge-methods`, `/generate`); canonical endpoint table added to Dev Notes |
| critical | Progress model contradiction — AC-4 required "current step, percentage, ETA" and Task 5.1 required "cancel-ability", both incompatible with the scope boundary explicitly calling out synchronous single-request execution | AC-4 rewritten to match synchronous model (loading indicator → step log on completion → error on failure); Task 5.1 updated accordingly; error-path behavior incorporated |
| high | AC-4 missing error-path behavior — only success path described; no AC for what the GUI shows when pipeline generation fails | Incorporated into the AC-4 rewrite — structured `what/why/fix` error display added |
| medium | "variables" vs "variable count" inconsistency between AC-1 and Task 3.1 | AC-1 changed from "variables" to "variable count" |
| medium | AC-2 missing edge case behavior — undefined for single-source selection and zero-overlap scenario | AC-2 extended to specify: overlap = columns present in all selected sources; single-source → no prompt; zero-overlap → informational message + continue allowed |
| medium | AC-5 "key demographics" undefined and marginals source unspecified | AC-5 now specifies income deciles, heating type distribution, vehicle type distribution as key demographics; notes marginals are provided by Epic 11 pipeline catalog metadata, not user-configurable in 17.1 |
| medium | AC-6 missing determinism requirement despite project context rule that all runs must be reproducible | AC-6 extended with explicit same-seed → identical-result requirement |
| medium | No non-regression check for existing workspace navigation after App.tsx/AppContext.tsx integration | New subtask 6.6 added to verify existing view modes and shortcuts remain functional |
