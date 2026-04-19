// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/** Dialog state and load flow for saved policy portfolios. */

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";

import { ApiError } from "@/api/client";
import { getPortfolio } from "@/api/portfolios";
import type { CompositionEntry } from "@/components/simulation/PortfolioCompositionPanel";
import type { Template } from "@/data/mock-data";

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
  setSelectedTemplateIds: (ids: string[]) => void;
  setResolutionStrategy: (strategy: ResolutionStrategy) => void;
  setActivePortfolioName: (name: string | null) => void;
  updateScenarioPortfolioName: (name: string | null) => void;
  setSelectedPortfolioName: (name: string | null) => void;
}

export function usePortfolioLoadDialog<ResolutionStrategy extends string>({
  templates,
  activeScenarioPortfolioName,
  compositionLength,
  validStrategies,
  defaultResolutionStrategy,
  loadedPortfolioRef,
  setComposition,
  setSelectedTemplateIds,
  setResolutionStrategy,
  setActivePortfolioName,
  updateScenarioPortfolioName,
  setSelectedPortfolioName,
}: UsePortfolioLoadDialogParams<ResolutionStrategy>) {
  const [loadDialogOpen, setLoadDialogOpen] = useState(false);

  const loadPortfolioIntoComposition = useCallback(async (name: string): Promise<boolean> => {
    try {
      const detail = await getPortfolio(name);
      const entries: CompositionEntry[] = detail.policies.map((policy) => {
        const template = templates.find((tmpl) => tmpl.type.replace(/-/g, "_") === policy.policy_type);
        return {
          templateId: template?.id ?? policy.policy_type,
          name: policy.name,
          parameters: Object.fromEntries(
            Object.entries(policy.parameters).filter(([, value]) => typeof value === "number"),
          ) as Record<string, number>,
          rateSchedule: policy.rate_schedule,
        };
      });
      setComposition(entries);
      setSelectedTemplateIds(entries.map((entry) => entry.templateId));
      setResolutionStrategy(
        validStrategies.includes(detail.resolution_strategy as ResolutionStrategy)
          ? (detail.resolution_strategy as ResolutionStrategy)
          : defaultResolutionStrategy,
      );
      setActivePortfolioName(name);
      return true;
    } catch (err) {
      if (err instanceof ApiError) {
        toast.warning(`Could not load portfolio '${name}': ${err.why}`);
      } else {
        toast.warning(`Could not load portfolio '${name}'`);
      }
      return false;
    }
  }, [
    templates,
    validStrategies,
    defaultResolutionStrategy,
    setComposition,
    setSelectedTemplateIds,
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
    toast.success(`Loaded portfolio '${name}'`);
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
