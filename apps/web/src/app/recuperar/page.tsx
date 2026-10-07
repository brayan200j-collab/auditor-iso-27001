import type { Metadata } from "next";
import Link from "next/link";

import { PublicShell } from "@/components/shared/PublicShell";
import { Card, CardDescription } from "@/components/ui/card";
import { auth } from "@/content/es";
import { RecoveryForm } from "@/features/auth";

export const metadata: Metadata = { title: auth.recovery.title };

export default function RecoveryPage() {
  return (
    <PublicShell>
      <Card className="mx-auto flex w-full max-w-md flex-col gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-foreground text-lg font-semibold">{auth.recovery.title}</h1>
          <CardDescription>{auth.recovery.description}</CardDescription>
        </div>
        <RecoveryForm />
        <Link href="/login" className="text-primary text-sm underline-offset-4 hover:underline">
          {auth.recovery.backToLogin}
        </Link>
      </Card>
    </PublicShell>
  );
}
