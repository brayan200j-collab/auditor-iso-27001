import { BookOpen, CircleHelp } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { guide } from "@/content/es";

import { CriterionDetails, criterionGuide } from "./CriteriaGuide";
import { ResultsGuide } from "./ResultsGuide";

/** Plain-language explanation of one criterion (results and finding detail). */
export function CriterionHelp({ code }: { code: string }) {
  const criterion = criterionGuide(code);
  if (!criterion) return null;
  return (
    <Card className="bg-pastel-periwinkle flex flex-col gap-3 border-0">
      <CardTitle className="flex items-center gap-2">
        <CircleHelp className="text-primary size-5" aria-hidden="true" />
        {guide.criterionHelp.title}
      </CardTitle>
      <CriterionDetails criterion={criterion} />
    </Card>
  );
}

/** Collapsible "how to read your results" next to the results. */
export function HowToReadResults() {
  return (
    <details className="group border-border/70 bg-surface shadow-card rounded-3xl border">
      <summary className="text-foreground flex cursor-pointer list-none items-center gap-2 rounded-3xl px-6 py-5 font-semibold [&::-webkit-details-marker]:hidden">
        <CircleHelp className="text-primary size-5" aria-hidden="true" />
        {guide.readResults}
      </summary>
      <div className="px-6 pb-6">
        <ResultsGuide />
      </div>
    </details>
  );
}

export function FirstStepsCard({ href }: { href: string }) {
  return (
    <section className="bg-pastel-lavender flex flex-wrap items-center justify-between gap-4 rounded-3xl p-6">
      <div className="flex items-start gap-3">
        <span className="bg-surface text-primary flex size-11 shrink-0 items-center justify-center rounded-2xl">
          <BookOpen className="size-5" aria-hidden="true" />
        </span>
        <div className="flex flex-col gap-1">
          <h2 className="text-foreground font-semibold">{guide.firstSteps.title}</h2>
          <p className="text-foreground/85 max-w-xl text-sm">{guide.firstSteps.text}</p>
        </div>
      </div>
      <Link href={href} className={buttonVariants({ variant: "outline" })}>
        {guide.firstSteps.cta}
      </Link>
    </section>
  );
}
