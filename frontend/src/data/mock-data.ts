// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Static mock data for all ReformLab prototype screens. */

export interface Population {
  id: string;
  name: string;
  households: number;
  source: string;
  year: number;
}

export interface Template {
  id: string;
  name: string;
  type: string;
  parameterCount: number;
  description: string;
  parameterGroups: string[];
  is_custom: boolean;
  // Story 24.1 / AC-1: Runtime availability metadata (required fields)
  runtime_availability: "live_ready" | "live_unavailable";
  availability_reason: string | null;
}

export interface Parameter {
  id: string;
  label: string;
  value: number;
  baseline: number;
  unit: string;
  group: string;
  type: "slider" | "number";
  min?: number;
  max?: number;
}

export interface DecileData {
  decile: string;
  baseline: number;
  reform: number;
  delta: number;
}

// @deprecated — use WorkspaceScenario (pending 20.3–20.6)
export interface Scenario {
  id: string;
  name: string;
  status: "draft" | "ready" | "running" | "completed" | "failed";
  isBaseline: boolean;
  parameterChanges: number;
  linkedBaseline?: string;
  lastRun?: string;
  templateId?: string;
  templateName?: string;
}

export interface SummaryStatistic {
  id: string;
  label: string;
  value: string;
  trend: "up" | "down" | "neutral";
  trendValue: string;
}

export const mockPopulations: Population[] = [
  {
    id: "quick-test-population",
    name: "Quick Test Population",
    households: 100,
    source: "Built-in demo data",
    year: 2026,
  },
  {
    id: "fr-synthetic-2024",
    name: "France Synthetic 2024",
    households: 100_000,
    source: "INSEE marginals",
    year: 2024,
  },
  {
    id: "fr-synthetic-2023",
    name: "France Synthetic 2023",
    households: 100_000,
    source: "INSEE marginals",
    year: 2023,
  },
  {
    id: "eu-silc-2022",
    name: "EU-SILC France Extract 2022",
    households: 50_000,
    source: "Eurostat EU-SILC",
    year: 2022,
  },
];

export const mockTemplates: Template[] = [
  {
    id: "carbon-tax-flat",
    name: "Carbon Tax \u2014 Flat Rate",
    type: "carbon-tax",
    parameterCount: 8,
    description: "Flat carbon tax rate applied uniformly across all households",
    parameterGroups: ["Tax Rates", "Thresholds"],
    is_custom: false,
    // Story 24.4: Runtime availability metadata
    runtime_availability: "live_ready",
    availability_reason: null,
  },
  {
    id: "carbon-tax-progressive",
    name: "Carbon Tax \u2014 Progressive",
    type: "carbon-tax",
    parameterCount: 12,
    description: "Progressive rate by income decile with exemptions",
    parameterGroups: ["Tax Rates", "Thresholds"],
    is_custom: false,
    runtime_availability: "live_ready",
    availability_reason: null,
  },
  {
    id: "carbon-tax-dividend",
    name: "Carbon Tax \u2014 With Dividend",
    type: "carbon-tax",
    parameterCount: 10,
    description: "Flat tax with equal per-capita dividend redistribution",
    parameterGroups: ["Tax Rates", "Thresholds", "Redistribution"],
    is_custom: false,
    runtime_availability: "live_ready",
    availability_reason: null,
  },
  {
    id: "subsidy-energy",
    name: "Energy Efficiency Subsidy",
    type: "subsidy",
    parameterCount: 6,
    description: "Means-tested energy efficiency subsidy for low-income households",
    parameterGroups: ["Redistribution", "Thresholds"],
    is_custom: false,
    runtime_availability: "live_ready",
    availability_reason: null,
  },
  {
    id: "feebate-vehicle",
    name: "Vehicle Feebate",
    type: "feebate",
    parameterCount: 9,
    description: "Fee on high-emission, rebate on low-emission vehicles",
    parameterGroups: ["Redistribution", "Thresholds"],
    is_custom: false,
    runtime_availability: "live_ready",
    availability_reason: null,
  },
  // Story 24.4: Non-regression — rebate template for TYPE_LABELS/TYPE_COLORS coverage
  {
    id: "rebate-energy",
    name: "Energy Rebate",
    type: "rebate",
    parameterCount: 6,
    description: "Direct rebate for energy-efficient purchases and renovations",
    parameterGroups: ["Redistribution", "Thresholds"],
    is_custom: false,
    runtime_availability: "live_ready",
    availability_reason: null,
  },
  // Story 24.4: Surfaced pack templates - Vehicle Malus
  {
    id: "vehicle-malus-flat-rate",
    name: "Vehicle Malus \u2014 Flat Rate",
    type: "vehicle_malus",
    parameterCount: 4,
    description: "Flat-rate malus for vehicles exceeding CO2 emissions threshold",
    parameterGroups: ["emission_threshold", "malus_rate_per_gkm", "rate_schedule", "threshold_schedule"],
    is_custom: true,
    runtime_availability: "live_ready",
    availability_reason: null,
  },
  {
    id: "vehicle-malus-french-2026",
    name: "Vehicle Malus \u2014 French 2026 System",
    type: "vehicle_malus",
    parameterCount: 5,
    description: "Tiered malus system following French 2026 emission bands",
    parameterGroups: ["emission_bands", "malus_schedule", "exemption_categories"],
    is_custom: true,
    runtime_availability: "live_ready",
    availability_reason: null,
  },
  // Story 24.4: Surfaced pack templates - Energy Poverty Aid
  {
    id: "energy-poverty-cheque-energie",
    name: "Energy Poverty Aid \u2014 Cheque \u00c9nergie",
    type: "energy_poverty_aid",
    parameterCount: 4,
    description: "Flat energy voucher for eligible households based on income ceiling",
    parameterGroups: ["income_ceiling", "rate_schedule", "eligible_categories"],
    is_custom: true,
    runtime_availability: "live_ready",
    availability_reason: null,
  },
  {
    id: "energy-poverty-generous",
    name: "Energy Poverty Aid \u2014 Generous",
    type: "energy_poverty_aid",
    parameterCount: 5,
    description: "Enhanced aid with higher income ceiling and household size multiplier",
    parameterGroups: ["income_ceiling", "rate_schedule", "eligible_categories", "household_size_multiplier"],
    is_custom: true,
    runtime_availability: "live_ready",
    availability_reason: null,
  },
];

