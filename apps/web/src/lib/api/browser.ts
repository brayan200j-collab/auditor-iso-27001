import createClient from "openapi-fetch";

import type { paths } from "./schema";

/**
 * Typed client for Client Components. Requests go to the same-origin BFF route
 * (`/api/backend/...`), which attaches the user's token on the server.
 */
export const browserApi = createClient<paths>({
  baseUrl: typeof window === "undefined" ? "/api/backend" : `${window.location.origin}/api/backend`,
  // Resolved on every call so instrumentation (and test interceptors) installed later apply.
  fetch: (request: Request) => globalThis.fetch(request),
});
