import type { Metadata } from "next";

import { PublicShell } from "@/components/shared/PublicShell";
import { guide } from "@/content/es";
import { GuideContent } from "@/features/guide";

export const metadata: Metadata = { title: guide.title, description: guide.description };

export default function PublicGuidePage() {
  return (
    <PublicShell>
      <GuideContent />
    </PublicShell>
  );
}
