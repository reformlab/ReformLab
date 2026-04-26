---
title: Architect Spike — Investment Decisions: Technology-Set as a First-Class Concept
date: 2026-04-26
author: Architect agent (bmad-architect)
project: ReformLab
epic: EPIC-28
story: 28.0
status: draft (gates stories 28.1–28.5)
related_artifacts:
  - _bmad-output/planning-artifacts/sprint-change-proposal-2026-04-26.md (Section 4.2)
  - _bmad-output/planning-artifacts/prd.md (FR43, FR46, FR47, FR50, FR51)
  - _bmad-output/planning-artifacts/architecture.md (Section 3.1 Adapter Pattern)
---

# Architect Spike — Investment Decisions: Technology-Set as a First-Class Concept

## 1. Executive summary

The good news: most of the plumbing the user's mental model demands already exists.
`HeatingStateUpdateStep`, `VehicleStateUpdateStep`, and
`apply_choices_to_population` already write chosen alternatives back into the
population's entity table; `DecisionRecordStep` already snapshots per-domain
results into a per-year decision log; `panel.py` already injects
`{domain}_chosen` / `{domain}_probabilities` / `{domain}_utilities` columns into
the panel. What is missing is the **analyst-facing "technology set"** that ties
those moving parts together: a typed contract that lives on `EngineConfig`,
flows through the API, is consumed by an `EngineConfigCompiler` that builds the
step pipeline, and is recorded in the manifest with a stable version. The
recommended approach is therefore (a) add `EngineConfig.technology_set` as a
per-domain, versioned structure on the frontend; (b) lift it to a typed Python
`TechnologySet` value object that maps onto the existing
`HeatingDomainConfig` / `VehicleDomainConfig`; (c) introduce a single new
`EngineConfigCompiler` that builds the step pipeline (no adapter contract change);
(d) add an optional `incumbent_<domain>` column convention to `PopulationData`
with explicit, fail-loud validation; (e) extend the manifest with a
`technology_set` block. Backward compatibility is preserved by keeping every new
field optional and short-circuiting the new pipeline when
`investmentDecisionsEnabled === false`.

---

## 2. Technology-set contract

### 2.1 Frontend type

Add to `frontend/src/types/workspace.ts`:

```ts
export type DecisionDomainKey = "heating" | "vehicle";

export interface TechnologyAlternative {
  id: string;                    // stable id, e.g. "heat_pump"
  name: string;                  // display label, e.g. "Install Heat Pump"
  attributes: Record<string, string | number>;  // mirrors Python Alternative.attributes
  isIncumbentOnly?: boolean;     // true for "keep_current"-like alternatives
}

export interface DomainTechnologySet {
  domain: DecisionDomainKey;
  enabled: boolean;
  alternatives: TechnologyAlternative[];     // ordered, must include at least one
  referenceAlternativeId: string | null;     // for ASC normalization (logit ref)
  costColumn?: string;                        // override default cost column
}

export interface TechnologySet {
  version: string;                            // canonical-set version, e.g. "fr-2026-04-26"
  domains: Partial<Record<DecisionDomainKey, DomainTechnologySet>>;
}
```

Then extend `EngineConfig` (currently
`frontend/src/types/workspace.ts:66-75`):

```ts
export interface EngineConfig {
  // ... existing fields ...
  technologySet?: TechnologySet | null;       // null when investmentDecisionsEnabled === false
}
```

**Example payload**:

```ts
{
  version: "fr-default-2026-04-26",
  domains: {
    heating: {
      domain: "heating",
      enabled: true,
      alternatives: [
        { id: "keep_current", name: "Keep Current Heating", attributes: {}, isIncumbentOnly: true },
        { id: "heat_pump", name: "Install Heat Pump",
          attributes: { heating_type: "heat_pump", heating_age: 0,
                        heating_emissions_kgco2_kwh: 0.057 } },
        { id: "gas_boiler", name: "Install Gas Boiler",
          attributes: { heating_type: "gas", heating_age: 0,
                        heating_emissions_kgco2_kwh: 0.227 } }
      ],
      referenceAlternativeId: "keep_current"
    }
  }
}
```

### 2.2 Backend type — relation to existing `Alternative` / `ChoiceSet`

Introduce a new value object in `src/reformlab/discrete_choice/technology_set.py`:

