import { Clock3, Play, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Scenario } from "@/data/mock-data";

interface ScenarioCardProps {
  scenario: Scenario;
  selected: boolean;
  onRun: (id: string) => void;
  onCompare: (id: string) => void;
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

export function ScenarioCard({ scenario, selected, onRun, onCompare }: ScenarioCardProps) {
  return (
    <Card className={selected ? "border-blue-500 bg-blue-50" : "border-slate-200 bg-white"}>
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
        <div className="flex gap-1">
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
          <Button size="sm" variant="ghost" aria-label="Delete scenario" disabled={scenario.isBaseline}>
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
