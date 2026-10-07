import "server-only";

import { notFound } from "next/navigation";

import { requireProfile, type Profile, type Role } from "@/lib/profile";

/**
 * Hides screens that do not belong to the user's role. Presentation only: the API enforces every
 * permission regardless of what the web app shows.
 */
export async function requireRole(...roles: Role[]): Promise<Profile> {
  const profile = await requireProfile();
  if (!roles.includes(profile.role)) notFound();
  return profile;
}
