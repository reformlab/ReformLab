// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * Portfolio Template Browser (Story 17.2, AC-1, AC-2).
 *
 * Multi-select card grid of available policy templates. Follows the
 * DataSourceBrowser.tsx multi-select pattern with aria-pressed toggle buttons.
 *
 * Story 25.1: Groups templates by category, adds category filter chips,
 * and displays category badges with help popover.
 */

import { useState, useMemo } from "react";
import { Search, CheckCircle2, AlertCircle, CircleHelp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
// Story 25.3: Import shared type constants
import { TYPE_COLORS, TYPE_LABELS } from "@/components/simulation/typeConstants";
import { cn } from "@/lib/utils";
import type { Template } from "@/data/mock-data";
import type { Category } from "@/api/types";

interface PortfolioTemplateBrowserProps {
  templates: Template[];
  selectedIds: string[];
  // Story 25.2: Changed from toggle to add-instance action
  onAddTemplate: (templateId: string) => void;
  // Story 25.1 / Task 3.1: Categories prop for grouping and filtering
  categories?: Category[] | null;
  // Story 25.2: Count of instances per template in composition
  templateInstanceCounts?: Record<string, number>;
}

// Helper component to render a single template card
interface TemplateCardProps {
  template: Template;
  inComposition: boolean;
  instanceCount: number;
  templateCategory: Category | null | undefined;
  onAdd: () => void;
}

function TemplateCard({ template, inComposition, instanceCount, templateCategory, onAdd }: TemplateCardProps) {
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onAdd();
    }
  };
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onAdd}
      onKeyDown={handleKeyDown}
      className={cn(
        "w-full border p-3 text-left transition-colors",
        "border-slate-200 bg-white hover:bg-slate-50",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="text-sm font-medium text-slate-900 truncate">
              {template.name}
            </p>
            {/* Story 24.1 / AC-1, #2: Runtime availability indicator */}
            {template.runtime_availability && (
              <Badge
                variant="outline"
                className={`text-xs ${
                  template.runtime_availability === "live_ready"
                    ? "bg-green-50 text-green-700 border-green-200"
                    : "bg-amber-50 text-amber-700 border-amber-200"
                }`}
              >
                {template.runtime_availability === "live_ready" ? (
                  <>
                    <CheckCircle2 className="h-3 w-3 mr-1 inline" /> Ready
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-3 w-3 mr-1 inline" /> Unavailable
                  </>
                )}
              </Badge>
            )}
            {/* Story 25.2: Count badge when template is in composition */}
            {inComposition && (
              <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                Added {instanceCount}×
              </Badge>
            )}
          </div>
          <p className="mt-0.5 text-xs text-slate-600 line-clamp-2">
            {template.description}
          </p>
          {/* Story 24.1 / AC-2: Display availability reason for unavailable templates */}
          {template.runtime_availability === "live_unavailable" && template.availability_reason && (
            <div className="mt-1.5 p-1.5 bg-amber-50 rounded border border-amber-200">
              <p className="text-xs text-amber-800">
                {template.availability_reason}
              </p>
            </div>
          )}
          <div className="mt-1.5 flex flex-wrap gap-1 items-center">
            {/* Story 25.1 / Task 3.5: Category badge (neutral color) */}
            {templateCategory && (
              <span className="inline-flex items-center px-1.5 py-0.5 text-xs font-medium bg-slate-100 text-slate-800">
                {templateCategory.label}
              </span>
            )}
            {/* Story 25.1 / AC-4: Help icon with formula explanation popover */}
            {templateCategory && (
              <Popover>
                <PopoverTrigger asChild>
                  <button
                    type="button"
                    onClick={(e) => e.stopPropagation()}
                    className="inline-flex items-center p-0.5 text-slate-500 hover:text-slate-700"
                    aria-label={`Formula help for ${templateCategory.label}`}
                  >
                    <CircleHelp className="h-3.5 w-3.5" />
                  </button>
                </PopoverTrigger>
                <PopoverContent className="w-64 text-xs" side="right">
                  <div className="space-y-2">
                    <div>
                      <p className="font-medium text-slate-900">Formula</p>
                      <p className="text-slate-700 font-mono bg-slate-50 px-1.5 py-0.5 rounded mt-1">
                        {templateCategory.formula_explanation}
                      </p>
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">Description</p>
                      <p className="text-slate-700">{templateCategory.description}</p>
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">Columns</p>
                      <p className="text-slate-700">{templateCategory.columns.join(", ")}</p>
                    </div>
                  </div>
                </PopoverContent>
              </Popover>
            )}
            <span
              className={cn(
                "inline-flex items-center px-1.5 py-0.5 text-xs font-medium",
                TYPE_COLORS[template.type] ?? "bg-slate-100 text-slate-700",
              )}
            >
              {TYPE_LABELS[template.type] ?? template.type}
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
        {/* Story 25.2: Add button indicator */}
        <div className="mt-0.5 text-slate-400 hover:text-blue-500">
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </div>
      </div>
    </div>
  );
}

