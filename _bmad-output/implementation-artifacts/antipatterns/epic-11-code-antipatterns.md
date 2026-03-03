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

## Story 11-3 (2026-03-03)

| Severity | Issue | Fix |
|----------|-------|-----|
| high | `test_bad_gzip_does_not_trigger_stale_fallback` calls `_fetch()` directly, never exercising the stale-cache fallback path in `download()`. Test name claims to verify stale-fallback prevention but is a duplicate of the preceding test. | Rewrote test to pre-seed a stale cache entry via `download()`, rename files to simulate staleness, then call `download()` with corrupt gzip data — now actually verifies `DataSourceValidationError` propagates through `download()` without triggering stale fallback. |
| medium | ADEME UTF-8 fallback failure propagates raw `pa.ArrowInvalid` — if both Windows-1252 and UTF-8 parsing fail, the second `pcsv.read_csv()` raises unhandled, bypassing error hierarchy and stale-cache fallback. | Wrapped fallback `read_csv()` in `try/except (pa.ArrowInvalid, pa.lib.ArrowKeyError)` that raises `DataSourceValidationError` with descriptive message. |
| medium | `make_*_config(**params)` docstrings claim params are "query parameters for the download request" but params are never applied to the URL — they only differentiate cache slots. | Updated all three docstrings to accurately state params differentiate cache slots only and are not appended to the download URL. |
| medium | SDES test assertions use pure-ASCII substrings (`"Auvergne"`, `"le-de-France"`) that match even if non-ASCII characters (`ô`, `Î`) are decoded incorrectly. | Changed to exact equality assertions: `region_names[0] == "Auvergne-Rhône-Alpes"` and `region_names[3] == "Île-de-France"`. |
| low | ADEME UTF-8 fallback test only asserts pure-ASCII value `"Gaz naturel"`, never verifying non-ASCII content decoded correctly via fallback path. | Added assertion checking `"métropolitaine"` in the geography column after UTF-8 fallback. |
