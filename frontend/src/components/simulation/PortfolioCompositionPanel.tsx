/**
 * Portfolio Composition Panel (Story 17.2, AC-2, AC-3).
 *
 * Ordered list of selected templates as cards with:
 * - Move-up / move-down buttons (arrow buttons, no DnD library)
 * - Remove button
 * - Expand/collapse for inline parameter editing
 * - ParameterRow editing when expanded
 *
 * Per AC-3, move-up is disabled for first item, move-down for last.
 */

import { useState } from "react";
import { ArrowUp, ArrowDown, Trash2, ChevronDown, ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { ParameterRow } from "@/components/simulation/ParameterRow";
import { cn } from "@/lib/utils";
import type { Template, Parameter } from "@/data/mock-data";

const TYPE_COLORS: Record<string, string> = {
  "carbon-tax": "bg-amber-100 text-amber-800",
  "carbon_tax": "bg-amber-100 text-amber-800",
  "subsidy": "bg-emerald-100 text-emerald-800",
  "rebate": "bg-blue-100 text-blue-800",
  "feebate": "bg-violet-100 text-violet-800",
};

const TYPE_LABELS: Record<string, string> = {
  "carbon-tax": "Carbon Tax",
  "carbon_tax": "Carbon Tax",
  "subsidy": "Subsidy",
  "rebate": "Rebate",
  "feebate": "Feebate",
};

export interface CompositionEntry {
  templateId: string;
  name: string;
  parameters: Record<string, number>;
}

interface PortfolioCompositionPanelProps {
  templates: Template[];
  composition: CompositionEntry[];
  onReorder: (fromIndex: number, toIndex: number) => void;
  onRemove: (index: number) => void;
  onParameterChange: (index: number, paramId: string, value: number) => void;
  /** Optional parameter schemas per template — used for inline editing */
  parameterSchemas?: Record<string, Parameter[]>;
}

export function PortfolioCompositionPanel({
  templates,
  composition,
  onReorder,
  onRemove,
  onParameterChange,
  parameterSchemas = {},
}: PortfolioCompositionPanelProps) {
  const [expandedIndices, setExpandedIndices] = useState<Set<number>>(new Set());

  const toggleExpanded = (index: number) => {
    setExpandedIndices((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  if (composition.length === 0) {
    return (
      <div className="border border-slate-200 bg-slate-50 p-6 text-center">
        <p className="text-sm text-slate-500">
          Select templates from the browser to add them here.
        </p>
        {composition.length < 2 ? (
          <p className="mt-1 text-xs text-amber-600">
            Add at least 2 policies to save a portfolio.
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <section aria-label="Portfolio composition" className="space-y-2">
      {composition.length < 2 ? (
        <p className="text-xs text-amber-600 border border-amber-200 bg-amber-50 p-2">
          Add at least 2 policies to save a portfolio.
        </p>
      ) : null}

      {composition.map((entry, index) => {
        const template = templates.find((t) => t.id === entry.templateId);
        const isFirst = index === 0;
        const isLast = index === composition.length - 1;
        const isExpanded = expandedIndices.has(index);
        const schemas = parameterSchemas[entry.templateId] ?? [];

        return (
          <div
            key={`${entry.templateId}-${index}`}
            className="border border-slate-200 bg-white"
          >
            {/* Card header */}
            <div className="flex items-center gap-2 p-3">
              {/* Order index */}
              <span className="text-xs font-mono text-slate-400 w-5 shrink-0">
                {index + 1}.
              </span>

              {/* Template info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <p className="text-sm font-medium text-slate-900 truncate">
                    {entry.name || template?.name || entry.templateId}
                  </p>
                  {template ? (
                    <>
                      <span
                        className={cn(
                          "inline-flex items-center px-1.5 py-0.5 text-xs font-medium shrink-0",
                          TYPE_COLORS[template.type] ?? "bg-slate-100 text-slate-700",
                        )}
                      >
                        {TYPE_LABELS[template.type] ?? template.type}
                      </span>
                      <Badge variant="default" className="text-xs shrink-0">
                        {template.parameterCount} params
                      </Badge>
                    </>
                  ) : null}
                </div>
              </div>

              {/* Action buttons */}
              <div className="flex items-center gap-1 shrink-0">
                {/* Expand/collapse */}
                <button
                  type="button"
                  onClick={() => toggleExpanded(index)}
                  className="border border-slate-200 p-1 hover:bg-slate-50"
                  aria-expanded={isExpanded}
                  aria-label={isExpanded ? "Collapse parameters" : "Expand parameters"}
                  title={isExpanded ? "Collapse" : "Expand parameters"}
                >
                  {isExpanded ? (
                    <ChevronDown className="h-3 w-3 text-slate-600" />
                  ) : (
                    <ChevronRight className="h-3 w-3 text-slate-600" />
                  )}
                </button>

                {/* Move up */}
                <button
                  type="button"
                  disabled={isFirst}
                  onClick={() => onReorder(index, index - 1)}
                  className={cn(
                    "border p-1",
                    isFirst
                      ? "border-slate-100 text-slate-300 cursor-not-allowed"
                      : "border-slate-200 text-slate-600 hover:bg-slate-50",
                  )}
                  aria-label="Move up"
                  title="Move up"
                >
                  <ArrowUp className="h-3 w-3" />
                </button>

                {/* Move down */}
                <button
                  type="button"
                  disabled={isLast}
                  onClick={() => onReorder(index, index + 1)}
                  className={cn(
                    "border p-1",
                    isLast
                      ? "border-slate-100 text-slate-300 cursor-not-allowed"
                      : "border-slate-200 text-slate-600 hover:bg-slate-50",
                  )}
                  aria-label="Move down"
                  title="Move down"
                >
                  <ArrowDown className="h-3 w-3" />
                </button>

                {/* Remove */}
                <button
                  type="button"
                  onClick={() => onRemove(index)}
                  className="border border-slate-200 p-1 text-red-500 hover:bg-red-50"
                  aria-label="Remove policy"
                  title="Remove"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            </div>

            {/* Expanded parameter editing */}
            {isExpanded ? (
              <div className="border-t border-slate-200">
                {schemas.length > 0 ? (
                  schemas
                    .filter((p) => p.type === "number" || p.type === "slider")
                    .map((param) => (
                      <ParameterRow
                        key={param.id}
                        parameter={param}
                        value={entry.parameters[param.id] ?? param.value}
                        onChange={(val) => onParameterChange(index, param.id, val)}
                      />
                    ))
                ) : (
                  <div className="p-3">
                    <p className="text-xs text-slate-400">
                      No configurable parameters for this template.
                    </p>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        );
      })}
    </section>
  );
}
