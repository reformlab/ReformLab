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
  | "runner";

// ============================================================================
// Scenario types
// ============================================================================

// String type (not closed union) to allow EPIC-21 evidence-related states.
// Known values at this revision: "draft" | "ready" | "running" | "completed" | "failed"
export type ScenarioStatus = string;

export interface EngineConfig {
  startYear: number;
  endYear: number;
  seed: number | null;
  investmentDecisionsEnabled: boolean;
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
}

// ============================================================================
// Stage definitions — single source of truth
// ============================================================================

// Import this in WorkflowNavRail, TopBar, and tests.
export const STAGES: { key: StageKey; label: string; activeFor: string[] }[] = [
  { key: "policies",   label: "Policies & Portfolio",    activeFor: ["policies"] },
  { key: "population", label: "Population",              activeFor: ["population", "data-fusion", "population-explorer"] },
  { key: "engine",     label: "Engine",                  activeFor: ["engine"] },
  { key: "results",    label: "Run / Results / Compare", activeFor: ["results", "comparison", "decisions", "runner"] },
];

// ============================================================================
// Type guards
// ============================================================================

const VALID_STAGES = new Set<string>(["policies", "population", "engine", "results"]);
export function isValidStage(s: string): s is StageKey {
  return VALID_STAGES.has(s);
}

const VALID_SUBVIEWS = new Set<string>(["data-fusion", "population-explorer", "comparison", "decisions", "runner"]);
export function isValidSubView(s: string): s is SubView {
  return VALID_SUBVIEWS.has(s);
}
