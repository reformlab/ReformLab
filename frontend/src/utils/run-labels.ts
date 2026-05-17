// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Run label helpers for policy/template/portfolio names.
 *
 * Story 27.10, AC-12.
 * Consolidates duplicate policyLabel helpers from ResultsListPanel and ResultDetailView.
 */

import type { ResultListItem, ResultDetailResponse } from "@/api/types";

/**
 * Returns a human-readable label for a run's policy/template/portfolio.
 *
 * Matches API types (ResultListItem, ResultDetailResponse) with snake_case field names.
 * Uses run_kind-aware fallback: "Portfolio run" vs "Scenario run".
 *
 * Consolidated behavior:
 * - ResultsListPanel.tsx: scenarioName || portfolioName || "Portfolio"/"Scenario"
 * - ResultDetailView.tsx: scenarioName || portfolioName || "Portfolio run"/"Scenario run"
 *
 * The reconciliation uses "Portfolio run" / "Scenario run" with " run" suffix.
 *
 * @example policyLabel({ portfolio_name: "Tax Reform A" }) // "Tax Reform A"
 * @example policyLabel({ template_name: "Carbon Tax" }) // "Carbon Tax"
 * @example policyLabel({ run_kind: "portfolio" }) // "Portfolio run"
 * @example policyLabel({ run_kind: "scenario" }) // "Scenario run"
 */
export function policyLabel(
  run: Pick<ResultListItem | ResultDetailResponse, "portfolio_name" | "template_name" | "run_kind">,
): string {
  if (run.portfolio_name) return run.portfolio_name;
  if (run.template_name) return run.template_name;
  return run.run_kind === "portfolio" ? "Portfolio run" : "Scenario run";
}
