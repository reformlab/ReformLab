# Quick Spec: Unified Data Model & JSON-Driven Population Loading

**Created:** 2026-03-24
**Status:** Completed
**Scope:** Internal refactoring + new capability (JSON folder convention)

---

## Problem

The project has two disconnected data paths that share zero types:

| Concern | Loaders (`population/loaders/`) | `load_population()` (`data/pipeline.py`) |
|---|---|---|
| Schema | Raw `pa.Schema` | `DataSchema` (required + optional columns) |
| Metadata | `INSEEDataset`, `ADEMEDataset`, `SDESDataset`, `EurostatDataset` (4 separate types) | `DataSourceMetadata` |
| Provenance | None (no manifest) | `DatasetManifest` (hash, timestamp, provenance) |
| Output | Bare `pa.Table` | `PopulationData` |

Consequences:
1. Loaders produce data with no provenance tracking — violates the project's "assumption transparency" principle.
2. Four per-provider dataset dataclasses carry near-identical fields but aren't interchangeable.
3. No bridge between the two paths — feeding loader output into the pipeline requires writing to disk and re-reading.
4. An analyst wanting to add a new data source must write a Python class. Declarative metadata (schema, column mappings, source info) is locked inside Python code.

## Goal

One mental model for all data, whether it comes from an institutional loader or a user-supplied file. Plus a JSON folder convention so non-Python users can define datasets declaratively.

## Non-Goals

- **No generic `JsonDrivenLoader`** — transformation logic (encoding fallback, ZIP extraction, gzip decompression, row skipping) stays in Python. JSON describes *what* the data is, not *how* to fetch it.
- **No schema evolution / drift resilience** — that's a separate concern (and the right spec to write after this one).
- **No new external dependencies** — the existing PyArrow + stdlib stack is sufficient.

---

## Changes

### 1. Unified dataset descriptor: `DatasetDescriptor`

Replace the four per-provider dataclasses (`INSEEDataset`, `ADEMEDataset`, `SDESDataset`, `EurostatDataset`) with a single type that merges dataset metadata with schema information.

```python
@dataclass(frozen=True)
class DatasetDescriptor:
    """Declarative description of a dataset — schema, metadata, and column mappings."""

    # Identity
    dataset_id: str
    provider: str                          # "insee", "ademe", "eurostat", "sdes", "user"
    description: str

    # Source
    url: str = ""                          # empty for user-supplied local files
    license: str = ""
    version: str = ""

    # Schema (uses DataSchema for required/optional semantics)
    schema: DataSchema                     # target schema after renaming

    # Column mapping (raw source name → project name)
    column_mapping: tuple[tuple[str, str], ...] = ()  # empty = no renaming needed

    # Parse options (for loaders that need them)
    encoding: str = "utf-8"
    separator: str = ","
    null_markers: tuple[str, ...] = ("",)
    file_format: str = "csv"               # "csv", "zip", "csv.gz", "parquet"
    skip_rows: int = 0
```

**Key design choice:** `DatasetDescriptor` carries a `DataSchema` (not a raw `pa.Schema`), giving every dataset required/optional column semantics from day one.

### 2. Loaders produce `PopulationData` + `DatasetManifest`

Update `CachedLoader.download()` return type from `pa.Table` to `tuple[PopulationData, DatasetManifest]`. The base class builds the manifest (content hash, timestamp, provenance from `DatasetDescriptor`) after validation.

This means the `DataSourceLoader` protocol changes:

```python
class DataSourceLoader(Protocol):
    def download(self, config: SourceConfig) -> tuple[PopulationData, DatasetManifest]: ...
    def status(self, config: SourceConfig) -> CacheStatus: ...
    def descriptor(self) -> DatasetDescriptor: ...  # replaces schema()
```

**Migration path for concrete loaders:**
- Each loader's `_fetch()` continues to return `pa.Table` (raw fetched data).
- `CachedLoader.download()` wraps the result: validate schema → cache → build manifest → wrap as `PopulationData`.
- Per-provider `XxxDataset` dataclasses are replaced by `DatasetDescriptor` entries in each catalog.
- Schema validation in `CachedLoader.download()` switches from raw `pa.Schema` comparison to `DataSchema` validation (required columns must be present, optional columns collected if available, type checking on all included columns).

### 3. JSON folder convention for `load_population`

A user can define a dataset as a folder:

```
my-dataset/
├── data.csv          # or data.parquet
├── schema.json       # DataSchema as JSON
└── source.json       # DataSourceMetadata as JSON
```

