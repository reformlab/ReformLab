import { useEffect, useMemo, useState } from "react";

import { LeftPanel } from "@/components/layout/LeftPanel";
import { MainContent } from "@/components/layout/MainContent";
import { RightPanel } from "@/components/layout/RightPanel";
import { WorkspaceLayout } from "@/components/layout/WorkspaceLayout";
import { AssumptionsReviewScreen } from "@/components/screens/AssumptionsReviewScreen";
import { ParameterEditingScreen } from "@/components/screens/ParameterEditingScreen";
import { PopulationSelectionScreen } from "@/components/screens/PopulationSelectionScreen";
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
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  mockDecileData,
  mockParameters,
  mockPopulations,
  mockScenarios,
  mockSimulationSteps,
  mockSummaryStats,
  mockTemplates,
} from "@/data/mock-data";

const STEP_ORDER: ConfigStep["key"][] = [
  "population",
  "template",
  "parameters",
  "assumptions",
];

const LEFT_COLLAPSE_STORAGE_KEY = "reformlab-left-panel-collapsed";
const RIGHT_COLLAPSE_STORAGE_KEY = "reformlab-right-panel-collapsed";

type ViewMode = "configuration" | "run" | "progress" | "results" | "comparison";

const TEMPLATE_FAST_PATHS: Record<string, Partial<Record<string, number>>> = {
  "carbon-tax-flat": { tax_rate: 55, dividend_per_capita: 0 },
  "carbon-tax-progressive": { tax_rate: 0.62, dividend_per_capita: 140 },
  "carbon-tax-dividend": { tax_rate: 48, dividend_per_capita: 150 },
  "subsidy-energy": { rebate_rate: 0.22, means_test_ceiling: 24000 },
  "feebate-vehicle": { rebate_rate: 0.18, exemption_threshold: 17500 },
};

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

