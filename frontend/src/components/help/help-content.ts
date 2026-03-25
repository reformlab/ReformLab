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
  "data-fusion": {
    title: "Population Builder",
    summary: "Create a synthetic population by selecting and merging data from multiple statistical sources.",
    tips: [
      "Select at least two data sources from the available providers to begin",
      "Overlapping variables (shared across sources) enable statistical matching for higher-quality fusion",
      "The merge method determines how records are combined — conditional sampling preserves correlations best",
      "Preview the generated population to verify demographic distributions before proceeding",
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
    title: "Policies & Portfolio",
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
    title: "Population",
    summary: "Select or build the household population dataset for your simulation.",
    tips: [
      "Pre-built populations (e.g., French synthetic 2024) are ready to use immediately",
      "Use the Data Fusion Workbench to merge multiple statistical sources into a custom population",
      "The population defines household composition, income distributions, and consumption patterns",
    ],
    concepts: [
      { term: "Data Fusion", definition: "Combining records from multiple data sources into a unified population dataset using statistical matching." },
    ],
  },
  "engine": {
    title: "Engine Configuration",
    summary: "Configure the simulation engine: time horizon, random seed, and investment decision modelling.",
    tips: [
      "Set start and end years to define the simulation horizon (2025–2050 is typical)",
      "An explicit seed ensures reproducible results across runs — leave blank for random",
      "Investment decision modelling enables behavioural responses to policy changes",
    ],
    concepts: [
      { term: "Random Seed", definition: "A value that initialises the random number generator, ensuring reproducible stochastic results." },
      { term: "Investment Decisions", definition: "Household decisions about capital goods (vehicles, heating systems) modelled as discrete choices under policy incentives." },
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
      "Use the nav rail on the left to move between Policies, Population, Engine, and Results stages.",
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
};

export function getHelpEntry(activeStage: StageKey, activeSubView: SubView | null): HelpEntry {
  if (activeSubView) {
    const subKey = `${activeStage}/${activeSubView}`;
    if (HELP_CONTENT[subKey]) return HELP_CONTENT[subKey]!;
  }
  return HELP_CONTENT[activeStage] ?? HELP_CONTENT["policies"]!;
}
