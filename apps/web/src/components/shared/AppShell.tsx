import type { ReactNode } from "react";

import { nav, roleLabels } from "@/content/es";
import type { NavItem } from "@/lib/navigation";

import { BrandMark } from "./BrandMark";
import { NavLinks } from "./NavLinks";

type AppShellProps = {
  userName: string;
  role: keyof typeof roleLabels;
  companyName?: string | null;
  items: NavItem[];
  actions: ReactNode;
  children: ReactNode;
};

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  return (
    parts.length > 1 ? `${parts[0]?.[0] ?? ""}${parts[1]?.[0] ?? ""}` : name.slice(0, 2)
  ).toUpperCase();
}

export function AppShell({ userName, role, companyName, items, actions, children }: AppShellProps) {
  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="border-border/70 bg-surface/90 sticky top-0 z-30 border-b backdrop-blur">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-4 px-4 pt-3 sm:px-6">
          <BrandMark href="/app" />
          <div className="flex items-center gap-3">
            <div className="hidden items-center gap-3 sm:flex">
              <span
                aria-hidden="true"
                title={nav.signedInAs(userName, roleLabels[role])}
                className="bg-primary-soft text-secondary-foreground flex size-9 items-center justify-center rounded-full text-xs font-semibold"
              >
                {initials(userName)}
              </span>
              <p className="flex flex-col text-right leading-tight">
                <span className="text-foreground text-sm font-medium">{userName}</span>
                <span className="text-muted-foreground text-xs">
                  {roleLabels[role]}
                  {companyName ? ` · ${companyName}` : ""}
                </span>
              </p>
            </div>
            {actions}
          </div>
        </div>
        <div className="mx-auto mt-3 w-full max-w-6xl px-4 sm:px-6">
          <NavLinks items={items} label={nav.main} />
        </div>
      </header>
      <main
        id="contenido"
        className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 py-8 sm:px-6 sm:py-10"
      >
        {children}
      </main>
      <footer className="text-muted-foreground mx-auto w-full max-w-6xl px-4 pb-8 text-xs sm:px-6">
        <div className="prism-line mb-4 w-16 opacity-80" aria-hidden="true" />
        Auditor Virtual · {nav.footer}
      </footer>
    </div>
  );
}
