// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Data fetching hooks for the ReformLab API. */

import { useCallback, useEffect, useState } from "react";

import { listPopulations, getPopulationPreview, getPopulationProfile, getPopulationCrosstab } from "@/api/populations";
import { listTemplates, getTemplate } from "@/api/templates";
import { listScenarios as apiListScenarios } from "@/api/scenarios";
import { runScenario as apiRunScenario } from "@/api/runs";
import { getIndicators } from "@/api/indicators";
import { listDataSources, listMergeMethods, getDataSourcePreview, getDataSourceProfile } from "@/api/data-fusion";
import { listPortfolios as apiListPortfolios, validatePortfolio as apiValidatePortfolio } from "@/api/portfolios";
import { listResults as apiListResults, deleteResult as apiDeleteResult } from "@/api/results";
import { AuthError } from "@/api/client";
import type {
  PopulationLibraryItem,
  RunRequest,
  RunResponse,
  TemplateListItem,
  TemplateDetailResponse,
  IndicatorResponse,
  PortfolioListItem,
  ValidatePortfolioRequest,
  ValidatePortfolioResponse,
  ResultListItem,
  PopulationPreviewResponse,
  PopulationProfileResponse,
  PopulationCrosstabResponse,
} from "@/api/types";
import type { Template, Parameter, MockDataSource, MockMergeMethod, MockPortfolio } from "@/data/mock-data";
import {
  mockTemplates,
  mockParameters,
  mockDataSources,
  mockMergeMethods,
  mockPortfolios,
} from "@/data/mock-data";
import { mockPopulationPreview, mockPopulationProfile } from "@/data/mock-population-explorer";

// ============================================================================
// Populations
// ============================================================================

export function usePopulations() {
  // Story 21.2 / AC6: Use PopulationLibraryItem directly from API
  // Mock data fallback with minimal evidence fields
  const mockWithEvidence: PopulationLibraryItem[] = [
    // Story 22.4: Quick Test Population for fast demos and smoke tests
    {
      id: "quick-test-population",
      name: "Quick Test Population",
      households: 100,
      source: "Built-in demo data",
      year: 2026,
      origin: "built-in",
      canonical_origin: "synthetic-public",
      access_mode: "bundled",
      trust_status: "demo-only",
      is_synthetic: true,
      column_count: 8,
      created_date: "2026-01-01T00:00:00Z",
    },
    {
      id: "mock-population",
      name: "Mock Population",
      households: 1000,
      source: "mock",
      year: 2025,
      origin: "built-in",
      canonical_origin: "synthetic-public",
      access_mode: "bundled",
      trust_status: "exploratory",
      column_count: 10,
      created_date: null,
      is_synthetic: true,
    },
  ];
  const [populations, setPopulations] = useState<PopulationLibraryItem[]>(mockWithEvidence);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [usingMockData, setUsingMockData] = useState(false);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await listPopulations();
      setPopulations(items.length > 0 ? items : []);
      setUsingMockData(false);
    } catch (err) {
      if (err instanceof AuthError) throw err;
      setError(err instanceof Error ? err : new Error(String(err)));
      setUsingMockData(true);
    } finally {
      setLoading(false);
    }
  }, []);

  return { populations, loading, error, usingMockData, refetch: fetch };
}

// ============================================================================
// Templates
// ============================================================================

export function useTemplates() {
  const [templates, setTemplates] = useState<Template[]>(mockTemplates);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [usingMockData, setUsingMockData] = useState(false);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await listTemplates();
      setTemplates(items.length > 0 ? items.map(mapTemplate) : []);
      setUsingMockData(false);
    } catch (err) {
      if (err instanceof AuthError) throw err;
      setError(err instanceof Error ? err : new Error(String(err)));
      setUsingMockData(true);
    } finally {
      setLoading(false);
    }
  }, []);

  return { templates, loading, error, usingMockData, refetch: fetch };
}

function mapTemplate(item: TemplateListItem): Template {
  return {
    id: item.id,
    name: item.name,
    type: item.type,
    parameterCount: item.parameter_count,
    description: item.description,
    parameterGroups: item.parameter_groups,
    is_custom: item.is_custom,
    // Story 24.1 / AC-1: Include runtime availability metadata in mapping
    runtime_availability: item.runtime_availability,
    availability_reason: item.availability_reason,
    // Story 25.1 / Task 2.4: Pass category_id through mapping
    category_id: item.category_id,
  };
}

// ============================================================================
// Template details (parameters)
// ============================================================================

