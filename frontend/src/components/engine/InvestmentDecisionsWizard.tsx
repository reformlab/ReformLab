// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** InvestmentDecisionsWizard — Guided 4-step wizard for investment decisions configuration.
 *
 * Replaces the dense InvestmentDecisionsAccordion with a clear, sequential flow:
 * 1. Enable — toggle feature on/off with explanation
 * 2. Model — choose logit model type
 * 3. Parameters — edit taste parameters (persisted to EngineConfig)
 * 4. Review — summary of choices with edit controls
 *
 * Story 22.6 — AC-1, AC-2, AC-3, AC-4.
 */

import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { CalibrationPanel } from "./CalibrationPanel";
import type { EngineConfig, CalibrationState, TasteParameters } from "@/types/workspace";
import { DEFAULT_TASTE_PARAMETERS } from "@/types/workspace";

// ============================================================================
// Types
// ============================================================================

interface InvestmentDecisionsWizardProps {
  engineConfig: EngineConfig;
  onUpdateEngineConfig: (config: EngineConfig) => void;
}

type WizardStep = 0 | 1 | 2 | 3;  // Enable | Model | Parameters | Review

const STEP_LABELS = ["Enable", "Model", "Parameters", "Review"] as const;

// ============================================================================
// Helper: Model descriptions
// ============================================================================

const LOGIT_MODEL_DESCRIPTIONS = {
  multinomial_logit: "Standard discrete choice model with independent alternatives.",
  nested_logit: "Groups similar alternatives into nests for more realistic substitution patterns.",
  mixed_logit: "Allows for random taste variation across the population.",
} as const;

// ============================================================================
// Component
// ============================================================================

