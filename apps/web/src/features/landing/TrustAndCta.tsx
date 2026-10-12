import { ArrowRight, CircleCheck, Info, LockKeyhole } from "lucide-react";
import Link from "next/link";

import { LogoSymbol } from "@/components/shared/BrandMark";
import { buttonVariants } from "@/components/ui/button";
import { landing, legal, publicPages } from "@/content/es";

export function Trust() {
  return (
    <section
      aria-labelledby="seguridad-titulo"
      id="seguridad"
      className="bg-primary text-primary-foreground -mx-4 scroll-mt-28 overflow-hidden rounded-[2.5rem] px-6 py-14 sm:mx-0 sm:px-12"
    >
      <div className="grid gap-10 lg:grid-cols-[1fr_1.2fr]">
        <div className="flex flex-col gap-4">
          <span className="flex size-12 items-center justify-center rounded-2xl bg-black/15">
            <LockKeyhole className="size-6" aria-hidden="true" />
          </span>
          <p className="text-sm font-semibold tracking-[0.12em] text-white uppercase">
            {landing.trust.eyebrow}
          </p>
          <h2 id="seguridad-titulo" className="text-3xl font-light tracking-[-0.02em] sm:text-4xl">
            {landing.trust.title}
          </h2>
          <p className="text-sm leading-relaxed text-white/90">{legal.aiPrivacy}</p>
          <p className="text-sm leading-relaxed text-white/90">{legal.aiProvider}</p>
        </div>
        <ul className="flex flex-col gap-3">
          {landing.trust.items.map((item) => (
            <li
              key={item}
              className="flex gap-3 rounded-2xl bg-black/15 p-4 text-sm leading-relaxed"
            >
              <CircleCheck className="mt-0.5 size-5 shrink-0" aria-hidden="true" />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

export function LimitsAndCta() {
  return (
    <section className="grid gap-6 py-16 lg:grid-cols-2">
      <div className="border-border/70 bg-surface shadow-card flex flex-col gap-4 rounded-3xl border p-7">
        <span className="bg-warning-soft text-warning flex size-11 items-center justify-center rounded-2xl">
          <Info className="size-5" aria-hidden="true" />
        </span>
        <h2 className="text-foreground text-xl font-semibold">{landing.limits.title}</h2>
        <ul className="text-muted-foreground flex flex-col gap-2 text-sm">
          {publicPages.limits.map((item) => (
            <li key={item} className="flex gap-2">
              <span
                aria-hidden="true"
                className="bg-muted-foreground mt-2 size-1.5 shrink-0 rounded-full"
              />
              {item}
            </li>
          ))}
        </ul>
        <p className="text-muted-foreground border-border/70 border-t pt-4 text-xs leading-relaxed">
          {legal.scopeDisclaimer}
        </p>
      </div>
      <div className="bg-pastel-lavender relative flex flex-col justify-between gap-6 overflow-hidden rounded-3xl p-7">
        <LogoSymbol className="absolute -right-6 -bottom-6 size-40 opacity-15" />
        <div className="relative flex flex-col gap-3">
          <h2 className="text-foreground text-2xl font-semibold tracking-tight">
            {landing.finalCta.title}
          </h2>
          <p className="text-foreground/80 leading-relaxed">{landing.finalCta.text}</p>
        </div>
        <div className="relative">
          <Link href="/login" className={buttonVariants({ size: "lg" })}>
            {landing.primaryCta}
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
        </div>
      </div>
    </section>
  );
}
