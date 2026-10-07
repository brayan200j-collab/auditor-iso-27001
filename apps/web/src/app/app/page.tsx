import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/PageHeader";
import { Alert } from "@/components/ui/alert";
import { brand, legal, nav } from "@/content/es";
import { requireProfile } from "@/lib/profile";

export const metadata: Metadata = { title: nav.home };

export default async function DashboardPage() {
  const profile = await requireProfile();
  return (
    <>
      <PageHeader title={nav.home} description={brand.tagline} />
      <p className="text-foreground">Hola, {profile.full_name}.</p>
      <Alert tone="neutral">{legal.scopeDisclaimer}</Alert>
    </>
  );
}
