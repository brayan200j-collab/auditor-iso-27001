import "server-only";

import { redirect } from "next/navigation";

import { serverApi } from "@/lib/api/server";

import type { components } from "./api/schema";

export type Profile = components["schemas"]["ProfileResponse"];
export type Role = Profile["role"];

/** Loads the signed-in user's profile from the API, or sends the visitor to the login page. */
export async function requireProfile(): Promise<Profile> {
  const api = await serverApi();
  const { data, response } = await api.GET("/api/v1/me");
  if (!data) {
    if (response.status === 401) redirect("/login");
    throw new Error(`Unable to load profile (${response.status})`);
  }
  return data;
}
