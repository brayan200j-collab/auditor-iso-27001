"use server";

import { revalidatePath } from "next/cache";

import { adminUsers } from "@/content/es";
import { failure, type ActionResult } from "@/lib/actions";
import { serverApi } from "@/lib/api/server";

import { createUserSchema, updateUserSchema } from "./schemas";

export async function createUserAction(input: unknown): Promise<ActionResult> {
  const parsed = createUserSchema.safeParse(input);
  if (!parsed.success) return { ok: false, message: adminUsers.validation.email };
  const { email, fullName, role, companyId } = parsed.data;
  const api = await serverApi();
  const { error } = await api.POST("/api/v1/users", {
    body: {
      email,
      full_name: fullName,
      role,
      company_id: role === "SME" ? companyId : null,
    },
  });
  if (error) return failure(error);
  revalidatePath("/app/admin/usuarios");
  return { ok: true, message: adminUsers.created };
}

export async function updateUserAction(userId: string, input: unknown): Promise<ActionResult> {
  const parsed = updateUserSchema.safeParse(input);
  if (!parsed.success) return { ok: false, message: adminUsers.validation.fullName };
  const api = await serverApi();
  const { error } = await api.PATCH("/api/v1/users/{user_id}", {
    params: { path: { user_id: userId } },
    body: {
      full_name: parsed.data.fullName,
      ...(parsed.data.companyId ? { company_id: parsed.data.companyId } : {}),
    },
  });
  if (error) return failure(error);
  revalidatePath("/app/admin/usuarios");
  return { ok: true, message: adminUsers.updated };
}

export async function setUserActiveAction(userId: string, active: boolean): Promise<ActionResult> {
  const api = await serverApi();
  const { error } = await api.PATCH("/api/v1/users/{user_id}", {
    params: { path: { user_id: userId } },
    body: { active },
  });
  if (error) return failure(error);
  revalidatePath("/app/admin/usuarios");
  revalidatePath(`/app/admin/usuarios/${userId}`);
  return { ok: true, message: adminUsers.updated };
}