export function InvestmentDecisionsWizard({ engineConfig, onUpdateEngineConfig }: InvestmentDecisionsWizardProps) {
  const [activeStep, setActiveStep] = useState<WizardStep>(0);
  const [visitedSteps, setVisitedSteps] = useState<Set<WizardStep>>(new Set([0]));

  // Track the previous model value to preserve it on re-enable
  const previousLogitModelRef = useRef<EngineConfig["logitModel"]>(engineConfig.logitModel);

  // Update ref when model changes from external sources (not our own toggle)
  useEffect(() => {
    if (engineConfig.logitModel !== null) {
      previousLogitModelRef.current = engineConfig.logitModel;
    }
  }, [engineConfig.logitModel]);

  const isEnabled = engineConfig.investmentDecisionsEnabled;
  // For Parameters step, use defaults if null (for slider display)
  // For Review step, we check if tasteParameters is actually configured
  const tasteParams = engineConfig.tasteParameters ?? DEFAULT_TASTE_PARAMETERS;

  // Sync step state when investment decisions are enabled from outside the component
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (isEnabled && activeStep === 0) {
      setActiveStep(1);  // Move to Model step when enabled externally
    } else if (!isEnabled && activeStep > 0) {
      setActiveStep(0);  // Return to Enable step when disabled
    }
  }, [isEnabled]);  // Only depend on isEnabled, not activeStep

  // ============================================================================
  // Step navigation
  // ============================================================================

  const goToStep = (step: WizardStep) => {
    setActiveStep(step);
    setVisitedSteps((prev) => new Set([...prev, step]));
  };

  const handleNext = () => {
    if (activeStep < 3) {
      const nextStep = (activeStep + 1) as WizardStep;
      setActiveStep(nextStep);
      setVisitedSteps((prev) => new Set([...prev, nextStep]));
    }
  };

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep((prev) => (prev - 1) as WizardStep);
    }
  };

  const handleToggle = (enabled: boolean) => {
    // Preserve existing model on re-enable; only set default on first enable
    // Use the ref to track the model across disable/enable cycles
    const newLogitModel = enabled
      ? (engineConfig.logitModel ?? previousLogitModelRef.current ?? "multinomial_logit")
      : null;

    // Update ref before disabling so we remember the model
    if (!enabled && engineConfig.logitModel !== null) {
      previousLogitModelRef.current = engineConfig.logitModel;
    }

    onUpdateEngineConfig({
      ...engineConfig,
      investmentDecisionsEnabled: enabled,
      logitModel: newLogitModel,
    });
    // When enabling, auto-advance to Model step
    if (enabled && activeStep === 0) {
      setActiveStep(1);
    }
  };

  const handleLogitModelChange = (model: EngineConfig["logitModel"]) => {
    onUpdateEngineConfig({
      ...engineConfig,
      logitModel: model,
    });
  };

  const handleTasteParameterChange = <K extends keyof TasteParameters>(
    key: K,
    value: TasteParameters[K],
  ) => {
    // Read from engineConfig directly to avoid stale closure
    const currentTasteParams = engineConfig.tasteParameters ?? DEFAULT_TASTE_PARAMETERS;
    onUpdateEngineConfig({
      ...engineConfig,
      tasteParameters: {
        ...currentTasteParams,
        [key]: value,
      },
    });
  };

  // ============================================================================
  // Step renderers
  // ============================================================================

  const renderStepIndicators = () => {
    return (
      <div className="flex items-center gap-3 mb-4">
        {STEP_LABELS.map((label, idx) => {
          const step = idx as WizardStep;
          const isCompleted = step < activeStep || (step === activeStep && visitedSteps.has(step) && step > 0);
          const isCurrent = step === activeStep;
          const isDisabled = !isEnabled && step > 0;

          return (
            <div key={label} className="flex items-center gap-1">
              <div
                className={`
                  flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium border-2
                  ${isDisabled
                    ? "bg-slate-100 border-slate-200 text-slate-400"
                    : isCompleted
                      ? "bg-emerald-500 border-emerald-500 text-white"
                      : isCurrent
                        ? "bg-blue-500 border-blue-500 text-white"
                        : "bg-white border-slate-300 text-slate-600"
                  }
                `}
              >
                {isCompleted ? <Check className="h-4 w-4" /> : idx + 1}
              </div>
              <span
                className={`
                  text-xs font-medium
                  ${isDisabled
                    ? "text-slate-400"
                    : isCurrent || isCompleted
                      ? "text-slate-900"
                      : "text-slate-600"
                  }
                `}
              >
                {label}
              </span>
              {idx < STEP_LABELS.length - 1 && (
                <div className={`w-8 h-0.5 ${idx < activeStep ? "bg-emerald-500" : "bg-slate-200"}`} />
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const renderEnableStep = () => (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-900 mb-2">Enable Investment Decisions</h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          Investment decisions model household technology adoption choices (e.g., electric vehicles,
          heat pumps) using behavioral economics. This is an advanced scenario feature that adds
          realism but requires additional configuration.
        </p>
      </div>

      <div className="flex items-center justify-between p-3 bg-slate-50 rounded border border-slate-200">
        <div>
          <p className="text-sm font-medium text-slate-900">Enable investment decisions</p>
          <p className="text-xs text-slate-500">Model household technology adoption</p>
        </div>
        <Switch
          checked={isEnabled}
          onChange={(e) => handleToggle(e.target.checked)}
          aria-label="Toggle investment decisions"
        />
      </div>
    </div>
  );

  const renderModelStep = () => (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-900 mb-2">Choose Logit Model</h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          Select the discrete choice model for investment decisions. Each model makes different
          assumptions about how households choose between alternatives.
        </p>
      </div>

      <div className="space-y-1">
        <label className="text-xs font-medium text-slate-700">Logit model</label>
        <select
          className="w-full rounded border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-400"
          value={engineConfig.logitModel ?? ""}
          onChange={(e) => handleLogitModelChange(e.target.value as EngineConfig["logitModel"])}
          aria-label="Logit model"
        >
          <option value="" disabled>Select a model...</option>
          <option value="multinomial_logit">Multinomial Logit</option>
          <option value="nested_logit">Nested Logit</option>
          <option value="mixed_logit">Mixed Logit</option>
        </select>
        {engineConfig.logitModel && (
          <p className="text-xs text-slate-500 mt-1">
            {LOGIT_MODEL_DESCRIPTIONS[engineConfig.logitModel]}
          </p>
        )}
      </div>
    </div>
  );

  const renderParametersStep = () => (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-slate-900 mb-2">Taste Parameters</h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          Taste parameters capture household preferences for different technology attributes.
          These values are used in the utility function for investment decisions.
        </p>
      </div>

      <div className="space-y-4">
        {/* β_price */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-slate-600">
            <span>Price sensitivity (β_price)</span>
            <span className="font-mono">{tasteParams.priceSensitivity.toFixed(1)}</span>
          </div>
          <Slider
            min={-5}
            max={0}
            step={0.1}
            value={[tasteParams.priceSensitivity]}
            onChange={([v]) => handleTasteParameterChange("priceSensitivity", v!)}
            aria-label="Price sensitivity"
          />
          <p className="text-xs text-slate-500">Negative: households prefer lower prices</p>
        </div>

        {/* β_range */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-slate-600">
            <span>Range anxiety (β_range)</span>
            <span className="font-mono">{tasteParams.rangeAnxiety.toFixed(1)}</span>
          </div>
          <Slider
            min={-3}
            max={0}
            step={0.1}
            value={[tasteParams.rangeAnxiety]}
            onChange={([v]) => handleTasteParameterChange("rangeAnxiety", v!)}
            aria-label="Range anxiety"
          />
          <p className="text-xs text-slate-500">Negative: households dislike limited range</p>
        </div>

        {/* β_green */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-slate-600">
            <span>Environmental preference (β_green)</span>
            <span className="font-mono">{tasteParams.envPreference.toFixed(1)}</span>
          </div>
          <Slider
            min={0}
            max={3}
            step={0.1}
            value={[tasteParams.envPreference]}
            onChange={([v]) => handleTasteParameterChange("envPreference", v!)}
            aria-label="Environmental preference"
          />
          <p className="text-xs text-slate-500">Positive: households prefer eco-friendly options</p>
        </div>
      </div>
    </div>
  );

  const renderReviewStep = () => {
    const calibrationState = engineConfig.calibrationState ?? "not_configured";

    const calibrationBadgeColor: Record<CalibrationState, string> = {
      not_configured: "text-amber-700 border-amber-300 bg-amber-50",
      in_progress: "text-blue-700 border-blue-300 bg-blue-50",
      completed: "text-emerald-700 border-emerald-300 bg-emerald-50",
    };

    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 mb-2">Review Configuration</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Review your investment decisions settings before running the scenario. You can edit
            any section by clicking the Edit button.
          </p>
        </div>

        {/* Summary cards */}
        <div className="space-y-3">
          {/* Logit model */}
          <div className="p-3 bg-slate-50 rounded border border-slate-200">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-slate-700">Logit model</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs text-blue-600 hover:text-blue-700 px-2"
                onClick={() => goToStep(1)}
              >
                Edit
              </Button>
            </div>
            <p className="text-sm text-slate-900 font-medium">
              {engineConfig.logitModel
                ? engineConfig.logitModel.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())
                : "Not selected"}
            </p>
          </div>

          {/* Taste parameters */}
          <div className="p-3 bg-slate-50 rounded border border-slate-200">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium text-slate-700">Taste parameters</span>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs text-blue-600 hover:text-blue-700 px-2"
                onClick={() => goToStep(2)}
              >
                Edit
              </Button>
            </div>
            {engineConfig.tasteParameters ? (
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <span className="text-slate-500">Price: </span>
                  <span className="font-mono font-medium">{tasteParams.priceSensitivity.toFixed(1)}</span>
                </div>
                <div>
                  <span className="text-slate-500">Range: </span>
                  <span className="font-mono font-medium">{tasteParams.rangeAnxiety.toFixed(1)}</span>
                </div>
                <div>
                  <span className="text-slate-500">Env: </span>
                  <span className="font-mono font-medium">{tasteParams.envPreference.toFixed(1)}</span>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">Not configured</p>
            )}
          </div>

          {/* Calibration status */}
          <div className="p-3 bg-slate-50 rounded border border-slate-200">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-700">Calibration status</span>
              <Badge variant="outline" className={calibrationBadgeColor[calibrationState]}>
                {calibrationState.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())}
              </Badge>
            </div>
          </div>
        </div>

        {/* Calibration panel stub */}
        <CalibrationPanel />
      </div>
    );
  };

  const renderStepContent = () => {
    if (!isEnabled && activeStep > 0) {
      // If disabled and not on Enable step, show Enable step
      return renderEnableStep();
    }

    switch (activeStep) {
      case 0:
        return renderEnableStep();
      case 1:
        return renderModelStep();
      case 2:
        return renderParametersStep();
      case 3:
        return renderReviewStep();
      default:
        return null;
    }
  };

  const renderNavigation = () => {
    if (activeStep === 3) {
      // Review step has its own Edit buttons
      return null;
    }

    const canGoNext =
      activeStep === 0 ? isEnabled // Enable step: can proceed if enabled (will auto-advance)
      : activeStep === 1 ? engineConfig.logitModel !== null // Model step: require selection
      : true; // Parameters step: always can proceed

    return (
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-200">
        <Button
          variant="ghost"
          size="sm"
          onClick={handleBack}
          disabled={activeStep === 0}
          className="text-slate-600"
        >
          <ChevronLeft className="h-4 w-4 mr-1" />
          Back
        </Button>

        {activeStep < 3 && (
          <Button
            size="sm"
            onClick={handleNext}
            disabled={!canGoNext}
            className="bg-blue-500 hover:bg-blue-600 text-white"
          >
            {activeStep === 0 ? "Continue when enabled" : "Next"}
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        )}
      </div>
    );
  };

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <div className="space-y-4">
      {/* Step indicators */}
      {isEnabled && renderStepIndicators()}

      {/* Step content */}
      {renderStepContent()}

      {/* Navigation buttons */}
      {renderNavigation()}
    </div>
  );
}
