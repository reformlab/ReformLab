# Epic 11 - Code Antipatterns

> **WARNING: ANTI-PATTERNS**
> The issues below were MISTAKES found during code review of previous stories.
> DO NOT repeat these patterns. Learn from them and avoid similar errors.
> These represent implementation mistakes (race conditions, missing tests, weak assertions, etc.)

## Story 11-2 (2026-03-03)

| Severity | Issue | Fix |
|----------|-------|-----|
| critical | `filosofi_2021_iris_declared` mapped `DISP_*` columns (disposable income) to `median_declared_income` — served factually wrong data. Both datasets also shared the same URL, making them produce identical outputs. | Changed column mapping to use `DEC_*` prefix (DEC_MED21, DEC_D121...DEC_D921), updated declared URL to `BASE_TD_FILO_IRIS_2021_DEC_CSV.zip`, updated disposable URL to `BASE_TD_FILO_IRIS_2021_DISP_CSV.zip` (correct filenames per INSEE page). |
| critical | Test fixture `filosofi_2021_iris_declared.csv` used `DISP_*` column headers, validating the wrong data identity. | Updated fixture headers to use `DEC_*` prefix. |
| high | Unreachable `else` branch in `_parse_csv` for/else loop — dead code that suggests misunderstanding of Python's for/else semantics. | Replaced for/else pattern with explicit try/except: try UTF-8, on `ArrowInvalid` fallback to Latin-1. |
| medium | `_NETWORK_ERRORS` built via `try/except ImportError` for stdlib modules that cannot fail to import (`urllib.error`, `http.client`). Misleading defensive code. | Removed try/except, defined `_NETWORK_ERRORS` tuple directly at module level. |
| medium | `urllib.request` imported inside `_fetch()` method body while `urllib.error` and `http.client` imported at module level — inconsistent. | Moved all three stdlib imports to module level. |
| medium | `timeout=300` magic number with no documentation or named constant. | Extracted to `_HTTP_TIMEOUT_SECONDS = 300` with docstring. |
| medium | `INSEEDataset.file_format: str` accepts any string value; only `"csv"` and `"zip"` are valid. | Changed to `Literal["csv", "zip"]`. |
| medium | No `_fetch()` test for `filosofi_2021_iris_disposable` dataset. | Added `test_iris_disposable_csv_parsing` test with value assertion (19200.0) to differentiate from declared fixture. |
