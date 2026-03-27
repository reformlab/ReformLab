# Story 21.2: Add origin/access mode/trust status contracts across backend APIs and frontend models

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

**As a** developer implementing the evidence governance system for Epic 21,
**I want** backend API responses and frontend types to include the canonical `origin`/`access_mode`/`trust_status` fields from Story 21.1,
**so that** evidence metadata is consistently surfaced throughout the product without inventing ad hoc label systems.

**Acceptance Criteria:**

1. **AC1:** `PopulationLibraryItem` Pydantic model in `src/reformlab/server/models.py` includes new fields:
   - `origin: Literal["open-official", "synthetic-public"]` (replaces `Literal["built-in", "generated", "uploaded"]`)
   - `access_mode: Literal["bundled", "fetched"]`
   - `trust_status: Literal["production-safe", "exploratory", "demo-only", "validation-pending", "not-for-public-inference"]`
2. **AC2:** `PopulationLibraryItem` TypeScript interface in `frontend/src/api/types.ts` mirrors the new backend contract with the same field names and literal types
3. **AC3:** Backend route handlers in `src/reformlab/server/routes/populations.py` map legacy origin detection (`built-in`/`generated`/`uploaded`) to canonical origin/access_mode/trust_status values
4. **AC4:** Origin mapping logic follows these rules:
   - `built-in` → `origin: "synthetic-public"`, `access_mode: "bundled"`, `trust_status: "exploratory"` (for bundled synthetic populations)
   - `generated` → `origin: "synthetic-public"`, `access_mode: "bundled"`, `trust_status: "exploratory"` (for data fusion generated populations)
   - `uploaded` → `origin: "open-official"`, `access_mode: "bundled"`, `trust_status: "exploratory"` (for user-uploaded data, treated as observed)
5. **AC5:** `DataSourceItem` and `DataSourceDetail` Pydantic models include evidence classification fields for data fusion sources
6. **AC6:** Data fusion route handlers populate evidence fields from provider catalogs (INSEE, Eurostat, ADEME, SDES) with appropriate origin/access_mode/trust_status values
7. **AC7:** All Pydantic models use `Literal` types from `reformlab.data` (imported from `src/reformlab/data/__init__.py`) rather than duplicating string values
8. **AC8:** Frontend components that display population metadata use the new fields for rendering trust status indicators and origin badges
9. **AC9:** Breaking change notice is documented: old `origin` values (`"built-in"`, `"generated"`, `"uploaded"`) are replaced by canonical values, and new fields (`access_mode`, `trust_status`) are added
10. **AC10:** Tests cover: API response models include new fields, origin mapping produces correct canonical values, frontend types match backend contracts, and error handling for invalid origin values

## Tasks / Subtasks

- [ ] **Task 1: Extend PopulationLibraryItem Pydantic model with evidence fields** (AC: 1, 7)
  - [ ] Import `DataAssetOrigin`, `DataAssetAccessMode`, `DataAssetTrustStatus` from `reformlab.data`
  - [ ] Replace `origin: Literal["built-in", "generated", "uploaded"]` with `origin: DataAssetOrigin` (narrowed to current-phase values)
  - [ ] Add `access_mode: DataAssetAccessMode` field
  - [ ] Add `trust_status: DataAssetTrustStatus` field
  - [ ] Update model docstring to reference Story 21.2 and evidence source matrix

- [ ] **Task 2: Extend DataSourceItem and DataSourceDetail with evidence fields** (AC: 5, 7)
  - [ ] Add `origin: DataAssetOrigin` field (open-official for all current providers)
  - [ ] Add `access_mode: DataAssetAccessMode` field (fetched for all current providers)
  - [ ] Add `trust_status: DataAssetTrustStatus` field (production-safe for official sources)
  - [ ] Add `data_class: Literal["structural"]` field (all fusion sources are structural in current phase)

- [ ] **Task 3: Update populations route handlers for origin mapping** (AC: 3, 4)
  - [ ] Modify `_get_population_origin()` to return `DataAssetOrigin` instead of legacy values
  - [ ] Add `_map_legacy_to_canonical_origin()` helper function with mapping rules
  - [ ] Add `_infer_access_mode_and_trust_status()` helper based on file location
  - [ ] Update `_scan_populations_with_origin()` to populate all three evidence fields
  - [ ] Update `upload_population()` metadata sidecar to include evidence fields

