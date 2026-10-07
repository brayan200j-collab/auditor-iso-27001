import type { Metadata } from "next";

import { PublicShell } from "@/components/shared/PublicShell";
import { Card } from "@/components/ui/card";
import { auth } from "@/content/es";
import { ResetPasswordForm } from "@/features/auth";

export const metadata: Metadata = { title: auth.reset.title };

export default function ResetPasswordPage() {
  return (
    <PublicShell>
      <Card className="mx-auto flex w-full max-w-md flex-col gap-4">
        <h1 className="text-foreground text-lg font-semibold">{auth.reset.title}</h1>
        <ResetPasswordForm />
      </Card>
    </PublicShell>
  );
}