```python
@dataclass(frozen=True)
class DomainTechnologySet:
    domain: str                                    # "heating" | "vehicle"
    enabled: bool
    alternatives: tuple[Alternative, ...]          # reuses existing Alternative
    reference_alternative_id: str | None
    cost_column: str | None = None

@dataclass(frozen=True)
class TechnologySet:
    version: str
    domains: dict[str, DomainTechnologySet]        # keyed by domain name

    def to_choice_set(self, domain: str) -> ChoiceSet:
        """Materialize a ChoiceSet for a given domain (existing type)."""
        return ChoiceSet(alternatives=self.domains[domain].alternatives)
```

This is **strictly a richer wrapper** around the existing `Alternative` /
`ChoiceSet` types. `DomainTechnologySet.alternatives` is a tuple of the same
`Alternative` instances `HeatingDomainConfig` / `VehicleDomainConfig` already
hold. We do **not** mutate `ChoiceSet`; we materialize one on demand via
`to_choice_set(domain)`.

**Why a new type instead of "list of ids"**: a list-of-ids would force a hidden
"global registry of canonical alternatives" and create a versioning footgun
(what if two scenarios at different times referenced the same id but with
different attributes?). Carrying the full `Alternative` payload means a
2026-04-26 scenario is reproducible from the manifest alone, even if the
canonical defaults shift.

### 2.3 Per-domain vs per-scenario — recommendation

**Per-domain.** A scenario can mix domains (heating + vehicle), and each domain
has its own incumbent column, cost column, eligibility filter, and population
schema requirements. A single flat list would force coupling between unrelated
concerns. The `domains: dict[str, DomainTechnologySet]` shape lets a scenario
enable heating only, vehicle only, or both, without conditional shapes.

### 2.4 Versioning and manifest reproducibility

Two layers of versioning, both required for FR51 / NFR9:

1. **Canonical-set version**: a string like `"fr-default-2026-04-26"` that names
   the published set the analyst started from. Stored on `TechnologySet.version`
   and surfaced in the wizard.
2. **Embedded snapshot**: the manifest stores the **fully-resolved**
   `TechnologySet` (every `DomainTechnologySet` with every `Alternative` and its
   `attributes`) — not a reference. This is the same pattern
   `RunManifest.policy` and `RunManifest.taste_parameters`
   (`src/reformlab/governance/manifest.py:171`) already use: snapshot, not
   reference.

Reproducibility rule: a 2026-04-26 run must reproduce bit-identically in 2027,
even if the canonical defaults evolve. The version string is for human
traceability; the snapshot is for determinism.

---

## 3. Population schema delta

### 3.1 Recommendation: one column per domain, in the menage entity table

```
incumbent_heating: dictionary<int32, utf8>  (PyArrow dictionary-encoded string)
incumbent_vehicle: dictionary<int32, utf8>
```

Each value is a `TechnologyAlternative.id` (e.g., `"gas_boiler"`,
`"buy_petrol"`). Dictionary encoding gives the type safety of a categorical
without the runtime cost of repeated long strings (relevant for 100k+
households).

### 3.2 Tradeoffs considered

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| One column per domain (`incumbent_heating`, `incumbent_vehicle`) | Simple to validate; aligns with `apply_choices_to_population` which already writes domain-prefixed columns; fits PyArrow dictionary encoding cleanly | More columns as domains grow | **Chosen** |
| Single keyed map column (`incumbent_tech: map<string, string>`) | One column regardless of domain count | PyArrow `map<>` is awkward to filter and join; harder to validate per-domain; harder to dictionary-encode | Rejected |
| Side-table (`incumbent_technologies` table joined on `household_id`) | Decouples decision-domain schema from population schema | Adds a join on every scenario step; breaks the "primary entity table is the truth" invariant the existing `apply_choices_to_population` relies on | Rejected |

### 3.3 PyArrow type choice

`pa.dictionary(pa.int32(), pa.utf8())` for incumbent columns. Rationale:

- Strings (alternative ids) are the natural format for both ingestion and
  manifest output.
- Dictionary encoding gives O(1) categorical filtering (`is_in`) which the
  eligibility filter (`evaluate_eligibility`) can use directly.
- Round-trips cleanly through Parquet (used by ResultStore).

**Already-used attribute columns** (e.g., `heating_type`, `vehicle_type`)
remain `pa.utf8()` and are written by `apply_choices_to_population`. The new
`incumbent_*` column is a **separate read-only-at-step-start** field that names
the alternative id rather than the underlying attribute label.

