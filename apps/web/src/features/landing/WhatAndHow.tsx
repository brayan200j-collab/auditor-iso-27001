import { FileSearch, ListChecks, UserCheck } from "lucide-react";

import { brand, landing } from "@/content/es";

import { SectionHeading } from "./SectionHeading";

const DEFAULT_PILLAR = { surface: "bg-pastel-periwinkle", Icon: FileSearch };
const PILLAR_STYLES = [
  DEFAULT_PILLAR,
  { surface: "bg-pastel-mint", Icon: UserCheck },
  { surface: "bg-pastel-peach", Icon: ListChecks },
];

export function WhatItIs() {
  return (
    <section aria-labelledby="que-es-titulo" id="que-es" className="scroll-mt-28 py-14">
      <div className="grid gap-10 lg:grid-cols-[1fr_1.2fr] lg:items-start">
        <div className="flex flex-col gap-5">
          <SectionHeading
            id="que-es-titulo"
            eyebrow={landing.what.eyebrow}
            title={landing.what.title}
          />
          <p className="text-muted-foreground leading-relaxed">{brand.definition}</p>
        </div>
        <ul className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
          {landing.what.pillars.map((pillar, index) => {
            const { surface, Icon } = PILLAR_STYLES[index] ?? DEFAULT_PILLAR;
            return (
              <li key={pillar.title} className={`${surface} flex gap-4 rounded-3xl p-6`}>
                <span className="bg-surface text-primary flex size-11 shrink-0 items-center justify-center rounded-2xl">
                  <Icon className="size-5" aria-hidden="true" />
                </span>
                <span className="flex flex-col gap-1">
                  <span className="text-foreground font-semibold">{pillar.title}</span>
                  <span className="text-foreground/80 text-sm leading-relaxed">{pillar.text}</span>
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}

export function HowItWorks() {
  return (
    <section
      aria-labelledby="como-funciona-titulo"
      id="como-funciona"
      className="bg-surface shadow-card -mx-4 scroll-mt-28 rounded-[2.5rem] px-6 py-14 sm:mx-0 sm:px-10"
    >
      <SectionHeading
        id="como-funciona-titulo"
        eyebrow={landing.how.eyebrow}
        title={landing.how.title}
        center
      />
      <ol className="mt-12 grid gap-6 md:grid-cols-5">
        {landing.how.steps.map((step, index) => (
          <li key={step.title} className="relative flex flex-col gap-3">
            <span className="flex items-center gap-3">
              <span className="bg-primary text-primary-foreground flex size-10 shrink-0 items-center justify-center rounded-full text-sm font-semibold">
                {index + 1}
              </span>
              {index < landing.how.steps.length - 1 ? (
                <span aria-hidden="true" className="bg-border hidden h-px flex-1 md:block" />
              ) : null}
            </span>
            <span className="text-foreground font-semibold">{step.title}</span>
            <span className="text-muted-foreground text-sm leading-relaxed">{step.text}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}
