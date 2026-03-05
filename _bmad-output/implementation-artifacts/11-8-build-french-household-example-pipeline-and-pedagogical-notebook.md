# Story 11.8: Build French Household Example Pipeline and Pedagogical Notebook

Status: ready-for-dev

## Story

As a **policy analyst** learning the ReformLab population generation library,
I want **a complete end-to-end French household example with a pedagogical notebook that explains each merge step in plain language**,
so that **I can understand how to build my own population from real institutional data and have a working reference implementation to adapt**.

## Acceptance Criteria

1. **Example pipeline produces French household population with all required attributes** — The French household example pipeline must generate a synthetic population with at least the following columns: household_id, income, household_size, region, housing_type, heating_type, vehicle_type, vehicle_age, energy_consumption, carbon_emissions.
2. **Pedagogical notebook runs end-to-end** — The notebook must execute from start to finish in CI without errors, demonstrating the complete pipeline workflow: load sources → merge methods → validate → visualize results.
3. **Each merge step is preceded by a plain-language explanation** — Before each merge operation, the notebook must include a markdown cell explaining: (a) what data is being merged, (b) what the merge method assumes, (c) when this method is appropriate vs. problematic, (d) a plain-language summary understandable to non-statisticians.
4. **Each merge step is followed by a summary chart** — After each merge operation, the notebook must include visualization showing the merged table's key distributions (e.g., income distribution by decile, vehicle fleet composition, heating system mix) with clear labels.
5. **Notebook runs in CI** — The notebook must pass automated execution in CI (no manual intervention required, all cells execute successfully).

## Tasks / Subtasks

