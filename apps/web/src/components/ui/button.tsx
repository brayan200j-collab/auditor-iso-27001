import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-full text-sm font-medium whitespace-nowrap transition-all duration-150 disabled:pointer-events-none disabled:opacity-55 focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-ring active:translate-y-px",
  {
    variants: {
      variant: {
        primary:
          "bg-primary text-primary-foreground shadow-[0_6px_20px_-8px_rgba(80,80,240,0.7)] hover:bg-primary-hover",
        secondary: "bg-secondary text-secondary-foreground hover:bg-primary-soft",
        outline:
          "border border-muted-foreground/60 bg-surface text-foreground hover:border-foreground hover:bg-surface-muted",
        danger: "bg-danger text-white hover:bg-danger/90",
        ghost: "text-foreground hover:bg-surface-muted",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-9 px-4",
        md: "h-11 px-5",
        lg: "h-12 px-7 text-base",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

type ButtonProps = ComponentProps<"button"> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean };

export function Button({ className, variant, size, asChild = false, ...props }: ButtonProps) {
  const Component = asChild ? Slot : "button";
  return <Component className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
