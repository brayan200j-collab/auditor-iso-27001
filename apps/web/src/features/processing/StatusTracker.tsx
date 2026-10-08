"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useEffect, useRef } from "react";

import { ProgressTimeline, type TimelineStep } from "@/components/shared/ProgressTimeline";
import { processingCopy } from "@/content/es";
import { browserApi } from "@/lib/api/browser";
import { apiErrorMessage } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/format";

import { nextInterval, STABLE_STATUSES } from "./polling";

type StatusTrackerProps = {
  evaluationId: string;
  initialStatus: string;
  initialSteps: TimelineStep[];
};

/** Live progress timeline. Polls while processing and refreshes the page when it settles. */
export function StatusTracker({ evaluationId, initialStatus, initialSteps }: StatusTrackerProps) {
  const router = useRouter();
  const attempts = useRef(0);
  const lastStatus = useRef(initialStatus);

  const { data } = useQuery({
    queryKey: ["evaluation-status", evaluationId],
    queryFn: async () => {
      attempts.current += 1;
      const { data: body, error } = await browserApi.GET(
        "/api/v1/evaluations/{evaluation_id}/status",
        {
          params: { path: { evaluation_id: evaluationId } },
        },
      );
      if (!body) throw new Error(apiErrorMessage(error));
      return body;
    },
    enabled: !STABLE_STATUSES.has(initialStatus),
    refetchInterval: (query) => {
      const status = query.state.data?.status ?? initialStatus;
      return STABLE_STATUSES.has(status) ? false : nextInterval(attempts.current);
    },
  });

  const status = data?.status ?? initialStatus;
  useEffect(() => {
    if (status !== lastStatus.current) {
      lastStatus.current = status;
      router.refresh();
    }
  }, [status, router]);

  const live = processingCopy.live[status as keyof typeof processingCopy.live];
  return (
    <div className="flex flex-col gap-3">
      <ProgressTimeline steps={data?.progress ?? initialSteps} />
      <p aria-live="polite" className="text-muted-foreground text-sm">
        {live ?? ""}
        {data?.criteria_total
          ? ` ${processingCopy.criteria(data.criteria_done ?? 0, data.criteria_total)}`
          : ""}
        {data ? ` ${processingCopy.updated(formatDateTime(data.updated_at))}` : ""}
      </p>
    </div>
  );
}
