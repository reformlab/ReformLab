// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Merge method selector for the Data Fusion Workbench (Story 17.1, AC-3). */

import { Shuffle, GitMerge, Layers } from "lucide-react";
import { cn } from "@/lib/utils";
import type { MockMergeMethod } from "@/data/mock-data";

const METHOD_ICONS: Record<string, React.ElementType> = {
  uniform: Shuffle,
  ipf: GitMerge,
  conditional: Layers,
};

interface MergeMethodSelectorProps {
  methods: MockMergeMethod[];
  selectedMethodId: string;
  onSelectMethod: (id: string) => void;
}

export function MergeMethodSelector({
  methods,
  selectedMethodId,
  onSelectMethod,
}: MergeMethodSelectorProps) {
  return (
    <section aria-label="Merge method selection" className="space-y-2">
      {methods.map((method) => {
        const Icon = METHOD_ICONS[method.id] ?? Shuffle;
        const selected = method.id === selectedMethodId;

        return (
          <button
            key={method.id}
            type="button"
            onClick={() => onSelectMethod(method.id)}
            className={cn(
              "block w-full border p-3 text-left transition-colors",
              selected
                ? "border-blue-500 bg-blue-50"
                : "border-slate-200 bg-white hover:bg-slate-50",
            )}
            aria-pressed={selected}
          >
            <div className="flex items-start gap-3">
              <Icon
                className={cn(
                  "mt-0.5 h-5 w-5 shrink-0",
                  selected ? "text-blue-600" : "text-slate-400",
                )}
              />
              <div className="flex-1">
                <p className="text-sm font-semibold text-slate-900">{method.name}</p>
                <p className="mt-0.5 text-xs text-slate-700">{method.what_it_does}</p>

                {selected ? (
                  <div className="mt-2 space-y-1.5 border-t border-slate-200 pt-2">
                    <p className="text-xs">
                      <span className="font-semibold text-slate-700">Assumption: </span>
                      <span className="text-slate-600">{method.assumption}</span>
                    </p>
                    <p className="text-xs">
                      <span className="font-semibold text-slate-700">When appropriate: </span>
                      <span className="text-slate-600">{method.when_appropriate}</span>
                    </p>
                    <p className="text-xs">
                      <span className="font-semibold text-slate-700">Trade-off: </span>
                      <span className="text-slate-600">{method.tradeoff}</span>
                    </p>
                  </div>
                ) : null}
              </div>

              <input
                type="radio"
                readOnly
                checked={selected}
                tabIndex={-1}
                aria-hidden="true"
                className="mt-0.5 h-4 w-4 shrink-0 accent-blue-500"
              />
            </div>
          </button>
        );
      })}
    </section>
  );
}
