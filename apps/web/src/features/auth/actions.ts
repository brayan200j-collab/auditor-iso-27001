"use server";

import { redirect } from "next/navigation";

import { auth } from "@/content/es";
import type { ActionResult } from "@/lib/actions";
import { serverApi } from "@/lib/api/server";
import {
  getAccessToken,
  requestPasswordReset,
  signInWithPassword,
  signOut,
  updatePassword,
} from "@/lib/auth";
import { env } from "@/lib/env";
import { consume } from "@/lib/rate-limit";
import { clientIp } from "@/lib/request";

import { loginSchema, recoverySchema, resetSchema } from "./schemas";

const MINUTE = 60_000;

async function allowed(scope: string, email: string): Promise<boolean> {
  const ip = await clientIp();
  const byIp = consume(`${scope}:ip:${ip}`, 10, MINUTE);
  const byEmail = consume(`${scope}:email:${email.toLowerCase()}`, 5, 15 * MINUTE);
  return byIp && byEmail;
}

export async function signInAction(input: unknown): Promise<ActionResult> {
  const parsed = loginSchema.safeParse(input);
  if (!parsed.success) return { ok: false, message: auth.login.invalidCredentials };
  const { email, password } = parsed.data;
  if (!(await allowed("login", email))) return { ok: false, message: auth.tooManyAttempts };

  const result = await signInWithPassword(email, password);
  if (!result.ok) return { ok: false, message: auth.login.invalidCredentials };

  const api = await serverApi(result.accessToken);
  const { response } = await api.POST("/api/v1/auth/login-event");
  if (response.status === 401) {
    // Valid Supabase account without an active profile in Auditor Virtual.
    await signOut();
    return { ok: false, message: auth.login.invalidCredentials };
  }
  redirect("/app");
}

export async function signOutAction(): Promise<void> {
  const token = await getAccessToken();
  if (token) {
    const api = await serverApi(token);
    await api.POST("/api/v1/auth/logout-event");
  }
  await signOut();
  redirect("/login");
}

export async function requestRecoveryAction(input: unknown): Promise<ActionResult> {
  const parsed = recoverySchema.safeParse(input);
  if (parsed.success && (await allowed("recovery", parsed.data.email))) {
    const redirectTo = `${env().NEXT_PUBLIC_SITE_URL}/restablecer`;
    await requestPasswordReset(parsed.data.email, redirectTo);
  }
  // Same answer in every case: never reveal whether an account exists.
  return { ok: true, message: auth.recovery.sent };
}

export async function resetPasswordAction(input: unknown): Promise<ActionResult> {
  const parsed = resetSchema.safeParse(input);
  if (!parsed.success) return { ok: false, message: auth.validation.passwordWeak };
  const updated = await updatePassword(parsed.data.password);
  if (!updated) return { ok: false, message: auth.reset.expired };
  await signOut();
  return { ok: true, message: auth.reset.success };
}
