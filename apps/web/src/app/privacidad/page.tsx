import type { Metadata } from "next";

import { PublicShell } from "@/components/shared/PublicShell";
import { Alert } from "@/components/ui/alert";
import { privacyPage } from "@/content/es";

export const metadata: Metadata = { title: privacyPage.title };

export default function PrivacyPage() {
  return (
    <PublicShell>
      <article className="flex max-w-3xl flex-col gap-6">
        <h1 className="text-foreground text-2xl font-semibold">{privacyPage.title}</h1>
        <Alert tone="warning">{privacyPage.draftNotice}</Alert>
        {privacyPage.sections.map((section) => (
          <section key={section.title} className="flex flex-col gap-2">
            <h2 className="text-foreground text-lg font-semibold">{section.title}</h2>
            {section.paragraphs.map((paragraph) => (
              <p key={paragraph} className="text-muted-foreground text-sm leading-relaxed">
                {paragraph}
              </p>
            ))}
          </section>
        ))}
      </article>
    </PublicShell>
  );
}
