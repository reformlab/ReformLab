// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Exogenous series comparison dimension — Story 21.6, AC-6.
 *
 * Extends Story 20.6 pluggable dimension infrastructure.
 * Allows filtering/grouping runs by exogenous time series assumptions.
 *
 * Note: The ComparisonDimension interface only passes the hash value to render(),
 * not the full runResult. Displaying series names would require a broader interface
 * change (e.g., render(value: T, runResult: ResultDetailResponse)).
 * For now, the dimension shows a truncated hash for identification.
 */

import type { ReactNode } from "react";
import type { ComparisonDimension, ResultDetailResponse } from "@/api/types";

// Story 21.6 / AC6: Exogenous comparison dimension
const exogenousDimension: ComparisonDimension<string> = {
  id: "exogenous",
  label: "Exogenous Series",
  description:
    "Deterministic hash of exogenous time series assumptions (energy prices, carbon tax rates, technology costs)",

  getValue(runResult: ResultDetailResponse): string | null {
    return runResult.exogenous_series_hash || null;
  },

  render(value: string): ReactNode {
    // Display truncated hash for identification
    // Note: series names are available in ResultDetailResponse.exogenous_series_names
    // but the ComparisonDimension interface doesn't pass runResult to render()
    if (!value) {
      return null;
    }
    return (
      <div className="text-xs">
        <div className="font-medium text-slate-900">Exogenous</div>
        <div className="text-slate-500 font-mono">{value.slice(0, 8)}</div>
      </div>
    );
  },
};

// Auto-register on module load
import * as DimensionRegistry from "./DimensionRegistry";

DimensionRegistry.register(exogenousDimension);

export { exogenousDimension };
