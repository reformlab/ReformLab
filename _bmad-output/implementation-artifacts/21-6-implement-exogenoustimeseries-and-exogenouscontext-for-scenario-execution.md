# Story 21.6: Implement ExogenousTimeSeries and ExogenousContext for Scenario Execution

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

**As a** policy analyst running scenario simulations,
**I want** scenarios to support scenario-specific exogenous time series inputs (energy prices, carbon tax rates, technology costs) with coverage validation and year-based lookup,
**so that** I can model different external assumption paths (e.g., high vs low energy price scenarios) and compare results across divergent exogenous assumptions.

## Acceptance Criteria

1. **AC1:** `ExogenousContext` frozen dataclass created at `src/reformlab/orchestrator/exogenous.py` with:
   - `series: dict[str, ExogenousAsset]` - mapping of series name to asset (e.g., `"energy_price_electricity"` → `ExogenousAsset`)
   - `get_value(series_name: str, year: int) -> float` - look up value for a specific series and year with interpolation
   - `validate_coverage(start_year: int, end_year: int) -> None` - validate ALL series have complete coverage for the year range
   - `get_asset(series_name: str) -> ExogenousAsset` - retrieve full asset for provenance metadata
   - `series_names: tuple[str, ...]` property - return sorted tuple of available series names
   - `from_assets(assets: tuple[ExogenousAsset, ...]) -> ExogenousContext` classmethod - factory that validates unique series names and builds context

2. **AC2:** `OrchestratorConfig` extended with optional `exogenous: ExogenousContext | None` field (default None for backward compatibility)
   - ExogenousContext flows through YearState.data using key `"exogenous_context"`
   - All steps can access exogenous values via `state.data["exogenous_context"].get_value(series_name, year)`
   - `RunRequest` in `src/reformlab/server/models.py` extended with optional `exogenous_series: list[str] | None` field for run API

3. **AC3:** Preflight validation check `exogenous-coverage` registered in `src/reformlab/server/routes/validation.py` (extends Story 20.7 infrastructure)
   - Runs `ExogenousContext.validate_coverage(start_year, end_year)` during scenario preflight
   - Returns ValidationCheckResult with passed/failed status and clear error message listing missing years/series
   - Only executes if `exogenous` is provided in OrchestratorConfig (no check for scenarios without exogenous inputs)

4. **AC4:** `ExogenousContext` serialized to/from JSON for scenario persistence and manifest recording:
   - `to_json() -> dict[str, Any]` - serializes to `{"series_names": list[str]}` format (assets stored separately by series name)
   - `from_json(data: dict[str, Any]) -> ExogenousContext` - classmethod loads assets via `load_exogenous_asset()` using series names
   - `RunManifest` extended with `exogenous_series: tuple[str, ...]` optional field recording series names used (empty tuple if none)
   - Scenario YAML extended with optional `exogenous_series: list[str]` field referencing assets by series name

5. **AC5:** Vehicle investment domain updated to consume exogenous fuel cost data:
   - `VehicleDomainConfig` extended with optional `fuel_price_series: str | None` field (default None for backward compatibility)
   - New `VehicleDomainConfig.fuel_price_default: float` field for legacy hardcoded cost (used when `fuel_price_series` is None)
   - Exogenous fuel price injection happens via `DiscreteChoiceStep` before adapter computation:
     - If `exogenous_context` and `domain.config.fuel_price_series` provided, inject fuel price into population as exogenous variable
     - Adapter (OpenFisca) reads injected variable to compute `total_vehicle_cost` per alternative
   - Fuel price injection recorded in YearState.metadata: `{"vehicle_fuel_cost": {"source": "exogenous:energy_price_petrol", "value": 1.75, "unit": "EUR/litre"}}`

6. **AC6:** Comparison dimension `exogenous` registered in frontend `frontend/src/components/comparison/DimensionRegistry.tsx`:
   - Extends Story 20.6 pluggable dimension infrastructure
   - `ResultDetailResponse` extended with `exogenous_series_hash: str | null` field for hash extraction
   - `ResultDetailResponse` extended with `exogenous_series_names: list[str] | null` field for display
   - `getValue()` returns `exogenous_series_hash` (SHA-256 hash of series names and values)
   - `render()` displays series count and sample series names from `exogenous_series_names`
   - Dimension allows filtering/grouping runs by exogenous assumptions

