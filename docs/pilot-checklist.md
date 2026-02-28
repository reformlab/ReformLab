# ReformLab Phase 1 Pilot Checklist

**Purpose:** This checklist guides external pilot users through the complete ReformLab carbon-tax workflow validation process. It ensures independent execution from documentation alone and validates Phase 1 exit criteria.

**Target audience:** Researchers or policy analysts unfamiliar with the ReformLab codebase.

**Time estimate:** 60-90 minutes (including installation, notebook execution, and verification).

---

## Prerequisites

Before starting, ensure you have:

- **Python 3.13+** installed (`python --version` to check)
- **pip** package manager (included with Python)
- **16 GB RAM** recommended for comfortable execution
- **Internet connection** for initial package installation (offline after that)
- **macOS, Linux, or Windows** (tested on macOS Darwin 25.3.0, Linux expected to work)

No API keys, data downloads, or external services are required.

---

## Part 1: Installation and API Smoke Test (10 minutes)

### Step 1.1: Create a fresh virtual environment

```bash
# Create a clean Python environment
python3 -m venv reformlab-pilot-env

# Activate the environment
# On macOS/Linux:
source reformlab-pilot-env/bin/activate
# On Windows:
# reformlab-pilot-env\Scripts\activate

# Verify Python version
python --version  # Should be 3.13 or higher
```

**Expected result:** Virtual environment activated, Python 3.13+ confirmed.

### Step 1.2: Install ReformLab

For the pilot, install from the provided wheel file or from the source distribution:

```bash
# Option A: Install from wheel (if provided)
pip install reformlab-0.1.0-py3-none-any.whl

# Option B: Install from source (if in the repository)
# cd reformlab
# pip install .
```

**Expected result:** Installation completes without errors.

### Step 1.3: Verify installation with API smoke test

```bash
python -c "import reformlab; print('✓ ReformLab installed successfully')"
```

**Expected result:** Prints `✓ ReformLab installed successfully`.

### Step 1.4: Run minimal API test

```bash
python << 'EOF'
from reformlab import ScenarioConfig, RunConfig

# Verify key classes are importable
scenario = ScenarioConfig(
    template_name='carbon-tax',
    parameters={'rate_schedule': {2025: 44.0}},
    start_year=2025,
    end_year=2025
)
config = RunConfig(scenario=scenario, seed=42)

print('✓ API smoke test passed')
print(f'  - ScenarioConfig created: {scenario.template_name}')
print(f'  - RunConfig created with seed: {config.seed}')
EOF
```

**Expected result:**
```
✓ API smoke test passed
  - ScenarioConfig created: carbon-tax
  - RunConfig created with seed: 42
```

---

## Part 2: Quickstart Notebook Execution (20 minutes)

### Step 2.1: Locate the quickstart notebook

The quickstart notebook is located at: `notebooks/quickstart.ipynb`

Open it in Jupyter:

```bash
# Install Jupyter if not already available
pip install jupyter

# Launch Jupyter
jupyter notebook notebooks/quickstart.ipynb
```

**Expected result:** Jupyter opens in your browser with the quickstart notebook loaded.

### Step 2.2: Execute all cells in order

In Jupyter, use `Run All Cells` (or `Kernel → Restart & Run All`).

**Expected outcomes:**

1. **Cell 1-6**: Imports, configuration, and first simulation run complete without errors
2. **Cell 8**: Panel data table displays with 100 rows × multiple columns
3. **Cell 11**: Distributional indicators computed (should show ~50 indicator records)
4. **Cell 13**: Bar chart displays "Carbon Tax Burden by Income Decile" (10 bars, blue)
5. **Cell 15-16**: Second simulation with higher rate (€100/tCO2) completes
6. **Cell 18**: Side-by-side comparison chart shows baseline vs. reform (gray and coral bars)
7. **Cell 21-22**: Run manifest displays with unique manifest ID, seeds, parameters
8. **Cell 26**: Export actions complete, CSV and Parquet files created in temp directory
9. **Cell 25**: Indicator export completes successfully

