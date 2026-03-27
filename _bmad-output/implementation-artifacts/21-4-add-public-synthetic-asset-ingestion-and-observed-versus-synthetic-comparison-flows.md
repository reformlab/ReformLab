# Story 21.4: Add public synthetic asset ingestion and observed-versus-synthetic comparison flows

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

**As a** policy analyst comparing different data sources,
**I want** to ingest public synthetic datasets through the same framework as observed data and run explicit observed-versus-synthetic comparisons with visible trust labels,
**so that** I can understand how synthetic populations differ from observed data while never confusing their trust boundaries.

## Acceptance Criteria

1. **AC1:** A `SyntheticAssetRegistry` exists in `src/reformlab/data/synthetic_catalog.py` that catalogs bundled public synthetic datasets with `StructuralAsset` descriptors
2. **AC2:** Public synthetic datasets are ingested using the same `load_population_folder()` pattern as observed data, with metadata files containing `DataAssetDescriptor` JSON
3. **AC3:** An `ObservedVsSyntheticComparison` utility in `src/reformlab/data/comparison.py` computes distributional statistics comparing observed and synthetic populations (marginal means, quantiles, variance)
4. **AC4:** A new API endpoint `GET /api/populations/compare` accepts two population IDs and returns comparison metrics with visible trust labels for both
5. **AC5:** The `PopulationLibraryItem` response includes a `is_synthetic` boolean field derived from `canonical_origin` for easier UI filtering
6. **AC6:** Frontend Population Library component displays trust status badges (color-coded: exploratory=yellow, demo-only=gray, production-safe=green) and synthetic indicator badges
7. **AC7:** At least one public synthetic dataset (`fr-synthetic-2024`) is bundled with metadata file containing full `DataAssetDescriptor` with `origin="synthetic-public"`, `access_mode="bundled"`, `trust_status="exploratory"`
8. **AC8:** Comparison view shows side-by-side metrics (row count, column count, mean/median for numeric columns, distribution comparison) with clear labels distinguishing observed vs synthetic
9. **AC9:** Tests cover: synthetic asset registration, metadata ingestion, comparison computation, API endpoint, frontend component rendering
10. **AC10:** All surfaces consistently display trust labels such that synthetic and observed data are never visually indistinguishable

## Tasks / Subtasks

- [ ] **Task 1: Create synthetic asset registry** (AC: 1, 7)
  - [ ] Create `src/reformlab/data/synthetic_catalog.py`
  - [ ] Define `SyntheticAssetRegistry` class with `register()`, `get(asset_id)`, `list_all()` methods
  - [ ] Registry holds `StructuralAsset` instances for bundled synthetic populations
  - [ ] Initialize registry with `fr-synthetic-2024` entry using existing synthetic population
  - [ ] Each entry has `DataAssetDescriptor` with `origin="synthetic-public"`, `access_mode="bundled"`, `trust_status="exploratory"`

- [ ] **Task 2: Create metadata files for bundled synthetic datasets** (AC: 2, 7)
  - [ ] Create `data/populations/fr-synthetic-2024/` folder structure
  - [ ] Add `data.parquet` (generated via `src/reformlab/data/synthetic.py`)
  - [ ] Add `descriptor.json` with full `DataAssetDescriptor` JSON
  - [ ] Add `schema.json` with `DataSchema` for the synthetic population
  - [ ] Verify `load_population_folder()` successfully loads synthetic assets

- [ ] **Task 3: Implement observed-vs-synthetic comparison utility** (AC: 3, 8)
  - [ ] Create `src/reformlab/data/comparison.py`
  - [ ] Define `PopulationComparison` result frozen dataclass with fields:
    - `observed_asset_id`, `synthetic_asset_id`
    - `row_counts: dict[str, int]` (observed, synthetic)
    - `column_counts: dict[str, int]`
    - `numeric_comparison: dict[str, NumericColumnComparison]`
    - `trust_labels: dict[str, dict[str, str]]` (origin, access_mode, trust_status for both)
  - [ ] Define `NumericColumnComparison` with: `observed_mean`, `synthetic_mean`, `relative_diff_pct`, `observed_median`, `synthetic_median`, `observed_std`, `synthetic_std`
  - [ ] Implement `compare_populations(observed_table, synthetic_table, observed_descriptor, synthetic_descriptor) -> PopulationComparison`
  - [ ] Use PyArrow compute for efficient statistics (mean, median, std)

