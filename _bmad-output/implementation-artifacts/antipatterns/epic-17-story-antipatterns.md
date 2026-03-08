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

## Story 17-3 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Failed-run persistence missing — AC-3 shows `status: completed/failed` badge but AC-2 and Task 2.7 only saved on success, creating dead-letter metadata schema | AC-2 updated to cover both outcomes; Task 1.2 documents `row_count=0` for failures; Task 2.7 rewritten with `try/finally` pattern; auto-save code snippet updated; failed mock entry added |
| critical | Portfolio-run metadata schema incompatible — `template_name: str` and `policy_type: str` were required non-optional fields, but portfolio runs have no single template | Added `run_kind: str` field; made `template_name`, `policy_type` optional (`str \| None`); `portfolio_name` already optional; updated all schemas (ResultMetadata, Pydantic models, TypeScript interfaces, mock data) |
| critical | Missing manifest fields in ResultMetadata — AC-4 requires Manifest tab to show `adapter_version` and `timestamps` but these were absent from the schema, making the metadata-only view (post-cache-eviction) unable to render required content | Added `adapter_version: str`, `started_at: str`, `finished_at: str` to `ResultMetadata`, `ResultDetailResponse`, and `ResultDetailResponse` TypeScript interface |
| critical | Missing export API specification — AC-4 commits to CSV/Parquet export buttons but no backend endpoints were defined; existing `exports.ts` is for indicator data, not run-specific panel data | Added Tasks 2.9 and 2.10 for `GET /api/results/{run_id}/export/csv` and `/parquet`; updated endpoint table and HTTP status matrix (200 streaming, 404 not found, 409 data evicted) |
| critical | Population/portfolio state passing unclarified — `SimulationRunnerScreen` pre-run summary reads selected population/portfolio but Task 7.4 only added `results`-related AppContext state, leaving the run initiation inputs undefined | Task 7.4 updated to verify/add `selectedPopulationId` and `selectedPortfolioName` from prior stories; pre-run sub-view local state for `startYear`, `endYear`, `seed` documented |
| high | Atomic write and corrupt-entry handling not specified for ResultStore — partial writes on crash could produce malformed JSON that breaks the entire results listing | Task 1.3 updated with atomic rename pattern; Task 1.4 updated with skip-and-log for corrupt entries; "ResultStore write safety" note added to Dev Notes |
| high | ResultStore custom exceptions not defined — inconsistent error propagation to `what/why/fix` format | `ResultStoreError` and `ResultNotFound` exception classes added to schema section; Task 1.2 updated to require their definition; route handler contract documented |
| medium | Testing standards missing failed-run and export test cases | Testing Standards section expanded with failed-run metadata tests, corrupt entry skip test, export endpoint tests (200/409/404), and `runs.py` regression tests |

## Story 17-4 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Welfare always excluded from API call | Changed Task 5.3 to pass `include_welfare: true` in the `comparePortfolios()` call. Also changed `PortfolioComparisonRequest.include_welfare` default from `False` to `True` in both Task 1.1 and the Pydantic model snippet — welfare is the expected default for this story's UI which always shows the Welfare tab. |
| critical | 404 vs 409 eviction semantics ambiguous — backend flow says "look up in cache, if missing → 404" but an evicted run IS in the metadata store | Rewrote Task 1.2 to check `ResultStore` metadata first (404 if unknown), then `ResultCache` (409 if in metadata but not in cache or panel_output is None). Updated HTTP status code matrix. Updated backend flow code comment to reflect two-store lookup sequence. |
| critical | Label safety not enforced in tasks — `compare_portfolios()` rejects reserved names and `delta_` prefix but Task 1.2 had no validation step | Rewrote Task 1.2 to include explicit label deduplication and reserved-name/prefix validation with 422 error. |
| high | No duplicate `run_ids` validation — only size bounds (2–5) specified | Added duplicate run_ids check (422) to Task 1.2 and Task 1.3 tests. |
| high | AC-3 methodology field not in API response contract — leaves dev to guess implementation | Added clarifying note to Task 5.7 that methodology descriptions are static frontend string constants keyed by indicator type, not returned by the API. |
| medium | Pydantic mutable default `list[str] = ["distributional", "fiscal"]` — mypy strict would flag this | Changed to `Field(default_factory=lambda: [...])` in both Task 1.1 and the Pydantic model snippet. |
| medium | `models.py` listed in "New files" section but it already exists | Removed from "New files", kept in "Modified files". |
| low | Testing rules from project-context.md (class-based grouping, AC references) not mentioned in test spec | Added class-based grouping examples to Task 1.3. |
