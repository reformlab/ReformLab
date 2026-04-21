// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** InvestmentDecisionsStageScreen — Stage 3: Investment Decisions Configuration.
 *
 * Dedicated stage for behavioral response modeling. When disabled, shows a summary
 * with enable toggle and Continue to Scenario action. When enabled, renders the
 * full InvestmentDecisionsWizard (Enable, Model, Parameters, Review steps).
 *
 * Story 26.2 — AC-1, AC-2, AC-7.
 */

import { useAppState } from "@/contexts/AppContext";
import { InvestmentDecisionsWizard } from "@/components/engine/InvestmentDecisionsWizard";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function InvestmentDecisionsStageScreen() {
  const {
    activeScenario,
    updateScenarioField,
    navigateTo,
  } = useAppState();

  // ============================================================================
  // Null state
  // ============================================================================

  if (!activeScenario) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-12 text-center">
        <p className="text-slate-500">No active scenario.</p>
        <Button onClick={() => navigateTo("policies")}>Go to Stage 1 to create a scenario</Button>
      </div>
    );
  }

  const engineConfig = activeScenario.engineConfig;
  const isEnabled = engineConfig.investmentDecisionsEnabled;

  const updateEngineConfig = (cfg: typeof engineConfig) => {
    updateScenarioField("engineConfig", cfg);
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="flex flex-col h-full">
      {/* ─── Toolbar ─────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 bg-white">
        <h1 className="text-xl font-semibold text-slate-900">Investment Decisions</h1>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigateTo("population")}
          >
            <ChevronLeft className="h-4 w-4 mr-1" />
            Back to Population
          </Button>
          <Button
            size="sm"
            onClick={() => navigateTo("scenario")}
          >
            Continue to Scenario
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>
      </div>

      {/* ─── Body ────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto p-6">
        {isEnabled ? (
          // Enabled: show wizard
          <div className="max-w-2xl">
            <InvestmentDecisionsWizard
              engineConfig={engineConfig}
              onUpdateEngineConfig={updateEngineConfig}
            />
          </div>
        ) : (
          // Disabled: show summary with enable toggle
          <div className="max-w-2xl space-y-6">
            <div>
              <h2 className="text-lg font-semibold text-slate-900 mb-2">Investment Decisions</h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                Investment decisions model household technology adoption choices (e.g., electric vehicles,
                heat pumps) using behavioral economics. This is an optional advanced feature.
              </p>
            </div>

            <div className="p-6 bg-slate-50 rounded-lg border border-slate-200 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Enable investment decisions</h3>
                  <p className="text-xs text-slate-500">Model household technology adoption</p>
                </div>
                <Switch
                  checked={isEnabled}
                  onChange={(e) => updateEngineConfig({
                    ...engineConfig,
                    investmentDecisionsEnabled: e.target.checked,
                    logitModel: e.target.checked ? "multinomial_logit" : null,
                  })}
                  aria-label="Toggle investment decisions"
                />
              </div>

              <div className="pt-4 border-t border-slate-200">
                <p className="text-xs text-slate-500 mb-3">
                  When enabled, you can configure the logit model and taste parameters that govern
                  household behavioral responses to policy changes.
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => navigateTo("scenario")}
                >
                  Skip to Scenario
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>

            <div className="text-sm text-slate-600">
              <p className="font-medium text-slate-700 mb-1">What are investment decisions?</p>
              <p className="text-xs">
                Investment decisions use discrete choice models (logit) to simulate how households
                choose between technologies like vehicles and heating systems based on costs and
                preferences. This adds behavioral realism to policy analysis but requires additional
                configuration and calibration data.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
