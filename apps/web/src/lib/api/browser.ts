import createClient from "openapi-fetch";

import type { paths } from "./schema";

/**
 * Typed client for Client Components. Requests go to the same-origin BFF route
 * (`/api/backend/...`), which attaches the user's token on the server.
 */
export const browserApi = createClient<paths>({ baseUrl: "/api/backend" });
