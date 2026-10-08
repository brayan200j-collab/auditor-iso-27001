import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

const alertVariants = cva("rounded-md border px-4 py-3 text-sm", {
  variants: {
    tone: {
      info: "border-info/30 bg-info-soft text-info",
      success: "border-success/30 bg-success-soft text-success",
      warning: "border-warning/30 bg-warning-soft text-warning",
      danger: "border-danger/30 bg-danger-soft text-danger",
      neutral: "border-border bg-neutral-soft text-foreground",
    },
  },
  defaultVariants: { tone: "info" },
});

type AlertProps = ComponentProps<"div"> & VariantProps<typeof alertVariants>;

export function Alert({ className, tone, role, ...props }: AlertProps) {
  const liveRole = role ?? (tone === "danger" ? "alert" : "status");
  return <div role={liveRole} className={cn(alertVariants({ tone }), className)} {...props} />;
}
