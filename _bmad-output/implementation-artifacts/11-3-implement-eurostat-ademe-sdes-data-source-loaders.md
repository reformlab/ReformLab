
# Story 11.3: Implement Eurostat, ADEME, and SDES data source loaders

Status: dev-complete

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want concrete data source loaders for Eurostat (EU-SILC income distribution, household energy consumption), ADEME (Base Carbone emission factors), and SDES (vehicle fleet composition),
so that downstream merge methods (Stories 11.4–11.6) can consume real European and French public data as schema-validated `pa.Table` objects through the `DataSourceLoader` protocol.

## Acceptance Criteria

1. Given the Eurostat loader, when called with a valid dataset code, then EU-level household data is returned as a schema-validated `pa.Table`.
2. Given the ADEME loader, when called, then energy consumption and emission factor datasets are returned with documented schemas.
3. Given the SDES loader, when called, then vehicle fleet composition data (including vehicle age classification) is returned as a schema-validated `pa.Table`.
4. Given all three loaders, when run, then each follows the `DataSourceLoader` protocol and integrates with the caching infrastructure from BKL-1101.
5. Given CI tests for all loaders, then they use fixture files and do not require network access.

## Tasks / Subtasks

- [x] Task 1: Create Eurostat loader — `eurostat.py` (AC: #1, #4)
  - [x]1.1 Create `src/reformlab/population/loaders/eurostat.py` with module docstring referencing Story 11.3, FR36, FR37
  - [x]1.2 Define `EurostatDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `encoding: str = "utf-8"`, `separator: str = ","`, `null_markers: tuple[str, ...] = ("", ":")`, `columns: tuple[tuple[str, str], ...] = ()` where each inner tuple is `(raw_sdmx_column_name, project_column_name)` — consistent with `INSEEDataset`/`ADEMEDataset`/`SDESDataset` pattern where the dataclass is the single source of truth for parsing configuration
  - [x]1.3 Define `EUROSTAT_CATALOG` as module-level `dict[str, EurostatDataset]` with at minimum:
    - `"ilc_di01"` — Income distribution by quantile (EU-SILC deciles D1–D10, shares/EUR)
    - `"nrg_d_hhq"` — Disaggregated final energy consumption in households
  - [x]1.4 Define per-dataset `pa.Schema` objects for the output columns each dataset produces (after column selection and renaming)
  - [x]1.5 Add `EUROSTAT_AVAILABLE_DATASETS` module-level constant
  - [x]1.6 Implement `EurostatLoader(CachedLoader)` with `__init__(self, *, cache, logger, dataset)` — store dataset reference, call `super().__init__()`
  - [x]1.7 Implement `schema(self) -> pa.Schema` — return schema for this loader's dataset
  - [x]1.8 Implement `_fetch(self, config: SourceConfig) -> pa.Table` — download gzip-compressed SDMX-CSV via `urllib.request`, decompress with `gzip.decompress()`, parse with `pyarrow.csv.read_csv()`, select and rename columns, cast types, return `pa.Table`
  - [x]1.9 On any network error, re-raise as `OSError` for stale-cache fallback
  - [x]1.10 Add structured logging: `event=fetch_start`, `event=fetch_complete` with `provider=eurostat dataset_id=... rows=... columns=...`
  - [x]1.11 Implement `get_eurostat_loader(dataset_id, *, cache, logger=None)` factory function with catalog validation
  - [x]1.12 Implement `make_eurostat_config(dataset_id, **params)` helper function

- [x] Task 2: Create ADEME loader — `ademe.py` (AC: #2, #4)
  - [x]2.1 Create `src/reformlab/population/loaders/ademe.py` with module docstring referencing Story 11.3, FR36, FR37
  - [x]2.2 Define `ADEMEDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `encoding: str = "windows-1252"`, `separator: str = ";"`, `null_markers: tuple[str, ...] = ("",)`, `columns: tuple[tuple[str, str], ...] = ()` — raw-to-project column rename mapping
  - [x]2.3 Define `ADEME_CATALOG` with at minimum:
    - `"base_carbone"` — Base Carbone V23.6 emission factors (CSV from data.gouv.fr)
  - [x]2.4 Define per-dataset `pa.Schema` for the output columns (subset of the 60+ raw columns, focused on emission factors relevant to carbon tax simulation)
  - [x]2.5 Add `ADEME_AVAILABLE_DATASETS` module-level constant
  - [x]2.6 Implement `ADEMELoader(CachedLoader)` with dataset-specific parsing — handle Windows-1252 encoding (primary), UTF-8 fallback, semicolon separator
  - [x]2.7 Implement `get_ademe_loader(dataset_id, *, cache, logger=None)` factory function
  - [x]2.8 Implement `make_ademe_config(dataset_id, **params)` helper function

- [x] Task 3: Create SDES loader — `sdes.py` (AC: #3, #4)
  - [x]3.1 Create `src/reformlab/population/loaders/sdes.py` with module docstring referencing Story 11.3, FR36, FR37
  - [x]3.2 Define `SDESDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `encoding: str = "utf-8"`, `separator: str = ";"`, `null_markers: tuple[str, ...] = ("",)`, `columns: tuple[tuple[str, str], ...] = ()`, `skip_rows: int = 0` — number of header rows to skip before the column name row (DiDo CSVs may have description rows)
  - [x]3.3 Define `SDES_CATALOG` with at minimum:
    - `"vehicle_fleet"` — Vehicle fleet composition by fuel type, age, Crit'Air, region (communal-level data from data.gouv.fr)
  - [x]3.4 Define per-dataset `pa.Schema` for the output columns (fleet counts by year, fuel type, region)
  - [x]3.5 Add `SDES_AVAILABLE_DATASETS` module-level constant
  - [x]3.6 Implement `SDESLoader(CachedLoader)` with DiDo CSV parsing — UTF-8 encoding, semicolon separator; wire `SDESDataset.skip_rows` into `ReadOptions(skip_rows=self._dataset.skip_rows)`
  - [x]3.7 Implement `get_sdes_loader(dataset_id, *, cache, logger=None)` factory function
  - [x]3.8 Implement `make_sdes_config(dataset_id, **params)` helper function

- [x] Task 4: Update `__init__.py` exports (AC: #4)
  - [x]4.1 Rename `AVAILABLE_DATASETS` → `INSEE_AVAILABLE_DATASETS` in `src/reformlab/population/loaders/insee.py` and update all references (factory functions, `__init__.py`, tests). Keep a `AVAILABLE_DATASETS = INSEE_AVAILABLE_DATASETS` alias for backward compatibility until all existing code is updated.
  - [x]4.2 Add all Eurostat exports to `src/reformlab/population/loaders/__init__.py`: `EurostatDataset`, `EurostatLoader`, `EUROSTAT_AVAILABLE_DATASETS`, `get_eurostat_loader`, `make_eurostat_config`
  - [x]4.3 Add all ADEME exports to `src/reformlab/population/loaders/__init__.py`: `ADEMEDataset`, `ADEMELoader`, `ADEME_AVAILABLE_DATASETS`, `get_ademe_loader`, `make_ademe_config`
  - [x]4.4 Add all SDES exports to `src/reformlab/population/loaders/__init__.py`: `SDESDataset`, `SDESLoader`, `SDES_AVAILABLE_DATASETS`, `get_sdes_loader`, `make_sdes_config`
  - [x]4.5 Add the same exports to `src/reformlab/population/__init__.py`

- [x] Task 5: Create test fixtures (AC: #5)
  - [x]5.1 Create `tests/fixtures/eurostat/` directory with small SDMX-CSV fixtures mimicking `ilc_di01` and `nrg_d_hhq` format (5–10 rows each, comma-separated, UTF-8)
  - [x]5.2 Create `tests/fixtures/ademe/` directory with small CSV fixture mimicking Base Carbone format (5–10 rows, semicolon-separated, Windows-1252 encoded)
  - [x]5.3 Create `tests/fixtures/sdes/` directory with small CSV fixture mimicking DiDo vehicle fleet format (5–10 rows, semicolon-separated, UTF-8)
  - [x]5.4 Add fixture helpers in `tests/population/loaders/conftest.py`: paths and byte-reading fixtures for each provider

- [x] Task 6: Write comprehensive tests (AC: all)
  - [x]6.1 `tests/population/loaders/test_eurostat.py`:
    - `TestEurostatLoaderProtocol`: `isinstance()` check against `DataSourceLoader`
    - `TestEurostatLoaderSchema`: `schema()` returns valid `pa.Schema` for each dataset
    - `TestEurostatLoaderFetch`: monkeypatch `urllib.request.urlopen` to return gzip-compressed fixture; verify `_fetch()` returns correctly-parsed `pa.Table`
    - `TestEurostatLoaderFetchMissingValues`: verify `:` and empty cells produce nulls
    - `TestEurostatLoaderFetchBadGzip`: verify `gzip.BadGzipFile` on corrupt gzip content raises `DataSourceValidationError` (not `OSError`) — prevents wrong stale-cache fallback since `BadGzipFile` inherits from `OSError`
    - `TestEurostatLoaderFetchHTTPError`: verify network errors re-raised as `OSError`
    - `TestEurostatLoaderDownloadIntegration`: full `download()` lifecycle via `CachedLoader`
    - `TestEurostatLoaderCatalog`: catalog completeness, factory function, invalid ID error
    - `TestMakeEurostatConfig`: config construction for each catalog entry
  - [x]6.2 `tests/population/loaders/test_ademe.py`:
    - `TestADEMELoaderProtocol`: protocol compliance
    - `TestADEMELoaderSchema`: schema correctness
    - `TestADEMELoaderFetch`: monkeypatch fetch with Windows-1252 fixture; verify parsing
    - `TestADEMELoaderFetchEncodingFallback`: UTF-8 fallback when primary encoding fails
    - `TestADEMELoaderFetchHTTPError`: network error handling
    - `TestADEMELoaderDownloadIntegration`: full download lifecycle
    - `TestADEMELoaderCatalog`: catalog and factory
    - `TestMakeAdemeConfig`: config construction
  - [x]6.3 `tests/population/loaders/test_sdes.py`:
    - `TestSDESLoaderProtocol`: protocol compliance
    - `TestSDESLoaderSchema`: schema correctness
    - `TestSDESLoaderFetch`: monkeypatch fetch with fixture; verify parsing
    - `TestSDESLoaderFetchSkipRows`: fixture with leading description rows; verify `skip_rows > 0` correctly skips to the header row
    - `TestSDESLoaderFetchHTTPError`: network error handling
    - `TestSDESLoaderDownloadIntegration`: full download lifecycle
    - `TestSDESLoaderCatalog`: catalog and factory
    - `TestMakeSDESConfig`: config construction

- [x] Task 7: Network integration tests (AC: #5)
  - [x]7.1 `tests/population/loaders/test_eurostat_network.py` — `@pytest.mark.network` real download of `ilc_di01` (small dataset)
  - [x]7.2 `tests/population/loaders/test_ademe_network.py` — `@pytest.mark.network` real download of Base Carbone CSV
  - [x]7.3 `tests/population/loaders/test_sdes_network.py` — `@pytest.mark.network` real download of vehicle fleet data

- [x] Task 8: Run full test suite and lint (AC: all)
  - [x]8.1 `uv run pytest tests/population/` — all tests pass
  - [x]8.2 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [x]8.3 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

## Dev Notes

### Architecture Context: Three Loaders Following the INSEE Pattern

This story implements 3 concrete `DataSourceLoader` implementations, all following the pattern established by `INSEELoader` in Story 11.2. The architecture specifies these files explicitly in `src/reformlab/population/loaders/`:

```
src/reformlab/population/loaders/
├── base.py        ← DataSourceLoader protocol + CachedLoader (Story 11.1)
├── cache.py       ← SourceCache (Story 11.1)
├── errors.py      ← Error hierarchy (Story 11.1)
├── insee.py       ← INSEELoader (Story 11.2) — THE TEMPLATE TO FOLLOW
├── eurostat.py    ← NEW: EurostatLoader (this story)
├── ademe.py       ← NEW: ADEMELoader (this story)
└── sdes.py        ← NEW: SDESLoader (this story)
```

**Every loader MUST:**

1. Subclass `CachedLoader` with keyword-only `__init__` accepting `cache: SourceCache`, `logger: logging.Logger`, and a loader-specific dataset dataclass
2. Override `schema() -> pa.Schema` returning per-dataset schema
3. Override `_fetch(config: SourceConfig) -> pa.Table` performing network download + parsing
4. Re-raise **all** network errors as `OSError` (enables `CachedLoader.download()` stale-cache fallback)
5. Use `DataSourceValidationError` for format/parsing errors (not `OSError`)
6. Provide a `get_{provider}_loader(dataset_id, *, cache, logger=None)` factory function
7. Provide a `make_{provider}_config(dataset_id, **params)` config helper
8. Export a frozen `{Provider}Dataset` dataclass and `{PROVIDER}_AVAILABLE_DATASETS` tuple
9. Use structured logging: `event=fetch_start`, `event=fetch_complete` with `provider=`, `dataset_id=`, etc.

### CachedLoader Contract (CRITICAL — read `base.py`)

The `CachedLoader.download()` method (lines 188–274 of `base.py`) orchestrates the full lifecycle. Concrete loaders ONLY implement `_fetch()` and `schema()`. Key contract rules:

- `_fetch()` **MUST** return a `pa.Table` with exact column names and types matching `schema()`. The validation gate at lines 246–270 checks column names (set equality) and types (exact match per field). A `float64` column in the schema requires `float64` in the table — not `int64`, not `string`.
- `_fetch()` **MUST** raise `OSError` on network failure. `CachedLoader.download()` catches `OSError` to trigger stale-cache fallback (line 230). Any other exception type bypasses fallback and propagates directly.
- `_fetch()` **MUST NOT** interact with the cache. Caching is handled by `CachedLoader.download()` after schema validation passes.

### No New Dependencies Required

All three loaders use only existing dependencies and stdlib:

- `urllib.request` / `urllib.error` — HTTP downloads (stdlib)
- `gzip` — gzip decompression for Eurostat (stdlib)
- `io.BytesIO` — in-memory file handling (stdlib)
- `pyarrow` / `pyarrow.csv` — CSV parsing, table construction (existing dependency)
- `http.client` — for `HTTPException` in network error handling (stdlib)

Do **not** introduce `requests`, `httpx`, `pandas`, `openpyxl`, or any new dependency.

### Network Error Handling Pattern (from INSEE)

All three loaders must follow the same network error handling pattern:

```python
_NETWORK_ERRORS: tuple[type[Exception], ...] = (
    urllib.error.URLError,
    OSError,
    http.client.HTTPException,
)

_HTTP_TIMEOUT_SECONDS = 300

def _fetch(self, config: SourceConfig) -> pa.Table:
    try:
        with urllib.request.urlopen(config.url, timeout=_HTTP_TIMEOUT_SECONDS) as response:
            raw_bytes = response.read()
    except _NETWORK_ERRORS as exc:
        raise OSError(
            f"Failed to download {provider}/{dataset_id} from {url}: {exc}"
        ) from exc
    # Parse raw_bytes → pa.Table ...
```

---

## Eurostat Loader — Detailed Specification

### Data Source: Eurostat SDMX 2.1 API

Eurostat provides bulk data via the SDMX 2.1 Dissemination API. No authentication required. Fully public, anonymous HTTPS GET.

**API base URL:**
```
https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{DATASET_CODE}
```

**Format choice: SDMX-CSV** (not TSV). SDMX-CSV is a standard long-format CSV (one observation per row) that pyarrow.csv can parse directly. TSV has a non-standard header format that requires custom parsing.

**Download URL pattern with gzip compression:**
```
https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{CODE}?format=SDMX-CSV&compressed=true
```

With `compressed=true`, the API returns a gzip-compressed `.csv.gz` file. This is **file-level compression** (not HTTP Content-Encoding), so `urllib` does NOT decompress it automatically. Use `gzip.decompress(raw_bytes)` to get the CSV content.

### Eurostat Datasets

| Dataset ID | Code | Description | Size (compressed) | Key Variables |
|---|---|---|---|---|
| `ilc_di01` | `ilc_di01` | Income distribution by quantile (EU-SILC) | ~75 KB | Income shares by decile (D1–D10), by country, by year |
| `nrg_d_hhq` | `nrg_d_hhq` | Household energy consumption | ~150 KB | Energy use in GWh by fuel type, end-use, country, year |

### SDMX-CSV Format Specifics

**Encoding:** UTF-8 (pure ASCII for dimension codes and numeric values).
**Separator:** Comma (`,`).
**Line endings:** `\r\n` (CRLF).

**Column structure per dataset:**

`ilc_di01` SDMX-CSV columns:
```
DATAFLOW,LAST UPDATE,freq,quantile,indic_il,currency,geo,TIME_PERIOD,OBS_VALUE,OBS_FLAG
```

Example rows:
```csv
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D1,SHARE,EUR,FR,2022,3.3,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D2,SHARE,EUR,FR,2022,4.8,b
```

`nrg_d_hhq` SDMX-CSV columns:
```
DATAFLOW,LAST UPDATE,freq,nrg_bal,siec,unit,geo,TIME_PERIOD,OBS_VALUE,OBS_FLAG
```

**Metadata columns to DROP:** `DATAFLOW`, `LAST UPDATE` (not useful for analysis).

**Missing values:** `OBS_VALUE` may be empty (missing observation). Use `null_values=["", ":"]` in ConvertOptions.

**Observation flags** (`OBS_FLAG`): Single or combined letters indicating data quality:
- `b` = break in time series, `e` = estimated, `p` = provisional, `c` = confidential, `u` = low reliability
- Flags are informational strings — keep as `utf8` type.

### Eurostat Column Mapping and Schemas

**`ilc_di01` column mapping:**
```python
_ILC_DI01_COLUMNS: tuple[tuple[str, str], ...] = (
    ("freq", "frequency"),
    ("quantile", "quantile"),
    ("indic_il", "indicator"),
    ("currency", "currency"),
    ("geo", "country"),
    ("TIME_PERIOD", "time_period"),
    ("OBS_VALUE", "value"),
    ("OBS_FLAG", "obs_flag"),
)
```

**`ilc_di01` output schema:**
```python
pa.schema([
    pa.field("frequency", pa.utf8()),
    pa.field("quantile", pa.utf8()),
    pa.field("indicator", pa.utf8()),
    pa.field("currency", pa.utf8()),
    pa.field("country", pa.utf8()),
    pa.field("time_period", pa.utf8()),
    pa.field("value", pa.float64()),
    pa.field("obs_flag", pa.utf8()),
])
```

**`nrg_d_hhq` column mapping:**
```python
_NRG_D_HHQ_COLUMNS: tuple[tuple[str, str], ...] = (
    ("freq", "frequency"),
    ("nrg_bal", "energy_balance"),
    ("siec", "energy_product"),
    ("unit", "unit"),
    ("geo", "country"),
    ("TIME_PERIOD", "time_period"),
    ("OBS_VALUE", "value"),
    ("OBS_FLAG", "obs_flag"),
)
```

**`nrg_d_hhq` output schema:**
```python
pa.schema([
    pa.field("frequency", pa.utf8()),
    pa.field("energy_balance", pa.utf8()),
    pa.field("energy_product", pa.utf8()),
    pa.field("unit", pa.utf8()),
    pa.field("country", pa.utf8()),
    pa.field("time_period", pa.utf8()),
    pa.field("value", pa.float64()),
    pa.field("obs_flag", pa.utf8()),
])
```

### Eurostat Parsing Strategy

```python
import gzip

def _fetch(self, config: SourceConfig) -> pa.Table:
    # 1. Download gzip-compressed SDMX-CSV
    raw_bytes = ...  # urllib.request.urlopen(config.url)

    # 2. Decompress gzip (file-level, NOT http-level)
    #    CRITICAL: gzip.BadGzipFile inherits from OSError. If not caught
    #    explicitly here, it propagates as OSError and CachedLoader.download()
    #    triggers stale-cache fallback instead of raising a validation error.
    try:
        csv_bytes = gzip.decompress(raw_bytes)
    except (OSError, gzip.BadGzipFile) as exc:
        raise DataSourceValidationError(
            summary="Gzip decompression failed",
            reason=f"Downloaded content for eurostat/{self._dataset.dataset_id} "
                   f"is not valid gzip: {exc}",
            fix="Check the Eurostat API URL and compressed=true parameter",
        ) from exc

    # 3. Parse with pyarrow.csv
    ds = self._dataset
    raw_names = [col[0] for col in ds.columns]
    project_names = [col[1] for col in ds.columns]
    schema = self.schema()

    column_types: dict[str, pa.DataType] = {}
    for raw_name, proj_name in ds.columns:
        column_types[raw_name] = schema.field(proj_name).type

    convert_options = pcsv.ConvertOptions(
        null_values=list(ds.null_markers),
        column_types=column_types,
        include_columns=raw_names,
    )
    parse_options = pcsv.ParseOptions(delimiter=ds.separator)
    read_options = pcsv.ReadOptions(encoding=ds.encoding)

    table = pcsv.read_csv(
        io.BytesIO(csv_bytes),
        read_options=read_options,
        parse_options=parse_options,
        convert_options=convert_options,
    )

    # 4. Rename columns
    table = table.rename_columns(project_names)
    return table
```

### Eurostat Fixture Design

Create `tests/fixtures/eurostat/ilc_di01.csv` (NOT gzip-compressed, plain CSV for readability — the test wraps it in gzip at runtime):

```csv
DATAFLOW,LAST UPDATE,freq,quantile,indic_il,currency,geo,TIME_PERIOD,OBS_VALUE,OBS_FLAG
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D1,SHARE,EUR,FR,2022,3.3,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D2,SHARE,EUR,FR,2022,4.8,b
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D3,SHARE,EUR,FR,2022,5.9,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D4,SHARE,EUR,FR,2022,6.8,
ESTAT:ILC_DI01(1.0),2024-03-15T23:00:00+0100,A,D5,SHARE,EUR,DE,2022,,c
```

Note: last row has empty OBS_VALUE (missing) and flag "c" (confidential). Tests should verify this produces `null` in the `value` column.

---

## ADEME Loader — Detailed Specification

### Data Source: Base Carbone via data.gouv.fr

ADEME provides the Base Carbone emission factors as a CSV download on data.gouv.fr. No authentication required. The data.gouv.fr URL serves the file directly.

**Download URL (stable data.gouv.fr resource):**
```
https://www.data.gouv.fr/api/1/datasets/r/ac6a3044-459c-4520-b85a-7e1740f7cd1f
```

**Current version:** V23.6 (updated February 2026), ~10.3 MB, ~18,600 emission factor records.

### ADEME CSV Format Specifics

**CRITICAL: Encoding is Windows-1252 (cp1252), NOT UTF-8.** This is the most important difference from INSEE and Eurostat. French characters like `é`, `è`, `ê`, `ô` are encoded as single bytes in Windows-1252 that are invalid UTF-8.

**Separator:** Semicolon (`;`).
**Line endings:** `\r\n` (CRLF).
**Quote character:** `"` (standard CSV quoting).

**Encoding handling strategy:**

`pyarrow.csv.ReadOptions(encoding=...)` supports Python codec names. Use `"windows-1252"` as the primary encoding, with `"utf-8"` as fallback (in case ADEME switches to UTF-8 in future versions). Follow the same try/catch `pa.ArrowInvalid` pattern as INSEE's encoding fallback:

```python
read_options = pcsv.ReadOptions(encoding="windows-1252")
try:
    table = pcsv.read_csv(io.BytesIO(raw_bytes), ...)
except pa.ArrowInvalid:
    # Fallback to UTF-8 (future-proofing)
    read_options = pcsv.ReadOptions(encoding="utf-8")
    table = pcsv.read_csv(io.BytesIO(raw_bytes), ...)
```

### ADEME Column Mapping and Schema

The Base Carbone CSV has 60+ columns. Select only those relevant to carbon tax microsimulation. The raw column names are French with spaces and accents:

**`base_carbone` column mapping (key subset):**
```python
_BASE_CARBONE_COLUMNS: tuple[tuple[str, str], ...] = (
    ("Identifiant de l'élément", "element_id"),
    ("Nom base français", "name_fr"),
    ("Nom attribut français", "attribute_name_fr"),
    ("Type Ligne", "line_type"),
    ("Unité français", "unit_fr"),
    ("Total poste non décomposé", "total_co2e"),
    ("CO2f", "co2_fossil"),
    ("CH4f", "ch4_fossil"),
    ("CH4b", "ch4_biogenic"),
    ("N2O", "n2o"),
    ("CO2b", "co2_biogenic"),
    ("Autre GES", "other_ghg"),
    ("Localisation géographique", "geography"),
    ("Sous-localisation géographique français", "sub_geography"),
    ("Contributeur", "contributor"),
)
```

**Note on column names:** See "Column Name Verification Strategy" section below for the approach to handling column name drift across data vintages.

**`base_carbone` output schema:**
```python
pa.schema([
    pa.field("element_id", pa.int64()),
    pa.field("name_fr", pa.utf8()),
    pa.field("attribute_name_fr", pa.utf8()),
    pa.field("line_type", pa.utf8()),
    pa.field("unit_fr", pa.utf8()),
    pa.field("total_co2e", pa.float64()),
    pa.field("co2_fossil", pa.float64()),
    pa.field("ch4_fossil", pa.float64()),
    pa.field("ch4_biogenic", pa.float64()),
    pa.field("n2o", pa.float64()),
    pa.field("co2_biogenic", pa.float64()),
    pa.field("other_ghg", pa.float64()),
    pa.field("geography", pa.utf8()),
    pa.field("sub_geography", pa.utf8()),
    pa.field("contributor", pa.utf8()),
])
```

**IMPORTANT:** See "Column Name Verification Strategy" section for handling column name drift. Run the network integration test early to verify ADEME headers match the mapping above.

### ADEME Fixture Design

Create `tests/fixtures/ademe/base_carbone.csv` — a small file (5–10 rows) encoded in **Windows-1252** with semicolon separator, mimicking the real Base Carbone format. Include:
- At least one row with French characters (`é`, `è`, `ê`) to test encoding
- At least one row with empty/null emission values
- Realistic column names from the real dataset

```
Identifiant de l'élément;Nom base français;Nom attribut français;Type Ligne;Unité français;Total poste non décomposé;CO2f;CH4f;CH4b;N2O;CO2b;Autre GES;Localisation géographique;Sous-localisation géographique français;Contributeur
1234;Gaz naturel;PCI;Elément;kgCO2e/kWh PCI;0.227;0.205;0.004;0;0.018;0;0;France métropolitaine;;ADEME
5678;Fioul domestique;PCI;Elément;kgCO2e/litre;3.25;3.15;0.001;0;0.089;0;0;France métropolitaine;;ADEME
9012;Électricité;Mix moyen;Elément;kgCO2e/kWh;0.0569;0.0479;0;0;0.009;0;0;France métropolitaine;;ADEME
```

**The fixture MUST be saved as Windows-1252 encoding**, not UTF-8. The `Write` tool outputs UTF-8, so the fixture must be generated programmatically. Add a fixture helper to `tests/population/loaders/conftest.py`:

```python
@pytest.fixture()
def ademe_base_carbone_csv_bytes() -> bytes:
    """Windows-1252 encoded ADEME Base Carbone CSV fixture."""
    content = (
        "Identifiant de l'élément;Nom base français;Nom attribut français;"
        "Type Ligne;Unité français;Total poste non décomposé;CO2f;CH4f;"
        "CH4b;N2O;CO2b;Autre GES;Localisation géographique;"
        "Sous-localisation géographique français;Contributeur\r\n"
        "1234;Gaz naturel;PCI;Elément;kgCO2e/kWh PCI;0.227;0.205;0.004;"
        "0;0.018;0;0;France métropolitaine;;ADEME\r\n"
        # ... more rows with French characters (é, è, ê) ...
    )
    return content.encode("windows-1252")
```

Tests that monkeypatch `_fetch` should use these bytes directly. The on-disk fixture file at `tests/fixtures/ademe/base_carbone.csv` should be created by a one-time setup script writing `content.encode("windows-1252")` to disk, NOT by the `Write` tool. Include at least one non-ASCII French character (e.g., `é` in `métropolitaine`, `è` in `Elément`) to verify encoding — these differ between UTF-8 (multi-byte) and Windows-1252 (single-byte).

---

## SDES Loader — Detailed Specification

### Data Source: Vehicle Fleet via data.gouv.fr

SDES provides communal-level vehicle fleet data as CSV on data.gouv.fr. The national/regional aggregates are XLSX-only (requires openpyxl, which we don't have), so use the communal-level CSV instead.

**Download URL (data.gouv.fr resource for communal vehicle fleet):**
```
https://www.data.gouv.fr/api/1/datasets/r/2f9fd9c8-e6e1-450e-8548-f479b8a401cd
```

**Alternative: DiDo API endpoint:**
```
https://data.statistiques.developpement-durable.gouv.fr/dido/api/v1/datafiles/3750a580-f249-42d3-b488-5cf8acb767b7/csv?millesime=2023-05&withColumnName=true&withColumnDescription=false&withColumnUnit=false
```

**Decision:** Use the data.gouv.fr URL in `SDES_CATALOG["vehicle_fleet"].url` for simplicity (single GET, no query params needed). The DiDo API URL above is informational only — do not use it in the catalog.

**Note:** The data.gouv.fr resource ID (`2f9fd9c8-...`) may change when new data vintages are published. The URL is stored in the catalog constant and can be updated easily.

### SDES CSV Format Specifics

**Encoding:** UTF-8.
**Separator:** Semicolon (`;`).
**Line endings:** Standard (`\n` or `\r\n`).
**Missing values:** Empty fields (no special markers observed).
**File size:** Large (~10 MB). This is fine for download/cache but test fixtures must be small.

**The DiDo CSV may have multiple header rows** (descriptions, units, column names). The data.gouv.fr version typically has a single header row. If using DiDo API directly, use query parameters `withColumnDescription=false&withColumnUnit=false` to get clean single-header output.

### SDES Column Mapping and Schema

The CSV columns include geographic codes, vehicle classification, and fleet counts by year:

**`vehicle_fleet` column mapping (key subset):**
```python
_VEHICLE_FLEET_COLUMNS: tuple[tuple[str, str], ...] = (
    ("REGION_CODE", "region_code"),
    ("REGION_LIBELLE", "region_name"),
    ("CLASSE_VEHICULE", "vehicle_class"),
    ("CATEGORIE_VEHICULE", "vehicle_category"),
    ("CARBURANT", "fuel_type"),
    ("AGE", "vehicle_age"),
    ("CRITAIR", "critair_sticker"),
    ("PARC_2022", "fleet_count_2022"),
)
```

**Note on column selection:** The raw CSV has fleet count columns for many years (`PARC_2011` through `PARC_2022` or later). For the initial loader, select only the most recent year column to keep the schema manageable. The mapping can be expanded later.

**Alternative approach:** Select multiple year columns:
```python
("PARC_2018", "fleet_2018"),
("PARC_2019", "fleet_2019"),
("PARC_2020", "fleet_2020"),
("PARC_2021", "fleet_2021"),
("PARC_2022", "fleet_2022"),
```

**`vehicle_fleet` output schema:**
```python
pa.schema([
    pa.field("region_code", pa.utf8()),
    pa.field("region_name", pa.utf8()),
    pa.field("vehicle_class", pa.utf8()),
    pa.field("vehicle_category", pa.utf8()),
    pa.field("fuel_type", pa.utf8()),
    pa.field("vehicle_age", pa.utf8()),
    pa.field("critair_sticker", pa.utf8()),
    pa.field("fleet_count_2022", pa.float64()),  # float64 for null handling
])
```

**Note:** Fleet counts use `float64` (not `int64`) to handle potential null values, following the same pattern as INSEE's `nb_fiscal_households`.

**IMPORTANT:** See "Column Name Verification Strategy" section for handling column name drift. Run the network integration test early to verify SDES headers match the mapping above.

### SDES Fixture Design

Create `tests/fixtures/sdes/vehicle_fleet.csv` — a small CSV (5–10 rows) mimicking the DiDo format:

```csv
REGION_CODE;REGION_LIBELLE;CLASSE_VEHICULE;CATEGORIE_VEHICULE;CARBURANT;AGE;CRITAIR;PARC_2022
84;Auvergne-Rhône-Alpes;VP;M1;Diesel;De 1 à 5 ans;Crit'Air 2;450000
84;Auvergne-Rhône-Alpes;VP;M1;Essence;De 1 à 5 ans;Crit'Air 1;380000
84;Auvergne-Rhône-Alpes;VP;M1;Electrique;De 1 à 5 ans;Crit'Air E;95000
11;Île-de-France;VP;M1;Diesel;De 1 à 5 ans;Crit'Air 2;520000
11;Île-de-France;VP;M1;Essence;Plus de 15 ans;;
```

Include at least one row with empty fleet count to test null handling.

---

### Test Pattern to Follow (from INSEE tests)

Follow the exact test structure from `tests/population/loaders/test_insee.py`:

1. **Test helpers** at top of file: `_make_gzip()` (for Eurostat), `_mock_urlopen()` (reuse from INSEE pattern):
   ```python
   def _make_gzip(csv_bytes: bytes) -> bytes:
       """Create gzip-compressed bytes from CSV content."""
       return gzip.compress(csv_bytes)
   ```
2. **Protocol compliance class**: verify `isinstance(loader, DataSourceLoader)`
3. **Schema class**: verify field names and types for each dataset
4. **Fetch class**: monkeypatch `urllib.request.urlopen` to return fixture data; for Eurostat, wrap fixture in gzip first
5. **Error handling class**: verify network errors become `OSError`
6. **Download integration class**: full `CachedLoader.download()` cycle — cache miss → fetch → cache → cache hit
7. **Catalog class**: verify `AVAILABLE_DATASETS`, factory function, invalid ID error
8. **Config class**: verify `make_{provider}_config` produces correct `SourceConfig`

### Network Integration Tests

Create `test_{provider}_network.py` files with `@pytest.mark.network` marker. These are excluded from CI by default (`addopts = "-m 'not integration and not scale and not network'"` in pyproject.toml).

For Eurostat network tests, download the smallest dataset (`ilc_di01` at ~75 KB compressed) to verify schema and basic row count. For ADEME and SDES, download and verify similarly.

### Project Structure Notes

**New files:**
- `src/reformlab/population/loaders/eurostat.py`
- `src/reformlab/population/loaders/ademe.py`
- `src/reformlab/population/loaders/sdes.py`
- `tests/population/loaders/test_eurostat.py`
- `tests/population/loaders/test_ademe.py`
- `tests/population/loaders/test_sdes.py`
- `tests/population/loaders/test_eurostat_network.py`
- `tests/population/loaders/test_ademe_network.py`
- `tests/population/loaders/test_sdes_network.py`
- `tests/fixtures/eurostat/ilc_di01.csv`
- `tests/fixtures/eurostat/nrg_d_hhq.csv`
- `tests/fixtures/ademe/base_carbone.csv`
- `tests/fixtures/sdes/vehicle_fleet.csv`

**Modified files:**
- `src/reformlab/population/loaders/__init__.py` — add all new exports
- `src/reformlab/population/__init__.py` — add all new exports
- `tests/population/loaders/conftest.py` — add fixture helpers for Eurostat, ADEME, SDES

**No changes** to `pyproject.toml` (no new dependencies, `network` marker already exists from Story 11.1)

### Alignment with Architecture

The architecture (`architecture.md`) specifies:

```
src/reformlab/population/
├── loaders/
│   ├── base.py        ← DataSourceLoader protocol (Story 11.1)
│   ├── insee.py       ← INSEE data loader (Story 11.2)
│   ├── eurostat.py    ← Eurostat data loader (this story)
│   ├── ademe.py       ← ADEME energy data loader (this story)
│   └── sdes.py        ← SDES vehicle fleet data loader (this story)
```

All loaders satisfy `DataSourceLoader` protocol via `CachedLoader` base class, matching the "External Data Caching & Offline Strategy" architecture section. Cache paths follow `~/.reformlab/cache/sources/{provider}/{dataset_id}/{hash}.parquet`.

### Error Handling Notes

- `_fetch()` should only raise `OSError` for network errors — `CachedLoader.download()` handles everything else
- Invalid dataset IDs → `DataSourceValidationError` (from factory function, not from `_fetch`)
- Schema mismatches are caught by `CachedLoader.download()` automatically after `_fetch()` returns
- For Eurostat gzip decompression errors → raise `DataSourceValidationError` (not `OSError`, since the download succeeded but the content is invalid)

### Column Name Verification Strategy

For all three data sources, the exact raw column names may vary across data vintages. The recommended approach:

1. **Start with the column names documented in this story** (based on 2026-03 research)
2. **Run the network integration test** early in development to verify column names against live data
3. **If column names differ**, update the catalog constants and fixtures accordingly
4. **Document any discrepancies** in the dev agent record

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#New-Subsystem-Population-Generation] — Directory structure, loader file specifications
- [Source: _bmad-output/planning-artifacts/architecture.md#External-Data-Caching-&-Offline-Strategy] — Cache protocol, offline semantics, DataSourceLoader protocol
- [Source: _bmad-output/planning-artifacts/epics.md#BKL-1103] — Story definition and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR36] — "Analyst can download and cache public datasets from institutional sources"
- [Source: _bmad-output/planning-artifacts/prd.md#FR37] — "Analyst can browse available datasets and select which to include in a population"
- [Source: _bmad-output/project-context.md#Python-Language-Rules] — Frozen dataclasses, Protocols, `from __future__ import annotations`
- [Source: _bmad-output/project-context.md#Critical-Implementation-Rules] — PyArrow canonical data type, no pandas in core logic
- [Source: src/reformlab/population/loaders/base.py] — DataSourceLoader Protocol, CachedLoader base class, SourceConfig, CacheStatus
- [Source: src/reformlab/population/loaders/cache.py] — SourceCache caching infrastructure
- [Source: src/reformlab/population/loaders/errors.py] — DataSourceError hierarchy
- [Source: src/reformlab/population/loaders/insee.py] — INSEELoader concrete implementation (THE PATTERN TO FOLLOW)
- [Source: tests/population/loaders/test_insee.py] — INSEE test patterns to replicate
- [Source: tests/population/loaders/conftest.py] — Test fixture patterns, MockCachedLoader
- [Source: _bmad-output/implementation-artifacts/11-1-define-datasourceloader-protocol-and-caching-infrastructure.md] — Story 11.1 (protocol + caching)
- [Source: _bmad-output/implementation-artifacts/11-2-implement-insee-data-source-loader.md] — Story 11.2 (INSEE loader, predecessor)
- [Source: Eurostat SDMX 2.1 API] — https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/sdmx2.1
- [Source: Eurostat ilc_di01] — https://ec.europa.eu/eurostat/databrowser/product/page/ilc_di01
- [Source: Eurostat nrg_d_hhq] — https://ec.europa.eu/eurostat/databrowser/product/page/NRG_D_HHQ
- [Source: Base Carbone on data.gouv.fr] — https://www.data.gouv.fr/datasets/base-carbone-r-2
- [Source: SDES Vehicle Fleet on data.gouv.fr] — https://www.data.gouv.fr/datasets/parc-de-vehicules-routiers

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None — clean implementation with one test fix (ADEME encoding fallback needed `ArrowKeyError` in addition to `ArrowInvalid`).

### Completion Notes List

- All 3 loaders (Eurostat, ADEME, SDES) implemented following the INSEE pattern exactly
- `AVAILABLE_DATASETS` renamed to `INSEE_AVAILABLE_DATASETS` with backward-compatible alias
- ADEME encoding fallback catches both `pa.ArrowInvalid` and `pa.lib.ArrowKeyError` (UTF-8 bytes decoded as Windows-1252 garble column names, producing `ArrowKeyError` not `ArrowInvalid`)
- Eurostat gzip decompression errors correctly raise `DataSourceValidationError` (not `OSError`) to prevent wrong stale-cache fallback
- ADEME fixture written as Windows-1252 via Python script (Write tool outputs UTF-8)
- 87 new tests + 1723 total pass, 0 regressions
- ruff, mypy strict: all clean

### File List

**New files:**
- `src/reformlab/population/loaders/eurostat.py`
- `src/reformlab/population/loaders/ademe.py`
- `src/reformlab/population/loaders/sdes.py`
- `tests/population/loaders/test_eurostat.py`
- `tests/population/loaders/test_ademe.py`
- `tests/population/loaders/test_sdes.py`
- `tests/population/loaders/test_eurostat_network.py`
- `tests/population/loaders/test_ademe_network.py`
- `tests/population/loaders/test_sdes_network.py`
- `tests/fixtures/eurostat/ilc_di01.csv`
- `tests/fixtures/eurostat/nrg_d_hhq.csv`
- `tests/fixtures/ademe/base_carbone.csv`
- `tests/fixtures/sdes/vehicle_fleet.csv`

**Modified files:**
- `src/reformlab/population/loaders/insee.py` — renamed `AVAILABLE_DATASETS` → `INSEE_AVAILABLE_DATASETS` + alias
- `src/reformlab/population/loaders/__init__.py` — added all new exports
- `src/reformlab/population/__init__.py` — added all new exports
- `tests/population/loaders/conftest.py` — added Eurostat, ADEME, SDES fixture helpers

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with Eurostat SDMX-CSV parsing, ADEME Windows-1252 handling, SDES DiDo CSV format, test fixture designs, and verified download URLs.
- 2026-03-03: Story implemented — all 3 loaders, 87 new tests, full CI validation (ruff + mypy strict + 1723 tests pass).
