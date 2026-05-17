// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Canonical workspace type definitions for ReformLab.
 *
 * Defines the four-stage workspace model (Story 20.1, AC-3).
 * StageKey, SubView, WorkspaceScenario, EngineConfig, STAGES.
 *
 * Story 20.1 — FR32 stage-based GUI.
 */

// ============================================================================
// Stage and routing types
// ============================================================================

export type StageKey = "policies" | "population" | "engine" | "results";

export type SubView =
  | "data-fusion"
  | "population-explorer"
  | "comparison"
  | "decisions"
  | "runner"
  | "source"  // Story 27.8: New Source sub-view for Population
  | "inspect"; // Story 27.8: New Inspect sub-view for Population

// ============================================================================
// Population sub-step types — Story 27.8 (restructured from Story 22.4)
// ============================================================================

export type PopulationSubStep = "source" | "inspect";

export const POPULATION_SUB_STEPS = [
  { key: "source" as const, label: "Source", subView: null as const | "source" },
  { key: "inspect" as const, label: "Inspect", subView: "inspect" as const },
] as const;

// ============================================================================
// Legacy sub-view migration — Story 27.8
// ============================================================================

/** Maps legacy Population sub-view values to new values.
 *
 * Story 27.8: Used for URL hash migration and activeSubView migration.
 * - Empty string (null sub-view) → "source" (Library default)
 * - "data-fusion" (Build) → "source" (Build is within Source)
 * - "population-explorer" (Explorer) → "inspect"
 *
 * Note: Object keys are always strings, so we use "" for null.
 */
export const LEGACY_POPULATION_SUBVIEW_MAP: Record<string, SubView> = {
  "": "source",
  "data-fusion": "source",
  "population-explorer": "inspect",
};

// ============================================================================
// Scenario types
// ============================================================================

// String type (not closed union) to allow EPIC-21 evidence-related states.
// Known values at this revision: "draft" | "ready" | "running" | "completed" | "failed"
export type ScenarioStatus = string;

// ============================================================================
// Investment decisions types — Story 22.6
// ============================================================================

// Story 28.1 / AC-1: Technology set types for investment decisions
export type DecisionDomainKey = "heating" | "vehicle";

export interface TechnologyAlternative {
  id: string;
  name: string;
  attributes: Record<string, string | number>;
  isIncumbentOnly?: boolean;
}

export interface DomainTechnologySet {
  domain: DecisionDomainKey;
  enabled: boolean;
  alternatives: TechnologyAlternative[];
  referenceAlternativeId: string | null;
  costColumn?: string;
}

export interface TechnologySet {
  version: string;
  domains: Partial<Record<DecisionDomainKey, DomainTechnologySet>>;
}

// Default technology set constant for legacy migration — Story 28.1 / AC-4, AC-7
export const DEFAULT_TECHNOLOGY_SET: TechnologySet = {
  version: "fr-default-2026-04-26",
  domains: {
    heating: {
      domain: "heating",
      enabled: true,
      alternatives: [
        { id: "keep_current", name: "Keep Current System", attributes: {}, isIncumbentOnly: true },
        { id: "condensing_boiler", name: "Condensing Boiler", attributes: {}, isIncumbentOnly: false },
        { id: "heat_pump_air", name: "Air Source Heat Pump", attributes: {}, isIncumbentOnly: false },
        { id: "heat_pump_ground", name: "Ground Source Heat Pump", attributes: {}, isIncumbentOnly: false },
        { id: "district_heating", name: "District Heating", attributes: {}, isIncumbentOnly: false },
      ],
      referenceAlternativeId: "keep_current",
      costColumn: "heating_cost",
    },
    vehicle: {
      domain: "vehicle",
      enabled: true,
      alternatives: [
        { id: "keep_current", name: "Keep Current Vehicle", attributes: {}, isIncumbentOnly: true },
        { id: "petrol", name: "Petrol Car", attributes: {}, isIncumbentOnly: false },
        { id: "diesel", name: "Diesel Car", attributes: {}, isIncumbentOnly: false },
        { id: "hybrid", name: "Hybrid Car", attributes: {}, isIncumbentOnly: false },
        { id: "ev", name: "Electric Vehicle", attributes: {}, isIncumbentOnly: false },
        { id: "plug_in_hybrid", name: "Plug-in Hybrid", attributes: {}, isIncumbentOnly: false },
      ],
      referenceAlternativeId: "keep_current",
      costColumn: "total_vehicle_cost",
    },
  },
};

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
  investmentDecisionsEnabled: boolean | null;  // Story 27.6: null = not started, false = explicitly skipped, true = enabled
  logitModel: "multinomial_logit" | "nested_logit" | "mixed_logit" | null;
  discountRate: number;  // fractional: 0.03 = 3%
  tasteParameters?: TasteParameters | null;  // Optional for backward compatibility
  calibrationState?: CalibrationState;  // Story 22.6; optional for persisted legacy scenarios
  // Story 28.1 / AC-1: Technology set for investment decisions
  technologySet?: TechnologySet | null;
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
  stageTouched?: Partial<Record<StageKey, boolean>>;  // Story 27.6: tracks which stages user has explicitly interacted with
}

// ============================================================================
// Stage definitions — single source of truth
// ============================================================================

// Import this in WorkflowNavRail, TopBar, and tests.
export const STAGES: { key: StageKey; label: string; activeFor: (StageKey | SubView)[] }[] = [
  { key: "policies",   label: "Policy",    activeFor: ["policies"] },
  { key: "population", label: "Population", activeFor: ["population", "data-fusion", "population-explorer", "source", "inspect"] }, // Story 27.8: added source, inspect
  { key: "engine",     label: "Scenario",  activeFor: ["engine"] },
  { key: "results",    label: "Run / Results / Compare", activeFor: ["results", "comparison", "decisions", "runner"] },
];

// ============================================================================
// Type guards
// ============================================================================

const VALID_STAGES = new Set<string>(["policies", "population", "engine", "results"]);
export function isValidStage(s: string): s is StageKey {
  return VALID_STAGES.has(s);
}

const VALID_SUBVIEWS = new Set<string>([
  "data-fusion",
  "population-explorer",
  "comparison",
  "decisions",
  "runner",
  "source",   // Story 27.8
  "inspect", // Story 27.8
]);
export function isValidSubView(s: string): s is SubView {
  return VALID_SUBVIEWS.has(s);
}

// ============================================================================
// Type guards for technology set — Story 28.1
// ============================================================================

export function hasTechnologySet(config: EngineConfig): config is EngineConfig & { technologySet: TechnologySet } {
  if (!config.technologySet) return false;

  // Validate structure: must have version and at least one domain
  const ts = config.technologySet;
  if (typeof ts.version !== "string" || !ts.version) return false;
  if (!ts.domains || typeof ts.domains !== "object") return false;

  const domainKeys = Object.keys(ts.domains);
  if (domainKeys.length === 0) return false;

  // Validate at least one domain has required structure
  return domainKeys.some((key) => {
    const domain = ts.domains[key as DecisionDomainKey];
    return (
      domain &&
      typeof domain.enabled === "boolean" &&
      Array.isArray(domain.alternatives)
    );
  });
}
