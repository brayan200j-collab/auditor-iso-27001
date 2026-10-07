import "server-only";

import { notFound } from "next/navigation";

import type { components } from "@/lib/api/schema";
import { serverApi } from "@/lib/api/server";

export type ChecklistVersionSummary = components["schemas"]["ChecklistVersionSummary"];
export type ChecklistVersion = components["schemas"]["ChecklistVersionResponse"];
export type ChecklistItem = components["schemas"]["ChecklistItemResponse"];

export async function listChecklistVersions(): Promise<ChecklistVersionSummary[]> {
  const api = await serverApi();
  const { data, error } = await api.GET("/api/v1/checklists");
  if (!data) throw new Error(`Unable to list checklist versions: ${JSON.stringify(error)}`);
  return data;
}

export async function getChecklistVersion(versionId: string): Promise<ChecklistVersion> {
  const api = await serverApi();
  const { data } = await api.GET("/api/v1/checklists/{version_id}", {
    params: { path: { version_id: versionId } },
  });
  if (!data) notFound();
  return data;
}
