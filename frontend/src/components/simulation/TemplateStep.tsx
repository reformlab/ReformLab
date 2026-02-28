import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { mockTemplates, type Template } from "@/data/mock-data";

/** Type badge colors */
const typeColors: Record<string, string> = {
  "carbon-tax": "bg-amber-50 text-amber-700 border-amber-200",
  subsidy: "bg-emerald-50 text-emerald-700 border-emerald-200",
  feebate: "bg-violet-50 text-violet-700 border-violet-200",
};

interface TemplateStepProps {
  /** Currently selected template id */
  selectedId: string | null;
  /** Called when a template is selected */
  onSelect: (id: string) => void;
}

export default function TemplateStep({
  selectedId,
  onSelect,
}: TemplateStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-slate-800">
          Select Template
        </h2>
        <p className="text-sm text-slate-500 mt-1">
          Choose a policy template. Selecting a template pre-fills parameters
          with sensible defaults.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {mockTemplates.map((tpl: Template) => {
          const isSelected = selectedId === tpl.id;
          return (
            <Card
              key={tpl.id}
              className={cn(
                "cursor-pointer transition-colors border",
                isSelected
                  ? "border-blue-300 bg-blue-50"
                  : "border-slate-200 hover:border-slate-300",
              )}
              onClick={() => onSelect(tpl.id)}
            >
              <CardContent className="p-3">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <div
                      className={cn(
                        "flex h-7 w-7 items-center justify-center rounded shrink-0",
                        isSelected
                          ? "bg-blue-100 text-blue-600"
                          : "bg-slate-100 text-slate-400",
                      )}
                    >
                      {isSelected ? (
                        <Check className="h-3.5 w-3.5" />
                      ) : (
                        <FileText className="h-3.5 w-3.5" />
                      )}
                    </div>
                    <h3 className="text-sm font-medium text-slate-800">
                      {tpl.name}
                    </h3>
                  </div>
                  <Badge
                    variant="outline"
                    className={cn("text-xs shrink-0", typeColors[tpl.type] ?? "")}
                  >
                    {tpl.type}
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  {tpl.description}
                </p>
                <p className="text-xs text-slate-400 font-mono mt-1">
                  {tpl.parameterCount} parameters
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