export const mockParameters: Parameter[] = [
  {
    id: "tax_rate",
    label: "Carbon tax rate",
    value: 44,
    baseline: 44,
    unit: "EUR/tCO2",
    group: "Tax Rates",
    type: "slider",
    min: 0,
    max: 200,
  },
  {
    id: "tax_rate_growth",
    label: "Annual rate increase",
    value: 10,
    baseline: 10,
    unit: "EUR/yr",
    group: "Tax Rates",
    type: "number",
  },
  {
    id: "exemption_threshold",
    label: "Exemption threshold",
    value: 15000,
    baseline: 15000,
    unit: "EUR/yr",
    group: "Thresholds",
    type: "slider",
    min: 0,
    max: 50000,
  },
  {
    id: "phase_in_years",
    label: "Phase-in period",
    value: 3,
    baseline: 3,
    unit: "years",
    group: "Thresholds",
    type: "number",
  },
  {
    id: "dividend_per_capita",
    label: "Dividend per capita",
    value: 120,
    baseline: 0,
    unit: "EUR/year",
    group: "Redistribution",
    type: "slider",
    min: 0,
    max: 500,
  },
  {
    id: "means_test_ceiling",
    label: "Means-test ceiling",
    value: 30000,
    baseline: 30000,
    unit: "EUR/yr",
    group: "Redistribution",
    type: "number",
  },
  {
    id: "rebate_rate",
    label: "Rebate rate",
    value: 0.15,
    baseline: 0.15,
    unit: "%",
    group: "Redistribution",
    type: "slider",
    min: 0,
    max: 1,
  },
  {
    id: "simulation_years",
    label: "Simulation horizon",
    value: 5,
    baseline: 5,
    unit: "years",
    group: "Thresholds",
    type: "number",
  },
];