### 3.4 Backward compatibility

Validation rule (in a new
`src/reformlab/discrete_choice/population_validation.py`):

```python
def validate_population_for_technology_set(
    population: PopulationData,
    technology_set: TechnologySet,
    *,
    entity_key: str = "menage",
) -> list[str]:
    """Return a list of human-readable warnings; raise on hard schema errors.

    - If technology_set is None or no domains enabled: return [] (no-op).
    - For each enabled domain, check incumbent_<domain> column exists and
      every distinct value is in technology_set.domains[d].alternatives.
    - If column missing: return a warning. The orchestrator will treat
      every household as if incumbent == reference_alternative_id (with
      a manifest warning recorded).
    - If column present but values include unknown ids: raise (fail-loud).
    """
```

The hard rule: **scenarios that don't enable investment decisions never touch
the incumbent columns**. Validation is gated on
`technology_set is not None and any(d.enabled for d in domains.values())`.

### 3.5 Migration path for existing populations

| Population | Action |
|------------|--------|
| `fr-synthetic-2024` (bundled) | Add `incumbent_heating` and `incumbent_vehicle` columns at generation time, defaulted from the existing `heating_type` / `vehicle_type` attribute columns. One-time data migration committed alongside story 28.2. Does not change row count or seed semantics. |
| Quick Test Population | Same one-time migration. Tiny population (~10 households), trivial. |
| User-uploaded populations | **No migration**. If the user's population doesn't have `incumbent_*` columns and the user enables investment decisions, the orchestrator emits a manifest warning ("incumbent column missing; treating all households as `<reference_alt>`") and proceeds. Users with sophisticated populations can supply the columns themselves. |
| Generated populations from data-fusion (Story 22) | The fusion pipeline writes `heating_type` / `vehicle_type` already; the migration adds a one-line alternative-id default mapping at the end of fusion. |

---

## 4. Choice-result writeback model

### 4.1 Current state (already implemented)

The writeback machinery the user expects is **already built** in EPIC-14:

- `DiscreteChoiceStep` (`src/reformlab/discrete_choice/step.py:189`) computes
  the cost matrix.
- `LogitChoiceStep` draws the chosen alternative deterministically from the
  year-level seed.
- `HeatingStateUpdateStep.execute` /
  `VehicleStateUpdateStep.execute`
  (`src/reformlab/discrete_choice/heating.py:265`,
  `src/reformlab/discrete_choice/vehicle.py:380`) call
  `apply_choices_to_population`
  (`src/reformlab/discrete_choice/domain_utils.py:65`) to write the chosen
  alternative's attributes back into `population.tables[entity_key]`,
  returning a **new** `PopulationData` (no in-place mutation).
- `DecisionRecordStep`
  (`src/reformlab/discrete_choice/decision_record.py:82`) snapshots the
  per-domain `ChoiceResult` into `state.data[DECISION_LOG_KEY]` (a tuple
  of `DecisionRecord`).
- `PanelOutput.from_orchestrator_result`
  (`src/reformlab/orchestrator/panel.py:67`) injects domain-prefixed
  columns (`{domain}_chosen`, `{domain}_probabilities`, `{domain}_utilities`)
  per year.

### 4.2 What changes in EPIC-28

**Two surgical additions**, plus one explicit transition record that the panel
already half-supports:

#### 4.2.1 Add `incumbent_<domain>` rewrite to `apply_choices_to_population`

