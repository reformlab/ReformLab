import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { mockPopulations, type Population } from "@/data/mock-data";

interface PopulationStepProps {
  /** Currently selected population id */
  selectedId: string | null;
  /** Called when a population is selected */
  onSelect: (id: string) => void;
}

export default function PopulationStep({
  selectedId,
  onSelect,
}: PopulationStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-800">
          Select Population
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Choose a synthetic population dataset for your simulation.
        </p>
      </div>

      <div className="grid gap-3">
        {mockPopulations.map((pop: Population) => {
          const isSelected = selectedId === pop.id;
          return (
            <Card
              key={pop.id}
              className={cn(
                "cursor-pointer transition-colors border",
                isSelected
                  ? "border-blue-300 bg-blue-50"
                  : "border-slate-200 hover:border-slate-300",
              )}
              onClick={() => onSelect(pop.id)}
            >
              <CardContent className="flex items-center justify-between p-3">
                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded",
                      isSelected
                        ? "bg-blue-100 text-blue-600"
                        : "bg-slate-100 text-slate-400",
                    )}
                  >
                    {isSelected ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <Users className="h-4 w-4" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-800">
                      {pop.name}
                    </p>
                    <p className="text-xs text-slate-500">
                      {pop.source} &middot; {pop.year}
                    </p>
                  </div>
                </div>
                <Badge
                  variant="secondary"
                  className="text-xs font-mono bg-slate-100 text-slate-600"
                >
                  {pop.households.toLocaleString()} households
                </Badge>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
