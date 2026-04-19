// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** API client functions for the Data Fusion Workbench (Story 17.1). */

import { apiFetch } from "@/api/client";
import type {
  DataSourceDetail,
  DataSourceItem,
  GenerationRequest,
  GenerationResult,
  MergeMethodInfo,
  PopulationPreviewResponse,
  PopulationProfileResponse,
} from "@/api/types";

/** List all available data sources grouped by provider. */
export async function listDataSources(): Promise<Record<string, DataSourceItem[]>> {
  const response = await apiFetch<{ sources: Record<string, DataSourceItem[]> }>(
    "/api/data-fusion/sources",
  );
  return response.sources;
}

/** Get detail for a specific dataset including column schema. */
export async function getDataSourceDetail(
  provider: string,
  datasetId: string,
): Promise<DataSourceDetail> {
  return apiFetch<DataSourceDetail>(`/api/data-fusion/sources/${provider}/${datasetId}`);
}

/** List all available merge methods with plain-language descriptions. */
export async function listMergeMethods(): Promise<MergeMethodInfo[]> {
  const response = await apiFetch<{ methods: MergeMethodInfo[] }>("/api/data-fusion/merge-methods");
  return response.methods;
}

/** Get a paginated preview of data source rows. */
export async function getDataSourcePreview(
  provider: string,
  datasetId: string,
  params?: { offset?: number; limit?: number; sort_by?: string; order?: "asc" | "desc" },
): Promise<PopulationPreviewResponse> {
  const query = new URLSearchParams();
  if (params?.offset !== undefined) query.set("offset", String(params.offset));
  if (params?.limit !== undefined) query.set("limit", String(params.limit));
  if (params?.sort_by) query.set("sort_by", params.sort_by);
  if (params?.order) query.set("order", params.order);
  const qs = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<PopulationPreviewResponse>(
    `/api/data-fusion/sources/${provider}/${datasetId}/preview${qs}`,
  );
}

/** Get per-column profile statistics for a data source. */
export async function getDataSourceProfile(
  provider: string,
  datasetId: string,
): Promise<PopulationProfileResponse> {
  return apiFetch<PopulationProfileResponse>(
    `/api/data-fusion/sources/${provider}/${datasetId}/profile`,
  );
}

/** Execute the population generation pipeline and return the result. */
export async function generatePopulation(request: GenerationRequest): Promise<GenerationResult> {
  return apiFetch<GenerationResult>("/api/data-fusion/generate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
