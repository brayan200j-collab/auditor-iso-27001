import { common } from "@/content/es";

type ErrorBody = { code?: unknown; message?: unknown } | undefined | null;

/** Extracts the Spanish message from an API error body, falling back to a generic text. */
export function apiErrorMessage(error: unknown): string {
  const body = error as ErrorBody;
  return typeof body?.message === "string" && body.message ? body.message : common.genericError;
}

export function apiErrorCode(error: unknown): string | undefined {
  const body = error as ErrorBody;
  return typeof body?.code === "string" ? body.code : undefined;
}
