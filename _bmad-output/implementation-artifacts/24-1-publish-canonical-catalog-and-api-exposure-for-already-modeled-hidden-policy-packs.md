# Story 24.1: Publish canonical catalog and API exposure for already-modeled hidden policy packs

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an analyst,
I want to see all available policy packs in the catalog, including those that are already modeled but not yet visible,
so that I can discover and configure the full range of available policy options.

## Acceptance Criteria

1. Given the canonical catalog or API, when inspected, then existing modeled hidden packs appear with stable identifiers plus `runtime_availability` and `availability_reason` metadata.
2. Given a pack that is not yet executable on the live path, when surfaced, then its status is explicit rather than silently failing at run time.
3. Given existing visible packs, when the catalog is updated, then their identifiers and grouping remain stable.
4. Given saved scenarios or portfolios that reference previously visible packs, when loaded, then they remain compatible after the catalog expansion.

## Tasks / Subtasks

- [ ] Add runtime availability metadata to backend API models (AC: #1)
  - [ ] Add `RuntimeAvailability` Literal type to `src/reformlab/server/models.py`: `"live_ready"` | `"live_unavailable"`
  - [ ] Add `runtime_availability` field to `TemplateListItem` and `TemplateDetailResponse` models
  - [ ] Add `availability_reason` field (optional string) to `TemplateListItem` and `TemplateDetailResponse` models
  - [ ] Set default values: `runtime_availability="live_unavailable"` and `availability_reason=None` for all packs initially

- [ ] Extend template pack discovery to include hidden packs (AC: #1, #2)
  - [ ] Verify all existing packs are discovered by `_load_builtin_packs()`:
    - carbon_tax (5 variants): already visible
    - subsidy (1 variant): already visible
    - rebate (1 variant): already visible
    - feebate (1 variant): already visible
    - vehicle_malus (2 variants): **hidden** - need to mark availability
    - energy_poverty_aid (2 variants): **hidden** - need to mark availability
  - [ ] Update `_template_to_list_item()` to include runtime availability fields
  - [ ] Create availability classifier function that determines `runtime_availability` based on policy type:
    - `carbon_tax`, `subsidy`, `rebate`, `feebate`: `live_ready` (already supported in Epic 23)
    - `vehicle_malus`, `energy_poverty_aid`: `live_unavailable` with reason `"Domain translation pending - see Story 24.2"`
  - [ ] Ensure stable identifiers: use YAML filename stem (e.g., `"vehicle-malus-flat-rate"`) as the canonical `id`

- [ ] Update frontend TypeScript types (AC: #1, #2)
  - [ ] Add `RuntimeAvailability` type alias to `frontend/src/api/types.ts`: `"live_ready"` | `"live_unavailable"`
  - [ ] Extend `TemplateListItem` interface with `runtime_availability?: RuntimeAvailability` field
  - [ ] Extend `TemplateListItem` interface with `availability_reason?: string | null` field
  - [ ] Extend `TemplateDetailResponse` interface (inherits from `TemplateListItem`)

- [ ] Update frontend template API to use new fields (AC: #1)
  - [ ] No changes needed to `frontend/src/api/templates.ts` - type change is transparent to API calls
  - [ ] Verify `listTemplates()` and `getTemplate()` functions correctly return new fields

- [ ] Ensure backward compatibility for existing saved scenarios and portfolios (AC: #3, #4)
  - [ ] Verify all existing visible packs retain their current identifiers:
    - `carbon-tax-flat-lump-sum-dividend`
    - `carbon-tax-flat-no-redistribution`
    - `carbon-tax-flat-progressive-dividend`
    - `carbon-tax-progressive-no-redistribution`
    - `carbon-tax-progressive-progressive-dividend`
    - `subsidy-energy-retrofit`
    - `rebate-progressive-income`
    - `feebate-vehicle-emissions`
  - [ ] Ensure scenarios referencing these packs load correctly after catalog update
  - [ ] Ensure portfolios including these packs validate correctly after catalog update

- [ ] Add catalog listing tests (AC: #1, #2)
  - [ ] Add test class `TestCatalogWithRuntimeAvailability` in `tests/server/test_api.py`
  - [ ] Test that all 11 existing packs appear in catalog listing
  - [ ] Test that visible packs have `runtime_availability: "live_ready"`
  - [ ] Test that hidden packs have `runtime_availability: "live_unavailable"` with `availability_reason`
  - [ ] Test that template detail endpoint includes runtime availability metadata
  - [ ] Test that stable identifiers are preserved for all existing packs

- [ ] Add API contract tests (AC: #1, #2)
  - [ ] Test that response models include new fields
  - [ ] Test that default values are correctly set
  - [ ] Test that custom templates inherit default availability metadata

- [ ] Add regression tests for pack stability (AC: #3, #4)
  - [ ] Test that existing pack identifiers are unchanged after catalog expansion
  - [ ] Test that scenario loading works with pre-existing saved scenarios
  - [ ] Test that portfolio validation works with pre-existing portfolios

## Dev Notes

### Architecture Context

The catalog implementation lives in two key layers:

1. **Backend Discovery (`src/reformlab/server/routes/templates.py`)**:
   - `_load_builtin_packs()` scans `src/reformlab/templates/packs/` for YAML template files
   - Each pack subdirectory (e.g., `carbon_tax/`, `subsidy/`, `vehicle_malus/`) contains `.yaml` templates
   - Templates are loaded via `load_scenario_template()` from `src/reformlab/templates/loader.py`
   - Currently discovers and returns all packs without distinguishing visibility or availability

2. **API Models (`src/reformlab/server/models.py`)**:
   - `TemplateListItem` and `TemplateDetailResponse` define the wire format
   - Currently include: id, name, type, parameter_count, description, parameter_groups, is_custom
   - Need to extend with runtime availability fields

### Existing Policy Pack Structure

The following packs exist in `src/reformlab/templates/packs/`:

| Policy Type | Variants | Status | Domain Module |
|-------------|-----------|---------|---------------|
| `carbon_tax` | 5 | **visible** | `src/reformlab/templates/carbon_tax/` |
| `subsidy` | 1 | **visible** | `src/reformlab/templates/subsidy/` |
| `rebate` | 1 | **visible** | `src/reformlab/templates/rebate/` |
| `feebate` | 1 | **visible** | `src/reformlab/templates/feebate/` |
| `vehicle_malus` | 2 | **hidden** | `src/reformlab/templates/vehicle_malus/` (custom type) |
| `energy_poverty_aid` | 2 | **hidden** | `src/reformlab/templates/energy_poverty_aid/` (custom type) |

**Hidden packs** (`vehicle_malus`, `energy_poverty_aid`) are "built-in custom" types:
- Registered at module import time via `register_policy_type()` and `register_custom_template()`
- Have `compute.py` and `compare.py` modules with domain logic
- Have YAML template files in their pack directories
- Need runtime availability metadata to surface them correctly

### Implementation Constraints

1. **No new runtime selector in UX** (Epic 24 requirement):
   - This story is about truthful discoverability, not about live execution yet
   - Runtime availability is metadata only, not a user-facing toggle

2. **Preserve stable identifiers**:
   - Template IDs are YAML filename stems (e.g., `"vehicle-malus-flat-rate"`)
   - These IDs are used in saved scenarios and portfolios
   - Must not change existing IDs

3. **Separate live translation work** (Story 24.2):
   - Hidden packs are surfaced but marked `live_unavailable` with explicit reason
   - Live translation logic is in Story 24.2, not this story
   - Catalog should be honest about current capabilities

### Testing Standards

Follow existing test patterns from `tests/server/test_api.py` and `tests/templates/carbon_tax/test_pack_loader.py`:

- Use `TestClient` from FastAPI with `auth_headers` fixture
- Test both list and detail endpoints
- Test response structure and field presence
- Test backward compatibility with existing functionality
- Test error cases (nonexistent templates, etc.)

### Source Tree Components to Touch

**Backend:**
- `src/reformlab/server/models.py` - Add runtime availability fields to API models
- `src/reformlab/server/routes/templates.py` - Update catalog listing to include availability metadata

**Frontend:**
- `frontend/src/api/types.ts` - Add runtime availability TypeScript types

**Tests:**
- `tests/server/test_api.py` - Add catalog availability tests

### Key Implementation Decisions

1. **Availability Classification Logic**:
   - For this story, use a simple static classifier based on policy type enum
   - Future stories may extend this with more sophisticated checks (e.g., OpenFisca variable mapping)
   - Keep classification in `_template_to_list_item()` to avoid global state

2. **Field Defaults**:
   - `runtime_availability` defaults to `"live_unavailable"` (safe default)
   - `availability_reason` defaults to `None`
   - Only explicitly mark known-ready packs as `"live_ready"`

3. **Custom Template Handling**:
   - Custom templates created via `/api/templates/custom` should inherit default availability
   - They are implicitly `live_unavailable` until explicitly enabled

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-24] - Epic 24 requirements
- [Source: src/reformlab/server/routes/templates.py] - Template listing API endpoint
- [Source: src/reformlab/server/models.py] - API response models
- [Source: src/reformlab/templates/packs/__init__.py] - Template pack utilities
- [Source: frontend/src/api/types.ts] - Frontend TypeScript types
- [Source: frontend/src/api/templates.ts] - Frontend template API client

## Dev Agent Record

### Agent Model Used

claude-opus-4-6

### Debug Log References

None - This is the initial story creation.

### Completion Notes List

None - Story not yet implemented.

### File List

**Files to be created:**
- None

**Files to be modified:**
- `src/reformlab/server/models.py` - Add runtime availability fields
- `src/reformlab/server/routes/templates.py` - Update catalog with availability metadata
- `frontend/src/api/types.ts` - Add runtime availability types
- `tests/server/test_api.py` - Add catalog availability tests

**Related files (read-only for context):**
- `src/reformlab/templates/packs/__init__.py` - Template pack utilities
- `src/reformlab/templates/schema.py` - Policy type definitions
- `src/reformlab/templates/vehicle_malus/__init__.py` - Hidden pack example
- `src/reformlab/templates/energy_poverty_aid/__init__.py` - Hidden pack example
