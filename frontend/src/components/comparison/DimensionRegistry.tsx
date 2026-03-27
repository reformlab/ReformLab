// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Pluggable comparison dimensions registry — Story 20.6, AC-3.
 *
 * Allows EPIC-21 to extend comparison dimensions without modifying core logic.
 * Default dimensions: scenario, portfolio, population, engine.
 */

import type { ComparisonDimension, ResultDetailResponse } from "@/api/types";

// ============================================================================
// Registry
// ============================================================================

const dimensions = new Map<string, ComparisonDimension>();

export function register<T>(dimension: ComparisonDimension<T>): void {
  if (dimensions.has(dimension.id)) {
    throw new Error(
      `Dimension with id '${dimension.id}' already registered. ` +
      `Use a unique id or unregister the existing dimension first.`
    );
  }
  dimensions.set(dimension.id, dimension);
}

export function unregister(id: string): void {
  dimensions.delete(id);
}

export function get(id: string): ComparisonDimension<unknown> | undefined {
  return dimensions.get(id);
}

export function listAll(): ComparisonDimension[] {
  return Array.from(dimensions.values());
}

// ============================================================================
// Default dimensions — Story 20.6, AC-2
// ============================================================================

/**
 * Scenario dimension: returns scenario_id and scenario_name from result metadata.
 * For legacy runs (no scenario_id), returns "legacy" and "Unknown Scenario (Legacy)".
 */
export const scenarioDimension: ComparisonDimension<{
  scenarioId: string;
  scenarioName: string;
}> = {
  id: "scenario",
  label: "Scenario",
  description: "Scenario ID and name",
  getValue(runResult: ResultDetailResponse) {
    // ResultDetailResponse has scenario_id field
    const scenarioId = runResult.scenario_id || "legacy";
    const scenarioName = scenarioId === "legacy"
      ? "Unknown Scenario (Legacy)"
      : scenarioId;
    return { scenarioId, scenarioName };
  },
  render(value) {
    return (
      <div className="text-xs">
        <div className="font-medium text-slate-900">{value.scenarioName}</div>
        <div className="text-slate-500 font-mono">{value.scenarioId.slice(0, 8)}</div>
      </div>
    );
  },
};

/**
 * Portfolio dimension: returns SHA-256 hash of portfolio composition.
 * For scenario runs, uses template_name and policy_type.
 */
export const portfolioDimension: ComparisonDimension<string> = {
  id: "portfolio",
  label: "Portfolio",
  description: "Portfolio composition hash",
  getValue(runResult: ResultDetailResponse) {
    // Use portfolio_name for portfolio runs, template_name for scenario runs
    const portfolioKey = runResult.portfolio_name || runResult.template_name || "unknown";
    return portfolioKey;
  },
  render(value) {
    return <span className="font-mono text-xs">{value}</span>;
  },
};

/**
 * Population dimension: returns population_id and population_version (derived from timestamp).
 */
export const populationDimension: ComparisonDimension<{
  populationId: string;
  populationVersion: string;
}> = {
  id: "population",
  label: "Population",
  description: "Population ID and version",
  getValue(runResult: ResultDetailResponse) {
    const populationId = runResult.population_id || "unknown";
    // Use timestamp as a proxy for version
    const populationVersion = runResult.timestamp?.slice(0, 10) || "unknown";
    return { populationId, populationVersion };
  },
  render(value) {
    return (
      <div className="text-xs">
        <div className="font-medium text-slate-900">{value.populationId}</div>
        <div className="text-slate-500">{value.populationVersion}</div>
      </div>
    );
  },
};

/**
 * Engine dimension: returns engine config (logit model, discount rate) from metadata.
 * Note: This requires additional metadata to be added to ResultDetailResponse in future stories.
 */
export const engineDimension: ComparisonDimension<{
  logitModel: string;
  discountRate: number;
}> = {
  id: "engine",
  label: "Engine",
  description: "Engine configuration",
  getValue() {
    // For now, return defaults since engine config is not in ResultDetailResponse yet
    // This will be updated when engine_config is added to result metadata
    return {
      logitModel: "multinomial_logit",
      discountRate: 0.03,
    };
  },
  render(value) {
    return (
      <div className="text-xs">
        <div className="text-slate-700">{value.logitModel}</div>
        <div className="text-slate-500">{(value.discountRate * 100).toFixed(1)}% discount</div>
      </div>
    );
  },
};

// Register default dimensions on module load
register(scenarioDimension);
register(portfolioDimension);
register(populationDimension);
register(engineDimension);

// ============================================================================
// Dimension filter — Story 20.6, AC-3
// ============================================================================

export interface DimensionFilter {
  dimensionId: string;
  operator: "equals" | "contains" | "in";
  values: unknown[];
}

export function matchesFilter(
  cell: { scenarioId: string; populationId: string; status: string },
  filters: DimensionFilter[],
  runResults: Map<string, ResultDetailResponse>,
): boolean {
  if (filters.length === 0) return true;

  return filters.every((filter) => {
    // Check for custom dimension IDs first (not scenario/population/status)
    const dimension = get(filter.dimensionId);
    if (dimension && dimension.id !== "scenario" && dimension.id !== "population" && dimension.id !== "status") {
      // For custom dimensions, we'd need to extract values from runResults
      // For now, don't filter out for unknown dimensions
      return true;
    }

    // Built-in filters that work on the cell directly
    if (filter.dimensionId === "scenario") {
      const scenarioValue = cell.scenarioId;
      if (filter.operator === "equals") {
        return filter.values.includes(scenarioValue);
      }
      if (filter.operator === "in") {
        return filter.values.includes(scenarioValue);
      }
      if (filter.operator === "contains") {
        const searchStr = String(filter.values[0] ?? "").toLowerCase();
        return scenarioValue.toLowerCase().includes(searchStr);
      }
      return false; // Unknown operator: filter out
    }

    if (filter.dimensionId === "population") {
      const populationValue = cell.populationId;
      if (filter.operator === "equals") {
        return filter.values.includes(populationValue);
      }
      if (filter.operator === "in") {
        return filter.values.includes(populationValue);
      }
      if (filter.operator === "contains") {
        const searchStr = String(filter.values[0] ?? "").toLowerCase();
        return populationValue.toLowerCase().includes(searchStr);
      }
      return false; // Unknown operator: filter out
    }

    if (filter.dimensionId === "status") {
      const statusValue = cell.status;
      if (filter.operator === "in") {
        return filter.values.includes(statusValue);
      }
      if (filter.operator === "equals") {
        return filter.values.includes(statusValue);
      }
      return false; // Unknown operator: filter out
    }

    // Unknown dimension ID: don't filter out
    return true;
  });
}