export const mockDecileData: DecileData[] = [
  { decile: "D1", baseline: -120, reform: -80, delta: 40 },
  { decile: "D2", baseline: -180, reform: -150, delta: 30 },
  { decile: "D3", baseline: -240, reform: -210, delta: 30 },
  { decile: "D4", baseline: -310, reform: -290, delta: 20 },
  { decile: "D5", baseline: -400, reform: -390, delta: 10 },
  { decile: "D6", baseline: -520, reform: -520, delta: 0 },
  { decile: "D7", baseline: -680, reform: -690, delta: -10 },
  { decile: "D8", baseline: -890, reform: -920, delta: -30 },
  { decile: "D9", baseline: -1200, reform: -1260, delta: -60 },
  { decile: "D10", baseline: -1800, reform: -1950, delta: -150 },
];

export const mockScenarios: Scenario[] = [
  {
    id: "baseline",
    name: "Baseline (No Policy)",
    status: "completed",
    isBaseline: true,
    parameterChanges: 0,
    lastRun: "2026-02-27 14:32",
  },
  {
    id: "reform-a",
    name: "Carbon Tax + Dividend",
    status: "completed",
    isBaseline: false,
    parameterChanges: 3,
    linkedBaseline: "baseline",
    lastRun: "2026-02-27 14:35",
    templateId: "carbon-tax-dividend",
    templateName: "Carbon Tax \u2014 With Dividend",
  },
];

export const mockSummaryStats: SummaryStatistic[] = [
  {
    id: "gini",
    label: "Gini coefficient",
    value: "0.289",
    trend: "down",
    trendValue: "-0.012",
  },
  {
    id: "fiscal-cost",
    label: "Net fiscal cost",
    value: "\u20AC2.1B",
    trend: "up",
    trendValue: "+\u20AC0.3B",
  },
  {
    id: "affected-pop",
    label: "Affected population",
    value: "78.4%",
    trend: "neutral",
    trendValue: "0.0%",
  },
];

// ============================================================================
// Data fusion mock data — Story 17.1
// ============================================================================

export interface MockDataSource {
  id: string;
  provider: string;
  name: string;
  description: string;
  variable_count: number;
  record_count: number | null;
  source_url: string;
}

export interface MockMergeMethod {
  id: string;
  name: string;
  what_it_does: string;
  assumption: string;
  when_appropriate: string;
  tradeoff: string;
  parameters: Array<{ name: string; type: string; description: string; required: boolean }>;
}

export const mockDataSources: Record<string, MockDataSource[]> = {
  insee: [
    {
      id: "filosofi_2021_commune",
      provider: "insee",
      name: "Filosofi 2021 Commune",
      description: "Filosofi 2021 commune-level income data (deciles D1-D9, median, poverty rate)",
      variable_count: 13,
      record_count: null,
      source_url: "https://www.insee.fr/fr/statistiques/6036907",
    },
    {
      id: "filosofi_2021_iris_declared",
      provider: "insee",
      name: "Filosofi 2021 IRIS Declared",
      description: "Filosofi 2021 IRIS-level declared income (quartiles/deciles)",
      variable_count: 14,
      record_count: null,
      source_url: "https://www.insee.fr/fr/statistiques/6036907",
    },
    {
      id: "filosofi_2021_iris_disposable",
      provider: "insee",
      name: "Filosofi 2021 IRIS Disposable",
      description: "Filosofi 2021 IRIS-level disposable income (quartiles/deciles)",
      variable_count: 14,
      record_count: null,
      source_url: "https://www.insee.fr/fr/statistiques/6036907",
    },
  ],
  eurostat: [
    {
      id: "ilc_di01",
      provider: "eurostat",
      name: "ILC DI01 Income Distribution",
      description: "Income distribution by quantile (EU-SILC deciles D1-D10, shares/EUR)",
      variable_count: 8,
      record_count: null,
      source_url: "https://ec.europa.eu/eurostat/databrowser/view/ilc_di01",
    },
    {
      id: "nrg_d_hhq",
      provider: "eurostat",
      name: "NRG D HHQ Energy Consumption",
      description: "Disaggregated final energy consumption in households",
      variable_count: 8,
      record_count: null,
      source_url: "https://ec.europa.eu/eurostat/databrowser/view/nrg_d_hhq",
    },
  ],
  ademe: [
    {
      id: "base_carbone",
      provider: "ademe",
      name: "Base Carbone",
      description: "Base Carbone V23.6 emission factors (CSV from data.gouv.fr)",
      variable_count: 15,
      record_count: null,
      source_url: "https://www.data.gouv.fr/fr/datasets/base-carbone-v23-6/",
    },
  ],
  sdes: [
    {
      id: "vehicle_fleet",
      provider: "sdes",
      name: "Vehicle Fleet",
      description:
        "Vehicle fleet composition by fuel type, age, Crit'Air, region (communal-level data from data.gouv.fr)",
      variable_count: 8,
      record_count: null,
      source_url: "https://www.data.gouv.fr/fr/datasets/parc-de-vehicules-en-circulation/",
    },
  ],
};

