// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Portfolio Template Browser (Story 17.2, AC-1, AC-2).
 *
 * Multi-select card grid of available policy templates. Follows the
 * DataSourceBrowser.tsx multi-select pattern with aria-pressed toggle buttons.
 * Groups templates by policy type.
 */

import { useState } from "react";
import { Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type { Template } from "@/data/mock-data";

const TYPE_LABELS: Record<string, string> = {
  "carbon-tax": "Carbon Tax",
  "subsidy": "Subsidy",
  "rebate": "Rebate",
  "feebate": "Feebate",
  "carbon_tax": "Carbon Tax",
};

const TYPE_COLORS: Record<string, string> = {
  "carbon-tax": "bg-amber-100 text-amber-800",
  "carbon_tax": "bg-amber-100 text-amber-800",
  "subsidy": "bg-emerald-100 text-emerald-800",
  "rebate": "bg-blue-100 text-blue-800",
  "feebate": "bg-violet-100 text-violet-800",
};

interface PortfolioTemplateBrowserProps {
  templates: Template[];
  selectedIds: string[];
  onToggleTemplate: (templateId: string) => void;
}

export function PortfolioTemplateBrowser({
  templates,
  selectedIds,
  onToggleTemplate,
}: PortfolioTemplateBrowserProps) {
  const [query, setQuery] = useState("");

  // Group templates by type
  const byType: Record<string, Template[]> = {};
  for (const t of templates) {
    const key = t.type;
    if (!byType[key]) byType[key] = [];
    byType[key].push(t);
  }

  const filtered = query
    ? templates.filter(
        (t) =>
          t.name.toLowerCase().includes(query.toLowerCase()) ||
          t.description.toLowerCase().includes(query.toLowerCase()) ||
          t.parameterGroups.some((g) => g.toLowerCase().includes(query.toLowerCase())),
      )
    : null;

  const displayGroups = filtered
    ? Object.fromEntries(
        Object.entries(byType).map(([type, items]) => [
          type,
          items.filter((t) => filtered.includes(t)),
        ]),
      )
    : byType;

  return (
    <section aria-label="Policy template browser" className="space-y-3">
      <div className="relative">
        <Search className="absolute left-2 top-2.5 h-4 w-4 text-slate-400" />
        <Input
          placeholder="Filter templates..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="pl-8"
          aria-label="Filter policy templates"
        />
      </div>

      {Object.entries(displayGroups).map(([type, items]) => {
        if (items.length === 0) return null;
        return (
          <section key={type} aria-label={`${TYPE_LABELS[type] ?? type} templates`}>
            <p className="mb-1 text-xs font-semibold uppercase text-slate-500">
              {TYPE_LABELS[type] ?? type}
            </p>
            <div className="grid gap-2 xl:grid-cols-2">
              {items.map((template) => {
                const selected = selectedIds.includes(template.id);
                return (
                  <button
                    key={template.id}
                    type="button"
                    onClick={() => onToggleTemplate(template.id)}
                    aria-pressed={selected}
                    className={cn(
                      "w-full border p-3 text-left transition-colors",
                      selected
                        ? "border-blue-500 bg-blue-50"
                        : "border-slate-200 bg-white hover:bg-slate-50",
                    )}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-slate-900 truncate">
                          {template.name}
                        </p>
                        <p className="mt-0.5 text-xs text-slate-600 line-clamp-2">
                          {template.description}
                        </p>
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          <span
                            className={cn(
                              "inline-flex items-center px-1.5 py-0.5 text-xs font-medium",
                              TYPE_COLORS[type] ?? "bg-slate-100 text-slate-700",
                            )}
                          >
                            {TYPE_LABELS[type] ?? type}
                          </span>
                          <Badge variant="default" className="text-xs">
                            {template.parameterCount} params
                          </Badge>
                          {template.parameterGroups.map((g) => (
                            <Badge key={g} variant="default" className="text-xs">
                              {g}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <input
                        type="checkbox"
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
            </div>
          </section>
        );
      })}

      {templates.length === 0 ? (
        <p className="text-sm text-slate-500">No templates available.</p>
      ) : null}
    </section>
  );
}
