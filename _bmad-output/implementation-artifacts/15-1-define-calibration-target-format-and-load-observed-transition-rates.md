# Story 15.1: Define Calibration Target Format and Load Observed Transition Rates

Status: ready-for-dev

## Story

As a **policy analyst**,
I want a well-defined format for observed transition rates (e.g., vehicle adoption from ADEME/SDES) that can be loaded and validated by the calibration engine,
so that I can calibrate discrete choice taste parameters against real-world data and trust that my calibration inputs are complete and consistent.

## Acceptance Criteria

1. **AC-1: Target format specification** — Given observed transition rate data (e.g., vehicle adoption rates from ADEME/SDES), when formatted as calibration targets, then the format specifies: decision domain, time period, transition type (from → to), observed rate, and source metadata.
2. **AC-2: File loading with validation** — Given a calibration target file (CSV or YAML), when loaded by the calibration engine, then targets are validated for completeness (all required fields present) and consistency (rates sum to ≤1.0 per origin state).
3. **AC-3: Multi-domain access** — Given calibration targets for multiple decision domains, when loaded, then each domain's targets are accessible independently.
4. **AC-4: Error reporting** — Given a calibration target with a missing or malformed field, when loaded, then a clear error message identifies the field and row.

## Tasks / Subtasks

- [ ] Task 1: Create `src/reformlab/calibration/` module structure (AC: 1)
  - [ ] 1.1: Create `__init__.py` with module docstring referencing Epic 15 / FR52
  - [ ] 1.2: Create `types.py` with frozen dataclasses: `CalibrationTarget`, `CalibrationTargetSet`
  - [ ] 1.3: Create `errors.py` with `CalibrationError` base, `CalibrationTargetValidationError`, `CalibrationTargetLoadError`

- [ ] Task 2: Define calibration target dataclasses (AC: 1, 3)
  - [ ] 2.1: `CalibrationTarget` frozen dataclass with fields: `domain: str`, `period: int`, `from_state: str`, `to_state: str`, `observed_rate: float`, `source_label: str`, `source_metadata: dict[str, str]`
  - [ ] 2.2: `CalibrationTargetSet` frozen dataclass wrapping `tuple[CalibrationTarget, ...]` with `by_domain(domain: str) -> CalibrationTargetSet` filtering method
  - [ ] 2.3: `__post_init__` validation on `CalibrationTarget`: rate in [0.0, 1.0], non-empty domain/from_state/to_state
  - [ ] 2.4: `CalibrationTargetSet.validate_consistency()` method: assert rates sum ≤ 1.0 per (domain, period, from_state) group — raise `CalibrationTargetValidationError` on violation

- [ ] Task 3: Define JSON Schema for YAML calibration target files (AC: 2, 4)
  - [ ] 3.1: Create `src/reformlab/calibration/schema/calibration-targets.schema.json` (Draft 2020-12)
  - [ ] 3.2: Schema requires `targets` array, each item with required fields: `domain`, `period`, `from_state`, `to_state`, `observed_rate`, `source_label`; optional: `source_metadata`, `weight`
  - [ ] 3.3: Numeric constraints: `observed_rate` minimum 0.0, maximum 1.0; `period` integer

- [ ] Task 4: Implement target loader (AC: 2, 3, 4)
  - [ ] 4.1: Create `loader.py` with `load_calibration_targets(path: Path) -> CalibrationTargetSet`
  - [ ] 4.2: Support CSV loading via `computation/ingestion.py` `ingest()` function with a `CALIBRATION_TARGET_SCHEMA` DataSchema constant
  - [ ] 4.3: Support YAML loading via `yaml.safe_load()` + jsonschema validation against the schema from Task 3
  - [ ] 4.4: Format dispatch by file extension (`.csv`, `.csv.gz`, `.parquet` → ingest path; `.yaml`, `.yml` → YAML path)
  - [ ] 4.5: Convert raw records to `CalibrationTarget` objects, then build `CalibrationTargetSet`
  - [ ] 4.6: Call `CalibrationTargetSet.validate_consistency()` after construction
  - [ ] 4.7: Error messages must identify the exact field name and row number for malformed data

- [ ] Task 5: Add governance integration (AC: 1)
  - [ ] 5.1: `CalibrationTargetSet.to_governance_entry(source_label: str) -> dict[str, Any]` returning `AssumptionEntry`-compatible dict with key `"calibration_targets"`, domain list, target count, and source metadata summary

