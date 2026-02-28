# Story 7.4: External Pilot User Can Run Complete Carbon-Tax Workflow

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As an **external pilot user (researcher or policy analyst unfamiliar with the codebase)**,
I want **to install reformlab from a shipped package, run the complete carbon-tax workflow end-to-end using documentation alone, and verify the results are credible**,
so that **I can independently validate the platform's readiness for production policy analysis and confirm Phase 1 exit criteria are met**.

## Acceptance Criteria

From backlog (BKL-704), aligned with FR35, NFR19, and Phase 1 exit criteria.

1. **AC-1: Clean install completes successfully**
   - Given a fresh Python 3.13+ environment with no prior ReformLab installation
   - When `pip install reformlab` is run
   - Then the package installs with all required dependencies and no errors

2. **AC-2: Carbon-tax quickstart runs without modification**
   - Given the installed package and shipped quickstart notebook
   - When the notebook is executed cell-by-cell
   - Then all cells complete without errors and produce distributional charts

3. **AC-3: Advanced notebook completes end-to-end**
   - Given the installed package and shipped advanced notebook
   - When the notebook is executed in full
   - Then multi-year projection with vintage tracking, baseline/reform comparison, and indicator exports complete successfully

4. **AC-4: Documentation enables independent execution**
   - Given the shipped documentation (README, quickstart notebook, API reference)
   - When an external user follows the instructions
   - Then they can complete the carbon-tax workflow without external assistance

5. **AC-5: Results are verifiable against benchmarks**
   - Given completed simulation outputs
   - When compared to the benchmark reference values shipped with the package
   - Then distributional patterns and aggregate indicators match within documented tolerances

6. **AC-6: Pilot package is self-contained**
   - Given the shipped package contents
   - When inspected
   - Then example datasets, templates, notebooks, and documentation are all included without requiring external downloads

7. **AC-7: Run manifests enable reproducibility**
   - Given a completed pilot workflow
   - When the run manifest is inspected
   - Then all parameters, seeds, versions, and assumptions are recorded
   - And a second run with the same manifest inputs produces identical outputs

## Dependencies

Dependency gate: if any hard dependency below is not `done`, set this story to `blocked`.

- **Hard dependencies (from backlog BKL-704):**
  - Story 6-2 (BKL-602): Quickstart notebook — DONE
  - Story 6-3 (BKL-603): Advanced notebook — DONE
  - Story 5-1 (BKL-501): Immutable run manifest schema — DONE

- **Integration dependencies (for complete pilot experience):**
  - Story 1-1 to 1-8: Computation adapter and data layer — all DONE
  - Story 2-1 to 2-7: Scenario templates and registry — all DONE
  - Story 3-1 to 3-7: Dynamic orchestrator and vintage tracking — all DONE
  - Story 4-1 to 4-6: Indicators and comparison — all DONE
  - Story 5-2 to 5-5: Governance and reproducibility — all DONE
  - Story 6-1 (BKL-601): Stable Python API — DONE
  - Story 6-5 (BKL-605): Export actions — DONE
  - Story 7-1 (BKL-701): Benchmark verification — DONE
  - Story 7-2 (BKL-702): Memory warnings — DONE
  - Story 7-3 (BKL-703): CI quality gates — DONE

- **Follow-on stories (not blocking):**
  - Story 7-5 (BKL-705): Define Phase 1 exit checklist and pilot sign-off criteria

## Tasks / Subtasks

- [ ] **Task 1: Verify package installation on clean environment** (AC: 1, 6)
  - [ ] Create a fresh Python 3.13+ virtual environment
  - [ ] Run `pip install reformlab` (from local build or TestPyPI)
  - [ ] Verify all dependencies install correctly
  - [ ] Confirm `import reformlab` works without errors
  - [ ] Document any installation issues or missing dependencies