7. **AC7:** At least one prebuilt exogenous time series asset created for flagship scenario:
   - `data/exogenous/energy_price_electricity/` - French residential electricity prices 2020-2035 (EUR/kWh)
   - `data/exogenous/energy_price_petrol/` - French petrol prices 2020-2035 (EUR/litre)
   - `data/exogenous/ev_purchase_cost/` - EV vehicle purchase cost trajectory 2020-2035 (EUR)
   - Each asset folder contains `descriptor.json`, `data.parquet` (or `values.json` for simple series), and `metadata.json`

8. **AC8:** API endpoints for exogenous asset management:
   - `GET /api/exogenous/series` - list all available exogenous assets with metadata (returns ExogenousAsset list)
   - `GET /api/exogenous/series/{series_name}` - get specific exogenous asset by name
   - `POST /api/exogenous/series` - register new exogenous asset (upload or reference to existing file)
   - Request/response models in `src/reformlab/server/models.py`: `ExogenousAssetRequest`, `ExogenousAssetResponse`

9. **AC9:** Frontend types and API client for exogenous series:
   - TypeScript types in `frontend/src/api/types.ts`: `ExogenousAssetRequest`, `ExogenousAssetResponse`
   - API client in `frontend/src/api/exogenous.ts`: `listExogenousSeries()`, `getExogenousSeries()`, `createExogenousSeries()`
   - Exogenous series selector component in Engine stage (optional enhancement, allows users to attach series to scenario)

10. **AC10:** Tests cover:
    - ExogenousContext creation, validation, and lookups with interpolation
    - Coverage validation failures for missing years
    - Preflight check integration with pass/fail scenarios
    - OrchestratorConfig exogenous field propagation through YearState
    - Vehicle domain exogenous fuel price injection and metadata recording
    - Comparison dimension hash determinism
    - API endpoint list/get/create operations
    - JSON serialization/deserialization with load_exogenous_asset() integration
    - Manifest exogenous_series field recording

## Tasks / Subtasks

- [ ] **Task 1: Create ExogenousContext core type** (AC: 1)
  - [ ] Create `src/reformlab/orchestrator/exogenous.py` module with `ExogenousContext` frozen dataclass
  - [ ] Implement `series: dict[str, ExogenousAsset]` field (private, accessed via properties)
  - [ ] Implement `get_value(series_name: str, year: int) -> float` method with:
    - Series name validation (raises `KeyError` with clear message)
    - Delegation to `ExogenousAsset.get_value(year)` for interpolation
  - [ ] Implement `validate_coverage(start_year: int, end_year: int) -> None` method:
    - Validates start_year <= end_year
    - Checks each series has coverage for ALL years in range using `ExogenousAsset.validate_coverage()`
    - Raises `OrchestratorError` with clear message listing missing years/series
  - [ ] Implement `get_asset(series_name: str) -> ExogenousAsset` method for provenance access
  - [ ] Implement `series_names` property returning sorted tuple of series names
  - [ ] Implement `from_assets(assets: tuple[ExogenousAsset, ...])` classmethod:
    - Validates unique series names (duplicate names raise error)
    - Builds context from asset name → asset mapping
  - [ ] Add module docstring referencing Story 21.6 and synthetic-data-decision-document Section 2.3

- [ ] **Task 2: Extend OrchestratorConfig and YearState flow** (AC: 2)
  - [ ] Add optional `exogenous: ExogenousContext | None` field to `OrchestratorConfig` in `src/reformlab/orchestrator/types.py`
  - [ ] Add `exogenous_series: list[str] | None` field to `RunRequest` in `src/reformlab/server/models.py`
  - [ ] Update orchestrator initialization to populate YearState.data with exogenous context:
    - If `config.exogenous` is provided, store in `initial_data["exogenous_context"]`
  - [ ] Update `src/reformlab/orchestrator/__init__.py` to export `ExogenousContext`
  - [ ] Add backward compatibility: scenarios without exogenous field continue to work (None default)

