import type { Metadata } from "next";

import { PublicShell } from "@/components/shared/PublicShell";
import { Card, CardDescription } from "@/components/ui/card";
import { auth } from "@/content/es";
import { LoginForm } from "@/features/auth";

export const metadata: Metadata = { title: auth.login.title };

export default function LoginPage() {
  return (
    <PublicShell>
      <Card className="mx-auto flex w-full max-w-md flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-foreground text-lg font-semibold">{auth.login.title}</h1>
          <CardDescription>{auth.login.description}</CardDescription>
        </div>
        <LoginForm />
      </Card>
    </PublicShell>
  );
}
