import { useMemo } from "react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { ChevronDown } from "lucide-react";
import ParameterRow from "./ParameterRow";
import type { Parameter } from "@/data/mock-data";

interface ParametersStepProps {
  /** Parameters to display */
  parameters: Parameter[];
  /** Called when a parameter value changes */
  onParameterChange: (id: string, value: number) => void;
}

export default function ParametersStep({
  parameters,
  onParameterChange,
}: ParametersStepProps) {
  /** Group parameters by their group field */
  const groups = useMemo(() => {
    const map = new Map<string, Parameter[]>();
    for (const p of parameters) {
      const existing = map.get(p.group);
      if (existing) {
        existing.push(p);
      } else {
        map.set(p.group, [p]);
      }
    }
    return Array.from(map.entries());
  }, [parameters]);

  return (
    <div className="space-y-2">
      {groups.map(([group, params]) => (
        <Collapsible key={group} defaultOpen>
          <CollapsibleTrigger className="flex w-full items-center justify-between rounded px-2 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500 hover:bg-slate-50">
            <span>{group}</span>
            <ChevronDown className="h-3.5 w-3.5 transition-transform [[data-state=closed]>&]:rotate-[-90deg]" />
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="space-y-0">
              {params.map((param) => (
                <ParameterRow
                  key={param.id}
                  parameter={param}
                  onChange={onParameterChange}
                />
              ))}
            </div>
          </CollapsibleContent>
        </Collapsible>
      ))}
    </div>
  );
}
