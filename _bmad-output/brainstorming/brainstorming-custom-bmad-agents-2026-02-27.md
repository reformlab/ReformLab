---
stepsCompleted: [1, 2, 3, 4]
inputDocuments: []
session_topic: 'Custom BMAD agents and workflows for the ReformLab micro-simulation platform'
session_goals: 'Generate rich possibilities for where custom BMAD agents/workflows add the most value across the full ReformLab lifecycle — from policy research to simulation execution to results interpretation'
selected_approach: 'ai-recommended'
techniques_used: ['Morphological Analysis', 'Cross-Pollination', 'Assumption Reversal']
ideas_generated: [22]
session_active: false
workflow_completed: true
---

# Brainstorming Session Results

**Topic:** Custom BMAD Agents & Workflows for ReformLab
**Facilitator:** Lucas
**Date:** 2026-02-27

## Session Overview

**Topic:** Custom BMAD agents and workflows for the ReformLab micro-simulation platform
**Goals:** Generate rich possibilities for where custom BMAD agents/workflows add the most value across the full ReformLab lifecycle — from policy research to simulation execution to results interpretation

**Key constraint established during session:** BMAD agents should only be used where input is *unstructured or ambiguous* (PDFs, failure diagnosis, narrative interpretation). Everything else should be deterministic product features. Future possibility of embedding BMAD agents in the end-user UX is parked — requires AI model API, not wanted for now.

### Context Guidance

_ReformLab is an OpenFisca-first environmental policy analysis platform with layered architecture: Computation Adapter → Data Layer → Scenario Templates → Dynamic Orchestrator → Indicators → Governance → Interfaces. The dynamic orchestrator is the core product. France/Europe focus, open-data-first, assumption transparency non-optional._

## Technique Selection

**Approach:** AI-Recommended Techniques

- **Morphological Analysis:** Systematic matrix of ReformLab layers x BMAD capabilities — 7 architecture layers x 3 BMAD artifact types (agents, workflows, modules)
- **Cross-Pollination:** Borrowed patterns from financial trading (confidence-scored triage), climate science (divergence narration), and urban planning (sensitivity analysis)
- **Assumption Reversal:** Stress-tested ideas against solo-user scenario, country-switching, and API cost/availability constraints

---

## Technique Execution Results

### Morphological Analysis

Systematically explored all 7 ReformLab architecture layers. Generated 21 initial ideas, then filtered aggressively based on Lucas's principle: **"If it can be a deterministic product feature, it should be."**

**Retired to deterministic product features:**
- Scenario forms and closed-question UIs (not AI)
- Assumption manifests — built into every run automatically
- Scenario comparison tables — deterministic diff
- Indicator interpretation — part of the product
- Governance peer review — part of the product
- Pre-flight validation for run configurations — algorithmic
- Sensitivity analysis — algorithmic
- Tutorials and onboarding — in-app UI tutorials preferred

### Cross-Pollination

- **From financial trading:** Confidence-scored extraction with human-in-the-loop triage (green/yellow/red) — folded into the Policy Document Ingestion Agent
- **From climate science:** Divergence narration pattern for multi-scenario communication — folded into the Results Communication Agent
- **From urban planning:** Sensitivity-first culture — retired to deterministic product

### Assumption Reversal

- Solo-user assumption: Data Scout Agent validated as high priority (accelerates demo creation)
- Country-switching: Reform Wizard and Variable Explorer need country-agnostic design
- API cost/availability: All agents need a frontier model eventually — design now, activate when ready

---

## Organized Ideas by Theme

### Theme 1: Unstructured Document Intelligence

