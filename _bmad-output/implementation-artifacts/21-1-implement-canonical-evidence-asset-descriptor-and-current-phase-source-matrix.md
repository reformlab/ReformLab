# Story 21.1: Implement canonical evidence asset descriptor and current-phase source matrix

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

**As a** developer building the evidence foundation for Epic 21,
**I want** a canonical `DataAssetDescriptor` type with origin/access_mode/trust_status classification plus a versioned source matrix of all current-phase datasets,
**so that** ingestion, APIs, manifests, and UI surfaces all use the same evidence classification contract.

**Acceptance Criteria:**

1. **AC1:** A frozen `DataAssetDescriptor` dataclass exists in `src/reformlab/data/descriptor.py` with fields: `asset_id`, `name`, `description`, `data_class`, `origin`, `access_mode`, `trust_status`, `source_url`, `license`, `version`, `geographic_coverage`, `years`, `intended_use`, `redistribution_allowed`, `redistribution_notes`, `update_cadence`, `quality_notes`, and `references`
2. **AC2:** `origin` is a `Literal` with values: `"open-official"`, `"synthetic-public"`, `"synthetic-internal"` (reserved), `"restricted"` (reserved)
3. **AC3:** `access_mode` is a `Literal` with values: `"bundled"`, `"fetched"`, `"deferred-user-connector"` (reserved)
4. **AC4:** `trust_status` is a `Literal` with values: `"production-safe"`, `"exploratory"`, `"demo-only"`, `"validation-pending"`, `"not-for-public-inference"`
5. **AC5:** `data_class` is a `Literal` with values: `"structural"`, `"exogenous"`, `"calibration"`, `"validation"`
6. **AC6:** All `Literal` types are exported from `src/reformlab/data/__init__.py` for reuse in APIs and Pydantic models
7. **AC7:** `DataAssetDescriptor` has `to_json()` and `from_json()` methods with full validation
8. **AC8:** An `EvidenceAssetError` exception type is added to `src/reformlab/data/errors.py` for evidence-specific validation failures
9. **AC9:** A versioned source matrix document exists at `_bmad-output/planning-artifacts/evidence-source-matrix-{version}.md` documenting all current-phase datasets referenced by docs, demos, and flagship workflow
10. **AC10:** The source matrix includes columns: asset_id, name, provider, description, data_class, origin, access_mode, default_trust_status, license, redistribution_allowed, years, direct_usability, known_limitations
11. **AC11:** All existing `DatasetDescriptor` and `DataSourceMetadata` usages are reviewed for compatibility (no breaking changes in this story)
12. **AC12:** Tests cover: construction with all fields, JSON round-trip, validation of invalid literal values, frozen immutability, and all edge cases
13. **AC13:** Module docstring references this story and the synthetic data decision document

## Tasks / Subtasks

- [ ] **Task 1: Create new error type for evidence validation** (AC: 8)
  - [ ] Add `EvidenceAssetError` to `src/reformlab/data/errors.py` (create file if needed)
  - [ ] Docstring explains it's for evidence-specific validation failures
  - [ ] Pattern matches `ManifestValidationError` in governance/errors.py

- [ ] **Task 2: Define Literal types for evidence classification** (AC: 2, 3, 4, 5, 6)
  - [ ] Add `DataAssetOrigin`, `DataAssetAccessMode`, `DataAssetTrustStatus`, `DataAssetClass` literals to `src/reformlab/data/descriptor.py`
  - [ ] Export from `src/reformlab/data/__init__.py`
  - [ ] Use `from __future__ import annotations` and `Literal` from `typing`
  - [ ] Add docstrings explaining each value with examples

- [ ] **Task 3: Implement DataAssetDescriptor frozen dataclass** (AC: 1, 7)
  - [ ] Create `DataAssetDescriptor` in `src/reformlab/data/descriptor.py`
  - [ ] All fields typed with defaults where appropriate
  - [ ] `__post_init__` validation for required fields and literal value constraints
  - [ ] `to_json()` returns `dict[str, Any]` with non-empty fields only
  - [ ] `from_json()` classmethod with validation and `EvidenceAssetError` on failure
  - [ ] Module-level docstring references Story 21.1 and synthetic-data-decision-document-2026-03-23.md

- [ ] **Task 4: Create comprehensive test suite** (AC: 12)
  - [ ] Create `tests/data/test_data_asset_descriptor.py`
  - [ ] Test class structure mirrors `tests/data/test_pipeline.py` (class-based grouping)
  - [ ] Tests: construction with all fields, JSON round-trip, validation of invalid literal values, frozen immutability
  - [ ] Error path tests: missing required fields, invalid literal values raise `EvidenceAssetError`
  - [ ] Fixtures for valid descriptors across all origins/access_modes/trust_statuses/data_classes

