import { type NextRequest } from "next/server";

import { getAccessToken } from "@/lib/auth";
import { env } from "@/lib/env";

/**
 * Backend-for-frontend proxy used by Client Components. It only forwards `/api/v1/*`, checks the
 * Origin of state-changing requests (CSRF) and attaches the user's access token server-side, so
 * browser JavaScript never handles the token.
 */

const FORWARDED_REQUEST_HEADERS = ["accept", "content-type", "content-length", "x-request-id"];
// Never content-length/content-encoding: fetch() already decompressed the upstream body (the API
// host serves brotli), so the upstream length would truncate what the browser reads.
const FORWARDED_RESPONSE_HEADERS = [
  "content-type",
  "content-disposition",
  "x-request-id",
  "retry-after",
];
const SAFE_METHODS = new Set(["GET", "HEAD"]);
const ALLOWED_PATH = /^api\/v1\/[A-Za-z0-9\-_/]+$/;

type Context = { params: Promise<{ path: string[] }> };

function jsonError(status: number, code: string, message: string): Response {
  return Response.json({ code, message, request_id: null }, { status });
}

/**
 * CSRF guard for state-changing calls: the browser's Origin must be this site. The configured
 * site URL and the domain the browser actually used (Host / X-Forwarded-Host, set by the hosting
 * platform) are both accepted, because one deployment is served under several domains; another
 * site's Origin never matches either.
 */
function isSameOrigin(request: NextRequest): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return request.headers.get("sec-fetch-site") === "same-origin";
  let originHost: string;
  try {
    originHost = new URL(origin).host;
  } catch {
    return false;
  }
  const allowed = new Set([
    new URL(env().NEXT_PUBLIC_SITE_URL).host,
    request.nextUrl.host,
    request.headers.get("x-forwarded-host")?.split(",")[0]?.trim(),
    request.headers.get("host"),
  ]);
  if (allowed.has(originHost)) return true;
  // Diagnostic only: origins and hosts are not sensitive and help explain rejected requests.
  console.warn("bff_origin_rejected", { origin, allowed: [...allowed].filter(Boolean) });
  return false;
}

async function forward(request: NextRequest, context: Context): Promise<Response> {
  const { path } = await context.params;
  const target = path.join("/");
  if (!ALLOWED_PATH.test(target) || target.includes("..")) {
    return jsonError(404, "NOT_FOUND", "El recurso solicitado no existe o no está disponible.");
  }
  if (!SAFE_METHODS.has(request.method) && !isSameOrigin(request)) {
    return jsonError(403, "FORBIDDEN", "No tienes permiso para realizar esta acción.");
  }

  const url = new URL(`${env().NEXT_PUBLIC_API_URL}/${target}`);
  url.search = request.nextUrl.search;
  const headers = new Headers();
  for (const name of FORWARDED_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const token = await getAccessToken();
  if (token) headers.set("authorization", `Bearer ${token}`);

  const hasBody = !SAFE_METHODS.has(request.method);
  let upstream: Response;
  try {
    upstream = await fetch(url, {
      method: request.method,
      headers,
      body: hasBody ? request.body : undefined,
      cache: "no-store",
      redirect: "manual",
      // Required by undici to stream a request body.
      ...(hasBody ? { duplex: "half" } : {}),
    } as RequestInit);
  } catch {
    return jsonError(
      503,
      "UPSTREAM_UNAVAILABLE",
      "El servicio no está disponible. Intenta más tarde.",
    );
  }

  const responseHeaders = new Headers({ "cache-control": "no-store" });
  for (const name of FORWARDED_RESPONSE_HEADERS) {
    const value = upstream.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }
  return new Response(upstream.body, { status: upstream.status, headers: responseHeaders });
}

export const GET = forward;
export const POST = forward;
export const PUT = forward;
export const PATCH = forward;
export const DELETE = forward;
