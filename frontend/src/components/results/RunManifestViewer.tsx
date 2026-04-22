// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Run Manifest Viewer — Story 26.4, AC-2, AC-4, AC-6.
 *
 * Comprehensive display of run reproducibility metadata organized into
 * collapsible sections: Overview, Execution, Policy, Data Provenance,
 * Lineage, Evidence, Warnings.
 */

import React from "react";
import { FileText, Hash, AlertTriangle, ChevronDown, ChevronRight } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Skeleton } from "@/components/ui/skeleton";
import type { ManifestResponse } from "@/api/types";

// ============================================================================
// Types
// ============================================================================

export interface RunManifestViewerProps {
  manifest: ManifestResponse | null;
  loading?: boolean;
  error?: string | null;
  onClose?: () => void;
}

// ============================================================================
// Helpers
// ============================================================================

function formatTs(ts: string): string {
  try {
    return new Date(ts).toLocaleString(undefined, {
      year: "numeric",
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return ts;
  }
}

function truncateHash(hash: string): string {
  return hash.length > 16 ? `${hash.slice(0, 8)}...${hash.slice(-8)}` : hash;
}

function safeStringify(value: unknown): string {
  try {
    return JSON.stringify(value);
  } catch {
    return "(unserializable value)";
  }
}

function runtimeModeBadge(mode: "live" | "replay" | "") {
  if (!mode) return null;
  const variant = mode === "live" ? "success" : "warning";
  const label = mode === "live" ? "Live OpenFisca" : "Replay";
  return (
    <Badge variant={variant} className="text-xs">
      {label}
    </Badge>
  );
}

function populationSourceBadge(source: "bundled" | "uploaded" | "generated" | null) {
  if (!source) return null;
  const colors = {
    bundled: "bg-blue-100 text-blue-800 border-blue-200",
    uploaded: "bg-amber-100 text-amber-800 border-amber-200",
    generated: "bg-purple-100 text-purple-800 border-purple-200",
  };
  return (
    <Badge variant="outline" className={`text-xs ${colors[source] || ""}`}>
      {source}
    </Badge>
  );
}

function hasEntries(value: Record<string, unknown>): boolean {
  return Object.keys(value).length > 0;
}

// ============================================================================
// Section Components
// ============================================================================

interface ManifestSectionProps {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

function ManifestSection({ title, icon, defaultOpen = true, children }: ManifestSectionProps) {
  const [open, setOpen] = React.useState(defaultOpen);

  return (
    <Collapsible
      open={open}
      onOpenChange={setOpen}
      className="border border-slate-200 rounded-lg bg-white"
    >
      <CollapsibleTrigger className="flex items-center justify-between w-full px-3 py-2 hover:bg-slate-50 transition-colors">
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-sm font-semibold text-slate-900">{title}</span>
        </div>
        {open ? <ChevronDown className="h-4 w-4 text-slate-400" /> : <ChevronRight className="h-4 w-4 text-slate-400" />}
      </CollapsibleTrigger>
      <CollapsibleContent className="px-3 pb-3">{children}</CollapsibleContent>
    </Collapsible>
  );
}

// ============================================================================
// RunManifestViewer
// ============================================================================

export function RunManifestViewer({ manifest, loading, error, onClose }: RunManifestViewerProps) {
  if (loading) {
    return (
      <section className="space-y-3" aria-label="Loading manifest">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-32 w-full" />
      </section>
    );
  }

  if (error || !manifest) {
    return (
      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4" aria-label="Manifest error">
        <AlertTriangle className="h-6 w-6 text-amber-600 mb-2" />
        <p className="text-sm font-semibold text-amber-900">No manifest data available</p>
        <p className="text-xs text-amber-700 mt-1">
          {error || "The full manifest could not be loaded. The result may have been evicted from cache."}
        </p>
        {onClose && (
          <Button variant="outline" size="sm" className="mt-3" onClick={onClose}>
            Close
          </Button>
        )}
      </section>
    );
  }

  return (
    <section className="space-y-3" aria-label="Run manifest viewer">
      {/* Header with close button */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Run Manifest</h2>
          <p className="text-xs text-slate-500 font-mono">{manifest.manifest_id.slice(0, 8)}</p>
        </div>
        {onClose && (
          <Button variant="outline" size="sm" onClick={onClose}>
            Close
          </Button>
        )}
      </div>

      {manifest.metadata_only ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-3" role="status">
          <div className="flex items-start gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" aria-hidden="true" />
            <div>
              <p className="text-sm font-semibold text-amber-900">Metadata-only manifest</p>
              <p className="text-xs text-amber-700">
                Panel data was evicted or is unavailable, so this view is built from stored metadata and manifest files only.
              </p>
            </div>
          </div>
        </div>
      ) : null}

      {/* Overview Section */}
      <ManifestSection title="Overview" icon={<FileText className="h-4 w-4 text-slate-500" />} defaultOpen={true}>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <span className="text-slate-500">Run ID</span>
          <span className="font-mono font-medium text-slate-800">{manifest.run_id.slice(0, 16)}...</span>

          <span className="text-slate-500">Manifest ID</span>
          <span className="font-mono font-medium text-slate-800">{manifest.manifest_id.slice(0, 16)}...</span>

          <span className="text-slate-500">Status</span>
          <span className="font-medium text-slate-800">{manifest.status || "completed"}</span>

          <span className="text-slate-500">Created</span>
          <span className="font-medium text-slate-800">{formatTs(manifest.created_at)}</span>

          {manifest.started_at && (
            <>
              <span className="text-slate-500">Started</span>
              <span className="font-medium text-slate-800">{formatTs(manifest.started_at)}</span>
            </>
          )}

          {manifest.finished_at && (
            <>
              <span className="text-slate-500">Finished</span>
              <span className="font-medium text-slate-800">{formatTs(manifest.finished_at)}</span>
            </>
          )}

          <span className="text-slate-500">Engine Version</span>
          <span className="font-mono font-medium text-slate-800">{manifest.engine_version}</span>

          <span className="text-slate-500">OpenFisca Version</span>
          <span className="font-mono font-medium text-slate-800">{manifest.openfisca_version}</span>

          <span className="text-slate-500">Adapter Version</span>
          <span className="font-mono font-medium text-slate-800">{manifest.adapter_version}</span>

          <span className="text-slate-500">Runtime Mode</span>
          <div className="flex items-center gap-2">
            {runtimeModeBadge(manifest.runtime_mode)}
            {populationSourceBadge(manifest.population_source)}
          </div>
        </div>
      </ManifestSection>

      {/* Execution Section */}
      <ManifestSection title="Execution" icon={<FileText className="h-4 w-4 text-slate-500" />} defaultOpen={false}>
        <div className="space-y-3">
          {/* Seeds */}
          {Object.keys(manifest.seeds).length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Seeds</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                {Object.entries(manifest.seeds).map(([key, value]) => (
                  <React.Fragment key={key}>
                    <dt className="text-slate-500">{key}</dt>
                    <dd className="font-mono font-medium text-slate-800">{value}</dd>
                  </React.Fragment>
                ))}
              </dl>
            </div>
          )}

          {/* Step Pipeline */}
          {manifest.step_pipeline.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Step Pipeline</p>
              <ol className="text-xs text-slate-700 space-y-0.5">
                {manifest.step_pipeline.map((step, i) => (
                  <li key={i} className="flex items-center gap-2">
                    <span className="text-slate-400">{i + 1}.</span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Population Reference */}
          {manifest.population_id && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Population</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                <dt className="text-slate-500">Population ID</dt>
                <dd className="font-mono font-medium text-slate-800">{manifest.population_id}</dd>
                {manifest.population_source && (
                  <>
                    <dt className="text-slate-500">Source</dt>
                    <dd className="font-medium text-slate-800">{manifest.population_source}</dd>
                  </>
                )}
              </dl>
            </div>
          )}
        </div>
      </ManifestSection>

      {/* Policy Section */}
      <ManifestSection title="Policy & Assumptions" icon={<FileText className="h-4 w-4 text-slate-500" />} defaultOpen={false}>
        <div className="space-y-3">
          {hasEntries(manifest.policy) && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Policy</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                {Object.entries(manifest.policy).map(([key, value]) => (
                  <React.Fragment key={key}>
                    <dt className="text-slate-500">{key}</dt>
                    <dd className="font-mono text-slate-800">{safeStringify(value)}</dd>
                  </React.Fragment>
                ))}
              </dl>
            </div>
          )}

          {/* Assumptions */}
          {manifest.assumptions.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Assumptions</p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-1 text-slate-500">Key</th>
                      <th className="text-left py-1 text-slate-500">Value</th>
                      <th className="text-left py-1 text-slate-500">Source</th>
                      <th className="text-left py-1 text-slate-500">Default</th>
                    </tr>
                  </thead>
                  <tbody>
                    {manifest.assumptions.map((a, i) => (
                      <tr key={i} className="border-b border-slate-100">
                        <td className="py-1 text-slate-700">{a.key}</td>
                        <td className="py-1 font-mono text-slate-800">{safeStringify(a.value)}</td>
                        <td className="py-1 text-slate-600">{a.source}</td>
                        <td className="py-1 text-slate-600">{a.is_default ? "Yes" : "No"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Mappings */}
          {manifest.mappings.length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Variable Mappings</p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-1 text-slate-500">OpenFisca Name</th>
                      <th className="text-left py-1 text-slate-500">Project Name</th>
                      <th className="text-left py-1 text-slate-500">Direction</th>
                    </tr>
                  </thead>
                  <tbody>
                    {manifest.mappings.map((m, i) => (
                      <tr key={i} className="border-b border-slate-100">
                        <td className="py-1 font-mono text-slate-800">{m.openfisca_name}</td>
                        <td className="py-1 text-slate-700">{m.project_name}</td>
                        <td className="py-1 text-slate-600">{m.direction}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {hasEntries(manifest.taste_parameters) && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Taste Parameters</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                {Object.entries(manifest.taste_parameters).map(([key, value]) => (
                  <React.Fragment key={key}>
                    <dt className="text-slate-500">{key}</dt>
                    <dd className="font-mono text-slate-800">{safeStringify(value)}</dd>
                  </React.Fragment>
                ))}
              </dl>
            </div>
          )}
        </div>
      </ManifestSection>

      {/* Data Provenance Section */}
      <ManifestSection title="Data Provenance" icon={<Hash className="h-4 w-4 text-slate-500" />} defaultOpen={false}>
        <div className="space-y-3">
          {/* Data Hashes */}
          {Object.keys(manifest.data_hashes).length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Input Hashes (SHA-256)</p>
              <dl className="grid grid-cols-1 gap-1 text-xs">
                {Object.entries(manifest.data_hashes).map(([key, hash]) => (
                  <div key={key}>
                    <dt className="text-slate-500">{key}</dt>
                    <dd className="font-mono text-slate-800 break-all" title={hash}>
                      {truncateHash(hash)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {/* Output Hashes */}
          {Object.keys(manifest.output_hashes).length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Output Hashes (SHA-256)</p>
              <dl className="grid grid-cols-1 gap-1 text-xs">
                {Object.entries(manifest.output_hashes).map(([key, hash]) => (
                  <div key={key}>
                    <dt className="text-slate-500">{key}</dt>
                    <dd className="font-mono text-slate-800 break-all" title={hash}>
                      {truncateHash(hash)}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {/* Integrity Hash */}
          {manifest.integrity_hash && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Integrity Hash</p>
              <p className="font-mono text-xs text-slate-800 break-all" title={manifest.integrity_hash}>
                {truncateHash(manifest.integrity_hash)}
              </p>
            </div>
          )}
        </div>
      </ManifestSection>

      {/* Lineage Section */}
      <ManifestSection title="Lineage" icon={<FileText className="h-4 w-4 text-slate-500" />} defaultOpen={false}>
        <div className="space-y-3">
          {/* Parent Manifest */}
          {manifest.parent_manifest_id && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Parent Manifest</p>
              <p className="font-mono text-xs text-slate-800">{manifest.parent_manifest_id}</p>
            </div>
          )}

          {/* Child Manifests */}
          {Object.keys(manifest.child_manifests).length > 0 && (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Child Manifests (by year)</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                {Object.entries(manifest.child_manifests).map(([year, id]) => (
                  <React.Fragment key={year}>
                    <dt className="text-slate-500">Year {year}</dt>
                    <dd className="font-mono text-slate-800">{id}</dd>
                  </React.Fragment>
                ))}
              </dl>
            </div>
          )}

          {!manifest.parent_manifest_id && Object.keys(manifest.child_manifests).length === 0 && (
            <p className="text-xs text-slate-400">No lineage information available.</p>
          )}
        </div>
      </ManifestSection>

      {/* Evidence Section */}
      <ManifestSection title="Evidence & Assets" icon={<FileText className="h-4 w-4 text-slate-500" />} defaultOpen={false}>
        <div className="space-y-3">
          {hasEntries(manifest.evidence_summary) ? (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Evidence Summary</p>
              <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                {Object.entries(manifest.evidence_summary).map(([key, value]) => (
                  <React.Fragment key={key}>
                    <dt className="text-slate-500">{key}</dt>
                    <dd className="font-mono text-slate-800">{safeStringify(value)}</dd>
                  </React.Fragment>
                ))}
              </dl>
            </div>
          ) : (
            <p className="text-xs text-slate-400">No evidence summary available.</p>
          )}
          {manifest.evidence_assets.length > 0 ? (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Evidence Assets</p>
              <ul className="text-xs text-slate-700 space-y-0.5">
                {manifest.evidence_assets.map((asset, i) => (
                  <li key={i} className="font-mono">{safeStringify(asset)}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {manifest.calibration_assets.length > 0 ? (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Calibration Assets</p>
              <ul className="text-xs text-slate-700 space-y-0.5">
                {manifest.calibration_assets.map((asset, i) => (
                  <li key={i} className="font-mono">{safeStringify(asset)}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {manifest.validation_assets.length > 0 ? (
            <div>
              <p className="text-xs font-semibold uppercase text-slate-500 mb-1">Validation Assets</p>
              <ul className="text-xs text-slate-700 space-y-0.5">
                {manifest.validation_assets.map((asset, i) => (
                  <li key={i} className="font-mono">{safeStringify(asset)}</li>
                ))}
              </ul>
            </div>
          ) : null}
          {!hasEntries(manifest.evidence_summary) &&
           manifest.evidence_assets.length === 0 &&
           manifest.calibration_assets.length === 0 &&
           manifest.validation_assets.length === 0 && (
            <p className="text-xs text-slate-400">No evidence or assets available.</p>
          )}
        </div>
      </ManifestSection>

      {/* Warnings Section */}
      <ManifestSection title="Warnings" icon={<AlertTriangle className="h-4 w-4 text-amber-500" />} defaultOpen={true}>
        {manifest.warnings.length > 0 ? (
          <ul className="text-xs text-slate-700 space-y-1">
            {manifest.warnings.map((warning, i) => (
              <li key={i} className="flex items-start gap-2">
                <AlertTriangle className="h-3 w-3 text-amber-500 mt-0.5 shrink-0" />
                <span>{warning}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-slate-400">No warnings.</p>
        )}
      </ManifestSection>
    </section>
  );
}
