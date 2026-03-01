import { Clock3, Copy, Play, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Scenario } from "@/data/mock-data";

interface ScenarioCardProps {
  scenario: Scenario;
  selected: boolean;
  onSelect: (id: string) => void;
  onRun: (id: string) => void;
  onCompare: (id: string) => void;
  onClone: (id: string) => void;
  onDelete: (id: string) => void;
}

function mapStatusToVariant(status: Scenario["status"]) {
  switch (status) {
    case "completed":
      return "success" as const;
    case "running":
      return "warning" as const;
    case "failed":
      return "destructive" as const;
    default:
      return "default" as const;
  }
}

export function ScenarioCard({ scenario, selected, onSelect, onRun, onCompare, onClone, onDelete }: ScenarioCardProps) {
  return (
    <Card
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      className={`cursor-pointer ${selected ? "border-blue-500 bg-blue-50" : "border-slate-200 bg-white"} focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500`}
      onClick={() => onSelect(scenario.id)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect(scenario.id);
        }
      }}
    >
      <CardHeader className="p-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-xs">{scenario.name}</CardTitle>
          <Badge variant={mapStatusToVariant(scenario.status)}>{scenario.status}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 p-2">
        <p className="text-xs text-slate-600">
          {scenario.parameterChanges} parameter{scenario.parameterChanges === 1 ? "" : "s"} changed
        </p>
        <p className="flex items-center gap-1 text-xs text-slate-500">
          <Clock3 className="h-3 w-3" />
          {scenario.lastRun ?? "Not run yet"}
        </p>
        <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
          <Button size="sm" className="w-full" onClick={() => onRun(scenario.id)}>
            <Play className="h-3 w-3" />
            Run
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="w-full"
            onClick={() => onCompare(scenario.id)}
          >
            Compare
          </Button>
          <Button
            size="sm"
            variant="ghost"
            aria-label="Clone scenario"
            onClick={() => onClone(scenario.id)}
          >
            <Copy className="h-3 w-3" />
          </Button>
          {!scenario.isBaseline ? (
            <Button
              size="sm"
              variant="ghost"
              aria-label="Delete scenario"
              onClick={() => onDelete(scenario.id)}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