- [ ] **Task 4: Add comparison API endpoint** (AC: 4)
  - [ ] Add `GET /api/populations/compare` to `src/reformlab/server/routes/populations.py`
  - [ ] Accepts query parameters: `observed_id`, `synthetic_id`
  - [ ] Validates both populations exist, raises 404 if not
  - [ ] Loads tables via `_load_population_table()`
  - [ ] Retrieves descriptors from metadata files
  - [ ] Calls `compare_populations()` utility
  - [ ] Returns comparison result with trust labels

- [ ] **Task 5: Add server response model for comparison** (AC: 4)
  - [ ] Add `PopulationComparisonResponse` to `src/reformlab/server/models.py`
  - [ ] Include trust labels for both assets
  - [ ] Match `PopulationComparison` structure from comparison utility

- [ ] **Task 6: Extend PopulationLibraryItem with is_synthetic field** (AC: 5)
  - [ ] Add `is_synthetic: bool` computed field to `PopulationLibraryItem` in `src/reformlab/server/models.py`
  - [ ] Derived from `canonical_origin == "synthetic-public"`
  - [ ] Update `_scan_populations_with_origin()` to populate this field

- [ ] **Task 7: Frontend trust status badge component** (AC: 6)
  - [ ] Create `frontend/src/components/shared/TrustStatusBadge.tsx`
  - [ ] Props: `status: DataAssetTrustStatus`, `origin: DataAssetOrigin`
  - [ ] Color coding: `exploratory`→yellow, `demo-only`→gray, `production-safe`→green, `validation-pending`→orange, `not-for-public-inference`→red
  - [ ] Display format: badge with icon + tooltip showing full trust status

- [ ] **Task 8: Frontend synthetic indicator badge** (AC: 6)
  - [ ] Create `frontend/src/components/shared/SyntheticBadge.tsx`
  - [ ] Props: `isSynthetic: boolean`
  - [ ] Shows "SYNTHETIC" pill badge when true, "OBSERVED" when false
  - [ ] Distinct visual style (dashed border, different background)

- [ ] **Task 9: Frontend comparison view component** (AC: 8)
  - [ ] Create `frontend/src/components/population/PopulationComparisonView.tsx`
  - [ ] Props: `observedId: string`, `syntheticId: string`
  - [ ] Fetches comparison data from `/api/populations/compare`
  - [ ] Displays side-by-side metrics in card layout
  - [ ] Shows trust badges for both populations
  - [ ] Numeric column comparisons with diff highlighting (green=close, red=divergent)

- [ ] **Task 10: Integrate badges into Population Library** (AC: 6)
  - [ ] Update `frontend/src/components/population/PopulationLibrary.tsx` (or library screen)
  - [ ] Add trust status badge and synthetic indicator badges to population cards
  - [ ] Ensure badges are always visible, never collapsed

- [ ] **Task 11: Add comparison entry point to UI** (AC: 8)
  - [ ] Add "Compare" button to population library when synthetic and observed both available
  - [ ] Update AppContext to track `comparisonState: {observedId, syntheticId} | null`
  - [ ] Add route handling for comparison view

- [ ] **Task 12: Create comprehensive test suite** (AC: 9)
  - [ ] Backend tests in `tests/data/test_synthetic_catalog.py`
  - [ ] Backend tests in `tests/data/test_comparison.py`
  - [ ] API tests for `/api/populations/compare` endpoint
  - [ ] Frontend component tests for TrustStatusBadge, SyntheticBadge, PopulationComparisonView
  - [ ] Integration test: end-to-end comparison flow

- [ ] **Task 13: Add TypeScript types for comparison** (AC: 4)
  - [ ] Add `NumericColumnComparison` interface to `frontend/src/api/types.ts`
  - [ ] Add `PopulationComparisonResponse` interface matching server model
  - [ ] Include trust status and origin fields

## Dev Notes

### Architecture Context

**From Epic 21 Story 21.4 Notes:**
> Support public synthetic datasets in the same ingestion framework as open official data, but never blur their trust boundary. The flagship scenario should be able to load at least one synthetic dataset variant and present an explicit observed-versus-synthetic comparison with visible trust labels.

**Key Design Principle:** Trust boundaries must never be blurred. Synthetic and observed data must be visually and semantically distinct at every surface.

### Relationship to Previous Stories

**Story 21.1** (completed):
- Created `DataAssetDescriptor` with `origin`, `access_mode`, `trust_status`
- Defines `origin="synthetic-public"` for public synthetic datasets
- Allowed trust statuses for synthetic-public: `exploratory`, `demo-only`, `validation-pending`, `not-for-public-inference`

