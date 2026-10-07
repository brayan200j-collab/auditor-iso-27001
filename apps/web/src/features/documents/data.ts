import "server-only";

import { serverApi } from "@/lib/api/server";

import type { UploadedDocument } from "./useDocumentUpload";

export async function listDocuments(evaluationId: string): Promise<UploadedDocument[]> {
  const api = await serverApi();
  const { data } = await api.GET("/api/v1/evaluations/{evaluation_id}/documents", {
    params: { path: { evaluation_id: evaluationId } },
  });
  return data ?? [];
}
