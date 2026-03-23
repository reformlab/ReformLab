// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Indicator computation API functions. */

import { apiFetch } from "./client";
import type {
  ComparisonRequest,
  IndicatorRequest,
  IndicatorResponse,
  IndicatorType,
  PortfolioComparisonRequest,
  PortfolioComparisonResponse,
} from "./types";

/** Compute an indicator from a cached simulation result. */
export async function getIndicators(
  type: IndicatorType,
  request: IndicatorRequest,
): Promise<IndicatorResponse> {
  return apiFetch<IndicatorResponse>(`/api/indicators/${type}`, {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/** Compute welfare comparison between baseline and reform runs. */
export async function compareScenarios(
  request: ComparisonRequest,
): Promise<IndicatorResponse> {
  return apiFetch<IndicatorResponse>("/api/comparison", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

/** Compare multiple portfolio simulation runs side-by-side. */
export async function comparePortfolios(
  request: PortfolioComparisonRequest,
): Promise<PortfolioComparisonResponse> {
  return apiFetch<PortfolioComparisonResponse>("/api/comparison/portfolios", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