- [ ] **Task 3: Add preflight validation check** (AC: 3)
  - [ ] Create `check_exogenous_coverage()` function in `src/reformlab/server/routes/validation.py`
  - [ ] Register validation check with ID `"exogenous-coverage"` using existing `register_check()` pattern
  - [ ] Check extracts `exogenous` from scenario's `engineConfig` (if provided)
  - [ ] Calls `ExogenousContext.validate_coverage()` with scenario start/end years
  - [ ] Returns `ValidationCheckResult` with:
    - `passed=True` if no exogenous or coverage valid
    - `passed=False` if coverage fails, with error message listing gaps
  - [ ] Add tests in `tests/server/test_routes_validation.py` for preflight integration

- [ ] **Task 4: Implement JSON serialization for scenarios** (AC: 4)
  - [ ] Add `to_json() -> dict[str, Any]` method to `ExogenousContext`:
    - Returns `{"series_names": list[str]}` format
  - [ ] Add `from_json(data: dict[str, Any]) -> ExogenousContext` classmethod:
    - Extracts series_names from JSON
    - Loads each asset via `load_exogenous_asset(series_name)` and builds context via `from_assets()`
  - [ ] Extend `RunManifest` in `src/reformlab/governance/manifest.py` with optional `exogenous_series: tuple[str, ...]` field (default empty tuple)
  - [ ] Update manifest recording in orchestrator to capture series names when exogenous is used
  - [ ] Extend scenario YAML schema in `src/reformlab/templates/schema.py`:
    - Add optional `exogenous_series: list[str]` field to baseline/reform scenarios
    - Series names validated against available assets during scenario load
  - [ ] Add tests for JSON round-trip and manifest field recording

- [ ] **Task 5: Update vehicle domain for exogenous fuel costs** (AC: 5)
  - [ ] Extend `VehicleDomainConfig` in `src/reformlab/discrete_choice/vehicle.py`:
    - Add `fuel_price_series: str | None = None` field (series name for exogenous lookup)
    - Add `fuel_price_default: float = 1.55` field (EUR/litre, used when no exogenous series configured)
  - [ ] Keep `default_vehicle_domain_config()` with `fuel_price_series=None` for backward compatibility
  - [ ] Update `DiscreteChoiceStep` in `src/reformlab/discrete_choice/step.py` to inject exogenous fuel prices:
    - Before adapter computation, check if domain has `fuel_price_series` configured
    - If exogenous context available and series configured, inject fuel price into population tables
    - Record metadata: `{"vehicle_fuel_cost": {"source": "exogenous:{series_name}", "value": float, "unit": "EUR/litre"}}`
    - If no exogenous, record metadata using default value
  - [ ] Update `VehicleInvestmentDomain` tests in `tests/discrete_choice/test_vehicle.py`:
    - Add test case for exogenous fuel price injection via DiscreteChoiceStep
    - Verify backward compatibility (no exogenous = default costs)
    - Verify metadata recording in YearState

- [ ] **Task 6: Register exogenous comparison dimension** (AC: 6)
  - [ ] Extend `ResultDetailResponse` in `src/reformlab/server/models.py`:
    - Add `exogenous_series_hash: str | None = None` field (SHA-256 hash)
    - Add `exogenous_series_names: list[str] | None = None` field (for display)
  - [ ] Extend `ResultDetailResponse` TypeScript interface in `frontend/src/api/types.ts`
  - [ ] Create `frontend/src/components/comparison/ExogenousDimension.tsx`:
    - Implement `ComparisonDimension<string>` with id="exogenous", label="Exogenous Series"
    - `getValue(runResult: ResultDetailResponse): string | null` returns `runResult.exogenous_series_hash`
    - `render(value: string): ReactNode` displays series count and names from `exogenous_series_names`
  - [ ] Register dimension in `DimensionRegistry` on module initialization
  - [ ] Add tests for hash determinism (same series → same hash, different series → different hash)
  - [ ] Update comparison UI to display exogenous dimension when available

- [ ] **Task 7: Create prebuilt exogenous assets** (AC: 7)
  - [ ] Create `data/exogenous/energy_price_electricity/` folder with:
    - `descriptor.json` - DataAssetDescriptor with data_class="exogenous", origin="open-official", source="Eurostat/Eurostat"
    - `values.json` - simple year → value mapping (2020-2035, EUR/kWh)
    - `metadata.json` - unit, frequency, source, vintage, interpolation_method
  - [ ] Create `data/exogenous/energy_price_petrol/` folder with similar structure
  - [ ] Create `data/exogenous/ev_purchase_cost/` folder with similar structure
  - [ ] Create `src/reformlab/data/exogenous_loader.py` with `load_exogenous_asset(name: str) -> ExogenousAsset` function:
    - Uses same pattern as `load_calibration_asset()` from Story 21.5 (path traversal protection, symlink protection)
  - [ ] Add tests for exogenous asset loading