**Critical check:** All cells execute without `NameError`, `ImportError`, or `AttributeError`. Charts render correctly.

### Step 2.3: Verify outputs

After execution, verify:

- [ ] Manifest ID is a valid UUID (e.g., `3266035b-42d8-45a6-b013-37007446e9fb`)
- [ ] Seeds are logged (e.g., `{'master': 42}`)
- [ ] Carbon tax values are reasonable (e.g., €150-200 for €44/tCO2 rate)
- [ ] Exported CSV and Parquet files exist and contain data

---

## Part 3: Advanced Notebook Execution (30 minutes)

### Step 3.1: Locate the advanced notebook

The advanced notebook is located at: `notebooks/advanced.ipynb`

Open it in Jupyter:

```bash
jupyter notebook notebooks/advanced.ipynb
```

### Step 3.2: Execute all cells in order

Use `Kernel → Restart & Run All`.

**Expected outcomes:**

1. **Cell 1-6**: Multi-year scenario (2025-2034) with escalating carbon tax configures and runs
2. **Cell 8**: Panel output shows 1,000 rows (100 households × 10 years)
3. **Cell 10**: Line chart displays 10-year carbon tax progression (rising curve)
4. **Cell 14**: Stacked area chart shows vintage fleet evolution (pre-2020, 2020-2024, 2025+)
5. **Cell 18-20**: Baseline scenario (€44/tCO2 constant) runs and indicators compute
6. **Cell 22**: Comparison table with baseline/reform/delta columns displays
7. **Cell 24**: Side-by-side bar chart comparing baseline vs. reform by decile (2030)
8. **Cell 26**: Time-series plot of reform impact (delta) over years
9. **Cell 28**: Fiscal comparison chart shows revenue differences
10. **Cell 32-34**: Manifests display with lineage metadata
11. **Cell 36-37**: Reproducibility check confirms deterministic reruns
12. **Cell 39**: Manifest exported as JSON excerpt
13. **Cell 41-42**: Export actions complete for panel, indicators, and comparison tables

**Critical check:** Multi-year execution completes in reasonable time (< 10 seconds). Comparison tables include `delta_reform` and `pct_delta_reform` columns.

### Step 3.3: Verify multi-year outputs

After execution, verify:

- [ ] Panel contains exactly 1,000 rows (100 households × 10 years)
- [ ] Years 2025-2034 are all represented in the panel
- [ ] Baseline and reform manifest IDs are different
- [ ] Reproducibility check confirms "✓ Rerun matches original output exactly (deterministic!)"
- [ ] Exported Parquet files preserve schema and metadata

---

## Part 4: Credibility and Reproducibility Verification (15 minutes)

### Step 4.1: Run benchmark verification

ReformLab includes a benchmark suite to validate simulation outputs against expected tolerances.

If you have access to the test suite:

```bash
# Install development dependencies
pip install pytest pytest-cov

# Run benchmark tests
pytest -m benchmark -v
```

**Expected result:** All benchmark tests pass (e.g., 7 passed).

**If tests are not available:** The quickstart and advanced notebooks already include credibility checks via indicator computation and visual inspection.

### Step 4.2: Verify reproducibility manually

Run the following script to confirm deterministic outputs:

```python
from reformlab import (
    RunConfig,
    ScenarioConfig,
    create_quickstart_adapter,
    run_scenario,
)

# Run 1
config = RunConfig(
    scenario=ScenarioConfig(
        template_name="carbon-tax",
        parameters={"rate_schedule": {2025: 44.0}},
        start_year=2025,
        end_year=2025,
    ),
    seed=42,
)

adapter1 = create_quickstart_adapter(
    carbon_tax_rate=44.0,
    year=2025,
    household_count=100,
)

result1 = run_scenario(config, adapter=adapter1)

# Run 2 with identical config
adapter2 = create_quickstart_adapter(
    carbon_tax_rate=44.0,
    year=2025,
    household_count=100,
)

result2 = run_scenario(config, adapter=adapter2)

# Compare outputs
panel1 = result1.panel_output.table
panel2 = result2.panel_output.table

tax1 = panel1["carbon_tax"].to_pylist()
tax2 = panel2["carbon_tax"].to_pylist()

if tax1 == tax2:
    print("✓ Reproducibility check PASSED: Identical outputs with same seed")
else:
    print("✗ Reproducibility check FAILED")

print(f"\nSeeds match: {result1.manifest.seeds == result2.manifest.seeds}")
print(f"Parameters match: {result1.manifest.parameters == result2.manifest.parameters}")
```

