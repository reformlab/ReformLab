// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * MobileStageSwitcher — horizontal stage navigation for narrow screens.
 *
 * Story 22.7 — AC-2: Stage navigation reachable from every screen at phone width.
 * Replaces the WorkflowNavRail on mobile (< lg breakpoint) with a horizontal
 * scrollable list of stage buttons.
 *
 * Shows all 4 canonical workflow stages with the active stage highlighted.
 * Hidden on desktop (lg+) where WorkflowNavRail is used instead.
 */

import type { StageKey, SubView } from "@/types/workspace";
import { STAGES } from "@/types/workspace";
import { cn } from "@/lib/utils";

export interface MobileStageSwitcherProps {
  activeStage: StageKey;
  navigateTo: (stage: StageKey, subView?: SubView | null) => void;
}

export function MobileStageSwitcher({ activeStage, navigateTo }: MobileStageSwitcherProps) {
  return (
    <nav
      aria-label="Mobile stage navigation"
      className="flex lg:hidden items-center gap-2 overflow-x-auto px-4 py-2 border-b border-slate-200 bg-white shrink-0"
    >
      {STAGES.map((stage) => {
        const active = stage.activeFor.includes(activeStage);
        return (
          <button
            key={stage.key}
            type="button"
            aria-label={stage.label}
            aria-pressed={active}
            onClick={() => { navigateTo(stage.key); }}
            className={cn(
              "flex-shrink-0 px-3 py-1.5 text-sm font-medium rounded-full transition-colors",
              active
                ? "bg-blue-500 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200",
            )}
          >
            {stage.label}
          </button>
        );
      })}
    </nav>
  );
}