- [ ] **Task 8: Add API endpoints for exogenous assets** (AC: 8)
  - [ ] Create `src/reformlab/server/routes/exogenous.py` router module
  - [ ] Implement `GET /api/exogenous/series` endpoint:
    - Returns list of all `ExogenousAssetResponse` with descriptor and metadata
    - Supports filtering by origin, unit, source via query params
  - [ ] Implement `GET /api/exogenous/series/{series_name}` endpoint:
    - Returns single `ExogenousAssetResponse` or 404 if not found
  - [ ] Implement `POST /api/exogenous/series` endpoint:
    - Request: `ExogenousAssetRequest` with name, values, unit, metadata
    - Validates using `ExogenousAsset` constructor (raises on validation failure)
    - Creates asset folder in `data/exogenous/{series_name}/`
    - Returns created asset with generated asset_id
  - [ ] Register router in `src/reformlab/server/app.py` with prefix `/api/exogenous`
  - [ ] Add Pydantic models to `src/reformlab/server/models.py`:
    - `ExogenousAssetRequest` - request fields matching `ExogenousAsset` structure
    - `ExogenousAssetResponse` - response with all asset fields including descriptor

- [ ] **Task 9: Add frontend types and API client** (AC: 9)
  - [ ] Add TypeScript types to `frontend/src/api/types.ts`:
    - `ExogenousAssetRequest` interface
    - `ExogenousAssetResponse` interface (matching Pydantic model)
  - [ ] Create `frontend/src/api/exogenous.ts` API client module:
    - `listExogenousSeries(filters?: ExogenousFilters): Promise<ExogenousAssetResponse[]>`
    - `getExogenousSeries(seriesName: string): Promise<ExogenousAssetResponse>`
    - `createExogenousSeries(request: ExogenousAssetRequest): Promise<ExogenousAssetResponse>`
  - [ ] (Optional) Add exogenous series selector to Engine stage UI:
    - Allow users to attach series to scenario configuration
    - Display selected series with trust status badges

- [ ] **Task 10: Create comprehensive test suite** (AC: 10)
  - [ ] `tests/orchestrator/test_exogenous.py` - core context tests:
    - `TestExogenousContextCreation` - from_assets, duplicate name rejection
    - `TestExogenousContextLookup` - get_value with interpolation, series name validation
    - `TestExogenousContextCoverage` - validate_coverage pass/fail with missing years
  - [ ] `tests/server/test_routes_exogenous.py` - API endpoint tests:
    - List all series, filter by origin/unit/source
    - Get specific series by name, 404 handling
    - Create new series with validation error responses (ErrorResponse format)
  - [ ] `tests/server/test_routes_validation.py` - preflight integration tests:
    - Exogenous coverage check pass (no exogenous, full coverage)
    - Exogenous coverage check fail (missing years, clear error message)
  - [ ] `tests/orchestrator/test_runner.py` - orchestrator integration tests:
    - OrchestratorConfig exogenous field propagation through YearState
    - Steps can access exogenous context from state
    - Backward compatibility (scenarios without exogenous field)
  - [ ] `tests/discrete_choice/test_vehicle.py` - vehicle domain tests:
    - Exogenous fuel price lookup (config.fuel_price_series provided)
    - Backward compatibility (no exogenous = legacy costs)
    - Metadata recording (fuel_price_source, value, unit)
  - [ ] `tests/governance/test_manifest.py` - manifest recording tests:
    - RunManifest.exogenous_series field populated when exogenous used
    - Field absent when no exogenous context
  - [ ] Frontend tests for comparison dimension hash determinism

## Dev Notes

### Architecture Context

**From Epic 21 Story 21.6 Notes:**
> Add read-only scenario exogenous context with coverage validation, year-slice lookup, provenance metadata, and interpolation rules. At least one flagship domain must consume scenario-specific exogenous inputs, and scenario comparison must support differing exogenous assumptions.

**From synthetic-data-decision-document Section 2.3:**
> Each scenario carries its own `ExogenousContext`. Scenario comparison workflows may differ in both policy parameters and exogenous assumptions. `ExogenousContext.validate_coverage(start_year, end_year)` must be called before orchestration begins. Missing years are a hard error, not a silent extrapolation.

