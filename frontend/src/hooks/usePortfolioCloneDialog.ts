// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * @deprecated Use `usePortfolioDialog({ mode: "clone", ... })` directly (Story 27.11).
 * This thin wrapper is provided for backward compatibility.
 */

import type { PortfolioListItem } from "@/api/types";
import { usePortfolioDialog, type CloneDialogState } from "./usePortfolioDialog";

export interface UsePortfolioCloneDialogParams {
  portfolios: PortfolioListItem[];
  refetchPortfolios: () => Promise<void>;
}

/**
 * @deprecated Use `usePortfolioDialog({ mode: "clone", ... })` directly.
 * Returns the same state as the unified hook's clone mode.
 */
export function usePortfolioCloneDialog(params: UsePortfolioCloneDialogParams): CloneDialogState {
  return usePortfolioDialog("clone", params);
}
