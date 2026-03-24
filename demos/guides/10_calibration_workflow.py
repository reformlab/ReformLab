"""ReformLab Calibration Workflow -- Fitting Taste Parameters to Observed Data.

Demonstrates the complete calibration lifecycle:
1. Load observed transition rates (calibration targets)
2. Build a CostMatrix and run the CalibrationEngine to fit beta parameters
3. Inspect convergence diagnostics and visualise training fit
4. Validate calibrated parameters against holdout data
5. Record calibration provenance in a RunManifest
6. Extract calibrated parameters and use them in a discrete choice simulation

Prerequisites: ReformLab installed with calibration and discrete choice modules.
Related guides: 08_discrete_choice_model, 09_population_generation
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pyarrow as pa
from matplotlib.patches import Patch

from reformlab.calibration import (
    CalibrationConfig,
    CalibrationEngine,
    CalibrationTarget,
    CalibrationTargetSet,
    capture_calibration_provenance,
    extract_calibrated_parameters,
    load_calibration_targets,
    make_calibration_reference,
    validate_holdout,
)
from reformlab.discrete_choice import (
    CostMatrix,
    TasteParameters,
    compute_probabilities,
    compute_utilities,
)
from reformlab.governance.manifest import RunManifest
from reformlab.visualization import plot_grouped_bars, show_figure

# ---------------------------------------------------------------------------
# Section 0: Setup
# ---------------------------------------------------------------------------
# Resolve paths relative to this script.
_SCRIPT_DIR = Path(__file__).parent
FIXTURES_DIR = (_SCRIPT_DIR / "../../tests/fixtures/calibration").resolve()

SEED = 42  # Deterministic seed for reproducibility

print("Calibration workflow API loaded")
print(f"Fixtures directory: {FIXTURES_DIR}")

# ---------------------------------------------------------------------------
# Section 1: Load Calibration Targets
# ---------------------------------------------------------------------------
#
# A calibration target records the observed fraction of households in a given
# from_state that chose a given to_state during a reference period, according
# to institutional data.
#
# Fields per row:
#   domain        -- decision domain (vehicle, heating, ...)
#   period        -- reference year for the observed data
#   from_state    -- current household state (origin)
#   to_state      -- chosen alternative (destination)
#   observed_rate -- fraction of households that made this choice
#   source_label  -- human-readable data source identifier

target_set = load_calibration_targets(FIXTURES_DIR / "valid_vehicle_targets.csv")

print(f"\nLoaded {len(target_set.targets)} calibration targets from valid_vehicle_targets.csv")
print()
print(f"{'domain':<10} {'period':<8} {'from_state':<12} {'to_state':<18} {'observed_rate':<15} {'source_label'}")
print("-" * 85)
for t in target_set.targets:
    print(f"{t.domain:<10} {t.period:<8} {t.from_state:<12} {t.to_state:<18} {t.observed_rate:<15.3f} {t.source_label}")

# Two from_state groups: petrol (4 alternatives) and ev (2 alternatives).
# Rates may sum to < 1.0 -- the remainder represents unclassified households.
#
# For this demo we use a simplified 2-alternative model (A and B) matching the
# conftest pattern, which is easier to reason about. The calibration mechanics
# are identical regardless of the number of alternatives.

# ---------------------------------------------------------------------------
# Section 2: Build Cost Matrix
# ---------------------------------------------------------------------------
#
# A CostMatrix is an N x M table where N = households, M = alternatives.
# Each cell [i, j] = cost for household i choosing alternative j.
# The calibration engine computes utility via V_ij = beta_cost * cost_ij.

training_cost_matrix = CostMatrix(
    table=pa.table({
        "A": pa.array([100.0, 150.0, 200.0]),
        "B": pa.array([200.0, 100.0, 300.0]),
    }),
    alternative_ids=("A", "B"),
)

training_from_states = pa.array(["petrol", "petrol", "diesel"])

print(f"\nTraining CostMatrix: {training_cost_matrix.n_households} households x {training_cost_matrix.n_alternatives} alternatives")
print(f"Alternative IDs: {training_cost_matrix.alternative_ids}")
print()
print("Cost matrix (EUR/year):")
print(f"  {'Household':<12} {'from_state':<12} {'Cost A':>10} {'Cost B':>10}")
print(f"  {'-'*46}")
cost_a = training_cost_matrix.table.column("A").to_pylist()
cost_b = training_cost_matrix.table.column("B").to_pylist()
from_list = training_from_states.to_pylist()
for i, (fs, ca, cb) in enumerate(zip(from_list, cost_a, cost_b)):
    print(f"  H{i:<11} {fs:<12} {ca:>10.0f} {cb:>10.0f}")

# H0 (petrol): A=100, B=200 -> A is clearly cheaper
# H1 (petrol): A=150, B=100 -> B is cheaper
# H2 (diesel): A=200, B=300 -> A is cheaper

# ---------------------------------------------------------------------------
# Section 3: Run Calibration Engine
# ---------------------------------------------------------------------------
#
# The calibration engine iteratively adjusts beta_cost until the model's
# simulated transition rates match the observed rates. Each iteration:
#   1. Compute utilities: V_ij = beta * cost_ij
#   2. Compute choice probabilities via the logit model
#   3. Aggregate probabilities by from_state to get simulated rates
#   4. Evaluate objective (MSE between observed and simulated rates)
#   5. Adjust beta and repeat until convergence

# Build simplified training targets matching the 2-alternative cost matrix.
training_target_set = CalibrationTargetSet(
    targets=(
        CalibrationTarget(
            domain="vehicle", period=2022,
            from_state="petrol", to_state="A",
            observed_rate=0.40, source_label="SDES 2022 demo",
        ),
        CalibrationTarget(
            domain="vehicle", period=2022,
            from_state="petrol", to_state="B",
            observed_rate=0.55, source_label="SDES 2022 demo",
        ),
        CalibrationTarget(
            domain="vehicle", period=2022,
            from_state="diesel", to_state="A",
            observed_rate=0.60, source_label="SDES 2022 demo",
        ),
    )
)

print(f"\nTraining target set: {len(training_target_set.targets)} targets")
for t in training_target_set.targets:
    print(f"  {t.from_state} -> {t.to_state}: observed_rate={t.observed_rate:.2f}")

# Configure and run the calibration engine.
config = CalibrationConfig(
    targets=training_target_set,
    cost_matrix=training_cost_matrix,
    from_states=training_from_states,
    domain="vehicle",
    initial_beta=-0.01,
    objective_type="mse",
    method="L-BFGS-B",
    max_iterations=100,
    rate_tolerance=0.05,
)

engine = CalibrationEngine(config=config)
result = engine.calibrate()

print("\nCalibration complete!")
print()
print(f"{'Diagnostic':<30} {'Value'}")
print("-" * 50)
print(f"{'Optimised beta_cost':<30} {result.optimized_parameters.beta_cost:.6f}")
print(f"{'Convergence flag':<30} {result.convergence_flag}")
print(f"{'Iterations':<30} {result.iterations}")
print(f"{'Gradient norm':<30} {result.gradient_norm}")
print(f"{'Method':<30} {result.method}")
print(f"{'Objective type':<30} {result.objective_type}")
print(f"{'Final objective value':<30} {result.objective_value:.8f}")
print(f"{'All within tolerance':<30} {result.all_within_tolerance}")

# Per-target rate comparisons.
print("\nPer-target rate comparisons:")
print()
print(f"  {'from_state':<12} {'to_state':<10} {'observed':>10} {'simulated':>10} {'abs_error':>10} {'within_tol':>12}")
print(f"  {'-'*57}")
for rc in result.rate_comparisons:
    print(
        f"  {rc.from_state:<12} {rc.to_state:<10} "
        f"{rc.observed_rate:>10.4f} {rc.simulated_rate:>10.4f} "
        f"{rc.absolute_error:>10.4f} {str(rc.within_tolerance):>12}"
    )

# ---------------------------------------------------------------------------
# Section 4: Visualize Training Fit
# ---------------------------------------------------------------------------
#
# A bar chart comparing observed_rate vs simulated_rate per target, with
# tolerance threshold bands.

target_labels = [f"{rc.from_state} -> {rc.to_state}" for rc in result.rate_comparisons]
fig, ax = plot_grouped_bars(
    target_labels,
    {
        "Observed": [rc.observed_rate for rc in result.rate_comparisons],
        "Simulated": [rc.simulated_rate for rc in result.rate_comparisons],
    },
    title="Training: Observed vs Simulated Transition Rates",
    xlabel="Transition (from_state -> to_state)",
    ylabel="Rate",
    colors=["#2196F3", "#FF9800"],
    xtick_rotation=15,
    ylim=(0, 1.0),
)

# Show tolerance bands around each observed rate.
observed_rates = [rc.observed_rate for rc in result.rate_comparisons]
x_positions = np.arange(len(observed_rates))
tol = config.rate_tolerance

for i, obs in enumerate(observed_rates):
    ax.fill_between(
        [i - 0.4, i + 0.4],
        obs - tol, obs + tol,
        color="red", alpha=0.10, zorder=0,
    )
    ax.hlines(
        [obs - tol, obs + tol], i - 0.4, i + 0.4,
        colors="red", linestyles="--", alpha=0.5, linewidths=0.8,
    )

ax.legend(
    handles=[*ax.get_legend_handles_labels()[0],
             Patch(facecolor="red", alpha=0.15, edgecolor="red",
                   linestyle="--", label=f"+/-{tol} tolerance")],
)
show_figure(fig)

print(f"All within tolerance (+/-{config.rate_tolerance}): {result.all_within_tolerance}")

# ---------------------------------------------------------------------------
# Section 5: Holdout Validation
# ---------------------------------------------------------------------------
#
# Holdout validation asks: does the calibrated beta generalise to a different
# time period? We use 2023 data to validate a model calibrated on 2022 data.

holdout_cost_matrix = CostMatrix(
    table=pa.table({
        "A": pa.array([110.0, 140.0, 210.0]),
        "B": pa.array([190.0, 110.0, 280.0]),
    }),
    alternative_ids=("A", "B"),
)
holdout_from_states = pa.array(["petrol", "petrol", "diesel"])

holdout_target_set = load_calibration_targets(FIXTURES_DIR / "holdout_vehicle_targets.csv")

print(f"\nHoldout CostMatrix: {holdout_cost_matrix.n_households} households")
print(f"Holdout targets: {len(holdout_target_set.targets)} targets (period=2023)")
print()
for t in holdout_target_set.targets:
    print(f"  {t.from_state} -> {t.to_state}: observed_rate={t.observed_rate:.2f} (period={t.period})")

# Validate calibrated parameters on holdout data.
holdout_result = validate_holdout(
    result,
    holdout_target_set,
    holdout_cost_matrix,
    holdout_from_states,
    rate_tolerance=config.rate_tolerance,
)

print(f"\nHoldout validation complete for domain={holdout_result.domain!r}")

# Side-by-side training vs holdout fit metrics.
print(f"\n{'Metric':<25} {'Training':>12} {'Holdout':>12}")
print("-" * 50)
print(f"{'MSE':<25} {holdout_result.training_fit.mse:>12.6f} {holdout_result.holdout_fit.mse:>12.6f}")
print(f"{'MAE':<25} {holdout_result.training_fit.mae:>12.6f} {holdout_result.holdout_fit.mae:>12.6f}")
print(f"{'Targets':<25} {holdout_result.training_fit.n_targets:>12d} {holdout_result.holdout_fit.n_targets:>12d}")
print(f"{'All Within Tolerance':<25} {str(holdout_result.training_fit.all_within_tolerance):>12} {str(holdout_result.holdout_fit.all_within_tolerance):>12}")
print()
print("Holdout per-target comparisons:")
for rc in holdout_result.holdout_rate_comparisons:
    print(f"  {rc.from_state} -> {rc.to_state}: obs={rc.observed_rate:.3f} sim={rc.simulated_rate:.3f} err={rc.absolute_error:.3f}")

# ---------------------------------------------------------------------------
# Section 6: Governance Provenance
# ---------------------------------------------------------------------------
#
# Every calibration run produces a beta coefficient that influences downstream
# simulations. capture_calibration_provenance() aggregates all relevant entries
# for recording in a RunManifest.

entries = capture_calibration_provenance(
    result,
    target_set=training_target_set,
    holdout_result=holdout_result,
)

print(f"\nGovernance entries captured: {len(entries)}")
print()
for entry in entries:
    print(f"Key: {entry['key']}")
    print(f"  source     : {entry['source']}")
    print(f"  is_default : {entry['is_default']}")
    value = entry['value']
    if isinstance(value, dict):
        for k, v in value.items():
            print(f"  {k:<28}: {v}")
    print()

# Create a calibration reference entry (links simulation back to calibration run).
ref_entry = make_calibration_reference("calib-run-2026-03-07-v1")
print("Calibration reference entry:")
print(f"  key        : {ref_entry['key']}")
print(f"  value      : {ref_entry['value']}")
print(f"  source     : {ref_entry['source']}")
print()

# Combine calibration entries + reference entry for a complete manifest.
manifest_assumptions = [*entries, ref_entry]
manifest = RunManifest(
    manifest_id="demo-manifest-2026-03-07",
    created_at="2026-03-07T00:00:00",
    engine_version="0.1.0",
    openfisca_version="44.0.0",
    adapter_version="0.1.0",
    scenario_version="v1",
    assumptions=manifest_assumptions,
)
print(f"RunManifest created with {len(manifest.assumptions)} assumption entries")
print(f"Assumption keys: {[a['key'] for a in manifest.assumptions]}")

# ---------------------------------------------------------------------------
# Section 7: Parameter Round-Trip
# ---------------------------------------------------------------------------
#
# When a simulation uses calibrated parameters from a prior calibration run,
# beta must be recovered exactly from the manifest -- not re-calibrated.
# extract_calibrated_parameters() performs this extraction.

extracted = extract_calibrated_parameters(entries, "vehicle")

print(f"\nExtracted TasteParameters:")
print(f"  extracted.beta_cost  = {extracted.beta_cost:.8f}")
print(f"  original  beta_cost  = {result.optimized_parameters.beta_cost:.8f}")
print()

# Verify exact equality (the manifest preserves the exact float value).
assert extracted.beta_cost == result.optimized_parameters.beta_cost, (
    f"Round-trip mismatch: {extracted.beta_cost} != {result.optimized_parameters.beta_cost}"
)
print("Exact equality confirmed: manifest round-trip preserves beta_cost perfectly")

reconstructed = TasteParameters(beta_cost=extracted.beta_cost)
assert reconstructed.beta_cost == extracted.beta_cost
print(f"TasteParameters({reconstructed.beta_cost:.6f}) reconstructed successfully")

# ---------------------------------------------------------------------------
# Section 8: Using Calibrated Parameters in Simulation
# ---------------------------------------------------------------------------
#
# Pass the extracted TasteParameters to compute_utilities() and
# compute_probabilities() -- the same functions used inside the orchestrator.

utilities = compute_utilities(training_cost_matrix, extracted)
probabilities = compute_probabilities(utilities)

print(f"\nCalibrated beta_cost = {extracted.beta_cost:.6f}")
print()
print("Per-household choice probability matrix:")
print()
print(f"  {'Household':<12} {'from_state':<12} {'P(choose A)':>12} {'P(choose B)':>12}")
print(f"  {'-'*50}")
prob_a = probabilities.column("A").to_pylist()
prob_b = probabilities.column("B").to_pylist()
for i, (fs, pa_val, pb_val) in enumerate(zip(from_list, prob_a, prob_b)):
    print(f"  H{i:<11} {fs:<12} {pa_val:>12.4f} {pb_val:>12.4f}")

print()
print("Verification: all probability rows sum to 1.0")
for i, (pa_val, pb_val) in enumerate(zip(prob_a, prob_b)):
    row_sum = pa_val + pb_val
    assert abs(row_sum - 1.0) < 1e-10, f"H{i}: probability sum = {row_sum}"
    print(f"  H{i}: P(A) + P(B) = {pa_val:.4f} + {pb_val:.4f} = {row_sum:.4f}")

# Visualise the per-household probability matrix.
household_labels = [f"H{i} ({fs})" for i, fs in enumerate(from_list)]
fig, ax = plot_grouped_bars(
    household_labels,
    {
        "P(choose A)": prob_a,
        "P(choose B)": prob_b,
    },
    title=f"Per-Household Choice Probabilities (calibrated beta_cost = {extracted.beta_cost:.4f})",
    xlabel="Household",
    ylabel="Choice Probability",
    colors=["#4CAF50", "#E91E63"],
    ylim=(0, 1.0),
)
show_figure(fig)

print("Calibrated beta feeds correctly through the discrete choice pipeline")

# ---------------------------------------------------------------------------
# Section 9: Summary
# ---------------------------------------------------------------------------
#
# Calibration Workflow Recap:
#   1. Load calibration targets        -> CalibrationTargetSet
#   2. Build cost matrix               -> CostMatrix
#   3. Run calibration engine           -> CalibrationResult (optimised beta)
#   4. Visualise training fit           -> Observed vs simulated bar chart
#   5. Validate on holdout data         -> HoldoutValidationResult
#   6. Record governance provenance     -> AssumptionEntry list -> RunManifest
#   7. Extract parameters               -> TasteParameters (exact beta)
#   8. Run simulation                   -> Choice probabilities
#
# Adapting for production:
#   - Larger populations (1000+ households) for better calibration quality
#   - Real institutional data (ADEME, SDES) via load_calibration_targets()
#   - Multiple domains (vehicle + heating) with separate CalibrationEngine runs
#   - log_likelihood objective for statistically principled estimation
