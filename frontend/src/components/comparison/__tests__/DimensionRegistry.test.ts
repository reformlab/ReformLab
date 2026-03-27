// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * DimensionRegistry tests — Story 20.6, AC-3.
 */

import { describe, expect, it, beforeEach } from "vitest";

import {
  register,
  unregister,
  get,
  listAll,
  scenarioDimension,
  portfolioDimension,
  populationDimension,
  engineDimension,
  matchesFilter,
} from "@/components/comparison/DimensionRegistry";
import type { ResultDetailResponse } from "@/api/types";

describe("DimensionRegistry", () => {
  beforeEach(() => {
    // Reset to default dimensions before each test
    unregister("custom-dimension");
  });

  it("lists default dimensions on module load", () => {
    const dimensions = listAll();
    const ids = dimensions.map((d) => d.id);

    expect(ids).toContain("scenario");
    expect(ids).toContain("portfolio");
    expect(ids).toContain("population");
    expect(ids).toContain("engine");
    expect(ids).toHaveLength(4);
  });

  it("registers a custom dimension", () => {
    const customDimension = {
      id: "custom-dimension",
      label: "Custom",
      description: "A custom dimension",
      getValue: () => "custom-value",
    };

    register(customDimension);

    const retrieved = get("custom-dimension");
    expect(retrieved).toBe(customDimension);
    expect(listAll()).toHaveLength(5);
  });

  it("throws error when registering duplicate dimension ID", () => {
    const customDimension = {
      id: "scenario", // Duplicate ID
      label: "Duplicate",
      description: "A duplicate dimension",
      getValue: () => "duplicate-value",
    };

    expect(() => register(customDimension)).toThrow(
      /Dimension with id 'scenario' already registered/
    );
  });

  it("unregisters a dimension", () => {
    const customDimension = {
      id: "custom-dimension",
      label: "Custom",
      description: "A custom dimension",
      getValue: () => "custom-value",
    };

    register(customDimension);
    expect(listAll()).toHaveLength(5);

    unregister("custom-dimension");
    expect(get("custom-dimension")).toBeUndefined();
    expect(listAll()).toHaveLength(4);
  });

  it("scenario dimension extracts scenario_id from result", () => {
    const mockResult: ResultDetailResponse = {
      run_id: "run-123",
      timestamp: "2026-03-27T10:00:00Z",
      run_kind: "scenario",
      start_year: 2025,
      end_year: 2030,
      population_id: "fr-synthetic-2024",
      seed: 42,
      row_count: 10000,
      manifest_id: "manifest-123",
      scenario_id: "my-scenario-id",
      adapter_version: "1.0",
      started_at: "2026-03-27T10:00:00Z",
      finished_at: "2026-03-27T10:01:00Z",
      status: "completed",
      data_available: true,
      template_name: "carbon_tax",
      policy_type: "carbon_tax",
      portfolio_name: null,
      indicators: null,
      columns: null,
      column_count: null,
    };

    const value = scenarioDimension.getValue(mockResult);
    expect(value).toEqual({
      scenarioId: "my-scenario-id",
      scenarioName: "my-scenario-id",
    });
  });

  it("scenario dimension returns legacy info for runs without scenario_id", () => {
    const mockResult: ResultDetailResponse = {
      run_id: "run-123",
      timestamp: "2026-03-27T10:00:00Z",
      run_kind: "scenario",
      start_year: 2025,
      end_year: 2030,
      population_id: "fr-synthetic-2024",
      seed: 42,
      row_count: 10000,
      manifest_id: "manifest-123",
      scenario_id: "", // Empty string = legacy
      adapter_version: "1.0",
      started_at: "2026-03-27T10:00:00Z",
      finished_at: "2026-03-27T10:01:00Z",
      status: "completed",
      data_available: true,
      template_name: "carbon_tax",
      policy_type: "carbon_tax",
      portfolio_name: null,
      indicators: null,
      columns: null,
      column_count: null,
    };

    const value = scenarioDimension.getValue(mockResult);
    expect(value).toEqual({
      scenarioId: "legacy",
      scenarioName: "Unknown Scenario (Legacy)",
    });
  });

  it("portfolio dimension uses portfolio_name or template_name", () => {
    const portfolioRun: ResultDetailResponse = {
      run_id: "run-123",
      timestamp: "2026-03-27T10:00:00Z",
      run_kind: "portfolio",
      start_year: 2025,
      end_year: 2030,
      population_id: "fr-synthetic-2024",
      seed: 42,
      row_count: 10000,
      manifest_id: "manifest-123",
      scenario_id: "scenario-123",
      adapter_version: "1.0",
      started_at: "2026-03-27T10:00:00Z",
      finished_at: "2026-03-27T10:01:00Z",
      status: "completed",
      data_available: true,
      template_name: null,
      policy_type: null,
      portfolio_name: "my-portfolio",
      indicators: null,
      columns: null,
      column_count: null,
    };

    const portfolioValue = portfolioDimension.getValue(portfolioRun);
    expect(portfolioValue).toBe("my-portfolio");

    const scenarioRun: ResultDetailResponse = {
      ...portfolioRun,
      run_kind: "scenario",
      portfolio_name: null,
      template_name: "carbon_tax",
    };

    const scenarioValue = portfolioDimension.getValue(scenarioRun);
    expect(scenarioValue).toBe("carbon_tax");
  });

  it("matchesFilter filters by scenario dimension", () => {
    const cell = {
      scenarioId: "scenario-1",
      populationId: "fr-synthetic-2024",
      status: "COMPLETED",
    };

    const scenarioFilter = {
      dimensionId: "scenario",
      operator: "equals" as const,
      values: ["scenario-1"],
    };

    expect(matchesFilter(cell, [scenarioFilter], new Map())).toBe(true);

    const mismatchedFilter = {
      dimensionId: "scenario",
      operator: "equals" as const,
      values: ["scenario-2"],
    };

    expect(matchesFilter(cell, [mismatchedFilter], new Map())).toBe(false);
  });

  it("matchesFilter filters by population dimension", () => {
    const cell = {
      scenarioId: "scenario-1",
      populationId: "fr-synthetic-2024",
      status: "COMPLETED",
    };

    const populationFilter = {
      dimensionId: "population",
      operator: "equals" as const,
      values: ["fr-synthetic-2024"],
    };

    expect(matchesFilter(cell, [populationFilter], new Map())).toBe(true);

    const mismatchedFilter = {
      dimensionId: "population",
      operator: "equals" as const,
      values: ["data-fusion-result"],
    };

    expect(matchesFilter(cell, [mismatchedFilter], new Map())).toBe(false);
  });

  it("matchesFilter filters by status", () => {
    const cell = {
      scenarioId: "scenario-1",
      populationId: "fr-synthetic-2024",
      status: "COMPLETED",
    };

    const statusFilter = {
      dimensionId: "status",
      operator: "in" as const,
      values: ["COMPLETED", "RUNNING"],
    };

    expect(matchesFilter(cell, [statusFilter], new Map())).toBe(true);

    const mismatchedFilter = {
      dimensionId: "status",
      operator: "in" as const,
      values: ["FAILED"],
    };

    expect(matchesFilter(cell, [mismatchedFilter], new Map())).toBe(false);
  });

  it("matchesFilter with contains operator", () => {
    const cell = {
      scenarioId: "scenario-1",
      populationId: "fr-synthetic-2024",
      status: "COMPLETED",
    };

    const containsFilter = {
      dimensionId: "scenario",
      operator: "contains" as const,
      values: ["scenario"],
    };

    expect(matchesFilter(cell, [containsFilter], new Map())).toBe(true);

    const mismatchedFilter = {
      dimensionId: "scenario",
      operator: "contains" as const,
      values: ["portfolio"],
    };

    expect(matchesFilter(cell, [mismatchedFilter], new Map())).toBe(false);
  });

  it("matchesFilter returns true when no filters", () => {
    const cell = {
      scenarioId: "scenario-1",
      populationId: "fr-synthetic-2024",
      status: "COMPLETED",
    };

    expect(matchesFilter(cell, [], new Map())).toBe(true);
  });

  it("matchesFilter requires all filters to match (AND logic)", () => {
    const cell = {
      scenarioId: "scenario-1",
      populationId: "fr-synthetic-2024",
      status: "COMPLETED",
    };

    const filters = [
      {
        dimensionId: "scenario",
        operator: "equals" as const,
        values: ["scenario-1"],
      },
      {
        dimensionId: "population",
        operator: "equals" as const,
        values: ["fr-synthetic-2024"],
      },
      {
        dimensionId: "status",
        operator: "in" as const,
        values: ["COMPLETED", "RUNNING"],
      },
    ];

    expect(matchesFilter(cell, filters, new Map())).toBe(true);

    const mismatchedFilters = [
      {
        dimensionId: "scenario",
        operator: "equals" as const,
        values: ["scenario-1"],
      },
      {
        dimensionId: "status",
        operator: "in" as const,
        values: ["FAILED"],
      },
    ];

    expect(matchesFilter(cell, mismatchedFilters, new Map())).toBe(false);
  });
});
