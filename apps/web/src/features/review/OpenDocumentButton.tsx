"use client";

import { ExternalLink } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { reviewCopy } from "@/content/es";
import { browserApi } from "@/lib/api/browser";
import { apiErrorMessage } from "@/lib/api/errors";

type OpenDocumentButtonProps = {
  evaluationId: string;
  documentId: string;
  /** Opens the PDF at this page (browsers' PDF viewers honour `#page=N`). */
  page?: number;
  label: string;
};

/** Opens the original PDF in a new tab through a short-lived, audited link. */
export function OpenDocumentButton({
  evaluationId,
  documentId,
  page,
  label,
}: OpenDocumentButtonProps) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const open = async () => {
    setError(null);
    // Opened synchronously so popup blockers allow it; the URL is set once the link arrives.
    const tab = window.open("about:blank", "_blank");
    if (tab) tab.opener = null;
    setBusy(true);
    const { data, error: failure } = await browserApi.GET(
      "/api/v1/evaluations/{evaluation_id}/documents/{document_id}/link",
      { params: { path: { evaluation_id: evaluationId, document_id: documentId } } },
    );
    setBusy(false);
    if (!data) {
      tab?.close();
      setError(apiErrorMessage(failure));
      return;
    }
    const url = page ? `${data.url}#page=${page}` : data.url;
    if (tab) tab.location.href = url;
    else window.location.assign(url);
  };

  return (
    <span className="inline-flex flex-col gap-1">
      <Button type="button" variant="outline" size="sm" disabled={busy} onClick={() => void open()}>
        <ExternalLink className="size-4" aria-hidden="true" />
        {busy ? reviewCopy.documents.opening : label}
      </Button>
      {error ? (
        <span role="alert" className="text-danger text-xs">
          {error}
        </span>
      ) : null}
    </span>
  );
}
