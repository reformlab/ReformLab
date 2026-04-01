---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
lastStep: 14
revision: 4.1
revisionDate: 2026-04-01
revisionScope: "Stage 1 redesign: three policy types (Tax/Subsidy/Transfer), API-driven categories with formula help, duplicate policies, create-from-scratch flow, editable parameter groups, policy set save/load independent from scenario. Plus April 1 consistency: five-stage workspace, inherited primary population, separate runtime and simulation modes, live-default execution, surfaced-pack availability guidance"
inputDocuments:
  - _bmad-output/planning-artifacts/research/technical-entity-graph-data-modeling-and-vectorized-simulation-engines-research-2026-02-23.md
  - _bmad-output/planning-artifacts/research/domain-generic-microsimulation-frameworks-research-2026-02-23.md
  - _bmad-output/branding/visual-identity-guide.md
---

# UX Design Specification ReformLab

**Author:** Lucas
**Date:** 2026-02-24

---

<!-- UX design content will be appended sequentially through collaborative workflow steps -->

## Strategic Direction Update (2026-02-24)

UX scope now assumes:

- OpenFisca provides baseline policy calculations.
- ReformLab UX focuses on no-code scenario operations, dynamic (10+ year) projections, and transparent run governance.
- MVP prioritizes analyst workflow UX before public citizen-facing UX.

## Revision 3.0 Update (2026-03-30)

Revision 3.0 keeps the Revision 2 four-stage architecture but tightens the product around actual use: stronger brand presence, clearer scenario controls, denser policy editing, explicit population sub-steps, user-facing `Scenario` terminology in place of `Engine`, a guided investment-decision flow, a quick test population, and demo-grade phone usability.

Task-level implementation detail for these changes lives in `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md`.

## Revision 4.1 Update (2026-04-01)

Revision 4.1 redesigns Stage 1 and makes the canonical UX consistent with April 1 workspace and runtime decisions:

**Stage 1 — Policies redesign:**

- Stage renamed from "Policies & Portfolio" to **Policies**. "Portfolio" removed from all user-facing copy; internal concept is now **Policy Set**.
- Three fundamental policy types: **Tax** (amber), **Subsidy** (emerald), **Transfer** (blue). Rebate = Subsidy. Feebate = policy set of Tax + Subsidy.
- **API-driven categories** (not hardcoded): each category maps to population columns (e.g., `carbon_emissions` → `emissions_co2`). Categories fetched from `GET /api/categories`.
- **Formula help** per category via help icon: shows how the policy applies (e.g., `emissions_co2 × tax_rate`). Content from API.
- **Duplicate policies allowed**: same template can be added multiple times with different parameters.
- **"+ Add Policy" flow**: from template (pre-filled) or from scratch (pick type + category → default parameter groups).
- **Editable parameter groups**: defaults per type (Mechanism / Eligibility / Schedule / Redistribution), user can rename/add/move/delete.
- **Policy sets saved independently from scenarios** — reusable across scenarios.
- **Cross-stage validation**: policy categories checked against population columns.

**Workspace and runtime:**

- the workspace is now a five-stage flow: `Policies`, `Population`, `Investment Decisions`, `Scenario`, `Run / Results / Compare`,
- the primary population is selected in `Population` and shown as inherited context in `Scenario`,
- `simulation_mode` belongs to the scenario definition and remains distinct from `runtime_mode`,
- normal web execution defaults to live OpenFisca, while replay remains available only through explicit demo or manual flows,
- surfaced policy packs must show clear live-availability status without introducing any runtime or engine selector in the first slice.

## Executive Summary

### Project Vision

ReformLab is an OpenFisca-first analyst product for environmental policy assessment. The MVP centers on carbon-tax and subsidy scenarios for French households, featuring OpenFisca baseline integration, template-driven scenario setup, dynamic year-by-year projections with vintage effects, and reproducible indicator outputs. The product offers two core interfaces: no-code workflow for analysts and notebook/API workflow for researchers. Public-facing UX remains post-MVP.

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

ReformLab's user experience is built around a **continuous analyst workspace** with two interconnected activity modes:

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
- **Local-first desktop web application:** Browser-based with a bundled local service layer. The default deployment is localhost on one machine; hosted deployment is optional later, but the core UX cannot depend on internet connectivity.
- **Offline-capable core workflows:** Simulation, inspection, comparison, lineage, and export work without external network calls. Links to documentation/repository are optional conveniences, not product dependencies.
- **Single-machine target:** 16GB laptop for MVP populations (up to 500k households).
- **Mode strategy:** The MVP covers the advanced analyst workspace. The broader "simple mode" from the brand strategy is treated as a downstream reporting/presentation surface, not a second authoring workflow in this spec revision.

### Effortless Interactions

- **Simulation execution:** Configured model → run → visual results in one click.
- **Scenario comparison:** Select two or more completed runs → side-by-side indicator tables and charts appear automatically.
- **Parameter sweeps:** Select a parameter, define a range, launch sensitivity analysis — results stream in as they complete.
- **Export:** Any table or chart → CSV/Parquet/Notebook with one action from the GUI or API.

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

**Confidence is the core emotion.** Every UX decision in ReformLab should build confidence across four layers:

1. **Confidence in the data** — "I know where this population came from and what assumptions shaped it." The analyst can inspect every step of the synthetic population construction pipeline and every data source connection.
2. **Confidence in the model** — "I understand what policy logic is being applied and can verify it." Policy templates, parameter choices, and OpenFisca mappings are visible and inspectable, not hidden behind abstractions.
3. **Confidence in the results** — "These numbers are correct, reproducible, and defensible to my director." Deterministic execution, run manifests, and benchmark validation make results trustworthy by construction.
4. **Confidence in myself** — "I can do this analysis without calling in a specialist." The GUI guides complex decisions without requiring deep technical expertise, and pre-built templates demonstrate correct patterns.

### Emotional Journey Mapping

| Stage | Current feeling (without tool) | Target feeling (with ReformLab) |
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

## UX Pattern Analysis & Inspiration

### Inspiring Products Analysis

**PolicyEngine** (policyengine.org) — Open-source tax-benefit reform simulator

What it does well:
- **Three-column layout** (parameter tree / charts / context sidebar) is proven for expert analytical tools.
- **Reform-as-delta** — reforms are sparse overrides on a baseline, never full copies. The baseline is protected.
- **"Reproduce in Python" tab** — auto-generates executable code from the current GUI state. Strong trust signal for researchers.
- **Waterfall contribution charts** — shows which policy component drives how much of the total outcome. Rare and analytically powerful.
- **URL-encoded state** — every configuration is shareable via link, essential for research collaboration.
- **Household income sweep chart** — shows net income across an earnings range for baseline vs. reform. Uniquely effective at surfacing benefit cliffs and phase-out slopes.
- **Audience-calibrated AI summaries** — ELI5/Normal/Wonk selector with inspectable prompt.

What it gets wrong:
- **No multi-scenario comparison** — compares exactly one reform against one baseline. Comparing two reforms requires two browser tabs. Critical gap for our use case.
- **No reform summary panel** — the user cannot see "your reform changes 4 parameters" at a glance. Must read generated Python code to audit.
- **Data provenance is invisible** — the underlying population dataset (what year, what reweighting method, what assumptions) is not explained in context.
- **No parameter dependency visualization** — changing one tax bracket shows no indication of interactions with related parameters.
- **Opaque computation wait** — shows queue position but no estimated time. Heavy reforms take 20-60 seconds with no progress signal.
- **No scenario family organization** — no way to group related reform variants.

**Scenario Planning Platforms** (Synario, Runway, Pigment)

What they do well:
- **Layer/branch model for scenario isolation** — scenarios are overlays on a protected baseline, never full copies. Prevents drift and corruption that plagues Excel-based workflows.
- **Real-time recalculation** — parameter changes produce instant visual feedback. Eliminates "run and wait" friction.
- **Toggle-based parameter control** (Synario) — on/off switches for binary policy decisions faster than numeric editing.
- **Audit trail** (Runway) — contextual log of who changed what assumption and when, with comments per change.
- **Pivot-by-scenario** (Synario, Anaplan) — any report or chart can be pivoted so the scenario dimension becomes the column axis.

What they get wrong:
- **No year-by-year temporal decomposition** — none show how a scenario diverges from baseline year-by-year with explanation of which assumption drove each year's delta. This is exactly our vintage tracking use case.
- **Governance is an afterthought** — audit trails are buried in settings/log tabs rather than surfaced alongside results.
- **Scenario proliferation** — no taxonomic organization beyond flat named lists. Breaks down above ~10 scenarios.
- **Missing assumption provenance** — tracks who changed a value, not what external data source or methodology version informed it.

**dbt** (data build tool) — Data lineage visualization

What it does well:
- **Click-to-highlight upstream chain** — clicking any output node immediately highlights its full dependency chain in purple, graying out everything irrelevant. Answers "where did this come from?" in one click.
- **Lens overlay system** — recolors the same DAG by different dimensions (test status, materialization type, data freshness) without changing the graph structure. Like switching map layers.
- **Depth-bounded tracing** — `2+my_model` shows exactly 2 levels upstream. The analyst controls investigation scope before expanding.
- **Passthrough vs. transform labeling** — column-level lineage explicitly labels whether data was passed through unchanged or actively transformed. Eliminates need to inspect code.
- **Four-level progressive disclosure ladder:**
  1. Overview (zoomed out, colors only — "are there failures?")
  2. Subgraph (focused context — "what feeds this model?")
  3. Node detail panel (key metadata — "what is this thing?")
  4. Full resource detail with column-level lineage (deep investigation)
- **Lineage diff** — comparing two states color-codes changed (orange), added (green), removed (red) nodes with automatic downstream impact rendering.

### Transferable UX Patterns

**Navigation & Layout:**
- **Three-column shell** (PolicyEngine) — parameter tree / main content / context sidebar. Proven for expert tools. Adapt for: configuration tree / workspace / run context.
- **Continuous workspace** (Figma model) — no page transitions between configure and execute. The workspace is always the same surface with contextual panels.

**Scenario Configuration:**
- **Layer/branch model** (Synario, Runway) — reforms are always delta layers on a protected baseline. Never edit the baseline directly. Never create full copies.
- **Reform summary panel** (gap in PolicyEngine — we fix this) — persistent panel showing "this scenario changes N parameters" with a human-readable list of overrides.
- **Toggle + slider controls** (Synario) — binary policy provisions use on/off switches; continuous parameters use sliders with numeric input.

**Results & Comparison:**
- **Waterfall contribution charts** (PolicyEngine) — show which policy component drives how much of the total outcome. Adopt directly for distributional indicator decomposition.
- **Multi-scenario overlay charts** (Runway, Pigment) — each scenario gets a color; all render on the same axes. Limit to 4-5 scenarios before the view degrades.
- **Side-by-side table columns** (Synario, Simul8) — baseline leftmost, one column per scenario, delta columns optional.

**Lineage & Traceability:**
- **Click-to-highlight upstream chain** (dbt) — clicking any indicator or chart value highlights the full pipeline: indicator formula → simulation step → policy parameter → population segment → data source.
- **Lens overlays for the pipeline DAG** (dbt) — microsimulation-specific lenses: assumption-sensitivity lens (user-specified vs. defaults), run-status lens (executed vs. cached), reform-diff lens (what changed between baseline and reform).
- **Depth-bounded tracing** (dbt) — "show 1 step back" / "show 2 steps back" / "show full chain." Prevents overwhelm.
- **Lineage diff for scenario comparison** (dbt Recce) — color-code pipeline nodes: orange = parameters differ, green = reform-only steps, gray = identical.

**Onboarding:**
- **Template-first start** (all platforms) — pre-built scenario templates onboard by doing. The template teaches the data model implicitly.
- **Zero-configuration first run** (our principle) — combine with PolicyEngine's instant feedback pattern.

### Anti-Patterns to Avoid

1. **Full-copy scenario model** — never let users create scenarios by duplicating the baseline. Creates untracked drift, the dominant failure mode in Excel-based research workflows.
2. **Export-only comparison** — scenario comparison must be live and interactive, not a "generate comparison report" button producing static output.
3. **Governance buried in a log tab** — run provenance must be surfaced contextually alongside results, not hidden in administrative screens.
4. **Opaque computation wait** — show progress indicators with estimated time, not just a spinner or queue position.
5. **Double-duty navigation** (PolicyEngine weakness) — don't use the same panel for both configuration tree and results navigation without a clear mode indicator.
6. **Flat scenario lists** — provide scenario family organization (e.g., "carbon tax at various rates — sensitivity variants") to keep libraries navigable.
7. **Hidden data provenance** — never show a result without making the underlying population dataset version, construction method, and source tables accessible in context.

### Design Inspiration Strategy

