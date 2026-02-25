---
stepsCompleted: [1, 2]
lastStep: 2
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-Microsimulation-2026-02-23.md
  - _bmad-output/planning-artifacts/research/technical-entity-graph-data-modeling-and-vectorized-simulation-engines-research-2026-02-23.md
  - _bmad-output/planning-artifacts/research/domain-generic-microsimulation-frameworks-research-2026-02-23.md
---

# UX Design Specification Microsimulation

**Author:** Lucas
**Date:** 2026-02-24

---

<!-- UX design content will be appended sequentially through collaborative workflow steps -->

## Strategic Direction Update (2026-02-24)

UX scope now assumes:

- OpenFisca provides baseline policy calculations.
- Microsimulation UX focuses on no-code scenario operations, dynamic (10+ year) projections, and transparent run governance.
- MVP prioritizes analyst workflow UX before public citizen-facing UX.

## Executive Summary

### Project Vision

Microsimulation is an OpenFisca-first analyst product for environmental policy assessment. The MVP centers on carbon-tax and subsidy scenarios for French households, featuring OpenFisca baseline integration, template-driven scenario setup, dynamic year-by-year projections with vintage effects, and reproducible indicator outputs. The product offers two core interfaces: no-code workflow for analysts and notebook/API workflow for researchers. Public-facing UX remains post-MVP.

### Target Users

**Sophie (Applied Policy Analyst)** — Works at France's Ministry of Ecological Transition. Comfortable with Python but frustrated by rebuilding infrastructure for every policy assessment. Needs fast distributional charts and automatic methodology documentation. Primary interface: no-code scenario workspace with optional advanced config editing.

**Marco (Academic Researcher)** — University economist publishing on carbon tax incidence and behavioral responses. Wants to plug in his own elasticities and export complete replication packages for journal appendices. Primary interface: Python API + Jupyter notebooks.

**Claire (Engaged Citizen)** — Non-technical user who wants to compare candidates' environmental policy proposals on her household. Primary interface: future web application (Phase 3, not MVP).

### Key Design Challenges

1. **Multi-persona coherence** — Sophie uses no-code scenario flows while Marco uses Python notebooks; both must share the same scenario and run-governance concepts.

2. **Making governance usable** — Assumption transparency only matters if users can inspect mappings, scenario versions, and year-to-year state updates quickly.

3. **Configuration complexity vs. no-code usability** — Analysts need fast controls for policy parameters and projection horizon without editing fragile config files.

4. **Dynamic workflow explainability** — Users must understand what changed year to year (especially vintage effects), not just final-year charts.

### Design Opportunities

1. **Scenario workspace as primary UX surface** — A no-code scenario board (baseline, reforms, run status, comparison) can become the analyst "daily cockpit."

2. **Template-driven onboarding** — Carbon-tax and subsidy templates can teach by doing, with guardrailed parameter edits and instant reruns.

3. **Run lineage as trust artifact** — If every output links back to data/version/assumption lineage, trust becomes a visible product feature.
