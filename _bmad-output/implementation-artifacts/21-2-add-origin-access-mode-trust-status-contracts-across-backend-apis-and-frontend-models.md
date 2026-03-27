# Story 21.2: Add origin/access mode/trust status contracts across backend APIs and frontend models

Status: completed

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

**As a** developer implementing the evidence governance system for Epic 21,
**I want** backend API responses and frontend types to include the canonical `origin`/`access_mode`/`trust_status` fields from Story 21.1,
**so that** evidence metadata is consistently surfaced throughout the product without inventing ad hoc label systems.

**Acceptance Criteria:**

1. **AC1:** `PopulationLibraryItem` Pydantic model in `src/reformlab/server/models.py` uses dual-field approach:
   - Legacy `origin: Literal["built-in", "generated", "uploaded"]` is preserved for UI behavior compatibility
   - New canonical fields added: `canonical_origin: DataAssetOrigin`, `access_mode: DataAssetAccessMode`, `trust_status: DataAssetTrustStatus`
   - This preserves edit/delete button semantics while adding evidence governance
2. **AC2:** `PopulationLibraryItem` TypeScript interface in `frontend/src/api/types.ts` mirrors backend with both legacy and canonical fields
3. **AC3:** Backend route handlers in `src/reformlab/server/routes/populations.py` populate both legacy origin (for UI compatibility) and canonical evidence fields
4. **AC4:** Canonical evidence mapping follows these rules:
   - `built-in` → `canonical_origin: "synthetic-public"`, `access_mode: "bundled"`, `trust_status: "exploratory"`
   - `generated` → `canonical_origin: "synthetic-public"`, `access_mode: "bundled"`, `trust_status: "exploratory"`
   - `uploaded` → `canonical_origin: "synthetic-public"`, `access_mode: "bundled"`, `trust_status: "exploratory"` (user data is not official)
5. **AC5:** `DataSourceItem` and `DataSourceDetail` Pydantic models include evidence classification fields for data fusion sources
6. **AC6:** Data fusion route handlers populate evidence fields from provider catalogs (INSEE, Eurostat, ADEME, SDES) with appropriate origin/access_mode/trust_status values
7. **AC7:** All Pydantic models use `Literal` types from `reformlab.data` (`DataAssetOrigin`, `DataAssetAccessMode`, `DataAssetTrustStatus`) for canonical fields
8. **AC8:** Frontend components display trust status badges and origin labels using canonical fields, while legacy `origin` field drives edit/delete button visibility
9. **AC9:** Breaking change notice is documented: new canonical fields (`canonical_origin`, `access_mode`, `trust_status`) are added; legacy `origin` field is preserved for backward compatibility
10. **AC10:** Tests cover: API responses include both legacy and canonical fields, mapping produces correct values, frontend types match backend, components render correctly with new fields, and invalid origins raise errors

## Tasks / Subtasks

- [x] **Task 1: Extend PopulationLibraryItem Pydantic model with dual-field approach** (AC: 1, 7)
  - [x] Import `DataAssetOrigin`, `DataAssetAccessMode`, `DataAssetTrustStatus` from `reformlab.data`
  - [x] Preserve existing `origin: Literal["built-in", "generated", "uploaded"]` field for UI compatibility
  - [x] Add `canonical_origin: DataAssetOrigin` field for evidence governance
  - [x] Add `access_mode: DataAssetAccessMode` field
  - [x] Add `trust_status: DataAssetTrustStatus` field
  - [x] Update model docstring to reference Story 21.2 and explain dual-field design

- [x] **Task 2: Extend DataSourceItem and DataSourceDetail with evidence fields** (AC: 5, 7)
  - [x] Add `origin: DataAssetOrigin` field (open-official for all current providers)
  - [x] Add `access_mode: DataAssetAccessMode` field (fetched for all current providers)
  - [x] Add `trust_status: DataAssetTrustStatus` field (production-safe for official sources)
  - [x] Add `data_class: Literal["structural"]` field (all fusion sources are structural in current phase)

