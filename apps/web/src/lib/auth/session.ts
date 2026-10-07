import "server-only";

import { createSupabaseServerClient } from "@/lib/auth/supabase";

/**
 * Returns the current access token (refreshed by the proxy). The API verifies it on every call;
 * the web app never makes authorization decisions from it.
 */
export async function getAccessToken(): Promise<string | null> {
  const supabase = await createSupabaseServerClient();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export type SignInResult = { ok: true; accessToken: string } | { ok: false };

export async function signInWithPassword(email: string, password: string): Promise<SignInResult> {
  const supabase = await createSupabaseServerClient();
  const { data, error } = await supabase.auth.signInWithPassword({ email, password });
  if (error || !data.session) return { ok: false };
  return { ok: true, accessToken: data.session.access_token };
}

export async function signOut(): Promise<void> {
  const supabase = await createSupabaseServerClient();
  await supabase.auth.signOut();
}

export async function requestPasswordReset(email: string, redirectTo: string): Promise<void> {
  const supabase = await createSupabaseServerClient();
  // The result is ignored on purpose: the response never reveals whether the email exists.
  await supabase.auth.resetPasswordForEmail(email, { redirectTo });
}

export async function exchangeRecoveryCode(code: string): Promise<boolean> {
  const supabase = await createSupabaseServerClient();
  const { error } = await supabase.auth.exchangeCodeForSession(code);
  return !error;
}

export async function updatePassword(password: string): Promise<boolean> {
  const supabase = await createSupabaseServerClient();
  const { data } = await supabase.auth.getSession();
  if (!data.session) return false;
  const { error } = await supabase.auth.updateUser({ password });
  return !error;
}
