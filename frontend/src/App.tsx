// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { LeftPanel } from "@/components/layout/LeftPanel";
import { MainContent } from "@/components/layout/MainContent";
import { RightPanel } from "@/components/layout/RightPanel";
import { WorkspaceLayout } from "@/components/layout/WorkspaceLayout";
import { PasswordPrompt } from "@/components/auth/PasswordPrompt";
import { ConfigurationScreen } from "@/components/screens/ConfigurationScreen";
import { DataFusionWorkbench } from "@/components/screens/DataFusionWorkbench";
import { PortfolioDesignerScreen } from "@/components/screens/PortfolioDesignerScreen";
import { SimulationRunnerScreen } from "@/components/screens/SimulationRunnerScreen";
import type { ConfigStepKey } from "@/components/simulation/ModelConfigStepper";
import { BehavioralDecisionViewerScreen } from "@/components/screens/BehavioralDecisionViewerScreen";
import { ComparisonDashboardScreen } from "@/components/screens/ComparisonDashboardScreen";
import { ResultsOverviewScreen } from "@/components/screens/ResultsOverviewScreen";
// ComparisonView (Phase 1 mock-driven prototype) is kept but no longer imported in workspace
import { RunProgressBar } from "@/components/simulation/RunProgressBar";
import { ScenarioCard } from "@/components/simulation/ScenarioCard";
import { SummaryStatCard } from "@/components/simulation/SummaryStatCard";
import { WorkflowNavRail } from "@/components/layout/WorkflowNavRail";
import { Toaster } from "@/components/ui/sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ContextualHelpPanel } from "@/components/help/ContextualHelpPanel";
import { Separator } from "@/components/ui/separator";
import { useAppState } from "@/contexts/AppContext";
import { ApiError } from "@/api/client";
import { exportCsv, exportParquet } from "@/api/exports";
import {
  mockSummaryStats,
} from "@/data/mock-data";

const LEFT_COLLAPSE_STORAGE_KEY = "reformlab-left-panel-collapsed";
const RIGHT_COLLAPSE_STORAGE_KEY = "reformlab-right-panel-collapsed";

type ViewMode = "configuration" | "run" | "progress" | "results" | "comparison" | "decisions" | "data-fusion" | "portfolio" | "runner";

function readStoredBool(key: string): boolean {
  const value = window.localStorage.getItem(key);
  return value === "true";
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
    refetchTemplates,
    selectedPortfolioName,
    results,
    apiConnected,
  } = useAppState();

  const [activeStep, setActiveStep] = useState<ConfigStepKey>("population");
  const [viewMode, setViewMode] = useState<ViewMode>("configuration");
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [isNarrow, setIsNarrow] = useState(false);
  const [previousViewMode, setPreviousViewMode] = useState<ViewMode>("results");

  const selectedTemplate = useMemo(
    () => templates.find((t) => t.id === selectedTemplateId),
    [templates, selectedTemplateId],
  );

  // Layout effects
  useEffect(() => {
    const onResize = () => {
      const width = window.innerWidth;
      setIsNarrow(width < 1024);
      if (width < 1024) {
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

  const openDecisions = () => {
    setPreviousViewMode(viewMode);
    setViewMode("decisions");
  };

  const backFromDecisions = () => {
    setViewMode(previousViewMode === "decisions" ? "results" : previousViewMode);
  };

  const selectedScenario = useMemo(
    () => scenarios.find((s) => s.id === selectedScenarioId),
    [scenarios, selectedScenarioId],
  );

  const mainPanelContent = (
    <>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-200 bg-gradient-to-r from-white to-indigo-50 p-3 shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold">ReformLab</h1>
            <Badge variant={apiConnected ? "success" : "warning"} className="rounded-full text-[10px] leading-none">
              {apiConnected ? "API connected" : "Sample data"}
            </Badge>
          </div>
          <p className="text-sm text-indigo-700">
            Environmental policy analysis workspace
          </p>
        </div>
        <div className="flex gap-2">
          {viewMode !== "configuration" && viewMode !== "comparison" && viewMode !== "decisions" && viewMode !== "data-fusion" && viewMode !== "portfolio" && viewMode !== "runner" ? (
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
        <ConfigurationScreen
          activeStep={activeStep}
          onStepSelect={setActiveStep}
          populations={populations}
          selectedPopulationId={selectedPopulationId}
          onSelectPopulation={setSelectedPopulationId}
          templates={templates}
          selectedTemplateId={selectedTemplateId}
          onSelectTemplate={selectTemplate}
          onTemplatesChanged={refetchTemplates}
          parameters={parameters}
          parameterValues={parameterValues}
          onParameterChange={setParameterValue}
          onGoToSimulation={() => setViewMode("run")}
        />
      ) : null}

      {viewMode === "run" ? (
        <section className="space-y-3 rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
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
        <ResultsOverviewScreen
          decileData={decileData}
          runResult={runResult}
          reformLabel={selectedScenario?.templateName ?? selectedScenario?.name ?? "Reform"}
          onCompare={openComparison}
          onViewDecisions={openDecisions}
          onRunAgain={handleStartRun}
          onExportCsv={handleExportCsv}
          onExportParquet={handleExportParquet}
        />
      ) : null}

      {viewMode === "comparison" ? (
        <ComparisonDashboardScreen
          results={results}
          onBack={backFromComparison}
        />
      ) : null}

      {viewMode === "decisions" && runResult?.run_id ? (
        <BehavioralDecisionViewerScreen
          runId={runResult.run_id}
          onBack={backFromDecisions}
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

      {viewMode === "runner" ? (
        <SimulationRunnerScreen
          selectedPopulationId={selectedPopulationId || null}
          selectedPortfolioName={selectedPortfolioName}
          selectedTemplateName={selectedTemplateId || null}
          onCancel={() => setViewMode("configuration")}
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
              <WorkflowNavRail
                viewMode={viewMode}
                setViewMode={setViewMode}
                collapsed={isNarrow ? true : leftCollapsed}
                selectedPopulationId={selectedPopulationId}
                dataFusionResult={dataFusionResult}
                portfolios={portfolios}
                results={results}
              />

              {scenarios.length > 0 && <Separator className="my-1" />}

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
            <ContextualHelpPanel viewMode={viewMode} activeStep={activeStep} />
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