- [ ] Task 6: Write tests (AC: all)
  - [ ] 6.1: Create `tests/calibration/__init__.py` and `conftest.py` with fixtures: sample target dicts, sample CSV bytes, sample YAML strings, `tmp_path` fixture files
  - [ ] 6.2: `test_types.py` — `TestCalibrationTarget`: frozen immutability, valid construction, rate bounds validation (`observed_rate < 0` raises, `> 1.0` raises), empty domain/state raises; `TestCalibrationTargetSet`: by_domain filtering, multi-domain access, validate_consistency passes for valid data, fails when rates sum > 1.0 with clear error
  - [ ] 6.3: `test_loader.py` — `TestCSVLoading`: valid CSV loads correctly, missing column raises with column name in message, malformed rate value raises with row number; `TestYAMLLoading`: valid YAML loads correctly, schema validation catches invalid fields, round-trip stability; `TestFormatDispatch`: `.csv` dispatches to CSV path, `.yaml` dispatches to YAML path, unknown extension raises
  - [ ] 6.4: `test_errors.py` — error hierarchy, `CalibrationTargetValidationError` is subclass of `CalibrationError`
  - [ ] 6.5: Create fixture files in `tests/fixtures/calibration/` — at least: `valid_vehicle_targets.csv`, `valid_heating_targets.csv`, `valid_multi_domain_targets.yaml`, `invalid_missing_field.csv`, `invalid_rate_sum.yaml`
  - [ ] 6.6: `test_governance.py` — `to_governance_entry()` returns correct structure with key, value, source, is_default fields

- [ ] Task 7: Lint, type-check, regression (AC: all)
  - [ ] 7.1: `uv run ruff check src/reformlab/calibration/ tests/calibration/`
  - [ ] 7.2: `uv run mypy src/reformlab/calibration/`
  - [ ] 7.3: `uv run mypy src/`
  - [ ] 7.4: `uv run pytest tests/` — full regression, zero failures

## Dev Notes

### Architecture Patterns (MUST FOLLOW)

**New module location:** `src/reformlab/calibration/` — follows the same pattern as `src/reformlab/discrete_choice/` (Epic 14). This is a new top-level subsystem parallel to `discrete_choice/`, `population/`, `orchestrator/`, etc.

**Module file layout:**
```
src/reformlab/calibration/
├── __init__.py                       # Public API exports, module docstring
├── types.py                          # CalibrationTarget, CalibrationTargetSet (frozen dataclasses)
├── errors.py                         # CalibrationError hierarchy
├── loader.py                         # load_calibration_targets() — CSV + YAML loading
└── schema/
    └── calibration-targets.schema.json  # JSON Schema for YAML format
```

**Frozen dataclasses everywhere** — all domain types use `@dataclass(frozen=True)`. Mutate via `dataclasses.replace()`.

**Every file starts with** `from __future__ import annotations`.

**Protocols, not ABCs** — use `Protocol` + `@runtime_checkable` for interfaces.

**Module docstrings** — every `.py` file must have a module-level docstring referencing story/FR (e.g., "Story 15.1 / FR52").

**Error hierarchy pattern** — follow `discrete_choice/errors.py`:
```python
class CalibrationError(Exception):
    """Base error for calibration subsystem."""

class CalibrationTargetValidationError(CalibrationError):
    """Raised when calibration targets fail consistency checks."""

class CalibrationTargetLoadError(CalibrationError):
    """Raised when a calibration target file cannot be loaded."""
```

**PyArrow is canonical** — use `pa.Table` for tabular data. No pandas in core logic.

**Structured logging** — `logging.getLogger(__name__)` with `key=value` format:
```python
logger.info("event=targets_loaded domain=%s n_targets=%d", domain_name, count)
```

### Key Data Types from Discrete Choice (Story 14.x) That Calibration Targets Must Align With

**Decision domains** — from `discrete_choice/domain.py`:
- Vehicle domain name: `"vehicle"` (from `vehicle.py`)
- Heating domain name: `"heating"` (from `heating.py`)

**Vehicle alternatives** — from `discrete_choice/vehicle.py`:
- IDs: `"keep_current"`, `"buy_petrol"`, `"buy_diesel"`, `"buy_hybrid"`, `"buy_electric"`, `"buy_no_vehicle"`
- Calibration `from_state` values correspond to current vehicle types: `"petrol"`, `"diesel"`, `"hybrid"`, `"ev"`, `"none"`
- Calibration `to_state` values correspond to alternative IDs (or the resulting type)

**Heating alternatives** — from `discrete_choice/heating.py`:
- IDs: `"keep_current"`, `"gas_boiler"`, `"heat_pump"`, `"electric"`, `"wood_pellet"`
- Similar from/to state mapping

**TasteParameters** — from `discrete_choice/types.py`:
```python
@dataclass(frozen=True)
class TasteParameters:
    beta_cost: float  # V_ij = beta_cost × cost_ij
```
Story 15.2 optimizes `beta_cost` to minimize gap between simulated and observed rates. The targets from 15.1 are what it optimizes against.