- [ ] Task 1 (AC: #1)
  - [ ] Subtask 1.1: Define French household example pipeline configuration
    - Create pipeline builder with 3-4 merge steps demonstrating uniform, IPF, and conditional sampling methods
    - Load sources: INSEE Filosofi (income distribution), Eurostat (household composition), ADEME (energy consumption), SDES (vehicle fleet)
    - Generate household_id as sequential integer column
    - Derive required attributes: household_size from Eurostat, region from INSEE/Eurostat, housing_type/heating_type from statistical matching, vehicle_type/vehicle_age from SDES, energy_consumption from ADEME, carbon_emissions from emission factors
    - Use deterministic seed (42) for reproducibility
  - [ ] Subtask 1.2: Implement pipeline execution script
    - Create standalone script (`examples/populations/french_household_pipeline.py`) that builds and executes the pipeline
    - Export final population to `data/populations/french-household-example-2024.csv` with all required columns
    - Generate summary statistics file (`french-household-example-summary.txt`) with row count, column list, and key marginal distributions
- [ ] Task 2 (AC: #2, #3, #4, #5)
  - [ ] Subtask 2.1: Create pedagogical notebook structure
    - Create `notebooks/population-french-household-example.ipynb`
    - Follow notebook structure from quickstart/advanced: title, prerequisites, learning objectives, time estimate
    - Section organization: Introduction → Load Data Sources → Merge Step 1 → Validate → Merge Step 2 → ... → Final Results → Export
  - [ ] Subtask 2.2: Write introduction and setup sections
    - Explain what population generation is and why it matters for policy analysis
    - List prerequisites: installed ReformLab with population module, optional real data download (fallback to fixtures)
    - Provide learning objectives: load sources, choose merge methods, validate against marginals, understand assumptions
  - [ ] Subtask 2.3: Implement data source loading section
    - Show how to use `get_insee_loader()`, `get_eurostat_loader()`, `get_ademe_loader()`, `get_sdes_loader()` from public API
    - Display cache status for each source (use `CacheStatus` to show if download needed or cached)
    - Load and display summary statistics for each source (rows, columns, sample rows)
  - [ ] Subtask 2.4: Implement merge step sections with pedagogical explanations
    - For each merge step:
      - Markdown cell: Plain-language explanation of what we're merging, method assumptions, when appropriate vs. problematic
      - Code cell: Execute the merge with `PopulationPipeline` builder API
      - Markdown cell: Summary of result (rows, columns, key distributions)
      - Visualization cell: Charts showing merged table distributions (use matplotlib/seaborn, match quickstart/advanced style)
    - At least 3 merge steps demonstrating: (a) Uniform merge (independence assumption), (b) IPF merge (constraint-based reweighting), (c) Conditional sampling (stratum-based matching)
  - [ ] Subtask 2.5: Implement validation section
    - Show how to use `PopulationValidator` with `MarginalConstraint` objects
    - Define 2-3 reference marginals (e.g., income decile distribution from INSEE, vehicle fleet composition from SDES)
    - Run validation and display results (passed/failed per marginal, deviation values)
    - Explain what validation tells us about population quality
  - [ ] Subtask 2.6: Implement final results and export section
    - Display final population summary: total households, attribute distributions
    - Show how to export to CSV/Parquet using PyArrow
    - Show how to access `PipelineResult.assumption_chain` for governance integration
    - Include "What to do next" section: adapt for your region, use different sources, try other merge methods
- [ ] Task 3 (AC: #5)
  - [ ] Subtask 3.1: Add notebook to CI
    - Add `pytest` test that executes the notebook using `nbclient` or `jupyter nbconvert`
    - Test must verify notebook runs to completion without errors
    - Test must verify expected outputs exist (population table exported, summary statistics generated)
  - [ ] Subtask 3.2: Create notebook fixtures for offline CI
    - Generate minimal fixture CSV files (10-20 rows each) for INSEE, Eurostat, ADEME, SDES sources
    - Store fixtures in `tests/fixtures/populations/sources/`
    - Modify notebook setup to use fixtures when `REFORMLAB_OFFLINE=1` environment variable is set
    - Ensure notebook runs in CI without network access (fixtures path detection)

## Dev Notes

### Relevant Architecture Patterns

- **Population generation library location**: `src/reformlab/population/` — all loaders, methods, pipeline, validation logic live here [Source: src/reformlab/population/__init__.py]
- **Data source loaders**: Follow `DataSourceLoader` protocol via `CachedLoader` base class [Source: src/reformlab/population/loaders/base.py]
- **Merge methods**: Follow `MergeMethod` protocol with `merge()` method signature [Source: src/reformlab/population/methods/base.py]
- **Pipeline builder**: Use `PopulationPipeline` fluent API with `add_source()` and `add_merge()` [Source: src/reformlab/population/pipeline.py]
- **Assumption recording**: `PipelineResult.assumption_chain` provides `to_governance_entries()` for governance integration [Source: src/reformlab/population/assumptions.py]
- **Validation**: `PopulationValidator` validates against `MarginalConstraint` objects with absolute deviation metric [Source: src/reformlab/population/validation.py]

### Source Tree Components

#### Files to Create

1. **`examples/populations/french_household_pipeline.py`** — Standalone script that builds and executes the French household example pipeline
   - Uses `PopulationPipeline` builder to compose sources and merge steps
   - Exports final population to CSV and generates summary statistics
   - Follows deterministic seed pattern (seed=42) for reproducibility

2. **`notebooks/population-french-household-example.ipynb`** — Pedagogical Jupyter notebook
   - Follows structure from existing notebooks (`notebooks/quickstart.ipynb`, `notebooks/advanced.ipynb`)
   - Contains markdown explanations before each merge step (pedagogical requirement)
   - Contains visualizations after each merge step (summary charts)
   - Runs end-to-end in CI with optional fixture fallback for offline execution

3. **`tests/fixtures/populations/sources/`** — Fixture directory for offline CI
   - `insee_filosofi_2021_fixture.csv` — Minimal INSEE income distribution fixture (10-20 rows)
   - `eurostat_hhcomp_2022_fixture.csv` — Minimal Eurostat household composition fixture (10-20 rows)
   - `ademe_energy_2023_fixture.csv` — Minimal ADEME energy consumption fixture (10-20 rows)
   - `sdes_vehicles_2023_fixture.csv` — Minimal SDES vehicle fleet fixture (10-20 rows)
   - Fixtures follow schema of real datasets but with minimal representative data

#### Files to Modify

1. **`tests/population/conftest.py`** — Add notebook execution fixture
   - Add `french_example_notebook_path` fixture pointing to notebook location
   - Add `source_fixtures_path` fixture pointing to fixture directory
   - Follow pattern from existing test fixtures in population module

2. **`.github/workflows/test.yml`** (or equivalent CI configuration) — Add notebook test to CI
   - Add step to execute notebook using `pytest` with `nbclient` integration
   - Ensure notebook runs in both online and offline modes (test both with and without `REFORMLAB_OFFLINE=1`)

### Testing Standards

- **Notebook testing**: Use `pytest` with `nbclient` or `jupyter nbconvert` to execute notebooks as tests
- **Fixture generation**: Create fixtures programmatically in conftest.py using PyArrow, not via Write tool (Write tool cannot encode Windows-1252 if needed)
- **Offline-first testing**: Notebook must run without network access when `REFORMLAB_OFFLINE=1` is set (uses fixtures)
- **Determinism**: Pipeline uses fixed seed (42) for all merge operations to ensure reproducible results
- **Validation testing**: Include assertion that validation results match expected tolerances (e.g., income decile deviation < 0.05)

### Project Structure Alignment

- **Notebooks location**: `notebooks/` directory (matches existing `quickstart.ipynb`, `advanced.ipynb`)
- **Examples scripts location**: `examples/populations/` directory (new, follows standard `examples/` pattern)
- **Test fixtures location**: `tests/fixtures/populations/sources/` (matches existing test fixture structure)
- **Population module**: All imports from `reformlab.population` public API [Source: src/reformlab/population/__init__.py]

### Integration Points

- **Population generation integrates with**: Data sources (INSEE, Eurostat, ADEME, SDES), merge methods (uniform, IPF, conditional), validation (PopulationValidator), governance (assumption recording)
- **Notebook demonstrates**: End-to-end workflow from raw data sources to validated synthetic population
- **Governance integration**: Show how `PipelineResult.assumption_chain.to_governance_entries()` produces dicts for `RunManifest.assumptions`

### Critical Design Decisions

1. **Pedagogical over compact code** — Notebook prioritizes understandability over code brevity. Each merge step has its own section with explanation, code, summary, and visualization. This matches the "teach by doing" philosophy from EPIC-11 scope notes.

2. **Real data sources with fixture fallback** — Notebook attempts to load from real institutional APIs (INSEE, Eurostat, ADEME, SDES) first, but falls back to fixtures in offline mode or when sources unavailable. This ensures CI runs without network dependencies.

3. **Minimal fixture size** — Fixtures are 10-20 rows each, just enough to demonstrate pipeline logic. This keeps fixtures version-control friendly and ensures fast CI execution.

4. **Deterministic seeds** — All merge operations use `MergeConfig(seed=42)` to ensure reproducible results across runs. This is critical for both notebook reliability and CI testing.

5. **Visualizations match existing style** — Use matplotlib/seaborn visualizations following the pattern established in `quickstart.ipynb` and `advanced.ipynb`. This maintains consistency across the notebook suite.

### Common Pitfalls to Avoid

1. **Assuming data sources are always available** — Network may fail, APIs may be down, or user may be offline. Always include fixture fallback with `REFORMLAB_OFFLINE=1` detection.

2. **Skipping pedagogical explanations** — The core requirement is teaching, not just showing working code. Each merge step MUST have a markdown cell explaining the method and its assumptions in plain language understandable to non-statisticians.

3. **Missing determinism** — Without fixed seeds, notebook results will vary across runs, confusing users and breaking CI tests. Always use `MergeConfig(seed=42)` (or similar deterministic seed).

4. **Overcomplicating the example** — Keep the French household example focused on demonstrating the pipeline workflow, not on building a production-ready population. Use representative but minimal merge steps (3-4 steps is sufficient).

5. **Hardcoding paths** — Use `Path(__file__).parent.resolve()` pattern to resolve paths relative to notebook location, matching existing notebook pattern in `advanced.ipynb`.

### References

- **Population module public API**: `src/reformlab/population/__init__.py` — Exports loaders, methods, pipeline, validation classes
- **Pipeline builder documentation**: `src/reformlab/population/pipeline.py` — `PopulationPipeline` class with fluent API
- **Merge methods base**: `src/reformlab/population/methods/base.py` — `MergeMethod` protocol and `MergeConfig` dataclass
- **Assumption recording**: `src/reformlab/population/assumptions.py` — `PipelineAssumptionChain.to_governance_entries()` method
- **Validation**: `src/reformlab/population/validation.py` — `PopulationValidator` class and `MarginalConstraint` dataclass
- **Existing notebook patterns**: `notebooks/quickstart.ipynb`, `notebooks/advanced.ipynb` — Reference for markdown style, code organization, visualization patterns
- **Story 11.6 synthesis**: `_bmad-output/implementation-artifacts/11-7-implement-population-validation-against-known-marginals-synthesis-final.md` — Reference for validation implementation
- **Project context**: `docs/project-context.md` — Critical rules for code style, testing, and development workflow

## Dev Agent Record

### Agent Model Used

glm-4.7 (zai-coding-plan/glm-4.7)

### Debug Log References

None (debug mode not enabled for this story creation).

### Completion Notes List

1. Analyzed existing population module implementation (loaders, methods, pipeline, validation)
2. Reviewed existing notebook patterns (quickstart, advanced) to match style
3. Checked sprint status to confirm stories 11.1-11.7 are done, 11.8 is in-progress
4. Examined antipatterns from previous stories to avoid common mistakes
5. Designed comprehensive task breakdown covering pipeline script, notebook, CI integration
6. Specified offline-first testing strategy with fixture fallback
7. Aligned with existing project structure (notebooks/, examples/, tests/fixtures/)
8. Incorporated pedagogical requirements from EPIC-11 scope notes

### File List

**New Files (4)**:
- `examples/populations/french_household_pipeline.py` — Standalone pipeline execution script
- `notebooks/population-french-household-example.ipynb` — Pedagogical notebook with explanations
- `tests/fixtures/populations/sources/insee_filosofi_2021_fixture.csv` — INSEE fixture (created programmatically in conftest)
- `tests/fixtures/populations/sources/eurostat_hhcomp_2022_fixture.csv` — Eurostat fixture (created programmatically in conftest)
- `tests/fixtures/populations/sources/ademe_energy_2023_fixture.csv` — ADEME fixture (created programmatically in conftest)
- `tests/fixtures/populations/sources/sdes_vehicles_2023_fixture.csv` — SDES fixture (created programmatically in conftest)

**Modified Files (3)**:
- `tests/population/conftest.py` — Add notebook execution and fixture path fixtures
- `tests/population/test_notebook.py` — New test file for notebook execution
- `.github/workflows/test.yml` (or equivalent) — Add notebook test step to CI

**Referenced Files**:
- `src/reformlab/population/__init__.py` — Public API exports
- `src/reformlab/population/pipeline.py` — `PopulationPipeline` class
- `src/reformlab/population/assumptions.py` — Assumption recording
- `src/reformlab/population/validation.py` — `PopulationValidator` class
- `notebooks/quickstart.ipynb` — Existing notebook pattern reference
- `notebooks/advanced.ipynb` — Existing notebook pattern reference
- `_bmad-output/implementation-artifacts/11-7-implement-population-validation-against-known-marginals-synthesis-final.md` — Previous story synthesis
