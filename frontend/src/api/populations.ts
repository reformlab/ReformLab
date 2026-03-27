// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Population dataset listing and explorer API functions. */

import { apiFetch } from "./client";
import type {
  PopulationLibraryItem,
  PopulationPreviewResponse,
  PopulationProfileResponse,
  PopulationCrosstabResponse,
  PopulationUploadResponse,
} from "./types";

/** List available population datasets.

Story 21.2 / AC2: Returns PopulationLibraryItem[] with dual-field evidence classification.
*/
export async function listPopulations(): Promise<PopulationLibraryItem[]> {
  const result = await apiFetch<{ populations: PopulationLibraryItem[] }>(
    "/api/populations",
  );
  return result.populations;
}

/** Get a paginated preview of population rows (first N rows with sort/filter). */
export async function getPopulationPreview(
  id: string,
  params?: { offset?: number; limit?: number; sort_by?: string; order?: "asc" | "desc" },
): Promise<PopulationPreviewResponse> {
  const query = new URLSearchParams();
  if (params?.offset !== undefined) query.set("offset", String(params.offset));
  if (params?.limit !== undefined) query.set("limit", String(params.limit));
  if (params?.sort_by) query.set("sort_by", params.sort_by);
  if (params?.order) query.set("order", params.order);
  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<PopulationPreviewResponse>(`/api/populations/${id}/preview${qs}`);
}

/** Get per-column profile statistics for a population. */
export async function getPopulationProfile(id: string): Promise<PopulationProfileResponse> {
  return apiFetch<PopulationProfileResponse>(`/api/populations/${id}/profile`);
}

/** Get cross-tabulation of two columns for a population. */
export async function getPopulationCrosstab(
  id: string,
  colA: string,
  colB: string,
): Promise<PopulationCrosstabResponse> {
  const query = new URLSearchParams({ col_a: colA, col_b: colB });
  return apiFetch<PopulationCrosstabResponse>(`/api/populations/${id}/crosstab?${query.toString()}`);
}

/** Upload a CSV or Parquet file as a new population dataset. */
export async function uploadPopulation(file: File): Promise<PopulationUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<PopulationUploadResponse>("/api/populations/upload", {
    method: "POST",
    body: formData,
  });
}

/** Delete a population dataset by ID. */
export async function deletePopulation(id: string): Promise<void> {
  await apiFetch<void>(`/api/populations/${id}`, { method: "DELETE" });
}
