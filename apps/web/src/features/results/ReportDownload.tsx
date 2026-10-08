"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Download } from "lucide-react";
import { useState } from "react";

import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { resultsCopy } from "@/content/es";
import { browserApi } from "@/lib/api/browser";
import { apiErrorMessage } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/format";

const copy = resultsCopy.report;
const POLL_MS = 3_000;

type ReportDownloadProps = { evaluationId: string; canGenerate: boolean };

/** Shows the report state (polling while it is generated) and downloads it via a signed URL. */
export function ReportDownload({ evaluationId, canGenerate }: ReportDownloadProps) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const key = ["report-status", evaluationId];

  const { data } = useQuery({
    queryKey: key,
    queryFn: async () => {
      const { data: body, error: failure } = await browserApi.GET(
        "/api/v1/evaluations/{evaluation_id}/report",
        { params: { path: { evaluation_id: evaluationId } } },
      );
      if (!body) throw new Error(apiErrorMessage(failure));
      return body;
    },
    refetchInterval: (query) => (query.state.data?.state === "PENDING" ? POLL_MS : false),
  });

  const download = async (reportId: string) => {
    setBusy(true);
    setError(null);
    const { data: signed, error: failure } = await browserApi.GET(
      "/api/v1/reports/{report_id}/download",
      { params: { path: { report_id: reportId } } },
    );
    setBusy(false);
    if (!signed) {
      setError(apiErrorMessage(failure));
      return;
    }
    window.location.assign(signed.url);
  };

  const generate = async () => {
    setBusy(true);
    setError(null);
    const { error: failure, response } = await browserApi.POST(
      "/api/v1/evaluations/{evaluation_id}/report",
      { params: { path: { evaluation_id: evaluationId } } },
    );
    setBusy(false);
    if (!response.ok) setError(apiErrorMessage(failure));
    await queryClient.invalidateQueries({ queryKey: key });
  };

  const state = data?.state;
  const reportId = data?.report_id;
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <CardTitle>{copy.title}</CardTitle>
        <CardDescription>{copy.description}</CardDescription>
      </div>
      <div aria-live="polite" className="flex flex-col gap-2 text-sm">
        {state === "PENDING" ? <p>{copy.pending}</p> : null}
        {state === "FAILED" ? <Alert tone="danger">{copy.failed}</Alert> : null}
        {state === "NONE" ? <p>{copy.none}</p> : null}
        {error ? <Alert tone="danger">{error}</Alert> : null}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {reportId ? (
          <Button type="button" disabled={busy} onClick={() => void download(reportId)}>
            <Download className="size-4" aria-hidden="true" />
            {busy ? copy.downloading : copy.download}
          </Button>
        ) : null}
        {canGenerate && (state === "FAILED" || state === "NONE") ? (
          <Button type="button" variant="outline" disabled={busy} onClick={() => void generate()}>
            {copy.generate}
          </Button>
        ) : null}
        {data?.version && data.generated_at ? (
          <span className="text-muted-foreground text-xs">
            {copy.version(data.version, formatDateTime(data.generated_at))}
          </span>
        ) : null}
      </div>
    </Card>
  );
}
