import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/PageHeader";
import { Alert } from "@/components/ui/alert";
import { metricsCopy } from "@/content/es";
import { getMetrics, MetricsView } from "@/features/metrics";
import { requireRole } from "@/lib/guards";

export const metadata: Metadata = { title: metricsCopy.title };

export default async function MetricsPage() {
  await requireRole("ADMIN", "MENTOR");
  const metrics = await getMetrics();
  return (
    <>
      <PageHeader title={metricsCopy.title} description={metricsCopy.description} />
      {metrics ? (
        <MetricsView metrics={metrics} />
      ) : (
        <Alert tone="neutral">{metricsCopy.noData}</Alert>
      )}
    </>
  );
}
