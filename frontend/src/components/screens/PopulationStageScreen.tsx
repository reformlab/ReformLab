// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PopulationStageScreen — Stage 2 wrapper (Story 20.1, AC-2).
 *
 * Thin wrapper that renders DataFusionWorkbench with props from AppContext.
 * Stage 2 (Population) is fully functional in this story.
 */

import { useAppState } from "@/contexts/AppContext";
import { DataFusionWorkbench } from "@/components/screens/DataFusionWorkbench";

export function PopulationStageScreen() {
  const { dataFusionSources, dataFusionMethods, dataFusionResult, setDataFusionResult } = useAppState();

  return (
    <DataFusionWorkbench
      sources={dataFusionSources}
      methods={dataFusionMethods}
      initialResult={dataFusionResult}
      onPopulationGenerated={setDataFusionResult}
    />
  );
}
