import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export function Table({ className, ...props }: ComponentProps<"table">) {
  return (
    <div className="border-border/70 bg-surface shadow-card w-full overflow-x-auto rounded-3xl border">
      <table className={cn("w-full text-left text-sm", className)} {...props} />
    </div>
  );
}

export function THead(props: ComponentProps<"thead">) {
  return (
    <thead
      className="bg-surface-muted/70 text-muted-foreground text-xs tracking-wide uppercase"
      {...props}
    />
  );
}

export function TBody(props: ComponentProps<"tbody">) {
  return <tbody className="divide-border divide-y" {...props} />;
}

export function TR(props: ComponentProps<"tr">) {
  return <tr {...props} />;
}

export function TH({ className, ...props }: ComponentProps<"th">) {
  return <th scope="col" className={cn("px-5 py-3.5 font-medium", className)} {...props} />;
}

export function TD({ className, ...props }: ComponentProps<"td">) {
  return <td className={cn("text-foreground px-5 py-4 align-top", className)} {...props} />;
}
