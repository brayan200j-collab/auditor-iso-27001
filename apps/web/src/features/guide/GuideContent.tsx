import type { ReactNode } from "react";

import { brand, guide } from "@/content/es";

import { CriteriaGuide } from "./CriteriaGuide";
import { DocumentTypes, UploadTips } from "./DocumentGuide";
import { PrintButton } from "./PrintButton";
import { ResultsGuide } from "./ResultsGuide";

const S = guide.sections;
const TOC = [
  { id: "iso", label: S.iso },
  { id: "plataforma", label: S.app },
  { id: "pasos", label: S.steps },
  { id: "documentos", label: S.documents },
  { id: "criterios", label: S.criteria },
  { id: "resultados", label: S.results },
  { id: "preguntas", label: S.faq },
  { id: "glosario", label: S.glossary },
];

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section
      id={id}
      aria-labelledby={`${id}-titulo`}
      className="border-border/70 bg-surface shadow-card scroll-mt-28 break-inside-avoid rounded-3xl border p-6 sm:p-8 print:shadow-none"
    >
      <h2
        id={`${id}-titulo`}
        className="text-foreground mb-4 text-2xl font-semibold tracking-tight"
      >
        {title}
      </h2>
      {children}
    </section>
  );
}

/** The user manual: shared by the public page and the in-app page, printable as a PDF. */
export function GuideContent() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex max-w-2xl flex-col gap-2">
          <h1 className="text-foreground text-3xl font-light tracking-[-0.02em] sm:text-4xl">
            {guide.title}
          </h1>
          <p className="text-muted-foreground">{guide.description}</p>
        </div>
        <PrintButton label={guide.print} />
      </div>

      <nav aria-label={guide.toc} className="print:hidden">
        <ul className="flex flex-wrap gap-2">
          {TOC.map((item) => (
            <li key={item.id}>
              <a
                href={`#${item.id}`}
                className="bg-surface text-foreground hover:bg-primary-soft border-border/70 inline-block rounded-full border px-3.5 py-1.5 text-sm font-medium"
              >
                {item.label}
              </a>
            </li>
          ))}
        </ul>
      </nav>

      <Section id="iso" title={S.iso}>
        <div className="text-foreground flex flex-col gap-3 leading-relaxed">
          {guide.iso.map((paragraph) => (
            <p key={paragraph}>{paragraph}</p>
          ))}
        </div>
      </Section>

      <Section id="plataforma" title={S.app}>
        <p className="text-foreground leading-relaxed">{guide.app}</p>
        <p className="text-muted-foreground mt-3 text-sm leading-relaxed">{brand.definition}</p>
      </Section>

      <Section id="pasos" title={S.steps}>
        <ol className="grid gap-4 sm:grid-cols-2">
          {guide.steps.map((step, index) => (
            <li key={step.title} className="flex gap-3">
              <span className="bg-primary text-primary-foreground flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold">
                {index + 1}
              </span>
              <span className="flex flex-col gap-0.5">
                <span className="text-foreground font-semibold">{step.title}</span>
                <span className="text-muted-foreground text-sm leading-relaxed">{step.text}</span>
              </span>
            </li>
          ))}
        </ol>
      </Section>

      <Section id="documentos" title={S.documents}>
        <div className="flex flex-col gap-4">
          <DocumentTypes />
          <UploadTips />
        </div>
      </Section>

      <Section id="criterios" title={S.criteria}>
        <CriteriaGuide />
      </Section>

      <Section id="resultados" title={S.results}>
        <ResultsGuide />
      </Section>

      <Section id="preguntas" title={S.faq}>
        <dl className="flex flex-col gap-4">
          {guide.faq.map((item) => (
            <div key={item.q} className="flex flex-col gap-1">
              <dt className="text-foreground font-semibold">{item.q}</dt>
              <dd className="text-muted-foreground leading-relaxed">{item.a}</dd>
            </div>
          ))}
        </dl>
      </Section>

      <Section id="glosario" title={S.glossary}>
        <dl className="grid gap-4 sm:grid-cols-2">
          {guide.glossary.map((item) => (
            <div key={item.term} className="bg-surface-muted/70 rounded-2xl p-4">
              <dt className="text-foreground font-semibold">{item.term}</dt>
              <dd className="text-muted-foreground mt-1 text-sm leading-relaxed">
                {item.definition}
              </dd>
            </div>
          ))}
        </dl>
      </Section>
    </div>
  );
}
