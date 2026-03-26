// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Mock data for the Population Data Explorer — Story 20.4.
 *
 * Provides realistic French household data for preview, profile, and summary views.
 * Used as fallback when the real API endpoints (Story 20.7) are unavailable.
 */

import type {
  PopulationPreviewResponse,
  PopulationProfileResponse,
  PopulationCrosstabResponse,
  ColumnInfo,
} from "@/api/types";

// ============================================================================
// Constants
// ============================================================================

const REGIONS = ["IDF", "PACA", "ARA", "OCC", "NAQ", "BFC", "NOR", "HDF", "GES", "PDL"];
const HOUSING_TYPES = ["apartment", "house", "collective", "mobile"];
const HEATING_TYPES = ["gas", "electric", "oil", "heat_pump", "wood", "district"];
const VEHICLE_TYPES = ["none", "petrol", "diesel", "hybrid", "electric", "lpg"];

// Deterministic pseudo-random helper (no Math.random — determinism required)
function pseudoRand(seed: number): number {
  let x = Math.sin(seed + 1) * 10000;
  x = x - Math.floor(x);
  return x;
}

function pickFrom<T>(arr: T[], seed: number): T {
  return arr[Math.floor(pseudoRand(seed) * arr.length)];
}

// ============================================================================
// Mock preview rows — 100 rows of French household data
// ============================================================================

function buildPreviewRows(): Record<string, unknown>[] {
  const rows: Record<string, unknown>[] = [];
  for (let i = 0; i < 100; i++) {
    const seed = i * 13;
    const incomeBase = 12000 + Math.floor(pseudoRand(seed) * 80000);
    const region = pickFrom(REGIONS, seed + 1);
    const housingType = pickFrom(HOUSING_TYPES, seed + 2);
    const heatingType = pickFrom(HEATING_TYPES, seed + 3);
    const vehicleType = pickFrom(VEHICLE_TYPES, seed + 4);
    const vehicleAge = vehicleType === "none" ? null : Math.floor(pseudoRand(seed + 5) * 20);
    const householdSize = 1 + Math.floor(pseudoRand(seed + 6) * 5);
    const energyConsumption = Math.floor(5000 + pseudoRand(seed + 7) * 25000);
    const carbonEmissions = Math.floor(energyConsumption * (0.1 + pseudoRand(seed + 8) * 0.4));

    rows.push({
      household_id: `FR-${String(i + 1).padStart(5, "0")}`,
      income: incomeBase,
      region,
      housing_type: housingType,
      heating_type: heatingType,
      vehicle_type: vehicleType,
      vehicle_age: vehicleAge,
      energy_consumption: energyConsumption,
      carbon_emissions: carbonEmissions,
      household_size: householdSize,
    });
  }
  return rows;
}

const PREVIEW_COLUMNS: ColumnInfo[] = [
  { name: "household_id", type: "string", description: "Unique household identifier" },
  { name: "income", type: "numeric", description: "Annual household income (EUR)" },
  { name: "region", type: "categorical", description: "French administrative region" },
  { name: "housing_type", type: "categorical", description: "Type of dwelling" },
  { name: "heating_type", type: "categorical", description: "Primary heating energy source" },
  { name: "vehicle_type", type: "categorical", description: "Primary vehicle fuel type" },
  { name: "vehicle_age", type: "numeric", description: "Vehicle age in years (null if no vehicle)" },
  { name: "energy_consumption", type: "numeric", description: "Annual energy consumption (kWh)" },
  { name: "carbon_emissions", type: "numeric", description: "Annual CO₂ equivalent emissions (kg)" },
  { name: "household_size", type: "numeric", description: "Number of persons in household" },
];

export const mockPopulationPreview: PopulationPreviewResponse = {
  id: "fr-synthetic-2024",
  name: "French Synthetic Population 2024",
  rows: buildPreviewRows(),
  columns: PREVIEW_COLUMNS,
  total_rows: 100000,
};

// ============================================================================
// Mock profile — per-column statistical profiles
// ============================================================================

