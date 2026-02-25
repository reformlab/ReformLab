---
title: Microsimulation Stakeholder Review Brief
description: Stakeholder-friendly review brief derived from the Product Requirements Document (PRD)
author: Lucas
date: 2026-02-24
source: _bmad-output/planning-artifacts/prd.md
---

# Microsimulation Stakeholder Review Brief

## Purpose Of This Brief

This brief prepares stakeholders to review and approve the Phase 1 direction for Microsimulation.  
It translates the PRD into a decision-ready summary focused on value, scope, risk, and governance.

## One-Page Snapshot

Microsimulation is an OpenFisca-first policy analysis product focused on environmental workflows.  
It helps analysts and researchers answer distributional policy questions in one governed workflow instead of stitching together multiple tools and undocumented scripts.

The Phase 1 goal is to prove that OpenFisca + Microsimulation layers can deliver credible carbon-tax and subsidy analysis on French households with transparent assumptions, dynamic projection, and reproducible outputs.

The core strategic position is complementary, not competitive, with OpenFisca:

- OpenFisca computes tax-benefit baseline results.
- Microsimulation handles data harmonization, environmental scenario templates, dynamic year-by-year orchestration, and analyst-facing workflows.

## Why Stakeholders Should Care

### Policy Teams

- Faster path from policy question to interpretable distributional outputs.
- Clear comparison of scenario trade-offs (winners, losers, fiscal effects).
- Transparent assumption logs that support internal challenge and revision.

### Research Teams

- Reproducible runs with deterministic outputs and explicit manifests.
- Notebook-first workflow aligned with current research practices.
- Extensible architecture that supports future domain expansion.

### Public-Sector Decision Makers

- Better auditability and trust than ad-hoc spreadsheet/script workflows.
- Lower dependence on restricted datasets for baseline analysis.
- Practical bridge between existing tax-benefit tools and broader policy simulation needs.

## Phase 1 Scope (What Is In)

Phase 1 focuses on proving product value and technical viability through a carbon tax use case.

### Included Capabilities

- Versioned OpenFisca integration (CSV/Parquet plus optional API orchestration).
- Data harmonization contracts across fiscal, synthetic, and environmental inputs.
- Template-driven baseline/reform environmental scenarios.
- Dynamic orchestrator for at least 10 yearly periods.
- Vintage/cohort tracking for environmental policy-relevant assets.
- Synthetic population workflow based on open published data.
- Built-in analytics for distributional, welfare, and fiscal outputs.
- Automatic assumption logging and immutable run manifests.
- Python API workflows in Jupyter notebooks.
- Early no-code scenario workflow for analysts.
- Carbon tax example set with multiple redistribution templates.
- Core documentation set (quickstart, templates, dynamic workflow, API docs, examples).

### Explicitly Deferred

- Endogenous market-clearing models.
- Physical-system loop modeling (climate/energy stock-flow).
- Full structural behavioral equilibrium layer.
- Public election showcase application.
- Cloud/distributed execution.
- Command-line-first interface.

## Success Gates For Phase 1 Review

Stakeholders should evaluate Phase 1 readiness against these outcome gates:

| Gate | What “Good” Looks Like |
| --- | --- |
| Usability Gate | New users can install, run, and interpret a meaningful example with minimal setup friction |
| Credibility Gate | Core benchmark and policy-validation tests pass and can be independently reproduced |
| Completeness Gate | A single run yields distributional, welfare, and fiscal outputs needed for policy comparison |
| Transparency Gate | Every run emits a complete manifest of parameters, sources, and assumptions |
| Interoperability Gate | OpenFisca outputs can be imported and used in combined policy analysis workflows |

## Strategic Bets And Review Risks

| Strategic Bet / Risk | Why It Matters | Current Mitigation |
| --- | --- | --- |
| Dynamic orchestration complexity may exceed MVP capacity | Could delay delivery before core value is proven | Start with deterministic yearly loop + one validated vintage dimension |
| Solo delivery concentration risk | Momentum and continuity depend on one builder | AI-assisted implementation, strict scope control, test-driven architecture |
| Trust gap for a new workflow layer | Adoption depends on external confidence in combined results | Benchmark validation, deterministic execution, assumption transparency |
| Perceived overlap with PolicyEngine | Differentiation risk in ecosystem narrative | Position on environmental templates, dynamic vintage analysis, and run governance |
| Limited external adoption after MVP | Product could remain a single-user tool | Prioritize external pilot usage and publish reproducible example workflows |

## Decisions Requested In This Review

Stakeholders are asked to approve or redirect the following:

1. Product Direction: Confirm Phase 1 remains focused on carbon-tax validation as proof of a reusable OpenFisca-first environmental workflow.
2. Positioning: Endorse OpenFisca-first strategy as the primary ecosystem path.
3. Scope Discipline: Confirm deferred features remain out of Phase 1 unless tied to validation risk.
4. Validation Standard: Confirm that independent reproducibility, benchmark pass criteria, and deterministic 10-year runs are mandatory release gates.
5. Pilot Strategy: Approve targeting at least one external policy/research pilot after Phase 1 validation.

## Questions To Resolve During Review

- What minimum evidence is required for stakeholders to treat results as decision-grade?
- Which external pilot profile has highest strategic value: ministry evaluation team or academic lab?
- What governance expectations apply for manifest auditability and version traceability before broader adoption?
- Which Phase 2 capability should be prioritized first after validation: reporting, sensitivity automation, or replication packaging?

## System Value Flow

The value proposition is a transparent path from data to policy insight:

```mermaid
flowchart LR
    A[OpenFisca + Data Inputs] --> B[Environmental Scenario Templates]
    B --> C[Dynamic Yearly Orchestrator]
    C --> D[Indicators and Comparisons]
    D --> E[Run Manifests and Assumption Logs]
    E --> F[Credible Policy Decisions]
```

Diagram summary: OpenFisca baselines and environmental templates flow through deterministic dynamic orchestration to produce auditable outputs stakeholders can trust and act on.

## Recommended Review Outcome

Approve Phase 1 continuation if all success gates are accepted as release criteria and the decision items above are confirmed.  
If not, adjust scope now before implementation effort expands into deferred capabilities.

## Source Traceability

This brief is derived from:

- `_bmad-output/planning-artifacts/prd.md`
- Its referenced planning research and product brief inputs listed in PRD frontmatter
