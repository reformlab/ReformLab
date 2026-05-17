// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * @deprecated Use `usePortfolioDialog({ mode: "save", ... })` directly (Story 27.11).
 * This thin wrapper is provided for backward compatibility.
 */

import type { Category, CompositionEntry, PortfolioConflict } from "@/api/types";
import type { Template } from "@/data/mock-data";
import { usePortfolioDialog, type LoadedPortfolioRef, type SaveDialogState } from "./usePortfolioDialog";

export interface UsePortfolioSaveDialogParams {
  templates: Template[];
  composition: CompositionEntry[];
  resolutionStrategy: string;
  conflicts: PortfolioConflict[];
  loadedPortfolioRef: LoadedPortfolioRef;
  setActivePortfolioName: (name: string | null) => void;
  updateScenarioPortfolioName: (name: string | null) => void;
  setSelectedPortfolioName: (name: string | null) => void;
  refetchPortfolios: () => Promise<void>;
  onSavedSuccessfully?: () => void;
  categories?: Category[] | null;
}

/**
 * @deprecated Use `usePortfolioDialog({ mode: "save", ... })` directly.
 * Returns the same state as the unified hook's save mode.
 */
export function usePortfolioSaveDialog(params: UsePortfolioSaveDialogParams): SaveDialogState {
  return usePortfolioDialog("save", params);
}
