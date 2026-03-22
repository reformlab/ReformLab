import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Plus, Trash2, X } from "lucide-react";
import { SelectionGrid } from "@/components/simulation/SelectionGrid";
import type { Template } from "@/data/mock-data";
import { createCustomTemplate } from "@/api/templates";

interface TemplateSelectionScreenProps {
  templates: Template[];
  selectedTemplateId: string;
  onSelectTemplate: (id: string) => void;
  onTemplatesChanged?: () => void;
}

interface ParamRow {
  name: string;
  type: string;
  default_value: string;
  unit: string;
}

const emptyParam: ParamRow = { name: "", type: "float", default_value: "0", unit: "" };

export function TemplateSelectionScreen({
  templates,
  selectedTemplateId,
  onSelectTemplate,
  onTemplatesChanged,
}: TemplateSelectionScreenProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [params, setParams] = useState<ParamRow[]>([{ ...emptyParam }]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function resetForm() {
    setName("");
    setDescription("");
    setParams([{ ...emptyParam }]);
    setError(null);
  }

  function updateParam(index: number, field: keyof ParamRow, value: string) {
    setParams((prev) =>
      prev.map((p, i) => (i === index ? { ...p, [field]: value } : p)),
    );
  }

  function addParam() {
    setParams((prev) => [...prev, { ...emptyParam }]);
  }

  function removeParam(index: number) {
    setParams((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit() {
    setError(null);
    if (!name.trim()) {
      setError("Name is required");
      return;
    }
    if (params.length === 0 || params.every((p) => !p.name.trim())) {
      setError("At least one parameter is required");
      return;
    }

    setSubmitting(true);
    try {
      await createCustomTemplate({
        name: name.trim(),
        description: description.trim(),
        parameters: params
          .filter((p) => p.name.trim())
          .map((p) => ({
            name: p.name.trim(),
            type: p.type,
            default:
              p.type === "str"
                ? p.default_value
                : Number.isFinite(Number(p.default_value))
                  ? Number(p.default_value)
                  : 0,
            unit: p.unit,
          })),
      });
      setOpen(false);
      resetForm();
      onTemplatesChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create template");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div />
        <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
          <Plus className="h-4 w-4 mr-1" />
          Create Custom Template
        </Button>
      </div>

      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-lg rounded-lg border bg-white p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Create Custom Template</h3>
              <Button variant="ghost" size="sm" onClick={() => { setOpen(false); resetForm(); }}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-700">Name (snake_case)</label>
                <Input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="my_custom_policy"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Description</label>
                <Input
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Optional description"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Parameters</label>
                <div className="space-y-2 mt-1">
                  {params.map((param, i) => (
                    <div key={i} className="flex gap-2 items-center">
                      <Input
                        value={param.name}
                        onChange={(e) => updateParam(i, "name", e.target.value)}
                        placeholder="param_name"
                        className="flex-1"
                      />
                      <Select
                        value={param.type}
                        onChange={(e) => updateParam(i, "type", e.target.value)}
                        className="w-auto flex-shrink-0"
                      >
                        <option value="float">float</option>
                        <option value="int">int</option>
                        <option value="str">str</option>
                      </Select>
                      <Input
                        value={param.default_value}
                        onChange={(e) => updateParam(i, "default_value", e.target.value)}
                        placeholder="default"
                        className="w-20"
                      />
                      <Input
                        value={param.unit}
                        onChange={(e) => updateParam(i, "unit", e.target.value)}
                        placeholder="unit"
                        className="w-20"
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => removeParam(i)}
                        disabled={params.length <= 1}
                      >
                        <Trash2 className="h-3.5 w-3.5 text-slate-400" />
                      </Button>
                    </div>
                  ))}
                </div>
                <Button variant="ghost" size="sm" onClick={addParam} className="mt-1">
                  <Plus className="h-3.5 w-3.5 mr-1" /> Add parameter
                </Button>
              </div>
              {error && <p className="text-sm text-red-600">{error}</p>}
              <Button onClick={handleSubmit} disabled={submitting} className="w-full">
                {submitting ? "Creating..." : "Create Template"}
              </Button>
            </div>
          </div>
        </div>
      )}

      <SelectionGrid
        items={templates}
        selectedId={selectedTemplateId}
        onSelect={onSelectTemplate}
        getId={(t) => t.id}
        renderCard={(template, selected) => (
          <Card className={selected ? "border-blue-500 bg-blue-50" : "border-slate-200 bg-white"}>
            <CardHeader>
              <div className="flex items-center gap-2">
                <CardTitle>{template.name}</CardTitle>
                {template.is_custom && (
                  <Badge variant="outline" className="text-xs bg-violet-50 text-violet-700 border-violet-200">
                    custom
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-700">{template.description}</p>
              <p className="data-mono mt-1 text-xs text-slate-500">
                {template.parameterCount} parameters
              </p>
            </CardContent>
          </Card>
        )}
      />
    </section>
  );
}