export default function App() {
  const [activeStep, setActiveStep] = useState<ConfigStep["key"]>("population");
  const [viewMode, setViewMode] = useState<ViewMode>("configuration");
  const [selectedPopulationId, setSelectedPopulationId] = useState(mockPopulations[0]?.id ?? "");
  const [selectedTemplateId, setSelectedTemplateId] = useState(mockTemplates[0]?.id ?? "");
  const [selectedScenarioIds, setSelectedScenarioIds] = useState<string[]>(["baseline", "reform-a"]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("reform-a");
  const [progress, setProgress] = useState(0);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [rightCollapsed, setRightCollapsed] = useState(false);
  const [isNarrow, setIsNarrow] = useState(false);
  const [parameterValues, setParameterValues] = useState<Record<string, number>>(() =>
    Object.fromEntries(mockParameters.map((parameter) => [parameter.id, parameter.value])),
  );

  const configSteps = useMemo(() => getConfigSteps(activeStep), [activeStep]);
  const selectedPopulation = useMemo(
    () => mockPopulations.find((population) => population.id === selectedPopulationId),
    [selectedPopulationId],
  );
  const selectedTemplate = useMemo(
    () => mockTemplates.find((template) => template.id === selectedTemplateId),
    [selectedTemplateId],
  );

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

  useEffect(() => {
    if (viewMode !== "progress") {
      return undefined;
    }

    const interval = window.setInterval(() => {
      setProgress((current) => {
        if (current >= 100) {
          window.clearInterval(interval);
          setViewMode("results");
          return 100;
        }
        return Math.min(current + 12, 100);
      });
    }, 450);

    return () => window.clearInterval(interval);
  }, [viewMode]);

  const currentProgressStep =
    mockSimulationSteps[Math.min(Math.floor(progress / 14), mockSimulationSteps.length - 1)] ??
    "Finalizing results...";

  const nextStep = () => {
    const currentIndex = STEP_ORDER.indexOf(activeStep);
    const next = STEP_ORDER[Math.min(currentIndex + 1, STEP_ORDER.length - 1)] ?? activeStep;
    setActiveStep(next);
  };

  const selectTemplate = (templateId: string) => {
    setSelectedTemplateId(templateId);
    const defaults = TEMPLATE_FAST_PATHS[templateId] ?? {};
    setParameterValues((current) => {
      const next = { ...current };
      for (const [key, value] of Object.entries(defaults)) {
        if (typeof value === "number") {
          next[key] = value;
        }
      }
      return next;
    });
  };

  const startRun = () => {
    setViewMode("progress");
    setProgress(0);
  };

  const mainPanelContent = (
    <>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 border border-slate-200 bg-white p-3">
        <div>
          <h1 className="text-lg font-semibold">ReformLab Static GUI Prototype</h1>
          <p className="text-sm text-slate-600">
            Dense Terminal layout with reusable React components for Stories 6-4a and 6-4b.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant={viewMode === "configuration" ? "default" : "outline"} onClick={() => setViewMode("configuration")}>
            Configuration
          </Button>
          <Button variant={viewMode === "run" ? "default" : "outline"} onClick={() => setViewMode("run")}>
            Simulation
          </Button>
        </div>
      </div>

      {viewMode === "configuration" ? (
        <section className="space-y-3">
          <ModelConfigStepper activeStep={activeStep} steps={configSteps} onStepSelect={setActiveStep} />

          {activeStep === "population" ? (
            <PopulationSelectionScreen
              populations={mockPopulations}
              selectedPopulationId={selectedPopulationId}
              onSelectPopulation={setSelectedPopulationId}
            />
          ) : null}

          {activeStep === "template" ? (
            <TemplateSelectionScreen
              templates={mockTemplates}
              selectedTemplateId={selectedTemplateId}
              onSelectTemplate={selectTemplate}
            />
          ) : null}

          {activeStep === "parameters" ? (
            <ParameterEditingScreen
              parameters={mockParameters}
              parameterValues={parameterValues}
              onParameterChange={(id, value) => setParameterValues((current) => ({ ...current, [id]: value }))}
            />
          ) : null}

          {activeStep === "assumptions" ? (
            <AssumptionsReviewScreen
              population={selectedPopulation}
              template={selectedTemplate}
              parameters={mockParameters}
              parameterValues={parameterValues}
            />
          ) : null}

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setViewMode("run")}>
              Jump to Simulation
            </Button>
            <Button onClick={nextStep}>Next Step</Button>
          </div>
        </section>
      ) : null}

      {viewMode === "run" ? (
        <section className="space-y-3 border border-slate-200 bg-white p-3">
          <h2 className="text-lg font-semibold">Run Trigger</h2>
          <p className="text-sm text-slate-600">
            Ready to compute baseline and reform results using mock data and simulated execution.
          </p>
          <div className="grid gap-2 xl:grid-cols-3">
            {mockSummaryStats.map((stat) => (
              <SummaryStatCard key={stat.id} stat={stat} />
            ))}
          </div>
          <div className="flex gap-2">
            <Button onClick={startRun}>Run Simulation</Button>
            <Button variant="outline" onClick={() => setViewMode("configuration")}>
              Back to Configuration
            </Button>
          </div>
        </section>
      ) : null}

      {viewMode === "progress" ? (
        <RunProgressBar
          progress={progress}
          currentStep={currentProgressStep}
          eta={`${Math.max(1, Math.round((100 - progress) / 12))}s`}
          onCancel={() => {
            setViewMode("run");
            setProgress(0);
          }}
        />
      ) : null}

      {viewMode === "results" ? (
        <section className="space-y-3">
          <DistributionalChart data={mockDecileData} />
          <div className="grid gap-2 xl:grid-cols-3">
            {mockSummaryStats.map((stat) => (
              <SummaryStatCard key={stat.id} stat={stat} />
            ))}
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setViewMode("comparison")}>Open Comparison</Button>
            <Button variant="outline" onClick={() => setViewMode("run")}>Run Again</Button>
          </div>
        </section>
      ) : null}

      {viewMode === "comparison" ? (
        <ComparisonView
          scenarios={mockScenarios}
          selectedScenarioIds={selectedScenarioIds}
          onChangeSelectedScenarioIds={setSelectedScenarioIds}
          decileData={mockDecileData}
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
              {mockScenarios.map((scenario) => (
                <ScenarioCard
                  key={scenario.id}
                  scenario={scenario}
                  selected={scenario.id === selectedScenarioId}
                  onRun={(id) => {
                    setSelectedScenarioId(id);
                    setViewMode("run");
                  }}
                  onCompare={(id) => {
                    setSelectedScenarioId(id);
                    setSelectedScenarioIds(["baseline", id]);
                    setViewMode("comparison");
                  }}
                />
              ))}
            </div>
          </LeftPanel>
        }
        mainPanel={<MainContent>{mainPanelContent}</MainContent>}
        rightPanel={
          <RightPanel collapsed={isNarrow ? true : rightCollapsed} onToggle={() => setRightCollapsed((current) => !current)}>
            <div className="space-y-3">
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
                  <Badge variant="violet">{activeStep}</Badge>
                </div>
              </section>
            </div>
          </RightPanel>
        }
      />
    </div>
  );
}