- [ ] **Task 4: Update data fusion route handlers for evidence metadata** (AC: 6)
  - [ ] Create provider-specific evidence mapping dict (INSEE, Eurostat, ADEME, SDES)
  - [ ] Modify `_build_source_item()` to populate evidence fields from catalog
  - [ ] Modify `_build_source_detail()` to include evidence fields
  - [ ] Add module-level constant for evidence source matrix reference

- [ ] **Task 5: Update frontend TypeScript types** (AC: 2, 9)
  - [ ] Replace `origin: "built-in" | "generated" | "uploaded"` with canonical origin literal in `PopulationLibraryItem`
  - [ ] Add `access_mode` field with literal type to `PopulationLibraryItem`
  - [ ] Add `trust_status` field with literal type to `PopulationLibraryItem`
  - [ ] Add `data_class` field to `DataSourceItem` and `DataSourceDetail` types
  - [ ] Update TypeScript interface docstrings with breaking change notice

- [ ] **Task 6: Update frontend components to use evidence fields** (AC: 8)
  - [ ] Update `PopulationLibraryScreen.tsx` to render trust status badges
  - [ ] Update nav rail summary to display origin/access_mode/trust_status
  - [ ] Add visual distinction for `exploratory` vs `production-safe` trust status
  - [ ] Ensure old origin-based display logic is migrated to use new fields

- [ ] **Task 7: Create comprehensive test suite** (AC: 10)
  - [ ] Create `tests/server/test_models_evidence.py` for Pydantic model validation
  - [ ] Create `tests/server/test_populations_evidence.py` for route handler tests
  - [ ] Test origin mapping produces correct canonical values for all legacy types
  - [ ] Test data fusion sources have correct evidence metadata
  - [ ] Test frontend types match backend contract structure

- [ ] **Task 8: Update documentation and migration notes** (AC: 9)
  - [ ] Document breaking change in `CHANGELOG.md` or migration guide
  - [ ] Update Story 21.1 source matrix reference with API integration notes
  - [ ] Add story note: frontend trust UI patterns are deferred to Story 21.4

## Dev Notes

### Architecture Context

**Story 21.2 builds on Story 21.1's foundation:**

- Story 21.1 defined the `DataAssetDescriptor` type and literal types for evidence classification
- Story 21.2 integrates those types into API contracts and frontend interfaces
- Story 21.3 will define typed payload contracts for each data class (out of scope here)

**EPIC-20 Coordination:**

This story replaces the placeholder `origin: "built-in" | "generated" | "uploaded"` tags from EPIC-20 Story 20.4 with the canonical evidence classification from Story 21.1. The mapping from legacy to canonical values is:

| Legacy Origin | Canonical Origin | Access Mode | Trust Status |
|-------------|------------------|-------------|--------------|
| `built-in` | `synthetic-public` | `bundled` | `exploratory` |
| `generated` | `synthetic-public` | `bundled` | `exploratory` |
| `uploaded` | `open-official` | `bundled` | `exploratory` |

**Rationale for mapping choices:**
- Built-in populations (e.g., `fr-synthetic-2024`) are synthetic-public bundled exploratory datasets
- Generated populations (from data fusion) are also synthetic-public bundled exploratory
- Uploaded populations are treated as open-official because they represent user-provided observed data, even if not from an official source

### Project Structure Notes

**File locations:**

- **Backend models:** `src/reformlab/server/models.py` — extend `PopulationLibraryItem`, `DataSourceItem`, `DataSourceDetail`
- **Backend routes:** `src/reformlab/server/routes/populations.py` — origin mapping logic
- **Backend routes:** `src/reformlab/server/routes/data_fusion.py` — evidence metadata for fusion sources
- **Frontend types:** `frontend/src/api/types.ts` — TypeScript interface updates
- **Frontend components:** `frontend/src/components/population/PopulationLibraryScreen.tsx` — display updates
- **Tests:** `tests/server/test_models_evidence.py`, `tests/server/test_populations_evidence.py`

**Imports from Story 21.1:**

```python
from reformlab.data import (
    DataAssetOrigin,
    DataAssetAccessMode,
    DataAssetTrustStatus,
    DataAssetClass,
)
```

### Type System Constraints

**Backend Pydantic model pattern:**

