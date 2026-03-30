// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Exogenous time series asset API functions — Story 21.6, AC9. */

import { apiFetch } from "./client";
import type {
  ExogenousAssetRequest,
  ExogenousAssetResponse,
  ExogenousFilters,
} from "./types";

/**
 * List all available exogenous time series assets.
 *
 * Story 21.6 / AC8.
 *
 * @param filters - Optional filters for origin, unit, or source
 * @returns List of exogenous assets
 */
export async function listExogenousSeries(
  filters?: ExogenousFilters,
): Promise<ExogenousAssetResponse[]> {
  const params = new URLSearchParams();
  if (filters?.origin) {
    params.append("origin", filters.origin);
  }
  if (filters?.unit) {
    params.append("unit", filters.unit);
  }
  if (filters?.source) {
    params.append("source", filters.source);
  }

  const query = params.toString();
  const url = `/api/exogenous/series${query ? `?${query}` : ""}`;

  return apiFetch<ExogenousAssetResponse[]>(url);
}

/**
 * Get a specific exogenous time series asset by name.
 *
 * Story 21.6 / AC8.
 *
 * @param seriesName - The series name (e.g., "energy_price_electricity")
 * @returns The requested exogenous asset
 */
export async function getExogenousSeries(
  seriesName: string,
): Promise<ExogenousAssetResponse> {
  return apiFetch<ExogenousAssetResponse>(
    `/api/exogenous/series/${encodeURIComponent(seriesName)}`,
  );
}

/**
 * Create a new exogenous time series asset.
 *
 * Story 21.6 / AC8.
 *
 * @param request - The asset creation request
 * @returns The created asset
 */
export async function createExogenousSeries(
  request: ExogenousAssetRequest,
): Promise<ExogenousAssetResponse> {
  return apiFetch<ExogenousAssetResponse>("/api/exogenous/series", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
