import { describe, expect, it } from "vitest";

import { nextInterval, STABLE_STATUSES } from "./polling";

describe("polling", () => {
  it("backs off progressively and caps the interval", () => {
    const intervals = Array.from({ length: 10 }, (_, attempt) => nextInterval(attempt));
    expect(intervals[0]).toBe(2000);
    expect(intervals).toEqual([...intervals].sort((a, b) => a - b));
    expect(Math.max(...intervals)).toBe(15000);
  });

  it("stops in states that need a person to act", () => {
    for (const status of ["PENDING_REVIEW", "APPROVED", "REJECTED", "FAILED"]) {
      expect(STABLE_STATUSES.has(status)).toBe(true);
    }
    expect(STABLE_STATUSES.has("EXTRACTING")).toBe(false);
    expect(STABLE_STATUSES.has("ANALYZING")).toBe(false);
  });
});
