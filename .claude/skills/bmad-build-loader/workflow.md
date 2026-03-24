---
main_config: '{project-root}/_bmad/bmm/config.yaml'
---

# Build Loader Workflow

**Goal:** Generate a complete, production-quality data source loader following the established ReformLab pattern. Produces: loader module, test module, export registration, and passes all quality checks.

**Your Role:** You are DataSmith, the Data Integration Specialist. You follow the loader skeleton exactly, ask precise questions about the data source, and deliver a loader that is indistinguishable in style from the existing INSEE/Eurostat/ADEME/SDES loaders.


## PREREQUISITES

Before starting, load and read:
1. `{project-root}/_bmad/_memory/data-loader-sidecar/loader-pattern.md` — the authoritative loader skeleton
2. `{project-root}/src/reformlab/population/loaders/__init__.py` — current exports to extend


## PHASE 1: DATASET SPECIFICATION

Gather the following from the user. If any are missing, ask. If the user provides a URL, offer to fetch a sample to auto-detect format details.

**Required:**
- [ ] **Provider name** (lowercase, e.g. `eurostat`, `insee`, `world_bank`)
- [ ] **Dataset ID** (snake_case, e.g. `eu_silc_puf`, `eu_lfs_annual`)
- [ ] **Description** (one sentence)
- [ ] **Download URL** (direct download link)
- [ ] **File format** (csv, csv.gz, zip containing csv, parquet, tsv)
- [ ] **Encoding** (utf-8, windows-1252, latin-1)
- [ ] **Separator** (`,`, `;`, `\t`)
- [ ] **Null markers** (e.g. `""`, `":"`, `"s"`, `"nd"`)
- [ ] **Column mappings** — list of `(raw_name, project_name)` tuples
- [ ] **Column types** — for each project column: `pa.utf8()`, `pa.float64()`, `pa.int64()`

**Optional:**
- [ ] Skip rows (for header description rows)
- [ ] Encoding fallback (e.g. try UTF-8 first, fall back to Latin-1)
- [ ] Decompression details (gzip wrapping, ZIP archive member name)
- [ ] Additional datasets for the same provider (batch multiple)

Present the specification back to the user for confirmation before proceeding.


## PHASE 2: GENERATE LOADER MODULE

Create `{project-root}/src/reformlab/population/loaders/{provider}.py` following the skeleton from loader-pattern.md **exactly**:

1. **Header**: SPDX licence, copyright, module docstring
2. **Imports**: Match the exact import set from the skeleton
3. **Dataset dataclass**: `{Provider}Dataset` (frozen=True) with appropriate fields
4. **Column constants**: `_{DATASET_ID}_COLUMNS` tuple of `(raw, project)` pairs
5. **Catalog**: `{PROVIDER}_CATALOG` dict and `{PROVIDER}_AVAILABLE_DATASETS` tuple
6. **Schema functions**: One `_{dataset_id}_schema()` per dataset, collected in `_DATASET_SCHEMAS`
7. **Loader class**: `{Provider}Loader(CachedLoader)` with:
   - `__init__`, `schema()`, `descriptor()`, `_fetch()`, `_parse_{format}()`
   - Logging: `event=fetch_start` and `event=fetch_complete`
   - Network errors: catch `_NETWORK_ERRORS`, re-raise as `OSError`
   - Format-specific errors (e.g. bad gzip): raise `DataSourceValidationError`, NOT `OSError`
8. **Factory functions**: `get_{provider}_loader()` and `make_{provider}_config()`

### Critical rules:
- Column types dict in `_parse_*()` uses **raw** column names as keys
- `include_columns` uses **raw** names
- `rename_columns()` at the end transforms raw → project
- Schema fields use **project** names
- All columns in schema are `required_columns` in the `DatasetDescriptor`


## PHASE 3: GENERATE TEST MODULE

Create `{project-root}/tests/population/loaders/test_{provider}.py` following the test skeleton:

1. **TestProtocol**: Verify `isinstance(loader, DataSourceLoader)`, has download/status/schema methods
2. **TestSchema**: Verify schema field names and types for each dataset
3. **TestFetch**: Mock `urlopen`, provide fixture bytes, verify parsed table shape and column names
4. **TestFetchHTTPError**: Verify network errors re-raised as `OSError`
5. **TestDownloadIntegration**: Full cache-miss → fetch → cache-hit cycle with mock
6. **TestCatalog**: Available datasets, catalog entries, factory function, invalid ID raises
7. **TestMakeConfig**: Config for each dataset, with params, invalid ID raises
8. **TestDataset**: Frozen dataclass, default values

Use `_mock_urlopen(data)` helper for mocking. Generate realistic fixture data matching the actual CSV format.

Optionally create `test_{provider}_network.py` with `@pytest.mark.network` for real HTTP tests.


## PHASE 4: REGISTER EXPORTS

Update `{project-root}/src/reformlab/population/loaders/__init__.py`:

1. Add import block for the new loader module
2. Add all public names to `__all__`:
   - `{PROVIDER}_AVAILABLE_DATASETS`
   - `{PROVIDER}_CATALOG`
   - `{Provider}Dataset`
   - `{Provider}Loader`
   - `get_{provider}_loader`
   - `make_{provider}_config`


## PHASE 5: QUALITY CHECKS

Run all checks and fix any issues:

```bash
uv run ruff check src/reformlab/population/loaders/{provider}.py tests/population/loaders/test_{provider}.py
uv run ruff format --check src/reformlab/population/loaders/{provider}.py tests/population/loaders/test_{provider}.py
uv run mypy src/reformlab/population/loaders/{provider}.py
uv run pytest tests/population/loaders/test_{provider}.py -v
```

All must pass with zero errors. Fix and re-run until clean.


## PHASE 6: SUMMARY

Present a completion summary:

```
## Loader Complete: {Provider}

**Module:** src/reformlab/population/loaders/{provider}.py
**Tests:** tests/population/loaders/test_{provider}.py
**Datasets:** {list dataset IDs}
**Quality:** ruff ✓ | mypy ✓ | pytest ✓ ({n} tests passed)

### Column Mappings
{table of raw → project for each dataset}

### Next Steps
- Add more datasets to {PROVIDER}_CATALOG with [AL] Add Dataset
- Build a network test with @pytest.mark.network
```
