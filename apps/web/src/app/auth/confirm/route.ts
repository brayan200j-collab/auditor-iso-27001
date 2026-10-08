import { NextResponse, type NextRequest } from "next/server";

import { verifyEmailLink, type EmailLinkType } from "@/lib/auth";

const LINK_TYPES = new Set<EmailLinkType>(["recovery", "invite"]);

function isLinkType(value: string | null): value is EmailLinkType {
  return value !== null && LINK_TYPES.has(value as EmailLinkType);
}

/**
 * Target of invitation and recovery emails. Verifies the one-time token on the server, which
 * opens an HttpOnly session, and continues to the password form. Never redirects elsewhere.
 */
export async function GET(request: NextRequest) {
  const tokenHash = request.nextUrl.searchParams.get("token_hash");
  const type = request.nextUrl.searchParams.get("type");
  const destination = request.nextUrl.clone();
  destination.search = "";
  destination.pathname =
    tokenHash && isLinkType(type) && (await verifyEmailLink(tokenHash, type))
      ? "/restablecer"
      : "/recuperar";
  return NextResponse.redirect(destination);
}
