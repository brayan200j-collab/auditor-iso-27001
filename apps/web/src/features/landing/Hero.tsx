import { ArrowRight, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { landing } from "@/content/es";

import { ProductPreview } from "./ProductPreview";

export function Hero() {
  return (
    <section className="grid items-center gap-12 py-10 lg:grid-cols-[1.05fr_1fr] lg:py-16">
      <div className="flex flex-col gap-6">
        <span className="bg-primary-soft text-secondary-foreground inline-flex w-fit items-center gap-2 rounded-full px-3 py-1 text-xs font-medium">
          <ShieldCheck className="size-4" aria-hidden="true" />
          {landing.eyebrow}
        </span>
        <h1 className="text-foreground text-4xl leading-[1.12] font-light tracking-[-0.03em] sm:text-5xl lg:text-[3.5rem]">
          {landing.headlineStart}{" "}
          <span className="text-gradient-brand font-medium">{landing.headlineAccent}</span>{" "}
          {landing.headlineEnd}
        </h1>
        <p className="text-muted-foreground max-w-xl text-base leading-relaxed sm:text-lg">
          {landing.lead}
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <Link href="/login" className={buttonVariants({ size: "lg" })}>
            {landing.primaryCta}
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
          <Link
            href="#como-funciona"
            className={buttonVariants({ variant: "outline", size: "lg" })}
          >
            {landing.secondaryCta}
          </Link>
        </div>
        <p className="text-muted-foreground text-sm">{landing.inviteNote}</p>
      </div>
      <ProductPreview />
    </section>
  );
}
