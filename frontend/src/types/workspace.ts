// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Canonical workspace type definitions for ReformLab.
 *
 * Defines the five-stage workspace model (Story 26.1, AC-1).
 * StageKey, SubView, WorkspaceScenario, EngineConfig, STAGES.
 *
 * Story 20.1 — FR32 stage-based GUI.
 * Story 26.1 — Migrate from four-stage to five-stage workspace.
 */

// ============================================================================
// Stage and routing types
// ============================================================================

export type StageKey = "policies" | "population" | "investment-decisions" | "scenario" | "results";

export type SubView =
  | "data-fusion"
  | "population-explorer"
  | "comparison"
  | "decisions"
  | "runner"
  | "manifest"; // Story 26.4

// ============================================================================
// Population sub-step types — Story 22.4
// ============================================================================

export type PopulationSubStep = "library" | "build" | "explorer";

export const POPULATION_SUB_STEPS = [
  { key: "library" as const, label: "Library", subView: null },
  { key: "build" as const, label: "Build", subView: "data-fusion" as const },
  { key: "explorer" as const, label: "Explorer", subView: "population-explorer" as const },
] as const;

// ============================================================================
// Scenario types
// ============================================================================

// String type (not closed union) to allow EPIC-21 evidence-related states.
// Known values at this revision: "draft" | "ready" | "running" | "completed" | "failed"
export type ScenarioStatus = string;

// ============================================================================
// Investment decisions types — Story 22.6
// ============================================================================

export interface TasteParameters {
  priceSensitivity: number;  // [-5, 0], default -1.5
  rangeAnxiety: number;      // [-3, 0], default -0.8
  envPreference: number;     // [0, 3], default 0.5
}

export type CalibrationState = "not_configured" | "in_progress" | "completed";

// Default taste parameters for new scenarios and migration
export const DEFAULT_TASTE_PARAMETERS: TasteParameters = {
  priceSensitivity: -1.5,
  rangeAnxiety: -0.8,
  envPreference: 0.5,
};

export interface EngineConfig {
  startYear: number;
  endYear: number;
  seed: number | null;
  investmentDecisionsEnabled: boolean;
  logitModel: "multinomial_logit" | "nested_logit" | "mixed_logit" | null;
  discountRate: number;  // fractional: 0.03 = 3%
  tasteParameters?: TasteParameters | null;  // Optional for backward compatibility
  calibrationState?: CalibrationState;  // Story 22.6; optional for persisted legacy scenarios
}

export interface WorkspaceScenario {
  id: string;                        // matches ScenarioResponse.name
  name: string;
  version: string;
  status: ScenarioStatus;
  isBaseline: boolean;
  baselineRef: string | null;
  portfolioName: string | null;      // references PortfolioListItem.name
  populationIds: string[];           // references PopulationItem.id
  engineConfig: EngineConfig;
  policyType: string | null;
  lastRunId: string | null;
  lastRunRuntimeMode?: "replay";  // Story 26.3: Historical runtime mode for replay badge. Only "replay" is stored; "live" is the default and never persisted.
}

// ============================================================================
// Stage definitions — single source of truth
// ============================================================================

// Import this in WorkflowNavRail, TopBar, and tests.
export const STAGES: { key: StageKey; label: string; activeFor: (StageKey | SubView)[] }[] = [
  { key: "policies",           label: "Policies",           activeFor: ["policies"] },
  { key: "population",         label: "Population",         activeFor: ["population", "data-fusion", "population-explorer"] },
  { key: "investment-decisions", label: "Investment Decisions", activeFor: ["investment-decisions"] },
  { key: "scenario",           label: "Scenario",           activeFor: ["scenario"] },
  { key: "results",            label: "Run / Results / Compare", activeFor: ["results", "comparison", "decisions", "runner", "manifest"] }, // Story 26.4: added "manifest"
];

// ============================================================================
// Type guards
// ============================================================================

const VALID_STAGES = new Set<string>(["policies", "population", "investment-decisions", "scenario", "results"]);
export function isValidStage(s: string): s is StageKey {
  return VALID_STAGES.has(s);
}

const VALID_SUBVIEWS = new Set<string>(["data-fusion", "population-explorer", "comparison", "decisions", "runner", "manifest"]); // Story 26.4: added "manifest"
export function isValidSubView(s: string): s is SubView {
  return VALID_SUBVIEWS.has(s);
}
