import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { LeftPanel } from "@/components/layout/LeftPanel";
import { MainContent } from "@/components/layout/MainContent";
import { RightPanel } from "@/components/layout/RightPanel";
import { WorkspaceLayout } from "@/components/layout/WorkspaceLayout";
import { PasswordPrompt } from "@/components/auth/PasswordPrompt";
import { AssumptionsReviewScreen } from "@/components/screens/AssumptionsReviewScreen";
import { DataFusionWorkbench } from "@/components/screens/DataFusionWorkbench";
import { ParameterEditingScreen } from "@/components/screens/ParameterEditingScreen";
import { PopulationSelectionScreen } from "@/components/screens/PopulationSelectionScreen";
import { PortfolioDesignerScreen } from "@/components/screens/PortfolioDesignerScreen";
import { TemplateSelectionScreen } from "@/components/screens/TemplateSelectionScreen";
import {
  type ConfigStep,
  ModelConfigStepper,
} from "@/components/simulation/ModelConfigStepper";
import { ComparisonView } from "@/components/simulation/ComparisonView";
import { DistributionalChart } from "@/components/simulation/DistributionalChart";
import { RunProgressBar } from "@/components/simulation/RunProgressBar";
import { ScenarioCard } from "@/components/simulation/ScenarioCard";
import { SummaryStatCard } from "@/components/simulation/SummaryStatCard";
import { Toaster } from "@/components/ui/sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useAppState } from "@/contexts/AppContext";
import { ApiError } from "@/api/client";
import { exportCsv, exportParquet } from "@/api/exports";
import {
  mockSummaryStats,
} from "@/data/mock-data";

const STEP_ORDER: ConfigStep["key"][] = [
  "population",
  "template",
  "parameters",
  "assumptions",
];

const LEFT_COLLAPSE_STORAGE_KEY = "reformlab-left-panel-collapsed";
const RIGHT_COLLAPSE_STORAGE_KEY = "reformlab-right-panel-collapsed";

type ViewMode = "configuration" | "run" | "progress" | "results" | "comparison" | "data-fusion" | "portfolio";

function readStoredBool(key: string): boolean {
  const value = window.localStorage.getItem(key);
  return value === "true";
}

function getConfigSteps(activeStep: ConfigStep["key"]): ConfigStep[] {
  return [
    { key: "population", label: "Population", status: activeStep === "population" ? "incomplete" : "complete" },
    { key: "template", label: "Policy", status: activeStep === "template" ? "incomplete" : "complete" },
    { key: "parameters", label: "Parameters", status: activeStep === "parameters" ? "incomplete" : "complete" },
    { key: "assumptions", label: "Validation", status: activeStep === "assumptions" ? "incomplete" : "complete" },
  ];
}

