<!-- VALIDATION_SYNTHESIS_START -->
## Synthesis Summary

Synthesized 2 independent validator reviews for Story 11.2 (Implement INSEE data source loader). **8 issues verified and fixed**, **5 issues dismissed** as false positives or low-priority. All Critical and High issues have been addressed with direct edits to the story file.

## Validations Quality

| Validator | Score | Comments |
|-----------|-------|----------|
| Validator A | 6/10 | Correctly identified the AC#2 household composition gap (critical), but several findings were over-cautious or already handled by the base class. The "MAJOR REWORK" verdict was inflated — most issues are spec clarifications, not structural rework. |
| Validator B | 8/10 | Strong technical depth. Identified 3 genuine critical issues with good evidence (AC#2, suppressed values, columns type contradiction). Cross-referenced actual code in `base.py` to verify schema validation strictness. Some enhancements were valuable (SourceConfig vs INSEEDataset clarification). |

**Overall validation quality: 7/10** — Good coverage with some noise. Validator B was more technically rigorous and provided actionable fixes. Both validators correctly identified the AC#2 gap as the top issue.

## Issues Verified (by severity)

### Critical

- **AC#2 household composition mismatch** | **Source**: Validator A + B (consensus) | **Fix**: Rewrote AC#2 from "household income distribution and household composition tables" to "at least 3 income distribution datasets at commune and IRIS granularity." Updated story statement to match. The catalog only contains Filosofi income datasets; RP Census files are 400-700MB and explicitly deferred in Dev Notes. Adding a large dataset would blow story scope.

- **`INSEEDataset.columns` type contradiction** | **Source**: Validator B | **Fix**: Task 1.2 said `columns: tuple[str, ...]` but Dev Notes showed `columns: tuple[tuple[str, str], ...] = ()  # (raw_name, project_name) pairs`. The Dev Notes version is architecturally correct (rename mapping needs both raw and project names). Fixed Task 1.2 to use `tuple[tuple[str, str], ...] = ()` with explicit documentation.

- **Filosofi suppressed values ("s", "nd") unhandled** | **Source**: Validator B | **Fix**: Added `null_markers: tuple[str, ...] = ("s", "nd", "")` field to `INSEEDataset`, added null value handling guidance to CSV Format Specifics and CSV Parsing Strategy sections, updated test fixtures to include rows with "s" and "nd", added test case 7.5b for suppressed value handling.

### High

- **Schema validation type casting is mandatory, not optional** | **Source**: Validator B | **Fix**: Added "Mandatory type casting" callout under Schema Design section, referencing `base.py:260-270` strict equality check. `_fetch()` must return exact types matching `schema()` or `DataSourceValidationError` is raised.

- **CSV parsing guidance conflict (stdlib csv vs pyarrow.csv)** | **Source**: Validator B | **Fix**: Removed the stdlib `csv.DictReader` example entirely. Replaced "CSV Parsing Strategy" section with pyarrow.csv-only guidance including `ConvertOptions` with `null_values` and `column_types`. Updated "No New Dependencies" section to remove `csv` and `io.StringIO`.

- **`_fetch()` SourceConfig vs INSEEDataset data source unclear** | **Source**: Validator B | **Fix**: Updated Task 2.3 to explicitly state: "SourceConfig carries URL + cache key; INSEEDataset carries format/encoding metadata." Developer now knows `config.url` for download and `self._dataset.encoding`/`self._dataset.separator` for parsing.

### Medium

- **ZIP extraction "first .csv" non-deterministic** | **Source**: Validator B | **Fix**: Updated Task 2.4 to specify: find first entry ending with `.csv` (case-insensitive) via `namelist()`, raise `DataSourceValidationError` if zero or multiple `.csv` files found.

- **Missing HTTP error (4xx/5xx) test case** | **Source**: Validator B | **Fix**: Added test case 7.5c: monkeypatch `urlopen` to raise `HTTPError(url, 404, ...)`, verify it's caught and re-raised as `OSError`. Also clarified in Error Handling Notes that `HTTPError` is a subclass of `URLError` and is caught by the existing exception clause.

### Low

- **`file_format` accepts "parquet" but no catalog entry uses it** | **Source**: Validator B | Deferred. Changed Task 1.2 to say `"csv" or "zip"` instead of `"csv" or "parquet"`. INSEE doesn't distribute Parquet, and the field is harmless defensive code. Full removal not warranted.

## Issues Dismissed

- **"No concrete URLs or download specs per dataset"** | **Raised by**: Validator A, partially Validator B | **Dismissal Reason**: The story provides URL patterns (`https://www.insee.fr/fr/statistiques/fichier/...`), specific reference URLs for each Filosofi dataset, and the IRIS download pattern. The developer can verify exact download URLs during implementation. Hardcoding URLs in the story is fragile — the catalog constants in code are the right place for them. Validator B's note about URL verification is reasonable but is implementation-time work, not a story deficiency.

- **"Large file / performance guidance missing"** | **Raised by**: Validator A | **Dismissal Reason**: The three datasets in scope are 3 KB, 835 KB, and 892 KB. The Dev Notes explicitly defer RP Census (400-700 MB) to future work. There is no large-file concern for this story's scope.

- **"Offline/stale-cache acceptance criteria missing"** | **Raised by**: Validator A | **Dismissal Reason**: Offline/stale-cache behavior is implemented by `CachedLoader.download()` in the base class (Story 11.1). The INSEE loader inherits this automatically. Adding a redundant AC would test the base class, not the INSEE loader. Already covered by Story 11.1's test suite.

- **"INVEST-Independent: depends on 11.1 not re-stated"** | **Raised by**: Validator A | **Dismissal Reason**: The story explicitly references Story 11.1 as the predecessor in Dev Notes ("Architecture Context" section), References section, and Architecture alignment section. The dependency is documented.

- **"Filosofi commune-level uses zone query interface, may not be simple GET"** | **Raised by**: Validator B | **Dismissal Reason**: This is an implementation-time concern. The developer will verify the actual download URL pattern during Task 1.3. If the commune-level page requires a different access pattern, the URL in the catalog entry will be adjusted. The IRIS-level URLs (confirmed working pattern) are the primary target; commune-level is supplementary.

## Deep Verify Integration

Deep Verify did not produce findings for this story.

### DV Findings Addressed
N/A

### DV Findings Dismissed
N/A

### DV-Validator Overlap
N/A

## Changes Applied

**Location**: Story file (line 11) - Story statement
**Change**: Removed "Recensement household composition" from scope
**Before**:
```
I want an INSEE data source loader that downloads, caches, and schema-validates key INSEE datasets (Filosofi income distributions and Recensement household composition),
```
**After**:
```
I want an INSEE data source loader that downloads, caches, and schema-validates key INSEE Filosofi income distribution datasets (commune-level and IRIS-level),
```

---

**Location**: Story file (line 17) - AC#2
**Change**: Aligned with actual catalog scope
**Before**:
```
2. Given the INSEE loader, when queried for available datasets, then at least household income distribution and household composition tables are available.
```
**After**:
```
2. Given the INSEE loader, when queried for available datasets, then at least 3 income distribution datasets at commune and IRIS granularity are available.
```

---

**Location**: Story file (line 25) - Task 1.2
**Change**: Fixed columns type from `tuple[str, ...]` to rename mapping, added null_markers field, changed file_format to csv/zip
**Before**:
```
1.2 Define `INSEEDataset` frozen dataclass with fields: ... `columns: tuple[str, ...]` (expected output columns)
```
**After**:
```
1.2 Define `INSEEDataset` frozen dataclass with fields: ... `null_markers: tuple[str, ...] = ("s", "nd", "")` (INSEE suppression markers), `columns: tuple[tuple[str, str], ...] = ()` where each inner tuple is `(raw_insee_column_name, project_column_name)` — serves as both documentation and rename mapping
```

---

**Location**: Story file (line 36) - Task 2.3
**Change**: Clarified SourceConfig vs INSEEDataset responsibility split
**Before**:
```
2.3 Implement `_fetch(self, config: SourceConfig) -> pa.Table` — download the dataset from `config.url` using `urllib.request`, parse CSV (semicolon-separated, UTF-8 default with Latin-1 fallback) or Parquet, select and rename columns to match schema, return `pa.Table`
```
**After**:
```
2.3 Implement `_fetch(self, config: SourceConfig) -> pa.Table` — download from `config.url` using `urllib.request`, parse using `self._dataset.encoding` and `self._dataset.separator` for format metadata (SourceConfig carries URL + cache key; INSEEDataset carries format/encoding metadata), select and rename columns per `self._dataset.columns` mapping, cast types to match `self.schema()`, return `pa.Table`
```

---

**Location**: Story file (line 37) - Task 2.4
**Change**: Specified deterministic ZIP extraction strategy
**Before**:
```
2.4 Handle ZIP-wrapped CSV files (INSEE often wraps CSVs in ZIP archives): detect `.zip` suffix, extract the first `.csv` file from the archive
```
**After**:
```
2.4 Handle ZIP-wrapped CSV files ...: detect `.zip` suffix in URL, extract using `zipfile.ZipFile(io.BytesIO(raw_bytes))`, find the first entry whose name ends with `.csv` (case-insensitive) via `namelist()`. If zero or multiple `.csv` files are found, raise `DataSourceValidationError` with a clear message listing the archive contents
```

---

**Location**: Story file (lines 66-67) - Tasks 7.5b, 7.5c
**Change**: Added suppressed values test and HTTP error test
**Before**:
```
7.5 `TestINSEELoaderFetchEncodingFallback`: verify Latin-1 fallback when UTF-8 decode fails
7.6 `TestINSEELoaderDownloadIntegration`: ...
```
**After**:
```
7.5 `TestINSEELoaderFetchEncodingFallback`: verify Latin-1 fallback when UTF-8 decode fails
7.5b `TestINSEELoaderFetchSuppressedValues`: verify that fixture rows containing "s" and "nd" in numeric income columns produce null values (not parse errors) in the output table
7.5c `TestINSEELoaderFetchHTTPError`: monkeypatch `urllib.request.urlopen` to raise `urllib.error.HTTPError(url, 404, 'Not Found', {}, None)` — verify it is caught and re-raised as `OSError`
7.6 `TestINSEELoaderDownloadIntegration`: ...
```

---

**Location**: Dev Notes - INSEE CSV Format Specifics
**Change**: Added INSEE null value markers documentation and updated loader steps
**Before**:
```
The loader should:
1. Download the raw CSV
2. Parse with semicolon separator and UTF-8 encoding (Latin-1 fallback)
3. Select relevant columns...
```
**After**:
```
**INSEE null value markers:** Filosofi files use "s" (secret statistique) and "nd" (non disponible) as string placeholders in numeric columns...

The loader should:
1. Download the raw CSV
2. Parse with semicolon separator and UTF-8 encoding (Latin-1 fallback)
3. Configure null value markers: `pyarrow.csv.ConvertOptions(null_values=["s", "nd", ""])`
4. Select relevant columns...
5. Cast to appropriate PyArrow types using `ConvertOptions(column_types={...})`
6. Return as `pa.Table`
```

---

**Location**: Dev Notes - Schema Design
**Change**: Added mandatory type casting callout
**Before**:
```
The column renaming mapping should be defined as a constant per dataset...
```
**After**:
```
The column renaming mapping should be defined as a constant per dataset...

**Mandatory type casting:** `CachedLoader.download()` enforces exact column name and type equality against `schema()` (see `base.py:260-270`). `_fetch()` **must** return a `pa.Table` with (1) project-standard column names, and (2) exact types matching the schema...
```

---

**Location**: Dev Notes - CSV Parsing Strategy
**Change**: Replaced stdlib csv + pyarrow.csv dual example with pyarrow.csv-only guidance
**Before**:
```
### CSV Parsing Strategy: stdlib csv → pa.Table
[stdlib csv example]
Alternatively, use `pyarrow.csv.read_csv()`...
Prefer `pyarrow.csv.read_csv()`...
```
**After**:
```
### CSV Parsing Strategy: pyarrow.csv
Use `pyarrow.csv.read_csv()` exclusively — it is efficient, already a project dependency, and handles type casting and null values natively. Do not use stdlib `csv` module.
[pyarrow.csv example with ConvertOptions including null_values and column_types]
```

---

**Location**: Dev Notes - INSEEDataset Design
**Change**: Updated dataclass to match corrected Task 1.2, added null_markers field
**Before**:
```
file_format: str  # "csv" or "parquet"
...
columns: tuple[tuple[str, str], ...] = ()  # (raw_name, project_name) pairs
```
**After**:
```
file_format: str  # "csv" or "zip" (INSEE distributes CSV or ZIP-wrapped CSV)
...
null_markers: tuple[str, ...] = ("s", "nd", "")  # INSEE suppression markers
columns: tuple[tuple[str, str], ...] = ()  # (raw_name, project_name) pairs
```

---

**Location**: Dev Notes - Test Fixture Design
**Change**: Added rows with suppressed values to fixture example
**Before**:
```
01001;L'Abergement-Clémenciat;330;22050;...
01002;L'Abergement-de-Varey;100;23800;...
```
**After**:
```
01001;L'Abergement-Clémenciat;330;22050;...
01002;L'Abergement-de-Varey;100;23800;...
01003;Ambérieu-en-Bugey;5200;19850;...
01004;Ambérieux-en-Dombes;s;s;s;s;...
01005;Ambléon;nd;nd;nd;nd;...
```

---

**Location**: Dev Notes - Error Handling Notes
**Change**: Clarified HTTPError inheritance chain
**Before**:
```
- INSEE servers returning 404 or error pages → `urllib.error.HTTPError` → re-raise as `OSError`
```
**After**:
```
- INSEE servers returning 404 or error pages → `urllib.error.HTTPError` (subclass of `urllib.error.URLError`) → caught by the `except (urllib.error.URLError, OSError)` clause → re-raised as `OSError`
```

<!-- VALIDATION_SYNTHESIS_END -->
