import { Alert } from "@/components/ui/alert";
import { Card, CardTitle } from "@/components/ui/card";
import { metricsCopy as copy } from "@/content/es";

import type { Metrics } from "./data";

type Row = { label: string; value: string | null };

function MetricList({ title, rows }: { title: string; rows: Row[] }) {
  return (
    <Card className="flex flex-col gap-3">
      <CardTitle>{title}</CardTitle>
      <dl className="divide-border divide-y text-sm">
        {rows.map((row) => (
          <div key={row.label} className="flex flex-wrap justify-between gap-2 py-2">
            <dt className="text-muted-foreground">{row.label}</dt>
            <dd className={row.value === null ? "text-muted-foreground" : "font-medium"}>
              {row.value ?? copy.noData}
            </dd>
          </div>
        ))}
      </dl>
    </Card>
  );
}

const when = <T,>(value: T | null | undefined, format: (v: T) => string): string | null =>
  value === null || value === undefined ? null : format(value);

/** Pilot metrics; any value without recorded data is shown as "Sin datos aún". */
export function MetricsView({ metrics }: { metrics: Metrics }) {
  const t = metrics.technical;
  const v = metrics.value;
  const answered = v.responses > 0;
  const technical: Row[] = [
    {
      label: copy.technical.processed,
      value: when(t.processed_ok_ratio, (ratio) =>
        copy.technical.processedValue(t.documents_processed_ok, t.documents_attempted, ratio),
      ),
    },
    { label: copy.technical.extractionErrors, value: String(t.extraction_errors) },
    { label: copy.technical.processingFailures, value: String(t.processing_failures) },
    {
      label: copy.technical.averageAnalysis,
      value: when(t.average_analysis_seconds, copy.seconds),
    },
    { label: copy.technical.llmCalls, value: String(t.llm_calls) },
    { label: copy.technical.tokens, value: t.approximate_tokens.toLocaleString("es-CO") },
    {
      label: copy.technical.modified,
      value: t.findings_reviewed
        ? copy.technical.modifiedValue(t.findings_modified, t.findings_reviewed)
        : null,
    },
    { label: copy.technical.denials, value: String(t.authorization_denials) },
  ];
  const value: Row[] = [
    { label: copy.value.responses, value: String(v.responses) },
    { label: copy.value.manualTime, value: when(v.average_manual_hours, copy.hours) },
    { label: copy.value.systemTime, value: when(v.average_system_hours, copy.hours) },
    { label: copy.value.usefulness, value: when(v.average_usefulness, copy.score) },
    { label: copy.value.ease, value: when(v.average_ease_of_use, copy.score) },
    { label: copy.value.trust, value: when(v.average_trust, copy.score) },
    {
      label: copy.value.actionable,
      value: answered ? copy.value.actionableValue(v.actionable_yes, v.responses) : null,
    },
    { label: copy.value.willingness, value: when(v.average_willingness_to_use, copy.score) },
    {
      label: copy.value.pay,
      value: answered ? copy.value.payValue(v.pay_yes, v.pay_maybe, v.pay_no) : null,
    },
  ];
  return (
    <div className="flex flex-col gap-6">
      {metrics.anonymized ? <Alert tone="info">{copy.anonymized}</Alert> : null}
      <div className="grid gap-6 lg:grid-cols-2">
        <MetricList title={copy.technicalTitle} rows={technical} />
        <MetricList title={copy.valueTitle} rows={value} />
      </div>
    </div>
  );
}
