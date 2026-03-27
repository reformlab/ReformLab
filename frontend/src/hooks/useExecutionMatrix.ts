// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** useExecutionMatrix hook — Story 20.6, Task 20.6.7.
 *
 * Provides access to the execution matrix state from AppContext.
 * The matrix is a Record<string, Record<string, ExecutionMatrixCell>>
 * where the outer key is scenarioId and inner key is populationId.
 */

import { useContext } from "react";
import { AppContext } from "@/contexts/AppContext";
import type { ExecutionMatrixCell } from "@/api/types";

export interface UseExecutionMatrixReturn {
  matrix: Record<string, Record<string, ExecutionMatrixCell>>;
  updateCell: (scenarioId: string, populationId: string, update: Partial<ExecutionMatrixCell>) => void;
  refreshMatrix: () => Promise<void>;
}

/**
 * Hook to access and manage the execution matrix state.
 * The matrix tracks execution status for scenario-by-population combinations.
 */
export function useExecutionMatrix(): UseExecutionMatrixReturn {
  const { executionMatrix, updateExecutionCell } = useContext(AppContext);

  /**
   * Refresh the matrix by fetching from the API.
   * Note: This requires backend Task 20.6.6 to be complete
   * so that /api/results returns scenario_id and population_id.
   */
  const refreshMatrix = async (): Promise<void> => {
    // TODO: Implement matrix refresh from /api/results
    // This requires backend to return scenario_id and population_id in result metadata
    // For now, the matrix is only updated via updateExecutionCell during runs
  };

  return {
    matrix: executionMatrix,
    updateCell: updateExecutionCell,
    refreshMatrix,
  };
}
