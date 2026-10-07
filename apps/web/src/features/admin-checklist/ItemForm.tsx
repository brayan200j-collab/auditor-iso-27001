"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useState, useTransition } from "react";
import { useForm } from "react-hook-form";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input, Select, Textarea } from "@/components/ui/input";
import { checklistCopy, effortLabels, priorityLabels, riskLabels } from "@/content/es";
import type { ActionResult } from "@/lib/actions";

import { updateItemAction } from "./actions";
import { itemSchema, type ItemValues } from "./schemas";

type ItemFormProps = { versionId: string; code: string; defaults: ItemValues };

const f = checklistCopy.fields;

export function ItemForm({ versionId, code, defaults }: ItemFormProps) {
  const [result, setResult] = useState<ActionResult | null>(null);
  const [pending, startTransition] = useTransition();
  const { register, handleSubmit } = useForm<ItemValues>({
    resolver: zodResolver(itemSchema),
    defaultValues: defaults,
  });

  const onSubmit = handleSubmit(
    (values) =>
      startTransition(async () => setResult(await updateItemAction(versionId, code, values))),
    () => setResult({ ok: false, message: checklistCopy.invalid }),
  );

  return (
    <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
      {result ? <Alert tone={result.ok ? "success" : "danger"}>{result.message}</Alert> : null}
      <Field id="item-name" label={f.name}>
        <Input id="item-name" {...register("name")} />
      </Field>
      <Field id="item-description" label={f.description}>
        <Textarea id="item-description" {...register("description")} />
      </Field>
      <Field id="item-question" label={f.question}>
        <Textarea id="item-question" {...register("evaluation_question")} />
      </Field>
      <Field id="item-evidence" label={f.evidence}>
        <Textarea id="item-evidence" {...register("expected_evidence")} />
      </Field>
      <div className="grid gap-4 md:grid-cols-3">
        <Field id="item-iso" label={f.iso}>
          <Input id="item-iso" {...register("iso_reference")} />
        </Field>
        <Field id="item-cis" label={f.cis}>
          <Input id="item-cis" {...register("cis_reference")} />
        </Field>
        <Field id="item-nist" label={f.nist}>
          <Input id="item-nist" {...register("nist_reference")} />
        </Field>
      </div>
      <Field id="item-reference-status" label={f.referenceStatus}>
        <Select id="item-reference-status" {...register("reference_status")}>
          <option value="draft">{checklistCopy.pendingReference}</option>
          <option value="confirmed">{checklistCopy.confirmedReference}</option>
        </Select>
      </Field>
      <Field id="item-keywords" label={f.keywords} hint={f.keywordsHint}>
        <Input id="item-keywords" aria-describedby="item-keywords-hint" {...register("keywords")} />
      </Field>
      <div className="grid gap-4 md:grid-cols-3">
        <Field id="item-priority" label={f.priority}>
          <Select id="item-priority" {...register("priority")}>
            {Object.entries(priorityLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </Field>
        <Field id="item-risk" label={f.risk}>
          <Select id="item-risk" {...register("risk_level")}>
            {Object.entries(riskLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </Field>
        <Field id="item-effort" label={f.effort}>
          <Select id="item-effort" {...register("effort")}>
            {Object.entries(effortLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </Field>
      </div>
      <label className="text-foreground flex items-center gap-2 text-sm">
        <input type="checkbox" className="size-4" {...register("active")} />
        {f.active}
      </label>
      <div>
        <Button type="submit" disabled={pending}>
          {checklistCopy.edit}
        </Button>
      </div>
    </form>
  );
}
