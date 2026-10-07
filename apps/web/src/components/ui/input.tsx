import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "border-border bg-surface text-foreground placeholder:text-muted-foreground aria-[invalid=true]:border-danger h-10 w-full rounded-md border px-3 text-sm",
        className,
      )}
      {...props}
    />
  );
}

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return (
    <textarea
      className={cn(
        "border-border bg-surface text-foreground placeholder:text-muted-foreground aria-[invalid=true]:border-danger min-h-24 w-full rounded-md border px-3 py-2 text-sm",
        className,
      )}
      {...props}
    />
  );
}

export function Select({ className, ...props }: ComponentProps<"select">) {
  return (
    <select
      className={cn(
        "border-border bg-surface text-foreground h-10 w-full rounded-md border px-3 text-sm",
        className,
      )}
      {...props}
    />
  );
}