export const mockMergeMethods: MockMergeMethod[] = [
  {
    id: "uniform",
    name: "Uniform Distribution",
    what_it_does:
      "Matches each household from one source to a randomly chosen household from another source, with equal probability.",
    assumption:
      "Variables in the two sources are statistically independent — knowing a household's income tells you nothing about their vehicle type.",
    when_appropriate:
      "Quick baseline when no better information is available about correlations between sources.",
    tradeoff:
      "Fast and simple, but may produce unrealistic combinations (e.g., low-income household paired with luxury vehicle).",
    parameters: [
      {
        name: "seed",
        type: "int",
        description: "Random seed for deterministic results (default: 42)",
        required: false,
      },
    ],
  },
  {
    id: "ipf",
    name: "Iterative Proportional Fitting (IPF)",
    what_it_does:
      "Adjusts matching weights so that the final population matches known aggregate statistics (marginals) from official sources.",
    assumption:
      "The population matches known distribution totals — if INSEE says 10% of households are in decile 1, the result respects that.",
    when_appropriate: "You have reliable census or administrative marginals to calibrate against.",
    tradeoff:
      "More accurate aggregates, but requires knowing the target marginals upfront; may not converge if constraints are contradictory.",
    parameters: [
      {
        name: "seed",
        type: "int",
        description: "Random seed for deterministic results (default: 42)",
        required: false,
      },
      {
        name: "ipf_constraints",
        type: "list[constraint]",
        description: "List of {dimension, targets} marginal constraints to satisfy",
        required: false,
      },
    ],
  },
  {
    id: "conditional",
    name: "Conditional Sampling",
    what_it_does:
      "Groups households by a shared variable (e.g., income bracket), then matches randomly only within the same group.",
    assumption:
      "Given the grouping variable, remaining variables are independent — within the same income bracket, vehicle and heating choices are uncorrelated.",
    when_appropriate:
      "You know that some variable (like income or region) correlates with variables in both sources.",
    tradeoff:
      "Preserves known correlations through the grouping variable, but assumes independence within groups.",
    parameters: [
      {
        name: "seed",
        type: "int",
        description: "Random seed for deterministic results (default: 42)",
        required: false,
      },
      {
        name: "strata_columns",
        type: "list[str]",
        description: "Shared column names to use for stratification",
        required: false,
      },
    ],
  },
];

// ============================================================================
// Portfolio mock data — Story 17.2
// ============================================================================

export interface MockPortfolioPolicy {
  name: string;
  template_id: string;
  policy_type: string;
  parameters: Record<string, unknown>;
  rate_schedule: Record<string, number>;
}

export interface MockPortfolio {
  name: string;
  description: string;
  version: string;
  policy_count: number;
  policies: MockPortfolioPolicy[];
  resolution_strategy: string;
}

export const mockPortfolios: MockPortfolio[] = [
  {
    name: "green-transition-2030",
    description: "Carbon tax with energy efficiency subsidy for low-income households",
    version: "1.0",
    policy_count: 2,
    policies: [
      {
        name: "Carbon Tax Trajectory",
        template_id: "carbon-tax-flat",
        policy_type: "carbon_tax",
        parameters: { tax_rate: 50, tax_rate_growth: 10 },
        rate_schedule: { "2025": 50, "2026": 60, "2027": 70, "2028": 80, "2029": 90, "2030": 100 },
      },
      {
        name: "Energy Efficiency Subsidy",
        template_id: "subsidy-energy",
        policy_type: "subsidy",
        parameters: { means_test_ceiling: 30000 },
        rate_schedule: { "2025": 5000, "2026": 5000, "2027": 4000 },
      },
    ],
    resolution_strategy: "error",
  },
];

// ============================================================================
// Results mock data — Story 17.3
// ============================================================================

