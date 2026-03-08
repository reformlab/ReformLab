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

## Story 17-3 (2026-03-07)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | Path traversal via `run_id` — `self._base_dir / run_id` in `ResultStore` accepts user-supplied run IDs from URL paths, allowing `../../etc` to escape the base directory via URL-encoded separators | Added `_resolve_safe()` using `Path.resolve()` + `relative_to()` check; added `ResultStoreError` handling (400) in all route handlers |
| critical | `DELETE /api/results/{run_id}` accepted `cache` parameter but never evicted from it (comment acknowledged the gap) | Added `ResultCache.delete()` method; called in delete route handler |
| critical | No test for simulation failure metadata path — `TestRunMetadataAutoSaveFailurePath` was missing entirely | Added `test_metadata_saved_on_simulation_exception` using `raise_server_exceptions=False` |
| high | Export callbacks in `ResultDetailView` not wired — buttons rendered but `onExportCsv`/`onExportParquet` were `undefined` in `SimulationRunnerScreen` | Imported `exportResultCsv`/`exportResultParquet`; passed as callbacks to both `ResultDetailView` instances |
| medium | Timestamp sort bug — `_parse_timestamp` returned timezone-naive `datetime.min` as fallback while all valid timestamps are timezone-aware, causing `TypeError` in `list.sort()` when any corrupt entry exists | Changed fallback to `datetime.min.replace(tzinfo=timezone.utc)`; added `timezone` import |

## Story 17-4 (2026-03-08)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | CSV export vulnerable to formula injection and malformed output — no escaping for commas/quotes, no `=+-@` prefix protection | Added `escapeCsvField()` helper — prefixes formula characters with `'`, double-quotes fields containing commas/quotes/newlines |
| high | `baseline_run_id` silently ignored when not in `run_ids` instead of returning 422 | Added explicit 422 validation before duplicate check |
| high | Error contract mismatch — FastAPI serializes `HTTPException(detail={...})` as `{"detail":{...}}` but `apiFetch` checks top-level `errorBody.what`, so structured errors never reach the screen | `apiFetch` and `apiFetchBlob` now also check `rawBody.detail.what` and construct `ApiError` from nested detail |
| medium | AC-3 partial — distributional detail panel always opens with `distRows[0]`, not the clicked bar/row | Added `onBarClick` prop to `MultiRunChart`; removed wrapper div; detail panel now receives actual clicked row |
| medium | AC-4 partial — relative mode bars use series palette colors instead of sign-based emerald/red | Added `<Cell>` per bar in relative mode with emerald-500/red-500/slate-400 based on value sign |
| medium | `CrossMetricPanel` mini-ranking always sorts descending, so `min_*` criteria display worst-to-best | Added `isMin` flag; sorts ascending for `min_*`, descending for `max_*` |
| medium | Welfare tab uses generic table instead of AC-2 winner/loser/net-change summary cards | **Deferred** — domain welfare data structure must be understood before designing cards; added as AI-Review follow-up |
| low | Test coverage gap — no test for `baseline_run_id` not in `run_ids` returning 422 | Added `test_baseline_run_id_not_in_run_ids_returns_422` |
| low | "View as table" toggle missing — companion table is hardcoded visible | **Deferred** — table is functional and accessible; toggle is UX polish; added as AI-Review follow-up |
| low | `ComparisonDashboardScreen` is 764 lines (SRP concern) | **Deferred** — noted as architectural improvement; added as AI-Review follow-up |

## Story 17-5 (2026-03-08)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `extractErrorDetail()` reads `err.body.detail.what` but `ApiError` stores `what/why/fix` directly — NoDecisionData/NoIncomeData UX paths never trigger in production | Rewrote to check `e["what"]` directly on the thrown object |
| high | Frontend tests mock `{ body: { detail: {...} } }` (fake shape) instead of real `ApiError` instances — tests green but prove nothing about production | Changed to `new ApiError({...})` instances |
| high | Invalid `group_value` (e.g., `"abc"`) causes unhandled `ValueError` → 500 | Added try/except + range validation before `int()` cast, returns 422 |
| high | Unsupported `group_by` value (e.g., `"region"`) silently ignored — returns unfiltered data | Added 422 validation before income column check |
| high | Missing `{domain}_chosen` column when households present returns zeroed counts instead of error — violates "data contracts fail loudly" rule | Raises HTTPException(500) when column absent but total_households > 0 |
| high | AC-4 partial — `AreaChart` had no `onClick`; year detail only openable from table rows, not chart | Added `onClick` handler to `AreaChart` using `chartState.activeLabel` |
| medium | Backend decile tests use `< 100` and `> 0` assertions — too weak to catch ranking errors | Added 3 new tests for invalid group_by, non-integer group_value, and out-of-range group_value (these catch the bugs fixed above) |

