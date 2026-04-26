# Story 28.3: Wire `DiscreteChoiceStep` outputs back into the population frame; orchestrator multi-period contract

Status: ready-for-dev

## Story

As a backend developer enabling multi-period technology transitions,
I want the discrete-choice step pipeline to write each chosen alternative back into the population's `incumbent_<domain>` column, emit a `TransitionRecord` per year capturing from→to, surface those transitions in the panel, and snapshot the technology set into the manifest,
so that a multi-year run reflects realistic transition dynamics and is reproducible byte-for-byte from the manifest.

## Acceptance Criteria

1. Given `apply_choices_to_population` (`src/reformlab/discrete_choice/domain_utils.py:65`), when extended in this story, then after writing chosen-alternative attribute columns it also writes the chosen alternative id to `incumbent_<domain>` (dictionary-encoded `pa.utf8`). The function still returns a new `PopulationData` (no in-place mutation).
2. Given a new `EngineConfigCompiler` (location: `src/reformlab/discrete_choice/engine_compiler.py` or equivalent), when invoked with a `TechnologySet`, then it builds a deterministic step pipeline ordered as `[heating_dc, heating_logit, heating_state_update, decision_record(heating), vehicle_dc, vehicle_logit, vehicle_state_update, decision_record(vehicle)]` — never interleaved across domains; only enabled domains contribute steps.
3. Given a new `TransitionRecord` dataclass (sibling of the existing `DecisionRecord`), when emitted by the per-year pipeline, then it captures `domain_name`, `year`, `household_ids`, `from_alternative_ids` (read from `incumbent_<domain>` at step start), `to_alternative_ids` (== `ChoiceResult.chosen`); these are stored under `state.data[TRANSITION_LOG_KEY]` mirroring the existing `DECISION_LOG_KEY` pattern.
4. Given the panel builder (`src/reformlab/orchestrator/panel.py:67, :221`), when extended in this story, then per-year per-row columns `{domain}_from` and `{domain}_to` are injected alongside the existing `{domain}_chosen` / `{domain}_probabilities` / `{domain}_utilities`.
5. Given the manifest writer at `src/reformlab/governance/capture.py` and `runner.py:597` (`_capture_manifest_fields`), when a run with a `TechnologySet` completes, then `RunManifest.technology_set` (a new optional field added to `manifest.py:154` per spike Section 6) holds the fully-resolved snapshot (version + per-domain alternatives + reference id + cost column).
6. Given a 5-year scenario with one domain enabled, when run end-to-end, then for every household and every year, `population_t.incumbent_<domain> == population_{t-1}.{domain}_chosen` (multi-period chaining invariant). A regression test in 28.5 will pin this invariant; this story must not break it.
7. Given the existing `CarryForwardConfig.__post_init__`, when this story lands, then it rejects (raises) any rule with `variable == "population_data"` while a state-update step runs in the same pipeline, preventing the spike-flagged "carry-forward clobber" failure mode (spike 10.1.3).
8. Given an ineligible household at year t (filtered by `EligibilityMergeStep`), when its incumbent is read at year t+1, then it equals the year-t `incumbent_<domain>` value unchanged. Eligibility filter does not perturb incumbent.
9. Given two domains enabled in one year (heating + vehicle), when run, then the `DECISION_LOG_KEY` and `TRANSITION_LOG_KEY` snapshots correctly contain entries for both domains and the second domain's results do not overwrite the first (verifies the spike's risk 10.1.1 mitigation).

## Tasks / Subtasks

