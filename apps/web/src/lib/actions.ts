import { apiErrorMessage } from "@/lib/api/errors";

/** Result returned by Server Actions to client forms. */
export type ActionResult = { ok: true; message?: string } | { ok: false; message: string };

export function failure(error: unknown): ActionResult {
  return { ok: false, message: apiErrorMessage(error) };
}
