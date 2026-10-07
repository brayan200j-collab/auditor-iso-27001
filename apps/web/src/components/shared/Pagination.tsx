import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { common, table } from "@/content/es";

type PaginationProps = {
  page: number;
  pageSize: number;
  total: number;
  /** Builds the URL of a page, preserving the current filters. */
  hrefFor: (page: number) => string;
};

export function Pagination({ page, pageSize, total, hrefFor }: PaginationProps) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  if (pages <= 1) return null;
  return (
    <nav aria-label={table.pagination} className="flex items-center justify-between gap-4">
      <p className="text-muted-foreground text-sm">{common.page(page, pages)}</p>
      <div className="flex gap-2">
        {page > 1 ? (
          <Link
            href={hrefFor(page - 1)}
            className={buttonVariants({ variant: "outline", size: "sm" })}
          >
            {table.previous}
          </Link>
        ) : null}
        {page < pages ? (
          <Link
            href={hrefFor(page + 1)}
            className={buttonVariants({ variant: "outline", size: "sm" })}
          >
            {table.next}
          </Link>
        ) : null}
      </div>
    </nav>
  );
}
