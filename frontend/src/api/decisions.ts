// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Decision outcome summary API functions — Story 17.5. */

import { apiFetch } from "./client";
import type { DecisionSummaryRequest, DecisionSummaryResponse } from "./types";

/** Fetch aggregate behavioral decision outcomes for a simulation run. */
export async function getDecisionSummary(
  request: DecisionSummaryRequest,
): Promise<DecisionSummaryResponse> {
  return apiFetch<DecisionSummaryResponse>("/api/decisions/summary", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
