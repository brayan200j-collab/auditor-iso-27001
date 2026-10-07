import "server-only";

import { notFound } from "next/navigation";

import type { components } from "@/lib/api/schema";
import { serverApi } from "@/lib/api/server";

export type User = components["schemas"]["UserResponse"];
export type UserPage = components["schemas"]["UserPage"];
export type UserRole = User["role"];

export type UserListFilters = { page: number; role?: UserRole; search?: string };

export async function listUsers({ page, role, search }: UserListFilters): Promise<UserPage> {
  const api = await serverApi();
  const { data, error } = await api.GET("/api/v1/users", {
    params: {
      query: { page, page_size: 20, ...(role ? { role } : {}), ...(search ? { search } : {}) },
    },
  });
  if (!data) throw new Error(`Unable to list users: ${JSON.stringify(error)}`);
  return data;
}

export async function getUser(userId: string): Promise<User> {
  const api = await serverApi();
  const { data } = await api.GET("/api/v1/users/{user_id}", {
    params: { path: { user_id: userId } },
  });
  if (!data) notFound();
  return data;
}
