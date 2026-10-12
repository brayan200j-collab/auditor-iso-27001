import { CircleCheck } from "lucide-react";
import type { Metadata } from "next";

import { LogoSymbol } from "@/components/shared/BrandMark";
import { PublicShell } from "@/components/shared/PublicShell";
import { Card, CardDescription } from "@/components/ui/card";
import { auth, brand, landing } from "@/content/es";
import { LoginForm } from "@/features/auth";

export const metadata: Metadata = { title: auth.login.title };

// The sign-in action waits for the API, which may need up to a minute to wake up on a free plan.
export const maxDuration = 60;

export default function LoginPage() {
  return (
    <PublicShell>
      <div className="shadow-card mx-auto grid w-full max-w-5xl overflow-hidden rounded-4xl lg:grid-cols-2">
        <aside className="bg-primary text-primary-foreground relative hidden flex-col justify-between gap-8 p-10 lg:flex">
          <LogoSymbol inverted className="size-14" />
          <div className="flex flex-col gap-4">
            <p className="text-3xl leading-tight font-light tracking-[-0.02em]">{brand.headline}</p>
            <ul className="flex flex-col gap-3 text-sm">
              {landing.what.pillars.map((pillar) => (
                <li key={pillar.title} className="flex items-center gap-2">
                  <CircleCheck className="size-5 shrink-0" aria-hidden="true" />
                  {pillar.title}
                </li>
              ))}
            </ul>
          </div>
          <p className="text-xs leading-relaxed text-white/90">{landing.inviteNote}</p>
          <div
            aria-hidden="true"
            className="absolute -right-16 -bottom-16 size-56 rounded-full bg-black/10"
          />
        </aside>
        <Card className="flex flex-col justify-center gap-6 rounded-none border-0 p-8 shadow-none sm:p-10">
          <div className="flex flex-col gap-2">
            <h1 className="text-foreground text-2xl font-semibold tracking-tight">
              {auth.login.title}
            </h1>
            <CardDescription>{auth.login.description}</CardDescription>
          </div>
          <LoginForm />
        </Card>
      </div>
    </PublicShell>
  );
}
