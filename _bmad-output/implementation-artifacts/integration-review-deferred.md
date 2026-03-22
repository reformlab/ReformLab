# Integration Review — Deferred Findings

**Source:** Adversarial integration review, 2026-03-20
**Status:** Known limitations — not planned for implementation

These findings don't break current functionality. They are documented here for future reference.

---

## F6: Multi-entity `entity_tables` never consumed (Medium)

**What:** `ComputationResult.entity_tables` (dict of PyArrow tables) is declared in `src/reformlab/computation/types.py` but `PanelOutput.from_orchestrator_result()` only processes `output_fields`. Secondary entity tables are silently dropped.

**Where:** `src/reformlab/orchestrator/panel.py` — `from_orchestrator_result()` method

**Impact:** Blocks future multi-entity scenarios (households + individuals). Harmless for current single-entity use.

**When to fix:** When multi-entity support becomes a requirement (likely Phase 3+).

---

## F7: Energy column units not enforced (Medium)

**What:** `SYNTHETIC_POPULATION_SCHEMA` defines `energy_transport_fuel`, `energy_heating_fuel`, `energy_natural_gas` as `float64` with no unit metadata. Carbon tax computation assumes liters (fuel) and m³ (gas). Supplying data in kWh or kg produces silently wrong results.

**Where:** `src/reformlab/data/schemas.py` — schema definition; `src/reformlab/templates/carbon_tax/compute.py` — unit assumptions

**Impact:** Will bite when integrating real data sources with different unit conventions.

**When to fix:** When real data sources are integrated (INSEE, SDES). Consider adding unit metadata to `DataSchema` or documenting units in column descriptions.

---

## F9: Calibration provenance captured from first year only (Low)

**What:** `capture_discrete_choice_parameters()` in `src/reformlab/governance/capture.py:354` extracts taste parameters from the first year containing a decision log, assuming parameters are consistent across years.

**Where:** `src/reformlab/governance/capture.py` — `capture_discrete_choice_parameters()` function

**Impact:** Correct for current static-calibration design. Would be a latent bug if adaptive calibration (year-varying taste parameters) is ever implemented.

**When to fix:** If/when adaptive calibration becomes a feature.

---

## F10: Population immutable across multi-year projections (Low)

**What:** `ComputationStep` stores population at init time and reuses the same table for all years. No aging, household formation, or fleet turnover within the orchestration loop.

**Where:** `src/reformlab/orchestrator/computation_step.py` — `self._population` fixed at init

**Impact:** Architecturally intentional (documented in CLAUDE.md: "orchestrator is not a computation engine"). Limits realism of multi-year projections but is by design.

**When to fix:** Not a bug. If population dynamics are needed, they would be a separate `PopulationEvolutionStep` in the pipeline. The `VintageTransitionStep` already handles asset aging as a separate concern.

---

## F11: Welfare comparison silently filtered in portfolio comparison (Low)

**What:** The comparison endpoint at `src/reformlab/server/routes/indicators.py` filters out `"welfare"` from `indicator_types` before calling `compare_portfolios()` because the domain layer raises `ValueError`. Users requesting welfare comparison silently receive no welfare data.

**Where:** `src/reformlab/server/routes/indicators.py` — welfare filtering logic

**Impact:** Silent data omission. Should either support multi-run welfare comparison or return an explicit warning/error.

**When to fix:** When welfare comparison for >2 runs is implemented in the indicators layer.

---

## F12: Replication reproduction doesn't verify adapter version match (Low)

**What:** `reproduce_from_package()` takes an `adapter` parameter but doesn't verify it matches the `adapter_version` recorded in the manifest. A user could reproduce with a different adapter version and get different results that still "pass" within tolerance.

**Where:** `src/reformlab/governance/replication.py` — `reproduce_from_package()` function

**Impact:** Undermines reproducibility guarantees in edge cases. The version is recorded but not enforced.

**When to fix:** When replication packages are shared externally and adapter version pinning matters. Add a version check with a `--force` flag to override.
