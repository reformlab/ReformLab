// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * PolicyCard — Extracted policy card component (Story 27.4).
 *
 * This is the unified policy card component used by both template-instantiated
 * and from-scratch policies. The renderer contains no branches based on policy
 * source identity — only data-driven rendering based on the entry properties.
 *
 * Story 27.3: Show actual parameter values inline in collapsed cards.
 * Story 27.4: Unified card component for all policy sources.
 */

import { useState, useCallback } from "react";
import { ArrowUp, ArrowDown, Trash2, ChevronDown, ChevronRight, CircleHelp, Settings, Plus, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ParameterRow } from "@/components/simulation/ParameterRow";
import { YearScheduleEditor } from "@/components/simulation/YearScheduleEditor";
import { TYPE_COLORS, TYPE_LABELS } from "@/components/simulation/typeConstants";
import { normalizePolicyType } from "@/utils/policyTypes";
import { cn } from "@/lib/utils";
import type { Template, Parameter } from "@/data/mock-data";
import type { Category, EditableParameterGroup } from "@/api/types";
import type { CompositionEntry } from "./PortfolioCompositionPanel";
import type { PolicyValidationError } from "./portfolioValidation";
import { Input } from "@/components/ui/input";

// ============================================================================
// Story 27.3: Parameter summary helper functions
// ============================================================================

/**
 * Format a parameter value for display, matching ParameterRow.formatValue() logic.
 */
function formatParameterValue(value: number, unit: string): string {
  if (unit === "%") {
    return `${Math.round(value * 100)}%`;
  }
  return `${value} ${unit}`;
}

/**
 * Resolve the effective value for a parameter using the resolution order:
 * 1. entry.parameters[paramId] — configured value (highest priority)
 * 2. schema.baseline — schema baseline
 * 3. null — no value available
 */
function resolveParameterValue(
  paramId: string,
  entryParameters: Record<string, number>,
  schema?: Parameter
): number | null {
  // Check configured value first
  if (paramId in entryParameters) {
    return entryParameters[paramId];
  }
  // Fall back to schema baseline
  if (schema?.baseline !== undefined) {
    return schema.baseline;
  }
  return null;
}

/**
 * Summarize a parameter group for display in collapsed card.
 * Shows actual values with proper formatting, truncating if too many.
 */
function summarizeParameterGroup(
  group: EditableParameterGroup | string,
  entry: CompositionEntry,
  schemas: Parameter[]
): string {
  // For legacy groups (string array), map via schemas
  const groupIds = typeof group === "string"
    ? schemas.filter((p) => p.group === group).map((p) => p.id)
    : group.parameterIds;

  if (groupIds.length === 0) {
    return "Parameters not yet set";
  }

  // Build parameter summaries
  const parts = groupIds.map((paramId) => {
    const schema = schemas.find((s) => s.id === paramId);
    const value = resolveParameterValue(paramId, entry.parameters, schema);

    if (value === null) {
      return "—";
    }

    if (!schema) {
      return `${value}`;
    }

    return formatParameterValue(value, schema.unit);
  });

  // Truncate long summaries: show first 2 + count
  if (parts.length > 3) {
    return `${parts.slice(0, 2).join("; ")} (+${parts.length - 2} more)`;
  }
  return parts.join("; ");
}

/**
 * Summarize the rate schedule for display.
 */
function summarizeRateSchedule(entry: CompositionEntry, schemas: Parameter[]): string {
  const scheduleEntries = Object.entries(entry.rateSchedule);
  if (scheduleEntries.length === 0) {
    return "Not scheduled";
  }

  // Find the earliest year's rate
  const sortedEntries = scheduleEntries.sort((a, b) => Number(a[0]) - Number(b[0]));
  const [firstYear, firstRate] = sortedEntries[0];

  // Try to find a schedule parameter to get the unit (more specific match to avoid false positives)
  const scheduleParam = schemas.find((p) => p.id.includes("rate_schedule"));
  const unit = scheduleParam?.unit ?? "";

  const formatted = formatParameterValue(firstRate, unit);
  return unit ? formatted + ` in ${firstYear}` : `${firstRate} in ${firstYear}`;
}

// ============================================================================
// PolicyCard Props
// ============================================================================

