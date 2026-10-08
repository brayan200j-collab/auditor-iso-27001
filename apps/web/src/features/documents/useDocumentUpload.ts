"use client";

import { useMutation } from "@tanstack/react-query";

import { uploadDocumentDirect, type UploadedDocument } from "@/lib/api/direct-upload";

export type { UploadedDocument };

export function useDocumentUpload(evaluationId: string) {
  return useMutation<UploadedDocument, Error, File>({
    mutationFn: (file) => uploadDocumentDirect(evaluationId, file),
  });
}