export interface MockResultItem {
  run_id: string;
  timestamp: string;
  run_kind: string;
  template_name: string | null;
  policy_type: string | null;
  portfolio_name: string | null;
  start_year: number;
  end_year: number;
  row_count: number;
  status: string;
  data_available: boolean;
}

export const mockResults: MockResultItem[] = [
  {
    run_id: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    timestamp: "2026-03-07T22:15:30Z",
    run_kind: "scenario",
    template_name: "Carbon Tax \u2014 With Dividend",
    policy_type: "carbon_tax",
    portfolio_name: null,
    start_year: 2025,
    end_year: 2030,
    row_count: 600000,
    status: "completed",
    data_available: true,
  },
  {
    run_id: "b2c3d4e5-f6a7-8901-bcde-f12345678901",
    timestamp: "2026-03-07T21:45:12Z",
    run_kind: "portfolio",
    template_name: null,
    policy_type: null,
    portfolio_name: "green-transition-2030",
    start_year: 2025,
    end_year: 2035,
    row_count: 1100000,
    status: "completed",
    data_available: false,
  },
  {
    run_id: "c3d4e5f6-a7b8-9012-cdef-123456789012",
    timestamp: "2026-03-07T20:30:00Z",
    run_kind: "scenario",
    template_name: "Carbon Tax \u2014 Uniform Rate",
    policy_type: "carbon_tax",
    portfolio_name: null,
    start_year: 2025,
    end_year: 2027,
    row_count: 0,
    status: "failed",
    data_available: false,
  },
];

/** Simulated progress steps for RunProgressBar */
export const mockSimulationSteps = [
  "Initializing population data...",
  "Computing year 2025...",
  "Computing year 2026...",
  "Computing year 2027...",
  "Computing year 2028...",
  "Computing year 2029...",
  "Aggregating indicators...",
  "Finalizing results...",
];

// ============================================================================
// Comparison mock data — Story 17.4
// ============================================================================

import type { PortfolioComparisonResponse } from "@/api/types";

/** Mock comparison response for ComparisonDashboardScreen development. */
export const mockComparisonResponse: PortfolioComparisonResponse = {
  comparisons: {
    distributional: {
      columns: ["field_name", "decile", "year", "metric", "Run A", "Run B", "delta_Run B"],
      data: {
        field_name: Array(10).fill("disposable_income") as string[],
        decile: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        year: Array(10).fill(2025) as number[],
        metric: Array(10).fill("mean") as string[],
        "Run A": [-120, -180, -240, -310, -400, -520, -680, -890, -1200, -1800],
        "Run B": [-80, -150, -210, -290, -390, -520, -690, -920, -1260, -1950],
        "delta_Run B": [40, 30, 30, 20, 10, 0, -10, -30, -60, -150],
      },
    },
    fiscal: {
      columns: ["field_name", "year", "metric", "Run A", "Run B", "delta_Run B"],
      data: {
        field_name: ["tax_revenue", "tax_revenue", "tax_revenue"],
        year: [2025, 2026, 2027],
        metric: ["revenue", "revenue", "revenue"],
        "Run A": [2100000000, 2300000000, 2500000000],
        "Run B": [1800000000, 2000000000, 2200000000],
        "delta_Run B": [-300000000, -300000000, -300000000],
      },
    },
  },
  cross_metrics: [
    {
      criterion: "max_fiscal_revenue",
      best_portfolio: "Run A",
      value: 6900000000,
      all_values: { "Run A": 6900000000, "Run B": 6000000000 },
    },
    {
      criterion: "min_fiscal_cost",
      best_portfolio: "Run B",
      value: 0,
      all_values: { "Run A": 0, "Run B": 0 },
    },
    {
      criterion: "max_fiscal_balance",
      best_portfolio: "Run A",
      value: 6900000000,
      all_values: { "Run A": 6900000000, "Run B": 6000000000 },
    },
  ],
  portfolio_labels: ["Run A", "Run B"],
  metadata: { baseline_label: "Run A", indicator_types: ["distributional", "fiscal"] },
  warnings: [],
};

// ============================================================================
// Decision viewer mock data — Story 17.5
// ============================================================================

import type { DecisionSummaryResponse } from "../api/types";

