import { NextRequest } from "next/server";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/auth", () => ({ getAccessToken: vi.fn(async () => "user-token") }));
vi.mock("@/lib/env", () => ({
  env: () => ({
    NEXT_PUBLIC_API_URL: "http://api.test",
    NEXT_PUBLIC_SITE_URL: "http://localhost:3000",
  }),
}));

const { GET, POST } = await import("./route");

function call(
  handler: typeof GET,
  path: string[],
  init?: { method?: string; headers?: Record<string, string> },
  site = "http://localhost:3000",
) {
  const request = new NextRequest(`${site}/api/backend/${path.join("/")}`, init);
  return handler(request, { params: Promise.resolve({ path }) });
}

describe("BFF proxy", () => {
  const fetchMock = vi.fn(async () => new Response("{}", { status: 200 }));

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    fetchMock.mockClear();
  });
  afterEach(() => vi.unstubAllGlobals());

  it("forwards API calls with the user's token", async () => {
    const response = await call(GET, ["api", "v1", "me"]);
    expect(response.status).toBe(200);
    const [url, init] = fetchMock.mock.calls[0] as unknown as [URL, RequestInit];
    expect(String(url)).toBe("http://api.test/api/v1/me");
    expect(new Headers(init.headers).get("authorization")).toBe("Bearer user-token");
  });

  it("refuses paths outside /api/v1", async () => {
    for (const path of [["healthz"], ["api", "v1", "..", "admin"], ["docs"]]) {
      const response = await call(GET, path);
      expect(response.status).toBe(404);
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("rejects cross-site state-changing requests", async () => {
    const response = await call(POST, ["api", "v1", "auth", "login-event"], {
      method: "POST",
      headers: { origin: "https://evil.example" },
    });
    expect(response.status).toBe(403);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("accepts same-origin state-changing requests", async () => {
    const response = await call(POST, ["api", "v1", "auth", "login-event"], {
      method: "POST",
      headers: { origin: "http://localhost:3000" },
    });
    expect(response.status).toBe(200);
  });

  it("accepts the other domains the same deployment is served on", async () => {
    const alias = "https://auditor-iso-27001-nv3h-git-main.vercel.app";
    const upload = ["api", "v1", "evaluations", "e1", "documents"];
    const same = await call(POST, upload, { method: "POST", headers: { origin: alias } }, alias);
    expect(same.status).toBe(200);
    const forged = await call(
      POST,
      upload,
      { method: "POST", headers: { origin: "https://evil.example" } },
      alias,
    );
    expect(forged.status).toBe(403);
  });

  it("accepts the domain the platform forwards, even behind an internal host", async () => {
    const response = await call(POST, ["api", "v1", "auth", "login-event"], {
      method: "POST",
      headers: {
        origin: "https://auditor-iso-27001-nv3h-abc123-team.vercel.app",
        "x-forwarded-host": "auditor-iso-27001-nv3h-abc123-team.vercel.app",
      },
    });
    expect(response.status).toBe(200);
  });

  it("rejects malformed origins", async () => {
    const response = await call(POST, ["api", "v1", "auth", "login-event"], {
      method: "POST",
      headers: { origin: "null" },
    });
    expect(response.status).toBe(403);
  });

  it("never forwards the compressed length of a decompressed upstream body", async () => {
    const body = JSON.stringify({ ticket: "x".repeat(300), expires_in: 300 });
    fetchMock.mockResolvedValueOnce(
      new Response(body, {
        status: 200,
        headers: { "content-type": "application/json", "content-length": "114" },
      }),
    );
    const response = await call(GET, ["api", "v1", "me"]);
    expect(response.headers.get("content-length")).toBeNull();
    expect(await response.json()).toEqual(JSON.parse(body));
  });
});
