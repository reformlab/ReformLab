// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Shared application state context for ReformLab.
 *
 * Provides API data (populations, templates, scenarios) and auth state
 * to all components via React Context.
 *
 * Story 20.1: Adds hash-based stage routing (activeStage, activeSubView, navigateTo)
 * and canonical scenario state (activeScenario, setActiveScenario, updateScenarioField).
 * Story 20.2: Adds first-launch demo scenario, returning-user restore, scenario
 * persistence (localStorage), and scenario entry flow actions.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { toast } from "sonner";

import { setOnAuthInvalid } from "@/api/client";
import { login, logout as apiLogout } from "@/api/auth";
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
import type { DecileData, Parameter, Scenario, Template, MockDataSource, MockMergeMethod } from "@/data/mock-data";
import { mockDecileData, mockParameters, mockScenarios } from "@/data/mock-data";
import type { RunResponse, IndicatorResponse, GenerationResult, PortfolioListItem, ResultListItem, PopulationLibraryItem } from "@/api/types";
import type { StageKey, SubView, WorkspaceScenario } from "@/types/workspace";
import { isValidStage, isValidSubView } from "@/types/workspace";
import {
  isFirstLaunch,
  markLaunched,
  saveScenario as persistScenario,
  loadScenario,
  saveStage as persistStage,
  loadStage,
  getSavedScenarios,
  saveScenarioToList,
  getManuallyEditedNames,
  saveManuallyEditedNames,
} from "@/hooks/useScenarioPersistence";
import { createDemoScenario, DEMO_SCENARIO_ID, DEMO_TEMPLATE_ID, DEMO_POPULATION_ID } from "@/data/demo-scenario";
import {
  generateScenarioSuggestion,
  generateScenarioCloneName,
} from "@/utils/naming";

// ============================================================================
// Context types
// ============================================================================

interface AppState {
  // Auth
  isAuthenticated: boolean;
  authLoading: boolean;
  authenticate: (password: string) => Promise<string | null>;
  logout: () => void;

  // Stage routing (Story 20.1 — AC-2)
  activeStage: StageKey;
  activeSubView: SubView | null;
  navigateTo: (stage: StageKey, subView?: SubView | null) => void;

  // Canonical scenario state (Story 20.1 — AC-3)
  activeScenario: WorkspaceScenario | null;
  setActiveScenario: (scenario: WorkspaceScenario | null) => void;
  updateScenarioField: <K extends keyof WorkspaceScenario>(field: K, value: WorkspaceScenario[K]) => void;

  // Scenario entry flow actions (Story 20.2 — AC-3, AC-5)
  savedScenarios: WorkspaceScenario[];
  saveCurrentScenario: () => void;
  loadSavedScenario: (id: string) => void;
  resetToDemo: () => void;
  createNewScenario: (templateId?: string) => void;
  cloneCurrentScenario: () => void;

  // Data
  populations: PopulationLibraryItem[];
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

  // Manifest viewer (Story 26.4)
  selectedResultForManifest: string | null;
  setSelectedResultForManifest: (runId: string | null) => void;

  // Execution matrix (Story 20.6, AC-1, AC-3)
  executionMatrix: Record<string, Record<string, import("@/api/types").ExecutionMatrixCell>>;
  updateExecutionCell: (
    scenarioId: string,
    populationId: string,
    update: Partial<import("@/api/types").ExecutionMatrixCell>,
  ) => void;

  // API connection status
  apiConnected: boolean;
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

  // Global 401 handler — any apiFetch 401 forces back to password prompt
  useEffect(() => {
    setOnAuthInvalid(() => {
      setIsAuthenticated(false);
      initializedRef.current = false;
    });
    return () => { setOnAuthInvalid(null); };
  }, []);