### Existing Code Patterns to Reference

**Story 21.3 (completed) - ExogenousAsset:**
- `ExogenousAsset` at `src/reformlab/data/assets.py` already has:
  - `get_value(year: int) -> float` with interpolation (linear, step, none)
  - `validate_coverage(start_year: int, end_year: int) -> None`
  - `to_json()` / `from_json()` serialization
  - `create_exogenous_asset()` factory function

**Story 20.7 (completed) - Preflight Infrastructure:**
- `ValidationCheck` protocol and `register_check()` in `src/reformlab/server/routes/validation.py`
- Preflight checks execute during scenario validation before run
- Use this pattern for exogenous coverage validation

**Story 20.6 (completed) - Comparison Dimensions:**
- `ComparisonDimension<T>` protocol at `frontend/src/components/comparison/`
- Registry pattern: `register<T>(dimension: ComparisonDimension<T>)`
- `getValue(runResult: ResultDetailResponse): T | null` extracts dimension value
- `render?(value: T): ReactNode` optional custom renderer

**Story 21.5 (completed) - Asset Loader Pattern:**
- `load_calibration_asset()` and `load_validation_asset()` in `src/reformlab/data/assets.py`
- Security hardening: path traversal protection, symlink attack protection
- Follow this pattern for `load_exogenous_asset()`

### Relationship to Previous Stories

**Story 21.3** (completed):
- Created `ExogenousAsset` with get_value(), validate_coverage(), interpolation
- ExogenousContext wraps multiple ExogenousAsset instances

**Story 21.2** (completed):
- Extended API models with evidence fields (origin, access_mode, trust_status)
- ExogenousAssetResponse should include these fields

**Epic 14 Stories 14.1-14.5** (completed):
- Vehicle investment domain exists in `src/reformlab/discrete_choice/vehicle.py`
- Cost matrix computation happens before logit choice
- This story extends vehicle domain to consume exogenous fuel prices

**Epic 20 Story 20.6** (completed):
- Comparison dimension infrastructure supports pluggable dimensions
- Exogenous dimension is a new comparison dimension, not a separate system

### Project Structure Notes

**New files to create:**
- `src/reformlab/orchestrator/exogenous.py` — ExogenousContext implementation
- `src/reformlab/data/exogenous_loader.py` — asset loader for exogenous series
- `src/reformlab/server/routes/exogenous.py` — API endpoints
- `frontend/src/api/exogenous.ts` — frontend API client
- `frontend/src/components/comparison/ExogenousDimension.tsx` — comparison dimension
- `tests/orchestrator/test_exogenous.py` — core context tests
- `tests/server/test_routes_exogenous.py` — API endpoint tests
- `data/exogenous/{series_name}/` — prebuilt asset folders

**Files to modify:**
- `src/reformlab/orchestrator/types.py` — add exogenous field to OrchestratorConfig
- `src/reformlab/orchestrator/runner.py` — propagate exogenous through YearState
- `src/reformlab/server/models.py` — add Pydantic request/response models, extend RunRequest and ResultDetailResponse
- `src/reformlab/server/app.py` — register exogenous router
- `src/reformlab/server/routes/validation.py` — add exogenous coverage check
- `src/reformlab/governance/manifest.py` — add exogenous_series field
- `src/reformlab/templates/schema.py` — extend scenario YAML schema
- `src/reformlab/discrete_choice/step.py` — inject exogenous fuel prices before adapter computation
- `src/reformlab/discrete_choice/vehicle.py` — add fuel_price_series and fuel_price_default fields
- `frontend/src/api/types.ts` — add TypeScript types
- `frontend/src/components/comparison/DimensionRegistry.tsx` — register exogenous dimension

### Type System Constraints