```python
from typing import Literal
from pydantic import BaseModel

from reformlab.data import DataAssetOrigin, DataAssetAccessMode, DataAssetTrustStatus

class PopulationLibraryItem(BaseModel):
    """Extended population item with canonical evidence classification.

    Story 21.2 / AC1: Replaces legacy origin tags with evidence governance
    contract from Story 21.1.
    """
    id: str
    name: str
    households: int
    source: str
    year: int
    origin: DataAssetOrigin  # "open-official" | "synthetic-public"
    access_mode: DataAssetAccessMode  # "bundled" | "fetched"
    trust_status: DataAssetTrustStatus  # "production-safe" | "exploratory" | ...
    column_count: int
    created_date: str | None = None
```

**Frontend TypeScript interface pattern:**

```typescript
export interface PopulationLibraryItem {
  id: string;
  name: string;
  households: number;
  source: string;
  year: number;
  origin: "open-official" | "synthetic-public";
  access_mode: "bundled" | "fetched";
  trust_status: "production-safe" | "exploratory" | "demo-only" | "validation-pending" | "not-for-public-inference";
  column_count: number;
  created_date: string | null;
}
```

### Origin Mapping Implementation

**Helper function in `populations.py`:**

```python
from reformlab.data import DataAssetOrigin, DataAssetAccessMode, DataAssetTrustStatus

def _map_legacy_origin_to_canonical(
    legacy_origin: Literal["built-in", "generated", "uploaded"],
) -> tuple[DataAssetOrigin, DataAssetAccessMode, DataAssetTrustStatus]:
    """Map legacy origin tag to canonical evidence classification.

    Story 21.2 / AC4: Mapping rules for legacy origin values.

    Returns:
        (origin, access_mode, trust_status) tuple
    """
    if legacy_origin == "built-in":
        return ("synthetic-public", "bundled", "exploratory")
    elif legacy_origin == "generated":
        return ("synthetic-public", "bundled", "exploratory")
    elif legacy_origin == "uploaded":
        return ("open-official", "bundled", "exploratory")
    else:
        # Fallback for unknown origins
        return ("synthetic-public", "bundled", "demo-only")
```

### Data Fusion Evidence Mapping

**Provider-specific evidence constants:**

```python
# Provider evidence mapping (Story 21.2 / AC6)
_PROVIDER_EVIDENCE: dict[str, dict[str, str]] = {
    "insee": {
        "origin": "open-official",
        "access_mode": "fetched",
        "trust_status": "production-safe",
        "data_class": "structural",
    },
    "eurostat": {
        "origin": "open-official",
        "access_mode": "fetched",
        "trust_status": "production-safe",
        "data_class": "structural",
    },
    "ademe": {
        "origin": "open-official",
        "access_mode": "fetched",
        "trust_status": "production-safe",
        "data_class": "structural",
    },
    "sdes": {
        "origin": "open-official",
        "access_mode": "fetched",
        "trust_status": "production-safe",
        "data_class": "structural",
    },
}
```

### Testing Standards

**From project-context.md:**
- Mirror source structure: `tests/server/` matches `src/reformlab/server/`
- Class-based test grouping
- Direct assertions with plain `assert`
- Use FastAPI `TestClient` for endpoint testing
- Error path tests use `pytest.raises(HTTPException, match=...)`

**Required test coverage:**
1. Pydantic model includes all three evidence fields (AC1, AC5)
2. Origin mapping produces correct canonical values for each legacy type (AC4)
3. Data fusion sources have correct evidence metadata (AC6)
4. Frontend types match backend contract structure (AC2)
5. API responses serialize evidence fields correctly (AC10)

**Example test structure:**

```python
class TestPopulationEvidenceMapping:
    """Tests for legacy origin to canonical evidence mapping.

    Story 21.2 / AC4: Mapping rules for population origins.
    """

    def test_builtin_population_maps_to_synthetic_public(self) -> None:
        """Given built-in origin, when mapped, returns synthetic-public."""
        origin, access_mode, trust = _map_legacy_origin_to_canonical("built-in")
        assert origin == "synthetic-public"
        assert access_mode == "bundled"
        assert trust == "exploratory"
```

### Frontend Component Updates

**Trust status badge component (to be added in Story 21.4):**

For this story, use simple conditional rendering based on `trust_status` field:

```typescript
// Simple trust status badge (Story 21.2)
const getTrustStatusBadge = (trustStatus: string) => {
  switch (trustStatus) {
    case "production-safe":
      return <Badge className="bg-green-100 text-green-800">Production-Safe</Badge>;
    case "exploratory":
      return <Badge className="bg-yellow-100 text-yellow-800">Exploratory</Badge>;
    case "demo-only":
      return <Badge className="bg-gray-100 text-gray-800">Demo Only</Badge>;
    default:
      return <Badge variant="outline">{trustStatus}</Badge>;
  }
};
```

