"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { checklistCopy } from "@/content/es";
import { failure, type ActionResult } from "@/lib/actions";
import { serverApi } from "@/lib/api/server";

import { itemSchema } from "./schemas";

export async function createDraftAction(): Promise<ActionResult> {
  const api = await serverApi();
  const { data, error } = await api.POST("/api/v1/checklists");
  if (!data) return failure(error);
  revalidatePath("/app/admin/checklist");
  redirect(`/app/admin/checklist/${data.id}`);
}

export async function publishVersionAction(versionId: string): Promise<ActionResult> {
  const api = await serverApi();
  const { error } = await api.POST("/api/v1/checklists/{version_id}/publish", {
    params: { path: { version_id: versionId } },
  });
  if (error) return failure(error);
  revalidatePath("/app/admin/checklist");
  revalidatePath(`/app/admin/checklist/${versionId}`);
  return { ok: true, message: checklistCopy.published };
}

export async function updateItemAction(
  versionId: string,
  code: string,
  input: unknown,
): Promise<ActionResult> {
  const parsed = itemSchema.safeParse(input);
  if (!parsed.success) return { ok: false, message: checklistCopy.invalid };
  const keywords = parsed.data.keywords
    .split(",")
    .map((keyword) => keyword.trim())
    .filter(Boolean);
  const api = await serverApi();
  const { error } = await api.PUT("/api/v1/checklists/{version_id}/items/{code}", {
    params: { path: { version_id: versionId, code } },
    body: { ...parsed.data, keywords },
  });
  if (error) return failure(error);
  revalidatePath(`/app/admin/checklist/${versionId}`);
  return { ok: true, message: checklistCopy.saved };
}
