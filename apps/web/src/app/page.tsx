import Link from "next/link";

import { PublicShell } from "@/components/shared/PublicShell";
import { buttonVariants } from "@/components/ui/button";
import { brand, legal, publicPages } from "@/content/es";

export default function HomePage() {
  return (
    <PublicShell>
      <section className="flex flex-col gap-6 py-6">
        <h1 className="text-foreground max-w-3xl text-3xl font-semibold sm:text-4xl">
          {brand.headline}
        </h1>
        <p className="text-muted-foreground max-w-3xl text-lg">{brand.definition}</p>
        <div>
          <Link href="/login" className={buttonVariants({ size: "lg" })}>
            {publicPages.login}
          </Link>
        </div>
      </section>

      <section aria-labelledby="como-funciona" className="flex flex-col gap-4 py-8">
        <h2 id="como-funciona" className="text-foreground text-xl font-semibold">
          {publicPages.howItWorksTitle}
        </h2>
        <ol className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {publicPages.steps.map((step, index) => (
            <li key={step.title} className="border-border bg-surface rounded-md border p-5">
              <p className="text-primary text-sm font-semibold">{index + 1}</p>
              <h3 className="text-foreground mt-1 font-semibold">{step.title}</h3>
              <p className="text-muted-foreground mt-2 text-sm">{step.text}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="grid gap-6 py-8 md:grid-cols-2">
        <div className="flex flex-col gap-2">
          <h2 className="text-foreground text-xl font-semibold">{publicPages.referencesTitle}</h2>
          <p className="text-muted-foreground text-sm">{publicPages.references}</p>
          <p className="text-muted-foreground text-sm">{legal.aiProvider}</p>
        </div>
        <div className="flex flex-col gap-2">
          <h2 className="text-foreground text-xl font-semibold">{publicPages.limitsTitle}</h2>
          <ul className="text-muted-foreground list-disc pl-5 text-sm">
            {publicPages.limits.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </section>
    </PublicShell>
  );
}
