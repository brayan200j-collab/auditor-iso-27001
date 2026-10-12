import { FileText, Lightbulb } from "lucide-react";
import Link from "next/link";

import { documentGuide as copy } from "@/content/es";

/** Which kinds of documents help, and which criteria each one covers. */
export function DocumentTypes({ compact = false }: { compact?: boolean }) {
  const types = compact ? copy.types.slice(0, 8) : copy.types;
  return (
    <ul className={`grid gap-3 ${compact ? "sm:grid-cols-2" : "sm:grid-cols-2 lg:grid-cols-3"}`}>
      {types.map((type) => (
        <li
          key={type.name}
          className="border-border/70 bg-surface flex gap-3 rounded-2xl border p-4"
        >
          <span className="bg-primary-soft text-primary flex size-9 shrink-0 items-center justify-center rounded-xl">
            <FileText className="size-4" aria-hidden="true" />
          </span>
          <span className="flex flex-col gap-1">
            <span className="text-foreground text-sm font-medium">{type.name}</span>
            <span className="text-muted-foreground text-xs">
              {copy.coversLabel} {type.covers.join(", ")}
            </span>
          </span>
        </li>
      ))}
    </ul>
  );
}

export function UploadTips() {
  return (
    <div className="bg-pastel-sky rounded-2xl p-4">
      <p className="text-foreground flex items-center gap-2 text-sm font-semibold">
        <Lightbulb className="size-4" aria-hidden="true" />
        {copy.tipsTitle}
      </p>
      <ul className="text-foreground/85 mt-2 flex list-disc flex-col gap-1 pl-5 text-sm">
        {copy.tips.map((tip) => (
          <li key={tip}>{tip}</li>
        ))}
      </ul>
    </div>
  );
}

/** Guidance shown next to the upload zone, for people who do not know what to upload. */
export function UploadHelp({ guideHref }: { guideHref: string }) {
  return (
    <details className="group border-border/70 bg-surface-muted/60 rounded-2xl border" open>
      <summary className="text-foreground cursor-pointer list-none rounded-2xl px-5 py-4 font-semibold [&::-webkit-details-marker]:hidden">
        {copy.title}
      </summary>
      <div className="flex flex-col gap-4 px-5 pb-5">
        <p className="text-muted-foreground text-sm">{copy.intro}</p>
        <DocumentTypes compact />
        <UploadTips />
        <Link href={guideHref} className="text-primary text-sm font-medium hover:underline">
          {copy.more}
        </Link>
      </div>
    </details>
  );
}