**Story 21.2** (completed):
- Extended API models with evidence fields
- Frontend TypeScript types include canonical evidence fields
- `PopulationLibraryItem` has `canonical_origin`, `access_mode`, `trust_status`

**Story 21.3** (completed):
- Created `StructuralAsset` combining `DataAssetDescriptor` with structural payload
- Factory function `create_structural_asset()` for convenient construction
- JSON serialization with full validation

**Epic 20 Story 20.4** (completed):
- Population Library component exists at `frontend/src/components/population/`
- `PopulationLibraryItem` type exists with legacy origin tags

### Project Structure Notes

**New files to create:**
- `src/reformlab/data/synthetic_catalog.py` — synthetic asset registry
- `src/reformlab/data/comparison.py` — observed vs synthetic comparison utility
- `frontend/src/components/shared/TrustStatusBadge.tsx` — trust status badge
- `frontend/src/components/shared/SyntheticBadge.tsx` — synthetic indicator badge
- `frontend/src/components/population/PopulationComparisonView.tsx` — comparison UI

**Files to modify:**
- `src/reformlab/server/routes/populations.py` — add comparison endpoint
- `src/reformlab/server/models.py` — add comparison response model, extend PopulationLibraryItem
- `frontend/src/api/types.ts` — add comparison TypeScript types
- `frontend/src/components/population/PopulationLibrary.tsx` — integrate badges

**Data folder structure:**
```
data/populations/
  fr-synthetic-2024/
    data.parquet          # Synthetic population data
    descriptor.json       # DataAssetDescriptor JSON
    schema.json           # DataSchema JSON
```

### Type System Constraints

**DataAssetDescriptor for synthetic populations:**
```python
DataAssetDescriptor(
    asset_id="fr-synthetic-2024",
    name="French Synthetic Population 2024",
    description="100k synthetic households for France - exploratory use only",
    data_class="structural",
    origin="synthetic-public",  # Public synthetic dataset
    access_mode="bundled",       # Bundled with product
    trust_status="exploratory",  # Not for production decisions
    # ... other optional fields
)
```

**Comparison result structure:**
```python
@dataclass(frozen=True)
class PopulationComparison:
    """Result of comparing observed vs synthetic population."""
    observed_asset_id: str
    synthetic_asset_id: str
    row_counts: dict[str, int]  # {"observed": N, "synthetic": M}
    column_counts: dict[str, int]
    numeric_comparison: dict[str, NumericColumnComparison]
    trust_labels: dict[str, dict[str, str]]  # Per-asset governance fields

@dataclass(frozen=True)
class NumericColumnComparison:
    """Comparison of a single numeric column."""
    column_name: str
    observed_mean: float
    synthetic_mean: float
    relative_diff_pct: float
    observed_median: float
    synthetic_median: float
    observed_std: float
    synthetic_std: float
```

### Testing Standards

**Backend tests:**
- Mirror source structure: `tests/data/test_synthetic_catalog.py`, `tests/data/test_comparison.py`
- Test class structure matches existing patterns
- Direct assertions with plain `assert`
- Error path tests use `pytest.raises(HTTPException)` for API, `pytest.raises(IngestionError)` for ingestion

**Frontend tests:**
- Component tests for badge components
- Mock API responses for comparison view
- Test trust status color mapping
- Test synthetic indicator display

### Integration with Existing Patterns

**Use existing `load_population_folder()` from Story 17.1:**
- Already supports `schema.json` and `source.json` metadata
- Extend to support `descriptor.json` with `DataAssetDescriptor`
- Fallback to legacy source.json if descriptor.json not present

**Population Library from Epic 20 Story 20.4:**
- Component exists at `frontend/src/components/population/`
- Add badges to existing population cards
- Add comparison trigger button

**Comparison Infrastructure from Epic 20 Story 20.6:**
- `ExecutionMatrixCell` and `ScenarioSummary` types exist
- Add population comparison as new dimension
- Reuse comparison UI patterns where applicable

### Trust Boundary Rules

**From synthetic-data-decision-document-2026-03-23.md Section 3.5:**
> The user interface and APIs must make invalid interpretation difficult. Concretely:
> - open official data and synthetic data must not appear identical in the UI
> - every dataset and output must expose origin, access_mode, trust_status, and intended-use label
> - synthetic results must remain visibly distinct from official observed data
> - any attempt to load deferred restricted sources in the current phase must fail explicitly

**Implementation rules:**
1. Badges must be visible in all list and detail views
2. Trust status must be displayed in tooltips on hover
3. Comparison view must show full governance metadata
4. Color coding must be consistent across all surfaces
5. Never show synthetic data as "production-safe"