**Adopt directly:**
- PolicyEngine's reform-as-delta model and waterfall contribution charts
- dbt's click-to-highlight lineage and four-level progressive disclosure
- Layer/branch scenario isolation from financial planning platforms
- Template-first onboarding from all platforms
- "Reproduce in Python" code bridge from PolicyEngine

**Adapt for our context:**
- dbt's lens overlay system → microsimulation-specific lenses (assumption sensitivity, run status, reform diff)
- dbt's depth-bounded tracing → "show N steps back" for pipeline investigation
- dbt's lineage diff → scenario comparison diff (what changed between baseline and reform)
- Financial platform real-time recalculation → instant for parameter tweaks, async with progress bar for full multi-year runs
- Scenario family grouping → organize by policy type, reform variant, sensitivity test

**Differentiate by addressing known gaps:**
- **Year-by-year temporal decomposition with vintage explanation** — no reviewed platform shows how a scenario diverges from baseline year-by-year with explanation of which vintage effect or parameter change drove each year's delta. This is our core differentiator.
- **Structured assumption provenance as a first-class UI element** — not just "who changed this value" but "what dataset version and methodology informed it."
- **Native multi-scenario comparison** — PolicyEngine's biggest gap. We ship with side-by-side and overlaid comparison for 2-5 scenarios from day one.
- **Reform summary panel** — persistent, human-readable summary of all parameter overrides in the current scenario.

## Design System Foundation

### Design System Choice

**React + Shadcn/ui (Tailwind CSS)** — a copy-paste component library built on Radix UI primitives with Tailwind CSS for styling. This approach provides maximum control over every component while leveraging proven, accessible primitives underneath.

Key characteristics:

- **Own your components**: Shadcn/ui copies component source into your project — no black-box dependency, full customization freedom
- **Tailwind CSS utility-first styling**: Rapid iteration, consistent design tokens, AI-friendly code generation
- **Radix UI accessibility primitives**: WCAG 2.1 AA compliance built into every interaction
- **TypeScript-first**: Strong typing for complex simulation domain objects

### Rationale for Selection

1. **AI-coded workflow alignment** — Tailwind's utility classes and Shadcn/ui's explicit component patterns are highly predictable for AI code generation. The user will rely on AI prompts for implementation, and this stack produces the most consistent AI-generated output across all major coding assistants.

2. **Maximum freedom without vendor lock-in** — Components live in the project, not in node_modules. Every button, dialog, and data table can be modified without forking a library or fighting upstream opinions. This matches the "totally free" principle expressed in the inspiration strategy.

3. **Progressive complexity support** — Simple components (buttons, inputs) work out of the box. Complex simulation-specific components (DAG viewers, parameter editors, run comparison panels) can be built from Radix primitives without fighting a design system's assumptions about what UI should look like.

4. **Confidence-building visual consistency** — Tailwind's design token system (colors, spacing, typography scales) enforces visual consistency automatically, supporting the core emotional goal of confidence through predictable, professional interfaces.

5. **Community and ecosystem** — Largest component ecosystem in React; extensive Tailwind plugin library; strong integration with visualization libraries (React Flow for DAG lineage, Recharts/Nivo for simulation outputs).

### Implementation Approach

**Core Stack:**

- **React 18+** with TypeScript — component framework
- **Shadcn/ui** — base component library (copied into `src/components/ui/`)
- **Tailwind CSS v4** — utility-first styling with design tokens
- **Radix UI** — accessible primitive layer (used by Shadcn/ui internally)

**Specialized Libraries:**

- **React Flow** — DAG visualization for data lineage and pipeline tracking (key differentiator)
- **Recharts or Nivo** — simulation output charts, comparison visualizations
- **TanStack Table** — high-performance data tables for assumption inspection and parameter grids
- **React Hook Form + Zod** — form handling for model configuration with schema validation

**Project Structure:**

```
src/
  components/
    ui/          # Shadcn/ui base components (Button, Dialog, Card, etc.)
    simulation/  # Domain-specific components (ParameterRow, RunQueuePanel, scenario/results views)
    lineage/     # DAG and lineage visualization components
    layout/      # Shell, navigation, workspace layout
  lib/
    design-tokens.ts  # Extended Tailwind theme configuration
```

**Design-in-code workflow (no Figma required):**

- Sketch rough layouts on paper or whiteboard
- Describe components to AI coding assistant, get working code directly
- Iterate in the browser with hot reload
- Shadcn/ui + Tailwind tokens serve as the design system — no separate design tool needed

### Customization Strategy

**Design Token Layer:**

- Extend Tailwind's default theme with ReformLab-specific tokens: confidence-palette colors (greens for validated, ambers for warnings, blues for information), simulation-state colors, data-quality indicators
- Typography scale optimized for data-dense interfaces: monospace for numbers/IDs, proportional for labels/descriptions
- Spacing scale tuned for dashboard density — tighter than default Shadcn/ui for information-rich panels

**Component Customization Phases:**

- **Phase 1 (MVP)**: Use Shadcn/ui defaults with custom color tokens — minimal visual customization, maximum development speed
- **Phase 2**: Refine component variants for simulation-specific patterns (run-status badges, confidence indicators, lineage node styles)
- **Phase 3**: Full visual identity refinement based on user testing feedback

**AI-Coding Guidelines:**

- All components follow Shadcn/ui's variant pattern (`cva` class variance authority) for consistent AI generation
- Tailwind-only styling — no CSS modules, no styled-components, no inline styles — single pattern for AI to learn
- Component props use TypeScript discriminated unions for simulation domain types, giving AI assistants strong type hints

## Defining Interaction

### The Core Loop

**"Tweak a parameter, see the distributional impact instantly."**

This is ReformLab's defining interaction — the single loop that, if executed perfectly, makes analysts adopt the tool and never go back to spreadsheets. The analyst adjusts a policy parameter (carbon tax rate, subsidy threshold, phase-out slope) and immediately sees who wins, who loses, and by how much across the population.

### User Mental Model

Analysts already think in terms of "change input, see output." Their current tools (Excel, ad-hoc Python scripts, Stata) support this mental model but with high friction: re-run scripts, wait for computation, manually rebuild charts, lose track of which version produced which result.

ReformLab preserves the familiar mental model while removing the friction. The parameter-to-chart loop feels like a conversation with the policy model rather than a batch processing job.

**Key mental model elements:**

- **Parameters are levers** — the analyst thinks of tax rates, thresholds, and phase-out slopes as things they "pull" to see effects. Sliders and numeric inputs match this metaphor directly.
- **Charts are the answer** — distributional bar charts, waterfall decompositions, and comparison tables are how analysts think about policy impact. Results should appear in these familiar forms, not raw data tables.
- **Scenarios are "what if" questions** — each scenario is a question the analyst is asking. The tool should make asking questions fast and comparing answers effortless.

### Success Criteria

| Criterion | Target |
|-----------|--------|
| Parameter change to chart update | < 2 seconds for cached or preview computations; otherwise queued recomputation with visible progress and preserved context |
| Analyst understands what changed | Waterfall chart highlights the parameter's contribution to the distributional shift |
| Surprising result is investigable | One click from any chart value to its lineage chain |
| Comparison is immediate | Adjusting a parameter in an editable scenario immediately marks dependent runs stale and refreshes comparison as soon as reruns complete |
| Loop is repeatable without friction | No manual save step is required between tweaks; edits are preserved and reruns are explicit when computation cost requires them |

### Novel vs. Established Patterns

**Established patterns we adopt:**

- Slider + numeric input for continuous parameters (every data tool does this)
- Bar charts and line charts for distributional output (analyst expectation)
- Side-by-side comparison layout (common in financial planning tools)

**Novel combination that defines us:**

- **Parameter change + instant distributional update + lineage traceability in one continuous surface.** No existing microsimulation tool combines all three. PolicyEngine has parameter-to-chart but no lineage. dbt has lineage but no parameter interaction. Financial planning tools have instant update but no distributional analysis. ReformLab fuses all three into one loop.

**Teaching strategy:** No education needed for the core loop — "move slider, see chart update" is universally understood. Lineage drill-down is discoverable: clickable chart values with a subtle "trace" affordance that reveals depth on demand.

### Experience Mechanics

**1. Initiation:**

- The analyst sees the current scenario's parameter panel (left column in the three-column layout)
- Parameters are grouped by policy domain (tax rates, thresholds, subsidies) with the most commonly adjusted parameters visible by default
- Each parameter shows its current value and the baseline value for reference

**2. Interaction:**

- **Slider drag** for continuous parameters (tax rate: 0-100%) — lightweight preview values update live; expensive recomputation triggers on release after debounce
- **Numeric input** for precise values — local validation is immediate; recomputation triggers on Enter or blur
- **Toggle switch** for binary provisions (enabled/disabled) — cached comparisons refresh instantly; uncached runs queue automatically with progress
- **The reform-as-delta indicator** shows which parameters differ from baseline, always visible

**3. Feedback:**

- **Distributional bar chart** redraws within 2 seconds when cached/previewable; otherwise the view keeps prior results visible, marks them stale, and shows queued recomputation progress
- **Waterfall contribution panel** shows how much of the distributional shift is attributable to the parameter just changed vs. other reform parameters
- **Delta indicators** on key summary statistics (Gini coefficient, fiscal cost, affected population %) update alongside the chart
- **Confidence signal**: if the result is deterministic (same inputs as a previous run), a subtle "verified" indicator appears

**4. Completion:**

- There is no explicit completion — the loop is continuous. The analyst tweaks, observes, tweaks again.
- When satisfied, the analyst can: name/save the scenario, export results, or clone the scenario to explore a variant
- The workspace preserves the current state automatically — closing and reopening returns to exactly this configuration

### Visual Identity

> For the complete color system, typography, chart palette, and visual style rules,
> see the canonical source: `_bmad-output/branding/visual-identity-guide.md`
>
> This UX spec covers component behavior and interaction patterns only.
> All visual styling decisions are maintained in the visual identity guide.

## User Journey Flows

### Journey 1: Model Configuration

**Goal:** Analyst builds a complete, validated model ready for simulation — synthetic population + data sources + policy configuration.

**Entry point:** Workspace opens with "New Model" or "Clone Existing Model" options. Pre-built templates (carbon tax, subsidy) are prominently displayed as fast-start paths.

```mermaid
flowchart TD
    A[Workspace Home] --> B{New or existing?}
    B -->|New from template| C[Select template]
    B -->|New from scratch| D[Empty model scaffold]
    B -->|Clone existing| E[Select model to clone]

    C --> F[Template loaded with defaults]
    D --> F2[Empty model with guided steps]
    E --> F3[Cloned model with all settings]

    F --> G[Step 1: Synthetic Population]
    F2 --> G
    F3 --> G

    G --> G1{Pre-built or custom?}
    G1 -->|Pre-built| G2[Select population dataset]
    G1 -->|Custom| G3[Pipeline builder]
    G3 --> G4[Select source tables]
    G4 --> G5[Define transformations]
    G5 --> G6[Preview population sample]
    G6 --> G7{Satisfied?}
    G7 -->|No| G4
    G7 -->|Yes| G8[Population ready ✓]
    G2 --> G8

    G8 --> H[Step 2: Data Source Connections]
    H --> H1[Map external data sources]
    H1 --> H2[Validate connections]
    H2 --> H3{All connected?}
    H3 -->|No| H1
    H3 -->|Yes| H4[Data sources ready ✓]

    H4 --> I[Step 3: Policy Configuration]
    I --> I1[Select OpenFisca variables]
    I1 --> I2[Map variables to population columns]
    I2 --> I3[Set parameter values]
    I3 --> I4[Preview policy formula summary]
    I4 --> I5{Satisfied?}
    I5 -->|No| I1
    I5 -->|Yes| I6[Policy configured ✓]

    I6 --> J[Step 4: Model Validation]
    J --> J1[Run validation checks]
    J1 --> J2{All checks pass?}
    J2 -->|No| J3[Show failing checks with fix suggestions]
    J3 --> J4[Analyst fixes issues]
    J4 --> J1
    J2 -->|Yes| J5[Model ready — show summary]
    J5 --> K[Model Summary Panel]
    K --> K1[Population: source, size, assumptions]
    K --> K2[Data: connected sources, mappings]
    K --> K3[Policy: variables, parameters, formulas]
    K --> K4[All traceable — every choice visible]
    K --> L[Ready to simulate →]
```

**Key UX decisions:**

- **Progressive steps, not a wizard:** Steps 1-4 are visible as a progress indicator but the analyst can jump between them freely. Completing one step doesn't lock it — they can always go back.
- **Template fast-path:** Templates pre-fill Steps 1-3 with sensible defaults. The analyst can review and modify any default, or accept and go straight to validation.
- **Pipeline visibility:** Every data transformation in the synthetic population builder shows input → transformation → output. The analyst never wonders "what happened to my data."
- **Validation before execution:** The model summary panel at the end is the "confidence checkpoint" — the analyst sees everything that will be computed before pressing Run.

