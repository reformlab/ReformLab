<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 3 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260303T134029Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 11.3

You are synthesizing 2 independent validator reviews.

Your mission:
1. VERIFY each issue raised by validators
   - Cross-reference with story content
   - Identify false positives (issues that aren't real problems)
   - Confirm valid issues with evidence

2. PRIORITIZE real issues by severity
   - Critical: Blocks implementation or causes major problems
   - High: Significant gaps or ambiguities
   - Medium: Improvements that would help
   - Low: Nice-to-have suggestions

3. SYNTHESIZE findings
   - Merge duplicate issues from different validators
   - Note validator consensus (if 3+ agree, high confidence)
   - Highlight unique insights from individual validators

4. APPLY changes to story file
   - You have WRITE PERMISSION to modify the story
   - CRITICAL: Before using Edit tool, ALWAYS Read the target file first
   - Use EXACT content from Read tool output as old_string, NOT content from this prompt
   - If Read output is truncated, use offset/limit parameters to locate the target section
   - Apply fixes for verified issues
   - Document what you changed and why

Output format:
## Synthesis Summary
## Issues Verified (by severity)
## Issues Dismissed (false positives with reasoning)
## Changes Applied

]]></mission>
<context>
<file id="b5c6fe32" path="_bmad-output/project-context.md" label="PROJECT CONTEXT"><![CDATA[

---
project_name: 'ReformLab'
user_name: 'Lucas'
date: '2026-02-27'
status: 'complete'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow_rules', 'critical_rules']
rule_count: 38
optimized_for_llm: true
---

# Project Context for AI Agents

_This file contains critical rules and patterns that AI agents must follow when implementing code in this project. Focus on unobvious details that agents might otherwise miss._

---

## Technology Stack & Versions

- **Python 3.13+** — `target-version = "py313"` (ruff), `python_version = "3.13"` (mypy strict)
- **uv** — package manager, **hatchling** — build backend
- **pyarrow >= 18.0.0** — canonical data type (`pa.Table`), CSV/Parquet I/O
- **pyyaml >= 6.0.2** — YAML template/config loading
- **jsonschema >= 4.23.0** — JSON Schema validation for templates
- **openfisca-core >= 44.0.0** — optional dependency (`[openfisca]` extra); never import outside adapter modules
- **pytest >= 8.3.3, ruff >= 0.15.0, mypy >= 1.19.0** — dev tooling
- **Planned frontend:** React 18+ / TypeScript / Vite / Shadcn/ui / Tailwind v4
- **Planned backend API:** FastAPI + uvicorn
- **Planned deployment:** Kamal 2 on Hetzner CX22

### Version Constraints

- mypy runs in **strict mode** with explicit `ignore_missing_imports` overrides for openfisca, pyarrow, jsonschema, yaml
- OpenFisca is optional — core library must function without it installed

## Critical Implementation Rules

### Python Language Rules

- **Every file starts with** `from __future__ import annotations` — no exceptions
- **Use `if TYPE_CHECKING:` guards** for imports that are only needed for annotations or would create circular dependencies; do the runtime import locally where needed
- **Frozen dataclasses are the default** — all domain types use `@dataclass(frozen=True)`; mutate via `dataclasses.replace()`, never by assignment
- **Protocols, not ABCs** — interfaces are `Protocol` + `@runtime_checkable`; no abstract base classes; structural (duck) typing only
- **Subsystem-specific exceptions** — each module defines its own error hierarchy; never raise bare `Exception` or `ValueError` for domain errors
- **Metadata bags** use `dict[str, Any]` with **stable string-constant keys** defined at module level (e.g., `STEP_EXECUTION_LOG_KEY`)
- **Union syntax** — use `X | None` not `Optional[X]`; use `dict[str, int]` not `Dict[str, int]` (modern generics, no `typing` aliases)
- **`tuple[...]` for immutable sequences** — function parameters and return types that are ordered-and-fixed use `tuple`, not `list`

### Architecture & Framework Rules

- **Adapter isolation is absolute** — only `computation/openfisca_adapter.py` and `openfisca_api_adapter.py` may import OpenFisca; all other code uses the `ComputationAdapter` protocol
- **Step pipeline contract** — steps implement `OrchestratorStep` protocol (`name` + `execute(year, state) -> YearState`); bare callables accepted via `adapt_callable()`; registration via `StepRegistry` with topological sort on `depends_on`
- **Template packs are YAML** — live in `src/reformlab/templates/packs/{policy_type}/`; validated against JSON Schemas in `templates/schema/`; each policy type has its own subpackage with `compute.py` + `compare.py`
- **Data flows through PyArrow** — `PopulationData` (dict of `pa.Table` by entity) → adapter → `ComputationResult` (`pa.Table`) → `YearState.data` → `PanelOutput` (stacked table) → indicators
- **`YearState` is the state token** — passed between steps and years; immutable (frozen dataclass); updated via `replace()`
- **Orchestrator is the core product** — never build custom policy engines, formula compilers, or entity graph engines; OpenFisca handles computation, this project handles orchestration

### Testing Rules

- **Mirror source structure** — `tests/{subsystem}/` matches `src/reformlab/{subsystem}/`; each has `__init__.py` and `conftest.py`
- **Class-based test grouping** — group tests by feature or acceptance criterion (e.g., `TestOrchestratorBasicExecution`); reference story/AC IDs in comments and docstrings
- **Fixtures in conftest.py** — subsystem-specific fixtures per `conftest.py`; build PyArrow tables inline, use `tmp_path` for I/O, golden YAML files in `tests/fixtures/`
- **Direct assertions** — use plain `assert`; no custom assertion helpers; use `pytest.raises(ExceptionClass, match=...)` for errors
- **Test helpers are explicit** — import shared callables from conftest directly (`from tests.orchestrator.conftest import ...`); no hidden magic
- **Golden file tests** — YAML fixtures in `tests/fixtures/templates/`; test load → validate → round-trip cycle
- **MockAdapter for unit tests** — never use real OpenFisca in orchestrator/template/indicator unit tests; `MockAdapter` is the standard test double

### Code Quality & Style Rules

- **ruff** enforces `E`, `F`, `I`, `W` rule sets; `src = ["src"]`; target Python 3.13
- **mypy strict** — all code must pass `mypy --strict`; new modules need `ignore_missing_imports` overrides in `pyproject.toml` only for third-party libs without stubs
- **File naming** — `snake_case.py` throughout; no PascalCase or kebab-case files
- **Class naming** — PascalCase for classes (`OrchestratorStep`, `CarbonTaxParameters`); no suffixes like `Impl` or `Base`
- **Module-level docstrings** — every module has a docstring explaining its role, referencing relevant story/FR
- **Section separators** — use `# ====...====` comment blocks to separate major sections within longer modules (see `step.py`)
- **No wildcard imports** — always import specific names; `from reformlab.orchestrator import Orchestrator, OrchestratorConfig`
- **Logging** — use `logging.getLogger(__name__)`; structured key=value format for parseable log lines (e.g., `year=%d seed=%s event=year_start`)

### Development Workflow Rules

- **Package manager is uv** — use `uv pip install`, `uv run pytest`, etc.; not `pip` directly
- **Test command** — `uv run pytest tests/` (or specific subsystem path)
- **Lint command** — `uv run ruff check src/ tests/` and `uv run mypy src/`
- **Source layout** — `src/reformlab/` is the installable package; `tests/` is separate; `pythonpath = ["src"]` in pytest config
- **Build system** — hatchling with `packages = ["src/reformlab"]`
- **No auto-formatting on save assumed** — agents must produce ruff-compliant code; run `ruff check --fix` if needed

### Critical Don't-Miss Rules

- **Never import OpenFisca outside adapter modules** — this is the single most important architectural boundary; violation couples the entire codebase to one backend
- **All domain types are frozen** — never add a mutable dataclass; if you need mutation, use `dataclasses.replace()` and return a new instance
- **Determinism is non-negotiable** — every run must be reproducible; seeds are explicit, logged in manifests, derived deterministically (`master_seed XOR year`)
- **Data contracts fail loudly** — contract validation at ingestion boundaries is field-level and blocking; never silently coerce or drop data
- **Assumption transparency** — every run produces a manifest (JSON); assumptions, versions, seeds, data hashes are all recorded
- **PyArrow is the canonical data type** — do not use pandas DataFrames in core logic; `pa.Table` is the standard; pandas only at display/export boundaries if needed
- **No custom formula compiler** — environmental policy logic is Python code in template `compute.py` modules, not YAML formula strings or DSLs
- **France/Europe first** — initial scenarios use French policy parameters (EUR, INSEE deciles, French carbon tax rates); European data sources (Eurostat, EU-SILC)

---

## Usage Guidelines

**For AI Agents:**

- Read this file before implementing any code
- Follow ALL rules exactly as documented
- When in doubt, prefer the more restrictive option
- Update this file if new patterns emerge

**For Humans:**

- Keep this file lean and focused on agent needs
- Update when technology stack changes
- Review quarterly for outdated rules
- Remove rules that become obvious over time

Last Updated: 2026-02-27


]]></file>
<file id="7243a2d9" path="_bmad-output/implementation-artifacts/11-3-implement-eurostat-ademe-sdes-data-source-loaders.md" label="STORY FILE"><![CDATA[


# Story 11.3: Implement Eurostat, ADEME, and SDES data source loaders

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a platform developer building the French household population pipeline,
I want concrete data source loaders for Eurostat (EU-SILC income distribution, household energy consumption), ADEME (Base Carbone emission factors), and SDES (vehicle fleet composition),
so that downstream merge methods (Stories 11.4–11.6) can consume real European and French public data as schema-validated `pa.Table` objects through the `DataSourceLoader` protocol.

## Acceptance Criteria

1. Given the Eurostat loader, when called with a valid dataset code, then EU-level household data is returned as a schema-validated `pa.Table`.
2. Given the ADEME loader, when called, then energy consumption and emission factor datasets are returned with documented schemas.
3. Given the SDES loader, when called, then vehicle fleet composition and age distribution data is returned.
4. Given all three loaders, when run, then each follows the `DataSourceLoader` protocol and integrates with the caching infrastructure from BKL-1101.
5. Given CI tests for all loaders, then they use fixture files and do not require network access.

## Tasks / Subtasks

- [ ] Task 1: Create Eurostat loader — `eurostat.py` (AC: #1, #4)
  - [ ] 1.1 Create `src/reformlab/population/loaders/eurostat.py` with module docstring referencing Story 11.3, FR36, FR37
  - [ ] 1.2 Define `EurostatDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `columns: tuple[tuple[str, str], ...] = ()` where each inner tuple is `(raw_sdmx_column_name, project_column_name)` — serves as both documentation and rename mapping
  - [ ] 1.3 Define `EUROSTAT_CATALOG` as module-level `dict[str, EurostatDataset]` with at minimum:
    - `"ilc_di01"` — Income distribution by quantile (EU-SILC deciles D1–D10, shares/EUR)
    - `"nrg_d_hhq"` — Disaggregated final energy consumption in households
  - [ ] 1.4 Define per-dataset `pa.Schema` objects for the output columns each dataset produces (after column selection and renaming)
  - [ ] 1.5 Add `EUROSTAT_AVAILABLE_DATASETS` module-level constant
  - [ ] 1.6 Implement `EurostatLoader(CachedLoader)` with `__init__(self, *, cache, logger, dataset)` — store dataset reference, call `super().__init__()`
  - [ ] 1.7 Implement `schema(self) -> pa.Schema` — return schema for this loader's dataset
  - [ ] 1.8 Implement `_fetch(self, config: SourceConfig) -> pa.Table` — download gzip-compressed SDMX-CSV via `urllib.request`, decompress with `gzip.decompress()`, parse with `pyarrow.csv.read_csv()`, select and rename columns, cast types, return `pa.Table`
  - [ ] 1.9 On any network error, re-raise as `OSError` for stale-cache fallback
  - [ ] 1.10 Add structured logging: `event=fetch_start`, `event=fetch_complete` with `provider=eurostat dataset_id=... rows=... columns=...`
  - [ ] 1.11 Implement `get_eurostat_loader(dataset_id, *, cache, logger=None)` factory function with catalog validation
  - [ ] 1.12 Implement `make_eurostat_config(dataset_id, **params)` helper function

- [ ] Task 2: Create ADEME loader — `ademe.py` (AC: #2, #4)
  - [ ] 2.1 Create `src/reformlab/population/loaders/ademe.py` with module docstring referencing Story 11.3, FR36, FR37
  - [ ] 2.2 Define `ADEMEDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `encoding: str = "windows-1252"`, `separator: str = ";"`, `null_markers: tuple[str, ...] = ("",)`, `columns: tuple[tuple[str, str], ...] = ()` — raw-to-project column rename mapping
  - [ ] 2.3 Define `ADEME_CATALOG` with at minimum:
    - `"base_carbone"` — Base Carbone V23.6 emission factors (CSV from data.gouv.fr)
  - [ ] 2.4 Define per-dataset `pa.Schema` for the output columns (subset of the 60+ raw columns, focused on emission factors relevant to carbon tax simulation)
  - [ ] 2.5 Add `ADEME_AVAILABLE_DATASETS` module-level constant
  - [ ] 2.6 Implement `ADEMELoader(CachedLoader)` with dataset-specific parsing — handle Windows-1252 encoding (primary), UTF-8 fallback, semicolon separator
  - [ ] 2.7 Implement `get_ademe_loader(dataset_id, *, cache, logger=None)` factory function
  - [ ] 2.8 Implement `make_ademe_config(dataset_id, **params)` helper function

- [ ] Task 3: Create SDES loader — `sdes.py` (AC: #3, #4)
  - [ ] 3.1 Create `src/reformlab/population/loaders/sdes.py` with module docstring referencing Story 11.3, FR36, FR37
  - [ ] 3.2 Define `SDESDataset` frozen dataclass with fields: `dataset_id: str`, `description: str`, `url: str`, `encoding: str = "utf-8"`, `separator: str = ";"`, `null_markers: tuple[str, ...] = ("",)`, `columns: tuple[tuple[str, str], ...] = ()`, `skip_rows: int = 0` — number of header rows to skip before the column name row (DiDo CSVs may have description rows)
  - [ ] 3.3 Define `SDES_CATALOG` with at minimum:
    - `"vehicle_fleet"` — Vehicle fleet composition by fuel type, age, Crit'Air, region (communal-level data from data.gouv.fr)
  - [ ] 3.4 Define per-dataset `pa.Schema` for the output columns (fleet counts by year, fuel type, region)
  - [ ] 3.5 Add `SDES_AVAILABLE_DATASETS` module-level constant
  - [ ] 3.6 Implement `SDESLoader(CachedLoader)` with DiDo CSV parsing — UTF-8 encoding, semicolon separator
  - [ ] 3.7 Implement `get_sdes_loader(dataset_id, *, cache, logger=None)` factory function
  - [ ] 3.8 Implement `make_sdes_config(dataset_id, **params)` helper function

- [ ] Task 4: Update `__init__.py` exports (AC: #4)
  - [ ] 4.1 Add all Eurostat exports to `src/reformlab/population/loaders/__init__.py`
  - [ ] 4.2 Add all ADEME exports to `src/reformlab/population/loaders/__init__.py`
  - [ ] 4.3 Add all SDES exports to `src/reformlab/population/loaders/__init__.py`
  - [ ] 4.4 Add the same exports to `src/reformlab/population/__init__.py`

- [ ] Task 5: Create test fixtures (AC: #5)
  - [ ] 5.1 Create `tests/fixtures/eurostat/` directory with small SDMX-CSV fixtures mimicking `ilc_di01` and `nrg_d_hhq` format (5–10 rows each, comma-separated, UTF-8)
  - [ ] 5.2 Create `tests/fixtures/ademe/` directory with small CSV fixture mimicking Base Carbone format (5–10 rows, semicolon-separated, Windows-1252 encoded)
  - [ ] 5.3 Create `tests/fixtures/sdes/` directory with small CSV fixture mimicking DiDo vehicle fleet format (5–10 rows, semicolon-separated, UTF-8)
  - [ ] 5.4 Add fixture helpers in `tests/population/loaders/conftest.py`: paths and byte-reading fixtures for each provider

- [ ] Task 6: Write comprehensive tests (AC: all)
  - [ ] 6.1 `tests/population/loaders/test_eurostat.py`:
    - `TestEurostatLoaderProtocol`: `isinstance()` check against `DataSourceLoader`
    - `TestEurostatLoaderSchema`: `schema()` returns valid `pa.Schema` for each dataset
    - `TestEurostatLoaderFetch`: monkeypatch `urllib.request.urlopen` to return gzip-compressed fixture; verify `_fetch()` returns correctly-parsed `pa.Table`
    - `TestEurostatLoaderFetchMissingValues`: verify `:` and empty cells produce nulls
    - `TestEurostatLoaderFetchHTTPError`: verify network errors re-raised as `OSError`
    - `TestEurostatLoaderDownloadIntegration`: full `download()` lifecycle via `CachedLoader`
    - `TestEurostatLoaderCatalog`: catalog completeness, factory function, invalid ID error
    - `TestMakeEurostatConfig`: config construction for each catalog entry
  - [ ] 6.2 `tests/population/loaders/test_ademe.py`:
    - `TestADEMELoaderProtocol`: protocol compliance
    - `TestADEMELoaderSchema`: schema correctness
    - `TestADEMELoaderFetch`: monkeypatch fetch with Windows-1252 fixture; verify parsing
    - `TestADEMELoaderFetchEncodingFallback`: UTF-8 fallback when primary encoding fails
    - `TestADEMELoaderFetchHTTPError`: network error handling
    - `TestADEMELoaderDownloadIntegration`: full download lifecycle
    - `TestADEMELoaderCatalog`: catalog and factory
    - `TestMakeAdemeConfig`: config construction
  - [ ] 6.3 `tests/population/loaders/test_sdes.py`:
    - `TestSDESLoaderProtocol`: protocol compliance
    - `TestSDESLoaderSchema`: schema correctness
    - `TestSDESLoaderFetch`: monkeypatch fetch with fixture; verify parsing
    - `TestSDESLoaderFetchHTTPError`: network error handling
    - `TestSDESLoaderDownloadIntegration`: full download lifecycle
    - `TestSDESLoaderCatalog`: catalog and factory
    - `TestMakeSDESConfig`: config construction

- [ ] Task 7: Network integration tests (AC: #5)
  - [ ] 7.1 `tests/population/loaders/test_eurostat_network.py` — `@pytest.mark.network` real download of `ilc_di01` (small dataset)
  - [ ] 7.2 `tests/population/loaders/test_ademe_network.py` — `@pytest.mark.network` real download of Base Carbone CSV
  - [ ] 7.3 `tests/population/loaders/test_sdes_network.py` — `@pytest.mark.network` real download of vehicle fleet data

- [ ] Task 8: Run full test suite and lint (AC: all)
  - [ ] 8.1 `uv run pytest tests/population/` — all tests pass
  - [ ] 8.2 `uv run ruff check src/reformlab/population/ tests/population/` — no lint errors
  - [ ] 8.3 `uv run mypy src/reformlab/population/` — no mypy errors (strict mode)

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
    csv_bytes = gzip.decompress(raw_bytes)

    # 3. Parse with pyarrow.csv
    raw_names = [col[0] for col in self._dataset.columns]
    project_names = [col[1] for col in self._dataset.columns]
    schema = self.schema()

    column_types: dict[str, pa.DataType] = {}
    for raw_name, proj_name in self._dataset.columns:
        column_types[raw_name] = schema.field(proj_name).type

    convert_options = pcsv.ConvertOptions(
        null_values=["", ":"],
        column_types=column_types,
        include_columns=raw_names,
    )
    parse_options = pcsv.ParseOptions(delimiter=",")
    read_options = pcsv.ReadOptions(encoding="utf-8")

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

**Note on column names:** The exact raw column names in the CSV must be verified against the fixture file. ADEME may use slightly different names across versions. The fixture should use the real column names from a recent download (V23.6). If the dev agent runs the network integration test and finds column name differences, update the mapping accordingly.

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

**IMPORTANT:** The exact raw column names may vary. Before finalizing the column mapping, run the network integration test to download a real Base Carbone file and check the actual headers. If column names differ from the above, adjust the `_BASE_CARBONE_COLUMNS` mapping. The fixture must use the same column names as the real file.

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

**The fixture MUST be saved as Windows-1252 encoding**, not UTF-8. Use Python to create it:
```python
content.encode("windows-1252")
```

Or use the `Write` tool with careful byte handling. Alternatively, if the fixture uses only ASCII-compatible characters, both encodings produce the same bytes — include at least one non-ASCII French character to test encoding.

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

**Recommendation:** Use the data.gouv.fr URL for simplicity (single GET, no query params needed). It returns the same CSV data.

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

**IMPORTANT:** Column names must be verified against the actual data. Run the network integration test first to confirm exact column names. SDES may use different names than documented. If column names differ, update the mapping in the catalog.

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

1. **Test helpers** at top of file: `_make_gzip()` (for Eurostat), `_mock_urlopen()` (reuse from INSEE pattern)
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

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2026-03-03: Story created by create-story workflow — comprehensive developer context with Eurostat SDMX-CSV parsing, ADEME Windows-1252 handling, SDES DiDo CSV format, test fixture designs, and verified download URLs.


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-3-implement-eurostat-ademe-sdes-data-source-loaders - implement-eurostat-ademe-sdes-data-source-loaders
**Story File:** _bmad-output/implementation-artifacts/11-3-implement-eurostat-ademe-sdes-data-source-loaders.md
**Validated:** 2026-03-03
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 2 | 0 |
| ⚡ Enhancements | 3 | 0 |
| ✨ Optimizations | 2 | 0 |
| 🤖 LLM Optimizations | 2 | 0 |

**Overall Assessment:** MAJOR REWORK

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | Offline-first/stale-cache behaviors not enforced in ACs; risks violating architecture’s cardinal rule | Acceptance Criteria & Tasks | +3 |
| 🔴 CRITICAL | No schema/column-name validation requirements; risk of ingesting wrong data shapes across three providers | Acceptance Criteria | +3 |
| 🟠 IMPORTANT | Story scope bundles three heterogeneous loaders plus fixtures/tests → likely too large for one sprint | INVEST (Small) | +1 |
| 🟠 IMPORTANT | Hidden dependency on live dataset column drift and resource URLs; no mitigation or fallback guidance | Hidden Dependencies | +1 |
| 🟠 IMPORTANT | Error handling gaps (gzip/encoding/CSV anomalies) not specified; could bypass validation or crash | Technical Spec | +1 |
| 🟢 CLEAN PASS | 1 clean category |  | -0.5 |

### Evidence Score: 6.5

| Score | Verdict |
|-------|---------|
| **6.5** | **MAJOR REWORK** |

---

## 🎯 Ruthless Story Validation 11.3

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | Weak | 2/10 | Depends on Story 11.1/11.2 cache/protocol plus live dataset availability; mostly acceptable but tied to prior work. |
| **N**egotiable | Poor | 6/10 | Highly prescriptive “how” steps (exact logging strings, decompression steps) reduce design flexibility. |
| **V**aluable | Good | 0/10 | Clear value: delivers three institutional loaders for population pipeline. |
| **E**stimable | Fair | 4/10 | Ambiguity in schemas/column names and live-data drift make effort estimation shaky. |
| **S**mall | Poor | 6/10 | Three loaders + fixtures + network tests in one story is large for a sprint; should split by provider. |
| **T**estable | Fair | 4/10 | ACs are high-level; lack concrete schemas, offline/stale cases, and error paths → partial testability. |

### INVEST Violations

- **[6/10] Negotiable:** Overly prescriptive tasks constrain implementation choices without focusing on outcomes.
- **[6/10] Small:** Scope bundles three sizable loaders; likely exceeds single-story size.
- **[4/10] Estimable:** Live data variability and absent schema specs impede reliable estimation.
- **[4/10] Testable:** Acceptance criteria omit measurable schema/offline/error behaviors.

### Acceptance Criteria Issues

- **Ambiguity:** “EU-level household data is returned” lacks explicit schemas or required columns; cannot be objectively verified.
  - *Quote:* "EU-level household data is returned as a schema-validated pa.Table."
  - *Recommendation:* Enumerate required columns, types, null handling per dataset.
- **Missing offline/stale behavior:** No AC ensures REFORMLAB_OFFLINE handling or stale-cache fallback mandated by architecture.
  - *Quote:* None
  - *Recommendation:* Add ACs covering offline mode cache hit/miss and network-failure stale fallback.
- **Error-path coverage missing:** Gzip/encoding/CSV anomalies and multi-CSV-in-zip scenarios not in ACs.
  - *Quote:* None
  - *Recommendation:* Add ACs for malformed archives, bad encoding, HTTP errors re-raised as OSError.
- **Catalog validity untested:** ACs don’t require catalog completeness or unknown-ID error messaging.
  - *Quote:* None
  - *Recommendation:* Add AC for invalid dataset IDs returning actionable error with suggestions.

### Hidden Risks and Dependencies

- **External data drift:** Column names/resource IDs for Eurostat/ADEME/SDES may change; story lacks strategy (pin versions, schema checks, fixtures update).  
  - *Impact:* Sudden breakage or silent wrong data.  
  - *Mitigation:* Require schema validation against fixtures plus fail-fast on mismatches; document version pins.
- **Offline-first governance:** Story omits explicit dependency on REFORMLAB_OFFLINE and stale-cache policy.  
  - *Impact:* Violates architecture; tests may hit real network unexpectedly.  
  - *Mitigation:* Add ACs and tests mirroring Story 11.1 offline semantics for all loaders.
- **Encoding/tooling dependency:** ADEME Windows-1252 assumption; missing fallback plans if dataset switches encoding.  
  - *Impact:* Crashes or garbled text.  
  - *Mitigation:* Mandate dual-encoding attempt and log fallback.

### Estimation Reality-Check

**Assessment:** Underestimated

Three heterogeneous loaders, catalog design, fixtures, and multiple network tests exceed a typical single-story effort; column drift and encoding quirks add uncertainty.

### Technical Alignment

**Status:** Partially aligned

- Missing explicit requirement to honor offline-first/stale-cache contract from architecture.md.
- No mandate to keep PyArrow as sole parsing backend and avoid pandas (a critical rule).
- Column/schema validation not specified, risking contract breach with downstream population pipeline.

---

## 🚨 Critical Issues (Must Fix)

### 1. Offline-first/stale-cache behaviors absent from ACs
**Impact:** Violates architecture’s top rule; loaders may attempt network in offline mode or skip stale-cache fallback.  
**Source:** Acceptance Criteria and Tasks omit offline/stale requirements.  
**Recommended Fix:** Add ACs covering REFORMLAB_OFFLINE cache miss failure, cache-hit offline success, and stale-cache fallback on network OSError for each loader.

### 2. Schemas/column-name validation not specified
**Impact:** Loader may return wrong shapes; downstream merges fail silently.  
**Source:** ACs state “schema-validated” without listing fields/types per dataset.  
**Recommended Fix:** Define per-dataset required columns and types in ACs; require validation failure on mismatch.

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Catalog integrity and unknown-ID errors
**Benefit:** Prevents silent misuse and aids discovery.  
**Current Gap:** ACs don’t require catalog listing or clear error message on invalid IDs.  
**Suggested Addition:** Add AC: unknown dataset IDs raise DataSourceValidationError listing available IDs.

### 2. Error-path test coverage
**Benefit:** Ensures robustness to real-world data anomalies.  
**Current Gap:** No ACs for gzip corruption, multi-CSV ZIPs, encoding failures, HTTP errors.  
**Suggested Addition:** Add ACs requiring these scenarios to raise DataSourceValidationError or OSError as appropriate.

### 3. Version pinning / drift detection
**Benefit:** Guards against upstream schema drift.  
**Current Gap:** No requirement to record dataset version/hash or fail on header changes.  
**Suggested Addition:** Mandate header/hash capture in metadata and fail-fast when headers change vs fixtures.

---

## ✨ Optimizations (Nice to Have)

### 1. Limit column selection for SDES to minimal years
**Value:** Reduces memory/IO for large fleet CSVs.  
**Suggestion:** Specify only latest year columns in schema, optional flag for multi-year expansion.

### 2. Streaming or chunked parsing guidance
**Value:** Prevents memory spikes on ADEME/Base Carbone (~10MB) and SDES (~10MB).  
**Suggestion:** Recommend pyarrow CSV chunking or document acceptable memory budget.

---

## 🤖 LLM Optimization Improvements

### 1. Collapse repetitive task lists
**Issue:** Verbose task bullets repeat patterns from INSEE story.  
**Token Impact:** Medium  
**Current:**
```
- [ ] 1.1 ... 
- [ ] 1.2 ...
...
```
**Optimized:**
```
Tasks: implement eurostat/ademe/sdes loaders using CachedLoader; add catalogs, schemas, factory+config helpers, fixtures, unit + @network tests; export symbols in __init__.py.
```
**Rationale:** Keeps essential steps while cutting boilerplate.

### 2. Surface critical constraints early
**Issue:** Offline-first and schema validation requirements buried/implicit.  
**Token Impact:** Low  
**Current:**
```
Story text notes caching integration but no explicit offline/stale rules in ACs.
```
**Optimized:**
```
Constraints (must): honor REFORMLAB_OFFLINE + stale-cache fallback; PyArrow-only parsing; schemas fixed per dataset; no new deps.
```
**Rationale:** Front-loads non-negotiables for the dev agent.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 65% |
| Architecture Alignment | 70% |
| Previous Story Integration | 60% |
| LLM Optimization Score | 60% |
| **Overall Quality Score** | **64%** |

### Disaster Prevention Assessment

- **Offline Compliance:** Needs fixes – offline/stale behavior unspecified.
- **Schema Contracts:** Needs fixes – no explicit schemas in ACs.
- **Error Handling:** Needs fixes – gzip/encoding/HTTP anomalies not covered.
- **Scope Size:** Risk – three loaders in one story.

### Competition Outcome

🏆 **Validator identified multiple gaps requiring updates before development.**

---

**Report Generated:** 2026-03-03  
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-3-implement-eurostat-ademe-sdes-data-source-loaders
**Story File:** `_bmad-output/implementation-artifacts/11-3-implement-eurostat-ademe-sdes-data-source-loaders.md`
**Validated:** 2026-03-03
**Validator:** Quality Competition Engine

---

## Executive Summary

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 1 | 0 |
| ⚡ Enhancements | 5 | 0 |
| ✨ Optimizations | 3 | 0 |
| 🤖 LLM Optimizations | 2 | 0 |

**Overall Assessment:** Story is well-structured and provides excellent developer context, but contains one real bug trap (`gzip.BadGzipFile` inherits from `OSError` — causes wrong stale-cache fallback) and several moderate gaps that could lead to implementation mistakes or silent test failures.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | `gzip.BadGzipFile` is a subclass of `OSError` — not caught as `DataSourceValidationError`, triggers stale-cache fallback on corrupt gzip data | Error Handling Notes section | +3 |
| 🟠 IMPORTANT | Windows-1252 fixture creation is ambiguous — LLM Write tool outputs UTF-8; no programmatic recipe given for binary-encoding a fixture file | ADEME Fixture Design section | +1 |
| 🟠 IMPORTANT | `AVAILABLE_DATASETS` naming asymmetry — INSEE exports unprefixed `AVAILABLE_DATASETS`, new loaders export `EUROSTAT_AVAILABLE_DATASETS` etc.; `__init__.py` strategy not specified | Task 4 / `__init__.py` exports | +1 |
| 🟡 MINOR | `EurostatDataset` dataclass missing structured `encoding`, `separator`, `null_markers` fields — encoding/null logic hard-coded in `_fetch()`, inconsistent with `INSEEDataset`/`ADEMEDataset` pattern | Task 1.2 | +0.3 |
| 🟡 MINOR | No test case for `SDESDataset.skip_rows` behavior — field defined in dataclass (Task 3.2) but absent from test plan (Task 6.3) | Tasks 3.2, 6.3 | +0.3 |
| 🟡 MINOR | Gzip-wrapping test helper not shown — story says "test wraps [fixture] in gzip at runtime" but provides no helper function example; compare to `_make_zip()` shown in the INSEELoader dev notes | Eurostat Fixture Design | +0.3 |
| 🟡 MINOR | Column name uncertainty disclaimer repeated three times (ADEME section, SDES section, "Column Name Verification Strategy" section) | Dev Notes | +0.3 |
| 🟡 MINOR | Story packages 3 structurally distinct loaders into a single 5 SP estimate — formats differ (gzip SDMX-CSV, Windows-1252 CSV, DiDo CSV), complexity likely underestimated | Estimation | +0.3 |
| 🟢 CLEAN PASS | INVEST — Independent (Stories 11.1 and 11.2 are done) | — | -0.5 |
| 🟢 CLEAN PASS | INVEST — Valuable (clear product need, feeds Stories 11.4–11.6) | — | -0.5 |
| 🟢 CLEAN PASS | Architecture alignment (file paths, protocol pattern, CachedLoader contract) | — | -0.5 |

### Evidence Score: **2.7**

| Score | Verdict |
|-------|---------|
| **2.7** | **PASS** |

---

## 🎯 Ruthless Story Validation 11.3

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ✅ Pass | 0/10 | Depends on Stories 11.1 and 11.2, both status: complete. No blockers. |
| **N**egotiable | ⚠️ Marginal | 3/10 | Very prescriptive about column mappings and exact URL strings, which is justified given the volatile nature of external data sources. Acceptable for this story type. |
| **V**aluable | ✅ Pass | 0/10 | Directly enables Stories 11.4–11.6 (merge methods). Clear downstream dependency. |
| **E**stimable | ⚠️ Marginal | 4/10 | Three structurally distinct loaders with different encoding/format challenges; 5 SP estimate likely 20–30% low. |
| **S**mall | ⚠️ Marginal | 5/10 | Three loaders × (implementation + unit tests + network tests + fixtures) is at the upper boundary of a single story. Could split into Eurostat vs. ADEME+SDES. Not a blocking issue. |
| **T**estable | ✅ Pass | 2/10 | ACs are clear and testable, but AC#2 (ADEME) doesn't specifically require Windows-1252 encoding to be verified. |

### INVEST Violations

- **[4/10] Estimable:** Three loaders with distinct formats (gzip SDMX-CSV, Windows-1252 CSV, DiDo CSV) is more work than the 5 SP estimate suggests. Risk of rushing SDES or ADEME implementation.
- **[5/10] Small:** Story is at the upper bound of reasonable sprint scope. Consider flagging to product owner for optional split if velocity is tight.

### Acceptance Criteria Issues

- **Missing scenario — Gzip decompression error:** No AC covers "Given a Eurostat download that returns corrupted gzip data, when the loader is called, then `DataSourceValidationError` is raised (not a stale-cache fallback)." This is a real failure mode that the story's error handling notes address verbally but don't codify as testable behavior.
  - *Quote:* "For Eurostat gzip decompression errors → raise `DataSourceValidationError` (not `OSError`, since the download succeeded but the content is invalid)"
  - *Recommendation:* Add AC: "Given Eurostat gzip content that is corrupt, when the loader is called, then `DataSourceValidationError` is raised."

- **Missing scenario — ADEME Windows-1252 encoding:** AC#2 only requires "datasets are returned with documented schemas." It does not require that Windows-1252 encoding is correctly handled and tested.
  - *Quote:* "Given the ADEME loader, when called, then energy consumption and emission factor datasets are returned with documented schemas."
  - *Recommendation:* Add: "...and given an ADEME fixture with non-ASCII French characters encoded in Windows-1252, then the loader correctly decodes them."

- **Ambiguous AC#3 (SDES) — "age distribution":** AC#3 mentions "vehicle fleet composition and age distribution data" but the catalog and column mapping only have one dataset (`vehicle_fleet`) with an `AGE` field. No separate age-distribution dataset is defined.
  - *Quote:* "Given the SDES loader, when called, then vehicle fleet composition and age distribution data is returned."
  - *Recommendation:* Clarify: age distribution is included as a field within `vehicle_fleet`, not a separate dataset.

### Hidden Risks and Dependencies

- **ADEME Base Carbone column instability:** The story acknowledges raw column names "may vary across data vintages." The V23.6 column names are documented but ADEME releases new versions periodically. If the network integration test is not run early, the fixture-based unit tests will pass but the real loader will fail on first production use.
  - *Impact:* Silent integration failure discovered only at population pipeline stage.
  - *Mitigation:* Story correctly flags "run network integration test early in development." Could strengthen by specifying this as a mandatory step before PR merge.

- **data.gouv.fr resource ID stability (SDES):** Story notes the resource ID in the URL "may change when new data vintages are published." This is a real ops risk.
  - *Impact:* Loader silently breaks after a new vintage is published on data.gouv.fr.
  - *Mitigation:* Story lacks a recommendation to document the vintage date alongside the URL constant, or to use a dataset-level stable URL instead of a resource-level URL.

### Estimation Reality-Check

**Assessment:** Underestimated (moderate)

Three loaders with structurally different challenges: Eurostat requires gzip decompression + SDMX format understanding; ADEME requires Windows-1252 encoding handling and a binary fixture file; SDES requires column verification against live data before implementation. Add 3 unit test files, 3 network test files, 4 fixture files (Eurostat × 2, ADEME × 1, SDES × 1). Each loader also needs factory functions and config helpers. Realistic range: 6–8 SP. The 5 SP estimate (from epics.md) is likely 20–30% low.

### Technical Alignment

**Status:** ✅ Aligned with minor gaps

- File paths (`eurostat.py`, `ademe.py`, `sdes.py`) match the architecture diagram exactly.
- Protocol satisfaction via `CachedLoader` subclassing matches the architecture's DataSourceLoader pattern.
- Cache path structure `~/.reformlab/cache/sources/{provider}/{dataset_id}/` correctly specified.
- `from __future__ import annotations` requirement — story does not explicitly remind dev to include it in all new files. (The existing stories do include this, but new files risk omission given the amount of code being written.)

---

## 🚨 Critical Issues (Must Fix)

### 1. `gzip.BadGzipFile` inherits from `OSError` — triggers wrong stale-cache fallback

**Impact:** Corrupted Eurostat gzip download triggers stale-cache fallback instead of raising `DataSourceValidationError`. Silent incorrect behavior: analyst uses old stale data thinking a new download succeeded.

**Source:** "Error Handling Notes" section of the story; Python stdlib `gzip` module behavior.

**Problem:**
The story correctly states: "For Eurostat gzip decompression errors → raise `DataSourceValidationError` (not `OSError`, since the download succeeded but the content is invalid)." However, it does not show the code to do this. In Python 3.8+, `gzip.BadGzipFile` is a subclass of `OSError`:

```python
# Python stdlib: gzip.BadGzipFile inherits OSError
class BadGzipFile(OSError):
    ...
```

If the developer writes:
```python
csv_bytes = gzip.decompress(raw_bytes)  # raises gzip.BadGzipFile on bad data
```

...and does NOT wrap this in a try/except, then `gzip.BadGzipFile` propagates out of `_fetch()` as an `OSError`. `CachedLoader.download()` at line 230 catches `OSError` and triggers stale-cache fallback. The result: a bad gzip download returns stale cached data with no error. This is wrong.

**Recommended Fix:**
Add explicit exception handling in `EurostatLoader._fetch()` for gzip decompression:

```python
import gzip

try:
    csv_bytes = gzip.decompress(raw_bytes)
except (OSError, gzip.BadGzipFile) as exc:
    raise DataSourceValidationError(
        summary="Gzip decompression failed",
        reason=f"Downloaded content for eurostat/{self._dataset.dataset_id} "
               f"is not valid gzip: {exc}",
        fix="Check the Eurostat API URL and compressed=true parameter",
    ) from exc
```

Add a corresponding test in `TestEurostatLoaderFetch`: monkeypatch `_fetch` to call `gzip.decompress(b"not-gzip")` and verify `DataSourceValidationError` is raised (not stale-cache fallback triggered).

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Windows-1252 fixture creation strategy — no binary-safe recipe given

**Benefit:** Prevents agent from creating a UTF-8 fixture that silently doesn't test Windows-1252 encoding.

**Source:** "ADEME Fixture Design" section.

**Current Gap:**
The story says "The fixture MUST be saved as Windows-1252 encoding" and "include at least one non-ASCII French character." But LLM agents use the `Write` tool which produces UTF-8 text files. A Python string literal like `"é"` in a Write tool call produces a UTF-8 byte sequence (`\xc3\xa9`), not the Windows-1252 byte (`\xe9`). If the fixture is UTF-8, the `ADEMELoader` encoding test will silently test UTF-8 as the fallback, not as the primary path.

**Suggested Addition:**

Add to the ADEME Dev Notes:

```
### Creating the Windows-1252 Fixture

The ADEME fixture MUST be generated programmatically in a test helper, NOT
written as a plain text file. Add to `tests/population/loaders/conftest.py`:

```python
@pytest.fixture()
def ademe_base_carbone_csv_bytes() -> bytes:
    """Windows-1252 encoded ADEME Base Carbone CSV fixture."""
    content = (
        "Identifiant de l'élément;Nom base français;...other headers...\r\n"
        "1234;Gaz naturel;...\r\n"
        "5678;Fioul domestique;...\r\n"
    )
    return content.encode("windows-1252")
```

The fixture in `tests/fixtures/ademe/base_carbone.csv` can be created by
writing these bytes to disk once (e.g., via a setup script or inline in
`conftest.py`). Tests that monkeypatch `_fetch` should return these bytes
directly, bypassing file I/O.
```

### 2. `AVAILABLE_DATASETS` naming asymmetry in `__init__.py`

**Benefit:** Prevents a confusing public API where INSEE datasets are discoverable via `AVAILABLE_DATASETS` but other loaders require provider-prefixed names.

**Source:** Task 4 and `src/reformlab/population/loaders/__init__.py` (existing code).

**Current Gap:**
Currently `__init__.py` exports `AVAILABLE_DATASETS` (unprefixed, from INSEE). The story adds `EUROSTAT_AVAILABLE_DATASETS`, `ADEME_AVAILABLE_DATASETS`, `SDES_AVAILABLE_DATASETS`. This is asymmetric. Downstream code (e.g., the GUI Workbench in EPIC-17) that wants to list ALL available datasets must know about four different constant names.

**Suggested Addition:**

Task 4 should include one of two options (story author should choose):
- **Option A:** Rename `AVAILABLE_DATASETS` → `INSEE_AVAILABLE_DATASETS` in `__init__.py` and add all four provider-prefixed constants consistently. (Breaking change to any code already using `AVAILABLE_DATASETS` — check Story 11.2 tests.)
- **Option B:** Keep `AVAILABLE_DATASETS` as INSEE-only, and add a module-level `ALL_AVAILABLE_DATASETS: dict[str, tuple[str, ...]]` that maps provider names to their datasets, enabling unified discovery.

Story should specify which option to implement.

### 3. `EurostatDataset` missing structured encoding/separator fields

**Benefit:** Consistency with `INSEEDataset`, `ADEMEDataset`, `SDESDataset` — all other dataset types carry encoding/separator/null_markers on the dataclass.

**Source:** Task 1.2 `EurostatDataset` definition.

**Current Gap:**
`EurostatDataset` only has `dataset_id`, `description`, `url`, `columns`. The encoding (`"utf-8"`), separator (`","`) and null markers (`["", ":"]`) are hard-coded in `EurostatLoader._fetch()`. This breaks the pattern where the dataclass is the single source of truth for parsing configuration. Future Eurostat datasets with different separators or null markers would require changing `_fetch()` rather than the catalog.

**Suggested Addition:**

```python
@dataclass(frozen=True)
class EurostatDataset:
    dataset_id: str
    description: str
    url: str
    encoding: str = "utf-8"
    separator: str = ","
    null_markers: tuple[str, ...] = ("", ":")
    columns: tuple[tuple[str, str], ...] = ()
```

And `EurostatLoader._fetch()` reads from `self._dataset.encoding`, `self._dataset.separator`, `self._dataset.null_markers` — same as `INSEELoader._parse_csv()`.

### 4. Gzip test-wrapping helper not shown

**Benefit:** Dev agent will know exactly how to wrap Eurostat fixture in gzip for unit tests, same way `_make_zip()` was shown for INSEE tests.

**Source:** "Eurostat Fixture Design" section.

**Current Gap:**
The story says "the test wraps it in gzip at runtime" but shows no helper function. Compare to `_make_zip()` in Story 11.2 dev notes and test_insee.py. Without an example, the dev may write `gzip.open()` (file-based) instead of `gzip.compress()` (bytes-based).

**Suggested Addition:**

Add to Eurostat test helper examples:

```python
def _make_gzip(csv_bytes: bytes) -> bytes:
    """Create gzip-compressed bytes from CSV content."""
    return gzip.compress(csv_bytes)
```

And in the fetch test:
```python
def test_fetch_sdmx_csv(self, source_cache, ...):
    fixture = Path("tests/fixtures/eurostat/ilc_di01.csv").read_bytes()
    gzip_bytes = _make_gzip(fixture)
    with patch("urllib.request.urlopen", return_value=_mock_urlopen(gzip_bytes)):
        table = loader._fetch(config)
    assert table.num_rows == 5
```

### 5. `SDESDataset.skip_rows` — no test coverage

**Benefit:** Prevents a defined feature from being silently broken or ignored.

**Source:** Tasks 3.2 and 6.3.

**Current Gap:**
Task 3.2 defines `skip_rows: int = 0` (for DiDo CSV description rows), but no test in Task 6.3 exercises `skip_rows > 0`. The field could be defined but never wired into `pyarrow.csv.ReadOptions(skip_rows=...)`. A future DiDo dataset with description rows would silently fail.

**Suggested Addition:**

Add to `TestSDESLoaderFetch`:
- `test_fetch_with_skip_rows`: Create a fixture with N leading non-header description rows, set `skip_rows=N` in the dataset, verify parsing still succeeds and correct column headers are found.

Also add to Task 3.6 implementation: "Wire `SDESDataset.skip_rows` into `ReadOptions(skip_rows=self._dataset.skip_rows)`."

---

## ✨ Optimizations (Nice to Have)

### 1. Column verification caveat is repeated three times

**Value:** Reduces token waste and confusion (reader wonders if each repeat is different guidance).

**Suggestion:**
The caveat "The exact raw column names may vary. Run the network integration test first." appears in: (a) ADEME column mapping notes, (b) SDES column notes, and (c) "Column Name Verification Strategy" section. Consolidate into the "Column Name Verification Strategy" section and reference it from ADEME/SDES sections with a one-liner.

### 2. Two SDES download URLs without clear winner

**Value:** Prevents indecision and inconsistent implementation.

**Suggestion:**
The story gives two SDES URLs and says "Recommendation: Use the data.gouv.fr URL for simplicity" — but then shows the DiDo API URL format for the catalog. Make the recommendation unambiguous: specify exactly which URL goes into `SDES_CATALOG["vehicle_fleet"].url` and mark the alternative as "informational only."

### 3. `from __future__ import annotations` reminder missing from new-file list

**Value:** Prevents a ruff error on the first run.

**Suggestion:**
The project rules say "Every file starts with `from __future__ import annotations` — no exceptions." The story's "Project Structure Notes" lists the new files but doesn't include this reminder. Add it explicitly to each new file requirement or add a single reminder in the "Architecture Context" section.

---

## 🤖 LLM Optimization Improvements

### 1. Network error handling pattern duplicated

**Issue:** Redundancy
**Token Impact:** ~80 tokens wasted

**Current:**
The "Network Error Handling Pattern (from INSEE)" section and "Error Handling Notes" section both describe the same `_NETWORK_ERRORS` tuple and `_HTTP_TIMEOUT_SECONDS` pattern. Then each per-loader spec section also mentions it.

**Optimized:**
Keep "Network Error Handling Pattern" once, prefix with "APPLIES TO ALL THREE LOADERS", remove per-loader repetitions. Reduces ~80 tokens, increases scanability.

### 2. SDMX-CSV column structure examples include `DATAFLOW` and `LAST UPDATE` columns with a "DROP" instruction scattered in prose

**Issue:** Ambiguity — instruction is in prose, not in the column mapping tuple
**Token Impact:** Minor, but clarity impact is high

**Current:**
"Metadata columns to DROP: `DATAFLOW`, `LAST UPDATE` (not useful for analysis)" — this is mentioned in prose but not reflected in the `EurostatDataset.columns` tuple. A dev agent building `include_columns` from the column mapping will correctly exclude these since they're not in the mapping, but might not understand WHY.

**Optimized:**
Add a comment directly in the `_ILC_DI01_COLUMNS` constant definition: `# Excluded (metadata, not for analysis): DATAFLOW, LAST UPDATE, freq`. This collocates the intent with the code.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 88% |
| Architecture Alignment | 96% |
| Previous Story Integration | 92% |
| LLM Optimization Score | 72% |
| **Overall Quality Score** | **87%** |

### Disaster Prevention Assessment

- **Reinvention:** ✅ No wheel reinvention — correctly extends `CachedLoader`; pyarrow.csv used throughout
- **Wrong Libraries:** ✅ No new dependencies; stdlib + pyarrow only
- **File Structure:** ✅ File paths match architecture spec exactly
- **Regressions:** ⚠️ `AVAILABLE_DATASETS` naming ambiguity could break existing Story 11.2 tests if renamed
- **Silent Bugs:** ⚠️ `gzip.BadGzipFile`/`OSError` inheritance is a genuine silent failure mode; Windows-1252 fixture encoding is a silent test correctness risk

### Competition Outcome

🏆 **Validator identified 11 improvements** (1 critical, 5 enhancements, 3 optimizations, 2 LLM) that prevent real implementation bugs and improve developer clarity.

---

**Report Generated:** 2026-03-03
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
</context>
<variables>
<var name="author">BMad</var>
<var name="communication_language">English</var>
<var name="date">2026-03-03</var>
<var name="description">Master synthesizes validator findings and applies changes to story file</var>
<var name="document_output_language">English</var>
<var name="epic_num">11</var>
<var name="implementation_artifacts">_bmad-output/implementation-artifacts</var>
<var name="installed_path">_bmad/bmm/workflows/4-implementation/validate-story-synthesis</var>
<var name="instructions">/Users/lucas/Workspace/bmad-assist/src/bmad_assist/workflows/validate-story-synthesis/instructions.xml</var>
<var name="name">validate-story-synthesis</var>
<var name="output_folder">_bmad-output</var>
<var name="planning_artifacts">_bmad-output/planning-artifacts</var>
<var name="project_context" file_id="b5c6fe32" load_strategy="EMBEDDED" token_approx="2024">embedded in prompt, file id: b5c6fe32</var>
<var name="project_knowledge">docs</var>
<var name="project_name">ReformLab</var>
<var name="session_id">d932e8bf-b871-40d8-a4dd-5c9d83b2b691</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="7243a2d9">embedded in prompt, file id: 7243a2d9</var>
<var name="story_id">11.3</var>
<var name="story_key">11-3-implement-eurostat-ademe-sdes-data-source-loaders</var>
<var name="story_num">3</var>
<var name="story_title">implement-eurostat-ademe-sdes-data-source-loaders</var>
<var name="template">False</var>
<var name="timestamp">20260303_1440</var>
<var name="user_name">Lucas</var>
<var name="user_skill_level">expert</var>
<var name="validator_count">2</var>
</variables>
<instructions><workflow>
  <critical>Communicate all responses in English and generate all documents in English</critical>

  <critical>You are the MASTER SYNTHESIS agent. Your role is to evaluate validator findings
    and produce a definitive synthesis with applied fixes.</critical>
  <critical>You have WRITE PERMISSION to modify the story file being validated.</critical>
  <critical>All context (project_context.md, story file, anonymized validations) is EMBEDDED below - do NOT attempt to read files.</critical>
  <critical>Apply changes to story file directly using atomic write pattern (temp file + rename).</critical>

  <step n="1" goal="Analyze validator findings">
    <action>Read all anonymized validator outputs (Validator A, B, C, D, etc.)</action>
    <action>For each issue raised:
      - Cross-reference with story content and project_context.md
      - Determine if issue is valid or false positive
      - Note validator consensus (if 3+ validators agree, high confidence issue)
    </action>
    <action>Issues with low validator agreement (1-2 validators) require extra scrutiny</action>
  </step>

  <step n="1.5" goal="Review Deep Verify technical findings" conditional="[Deep Verify Findings] section present">
    <critical>Deep Verify provides automated technical analysis that complements validator reviews.
      DV findings focus on: patterns, boundary cases, assumptions, temporal issues, security, and worst-case scenarios.</critical>

    <action>Review each DV finding:
      - CRITICAL findings: Must be addressed - these indicate serious technical issues
      - ERROR findings: Should be addressed unless clearly false positive
      - WARNING findings: Consider addressing, document if dismissed
    </action>

    <action>Cross-reference DV findings with validator findings:
      - If validators AND DV flag same issue: High confidence, prioritize fix
      - If only DV flags issue: Verify technically valid, may be edge case validators missed
      - If only validators flag issue: Normal processing per step 1
    </action>

    <action>For each DV finding, determine:
      - Is this a genuine issue in the story specification?
      - Does the story need to address this edge case/scenario?
      - Is this already covered but DV missed it? (false positive)
    </action>

    <action>DV findings with patterns (CC-*, SEC-*, DB-*, DT-*, GEN-*) reference known antipatterns.
      Treat pattern-matched findings as higher confidence.</action>
  </step>

  <step n="2" goal="Verify and prioritize issues">
    <action>For verified issues, assign severity:
      - Critical: Blocks implementation or causes major problems
      - High: Significant gaps or ambiguities that need attention
      - Medium: Improvements that would help quality
      - Low: Nice-to-have suggestions
    </action>
    <action>Document false positives with clear reasoning for dismissal:
      - Why the validator was wrong
      - What evidence contradicts the finding
      - Reference specific story content or project_context.md
    </action>
  </step>

  <step n="3" goal="Apply changes to story file">
    <action>For each verified issue (starting with Critical, then High), apply fix directly to story file</action>
    <action>Changes should be natural improvements:
      - DO NOT add review metadata or synthesis comments to story
      - DO NOT reference the synthesis or validation process
      - Preserve story structure, formatting, and style
      - Make changes look like they were always there
    </action>
    <action>For each change, log in synthesis output:
      - File path modified
      - Section/line reference (e.g., "AC4", "Task 2.3")
      - Brief description of change
      - Before snippet (2-3 lines context)
      - After snippet (2-3 lines context)
    </action>
    <action>Use atomic write pattern for story modifications to prevent corruption</action>
  </step>

  <step n="4" goal="Generate synthesis report">
    <critical>Your synthesis report MUST be wrapped in HTML comment markers for extraction:</critical>
    <action>Produce structured output in this exact format (including the markers):</action>
    <output-format>
&lt;!-- VALIDATION_SYNTHESIS_START --&gt;
## Synthesis Summary
[Brief overview: X issues verified, Y false positives dismissed, Z changes applied to story file]

## Validations Quality
[For each validator: name, score, comments]
[Summary of validation quality - 1-10 scale]

## Issues Verified (by severity)

### Critical
[Issues that block implementation - list with evidence and fixes applied]
[Format: "- **Issue**: Description | **Source**: Validator(s) | **Fix**: What was changed"]

### High
[Significant gaps requiring attention]

### Medium
[Quality improvements]

### Low
[Nice-to-have suggestions - may be deferred]

## Issues Dismissed
[False positives with reasoning for each dismissal]
[Format: "- **Claimed Issue**: Description | **Raised by**: Validator(s) | **Dismissal Reason**: Why this is incorrect"]

## Deep Verify Integration
[If DV findings were present, document how they were handled]

### DV Findings Addressed
[List DV findings that resulted in story changes]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Action**: {What was changed}"]

### DV Findings Dismissed
[List DV findings determined to be false positives or not applicable]
[Format: "- **{ID}** [{SEVERITY}]: {Title} | **Reason**: {Why dismissed}"]

### DV-Validator Overlap
[Note any findings flagged by both DV and validators - these are high confidence]
[If no DV findings: "Deep Verify did not produce findings for this story."]

## Changes Applied
[Complete list of modifications made to story file]
[Format for each change:
  **Location**: [File path] - [Section/line]
  **Change**: [Brief description]
  **Before**:
  ```
  [2-3 lines of original content]
  ```
  **After**:
  ```
  [2-3 lines of updated content]
  ```
]
&lt;!-- VALIDATION_SYNTHESIS_END --&gt;
    </output-format>

  </step>

  <step n="5" goal="Final verification">
    <action>Verify all Critical and High issues have been addressed</action>
    <action>Confirm story file changes are coherent and preserve structure</action>
    <action>Ensure synthesis report is complete with all sections populated</action>
  </step>
</workflow></instructions>
<output-template></output-template>
</compiled-workflow>