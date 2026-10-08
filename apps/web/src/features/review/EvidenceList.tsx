import { FileText, TriangleAlert } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { reviewCopy } from "@/content/es";

import { OpenDocumentButton } from "./OpenDocumentButton";

type Evidence = {
  document_id?: string;
  document_name: string | null;
  page: number;
  quote: string;
  citation_verified: boolean;
};

/** With `evaluationId`, each citation can open the original PDF at its page (reviewers). */
export function EvidenceList({
  evidence,
  evaluationId,
}: {
  evidence: Evidence[];
  evaluationId?: string;
}) {
  if (evidence.length === 0) {
    return <p className="text-muted-foreground text-sm">{reviewCopy.noCitations}</p>;
  }
  return (
    <ul className="flex flex-col gap-3">
      {evidence.map((item, index) => (
        <li key={`${item.page}-${index}`} className="border-border rounded-md border p-3">
          <p className="text-muted-foreground flex flex-wrap items-center gap-2 text-xs">
            <FileText className="size-4" aria-hidden="true" />
            <span className="text-foreground font-medium">{item.document_name ?? "—"}</span>
            <span>· {reviewCopy.page(item.page)}</span>
            {item.citation_verified ? null : (
              <Badge tone="danger">
                <TriangleAlert className="size-3" aria-hidden="true" />
                {reviewCopy.unverified}
              </Badge>
            )}
          </p>
          <blockquote className="border-primary/40 text-foreground mt-2 border-l-4 pl-3 text-sm italic">
            {item.quote}
          </blockquote>
          {item.citation_verified ? null : (
            <p className="text-muted-foreground mt-1 text-xs">{reviewCopy.unverifiedHelp}</p>
          )}
          {evaluationId && item.document_id ? (
            <div className="mt-2">
              <OpenDocumentButton
                evaluationId={evaluationId}
                documentId={item.document_id}
                page={item.page}
                label={reviewCopy.documents.atPage(item.page)}
              />
            </div>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