**ExogenousContext:**
```python
@dataclass(frozen=True)
class ExogenousContext:
    """Read-only exogenous time series context for scenario execution.

    Wraps multiple ExogenousAsset instances and provides unified lookup
    and coverage validation. Each scenario carries its own ExogenousContext,
    enabling comparison across divergent exogenous assumptions.

    Attributes:
        _series: Internal mapping of series name → ExogenousAsset (private)

    Story 21.6 / AC1.
    """
    _series: dict[str, ExogenousAsset] = field(default_factory=dict)

    def get_value(self, series_name: str, year: int) -> float:
        """Look up value for series and year with interpolation.

        Args:
            series_name: Series identifier (e.g., "energy_price_electricity").
            year: Year to look up.

        Returns:
            Float value for the requested year.

        Raises:
            KeyError: If series_name not found.
            EvidenceAssetError: If year missing and interpolation disabled.
        """
        ...

    def validate_coverage(self, start_year: int, end_year: int) -> None:
        """Validate ALL series have complete coverage for year range.

        Args:
            start_year: First year (inclusive).
            end_year: Last year (inclusive).

        Raises:
            ValueError: If start_year > end_year.
            EvidenceAssetError: If any series has missing years.
        """
        ...

    @property
    def series_names(self) -> tuple[str, ...]:
        """Sorted tuple of available series names."""
        ...

    @classmethod
    def from_assets(cls, assets: tuple[ExogenousAsset, ...]) -> ExogenousContext:
        """Create context from tuple of ExogenousAsset instances.

        Validates unique series names (duplicates raise error).

        Args:
            assets: Tuple of exogenous assets.

        Returns:
            ExogenousContext with name → asset mapping.

        Raises:
            ValueError: If duplicate series names detected.
        """
        ...
```

**VehicleDomainConfig Extension:**
```python
@dataclass(frozen=True)
class VehicleDomainConfig:
    """Configuration for the vehicle investment decision domain."""
    # ... existing fields ...
    fuel_price_series: str | None = None  # Series name for exogenous fuel prices
    fuel_price_default: float = 1.55  # EUR/litre, used when no exogenous series
```

### Storage Format Specification

**Exogenous asset folder structure:**
```
data/exogenous/{series_name}/
    values.json           # Year → value mapping (simple series)
    # OR data.parquet      # For complex multi-column series
    descriptor.json       # DataAssetDescriptor JSON
    metadata.json         # Series-specific metadata (unit, frequency, source, vintage, etc.)
    schema.json           # DataSchema (optional, for Parquet)
```

**values.json schema:**
```json
{
    "2020": 0.185,
    "2021": 0.192,
    "2022": 0.201,
    ...
}
```

**metadata.json schema:**
```json
{
    "unit": "EUR/kWh",
    "frequency": "annual",
    "source": "Eurostat",
    "vintage": "2024-Q2",
    "interpolation_method": "linear",
    "aggregation_method": "mean",
    "revision_policy": "latest"
}
```

### Comparison Dimension Design

**Exogenous Dimension Hash:**
```typescript
// Deterministic hash of exogenous series names and values
function hashExogenousContext(context: ExogenousContext): string {
    const sortedNames = context.seriesNames.sort();
    const hashInput = sortedNames.map(name => {
        const asset = context.getAsset(name);
        return `${name}:${JSON.stringify(asset.values)}`;
    }).join("|");
    return sha256(hashInput);
}
```

**Comparison Registration:**
```typescript
registerDimension<string>({
    id: "exogenous",
    label: "Exogenous Series",
    description: "Deterministic hash of exogenous time series assumptions",
    getValue: (runResult) => {
        // Extract from runResult.exogenous_series_hash
        return runResult.exogenous_series_hash || null;
    },
    render: (hash, runResult) => {
        // Display series count and sample names from runResult.exogenous_series_names
        const names = runResult.exogenous_series_names || [];
        return <ExogenousBadge hash={hash} seriesNames={names} />;
    },
});
```

### Preflight Check Integration

**Check Registration Pattern:**
```python
# src/reformlab/server/routes/validation.py
def _check_exogenous_coverage(request: PreflightRequest) -> ValidationCheckResult:
    """Preflight check for exogenous time series coverage."""
    scenario = request.scenario
    engine_config = scenario.get("engineConfig", {})

    # Skip if no exogenous series configured
    exogenous_series = engine_config.get("exogenousSeries")
    if not exogenous_series:
        return ValidationCheckResult(
            id="exogenous-coverage",
            label="Exogenous series coverage",
            passed=True,
            severity="warning",
            message="No exogenous series configured"
        )

    # Load and validate coverage
    try:
        context = ExogenousContext.from_assets(...)  # Load from asset store
        start_year = engine_config.get("startYear", 2025)
        end_year = engine_config.get("endYear", 2030)
        context.validate_coverage(start_year, end_year)
        return ValidationCheckResult(
            id="exogenous-coverage",
            label="Exogenous series coverage",
            passed=True,
            severity="info",
            message=f"All {len(exogenous_series)} series have coverage {start_year}-{end_year}"
        )
    except EvidenceAssetError as exc:
        return ValidationCheckResult(
            id="exogenous-coverage",
            label="Exogenous series coverage",
            passed=False,
            severity="error",
            message=str(exc)
        )

register_check(ValidationCheck(
    check_id="exogenous-coverage",
    label="Exogenous series coverage",
    severity="error",
    check_fn=_check_exogenous_coverage
))
```

