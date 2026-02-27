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

export interface Scenario {
  id: string;
  name: string;
  status: "draft" | "ready" | "running" | "completed" | "failed";
  isBaseline: boolean;
  parameterChanges: number;
  linkedBaseline?: string;
  lastRun?: string;
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
  },
  {
    id: "carbon-tax-progressive",
    name: "Carbon Tax \u2014 Progressive",
    type: "carbon-tax",
    parameterCount: 12,
    description: "Progressive rate by income decile with exemptions",
  },
  {
    id: "carbon-tax-dividend",
    name: "Carbon Tax \u2014 With Dividend",
    type: "carbon-tax",
    parameterCount: 10,
    description: "Flat tax with equal per-capita dividend redistribution",
  },
  {
    id: "subsidy-energy",
    name: "Energy Efficiency Subsidy",
    type: "subsidy",
    parameterCount: 6,
    description: "Means-tested energy efficiency subsidy for low-income households",
  },
  {
    id: "feebate-vehicle",
    name: "Vehicle Feebate",
    type: "feebate",
    parameterCount: 9,
    description: "Fee on high-emission, rebate on low-emission vehicles",
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
