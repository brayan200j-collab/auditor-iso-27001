import Link from "next/link";
import type { ReactNode } from "react";

import { legal, publicPages } from "@/content/es";

import { BrandMark } from "./BrandMark";

export function PublicShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="border-border bg-surface border-b">
        <div className="mx-auto flex w-full max-w-5xl items-center justify-between gap-4 px-6 py-4">
          <BrandMark />
          <nav aria-label={publicPages.login} className="flex items-center gap-4 text-sm">
            <Link href="/privacidad" className="text-muted-foreground hover:text-foreground">
              {publicPages.privacy}
            </Link>
            <Link
              href="/login"
              className="bg-primary text-primary-foreground hover:bg-primary-hover rounded-md px-4 py-2 font-medium"
            >
              {publicPages.login}
            </Link>
          </nav>
        </div>
      </header>
      <main id="contenido" className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-6 py-10">
        {children}
      </main>
      <footer className="border-border bg-surface border-t">
        <div className="text-muted-foreground mx-auto flex w-full max-w-5xl flex-col gap-2 px-6 py-6 text-xs">
          <p>{legal.scopeDisclaimer}</p>
          <p>{publicPages.academic}</p>
        </div>
      </footer>
    </div>
  );
}