- [ ] **Task 2: Audit shipped package contents** (AC: 6)
  - [ ] Verify `pyproject.toml` includes all required entries: examples, notebooks, data
  - [ ] Confirm MANIFEST.in (if used) or pyproject.toml `[tool.setuptools.package-data]` includes:
    - `notebooks/quickstart.ipynb`
    - `notebooks/advanced.ipynb`
    - Example YAML workflow configurations
    - Benchmark reference data
    - Synthetic population fixtures
  - [ ] Verify package size is reasonable (< 50MB for core package)
  - [ ] Document what is NOT included and should be (if any)

- [ ] **Task 3: Validate quickstart notebook execution** (AC: 2, 4)
  - [ ] Run `quickstart.ipynb` on fresh install environment
  - [ ] Verify all cells execute without errors
  - [ ] Verify distributional charts are produced
  - [ ] Verify manifest is generated
  - [ ] Time the total execution (target: < 30 minutes including reading)
  - [ ] Document any confusing steps or missing explanations

- [ ] **Task 4: Validate advanced notebook execution** (AC: 3, 4)
  - [ ] Run `advanced.ipynb` on fresh install environment
  - [ ] Verify multi-year projection (e.g., 2025-2030) completes
  - [ ] Verify vintage tracking state is visible in outputs
  - [ ] Verify baseline/reform comparison produces side-by-side tables
  - [ ] Verify indicator exports (CSV/Parquet) work correctly
  - [ ] Document any issues or missing functionality

- [ ] **Task 5: Benchmark verification** (AC: 5)
  - [ ] Locate benchmark reference values in shipped package
  - [ ] Run benchmark suite against quickstart outputs: `run_benchmarks(result=result)`
  - [ ] Verify all benchmark tests pass
  - [ ] If any fail: document expected vs actual, determine if tolerance needs adjustment
  - [ ] Confirm distributional patterns match known carbon tax literature (qualitative check)

- [ ] **Task 6: Reproducibility verification** (AC: 7)
  - [ ] Complete a full pilot run and save the manifest
  - [ ] Re-run with identical seed and configuration
  - [ ] Compare output hashes (should be identical)
  - [ ] Cross-machine test: run on a different OS/Python environment with same versions
  - [ ] Document any reproducibility issues

- [ ] **Task 7: Documentation gap analysis** (AC: 4)
  - [ ] Review README for clarity and completeness
  - [ ] Review quickstart notebook narrative
  - [ ] Review advanced notebook narrative
  - [ ] Identify missing explanations or confusing sections
  - [ ] Add missing documentation or clarifications
  - [ ] Ensure YAML template documentation exists
  - [ ] Ensure API reference docstrings are complete

- [ ] **Task 8: Create pilot onboarding checklist** (AC: all)
  - [ ] Create `docs/pilot-checklist.md` with step-by-step instructions
  - [ ] Include: environment setup, installation, first run, verification steps
  - [ ] Include: common troubleshooting guidance
  - [ ] Include: links to additional resources

- [ ] **Task 9: Final pilot validation** (AC: all)
  - [ ] Complete full workflow as if external user (no codebase knowledge)
  - [ ] Record any friction points or errors
  - [ ] Fix blocking issues
  - [ ] Document non-blocking issues for future improvement
  - [ ] Confirm pilot readiness

## Dev Notes

### Architecture Alignment

This story validates the complete Phase 1 platform against external adoption requirements. It is the capstone story for Epic 7 (Trusted Outputs and External Pilot Validation) and directly gates Phase 1 exit.

**PRD Context:**
- FR35: "User can access template authoring and dynamic-run documentation with reproducible examples"
- NFR19: "All shipped examples run end-to-end without modification on a fresh install (tested in CI)"
- Phase 1 exit criterion: "At least one external pilot user runs the workflow and confirms credibility"

**User Journey Reference:**
- Alex (First-Time Installer): pip install → quickstart notebook → carbon tax charts in 15 minutes
- Sophie (Policy Analyst): YAML policy definition → scenario comparison → distributional analysis
- Marco (Researcher): Python API → Jupyter workflow → reproducible results via run manifests

