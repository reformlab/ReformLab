# Story 29.2: Resolve generic-name placeholders (`irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone`)

Status: ready-for-dev

## Story

As a backend developer maintaining the live OpenFisca path,
I want the remaining generic-name placeholders in `_DEFAULT_OUTPUT_MAPPING` replaced with actual OpenFisca-France variable names or removed if no equivalents exist,
so that the mapping reflects reality and the test suite stops encoding broken variable names.

## Acceptance Criteria

1. Given the four placeholder names (`irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone`) in `_DEFAULT_OUTPUT_MAPPING`, when research is complete, then each placeholder is either (a) replaced with an actual OpenFisca-France variable name that produces the equivalent output, OR (b) removed from the mapping with rationale documented in comments.
2. Given a placeholder is replaced with an actual variable name, when the mapping is updated, then the English project name (right-hand side) is preserved to maintain backward compatibility with existing code that references the normalized column names (`income_tax`, `net_income`, `gross_income`, `carbon_tax`).
3. Given a placeholder is removed from the mapping, when tests are updated in Story 29.4, then no new tests reference the removed name and existing tests are updated to use alternative variables or skip the assertion.
4. Given the updated mapping, when reviewed against `_DEFAULT_LIVE_OUTPUT_VARIABLES`, then none of the four placeholder names appear in the live output tuple (they remain excluded until Story 29.3).
5. Given the `taxe_carbone` placeholder, when researched, then it is confirmed that carbon tax is a ReformLab-specific policy template output, not a core OpenFisca-France variable, and the mapping entry is either removed (recommended) or documented as ReformLab-specific.

## Tasks / Subtasks