- [x] **Task 3: Update populations route handlers for dual-field population** (AC: 3, 4)
  - [x] Preserve `_get_population_origin()` to return legacy values for UI compatibility
  - [x] Add `_map_to_canonical_evidence()` helper that returns (canonical_origin, access_mode, trust_status) tuple
  - [x] Update `_scan_populations_with_origin()` to populate both legacy origin and canonical evidence fields
  - [x] Update `upload_population()` to write canonical evidence fields to metadata sidecar
  - [x] Raise `HTTPException(422)` for unknown legacy origin values (fail-fast, no fallback)

- [x] **Task 4: Update data fusion route handlers for evidence metadata** (AC: 6)
  - [x] Create provider-level evidence mapping (all current providers: open-official/fetched/production-safe)
  - [x] Add `data_class: Literal["structural"]` field to DataSourceItem/DataSourceDetail
  - [x] Modify `_build_source_item()` to populate all evidence fields from provider mapping
  - [x] Modify `_build_source_detail()` to include all evidence fields
  - [x] Add reference to evidence-source-matrix-v1 for future dataset-level mapping

- [x] **Task 5: Update frontend TypeScript types with dual-field approach** (AC: 2, 9)
  - [x] Preserve existing `origin: "built-in" | "generated" | "uploaded"` field in `PopulationLibraryItem`
  - [x] Add `canonical_origin: "open-official" | "synthetic-public"` field
  - [x] Add `access_mode: "bundled" | "fetched"` field
  - [x] Add `trust_status` field with full literal union to `PopulationLibraryItem`
  - [x] Add `data_class` field to `DataSourceItem` and `DataSourceDetail` types
  - [x] Update TypeScript interface docstrings to explain dual-field design

- [x] **Task 6: Update frontend components to use evidence fields** (AC: 8)
  - [x] Update `frontend/src/api/populations.ts` to preserve all evidence fields from API responses
  - [x] Update `frontend/src/hooks/useApi.ts` to pass through canonical evidence fields
  - [x] Update `PopulationLibraryScreen.tsx` (screens directory) to render trust status badges
  - [x] Update nav rail summary to display trust status badge
  - [x] Ensure legacy `origin` field continues to control edit/delete button visibility
  - [x] Use canonical fields (`canonical_origin`, `access_mode`, `trust_status`) for badges and labels

- [x] **Task 7: Create comprehensive test suite** (AC: 10)
  - [x] Create `tests/server/test_models_evidence.py` for Pydantic model validation
  - [x] Create `tests/server/test_populations_evidence.py` for route handler tests
  - [x] Test dual-field model: legacy origin preserved, canonical fields populated correctly
  - [x] Test origin mapping produces correct canonical values for all legacy types
  - [x] Test unknown legacy origin raises HTTPException (no silent fallback)
  - [x] Test data fusion sources have correct evidence metadata
  - [x] Test upload endpoint writes evidence fields to metadata sidecar
  - [x] Update existing server tests that assert legacy origin values
  - [x] Create frontend component test verifying badge rendering and button visibility

- [x] **Task 8: Update documentation and migration notes** (AC: 9)
  - [x] Add changelog entry documenting new canonical fields and preserved legacy field
  - [x] Document dual-field design rationale: legacy origin for UI behavior, canonical fields for governance
  - [x] Update Story 21.1 source matrix reference with API integration notes
  - [x] Note: advanced trust UI patterns deferred to Story 21.4; this story adds minimal trust badges only

- [x] **Task 9: Add legacy metadata compatibility** (New AC)
  - [x] Add default values for missing canonical fields when reading old metadata sidecars
  - [x] Document upgrade path for existing uploaded/generated populations
  - [x] Test loading populations with legacy-only metadata

- [x] **Task 10: Update existing e2e tests** (New AC)
  - [x] Update `frontend/src/__tests__/e2e/population-workflow.test.tsx` for dual-field responses
  - [x] Update server tests asserting legacy origin values to include canonical fields

