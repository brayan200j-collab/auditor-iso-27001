import { FileText } from "lucide-react";

import { Card, CardDescription, CardTitle } from "@/components/ui/card";
import { reviewCopy } from "@/content/es";

import { OpenDocumentButton } from "./OpenDocumentButton";

type ReviewDocument = { id: string; original_name: string; page_count: number };

const copy = reviewCopy.documents;

/** The evaluation's original PDFs, so the reviewer can contrast the AI analysis with the source. */
export function ReviewDocuments({
  evaluationId,
  documents,
}: {
  evaluationId: string;
  documents: ReviewDocument[];
}) {
  return (
    <Card className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <CardTitle>{copy.title}</CardTitle>
        <CardDescription>{copy.hint}</CardDescription>
      </div>
      {documents.length === 0 ? <p className="text-sm">{copy.empty}</p> : null}
      <ul className="flex flex-col gap-2">
        {documents.map((document) => (
          <li
            key={document.id}
            className="border-border flex flex-wrap items-center justify-between gap-3 rounded-md border p-3"
          >
            <span className="flex items-center gap-2 text-sm">
              <FileText className="text-muted-foreground size-4" aria-hidden="true" />
              <span className="font-medium">{document.original_name}</span>
              <span className="text-muted-foreground">· {copy.pages(document.page_count)}</span>
            </span>
            <OpenDocumentButton
              evaluationId={evaluationId}
              documentId={document.id}
              label={copy.open}
            />
          </li>
        ))}
      </ul>
    </Card>
  );
}
