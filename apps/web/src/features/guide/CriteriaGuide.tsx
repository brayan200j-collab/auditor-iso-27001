import { ChevronDown, FileText, Search } from "lucide-react";

import { criteriaGroups, guide, type CriterionGuide } from "@/content/es";

const GROUP_SURFACES = [
  "bg-pastel-periwinkle",
  "bg-pastel-peach",
  "bg-pastel-mint",
  "bg-pastel-lavender",
  "bg-pastel-sky",
  "bg-pastel-aqua",
  "bg-pastel-periwinkle",
  "bg-pastel-peach",
  "bg-pastel-mint",
];

export function CriterionDetails({ criterion }: { criterion: CriterionGuide }) {
  return (
    <div className="flex flex-col gap-3 text-sm">
      <p className="text-foreground leading-relaxed">{criterion.plain}</p>
      <p className="flex gap-2 leading-relaxed">
        <Search className="text-primary mt-0.5 size-4 shrink-0" aria-hidden="true" />
        <span>
          <span className="text-foreground font-medium">{guide.criterionHelp.lookFor}: </span>
          <span className="text-muted-foreground">{criterion.lookFor}</span>
        </span>
      </p>
      <div className="flex flex-col gap-1.5">
        <p className="text-foreground font-medium">{guide.criterionHelp.documents}</p>
        <ul className="flex flex-wrap gap-2">
          {criterion.documents.map((document) => (
            <li
              key={document}
              className="bg-surface-muted text-foreground inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs"
            >
              <FileText className="text-muted-foreground size-3.5" aria-hidden="true" />
              {document}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/** The 30 criteria in plain language, grouped by theme; every criterion expands on demand. */
export function CriteriaGuide() {
  return (
    <div className="flex flex-col gap-6">
      {criteriaGroups.map((group, index) => (
        <section
          key={group.id}
          aria-labelledby={`grupo-${group.id}`}
          className={`${GROUP_SURFACES[index] ?? "bg-pastel-periwinkle"} rounded-3xl p-5 sm:p-6`}
        >
          <h3 id={`grupo-${group.id}`} className="text-foreground text-lg font-semibold">
            {group.title}
          </h3>
          <p className="text-foreground/80 mt-1 text-sm">{group.intro}</p>
          <ul className="mt-4 flex flex-col gap-2">
            {group.criteria.map((criterion) => (
              <li key={criterion.code}>
                <details className="group bg-surface rounded-2xl">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-3 rounded-2xl px-4 py-3 [&::-webkit-details-marker]:hidden">
                    <span className="flex flex-wrap items-baseline gap-2">
                      <span className="text-primary text-xs font-semibold">{criterion.code}</span>
                      <span className="text-foreground font-medium">{criterion.title}</span>
                    </span>
                    <ChevronDown
                      className="text-muted-foreground size-4 shrink-0 transition-transform group-open:rotate-180"
                      aria-hidden="true"
                    />
                  </summary>
                  <div className="border-border/70 border-t px-4 py-4">
                    <CriterionDetails criterion={criterion} />
                  </div>
                </details>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

const BY_CODE = new Map(criteriaGroups.flatMap((group) => group.criteria).map((c) => [c.code, c]));

export function criterionGuide(code: string): CriterionGuide | undefined {
  return BY_CODE.get(code);
}
