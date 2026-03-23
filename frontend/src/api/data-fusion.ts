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

/** Execute the population generation pipeline and return the result. */
export async function generatePopulation(request: GenerationRequest): Promise<GenerationResult> {
  return apiFetch<GenerationResult>("/api/data-fusion/generate", {
    method: "POST",
    body: JSON.stringify(request),
  });
}
