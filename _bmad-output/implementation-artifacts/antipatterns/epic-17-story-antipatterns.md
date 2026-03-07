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

## Story 17-2 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Missing AC for conflict validation | Added AC-6 covering conflict display, save-block under `resolution_strategy="error"`, and warning-but-permit for other strategies. |
| critical | Undefined PUT versioning semantics | Added "Backend — Versioning semantics for PUT" section explaining `registry.save()` idempotency and SHA-256 content hash behavior. |
| critical | No `delete()` method in `ScenarioRegistry` | Added "Backend — DELETE implementation" section with `shutil.rmtree()` pattern and safety checks. |
| critical | Route collision `/validate` vs `/{name}` | Added explicit note to route pattern section: "declare `/validate` before `/{name}` so the static route is matched first." |
| critical | Unspecified Pydantic request model for POST | Added full "Pydantic Request/Response Models" section with `CreatePortfolioRequest`, `UpdatePortfolioRequest`, `ClonePortfolioRequest`, `ValidatePortfolioRequest`, `ValidatePortfolioResponse`, `PortfolioListItem`, `PortfolioDetailResponse`, `PortfolioPolicyItem`. |
| high | Template source for AC-1 unspecified | Added "Template Source for AC-1" section: templates come from existing `GET /api/templates`, no new endpoint required. |
| high | `selectedPortfolioId` vs name-keyed backend | Renamed to `selectedPortfolioName` in Task 6.3. |
| high | Year schedule year range ambiguous | AC-4 now explicitly states "fixed at 2025–2035; dynamic scenario-driven range is out of scope." |
| high | Frontend parameter schema for composition | Added "Frontend Parameter Schema for Composition Panel" section explaining template metadata drives `ParameterRow` rendering and `rate_schedule` → `YearScheduleEditor`. |
| high | Clone endpoint missing `registry.save()` call | Added "Backend — Clone implementation" section noting `clone()` returns in-memory copy only; must call `registry.save()` after. |
| medium | API status code matrix missing | Added "Backend — HTTP status code matrix" table covering all 7 endpoints. |
| medium | Portfolio name validation rules absent | Added "Backend — Portfolio name validation" with slug regex, reserved names, client-side enforcement note. |
| medium | AC-2 save-block UI behavior implicit | AC-2 now specifies disabled save button with exact hint text. |
| medium | AC-3 boundary behavior unspecified | AC-3 now specifies first/last item disabled states and order persistence on save/load. |
| medium | AC-5 clone 409 and load fidelity | AC-5 now specifies 409 conflict with suggested rename, and explicit order-restored-on-load guarantee. |