- [ ] Extend `apply_choices_to_population` (AC: #1)
  - [ ] At `domain_utils.py:65`, after the existing `attr_key` loop, add `set_column` / `append_column` writing the chosen alternative id to `incumbent_<domain>`
  - [ ] Preserve dictionary encoding (`pa.dictionary(pa.int32(), pa.utf8())`)
  - [ ] Add a unit test asserting incumbent column is written and the function returns a new PopulationData
- [ ] `EngineConfigCompiler` (AC: #2)
  - [ ] New module that takes a `TechnologySet` (and existing taste-parameters/calibration state) and returns a pipeline step list
  - [ ] Domain ordering: heating before vehicle (deterministic; document why)
  - [ ] When a domain is disabled, omit its steps entirely
  - [ ] Unit tests covering: heating-only, vehicle-only, both-enabled, both-disabled (returns empty step list)
- [ ] `TransitionRecord` and `TRANSITION_LOG_KEY` (AC: #3)
  - [ ] New dataclass in `src/reformlab/discrete_choice/decision_record.py` (or a new sibling module) — frozen, with `pa.Array` fields
  - [ ] State key constant `TRANSITION_LOG_KEY = "transition_log"`
  - [ ] Emit from each domain's state-update step (not from `DecisionRecordStep` — keep responsibilities split)
- [ ] Panel column injection (AC: #4)
  - [ ] Extend `_build_decision_columns` (`panel.py:221`) to read `TRANSITION_LOG_KEY` and add `{domain}_from`, `{domain}_to` columns
  - [ ] Update panel-shape tests
- [ ] Manifest field + capture (AC: #5)
  - [ ] Add `technology_set: dict[str, Any] = field(default_factory=dict)` to `RunManifest` at `manifest.py:109` (or wherever the dataclass is defined)
  - [ ] Add to `OPTIONAL_JSON_FIELDS` at `:62-72`
  - [ ] New `capture_technology_set()` in `governance/capture.py` mirroring `capture_discrete_choice_parameters()` (`runner.py:576`)
  - [ ] Wire into `_capture_manifest_fields` (`runner.py:597`)
- [ ] Carry-forward guardrail (AC: #7)
  - [ ] In `CarryForwardConfig.__post_init__`, reject `variable == "population_data"` if state-update steps are present
  - [ ] Unit test for the rejection
- [ ] Eligibility-incumbent invariance test (AC: #8)
  - [ ] Test: ineligible household at year t → its incumbent unchanged at year t+1
- [ ] Multi-domain non-clobber test (AC: #9)
  - [ ] Test: two domains in one year → both decision/transition records present
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`, `uv run mypy src/`, `uv run pytest tests/discrete_choice/ tests/orchestrator/ tests/governance/`

## Dev Notes

- **The hardest part of this story is the multi-period chaining invariant (AC #6).** The spike confirms the existing `Orchestrator._run_year` already threads `population_data` forward via `current_state` (`runner.py:118`). This story does NOT add a new chaining mechanism; it ensures the writeback writes to the right column so the existing chaining picks it up.
- **No `ComputationAdapter` change** (spike Section 5).
- **No OpenFisca change.** OpenFisca's TaxBenefitSystem reads the attribute columns (`heating_type`, `vehicle_type`), which `apply_choices_to_population` already writes back. The new `incumbent_<domain>` column is read only by the discrete-choice pipeline and the transition-record emitter.
- Manifest growth is ~5–10 KB per run (spike 10.4) — acceptable.
- This story depends on 28.1 (types) and 28.2 (population schema). It is the gating dependency for 28.4 (wizard reads transitions for warnings) and 28.5 (end-to-end regression).

### Project Structure Notes

- New files: `src/reformlab/discrete_choice/engine_compiler.py`, possibly `src/reformlab/discrete_choice/transition_record.py`, matching tests
- Modified: `src/reformlab/discrete_choice/domain_utils.py`, `src/reformlab/discrete_choice/decision_record.py` (or sibling), `src/reformlab/orchestrator/panel.py`, `src/reformlab/orchestrator/runner.py`, `src/reformlab/governance/manifest.py`, `src/reformlab/governance/capture.py`
- No deletions

### References

- [Source: _bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md#Section-4]
- [Source: _bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md#Section-6] (manifest)
- [Source: _bmad-output/planning-artifacts/spike-investment-decisions-technology-set-2026-04-26.md#Section-10.1] (multi-period risks)
- [Source: src/reformlab/discrete_choice/domain_utils.py:65] (writeback target)
- [Source: src/reformlab/orchestrator/panel.py:67, :221] (panel injection)
- [Source: src/reformlab/orchestrator/runner.py:118, :576, :597]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