function buildIncomeHistogram(): Array<{ bin_start: number; bin_end: number; count: number }> {
  const bins: Array<{ bin_start: number; bin_end: number; count: number }> = [];
  const step = 5000;
  // 20 bins from 0 to 100000
  for (let i = 0; i < 20; i++) {
    const binStart = i * step;
    const binEnd = (i + 1) * step;
    // Log-normal-ish distribution peaking around bin 5-7 (25K-35K)
    const peak = 7;
    const dist = Math.exp(-0.5 * Math.pow((i - peak) / 3, 2));
    bins.push({ bin_start: binStart, bin_end: binEnd, count: Math.floor(dist * 8000) });
  }
  return bins;
}

export const mockPopulationProfile: PopulationProfileResponse = {
  id: "fr-synthetic-2024",
  columns: [
    {
      name: "income",
      profile: {
        type: "numeric",
        count: 100000,
        nulls: 0,
        null_pct: 0,
        min: 0,
        max: 120000,
        mean: 28500,
        median: 25000,
        std: 15200,
        percentiles: { p10: 10000, p25: 17500, p50: 25000, p75: 37500, p90: 52000 },
        histogram_buckets: buildIncomeHistogram(),
      },
    },
    {
      name: "region",
      profile: {
        type: "categorical",
        count: 100000,
        nulls: 0,
        null_pct: 0,
        cardinality: 10,
        value_counts: [
          { value: "IDF", count: 22000 },
          { value: "ARA", count: 12000 },
          { value: "PACA", count: 10000 },
          { value: "OCC", count: 9500 },
          { value: "NAQ", count: 9000 },
          { value: "HDF", count: 8500 },
          { value: "GES", count: 8000 },
          { value: "NOR", count: 7500 },
          { value: "PDL", count: 7000 },
          { value: "BFC", count: 6500 },
        ],
      },
    },
    {
      name: "housing_type",
      profile: {
        type: "categorical",
        count: 100000,
        nulls: 0,
        null_pct: 0,
        cardinality: 4,
        value_counts: [
          { value: "apartment", count: 46000 },
          { value: "house", count: 38000 },
          { value: "collective", count: 12000 },
          { value: "mobile", count: 4000 },
        ],
      },
    },
    {
      name: "heating_type",
      profile: {
        type: "categorical",
        count: 100000,
        nulls: 0,
        null_pct: 0,
        cardinality: 6,
        value_counts: [
          { value: "gas", count: 38000 },
          { value: "electric", count: 28000 },
          { value: "oil", count: 14000 },
          { value: "heat_pump", count: 10000 },
          { value: "wood", count: 7000 },
          { value: "district", count: 3000 },
        ],
      },
    },
    {
      name: "vehicle_type",
      profile: {
        type: "categorical",
        count: 100000,
        nulls: 0,
        null_pct: 0,
        cardinality: 6,
        value_counts: [
          { value: "petrol", count: 38000 },
          { value: "diesel", count: 30000 },
          { value: "none", count: 16000 },
          { value: "hybrid", count: 9000 },
          { value: "electric", count: 5000 },
          { value: "lpg", count: 2000 },
        ],
      },
    },
    {
      name: "vehicle_age",
      profile: {
        type: "numeric",
        count: 84000,
        nulls: 16000,
        null_pct: 16,
        min: 0,
        max: 20,
        mean: 8.5,
        median: 8,
        std: 4.8,
        percentiles: { p10: 2, p25: 5, p50: 8, p75: 12, p90: 16 },
        histogram_buckets: Array.from({ length: 21 }, (_, i) => ({
          bin_start: i,
          bin_end: i + 1,
          count: Math.floor(84000 * Math.exp(-0.5 * Math.pow((i - 8) / 4, 2)) / 10),
        })),
      },
    },
    {
      name: "energy_consumption",
      profile: {
        type: "numeric",
        count: 100000,
        nulls: 0,
        null_pct: 0,
        min: 5000,
        max: 30000,
        mean: 14200,
        median: 13500,
        std: 4800,
        percentiles: { p10: 7500, p25: 10500, p50: 13500, p75: 17500, p90: 21000 },
        histogram_buckets: Array.from({ length: 20 }, (_, i) => ({
          bin_start: 5000 + i * 1500,
          bin_end: 5000 + (i + 1) * 1500,
          count: Math.floor(100000 * Math.exp(-0.5 * Math.pow((i - 6) / 4, 2)) / 10),
        })),
      },
    },
    {
      name: "carbon_emissions",
      profile: {
        type: "numeric",
        count: 100000,
        nulls: 0,
        null_pct: 0,
        min: 500,
        max: 12000,
        mean: 4200,
        median: 3800,
        std: 2100,
        percentiles: { p10: 1500, p25: 2500, p50: 3800, p75: 5500, p90: 7500 },
        histogram_buckets: Array.from({ length: 20 }, (_, i) => ({
          bin_start: i * 600,
          bin_end: (i + 1) * 600,
          count: Math.floor(100000 * Math.exp(-0.5 * Math.pow((i - 6) / 3.5, 2)) / 9),
        })),
      },
    },
    {
      name: "household_size",
      profile: {
        type: "numeric",
        count: 100000,
        nulls: 0,
        null_pct: 0,
        min: 1,
        max: 5,
        mean: 2.4,
        median: 2,
        std: 1.1,
        percentiles: { p10: 1, p25: 1, p50: 2, p75: 3, p90: 4 },
        histogram_buckets: [
          { bin_start: 1, bin_end: 2, count: 28000 },
          { bin_start: 2, bin_end: 3, count: 32000 },
          { bin_start: 3, bin_end: 4, count: 22000 },
          { bin_start: 4, bin_end: 5, count: 12000 },
          { bin_start: 5, bin_end: 6, count: 6000 },
        ],
      },
    },
    {
      name: "household_id",
      profile: {
        type: "categorical",
        count: 100000,
        nulls: 0,
        null_pct: 0,
        cardinality: 100000,
        value_counts: [],
      },
    },
  ],
};

