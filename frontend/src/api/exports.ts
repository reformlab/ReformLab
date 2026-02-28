/** Export download trigger functions. */

import { apiFetchBlob } from "./client";
import type { ExportRequest } from "./types";

/** Trigger a browser file download from a Blob. */
function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/** Export a cached simulation result as CSV and trigger browser download. */
export async function exportCsv(runId: string): Promise<void> {
  const body: ExportRequest = { run_id: runId };
  const { blob, filename } = await apiFetchBlob("/api/exports/csv", {
    method: "POST",
    body: JSON.stringify(body),
  });
  triggerDownload(blob, filename);
}

/** Export a cached simulation result as Parquet and trigger browser download. */
export async function exportParquet(runId: string): Promise<void> {
  const body: ExportRequest = { run_id: runId };
  const { blob, filename } = await apiFetchBlob("/api/exports/parquet", {
    method: "POST",
    body: JSON.stringify(body),
  });
  triggerDownload(blob, filename);
}
