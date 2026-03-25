// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { useEffect, useState } from "react";
import { ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { getHelpEntry } from "@/components/help/help-content";
import type { StageKey, SubView } from "@/types/workspace";

interface ContextualHelpPanelProps {
  activeStage: StageKey;
  activeSubView: SubView | null;
}

export function ContextualHelpPanel({ activeStage, activeSubView }: ContextualHelpPanelProps) {
  const help = getHelpEntry(activeStage, activeSubView);
  const [conceptsOpen, setConceptsOpen] = useState(false);

  useEffect(() => {
    setConceptsOpen(false);
  }, [activeStage, activeSubView]);

  return (
    <div className="space-y-3">
      {/* Title */}
      <p className="text-sm font-semibold text-slate-900">{help.title}</p>

      {/* Summary */}
      <p className="text-xs leading-normal text-slate-600">{help.summary}</p>

      {/* Tips */}
      <ul className="list-disc space-y-1 pl-4">
        {help.tips.map((tip, i) => (
          <li key={i} className="text-xs text-slate-500">{tip}</li>
        ))}
      </ul>

      {/* Key Concepts (collapsible) */}
      {help.concepts && help.concepts.length > 0 ? (
        <Collapsible open={conceptsOpen} onOpenChange={setConceptsOpen}>
          <CollapsibleTrigger className="flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-800">
            <ChevronRight
              className={cn(
                "h-3 w-3 transition-transform",
                conceptsOpen && "rotate-90",
              )}
            />
            Key Concepts
          </CollapsibleTrigger>
          <CollapsibleContent>
            <dl className="mt-1.5 space-y-1.5 pl-4">
              {help.concepts.map((c) => (
                <div key={c.term}>
                  <dt className="text-xs font-medium text-slate-700">
                    {c.term}
                  </dt>
                  <dd className="text-xs leading-normal text-slate-500">
                    {c.definition}
                  </dd>
                </div>
              ))}
            </dl>
          </CollapsibleContent>
        </Collapsible>
      ) : null}
    </div>
  );
}
