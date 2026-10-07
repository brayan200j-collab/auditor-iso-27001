import type { Metadata } from "next";

import { PageHeader } from "@/components/shared/PageHeader";
import { Pagination } from "@/components/shared/Pagination";
import { StatusFilter } from "@/components/shared/StatusFilter";
import { evaluations } from "@/content/es";
import { AssignReviewerForm } from "@/features/admin-evaluations";
import { listUsers } from "@/features/admin-users";
import { EvaluationsTable, listEvaluations } from "@/features/evaluations";
import { pageParam } from "@/lib/format";
import { requireRole } from "@/lib/guards";
import { statusParam } from "@/lib/params";

export const metadata: Metadata = { title: evaluations.adminTitle };

export default async function AdminEvaluationsPage({
  searchParams,
}: PageProps<"/app/admin/evaluaciones">) {
  await requireRole("ADMIN");
  const params = await searchParams;
  const page = pageParam(params.page);
  const status = statusParam(params.status);
  const [result, reviewerPage] = await Promise.all([
    listEvaluations(page, status),
    listUsers({ page: 1, role: "REVIEWER" }),
  ]);
  const reviewers = reviewerPage.items
    .filter((reviewer) => reviewer.active)
    .map((reviewer) => ({ id: reviewer.id, name: reviewer.full_name }));

  return (
    <>
      <PageHeader title={evaluations.adminTitle} description={evaluations.adminDescription} />
      <StatusFilter current={status} />
      <EvaluationsTable
        items={result.items}
        emptyMessage={evaluations.emptyAdmin}
        hrefFor={(evaluation) => `/app/revision/${evaluation.id}`}
        showCompany
        showReviewer
        extra={(evaluation) => (
          <AssignReviewerForm
            evaluationId={evaluation.id}
            evaluationTitle={evaluation.title}
            currentReviewerId={evaluation.reviewer_id}
            reviewers={reviewers}
            disabled={evaluation.status === "APPROVED"}
          />
        )}
      />
      <Pagination
        page={result.meta.page}
        pageSize={result.meta.page_size}
        total={result.meta.total}
        hrefFor={(target) =>
          `/app/admin/evaluaciones?${new URLSearchParams({ page: String(target), ...(status ? { status } : {}) })}`
        }
      />
    </>
  );
}
