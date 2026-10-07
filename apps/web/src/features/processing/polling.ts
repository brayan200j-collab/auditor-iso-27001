/** Statuses in which nothing changes without a user action: polling stops. */
export const STABLE_STATUSES = new Set([
  "DRAFT",
  "RECEIVED",
  "PENDING_REVIEW",
  "APPROVED",
  "REJECTED",
  "FAILED",
]);

const MIN_INTERVAL_MS = 2_000;
const MAX_INTERVAL_MS = 15_000;

/** Increasing interval: 2 s, 3 s, 4.5 s… capped at 15 s. */
export function nextInterval(attempt: number): number {
  return Math.min(MAX_INTERVAL_MS, Math.round(MIN_INTERVAL_MS * 1.5 ** attempt));
}
