import Link from "next/link";
import type { ReactNode } from "react";

import { nav, roleLabels } from "@/content/es";
import type { NavItem } from "@/lib/navigation";

import { BrandMark } from "./BrandMark";

type AppShellProps = {
  userName: string;
  role: keyof typeof roleLabels;
  companyName?: string | null;
  items: NavItem[];
  actions: ReactNode;
  children: ReactNode;
};

export function AppShell({ userName, role, companyName, items, actions, children }: AppShellProps) {
  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="border-border bg-surface border-b">
        <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-3">
          <BrandMark href="/app" />
          <div className="flex items-center gap-4">
            <p className="text-muted-foreground text-sm">
              {nav.signedInAs(userName, roleLabels[role])}
              {companyName ? ` · ${companyName}` : ""}
            </p>
            {actions}
          </div>
        </div>
        <nav aria-label={nav.main} className="mx-auto w-full max-w-6xl px-6">
          <ul className="flex flex-wrap gap-1 text-sm">
            {items.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="text-foreground hover:bg-surface-muted inline-block rounded-t-md px-3 py-2"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </header>
      <main
        id="contenido"
        className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-8"
      >
        {children}
      </main>
    </div>
  );
}
