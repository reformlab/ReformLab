// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Exogenous series comparison dimension — Story 21.6, AC-6.
 *
 * Extends Story 20.6 pluggable dimension infrastructure.
 * Allows filtering/grouping runs by exogenous time series assumptions.
 */

import type { ReactNode } from "react";
import type { ComparisonDimension, ResultDetailResponse } from "@/api/types";

// Story 21.6 / AC6: Exogenous comparison dimension
// Note: The actual hash is computed on the server side and returned via
// exogenous_series_hash field. The hash function below is for reference only.
// function hashExogenousContext(...) { ... }

const exogenousDimension: ComparisonDimension<string> = {
  id: "exogenous",
  label: "Exogenous Series",
  description:
    "Deterministic hash of exogenous time series assumptions (energy prices, carbon tax rates, technology costs)",

  getValue(runResult: ResultDetailResponse): string | null {
    return runResult.exogenous_series_hash || null;
  },

  render(value: string): ReactNode {
    // We can't access series_names from just the hash, so display generic message
    // In a full implementation, the API would return both hash and names
    return (
      <div className="text-xs">
        <div className="font-medium text-slate-900">Exogenous</div>
        <div className="text-slate-500 font-mono">{value.slice(0, 8)}</div>
      </div>
    );
  },
};

// Auto-register on module load
import { DimensionRegistry } from "./DimensionRegistry";

DimensionRegistry.register(exogenousDimension);

export { exogenousDimension };