export function PortfolioTemplateBrowser({
  templates,
  selectedIds,
  onAddTemplate,
  categories,
  templateInstanceCounts = {},
}: PortfolioTemplateBrowserProps) {
  const [query, setQuery] = useState("");
  // Story 25.1 / Task 3.3: Category filter state
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);

  // Story 25.1 / AC-6: Determine if we should show grouped or flat layout
  // undefined = not provided (flat list, no warning — pre-categories behavior)
  // null = still loading (flat list, no warning yet)
  // [] = API failed (flat list + warning)
  // non-empty = loaded successfully (grouped)
  const categoriesLoaded = categories != null;
  const shouldShowGrouped = categoriesLoaded && categories!.length > 0;
  const categoriesFailed = categoriesLoaded && categories!.length === 0;

  // Story 25.1 / AC-8: Filter by both category and query (AND logic)
  const filtered = useMemo(() => {
    let result = templates;

    // Category filter
    if (selectedCategoryId) {
      result = result.filter((t) => t.category_id === selectedCategoryId);
    }

    // Search query filter
    if (query) {
      result = result.filter(
        (t) =>
          t.name.toLowerCase().includes(query.toLowerCase()) ||
          t.description.toLowerCase().includes(query.toLowerCase()) ||
          t.parameterGroups.some((g) => g.toLowerCase().includes(query.toLowerCase())),
      );
    }

    return result;
  }, [templates, selectedCategoryId, query]);

  // Category lookup map
  const categoryMap = useMemo(() => {
    const map = new Map<string, Category>();
    if (categories) {
      for (const cat of categories) {
        map.set(cat.id, cat);
      }
    }
    return map;
  }, [categories]);

  // Build display groups from filtered results
  const displayGroups = useMemo(() => {
    // Story 25.1 / AC-6: If categories failed, return empty groups for flat display
    if (!shouldShowGrouped) {
      return {};
    }
    const groups: Record<string, Template[]> = {};
    for (const t of filtered) {
      // AC-5: Templates without category or with unknown category go to "Other"
      const key = (t.category_id && categoryMap.has(t.category_id)) ? t.category_id : "other";
      if (!groups[key]) groups[key] = [];
      groups[key].push(t);
    }
    return groups;
  }, [filtered, shouldShowGrouped, categoryMap]);

  // Story 25.1 / Task 3.5: Sort "Other" group last, named categories in API-defined order
  const sortedGroupKeys = useMemo(() => {
    const keys = Object.keys(displayGroups);
    const categoryOrder = (categories ?? []).map((c) => c.id);
    return keys.sort((a, b) => {
      if (a === "other") return 1;
      if (b === "other") return -1;
      const ia = categoryOrder.indexOf(a);
      const ib = categoryOrder.indexOf(b);
      if (ia === -1 && ib === -1) return a.localeCompare(b);
      if (ia === -1) return 1;
      if (ib === -1) return -1;
      return ia - ib;
    });
  }, [displayGroups, categories]);

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

      {/* Story 25.1 / AC-6: Non-blocking warning if categories failed to load */}
      {categoriesFailed && templates.length > 0 ? (
        <div className="p-2 bg-amber-50 border border-amber-200 rounded text-xs text-amber-800">
          Categories could not be loaded. Templates are shown ungrouped.
        </div>
      ) : null}

      {/* Story 25.1 / Task 3.3: Category filter chips */}
      {shouldShowGrouped ? (
        <div className="flex flex-wrap gap-1.5">
          <Button
            size="sm"
            variant={selectedCategoryId === null ? "default" : "outline"}
            onClick={() => setSelectedCategoryId(null)}
            className="text-xs h-7"
          >
            All Categories
          </Button>
          {categories && categories.map((cat) => (
            <Button
              key={cat.id}
              size="sm"
              variant={selectedCategoryId === cat.id ? "default" : "outline"}
              onClick={() => setSelectedCategoryId(cat.id)}
              className="text-xs h-7"
            >
              {cat.label}
            </Button>
          ))}
        </div>
      ) : null}

      {/* Story 25.1 / AC-6: Flat list when categories failed or still loading */}
      {!shouldShowGrouped ? (
        <div className="grid gap-2 xl:grid-cols-2">
          {filtered.map((template) => {
            const inComposition = selectedIds.includes(template.id);
            const instanceCount = templateInstanceCounts[template.id] || 0;
            const templateCategory = template.category_id ? categoryMap.get(template.category_id) : null;
            return (
              <TemplateCard
                key={template.id}
                template={template}
                inComposition={inComposition}
                instanceCount={instanceCount}
                templateCategory={templateCategory}
                onAdd={() => onAddTemplate(template.id)}
              />
            );
          })}
        </div>
      ) : (
        sortedGroupKeys.map((categoryId) => {
          const items = displayGroups[categoryId];
          if (!items || items.length === 0) return null;

          const category = categoryMap.get(categoryId);
          const categoryLabel = categoryId === "other" ? "Other" : category?.label ?? categoryId;

          return (
            <section key={categoryId} aria-label={`${categoryLabel} templates`}>
              <p className="mb-1 text-xs font-semibold uppercase text-slate-500">
                {categoryLabel}
              </p>
              <div className="grid gap-2 xl:grid-cols-2">
                {items.map((template) => {
                  const inComposition = selectedIds.includes(template.id);
                  const instanceCount = templateInstanceCounts[template.id] || 0;
                  const templateCategory = template.category_id ? categoryMap.get(template.category_id) : null;
                  return (
                    <TemplateCard
                      key={template.id}
                      template={template}
                      inComposition={inComposition}
                      instanceCount={instanceCount}
                      templateCategory={templateCategory}
                      onAdd={() => onAddTemplate(template.id)}
                    />
                  );
                })}
              </div>
            </section>
          );
        })
      )}

      {templates.length === 0 ? (
        <p className="text-sm text-slate-500">No templates available.</p>
      ) : null}
    </section>
  );
}
