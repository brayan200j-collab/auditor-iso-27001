import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export function Table({ className, ...props }: ComponentProps<"table">) {
  return (
    <div className="border-border bg-surface w-full overflow-x-auto rounded-md border">
      <table className={cn("w-full text-left text-sm", className)} {...props} />
    </div>
  );
}

export function THead(props: ComponentProps<"thead">) {
  return <thead className="bg-surface-muted text-muted-foreground" {...props} />;
}

export function TBody(props: ComponentProps<"tbody">) {
  return <tbody className="divide-border divide-y" {...props} />;
}

export function TR(props: ComponentProps<"tr">) {
  return <tr {...props} />;
}

export function TH({ className, ...props }: ComponentProps<"th">) {
  return <th scope="col" className={cn("px-4 py-3 font-semibold", className)} {...props} />;
}

export function TD({ className, ...props }: ComponentProps<"td">) {
  return <td className={cn("text-foreground px-4 py-3 align-top", className)} {...props} />;
}