### Testing Standards

**Backend tests:**
- `tests/orchestrator/test_exogenous.py` — context creation, lookups, coverage validation
- `tests/server/test_routes_exogenous.py` — API list/get/create operations
- `tests/server/test_routes_validation.py` — preflight integration
- `tests/orchestrator/test_runner.py` — orchestrator integration
- `tests/discrete_choice/test_vehicle.py` — vehicle domain exogenous fuel price injection
- `tests/governance/test_manifest.py` — manifest field recording

**Frontend tests:**
- Comparison dimension hash determinism tests
- API client tests

### Integration with Existing Patterns

**Use existing asset loader pattern from Story 21.5:**
```python
# src/reformlab/data/exogenous_loader.py
_EXOGENOUS_ASSETS_BASE_PATH = Path("data/exogenous")

def load_exogenous_asset(series_name: str) -> ExogenousAsset:
    """Load exogenous asset from disk by series_name."""
    # Security: Validate series_name to prevent path traversal
    if "/" in series_name or "\\" in series_name or ".." in series_name:
        raise EvidenceAssetError(...)

    asset_path = _EXOGENOUS_ASSETS_BASE_PATH / series_name

    # Security: Resolve and verify containment
    resolved_path = asset_path.resolve()
    base_resolved = _EXOGENOUS_ASSETS_BASE_PATH.resolve()
    if not str(resolved_path).startswith(str(base_resolved)):
        raise EvidenceAssetError(...)

    # Load descriptor.json, values.json, metadata.json
    # Construct via ExogenousAsset.from_json()
    ...
```

### Trust Boundary Rules

**From synthetic-data-decision-document Section 2.3:**
> This category is strictly **read-only** from the simulation's perspective. The orchestrator looks up exogenous values by year; it never mutates them.

**Implementation rules:**
1. `ExogenousContext._series` is private dict (access via methods only)
2. `get_value()` does NOT modify underlying assets (delegates to immutable ExogenousAsset)
3. Coverage validation is read-only check (no mutation)
4. Scenario comparison uses hash of series values (no mutation)

### Prebuilt Asset Values

**French Residential Electricity Prices (EUR/kWh):**
- Source: Eurostat/nrg_pc_204
- Values (approximate, 2020-2035):
  - 2020: 0.185
  - 2025: 0.195
  - 2030: 0.205
  - 2035: 0.215

**French Petrol Prices (EUR/litre):**
- Source: Eurostat/nrg_pc_202
- Values (approximate, 2020-2035):
  - 2020: 1.45
  - 2025: 1.55
  - 2030: 1.65
  - 2035: 1.75

**EV Purchase Cost (EUR):**
- Source: ADEME/ICCT projections
- Values (approximate, 2020-2035):
  - 2020: 35000
  - 2025: 28000
  - 2030: 22000
  - 2035: 18000

### References

**Primary source documents:**
- [synthetic-data-decision-document-2026-03-23.md](/Users/lucas/Workspace/reformlab/_bmad-output/planning-artifacts/synthetic-data-decision-document-2026-03-23.md) — Section 2.3: Exogenous Data
- [epic-21-trust-governed-open-synthetic-evidence-foundation.md](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/epic-21-trust-governed-open-synthetic-evidence-foundation.md) — Story 21.6 notes
- [Story 21.3](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-3-implement-typed-structural-exogenous-calibration-and-validation-asset-schemas.md) — ExogenousAsset pattern
- [Story 20.6](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/20-6-refactor-run-results-compare-around-scenario-by-population-execution.md) — Comparison dimension infrastructure
- [Story 20.7](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/20-7-extend-backend-apis-for-population-explorer-and-execution-contract-validation.md) — Preflight check infrastructure
- [Story 21.5](/Users/lucas/Workspace/reformlab/_bmad-output/implementation-artifacts/21-5-separate-calibration-targets-from-validation-benchmarks-and-implement-trust-status-rules.md) — Asset loader security pattern

