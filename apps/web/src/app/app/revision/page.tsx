import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { StatusFilter } from "@/components/shared/StatusFilter";
import { evaluations } from "@/content/es";
import { EvaluationsTable, listEvaluations } from "@/features/evaluations";
import { pageParam } from "@/lib/format";
import { requireRole } from "@/lib/guards";
import { statusParam } from "@/lib/params";

export const metadata: Metadata = { title: evaluations.reviewerTitle };

export default async function AssignedEvaluationsPage({
  searchParams,
}: PageProps<"/app/revision">) {
  await requireRole("REVIEWER", "ADMIN");
  const params = await searchParams;
  const page = pageParam(params.page);
  const status = statusParam(params.status);
  const result = await listEvaluations(page, status);

  return (
    <>
      <PageHeader title={evaluations.reviewerTitle} description={evaluations.reviewerDescription} />
      <StatusFilter current={status} />
      <EvaluationsTable
        items={result.items}
        emptyMessage={evaluations.emptyReviewer}
        hrefFor={(evaluation) => `/app/revision/${evaluation.id}`}
        showCompany
      />
      <Pagination
        page={result.meta.page}
        pageSize={result.meta.page_size}
        total={result.meta.total}
        hrefFor={(target) =>
          `/app/revision?${new URLSearchParams({ page: String(target), ...(status ? { status } : {}) })}`
        }
      />
    </>
  );
}