  const authenticate = useCallback(async (password: string): Promise<string | null> => {
    setAuthLoading(true);
    try {
      const response = await login(password);
      setAuthToken(response.token);
      setIsAuthenticated(true);
      return null;
    } catch (err) {
      return err instanceof Error ? err.message : "Login failed";
    } finally {
      setAuthLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    apiLogout();  // revoke token server-side (best-effort)
    setAuthToken(null);
    setIsAuthenticated(false);
    initializedRef.current = false;
  }, []);

  // ============================================================================
  // Stage routing — hash-based (Story 20.1, AC-2)
  // ============================================================================

  const [activeStage, setActiveStage] = useState<StageKey>("policies");
  const [activeSubView, setActiveSubView] = useState<SubView | null>(null);

  useEffect(() => {
    function onHashChange() {
      const hash = window.location.hash.slice(1); // remove leading #
      const [stage, sub] = hash.split("/");

      // Story 26.1: Migrate legacy #engine hash to #scenario
      const migratedStage = stage === "engine" ? "scenario" : stage;
      const validSubView = sub && isValidSubView(sub) ? sub : null;

      if (migratedStage && isValidStage(migratedStage)) {
        setActiveStage(migratedStage);
        setActiveSubView(validSubView);
        // Update hash if migration occurred
        if (stage === "engine") {
          window.location.hash = validSubView ? `scenario/${validSubView}` : "scenario";
        }
      } else {
        // Empty hash or unknown stage → default to policies
        setActiveStage("policies");
        setActiveSubView(null);
      }
    }
    window.addEventListener("hashchange", onHashChange);
    onHashChange(); // read initial hash on mount
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const navigateTo = useCallback((stage: StageKey, subView?: SubView | null) => {
    const hash = subView ? `${stage}/${subView}` : stage;
    window.location.hash = hash;
    // hashchange event fires automatically, updating state via the listener above
  }, []);

  // ============================================================================
  // Canonical scenario state — (Story 20.1, AC-3)
  // ============================================================================

  const [activeScenario, setActiveScenario] = useState<WorkspaceScenario | null>(null);

  const updateScenarioField = useCallback(<K extends keyof WorkspaceScenario>(
    field: K,
    value: WorkspaceScenario[K],
  ) => {
    setActiveScenario((current) => {
      if (!current) return null;

      // Story 22.3: Track manual edits to the name field
      if (field === "name" && current.id) {
        // Don't mark demo scenario as manually edited (should always get auto-updates)
        if (current.id !== DEMO_SCENARIO_ID) {
          setManuallyEditedScenarioNames((prev) => {
            const updated = new Set(prev);
            updated.add(current.id);
            // Persist to localStorage
            saveManuallyEditedNames(updated);
            return updated;
          });
        }
      }

      return { ...current, [field]: value };
    });
  }, []);

  // ============================================================================
  // Scenario persistence — (Story 20.2, AC-2, AC-5)
  // ============================================================================

  // Gate that ensures the initialization effect fires exactly once per auth session
  // and prevents persistence effects from overwriting restored state before init completes.
  const initializedRef = useRef(false);

  // Saved scenarios React state (lazy-initialized from localStorage)
  const [savedScenarios, setSavedScenarios] = useState<WorkspaceScenario[]>(() => getSavedScenarios());

  // Story 22.3: Track scenario IDs with manually edited names (lazy-initialized from localStorage)
  const [manuallyEditedScenarioNames, setManuallyEditedScenarioNames] = useState<Set<string>>(
    () => getManuallyEditedNames(),
  );

  // Loaded scenarios keep their stored name while the restored context is unchanged.
  const loadedScenarioNameContextRef = useRef<{
    scenarioId: string;
    portfolioName: string | null;
    populationId: string;
  } | null>(null);

  // Policy set selection is used by scenario auto-naming.
  const [selectedPortfolioName, setSelectedPortfolioName] = useState<string | null>(null);

  const refreshSavedScenarios = useCallback(
    () => setSavedScenarios(getSavedScenarios()),
    [],
  );

  // Initialization effect — first-launch vs returning-user
  // Runs after hash routing is set up (above) but before mock-data warning (below).
  useEffect(() => {
    if (!isAuthenticated) return;
    if (initializedRef.current) return;
    initializedRef.current = true;

    if (isFirstLaunch()) {
      // First launch: load demo scenario
      const demo = createDemoScenario();
      loadedScenarioNameContextRef.current = null;
      setActiveScenario(demo);
      setSelectedTemplateId(DEMO_TEMPLATE_ID);
      setSelectedPopulationId(DEMO_POPULATION_ID);
      markLaunched();
      navigateTo("results", "runner");
    } else {
      // Returning user: restore saved scenario
      const saved = loadScenario();
      if (saved) {
        const primaryPopulationId = saved.populationIds[0] ?? "";
        loadedScenarioNameContextRef.current = {
          scenarioId: saved.id,
          portfolioName: saved.portfolioName,
          populationId: primaryPopulationId,
        };
        setActiveScenario(saved);
        setSelectedPortfolioName(saved.portfolioName);
        // Sync legacy selectors so startRun() uses the restored scenario's values
        if (saved.policyType) setSelectedTemplateId(saved.policyType);
        if (primaryPopulationId) setSelectedPopulationId(primaryPopulationId);
      } else {
        // localStorage externally cleared — fall back to demo (do NOT call markLaunched)
        const demo = createDemoScenario();
        loadedScenarioNameContextRef.current = null;
        setActiveScenario(demo);
        setSelectedTemplateId(DEMO_TEMPLATE_ID);
        setSelectedPopulationId(DEMO_POPULATION_ID);
      }
      const savedStage = loadStage();
      if (savedStage) navigateTo(savedStage);
      else navigateTo("results", "runner");
    }
  }, [isAuthenticated, navigateTo]);

  // Persist activeScenario to localStorage whenever it changes (after init)
  useEffect(() => {
    if (!isAuthenticated || !initializedRef.current) return;
    persistScenario(activeScenario);
  }, [activeScenario, isAuthenticated]);

  // Persist activeStage to localStorage whenever it changes (after init)
  useEffect(() => {
    if (!isAuthenticated || !initializedRef.current) return;
    persistStage(activeStage);
  }, [activeStage, isAuthenticated]);

  // ============================================================================
  // API health check — pings /api/health to determine real connectivity
  // ============================================================================

  const [apiConnected, setApiConnected] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      setApiConnected(false);
      return;
    }

    let cancelled = false;

    const check = async () => {
      try {
        const res = await fetch("/api/health", { method: "GET" });
        if (!cancelled) setApiConnected(res.ok);
      } catch {
        if (!cancelled) setApiConnected(false);
      }
    };

    // Check immediately on auth, then every 30s
    check();
    const id = setInterval(check, 30_000);
    return () => { cancelled = true; clearInterval(id); };
  }, [isAuthenticated]);