In `domain_utils.py:65`, after the `attr_key` loop, also write the chosen
alternative id to `incumbent_<domain>`. This is one extra `set_column` /
`append_column` call. The change is local to the existing helper and does
**not** affect the in-place-vs-new debate (it remains "return a new
PopulationData").

#### 4.2.2 Add a transition-record side table per year

Today, `DecisionRecord.chosen` records the to-tech but not the from-tech.
Add a sibling structure:

```python
@dataclass(frozen=True)
class TransitionRecord:
    domain_name: str
    year: int
    household_ids: pa.Array         # int64
    from_alternative_ids: pa.Array  # utf8 (read from incumbent_<domain> at step start)
    to_alternative_ids: pa.Array    # utf8 (== ChoiceResult.chosen)
```

Stored in `state.data[TRANSITION_LOG_KEY] = (...TransitionRecord, ...)` —
mirroring `DECISION_LOG_KEY`. `panel.py` extends `_build_decision_columns`
(`src/reformlab/orchestrator/panel.py:221`) to also inject
`{domain}_from` and `{domain}_to` per year. This is a small additive change.

#### 4.2.3 Mutate population? No — return a new one (already the case)

The existing pattern is "return a new `PopulationData`". `PopulationData` is a
frozen dataclass; `PyArrow` tables are immutable. We keep this. No in-place
mutation. The "merge happens" inside `HeatingStateUpdateStep` /
`VehicleStateUpdateStep`, which is correct — the orchestrator just passes
`YearState` forward.

### 4.3 Multi-period chaining — where does it happen?

It already happens. Each year's pipeline is:

```
DiscreteChoiceStep → LogitChoiceStep → <Domain>StateUpdateStep → DecisionRecordStep → ComputationStep → CarryForwardStep
```

The output `YearState.data["population_data"]` becomes the input
`YearState.data["population_data"]` for year+1 because `Orchestrator._run_year`
threads `current_state` forward (`src/reformlab/orchestrator/runner.py:118`).
No new orchestrator step is required for chaining. **EPIC-28 only needs to
ensure the step pipeline is correctly assembled when
`technology_set.domains[d].enabled === true`.** This assembly is the job of a
new `EngineConfigCompiler` (Story 28.1).

### 4.4 Determinism

Confirmed. The chain `master_seed → Orchestrator._derive_year_seed(year) →
YearState.seed → LogitChoiceStep.draw_choices(seed=year_seed)` is fully
deterministic across periods.
`apply_choices_to_population` is purely deterministic (sorted iteration over
`all_attr_keys`, see `domain_utils.py:122`). The new
`incumbent_<domain>` writeback is order-deterministic by construction.

### 4.5 Transition-record storage location

| Surface | Stores | Why |
|---------|--------|-----|
| Panel (`PanelOutput.table`) | `{domain}_from`, `{domain}_to`, `{domain}_chosen` per row per year | Analyst-facing; enables "show me transitions" queries |
| Manifest (`RunManifest.discrete_choice_parameters` already exists; extend) | Per-year aggregate counts (`n_switchers`, `per_alternative_counts`) plus `technology_set` snapshot | Provenance and reproducibility |
| `state.data[TRANSITION_LOG_KEY]` | Per-year tuple of `TransitionRecord` (transient) | Inter-step communication only; cleared between years if memory pressure rises |

---

## 5. Adapter contract impact

**No change to `ComputationAdapter`.** The adapter (`compute(population, policy,
period) -> ComputationResult`) is already invariant to whether the population
carries `incumbent_<domain>` columns; OpenFisca only reads variables the policy
references. The adapter has never known about decision domains and should not
start.

**OpenFisca's `TaxBenefitSystem`** does **not** need to know about the
technology set. Subsidy / malus formulas read `vehicle_type`, `heating_type`,
etc. — which `apply_choices_to_population` already writes back into the
population. The technology set is upstream of the adapter call; OpenFisca sees
the resulting population and computes subsidies accordingly.

**Recommendation**: keep all changes **above** the adapter, in
`src/reformlab/discrete_choice/` and `src/reformlab/orchestrator/`. This is
consistent with CLAUDE.md's "no module outside `computation/` imports OpenFisca
directly" rule.

**Fallback (rejected)**: pushing the technology-set check into the adapter
would couple OpenFisca to investment-decisions concerns. Not worth the cost.

---

## 6. Manifest impact

### 6.1 New manifest fields

Extend `RunManifest` (`src/reformlab/governance/manifest.py:154`) with one new
optional field:

```python
technology_set: dict[str, Any] = field(default_factory=dict)
# Shape:
#   {
#     "version": "fr-default-2026-04-26",
#     "domains": {
#       "heating": {
#         "enabled": true,
#         "alternatives": [{"id": "...", "name": "...", "attributes": {...}}, ...],
#         "reference_alternative_id": "keep_current",
#         "cost_column": "total_heating_cost"
#       }
#     }
#   }
```

The existing `taste_parameters: dict[str, Any]` field
(`manifest.py:171`) already covers FR51; no change to that.

The existing per-year domain-counts (`{domain}_per_alternative_counts` in
metadata) already gives FR50 coverage; no change.

### 6.2 Manifest version bump strategy

`RunManifest` does not currently carry a `manifest_schema_version` field
(verified — `manifest.py:38-72`). Two options:

| Option | Description | Recommendation |
|--------|-------------|----------------|
| A. Add `technology_set` as `OPTIONAL_JSON_FIELDS` | Fully backward compatible — old manifests load without the field. Same pattern as the eight other optional fields added since 21.6 (`manifest.py:62-72`). | **Chosen** |
| B. Introduce `manifest_schema_version: str` and bump from "1.0" to "1.1" | Heavier; would require touching every existing manifest reader. | Defer to a future story when the field count justifies it. |

Option A is consistent with the project's incremental-additive history and
keeps the EPIC-28 risk surface small.

### 6.3 Capture path

A new `capture_technology_set(...)` in
`src/reformlab/governance/capture.py`, called from
`OrchestratorRunner._capture_manifest_fields`
(`src/reformlab/orchestrator/runner.py:597`), reads the technology set from the
workflow request and serializes the snapshot. This mirrors the pattern of
`capture_discrete_choice_parameters` (`runner.py:576`).

---

## 7. UI surface

### 7.1 Where the new wizard step sits

Today (`InvestmentDecisionsWizard.tsx:35`):
```
Enable → Model → Parameters → Review
```

Proposed (one new step):
```
Enable → Technology → Model → Parameters → Review
```

Rationale: the analyst answers "are decisions in scope?" first (Enable), then
"in scope for which technologies?" (Technology), then "which model?" (Model),
then "calibrate the model" (Parameters). Putting Technology before Model means
calibration ASCs can validate against the chosen alternative ids on Parameters.

### 7.2 Step content (Technology)

- Per-domain expandable section (heading + switch).
- For each enabled domain:
  - Pre-populated alternative list from the canonical set
    (`fr-default-2026-04-26`).
  - Allow add / remove / reorder.
  - Show one alternative pinned as the "reference" (radio). Maps to
    `referenceAlternativeId`.
  - **Auto-populate behavior**: if the active scenario's selected
    population already has an `incumbent_<domain>` column with values, show
    a green badge next to the domain header: "Incumbent technology detected
    in population". Pre-check the corresponding alternatives in the list.
    If alternatives are missing (population has `incumbent_heating === "oil"`
    but the canonical set excludes oil), surface a non-silent inline warning:
    "Population has incumbent values not in your set: oil (3,200 households).
    Add it to your set or those households will start at the reference
    alternative."

### 7.3 Warning behaviour

Per the toast policy memory (`feedback_error_toasts_user_initiated_only.md`,
EPIC-27 work): wizard warnings render **inline** (banner-style), not as toasts.
Inline because the wizard is an explicit user-initiated context but the
population mismatch is a passive detection. Three concrete cases:

| Case | Surface | Severity |
|------|---------|----------|
| Population missing incumbent column entirely | Inline banner above alternative list: "Selected population doesn't carry incumbent technology. All households will start at the reference alternative." | Warning |
| Population has incumbent column with values not in chosen set | Inline banner per domain: "3,200 households have technology X not in your set; they will start at the reference alternative." | Warning |
| Population has incumbent column with values matching chosen set | Inline confirmation: "Incumbent matched in 100% of households." | Info |

### 7.4 Default behaviour

When the user opens the Technology step for the first time and the population
has no incumbent column, the canonical default set (`fr-default-2026-04-26`) is
**not** auto-applied. The step shows a primary CTA "Use default
French set (5 heating, 6 vehicle)" — explicit choice, never silent. Once
applied, the user can edit; subsequent visits remember the set on the scenario.

---

## 8. Open questions for PM

The sprint change proposal flags FR additions as PM work. Concretely, PM should
add or extend:

- **FR additions (mandatory before stories 28.1–28.5 are sized)**:
  - **FR47-extension** (or new **FR47a**): Analyst can declare the set of
    in-scope technologies for an investment decision per domain.
  - **FR50-extension**: Panel output records the from-technology and
    to-technology per household per year (transition record), in addition to
    the existing chosen-alternative.
  - **New FR**: Population data may carry an `incumbent_<domain>` column per
    investment-decision domain; if absent, all households default to the
    domain's reference alternative with a recorded manifest warning.
  - **New FR**: Run manifests record the fully-resolved technology set
    (version + per-domain alternative snapshot) for reproducibility.
- **NFR clarifications**:
  - Confirm NFR9 wording covers the technology-set snapshot (it does — "every
    parameter, every assumption, every input" — but a footnote naming the new
    field will help auditors).
- **UX-spec amendments**:
  - The wizard step "Technology" between Enable and Model.
  - Inline (non-toast) warning patterns for population/set mismatch.
  - The "Use default French set" explicit-choice CTA.

---

## 9. Sized story breakdown

| Story | Scope (one line) | SP | Dependencies | Key risk |
|-------|------------------|----|--------------|----------|
| **28.1** | Define `TechnologySet` types (frontend + backend), wire into `EngineConfig`, add API endpoint `GET /api/discrete-choice/technology-sets/default?domain=heating` returning the canonical set, persist to localStorage and scenario JSON | 5 | None (gate for 28.2–28.5) | Type drift between TS interface and Python `@dataclass(frozen=True)` — mitigate with a manifest-roundtrip integration test |
| **28.2** | Population schema delta: add optional `incumbent_<domain>` columns; backfill `fr-synthetic-2024` and Quick Test; new `validate_population_for_technology_set` helper; data-fusion writes incumbent at end of pipeline | 5 | 28.1 | Forgotten user-uploaded populations — mitigate via inline wizard warning (Story 28.4) and explicit fail-loud on unknown ids |
| **28.3** | `EngineConfigCompiler` builds the discrete-choice step pipeline from `TechnologySet`; extend `apply_choices_to_population` to write `incumbent_<domain>`; introduce `TransitionRecord` and emit per year; extend `panel.py` with `{domain}_from` / `{domain}_to` columns; capture `technology_set` in manifest | 5 | 28.1, 28.2 | Multi-period chaining bug (chain pop_t → pop_{t+1}) is the highest-risk surface — mitigate with a 5-year integration test asserting `incumbent_heating` matches last year's `chosen` |
| **28.4** | Investment Decisions wizard "Technology" step between Enable and Model; reactive defaults from population's `incumbent_<domain>`; inline warnings for mismatch; explicit CTA for canonical set | 3 | 28.1 (types), 28.2 (so warnings can read incumbent column) | Mock population API in Vitest needs `incumbent_*` data — pre-existing mock pattern handles this |
| **28.5** | End-to-end regression: 5-year heating scenario, 100k households, mixed initial incumbents; assert manifest snapshot equality across two runs (NFR6/NFR7); assert transition counts match a fixture; backward-compat: scenario without investment decisions still runs | 3 | 28.1–28.4 | Test runtime budget on CI — mitigate by using the 1k-household fixture for snapshot, full 100k only on nightly |

**Total: 21 SP** (matches the proposal's estimate).

---

## 10. Risks and unknowns

### 10.1 Highest risk — multi-period state transitions in the orchestrator

Even though the chaining mechanism exists, three subtle failure modes need
explicit coverage:

- **State key collision across domains**: `DiscreteChoiceStep` /
  `LogitChoiceStep` / state-update steps share the keys
  `DISCRETE_CHOICE_RESULT_KEY` and `DISCRETE_CHOICE_METADATA_KEY`
  (`step.py:42-44`). Running two domains in one year (heating + vehicle)
  already requires the existing `DecisionRecordStep` snapshot pattern to
  prevent the second domain from overwriting the first's results. EPIC-28 must
  preserve and document this pattern; the `EngineConfigCompiler` must order
  steps as `[heating_dc, heating_logit, heating_state_update,
  decision_record(heating), vehicle_dc, vehicle_logit, vehicle_state_update,
  decision_record(vehicle)]` — never interleaved.
- **Eligibility filter + multi-year**: ineligible households in year t must
  retain their incumbent through year t+1 unchanged. The existing
  `EligibilityMergeStep` handles this for the year-level result; verify it
  also leaves `incumbent_<domain>` untouched (it should, because eligibility
  filter operates before `DiscreteChoiceStep`).
- **Carry-forward interaction**: the `CarryForwardStep` operates on
  `state.data` keys via rules. Verify no rule is configured for
  `population_data` itself (which would clobber the writeback). Add a
  guardrail in `CarryForwardConfig.__post_init__` that rejects
  `variable == "population_data"` if any state-update step runs in the same
  pipeline.

### 10.2 Type-system risk — TS / Python drift

`TechnologySet` lives in two places (TS + Python). Risk: someone adds a field
on one side only. Mitigation: a single contract test
(`tests/server/test_technology_set_roundtrip.py`) that posts a
`TechnologySet` JSON shape, runs an orchestrator, reads back the manifest, and
asserts schema equivalence. Same pattern as existing `test_runs.py`.

### 10.3 Backward-compat risk — silent breakage of old scenarios

Old scenarios stored in localStorage have no `technologySet` field. The
frontend must treat missing → null → "use legacy `default_heating_domain_config`
+ `default_vehicle_domain_config`" only when `investmentDecisionsEnabled ===
true`. If `enabled === false` (the common case), no migration needed.
Mitigation: explicit migration in `useScenarioPersistence`
(`frontend/src/hooks/useScenarioPersistence.ts`).

### 10.4 Manifest growth

Embedding the full `TechnologySet` snapshot per run grows the manifest by
~5–10 KB. Acceptable (manifests are already 50–200 KB with policy and
assumption snapshots). Not a hot path for indicator / panel storage.

### 10.5 Calibration interaction (EPIC-15 future)

The Parameters step's ASCs key on alternative ids
(`TasteParameters.asc: dict[str, float]`). If the user removes an alternative
in the Technology step after configuring ASCs, the orphan ASC key must be
detected. Mitigation: validate ASC keys against `TechnologySet` on every
wizard "Next" out of Parameters; this is wizard-side validation already
sketched in 28.4.

### 10.6 OpenFisca variable coverage (EPIC-29 dependency)

EPIC-29 restores French-named output variables (e.g., `vehicle_malus`,
`subsidy_amount`). The wizard's "cost_column" defaults
(`total_heating_cost`, `total_vehicle_cost`) presume those variables exist.
This is **already true** today (the existing
`HeatingDomainConfig.cost_column` and `VehicleDomainConfig.cost_column`
defaults). EPIC-28 doesn't add a new dependency on EPIC-29, but the test
fixture sweep in 29.4 should not drop the cost-column names.

---

## Appendix A — File reference index

| Concern | Files |
|---------|-------|
| `EngineConfig` (frontend) | `frontend/src/types/workspace.ts:66-75` |
| Wizard | `frontend/src/components/engine/InvestmentDecisionsWizard.tsx`, `frontend/src/components/screens/InvestmentDecisionsStageScreen.tsx` |
| `Alternative`, `ChoiceSet`, `ChoiceResult`, `TasteParameters` | `src/reformlab/discrete_choice/types.py` |
| Domain configs | `src/reformlab/discrete_choice/heating.py`, `src/reformlab/discrete_choice/vehicle.py` |
| Writeback | `src/reformlab/discrete_choice/domain_utils.py:65` (`apply_choices_to_population`) |
| Decision record snapshot | `src/reformlab/discrete_choice/decision_record.py` |
| Orchestrator step pipeline | `src/reformlab/orchestrator/runner.py:118`, `src/reformlab/orchestrator/types.py` |
| Panel injection | `src/reformlab/orchestrator/panel.py:67`, `:221` |
| Population type | `src/reformlab/computation/types.py:19` |
| Adapter contract (no change) | `src/reformlab/computation/adapter.py:11` |
| Manifest schema | `src/reformlab/governance/manifest.py:109`, optional fields at `:62-72` |
| Capture path | `src/reformlab/governance/capture.py`, `src/reformlab/orchestrator/runner.py:597` (`_capture_manifest_fields`) |

---

## Appendix B — Backward-compatibility checklist (gate for 28.5)

- [ ] Scenarios with `investmentDecisionsEnabled === false` produce identical
      panels to current main (byte-for-byte).
- [ ] Scenarios with `investmentDecisionsEnabled === true` and no
      `technologySet` field load with a legacy-default fallback and emit a
      manifest warning.
- [ ] Populations without `incumbent_<domain>` columns and
      `investmentDecisionsEnabled === false` produce identical panels.
- [ ] Populations without `incumbent_<domain>` columns and
      `investmentDecisionsEnabled === true` produce a panel with all
      households starting at the domain's reference alternative, plus a
      recorded manifest warning.
- [ ] Existing manifest fixtures load via `RunManifest.from_dict` after the
      `technology_set` field is added (it's optional).
- [ ] `OrchestratorResult` of a no-decisions run is bit-identical to current
      main.
