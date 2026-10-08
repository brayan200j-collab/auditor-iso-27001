import { common } from "@/content/es";

import { browserApi } from "./browser";
import { apiErrorMessage } from "./errors";
import type { components } from "./schema";

export type UploadedDocument = components["schemas"]["DocumentResponse"];

export class UploadError extends Error {}

function apiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_URL;
  if (!base) throw new UploadError(common.genericError);
  return base.replace(/\/+$/, "");
}

/**
 * Uploads a PDF straight to the API. Web hosting limits function request bodies (4.5 MB on
 * Vercel) below the 20 MB the product accepts, so the BFF only obtains a short-lived ticket
 * bound to this user and evaluation; the session token never leaves its HttpOnly cookie.
 */
export async function uploadDocumentDirect(
  evaluationId: string,
  file: File,
): Promise<UploadedDocument> {
  const { data: ticket, error } = await browserApi.POST(
    "/api/v1/evaluations/{evaluation_id}/documents/upload-ticket",
    { params: { path: { evaluation_id: evaluationId } } },
  );
  if (!ticket) throw new UploadError(apiErrorMessage(error));

  const form = new FormData();
  form.append("file", file, file.name);
  let response: Response;
  try {
    response = await globalThis.fetch(
      `${apiBase()}/api/v1/evaluations/${encodeURIComponent(evaluationId)}/documents`,
      { method: "POST", headers: { "x-upload-ticket": ticket.ticket }, body: form },
    );
  } catch {
    throw new UploadError(common.genericError);
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new UploadError(apiErrorMessage(body));
  return body as UploadedDocument;
}
