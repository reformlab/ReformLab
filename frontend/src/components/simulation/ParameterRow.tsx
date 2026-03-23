// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import type { Parameter } from "@/data/mock-data";

interface ParameterRowProps {
  parameter: Parameter;
  value: number;
  onChange: (nextValue: number) => void;
}

function formatValue(parameter: Parameter, value: number): string {
  if (parameter.unit === "%") {
    return `${Math.round(value * 100)}%`;
  }
  return `${value} ${parameter.unit}`;
}

export function ParameterRow({ parameter, value, onChange }: ParameterRowProps) {
  const [editing, setEditing] = useState(false);
  const delta = useMemo(() => value - parameter.baseline, [parameter.baseline, value]);
  const hasDelta = Math.abs(delta) > 1e-6;

  return (
    <div className="border-b border-slate-200 p-3 hover:bg-slate-50">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm text-slate-900">{parameter.label}</p>
          <p className="text-xs text-slate-500">
            Baseline <span className="data-mono">{formatValue(parameter, parameter.baseline)}</span>
          </p>
        </div>
        <div className="flex items-center gap-2">
          {hasDelta ? (
            <Badge variant="info" className="data-mono">
              {delta > 0 ? "+" : ""}
              {parameter.unit === "%" ? `${Math.round(delta * 100)}%` : delta}
            </Badge>
          ) : (
            <Badge variant="default">Unchanged</Badge>
          )}
          <button
            type="button"
            className="border border-slate-300 px-2 py-1 text-xs"
            onClick={() => setEditing((current) => !current)}
          >
            {editing ? "Done" : "Edit"}
          </button>
        </div>
      </div>

      <div className="mt-2">
        <p className="data-mono text-sm font-medium text-slate-800">{formatValue(parameter, value)}</p>
      </div>

      {editing ? (
        <div className="mt-2 space-y-2">
          {parameter.type === "slider" && typeof parameter.min === "number" && typeof parameter.max === "number" ? (
            <Slider
              min={parameter.min}
              max={parameter.max}
              step={parameter.unit === "%" ? 0.01 : 1}
              value={[value]}
              onValueChange={(next) => onChange(next[0] ?? value)}
              aria-label={`Edit ${parameter.label}`}
            />
          ) : null}
          <Input
            type="number"
            value={value}
            onChange={(event) => onChange(Number(event.target.value))}
            className="data-mono"
            aria-label={`Input ${parameter.label}`}
          />
        </div>
      ) : null}
    </div>
  );
}