**DecisionRecord** — from `discrete_choice/decision_record.py`:
- `DecisionRecord.chosen: pa.Array` — N-element string array of chosen alternative IDs
- Aggregate simulated transition rates are computed from `chosen` (count per alternative / N)

### CSV Data Schema for Calibration Targets

Use the existing `DataSchema` + `ingest()` pattern from `computation/ingestion.py`:

```python
CALIBRATION_TARGET_SCHEMA = DataSchema(
    schema=pa.schema([
        pa.field("domain", pa.utf8()),
        pa.field("period", pa.int64()),
        pa.field("from_state", pa.utf8()),
        pa.field("to_state", pa.utf8()),
        pa.field("observed_rate", pa.float64()),
        pa.field("source_label", pa.utf8()),
    ]),
    required_columns=("domain", "period", "from_state", "to_state", "observed_rate", "source_label"),
    optional_columns=(),
)
```

### YAML Format Example

```yaml
# calibration-targets.yaml
targets:
  - domain: vehicle
    period: 2022
    from_state: petrol
    to_state: buy_electric
    observed_rate: 0.03
    source_label: "SDES vehicle fleet 2022"
    source_metadata:
      dataset: "parc-automobile-2022"
      url: "https://data.gouv.fr/..."
      year: "2022"
  - domain: vehicle
    period: 2022
    from_state: petrol
    to_state: keep_current
    observed_rate: 0.85
    source_label: "SDES vehicle fleet 2022"
  - domain: heating
    period: 2022
    from_state: gas
    to_state: heat_pump
    observed_rate: 0.05
    source_label: "ADEME heating transitions 2022"
```

### CSV Format Example

```csv
domain,period,from_state,to_state,observed_rate,source_label
vehicle,2022,petrol,buy_electric,0.03,SDES vehicle fleet 2022
vehicle,2022,petrol,keep_current,0.85,SDES vehicle fleet 2022
vehicle,2022,petrol,buy_hybrid,0.05,SDES vehicle fleet 2022
vehicle,2022,petrol,buy_diesel,0.02,SDES vehicle fleet 2022
heating,2022,gas,heat_pump,0.05,ADEME heating transitions 2022
```

### Consistency Validation Rule

For each unique (domain, period, from_state) group, the sum of `observed_rate` values must be ≤ 1.0. This reflects that a household starting from state X can transition to multiple states, but total probability cannot exceed 1.0 (the remainder is implicitly "keep current" or uncaptured transitions).

Example valid group: `(vehicle, 2022, petrol)` → rates sum to 0.95 ≤ 1.0 ✓
Example invalid group: `(vehicle, 2022, petrol)` → rates sum to 1.05 > 1.0 ✗

### Governance Integration Pattern

Follow `population/validation.py` `to_governance_entry()`:
```python
def to_governance_entry(self, *, source_label: str = "calibration_targets") -> dict[str, Any]:
    return {
        "key": "calibration_targets",
        "value": {
            "domains": sorted(set(t.domain for t in self.targets)),
            "n_targets": len(self.targets),
            "periods": sorted(set(t.period for t in self.targets)),
            "sources": sorted(set(t.source_label for t in self.targets)),
        },
        "source": source_label,
        "is_default": False,
    }
```

### JSON Schema Pattern

Follow `templates/schema/scenario-template.schema.json`:
- Use `"$schema": "https://json-schema.org/draft/2020-12/schema"`
- Use `"additionalProperties": false` for strict validation
- Numeric constraints: `"minimum": 0, "maximum": 1` for `observed_rate`
- `"type": "integer"` for `period`
- Validate with `jsonschema.Draft202012Validator`

### Data Source References

- **SDES** — vehicle fleet composition data already loaded by `population/loaders/sdes.py`. Fleet counts by fuel type provide the basis for computing observed vehicle transition rates.
- **ADEME** — Base Carbone emission factors already loaded by `population/loaders/ademe.py`. Heating transition rates would come from ADEME's energy renovation surveys.

Note: Story 15.1 does NOT download from these sources. It loads pre-formatted calibration target files (CSV/YAML) that the analyst prepares from institutional data. The loader handles file format, schema validation, and semantic consistency — not data acquisition.

### What Story 15.2 Will Consume

The `CalibrationTargetSet` object produced by this story's loader is the primary input to Story 15.2's `CalibrationEngine`. The engine will:
1. Load targets via `load_calibration_targets(path)`
2. Filter by domain via `target_set.by_domain("vehicle")`
3. Run the logit model with candidate β values
4. Compare simulated aggregate rates against `CalibrationTarget.observed_rate`
5. Optimize β to minimize the gap

### Cross-Story Dependencies

