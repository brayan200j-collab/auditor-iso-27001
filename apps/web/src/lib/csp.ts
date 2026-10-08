/**
 * Content Security Policy with a per-request nonce (CLAUDE.md section 9).
 *
 * Scripts run only with the nonce Next.js adds to its own tags ('strict-dynamic' lets them load
 * their chunks); no inline or third-party scripts. The browser talks to this origin (Supabase Auth
 * runs on the server, API calls go through the BFF route) and to the API only for PDF uploads. Development adds what React Fast
 * Refresh needs ('unsafe-eval' and the websocket).
 */
export function buildCsp(nonce: string, isDev: boolean, apiOrigin?: string): string {
  const directives: Record<string, string[]> = {
    "default-src": ["'self'"],
    "script-src": [
      "'self'",
      `'nonce-${nonce}'`,
      "'strict-dynamic'",
      ...(isDev ? ["'unsafe-eval'"] : []),
    ],
    "style-src": ["'self'", "'unsafe-inline'"],
    "img-src": ["'self'", "data:", "blob:"],
    "font-src": ["'self'"],
    // The API origin is allowed only for direct PDF uploads with a short-lived ticket.
    "connect-src": ["'self'", ...(apiOrigin ? [apiOrigin] : []), ...(isDev ? ["ws:"] : [])],
    "frame-ancestors": ["'none'"],
    "form-action": ["'self'"],
    "base-uri": ["'self'"],
    "object-src": ["'none'"],
  };
  const policy = Object.entries(directives).map(([name, values]) => `${name} ${values.join(" ")}`);
  if (!isDev) policy.push("upgrade-insecure-requests");
  return policy.join("; ");
}

export function createNonce(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return btoa(String.fromCharCode(...bytes));
}

/** Origin of the API URL, or undefined when it is missing or malformed. */
export function originOf(url: string | undefined): string | undefined {
  if (!url) return undefined;
  try {
    return new URL(url).origin;
  } catch {
    return undefined;
  }
}
