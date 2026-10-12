import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export function Card({ className, ...props }: ComponentProps<"section">) {
  return (
    <section
      className={cn(
        "border-border/70 bg-surface shadow-card rounded-3xl border p-6 sm:p-7",
        className,
      )}
      {...props}
    />
  );
}

export function CardTitle({ className, children, ...props }: ComponentProps<"h2">) {
  return (
    <h2
      className={cn("text-foreground text-lg font-semibold tracking-tight", className)}
      {...props}
    >
      {children}
    </h2>
  );
}

export function CardDescription({ className, ...props }: ComponentProps<"p">) {
  return <p className={cn("text-muted-foreground text-sm", className)} {...props} />;
}
