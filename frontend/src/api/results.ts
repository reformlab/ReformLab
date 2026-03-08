/** Result persistence API functions — Story 17.3. */

import { apiFetch } from "./client";
import type { ResultDetailResponse, ResultListItem } from "./types";

/** List all saved simulation results in reverse chronological order. */
export async function listResults(): Promise<ResultListItem[]> {
  return apiFetch<ResultListItem[]>("/api/results");
}

/** Get the full detail for a single saved simulation result. */
export async function getResult(runId: string): Promise<ResultDetailResponse> {
  return apiFetch<ResultDetailResponse>(`/api/results/${runId}`);
}

/** Delete a saved simulation result from the persistent store. */
export async function deleteResult(runId: string): Promise<void> {
  await apiFetch<void>(`/api/results/${runId}`, { method: "DELETE" });
}

/** Download the panel data for a run as a CSV file. */
export async function exportResultCsv(runId: string): Promise<void> {
  const url = `/api/results/${runId}/export/csv`;
  // Use native fetch with auth header via apiFetch pattern (raw download)
  const { getAuthToken } = await import("./client");
  const token = getAuthToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(url, { headers });
  if (!response.ok) {
    const data = (await response.json()) as { detail?: { what?: string; why?: string; fix?: string } };
    const detail = data.detail ?? {};
    throw new Error(detail.what ?? `Export failed (${response.status})`);
  }

  const blob = await response.blob();
  const anchor = document.createElement("a");
  anchor.href = URL.createObjectURL(blob);
  anchor.download = `${runId}.csv`;
  anchor.click();
  URL.revokeObjectURL(anchor.href);
}

/** Download the panel data for a run as a Parquet file. */
export async function exportResultParquet(runId: string): Promise<void> {
  const url = `/api/results/${runId}/export/parquet`;
  const { getAuthToken } = await import("./client");
  const token = getAuthToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const response = await fetch(url, { headers });
  if (!response.ok) {
    const data = (await response.json()) as { detail?: { what?: string; why?: string; fix?: string } };
    const detail = data.detail ?? {};
    throw new Error(detail.what ?? `Export failed (${response.status})`);
  }

  const blob = await response.blob();
  const anchor = document.createElement("a");
  anchor.href = URL.createObjectURL(blob);
  anchor.download = `${runId}.parquet`;
  anchor.click();
  URL.revokeObjectURL(anchor.href);
}
