/** Data fetching hooks for the ReformLab API. */

import { useCallback, useState } from "react";

import { listPopulations } from "@/api/populations";
import { listTemplates, getTemplate } from "@/api/templates";
import { listScenarios as apiListScenarios } from "@/api/scenarios";
import { runScenario as apiRunScenario } from "@/api/runs";
import { getIndicators } from "@/api/indicators";
import { listDataSources, listMergeMethods } from "@/api/data-fusion";
import { AuthError } from "@/api/client";
import type {
  PopulationItem,
  RunRequest,
  RunResponse,
  TemplateListItem,
  TemplateDetailResponse,
  IndicatorResponse,
} from "@/api/types";
import type { Population, Template, Parameter, MockDataSource, MockMergeMethod } from "@/data/mock-data";
import {
  mockPopulations,
  mockTemplates,
  mockParameters,
  mockDataSources,
  mockMergeMethods,
} from "@/data/mock-data";

// ============================================================================
// Populations
// ============================================================================

export function usePopulations() {
  const [populations, setPopulations] = useState<Population[]>(mockPopulations);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [usingMockData, setUsingMockData] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await listPopulations();
      if (items.length > 0) {
        setPopulations(items.map(mapPopulation));
        setUsingMockData(false);
      }
      // If empty, keep mock data as fallback
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

function mapPopulation(item: PopulationItem): Population {
  return {
    id: item.id,
    name: item.name,
    households: item.households,
    source: item.source,
    year: item.year,
  };
}

// ============================================================================
// Templates
// ============================================================================

export function useTemplates() {
  const [templates, setTemplates] = useState<Template[]>(mockTemplates);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [usingMockData, setUsingMockData] = useState(true);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await listTemplates();
      if (items.length > 0) {
        setTemplates(items.map(mapTemplate));
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
  const defaults = detail.default_parameters;

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