export interface PolicyCardProps {
  /** The composition entry (policy) to render */
  entry: CompositionEntry;
  /** Template metadata (if applicable) */
  template?: Template;
  /** Parameter schemas for this template */
  schemas: Parameter[];
  /** Index of this entry in the composition list */
  index: number;
  /** Whether this is the first entry (move-up disabled) */
  isFirst: boolean;
  /** Whether this is the last entry (move-down disabled) */
  isLast: boolean;
  /** Whether the card is expanded (controlled by parent) */
  isExpanded: boolean;
  /** Categories for category badge display */
  categories?: Category[] | null;
  /** Index of card in edit-groups mode (null = none) */
  editGroupsIndex: number | null;
  /** Validation error for this policy (if any) */
  validationError?: PolicyValidationError;
  /** Callback to toggle expand state */
  onToggleExpand: (index: number) => void;
  /** Callback to toggle edit-groups mode */
  onToggleEditGroups?: (index: number) => void;
  /** Callback to rename a group */
  onGroupRename?: (policyIndex: number, groupId: string, newName: string) => void;
  /** Callback to add a new group */
  onAddGroup?: (policyIndex: number) => void;
  /** Callback to delete a group */
  onDeleteGroup?: (policyIndex: number, groupId: string) => void;
  /** Callback to move parameter between groups */
  onMoveParameter?: (policyIndex: number, paramId: string, fromGroupId: string, toGroupId: string) => void;
  /** Callback to remove this policy */
  onRemove: (index: number) => void;
  /** Callback to reorder policies */
  onReorder: (fromIndex: number, toIndex: number) => void;
  /** Callback when parameter value changes */
  onParameterChange: (index: number, paramId: string, value: number) => void;
  /** Callback when rate schedule changes */
  onRateScheduleChange: (index: number, schedule: Record<string, number>) => void;
}

// ============================================================================
// PolicyCard Component
// ============================================================================

