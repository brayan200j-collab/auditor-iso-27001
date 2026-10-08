import type { Metadata } from "next";
import Link from "next/link";

import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { StatusFilter } from "@/components/shared/StatusFilter";
import { buttonVariants } from "@/components/ui/button";
import { evaluations } from "@/content/es";
import { EvaluationsTable, listEvaluations } from "@/features/evaluations";
import { pageParam } from "@/lib/format";
import { requireRole } from "@/lib/guards";
import { statusParam } from "@/lib/params";

export const metadata: Metadata = { title: evaluations.listTitle };

export default async function MyEvaluationsPage({ searchParams }: PageProps<"/app/evaluaciones">) {
  await requireRole("SME");
  const params = await searchParams;
  const page = pageParam(params.page);
  const status = statusParam(params.status);
  const result = await listEvaluations(page, status);

  return (
    <>
      <PageHeader
        title={evaluations.listTitle}
        description={evaluations.listDescription}
        actions={
          <Link href="/app/evaluaciones/nueva" className={buttonVariants()}>
            {evaluations.newTitle}
          </Link>
        }
      />
      <StatusFilter current={status} />
      <EvaluationsTable
        items={result.items}
        emptyMessage={evaluations.empty}
        hrefFor={(evaluation) => `/app/evaluaciones/${evaluation.id}`}
      />
      <Pagination
        page={result.meta.page}
        pageSize={result.meta.page_size}
        total={result.meta.total}
        hrefFor={(target) =>
          `/app/evaluaciones?${new URLSearchParams({ page: String(target), ...(status ? { status } : {}) })}`
        }
      />
    </>
  );
}
