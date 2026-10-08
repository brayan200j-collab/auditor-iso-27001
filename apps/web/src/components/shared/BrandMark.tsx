import Link from "next/link";

import { brand } from "@/content/es";

export function BrandMark({ href = "/" }: { href?: string }) {
  return (
    <Link href={href} className="flex flex-col leading-tight">
      <span className="text-primary text-lg font-semibold">{brand.name}</span>
      <span className="text-muted-foreground text-xs">{brand.tagline}</span>
    </Link>
  );
}
