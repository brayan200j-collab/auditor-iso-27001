import "server-only";

import createClient from "openapi-fetch";

import { getAccessToken } from "@/lib/auth";
import { env } from "@/lib/env";

import type { paths } from "./schema";

export type ApiClient = ReturnType<typeof createClient<paths>>;

/** Typed FastAPI client for Server Components and Server Actions (adds the user's JWT). */
export async function serverApi(accessToken?: string): Promise<ApiClient> {
  const token = accessToken ?? (await getAccessToken());
  return createClient<paths>({
    baseUrl: env().NEXT_PUBLIC_API_URL,
    headers: token ? { authorization: `Bearer ${token}` } : {},
    cache: "no-store",
  });
}