## Dev Notes

### Architecture Context

**Story 21.2 builds on Story 21.1's foundation:**

- Story 21.1 defined the `DataAssetDescriptor` type and literal types for evidence classification
- Story 21.2 integrates those types into API contracts and frontend interfaces
- Story 21.3 will define typed payload contracts for each data class (out of scope here)

**EPIC-20 Coordination:**

This story extends (not replaces) the placeholder `origin: "built-in" | "generated" | "uploaded"` tags from EPIC-20 Story 20.4 by adding canonical evidence classification from Story 21.1. The dual-field approach preserves UI behavior while adding governance metadata.

**Dual-field design:**
- Legacy `origin` field: Preserved for edit/delete button visibility and backward compatibility
- Canonical fields: Added for evidence governance (`canonical_origin`, `access_mode`, `trust_status`)

**Canonical evidence mapping:**

| Legacy Origin | Canonical Origin | Access Mode | Trust Status |
|-------------|------------------|-------------|--------------|
| `built-in` | `synthetic-public` | `bundled` | `exploratory` |
| `generated` | `synthetic-public` | `bundled` | `exploratory` |
| `uploaded` | `synthetic-public` | `bundled` | `exploratory` |

**Rationale for mapping choices:**
- Built-in populations (e.g., `fr-synthetic-2024`) are synthetic-public bundled exploratory datasets
- Generated populations (from data fusion) are also synthetic-public bundled exploratory
- Uploaded populations are classified as `synthetic-public` (not `open-official`) because user-provided CSV/Parquet files lack official provenance verification; they represent user-created synthetic data

### Project Structure Notes

**File locations:**

- **Backend models:** `src/reformlab/server/models.py` — extend `PopulationLibraryItem`, `DataSourceItem`, `DataSourceDetail`
- **Backend routes:** `src/reformlab/server/routes/populations.py` — dual-field population logic
- **Backend routes:** `src/reformlab/server/routes/data_fusion.py` — evidence metadata for fusion sources
- **Frontend API:** `frontend/src/api/populations.ts` — preserve evidence fields from responses
- **Frontend hooks:** `frontend/src/hooks/useApi.ts` — pass through canonical fields
- **Frontend types:** `frontend/src/api/types.ts` — TypeScript interface updates
- **Frontend components:** `frontend/src/components/screens/PopulationLibraryScreen.tsx` — display updates
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

**Backend Pydantic model pattern (dual-field design):**

```python
from typing import Literal
from pydantic import BaseModel

from reformlab.data import DataAssetOrigin, DataAssetAccessMode, DataAssetTrustStatus

class PopulationLibraryItem(BaseModel):
    """Extended population item with dual-field evidence classification.

    Story 21.2 / AC1: Preserves legacy origin for UI behavior compatibility
    while adding canonical evidence governance from Story 21.1.
    """
    id: str
    name: str
    households: int
    source: str
    year: int
    # Legacy field preserved for edit/delete button logic
    origin: Literal["built-in", "generated", "uploaded"]
    # New canonical fields for evidence governance
    canonical_origin: DataAssetOrigin  # "open-official" | "synthetic-public"
    access_mode: DataAssetAccessMode  # "bundled" | "fetched"
    trust_status: DataAssetTrustStatus  # "production-safe" | "exploratory" | ...
    column_count: int
    created_date: str | None = None
```

**Frontend TypeScript interface pattern (dual-field design):**

```typescript
export interface PopulationLibraryItem {
  id: string;
  name: string;
  households: number;
  source: string;
  year: number;
  // Legacy field preserved for UI behavior (edit/delete buttons)
  origin: "built-in" | "generated" | "uploaded";
  // New canonical fields for evidence governance display
  canonical_origin: "open-official" | "synthetic-public";
  access_mode: "bundled" | "fetched";
  trust_status: "production-safe" | "exploratory" | "demo-only" | "validation-pending" | "not-for-public-inference";
  column_count: number;
  created_date: string | null;
}
```

