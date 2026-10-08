import { documentsCopy } from "@/content/es";

export const MAX_UPLOAD_BYTES = 20 * 1024 * 1024;

/** Client-side pre-check for a better experience; the API validates everything again. */
export function preCheck(file: File): string | null {
  if (file.size === 0) return documentsCopy.clientErrors.empty;
  if (file.size > MAX_UPLOAD_BYTES) return documentsCopy.clientErrors.size;
  const looksPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
  if (!looksPdf) return documentsCopy.clientErrors.type;
  return null;
}
