// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import type { StageKey, SubView } from "@/types/workspace";

export interface HelpEntry {
  title: string;
  summary: string;
  tips: string[];
  concepts?: Array<{ term: string; definition: string }>;
}

export const HELP_CONTENT: Record<string, HelpEntry> = {
  "population/data-fusion": {
    title: "Population Builder",
    summary: "Create a synthetic population by selecting and merging data from multiple statistical sources.",
    tips: [
      "Select at least two data sources from the available providers to begin",
      "Use Inspect columns on any source card to verify row counts and available fields before selecting it",
      "Overlapping variables (shared across sources) enable statistical matching for higher-quality fusion",
      "The merge method determines how records are combined — conditional sampling preserves correlations best",
      "Preview the generated population to verify record counts and merged columns before proceeding",
    ],
    concepts: [
      { term: "Data Fusion", definition: "Combining records from multiple data sources into a unified population dataset using statistical matching." },
      { term: "Overlapping Variables", definition: "Variables present in multiple sources that serve as matching keys for statistical fusion." },
      { term: "Conditional Sampling", definition: "A merge method that preserves correlations between variables by sampling conditionally on shared keys." },
    ],
  },
  "portfolio": {
    title: "Portfolio Composition",
    summary: "Compose policy templates into a single reform package with inline parameter editing and conflict resolution.",
    tips: [
      "A portfolio of one policy is valid — single-policy portfolios are fully supported",
      "Policy ordering matters — policies are applied in the sequence shown in the composition panel",
      "Use year schedules to phase in rate changes over the simulation horizon",
      "The conflict resolution strategy determines what happens when two policies modify the same parameter",
      "Saved portfolios are independent of scenarios — saving a portfolio does not save the scenario",
    ],
    concepts: [
      { term: "Policy Portfolio", definition: "A bundle of one or more policy templates combined into a coherent reform package." },
      { term: "Conflict Resolution", definition: "A strategy for handling cases where two policies set the same parameter (sum, first_wins, last_wins, max, or error)." },
      { term: "Year Schedule", definition: "A per-year rate mapping that allows gradual phase-in of policy changes over time." },
    ],
  },
  "configuration:population": {
    title: "Select Population",
    summary: "Choose the population dataset for your simulation.",
    tips: [
      "Pre-built populations (e.g., French synthetic 2024) are ready to use immediately",
      "Custom populations created in the Population Builder appear here automatically",
      "The population defines household composition, income distributions, and consumption patterns used in the simulation",
    ],
  },
  "configuration:template": {
    title: "Choose Policy Template",
    summary: "Select a policy template that defines the reform to simulate.",
    tips: [
      "Each template maps to an OpenFisca policy type with predefined parameters",
      "Custom templates can be created with the 'Create Custom Template' button",
      "The template determines which parameters are available for configuration in the next step",
    ],
  },
  "configuration:parameters": {
    title: "Configure Parameters",
    summary: "Adjust policy parameters to define your specific reform scenario.",
    tips: [
      "Parameter values define the details of your reform — tax rates, thresholds, exemptions",
      "Changes from default values are tracked and shown in the assumptions review",
      "Use realistic values based on published policy proposals for meaningful analysis",
    ],
    concepts: [
      { term: "Parameter Overrides", definition: "Changes to default template values that define how your reform differs from the baseline." },
    ],
  },
  "configuration:assumptions": {
    title: "Review Assumptions",
    summary: "Verify all assumptions and data sources before running the simulation.",
    tips: [
      "The assumption review lists every parameter value and data source used in the simulation",
      "All assumptions are recorded in the run manifest for reproducibility",
      "Proceed to simulation when you are satisfied with the configuration",
    ],
  },
  "run": {
    title: "Run Simulation",
    summary: "Execute the configured simulation across the specified year range.",
    tips: [
      "The simulation computes both baseline and reform scenarios year by year",
      "Results include distributional impact, fiscal balance, and welfare indicators",
      "Each run gets a unique ID for tracking, export, and cross-run comparison",
    ],
  },
  "progress": {
    title: "Simulation in Progress",
    summary: "The simulation is computing results for each year in the range.",
    tips: [
      "Year-by-year computation ensures demographic transitions and behavioral responses are captured",
      "Results are typically ready within a few seconds for standard-sized populations",
    ],
  },
  "runner": {
    title: "Simulation Runner",
    summary: "Configure and execute a full multi-year simulation run with explicit controls.",
    tips: [
      "Set start and end years to define the simulation horizon",
      "An explicit seed ensures reproducible results — leave blank for random",
      "Past simulation results are listed below the configuration form",
    ],
  },
  "results": {
    title: "Results Overview",
    summary: "Explore the distributional impact of your reform across income deciles.",
    tips: [
      "The bar chart shows net impact by income decile — positive values mean households gain",
      "Summary statistics highlight the mean impact and the most affected groups",
      "Use 'Compare Runs' to see side-by-side analysis of multiple scenarios",
      "Export data as CSV (for spreadsheets) or Parquet (for programmatic analysis) from the Data & Export tab",
    ],
  },
  "comparison": {
    title: "Comparison Dashboard",
    summary: "Compare up to 5 simulation runs side-by-side with distributional and fiscal indicators.",
    tips: [
      "Select 2–5 completed runs from the list, then click Compare",
      "The first selected run is treated as the baseline for relative comparisons",
      "Toggle between absolute and relative views to see raw values or percentage changes",
      "Click any chart bar to see detailed indicator values in the panel below",
    ],
    concepts: [
      { term: "Baseline Run", definition: "The reference run against which all other selected runs are compared to compute deltas." },
      { term: "Distributional Indicators", definition: "Metrics showing how reform impact varies across income deciles." },
      { term: "Cross-Portfolio Metrics", definition: "Aggregate metrics that rank and compare reform packages on key dimensions." },
    ],
  },
  "decisions": {
    title: "Behavioral Decisions",
    summary: "Explore how households respond to policy changes through discrete choice modeling.",
    tips: [
      "The transition chart shows year-by-year changes in household vehicle fleet or heating systems",
      "Filter by income decile to see how behavioral responses vary across the population",
      "Click a year on the chart to see detailed transition probabilities for that period",
    ],
    concepts: [
      { term: "Discrete Choice Model", definition: "A model of household decision-making that assigns probabilities to technology adoption choices based on costs and preferences." },
      { term: "Transition Probabilities", definition: "The likelihood that a household switches from one technology to another in a given year." },
    ],
  },

  // Stage-level keys (Story 20.1, updated Story 20.3)
  "policies": {
    title: "Policy",
    summary: "Browse policy templates and compose a portfolio inline — no multi-step wizard. A single policy is a valid portfolio.",
    tips: [
      "The template browser (left) and composition panel (right) are visible simultaneously — no separate steps",
      "Add a single policy template to create a portfolio of one; two or more policies unlock conflict detection",
      "Conflicts are detected automatically and shown inline with a resolution strategy selector",
      "Save, Load, Clone, and Clear operate on the portfolio only — scenario operations are separate",
      "The nav rail shows a completion checkmark when a portfolio is saved and linked to this scenario",
    ],
    concepts: [
      { term: "Policy Portfolio", definition: "A bundle of one or more policy templates combined into a coherent reform package. Portfolios are saved independently of scenarios." },
      { term: "Conflict Resolution", definition: "A strategy for handling cases where two policies set the same parameter: sum, first_wins, last_wins, max, or error (blocks save)." },
      { term: "Year Schedule", definition: "A per-year rate mapping that allows gradual phase-in of policy changes over time." },
      { term: "Inline Composition", definition: "The template browser and composition panel are always visible side-by-side, eliminating the need for a step-by-step wizard flow." },
    ],
  },
  "population": {
    title: "Population Library",
    summary: "Browse, preview, explore, and select household population datasets. Upload custom CSV/Parquet files or build a new fused population.",
    tips: [
      "Click Inspect on a card to confirm row counts and scan the available columns before opening anything else",
      "Click Preview (eye icon) for a quick 100-row scan before committing — closes on Escape or backdrop click",
      "Click Explore (chart icon) to open the Full Data Explorer with Table, Profile, and Summary tabs",
      "Click Select to link a population to your active scenario — a checkmark appears on the card",
      "Built-in populations cannot be deleted; only generated and uploaded ones can",
      "Upload a CSV or Parquet file to add a custom population — schema is validated client-side before confirming",
      "Click Build New to open the Data Fusion Workbench and merge multiple statistical sources",
    ],
    concepts: [
      { term: "Data Fusion", definition: "Combining records from multiple data sources into a unified population dataset using statistical matching." },
      { term: "Origin Tag", definition: "[Built-in] for pre-loaded datasets, [Generated] for Data Fusion outputs, [Uploaded] for user-provided files." },
    ],
  },
  "population/population-explorer": {
    title: "Full Data Explorer",
    summary: "Investigate a population dataset with three views: paginated Table, column Profile with histograms, and dataset Summary.",
    tips: [
      "Table tab: click column headers to sort, type in filter boxes to narrow rows, use Prev/Next for pagination",
      "Profile tab: select any column from the list on the left — numeric columns show histograms and percentile bars",
      "Profile tab: use the Cross-tabulate selector to overlay a second categorical column as a stacked bar chart",
      "Summary tab: the completeness table highlights columns with >10% nulls in amber and >50% nulls in red",
    ],
    concepts: [
      { term: "Column Profile", definition: "Statistical summary of a single column: distribution histogram, percentiles, min/max/mean for numerics; value counts for categoricals." },
      { term: "Cross-tabulation", definition: "A stacked bar chart showing how values of one column distribute across the categories of another." },
    ],
  },
  "investment-decisions": {
    title: "Investment Decisions",
    summary: "Configure behavioral response models for household technology adoption (vehicles, heating systems). Optional advanced feature—skip when disabled.",
    tips: [
      "Investment decisions are disabled by default—enable the toggle to configure behavioral modeling",
      "When enabled, you must select a logit model and configure taste parameters",
      "The four-step wizard guides you through: Enable, Model selection, Parameters, and Review",
      "Use Continue to Scenario at any time—Stage 3 is optional and does not block validation when disabled",
      "Calibration is optional but recommended for realistic behavioral responses",
    ],
    concepts: [
      { term: "Discrete Choice Model", definition: "A statistical model that predicts household choices between alternatives (e.g., vehicle types) based on utility maximization." },
      { term: "Logit Model", definition: "A type of discrete choice model: Multinomial Logit (basic), Nested Logit (groups similar alternatives), Mixed Logit (allows preference variation)." },
      { term: "Taste Parameters", definition: "Coefficients that capture household preferences for technology attributes: price sensitivity, range anxiety, environmental preference." },
    ],
  },
  "scenario": {
    title: "Scenario Configuration",
    summary: "Review your inherited primary population, configure time horizon and execution settings, and run cross-stage validation. This stage is the integration gate before execution.",
    tips: [
      "Primary population is inherited from Stage 2 and cannot be edited in Stage 4 — click 'Change in Stage 2' to modify your selection",
      "Runtime always shows 'Live OpenFisca' as the current execution mode — no runtime selector needed",
      "A 'Replay' badge may appear to indicate that your last run used replay mode — this is historical information only",
      "Sensitivity population is optional — add it for comparison analysis",
      "Set Start and End year — the 'N-year projection' label updates automatically. Max 50 years.",
      "Investment decisions show a read-only summary here — click 'Configure in Stage 3' to edit them",
      "The right panel shows a live validation checklist — all red checks must be resolved before Run is enabled.",
      "Click 'Go to Stage X' links in validation messages to jump directly to the fixing stage",
      "Save Scenario persists the full configuration (portfolio + population + settings) to your saved list.",
      "Clone Scenario creates a copy with '(copy)' appended — useful for sensitivity analysis variants.",
      "The memory preflight check runs when you click Run — it estimates if your population fits in RAM.",
    ],
    concepts: [
      { term: "Inherited Population", definition: "The primary population selected in Stage 2 that will be used for this scenario. Shown as read-only context in Stage 4 to prevent accidental changes during final review. Not editable in Stage 4 — use 'Change in Stage 2' link to modify." },
      { term: "Runtime Mode", definition: "The current execution mode is always 'Live OpenFisca' for standard web execution. An optional 'Replay' badge may appear to indicate that the scenario's last run used replay mode (historical metadata only)." },
      { term: "Random Seed", definition: "A value that initialises the random number generator, ensuring reproducible stochastic results." },
      { term: "Logit Model", definition: "A discrete choice model (multinomial, nested, or mixed logit) governing how households respond to policy-driven cost changes." },
      { term: "Cross-stage validation", definition: "A checklist that verifies portfolio, population, time horizon, investment decisions, and memory constraints are all satisfied before the simulation can run." },
    ],
  },

  // Stage 4 sub-view keys (Story 20.1)
  "results/runner": {
    title: "Simulation Runner",
    summary: "Configure and execute a full multi-year simulation run with explicit controls.",
    tips: [
      "First launch? The demo scenario is pre-configured — click Run Simulation to see your first distributional chart.",
      "Set start and end years to define the simulation horizon",
      "An explicit seed ensures reproducible results — leave blank for random",
      "Past simulation results are listed below the configuration form",
    ],
  },
  "onboarding": {
    title: "Getting Started",
    summary: "Welcome to ReformLab — your environmental policy analysis workspace.",
    tips: [
      "Click the scenario name in the top bar to switch scenarios, create new, or reset to the demo.",
      "The demo scenario is pre-configured with the Carbon Tax + Dividend template — just click Run.",
      "Use the nav rail on the left to move between Policies, Population, Investment Decisions, Scenario, and Results stages.",
    ],
  },
  "results/comparison": {
    title: "Comparison Dashboard",
    summary: "Compare up to 5 simulation runs side-by-side with distributional and fiscal indicators.",
    tips: [
      "Select 2–5 completed runs from the list, then click Compare",
      "The first selected run is treated as the baseline for relative comparisons",
      "Toggle between absolute and relative views to see raw values or percentage changes",
    ],
    concepts: [
      { term: "Baseline Run", definition: "The reference run against which all other selected runs are compared to compute deltas." },
      { term: "Distributional Indicators", definition: "Metrics showing how reform impact varies across income deciles." },
    ],
  },
  "results/decisions": {
    title: "Behavioral Decisions",
    summary: "Explore how households respond to policy changes through discrete choice modeling.",
    tips: [
      "The transition chart shows year-by-year changes in household vehicle fleet or heating systems",
      "Filter by income decile to see how behavioral responses vary across the population",
      "Click a year on the chart to see detailed transition probabilities for that period",
    ],
    concepts: [
      { term: "Discrete Choice Model", definition: "A model of household decision-making that assigns probabilities to technology adoption choices based on costs and preferences." },
      { term: "Transition Probabilities", definition: "The likelihood that a household switches from one technology to another in a given year." },
    ],
  },
  "results/manifest": {
    title: "Run Manifest Viewer",
    summary: "Inspect the complete reproducibility metadata for any simulation run, including assumptions, data sources, hashes, and lineage.",
    tips: [
      "The manifest records every assumption, data source, and computation step for full reproducibility",
      "Hash values verify data integrity — data_hashes confirm input files, integrity_hash confirms the full computation",
      "Lineage tracking shows parent and child manifests, enabling traceability across multi-year scenarios",
      "When panel data is evicted from memory, the manifest remains accessible with a metadata-only flag",
      "Use collapsible sections to navigate the comprehensive metadata display",
      "Click truncated hashes to see full values in tooltips",
    ],
    concepts: [
      { term: "Run Manifest", definition: "A comprehensive record of all metadata for a simulation run, including assumptions, data sources, hashes, versions, and lineage links." },
      { term: "Data Hash", definition: "A SHA-256 hash of input data files that confirms the exact data version used in the computation." },
      { term: "Integrity Hash", definition: "A SHA-256 hash of the complete computation output that verifies the reproducibility of the full simulation result." },
      { term: "Lineage", definition: "The chain of related manifests via parent_manifest_id and child_manifests, enabling traceability across multi-year scenarios and derived runs." },
      { term: "Assumptions", definition: "Parameter values and configuration settings that define how the reform differs from baseline, recorded with source attribution." },
      { term: "Mappings", definition: "The bidirectional mapping between project parameter names and OpenFisca variable names used in computation." },
    ],
  },
};

export function getHelpEntry(activeStage: StageKey, activeSubView: SubView | null): HelpEntry {
  if (activeSubView) {
    const subKey = `${activeStage}/${activeSubView}`;
    if (HELP_CONTENT[subKey]) return HELP_CONTENT[subKey]!;
  }
  return HELP_CONTENT[activeStage] ?? HELP_CONTENT["policies"]!;
}