| Story | Relationship |
|---|---|
| **14.2** | `TasteParameters.beta_cost` — what 15.2 will optimize against 15.1's targets |
| **14.3** | Vehicle alternative IDs define valid `to_state` values for vehicle domain |
| **14.4** | Heating alternative IDs define valid `to_state` values for heating domain |
| **14.6** | `DecisionRecord.chosen` provides simulated rates for comparison |
| **15.2** | Direct consumer — `CalibrationEngine` takes `CalibrationTargetSet` as input |
| **15.3** | Uses same loader for holdout data (different file, same format) |
| **15.4** | `source_metadata` from targets flows into run manifests |
| **15.5** | Notebook demo loads and displays targets |

### Project Structure Notes

- New module `src/reformlab/calibration/` is consistent with the flat subsystem layout (`computation/`, `orchestrator/`, `templates/`, `indicators/`, `governance/`, `population/`, `discrete_choice/`, `vintage/`, `interfaces/`).
- Test directory `tests/calibration/` mirrors source with `__init__.py` + `conftest.py`.
- Fixture files in `tests/fixtures/calibration/` follow the existing convention (`tests/fixtures/templates/`, `tests/fixtures/` for golden files).
- Schema file in `src/reformlab/calibration/schema/` follows the `templates/schema/` convention.
- Must add `calibration` to mypy overrides in `pyproject.toml` if needed (check existing `[[tool.mypy.overrides]]` patterns).

### Testing Standards Summary

- Class-based test grouping: `TestCalibrationTarget`, `TestCalibrationTargetSet`, `TestCalibrationTargetLoader`
- Docstrings in Given/When/Then format
- Direct `assert` statements — no custom assertion helpers
- `pytest.raises(CalibrationTargetValidationError, match=...)` for error cases
- Inline PyArrow table construction in fixtures
- `tmp_path` for file I/O tests
- Golden YAML/CSV files in `tests/fixtures/calibration/`
- Reference story/AC IDs in test comments

### References

- [Source: docs/epics.md — Epic 15 / Story 15.1 acceptance criteria]
- [Source: docs/project-context.md — coding conventions, frozen dataclasses, PyArrow canonical type]
- [Source: src/reformlab/discrete_choice/types.py — TasteParameters, Alternative, ChoiceResult]
- [Source: src/reformlab/discrete_choice/domain.py — DecisionDomain protocol]
- [Source: src/reformlab/discrete_choice/vehicle.py — vehicle alternatives and domain]
- [Source: src/reformlab/discrete_choice/heating.py — heating alternatives and domain]
- [Source: src/reformlab/discrete_choice/decision_record.py — DecisionRecord format]
- [Source: src/reformlab/computation/ingestion.py — DataSchema, ingest() function]
- [Source: src/reformlab/population/loaders/base.py — DataSourceLoader protocol, CachedLoader pattern]
- [Source: src/reformlab/population/loaders/sdes.py — SDES loader for vehicle fleet data]
- [Source: src/reformlab/population/loaders/ademe.py — ADEME loader for emission factors]
- [Source: src/reformlab/population/validation.py — to_governance_entry() pattern]
- [Source: src/reformlab/governance/capture.py — assumption capture patterns]
- [Source: src/reformlab/governance/manifest.py — AssumptionEntry TypedDict, RunManifest]
- [Source: src/reformlab/templates/schema/scenario-template.schema.json — JSON Schema conventions]
- [Source: src/reformlab/templates/workflow.py — jsonschema Draft202012Validator usage pattern]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed — comprehensive developer guide created
- All Epic 14 discrete choice code analyzed for alignment with calibration target format
- CSV and YAML loading patterns extracted from existing codebase (ingestion.py, loader.py)
- Governance integration pattern extracted from population/validation.py
- JSON Schema conventions extracted from templates/schema/
- Error hierarchy pattern extracted from discrete_choice/errors.py
- Cross-story dependency map built covering stories 14.2–14.6 and 15.2–15.5

### File List

New files to create:
- `src/reformlab/calibration/__init__.py`
- `src/reformlab/calibration/types.py`
- `src/reformlab/calibration/errors.py`
- `src/reformlab/calibration/loader.py`
- `src/reformlab/calibration/schema/calibration-targets.schema.json`
- `tests/calibration/__init__.py`
- `tests/calibration/conftest.py`
- `tests/calibration/test_types.py`
- `tests/calibration/test_loader.py`
- `tests/calibration/test_errors.py`
- `tests/calibration/test_governance.py`
- `tests/fixtures/calibration/valid_vehicle_targets.csv`
- `tests/fixtures/calibration/valid_heating_targets.csv`
- `tests/fixtures/calibration/valid_multi_domain_targets.yaml`
- `tests/fixtures/calibration/invalid_missing_field.csv`
- `tests/fixtures/calibration/invalid_rate_sum.yaml`