### Breaking Changes and Migration

**Frontend breaking change (AC9):**

The `origin` field type changes from:
```typescript
origin: "built-in" | "generated" | "uploaded"
```

To:
```typescript
origin: "open-official" | "synthetic-public"
access_mode: "bundled" | "fetched"
trust_status: "production-safe" | "exploratory" | "demo-only" | "validation-pending" | "not-for-public-inference"
```

**Migration path for existing code:**
- Components using `origin === "built-in"` should check `origin === "synthetic-public"`
- Components displaying origin badges should use `trust_status` for visual distinction
- The old three-way origin distinction is now captured by the combination of `origin` + `access_mode` + `trust_status`

### EPIC-20 Coordination Notes

**Population Library (Story 20.4):** The `PopulationLibraryItem` type already exists with legacy origin field. This story updates that type to use canonical evidence classification.

**Engine Validation (Story 20.5):** Preflight checks may need to be aware of trust status in future stories (Story 21.5), but this story only adds the fields to API responses.

**Results/Compare (Story 20.6):** Result metadata may include evidence classification in future stories, but this story focuses on population and data source responses only.

### References

**Primary source documents:**
- [synthetic-data-decision-document-2026-03-23.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/synthetic-data-decision-document-2026-03-23.md) — Sections 2, 3 for evidence taxonomy
- [evidence-source-matrix-v1-2026-03-27.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/evidence-source-matrix-v1-2026-03-27.md) — Current-phase dataset evidence classifications
- [epic-21-trust-governed-open-synthetic-evidence-foundation.md](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/epic-21-trust-governed-open-synthetic-evidence-foundation.md) — Story 21.2 notes and epic context
- [Story 21.1](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-1-implement-canonical-evidence-asset-descriptor-and-current-phase-source-matrix.md) — DataAssetDescriptor and literal type definitions

**Code patterns to follow:**
- [src/reformlab/data/descriptor.py](/Users/lucas/Workspace/reformlab/src/reformlab/data/descriptor.py) — Literal type definitions (Story 21.1)
- [src/reformlab/server/models.py](/Users/lucas/Workspace/reformlab/src/reformlab/server/models.py) — Existing Pydantic model patterns
- [src/reformlab/server/routes/populations.py](/Users/lucas/Workspace/reformlab/src/reformlab/server/routes/populations.py) — Population route handlers
- [src/reformlab/server/routes/data_fusion.py](/Users/lucas/Workspace/reformlab/src/reformlab/server/routes/data_fusion.py) — Data fusion route handlers
- [frontend/src/api/types.ts](/Users/lucas/Workspace/reformlab/frontend/src/api/types.ts) — Frontend type definitions

**Project context:**
- [docs/project-context.md](/Users/lucas/Workspace/reformlab/docs/project-context.md) — Critical rules for language rules, framework rules, testing rules
- [_bmad-output/project-context.md](/Users/lucas/Workspace/reformlab/_bmad-output/project-context.md) — Technology stack, architecture patterns

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None (story creation)

### Completion Notes List

- Story 21.2 is an API contract and frontend type update story
- Extends Story 21.1's DataAssetDescriptor types into API layer
- Replaces EPIC-20's placeholder origin tags with canonical evidence classification
- No changes to data layer types or domain logic (those come in Story 21.3)
- Frontend trust UI patterns are deferred to Story 21.4

### File List

**Files to modify:**
- `src/reformlab/server/models.py` — Extend PopulationLibraryItem, DataSourceItem, DataSourceDetail
- `src/reformlab/server/routes/populations.py` — Origin mapping logic
- `src/reformlab/server/routes/data_fusion.py` — Evidence metadata for fusion sources
- `frontend/src/api/types.ts` — TypeScript interface updates
- `frontend/src/components/population/PopulationLibraryScreen.tsx` — Display updates

**Files to create:**
- `tests/server/test_models_evidence.py` — Pydantic model tests
- `tests/server/test_populations_evidence.py` — Route handler tests
- `tests/server/test_data_fusion_evidence.py` — Data fusion evidence tests

## Change Log

### 2026-03-27: Story Created

**Status:** ready-for-dev

**Created comprehensive story with:**
- 10 acceptance criteria covering backend models, frontend types, and route handlers
- 8 tasks with subtasks for implementation
- Architecture context and EPIC-20 coordination notes
- Origin mapping rules and rationale
- Data fusion evidence mapping patterns
- Breaking change documentation
- Test coverage requirements