- [ ] Research actual OpenFisca-France variable names (AC: #1)
  - [ ] Install and import `openfisca_france` in a Python REPL
  - [ ] Inspect `CountryTaxBenefitSystem().variables.keys()` to find actual income tax, net income, and gross income variable names
  - [ ] Document findings: which placeholders have equivalents and which don't
- [ ] Update `_DEFAULT_OUTPUT_MAPPING` (AC: #1, #2, #5)
  - [ ] For each placeholder with an equivalent: replace French name, keep English name
  - [ ] For each placeholder without equivalent: remove entry, add comment explaining why
  - [ ] For `taxe_carbone`: confirm it's ReformLab-specific and remove or document
- [ ] Update inline documentation (AC: #1)
  - [ ] Add comments explaining the resolution decision for each placeholder
  - [ ] Document the 2026-04-26 hotfix context in `_DEFAULT_OUTPUT_MAPPING` docstring
  - [ ] Update `_DEFAULT_LIVE_OUTPUT_VARIABLES` docstring to reflect remaining placeholders
- [ ] Verify no live requests include placeholder names (AC: #4)
  - [ ] Confirm `_DEFAULT_LIVE_OUTPUT_VARIABLES` still excludes all four placeholders
  - [ ] Add inline comment listing the excluded placeholders with rationale
- [ ] Create migration plan for Story 29.4 (test fixture cleanup)
  - [ ] Document which test files reference the placeholder names
  - [ ] Provide mapping of old placeholder → new actual variable (or "remove if N/A")
  - [ ] List specific test assertions that need updating
- [ ] Quality gates
  - [ ] `uv run ruff check src/ tests/`
  - [ ] `uv run mypy src/`
  - [ ] `uv run pytest tests/computation/test_result_normalizer.py -k "test_default_mapping"`

## Dev Notes

### Critical Context for Implementation

**The Problem (from 2026-04-26 hotfix commit 617e0b15):**
- Eight names in `_DEFAULT_OUTPUT_MAPPING` do not exist in openfisca-france 44.2.2
- Four were custom variables implemented in Story 29.1: `montant_subvention`, `eligible_subvention`, `malus_ecologique`, `aide_energie`
- Four are "generic-name placeholders": `irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone`
- The hotfix narrowed `_DEFAULT_LIVE_OUTPUT_VARIABLES` to only include variables that resolve today, preventing live-run failures

**The Solution:**
- Story 29.1 implemented the four custom variables (subsidy/malus/energy-aid)
- Story 29.2 resolves the four generic-name placeholders by replacing them with actual variable names or removing them
- Story 29.3 will then restore the full set of resolved names to `_DEFAULT_LIVE_OUTPUT_VARIABLES`

**Key Architectural Constraints:**
1. **Mapping preservation**: English project names (right-hand side) must be preserved for backward compatibility
2. **Test hygiene**: Tests should reference actual variables, not placeholders (Story 29.4 handles cleanup)
3. **Live safety**: Placeholder names must remain excluded from `_DEFAULT_LIVE_OUTPUT_VARIABLES` until Story 29.3

### Placeholder Analysis (Initial Research Required)

**1. `irpp` → "income_tax"**
- `irpp` is the old French acronym for "Impôt sur le Revenu des Personnes Physiques"
- May have an actual OpenFisca-France equivalent like `impot_revenu`, `impot_sur_le_revenu`, or similar
- If no direct equivalent, `impots_directs` (which exists) might be the closest substitute
- Research required: `python -c "from openfisca_france import CountryTaxBenefitSystem; print([v for v in CountryTaxBenefitSystem().variables.keys() if 'impot' in v.lower() or 'revenu' in v.lower()])"`

**2. `revenu_net` → "net_income"**
- Net income concept may not have a direct OpenFisca-France variable
- `revenu_disponible` (disposable income) exists and might be the closest equivalent
- Research required: Check if `revenu_net` exists or if `revenu_disponible` is the intended proxy

**3. `revenu_brut` → "gross_income"**
- Gross income concept may not have a direct OpenFisca-France variable
- `salaire_de_base` (base salary) exists for individuals, but is person-level, not household-level
- Research required: Check for household-level gross income variables or document as "no equivalent"

**4. `taxe_carbone` → "carbon_tax"**
- Carbon tax is a ReformLab-specific policy template output, not a core OpenFisca-France variable
- This should be removed from `_DEFAULT_OUTPUT_MAPPING` as it represents policy-specific output, not core tax-benefit variables
- Templates using carbon tax should use explicit MappingConfig files instead of relying on the default mapping
- Decision: Remove from default mapping, add comment explaining it's policy-specific

### Research Commands

```bash
# List all OpenFisca-France variables (grep for income/tax related)
python -c "
from openfisca_france import CountryTaxBenefitSystem
tbs = CountryTaxBenefitSystem()
vars = sorted(tbs.variables.keys())
for v in vars:
    if any(keyword in v.lower() for keyword in ['impot', 'revenu', 'salaire', 'taxe', 'income']):
        print(v)
"

# Check if specific variables exist
python -c "
from openfisca_france import CountryTaxBenefitSystem
tbs = CountryTaxBenefitSystem()
print('irpp:', 'irpp' in tbs.variables)
print('revenu_net:', 'revenu_net' in tbs.variables)
print('revenu_brut:', 'revenu_brut' in tbs.variables)
print('taxe_carbone:', 'taxe_carbone' in tbs.variables)
print('impots_directs:', 'impots_directs' in tbs.variables)
print('revenu_disponible:', 'revenu_disponible' in tbs.variables)
"
```

### Test Files to Update (Story 29.4 Reference)

The following test files reference the placeholder names and will need updates in Story 29.4:
- `tests/computation/test_result_normalizer.py:148-149, 261-267`
- `tests/server/test_dependencies.py:126-130` (excludes placeholders from live output)
- `tests/computation/test_openfisca_api_adapter.py:789-795, 889-890, 904-905` (mocks placeholders)
- `tests/computation/test_openfisca_integration.py:672-674` (comments mentioning placeholders)

This story (29.2) focuses on the mapping changes; Story 29.4 handles the test cleanup.

### Implementation Locations

**Files to Modify:**
- `src/reformlab/computation/result_normalizer.py` — Update `_DEFAULT_OUTPUT_MAPPING` and docstrings

**Files to Reference (Read-Only):**
- `src/reformlab/computation/result_normalizer.py:46-60` — Current `_DEFAULT_OUTPUT_MAPPING`
- `src/reformlab/computation/result_normalizer.py:66-72` — Current `_DEFAULT_LIVE_OUTPUT_VARIABLES`
- Git commit `617e0b15` — Hotfix that excluded placeholder names

### Expected Outcomes

**After resolution, `_DEFAULT_OUTPUT_MAPPING` should:**
- Contain only variable names that either (a) exist in core OpenFisca-France OR (b) exist as ReformLab custom variables (from Story 29.1)
- Have clear comments explaining why certain mappings were removed
- Preserve English project names for backward compatibility
- Be ready for Story 29.3 to restore the full set to `_DEFAULT_LIVE_OUTPUT_VARIABLES`

**After resolution, `_DEFAULT_LIVE_OUTPUT_VARIABLES` should:**
- Still exclude all four placeholder names (until Story 29.3)
- Include the four custom variables from Story 29.1 (added in Story 29.3, not this story)
- Have updated docstring reflecting current state

### Quality Gates

Run these before marking the story done:
```bash
uv run ruff check src/ tests/
uv run mypy src/
uv run pytest tests/computation/test_result_normalizer.py::TestNormalizeComputationResult::test_default_mapping_constants -v
```

### Dependencies

**Blocked by:** Story 29.1 (custom variables must be implemented first to avoid confusion)
**Blocks:** Story 29.3 (cannot restore names until placeholders are resolved), Story 29.4 (test cleanup depends on final mapping decisions)

### Project Structure Notes

**Modified:**
- `src/reformlab/computation/result_normalizer.py` — Update `_DEFAULT_OUTPUT_MAPPING`, docstrings, and comments

**No new files created** — This story is purely about replacing/removing placeholder names in existing mappings.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic-29] — Epic 29 context and story dependencies
- [Source: src/reformlab/computation/result_normalizer.py:46-72] — Current mapping and live output variables
- [Source: Git commit 617e0b15] — 2026-04-26 hotfix that excluded placeholder names from live requests
- [Source: _bmad-output/implementation-artifacts/29-1-implement-custom-openfisca-variables-subsidy-malus-energy-aid.md] — Story 29.1 context for custom variables

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

No debug logs. Story file created through comprehensive analysis of Epic 29 context, Story 29.1 completion state, and the 2026-04-26 hotfix commit.

### Completion Notes List

1. **Epic 29 Analysis Complete** — Reviewed Epic 29 scope: five stories (29.1-29.5) covering custom variable implementation, placeholder resolution, live output restoration, test cleanup, and regression tests.
2. **Story 29.1 Completion Understood** — Story 29.1 implemented four custom variables (`montant_subvention`, `eligible_subvention`, `malus_ecologique`, `aide_energie`) that were added in Story 24.2 but never implemented.
3. **Placeholder Problem Identified** — Four additional names (`irpp`, `revenu_net`, `revenu_brut`, `taxe_carbone`) are "generic-name placeholders" that don't exist in core OpenFisca-France and were excluded from `_DEFAULT_LIVE_OUTPUT_VARIABLES` by hotfix 617e0b15.
4. **Hotfix Context Verified** — Commit 617e0b15 (2026-04-26) narrowed `_DEFAULT_LIVE_OUTPUT_VARIABLES` from 12 variables to 4 variables that actually resolve, preventing "Unknown output variables" errors.
5. **Test Impact Mapped** — Identified 7 test files referencing placeholder names that will need updates in Story 29.4.
6. **Research Framework Provided** — Included Python REPL commands for discovering actual OpenFisca-France variable names and decision framework for replace vs. remove.
7. **Resolution Strategy Defined** — Clear criteria: (a) replace with actual variable if equivalent exists, (b) remove if no equivalent exists, (c) document `taxe_carbone` as ReformLab-specific policy output.
8. **Dependency Chain Clarified** — Story 29.2 (this story) resolves placeholders, enabling Story 29.3 to restore full live output set, followed by Story 29.4 test cleanup and Story 29.5 regression tests.

### File List

**Files to Modify:**
- `src/reformlab/computation/result_normalizer.py` — Update `_DEFAULT_OUTPUT_MAPPING` to replace/remove placeholder names, update docstrings and comments

**Files to Reference (Read-Only Context):**
- `src/reformlab/computation/result_normalizer.py:46-72` — Current mapping and live output variables
- `_bmad-output/planning-artifacts/epics.md#Epic-29` — Epic 29 context and story dependencies
- Git commit `617e0b15` — 2026-04-26 hotfix context

**Files for Story 29.4 (Test Cleanup - Not This Story):**
- `tests/computation/test_result_normalizer.py`
- `tests/server/test_dependencies.py`
- `tests/computation/test_openfisca_api_adapter.py`
- `tests/computation/test_openfisca_integration.py`
