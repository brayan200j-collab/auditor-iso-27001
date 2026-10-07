import type { ReactNode } from "react";

export function EmptyState({ message, action }: { message: string; action?: ReactNode }) {
  return (
    <div className="border-border bg-surface flex flex-col items-start gap-3 rounded-md border border-dashed p-6">
      <p className="text-muted-foreground text-sm">{message}</p>
      {action}
    </div>
  );
}
