import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

import { buildCsp, createNonce } from "@/lib/csp";

const PROTECTED_PREFIX = "/app";

/**
 * Refreshes the Supabase session cookie on every request and redirects anonymous visitors away
 * from the private area. This is an optimistic check only: FastAPI authorizes every request.
 */
export async function proxy(request: NextRequest) {
  const nonce = createNonce();
  const csp = buildCsp(nonce, process.env.NODE_ENV === "development");
  // Next.js reads the nonce from the request's CSP header and adds it to its own scripts.
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("content-security-policy", csp);
  const next = () => NextResponse.next({ request: { headers: requestHeaders } });
  const secure = (result: NextResponse) => {
    result.headers.set("content-security-policy", csp);
    return result;
  };

  let response = next();
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL ?? "",
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? "",
    {
      cookieOptions: {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
      },
      cookies: {
        getAll: () => request.cookies.getAll(),
        setAll: (cookiesToSet, headers) => {
          for (const { name, value } of cookiesToSet) request.cookies.set(name, value);
          requestHeaders.set("cookie", request.cookies.toString());
          response = next();
          for (const { name, value, options } of cookiesToSet) {
            response.cookies.set(name, value, options);
          }
          for (const [key, value] of Object.entries(headers ?? {})) {
            response.headers.set(key, String(value));
          }
        },
      },
    },
  );

  const { data } = await supabase.auth.getClaims();
  const isAuthenticated = Boolean(data?.claims?.sub);
  const { pathname } = request.nextUrl;

  if (pathname.startsWith(PROTECTED_PREFIX) && !isAuthenticated) {
    const login = request.nextUrl.clone();
    login.pathname = "/login";
    login.search = "";
    return secure(NextResponse.redirect(login));
  }
  if (pathname === "/login" && isAuthenticated) {
    const home = request.nextUrl.clone();
    home.pathname = "/app";
    home.search = "";
    return secure(NextResponse.redirect(home));
  }
  return secure(response);
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|api/backend).*)"],
};
