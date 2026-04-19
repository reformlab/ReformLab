// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PopulationUploadZone — drag-and-drop file upload with schema validation report.
 *
 * Story 20.4 AC-4 acceptance mode: schema validation is client-side (no backend).
 * The real upload path (POST /api/populations/upload) is wired in Story 20.7.
 *
 * Story 20.4 — AC-4.
 */

import { useEffect, useRef, useState } from "react";
import { Upload, X, FileSpreadsheet, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { PopulationLibraryItem, PopulationUploadResponse } from "@/api/types";

// ============================================================================
// Constants
// ============================================================================

/** Minimum required columns for a valid ReformLab population dataset. */
const REQUIRED_COLUMNS = ["household_id", "income", "region", "household_size"];

// ============================================================================
// Types
// ============================================================================

export interface PopulationUploadZoneProps {
  onClose: () => void;
  onConfirm: (population: PopulationLibraryItem) => void;
}

type UploadState = "idle" | "dragging" | "processing" | "validated" | "error";

// ============================================================================
// Client-side schema validation (Story 20.4 mode — no backend)
// ============================================================================

async function readCsvHeader(file: File): Promise<string[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const firstLine = text.split("\n")[0] ?? "";
      const cols = firstLine
        .split(",")
        .map((c) => c.trim().replace(/^["']|["']$/g, "").toLowerCase());
      resolve(cols);
    };
    reader.onerror = () => { reject(new Error("Failed to read file")); };
    reader.readAsText(file.slice(0, 4096)); // Only read first 4KB for header
  });
}

async function simulateSchemaValidation(file: File): Promise<PopulationUploadResponse> {
  let columns: string[] = [];

  if (file.name.endsWith(".csv")) {
    try {
      columns = await readCsvHeader(file);
    } catch {
      columns = [];
    }
  } else if (file.name.endsWith(".parquet")) {
    // Client-side Parquet schema parsing is not supported in Story 20.4 mode.
    // Assume the file is valid; Story 20.7 performs real schema validation via the API.
    return {
      id: `uploaded-${Date.now()}`,
      name: file.name.replace(/\.(csv|parquet)$/i, ""),
      row_count: Math.floor(file.size / 150),
      column_count: 0,
      matched_columns: [],
      unrecognized_columns: [],
      missing_required: [],
      valid: true,
    };
  }

  const matched = REQUIRED_COLUMNS.filter((rc) => columns.includes(rc));
  const missing = REQUIRED_COLUMNS.filter((rc) => !columns.includes(rc));
  const unrecognized = columns.filter(
    (c) => c !== "" && !REQUIRED_COLUMNS.includes(c),
  );

  const estimatedRows = Math.floor(file.size / 100); // rough estimate

  return {
    id: `uploaded-${Date.now()}`,
    name: file.name.replace(/\.(csv|parquet)$/i, ""),
    row_count: estimatedRows,
    column_count: columns.length || 0,
    matched_columns: matched,
    unrecognized_columns: unrecognized,
    missing_required: missing,
    valid: missing.length === 0,
  };
}

// ============================================================================
// Validation report
// ============================================================================

function ValidationReport({ report }: { report: PopulationUploadResponse }) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
      <div className="flex items-center gap-3">
        <FileSpreadsheet className="h-5 w-5 text-slate-500" />
        <div>
          <p className="text-sm font-semibold text-slate-900">{report.name}</p>
          <p className="text-xs text-slate-400">
            ~{report.row_count.toLocaleString()} rows · {report.column_count} columns
          </p>
        </div>
      </div>

      {/* Matched columns */}
      {report.matched_columns.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-medium text-slate-600">
            <CheckCircle2 className="mr-1 inline h-3 w-3 text-green-500" />
            Matched columns ({report.matched_columns.length})
          </p>
          <div className="flex flex-wrap gap-1">
            {report.matched_columns.map((c) => (
              <Badge key={c} variant="secondary" className="text-[10px] text-green-700 bg-green-50">
                {c}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Unrecognized columns */}
      {report.unrecognized_columns.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-medium text-slate-600">
            <AlertTriangle className="mr-1 inline h-3 w-3 text-amber-500" />
            Unrecognized columns ({report.unrecognized_columns.length})
            <span className="ml-1 text-slate-400">— will be kept but not used</span>
          </p>
          <div className="flex flex-wrap gap-1">
            {report.unrecognized_columns.map((c) => (
              <Badge key={c} variant="outline" className="text-[10px] text-amber-700 border-amber-200">
                {c}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Missing required columns */}
      {report.missing_required.length > 0 && (
        <div>
          <p className="mb-1 text-xs font-medium text-red-600">
            <XCircle className="mr-1 inline h-3 w-3 text-red-500" />
            Missing required columns ({report.missing_required.length}) — upload blocked
          </p>
          <div className="flex flex-wrap gap-1">
            {report.missing_required.map((c) => (
              <Badge key={c} variant="secondary" className="text-[10px] text-red-700 bg-red-50">
                {c}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main component
// ============================================================================

export function PopulationUploadZone({ onClose, onConfirm }: PopulationUploadZoneProps) {
  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [report, setReport] = useState<PopulationUploadResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Close on Escape
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  async function processFile(file: File) {
    if (!file.name.match(/\.(csv|parquet)$/i)) {
      setErrorMsg("Only .csv and .parquet files are accepted.");
      setUploadState("error");
      return;
    }
    setUploadState("processing");
    try {
      const result = await simulateSchemaValidation(file);
      setReport(result);
      setUploadState("validated");
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Validation failed");
      setUploadState("error");
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setUploadState("idle");
    const file = e.dataTransfer.files[0];
    if (file) void processFile(file);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) void processFile(file);
  }

  function handleConfirm() {
    if (!report || !report.valid) return;
    const population: PopulationLibraryItem = {
      id: report.id,
      name: report.name,
      households: report.row_count,
      source: "upload",
      year: new Date().getFullYear(),
      origin: "uploaded",
      // Story 21.2 / AC3: Canonical evidence fields for uploaded populations
      canonical_origin: "synthetic-public",
      access_mode: "bundled",
      trust_status: "exploratory",
      column_count: report.column_count,
      created_date: new Date().toISOString(),
      is_synthetic: true,
    };
    onConfirm(population);
  }

  function handleReset() {
    setReport(null);
    setUploadState("idle");
    setErrorMsg("");
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-label="Upload population">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/30" onClick={onClose} aria-hidden="true" />

      {/* Panel */}
      <div className="relative z-10 flex w-full max-w-lg flex-col gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900">Upload Population</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close upload"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {uploadState !== "validated" && uploadState !== "error" && (
          <>
            {/* Drop zone */}
            <div
              className={`flex flex-col items-center gap-3 rounded-lg border-2 border-dashed p-10 text-center transition-colors ${
                uploadState === "dragging"
                  ? "border-blue-500 bg-blue-50"
                  : "border-slate-300 bg-slate-50 hover:border-slate-400"
              }`}
              onDragOver={(e) => { e.preventDefault(); setUploadState("dragging"); }}
              onDragLeave={() => { setUploadState("idle"); }}
              onDrop={handleDrop}
              aria-label="Drop zone for population file"
            >
              {uploadState === "processing" ? (
                <>
                  <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-blue-500" />
                  <p className="text-sm text-slate-500">Validating file…</p>
                </>
              ) : (
                <>
                  <Upload className="h-8 w-8 text-slate-400" />
                  <div>
                    <p className="text-sm font-medium text-slate-700">
                      Drop a file here, or{" "}
                      <button
                        type="button"
                        className="text-blue-600 underline hover:text-blue-700"
                        onClick={() => { fileInputRef.current?.click(); }}
                      >
                        browse
                      </button>
                    </p>
                    <p className="mt-1 text-xs text-slate-400">.csv or .parquet only</p>
                  </div>
                </>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.parquet"
              className="hidden"
              onChange={handleFileChange}
            />
          </>
        )}

        {/* Validation report */}
        {uploadState === "validated" && report && (
          <ValidationReport report={report} />
        )}

        {/* Error state */}
        {uploadState === "error" && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {errorMsg}
          </div>
        )}

        {/* Action buttons */}
        {(uploadState === "validated" || uploadState === "error") && (
          <div className="flex justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={handleReset}>
              Choose different file
            </Button>
            <Button variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            {uploadState === "validated" && report && (
              <Button
                size="sm"
                disabled={!report.valid}
                onClick={handleConfirm}
                title={!report.valid ? "Missing required columns — cannot upload" : undefined}
              >
                Add to Library
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
