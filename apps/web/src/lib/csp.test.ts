import { describe, expect, it } from "vitest";

import { buildCsp, createNonce, originOf } from "./csp";

describe("buildCsp", () => {
  it("allows only nonce scripts and same-origin connections in production", () => {
    const csp = buildCsp("abc123", false);
    expect(csp).toContain("script-src 'self' 'nonce-abc123' 'strict-dynamic'");
    expect(csp).not.toContain("unsafe-eval");
    expect(csp).toContain("connect-src 'self'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("upgrade-insecure-requests");
    expect(csp).not.toMatch(/script-src[^;]*unsafe-inline/);
  });

  it("adds only what Fast Refresh needs in development", () => {
    const csp = buildCsp("n", true);
    expect(csp).toContain("'unsafe-eval'");
    expect(csp).toContain("connect-src 'self' ws:");
    expect(csp).not.toContain("upgrade-insecure-requests");
  });
});

describe("API origin", () => {
  it("allows connections to the API origin only, for direct uploads", () => {
    const csp = buildCsp("n", false, originOf("https://api.example.com/some/path"));
    expect(csp).toContain("connect-src 'self' https://api.example.com;");
    expect(buildCsp("n", false, originOf("not a url"))).toContain("connect-src 'self';");
  });
});

describe("createNonce", () => {
  it("returns a fresh base64 value each time", () => {
    const first = createNonce();
    expect(first).toMatch(/^[A-Za-z0-9+/]{22}==$/);
    expect(createNonce()).not.toBe(first);
  });
});