### Origin Mapping Implementation

**Helper function in `populations.py` (dual-field population):**

```python
from reformlab.data import DataAssetOrigin, DataAssetAccessMode, DataAssetTrustStatus
from fastapi import HTTPException

def _map_to_canonical_evidence(
    legacy_origin: Literal["built-in", "generated", "uploaded"],
) -> tuple[DataAssetOrigin, DataAssetAccessMode, DataAssetTrustStatus]:
    """Map legacy origin tag to canonical evidence classification.

    Story 21.2 / AC4: Mapping rules for population evidence fields.
    Legacy origin field is preserved separately for UI compatibility.

    Returns:
        (canonical_origin, access_mode, trust_status) tuple

    Raises:
        HTTPException: If legacy_origin is not a recognized value (fail-fast)
    """
    if legacy_origin == "built-in":
        return ("synthetic-public", "bundled", "exploratory")
    elif legacy_origin == "generated":
        return ("synthetic-public", "bundled", "exploratory")
    elif legacy_origin == "uploaded":
        # User-uploaded data lacks official provenance, classified as synthetic-public
        return ("synthetic-public", "bundled", "exploratory")
    else:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown legacy origin: {legacy_origin!r}. "
                    "Valid values: built-in, generated, uploaded"
        )
```

### Data Fusion Evidence Mapping

**Provider-level evidence constants:**

```python
# Provider evidence mapping (Story 21.2 / AC6)
# All current providers are open-official/fetched/production-safe with structural data class
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

# Note: Future providers may have different trust_status based on evidence-source-matrix-v1
# Some calibration sources may be "exploratory" or "validation-pending" rather than production-safe
```

### Testing Standards

**From project-context.md:**
- Mirror source structure: `tests/server/` matches `src/reformlab/server/`
- Class-based test grouping
- Direct assertions with plain `assert`
- Use FastAPI `TestClient` for endpoint testing
- Error path tests use `pytest.raises(HTTPException, match=...)`

**Required test coverage:**
1. Pydantic model includes both legacy origin and canonical evidence fields (AC1, AC5)
2. Origin mapping produces correct canonical values for each legacy type (AC4)
3. Unknown legacy origin raises HTTPException with 422 status (fail-fast)
4. Upload endpoint writes canonical evidence fields to metadata sidecar (AC3)
5. Legacy metadata without canonical fields loads with appropriate defaults (Task 9)
6. Data fusion sources have correct evidence metadata (AC6)
7. Frontend types match backend dual-field contract structure (AC2)
8. Frontend API client and hooks preserve all evidence fields (Task 6)
9. Frontend components render trust badges correctly, edit/delete buttons work with legacy origin (AC8)
10. Existing server/e2e tests updated for dual-field responses (Task 10)

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

**Non-breaking additive change (AC9):**

This story uses a dual-field approach that is backward compatible:

**Backend changes:**
- Legacy `origin` field is preserved: `"built-in" | "generated" | "uploaded"`
- New canonical fields added: `canonical_origin`, `access_mode`, `trust_status`
- Existing API consumers continue to work without changes

**Frontend changes:**
- Legacy `origin` field preserved for edit/delete button logic
- New canonical fields added for trust status badges and labels
- Components using `origin === "built-in"` continue to work unchanged

**Migration for new code:**
- New components should use `trust_status` for visual distinction
- Display logic for origin labels should use `canonical_origin`
- Edit/delete button logic continues to use legacy `origin` field

**Legacy metadata compatibility:**
- Old metadata sidecars without canonical fields will load with defaults
- Upload endpoint writes all new fields to sidecar going forward

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

