// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { LeftPanel } from "@/components/layout/LeftPanel";
import { MainContent } from "@/components/layout/MainContent";
import { RightPanel } from "@/components/layout/RightPanel";
import { WorkspaceLayout } from "@/components/layout/WorkspaceLayout";
import { TopBar } from "@/components/layout/TopBar";
import { PasswordPrompt } from "@/components/auth/PasswordPrompt";
import { SimulationRunnerScreen } from "@/components/screens/SimulationRunnerScreen";
import { BehavioralDecisionViewerScreen } from "@/components/screens/BehavioralDecisionViewerScreen";
import { ComparisonDashboardScreen } from "@/components/screens/ComparisonDashboardScreen";
import { ResultsOverviewScreen } from "@/components/screens/ResultsOverviewScreen";
import { PoliciesStageScreen } from "@/components/screens/PoliciesStageScreen";
import { PopulationStageScreen } from "@/components/screens/PopulationStageScreen";
import { EngineStageScreen } from "@/components/screens/EngineStageScreen";
import { WorkflowNavRail } from "@/components/layout/WorkflowNavRail";
import { Toaster } from "@/components/ui/sonner";
import { ContextualHelpPanel } from "@/components/help/ContextualHelpPanel";
import { useAppState } from "@/contexts/AppContext";
import { ApiError } from "@/api/client";
import { exportCsv, exportParquet } from "@/api/exports";

const LEFT_COLLAPSE_STORAGE_KEY = "reformlab-left-panel-collapsed";
const RIGHT_COLLAPSE_STORAGE_KEY = "reformlab-right-panel-collapsed";

function readStoredBool(key: string): boolean {
  const value = window.localStorage.getItem(key);
  return value === "true";
}

function Workspace() {
  const {
    selectedPopulationId,
    populations,
    decileData,
    startRun,
    runResult,
    dataFusionResult,
    portfolios,
    results,
    activeStage,
    activeSubView,
    navigateTo,
    activeScenario,
    selectedPortfolioName,
    selectedTemplateId,
  } = useAppState();

  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [isNarrow, setIsNarrow] = useState(false);

  // Story 22.4: Track explorer population ID from PopulationStageScreen
  const [explorerPopulationId, setExplorerPopulationId] = useState<string | null>(null);

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

  // Run simulation using real API — navigates to results/runner stage
  const handleStartRun = async () => {
    navigateTo("results", "runner");
    try {
      await startRun();
      navigateTo("results");
    } catch (err) {
      // Already on results/runner — just show toast
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

  const selectedScenario = useMemo(
    () => results.find((r) => r.run_id === runResult?.run_id),
    [results, runResult],
  );

  // Stage 4 sub-view content
  const resultsContent = (() => {
    if (activeSubView === "runner") {
      return <SimulationRunnerScreen onCancel={() => { navigateTo("results"); }} />;
    }
    if (activeSubView === "comparison") {
      return (
        <ComparisonDashboardScreen
          results={results}
          onBack={() => { navigateTo("results"); }}
        />
      );
    }
    if (activeSubView === "decisions") {
      if (!runResult?.run_id) {
        return (
          <div className="flex flex-col items-center justify-center gap-3 p-12 text-center">
            <p className="text-sm text-slate-500">No simulation run available. Run a simulation first to view behavioral decisions.</p>
          </div>
        );
      }
      return (
        <BehavioralDecisionViewerScreen
          runId={runResult.run_id}
          onBack={() => { navigateTo("results"); }}
        />
      );
    }
    // Default results overview (activeSubView === null)
    return (
      <ResultsOverviewScreen
        decileData={decileData}
        runResult={runResult}
        reformLabel={selectedScenario?.template_name ?? "Reform"}
        onCompare={() => { navigateTo("results", "comparison"); }}
        onViewDecisions={() => { navigateTo("results", "decisions"); }}
        onRunAgain={handleStartRun}
        onExportCsv={handleExportCsv}
        onExportParquet={handleExportParquet}
      />
    );
  })();

  // Stage-based main content
  const mainPanelContent = (
    <>
      {activeStage === "policies" ? <PoliciesStageScreen /> : null}
      {activeStage === "population" ? (
        <PopulationStageScreen
          onExplorerPopulationChange={setExplorerPopulationId}
        />
      ) : null}
      {activeStage === "engine" ? <EngineStageScreen /> : null}
      {activeStage === "results" ? resultsContent : null}
    </>
  );

  return (
    <div className="flex h-screen flex-col">
      {window.innerWidth < 1280 ? (
        <div className="shrink-0 border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
          ReformLab is designed for desktop use. Please use a laptop or desktop browser (&gt;= 1280px).
        </div>
      ) : null}

      <WorkspaceLayout
        topBar={<TopBar />}
        leftCollapsed={leftCollapsed}
        rightCollapsed={rightCollapsed}
        leftPanel={
          <LeftPanel collapsed={isNarrow ? true : leftCollapsed} onToggle={() => { setLeftCollapsed((current) => !current); }}>
            <WorkflowNavRail
              activeStage={activeStage}
              navigateTo={navigateTo}
              collapsed={isNarrow ? true : leftCollapsed}
              selectedPopulationId={selectedPopulationId}
              dataFusionResult={dataFusionResult}
              portfolios={portfolios}
              results={results}
              activeScenario={activeScenario}
              populations={populations}
              explorerPopulationId={explorerPopulationId}
              activeSubView={activeSubView}
            />
          </LeftPanel>
        }
        mainPanel={<MainContent>{mainPanelContent}</MainContent>}
        rightPanel={
          <RightPanel collapsed={isNarrow ? true : rightCollapsed} onToggle={() => { setRightCollapsed((current) => !current); }}>
            <ContextualHelpPanel activeStage={activeStage} activeSubView={activeSubView} />
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