- [ ] **Task 5: Create versioned source matrix document** (AC: 9, 10)
  - [ ] Create `_bmad-output/planning-artifacts/evidence-source-matrix-v1-2026-03-27.md`
  - [ ] Document all current-phase datasets from demos, docs, flagship workflow
  - [ | Include at minimum: French synthetic population (built-in), INSEE sources, Eurostat sources, ADEME sources, calibration targets
  - [ ] All rows have: asset_id, name, provider, description, data_class, origin, access_mode, default_trust_status, license, redistribution_allowed, years, direct_usability, known_limitations
  - [ ] Section header explains scope: current-phase open + synthetic only

- [ ] **Task 6: Review existing patterns for compatibility** (AC: 11)
  - [ ] Document in story notes how `DataAssetDescriptor` relates to existing `DatasetDescriptor` and `DataSourceMetadata`
  - [ ] Confirm no breaking changes to existing APIs in this story
  - [ ] Note integration points for Story 21.2 (API surface) and Story 21.3 (typed schemas)

## Dev Notes

### Architecture Context

**Evidence Taxonomy (from synthetic-data-decision-document-2026-03-23.md):**

The synthetic data decision document defines a **broader data taxonomy** that ReformLab must implement:

| Data Class | Role | Example Questions |
| ----- | ----- | ----- |
| **Structural Data** | Define who or what is modeled | "Who are the households, people, firms, and places?" |
| **Exogenous Data** | Provide observed/projected context inputs | "What are energy prices, carbon tax rates, technology costs this year?" |
| **Calibration and Validation Data** | Fit and test the model | "Does the model reproduce observed reality well enough?" |
| **Governance Data** | Constrain use and claims | "What can be used, and what can be claimed from it?" |

**Story 21.1 Scope:** This story implements the **governance envelope** (DataAssetDescriptor) plus the **source matrix** documentation. It does NOT implement the typed payload contracts for each data class—that's Story 21.3.

**Key Design Decision:** `DataAssetDescriptor` is the **shared asset envelope** carrying origin, access mode, trust status, provenance, and intended-use metadata. It applies to ALL data classes (structural, exogenous, calibration, validation). The payload-specific contracts come in Story 21.3.

### Classification Axes (Section 3.2 of synthetic data decision doc)

**Origin** (where the asset comes from):
- `open-official` — openly usable official or institutional data
- `synthetic-public` — public synthetic datasets from trusted external producers
- `synthetic-internal` — internally generated synthetic assets (future phase, reserved)
- `restricted` — access-controlled data (future phase, reserved)

**Access Mode** (how ReformLab obtains it):
- `bundled` — distributed with the product or repo
- `fetched` — obtained automatically from public sources
- `deferred-user-connector` — reserved for future restricted-data integration

**Trust Status** (what can be claimed about it):
- `production-safe` — validated for decision-support use
- `exploratory` — suitable for exploration, not decision support
- `demo-only` — example data, not for analysis
- `validation-pending` — requires validation dossier before production use
- `not-for-public-inference` — internal use, cannot be used for public claims

**Current-Phase Supported Combinations:**

| Origin | Access Mode | Current Phase Support | Allowed Trust Statuses |
| ----- | ----- | ----- | ----- |
| `open-official` | `bundled` or `fetched` | Yes | `production-safe`, `exploratory` |
| `synthetic-public` | `bundled` or `fetched` | Yes | `exploratory`, `demo-only`, `validation-pending`, `not-for-public-inference` |
| `synthetic-internal` | not yet implemented | No | future |
| `restricted` | `deferred-user-connector` | No | future |

### Project Structure Notes

**File locations:**

- **New type:** `src/reformlab/data/descriptor.py` — extends existing file with `DatasetDescriptor`
- **New error:** `src/reformlab/data/errors.py` — new file (pattern: `src/reformlab/governance/errors.py`)
- **Tests:** `tests/data/test_data_asset_descriptor.py` — mirrors existing `tests/data/test_pipeline.py` structure
- **Exports:** `src/reformlab/data/__init__.py` — add new literals and `DataAssetDescriptor`
- **Matrix doc:** `_bmad-output/planning-artifacts/evidence-source-matrix-v1-2026-03-27.md`

**Existing patterns to follow:**

1. **Frozen dataclass pattern** (from `src/reformlab/data/pipeline.py`):
```python
@dataclass(frozen=True)
class DataSourceMetadata:
    name: str
    version: str
    url: str
    description: str
    license: str = ""
```

2. **JSON serialization pattern** (from `src/reformlab/data/descriptor.py`):
```python
def to_json(self) -> dict[str, Any]:
    result: dict[str, Any] = {"dataset_id": self.dataset_id, ...}
    if self.url:
        result["url"] = self.url
    return result

@classmethod
def from_json(cls, data: dict[str, Any]) -> DatasetDescriptor:
    try:
        return cls(...)
    except KeyError as exc:
        msg = f"DatasetDescriptor JSON missing required key: {exc}"
        raise ValueError(msg) from exc
```

3. **Error type pattern** (from `src/reformlab/governance/errors.py`):
```python
class ManifestValidationError(Exception):
    """Raised when manifest validation fails.

    Indicates missing required fields, invalid field types, invalid hash
    formats, or other structural validation issues.
    """
    pass
```

4. **Testing pattern** (from `tests/data/test_pipeline.py`):
```python
class TestDataSourceMetadata:
    """Tests for DataSourceMetadata frozen dataclass."""

    def test_create_with_all_fields(self) -> None:
        """Given all fields, when created,
        then all fields are accessible."""
        source = DataSourceMetadata(...)
        assert source.name == "test"
```

### Type System Constraints

**From project-context.md:**
- Use `from __future__ import annotations` — no exceptions
- Use `Literal` from `typing` for string enums (not `enum.Enum`)
- Use `X | None` not `Optional[X]`
- Use `dict[str, Any]` not `Dict[str, Any]` (modern generics)
- Frozen dataclasses are the default — mutate via `dataclasses.replace()`
- All validation errors should raise `EvidenceAssetError` with clear messages

**Literal type definitions:**
```python
from __future__ import annotations
from typing import Literal

DataAssetOrigin = Literal[
    "open-official",
    "synthetic-public",
    "synthetic-internal",  # reserved for future
    "restricted",  # reserved for future
]

DataAssetAccessMode = Literal[
    "bundled",
    "fetched",
    "deferred-user-connector",  # reserved for future
]

DataAssetTrustStatus = Literal[
    "production-safe",
    "exploratory",
    "demo-only",
    "validation-pending",
    "not-for-public-inference",
]

DataAssetClass = Literal[
    "structural",
    "exogenous",
    "calibration",
    "validation",
]
```

### Integration with Existing Types

**Relationship to existing types:**

- `DataSourceMetadata` (existing): Basic provenance (name, version, url, description, license)
- `DatasetDescriptor` (existing): Schema + metadata + column mappings for data loading
- `DataAssetDescriptor` (new): Governance envelope with origin/access_mode/trust_status + extended provenance

**Migration note:** This story does NOT replace or break existing types. `DataAssetDescriptor` is additive for the evidence system. Story 21.2 will integrate these fields into API responses and frontend models.

### Source Matrix Document Structure

**Template for `_bmad-output/planning-artifacts/evidence-source-matrix-v1-2026-03-27.md`:**

```markdown
# Evidence Source Matrix v1 (2026-03-27)

Version: 1.0.0
Status: current-phase
Scope: open official + synthetic data (restricted deferred)

## Current-Phase Supported Datasets

This matrix documents all datasets referenced by docs, demos, and the flagship workflow.

### Structural Data

| asset_id | name | provider | description | origin | access_mode | default_trust_status | license | redistribution_allowed | years | direct_usability | known_limitations |
|----------|------|----------|-------------|--------|-------------|---------------------|---------|----------------------|-------|-----------------|-------------------|
| fr-synthetic-2024 | French Synthetic Population 2024 | ReformLab | 100k synthetic households for France | synthetic-public | bundled | exploratory | CC-BY-4.0 | true | 2024 | true | Not calibrated against official marginals |
| insee-fideli-2021 | Fidéli (Données de cadrage) | INSEE | French demographic data sources | open-official | fetched | production-safe | Open License | true | 2021 | true | Access requires registration |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

### Exogenous Data

| asset_id | name | provider | description | origin | access_mode | ... |
|----------|------|----------|-------------|--------|-------------|-----|
| energy-price-elec-fr | Electricity Prices France | Eurostat | Monthly electricity prices by consumer | open-official | fetched | ... |
| ... | ... | ... | ... | ... | ... | ... |

### Calibration Data

| asset_id | name | provider | description | ... |
|----------|------|----------|-------------|-----|
| ev-adoption-fr | EV Adoption Rates France | ADEME | Historical EV market share by year | ... |
```

### Testing Standards

**From project-context.md:**
- Mirror source structure: `tests/data/` matches `src/reformlab/data/`
- Class-based test grouping
- Direct assertions with plain `assert`
- Fixtures in `conftest.py` for shared test data
- Error path tests use `pytest.raises(EvidenceAssetError, match=...)`

**Required test coverage:**
1. Construction with all fields (positive case)
2. Construction with minimal required fields (defaults work)
3. JSON round-trip (to_json → from_json → equality)
4. Invalid literal values raise `EvidenceAssetError`
5. Missing required fields raise `EvidenceAssetError`
6. Frozen immutability (raises `FrozenInstanceError` on mutation)
7. Edge cases: empty strings, None handling, special characters

**Quality checks before marking story done:**
```bash
uv run ruff check src/reformlab/data/
uv run mypy src/reformlab/data/
uv run pytest tests/data/test_data_asset_descriptor.py -v
```

### EPIC-20 Coordination Notes

**Frontend origin tags (Story 20.4):** The current frontend uses `origin: "built-in" | "generated" | "uploaded"` in `PopulationLibraryItem` ([Source: frontend/src/api/types.ts:475]). Story 21.2 will replace these with the canonical `origin`/`access_mode`/`trust_status` contracts. Do NOT change frontend types in this story.

**Population metadata (Story 20.7):** The current `PopulationLibraryItem` API response includes `origin`, `column_count`, `created_date`. Story 21.2 will add `access_mode` and `trust_status` to match the new contract.

### References

**Primary source documents:**
- [synthetic-data-decision-document-2026-03-23.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/synthetic-data-decision-document-2026-03-23.md) — Sections 2, 3, 7 for evidence taxonomy and classification axes
- [epic-21-trust-governed-open-synthetic-evidence-foundation.md](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/epic-21-trust-governed-open-synthetic-evidence-foundation.md) — Story 21.1 notes and epic context
- [prd.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/prd.md) — Data Governance & Privacy section (NFR11-NFR13)

**Code patterns to follow:**
- [src/reformlab/data/descriptor.py](/Users/lucas/Workspace/reformlab/src/reformlab/data/descriptor.py) — Existing `DatasetDescriptor` pattern
- [src/reformlab/data/pipeline.py](/Users/lucas/Workspace/reformlab/src/reformlab/data/pipeline.py) — `DataSourceMetadata`, `DatasetManifest` patterns
- [src/reformlab/governance/manifest.py](/Users/lucas/Workspace/reformlab/src/reformlab/governance/manifest.py) — Frozen dataclass with validation
- [src/reformlab/governance/errors.py](/Users/lucas/Workspace/reformlab/src/reformlab/governance/errors.py) — Error type pattern
- [tests/data/test_pipeline.py](/Users/lucas/Workspace/reformlab/tests/data/test_pipeline.py) — Test class structure
- [src/reformlab/server/models.py](/Users/lucas/Workspace/reformlab/src/reformlab/server/models.py) — Pydantic model patterns for future API integration (Story 21.2)

**Project context:**
- [docs/project-context.md](/Users/lucas/Workspace/reformlab/docs/project-context.md) — Critical rules for language rules, framework rules, testing rules
- [_bmad-output/project-context.md](/Users/lucas/Workspace/reformlab/_bmad-output/project-context.md) — Technology stack, architecture patterns

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None (story creation)

### Completion Notes List

- Story 21.1 is a pure backend type definition + documentation story
- No API changes in this story (deferred to Story 21.2)
- No UI changes in this story (deferred to Story 21.2 and 21.4)
- Foundation for Epic 21: all other stories depend on the `DataAssetDescriptor` contract
- Source matrix is living documentation to be updated as new datasets are added

### File List

**New files to create:**
- `src/reformlab/data/errors.py`
- `_bmad-output/planning-artifacts/evidence-source-matrix-v1-2026-03-27.md`
- `tests/data/test_data_asset_descriptor.py`

**Files to modify:**
- `src/reformlab/data/descriptor.py` — add `DataAssetDescriptor` and Literal types
- `src/reformlab/data/__init__.py` — export new types
- `tests/data/__init__.py` — no changes needed

**Files to read for context (already analyzed):**
- `src/reformlab/data/pipeline.py`
- `src/reformlab/governance/manifest.py`
- `src/reformlab/governance/errors.py`
- `tests/data/test_pipeline.py`
- `src/reformlab/server/models.py`
- `frontend/src/api/types.ts`
