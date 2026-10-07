import { NextResponse, type NextRequest } from "next/server";

import { exchangeRecoveryCode } from "@/lib/auth";

const ALLOWED_NEXT = new Set(["/restablecer"]);

/** Completes the password-recovery link (PKCE code exchange) and continues to a fixed page. */
export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const next = request.nextUrl.searchParams.get("next") ?? "/restablecer";
  const destination = request.nextUrl.clone();
  destination.search = "";
  destination.pathname = ALLOWED_NEXT.has(next) ? next : "/restablecer";
  if (!code || !(await exchangeRecoveryCode(code))) {
    destination.pathname = "/recuperar";
  }
  return NextResponse.redirect(destination);
}