export function useTemplateDetails(templateId: string) {
  const [parameters, setParameters] = useState<Parameter[]>(mockParameters);
  const [defaultValues, setDefaultValues] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    if (!templateId) return;
    setLoading(true);
    setError(null);
    try {
      const detail = await getTemplate(templateId);
      const mapped = mapTemplateParameters(detail);
      if (mapped.length > 0) {
        setParameters(mapped);
        setDefaultValues(
          Object.fromEntries(mapped.map((p) => [p.id, p.value])),
        );
      }
    } catch (err) {
      if (err instanceof AuthError) throw err;
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [templateId]);

  return { parameters, defaultValues, loading, error, refetch: fetch };
}

function mapTemplateParameters(detail: TemplateDetailResponse): Parameter[] {
  const params: Parameter[] = [];
  const defaults = detail.default_policy;

  for (const [key, value] of Object.entries(defaults)) {
    if (typeof value !== "number") continue;

    // Infer parameter metadata from key name
    const label = key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
    const unit = inferUnit(key);
    const group = inferGroup(key, detail.parameter_groups);

    params.push({
      id: key,
      label,
      value,
      baseline: value,
      unit,
      group,
      type: value > 100 || key.includes("threshold") || key.includes("ceiling") ? "number" : "slider",
      min: 0,
      max: value > 100 ? value * 3 : value > 1 ? value * 5 : 1,
    });
  }

  return params;
}

function inferUnit(key: string): string {
  if (key.includes("rate") && !key.includes("growth")) return "%";
  if (key.includes("growth")) return "EUR/yr";
  if (key.includes("threshold") || key.includes("ceiling") || key.includes("dividend")) return "EUR";
  if (key.includes("year") || key.includes("period")) return "years";
  return "";
}

function inferGroup(key: string, groups: string[]): string {
  if (key.includes("rate") || key.includes("tax")) return groups.find((g) => g.toLowerCase().includes("rate")) ?? "Tax Rates";
  if (key.includes("threshold") || key.includes("year") || key.includes("period") || key.includes("phase")) return groups.find((g) => g.toLowerCase().includes("threshold")) ?? "Thresholds";
  if (key.includes("dividend") || key.includes("rebate") || key.includes("subsidy") || key.includes("means") || key.includes("ceiling")) return groups.find((g) => g.toLowerCase().includes("redistribution")) ?? "Redistribution";
  return groups[0] ?? "General";
}

// ============================================================================
// Scenario list
// ============================================================================

export function useScenarioList() {
  const [scenarioNames, setScenarioNames] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const names = await apiListScenarios();
      setScenarioNames(names);
    } catch (err) {
      if (err instanceof AuthError) throw err;
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, []);

  return { scenarioNames, loading, error, refetch: fetch };
}

// ============================================================================
// Run simulation
// ============================================================================

export function useRunSimulation() {
  const [result, setResult] = useState<RunResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const run = useCallback(async (request: RunRequest) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await apiRunScenario(request);
      setResult(response);
      return response;
    } catch (err) {
      if (err instanceof AuthError) throw err;
      const error = err instanceof Error ? err : new Error(String(err));
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  return { result, loading, error, run };
}

// ============================================================================
// Indicators
// ============================================================================

export function useIndicators() {
  const [data, setData] = useState<IndicatorResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async (runId: string, type: "distributional" | "geographic" | "welfare" | "fiscal" = "distributional") => {
    setLoading(true);
    setError(null);
    try {
      const response = await getIndicators(type, { run_id: runId });
      setData(response);
      return response;
    } catch (err) {
      if (err instanceof AuthError) throw err;
      setError(err instanceof Error ? err : new Error(String(err)));
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, fetch };
}

// ============================================================================
// Data sources (data fusion)
// ============================================================================

export function useDataSources() {
  const [sources, setSources] = useState<Record<string, MockDataSource[]>>(mockDataSources);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [usingMockData, setUsingMockData] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listDataSources();
      if (Object.keys(data).length > 0) {
        setSources(data as unknown as Record<string, MockDataSource[]>);
        setUsingMockData(false);
      }
    } catch (err) {
      if (err instanceof AuthError) throw err;
      setError(err instanceof Error ? err : new Error(String(err)));
      setUsingMockData(true);
    } finally {
      setLoading(false);
    }
  }, []);

  return { sources, loading, error, usingMockData, refetch: fetch };
}

// ============================================================================
// Merge methods (data fusion)
// ============================================================================

export function useMergeMethods() {
  const [methods, setMethods] = useState<MockMergeMethod[]>(mockMergeMethods);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [usingMockData, setUsingMockData] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listMergeMethods();
      if (data.length > 0) {
        setMethods(data as unknown as MockMergeMethod[]);
        setUsingMockData(false);
      }
    } catch (err) {
      if (err instanceof AuthError) throw err;
      setError(err instanceof Error ? err : new Error(String(err)));
      setUsingMockData(true);
    } finally {
      setLoading(false);
    }
  }, []);

  return { methods, loading, error, usingMockData, refetch: fetch };
}

