// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Investment decisions toggle with inline accordion.
 *
 * Renders a Switch toggle. When enabled, expands inline to show logit model
 * selector, taste parameter sliders (local state only — not persisted to
 * EngineConfig in Story 20.5), and CalibrationPanel stub.
 *
 * Story 20.5 — AC-1.
 */

import { useState } from "react";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { CalibrationPanel } from "./CalibrationPanel";
import type { EngineConfig } from "@/types/workspace";

// ============================================================================
// Types
// ============================================================================

interface InvestmentDecisionsAccordionProps {
  config: EngineConfig;
  onEngineConfigChange: (config: EngineConfig) => void;
}

// ============================================================================
// Taste parameter defaults (local state only — not persisted in Story 20.5)
// ============================================================================

interface TasteParams {
  priceSensitivity: number;  // β_price: [-5, 0], default -1.5
  rangeAnxiety: number;      // β_range: [-3, 0], default -0.8
  envPreference: number;     // β_green: [0, 3], default 0.5
}

const DEFAULT_TASTE_PARAMS: TasteParams = {
  priceSensitivity: -1.5,
  rangeAnxiety: -0.8,
  envPreference: 0.5,
};

// ============================================================================
// Component
// ============================================================================

export function InvestmentDecisionsAccordion({ config, onEngineConfigChange }: InvestmentDecisionsAccordionProps) {
  // TODO(Story 20.6+): persist taste params to EngineConfig
  const [tasteParams, setTasteParams] = useState<TasteParams>(DEFAULT_TASTE_PARAMS);

  const handleToggle = (enabled: boolean) => {
    onEngineConfigChange({
      ...config,
      investmentDecisionsEnabled: enabled,
      logitModel: enabled ? "multinomial_logit" : null,
    });
  };

  return (
    <div className="space-y-3">
      {/* Toggle row */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-900">Investment Decisions</p>
          <p className="text-xs text-slate-500">Model household technology adoption</p>
        </div>
        <Switch
          checked={config.investmentDecisionsEnabled}
          onChange={(e) => handleToggle(e.target.checked)}
          aria-label="Toggle investment decisions"
        />
      </div>

      {/* Accordion content — visible when enabled */}
      {config.investmentDecisionsEnabled && (
        <div className="pl-3 border-l-2 border-slate-200 space-y-4">
          {/* Logit model selector */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-600">Logit model</label>
            <select
              className="w-full rounded border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-slate-400"
              value={config.logitModel ?? "multinomial_logit"}
              onChange={(e) => onEngineConfigChange({
                ...config,
                logitModel: e.target.value as EngineConfig["logitModel"],
              })}
              aria-label="Logit model"
            >
              <option value="multinomial_logit">Multinomial Logit</option>
              <option value="nested_logit">Nested Logit</option>
              <option value="mixed_logit">Mixed Logit</option>
            </select>
          </div>

          {/* Taste parameter sliders */}
          <div className="space-y-3">
            <p className="text-xs font-medium text-slate-600">Taste parameters</p>

            {/* β_price */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-slate-600">
                <span>Price sensitivity (β_price)</span>
                <span className="font-mono">{tasteParams.priceSensitivity.toFixed(1)}</span>
              </div>
              <Slider
                min={-5}
                max={0}
                step={0.1}
                value={[tasteParams.priceSensitivity]}
                onValueChange={([v]) => setTasteParams((p) => ({ ...p, priceSensitivity: v! }))}
                aria-label="Price sensitivity"
              />
            </div>

            {/* β_range */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-slate-600">
                <span>Range anxiety (β_range)</span>
                <span className="font-mono">{tasteParams.rangeAnxiety.toFixed(1)}</span>
              </div>
              <Slider
                min={-3}
                max={0}
                step={0.1}
                value={[tasteParams.rangeAnxiety]}
                onValueChange={([v]) => setTasteParams((p) => ({ ...p, rangeAnxiety: v! }))}
                aria-label="Range anxiety"
              />
            </div>

            {/* β_green */}
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-slate-600">
                <span>Environmental preference (β_green)</span>
                <span className="font-mono">{tasteParams.envPreference.toFixed(1)}</span>
              </div>
              <Slider
                min={0}
                max={3}
                step={0.1}
                value={[tasteParams.envPreference]}
                onValueChange={([v]) => setTasteParams((p) => ({ ...p, envPreference: v! }))}
                aria-label="Environmental preference"
              />
            </div>
          </div>

          {/* Calibration panel stub */}
          <CalibrationPanel />
        </div>
      )}
    </div>
  );
}
