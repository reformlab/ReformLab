
# Story 11.2: Implement INSEE data source loader

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want an INSEE data source loader that downloads, caches, and schema-validates key INSEE Filosofi income distribution datasets (commune-level and IRIS-level),
so that downstream merge methods (Stories 11.4–11.6) can consume real French public data as `pa.Table` objects through the `DataSourceLoader` protocol.

## Acceptance Criteria

1. Given a valid INSEE dataset identifier, when the loader downloads it, then a schema-validated `pa.Table` is returned with documented columns.
2. Given the INSEE loader, when queried for available datasets, then at least 3 income distribution datasets at commune and IRIS granularity are available.
3. Given an invalid or unavailable INSEE dataset ID, when requested, then a clear error identifies the specific dataset and suggests alternatives.
4. Given the INSEE loader, when run in CI, then tests use fixture files (no real network calls) marked with `pytest -m network` for opt-in integration tests.

## Tasks / Subtasks

- [x] Task 1: Define INSEE dataset catalog and schema constants (AC: #1, #2, #3)
  - [x] 1.1 Create `src/reformlab/population/loaders/insee.py` with module docstring referencing Story 11.2, FR36, FR37
  - [x] 1.2 Define `INSEEDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `file_format: str` (csv or zip), `encoding: str` (default "utf-8"), `separator: str` (default ";"), `null_markers: tuple[str, ...] = ("s", "nd", "")` (INSEE suppression markers), `columns: tuple[tuple[str, str], ...] = ()` where each inner tuple is `(raw_insee_column_name, project_column_name)` — serves as both documentation and rename mapping
  - [x] 1.3 Define the INSEE dataset catalog as a module-level `dict[str, INSEEDataset]` mapping dataset IDs to their metadata. Include at minimum:
    - `"filosofi_2021_commune"` — Filosofi 2021 commune-level income data (deciles D1–D9, median, poverty rate)
    - `"filosofi_2021_iris_declared"` — Filosofi 2021 IRIS-level declared income
    - `"filosofi_2021_iris_disposable"` — Filosofi 2021 IRIS-level disposable income
  - [x] 1.4 Define a `pa.Schema` per dataset for the output columns the loader produces (subset of raw columns, renamed/typed to project conventions)
  - [x] 1.5 Add a `AVAILABLE_DATASETS` module-level constant exposing the catalog keys for discovery

- [x] Task 2: Implement `INSEELoader` class extending `CachedLoader` (AC: #1, #2)
  - [x] 2.1 `INSEELoader.__init__(self, *, cache: SourceCache, logger: logging.Logger, dataset: INSEEDataset)` — store the dataset reference, call `super().__init__()`
  - [x] 2.2 Implement `schema(self) -> pa.Schema` — return the schema for the loader's dataset
  - [x] 2.3 Implement `_fetch(self, config: SourceConfig) -> pa.Table` — download from `config.url` using `urllib.request`, parse using `self._dataset.encoding` and `self._dataset.separator` for format metadata (SourceConfig carries URL + cache key; INSEEDataset carries format/encoding metadata), select and rename columns per `self._dataset.columns` mapping, cast types to match `self.schema()`, return `pa.Table`
  - [x] 2.4 Handle ZIP-wrapped CSV files (INSEE often wraps CSVs in ZIP archives): detect `.zip` suffix in URL, extract using `zipfile.ZipFile(io.BytesIO(raw_bytes))`, find the first entry whose name ends with `.csv` (case-insensitive) via `namelist()`. If zero or multiple `.csv` files are found, raise `DataSourceValidationError` with a clear message listing the archive contents
  - [x] 2.5 On any network error (`urllib.error.URLError`, `OSError`, `http.client.HTTPException`), re-raise as `OSError` so `CachedLoader.download()` can handle stale-cache fallback correctly
  - [x] 2.6 Add structured logging: `event=fetch_start`, `event=fetch_complete` with `provider=insee dataset_id=... url=... rows=... columns=...`

- [x] Task 3: Implement `get_insee_loader` factory function (AC: #2, #3)
  - [x] 3.1 Create `get_insee_loader(dataset_id: str, *, cache: SourceCache, logger: logging.Logger | None = None) -> INSEELoader` factory that looks up dataset from catalog and constructs the loader
  - [x] 3.2 When `dataset_id` is not in the catalog, raise `DataSourceValidationError` with summary "Unknown INSEE dataset", reason listing the requested ID, and fix listing available dataset IDs
  - [x] 3.3 When `logger` is `None`, default to `logging.getLogger("reformlab.population.loaders.insee")`

- [x] Task 4: Implement `make_insee_config` helper (AC: #1, #2)
  - [x] 4.1 Create `make_insee_config(dataset_id: str, **params: str) -> SourceConfig` convenience function that constructs a `SourceConfig` from the catalog entry, using `provider="insee"`, the catalog's URL, and any additional params
  - [x] 4.2 When `dataset_id` is not in the catalog, raise `DataSourceValidationError` with guidance

- [x] Task 5: Update `__init__.py` exports (AC: all)
  - [x] 5.1 Add `INSEELoader`, `INSEEDataset`, `AVAILABLE_DATASETS`, `get_insee_loader`, `make_insee_config` to `src/reformlab/population/loaders/__init__.py`
  - [x] 5.2 Add the same exports to `src/reformlab/population/__init__.py`

- [x] Task 6: Create test fixtures (AC: #4)
  - [x] 6.1 Create `tests/fixtures/insee/` directory
  - [x] 6.2 Create small CSV fixture files mimicking Filosofi commune-level format (5-10 rows, semicolon-separated, UTF-8, with real column names from INSEE)
  - [x] 6.3 Create a small Parquet fixture file mimicking the relevant schema
  - [x] 6.4 Add conftest fixtures in `tests/population/loaders/conftest.py`: `insee_fixture_dir`, `filosofi_commune_csv_path`, `filosofi_commune_table`

- [x] Task 7: Write comprehensive tests (AC: all)
  - [x] 7.1 `tests/population/loaders/test_insee.py` — `TestINSEELoaderProtocol`: `INSEELoader` instance satisfies `DataSourceLoader` protocol via `isinstance()` check
  - [x] 7.2 `TestINSEELoaderSchema`: `schema()` returns a valid `pa.Schema` with expected field names and types for each dataset
  - [x] 7.3 `TestINSEELoaderFetch`: monkeypatch `urllib.request.urlopen` to return fixture CSV content; verify `_fetch()` returns correctly-parsed `pa.Table` with expected columns and types
  - [x] 7.4 `TestINSEELoaderFetchZip`: monkeypatch `urllib.request.urlopen` to return a ZIP-wrapped CSV fixture; verify extraction and parsing
  - [x] 7.5 `TestINSEELoaderFetchEncodingFallback`: verify Latin-1 fallback when UTF-8 decode fails
  - [x] 7.5b `TestINSEELoaderFetchSuppressedValues`: verify that fixture rows containing `"s"` and `"nd"` in numeric income columns produce `null` values (not parse errors) in the output table
  - [x] 7.5c `TestINSEELoaderFetchHTTPError`: monkeypatch `urllib.request.urlopen` to raise `urllib.error.HTTPError(url, 404, 'Not Found', {}, None)` — verify it is caught and re-raised as `OSError` so `CachedLoader.download()` handles it correctly
  - [x] 7.6 `TestINSEELoaderDownloadIntegration`: full `download()` cycle via `CachedLoader` — cache miss → fetch → cache → cache hit (uses monkeypatched `_fetch`, no real network)
  - [x] 7.7 `TestINSEELoaderCatalog`: verify `AVAILABLE_DATASETS` contains at least the required datasets, `get_insee_loader` returns correct loader, invalid ID raises error with suggestions
  - [x] 7.8 `TestMakeInseeConfig`: verify `make_insee_config` produces correct `SourceConfig` for each catalog entry
  - [x] 7.9 `tests/population/loaders/test_insee_network.py` — `@pytest.mark.network` integration tests: real HTTP download of a small Filosofi commune-level file, verify schema and row count are reasonable. These tests are excluded from CI by default.

- [x] Task 8: Run full test suite and lint (AC: all)
  - [x] 8.1 `uv run pytest tests/population/` — all tests pass
  - [x] 8.2 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [x] 8.3 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: First Concrete Loader

This is the **first concrete `DataSourceLoader` implementation** in the codebase. Story 11.1 delivered the protocol, caching infrastructure, and `CachedLoader` base class. This story proves the pattern works end-to-end with a real institutional data source.

Story 11.3 (Eurostat, ADEME, SDES loaders) depends on this story establishing the concrete loader pattern. The pattern established here becomes the template for all subsequent loaders.

### INSEE Data Sources — What to Download

INSEE provides data as **direct file downloads** from `https://www.insee.fr/fr/statistiques/fichier/...`. No authentication is required. No API key needed. Files are publicly accessible via anonymous HTTPS GET.

**Key datasets for carbon tax microsimulation:**

| Dataset ID | Source | Format | Size | What it provides |
|---|---|---|---|---|
| `filosofi_2021_commune` | Filosofi 2021 | CSV | ~3 KB | Income deciles (D1–D9), median, poverty rates by commune |
| `filosofi_2021_iris_declared` | Filosofi 2021 IRIS | CSV | ~835 KB | Declared income quartiles/deciles at IRIS level |
| `filosofi_2021_iris_disposable` | Filosofi 2021 IRIS | CSV | ~892 KB | Disposable income quartiles/deciles at IRIS level |

**Important context:**
- Filosofi 2021 is the **last available vintage** — the 2022 vintage was not produced due to the housing tax (taxe d'habitation) suppression disrupting fiscal data sources.
- INSEE census (Recensement RP) files are very large (400–700 MB) and are better handled by a separate config/dataset entry for opt-in loading. Start with the small Filosofi files.
- INSEE CSVs use **semicolon separators** (`;`) and are predominantly **UTF-8** for recent files (2021+). Older vintages (pre-2020) may use Latin-1 or Windows-1252.

### INSEE CSV Format Specifics

Filosofi commune-level CSV structure (tab `filo2021_cc_rev.csv`):
- Separator: `;`
- Encoding: UTF-8 (modern files)
- Header row with INSEE variable codes (e.g., `CODGEO`, `LIBGEO`, `NBMENFISC21`, `MED21`, `D121`, `D221`, ..., `D921`)
- `CODGEO` = commune code (5 chars), `LIBGEO` = commune name
- `MED21` = median standard of living, `D121`–`D921` = income decile thresholds
- `NBMENFISC21` = number of fiscal households

**INSEE null value markers:** Filosofi files use `"s"` (secret statistique — suppressed for privacy when cell size is too small) and `"nd"` (non disponible — data not available) as string placeholders in numeric columns. Small communes regularly have suppressed decile values. These must be treated as nulls during parsing.

The loader should:
1. Download the raw CSV
2. Parse with semicolon separator and UTF-8 encoding (Latin-1 fallback)
3. Configure null value markers: `pyarrow.csv.ConvertOptions(null_values=["s", "nd", ""])`
4. Select relevant columns and rename to project-standard names (e.g., `CODGEO` → `commune_code`, `MED21` → `median_income`, `D121` → `decile_1`, etc.)
5. Cast to appropriate PyArrow types using `ConvertOptions(column_types={...})` — `commune_code` as `utf8`, income values as `float64`
6. Return as `pa.Table`

### HTTP Download — stdlib Only

The project has **no HTTP client library** in its dependencies (no `requests`, no `httpx`). Use `urllib.request` from stdlib:

```python
import io
import urllib.error
import urllib.request

def _fetch(self, config: SourceConfig) -> pa.Table:
    self._logger.debug(
        "event=fetch_start provider=%s dataset_id=%s url=%s",
        config.provider, config.dataset_id, config.url,
    )
    try:
        with urllib.request.urlopen(config.url, timeout=300) as response:
            raw_bytes = response.read()
    except (urllib.error.URLError, OSError) as exc:
        raise OSError(
            f"Failed to download {config.provider}/{config.dataset_id} from {config.url}: {exc}"
        ) from exc
    # Parse raw_bytes → pa.Table
    ...
```

**ZIP handling:** Some INSEE files are distributed as `.zip` archives. Detect by URL suffix or content-type and extract using `zipfile.ZipFile(io.BytesIO(raw_bytes))`.

**Encoding fallback:** Try UTF-8 first, fall back to Latin-1 on `UnicodeDecodeError`. This is a common pattern for INSEE files.

### Schema Design

Each dataset should have a defined output schema. The loader transforms raw INSEE column names to project-standard names:

**Filosofi commune-level output schema (example):**
```python
pa.schema([
    pa.field("commune_code", pa.utf8()),        # CODGEO
    pa.field("commune_name", pa.utf8()),         # LIBGEO
    pa.field("nb_fiscal_households", pa.int64()),# NBMENFISC21
    pa.field("median_income", pa.float64()),     # MED21
    pa.field("decile_1", pa.float64()),          # D121
    pa.field("decile_2", pa.float64()),          # D221
    pa.field("decile_3", pa.float64()),          # D321
    pa.field("decile_4", pa.float64()),          # D421
    pa.field("decile_5", pa.float64()),          # D521 (= median)
    pa.field("decile_6", pa.float64()),          # D621
    pa.field("decile_7", pa.float64()),          # D721
    pa.field("decile_8", pa.float64()),          # D821
    pa.field("decile_9", pa.float64()),          # D921
])
```

The column renaming mapping should be defined as a constant per dataset, keeping raw INSEE names documented in comments.

**Mandatory type casting:** `CachedLoader.download()` enforces exact column name and type equality against `schema()` (see `base.py:260-270`). `_fetch()` **must** return a `pa.Table` with (1) project-standard column names (not raw INSEE names), and (2) exact types matching the schema (`float64`, not auto-inferred `int64` or `string`). Use `pyarrow.csv.ConvertOptions(column_types={...})` to enforce types at parse time. The validation gate raises `DataSourceValidationError` before caching if types don't match.

### No New Dependencies Required

Everything is achievable with:
- `urllib.request` / `urllib.error` — HTTP downloads (stdlib)
- `zipfile` — ZIP extraction (stdlib)
- `io.BytesIO` — in-memory file handling (stdlib)
- `pyarrow` / `pyarrow.csv` — CSV parsing, table construction, and Parquet I/O (existing dependency)

Do **not** introduce `requests`, `pandas`, or `pynsee` as dependencies.

### CSV Parsing Strategy: pyarrow.csv

Use `pyarrow.csv.read_csv()` exclusively — it is efficient, already a project dependency, and handles type casting and null values natively. Do not use stdlib `csv` module.

```python
import pyarrow.csv as pcsv

read_options = pcsv.ReadOptions(encoding=encoding)
parse_options = pcsv.ParseOptions(delimiter=separator)
convert_options = pcsv.ConvertOptions(
    null_values=["s", "nd", ""],       # INSEE suppressed/unavailable markers
    column_types={"commune_code": pa.string(), "median_income": pa.float64(), ...},
    include_columns=["CODGEO", "LIBGEO", ...],  # Select only relevant raw columns
)
table = pcsv.read_csv(io.BytesIO(raw_bytes), read_options=read_options,
                       parse_options=parse_options, convert_options=convert_options)
# Then rename columns from raw INSEE names to project names
```

Use `ConvertOptions` for column selection, type casting, and null value handling. Column renaming is done after parsing using the `INSEEDataset.columns` mapping.

### `INSEEDataset` Design

```python
@dataclass(frozen=True)
class INSEEDataset:
    """Metadata for a known INSEE dataset."""
    dataset_id: str
    description: str
    url: str
    file_format: str  # "csv" or "zip" (INSEE distributes CSV or ZIP-wrapped CSV)
    encoding: str = "utf-8"
    separator: str = ";"
    null_markers: tuple[str, ...] = ("s", "nd", "")  # INSEE suppression markers
    columns: tuple[tuple[str, str], ...] = ()  # (raw_name, project_name) pairs
```

The `columns` field serves as both documentation and the rename mapping. `null_markers` configures `pyarrow.csv.ConvertOptions(null_values=...)`.

### Test Fixture Design

Create minimal CSV fixtures that mimic real INSEE format:

```csv
CODGEO;LIBGEO;NBMENFISC21;MED21;D121;D221;D321;D421;D521;D621;D721;D821;D921
01001;L'Abergement-Clémenciat;330;22050;12180;14790;17120;19460;22050;24950;28420;33500;42890
01002;L'Abergement-de-Varey;100;23800;13500;16200;18900;21300;23800;26700;30200;35100;44500
01003;Ambérieu-en-Bugey;5200;19850;10200;12500;14800;17200;19850;22800;26500;31800;41200
01004;Ambérieux-en-Dombes;s;s;s;s;s;s;s;s;s;s;s
01005;Ambléon;nd;nd;nd;nd;nd;nd;nd;nd;nd;nd;nd
```

Include at least one row with `"s"` (suppressed) and one with `"nd"` (non-available) markers — these are critical for testing null handling. Keep fixtures small (5-10 rows) and realistic. Store in `tests/fixtures/insee/`. Use `tmp_path` in tests for cache directories.

### Network Integration Tests

Create `tests/population/loaders/test_insee_network.py` with `@pytest.mark.network` marker. These tests hit real INSEE servers and are excluded from CI by default (`addopts = "-m 'not integration and not scale and not network'"`).

```python
@pytest.mark.network
class TestINSEELoaderRealDownload:
    def test_filosofi_commune_real_download(self, tmp_path):
        """Given a real INSEE URL, when downloaded, then returns valid table."""
        ...
```

### Project Structure Notes

- **New file:** `src/reformlab/population/loaders/insee.py` — the INSEE loader implementation
- **Modified files:**
  - `src/reformlab/population/loaders/__init__.py` — add `INSEELoader` exports
  - `src/reformlab/population/__init__.py` — add `INSEELoader` exports
  - `tests/population/loaders/conftest.py` — add INSEE fixture helpers
- **New test files:**
  - `tests/population/loaders/test_insee.py` — unit tests
  - `tests/population/loaders/test_insee_network.py` — network integration tests
- **New fixture directory:** `tests/fixtures/insee/`
- **No changes** to `pyproject.toml` (no new dependencies, `network` marker already exists from 11.1)

### Alignment with Architecture

The architecture specifies `src/reformlab/population/loaders/insee.py` explicitly. The loader satisfies `DataSourceLoader` protocol via `CachedLoader` base class, matching the pattern specified in the "External Data Caching & Offline Strategy" architecture section.

### Error Handling Notes

- `_fetch()` should only raise `OSError` for network errors — `CachedLoader.download()` handles everything else
- Invalid dataset IDs → `DataSourceValidationError` (from factory function, not from `_fetch`)
- Schema mismatches are caught by `CachedLoader.download()` automatically after `_fetch()` returns
- INSEE servers returning 404 or error pages → `urllib.error.HTTPError` (subclass of `urllib.error.URLError`) → caught by the `except (urllib.error.URLError, OSError)` clause → re-raised as `OSError`

### INSEE Data Encoding Notes

| File vintage | Encoding | Notes |
|---|---|---|
| Filosofi 2021+ | UTF-8 | Modern files, confirmed in documentation |
| RP Census 2021+ | UTF-8 | Parquet files have no encoding issues |
| Older files (pre-2020) | Latin-1 or cp1252 | Some data.gouv.fr hosted files |

The loader should try UTF-8 first, catch `UnicodeDecodeError`, then retry with Latin-1. Log the fallback as a debug event.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, `insee.py` file specification
- [Source: _bmad-output/planning-artifacts/architecture.md#External-Data-Caching-&-Offline-Strategy] — Cache protocol, offline semantics, `DataSourceLoader` protocol
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1102] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR36] — "Analyst can download and cache public datasets from institutional sources (INSEE, Eurostat, ADEME, SDES)"
- [Source: _bmad-output/planning-artifacts/prd.md#FR37] — "Analyst can browse available datasets and select which to include in a population"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/loaders/base.py] — `DataSourceLoader` Protocol, `CachedLoader` base class, `SourceConfig`, `CacheStatus`
- [Source: src/reformlab/population/loaders/cache.py] — `SourceCache` caching infrastructure
- [Source: src/reformlab/population/loaders/errors.py] — `DataSourceError` hierarchy
- [Source: tests/population/loaders/conftest.py] — `MockCachedLoader` pattern, test fixtures
- [Source: _bmad-output/implementation-artifacts/11-1-define-datasourceloader-protocol-and-caching-infrastructure.md] — Predecessor story (protocol + caching), patterns to follow
- [Source: INSEE Filosofi 2021 commune-level] — https://www.insee.fr/fr/statistiques/7758831 (income deciles by commune)
- [Source: INSEE Filosofi 2021 IRIS-level] — https://www.insee.fr/fr/statistiques/8229323 (income at IRIS level)
- [Source: INSEE API documentation] — https://www.insee.fr/fr/information/8184146 (no auth needed for file downloads)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

No debug issues encountered. All tests passed on first run after lint fixes.

### Completion Notes List

- Implemented `INSEELoader` as the first concrete `DataSourceLoader` in the codebase, extending `CachedLoader` base class from Story 11.1
- `INSEEDataset` frozen dataclass holds per-dataset metadata (URL, encoding, separator, null markers, column mapping)
- `INSEE_CATALOG` maps 3 dataset IDs to `INSEEDataset` instances: `filosofi_2021_commune`, `filosofi_2021_iris_declared`, `filosofi_2021_iris_disposable`
- Per-dataset `pa.Schema` definitions enforce exact types (utf8 for codes/names, float64 for all numeric columns including `nb_fiscal_households` — required because INSEE suppression markers make the column nullable)
- ZIP extraction handles `.csv` suffix detection (case-insensitive), with clear errors for 0 or >1 CSV entries
- CSV parsing uses `pyarrow.csv.read_csv()` with `ConvertOptions(null_values=["s","nd",""], column_types={...}, include_columns=[...])` for column selection, type casting, and null handling in one pass
- Encoding fallback: tries primary encoding (UTF-8), catches `pa.ArrowInvalid`, retries with Latin-1
- Network errors caught and re-raised as `OSError` for `CachedLoader.download()` stale-cache fallback
- 35 unit tests covering protocol compliance, schema correctness, CSV parsing, ZIP extraction, encoding fallback, suppressed values, HTTP errors, full download lifecycle, catalog/factory, and config helpers
- 1 network integration test (`@pytest.mark.network`) excluded from CI by default
- Full test suite: 1635 passed, 0 failures, 0 regressions

### File List

**New files:**
- `src/reformlab/population/loaders/insee.py` — INSEE loader implementation
- `tests/population/loaders/test_insee.py` — 35 unit tests
- `tests/population/loaders/test_insee_network.py` — network integration tests
- `tests/fixtures/insee/filosofi_2021_commune.csv` — commune-level CSV fixture (5 rows, includes "s" and "nd" markers)
- `tests/fixtures/insee/filosofi_2021_iris_declared.csv` — IRIS declared income CSV fixture (3 rows)
- `tests/fixtures/insee/filosofi_2021_iris_disposable.csv` — IRIS disposable income CSV fixture (3 rows)

**Modified files:**
- `src/reformlab/population/loaders/__init__.py` — added INSEE exports
- `src/reformlab/population/__init__.py` — added INSEE exports
- `tests/population/loaders/conftest.py` — added INSEE fixture helpers

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with INSEE data source details, CSV parsing strategy, schema design, and test fixture approach.
- 2026-03-03: Post-validation fixes — aligned AC#2 with actual catalog scope (income datasets only, household composition deferred), fixed INSEEDataset.columns type to tuple[tuple[str,str],...] rename mapping, added INSEE null marker handling (s/nd), added mandatory type casting callout, consolidated CSV parsing to pyarrow.csv only, clarified ZIP extraction strategy, added suppressed values and HTTP error test cases.
- 2026-03-03: Story implemented — all 8 tasks complete, 35 unit tests + 1 network integration test, full suite green (1635 passed), ruff clean, mypy strict clean.
