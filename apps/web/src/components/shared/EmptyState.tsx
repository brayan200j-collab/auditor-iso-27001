import type { ReactNode } from "react";

export function EmptyState({ message, action }: { message: string; action?: ReactNode }) {
  return (
    <div className="border-border-strong bg-surface/70 flex flex-col items-start gap-3 rounded-3xl border border-dashed p-6 sm:p-8">
      <p className="text-muted-foreground text-sm">{message}</p>
      {action}
    </div>
  );
}
