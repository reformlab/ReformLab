// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PoliciesStageScreen — Stage 1 wrapper (Story 20.1, AC-2).
 *
 * Thin wrapper that renders PortfolioDesignerScreen with props from AppContext.
 * Stage 1 (Policies & Portfolio) is fully functional in this story.
 */

import { useAppState } from "@/contexts/AppContext";
import { PortfolioDesignerScreen } from "@/components/screens/PortfolioDesignerScreen";

export function PoliciesStageScreen() {
  const { templates, portfolios, refetchPortfolios } = useAppState();

  return (
    <PortfolioDesignerScreen
      templates={templates}
      savedPortfolios={portfolios}
      onSaved={() => { void refetchPortfolios(); }}
      onDeleted={() => { void refetchPortfolios(); }}
    />
  );
}