### Current State Assessment

**What exists (all DONE):**
- Complete Python API (`src/reformlab/interfaces/api.py`) with `run_scenario()`, `ScenarioConfig`, `RunConfig`, `SimulationResult`
- Quickstart notebook (`notebooks/quickstart.ipynb`) demonstrating carbon tax workflow
- Advanced notebook (`notebooks/advanced.ipynb`) with multi-year projections
- Benchmark suite (`governance/benchmarking.py`) with `run_benchmarks()` API
- Memory warning system (`governance/memory.py`)
- CI quality gates with coverage enforcement
- Export actions (CSV/Parquet) in `SimulationResult.export_csv()` / `export_parquet()`
- Run manifest generation with full provenance

**What needs verification:**
- Package contents include all required artifacts when installed via pip
- Documentation is sufficient for independent external execution
- Benchmark tolerances are calibrated correctly
- Cross-machine reproducibility is confirmed

### Implementation Approach

This story is primarily a **validation and verification task**, not a feature implementation story. The work involves:

1. **Testing from external perspective**: Simulate being an external user with no codebase knowledge
2. **Package auditing**: Ensure pip-installable package is complete and self-contained
3. **Documentation polish**: Fill gaps in explanations and instructions
4. **Benchmark calibration**: Confirm shipped benchmarks match expected outputs
5. **Reproducibility testing**: Verify manifest-based reruns produce identical results

**Key principle:** No new features. Fix only what is needed for a clean external pilot experience.

### Package Inclusion Verification

Check `pyproject.toml` for package data inclusion:

```toml
[tool.setuptools.package-data]
reformlab = [
    "py.typed",
    # Ensure these are included:
    # - Example workflows
    # - Benchmark references
    # - Synthetic population fixtures
]
```

Notebooks are typically NOT included in the package itself but distributed via:
- GitHub repository clone
- Separate documentation site
- ReadTheDocs or similar

**Decision:** For pilot, ensure notebooks are:
1. Accessible from GitHub repository (clearly documented)
2. Runnable with a fresh `pip install reformlab`
3. Reference shipped synthetic data (no external downloads)

### Benchmark Reference Integration

From Story 7-1, the benchmark suite is in place. For pilot validation:

```python
from reformlab import run_scenario, run_benchmarks

result = run_scenario(config, adapter=adapter)
benchmark_result = run_benchmarks(result=result)

# Expected: all benchmarks pass
assert benchmark_result.all_passed
```

If benchmarks fail, investigate:
- Are reference values correct for current synthetic data?
- Are tolerances appropriate for floating-point variance?
- Is there a legitimate bug in the computation?

### Cross-Machine Reproducibility

To validate NFR7 (identical outputs across machines):

1. Run on Ubuntu (CI environment)
2. Run on macOS (development machine)
3. Run on Windows (if available)
4. Compare output hashes from manifests

Documented tolerances apply for floating-point differences. Document any platform-specific variance.

### Documentation Checklist

**README.md:**
- [ ] Clear installation instructions
- [ ] Link to quickstart notebook
- [ ] Link to API documentation
- [ ] Link to example workflows

**Quickstart notebook:**
- [ ] Prerequisites stated clearly
- [ ] All code cells self-contained
- [ ] Outputs explained
- [ ] Next steps clearly indicated

**Advanced notebook:**
- [ ] Multi-year workflow demonstrated
- [ ] Vintage tracking explained
- [ ] Baseline/reform comparison shown
- [ ] Export actions demonstrated

### Testing Standards

