import "server-only";

import type { components } from "@/lib/api/schema";
import { serverApi } from "@/lib/api/server";

export type Dashboard = components["schemas"]["DashboardResponse"];
export type Metrics = components["schemas"]["MetricsResponse"];
export type AuditLogPage = components["schemas"]["AuditLogPage"];
export type AuditAction = components["schemas"]["AuditAction"];
export type AuditOutcome = components["schemas"]["AuditOutcome"];

export async function getDashboard(): Promise<Dashboard | null> {
  const api = await serverApi();
  const { data } = await api.GET("/api/v1/dashboard");
  return data ?? null;
}

export async function getMetrics(): Promise<Metrics | null> {
  const api = await serverApi();
  const { data } = await api.GET("/api/v1/metrics");
  return data ?? null;
}

export async function listAuditLogs(query: {
  page: number;
  action?: AuditAction;
  outcome?: AuditOutcome;
}): Promise<AuditLogPage | null> {
  const api = await serverApi();
  const { data } = await api.GET("/api/v1/audit-logs", {
    params: { query: { page: query.page, action: query.action, outcome: query.outcome } },
  });
  return data ?? null;
}