export const mockDecisionSummaryResponse: DecisionSummaryResponse = {
  run_id: "mock-decision-run",
  domains: [
    {
      domain_name: "vehicle",
      alternative_ids: ["keep_current", "buy_petrol", "buy_diesel", "buy_hybrid", "buy_ev", "buy_no_vehicle"],
      alternative_labels: {
        keep_current: "Keep Current",
        buy_petrol: "Petrol",
        buy_diesel: "Diesel",
        buy_hybrid: "Hybrid",
        buy_ev: "Electric (EV)",
        buy_no_vehicle: "No Vehicle",
      },
      yearly_outcomes: [
        { year: 2025, total_households: 10000, counts: { keep_current: 7000, buy_petrol: 800, buy_diesel: 400, buy_hybrid: 600, buy_ev: 1000, buy_no_vehicle: 200 }, percentages: { keep_current: 70, buy_petrol: 8, buy_diesel: 4, buy_hybrid: 6, buy_ev: 10, buy_no_vehicle: 2 }, mean_probabilities: null },
        { year: 2026, total_households: 10000, counts: { keep_current: 6200, buy_petrol: 700, buy_diesel: 300, buy_hybrid: 700, buy_ev: 1800, buy_no_vehicle: 300 }, percentages: { keep_current: 62, buy_petrol: 7, buy_diesel: 3, buy_hybrid: 7, buy_ev: 18, buy_no_vehicle: 3 }, mean_probabilities: null },
        { year: 2027, total_households: 10000, counts: { keep_current: 5500, buy_petrol: 600, buy_diesel: 200, buy_hybrid: 800, buy_ev: 2600, buy_no_vehicle: 300 }, percentages: { keep_current: 55, buy_petrol: 6, buy_diesel: 2, buy_hybrid: 8, buy_ev: 26, buy_no_vehicle: 3 }, mean_probabilities: null },
        { year: 2028, total_households: 10000, counts: { keep_current: 4800, buy_petrol: 500, buy_diesel: 100, buy_hybrid: 900, buy_ev: 3400, buy_no_vehicle: 300 }, percentages: { keep_current: 48, buy_petrol: 5, buy_diesel: 1, buy_hybrid: 9, buy_ev: 34, buy_no_vehicle: 3 }, mean_probabilities: null },
        { year: 2029, total_households: 10000, counts: { keep_current: 4000, buy_petrol: 400, buy_diesel: 50, buy_hybrid: 1000, buy_ev: 4250, buy_no_vehicle: 300 }, percentages: { keep_current: 40, buy_petrol: 4, buy_diesel: 0.5, buy_hybrid: 10, buy_ev: 42.5, buy_no_vehicle: 3 }, mean_probabilities: null },
      ],
      eligibility: { n_total: 10000, n_eligible: 7000, n_ineligible: 3000 },
    },
    {
      domain_name: "heating",
      alternative_ids: ["keep_current", "gas_boiler", "heat_pump", "electric", "wood_pellet"],
      alternative_labels: {
        keep_current: "Keep Current",
        gas_boiler: "Gas Boiler",
        heat_pump: "Heat Pump",
        electric: "Electric",
        wood_pellet: "Wood/Pellet",
      },
      yearly_outcomes: [
        { year: 2025, total_households: 10000, counts: { keep_current: 8000, gas_boiler: 500, heat_pump: 1000, electric: 300, wood_pellet: 200 }, percentages: { keep_current: 80, gas_boiler: 5, heat_pump: 10, electric: 3, wood_pellet: 2 }, mean_probabilities: null },
        { year: 2026, total_households: 10000, counts: { keep_current: 7200, gas_boiler: 400, heat_pump: 1700, electric: 400, wood_pellet: 300 }, percentages: { keep_current: 72, gas_boiler: 4, heat_pump: 17, electric: 4, wood_pellet: 3 }, mean_probabilities: null },
        { year: 2027, total_households: 10000, counts: { keep_current: 6500, gas_boiler: 300, heat_pump: 2400, electric: 500, wood_pellet: 300 }, percentages: { keep_current: 65, gas_boiler: 3, heat_pump: 24, electric: 5, wood_pellet: 3 }, mean_probabilities: null },
      ],
      eligibility: null,
    },
  ],
  metadata: { start_year: 2025, end_year: 2029 },
  warnings: [],
};
