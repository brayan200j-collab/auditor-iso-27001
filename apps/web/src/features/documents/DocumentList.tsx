"use client";

import { FileText } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { EmptyState } from "@/components/shared/EmptyState";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { documentsCopy } from "@/content/es";
import { browserApi } from "@/lib/api/browser";
import { apiErrorMessage } from "@/lib/api/errors";
import { formatDateTime } from "@/lib/format";

import type { UploadedDocument } from "./useDocumentUpload";

type DocumentListProps = {
  evaluationId: string;
  documents: UploadedDocument[];
  canDelete: boolean;
};

export function DocumentList({ evaluationId, documents, canDelete }: DocumentListProps) {
  const router = useRouter();
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [pending, startTransition] = useTransition();

  if (documents.length === 0) return <EmptyState message={documentsCopy.empty} />;

  const remove = (documentId: string) => {
    startTransition(async () => {
      const { error } = await browserApi.DELETE(
        "/api/v1/evaluations/{evaluation_id}/documents/{document_id}",
        { params: { path: { evaluation_id: evaluationId, document_id: documentId } } },
      );
      setMessage(
        error
          ? { ok: false, text: apiErrorMessage(error) }
          : { ok: true, text: documentsCopy.removed },
      );
      router.refresh();
    });
  };

  return (
    <div className="flex flex-col gap-3">
      {message ? <Alert tone={message.ok ? "success" : "danger"}>{message.text}</Alert> : null}
      <ul className="divide-border border-border bg-surface divide-y rounded-md border">
        {documents.map((document) => (
          <li key={document.id} className="flex flex-wrap items-center justify-between gap-3 p-4">
            <div className="flex items-center gap-3">
              <FileText className="text-primary size-5" aria-hidden="true" />
              <div>
                <p className="text-foreground text-sm font-medium">{document.original_name}</p>
                <p className="text-muted-foreground text-xs">
                  {documentsCopy.pages(document.page_count)} ·{" "}
                  {documentsCopy.size(document.size_bytes)} · {formatDateTime(document.created_at)}
                </p>
              </div>
            </div>
            {canDelete ? (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                disabled={pending}
                aria-label={documentsCopy.removeLabel(document.original_name)}
                onClick={() => remove(document.id)}
              >
                {documentsCopy.remove}
              </Button>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
