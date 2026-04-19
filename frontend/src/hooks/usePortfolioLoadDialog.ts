// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Dialog state and load flow for saved policy portfolios. */

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { ApiError } from "@/api/client";
import { getPortfolio } from "@/api/portfolios";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import type { EditableParameterGroup, PortfolioPolicyItem } from "@/api/types";
import type { Template } from "@/data/mock-data";

// Story 25.4: Default parameter-to-group assignments for migration
const DEFAULT_PARAM_ASSIGNMENTS: Record<string, string[]> = {
  "Mechanism": ["rate", "unit"],
  "Eligibility": ["threshold", "ceiling", "income_cap"],
  "Schedule": [], // Uses year schedule editor
  "Redistribution": ["divisible", "recipients", "income_weights"],
};

interface LoadedPortfolioRef {
  current: string | null;
}

interface UsePortfolioLoadDialogParams<ResolutionStrategy extends string> {
  templates: Template[];
  activeScenarioPortfolioName: string | null | undefined;
  compositionLength: number;
  validStrategies: readonly ResolutionStrategy[];
  defaultResolutionStrategy: ResolutionStrategy;
  loadedPortfolioRef: LoadedPortfolioRef;
  setComposition: (composition: CompositionEntry[]) => void;
  setResolutionStrategy: (strategy: ResolutionStrategy) => void;
  setActivePortfolioName: (name: string | null) => void;
  updateScenarioPortfolioName: (name: string | null) => void;
  setSelectedPortfolioName: (name: string | null) => void;
  // Story 25.2: Setter for instance counter (ref-based to avoid stale closure)
  setInstanceCounter?: (value: number) => void;
}

export function usePortfolioLoadDialog<ResolutionStrategy extends string>({
  templates,
  activeScenarioPortfolioName,
  compositionLength,
  validStrategies,
  defaultResolutionStrategy,
  loadedPortfolioRef,
  setComposition,
  setResolutionStrategy,
  setActivePortfolioName,
  updateScenarioPortfolioName,
  setSelectedPortfolioName,
  setInstanceCounter,
}: UsePortfolioLoadDialogParams<ResolutionStrategy>) {
  const [loadDialogOpen, setLoadDialogOpen] = useState(false);

  const loadPortfolioIntoComposition = useCallback(async (name: string): Promise<boolean> => {
    try {
      const detail = await getPortfolio(name);
      // Story 25.2: Generate unique instance IDs for each loaded policy
      const entries: CompositionEntry[] = detail.policies.map((policy, index) => {
        const template = templates.find((tmpl) => tmpl.type.replace(/-/g, "_") === policy.policy_type);
        const templateId = template?.id ?? policy.policy_type;

        // Story 25.4: Restore or migrate editable parameter groups
        let editableParameterGroups: EditableParameterGroup[] | undefined;
        const policyEditableGroups = (policy as PortfolioPolicyItem & { editable_parameter_groups?: EditableParameterGroup[] }).editable_parameter_groups;
        const policyParameterGroups = (policy as PortfolioPolicyItem & { parameter_groups?: string[] }).parameter_groups;

        if (policyEditableGroups && policyEditableGroups.length > 0) {
          // Use editable groups from saved portfolio
          editableParameterGroups = policyEditableGroups;
        } else if (policyParameterGroups && policyParameterGroups.length > 0) {
          // Migrate from parameter_groups string array to editable structure
          editableParameterGroups = policyParameterGroups.map((groupName: string, idx: number) => ({
            id: `group-${idx}`,
            name: groupName,
            parameterIds: DEFAULT_PARAM_ASSIGNMENTS[groupName] ?? [],
          }));
        }
        // Note: If neither exists, the parameter groups will be generated from template defaults

        return {
          instanceId: `${templateId}-ins${index}`, // Use index for initial load
          templateId,
          name: policy.name,
          parameters: Object.fromEntries(
            Object.entries(policy.parameters).filter(([, value]) => typeof value === "number"),
          ) as Record<string, number>,
          rateSchedule: policy.rate_schedule,
          // Story 25.3: Restore from-scratch policy fields
          policy_type: policy.policy_type,
          category_id: policy.category_id,
          parameter_groups: (policy as PortfolioPolicyItem & { parameter_groups?: string[] }).parameter_groups,
          // Story 25.4: Restore editable parameter groups
          editableParameterGroups,
        };
      });
      setComposition(entries);
      // Story 25.2: Update instance counter to prevent collisions with loaded items
      if (setInstanceCounter) {
        setInstanceCounter(detail.policies.length);
      }
      setResolutionStrategy(
        validStrategies.includes(detail.resolution_strategy as ResolutionStrategy)
          ? (detail.resolution_strategy as ResolutionStrategy)
          : defaultResolutionStrategy,
      );
      setActivePortfolioName(name);
      return true;
    } catch (err) {
      if (err instanceof ApiError) {
        toast.warning(`Could not load policy set '${name}': ${err.why}`);
      } else {
        toast.warning(`Could not load policy set '${name}'`);
      }
      return false;
    }
  }, [
    templates,
    validStrategies,
    defaultResolutionStrategy,
    setComposition,
    setInstanceCounter,
    setResolutionStrategy,
    setActivePortfolioName,
  ]);

  useEffect(() => {
    if (!activeScenarioPortfolioName) return;
    if (compositionLength > 0) return;
    if (loadedPortfolioRef.current === activeScenarioPortfolioName) return;

    loadedPortfolioRef.current = activeScenarioPortfolioName;
    void loadPortfolioIntoComposition(activeScenarioPortfolioName).then((loaded) => {
      if (!loaded && loadedPortfolioRef.current === activeScenarioPortfolioName) {
        loadedPortfolioRef.current = null;
      }
    });
  }, [
    activeScenarioPortfolioName,
    compositionLength,
    loadedPortfolioRef,
    loadPortfolioIntoComposition,
  ]);

  const openLoadDialog = useCallback(() => {
    setLoadDialogOpen(true);
  }, []);

  const closeLoadDialog = useCallback(() => {
    setLoadDialogOpen(false);
  }, []);

  const handleLoad = useCallback(async (name: string) => {
    const ok = await loadPortfolioIntoComposition(name);
    if (!ok) return;

    loadedPortfolioRef.current = name;
    updateScenarioPortfolioName(name);
    setSelectedPortfolioName(name);
    setLoadDialogOpen(false);
    toast.success(`Loaded policy set '${name}'`);
  }, [
    loadPortfolioIntoComposition,
    loadedPortfolioRef,
    updateScenarioPortfolioName,
    setSelectedPortfolioName,
  ]);

  return {
    loadDialogOpen,
    openLoadDialog,
    closeLoadDialog,
    handleLoad,
  };
}
