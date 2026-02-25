---
stepsCompleted: [1, 2, 3, 4]
lastStep: 4
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

## Core User Experience

### Defining Experience

Microsimulation's user experience is built around a **continuous analyst workspace** with two interconnected activity modes:

**Mode 1 — Model Configuration (complex but guided):**
The analyst selects or builds a synthetic population, connects data sources, and defines the policy model. This involves real analytical decisions: which source tables to use, how to construct the synthetic population, what policy parameters to set, and how to map OpenFisca variables. The UX must make this process navigable and transparent — every data manipulation step is tracked and visible so the user can always inspect how the dataset was built and what assumptions were made.

Pre-built synthetic population pipelines and policy templates provide fast-start paths. Customization extends these paths naturally rather than requiring a separate workflow.

**Measurable target:** A returning analyst (Sophie) can configure a new policy model from an existing template in under 15 minutes.

**Mode 2 — Simulation Execution (effortless):**
Once the model is configured, running simulations is a single action. The analyst launches a run, compares scenarios side-by-side, sweeps parameters for sensitivity analysis, and sees distributional charts, welfare tables, and fiscal indicators immediately. No configuration questions, no intermediate steps — push a button, see results.

**These modes are not sequential stages.** The workspace supports fluid movement between them. An analyst runs a simulation, sees unexpected results, inspects the data construction choices, adjusts a parameter or data assumption, and re-runs — all within the same workspace without context switching.

### Platform Strategy

- **GUI-first design:** The GUI is the primary interface for both model configuration and simulation execution. An analyst can complete the full workflow — from synthetic population selection through policy configuration to scenario comparison — without writing code.
- **Code-alongside (MVP scope):** The GUI operates through the same Python API objects used in notebooks. Users can export their current configuration and workflow as a notebook at any point. A live side-by-side code panel is a Phase 2 GUI expansion.
- **Desktop web application:** Browser-based (localhost or hosted), mouse/keyboard primary.
- **Fully offline:** No network calls required for core workflows (NFR13). All data and computation are local.
- **Single-machine target:** 16GB laptop for MVP populations (up to 500k households).

### Effortless Interactions

- **Simulation execution:** Configured model → run → visual results in one click.
- **Scenario comparison:** Select two or more completed runs → side-by-side indicator tables and charts appear automatically.
- **Parameter sweeps:** Select a parameter, define a range, launch sensitivity analysis — results stream in as they complete.
- **Export:** Any table or chart → CSV/Parquet with one action from the GUI or API.

### Critical Success Moments

1. **First distributional chart from zero configuration** — Alex opens the GUI for the first time. A pre-loaded carbon tax template and synthetic population are ready. He clicks Run, sees income-decile impact bars in under 15 minutes. No setup required. This is the "I'm never going back" moment.
2. **Reverse-traceability from results to assumptions** — Sophie clicks on a surprising number in a chart and traces it backward: which policy formula produced it → which population slice fed it → which synthetic data assumptions built that slice → which source tables were used. Trust is earned through this drill-down, not through documentation.
3. **Instant scenario comparison** — Sophie modifies one parameter in a reform scenario, re-runs, and sees the baseline vs. reform comparison update. The speed makes iterative policy analysis feel like a conversation.
4. **Model configuration completion with confidence** — The analyst finishes configuring a custom synthetic population and policy model. The system shows a summary: data sources, assumptions, parameter choices, all traceable. The analyst knows exactly what will be computed before pressing "Run."
5. **Deterministic trust signal** — An analyst re-runs the same configuration and sees identical results. The GUI surfaces this: "Same inputs → same outputs." Reproducibility is visible, not assumed.

### Experience Principles

1. **Zero-configuration first run** — The default state of the GUI when first opened is: pre-loaded carbon tax template, pre-loaded synthetic population, Run button visible. A new user produces their first distributional chart without configuring anything.
2. **Configuration is complex but navigable** — Model setup involves real analytical decisions. The UX guides without hiding complexity. Every step is visible, traceable, and reversible. Target: new model from template in under 15 minutes.
3. **Execution is instant and unquestioned** — Once configured, running simulations, comparisons, and sensitivity sweeps feels like a single action with immediate visual results.
4. **Lineage is the trust moat** — From synthetic population construction through policy configuration to simulation output, the user can trace any number back to its source assumptions. No other tool in this space makes assumptions this visible. Progressive disclosure keeps the default view clean (summary), with full pipeline drill-down on demand. This is the product's competitive differentiator.
5. **Determinism is a UX feature** — "Same inputs → same outputs" is surfaced in the interface, not just a backend guarantee. Reproducibility builds analyst confidence and institutional trust.
6. **GUI-first, code-alongside** — The GUI is the primary design surface for all users. Configuration is exportable as notebooks. Code is always accessible but never required.
7. **Continuous workspace, not staged wizard** — The analyst moves fluidly between configuration and execution. Inspect results, adjust assumptions, re-run — all without leaving the workspace.

