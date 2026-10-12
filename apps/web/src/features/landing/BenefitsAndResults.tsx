import {
  BookCheck,
  Clock,
  FileDown,
  Gauge,
  Handshake,
  Layers,
  ListOrdered,
  Quote,
  Route,
  UserCheck,
} from "lucide-react";

import { landing } from "@/content/es";

import { SectionHeading } from "./SectionHeading";

const BENEFIT_ICONS = [Clock, Quote, UserCheck, ListOrdered, BookCheck, Handshake];
const DEFAULT_RESULT = { surface: "bg-pastel-mint", Icon: Gauge };
const RESULT_STYLES = [
  DEFAULT_RESULT,
  { surface: "bg-pastel-peach", Icon: Layers },
  { surface: "bg-pastel-sky", Icon: Route },
  { surface: "bg-pastel-lavender", Icon: FileDown },
];

export function Benefits() {
  return (
    <section aria-labelledby="ventajas-titulo" id="ventajas" className="scroll-mt-28 py-16">
      <SectionHeading
        id="ventajas-titulo"
        eyebrow={landing.benefits.eyebrow}
        title={landing.benefits.title}
      />
      <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {landing.benefits.items.map((item, index) => {
          const Icon = BENEFIT_ICONS[index] ?? Clock;
          return (
            <li
              key={item.title}
              className="border-border/70 bg-surface shadow-card hover:shadow-raised flex flex-col gap-3 rounded-3xl border p-6 transition-shadow"
            >
              <span className="bg-primary-soft text-primary flex size-11 items-center justify-center rounded-2xl">
                <Icon className="size-5" aria-hidden="true" />
              </span>
              <span className="text-foreground text-lg font-semibold">{item.title}</span>
              <span className="text-muted-foreground text-sm leading-relaxed">{item.text}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}

export function Results() {
  return (
    <section aria-labelledby="resultados-titulo" id="resultados" className="scroll-mt-28 py-16">
      <SectionHeading
        id="resultados-titulo"
        eyebrow={landing.results.eyebrow}
        title={landing.results.title}
      />
      <ul className="mt-10 grid gap-5 md:grid-cols-2">
        {landing.results.items.map((item, index) => {
          const { surface, Icon } = RESULT_STYLES[index] ?? DEFAULT_RESULT;
          return (
            <li key={item.title} className={`${surface} flex flex-col gap-4 rounded-3xl p-7`}>
              <span className="bg-surface text-primary flex size-12 items-center justify-center rounded-2xl">
                <Icon className="size-6" aria-hidden="true" />
              </span>
              <span className="text-foreground text-xl font-semibold">{item.title}</span>
              <span className="text-foreground/80 leading-relaxed">{item.text}</span>
              {index === 2 ? (
                <span className="flex flex-wrap gap-2">
                  {landing.results.phases.map((phase, phaseIndex) => (
                    <span
                      key={phase}
                      className="bg-surface text-foreground rounded-full px-3 py-1 text-xs font-medium"
                    >
                      {phaseIndex + 1}. {phase}
                    </span>
                  ))}
                </span>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