// ============================================================================
// Portfolios (Story 17.2)
// ============================================================================

export function usePortfolios() {
  const [portfolios, setPortfolios] = useState<PortfolioListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [usingMockData, setUsingMockData] = useState(false);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiListPortfolios();
      setPortfolios(data);
      setUsingMockData(false);
    } catch (err) {
      if (err instanceof AuthError) throw err;
      setError(err instanceof Error ? err : new Error(String(err)));
      // Fall back to mock portfolios as PortfolioListItem shape
      setPortfolios(
        mockPortfolios.map((p: MockPortfolio) => ({
          name: p.name,
          description: p.description,
          version_id: p.version,
          policy_count: p.policy_count,
        })),
      );
      setUsingMockData(true);
    } finally {
      setLoading(false);
    }
  }, []);

  return { portfolios, loading, error, usingMockData, refetch: fetch };
}

// ============================================================================
// Results — Story 17.3
// ============================================================================

export function useResults() {
  const [results, setResults] = useState<ResultListItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiListResults();
      setResults(data);
    } catch (err) {
      if (err instanceof AuthError) throw err;
      setError(err instanceof Error ? err : new Error(String(err)));
      // Fall back to empty list rather than showing mock data
    } finally {
      setLoading(false);
    }
  }, []);

  const remove = useCallback(async (runId: string) => {
    await apiDeleteResult(runId);
    setResults((current) => current.filter((r) => r.run_id !== runId));
  }, []);

  return { results, loading, error, refetch: fetch, remove };
}

// ============================================================================
// Population explorer hooks — Story 20.4
// ============================================================================

export function usePopulationPreview(id: string | null) {
  // Initialize with mock data so components always have data to render.
  // Auto-fetches from API on mount/id change; keeps mock data on API failure.
  const [data, setData] = useState<PopulationPreviewResponse>(() =>
    id ? { ...mockPopulationPreview, id, name: id } : mockPopulationPreview
  );
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    (async () => {
      try {
        const result = await getPopulationPreview(id);
        if (result) setData(result);
      } catch (err) {
        if (err instanceof AuthError) throw err;
        // Keep mock data on API failure — Story 20.7 wires the real endpoint
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  return { data, loading };
}

export function usePopulationProfile(id: string | null) {
  // Initialize with mock data; auto-fetches on id change; keeps mock on failure.
  const [data, setData] = useState<PopulationProfileResponse>(mockPopulationProfile);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    (async () => {
      try {
        const result = await getPopulationProfile(id);
        if (result) setData(result);
      } catch (err) {
        if (err instanceof AuthError) throw err;
        // Keep mock data on API failure — Story 20.7 wires the real endpoint
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  return { data, loading };
}

export function usePopulationCrosstab(id: string | null, colA: string | null, colB: string | null) {
  const [data, setData] = useState<PopulationCrosstabResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    if (!id || !colA || !colB) return;
    setLoading(true);
    setError(null);
    try {
      const result = await getPopulationCrosstab(id, colA, colB);
      setData(result);
    } catch (err) {
      if (err instanceof AuthError) throw err;
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setLoading(false);
    }
  }, [id, colA, colB]);

  return { data, loading, error, refetch: fetch };
}

// ============================================================================
// Data source explorer hooks
// ============================================================================

export function useDataSourcePreview(provider: string | null, datasetId: string | null) {
  const [data, setData] = useState<PopulationPreviewResponse>(() =>
    mockPopulationPreview
  );
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!provider || !datasetId) return;
    setLoading(true);
    (async () => {
      try {
        const result = await getDataSourcePreview(provider, datasetId);
        if (result) setData(result);
      } catch (err) {
        if (err instanceof AuthError) throw err;
      } finally {
        setLoading(false);
      }
    })();
  }, [provider, datasetId]);

  return { data, loading };
}

export function useDataSourceProfile(provider: string | null, datasetId: string | null) {
  const [data, setData] = useState<PopulationProfileResponse>(mockPopulationProfile);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!provider || !datasetId) return;
    setLoading(true);
    (async () => {
      try {
        const result = await getDataSourceProfile(provider, datasetId);
        if (result) setData(result);
      } catch (err) {
        if (err instanceof AuthError) throw err;
      } finally {
        setLoading(false);
      }
    })();
  }, [provider, datasetId]);

  return { data, loading };
}

export function useValidatePortfolio() {
  const [result, setResult] = useState<ValidatePortfolioResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const validate = useCallback(async (request: ValidatePortfolioRequest) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiValidatePortfolio(request);
      setResult(response);
      return response;
    } catch (err) {
      if (err instanceof AuthError) throw err;
      const e = err instanceof Error ? err : new Error(String(err));
      setError(e);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { result, loading, error, validate };
}
