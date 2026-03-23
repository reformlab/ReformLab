// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { useMemo } from "react";

import { ParameterRow } from "@/components/simulation/ParameterRow";
import type { Parameter } from "@/data/mock-data";

interface ParameterEditingScreenProps {
  parameters: Parameter[];
  parameterValues: Record<string, number>;
  onParameterChange: (id: string, value: number) => void;
}

export function ParameterEditingScreen({
  parameters,
  parameterValues,
  onParameterChange,
}: ParameterEditingScreenProps) {
  const grouped = useMemo(() => {
    const groups = new Map<string, Parameter[]>();
    for (const parameter of parameters) {
      const current = groups.get(parameter.group) ?? [];
      current.push(parameter);
      groups.set(parameter.group, current);
    }
    return Array.from(groups.entries());
  }, [parameters]);

  return (
    <section className="space-y-4">
      {grouped.map(([groupName, groupParameters]) => (
        <div key={groupName} className="rounded-lg border border-slate-200 bg-white">
          <h3 className="border-b border-slate-200 bg-slate-50 p-3 text-sm font-semibold">{groupName}</h3>
          {groupParameters.map((parameter) => (
            <ParameterRow
              key={parameter.id}
              parameter={parameter}
              value={parameterValues[parameter.id] ?? parameter.value}
              onChange={(next) => onParameterChange(parameter.id, next)}
            />
          ))}
        </div>
      ))}
    </section>
  );
}
