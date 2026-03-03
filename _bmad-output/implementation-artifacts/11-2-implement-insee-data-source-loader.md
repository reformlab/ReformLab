
# Story 11.2: Implement INSEE data source loader

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want an INSEE data source loader that downloads, caches, and schema-validates key INSEE datasets (Filosofi income distributions and Recensement household composition),
so that downstream merge methods (Stories 11.4–11.6) can consume real French public data as `pa.Table` objects through the `DataSourceLoader` protocol.

## Acceptance Criteria

1. Given a valid INSEE dataset identifier, when the loader downloads it, then a schema-validated `pa.Table` is returned with documented columns.
2. Given the INSEE loader, when queried for available datasets, then at least household income distribution and household composition tables are available.
3. Given an invalid or unavailable INSEE dataset ID, when requested, then a clear error identifies the specific dataset and suggests alternatives.
4. Given the INSEE loader, when run in CI, then tests use fixture files (no real network calls) marked with `pytest -m network` for opt-in integration tests.

## Tasks / Subtasks

- [ ] Task 1: Define INSEE dataset catalog and schema constants (AC: #1, #2, #3)
  - [ ] 1.1 Create `src/reformlab/population/loaders/insee.py` with module docstring referencing Story 11.2, FR36, FR37
  - [ ] 1.2 Define `INSEEDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `file_format: str` (csv or parquet), `encoding: str` (default "utf-8"), `separator: str` (default ";"), `columns: tuple[str, ...]` (expected output columns)
  - [ ] 1.3 Define the INSEE dataset catalog as a module-level `dict[str, INSEEDataset]` mapping dataset IDs to their metadata. Include at minimum:
    - `"filosofi_2021_commune"` — Filosofi 2021 commune-level income data (deciles D1–D9, median, poverty rate)
    - `"filosofi_2021_iris_declared"` — Filosofi 2021 IRIS-level declared income
    - `"filosofi_2021_iris_disposable"` — Filosofi 2021 IRIS-level disposable income
  - [ ] 1.4 Define a `pa.Schema` per dataset for the output columns the loader produces (subset of raw columns, renamed/typed to project conventions)
  - [ ] 1.5 Add a `AVAILABLE_DATASETS` module-level constant exposing the catalog keys for discovery

- [ ] Task 2: Implement `INSEELoader` class extending `CachedLoader` (AC: #1, #2)
  - [ ] 2.1 `INSEELoader.__init__(self, *, cache: SourceCache, logger: logging.Logger, dataset: INSEEDataset)` — store the dataset reference, call `super().__init__()`
  - [ ] 2.2 Implement `schema(self) -> pa.Schema` — return the schema for the loader's dataset
  - [ ] 2.3 Implement `_fetch(self, config: SourceConfig) -> pa.Table` — download the dataset from `config.url` using `urllib.request`, parse CSV (semicolon-separated, UTF-8 default with Latin-1 fallback) or Parquet, select and rename columns to match schema, return `pa.Table`
  - [ ] 2.4 Handle ZIP-wrapped CSV files (INSEE often wraps CSVs in ZIP archives): detect `.zip` suffix, extract the first `.csv` file from the archive
  - [ ] 2.5 On any network error (`urllib.error.URLError`, `OSError`, `http.client.HTTPException`), re-raise as `OSError` so `CachedLoader.download()` can handle stale-cache fallback correctly
  - [ ] 2.6 Add structured logging: `event=fetch_start`, `event=fetch_complete` with `provider=insee dataset_id=... url=... rows=... columns=...`

- [ ] Task 3: Implement `get_insee_loader` factory function (AC: #2, #3)
  - [ ] 3.1 Create `get_insee_loader(dataset_id: str, *, cache: SourceCache, logger: logging.Logger | None = None) -> INSEELoader` factory that looks up dataset from catalog and constructs the loader
  - [ ] 3.2 When `dataset_id` is not in the catalog, raise `DataSourceValidationError` with summary "Unknown INSEE dataset", reason listing the requested ID, and fix listing available dataset IDs
  - [ ] 3.3 When `logger` is `None`, default to `logging.getLogger("reformlab.population.loaders.insee")`

- [ ] Task 4: Implement `make_insee_config` helper (AC: #1, #2)
  - [ ] 4.1 Create `make_insee_config(dataset_id: str, **params: str) -> SourceConfig` convenience function that constructs a `SourceConfig` from the catalog entry, using `provider="insee"`, the catalog's URL, and any additional params
  - [ ] 4.2 When `dataset_id` is not in the catalog, raise `DataSourceValidationError` with guidance

- [ ] Task 5: Update `__init__.py` exports (AC: all)
  - [ ] 5.1 Add `INSEELoader`, `INSEEDataset`, `AVAILABLE_DATASETS`, `get_insee_loader`, `make_insee_config` to `src/reformlab/population/loaders/__init__.py`
  - [ ] 5.2 Add the same exports to `src/reformlab/population/__init__.py`

- [ ] Task 6: Create test fixtures (AC: #4)
  - [ ] 6.1 Create `tests/fixtures/insee/` directory
  - [ ] 6.2 Create small CSV fixture files mimicking Filosofi commune-level format (5-10 rows, semicolon-separated, UTF-8, with real column names from INSEE)
  - [ ] 6.3 Create a small Parquet fixture file mimicking the relevant schema
  - [ ] 6.4 Add conftest fixtures in `tests/population/loaders/conftest.py`: `insee_fixture_dir`, `filosofi_commune_csv_path`, `filosofi_commune_table`

- [ ] Task 7: Write comprehensive tests (AC: all)
  - [ ] 7.1 `tests/population/loaders/test_insee.py` — `TestINSEELoaderProtocol`: `INSEELoader` instance satisfies `DataSourceLoader` protocol via `isinstance()` check
  - [ ] 7.2 `TestINSEELoaderSchema`: `schema()` returns a valid `pa.Schema` with expected field names and types for each dataset
  - [ ] 7.3 `TestINSEELoaderFetch`: monkeypatch `urllib.request.urlopen` to return fixture CSV content; verify `_fetch()` returns correctly-parsed `pa.Table` with expected columns and types
  - [ ] 7.4 `TestINSEELoaderFetchZip`: monkeypatch `urllib.request.urlopen` to return a ZIP-wrapped CSV fixture; verify extraction and parsing
  - [ ] 7.5 `TestINSEELoaderFetchEncodingFallback`: verify Latin-1 fallback when UTF-8 decode fails
  - [ ] 7.6 `TestINSEELoaderDownloadIntegration`: full `download()` cycle via `CachedLoader` — cache miss → fetch → cache → cache hit (uses monkeypatched `_fetch`, no real network)
  - [ ] 7.7 `TestINSEELoaderCatalog`: verify `AVAILABLE_DATASETS` contains at least the required datasets, `get_insee_loader` returns correct loader, invalid ID raises error with suggestions
  - [ ] 7.8 `TestMakeInseeConfig`: verify `make_insee_config` produces correct `SourceConfig` for each catalog entry
  - [ ] 7.9 `tests/population/loaders/test_insee_network.py` — `@pytest.mark.network` integration tests: real HTTP download of a small Filosofi commune-level file, verify schema and row count are reasonable. These tests are excluded from CI by default.

- [ ] Task 8: Run full test suite and lint (AC: all)
  - [ ] 8.1 `uv run pytest tests/population/` — all tests pass
  - [ ] 8.2 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [ ] 8.3 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

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

The loader should:
1. Download the raw CSV
2. Parse with semicolon separator and UTF-8 encoding (Latin-1 fallback)
3. Select relevant columns and rename to project-standard names (e.g., `CODGEO` → `commune_code`, `MED21` → `median_income`, `D121` → `decile_1`, etc.)
4. Cast to appropriate PyArrow types (`commune_code` as `utf8`, income values as `float64`)
5. Return as `pa.Table`

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

### No New Dependencies Required

Everything is achievable with:
- `urllib.request` / `urllib.error` — HTTP downloads (stdlib)
- `zipfile` — ZIP extraction (stdlib)
- `io.BytesIO` / `io.StringIO` — in-memory file handling (stdlib)
- `csv` — CSV parsing (stdlib, use for CSV → PyArrow conversion)
- `pyarrow` — table construction and Parquet I/O (existing dependency)

Do **not** introduce `requests`, `pandas`, or `pynsee` as dependencies.

### CSV Parsing Strategy: stdlib csv → pa.Table

Since `pandas` is not a project dependency and the project uses `pa.Table` as canonical data type:

```python
import csv
import io

def _parse_csv(self, raw_bytes: bytes, encoding: str, separator: str) -> pa.Table:
    """Parse raw CSV bytes into a pa.Table with column renaming."""
    text = raw_bytes.decode(encoding)
    reader = csv.DictReader(io.StringIO(text), delimiter=separator)
    # Build column arrays from rows
    columns: dict[str, list] = {col: [] for col in self._column_mapping}
    for row in reader:
        for raw_name, project_name in self._column_mapping.items():
            columns[project_name].append(row.get(raw_name))
    # Convert to pa.Table with typed arrays
    ...
```

Alternatively, use `pyarrow.csv.read_csv()` which is already available:

```python
import pyarrow.csv as pcsv

read_options = pcsv.ReadOptions(encoding=encoding)
parse_options = pcsv.ParseOptions(delimiter=separator)
table = pcsv.read_csv(io.BytesIO(raw_bytes), read_options=read_options, parse_options=parse_options)
```

Prefer `pyarrow.csv.read_csv()` — it's more efficient and already a project dependency. Use `ConvertOptions` for column selection and type casting.

### `INSEEDataset` Design

```python
@dataclass(frozen=True)
class INSEEDataset:
    """Metadata for a known INSEE dataset."""
    dataset_id: str
    description: str
    url: str
    file_format: str  # "csv" or "parquet"
    encoding: str = "utf-8"
    separator: str = ";"
    columns: tuple[tuple[str, str], ...] = ()  # (raw_name, project_name) pairs
```

The `columns` field serves as both documentation and the rename mapping.

### Test Fixture Design

Create minimal CSV fixtures that mimic real INSEE format:

```csv
CODGEO;LIBGEO;NBMENFISC21;MED21;D121;D221;D321;D421;D521;D621;D721;D821;D921
01001;L'Abergement-Clémenciat;330;22050;12180;14790;17120;19460;22050;24950;28420;33500;42890
01002;L'Abergement-de-Varey;100;23800;13500;16200;18900;21300;23800;26700;30200;35100;44500
```

Keep fixtures small (5-10 rows) and realistic. Store in `tests/fixtures/insee/`. Use `tmp_path` in tests for cache directories.

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
- INSEE servers returning 404 or error pages → `urllib.error.HTTPError` → re-raise as `OSError`

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

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with INSEE data source details, CSV parsing strategy, schema design, and test fixture approach.