**Code patterns to follow:**
- [src/reformlab/data/assets.py](/Users/lucas/Workspace/reformlab/src/reformlab/data/assets.py) — ExogenousAsset with get_value(), validate_coverage()
- [src/reformlab/server/routes/validation.py](/Users/lucas/Workspace/reformlab/src/reformlab/server/routes/validation.py) — ValidationCheck protocol
- [src/reformlab/discrete_choice/vehicle.py](/Users/lucas/Workspace/reformlab/src/reformlab/discrete_choice/vehicle.py) — Vehicle domain cost computation
- [frontend/src/components/comparison/DimensionRegistry.tsx](/Users/lucas/Workspace/reformlab/frontend/src/components/comparison/) — Comparison dimension pattern

**Project context:**
- [_bmad-output/project-context.md](/Users/lucas/Workspace/reformlab/_bmad-output/project-context.md) — Critical rules for language rules, framework rules, testing rules

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None (story creation)

### Completion Notes List

ULTIMATE CONTEXT ENGINE ANALYSIS COMPLETED - Comprehensive developer guide created

**Context extraction completed from:**
- Epic 21 story definition and notes
- Synthetic data decision document (Section 2.3: Exogenous Data)
- Existing ExogenousAsset implementation (Story 21.3)
- Story 20.6 comparison dimension infrastructure
- Story 20.7 preflight check infrastructure
- Story 21.5 asset loader security pattern
- Vehicle investment domain implementation (Epic 14)

**Key developer guardrails provided:**
- Complete type specifications for ExogenousContext
- Storage format specification for prebuilt assets
- Preflight check integration pattern
- Comparison dimension design with hash algorithm
- Security patterns from Story 21.5 asset loaders
- Backward compatibility requirements
- Trust boundary rules (read-only enforcement)
- Comprehensive test coverage requirements

### File List

**New files to create:**
- `src/reformlab/orchestrator/exogenous.py` — ExogenousContext implementation
- `src/reformlab/data/exogenous_loader.py` — Asset loader with security hardening
- `src/reformlab/server/routes/exogenous.py` — API endpoints
- `frontend/src/api/exogenous.ts` — Frontend API client
- `frontend/src/components/comparison/ExogenousDimension.tsx` — Comparison dimension
- `tests/orchestrator/test_exogenous.py` — Core context tests
- `tests/server/test_routes_exogenous.py` — API endpoint tests
- `data/exogenous/energy_price_electricity/` — Prebuilt asset folders
- `data/exogenous/energy_price_petrol/`
- `data/exogenous/ev_purchase_cost/`

**Files to modify:**
- `src/reformlab/orchestrator/types.py` — Add exogenous field to OrchestratorConfig
- `src/reformlab/orchestrator/runner.py` — Propagate exogenous through YearState
- `src/reformlab/server/models.py` — Add ExogenousAssetRequest/Response, extend RunRequest and ResultDetailResponse
- `src/reformlab/server/app.py` — Register exogenous router
- `src/reformlab/server/routes/validation.py` — Add exogenous coverage preflight check
- `src/reformlab/governance/manifest.py` — Add exogenous_series field
- `src/reformlab/templates/schema.py` — Extend scenario YAML schema
- `src/reformlab/discrete_choice/step.py` — Inject exogenous fuel prices before adapter computation
- `src/reformlab/discrete_choice/vehicle.py` — Add fuel_price_series and fuel_price_default fields
- `frontend/src/api/types.ts` — Add TypeScript types
- `frontend/src/components/comparison/DimensionRegistry.tsx` — Register exogenous dimension

**Tests to create/modify:**
- `tests/orchestrator/test_exogenous.py` — New
- `tests/server/test_routes_exogenous.py` — New
- `tests/server/test_routes_validation.py` — Add preflight integration tests
- `tests/orchestrator/test_runner.py` — Add orchestrator integration tests
- `tests/discrete_choice/test_vehicle.py` — Add exogenous fuel price injection tests
- `tests/governance/test_manifest.py` — Add manifest field recording tests
- Frontend tests for comparison dimension hash determinism
