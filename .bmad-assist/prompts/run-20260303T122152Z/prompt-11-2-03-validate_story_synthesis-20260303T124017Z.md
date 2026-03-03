<?xml version="1.0" encoding="UTF-8"?>
<!-- BMAD Prompt Run Metadata -->
<!-- Epic: 11 -->
<!-- Story: 2 -->
<!-- Phase: validate-story-synthesis -->
<!-- Timestamp: 20260303T124017Z -->
<compiled-workflow>
<mission><![CDATA[

Master Synthesis: Story 11.2

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
<file id="51f70c3b" path="_bmad-output/implementation-artifacts/11-2-implement-insee-data-source-loader.md" label="STORY FILE"><![CDATA[


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


]]></file>
<file id="1d910d88" path="[Validator A]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-2-implement-insee-data-source-loader - implement-insee-data-source-loader  
**Story File:** _bmad-output/implementation-artifacts/11-2-implement-insee-data-source-loader.md  
**Validated:** 2026-03-03  
**Validator:** Quality Competition Engine

---

## Executive Summary

### Issues Overview

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 1 | 0 |
| ⚡ Enhancements | 3 | 0 |
| ✨ Optimizations | 1 | 0 |
| 🤖 LLM Optimizations | 1 | 0 |

**Overall Assessment:** Story needs significant rework to close gaps (MAJOR REWORK).

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | AC2 demands household composition datasets but catalog/tasks only cover income datasets; AC cannot be met | Acceptance Criteria vs Tasks | +3 |
| 🟠 IMPORTANT | AC1 “schema-validated… documented columns” lacks explicit column lists/types per dataset → untestable | Acceptance Criteria | +1 |
| 🟠 IMPORTANT | No concrete URLs or download specs per dataset → hidden external dependency blocks implementation | Tasks 1.3 | +1 |
| 🟠 IMPORTANT | Household composition dataset not scoped yet likely large (hundreds MB); no performance/streaming guidance | AC2/Dev Notes | +1 |
| 🟡 MINOR | Offline/stale-cache behavior not required in AC for this loader though base supports it; risk of untested regressions | AC list | +0.3 |
| 🟠 IMPORTANT | Estimation hindered: missing schema/URL for composition dataset makes effort uncertain | Estimation | +1 |
| 🟢 CLEAN PASS | Technical alignment largely consistent with architecture |  | -0.5 |

### Evidence Score: 6.8

| Score | Verdict |
|-------|---------|
| **6.8** | **MAJOR REWORK** |

---

## 🎯 Ruthless Story Validation 11.2

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ⚠️ Partial | 3/10 | Depends on Story 11.1 (protocol/cache) but not re-stated; also composition dataset undefined—may depend on future story. |
| **N**egotiable | ✅ OK | 1/10 | Implementation details allow some freedom (urllib/pyarrow choices given but acceptable). |
| **V**aluable | ✅ OK | 0/10 | Clear value: unlocks real INSEE data for population pipeline. |
| **E**stimable | ⚠️ Weak | 6/10 | Missing URLs, schemas for composition dataset create estimation uncertainty. |
| **S**mall | ✅ OK | 2/10 | Scope confined to one loader + fixtures, but composition dataset size risk could bloat. |
| **T**estable | ⚠️ Weak | 6/10 | AC1 lacks explicit column specs; AC2 composition dataset absent → untestable. |

### INVEST Violations

- **[6/10] Testable:** ACs don’t enumerate columns/types; composition dataset absent so AC2 cannot be objectively tested.
- **[6/10] Estimable:** Missing concrete inputs (URLs, schema) for composition dataset undermines estimation.
- **[3/10] Independent:** Hidden dependency on future composition dataset work.

### Acceptance Criteria Issues

- **Missing Coverage:** AC2 requires “household composition tables” but tasks/catalog list only income datasets; composition dataset unspecified.
  - *Quote:* "when queried for available datasets, then at least household income distribution and household composition tables are available."
  - *Recommendation:* Add concrete composition dataset entries (IDs, URLs, schemas) to catalog and tests.
- **Ambiguous:** AC1 “schema-validated pa.Table with documented columns” doesn’t state the columns/types for each dataset.
  - *Quote:* "returns a schema-validated `pa.Table` with documented columns."
  - *Recommendation:* Enumerate expected columns and types per dataset in ACs or a table.
- **Untestable Edge Cases:** No AC for handling ZIP-wrapped CSV, encoding fallback, or offline/stale cache—implementation may skip or regress.
  - *Quote:* AC list omits these behaviors.
  - *Recommendation:* Add ACs for ZIP handling, encoding fallback, offline cache behavior.

### Hidden Risks and Dependencies

- **External Data URLs Unknown:** Catalog lacks concrete INSEE download URLs; devs must research, blocking progress.
  - *Impact:* Schedule risk, mis-URL leading to failing downloads.
  - *Mitigation:* Provide vetted URLs for each dataset.
- **Large File Handling:** Composition datasets (Recensement) can be 400–700MB; story gives no streaming/memory guidance.
  - *Impact:* OOM/performance regressions; CI infeasible.
  - *Mitigation:* Require chunked/streaming strategy or clarify scope to small samples.
- **Fixture Gap:** AC4 only states “fixture files” but doesn’t include composition fixture; missing test assets will stall CI.
  - *Impact:* Tests can’t be written/run; acceptance unverified.
  - *Mitigation:* Add fixture requirements for every cataloged dataset.

### Estimation Reality-Check

**Assessment:** Underestimated — key inputs (URLs, schemas, fixture scope) missing; composition dataset size risk not accounted for.

### Technical Alignment

**Status:** Largely aligned (adapter + cache, pyarrow, no pandas).  
No blocking architecture conflicts found.

---

## 🚨 Critical Issues (Must Fix)

### 1. Composition dataset missing from scope

**Impact:** AC2 cannot be met; developer lacks target schema/URL; implementation will ship incomplete, causing failing acceptance.  
**Source:** AC2 vs Tasks (catalog lists only income datasets).

**Problem:** Story promises household composition availability but provides no dataset definition, schema, URL, fixtures, or tests for it.  
**Recommended Fix:** Add at least one composition dataset entry (e.g., RP household composition extract) with ID, URL, schema, expected columns/types, and corresponding tests/fixtures; adjust tasks accordingly.

---

## ⚡ Enhancement Opportunities (Should Add)

### 2. Explicit column schemas per dataset
**Benefit:** Makes AC1 testable; reduces mis-parsing risk.  
**Source:** AC1 language.  
**Current Gap:** “documented columns” not enumerated.  
**Suggested Addition:** Table of raw→project column mappings and pyarrow types for each catalog entry (income & composition).

### 3. Concrete download metadata
**Benefit:** Removes blocking research; ensures consistent URLs and expected file formats.  
**Source:** Tasks 1.x.  
**Current Gap:** URLs, file sizes, compression not specified.  
**Suggested Addition:** Provide canonical HTTPS URLs, expected size, compression (zip/plain), and update tasks to verify.

### 4. Large-file / performance guidance
**Benefit:** Prevents OOM/timeouts on composition data.  
**Source:** Dev Notes mention CSV parsing but not size handling.  
**Current Gap:** No limits or strategy for 400MB+ files.  
**Suggested Addition:** Scope composition dataset to small sample, or require streaming/chunked read and documented performance budget.

---

## ✨ Optimizations (Nice to Have)

### 5. Offline/stale-cache acceptance
**Value:** Guards regressions in offline-first promise.  
**Suggestion:** Add AC ensuring INSEE loader honors `REFORMLAB_OFFLINE` and uses stale cache on network failure (leveraging CachedLoader behavior).

---

## 🤖 LLM Optimization Improvements

### 6. Trim verbose Dev Notes; surface requirements table
**Issue:** Token overhead hides key requirements.  
**Token Impact:** Medium reduction.  
**Current:**
```
Long narrative on CSV parsing strategy and encoding notes scattered across paragraphs.
```
**Optimized:**
```
Parsing requirements (must):
- Use pyarrow.csv; delimiter=';'; encoding utf-8 then latin-1 fallback.
- Detect .zip → extract first .csv.
- Log event=fetch_start/fetch_complete with provider, dataset_id, url, rows, cols.
- No new deps (requests/pandas disallowed).
```
**Rationale:** Converts prose into scannable, actionable checklist for dev agents.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 62% |
| Architecture Alignment | 85% |
| Previous Story Integration | 70% |
| LLM Optimization Score | 55% |
| **Overall Quality Score** | **68%** |

### Disaster Prevention Assessment

- Reinvention Risk: Mitigated by recommending catalog/schema reuse.
- Spec Gaps: Significant (composition dataset, schemas).
- File Structure: OK.
- Regression Risk: Moderate (offline/cache not in AC).
- Implementation Vagueness: Moderate.

### Competition Outcome

🏆 Validator identified 6 improvements that materially enhance story clarity and testability.

---

**Report Generated:** 2026-03-03  
**Validation Engine:** BMAD Method Quality Competition v1.0

]]></file>
<file id="557aedd2" path="[Validator B]" label="VALIDATION OUTPUT"><![CDATA[

# 🎯 Story Context Validation Report

**Story:** 11-2-implement-insee-data-source-loader
**Story File:** `_bmad-output/implementation-artifacts/11-2-implement-insee-data-source-loader.md`
**Validated:** 2026-03-03
**Validator:** Quality Competition Engine

---

## Executive Summary

| Category | Found | Applied |
|----------|-------|---------|
| 🚨 Critical Issues | 3 | 0 |
| ⚡ Enhancements | 4 | 0 |
| ✨ Optimizations | 3 | 0 |
| 🤖 LLM Optimizations | 2 | 0 |

**Overall Assessment:** Story requires fixes before development. Three critical issues will cause AC failures or implementation defects; the most serious is a direct contradiction between AC#2 and the implementation tasks (no household composition dataset in catalog). Minor issues are largely correctable without structural changes.

---

## Evidence Score Summary

| Severity | Description | Source | Score |
|----------|-------------|--------|-------|
| 🔴 CRITICAL | AC#2 vs catalog mismatch — no household composition dataset defined, only 3 Filosofi income datasets | Task 1.3 vs AC#2 | +3 |
| 🔴 CRITICAL | Missing handling for Filosofi suppressed values ("s", "nd") — will cause float64 cast failure on real data | Dev Notes / INSEE data format | +3 |
| 🔴 CRITICAL | `INSEEDataset.columns` field type contradicts itself: `tuple[str, ...]` (Task 1.2) vs `tuple[tuple[str, str], ...]` (Dev Notes) | Task 1.2 vs Dev Notes schema | +3 |
| 🟠 IMPORTANT | Reference URLs are documentation pages, not direct download URLs — actual file URLs differ | References section | +1 |
| 🟠 IMPORTANT | Filosofi commune-level data uses zone query interface (`/zones/7758831`), may not be a simple GET | Dev Notes / verified via web | +1 |
| 🟠 IMPORTANT | `INSEEDataset.file_format` accepts "parquet" but INSEE does not offer Parquet format for any listed dataset | Task 1.2 / INSEE page | +1 |
| 🟠 IMPORTANT | Schema validation in `CachedLoader.download()` enforces exact type match — `_fetch()` must cast explicitly, story undersells this requirement | `base.py:260-270` | +1 |
| 🟡 MINOR | `pyarrow.csv` `ConvertOptions(null_values=...)` not mentioned for handling "s"/"nd" strings | Dev Notes / CSV parsing | +0.3 |
| 🟡 MINOR | ZIP extraction "first .csv file" is non-deterministic when archive contains multiple CSVs | Task 2.4 | +0.3 |
| 🟡 MINOR | `make_insee_config(**params)` interaction with dataset's default URL not specified | Task 4.1 | +0.3 |
| 🟢 CLEAN PASS | INVEST-N (Negotiable): Leaves room for implementation flexibility | — | -0.5 |
| 🟢 CLEAN PASS | INVEST-V (Valuable): Value clearly stated, contributes to EPIC-11 goals | — | -0.5 |
| 🟢 CLEAN PASS | INVEST-I (Independent): 11.1 dependency explicitly documented, no circular deps | — | -0.5 |
| 🟢 CLEAN PASS | INVEST-S (Small): Well-scoped, 5 SP estimate is appropriate | — | -0.5 |

### Evidence Score: **12.4**

| Score | Verdict |
|-------|---------|
| **12.4** | **REJECT** |

---

## 🎯 Ruthless Story Validation 11.2

### INVEST Criteria Assessment

| Criterion | Status | Severity | Details |
|-----------|--------|----------|---------|
| **I**ndependent | ✅ PASS | 2/10 | Explicit 11.1 dependency documented; no circular deps |
| **N**egotiable | ✅ PASS | 2/10 | Leaves column naming, parse strategy to developer |
| **V**aluable | ✅ PASS | 1/10 | First concrete loader enabling population pipeline — clear value |
| **E**stimable | ⚠️ MARGINAL | 4/10 | AC#2 gap and URL unknowns create hidden scope; commune-level download may be more complex than assumed |
| **S**mall | ✅ PASS | 2/10 | 5 SP, single file + tests — appropriate scope |
| **T**estable | ❌ FAIL | 7/10 | AC#2 cannot be satisfied as written (no household composition dataset in catalog) |

### INVEST Violations

- **[7/10] Testable:** AC#2 requires "household income distribution **and household composition** tables" but all 3 catalog entries in Task 1.3 are Filosofi income datasets. No household composition dataset is defined anywhere in the tasks. The Dev Notes acknowledge RP Census data is large and should be "opt-in" but don't include any catalog entry for it. The AC cannot pass.

### Acceptance Criteria Issues

- **Contradiction:** AC#2 cannot be satisfied as implemented.
  - *Quote:* "Given the INSEE loader, when queried for available datasets, then at least household income distribution and household composition tables are available."
  - *Recommendation:* Either (a) add a lightweight household composition dataset entry to the catalog (e.g., a small RP 2021 aggregated table or redirect to RP data), or (b) update AC#2 to match reality: "at least 3 income distribution datasets at commune and IRIS granularity are available."

- **Missing error scenario:** No AC covers what happens when a network download returns an HTTP 4xx/5xx status. The existing ACs cover network failure (timeout, no connectivity) but not a valid HTTP connection that returns an error page.
  - *Recommendation:* Add: "Given the INSEE server returns an HTTP error (4xx/5xx), when the loader is called, then a `DataSourceDownloadError` is raised."

### Hidden Risks and Dependencies

- **INSEE URL stability:** INSEE regularly reorganizes dataset pages and file paths. URLs hard-coded in the catalog will break. No fallback or `data.gouv.fr` mirror strategy is mentioned.
  - *Impact:* Network tests will break without notice; catalog entries become stale.
  - *Mitigation:* Document in Dev Notes that URLs should be verified before tagging a release; mention `data.gouv.fr` as a stable alternative host for Filosofi data.

- **Filosofi commune-level access pattern:** The commune-level page uses `/zones/7758831` (geographic selector interface), not a static file URL. Direct GET via `urllib.request` may not work without a geographic zone parameter.
  - *Impact:* `filosofi_2021_commune` catalog entry may have an unusable URL; developer will discover this only during network testing.
  - *Mitigation:* Verify the direct download URL before implementing the catalog entry. The IRIS-level URL pattern is confirmed: `https://www.insee.fr/fr/statistiques/fichier/8229323/BASE_TD_FILO_IRIS_2021_DEC_CSV.zip`.

### Estimation Reality-Check

**Assessment:** Underestimated if commune-level URL requires non-trivial access pattern; realistic for IRIS-only scope.

The 5 SP estimate is reasonable if:
- IRIS-level downloads work as described (confirmed via web fetch)
- The commune-level URL issue is resolved quickly

It becomes underestimated if:
- AC#2 requires a household composition dataset (adds unknown scope)
- Filosofi commune-level requires a parameterized zone query (additional HTTP logic)

### Technical Alignment

**Status:** Mostly aligned; three deviations.

- **Columns type field contradiction:** `INSEEDataset.columns: tuple[str, ...]` in Task 1.2 vs `columns: tuple[tuple[str, str], ...] = ()  # (raw_name, project_name) pairs` in Dev Notes. These are two different types. The Dev Notes version is the one that makes sense architecturally (rename mapping), but the Task version is what a developer following tasks would implement.
  - *Architecture Reference:* Dev Notes Schema Design section
  - *Recommendation:* Fix Task 1.2 to use `columns: tuple[tuple[str, str], ...] = field(default_factory=tuple)` explicitly, and remove the ambiguous `tuple[str, ...]` definition.

- **`file_format: "parquet"` not used by any catalog entry:** INSEE does not distribute Parquet files. All realistic catalog entries will be `"csv"` (ZIP-wrapped). The field definition implies Parquet is a valid input format, which adds dead code paths.
  - *Architecture Reference:* Dev Notes "INSEE Data Sources — What to Download" table
  - *Recommendation:* Either remove `file_format` and infer format from URL suffix, or restrict to `Literal["csv", "zip"]`.

- **Schema validation requires exact type matching in `CachedLoader.download()`:** `base.py:260-270` checks `actual_type.equals(expected_type)` — this is strict. `pyarrow.csv.read_csv()` infers types from content; if a column looks like integers, it produces `int64`, not `float64`. The story says "cast to appropriate PyArrow types" but frames it as optional good practice. It is mandatory for the schema validation in `CachedLoader` to pass.
  - *Architecture Reference:* `src/reformlab/population/loaders/base.py:246-270`
  - *Recommendation:* Add a Dev Note callout: "Type casting in `_fetch()` is **mandatory**, not optional — `CachedLoader.download()` enforces exact type equality. Use `pyarrow.csv.ConvertOptions(column_types={...})` or explicit `table.cast()` calls."

---

## 🚨 Critical Issues (Must Fix)

### 1. AC#2 Cannot Be Satisfied — No Household Composition Dataset in Catalog

**Impact:** Story will fail its acceptance test at review; reviewer will correctly note that `AVAILABLE_DATASETS` contains only income datasets.
**Source:** Task 1.3 vs AC#2

**Problem:**
AC#2 reads: "at least household income distribution **and household composition** tables are available." Task 1.3 defines exactly 3 catalog entries: `filosofi_2021_commune`, `filosofi_2021_iris_declared`, `filosofi_2021_iris_disposable`. All three are Filosofi income/welfare datasets. None is a household composition dataset. The Dev Notes say RP Census data is large (400–700 MB) and should be opt-in, but don't add any catalog entry for household composition — not even a small aggregated summary table.

**Recommended Fix:**
Choose one of:
- **Option A (Preferred):** Add a 4th catalog entry for a small INSEE RP 2021 household composition aggregate (e.g., `"rp_2021_household_composition"` — commune-level household size distribution from RP). INSEE distributes lightweight aggregate files from RP that are <5 MB.
- **Option B (Simpler):** Rewrite AC#2 to accurately reflect the scope: "at least 3 income distribution datasets at commune and IRIS granularity are available." This removes the household composition requirement from this story and defers it to when the pipeline actually needs it (Story 11.6+).

---

### 2. Filosofi Suppressed Values ("s", "nd") Will Break Float Casting

**Impact:** Any commune or IRIS with suppressed data (small cell size, privacy) will cause a parse failure or produce `null` values that break downstream type validation.
**Source:** Missing from Dev Notes; INSEE format documentation

**Problem:**
INSEE Filosofi data uses `"s"` (secret/suppressed for privacy protection) and `"nd"` (non disponible) as string placeholders in numeric income columns. Real commune-level Filosofi data for small communes regularly has suppressed decile values. When `pyarrow.csv.read_csv()` encounters `"s"` in a `float64` column without explicit null configuration, it will either:
- Fail with a parse error (if strict mode)
- Silently produce `null` or cast incorrectly (if auto-inferred)

This is not mentioned anywhere in the story.

**Recommended Fix:**
Add to Dev Notes CSV parsing section:

> **INSEE null value markers:** Filosofi files use `"s"` (suppressed) and `"nd"` (non-available) as string placeholders in numeric columns. Configure `pyarrow.csv.ConvertOptions(null_values=["s", "nd", ""])` when calling `pcsv.read_csv()`, and set `column_types` for all numeric fields to `pa.float64()` explicitly.

Add a test case in Task 7.3 to verify that a fixture row with `"s"` in an income column produces `null` (not an error) in the output table.

---

### 3. `INSEEDataset.columns` Field Type Is Contradictory

**Impact:** Developer will have to choose one interpretation; whichever they pick will conflict with one section of the story. The rename mapping won't work if `tuple[str, ...]` is implemented instead of `tuple[tuple[str, str], ...]`.
**Source:** Task 1.2 vs Dev Notes "INSEEDataset Design"

**Problem:**
Task 1.2 defines: `columns: tuple[str, ...]` — a flat tuple of expected output column names.
Dev Notes define: `columns: tuple[tuple[str, str], ...] = ()  # (raw_name, project_name) pairs` — a tuple of pairs for rename mapping.

These are fundamentally different types. The Dev Notes version is the one that makes architectural sense (the loader needs to know both raw INSEE names and project names to do renaming). But a developer following the tasks literally will implement `tuple[str, ...]` — which provides no rename information.

**Recommended Fix:**
Remove the `columns: tuple[str, ...]` definition from Task 1.2 and replace with the Dev Notes version: `columns: tuple[tuple[str, str], ...] = field(default_factory=tuple)` with the clarification that each inner tuple is `(raw_insee_column_name, project_column_name)`. Also update the schema example in Task 1.4 to show how the columns field drives the rename mapping.

---

## ⚡ Enhancement Opportunities (Should Add)

### 1. Provide Verified Direct Download URLs for All Catalog Entries

**Benefit:** Eliminates guesswork; developer can run network tests immediately.
**Source:** References section points to documentation pages, not file URLs.

**Current Gap:**
References list:
- `https://www.insee.fr/fr/statistiques/7758831` — this is a geographic selector interface page, not a direct download
- `https://www.insee.fr/fr/statistiques/8229323` — this is a documentation page

The actual IRIS-level download URL (confirmed via web fetch) is:
- `https://www.insee.fr/fr/statistiques/fichier/8229323/BASE_TD_FILO_IRIS_2021_DEC_CSV.zip` (declared income)
- `https://www.insee.fr/fr/statistiques/fichier/8229323/BASE_TD_FILO_IRIS_2021_DISP_CSV.zip` (disposable income — assumed, matching pattern)

The commune-level download URL needs to be verified separately — the `filo2021_cc_rev.csv` file may be available via `data.gouv.fr` rather than a direct INSEE URL.

**Suggested Addition:**
Update the dataset catalog in Task 1.3 with verified direct download URLs, and add a note in Dev Notes: "Verify all URLs before committing the catalog. Use `data.gouv.fr` as a stable mirror fallback for INSEE files (e.g., `https://www.data.gouv.fr/fr/datasets/...`)."

---

### 2. Clarify That `_fetch()` Column Renaming is Mandatory, Not Optional

**Benefit:** Prevents a class of schema validation failures that are hard to debug.
**Source:** `src/reformlab/population/loaders/base.py:246-270`

**Current Gap:**
`CachedLoader.download()` validates column names AND types against `self.schema()` with exact matching. The story describes column renaming and type casting as implementation guidance, but doesn't clearly state that the validation gate in the parent class makes this mandatory.

**Suggested Addition:**
Add a boxed callout in Dev Notes under "Schema Design":
> ⚠️ **Critical:** `CachedLoader.download()` enforces exact column name and type equality against `schema()`. `_fetch()` MUST return a `pa.Table` with (1) project-standard column names, not raw INSEE names, and (2) exact types matching the schema (`float64`, not `int64` or `string`). The validation gate raises `DataSourceValidationError` before caching — test this explicitly in Task 7.3.

---

### 3. Add Test Case for HTTP Error Response (4xx/5xx)

**Benefit:** Ensures the loader handles server errors gracefully; currently no AC or test covers this.
**Source:** Missing from Task 7

**Current Gap:**
The tests cover: network timeout/failure (OSError), cache hit, cache miss, offline mode, ZIP handling, encoding fallback. But there is no test for a valid HTTP connection that returns a 4xx/5xx status code. `urllib.request.urlopen()` raises `urllib.error.HTTPError` for 4xx/5xx, which is a subclass of `urllib.error.URLError`, not `OSError`. Task 2.5 says to re-raise as `OSError`, but if the developer only handles `urllib.error.URLError` and `OSError`, an HTTP 404 may propagate as `HTTPError` instead.

**Suggested Addition:**
Add Task 7.3b: "Monkeypatch `urllib.request.urlopen` to raise `urllib.error.HTTPError(url, 404, 'Not Found', {}, None)` — verify `DataSourceDownloadError` is raised (not `HTTPError` propagating unhandled)."

---

### 4. Specify Which File to Extract from ZIP Archives

**Benefit:** Prevents non-deterministic behavior when ZIP contains multiple CSVs.
**Source:** Task 2.4

**Current Gap:**
Task 2.4 says "extract the first `.csv` file from the archive." Real INSEE ZIP archives for IRIS data contain exactly one CSV, but the "first file" heuristic fails if the structure changes. No filename-matching strategy is specified.

**Suggested Addition:**
Update Task 2.4: "Extract the CSV file from the archive by finding the first entry whose name ends with `.csv` (case-insensitive) using `zipfile.namelist()`. If zero or multiple `.csv` files are found, raise `DataSourceValidationError` with a clear message."

---

## ✨ Optimizations (Nice to Have)

### 1. Document `pyarrow.csv.ConvertOptions` null_values for Filosofi

**Value:** Avoids silent data quality issues; saves debugging time with real INSEE data.

**Suggestion:**
Add to the "CSV Parsing Strategy" Dev Notes section:
```python
pcsv.ConvertOptions(
    null_values=["s", "nd", ""],   # INSEE suppressed/unavailable markers
    column_types={"commune_code": pa.string(), "median_income": pa.float64(), ...}
)
```
This is required for correct behavior with real Filosofi files, not just an optimization.

---

### 2. Add data.gouv.fr as a Stable Mirror for INSEE Files

**Value:** Reduces URL rot risk; data.gouv.fr maintains stable persistent URLs for INSEE datasets.

**Suggestion:**
Add a note in Dev Notes: "Consider registering both an INSEE URL and a `data.gouv.fr` mirror URL per dataset, or using `data.gouv.fr` as the primary source. Example: Filosofi 2021 commune is available at `https://www.data.gouv.fr/fr/datasets/r/...` with more stable URL semantics."

---

### 3. Clarify `INSEELoader` Constructor Order (super() before or after dataset assignment)

**Value:** Avoids potential confusion since `CachedLoader.__init__` has a runtime guard.

**Suggestion:**
Task 2.1 says "store the dataset reference, call `super().__init__()`". Since `CachedLoader.__init__` checks class-level method overrides (not instance state), call order doesn't affect the guard — but clarify: "Call `super().__init__(cache=cache, logger=logger)` after setting `self._dataset = dataset` to make the assignment visible before any super() logic runs."

---

## 🤖 LLM Optimization Improvements

### 1. Consolidate Conflicting CSV Parsing Guidance

**Issue:** Conflicting recommendations — wastes tokens and creates ambiguity.
**Token Impact:** ~200 tokens of conflicting guidance

**Current:**
```
# Dev Notes show stdlib csv approach:
import csv
def _parse_csv(self, raw_bytes, encoding, separator):
    reader = csv.DictReader(...)
    
# Then immediately says:
# Prefer `pyarrow.csv.read_csv()` — it's more efficient...
```

**Optimized:**
```
Use `pyarrow.csv.read_csv(io.BytesIO(raw_bytes), ...)` exclusively.
The stdlib `csv` approach shown above is illustrative only — do not implement it.
```

**Rationale:** The current text shows two approaches then says to prefer one. A dev agent may implement the first one shown. Remove the stdlib csv example entirely or move it to a "why pyarrow is better" footnote.

---

### 2. Remove Redundant `INSEEDataset` vs `SourceConfig` Mapping Explanation

**Issue:** The relationship between `INSEEDataset` and `SourceConfig` is mentioned in Task 4.1 and indirectly in Task 2.1, with the factory functions serving as the bridge. The story never states this relationship concisely.
**Token Impact:** ~150 tokens of implied (not stated) relationship

**Current:**
The mapping between `INSEEDataset.url` → `SourceConfig.url` is implicit in Task 4.1's `make_insee_config` description. The developer must infer that `INSEELoader._fetch(config: SourceConfig)` must also use `self._dataset` for encoding/separator info (because those aren't in `SourceConfig`).

**Optimized:**
Add one explicit sentence to Task 2.3:
> "`_fetch(config: SourceConfig)` uses `config.url` for the download URL and `self._dataset.encoding` + `self._dataset.separator` for parsing — the `SourceConfig` carries the URL + cache key context; `INSEEDataset` carries the format/encoding metadata."

**Rationale:** This avoids a common dev agent mistake of trying to extract encoding from `SourceConfig.params` instead of `self._dataset`.

---

## 📝 Changes Applied

No changes were applied to the story file. This report serves as documentation only.

---

## 🏆 Competition Results

### Quality Metrics

| Metric | Score |
|--------|-------|
| Requirements Coverage | 72% |
| Architecture Alignment | 85% |
| Previous Story Integration | 90% |
| LLM Optimization Score | 75% |
| **Overall Quality Score** | **80%** |

### Disaster Prevention Assessment

- **Reinvention Prevention:** ✅ Correctly identifies `CachedLoader` base class and `MockCachedLoader` test pattern from 11.1
- **Technical Specification Disasters:** ❌ `INSEEDataset.columns` type contradiction will force an implementation decision that splits from spec
- **File Structure Disasters:** ✅ File locations and naming conventions are correct
- **Regression Disasters:** ✅ No breaking changes to existing 11.1 infrastructure; test markers already in pyproject.toml
- **Implementation Disasters:** ❌ Missing null value handling for Filosofi "s"/"nd" — will silently break on real data; AC#2 gap will cause review failure

### Competition Outcome

🏆 **Validator identified 12 issues** that require attention before this story can be safely implemented. Three critical issues — AC mismatch, missing null value handling, and type field contradiction — are blockers. Fixing these requires approximately 1 hour of story revision, not code changes.

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
<var name="session_id">a150e0e4-297d-4d19-bb87-fad4cc2cae43</var>
<var name="sprint_status">_bmad-output/implementation-artifacts/sprint-status.yaml</var>
<var name="story_file" file_id="51f70c3b">embedded in prompt, file id: 51f70c3b</var>
<var name="story_id">11.2</var>
<var name="story_key">11-2-implement-insee-data-source-loader</var>
<var name="story_num">2</var>
<var name="story_title">implement-insee-data-source-loader</var>
<var name="template">False</var>
<var name="timestamp">20260303_1340</var>
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