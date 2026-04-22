# Story 26.5: Add Quick Test Population to the Population Library

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst using the ReformLab workspace,
I want a visually differentiated Quick Test Population available in the Population Library for fast demos and smoke testing,
so that I can quickly demonstrate the platform without waiting for large datasets to load, while clearly understanding this population is not suitable for substantive analysis.

## Acceptance Criteria

1. Given the Population Library renders, then Quick Test Population appears near the top of the library grid (before all other populations).
2. Given Quick Test Population is displayed, then it shows visual differentiation: amber border/background, "Fast demo / smoke test" badge with Zap icon, and "Demo Only" trust status badge.
3. Given Quick Test Population card is rendered, then it displays a tooltip explaining "For fast demos and smoke testing only — not for substantive analysis" on hover.
4. Given the analyst selects Quick Test Population, then Scenario stage inherits it as the primary population and shows it in the inherited population context.
5. Given Quick Test Population is selected, then it can be used to run a simulation like any other population (100 households, fast execution).
6. Given analysis-grade population recommendations are shown, then Quick Test Population is visually differentiated and NOT promoted as a recommended analysis population.

## Tasks / Subtasks

- [ ] Add Quick Test Population backend data (AC: #1, #5)
  - [ ] Create `data/populations/quick-test-population/` folder
  - [ ] Create `data/populations/quick-test-population/descriptor.json` with Quick Test Population metadata (name, description, origin=synthetic-public, access_mode=bundled, trust_status=demo-only)
  - [ ] Create `data/populations/quick-test-population/data.parquet` with 100 households and minimal schema (household_id, person_id, age, income, energy_transport_fuel, energy_heating_fuel, carbon_emissions)
  - [ ] Create `data/populations/quick-test-population/schema.json` defining the column types
  - [ ] Generate deterministic data using seed=42 for reproducibility

- [ ] Verify backend API includes Quick Test Population (AC: #1)
  - [ ] Backend `_scan_populations_with_origin()` should automatically pick up the quick-test-population folder
  - [ ] Verify GET /api/populations returns Quick Test Population with correct metadata
  - [ ] Verify trust_status is "demo-only" and origin is "synthetic-public"
  - [ ] Add backend test for Quick Test Population inclusion in list response

- [ ] Verify frontend displays Quick Test Population correctly (AC: #1, #2, #3, #6)
  - [ ] PopulationLibraryScreen already has visual differentiation (Story 22.4) — verify it still works after Epic 26 migration
  - [ ] Verify Quick Test Population appears first in the sorted list (PopulationLibraryScreen lines 260-264)
  - [ ] Verify amber border/background (border-amber-200 bg-amber-50/30) renders correctly
  - [ ] Verify "Fast demo / smoke test" badge with Zap icon renders
  - [ ] Verify tooltip shows on hover
  - [ ] Verify "Demo Only" trust status badge renders

- [ ] Verify Scenario stage inherits Quick Test Population (AC: #4)
  - [ ] ScenarioStageScreen should show Quick Test Population in inherited population context when selected
  - [ ] Verify population name appears correctly in Scenario stage
  - [ ] Verify source badge shows as "[Built-in]"
  - [ ] Verify household count shows as "100 households"

- [ ] Add tests for Quick Test Population (AC: #1, #2, #3, #4, #5, #6)
  - [ ] Update PopulationLibraryScreen.test.tsx to verify Quick Test Population rendering
  - [ ] Add test for Quick Test Population appearing first in grid
  - [ ] Add test for visual differentiation (amber colors, badge, tooltip)
  - [ ] Add test for Quick Test Population selection and Scenario inheritance
  - [ ] Add backend test for Quick Test Population in /api/populations response

- [ ] Documentation and edge cases (AC: #6)
  - [ ] Ensure Quick Test Population is NOT recommended as analysis-grade population
  - [ ] Verify help content explains Quick Test Population purpose and limitations
  - [ ] Add copy explaining when to use Quick Test Population vs analysis populations

## Dev Notes

### Current State Analysis

**What's Already Implemented (Story 22.4):**
- Frontend constant definition: `frontend/src/data/quick-test-population.ts`
- Visual differentiation in `PopulationLibraryScreen.tsx` (lines 76-89, 101-110, 260-264):
  - Amber border and background (`border-amber-200 bg-amber-50/30`)
  - "Fast demo / smoke test" badge with Zap icon
  - Always sorted first in the population grid
- Tests for visual rendering in `PopulationLibraryScreen.test.tsx` (describe block "Quick Test Population (Story 22.4)")
- Mock data in `frontend/src/hooks/useApi.ts` includes Quick Test Population

**What's Missing:**
- Backend data file: `data/populations/quick-test-population/` folder with data.parquet and descriptor.json
- API integration: The backend doesn't return Quick Test Population because it only scans the data directory
- When the real API is called (not mock), Quick Test Population disappears

**Why This Matters:**
Quick Test Population currently only appears when using mock data (API fallback). When the backend API works correctly, Quick Test Population is missing from the library. Story 26.5 completes the feature by adding the backend data so Quick Test Population is always available.

### Architecture Context

**Population Data Structure:**

Populations can be stored in two formats:
1. **File-based:** `data/populations/{population_id}.csv` or `.parquet` (legacy)
2. **Folder-based:** `data/populations/{population_id}/` with:
   - `data.parquet` or `data.csv` (the actual data)
   - `descriptor.json` (metadata: name, origin, access_mode, trust_status, etc.)
   - `schema.json` (column definitions, optional)

Quick Test Population should use the **folder-based structure** to include proper metadata.

**Backend Population Discovery:**

The backend `_scan_populations_with_origin()` function in `src/reformlab/server/routes/populations.py` automatically discovers populations by:
1. Scanning `data/populations/` for folders (with descriptor.json)
2. Scanning for `.csv` and `.parquet` files
3. Reading metadata from descriptor.json or deriving defaults

**Quick Test Population Metadata:**

Based on frontend mock data and UX requirements:
- `id`: "quick-test-population"
- `name`: "Quick Test Population"
- `households`: 100 (intentionally small for fast runs)
- `year`: 2026 (current year)
- `origin`: "built-in" (legacy field for UI behavior)
- `canonical_origin`: "synthetic-public"
- `access_mode`: "bundled"
- `trust_status`: "demo-only"
- `is_synthetic`: true
- `column_count`: 8 (minimal schema for carbon tax demo)

**Data Schema:**

Minimal columns needed for carbon tax demo:
- `household_id` (int64) - household identifier
- `person_id` (int64) - person identifier
- `age` (int64) - person age
- `income` (double) - household income
- `energy_transport_fuel` (double) - transport fuel consumption
- `energy_heating_fuel` (double) - heating fuel consumption
- `energy_natural_gas` (double) - natural gas consumption
- `carbon_emissions` (double) - computed carbon emissions

**Deterministic Generation:**

Use seed=42 to generate the 100 households so the Quick Test Population is reproducible across deployments. This aligns with the project's determinism requirements.

### Frontend Integration

**PopulationLibraryScreen.tsx** (already implemented, verify still works):

```typescript
// Lines 260-264: Quick Test Population is always sorted first
const quickTestPop = populations.find((p) => p.id === QUICK_TEST_POPULATION_ID);
const otherPops = populations.filter((p) => p.id !== QUICK_TEST_POPULATION_ID);
const sortedPopulations = quickTestPop ? [quickTestPop, ...otherPops] : populations;

// Lines 76-89: Special visual treatment for Quick Test Population
const isQuickTest = population.id === QUICK_TEST_POPULATION_ID;
// ... amber border/background, badge, tooltip
```

**ScenarioStageScreen.tsx** (needs verification):

Scenario stage should display Quick Test Population in the inherited population context when selected. The existing `selectedPopulationId` flow should work without changes since Quick Test Population is just another population from the API.

### Testing Strategy

**Backend Tests:** `tests/server/test_populations.py` (MODIFY)

Add test for Quick Test Population:
```python
def test_list_populations_includes_quick_test_population():
    """Quick Test Population should be included in the populations list — Story 26.5."""
    response = client.get("/api/populations")
    assert response.status_code == 200
    populations = response.json()["populations"]

    # Find Quick Test Population
    quick_test = next((p for p in populations if p["id"] == "quick-test-population"), None)
    assert quick_test is not None
    assert quick_test["name"] == "Quick Test Population"
    assert quick_test["households"] == 100
    assert quick_test["trust_status"] == "demo-only"
    assert quick_test["canonical_origin"] == "synthetic-public"
```

**Frontend Tests:** `frontend/src/components/screens/__tests__/PopulationLibraryScreen.test.tsx` (MODIFY)

Existing tests already cover Quick Test Population rendering (lines 95-185). Verify these tests still pass after Epic 26 migration.

Add integration test for Quick Test Population selection:
```typescript
it("Quick Test Population selection is preserved in Scenario stage", async () => {
  // Select Quick Test Population
  const onSelect = vi.fn();
  render(<PopulationLibraryScreen {...baseProps({ onSelect })} />);
  const selectButtons = screen.getAllByText("Select");
  await userEvent.click(selectButtons[0]); // First button is Quick Test Population
  expect(onSelect).toHaveBeenCalledWith(QUICK_TEST_POPULATION_ID);
});
```

### Project Structure Notes

**Files to Create:**
- `data/populations/quick-test-population/descriptor.json` — Metadata
- `data/populations/quick-test-population/data.parquet` — 100 households
- `data/populations/quick-test-population/schema.json` — Column definitions

**Files to Verify:**
- `frontend/src/components/screens/PopulationLibraryScreen.tsx` — Visual differentiation (already done)
- `frontend/src/components/screens/PopulationStageScreen.tsx` — Merged populations include Quick Test Population
- `frontend/src/contexts/AppContext.tsx` — Scenario state handling

**Files to Modify:**
- `tests/server/test_populations.py` — Add Quick Test Population test
- `frontend/src/components/screens/__tests__/PopulationLibraryScreen.test.tsx` — Verify existing tests

### Implementation Order Recommendation

1. **Phase 1: Backend Data** (AC: #1, #5)
   - Create quick-test-population folder with descriptor.json, schema.json
   - Generate deterministic 100-household data.parquet
   - Verify backend discovers and returns Quick Test Population

2. **Phase 2: API Verification** (AC: #1)
   - Add backend test for Quick Test Population inclusion
   - Verify GET /api/populations response includes Quick Test Population

3. **Phase 3: Frontend Verification** (AC: #1, #2, #3, #6)
   - Verify PopulationLibraryScreen visual differentiation still works
   - Verify Quick Test Population appears first in sorted list
   - Verify badges, tooltip, and colors render correctly

4. **Phase 4: Scenario Integration** (AC: #4)
   - Verify Scenario stage inherits Quick Test Population correctly
   - Test selection flow from library to scenario

5. **Phase 5: Testing and Documentation** (AC: #6)
   - Run all existing PopulationLibraryScreen tests
   - Add Scenario inheritance test
   - Update help content if needed

### Key Design Decisions

**Folder-Based Structure:** Quick Test Population uses the folder-based structure (not a single CSV file) to include proper metadata via descriptor.json. This ensures the backend correctly sets trust_status=demo-only and canonical_origin=synthetic-public.

**Deterministic Generation:** The 100 households are generated deterministically using seed=42. This ensures the Quick Test Population is identical across all deployments, supporting reproducibility goals.

**Minimal Schema:** Quick Test Population uses only 8 columns needed for carbon tax demos. This keeps it lightweight while still supporting the most common demo scenario.

**Position in Library:** Quick Test Population is always sorted first in the library grid, regardless of alphabetical order. This ensures it's easy to find for demos and walkthroughs.

**Visual Differentiation:** Amber colors (not red or error colors) communicate "this is different" without implying something is broken. The Zap icon and "Fast demo / smoke test" label clearly communicate purpose.

### Out of Scope

To avoid scope creep:
- **Multiple quick test variants** — Only one Quick Test Population is needed
- **Configurable quick test size** — 100 households is fixed and sufficient
- **Advanced analysis features** — Quick Test Population is for demos only
- **Policy-specific quick test data** — Minimal schema supports carbon tax demos; other policies work but may have limited columns

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-26.5] - Story requirements
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#UX-DR14] - Quick Test Population UX requirements
- [Source: frontend/src/data/quick-test-population.ts] - Frontend Quick Test Population definition
- [Source: frontend/src/components/screens/PopulationLibraryScreen.tsx] - Visual differentiation implementation
- [Source: src/reformlab/server/routes/populations.py] - Backend population discovery logic
- [Source: data/populations/fr-synthetic-2024/descriptor.json] - Example descriptor.json structure

## Dev Agent Record

### Agent Model Used

claude-opus-4-6 (story creation)

### Debug Log References

None — story created with comprehensive context from existing codebase analysis.

### Completion Notes List

Story 26.5 created with comprehensive developer context:

**Context Sources Analyzed:**
- Epic 26 Story 26.5 requirements and UX-DR14
- Existing Quick Test Population frontend implementation (Story 22.4)
- Population library screen and visual differentiation code
- Backend population discovery and API implementation
- Data directory structure and population file formats
- Mock data patterns and API hooks

**Key Findings:**
- Quick Test Population visual differentiation is ALREADY implemented (Story 22.4)
- What's missing: Backend data file so Quick Test Population appears in real API responses
- The frontend mock data includes Quick Test Population, but it disappears when real API is called
- Solution: Create `data/populations/quick-test-population/` folder with data.parquet and descriptor.json

**Implementation Strategy:**
1. Create backend data folder with deterministic 100-household dataset
2. Backend automatically discovers and includes it in /api/populations
3. Frontend already handles it correctly (sorting, visual differentiation)
4. Verify Scenario inheritance works with existing population flow

**Testing Strategy:**
- Backend test for Quick Test Population inclusion in list response
- Frontend tests already exist; verify they still pass
- Integration test for Scenario inheritance

Status set to: ready-for-dev

### File List

- `_bmad-output/implementation-artifacts/26-5-add-quick-test-population-to-the-population-library.md`