## Story 17-6 (2026-03-08)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `POST /api/indicators/welfare` is runtime-broken — `welfare` in `VALID_INDICATOR_TYPES` allows the single-run endpoint to reach `result.indicators("welfare")` without `reform_result`, crashing at the computation layer | Added explicit 422 before store/cache checks, directing users to `POST /api/comparison` |
| high | `except ResultStoreError:` in `compare_portfolio_runs()` catches all store I/O errors, converting disk failures into false 404 "not found" responses | Changed to `except ResultNotFound:` — other `ResultStoreError` subclasses now bubble up correctly as 500 |
| medium | `TestIndicatorWelfare` tests expected 404/409 from welfare endpoint, but Fix 1 causes 422 to fire before any store/cache lookup, breaking 2 tests | Replaced both tests with a single `test_welfare_single_run_returns_422_with_structured_error` that verifies the correct 422 response and message content |

## Story 17-7 (2026-03-08)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `run_simulation()` in `runs.py` bypassed DI for `ResultStore` — called `get_result_store()` directly inside `finally`, preventing `app.dependency_overrides` from working in tests | Added `store: ResultStore = Depends(get_result_store)` to function signature; removed `store = get_result_store()` from `finally` block |
| high | `_lookup_run()` in `exports.py` only caught `ResultNotFound` — path traversal or malformed `run_id` would raise uncaught `ResultStoreError` → 500 instead of structured 400 | Added `except ResultStoreError:` → 400 handler matching the pattern used in all other routes |
| medium | `load_from_disk()` hardcoded `success=True` — misrepresents runs if a failed run somehow has `panel.parquet` (defensive correctness) | Changed to `success=metadata.status == "completed"` |
| medium | `save_panel()` and `save_manifest()` left `.tmp` files on failure — `to_parquet()` or `write_text()` exceptions orphaned temp artifacts | Wrapped write+replace in `try/except` with `tmp.unlink(missing_ok=True)` in exception handler before re-raising |
| medium | `ResultCache.store()` evicted an unrelated LRU entry when `run_id` already existed in cache and cache was at capacity | Guard changed to `if run_id not in self._cache and len(self._cache) >= self._max_size` |
| medium | Corrupt Parquet schema metadata was silently coerced to `{}` with no logging — `except (json.JSONDecodeError, ValueError): panel_metadata = {}` | Added `logger.warning("event=panel_metadata_corrupt run_id=%s", run_id)` before fallback |

## Story 17-8 (2026-03-08)

| Severity | Issue | Fix |
|----------|-------|-----|
| medium | Data fusion error test (Task 2.3) only asserted `generatePopulation` was called; never verified the error UI (`what/why/fix` sections) was rendered — failing AC-3 regression detection. | Added `waitFor` assertion on `aria-label="Generation failed"` section, plus text assertions for `what` and `why` content. |
| medium | Comparison export test (Task 5.5) clicked the Export CSV button without asserting the download was triggered (`anchor.click()` never verified) — failing AC-3 regression detection. | Added local `anchorClickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click")` and asserted `toHaveBeenCalledOnce()` after button click. |
| low | `helpers.ts` missing `mockDecisionSummary` factory specified in Task 1.2 (spec-implementation gap). | Added `mockDecisionSummary(overrides?)` factory with a `DomainSummary` stub and proper `DecisionSummaryResponse` type import. |
| low | All task checkboxes unchecked and Dev Agent Record empty despite story marked `done`. | Marked all tasks `[x]`, filled Dev Agent Record (model, completion notes, file list), added Senior Developer Review section. |
