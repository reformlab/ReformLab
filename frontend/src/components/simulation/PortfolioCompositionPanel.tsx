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
 * Story 27.3: Show actual parameter values inline in policy cards.
 * Story 27.4: Unified PolicyCard component for all policy sources.
 */

import { useState, useEffect, useCallback } from "react";
import { PolicyCard } from "@/components/simulation/PolicyCard";
import type { Template, Parameter } from "@/data/mock-data";
// Story 27.11: Import CompositionEntry from api/types (moved from PortfolioCompositionPanel)
import type { CompositionEntry, Category } from "@/api/types";
// Story 25.6: Import validation error type
import type { PolicyValidationError } from "@/components/simulation/portfolioValidation";

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
  // Story 27.4: Track expanded indices as a Set for parent-controlled expand state
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

  const toggleExpanded = useCallback((index: number) => {
    setExpandedIndices((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  }, []);

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

        // Story 25.6: Check if this policy has validation errors
        const policyError = validationErrors.find((err) => err.policyIndex === index);

        return (
          <PolicyCard
            key={entry.instanceId || `${entry.templateId}-${index}`}
            entry={entry}
            template={template}
            schemas={schemas}
            index={index}
            isFirst={isFirst}
            isLast={isLast}
            isExpanded={isExpanded}
            categories={categories}
            editGroupsIndex={editGroupsIndex}
            validationError={policyError}
            onToggleExpand={toggleExpanded}
            onToggleEditGroups={onToggleEditGroups}
            onGroupRename={onGroupRename}
            onAddGroup={onAddGroup}
            onDeleteGroup={onDeleteGroup}
            onMoveParameter={onMoveParameter}
            onRemove={onRemove}
            onReorder={onReorder}
            onParameterChange={onParameterChange}
            onRateScheduleChange={onRateScheduleChange}
          />
        );
      })}
    </section>
  );
}
