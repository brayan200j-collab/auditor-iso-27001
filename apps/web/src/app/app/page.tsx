import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { EmptyState } from "@/components/shared/EmptyState";
import { PageHeader } from "@/components/shared/PageHeader";
import { Alert } from "@/components/ui/alert";
import { buttonVariants } from "@/components/ui/button";
import { brand, dashboardCopy, legal, nav } from "@/content/es";
import { DashboardCards, getDashboard } from "@/features/metrics";
import { requireProfile } from "@/lib/profile";

export const metadata: Metadata = { title: nav.home };

export default async function DashboardPage() {
  const profile = await requireProfile();
  if (profile.role === "MENTOR") redirect("/app/metricas");
  const counts = await getDashboard();
  const empty =
    counts !== null &&
    counts.active_evaluations + counts.approved === 0 &&
    counts.documents_processed === 0;

  return (
    <>
      <PageHeader title={nav.home} description={brand.tagline} />
      <p className="text-foreground">{dashboardCopy.greeting(profile.full_name)}</p>
      {counts ? <DashboardCards counts={counts} /> : null}
      {empty ? (
        <EmptyState
          message={dashboardCopy.empty[profile.role]}
          action={
            profile.role === "SME" ? (
              <Link href="/app/evaluaciones/nueva" className={buttonVariants()}>
                {dashboardCopy.start}
              </Link>
            ) : undefined
          }
        />
      ) : null}
      <Alert tone="neutral">{legal.scopeDisclaimer}</Alert>
    </>
  );
}