**Local validation:**
```bash
# Create fresh environment
uv venv --python 3.13 pilot-test
source pilot-test/bin/activate

# Install package
pip install reformlab

# Run quickstart notebook
cd notebooks
jupyter execute quickstart.ipynb

# Run advanced notebook
jupyter execute advanced.ipynb

# Verify benchmarks
python -c "from reformlab import run_scenario, run_benchmarks, ScenarioConfig, RunConfig, create_quickstart_adapter; adapter = create_quickstart_adapter(carbon_tax_rate=44.0, year=2025, household_count=100); config = RunConfig(scenario=ScenarioConfig(template_name='carbon-tax', parameters={'rate_schedule': {2025: 44.0}}, start_year=2025, end_year=2025), seed=42); result = run_scenario(config, adapter=adapter); benchmarks = run_benchmarks(result=result); print(benchmarks)"
```

### Scope Guardrails

**In scope:**
- Package content verification
- Notebook execution validation
- Documentation gap filling
- Benchmark calibration
- Reproducibility testing
- Pilot onboarding checklist creation

**Out of scope:**
- New feature development
- Major documentation rewrites
- Performance optimization
- GUI validation (covered by Story 6-4b)
- PyPI publishing (separate release process)

### Previous Story Intelligence

From Story 7-3 (enforce-ci-quality-gates):
- CI pipeline runs lint, type checks, tests, and coverage enforcement
- Coverage threshold is 80% for Phase 1
- All shipped examples are CI-validated via `pytest --nbmake`

From Story 7-1 (verify-simulation-outputs-against-benchmarks):
- Benchmark suite established with custom pytest marker `@pytest.mark.benchmark`
- Deterministic fixtures in `tests/benchmarks/`
- Tolerances documented for distributional indicators

From Story 7-2 (warn-before-exceeding-memory-limits):
- Memory warning system active for populations > 500k on 16GB RAM
- Warning displayed before execution, not as runtime error

Apply learnings:
- Test from external user perspective (no insider knowledge)
- Document any friction points clearly
- Ensure notebooks run without CI-specific environment variables

### Git Intelligence

Recent commits:
- `41b9ac8` overnight-build: 7-3-enforce-ci-quality-gates — code review (DONE)
- `77f94d9` overnight-build: 7-3-enforce-ci-quality-gates — dev story (DONE)

Pattern: Epic 7 stories are validation/hardening tasks. This story follows the same pattern — verify rather than build.

### File Structure Notes

**Files to verify (not create):**
- `notebooks/quickstart.ipynb` — must run on fresh install
- `notebooks/advanced.ipynb` — must run on fresh install
- `pyproject.toml` — package data inclusion
- `README.md` — installation and quickstart instructions

**Files to create:**
- `docs/pilot-checklist.md` — step-by-step pilot onboarding guide

**Files to potentially modify:**
- `README.md` — if documentation gaps found
- `notebooks/quickstart.ipynb` — if cell execution issues found
- `notebooks/advanced.ipynb` — if cell execution issues found
- `pyproject.toml` — if package data missing

### Project Structure Notes

- Alignment with existing project structure: all changes in standard locations
- No new subsystem directories needed
- Documentation goes in `docs/` directory

### References

- [Source: _bmad-output/planning-artifacts/phase-1-implementation-backlog-2026-02-25.md#BKL-704] — Story requirements and acceptance criteria
- [Source: _bmad-output/planning-artifacts/prd.md#FR35] — Documentation requirements
- [Source: _bmad-output/planning-artifacts/prd.md#NFR19] — Shipped examples CI-tested requirement
- [Source: _bmad-output/planning-artifacts/prd.md#Phase 1 Exit Criteria] — External pilot validation
- [Source: _bmad-output/planning-artifacts/architecture.md] — Package structure and deployment
- [Source: src/reformlab/interfaces/api.py] — Public API implementation
- [Source: notebooks/quickstart.ipynb] — Quickstart notebook
- [Source: notebooks/advanced.ipynb] — Advanced notebook
- [Source: _bmad-output/implementation-artifacts/7-3-enforce-ci-quality-gates.md] — Previous story patterns
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml] — Dependency completion status

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