### Journey 2: First-Run Onboarding

**Goal:** Alex (new user) produces a distributional chart in under 15 minutes with zero configuration.

**Entry point:** First launch of the application. No login, no setup wizard. A pre-seeded demo scenario is loaded with valid defaults for Stages 1-3.

```mermaid
flowchart TD
    A[First launch] --> B[Workspace opens]
    B --> C[Demo scenario loaded]
    C --> D[Stages 1-3 prefilled: portfolio, population, engine]
    D --> E[Stage 4 opens with Run enabled]

    E --> F{User clicks Run}
    F --> G[Progress indicator: computing...]
    G --> H[Distributional chart appears]
    H --> I[Income decile impact bars]

    I --> J{User explores}
    J -->|Clicks a bar| K[Lineage drill-down: which households, what formula]
    J -->|Adjusts a parameter| L[Chart updates live — core loop begins]
    J -->|Clicks Compare| M[Clone scenario prompt]

    K --> J
    L --> J
    M --> N[Second scenario created as delta]
    N --> O[Side-by-side comparison view]
    O --> J
```

**Key UX decisions:**

- **No empty state, ever.** The workspace opens on a valid scenario, not an unconfigured shell. The Run button works immediately.
- **The demo scenario IS the tutorial.** By exploring the pre-seeded scenario, the analyst learns what the policy, population, decision, and scenario stages contain without having to complete them first.
- **First chart is the hook.** Everything before the first chart is automatic. Everything after is the analyst's curiosity driving exploration.
- **The stage-based IA remains visible.** Even though the first launch opens on the run/results surface, the analyst can move backward into the earlier stages to inspect or edit the scenario that produced the result.
- **Gentle discovery:** The lineage drill-down and scenario comparison are discoverable (clickable chart elements, visible "Compare" action) but not pushed. The analyst finds them when they're ready.

### Journey 3: Scenario Workspace

**Goal:** Analyst creates, clones, runs, and compares scenarios within the continuous workspace.

**Entry point:** From a configured model (Journey 1 complete) or from the pre-loaded template.

```mermaid
flowchart TD
    A[Model configured] --> B[Baseline scenario exists]

    B --> C{Action?}
    C -->|Create reform| D[New scenario as delta layer]
    C -->|Clone existing| E[Clone with all overrides copied]
    C -->|Run| F[Execute simulation]
    C -->|Compare| G[Select scenarios to compare]

    D --> D1[Scenario inherits baseline]
    D1 --> D2[Modify parameters — reform-as-delta]
    D2 --> D3[Reform summary: N parameters changed]
    D3 --> C

    E --> E1[Cloned scenario appears]
    E1 --> D2

    F --> F1[Progress bar with ETA]
    F1 --> F2[Results stream in as computed]
    F2 --> F3[Full results: charts + tables + indicators]
    F3 --> C

    G --> G1[Select 2-5 scenarios]
    G1 --> G2{Comparison mode}
    G2 -->|Side-by-side| G3[Columns: baseline + reforms]
    G2 -->|Overlay| G4[All scenarios on same chart axes]
    G2 -->|Delta table| G5[Difference from baseline per indicator]

    G3 --> H[Core loop: tweak parameter in any scenario]
    G4 --> H
    G5 --> H
    H --> H1[Charts update live]
    H1 --> C
```

**Key UX decisions:**

- **Baseline is protected.** The baseline scenario cannot be directly edited. All reforms are delta layers. This prevents the #1 failure mode from Excel-based workflows.
- **Reform summary always visible.** A persistent indicator shows "this scenario changes N parameters" with a human-readable list. The analyst always knows what makes this scenario different.
- **Comparison is a view, not a report.** Selecting scenarios to compare switches the main content area to comparison mode. It's not a "generate comparison" action that produces a separate artifact.
- **The core loop lives here.** The parameter-to-chart loop (tweak → see) operates within the scenario workspace. Adjusting a parameter in a reform scenario updates the comparison view in real time.
- **Scenario families:** Scenarios can be grouped (e.g., "carbon tax rate variants — 20, 40, 60, 80 EUR/ton"). Groups are collapsible in the scenario selector. Prevents flat-list proliferation above ~10 scenarios.

### Journey 4: Assumption Inspection (Lineage Drill-Down)

**Goal:** Analyst traces any result back to its source assumptions to verify correctness and build trust.

**Entry point:** Any clickable value in the results view — chart bar, table cell, summary indicator.

```mermaid
flowchart TD
    A[Analyst sees a result value] --> B{Clicks the value}

    B --> C[Level 1: Indicator summary]
    C --> C1[Which formula produced this]
    C --> C2[Which population slice fed it]
    C --> C3[Which parameters applied]

    C1 --> D{Wants more depth?}
    C2 --> D
    C3 --> D

    D -->|Yes| E[Level 2: Subgraph view]
    E --> E1[DAG showing 2 levels upstream]
    E1 --> E2[Nodes: data source → transformation → policy formula → indicator]
    E2 --> E3[Click any node for detail]

    E3 --> F{Wants full chain?}
    F -->|Yes| G[Level 3: Full lineage]
    G --> G1[Complete pipeline from source tables to this value]
    G1 --> G2[Each node shows: input data, transformation applied, output]
    G2 --> G3[Lens overlays available]

    G3 --> H{Lens selection}
    H -->|Assumption sensitivity| H1[Color by: user-specified vs. default values]
    H -->|Run status| H2[Color by: freshly computed vs. cached]
    H -->|Reform diff| H3[Color by: differs from baseline vs. identical]

    F -->|No| I[Return to results view]
    D -->|No| I

    H1 --> I
    H2 --> I
    H3 --> I
```

**Key UX decisions:**

- **Four-level progressive disclosure** (adapted from dbt):
  1. **Result value** — the number in the chart or table (default view)
  2. **Indicator summary** — one-click popup showing formula, population slice, parameters (Level 1)
  3. **Subgraph** — DAG showing 2 levels upstream with clickable nodes (Level 2)
  4. **Full lineage** — complete pipeline with lens overlays (Level 3)
- **Depth-bounded by default.** The analyst sees 2 levels upstream initially, not the full chain. They expand on demand. This prevents overwhelm.
- **Lens overlays recolor the same DAG** by different dimensions without changing the graph structure. The analyst switches lenses to ask different questions about the same pipeline.
- **Every node is inspectable.** Clicking a DAG node shows: what data came in, what transformation was applied, what data came out. No black boxes.
- **Return is always one click.** From any depth of lineage, the analyst can return to the results view immediately. Exploration is always safe and reversible.

### Journey 5: Export Flow

**Goal:** Analyst exports results as CSV or Parquet for external use (reports, further analysis, sharing).

**Entry point:** Any results view — chart, table, comparison, or full run output.

```mermaid
flowchart TD
    A[Results view] --> B{Export trigger}
    B -->|Single chart/table| C[Export this view]
    B -->|Full run output| D[Export complete results]
    B -->|Comparison| E[Export comparison dataset]

    C --> F[Format selection]
    D --> F
    E --> F

    F --> F1{Format?}
    F1 -->|CSV| G1[CSV with headers and metadata comment block]
    F1 -->|Parquet| G2[Parquet with schema and run manifest embedded]
    F1 -->|Notebook| G3[Jupyter notebook reproducing this analysis]

    G1 --> H[Preview: first 10 rows + column summary]
    G2 --> H
    G3 --> H2[Preview: notebook cells]

    H --> I{Confirm export}
    H2 --> I
    I -->|Confirm| J[File saved to export directory]
    J --> K[Export confirmation with:]
    K --> K1[File path and size]
    K --> K2[Run manifest: what configuration produced this]
    K --> K3[Reproducibility hash: same inputs → same file]

    I -->|Cancel| A
```

**Key UX decisions:**

- **One-action export.** From any view, the export action is at most 2 clicks: trigger → confirm. Format defaults to the last-used format.
- **Run manifest always included.** Every export includes metadata about what configuration, parameters, and population produced the result. The analyst never has an orphaned data file without provenance.
- **Notebook export is a first-class option.** "Reproduce in Python" (inspired by PolicyEngine) generates a Jupyter notebook that recreates the exact analysis. This bridges Sophie's GUI workflow with Marco's notebook workflow.
- **Preview before write.** The analyst sees what will be exported (first rows, column summary) before committing. No surprises.
- **Reproducibility hash.** The export includes a hash that proves: re-running the same configuration produces the identical file. Trust by construction.

### Journey Patterns

**Patterns recurring across all five journeys:**

| Pattern | Description | Used in |
|---------|-------------|---------|
| **Progressive disclosure** | Start with summary, reveal depth on demand | Model config (steps), Lineage (4 levels), Scenario comparison (modes) |
| **Validation before action** | Show what will happen, confirm, then execute | Model validation, Export preview, Run summary |
| **Always reversible** | Every action can be undone or returned from | Model config (edit any step), Lineage (return to results), Scenario (clone before editing) |
| **Reform-as-delta** | Changes are sparse overrides, never full copies | Scenario creation, Parameter editing, Model cloning |
| **Provenance attached** | Every output carries metadata about its origin | Export manifest, Run summary, Lineage nodes |
| **Template fast-path** | Pre-built defaults for common operations | Onboarding template, Policy templates, Population datasets |

### Flow Optimization Principles

1. **Minimize clicks to value.** Onboarding: 1 click (Run) to first chart. Export: 2 clicks (trigger + confirm). Scenario creation: 1 click (clone) + parameter tweaks.

2. **Never block the core loop.** Model configuration is the only journey that requires sequential completion. All other journeys can be entered from any workspace state.

3. **Errors are navigation aids, not dead ends.** Every validation failure names the exact issue, suggests a fix, and provides a link to the relevant configuration step. The analyst is never stuck.

4. **State is always preserved.** Closing the browser and reopening returns to exactly the same workspace state. No lost work, no "start over" scenarios.

5. **Journeys compose naturally.** Model config → Run → Inspect lineage → Adjust parameter → Re-run → Compare → Export. The workspace supports this fluid chain without mode switches or page transitions.

## Component Strategy

### Design System Components (Shadcn/ui — used as-is)

These Shadcn/ui components cover standard UI needs with no customization beyond our design tokens:

| Component | Usage in ReformLab |
|-----------|------------------------|
| Button | Run, Export, Clone, Compare actions |
| Input | Numeric parameter values, search fields |
| Select | Dataset selection, format picker, lens selector |
| Slider | Continuous parameter adjustment (tax rates, thresholds) |
| Switch | Binary policy provisions (enabled/disabled) |
| Dialog | Export confirmation, scenario naming, model validation summary |
| Popover | Lineage Level 1 indicator summary (click-to-inspect) |
| Tooltip | Parameter descriptions, icon labels, abbreviated values |
| Card | Scenario summary cards, result summary cards, DAG node containers |
| Table | Indicator tables, comparison tables, assumption grids |
| Tabs | Comparison modes (side-by-side / overlay / delta), export format tabs |
| Badge | Run status, validation status, reform-delta count |
| Collapsible | Parameter groups, scenario families, panel sections |
| Sheet | Mobile-width panel expansion (side panels on narrow viewports) |
| Separator | Visual section dividers within panels |
| ScrollArea | Long parameter lists, large tables, DAG overflow |
| ResizablePanel | Three-column layout with draggable dividers |
| Command | Quick-action palette (Cmd+K) for scenario search, parameter jump |

### Custom Components

Components not available in Shadcn/ui, designed specifically for ReformLab's domain:

#### ParameterRow

**Purpose:** Dense, inline parameter editing within the left panel. The primary input component for the core loop.

**Anatomy:**

- Label (parameter name, `text-sm font-normal`)
- Current value (`text-sm font-medium mono`, editable inline)
- Baseline value (muted, `text-xs text-slate-400 mono`) — shows what the baseline is when in a reform scenario
- Delta indicator (`sky` badge) — appears only when value differs from baseline
- Unreviewed indicator (`stone` + clock icon) — appears for default values not yet explicitly confirmed

**States:**

- Default: label + value displayed inline
- Hover: subtle background highlight (`bg-slate-50`)
- Editing: blue focus ring, value becomes editable input or slider depending on parameter type
- Modified (reform): `sky` delta badge visible, value in `font-medium`
- Unreviewed: `stone` clock icon, lighter text weight

**Interaction:** Click value to edit inline. For continuous parameters, a slider appears below on click. Enter or blur commits. Esc reverts.

#### ScenarioSummaryCard

**Purpose:** Compact card representing one saved scenario in a scenario registry, compare picker, or clone dialog.

**Anatomy:**

- Scenario name
- Scenario type: baseline / reform
- Linked portfolio and population summary
- Status badge: draft / ready / running / completed / failed
- Delta summary: "3 parameters changed" with expand-to-list
- Last run timestamp
- Actions: Open, Clone, View latest results, Delete