  // ============================================================================
  // Data hooks
  // ============================================================================

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

  // Comparison state (Story 17.4)
  const [selectedComparisonRunIds, setSelectedComparisonRunIds] = useState<string[]>([]);

  // Manifest viewer state (Story 26.4)
  const [selectedResultForManifest, setSelectedResultForManifest] = useState<string | null>(null);

  // Execution matrix state (Story 20.6, AC-1, AC-3)
  const [executionMatrix, setExecutionMatrix] = useState<
    Record<string, Record<string, import("@/api/types").ExecutionMatrixCell>>
  >({});

  const updateExecutionCell = useCallback((
    scenarioId: string,
    populationId: string,
    update: Partial<import("@/api/types").ExecutionMatrixCell>,
  ) => {
    setExecutionMatrix((prev) => ({
      ...prev,
      [scenarioId]: {
        ...(prev[scenarioId] || {}),
        [populationId]: {
          ...(prev[scenarioId]?.[populationId] || {
            scenarioId,
            populationId,
            status: "NOT_EXECUTED" as const,
          }),
          ...update,
        },
      },
    }));
  }, []);

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
    if (populations.length > 0) {
      setSelectedPopulationId((current) => current || populations[0].id);
    }
  }, [populations]);

  useEffect(() => {
    if (templates.length > 0) {
      setSelectedTemplateId((current) => current || templates[0].id);
    }
  }, [templates]);

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
      refetchPopulations().catch(() => {});
      refetchTemplates().catch(() => {});
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
        toast.warning("Loaded sample data — API returned empty or errored for populations/templates", {
          id: "mock-data-warning",
          duration: 10000,
        });
      }
    }
  }, [isAuthenticated, populationsLoading, templatesLoading, populationsMock, templatesMock]);

  // Story 22.3: Auto-update scenario name when portfolio or population context changes
  // Only applies if the scenario name hasn't been manually edited and it's not the demo scenario
  const activeScenarioId = activeScenario?.id;
  const activeScenarioName = activeScenario?.name;
  const activeScenarioPortfolioName = activeScenario?.portfolioName;
  const activeScenarioPopulationIds = activeScenario?.populationIds;

  useEffect(() => {
    if (!activeScenarioId) return; // Null guard - no active scenario to update

    const demoId = DEMO_SCENARIO_ID;
    const isManuallyEdited = manuallyEditedScenarioNames.has(activeScenarioId);
    const isDemo = activeScenarioId === demoId;

    // Preserve the curated first-launch demo name; auto-naming is for user scenarios.
    if (isDemo) return;

    // Skip auto-update if name was manually edited.
    if (isManuallyEdited) return;

    const loadedNameContext = loadedScenarioNameContextRef.current;
    if (loadedNameContext?.scenarioId === activeScenarioId) {
      const restoredContextUnchanged =
        loadedNameContext.portfolioName === selectedPortfolioName &&
        loadedNameContext.populationId === selectedPopulationId;
      if (restoredContextUnchanged) return;
      loadedScenarioNameContextRef.current = null;
    }

    // Generate suggested name from current context
    const suggestedName = generateScenarioSuggestion(
      selectedPortfolioName,
      selectedPopulationId,
      populations,
      templates,
      [], // Composition not available in AppContext
    );

    // Only update if the suggested name differs from the current name
    if (suggestedName !== activeScenarioName) {
      setActiveScenario((prev) =>
        prev ? { ...prev, name: suggestedName } : null
      );
    }
  }, [
    activeScenarioPortfolioName,
    activeScenarioPopulationIds,
    activeScenarioId,
    activeScenarioName,
    selectedPortfolioName,
    selectedPopulationId,
    populations,
    templates,
    manuallyEditedScenarioNames,
  ]);

  // ============================================================================
  // Scenario entry flow actions — (Story 20.2, AC-3)
  // ============================================================================

  const saveCurrentScenario = useCallback(() => {
    if (!activeScenario) return;
    saveScenarioToList(activeScenario);
    refreshSavedScenarios();
    toast.success("Scenario saved");
  }, [activeScenario, refreshSavedScenarios]);

  const loadSavedScenario = useCallback((id: string) => {
    const list = getSavedScenarios();
    const found = list.find((s) => s.id === id);
    if (found) {
      const primaryPopulationId = found.populationIds[0] ?? "";
      loadedScenarioNameContextRef.current = {
        scenarioId: found.id,
        portfolioName: found.portfolioName,
        populationId: primaryPopulationId,
      };
      setActiveScenario(found);
      setSelectedPortfolioName(found.portfolioName);
      // Sync legacy selectors so startRun() uses the loaded scenario's values
      if (found.policyType) setSelectedTemplateId(found.policyType);
      if (primaryPopulationId) setSelectedPopulationId(primaryPopulationId);
      navigateTo("policies");
    }
  }, [navigateTo]);

  const resetToDemo = useCallback(() => {
    loadedScenarioNameContextRef.current = null;
    setActiveScenario(createDemoScenario());
    setSelectedPortfolioName(null);
    setSelectedTemplateId(DEMO_TEMPLATE_ID);
    setSelectedPopulationId(DEMO_POPULATION_ID);
    navigateTo("results", "runner");
    toast.info("Demo scenario loaded");
  }, [navigateTo]);

  const createNewScenario = useCallback((templateId?: string) => {
    // Story 22.3: Generate scenario name from current context
    const suggestedName = generateScenarioSuggestion(
      selectedPortfolioName,
      selectedPopulationId,
      populations,
      templates,
      [], // Composition not available in AppContext; portfolioName is used instead
    );

    const newScenario: WorkspaceScenario = {
      id: crypto.randomUUID(),
      name: suggestedName,
      version: "1.0",
      status: "draft",
      isBaseline: false,
      baselineRef: null,
      portfolioName: null,
      populationIds: selectedPopulationId ? [selectedPopulationId] : [],
      engineConfig: {
        startYear: 2025,
        endYear: 2030,
        seed: null,
        investmentDecisionsEnabled: false,
        logitModel: null,
        discountRate: 0.03,
        tasteParameters: null,  // Story 22.6
        calibrationState: "not_configured",  // Story 22.6
      },
      policyType: templateId ?? null,
      lastRunId: null,
    };
    loadedScenarioNameContextRef.current = null;
    setActiveScenario(newScenario);
    if (templateId) {
      setSelectedTemplateId(templateId);
    }
    navigateTo("policies");
  }, [navigateTo, selectedPortfolioName, selectedPopulationId, populations, templates]);

  const cloneCurrentScenario = useCallback(() => {
    if (!activeScenario) return;

    // Story 22.3: Use collision handling for clone names
    const existingNames = new Set(savedScenarios.map((s) => s.name));
    const cloneName = generateScenarioCloneName(activeScenario.name, existingNames);

    const cloned: WorkspaceScenario = {
      ...activeScenario,
      id: crypto.randomUUID(),
      name: cloneName,
    };
    loadedScenarioNameContextRef.current = null;
    setActiveScenario(cloned);

    // Story 22.3: Mark cloned name as manually edited (cloned name is "manual" by definition)
    setManuallyEditedScenarioNames((prev) => {
      const updated = new Set(prev);
      updated.add(cloned.id);
      // Persist to localStorage
      saveManuallyEditedNames(updated);
      return updated;
    });

    toast.success("Scenario cloned");
  }, [activeScenario, savedScenarios]);

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
          policy: parameterValues,
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
        policy: parameterValues,
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

    // Story 22.3: Clean up manually edited names set when scenario is deleted
    setManuallyEditedScenarioNames((prev) => {
      const updated = new Set(prev);
      updated.delete(id);
      // Persist to localStorage
      saveManuallyEditedNames(updated);
      return updated;
    });
  }, [selectedScenarioId]);

  const value = useMemo<AppState>(
    () => ({
      isAuthenticated,
      authLoading,
      authenticate,
      logout,
      activeStage,
      activeSubView,
      navigateTo,
      activeScenario,
      setActiveScenario,
      updateScenarioField,
      savedScenarios,
      saveCurrentScenario,
      loadSavedScenario,
      resetToDemo,
      createNewScenario,
      cloneCurrentScenario,
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
      selectedResultForManifest,
      setSelectedResultForManifest,
      executionMatrix,
      updateExecutionCell,
      apiConnected,
    }),
    [
      isAuthenticated, authLoading, authenticate, logout,
      activeStage, activeSubView, navigateTo,
      activeScenario, setActiveScenario, updateScenarioField,
      savedScenarios, saveCurrentScenario, loadSavedScenario, resetToDemo, createNewScenario, cloneCurrentScenario,
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
      selectedResultForManifest, setSelectedResultForManifest,
      executionMatrix, updateExecutionCell,
      apiConnected,
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
