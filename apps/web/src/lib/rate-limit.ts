import "server-only";

type Window = { count: number; resetAt: number };

const buckets = new Map<string, Window>();
const MAX_KEYS = 10_000;

/**
 * Fixed-window, in-memory limiter for login and recovery attempts. It protects a single server
 * instance; a multi-instance deployment needs a shared store (see docs/DECISIONS.md, D-016).
 */
export function consume(key: string, limit: number, windowMs: number, now = Date.now()): boolean {
  if (buckets.size > MAX_KEYS) {
    for (const [bucketKey, window] of buckets) if (window.resetAt <= now) buckets.delete(bucketKey);
  }
  const current = buckets.get(key);
  if (!current || current.resetAt <= now) {
    buckets.set(key, { count: 1, resetAt: now + windowMs });
    return true;
  }
  current.count += 1;
  return current.count <= limit;
}

export function resetRateLimits(): void {
  buckets.clear();
}