**Policy Document Ingestion Agent (#10-11 + #22)** — THE STAR IDEA
_Concept:_ Accepts PDFs of legislative texts, ministerial decrees, or policy proposals. Extracts parameters (rates, thresholds, dates, eligibility criteria, phase-in schedules), maps them to OpenFisca variables, produces draft model configuration with confidence-scored triage: green (auto-accept), yellow (review suggested), red (must verify).
_Novelty:_ Every policy document is structured differently — can't be a form. Confidence scoring borrowed from financial trading makes AI extraction trustworthy by making uncertainty visible.

**Reform Definition Wizard Workflow (#4)**
_Concept:_ Guided workflow translating policy intent ("carbon tax at 44EUR/tonne with household exemptions below median income") into valid OpenFisca reform definitions. Asks policy questions, not code questions.
_Novelty:_ Bridges the gap between policy language and OpenFisca's technical API.

### Theme 2: Data Research & Preparation

**Policy Data Scout Agent (#1)** — HIGH PRIORITY FOR DEMO CREATION
_Concept:_ Researches and locates open datasets (INSEE, Eurostat, EU-SILC, emission factors) for a given policy scenario. Produces structured data manifests with source URLs, vintage dates, licensing.
_Novelty:_ Turns manual "hunt for the right CSV" into guided, reproducible research. Immediate value: accelerates creation of multiple demo examples in the coming weeks. Could extend the existing BMAD Analyst agent (Mary).

**Data Contract Validator Workflow (#2)** — BORDERLINE
_Concept:_ Validates raw data against target schemas with conversational explanations of failures.
_Decision:_ May be deterministic enough for the product.

**Synthetic Population Builder Workflow (#3)** — BORDERLINE
_Concept:_ Guides construction of synthetic household populations with documented assumptions.
_Decision:_ May be deterministic with good UX.

### Theme 3: Debugging & Quality Assurance

**Run Failure Diagnostician Agent (#13)** — CRUCIAL
_Concept:_ Examines run manifests, logs, intermediate outputs, and data vintages to diagnose orchestration failures. Detective work across multiple layers — data mismatch? Parameter out of range? OpenFisca version incompatibility?
_Novelty:_ Debugging multi-year orchestration failures is genuinely ambiguous. Even more valuable as a solo developer with no colleague to rubber-duck with.

**QA / Sanity Check Agent (#21)**
_Concept:_ Reviews simulation outputs against benchmarks, historical data, and common-sense heuristics. Flags plausibility issues ("This says carbon tax generated negative revenue..." or "40% emission drop in year 1 — realistic?").
_Novelty:_ Checks plausibility, not just types and ranges. Requires domain knowledge.

### Theme 4: Communication & Navigation

**Results Communication Agent (#20 + #23)**
_Concept:_ Produces audience-appropriate outputs from simulation runs: technical appendix for economists, executive summary for politicians, public-facing explainer. Includes divergence narration for multi-scenario comparisons (explains *why* results differ, not just *that* they differ).
_Novelty:_ Same data, three completely different narratives. Fundamentally a language task.

**OpenFisca Variable Explorer Agent (#5)**
_Concept:_ Navigates the OpenFisca-France variable tree, explains computation chains in plain language. Maps policy intent to the right variables and their dependencies.
_Novelty:_ OpenFisca's variable graph is huge and poorly documented. Acts as a navigable map.

**Vintage Compatibility Checker Workflow (#6)** — BORDERLINE
_Concept:_ Migration reports when updating OpenFisca versions — flags renames, deprecations, formula changes.
_Decision:_ Could be partly deterministic, but migration advice may need judgment.

---

## Prioritization

### High Priority (build these, immediate value)

| Agent/Workflow | Why now |
|---|---|
| **Policy Data Scout Agent (#1)** | Accelerates demo creation work in the coming weeks |
| **Policy Document Ingestion Agent (#10-11 + #22)** | Star idea — genuinely needs AI, highest value |
| **Run Failure Diagnostician Agent (#13)** | Crucial for solo development — debugging partner |

### Medium Priority (high value, can wait for API readiness)

| Agent/Workflow | Why later |
|---|---|
| **Results Communication Agent (#20+23)** | Needs frontier model quality for good narratives |
| **QA / Sanity Check Agent (#21)** | Needs domain knowledge + good model |
| **OpenFisca Variable Explorer Agent (#5)** | Valuable but Lucas knows the variable tree today |
| **Reform Definition Wizard Workflow (#4)** | Valuable but manual process works for now |

### Borderline (may belong in deterministic product)

| Agent/Workflow | Decision |
|---|---|
| **Data Contract Validator (#2)** | Probably deterministic |
| **Synthetic Population Builder (#3)** | Probably deterministic with good UX |
| **Vintage Compatibility Checker (#6)** | Probably deterministic |

---

## Build Path

**How to create these agents:** Use BMAD's existing builder tools:
- **Bond** (Agent Builder agent) — creates new BMAD agents with proper structure, personas, menus, compliance
- **Wendy** (Workflow Builder agent) — creates new BMAD workflows with states, transitions, error handling
- **Mary** (Analyst agent) — could serve as starting point / extension for the Data Scout Agent

**Key design principle:** All agents should be designed now within BMAD but activated only when an AI model API is available. France-first, but country-agnostic in architecture.

---

## Session Summary

**Ideas generated:** 22 total, 10 survived filtering, 3 identified as high priority
**Key insight:** The strongest filter was "Does this need language understanding or ambiguity handling?" — everything else belongs as a deterministic product feature
**Breakthrough concept:** Confidence-scored triage pattern (#22) from financial trading, applied to policy document ingestion
**Creative journey:** Morphological Analysis provided systematic coverage, Cross-Pollination injected non-obvious patterns, Assumption Reversal confirmed priorities and pruned scope