**Expected result:**
```
✓ Reproducibility check PASSED: Identical outputs with same seed

Seeds match: True
Parameters match: True
```

---

## Part 5: Documentation Independence Check (10 minutes)

### Step 5.1: Review README and documentation

Verify that you could have completed the above steps using only the provided documentation:

- [ ] `README.md` clearly explains installation (`pip install reformlab`)
- [ ] Quickstart notebook is linked from README or docs
- [ ] Prerequisites are stated (Python 3.13+, no external data)
- [ ] API usage is demonstrated in notebooks

### Step 5.2: Identify friction points

Document any points where you needed to:

- Consult external resources (StackOverflow, OpenFisca docs, etc.)
- Make assumptions not stated in the documentation
- Debug errors due to unclear instructions
- Modify code to make examples work

**Action:** Share friction points with the ReformLab maintainers for documentation improvements.

---

## Part 6: Pilot Sign-Off

### Pilot Execution Summary

- [ ] **AC-1:** Clean install and API smoke test succeeded
- [ ] **AC-2:** Quickstart notebook ran without code edits
- [ ] **AC-3:** Advanced multi-year notebook ran end-to-end
- [ ] **AC-4:** Documentation was sufficient for independent execution
- [ ] **AC-5:** Benchmark checks passed (or credibility confirmed via visual inspection)
- [ ] **AC-6:** Reproducibility demonstrated via identical reruns
- [ ] **AC-7:** All required artifacts (notebooks, examples, docs) were accessible

### Environment Details

Record your execution environment for the pilot report:

- **OS:** (e.g., macOS Darwin 25.3.0)
- **Python version:** (e.g., Python 3.13.0)
- **ReformLab version:** (e.g., 0.1.0)
- **Total execution time:** (e.g., 75 minutes)
- **Issues encountered:** (list any blockers or friction points)

### Final Sign-Off

**Pilot outcome:** ☐ PASS ☑ PASS WITH MINOR ISSUES ☐ FAIL

**Comments:**

_[External pilot user adds comments here about the experience, credibility of results, and readiness for production use]_

---

## Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'reformlab'`

**Solution:** Ensure the virtual environment is activated and ReformLab is installed:

```bash
source reformlab-pilot-env/bin/activate
pip install reformlab
```

### Issue: Notebooks fail with `NameError: name 'export_dir' is not defined`

**Solution:** This indicates cells are out of order. Ensure you are using the latest version of the notebooks from the pilot distribution. The cell that creates `export_dir` must run before cells that use it.

### Issue: Charts do not render in Jupyter

**Solution:** Ensure `matplotlib` is installed:

```bash
pip install matplotlib
```

### Issue: Benchmark tests fail

**Solution:** Check that you are using the exact ReformLab version specified in the pilot bundle. Version mismatches can cause reference value differences.

### Issue: Performance is slow (multi-year runs take > 30 seconds)

**Solution:** Ensure you have at least 16 GB RAM available. Close other memory-intensive applications. Consider reducing `household_count` in test runs.

---

## Next Steps After Pilot

If the pilot is successful:

1. **Production deployment:** Install ReformLab on your production environment
2. **Custom scenarios:** Build your own scenario templates (see API documentation)
3. **Integration:** Export outputs to your preferred analysis tools (R, Stata, Tableau, etc.)
4. **Collaboration:** Share run manifests with colleagues for reproducibility
5. **Feedback:** Report issues or feature requests via GitHub

---

**End of Pilot Checklist**

For questions or support, see the project documentation or contact the ReformLab maintainers.