export function PolicyCard({
  entry,
  template,
  schemas,
  index,
  isFirst,
  isLast,
  isExpanded,
  categories,
  editGroupsIndex = null,
  validationError,
  onToggleExpand,
  onToggleEditGroups,
  onGroupRename,
  onAddGroup,
  onDeleteGroup,
  onMoveParameter,
  onRemove,
  onReorder,
  onParameterChange,
  onRateScheduleChange,
}: PolicyCardProps) {
  // Story 27.3: Local state for highlighted group (parent does not control this)
  const [highlightedGroupId, setHighlightedGroupId] = useState<string | null>(null);

  // Story 27.3: Handler for group chip click (click-to-preview affordance)
  const handleGroupChipClick = useCallback(
    (groupId: string) => {
      // Expand the card
      onToggleExpand(index);

      // Set highlight
      const compositeKey = `${entry.instanceId || `index-${index}`}:${groupId}`;
      setHighlightedGroupId(compositeKey);

      // Scroll to group (next tick after DOM update)
      setTimeout(() => {
        const el = document.querySelector(`[data-group-key="${compositeKey}"]`);
        el?.scrollIntoView({ behavior: "smooth", block: "nearest" });

        // Remove highlight after animation
        setTimeout(() => setHighlightedGroupId(null), 1000);
      }, 0);
    },
    [index, entry.instanceId, onToggleExpand]
  );

  // Story 27.3: Keyboard handler for accessibility
  const handleGroupChipKeyDown = useCallback(
    (e: React.KeyboardEvent, groupId: string) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleGroupChipClick(groupId);
      }
    },
    [handleGroupChipClick]
  );

  // Story 25.2: Look up category by template.category_id or entry.category_id
  const category = entry.category_id && categories
    ? categories.find((c) => c.id === entry.category_id)
    : template?.category_id && categories
      ? categories.find((c) => c.id === template.category_id)
      : null;

  // Story 25.3: Determine policy type
  const policyType = entry.policy_type ?? template?.type;
  const parameterGroups = entry.parameter_groups ?? [];

  return (
    <div
      className={cn(
        "border bg-white",
        editGroupsIndex === index ? "border-blue-500" : "border-slate-200",
        validationError ? "border-red-300 bg-red-50/30" : "",
      )}
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
            {/* Story 25.6: Error badge */}
            {validationError && (
              <Badge variant="destructive" className="text-xs shrink-0 flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                Error
              </Badge>
            )}
            {/* Story 25.4: Editing badge */}
            {editGroupsIndex === index && (
              <Badge variant="info" className="text-xs shrink-0">
                Editing
              </Badge>
            )}
            <p className="text-sm font-medium text-slate-900 truncate">
              {entry.name || template?.name || entry.templateId}
            </p>
            {/* Story 25.3: Type badge */}
            {policyType ? (
              <span
                className={cn(
                  "inline-flex items-center px-1.5 py-0.5 text-xs font-medium shrink-0",
                  TYPE_COLORS[policyType] ?? "bg-slate-100 text-slate-700",
                )}
              >
                {TYPE_LABELS[policyType] ?? policyType}
              </span>
            ) : null}
            {/* Story 27.4: Parameter count badge - now unified for both sources */}
            {entry.editableParameterGroups && (
              <Badge variant="default" className="text-xs shrink-0">
                {entry.editableParameterGroups.reduce((sum, g) => sum + g.parameterIds.length, 0)} params
              </Badge>
            )}
            {/* Story 27.3: Collapsed card parameter summaries */}
            {!isExpanded && (entry.editableParameterGroups || parameterGroups.length > 0) && (
              <div className="flex flex-wrap gap-1.5 mt-1">
                {/* editableParameterGroups (Story 25.4) */}
                {entry.editableParameterGroups && entry.editableParameterGroups.length > 0
                  ? entry.editableParameterGroups.map((group) => {
                      const summary = summarizeParameterGroup(group, entry, schemas);

                      return (
                        <button
                          key={group.id}
                          type="button"
                          tabIndex={0}
                          aria-expanded={isExpanded}
                          onClick={() => handleGroupChipClick(group.id)}
                          onKeyDown={(e) => handleGroupChipKeyDown(e, group.id)}
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 text-xs font-medium rounded transition-colors",
                            "border border-slate-200 bg-slate-50 text-slate-700",
                            "hover:bg-slate-100 hover:border-slate-300",
                            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                          )}
                        >
                          <span className="truncate max-w-[200px]">
                            <span className="font-medium">{group.name}</span>: {summary}
                          </span>
                        </button>
                      );
                    })
                  : // Legacy parameter_groups (string array)
                    parameterGroups.map((group) => {
                      const summary = summarizeParameterGroup(group, entry, schemas);
                      const groupId = group.toLowerCase().replace(/\s+/g, "-");

                      return (
                        <button
                          key={group}
                          type="button"
                          tabIndex={0}
                          aria-expanded={isExpanded}
                          onClick={() => handleGroupChipClick(groupId)}
                          onKeyDown={(e) => handleGroupChipKeyDown(e, groupId)}
                          className={cn(
                            "inline-flex items-center px-2 py-0.5 text-xs font-medium rounded transition-colors",
                            "border border-slate-200 bg-slate-50 text-slate-700",
                            "hover:bg-slate-100 hover:border-slate-300",
                            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                          )}
                        >
                          <span className="truncate max-w-[200px]">
                            <span className="font-medium">{group}</span>: {summary}
                          </span>
                        </button>
                      );
                    })}
                {/* Story 27.3: Rate schedule summary */}
                {Object.keys(entry.rateSchedule).length > 0 && (
                  <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium rounded bg-slate-50 text-slate-600">
                    Schedule: {summarizeRateSchedule(entry, schemas)}
                  </span>
                )}
              </div>
            )}
            {category ? (
              <>
                <span className="inline-flex items-center px-1.5 py-0.5 text-xs font-medium bg-slate-100 text-slate-800">
                  {category.label}
                </span>
                {/* Story 25.2: Formula help popover */}
                <Popover>
                  <PopoverTrigger asChild>
                    <button
                      type="button"
                      onClick={(e) => e.stopPropagation()}
                      className="inline-flex items-center p-0.5 text-slate-500 hover:text-slate-700"
                      aria-label={`Formula help for ${category.label}`}
                    >
                      <CircleHelp className="h-3.5 w-3.5" />
                    </button>
                  </PopoverTrigger>
                  <PopoverContent className="w-64 text-xs" side="right">
                    <div className="space-y-2">
                      <div>
                        <p className="font-medium text-slate-900">Formula</p>
                        <p className="text-slate-700 font-mono bg-slate-50 px-1.5 py-0.5 rounded mt-1">
                          {category.formula_explanation}
                        </p>
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">Description</p>
                        <p className="text-slate-700">{category.description}</p>
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">Columns</p>
                        <p className="text-slate-700">{category.columns.join(", ")}</p>
                      </div>
                    </div>
                  </PopoverContent>
                </Popover>
              </>
            ) : null}
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1 shrink-0">
          {/* Story 27.4: Edit groups button - now shown whenever editableParameterGroups exists */}
          {onToggleEditGroups && entry.editableParameterGroups && entry.editableParameterGroups.length > 0 && (
            <button
              type="button"
              onClick={() => onToggleEditGroups(index)}
              className={cn(
                "border p-1",
                editGroupsIndex === index
                  ? "border-blue-500 bg-blue-50 text-blue-600"
                  : "border-slate-200 text-slate-600 hover:bg-slate-50",
              )}
              aria-label="Edit parameter groups"
              title="Customize parameter groups"
            >
              <Settings className="h-3 w-3" />
            </button>
          )}
          {/* Expand/collapse */}
          <button
            type="button"
            onClick={() => onToggleExpand(index)}
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
        <div className="border-t border-slate-200 p-3 space-y-3">
          {/* Year-indexed rate schedule editor */}
          <div>
            <p className="text-xs font-semibold text-slate-700 mb-1">
              Rate Schedule
            </p>
            <YearScheduleEditor
              schedule={
                Object.fromEntries(
                  Object.entries(entry.rateSchedule).map(([k, v]) => [Number(k), v]),
                ) as Record<number, number>
              }
              onChange={(sched) => {
                onRateScheduleChange(
                  index,
                  Object.fromEntries(
                    Object.entries(sched).map(([k, v]) => [String(k), v]),
                  ),
                );
              }}
              unit={normalizePolicyType(policyType) === "carbon_tax" || policyType === "tax" ? "€/tonne" : "€"}
            />
          </div>

          {/* Story 25.3/25.4: Parameter groups display */}
          {(parameterGroups.length > 0 || (entry.editableParameterGroups && entry.editableParameterGroups.length > 0)) && (
            <div>
              <p className="text-xs font-semibold text-slate-700 mb-2">
                Parameter Groups
              </p>
              {/* Story 25.4: Editable groups */}
              {entry.editableParameterGroups && entry.editableParameterGroups.length > 0 ? (
                <div className="space-y-2">
                  {entry.editableParameterGroups.map((group) => {
                    const compositeKey = `${entry.instanceId || `index-${index}`}:${group.id}`;
                    const isHighlighted = highlightedGroupId === compositeKey;

                    return (
                      <div
                        key={group.id}
                        data-group-key={compositeKey}
                        className={cn(
                          "border border-slate-200 rounded p-2 bg-slate-50 transition-all",
                          isHighlighted && "ring-2 ring-blue-300"
                        )}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          {/* Story 25.4: Edit mode - rename input */}
                          {editGroupsIndex === index && onGroupRename ? (
                            <Input
                              value={group.name}
                              onChange={(e) => onGroupRename(index, group.id, e.target.value)}
                              className="border-0 bg-transparent p-0 h-auto text-xs font-medium focus-visible:ring-1 focus-visible:ring-blue-500 flex-1"
                              aria-label={`Rename group ${group.name}`}
                            />
                          ) : (
                            <p className="text-xs font-medium text-slate-900">{group.name}</p>
                          )}
                          <Badge variant="outline" className="text-xs shrink-0">
                            {group.parameterIds.length} {group.parameterIds.length === 1 ? "param" : "params"}
                          </Badge>
                          {/* Story 25.4: Delete button */}
                          {editGroupsIndex === index && onDeleteGroup && (
                            <button
                              type="button"
                              onClick={() => onDeleteGroup(index, group.id)}
                              disabled={group.parameterIds.length > 0 || entry.editableParameterGroups!.length <= 1}
                              className={cn(
                                "p-1 text-red-500 hover:bg-red-50 shrink-0",
                                (group.parameterIds.length > 0 || entry.editableParameterGroups!.length <= 1) && "opacity-50 cursor-not-allowed hover:bg-transparent",
                              )}
                              aria-label="Delete group"
                              title={
                                group.parameterIds.length > 0
                                  ? "Remove all parameters before deleting this group"
                                  : entry.editableParameterGroups!.length <= 1
                                    ? "Cannot delete the last group"
                                    : "Delete group"
                              }
                            >
                              <Trash2 className="h-3 w-3" />
                            </button>
                          )}
                        </div>
                        {/* Story 25.4: Show parameters in group */}
                        {group.parameterIds.length > 0 ? (
                          <div className="text-xs text-slate-600 space-y-0.5">
                            {group.parameterIds.map((paramId) => {
                              const param = schemas.find((s) => s.id === paramId);
                              const value = resolveParameterValue(paramId, entry.parameters, param);

                              return (
                                <div key={paramId} className="flex items-center gap-2">
                                  <span>{paramId}: </span>
                                  <span className="font-mono">
                                    {value === null ? "—" : param ? formatParameterValue(value, param.unit) : String(value)}
                                  </span>
                                  {/* Story 25.4: Move dropdown */}
                                  {editGroupsIndex === index && onMoveParameter && (
                                    <select
                                      className="text-xs h-6 border border-slate-200 rounded px-1"
                                      aria-label={`Move parameter ${paramId} to`}
                                      title={`Move ${paramId} to another group`}
                                      value={group.id}
                                      onChange={(e) => onMoveParameter(index, paramId, group.id, e.target.value)}
                                    >
                                      {entry.editableParameterGroups!.map((g) => (
                                        <option key={g.id} value={g.id}>{g.name}</option>
                                      ))}
                                    </select>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="text-xs text-slate-500 italic">Parameters not yet set</div>
                        )}
                      </div>
                    );
                  })}
                    {/* Story 25.4: Add group button */}
                  {editGroupsIndex === index && onAddGroup && (
                    <button
                      type="button"
                      onClick={() => onAddGroup(index)}
                      className="w-full text-xs border border-slate-200 px-2 py-1.5 hover:bg-slate-50 rounded flex items-center justify-center gap-1"
                    >
                      <Plus className="h-3 w-3" />
                      Add group
                    </button>
                  )}
                </div>
              ) : (
                /* Story 25.3: Static groups (legacy) */
                /* Story 27.3: Dynamic parameter values instead of hardcoded placeholders */
                <div className="space-y-2">
                  {parameterGroups.map((group) => {
                    // Map group name to parameters via schemas
                    const groupParams = schemas.filter((p) => p.group === group);
                    const groupId = group.toLowerCase().replace(/\s+/g, "-");
                    const compositeKey = `${entry.instanceId || `index-${index}`}:${groupId}`;
                    const isHighlighted = highlightedGroupId === compositeKey;

                    return (
                      <div
                        key={group}
                        data-group-key={compositeKey}
                        className={cn(
                          "border border-slate-200 rounded p-2 bg-slate-50 transition-all",
                          isHighlighted && "ring-2 ring-blue-300"
                        )}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <p className="text-xs font-medium text-slate-900">{group}</p>
                          <Badge variant="outline" className="text-xs">
                            {groupParams.length} {groupParams.length === 1 ? "param" : "params"}
                          </Badge>
                        </div>
                        {/* Show actual parameter values (Story 27.3) */}
                        {groupParams.length > 0 ? (
                          <div className="text-xs text-slate-600 space-y-0.5">
                            {groupParams.map((param) => {
                              const value = resolveParameterValue(param.id, entry.parameters, param);
                              if (value === null) {
                                return (
                                  <div key={param.id}>
                                    <span>{param.id}: </span>
                                    <span className="font-mono">—</span>
                                  </div>
                                );
                              }
                              return (
                                <div key={param.id}>
                                  <span>{param.id}: </span>
                                  <span className="font-mono">{formatParameterValue(value, param.unit)}</span>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <div className="text-xs text-slate-500 italic">Parameters not yet set</div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* ParameterRow editing (when schemas available) */}
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
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