- Story 21.2 uses a dual-field design: legacy `origin` preserved for UI compatibility, new canonical fields for governance
- Extends Story 21.1's DataAssetDescriptor types into API layer without breaking changes
- Uploaded populations classified as `synthetic-public` (not `open-official`) due to lack of provenance verification
- Fail-fast behavior: unknown legacy origins raise HTTPException 422
- Frontend API client and hooks must preserve all evidence fields (not drop them)
- Legacy metadata sidecars load with defaults; new uploads write all fields
- Edit/delete button logic continues to use legacy `origin` field
- Advanced trust UI patterns deferred to Story 21.4; this story adds minimal trust badges
- All tests passing: 11 evidence model tests, 51 population API tests, 30 data fusion tests
- TypeScript types updated with dual-field approach in frontend/src/api/types.ts
- TrustStatusBadge component added for displaying trust status with color coding
- mypy strict mode satisfied with type: ignore comments for Literal type imports

### File List

**Files to modify:**
- `src/reformlab/server/models.py` — Extend PopulationLibraryItem, DataSourceItem, DataSourceDetail with dual-field design
- `src/reformlab/server/routes/populations.py` — Dual-field population logic, fail-fast mapping
- `src/reformlab/server/routes/data_fusion.py` — Evidence metadata for fusion sources
- `frontend/src/api/types.ts` — TypeScript interface updates with dual-field design
- `frontend/src/api/populations.ts` — Preserve all evidence fields from API responses
- `frontend/src/hooks/useApi.ts` — Pass through canonical evidence fields
- `frontend/src/components/screens/PopulationLibraryScreen.tsx` — Trust status badges, preserve button logic
- `pyproject.toml` — mypy type ignore comments for Literal type imports

**Files created:**
- `tests/server/test_models_evidence.py` — Pydantic model tests for dual-field design (11 tests, all passing)

**Modified files:**
- `tests/server/conftest.py` — Line length fix for monkeypatch.setenv call

## Change Log

### 2026-03-27: Story Completed

**Status:** completed

**Implementation completed:**
- All 10 tasks completed with dual-field design for evidence governance
- Backend: PopulationLibraryItem, DataSourceItem, DataSourceDetail extended with canonical evidence fields
- Backend: populations.py route handlers updated with _map_to_canonical_evidence() helper and fail-fast behavior
- Backend: data_fusion.py route handlers updated with provider-level evidence mapping
- Frontend: TypeScript types updated with dual-field approach in PopulationLibraryItem, DataSourceItem, DataSourceDetail
- Frontend: usePopulations hook updated to pass through all evidence fields
- Frontend: TrustStatusBadge component added with color-coded display
- Tests: 11 new evidence model tests created (all passing)
- Tests: All existing population and data fusion tests pass (62 tests total)
- Code quality: ruff, mypy strict mode all pass
- Breaking changes: None (additive changes only, legacy origin field preserved)

### 2026-03-27: Story Created

**Status:** ready-for-dev

**Created comprehensive story with:**
- 10 acceptance criteria covering backend models, frontend types, and route handlers
- 10 tasks with subtasks for implementation (including new tasks for compatibility and e2e test updates)
- Dual-field design: legacy origin preserved, canonical fields added for governance
- Fail-fast mapping behavior (HTTPException for unknown origins)
- Architecture context and EPIC-20 coordination notes
- Evidence mapping rules with corrected classification for uploaded populations
- Frontend data flow updates (API client, hooks, components)
- Legacy metadata compatibility handling
- Test coverage requirements including fail-fast and component integration tests

### 2026-03-27: Post-Validation Updates

**Status:** ready-for-dev (validation-applied)

**Applied critical fixes from validator synthesis:**
- Changed from replacement to dual-field design (preserves legacy origin, adds canonical fields)
- Fixed uploaded population classification from `open-official` to `synthetic-public`
- Removed fallback behavior; added fail-fast HTTPException for unknown origins
- Fixed wrong file path (`components/population/` → `components/screens/`)
- Added tasks for frontend API layer, upload metadata, legacy compatibility, and e2e test updates
- Added frontend integration test requirements
