import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { login, logout, type SeedRole } from "./support";

const WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

async function expectAccessible(page: Page, path: string): Promise<void> {
  await page.goto(path);
  await page.waitForLoadState("networkidle");
  const results = await new AxeBuilder({ page }).withTags(WCAG).analyze();
  const summary = results.violations.map(
    (violation) => `${path} · ${violation.id}: ${violation.nodes.map((n) => n.target).join(", ")}`,
  );
  expect(summary).toEqual([]);
}

test("public pages meet WCAG 2.1 AA", async ({ page }) => {
  for (const path of ["/", "/login", "/recuperar", "/privacidad"]) {
    await expectAccessible(page, path);
  }
});

const PAGES: Record<Exclude<SeedRole, "SME_B">, string[]> = {
  SME: ["/app", "/app/evaluaciones", "/app/evaluaciones/nueva"],
  REVIEWER: ["/app", "/app/revision"],
  ADMIN: [
    "/app",
    "/app/admin/evaluaciones",
    "/app/admin/empresas",
    "/app/admin/usuarios",
    "/app/admin/checklist",
    "/app/admin/auditoria",
    "/app/metricas",
  ],
  MENTOR: ["/app/metricas"],
};

for (const [role, paths] of Object.entries(PAGES) as [keyof typeof PAGES, string[]][]) {
  test(`${role} screens meet WCAG 2.1 AA`, async ({ page }) => {
    await login(page, role, role === "MENTOR" ? /\/app\/metricas$/ : /\/app$/);
    for (const path of paths) await expectAccessible(page, path);
    await logout(page);
  });
}

test("CSP header is set with a per-request nonce", async ({ page }) => {
  const first = await page.goto("/login");
  const second = await page.goto("/login");
  const csp = first?.headers()["content-security-policy"] ?? "";
  expect(csp).toMatch(/script-src 'self' 'nonce-[^']+' 'strict-dynamic'/);
  expect(csp).toContain("frame-ancestors 'none'");
  expect(second?.headers()["content-security-policy"]).not.toBe(csp);
  await expect(page.getByRole("button", { name: "Ingresar" })).toBeEnabled();
});
