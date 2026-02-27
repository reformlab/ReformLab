import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Template } from "@/data/mock-data";

interface TemplateSelectionScreenProps {
  templates: Template[];
  selectedTemplateId: string;
  onSelectTemplate: (id: string) => void;
}

export function TemplateSelectionScreen({
  templates,
  selectedTemplateId,
  onSelectTemplate,
}: TemplateSelectionScreenProps) {
  return (
    <section className="grid gap-2 xl:grid-cols-2">
      {templates.map((template) => {
        const selected = selectedTemplateId === template.id;
        return (
          <button
            type="button"
            key={template.id}
            onClick={() => onSelectTemplate(template.id)}
            className="text-left"
          >
            <Card className={selected ? "border-blue-500 bg-blue-50" : "border-slate-200 bg-white"}>
              <CardHeader>
                <CardTitle>{template.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-700">{template.description}</p>
                <p className="data-mono mt-1 text-xs text-slate-500">
                  {template.parameterCount} parameters
                </p>
              </CardContent>
            </Card>
          </button>
        );
      })}
    </section>
  );
}
