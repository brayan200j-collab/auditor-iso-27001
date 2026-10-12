import Link from "next/link";
import type { ReactNode } from "react";

import { buttonVariants } from "@/components/ui/button";
import { brand, landing, legal, publicPages } from "@/content/es";

import { BrandMark } from "./BrandMark";

const SECTIONS = [
  { href: "/guia", label: landing.nav.guide },
  { href: "/#que-es", label: landing.nav.what },
  { href: "/#como-funciona", label: landing.nav.how },
  { href: "/#ventajas", label: landing.nav.benefits },
  { href: "/#resultados", label: landing.nav.results },
  { href: "/#seguridad", label: landing.nav.trust },
];

// The header keeps the essentials on one line; the footer lists every section.
const HEADER_SECTIONS = SECTIONS.filter((section) => section.href !== "/#que-es");

export function PublicShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="border-border/70 bg-surface/90 sticky top-0 z-30 border-b backdrop-blur print:hidden">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3.5 sm:px-6">
          <BrandMark />
          <nav aria-label={landing.nav.label} className="hidden lg:block">
            <ul className="flex items-center gap-1 text-sm">
              {HEADER_SECTIONS.map((section) => (
                <li key={section.href}>
                  <Link
                    href={section.href}
                    className="text-muted-foreground hover:bg-surface-muted hover:text-foreground rounded-full px-3 py-2 font-medium whitespace-nowrap transition-colors"
                  >
                    {section.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
          <nav aria-label={publicPages.login} className="flex items-center gap-2 text-sm">
            <Link
              href="/privacidad"
              className="text-muted-foreground hover:text-foreground hidden px-2 font-medium whitespace-nowrap xl:inline"
            >
              {publicPages.privacy}
            </Link>
            <Link href="/login" className={buttonVariants({ size: "sm" })}>
              {publicPages.login}
            </Link>
          </nav>
        </div>
      </header>
      <main
        id="contenido"
        className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-8 sm:px-6"
      >
        {children}
      </main>
      <footer className="border-border/70 bg-surface border-t print:hidden">
        <div className="mx-auto grid w-full max-w-6xl gap-8 px-4 py-10 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr]">
          <div className="flex flex-col gap-3">
            <BrandMark showTagline />
            <div className="prism-line w-20" aria-hidden="true" />
            <p className="text-muted-foreground text-xs leading-relaxed">{publicPages.academic}</p>
          </div>
          <nav aria-label={landing.footer.product} className="flex flex-col gap-2 text-sm">
            <p className="text-foreground font-semibold">{landing.footer.product}</p>
            {SECTIONS.map((section) => (
              <Link
                key={section.href}
                href={section.href}
                className="text-muted-foreground hover:text-foreground"
              >
                {section.label}
              </Link>
            ))}
          </nav>
          <nav aria-label={landing.footer.legal} className="flex flex-col gap-2 text-sm">
            <p className="text-foreground font-semibold">{landing.footer.legal}</p>
            <Link href="/privacidad" className="text-muted-foreground hover:text-foreground">
              {publicPages.privacy}
            </Link>
            <Link href="/login" className="text-muted-foreground hover:text-foreground">
              {publicPages.login}
            </Link>
          </nav>
        </div>
        <div className="border-border/70 border-t">
          <p className="text-muted-foreground mx-auto w-full max-w-6xl px-4 py-5 text-xs leading-relaxed sm:px-6">
            {legal.scopeDisclaimer} · {brand.name}
          </p>
        </div>
      </footer>
    </div>
  );
}
