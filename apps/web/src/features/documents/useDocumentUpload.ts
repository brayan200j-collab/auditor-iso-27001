"use client";

import { useMutation } from "@tanstack/react-query";

import { browserApi } from "@/lib/api/browser";
import { apiErrorMessage } from "@/lib/api/errors";
import type { components } from "@/lib/api/schema";

export type UploadedDocument = components["schemas"]["DocumentResponse"];

export function useDocumentUpload(evaluationId: string) {
  return useMutation<UploadedDocument, Error, File>({
    mutationFn: async (file) => {
      const { data, error } = await browserApi.POST(
        "/api/v1/evaluations/{evaluation_id}/documents",
        {
          params: { path: { evaluation_id: evaluationId } },
          body: { file: file as unknown as string },
          bodySerializer: () => {
            const form = new FormData();
            form.append("file", file, file.name);
            return form;
          },
        },
      );
      if (!data) throw new Error(apiErrorMessage(error));
      return data;
    },
  });
}
