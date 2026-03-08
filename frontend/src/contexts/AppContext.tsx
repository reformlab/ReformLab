/** Shared application state context for ReformLab.
 *
 * Provides API data (populations, templates, scenarios) and auth state
 * to all components via React Context.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { toast } from "sonner";

import { AuthError } from "@/api/client";
import { login } from "@/api/auth";
import { getAuthToken, setAuthToken } from "@/api/client";
import { createScenario as apiCreateScenario, cloneScenario as apiCloneScenario } from "@/api/scenarios";
import {
  usePopulations,
  useTemplates,
  useTemplateDetails,
  useRunSimulation,
  useIndicators,
  useDataSources,
  useMergeMethods,
  usePortfolios,
  useResults,
} from "@/hooks/useApi";
import type { DecileData, Parameter, Population, Scenario, Template, MockDataSource, MockMergeMethod } from "@/data/mock-data";
import { mockDecileData, mockParameters, mockScenarios } from "@/data/mock-data";
import type { RunResponse, IndicatorResponse, GenerationResult, PortfolioListItem, ResultListItem } from "@/api/types";

// ============================================================================
// Context types
// ============================================================================

interface AppState {
  // Auth
  isAuthenticated: boolean;
  authLoading: boolean;
  authenticate: (password: string) => Promise<boolean>;
  logout: () => void;

  // Data
  populations: Population[];
  templates: Template[];
  parameters: Parameter[];
  parameterValues: Record<string, number>;
  setParameterValue: (id: string, value: number) => void;
  scenarios: Scenario[];
  decileData: DecileData[];

  // Selections
  selectedPopulationId: string;
  setSelectedPopulationId: (id: string) => void;
  selectedTemplateId: string;
  selectTemplate: (id: string) => void;
  selectedScenarioId: string;
  setSelectedScenarioId: (id: string) => void;

  // Actions
  startRun: () => Promise<void>;
  runLoading: boolean;
  runResult: RunResponse | null;
  cloneScenario: (id: string) => void;
  deleteScenario: (id: string) => void;

  // Loading states
  populationsLoading: boolean;
  templatesLoading: boolean;
  parametersLoading: boolean;

  // Refetch
  refetchPopulations: () => Promise<void>;
  refetchTemplates: () => Promise<void>;

  // Data fusion (Story 17.1)
  dataFusionSources: Record<string, MockDataSource[]>;
  dataFusionMethods: MockMergeMethod[];
  dataFusionResult: GenerationResult | null;
  setDataFusionResult: (result: GenerationResult | null) => void;
  dataFusionSourcesLoading: boolean;

  // Portfolios (Story 17.2)
  portfolios: PortfolioListItem[];
  portfoliosLoading: boolean;
  refetchPortfolios: () => Promise<void>;

  // Results (Story 17.3)
  results: ResultListItem[];
  resultsLoading: boolean;
  refetchResults: () => Promise<void>;
  selectedPortfolioName: string | null;
  setSelectedPortfolioName: (name: string | null) => void;

  // Comparison (Story 17.4)
  selectedComparisonRunIds: string[];
  setSelectedComparisonRunIds: (ids: string[]) => void;
}

const AppContext = createContext<AppState | null>(null);

export function useAppState(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppState must be used within AppProvider");
  return ctx;
}

// ============================================================================
// Provider
// ============================================================================

export function AppProvider({ children }: { children: ReactNode }) {
  // Auth state
  const [isAuthenticated, setIsAuthenticated] = useState(() => !!getAuthToken());
  const [authLoading, setAuthLoading] = useState(false);

  const authenticate = useCallback(async (password: string) => {
    setAuthLoading(true);
    try {
      const response = await login(password);
      setAuthToken(response.token);
      setIsAuthenticated(true);
      return true;
    } catch {
      return false;
    } finally {
      setAuthLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    setAuthToken(null);
    setIsAuthenticated(false);
  }, []);

  // Data hooks
  const { populations, loading: populationsLoading, usingMockData: populationsMock, refetch: refetchPopulations } = usePopulations();
  const { templates, loading: templatesLoading, usingMockData: templatesMock, refetch: refetchTemplates } = useTemplates();

  // Data fusion hooks (Story 17.1)
  const { sources: dataFusionSources, loading: dataFusionSourcesLoading, refetch: refetchDataFusionSources } = useDataSources();
  const { methods: dataFusionMethods, refetch: refetchDataFusionMethods } = useMergeMethods();
  const [dataFusionResult, setDataFusionResult] = useState<GenerationResult | null>(null);

  // Portfolio hooks (Story 17.2)
  const { portfolios, loading: portfoliosLoading, refetch: refetchPortfolios } = usePortfolios();

  // Results hooks (Story 17.3)
  const { results, loading: resultsLoading, refetch: refetchResults } = useResults();
  const [selectedPortfolioName, setSelectedPortfolioName] = useState<string | null>(null);

  // Comparison state (Story 17.4)
  const [selectedComparisonRunIds, setSelectedComparisonRunIds] = useState<string[]>([]);

  // Selections
  const [selectedPopulationId, setSelectedPopulationId] = useState("");
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [selectedScenarioId, setSelectedScenarioId] = useState("reform-a");
  const [scenarios, setScenarios] = useState<Scenario[]>(() => [...mockScenarios]);

  // Template details
  const { parameters: templateParams, defaultValues, loading: parametersLoading, refetch: refetchParams } = useTemplateDetails(selectedTemplateId);
  const [parameterValues, setParameterValues] = useState<Record<string, number>>(() =>
    Object.fromEntries(mockParameters.map((p) => [p.id, p.value])),
  );

  // Set initial selection when populations/templates load
  useEffect(() => {
    if (populations.length > 0 && !selectedPopulationId) {
      setSelectedPopulationId(populations[0].id);
    }
  }, [populations, selectedPopulationId]);

  useEffect(() => {
    if (templates.length > 0 && !selectedTemplateId) {
      setSelectedTemplateId(templates[0].id);
    }
  }, [templates, selectedTemplateId]);

  // Fetch template details when template selection changes
  useEffect(() => {
    if (selectedTemplateId && isAuthenticated) {
      refetchParams().catch(() => {});
    }
  }, [selectedTemplateId, isAuthenticated, refetchParams]);

  // Update parameter values when template defaults change
  useEffect(() => {
    if (Object.keys(defaultValues).length > 0) {
      setParameterValues(defaultValues);
    }
  }, [defaultValues]);

  // Fetch data on auth
  useEffect(() => {
    if (isAuthenticated) {
      refetchResults().catch(() => {});
      refetchPopulations().catch((err) => {
        if (err instanceof AuthError) {
          setIsAuthenticated(false);
          setAuthToken(null);
        }
      });
      refetchTemplates().catch((err) => {
        if (err instanceof AuthError) {
          setIsAuthenticated(false);
          setAuthToken(null);
        }
      });
      refetchDataFusionSources().catch(() => {});
      refetchDataFusionMethods().catch(() => {});
      refetchPortfolios().catch(() => {});
      refetchResults().catch(() => {});
    }
  }, [isAuthenticated, refetchPopulations, refetchTemplates, refetchDataFusionSources, refetchDataFusionMethods, refetchPortfolios, refetchResults]);

  // Warn user if data is still mock after loading completes
  useEffect(() => {
    if (isAuthenticated && !populationsLoading && !templatesLoading) {
      if (populationsMock || templatesMock) {
        toast.warning("Using sample data — backend API may be unavailable", {
          id: "mock-data-warning",
          duration: 8000,
        });
      }
    }
  }, [isAuthenticated, populationsLoading, templatesLoading, populationsMock, templatesMock]);

  const selectTemplate = useCallback((id: string) => {
    setSelectedTemplateId(id);
  }, []);

  const setParameterValue = useCallback((id: string, value: number) => {
    setParameterValues((current) => ({ ...current, [id]: value }));
  }, []);

  // Run simulation
  const { result: runResult, loading: runLoading, run: executeRun } = useRunSimulation();
  const { fetch: fetchIndicators } = useIndicators();

  // Decile data from indicators
  const [decileData, setDecileData] = useState<DecileData[]>(mockDecileData);

  // When run result comes in, fetch distributional indicators
  useEffect(() => {
    if (runResult?.run_id) {
      fetchIndicators(runResult.run_id, "distributional").then((response) => {
        if (response) {
          const mapped = mapIndicatorToDecileData(response);
          if (mapped.length > 0) {
            setDecileData(mapped);
          }
        }
      }).catch(() => {});
    }
  }, [runResult, fetchIndicators]);

  const formatTimestamp = (): string => {
    const now = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}`;
  };

  const startRun = useCallback(async () => {
    const template = templates.find((t) => t.id === selectedTemplateId);
    const templateName = template?.name ?? selectedTemplateId;

    // Count changed parameters
    const changedCount = templateParams.filter((p) => {
      const currentVal = parameterValues[p.id] ?? p.value;
      return Math.abs(currentVal - p.baseline) > 1e-6;
    }).length;

    // Create or update scenario
    const currentScenario = scenarios.find((s) => s.id === selectedScenarioId);
    const needsNewScenario = !currentScenario || currentScenario.isBaseline || currentScenario.templateId !== selectedTemplateId;

    let activeScenarioId = selectedScenarioId;

    if (needsNewScenario) {
      const existingCount = scenarios.filter((s) => !s.isBaseline).length;
      const newId = `reform-${String.fromCharCode(97 + existingCount)}`;
      const newScenario: Scenario = {
        id: newId,
        name: templateName,
        status: "running",
        isBaseline: false,
        parameterChanges: changedCount,
        linkedBaseline: "baseline",
        lastRun: formatTimestamp(),
        templateId: selectedTemplateId,
        templateName,
      };
      setScenarios((current) => [...current, newScenario]);
      setSelectedScenarioId(newId);
      activeScenarioId = newId;

      // Register scenario with backend API
      try {
        const template = templates.find((t) => t.id === selectedTemplateId);
        await apiCreateScenario({
          name: newId,
          policy_type: template?.type ?? "carbon_tax",
          parameters: parameterValues,
          start_year: 2025,
          end_year: 2030,
          description: templateName,
          baseline_ref: null,
        });
      } catch {
        // Non-fatal: scenario still runs even if registration fails
        // Non-fatal: run will still proceed
      }
    } else {
      setScenarios((current) =>
        current.map((s) =>
          s.id === selectedScenarioId
            ? { ...s, status: "running" as const, parameterChanges: changedCount, lastRun: formatTimestamp() }
            : s,
        ),
      );
    }

    try {
      await executeRun({
        template_name: selectedTemplateId,
        parameters: parameterValues,
        start_year: 2025,
        end_year: 2030,
        population_id: selectedPopulationId || null,
      });

      // Mark completed
      setScenarios((current) =>
        current.map((s) =>
          s.id === activeScenarioId
            ? { ...s, status: "completed" as const }
            : s,
        ),
      );
    } catch {
      // Mark failed
      setScenarios((current) =>
        current.map((s) =>
          s.id === activeScenarioId
            ? { ...s, status: "failed" as const }
            : s,
        ),
      );
    }
  }, [templates, selectedTemplateId, templateParams, parameterValues, scenarios, selectedScenarioId, selectedPopulationId, executeRun]);

  const cloneScenario = useCallback((id: string) => {
    const source = scenarios.find((s) => s.id === id);
    if (!source) return;
    const existingCount = scenarios.filter((s) => !s.isBaseline).length;
    const newId = `reform-${String.fromCharCode(97 + existingCount)}`;
    const cloneName = `${source.name} (copy)`;
    const cloned: Scenario = {
      ...source,
      id: newId,
      name: cloneName,
      status: "draft",
      isBaseline: false,
      linkedBaseline: source.isBaseline ? source.id : source.linkedBaseline,
      lastRun: undefined,
    };
    setScenarios((current) => [...current, cloned]);
    setSelectedScenarioId(newId);

    // Clone on backend (fire-and-forget for MVP)
    apiCloneScenario(id, cloneName).catch(() => {
      // Non-fatal: local clone still works
    });
  }, [scenarios]);

  const deleteScenario = useCallback((id: string) => {
    setScenarios((current) => current.filter((s) => s.id !== id));
    if (selectedScenarioId === id) {
      setSelectedScenarioId("baseline");
    }
  }, [selectedScenarioId]);

  const value = useMemo<AppState>(
    () => ({
      isAuthenticated,
      authLoading,
      authenticate,
      logout,
      populations,
      templates,
      parameters: templateParams,
      parameterValues,
      setParameterValue,
      scenarios,
      decileData,
      selectedPopulationId,
      setSelectedPopulationId,
      selectedTemplateId,
      selectTemplate,
      selectedScenarioId,
      setSelectedScenarioId,
      startRun,
      runLoading,
      runResult,
      cloneScenario,
      deleteScenario,
      populationsLoading,
      templatesLoading,
      parametersLoading,
      refetchPopulations,
      refetchTemplates,
      dataFusionSources,
      dataFusionMethods,
      dataFusionResult,
      setDataFusionResult,
      dataFusionSourcesLoading,
      portfolios,
      portfoliosLoading,
      refetchPortfolios,
      results,
      resultsLoading,
      refetchResults,
      selectedPortfolioName,
      setSelectedPortfolioName,
      selectedComparisonRunIds,
      setSelectedComparisonRunIds,
    }),
    [
      isAuthenticated, authLoading, authenticate, logout,
      populations, templates, templateParams, parameterValues, setParameterValue,
      scenarios, decileData,
      selectedPopulationId, selectedTemplateId, selectTemplate,
      selectedScenarioId,
      startRun, runLoading, runResult,
      cloneScenario, deleteScenario,
      populationsLoading, templatesLoading, parametersLoading,
      refetchPopulations, refetchTemplates,
      dataFusionSources, dataFusionMethods, dataFusionResult, setDataFusionResult, dataFusionSourcesLoading,
      portfolios, portfoliosLoading, refetchPortfolios,
      results, resultsLoading, refetchResults,
      selectedPortfolioName, setSelectedPortfolioName,
      selectedComparisonRunIds, setSelectedComparisonRunIds,
    ],
  );

  return <AppContext value={value}>{children}</AppContext>;
}

// ============================================================================
// Helpers
// ============================================================================

function mapIndicatorToDecileData(response: IndicatorResponse): DecileData[] {
  const data = response.data;
  const deciles = data["decile"] as string[] | undefined;
  const baseline = data["baseline"] as number[] | undefined;
  const reform = data["reform"] as number[] | undefined;
  const delta = data["delta"] as number[] | undefined;

  if (!deciles || !baseline || !reform) return [];

  return deciles.map((d, i) => ({
    decile: String(d),
    baseline: baseline[i] ?? 0,
    reform: reform[i] ?? 0,
    delta: delta?.[i] ?? (reform[i] ?? 0) - (baseline[i] ?? 0),
  }));
}
