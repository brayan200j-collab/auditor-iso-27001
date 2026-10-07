import { beforeEach, describe, expect, it } from "vitest";

import { consume, resetRateLimits } from "./rate-limit";

describe("consume", () => {
  beforeEach(() => resetRateLimits());

  it("allows up to the limit within a window and then blocks", () => {
    const results = Array.from({ length: 4 }, () => consume("login:ip:1", 3, 1000, 0));
    expect(results).toEqual([true, true, true, false]);
  });

  it("resets after the window", () => {
    consume("k", 1, 1000, 0);
    expect(consume("k", 1, 1000, 500)).toBe(false);
    expect(consume("k", 1, 1000, 1000)).toBe(true);
  });
});
