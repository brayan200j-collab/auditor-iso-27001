import type { Metadata } from "next";

import { guide } from "@/content/es";
import { GuideContent } from "@/features/guide";
import { requireProfile } from "@/lib/profile";

export const metadata: Metadata = { title: guide.title };

export default async function AppGuidePage() {
  await requireProfile();
  return <GuideContent />;
}
