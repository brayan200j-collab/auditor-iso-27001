import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: ComponentProps<"input">) {
  return (
    <input
      className={cn(
        "border-border-strong bg-surface text-foreground placeholder:text-muted-foreground hover:border-muted-foreground focus:border-primary aria-[invalid=true]:border-danger h-11 w-full rounded-md border px-3.5 text-sm transition-colors",
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
        "border-border-strong bg-surface text-foreground placeholder:text-muted-foreground hover:border-muted-foreground focus:border-primary aria-[invalid=true]:border-danger min-h-28 w-full rounded-md border px-3.5 py-2.5 text-sm transition-colors",
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
        "border-border-strong bg-surface text-foreground hover:border-muted-foreground focus:border-primary h-11 w-full rounded-md border px-3.5 text-sm transition-colors",
        className,
      )}
      {...props}
    />
  );
}
