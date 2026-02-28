/** Indicator computation API functions. */

import { apiFetch } from "./client";
import type {
  ComparisonRequest,
  IndicatorRequest,
  IndicatorResponse,
  IndicatorType,
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
