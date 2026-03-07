# Epic 17 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 17-1 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | AC-5 validation — backend hardcodes `validation_result=None`, so no marginal check data is ever returned | Deferred — wiring `PopulationValidator` requires understanding catalog marginal API; added as AI-Review follow-up |
| critical | AC-5 distributions — `PopulationPreview` uses placeholder `100 - i * 8` values, not real population statistics | Deferred — explicitly commented "not in scope for 17.1"; added as AI-Review follow-up |
| high | `<a>` nested inside `<button>` — HTML spec violation; browsers handle nested interactive elements inconsistently | Restructured card to `<div>` wrapper with `<button>` for selection and sibling `<a>` for the link |
| high | AC-2 VariableOverlapView — overlap table not implemented, shows static text; `hasKnownOverlap = false` hardcoded | Deferred — explicitly documented design decision in Dev Agent Record; added as AI-Review follow-up |
| medium | `list_sources` broad `except Exception` silently drops datasets without loud failure | Changed to `except (AttributeError, KeyError)` with ERROR-level logging — prevents masking programming errors while being resilient to individually malformed catalog entries |
| medium | Task 1.3 column schema contract — `ColumnInfo` missing `type` field; task specifies `(name, type, description)` | Added `type: str = ""` to backend `ColumnInfo`; added `type: string` to frontend `ColumnInfo` interface |
| medium | Determinism test only asserts `record_count` equality on a fully mocked pipeline; proves nothing about reproducibility | Deferred — mock design is intentional; fixing properly requires a content-hash assertion; added as AI-Review follow-up |
| low | AC-1 — `record_count` always `None` in source listing; card conditionally hides the badge | Deferred — catalog metadata doesn't expose record counts without loading data; added as AI-Review follow-up |

## Story 17-2 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Delete endpoint fails-open — if `get_entry_type` raises an exception, `entry_type` defaults to `"portfolio"` and `shutil.rmtree` proceeds, potentially deleting non-portfolio entries | Changed fallback to `entry_type = "unknown"` so the `entry_type != "portfolio"` guard fails closed |
| high | AC-4 gap — `rate_schedule` always sent as `{}` in both `validatePortfolio` and `createPortfolio` API calls; user-edited schedule values discarded | Added `rateSchedule: Record<string, number>` to `CompositionEntry`, wired `YearScheduleEditor` into the composition panel, propagated values to API payloads |
| medium | `validate_compatibility` exception swallowed — broad `except Exception` returns empty conflicts (`is_compatible=True`), masking errors | Re-raised as `HTTPException(500)` with structured error detail |
| medium | Falsy value serialization — `if val:` drops zero-valued parameters (e.g., a `rate = 0` or empty thresholds) from detail response | Changed to `if val is not None and val != () and val != {}:` |
| medium | Bad rate_schedule year key raises unhandled 500 — `int("bad")` raises `ValueError` with no exception handler | Wrapped in `try/except ValueError` → `HTTPException(422)` |
| medium | AC-5 gap — saved portfolios list is read-only; no delete/load/clone buttons in GUI | Added delete button per portfolio row; wired `deletePortfolio` API call with toast feedback; load/clone deferred (see action items) |
| low | AC-2 gap — `parameterSchemas` prop exists in `PortfolioCompositionPanel` but is never populated by `PortfolioDesignerScreen`; ParameterRow editing non-functional | Deferred (requires fetching `GET /api/templates/{id}` per template; added as action item). `YearScheduleEditor` now always shown in expanded panel, covering the main AC-4 use case. |
