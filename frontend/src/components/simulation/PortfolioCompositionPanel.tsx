// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
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
 *
 * Story 25.2: Category badges and duplicate instance support.
 * Story 25.3: From-scratch policies with policy_type and category_id fields.
 */

import { useState, useEffect } from "react";
import { ArrowUp, ArrowDown, Trash2, ChevronDown, ChevronRight, CircleHelp, Settings, Plus, AlertCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { ParameterRow } from "@/components/simulation/ParameterRow";
import { YearScheduleEditor } from "@/components/simulation/YearScheduleEditor";
// Story 25.3: Import shared type constants
import { TYPE_COLORS, TYPE_LABELS } from "@/components/simulation/typeConstants";
import { cn } from "@/lib/utils";
import type { Template, Parameter } from "@/data/mock-data";
import type { Category, EditableParameterGroup } from "@/api/types";
import { Input } from "@/components/ui/input";
// Story 25.6: Import validation error type
import type { PolicyValidationError } from "@/components/simulation/portfolioValidation";

export interface CompositionEntry {
  templateId: string;
  name: string;
  parameters: Record<string, number>;
  /** Year-indexed rate schedule; keys are year strings for JSON wire format. */
  rateSchedule: Record<string, number>;
  /** Story 25.2: Unique instance ID for duplicate policy support */
  instanceId?: string;
  /** Story 25.3: Policy type for from-scratch policies (optional, inferred from template for templates) */
  policy_type?: string;
  /** Story 25.3: Category ID for from-scratch policies (optional) */
  category_id?: string;
  /** Story 25.3: Parameter groups for from-scratch policies */
  parameter_groups?: string[];
  /** Story 25.4: Editable parameter groups */
  editableParameterGroups?: EditableParameterGroup[];
}

interface PortfolioCompositionPanelProps {
  templates: Template[];
  composition: CompositionEntry[];
  onReorder: (fromIndex: number, toIndex: number) => void;
  onRemove: (index: number) => void;
  onParameterChange: (index: number, paramId: string, value: number) => void;
  onRateScheduleChange: (index: number, schedule: Record<string, number>) => void;
  /** Optional parameter schemas per template — used for inline editing */
  parameterSchemas?: Record<string, Parameter[]>;
  /**
   * Minimum number of policies required before showing the "add more" warning.
   * Defaults to 1.
   */
  minimumPolicies?: number;
  /** Story 25.2: Categories for category badge display */
  categories?: Category[] | null;
  /** Story 25.3: Instance ID to auto-expand on mount (for newly created policies) */
  autoExpandInstanceId?: string | null;
  /** Story 25.4: Index of card in edit-groups mode (null = none) */
  editGroupsIndex?: number | null;
  /** Story 25.4: Callback to toggle edit-groups mode */
  onToggleEditGroups?: (index: number) => void;
  /** Story 25.4: Callback to rename a group */
  onGroupRename?: (policyIndex: number, groupId: string, newName: string) => void;
  /** Story 25.4: Callback to add a new group */
  onAddGroup?: (policyIndex: number) => void;
  /** Story 25.4: Callback to delete a group */
  onDeleteGroup?: (policyIndex: number, groupId: string) => void;
  /** Story 25.4: Callback to move parameter between groups */
  onMoveParameter?: (policyIndex: number, paramId: string, fromGroupId: string, toGroupId: string) => void;
  /** Story 25.6: Validation errors for policies in the composition */
  validationErrors?: PolicyValidationError[];
}

export function PortfolioCompositionPanel({
  templates,
  composition,
  onReorder,
  onRemove,
  onParameterChange,
  onRateScheduleChange,
  parameterSchemas = {},
  minimumPolicies = 1,
  categories,
  autoExpandInstanceId,
  editGroupsIndex = null,
  onToggleEditGroups,
  onGroupRename,
  onAddGroup,
  onDeleteGroup,
  onMoveParameter,
  validationErrors = [],
}: PortfolioCompositionPanelProps) {
  const [expandedIndices, setExpandedIndices] = useState<Set<number>>(new Set());

  // Story 25.3: Auto-expand the newly created policy when autoExpandInstanceId changes
  useEffect(() => {
    if (autoExpandInstanceId !== null) {
      const index = composition.findIndex((c) => c.instanceId === autoExpandInstanceId);
      if (index !== -1) {
        setExpandedIndices((prev) => new Set(prev).add(index));
      }
    }
  }, [autoExpandInstanceId, composition]);

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
        {composition.length < minimumPolicies ? (
          <p className="mt-1 text-xs text-amber-600">
            Add at least {minimumPolicies} {minimumPolicies === 1 ? "policy" : "policies"} to save a policy set.
          </p>
        ) : null}
      </div>
    );
  }

  return (
    <section aria-label="Policy Set Composition" className="space-y-2">
      {composition.length < minimumPolicies ? (
        <p className="text-xs text-amber-600 border border-amber-200 bg-amber-50 p-2">
          Add at least {minimumPolicies} {minimumPolicies === 1 ? "policy" : "policies"} to save a policy set.
        </p>
      ) : null}

      {composition.map((entry, index) => {
        const template = templates.find((t) => t.id === entry.templateId);
        const isFirst = index === 0;
        const isLast = index === composition.length - 1;
        const isExpanded = expandedIndices.has(index);
        const schemas = parameterSchemas[entry.templateId] ?? [];

        // Story 25.2: Look up category by template.category_id
        // Story 25.3: For from-scratch policies, use entry.category_id directly
        const category = entry.category_id && categories
          ? categories.find((c) => c.id === entry.category_id)
          : template?.category_id && categories
            ? categories.find((c) => c.id === template.category_id)
            : null;

        // Story 25.3: Determine policy type - use entry.policy_type for from-scratch, template.type for templates
        const policyType = entry.policy_type ?? template?.type;
        const parameterGroups = entry.parameter_groups ?? [];

        // Story 25.6: Check if this policy has validation errors
        const policyError = validationErrors.find((err) => err.policyIndex === index);

        return (
          <div
            key={entry.instanceId || `${entry.templateId}-${index}`}
            className={cn(
              "border bg-white",
              editGroupsIndex === index ? "border-blue-500" : "border-slate-200",
              policyError ? "border-red-300 bg-red-50/30" : "",
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
                  {policyError && (
                    <Badge variant="default" className="text-xs shrink-0 bg-red-500 text-white flex items-center gap-1">
                      <AlertCircle className="h-3 w-3" />
                      Error
                    </Badge>
                  )}
                  {/* Story 25.4: Editing badge */}
                  {editGroupsIndex === index && (
                    <Badge variant="default" className="text-xs shrink-0 bg-blue-500 text-white">
                      Editing
                    </Badge>
                  )}
                  <p className="text-sm font-medium text-slate-900 truncate">
                    {entry.name || template?.name || entry.templateId}
                  </p>
                  {/* Story 25.3: Type badge - use policyType variable */}
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
                  {/* Story 25.3: Parameter count badge - only show for template-based policies */}
                  {template && (
                    <Badge variant="default" className="text-xs shrink-0">
                      {template.parameterCount} params
                    </Badge>
                  )}
                  {/* Story 25.2: Category badge with neutral slate color */}
                  {/* Story 25.3: Show category badge for both template and from-scratch policies */}
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
                {/* Story 25.4: Edit groups button */}
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
              <div className="border-t border-slate-200 p-3 space-y-3">
                {/* Year-indexed rate schedule editor (AC-4) */}
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
                    unit={policyType?.replace(/-/g, "_") === "carbon_tax" || policyType === "tax" ? "€/tonne" : "€"}
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
                        {entry.editableParameterGroups.map((group) => (
                          <div
                            key={group.id}
                            className="border border-slate-200 rounded p-2 bg-slate-50"
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
                            {group.parameterIds.length > 0 && (
                              <div className="text-xs text-slate-600 space-y-0.5">
                                {group.parameterIds.map((paramId) => (
                                  <div key={paramId} className="flex items-center gap-2">
                                    <span>{paramId}: <span className="font-mono">{String(entry.parameters[paramId] ?? 0)}</span></span>
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
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
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
                      <div className="space-y-2">
                        {parameterGroups.map((group) => (
                          <div
                            key={group}
                            className="border border-slate-200 rounded p-2 bg-slate-50"
                          >
                            <div className="flex items-center justify-between mb-1">
                              <p className="text-xs font-medium text-slate-900">{group}</p>
                              <Badge variant="outline" className="text-xs">
                                {/* Show parameter count based on group */}
                                {group === "Mechanism" && "2 params"}
                                {group === "Eligibility" && "2 params"}
                                {group === "Schedule" && "0 params"}
                                {group === "Redistribution" && "2 params"}
                              </Badge>
                            </div>
                            {/* Show placeholder parameter values */}
                            {group === "Mechanism" && (
                              <div className="text-xs text-slate-600 space-y-0.5">
                                <div>rate: <span className="font-mono">0</span></div>
                                <div>unit: <span className="font-mono">EUR</span></div>
                              </div>
                            )}
                            {group === "Eligibility" && (
                              <div className="text-xs text-slate-600 space-y-0.5">
                                <div>threshold: <span className="font-mono">0</span></div>
                                <div>ceiling: <span className="font-mono">null</span></div>
                              </div>
                            )}
                            {group === "Schedule" && (
                              <div className="text-xs text-slate-500 italic">No years configured</div>
                            )}
                            {group === "Redistribution" && (
                              <div className="text-xs text-slate-600 space-y-0.5">
                                <div>divisible: <span className="font-mono">true</span></div>
                                <div>recipients: <span className="font-mono">all</span></div>
                              </div>
                            )}
                          </div>
                        ))}
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
      })}
    </section>
  );
}
