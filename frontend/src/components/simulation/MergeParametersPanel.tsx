/** Merge method parameter configuration panel (Story 17.1, AC-3). */

import { Input } from "@/components/ui/input";

interface MergeParametersPanelProps {
  methodId: string;
  seed: number;
  strataColumns: string;
  onSeedChange: (seed: number) => void;
  onStrataColumnsChange: (cols: string) => void;
}

export function MergeParametersPanel({
  methodId,
  seed,
  strataColumns,
  onSeedChange,
  onStrataColumnsChange,
}: MergeParametersPanelProps) {
  return (
    <section
      aria-label="Merge parameters"
      className="border border-slate-200 bg-white p-3 space-y-3"
    >
      <p className="text-sm font-semibold text-slate-900">Parameters</p>

      {/* Seed — available for all methods */}
      <div className="space-y-1">
        <label htmlFor="merge-seed" className="block text-xs font-medium text-slate-700">
          Random Seed
        </label>
        <Input
          id="merge-seed"
          type="number"
          min={0}
          value={seed}
          onChange={(e) => onSeedChange(Number(e.target.value))}
          className="data-mono w-32"
          aria-describedby="merge-seed-hint"
        />
        <p id="merge-seed-hint" className="text-xs text-slate-500">
          Same seed + configuration → identical results (deterministic)
        </p>
      </div>

      {/* Strata columns — conditional sampling only */}
      {methodId === "conditional" ? (
        <div className="space-y-1">
          <label htmlFor="strata-columns" className="block text-xs font-medium text-slate-700">
            Stratification Columns
          </label>
          <Input
            id="strata-columns"
            type="text"
            placeholder="e.g. commune_code, region_code"
            value={strataColumns}
            onChange={(e) => onStrataColumnsChange(e.target.value)}
            aria-describedby="strata-columns-hint"
          />
          <p id="strata-columns-hint" className="text-xs text-slate-500">
            Comma-separated column names shared across both sources to use for stratification
          </p>
        </div>
      ) : null}

      {/* IPF note */}
      {methodId === "ipf" ? (
        <p className="text-xs text-slate-500">
          IPF constraints (target marginals) will be derived from catalog metadata automatically.
          Advanced constraint editing is available in Story 17.6.
        </p>
      ) : null}
    </section>
  );
}