### References

**Primary source documents:**
- [synthetic-data-decision-document-2026-03-23.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/synthetic-data-decision-document-2026-03-23.md) — Sections 2.6, 3.2, 3.5 for evidence taxonomy and trust governance
- [epic-21-trust-governed-open-synthetic-evidence-foundation.md](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/epic-21-trust-governed-open-synthetic-evidence-foundation.md) — Story 21.4 notes
- [Story 21.1](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-1-implement-canonical-evidence-asset-descriptor-and-current-phase-source-matrix.md) — DataAssetDescriptor pattern
- [Story 21.2](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-2-add-origin-access-mode-trust-status-contracts-across-backend-apis-and-frontend-models.md) — API model integration
- [Story 21.3](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-3-implement-typed-structural-exogenous-calibration-and-validation-asset-schemas.md) — StructuralAsset type

**Code patterns to follow:**
- [src/reformlab/data/pipeline.py](/Users/lucas/Workspace/reformlab/src/reformlab/data/pipeline.py) — load_population_folder() pattern
- [src/reformlab/data/assets.py](/Users/lucas/Workspace/reformlab/src/reformlab/data/assets.py) — StructuralAsset factory pattern
- [src/reformlab/server/routes/populations.py](/Users/lucas/Workspace/reformlab/src/reformlab/server/routes/populations.py) — Population endpoint patterns
- [src/reformlab/data/synthetic.py](/Users/lucas/Workspace/reformlab/src/reformlab/data/synthetic.py) — Synthetic population generation

**Project context:**
- [docs/project-context.md](/Users/lucas/Workspace/reformlab/docs/project-context.md) — Critical rules for language rules, framework rules, testing rules
- [_bmad-output/project-context.md](/Users/lucas/Workspace/reformlab/_bmad-output/project-context.md) — Technology stack, architecture patterns

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None (story creation)

### Completion Notes List

- Story 21.4 implements public synthetic asset ingestion and observed-versus-synthetic comparison flows
- Uses `DataAssetDescriptor` from Story 21.1 for governance metadata
- Uses `StructuralAsset` from Story 21.3 for typed payload contract
- Extends population ingestion infrastructure from Epic 20 Story 20.4
- Adds `SyntheticAssetRegistry` for cataloging bundled synthetic datasets
- Creates comparison utility `ObservedVsSyntheticComparison` for distributional statistics
- Adds API endpoint `GET /api/populations/compare` for comparison data
- Frontend components: `TrustStatusBadge`, `SyntheticBadge`, `PopulationComparisonView`
- Trust status color coding: exploratory=yellow, demo-only=gray, production-safe=green, validation-pending=orange, not-for-public-inference=red
- `is_synthetic` boolean field added to `PopulationLibraryItem` for easier UI filtering
- At least one bundled synthetic dataset (`fr-synthetic-2024`) with full metadata
- Trust boundary rules enforced: synthetic and observed data never visually indistinguishable

### File List

**Files to create:**
- `src/reformlab/data/synthetic_catalog.py` — SyntheticAssetRegistry class
- `src/reformlab/data/comparison.py` — ObservedVsSyntheticComparison utility
- `frontend/src/components/shared/TrustStatusBadge.tsx` — Trust status badge component
- `frontend/src/components/shared/SyntheticBadge.tsx` — Synthetic indicator badge component
- `frontend/src/components/population/PopulationComparisonView.tsx` — Comparison view component
- `data/populations/fr-synthetic-2024/data.parquet` — Bundled synthetic population
- `data/populations/fr-synthetic-2024/descriptor.json` — DataAssetDescriptor metadata
- `data/populations/fr-synthetic-2024/schema.json` — DataSchema metadata

**Files to modify:**
- `src/reformlab/server/routes/populations.py` — Add comparison endpoint
- `src/reformlab/server/models.py` — Add comparison response model, extend PopulationLibraryItem
- `frontend/src/api/types.ts` — Add comparison TypeScript types
- `frontend/src/components/population/PopulationLibrary.tsx` — Integrate badges

**Tests to create:**
- `tests/data/test_synthetic_catalog.py` — Registry tests
- `tests/data/test_comparison.py` — Comparison utility tests
- `tests/server/test_routes_populations.py` — API endpoint tests (or add to existing)
- `frontend/src/components/shared/__tests__/TrustStatusBadge.test.tsx`
- `frontend/src/components/shared/__tests__/SyntheticBadge.test.tsx`
- `frontend/src/components/population/__tests__/PopulationComparisonView.test.tsx`