**States:**

- Default: compact summary in list or modal picker
- Selected: `bg-blue-50` highlight, border accent
- Running: animated status badge, progress percentage
- Failed: `red` border accent, error summary visible

**Variants:**

- Baseline scenario summary
- Reform scenario summary

#### RunProgressBar

**Purpose:** Shows simulation execution progress with ETA and cancel option.

**Anatomy:**

- Progress bar (percentage complete)
- ETA text ("~8 seconds remaining")
- Current step label ("Computing year 2027...")
- Cancel button

**States:**

- Computing: animated progress bar with step label
- Streaming: results appearing as computed, progress continues
- Complete: bar fills, transitions to results view automatically
- Cancelled: bar stops, partial results available if any

#### LineagePopover (Level 1)

**Purpose:** One-click inspection popup from any result value. The entry point to the lineage drill-down journey.

**Anatomy:**

- Triggering value highlighted with underline affordance
- Popover showing:
  - Formula that produced this value
  - Population slice (count, filter description)
  - Key parameters applied
  - "Explore lineage →" link to Level 2 subgraph

**States:**

- Closed: value shows subtle underline on hover (affordance that it's clickable)
- Open: popover with summary, click outside to dismiss
- Navigating: clicking "Explore lineage" transitions main content to DAG subgraph view

#### LineageDAGView (Levels 2-3)

**Purpose:** React Flow-based DAG visualization showing data pipeline from sources to results.

**Anatomy:**

- DAG canvas with custom nodes (Shadcn/ui Card-based)
- Node types: DataSource, Transformation, PolicyFormula, Indicator
- Edge types: data flow (solid), parameter dependency (dashed)
- Depth controls: "1 level" / "2 levels" / "Full chain" toggle
- Lens selector: assumption sensitivity / run status / reform diff
- Minimap for navigation in large graphs

**Node design (custom React Flow nodes):**

- Each node is a Shadcn/ui Card (`p-2`, `rounded-md`, `border-slate-200`)
- Icon + label + type badge
- Click to expand: shows input/output data summary
- Highlighted state: `violet` border + background when in active lineage chain
- Dimmed state: `opacity-30` when not in active chain (dbt-inspired gray-out)

**Lens overlay behavior:**

- Assumption sensitivity: nodes colored `emerald` (user-specified) vs. `stone` (default)
- Run status: nodes colored `emerald` (fresh) vs. `amber` (cached/stale)
- Reform diff: nodes colored `sky` (differs from baseline) vs. `slate` (identical)

#### WaterfallChart

**Purpose:** Shows which policy component drives how much of the total distributional shift. Adapted from PolicyEngine's waterfall pattern.

**Anatomy:**

- Vertical bars: one per policy component contribution
- Starting bar (baseline value) → intermediate bars (each component's delta) → ending bar (reform value)
- Color coding: positive contributions (`emerald`), negative contributions (`red`)
- Labels: component name + delta value on each bar
- Clickable bars: each links to the relevant policy parameter for the core loop

**States:**

- Static: shows decomposition for current scenario
- Comparison: shows two waterfall stacks side-by-side for two scenarios
- Animated: bars transition smoothly when a parameter changes (150ms ease-out)

#### ComparisonView

**Purpose:** Main content area component for multi-scenario comparison. Hosts three sub-modes.

**Sub-modes (via Tabs component):**

- **Side-by-side:** Columns per scenario with indicator rows. Baseline leftmost. Delta columns optional.
- **Overlay:** All scenarios rendered on the same chart axes. Color-coded per scenario from chart palette.
- **Delta table:** Difference from baseline per indicator. Positive/negative color coding.

**Anatomy:**

- Scenario selector (which scenarios to compare, max 5)
- Mode tabs (side-by-side / overlay / delta)
- Content area adapting to selected mode
- Parameter editing launches from the owning scenario context; comparison views reflect stale/refreshing state until dependent reruns complete

#### ModelConfigStepper (Retired after Revision 2.0)

**Purpose:** Historical progress indicator for the original four-step model configuration journey. Retained here for reference only; the active shell now uses the five-stage nav rail defined by the current canonical revisions.

**Anatomy:**

- Horizontal step bar: Population → Data Sources → Policy → Validation
- Each step shows: icon + label + status (incomplete / complete / has errors)
- Current step highlighted with `blue` accent
- Click any step to navigate directly

**States:**

- Step incomplete: `slate` icon, muted label
- Step complete: `emerald` checkmark icon
- Step has errors: `red` warning icon
- Current step: `blue` accent, expanded content below

#### ExportPreview

**Purpose:** Preview panel shown before confirming an export. Builds confidence that the right data is being exported.

**Anatomy:**

- Format selector (CSV / Parquet / Notebook)
- Preview area: first 10 rows for tabular data, cell outline for notebooks
- Metadata summary: run configuration, population, parameter snapshot
- File size estimate
- Confirm / Cancel buttons

### Component Implementation Strategy

**Build order aligned with journey priority:**

**Current baseline build order (post-Phase 1):**

1. Stage-based shell (Sidebar + TopBar + main content)
2. ParameterRow — shared parameter editing pattern for policy and engine settings
3. RunProgressBar / RunQueuePanel — execution feedback
4. Basic chart integration (Recharts bar chart for distributional results)
5. ComparisonView (side-by-side mode first)
6. ScenarioSummaryCard — scenario registry and compare picker
7. Cross-stage validation summary before execution

**Phase 1b — Lineage (Sprint 5-6):**

8. LineagePopover (Level 1) — one-click inspection
9. LineageDAGView (Levels 2-3) — React Flow custom nodes
10. WaterfallChart — contribution decomposition

**Phase 2 — Polish:**

11. ComparisonView (overlay + delta modes)
12. ExportPreview
13. Command palette (Cmd+K)
14. Lens overlay system for DAG

**AI-coding component convention:**

- Every custom component lives in `src/components/simulation/`
- Each component is a single `.tsx` file with co-located types
- Props use TypeScript interfaces with JSDoc descriptions (helps AI understand component API)
- All components use Tailwind classes only — no CSS modules
- Storybook stories optional for Phase 2, not MVP

### Implementation Roadmap Snapshot

| Phase | Components | Dependency | Target |
|-------|-----------|------------|--------|
| Current baseline | Stage shell, ParameterRow, RunProgressBar, RunQueuePanel, basic charts, ComparisonView (side-by-side), ScenarioSummaryCard | Scenario/run APIs and stage routing | Active baseline |
| Near-term | LineagePopover, LineageDAGView, WaterfallChart | Lineage data model from computation engine | Active follow-on |
| Later polish | ComparisonView (all modes), ExportPreview, Command palette, Lens overlays | Core loop stable | Next refinement pass |

## UX Consistency Patterns

### Action Hierarchy

**Primary actions** (one per view): Filled button, `bg-blue-600 text-white`. Used for the single most important action in the current context.

| Context | Primary action |
|---------|---------------|
| Model configuration | "Validate Model" |
| Scenario workspace | "Run" |
| Comparison view | "Export" |
| Export preview | "Confirm Export" |

**Secondary actions**: Outline button, `border-slate-300 text-slate-700`. Used for supporting actions: Clone, Compare, Add Parameter, Switch Lens.

**Tertiary actions**: Ghost button (no border), `text-slate-500`. Used for navigation and less important actions: Back, Cancel, Collapse Panel.

**Destructive actions**: Outline button with `border-red-300 text-red-600`. Always require confirmation dialog. Used for: Delete Scenario, Remove Data Source, Reset Parameters.

**Icon-only actions**: `ghost` variant with Lucide icon, tooltip required. Used in dense areas: parameter row actions, scenario card actions, table row actions.

**Rule:** Never show two filled (primary) buttons in the same view. If two actions compete for prominence, one is secondary.

### Feedback & State Communication

**Success feedback:**

- Transient toast (bottom-right, auto-dismiss 3 seconds): "Scenario saved", "Export complete", "Model validated"
- Inline indicator: `emerald` checkmark next to the completed item
- No modal dialogs for success — never interrupt the workflow for good news

**Warning feedback:**

- Persistent inline banner (within the relevant panel, not global): `amber` background, warning icon, actionable text
- Example: "3 parameters use default values — review before running" with "Review" link
- Warnings never block actions — the analyst can proceed and address later

**Error feedback:**

- Inline at the source: red border on the failing field + error message below it
- Error message format: **"[What failed]** — [Why] — [How to fix]"
- Example: **"Tax rate out of range** — Value must be 0-100% — Enter a value between 0 and 100"
- Never show raw exceptions, stack traces, or technical error codes
- Errors block only the specific action that failed, never the entire workspace

**Info feedback:**

- Subtle inline text (`text-slate-500`, info icon) for contextual help
- Tooltip on hover for brief explanations
- No info modals or popups unless explicitly triggered by user

**State indicators (always visible, never require interaction to see):**

| State | Visual | Example |
|-------|--------|---------|
| Running | Animated spinner + progress bar | Simulation computing |
| Complete | `emerald` checkmark badge | Run finished |
| Failed | `red` X badge | Run failed |
| Draft | `slate` circle badge | Scenario not yet run |
| Modified | `sky` delta badge | Parameter differs from baseline |
| Unreviewed | `stone` clock icon | Default value not yet confirmed |
| Stale | `amber` warning badge | Cached result from outdated config |

### Error Handling

**Principle:** Every error is a navigation aid. The analyst should finish reading an error message knowing exactly what to do next.

**Validation errors (before execution):**

- Show all failing checks at once, not one at a time
- Each check links to the relevant configuration step
- Model validation summary: "3 issues found" with expandable list
- Analyst can fix in any order, re-validate when ready

**Runtime errors (during execution):**

- Simulation continues for non-fatal errors (e.g., missing value for one household → skip and report)
- Fatal errors stop execution, show partial results if available
- Error message names the exact year/step/household where failure occurred
- "Re-run from last checkpoint" action when possible

**Data errors (missing or invalid data):**

- Highlighted in the data source panel with `red` border
- Error shows: which column, which rows, what's wrong
- Suggest fix: "Column 'income' has 42 null values — fill with median, drop rows, or provide custom value"

### Data Editing Patterns

**Inline editing (parameters, scenario names, values):**

- Click to enter edit mode (or focus via Tab)
- Blue focus ring signals "you are editing"
- Enter or blur = commit change
- Esc = revert to previous value
- No separate "Edit" button — the value itself is the edit target

**Validation during editing:**

- Real-time validation as user types (e.g., range check on tax rate)
- Invalid values: red border + error message appears below the field
- Cannot commit invalid values — Enter is blocked, blur reverts

**Undo/revert:**

- Ctrl+Z undoes the last parameter change (single level for MVP)
- "Reset to baseline" action on any modified parameter (returns to baseline value)
- "Reset all parameters" on scenario level (returns all overrides to baseline)
- No confirmation needed for undo — it's always safe and fast

### Navigation & Panel Management

**Current shell behavior:**

- **Sidebar:** Persistent nav rail for the four stages plus stage-completion summaries.
- **Main content:** Shows the active stage screen or stage sub-view (results, comparison, lineage, data explorer).
- **Right panel:** Optional contextual metadata/help surface that updates with current selection.

**Panel collapse:**

- Sidebar and contextual panels can collapse to preserve chart/data space.
- Collapsed state uses icon rails or compact toggles consistent with the stage shell.
- Panel state is persisted per session.

**Navigation within panels:**

- Scroll regions remain independent where data density requires it.
- Stage changes and major sub-views are route-addressable within the SPA.
- Browser back/forward returns to the previous stage or sub-view.
- Cmd+K opens command palette for quick navigation: jump to any stage, scenario, parameter, or view.

**Breadcrumb pattern (for lineage drill-down only):**

- When drilling into lineage (Levels 2-3), a breadcrumb appears above the main content: "Results > Gini Coefficient > Lineage > Full Chain"
- Each breadcrumb segment is clickable to return to that level
- "X" button returns directly to results view from any depth

### Loading & Progress Patterns

**Instant operations (< 200ms):** No loading indicator. Parameter edits, panel toggles, tab switches, tooltip shows. Feels instant.

**Fast operations (200ms - 2s):** Skeleton loader in the affected area only. Chart redraws, comparison recalculations, lineage popup loading. A subtle placeholder appears where the content will be.

**Slow operations (2s - 30s):** RunProgressBar component. Full simulation runs, model validation, large exports. Shows: progress percentage, current step, ETA, cancel button.

**Very slow operations (30s+):** Same as slow, but with additional context: "This is a large population (500k households). Estimated time: ~45 seconds." The analyst can continue working in other panels while the computation runs.

**Rule:** Never show a full-page spinner. Loading is always scoped to the component or panel that's waiting. The rest of the workspace remains interactive.

**Optimistic updates:** Parameter changes optimistically update the UI (slider position, value display) before the chart recomputes. If recomputation fails, the parameter reverts with an error message.

## Responsive Design & Accessibility

### Responsive Strategy

**Desktop-first for MVP.** ReformLab is an analytical workstation used primarily on laptops and desktop monitors. Phone authoring is not a target use case, but zoomed and narrow desktop windows must remain operable for accessibility.

**Target viewports:**

| Viewport | Width | Layout behavior |
|----------|-------|----------------|
| Large desktop | 1920px+ | All three columns open, generous main content area |
| Standard desktop | 1440-1919px | All three columns open, comfortable density |
| Laptop | 1280-1439px | Sidebar collapses to rail; contextual panel optional |
| Narrow / zoomed desktop | 1024-1279px | One side panel at a time; secondary surfaces open as Sheet/drawer overlays |
| Minimum operable width | 768-1023px | Single main column with drawers for navigation/context; data-heavy views may switch to table-first mode |

**Phones are discouraged, not hard-blocked.** Below 768px, the app may present a compact read-only warning state, but core navigation and exported outputs remain reachable. This keeps zoomed desktop use compatible with accessibility expectations.

### Breakpoint Strategy

**Tailwind breakpoint mapping:**

```css
sm: 640px — compact/read-only warning and drawer behavior
md: 768px — minimum operable single-column workspace
lg: 1024px — narrow desktop / zoomed desktop layout
xl: 1280px — standard desktop with collapsed auxiliary panels
2xl: 1440px+ — full three-column layout
```

**Breakpoint behavior:**

- `2xl` and above: three columns open by default, standard component spacing
- `xl` to `2xl`: sidebar open or rail, contextual panel optional
- `lg` to `xl`: one auxiliary panel visible at a time; drawers/Sheets for secondary surfaces
- `md` to `lg`: single main column with drawers for navigation, context, and inspectors
- Below `md`: compact warning state; no promise of comfortable authoring

**Still desktop-first.** The CSS is authored from the desktop layout down, but narrower breakpoints exist so browser zoom, split-screen, and accessibility use remain functional.

### Accessibility Strategy

**Compliance level: WCAG 2.1 AA.**

This is the industry standard for professional web applications. It covers the accessibility needs of most users without the exceptional requirements of AAA compliance.

**What AA compliance means for ReformLab:**

| Requirement | Implementation |
|-------------|---------------|
| Color contrast 4.5:1 (text) | Tailwind color scales 500-900 on light backgrounds; verified by design token selection |
| Color contrast 3:1 (large text/UI) | All interactive borders and icons meet 3:1 minimum |
| Color not sole indicator | Every state uses color + icon or color + label (defined in Visual Foundation) |
| Keyboard navigable | All interactive elements reachable and operable via keyboard (Radix UI provides this) |
| Focus visible | Blue focus ring (`ring-2 ring-blue-500`) on all focusable elements |
| Screen reader support | Semantic HTML + ARIA labels from Radix UI primitives |
| Text resizable to 200% | Layout uses relative units (`rem`, `%`); tested at 200% browser zoom |
| No seizure-inducing content | Chart animations are 150ms (well under flicker threshold); respect `prefers-reduced-motion` |

**Accessibility beyond compliance:**

- **Chart data as tables:** Every chart has a hidden accessible table with the same data, surfaced for screen readers. A "View as table" toggle is visible for all users who prefer tabular data.
- **Monospace for data:** Using IBM Plex Mono for numbers ensures digit alignment and readability for users with dyslexia or visual processing differences.
- **High contrast mode:** Respects OS-level `prefers-contrast: more` media query. Increases border weight from 1px to 2px, darkens text to `slate-900`, and increases badge contrast.

### Testing Strategy

**Automated testing (integrated into CI):**

- **axe-core** via `@axe-core/react` — automated WCAG AA audit on every component render during development
- **eslint-plugin-jsx-a11y** — catches accessibility issues at lint time (missing alt text, invalid ARIA)
- **Lighthouse CI** — accessibility score checked on every build, minimum threshold 90/100

**Manual testing checklist (before each sprint release):**

- [ ] Tab through entire workspace — all interactive elements reachable in logical order
- [ ] Verify focus ring visible on every focusable element
- [ ] Navigate parameter editing with keyboard only (Tab, Enter, Esc, Arrow keys)
- [ ] Run VoiceOver (macOS) through core journey: open workspace → run simulation → inspect result
- [ ] Test at 200% browser zoom — no content clipping, no horizontal scroll
- [ ] Test with `prefers-reduced-motion: reduce` — no animations
- [ ] Test with `prefers-contrast: more` — enhanced borders and text contrast
- [ ] Verify all chart data accessible via "View as table" toggle

**Color blindness validation:**

- Test chart color palette with Sim Daltonism or similar tool
- Verify all chart scenarios distinguishable under protanopia, deuteranopia, and tritanopia
- Confirm state indicators (emerald/amber/red) remain distinguishable — our icon+color pattern ensures this

### Implementation Guidelines

**For AI-assisted development — include in every component prompt:**

1. **Semantic HTML first.** Use `<button>` not `<div onClick>`. Use `<nav>`, `<main>`, `<aside>` for layout regions. Use `<table>` for tabular data, never CSS grid pretending to be a table.

2. **ARIA from Radix.** Don't add custom ARIA attributes — Shadcn/ui + Radix UI handle this. Only add `aria-label` when the visual label is insufficient (e.g., icon-only buttons).

3. **Keyboard patterns.** Every custom component must support: Tab (enter), Escape (exit/cancel), Enter (confirm/activate), Arrow keys (navigate within). Shadcn/ui components already do this.

4. **Focus management.** When a dialog opens, focus moves to the dialog. When it closes, focus returns to the trigger. When a panel collapses, focus moves to the collapse toggle. Radix UI handles this for standard components.

5. **Relative units everywhere.** `rem` for font sizes and spacing, `%` or `fr` for layout widths. Never `px` for text. `px` acceptable only for borders (1px) and very specific spacing (the 48px icon rail).

6. **Test at zoom.** After implementing any layout, test at 200% browser zoom. If content clips or requires horizontal scroll, fix the layout.

---

## Revision 2.0 — Information Architecture Restructuring (2026-03-24)

> **This revision supersedes:** the User Journey Flows section (Journey 1: Model Configuration flow and any Journey 2 interpretation that conflicts with stage-based onboarding), the original component sequencing tied to `ScenarioCard`, `ModelConfigStepper`, and the pre-revision shell layout, and the Navigation & Panel Management section. Where older sections use pre-revision terminology, the canonical object model below takes precedence.
>
> **Motivation:** The original information architecture mixed concerns within a single "Configuration" stage — population selection, policy template selection, parameter editing, and validation all lived together. User testing revealed this creates confusion: the link between Portfolio and Policy was unclear, Population appeared in two places (Data Fusion and Configuration), calibration was missing, and the Configuration screen felt like a grab-bag. Revision 2 introduced the initial stage-based model; the current canonical model is the five-stage flow defined in Revision 4.1.

### Revision: Stage-Based Information Architecture

The workspace now follows a five-stage linear workflow. Each stage represents one complete category of decision. Stages are navigable in any order (not a blocking wizard) but the natural flow is sequential.

```
Stage 1: POLICIES
  └─ "What policies am I testing?"

Stage 2: POPULATION
  └─ "Who does this affect?"

Stage 3: INVESTMENT DECISIONS
  └─ "What optional household behavior should be modeled?"

Stage 4: SCENARIO
  └─ "How should this scenario execute?"

Stage 5: RUN / RESULTS / COMPARE
  └─ "What happened?"
```

### Revision: Canonical Object Model

The five-stage shell organizes one underlying analysis model. The canonical workflow artifacts are:

| Artifact | Definition | Created/edited in | Notes |
|---|---|---|---|
| **Policy Set** | Reusable bundle of one or more policies plus their parameter schedules, independent from scenarios | Stage 1 | A single policy is a valid policy set; save/load decoupled from scenario |
| **Population** | Reusable dataset selected, generated, or uploaded for analysis | Stage 2 | Populations remain inspectable outside any one run |
| **Scenario** | Versioned analysis definition combining a policy set, selected population set, simulation configuration, mappings, and metadata | Stages 1-4 | This is the primary save/clone/reform-as-delta object |
| **Run** | Execution of one scenario version for one population or one row of a run matrix | Stage 5 | Runs produce manifests, results, lineage, and exports |
| **Comparison** | View over two or more completed runs | Stage 5 | Comparisons are derived views, not first-class saved configs |

**Authoritative relationships:**

- A scenario references exactly one policy set version and one or more population selections.
- A scenario owns simulation settings such as `simulation_mode`, horizon controls, sensitivity-population choices, and other execution controls.
- Run metadata owns `runtime_mode` and keeps that contract separate from `simulation_mode`.
- A run is never edited directly. To change results, the user edits or clones the scenario and executes a new run.
- Reform-as-delta applies at the scenario level: a reform scenario stores sparse overrides relative to a baseline scenario version.
- Zero-configuration onboarding uses a pre-seeded demo scenario that already has valid Stage 1-4 selections.

**Why the staged model instead of the previous mixed model:**

| Previous structure | Problem | New structure |
|---|---|---|
| Configuration → Population step | Population also in Data Fusion — duplicated | Stage 2: Population (single place) |
| Configuration → Policy Template step | Disconnected from Policy Set | Stage 1: Policies (unified) |
| Configuration → Parameters step | Mixed policy params with execution params | Stage 1 for policy params, Stage 3 for decisions, Stage 4 for scenario execution controls |
| Configuration → Validation step | Validated everything at once | Validation is per-stage (each stage validates its own completeness) |
| Portfolio Designer (separate screen) | Users couldn't see policies inside portfolio | Stage 1 makes Policy Set = collection of policies, visible and editable inline |
| No execution-controls home | Horizon, validation, and runtime summary had no clear home | Stage 4: Scenario → execution controls + validation |

### Revision: Application Shell & Navigation

**The shell follows Pattern 2 (sidebar + slim top bar)**, aligned with the visual identity guide's "Dense Terminal with selective softening" direction.

#### Shell Layout

```
┌──────────┬──────────────────────────────────────────────────┐
│ bg-sl-50 │ bg-white                                  h-12  │
│          │  Stage Name                    📄  🔗  ●  ⚙     │
│  [logo]  │  border-b border-slate-200                      │
│  ──────  ├──────────────────────────────────────────────────┤
│ border-r │                                                  │
│ sl-200   │  (main content area, bg-white)                  │
│  [1] ●   │                                                  │
│   │      │  Panel containers: border-slate-200              │
│  [2] ○   │  Square corners (per brand guide)                │
│   │      │  No shadows on static elements                   │
│  [3] ○   │  No gradients anywhere                           │
│   │      │                                                  │
│  [4] ○   │  Data values: IBM Plex Mono, font-medium         │
│          │  Labels: Inter, font-normal                      │
│          │                                                  │
└──────────┴──────────────────────────────────────────────────┘
```

#### Sidebar (Navigation Chrome)

- **Background:** `bg-slate-50` (chrome surface per visual identity guide)
- **Border:** `border-r border-slate-200`
- **Collapsed state:** `bg-slate-100`, icon-only rail
- **Top element:** Logo mark (bimodal dot histogram, Slate 700 + Emerald 500), max 24px height
- **Below logo:** Wordmark "ReformLab" in Inter semibold, `text-slate-700` — visible when expanded, hidden when collapsed
- **Stage indicators:** Five numbered circles with connecting lines (existing `WorkflowNavRail` pattern), updated labels:
  1. Policies
  2. Population
  3. Investment Decisions
  4. Scenario
  5. Results
- **Stage indicator states:**
  - Active: `bg-blue-500 text-white`
  - Complete: `bg-emerald-500 text-white` with check icon
  - Incomplete: `border-2 border-slate-300 bg-white text-slate-500`
- **Summary lines** below each stage label (when expanded): e.g., "3 policies", "45k records", "2025–2035"
- **No scenario cards in sidebar** — scenarios are managed within their respective stages

#### Top Bar

- **Height:** 48px (`h-12`)
- **Background:** `bg-white` (active content surface)
- **Border:** `border-b border-slate-200`
- **Position:** Inside the main content column, not spanning the sidebar
- **Left side:** Current stage name in `text-lg font-semibold text-slate-900` (Inter). Dynamic — updates based on active nav rail selection.
- **Right side:** Utility icon links in `text-slate-500`, Lucide line-style icons:
  - Documentation link (BookOpen icon) — opens docs in new tab
  - GitHub link (Github icon) — opens repository
  - Local service status indicator — `w-2 h-2 rounded-full` dot: `bg-emerald-500` when the bundled backend is ready, `bg-amber-500` when running in sample-data mode. Tooltip on hover: "Local engine ready" / "Sample data — start local backend for live data"
  - Settings gear (Settings icon) — opens settings panel
- **No logo, no subtitle, no gradient, no shadow, no contextual navigation buttons**

#### Brand Compliance Checklist (Shell)

Per `_bmad-output/branding/visual-identity-guide.md`:

| Rule | Implementation |
|---|---|
| No gradients anywhere | Removed `bg-gradient-to-r from-white to-indigo-50` from header |
| No shadows on static layout | No `shadow-sm` on panels or header |
| No brand logo inside workspace content | Logo lives in sidebar (chrome), not in main content |
| No decorative elements | Removed subtitle "Environmental policy analysis workspace" |
| Panel containers: square corners | `rounded-none` on all panel containers (not `rounded-lg`) |
| Interactive components: `rounded-md` | Buttons, inputs, cards retain `rounded-md` |
| Numbers in IBM Plex Mono | All data values use `font-mono font-medium` |
| Colors from palette only | Removed all `indigo-*` classes; using only slate/blue/emerald/amber/red/violet |

### Revision: Stage 1 — Policies

**Purpose:** Define what policies to test. A Policy Set is a reusable bundle of one or more policies. A single policy is a valid policy set.

> **Supersedes:** The Revision 2 "Policies & Portfolio" section. The word "Portfolio" is removed from all user-facing product copy. The internal concept is now **Policy Set**. All references to "portfolio" in earlier sections should be read as "policy set".

#### Three Fundamental Policy Types

Every policy has exactly one type. Types are exhaustive — there is no "other" type.

| Type | Color | Badge classes | What it does | Examples |
|------|-------|--------------|-------------|---------|
| **Tax** | Amber | `bg-amber-100 text-amber-800` | Takes money from households | Carbon tax, energy tax, vehicle malus, pollution levy |
| **Subsidy** | Emerald | `bg-emerald-100 text-emerald-800` | Gives money/value to households | Energy efficiency grant, vehicle bonus, renovation aid, appliance rebate |
| **Transfer** | Blue | `bg-blue-100 text-blue-800` | Redistributes between households | Carbon dividend, energy poverty aid, climate cheque, means-tested allowance |

**Rebate** is a form of Subsidy (purchase-triggered). No separate type needed.

**Feebate** (e.g., vehicle bonus-malus) is a Policy Set of two policies: one Tax + one Subsidy. A feebate template creates two separate, individually editable policies in the composition panel.

#### API-Driven Categories

Categories are **not hardcoded in the frontend**. They come from the API and represent the population column(s) a policy operates on. The API endpoint `GET /api/categories` returns:

```json
[
  {
    "id": "carbon_emissions",
    "label": "Carbon Emissions",
    "columns": ["emissions_co2"],
    "compatible_types": ["tax", "subsidy", "transfer"],
    "formula_explanation": "emissions_co2 × tax_rate",
    "description": "Applies to household CO₂ emissions (tonnes/year)"
  },
  {
    "id": "energy_consumption",
    "label": "Energy Consumption",
    "columns": ["energy_kwh", "energy_cost"],
    "compatible_types": ["tax", "subsidy", "transfer"],
    "formula_explanation": "energy_kwh × rate_per_kwh",
    "description": "Applies to household energy consumption"
  },
  {
    "id": "vehicle_emissions",
    "label": "Vehicle Emissions",
    "columns": ["vehicle_co2", "vehicle_type"],
    "compatible_types": ["tax", "subsidy"],
    "formula_explanation": "vehicle_co2 × malus_rate",
    "description": "Applies to vehicle emission levels"
  },
  {
    "id": "housing",
    "label": "Housing",
    "columns": ["housing_type", "housing_efficiency"],
    "compatible_types": ["subsidy", "transfer"],
    "formula_explanation": "renovation_cost × subsidy_rate",
    "description": "Applies to housing characteristics and efficiency"
  },
  {
    "id": "income",
    "label": "Income",
    "columns": ["disposable_income", "decile"],
    "compatible_types": ["transfer"],
    "formula_explanation": "max(0, ceiling − disposable_income)",
    "description": "Applies to household income for means-tested transfers"
  }
]
```

**Every policy must have at least one category.** The category determines:
- Which population columns the policy reads
- Which formula structure is applied
- Cross-stage validation: if the population doesn't have the required columns, a warning is shown

#### Category Help / Formula Explanation

Each policy card displays a **help icon** (CircleHelp from Lucide) next to the category badge. Tapping it reveals an inline explanation:

```
┌─────────────────────────────────────────────┐
│ ℹ Carbon Emissions                          │
│                                             │
│ How it works:                               │
│   emissions_co2 × tax_rate = tax_amount     │
│                                             │
│ Applies to the CO₂ emissions column in      │
│ your population data (tonnes/year).         │
│                                             │
│ Required columns: emissions_co2             │
└─────────────────────────────────────────────┘
```

This uses a Popover (existing Shadcn component), not a modal. The `formula_explanation` and `description` fields come directly from the API.

#### Information Architecture

```
Stage 1: POLICIES
│
├─ Policy Browser (left panel)
│   ├─ "+ Add Policy" primary button (opens add-policy flow)
│   ├─ Template catalog: grouped by category, filterable
│   │   ├─ Template card: name, type badge, category badge, live-availability badge, description, param count
│   │   ├─ Click "Add" button on card → adds instance to composition
│   │   └─ Same template can be added multiple times (duplicates allowed)
│   └─ Search / filter by type, category, or keyword
│
├─ Add Policy Flow (triggered by "+ Add Policy" or template card)
│   ├─ Two paths:
│   │   ├─ From Template: select template → pre-filled parameters added to composition
│   │   └─ From Scratch: pick type (Tax/Subsidy/Transfer) → pick category → get default parameter groups
│   └─ Composite templates (e.g., feebate) add multiple policies at once
│
├─ Policy Composition (right panel, inline)
│   ├─ Ordered list of policies
│   ├─ Per-policy card:
│   │   ├─ Header: name, type badge, category badge + help icon
│   │   ├─ Summary line (key values at a glance, e.g., "€44/tCO₂, 3yr phase-in")
│   │   ├─ Expand to edit parameters (grouped by parameter group)
│   │   ├─ Parameter groups: collapsible sections (Mechanism / Eligibility / Schedule / Redistribution)
│   │   ├─ Groups are editable: rename, add new, move parameters between, delete empty
│   │   └─ Year schedule editor (start year, end year, phase-in)
│   ├─ Reorder with up/down arrow buttons
│   ├─ Remove individual policies
│   └─ Conflict detection (inline amber warnings)
│
├─ Policy Set Actions
│   ├─ Save policy set (name + description) — independent from scenario
│   ├─ Load saved policy set
│   ├─ Clone policy set
│   └─ Clear / start over
│
└─ Validation
    ├─ Per-policy: required parameters filled, ranges valid, category assigned
    ├─ Cross-policy: conflict detection with resolution strategy selector
    ├─ Cross-stage: category columns vs. population columns compatibility
    └─ Green checkmark when policy set is valid and ready
```

#### Default Parameter Groups

When creating a policy (from template or from scratch), default parameter groups are assigned based on the policy type:

| Group | Default for types | Purpose |
|-------|-------------------|---------|
| **Mechanism** | All (Tax, Subsidy, Transfer) | Core rates and amounts — the primary lever |
| **Eligibility** | All | Thresholds, exemptions, means tests — who qualifies |
| **Schedule** | All | Phase-in periods, year trajectories — when/how it ramps |
| **Redistribution** | Tax (optional for Subsidy, Transfer) | Revenue allocation — where the money goes |

Groups are **editable by the user**: rename, add new groups, move parameters between groups, delete empty groups. This is not exposed by default — an "Edit groups" toggle or gear icon reveals the group management controls.

The **primary parameter** (the rate/amount in the Mechanism group) is always visible in the policy card header as a summary line, even when the card is collapsed.

#### Key Design Decisions

- **Stage is named "Policies"**, not "Policies & Portfolio". The collection of policies is internally called a "Policy Set" but the user sees "Policies" as the stage name.
- **Policy types are a closed set of three**: Tax, Subsidy, Transfer. No "other" or "custom type".
- **Categories come from the API**, not hardcoded. The frontend fetches and displays them. Categories determine which population columns are used.
- **Surfaced packs must show truthful availability.** Cards and detail panels display live availability using catalog metadata such as `Live ready` or `Unavailable for live execution`, plus a short reason when unavailable.
- **Formula help is always available** via a help icon per category. The explanation comes from the API.
- **Duplicates are allowed.** The same template can be added multiple times with different parameters (e.g., two carbon taxes at different rates).
- **"+ Add Policy" is the primary action**, not toggling templates. Templates are a catalog to add from.
- **Two creation paths**: from template (pre-filled) or from scratch (pick type + category, get default groups).
- **Composite templates** (feebate, tax+dividend) create multiple policies in one action. Each resulting policy is independently editable.
- **Parameter groups are editable** but start with sensible defaults per type.
- **Policy sets are saved independently from scenarios.** A policy set can be loaded into any scenario.
- **Policy parameters live with their policy.** Expanding a policy card reveals grouped parameter editors.
- **Conflict detection is inline and non-blocking.** Amber warnings with resolution strategy selector.

#### User Flow

```mermaid
flowchart TD
    A[Stage 1: Policies] --> B{Add policy}
    B -->|From template| C[Browse template catalog]
    B -->|From scratch| D[Pick type + category]
    C --> E[Add to composition]
    D --> F[Get default parameter groups]
    F --> E
    E --> G[Expand policy → edit parameters by group]
    G --> H{More policies?}
    H -->|Yes| B
    H -->|No| I[Review composition]
    I --> J{Conflicts?}
    J -->|Yes| K[Set resolution strategy]
    K --> I
    J -->|No| L[Policy set valid ✓ → proceed to Stage 2]
```

#### Cross-Stage Validation (Policies × Population)

When both Stage 1 and Stage 2 are configured, the system validates that the population dataset has the columns required by the selected policies' categories. Warnings appear in both stages:

- **In Stage 1:** "⚠ Your population is missing column `vehicle_co2` — Vehicle Emissions policies won't have data."
- **In Stage 2:** "⚠ Selected policies require columns: `emissions_co2`, `vehicle_co2`. Current population is missing: `vehicle_co2`."

These are warnings, not blockers — the user can proceed, but the simulation will skip policies that lack data.

### Revision: Stage 2 — Population

**Purpose:** Prepare the population data that policies will be applied to. This stage is a complete data workspace: select, build, upload, explore, and profile population datasets. Population artifacts are versioned and immutable once referenced by a saved scenario or completed run.

#### Information Architecture

```
Stage 2: POPULATION
│
├─ Population Library
│   ├─ List of available populations
│   │   ├─ [Built-in] Pre-loaded synthetic populations (FR-2023-SILC, etc.)
│   │   ├─ [Generated] Populations built via Data Fusion
│   │   └─ [Uploaded] User-provided CSV/Parquet files
│   ├─ Per-population metadata: name, source, row count, column count, created date
│   └─ Per-population actions:
│       ├─ 👁 Quick Preview (slide-over sheet)
│       ├─ 📊 Full Data Explorer (full-screen)
│       ├─ ✏️ Edit as New Version via Data Fusion
│       ├─ 📤 Upload New
│       └─ 🗑 Delete
│
├─ Data Fusion Workbench (existing, for building new populations)
│   └─ Creates a new population in the library when complete
│
├─ Upload Flow
│   ├─ Drop zone: drag CSV/Parquet or click to browse
│   │   └─ Style: `border-2 border-dashed border-slate-300` idle,
│   │     `border-blue-500 bg-blue-50` on drag-over
│   ├─ Import report:
│   │   ├─ ✓ Row count, column count
│   │   ├─ ✓ Matched columns (mapped to expected schema)
│   │   ├─ ⚠ Unrecognized columns (retained, not ignored)
│   │   ├─ ⚠ Missing required columns (import allowed as draft)
│   │   └─ Next step link → "Open mapping and remediation"
│   └─ Confirm → draft population version added to library
│
├─ Quick Preview (slide-over Sheet component)
│   ├─ First 100 rows in a sortable table
│   ├─ Column headers with sort arrows
│   ├─ Per-column filter row
│   ├─ Row count indicator
│   └─ "Open full view" link → Full Data Explorer
│
└─ Full Data Explorer (replaces main content area)
    ├─ [Tab 1: Table View]
    │   ├─ Paginated data table (TanStack Table)
    │   ├─ Server-side pagination: 50-100 rows per page
    │   ├─ Sortable columns (click header)
    │   ├─ Per-column filters (text/range)
    │   ├─ Column resize
    │   ├─ IBM Plex Mono for all data values
    │   └─ Total rows / current view count
    │
    ├─ [Tab 2: Profile View]
    │   ├─ Column list (left sidebar within the view)
    │   │   └─ Click any column to profile it
    │   ├─ Column profile panel (right)
    │   │   ├─ For NUMERIC columns:
    │   │   │   ├─ Histogram (20 bins, horizontal bars, Slate 400 fill)
    │   │   │   ├─ Percentile bar (P10/P25/P50/P75/P90)
    │   │   │   ├─ Stats card: min, max, mean, median, std, null count
    │   │   │   └─ Cross-tab selector → pick second column for stacked/grouped bars
    │   │   ├─ For CATEGORICAL columns:
    │   │   │   ├─ Horizontal bar chart of value counts (top 20)
    │   │   │   ├─ Cardinality badge ("10 unique values")
    │   │   │   └─ Cross-tab selector → stacked bars with another categorical
    │   │   └─ For BOOLEAN columns:
    │   │       └─ True/False proportion bar with counts
    │   └─ Chart colors: Slate 400 primary, Blue 500 secondary,
    │     Violet 500 tertiary (from brand chart palette)
    │
    └─ [Tab 3: Summary View]
        ├─ Dataset overview: row count, column count, memory size
        ├─ Column type breakdown (N numeric, M categorical, K boolean)
        ├─ Completeness heatmap (columns × null percentage)
        └─ Top-level stats per column in a compact table
```

#### Backend Support

```
GET /api/populations/{id}/preview?offset=0&limit=100&sort_by=income&order=desc
  → Paginated rows for Table View

GET /api/populations/{id}/profile
  → Per-column statistics computed via PyArrow:
    - type, count, nulls, null_pct
    - Numeric: min, max, mean, median, std, percentiles [10,25,50,75,90], histogram_buckets (20 bins)
    - Categorical: value_counts (top 20), cardinality
    - Boolean: true_count, false_count

GET /api/populations/{id}/crosstab?col_a=region&col_b=tenure_type
  → Cross-tabulation data for stacked bar charts

POST /api/populations/upload
  → Accepts multipart CSV or Parquet file
  → Returns import report: matched_columns, unrecognized_columns, missing_required, row_count, status
  → On success: draft population version added to library
```

#### Key Design Decisions

- **Population Library is the entry point.** The user sees all available populations first, then chooses to explore, build, or upload.
- **Population edits are copy-on-write.** "Edit" always creates a new derived version; saved scenarios and completed runs continue pointing at the older immutable version.
- **Quick Preview (slide-over) for spot-checks.** 10-second interaction: open, scan, close. Uses Shadcn Sheet component.
- **Full Data Explorer for deep investigation.** Tab-based: Table, Profile, Summary. The Profile tab is the visual data exploration experience.
- **Cross-tab charts are the key visual insight.** Stacked bars per attribute (e.g., region × tenure type) give the analyst a static picture of the population structure. This is what was missing.
- **TanStack Table (headless) for the data table.** Maximum control over styling to maintain brand compliance. Server-side pagination to handle 500k rows.
- **Recharts for all profiler charts.** Already in the project. Histogram via BarChart, value counts via horizontal BarChart, cross-tabs via stacked BarChart.
- **Upload is permissive, execution is strict.** Import accepts imperfect files as drafts, then guides the analyst through mapping/remediation. Stage 3 remains the hard gate before execution.

#### Visual Profiler Example

For a categorical column `region` cross-tabbed with `tenure_type`:

```
  Île-de-France  ████████████░░░░░░░░   Owner 62% │ Renter 38%
  Occitanie      ██████████████░░░░░░   Owner 71% │ Renter 29%
  Bretagne       ████████████████░░░░   Owner 78% │ Renter 22%
  PACA           ██████████████░░░░░░   Owner 69% │ Renter 31%
```

Colors: Slate 400 for first category, Blue 500 for second. Chart palette from the visual identity guide.

### Revision: Stage 3 — Investment Decisions

**Purpose:** Configure optional household decision behavior in a dedicated workspace. This stage is skipped in the happy path when decision behavior is disabled.

#### Information Architecture

```
Stage 3: INVESTMENT DECISIONS
│
├─ Decision Enablement
│   ├─ Toggle: Enable investment decisions
│   └─ Summary copy explaining this is optional
│
├─ Model Selection
│   ├─ Domain selector (vehicle / heating / renovation where supported)
│   ├─ Model choice / profile
│   └─ Calibration status summary
│
├─ Parameters
│   ├─ Taste / cost assumptions
│   ├─ Eligibility or availability constraints
│   └─ Review-ready parameter summaries
│
└─ Validation
    ├─ Unsupported decision domains fail clearly
    ├─ Missing calibration or required parameters are surfaced clearly
    └─ User can continue directly to Scenario when decisions are disabled
```

#### Key Design Decisions

- **Dedicated stage, not nested subsection.** Investment decisions are no longer configured inside `Scenario`.
- **Optional by default.** The default path remains simple; analysts can skip directly to `Scenario` when decision behavior is off.
- **Scenario consumes, not edits.** The later `Scenario` stage summarizes enabled decision behavior but does not own detailed editing.

### Revision: Stage 4 — Scenario

**Purpose:** Configure how the selected policy set and inherited population will execute. This stage owns scenario-level execution semantics, simulation-mode controls, optional sensitivity populations, run validation, and final readiness before execution.

#### Information Architecture

```
Stage 4: SCENARIO
│
├─ Inherited Population Context
│   ├─ Primary population summary from Stage 2
│   ├─ Source class badge: Built-in / Generated / Uploaded
│   └─ Optional [+ Add population for sensitivity]
│
├─ Simulation Mode
│   ├─ `Annual` — iterative yearly execution with intermediate-year outputs
│   └─ `X-Year Step` — one modeled step over X years with endpoint outputs
│
├─ Horizon & Execution Controls
│   ├─ Start year / end year for annual mode
│   ├─ Horizon-step size for `X-Year Step` mode
│   ├─ Seed and related execution controls
│   ├─ Discount rate and advanced execution controls where relevant
│   └─ Cache / reuse controls where supported
│
├─ Runtime Summary
│   ├─ Runtime: `Live OpenFisca` shown as the default web path
│   ├─ Explicit replay/demo badge only when the user entered a replay flow
│   └─ No user-facing runtime selector in the standard path
│
├─ Run Summary
│   ├─ Scenario: "{scenario_name}"
│   ├─ Policy set: "{policy_set_name}" (N policies)
│   ├─ Primary population and optional sensitivity populations
│   ├─ Simulation mode and horizon summary
│   ├─ Decision-behavior summary from Stage 3
│   ├─ Total runs: Scenario × Populations = N runs
│   └─ Estimated computation time (if available)
│
└─ Validation
    ├─ Policy set must be valid
    ├─ At least one executable population is attached
    ├─ Selected population schema satisfies active policy requirements
    ├─ Required OpenFisca/project field mappings resolve cleanly
    ├─ Policy year schedules fit the chosen simulation mode and horizon
    ├─ Draft population imports must be fully mapped before execution
    ├─ Runtime preflight passes for the selected matrix
    ├─ Unsupported live-only or replay-only combinations fail clearly
    └─ All checks pass → "Ready to Run" primary button enabled
```

#### Key Design Decisions

- **Primary population is inherited, not reselected.** Stage 2 owns primary selection; Stage 4 shows that context and only adds optional sensitivity populations.
- **`simulation_mode` and `runtime_mode` are distinct concepts.** `Scenario` owns `simulation_mode` (`annual` or `horizon_step`). Runtime remains `live` by default for standard web runs and only changes to `replay` in explicit replay/demo flows.
- **No engine selector in the first slice.** Analysts should understand execution truthfully from summary copy and badges, not from a new control they must choose.
- **Run Summary is a pre-flight checklist.** Before pressing Run, the analyst sees the policy set, inherited population context, simulation mode, runtime summary, and validation state in one place.
- **Scenario is assembled here as a first-class object.** Saving or cloning here persists the policy set reference, inherited populations, simulation settings, mappings, and metadata.
- **Cross-stage validation happens here.** Stage 4 is the integration gate where policy requirements, population schema, mappings, decision settings, schedules, and runtime preflight are checked together before execution.

#### User Flow

```mermaid
flowchart TD
    A[Stage 4: Scenario] --> B[Review inherited primary population]
    B --> C{Add sensitivity population?}
    C -->|Yes| D[+ Add population]
    D --> E[Choose simulation mode]
    C -->|No| E
    E --> F{Annual or X-Year Step?}
    F -->|Annual| G[Set start/end years]
    F -->|X-Year Step| H[Set horizon-step size]
    G --> I[Review runtime and run summary]
    H --> I
    I --> J{All checks pass?}
    J -->|Yes| K[Run Simulation → Stage 5]
    J -->|No| L[Show failing checks with links to fix]
    L --> A
```

### Revision: Stage 5 — Run / Results / Compare

**Purpose:** Execute simulations, view results, compare across runs.

#### Information Architecture

```
Stage 5: RUN / RESULTS / COMPARE
│
├─ Run Queue
│   ├─ List of queued runs (Scenario × Population matrix)
│   ├─ Per-run: status (queued / running / completed / failed)
│   ├─ Progress bar per running simulation (RunProgressBar component)
│   └─ Cancel individual runs or cancel all
│
├─ Results View (when at least one run is completed)
│   ├─ Run selector: dropdown or tabs for completed runs
│   ├─ Distributional charts (income decile impact bars)
│   ├─ Summary statistics cards (Gini, fiscal cost, affected %)
│   ├─ Waterfall contribution chart
│   ├─ Run manifest / lineage access
│   └─ Export actions (CSV, Parquet, Notebook)
│
├─ Comparison View
│   ├─ Select 2-5 completed runs to compare
│   ├─ [Tab: Side-by-side] — columns per run, indicator rows
│   ├─ [Tab: Overlay] — all runs on same chart axes
│   ├─ [Tab: Delta table] — difference from baseline per indicator
│   ├─ Absolute / relative toggle
│   └─ Export comparison data (CSV, Notebook manifest)
│
└─ Run Manifest Viewer
    └─ Per-run drill-down into assumptions, mappings, lineage, and reproducibility metadata
```

#### Key Design Decisions

- **Run Queue handles the multi-population matrix.** If the user selected 2 populations in Stage 4, they see 2 runs queued. Each run is independently cancellable.
- **Results and Comparison are sub-views within Stage 5**, not separate stages. The nav rail shows Stage 5 as active for all three.
- **Scenario remains the durable analysis object.** Stage 5 executes scenario versions and compares their runs; it does not replace the scenario registry.
- **The core loop lives here.** Quick parameter tweaks cycle between the owning scenario context and Stage 5; stale results stay visible until reruns complete, so the analyst never loses orientation.

### Revision: Updated Component Strategy

#### Components to Retire

| Component | Reason |
|---|---|
| `ConfigurationScreen` | Replaced by the staged workspace. Its children are redistributed across Policies, Population, Investment Decisions, and Scenario. |
| `ModelConfigStepper` (4-step: Population/Policy/Parameters/Validation) | Replaced by the 5-stage nav rail. Each stage has its own internal validation. |
| `PopulationSelectionScreen` (inside Configuration) | Moved to Stage 2 Population Library. |
| `TemplateSelectionScreen` (inside Configuration) | Absorbed into Stage 1 Policy Template Browser. |
| `ParameterEditingScreen` (inside Configuration) | Policy parameters absorbed into Stage 1. Decision behavior lives in Stage 3 and scenario execution controls live in Stage 4. |
| `AssumptionsReviewScreen` (inside Configuration) | Run Summary in Stage 4 serves this purpose. |
| `ScenarioCard` (left-panel selector) | Replaced by stage-local scenario registry/compare pickers such as `ScenarioSummaryCard`. |
| Gradient header box in `App.tsx` | Replaced by TopBar component. |

#### New Components

| Component | Location | Purpose |
|---|---|---|
| `TopBar` | `components/layout/TopBar.tsx` | 48px slim top bar: stage name + utility icons |
| `PoliciesStageScreen` | `components/screens/PoliciesStageScreen.tsx` | Stage 1: policy browser + inline policy composition with API-driven categories |
| `PopulationLibraryScreen` | `components/screens/PopulationLibraryScreen.tsx` | Stage 2: population list with preview/profile/upload actions |
| `PopulationDataTable` | `components/population/PopulationDataTable.tsx` | TanStack Table for paginated, sortable, filterable population data |
| `PopulationProfiler` | `components/population/PopulationProfiler.tsx` | Visual column profiler: histograms, value counts, cross-tabs, stats |
| `PopulationSummary` | `components/population/PopulationSummary.tsx` | Dataset-level overview: row/column counts, type breakdown, completeness |
| `PopulationUploadZone` | `components/population/PopulationUploadZone.tsx` | Drag-and-drop file upload with import report and mapping triage |
| `EngineScreen` | `components/screens/EngineScreen.tsx` | Stage 3: time horizon, population selection, projection assumptions, run summary |
| `ScenarioSummaryCard` | `components/simulation/ScenarioSummaryCard.tsx` | Saved scenario list item for open/clone/result access flows |
| `ProjectionAssumptionsAccordion` | `components/simulation/ProjectionAssumptionsAccordion.tsx` | Inline accordion: uprating, vintage handling, optional behavioral-response profile |
| `RunQueuePanel` | `components/simulation/RunQueuePanel.tsx` | Multi-run queue with per-run progress and cancel |

#### Updated Component Tree

```
App
├─ TopBar (stage name, utility icons)
├─ WorkspaceLayout
│   ├─ Sidebar (WorkflowNavRail — 4 stages + logo)
│   ├─ MainContent
│   │   ├─ PoliciesStageScreen (Stage 1)
│   │   │   ├─ PolicyBrowser (template catalog + "Add Policy" flow)
│   │   │   ├─ PolicyCompositionPanel (inline, grouped parameters)
│   │   │   └─ Conflict validation + cross-stage category warnings
│   │   ├─ PopulationLibraryScreen (Stage 2)
│   │   │   ├─ Population list with action buttons
│   │   │   ├─ DataFusionWorkbench (existing)
│   │   │   ├─ PopulationUploadZone
│   │   │   ├─ PopulationDataTable (TanStack Table, in Sheet or full-screen)
│   │   │   ├─ PopulationProfiler (histograms, cross-tabs, stats)
│   │   │   └─ PopulationSummary
│   │   ├─ EngineScreen (Stage 3)
│   │   │   ├─ Time horizon inputs
│   │   │   ├─ Population selector (+ sensitivity add)
│   │   │   ├─ ScenarioSummaryCard / save-clone controls
│   │   │   ├─ ProjectionAssumptionsAccordion
│   │   │   │   ├─ Uprating selector
│   │   │   │   ├─ Vintage handling selector
│   │   │   │   └─ Optional behavioral-response selector
│   │   │   ├─ Other engine parameters
│   │   │   └─ Run summary + "Run Simulation" button
│   │   └─ Stage 4 (Run/Results/Compare)
│   │       ├─ RunQueuePanel
│   │       ├─ ResultsOverviewScreen (existing)
│   │       ├─ ComparisonDashboardScreen (existing)
│   │       └─ RunManifestViewerScreen
│   └─ RightPanel (ContextualHelpPanel — existing)
```

### Revision: Updated Nav Rail Stages

The `WorkflowNavRail` component is updated with new stage definitions:

```typescript
const STAGES = [
  {
    key: "policies",
    label: "Policies",
    targetMode: "policies",
    activeFor: ["policies"],
  },
  {
    key: "population",
    label: "Population",
    targetMode: "population",
    activeFor: ["population", "data-fusion", "population-explorer"],
  },
  {
    key: "investment-decisions",
    label: "Investment Decisions",
    targetMode: "investment-decisions",
    activeFor: ["investment-decisions"],
  },
  {
    key: "scenario",
    label: "Scenario",
    targetMode: "scenario",
    activeFor: ["scenario"],
  },
  {
    key: "results",
    label: "Run / Results / Compare",
    targetMode: "results",
    activeFor: ["results", "comparison", "decisions", "runner"],
  },
];
```

### Revision: Updated User Journey — Model Configuration

This replaces Journey 1 from the original spec.

```mermaid
flowchart TD
    A[Workspace opens] --> B{First launch or returning?}
    B -->|First launch| C[Pre-seeded demo scenario loads]
    B -->|Returning| D[Open saved scenario]
    C --> E[Stage 4 visible with Run enabled]
    D --> F[Resume at last active stage]
    E --> G{Needs edits?}
    F --> G
    G -->|Policies| H[Stage 1: edit policy set]
    G -->|Population| I[Stage 2: inspect/select population]
    G -->|Investment Decisions| J[Stage 3: decision behavior]
    G -->|Scenario| K[Stage 4: configure scenario + validate]
    G -->|No edits| L[Run scenario]
    H --> J
    I --> K
    J --> K
    K --> M{All integration checks pass?}
    M -->|Yes| L
    M -->|No| N[Fix linked issues in relevant stage]
    N --> H
    L --> O[Stage 5: queue, results, compare]
```

### Revision: Implementation Priority

**Epic: GUI Restructuring** — suggested story order:

1. **Shell & TopBar** — Replace gradient header with slim top bar. Add logo mark to sidebar. Apply brand compliance fixes (remove gradients, shadows, indigo colors, add square corners to panels).
2. **Nav Rail Update** — Update WorkflowNavRail to 5 stages. Wire stage/sub-view routing.
3. **Stage 1: Policies** — Unify TemplateSelectionScreen + ParameterEditingScreen + PortfolioDesignerScreen into one inline flow. Revision 4 adds three policy types, API-driven categories, and create-from-scratch flow.
4. **Stage 2: Population Library** — Population list with preview/edit/delete actions. Upload flow with import report and mapping triage.
5. **Stage 2: Population Data Explorer** — TanStack Table for paginated data. Visual profiler with histograms, value counts, cross-tabs. Summary tab.
6. **Stage 3: Investment Decisions** — Optional decision-behavior enablement, model selection, parameters, and review.
7. **Stage 4: Scenario** — Inherited primary population, simulation mode, horizon settings, scenario save/clone, runtime summary, and integration validation.
8. **Stage 5: Run Queue** — Multi-run queue for scenario × population matrix.
9. **Cleanup** — Retire ConfigurationScreen, ModelConfigStepper, old ScenarioCard sidebar usage, and unused screens. Remove dead code.

## Revision 3.0 — Interaction Fit, Naming, and Mobile Demo Viability (2026-03-30)

> **This revision supersedes:** the Revision 2 subsections `Application Shell & Navigation`, `Stage 1 — Policies & Portfolio`, `Stage 2 — Population`, `Stage 3 — Engine`, `Updated Nav Rail Stages`, and any earlier responsive guidance that conflicts with the narrower-screen behavior below.
>
> **Motivation:** Revision 2 fixed the architecture. Revision 3 responds to actual product use. The stage model is working, but several friction points remain: weak branding in the shell, scenario controls competing with the logo, generic naming defaults, hidden Population sub-views, the misleading `Engine` label, an under-guided investment-decision flow, no explicit fast test population, and poor phone demo ergonomics.

### Revision: Four-Stage Architecture Remains Intact

Revision 3 does not change the top-level workflow:

```
Stage 1: POLICIES
Stage 2: POPULATION
Stage 3: SCENARIO
Stage 4: RUN / RESULTS / COMPARE
```

The change is interpretive, not structural:

- Stage 1 is now **Policies** (not "Policies & Portfolio"). See Revision 4 below.
- Stage 3 is now presented to users as **Scenario**, not **Engine**.
- Internal route keys and type names may remain `engine` in code if that keeps the refactor low-risk.
- The object model still distinguishes **Policy Set** from **Scenario**.

### Revision: Application Shell And Scenario Controls

Revision 2 treated the logo as sidebar chrome and the top bar as a pure stage header. Current implementation experience shows the product needs a stronger shell identity and clearer separation between brand and scenario navigation.

#### Shell Principles

- The workspace keeps a slim top bar plus stage navigation.
- The shell must show a stronger brand presence than Revision 2 specified.
- Scenario switching remains globally accessible, but it must no longer sit beside the brand mark.

#### Updated Top Bar Guidance

- The top bar includes a dedicated brand block with:
  - larger logo treatment,
  - `ReformLab` wordmark,
  - spacing that makes the product identity immediately legible in demos.
- GitHub and website links are first-class shell actions and must be wired:
  - Website: `https://reform-lab.eu`
  - GitHub: `https://github.com/reformlab/ReformLab`
- External links open in a new tab.
- The active scenario trigger moves into a dedicated scenario-controls area separate from the brand block.
- Stage title remains visible, but it no longer owns the full left side of the top bar.

#### Updated Navigation Guidance

- The top-level nav remains the five-stage workflow.
- When Population is active, the nav pattern should expose stage-local sub-steps:
  - `Library`
  - `Build`
  - `Explorer`
- These are sub-steps, not additional top-level stages.

### Revision: Stage 1 — Policies

> **Supersedes:** Revision 3 "Policies & Portfolio" layout and naming guidance. Revision 4 redesign above is now canonical for Stage 1.

Revision 3 layout and density guidance still applies to the Revision 4 structure:

#### Updated Layout Guidance

- On desktop, Stage 1 uses a deliberate **50/50 split** between:
  - policy browser (left panel),
  - policy composition and editing (right panel).
- This split should feel like one workbench, not a primary panel plus a cramped sidebar.
- On phone, the panels stack vertically.

#### Updated Density Guidance

- Parameter controls should become slightly denser than the current default.
- Parameter labels may use `text-xs`; editable values remain comfortably legible.
- Section headings and validation states should still anchor the eye.
- Within a policy card, the **primary parameter summary** (e.g., "€44/tCO₂") is always visible in the collapsed header.
- Parameter groups use collapsible sections — only the active group is expanded by default.

#### Updated Policy Set Naming Guidance

- The save flow should pre-fill a deterministic suggested policy set name derived from the selected policy types and categories.
- The system may keep updating the suggestion only until the user manually edits it.
- Once edited manually, the name is user-owned and must not be overwritten.

### Revision: Stage 2 — Population

Revision 2 made Population a complete data workspace. Revision 3 clarifies wayfinding and adds a faster demo/test path.

#### Updated Population Navigation

- The user should see Population sub-steps in navigation when Stage 2 is active.
- Hidden route state alone is not sufficient product guidance.

#### Updated Library Guidance

- The Population Library remains the default entry view.
- Add a clearly labeled built-in **Quick Test Population** near the top of the library.
- It is intended for:
  - demos,
  - smoke tests,
  - quick walkthroughs.
- It must be visually differentiated from analysis-grade populations with copy such as:
  - `Fast demo / smoke test`
  - `Not for substantive analysis`

### Revision: Stage 3 — Scenario

This Revision 3 subsection is retained for history but superseded by the Revision 4.1 five-stage model.

#### Updated Scope

This earlier Revision 3 section is superseded by the April 1 stage split:

- Stage 3 is now **Investment Decisions** and owns optional decision-behavior enablement, model selection, parameter editing, calibration status, and review.
- Stage 4 is now **Scenario** and owns simulation mode, horizon settings, inherited primary population context, optional sensitivity populations, save/clone actions, and cross-stage validation before execution.
- Primary population selection remains owned by `Population`.
- Investment decisions are summarized in `Scenario` but not edited there.

#### Updated Naming Guidance

- New scenarios should not default to `New Scenario`.
- Scenario names should be suggested deterministically from current context, preferring:
  - policy set name,
  - primary population name,
  - simple fallback phrasing when full context is not yet available.
- The system may refine an auto-generated name until the user manually edits it.
- Manual edits freeze the name.

#### Updated Investment Decision Guidance

Investment decisions no longer live inside the Scenario stage. The guided flow remains:

1. `Enable`
2. `Model`
3. `Parameters`
4. `Review`

This remains optional, but it is now handled in the dedicated `Investment Decisions` stage before Scenario validation.

### Revision: Updated Nav Rail Labels

Revision 3 user-facing labels are:

```typescript
const STAGES = [
  {
    key: "policies",
    label: "Policies",
    activeFor: ["policies"],
  },
  {
    key: "population",
    label: "Population",
    activeFor: ["population", "data-fusion", "population-explorer"],
  },
  {
    key: "investment-decisions",
    label: "Investment Decisions",
    activeFor: ["investment-decisions"],
  },
  {
    key: "scenario",
    label: "Scenario",
    activeFor: ["scenario"],
  },
  {
    key: "results",
    label: "Run / Results / Compare",
    activeFor: ["results", "comparison", "decisions", "runner"],
  },
];
```

The persistence and routing model does not need a full internal rename in this revision if that adds unnecessary implementation risk.

### Revision: Mobile Demo Viability

Revision 3 adds a narrow-screen constraint:

- the app should be presentable and navigable on a phone for demos and light edits,
- without promising a full mobile product redesign.

#### Mobile Rules

- No page-level horizontal overflow at phone width.
- Stage navigation must remain reachable from every screen.
- The top bar should collapse low-priority actions into overflow when space is tight.
- Desktop split layouts stack vertically on phone.
- Fixed-width secondary panels move below primary content on phone.
- Population cards collapse to a single-column mobile layout.

#### Explicit Scope Boundary

This revision targets **demo-grade phone usability**, not perfect analytic parity on mobile. Dense result tables and advanced analysis remain desktop-first.

### Revision: Implementation Reference

For implementation-ready delta requirements, acceptance criteria, affected files, and story grouping, use:

- `_bmad-output/implementation-artifacts/ux-revision-3-implementation-spec.md`
