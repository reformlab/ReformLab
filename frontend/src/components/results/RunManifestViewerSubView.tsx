// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Run Manifest Viewer Sub-View — Story 26.4, AC-3.
 *
 * Wrapper component that fetches manifest data and passes it to RunManifestViewer.
 * Handles loading, error, and empty states.
 */

import { useEffect, useState } from "react";

import { RunManifestViewer } from "@/components/results/RunManifestViewer";
import { getManifest } from "@/api/results";
import type { ManifestResponse } from "@/api/types";

export interface RunManifestViewerSubViewProps {
  runId: string | null;
  onBack: () => void;
}

export function RunManifestViewerSubView({ runId, onBack }: RunManifestViewerSubViewProps) {
  const [manifest, setManifest] = useState<ManifestResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) {
      setError("No run ID provided");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    getManifest(runId)
      .then((data) => {
        setManifest(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load manifest:", err);
        setError(err instanceof Error ? err.message : "Failed to load manifest");
        setLoading(false);
      });
  }, [runId]);

  return (
    <div className="max-w-4xl mx-auto py-6">
      <div className="mb-4">
        <button
          onClick={onBack}
          className="text-sm text-slate-600 hover:text-slate-900 flex items-center gap-1"
        >
          ← Back to results
        </button>
      </div>
      <RunManifestViewer manifest={manifest} loading={loading} error={error} onClose={onBack} />
    </div>
  );
}