## Desired Emotional Response

### Primary Emotional Goals

**Confidence is the core emotion.** Every UX decision in Microsimulation should build confidence across four layers:

1. **Confidence in the data** — "I know where this population came from and what assumptions shaped it." The analyst can inspect every step of the synthetic population construction pipeline and every data source connection.
2. **Confidence in the model** — "I understand what policy logic is being applied and can verify it." Policy templates, parameter choices, and OpenFisca mappings are visible and inspectable, not hidden behind abstractions.
3. **Confidence in the results** — "These numbers are correct, reproducible, and defensible to my director." Deterministic execution, run manifests, and benchmark validation make results trustworthy by construction.
4. **Confidence in myself** — "I can do this analysis without calling in a specialist." The GUI guides complex decisions without requiring deep technical expertise, and pre-built templates demonstrate correct patterns.

### Emotional Journey Mapping

| Stage | Current feeling (without tool) | Target feeling (with Microsimulation) |
|-------|-------------------------------|--------------------------------------|
| **First discovery** | Skepticism — "another framework that won't work for my use case" | Curiosity — "this looks like it understands my actual workflow" |
| **First run** | Anxiety — "will I spend two hours configuring before seeing anything?" | Surprise — "I clicked Run and got distributional charts from the default template in minutes" |
| **Model configuration** | Overwhelm — "so many scripts to chain, so many assumptions to track manually" | Clarity — "I can see every step, every data source, every assumption — and change any of them" |
| **Seeing results** | Doubt — "is this number right? I can't trace where it came from" | Trust — "I can click any number and trace it back to source assumptions" |
| **When something goes wrong** | Fragility — "I changed one thing and something broke but I don't know what" | Understanding — "the system tells me exactly what failed, why, and what to check" |
| **Returning next time** | Dread — "I have to rebuild everything from scratch again" | Ease — "my previous configurations are here, I can clone and modify in minutes" |

### Micro-Emotions

**Critical confidence signals the UX must reinforce:**

- **Confidence over confusion** — At every decision point in model configuration, the analyst knows what's being asked, what the options mean, and what will happen next. No unexplained jargon, no hidden defaults.
- **Trust over skepticism** — Results are backed by visible lineage. The analyst never has to "just believe" a number — she can always verify it.
- **Accomplishment over frustration** — Completing a configuration or producing a comparison feels like a milestone. The system acknowledges progress and shows what was achieved.
- **Control over anxiety** — Every action is reversible. The analyst can undo parameter changes, revert to a previous scenario version, or re-run from a known good state. Nothing is permanent until explicitly saved.

**Emotions to actively prevent:**

- **Fragility** — The feeling that changing one parameter might break everything. The system must validate configurations before execution and contain errors to the specific failing component.
- **Opacity** — The feeling that something is happening behind the scenes that can't be understood. Every computation, transformation, and assumption is inspectable.
- **Abandonment** — The feeling of being stuck without guidance. Error messages are actionable, configuration guidance is contextual, and the path forward is always visible.

### Design Implications

| Emotional goal | UX design approach |
|---|---|
| Confidence in data | Data pipeline summary panel showing source → transformation → population with drill-down at each stage |
| Confidence in model | Policy configuration shows live preview of what will be computed, with parameter validation before run |
| Confidence in results | Every chart/table cell is clickable for lineage drill-down; deterministic rerun indicator visible |
| Confidence in self | Progressive complexity — start with template defaults, reveal advanced options as the analyst gains familiarity |
| Control over anxiety | Undo/revert available at every step; scenario versioning means nothing is lost; validation runs before execution |
| Trust over skepticism | Run manifests accessible from any result view; benchmark validation status visible for templates |
| Understanding over fragility | Error messages name the exact field/parameter/step that failed, suggest specific fixes, and never show raw tracebacks |

### Emotional Design Principles

1. **Every number is defensible** — If an analyst can't explain a result to their director by tracing it through the interface, the UX has failed. Lineage drill-down is not a power-user feature — it's the core trust mechanism.
2. **Errors build confidence, not destroy it** — When something goes wrong, the system response should increase the analyst's understanding. Clear error identification, specific fix suggestions, and preserved state make errors learning moments rather than setbacks.
3. **Progress is visible and persistent** — The analyst should always know where they are in the workflow, what's been completed, and what's saved. No lost work, no ambiguous state.
4. **Complexity is earned, not imposed** — New users see clean defaults and simple actions. Advanced configuration reveals itself as the analyst explores. The interface never overwhelms on first contact.
5. **Speed reinforces confidence** — Fast execution (seconds, not minutes) is not just a performance feature — it's an emotional signal that the system is working correctly and the analyst is in control.