function Workspace() {
  const {
    populations,
    templates,
    parameters,
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
    dataFusionSources,
    dataFusionMethods,
    dataFusionResult,
    setDataFusionResult,
    portfolios,
    refetchPortfolios,
  } = useAppState();

  const [activeStep, setActiveStep] = useState<ConfigStep["key"]>("population");
  const [viewMode, setViewMode] = useState<ViewMode>("configuration");
  const [selectedScenarioIds, setSelectedScenarioIds] = useState<string[]>(["baseline", "reform-a"]);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [isNarrow, setIsNarrow] = useState(false);
  const [previousViewMode, setPreviousViewMode] = useState<ViewMode>("results");

  const configSteps = useMemo(() => getConfigSteps(activeStep), [activeStep]);
  const selectedPopulation = useMemo(
    () => populations.find((p) => p.id === selectedPopulationId),
    [populations, selectedPopulationId],
  );
  const selectedTemplate = useMemo(
    () => templates.find((t) => t.id === selectedTemplateId),
    [templates, selectedTemplateId],
  );

  // Filter parameters based on selected template's parameter groups
  const filteredParameters = useMemo(() => {
    if (!selectedTemplate) return parameters;
    return parameters.filter((p) => selectedTemplate.parameterGroups.includes(p.group));
  }, [selectedTemplate, parameters]);

  // Layout effects
  useEffect(() => {
    const onResize = () => {
      const width = window.innerWidth;
      setIsNarrow(width < 1440);
      if (width < 1440) {
        setLeftCollapsed(true);
        setRightCollapsed(true);
      }
    };

    setLeftCollapsed(readStoredBool(LEFT_COLLAPSE_STORAGE_KEY));
    setRightCollapsed(readStoredBool(RIGHT_COLLAPSE_STORAGE_KEY));
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  useEffect(() => {
    window.localStorage.setItem(LEFT_COLLAPSE_STORAGE_KEY, String(leftCollapsed));
  }, [leftCollapsed]);

  useEffect(() => {
    window.localStorage.setItem(RIGHT_COLLAPSE_STORAGE_KEY, String(rightCollapsed));
  }, [rightCollapsed]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key === "[") {
        event.preventDefault();
        setLeftCollapsed((current) => !current);
      }
      if ((event.metaKey || event.ctrlKey) && event.key === "]") {
        event.preventDefault();
        setRightCollapsed((current) => !current);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  // Navigation
  const nextStep = () => {
    const currentIndex = STEP_ORDER.indexOf(activeStep);
    if (currentIndex >= STEP_ORDER.length - 1) {
      setViewMode("run");
      return;
    }
    const next = STEP_ORDER[currentIndex + 1] ?? activeStep;
    setActiveStep(next);
  };

  // Run simulation using real API
  const handleStartRun = async () => {
    setViewMode("progress");
    try {
      await startRun();
      setViewMode("results");
    } catch (err) {
      setViewMode("run");
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else if (err instanceof Error) {
        toast.error("Simulation failed", { description: err.message });
      }
    }
  };

  // Export handlers
  const handleExportCsv = async () => {
    if (!runResult?.run_id) {
      toast.error("No results to export", { description: "Run a simulation first" });
      return;
    }
    try {
      await exportCsv(runResult.run_id);
      toast.success("CSV exported");
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else {
        toast.error("Export failed");
      }
    }
  };

  const handleExportParquet = async () => {
    if (!runResult?.run_id) {
      toast.error("No results to export", { description: "Run a simulation first" });
      return;
    }
    try {
      await exportParquet(runResult.run_id);
      toast.success("Parquet exported");
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(`${err.what} — ${err.why}`, { description: err.fix });
      } else {
        toast.error("Export failed");
      }
    }
  };

  // Comparison
  const openComparison = () => {
    setPreviousViewMode(viewMode);
    setViewMode("comparison");
  };

  const backFromComparison = () => {
    setViewMode(previousViewMode === "comparison" ? "results" : previousViewMode);
  };

  const selectedScenario = useMemo(
    () => scenarios.find((s) => s.id === selectedScenarioId),
    [scenarios, selectedScenarioId],
  );

  const isLastStep = activeStep === STEP_ORDER[STEP_ORDER.length - 1];

  const mainPanelContent = (
    <>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 border border-slate-200 bg-white p-3">
        <div>
          <h1 className="text-lg font-semibold">ReformLab</h1>
          <p className="text-sm text-slate-600">
            Environmental policy analysis workspace
          </p>
        </div>
        <div className="flex gap-2">
          {viewMode !== "configuration" && viewMode !== "comparison" && viewMode !== "data-fusion" && viewMode !== "portfolio" ? (
            <Button variant="outline" onClick={() => setViewMode("configuration")}>
              Configuration
            </Button>
          ) : null}
          {viewMode === "configuration" ? (
            <Button onClick={() => setViewMode("run")}>
              Simulation
            </Button>
          ) : null}
          {viewMode === "comparison" ? (
            <Button variant="outline" onClick={backFromComparison}>
              Back to Results
            </Button>
          ) : null}
          {viewMode === "data-fusion" ? (
            <Button variant="outline" onClick={() => setViewMode("configuration")}>
              Configure Policy
            </Button>
          ) : null}
          {viewMode === "portfolio" ? (
            <Button variant="outline" onClick={() => setViewMode("configuration")}>
              Configure Policy
            </Button>
          ) : null}
        </div>
      </div>

      {viewMode === "configuration" ? (
        <section className="space-y-3">
          <ModelConfigStepper activeStep={activeStep} steps={configSteps} onStepSelect={setActiveStep} />

          {activeStep === "population" ? (
            <PopulationSelectionScreen
              populations={populations}
              selectedPopulationId={selectedPopulationId}
              onSelectPopulation={setSelectedPopulationId}
            />
          ) : null}

          {activeStep === "template" ? (
            <TemplateSelectionScreen
              templates={templates}
              selectedTemplateId={selectedTemplateId}
              onSelectTemplate={selectTemplate}
            />
          ) : null}

          {activeStep === "parameters" ? (
            <ParameterEditingScreen
              parameters={filteredParameters}
              parameterValues={parameterValues}
              onParameterChange={setParameterValue}
            />
          ) : null}

          {activeStep === "assumptions" ? (
            <AssumptionsReviewScreen
              population={selectedPopulation}
              template={selectedTemplate}
              parameters={filteredParameters}
              parameterValues={parameterValues}
            />
          ) : null}

          <div className="flex justify-end">
            <Button onClick={nextStep}>
              {isLastStep ? "Go to Simulation" : "Next Step"}
            </Button>
          </div>
        </section>
      ) : null}

      {viewMode === "run" ? (
        <section className="space-y-3 border border-slate-200 bg-white p-3">
          <h2 className="text-lg font-semibold">Run Simulation</h2>
          <p className="text-sm text-slate-600">
            Ready to compute baseline and reform results for{" "}
            <span className="font-medium">{selectedTemplate?.name ?? "selected policy"}</span>.
          </p>
          <div className="grid gap-2 xl:grid-cols-3">
            {mockSummaryStats.map((stat) => (
              <SummaryStatCard key={stat.id} stat={stat} />
            ))}
          </div>
          <Button onClick={handleStartRun} disabled={runLoading}>
            {runLoading ? "Running..." : "Run Simulation"}
          </Button>
        </section>
      ) : null}

      {viewMode === "progress" ? (
        <RunProgressBar
          progress={runLoading ? 50 : 100}
          currentStep={runLoading ? "Computing simulation..." : "Complete"}
          eta={runLoading ? "estimating..." : "0s"}
          onCancel={() => setViewMode("run")}
        />
      ) : null}

      {viewMode === "results" ? (
        <section className="space-y-3">
          <DistributionalChart
            data={decileData}
            reformLabel={selectedScenario?.templateName ?? selectedScenario?.name ?? "Reform"}
          />
          <div className="grid gap-2 xl:grid-cols-3">
            {mockSummaryStats.map((stat) => (
              <SummaryStatCard key={stat.id} stat={stat} />
            ))}
          </div>
          <div className="flex gap-2">
            <Button onClick={openComparison}>Open Comparison</Button>
            <Button variant="outline" onClick={handleStartRun}>Run Again</Button>
            <Button variant="outline" onClick={handleExportCsv}>Export CSV</Button>
            <Button variant="outline" onClick={handleExportParquet}>Export Parquet</Button>
          </div>
        </section>
      ) : null}

      {viewMode === "comparison" ? (
        <ComparisonView
          scenarios={scenarios}
          selectedScenarioIds={selectedScenarioIds}
          onChangeSelectedScenarioIds={setSelectedScenarioIds}
          decileData={decileData}
        />
      ) : null}

      {viewMode === "data-fusion" ? (
        <DataFusionWorkbench
          sources={dataFusionSources}
          methods={dataFusionMethods}
          initialResult={dataFusionResult}
          onPopulationGenerated={setDataFusionResult}
        />
      ) : null}

      {viewMode === "portfolio" ? (
        <PortfolioDesignerScreen
          templates={templates}
          savedPortfolios={portfolios}
          onSaved={() => { void refetchPortfolios(); }}
          onDeleted={() => { void refetchPortfolios(); }}
        />
      ) : null}
    </>
  );

  return (
    <div className="min-h-screen p-3">
      {window.innerWidth < 1280 ? (
        <div className="border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
          ReformLab is designed for desktop use. Please use a laptop or desktop browser (&gt;= 1280px).
        </div>
      ) : null}

      <WorkspaceLayout
        leftCollapsed={leftCollapsed}
        rightCollapsed={rightCollapsed}
        leftPanel={
          <LeftPanel collapsed={isNarrow ? true : leftCollapsed} onToggle={() => setLeftCollapsed((current) => !current)}>
            <div className="space-y-2">
              <Button
                variant={viewMode === "data-fusion" ? "default" : "outline"}
                className="w-full"
                onClick={() => setViewMode("data-fusion")}
              >
                Population
              </Button>

              <Button
                variant={viewMode === "portfolio" ? "default" : "outline"}
                className="w-full"
                onClick={() => setViewMode("portfolio")}
              >
                Portfolio
              </Button>

              <Button
                variant={viewMode === "configuration" ? "default" : "outline"}
                className="w-full"
                onClick={() => setViewMode("configuration")}
              >
                Configure Policy
              </Button>

              {scenarios.map((scenario) => (
                <ScenarioCard
                  key={scenario.id}
                  scenario={scenario}
                  selected={scenario.id === selectedScenarioId}
                  onSelect={(id) => {
                    setSelectedScenarioId(id);
                    const s = scenarios.find((sc) => sc.id === id);
                    if (s?.status === "completed") {
                      setViewMode("results");
                    }
                  }}
                  onRun={(id) => {
                    setSelectedScenarioId(id);
                    const s = scenarios.find((sc) => sc.id === id);
                    if (s?.templateId) {
                      selectTemplate(s.templateId);
                    }
                    setViewMode("run");
                  }}
                  onCompare={(id) => {
                    setSelectedScenarioId(id);
                    setSelectedScenarioIds(["baseline", id]);
                    setPreviousViewMode(viewMode);
                    setViewMode("comparison");
                  }}
                  onClone={cloneScenario}
                  onDelete={deleteScenario}
                />
              ))}
            </div>
          </LeftPanel>
        }
        mainPanel={<MainContent>{mainPanelContent}</MainContent>}
        rightPanel={
          <RightPanel collapsed={isNarrow ? true : rightCollapsed} onToggle={() => setRightCollapsed((current) => !current)}>
            <div className="space-y-3">
              {selectedScenario ? (
                <section className="border border-slate-200 bg-white p-3">
                  <p className="text-xs font-semibold uppercase text-slate-500">Selected Scenario</p>
                  <p className="text-sm font-medium text-slate-800">{selectedScenario.name}</p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    <Badge variant={selectedScenario.status === "completed" ? "success" : "default"}>
                      {selectedScenario.status}
                    </Badge>
                  </div>
                  {selectedScenario.lastRun ? (
                    <p className="mt-1 text-xs text-slate-500">Last run: {selectedScenario.lastRun}</p>
                  ) : null}
                  {selectedScenario.templateName ? (
                    <p className="mt-1 text-xs text-slate-500">Policy: {selectedScenario.templateName}</p>
                  ) : null}
                  <p className="mt-1 text-xs text-slate-500">
                    {selectedScenario.parameterChanges} parameter{selectedScenario.parameterChanges === 1 ? "" : "s"} changed
                  </p>
                </section>
              ) : null}

              <section className="border border-slate-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase text-slate-500">Population</p>
                <p className="text-sm text-slate-800">{selectedPopulation?.name}</p>
              </section>

              <section className="border border-slate-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase text-slate-500">Template</p>
                <p className="text-sm text-slate-800">{selectedTemplate?.name}</p>
              </section>

              <section className="border border-slate-200 bg-white p-3">
                <p className="text-xs font-semibold uppercase text-slate-500">Workspace State</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  <Badge variant="info">{viewMode}</Badge>
                  {viewMode === "configuration" ? (
                    <Badge variant="violet">{activeStep}</Badge>
                  ) : null}
                </div>
              </section>
            </div>
          </RightPanel>
        }
      />
    </div>
  );
}

export default function App() {
  const { isAuthenticated, authLoading, authenticate } = useAppState();

  if (!isAuthenticated) {
    return (
      <>
        <PasswordPrompt onSubmit={authenticate} loading={authLoading} />
        <Toaster />
      </>
    );
  }

  return (
    <>
      <Workspace />
      <Toaster />
    </>
  );
}