// ============================================================================
// Mock summary — dataset-level overview
// ============================================================================

export interface PopulationSummaryData {
  record_count: number;
  column_count: number;
  estimated_memory_mb: number;
  columns: Array<{
    name: string;
    type: "numeric" | "categorical" | "boolean" | "string";
    null_pct: number;
    cardinality: number | null;
  }>;
}

export const mockPopulationSummary: PopulationSummaryData = {
  record_count: 100000,
  column_count: 10,
  estimated_memory_mb: 12.5,
  columns: [
    { name: "household_id", type: "string", null_pct: 0, cardinality: 100000 },
    { name: "income", type: "numeric", null_pct: 0, cardinality: null },
    { name: "region", type: "categorical", null_pct: 0, cardinality: 10 },
    { name: "housing_type", type: "categorical", null_pct: 0, cardinality: 4 },
    { name: "heating_type", type: "categorical", null_pct: 0, cardinality: 6 },
    { name: "vehicle_type", type: "categorical", null_pct: 0, cardinality: 6 },
    { name: "vehicle_age", type: "numeric", null_pct: 16, cardinality: null },
    { name: "energy_consumption", type: "numeric", null_pct: 0, cardinality: null },
    { name: "carbon_emissions", type: "numeric", null_pct: 0, cardinality: null },
    { name: "household_size", type: "numeric", null_pct: 0, cardinality: null },
  ],
};

// ============================================================================
// Mock crosstab — region × housing_type
// ============================================================================

export const mockCrosstabData: PopulationCrosstabResponse = {
  col_a: "region",
  col_b: "housing_type",
  data: REGIONS.map((region, i) => {
    const total = 5000 + Math.floor(pseudoRand(i * 7) * 20000);
    return {
      region,
      apartment: Math.floor(total * (0.3 + pseudoRand(i + 1) * 0.3)),
      house: Math.floor(total * (0.3 + pseudoRand(i + 2) * 0.3)),
      collective: Math.floor(total * 0.1),
      mobile: Math.floor(total * 0.05),
    };
  }),
};
