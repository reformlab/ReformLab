// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * @deprecated Use `usePortfolioDialog({ mode: "load", ... })` directly (Story 27.11).
 * This thin wrapper is provided for backward compatibility.
 */

import type { CompositionEntry } from "@/api/types";
import type { Template } from "@/data/mock-data";
import { usePortfolioDialog, type LoadedPortfolioRef, type LoadDialogState } from "./usePortfolioDialog";

export interface UsePortfolioLoadDialogParams<ResolutionStrategy extends string> {
  templates: Template[];
  activeScenarioPortfolioName: string | null | undefined;
  compositionLength: number;
  validStrategies: readonly ResolutionStrategy[];
  defaultResolutionStrategy: ResolutionStrategy;
  loadedPortfolioRef: LoadedPortfolioRef;
  setComposition: (composition: CompositionEntry[]) => void;
  setResolutionStrategy: (strategy: ResolutionStrategy) => void;
  setActivePortfolioName: (name: string | null) => void;
  updateScenarioPortfolioName: (name: string | null) => void;
  setSelectedPortfolioName: (name: string | null) => void;
  setInstanceCounter?: (value: number) => void;
  onLoadedSuccessfully?: () => void;
}

/**
 * @deprecated Use `usePortfolioDialog({ mode: "load", ... })` directly.
 * Returns the same state as the unified hook's load mode.
 */
export function usePortfolioLoadDialog<ResolutionStrategy extends string>(
  params: UsePortfolioLoadDialogParams<ResolutionStrategy>,
): LoadDialogState {
  return usePortfolioDialog("load", params);
}