**`schema.json`** example:
```json
{
  "columns": [
    {"name": "household_id", "type": "int64", "required": true},
    {"name": "income", "type": "float64", "required": true},
    {"name": "region_code", "type": "utf8", "required": false}
  ]
}
```

**`source.json`** example:
```json
{
  "name": "my-household-survey",
  "version": "2024-Q1",
  "url": "https://example.org/data",
  "description": "Custom household survey for Île-de-France",
  "license": "CC-BY-4.0"
}
```

New function:

```python
def load_population_folder(
    path: str | Path,
    *,
    allowed_roots: tuple[Path, ...] | None = None,
) -> tuple[PopulationData, DatasetManifest]:
    """Load a dataset from a folder containing data + JSON metadata."""
```

Logic:
1. Find data file (`data.csv`, `data.parquet`, or the single CSV/Parquet in the folder).
2. Read `schema.json` → build `DataSchema`.
3. Read `source.json` → build `DataSourceMetadata`.
4. Delegate to existing `load_dataset()`.
5. Return `(PopulationData, DatasetManifest)`.

### 4. JSON serialization for `DataSchema` and `DataSourceMetadata`

Add `to_json()` / `from_json()` class methods to both types:

```python
class DataSchema:
    def to_json(self) -> dict: ...

    @classmethod
    def from_json(cls, data: dict) -> DataSchema: ...

class DataSourceMetadata:
    def to_json(self) -> dict: ...

    @classmethod
    def from_json(cls, data: dict) -> DataSourceMetadata: ...
```

PyArrow type strings map directly: `"int64"` → `pa.int64()`, `"float64"` → `pa.float64()`, `"utf8"` → `pa.utf8()`, etc. Use `pa.field(name, pa.type_for_alias(type_string))` for the mapping — no custom type registry needed.

### 5. Example: existing loader as JSON

To demonstrate the pattern, provide a reference example showing how the INSEE Filosofi commune dataset's metadata maps to JSON. This is documentation, not a functional change — loaders continue to use Python catalogs.

```
docs/examples/dataset-folder/
├── README.md                           # explains the convention
└── insee-filosofi-commune/
    ├── schema.json                     # matches _commune_schema()
    └── source.json                     # matches INSEE_CATALOG entry
```

---

## Implementation Order

1. **`DataSchema.from_json()` / `to_json()`** + **`DataSourceMetadata.from_json()` / `to_json()`** — foundation, no breaking changes, fully testable in isolation.

2. **`DatasetDescriptor`** — new type, coexists with old per-provider types initially.

3. **`load_population_folder()`** — new function using (1). No changes to existing code. Can be shipped and validated independently.

4. **Migrate `CachedLoader`** — update `download()` to return `(PopulationData, DatasetManifest)`, replace `schema()` with `descriptor()`, update validation to use `DataSchema`. Update `DataSourceLoader` protocol.

5. **Migrate concrete loaders** — replace `INSEEDataset`/`ADEMEDataset`/etc. with `DatasetDescriptor` in each catalog. Update `_fetch()` callers. Remove old per-provider dataclasses.

6. **Example JSON folder** in `docs/examples/`.

Steps 1–3 are additive (no breaking changes). Steps 4–5 are the refactoring proper.

---

## Testing Strategy

- **Unit tests for JSON round-trip:** `DataSchema` → JSON → `DataSchema` preserves all fields, types, required/optional semantics.
- **Unit tests for `load_population_folder()`:** valid folder, missing schema.json, missing data file, invalid schema, type mismatches.
- **Integration tests for migrated loaders:** existing loader tests should pass with updated return types (need to unpack `(PopulationData, DatasetManifest)` instead of bare `pa.Table`).
- **Provenance tests:** verify that loader downloads now produce `DatasetManifest` with correct content hash, timestamp, and source metadata.

## Risks

- **Breaking change to `DataSourceLoader` protocol:** All code that calls `loader.download()` and expects a `pa.Table` must be updated. Grep for all call sites before starting step 4.
- **`pa.type_for_alias()` coverage:** Verify it handles all PyArrow types used in the project (`int64`, `float64`, `utf8`, `bool_`, `date32`, etc.). If not, a small mapping dict suffices.
- **Column mapping direction:** JSON `column_mapping` must clearly document that it's `[raw_name, project_name]`, not the reverse.

## Review Notes

- Adversarial review completed
- Findings: 14 total, 11 fixed, 3 skipped (F6 deferred as acceptable for current scale, F12 undecided/minor, F13 noise)
- Resolution approach: auto-fix
- Key fixes: path traversal guard on `load_population_folder`, lossy JSON round-trip, IngestionError wrapping, .pyi stub sync, `descriptor()` override guard, `from_json` error handling, removed non-canonical re-export
