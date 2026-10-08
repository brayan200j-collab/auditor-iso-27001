import { expect, test } from "@playwright/test";

import { login, logout } from "./support";

test("dashboards, pilot metrics and the audit log respect each role", async ({ page }) => {
  await login(page, "SME");
  for (const label of ["Evaluaciones activas", "Aprobadas", "Hallazgos de alta prioridad"]) {
    await expect(page.getByText(label, { exact: true })).toBeVisible();
  }
  await page.goto("/app/metricas");
  await expect(page.getByRole("heading", { name: "Métricas del piloto" })).toHaveCount(0);
  await page.goto("/app");
  await logout(page);

  await login(page, "ADMIN");
  await page.getByRole("link", { name: "Métricas" }).click();
  await expect(page.getByRole("heading", { name: "Métricas del piloto" })).toBeVisible();
  await expect(page.getByText("Métricas técnicas")).toBeVisible();
  await expect(page.getByText("Vista anonimizada", { exact: false })).toHaveCount(0);
  await page.getByRole("link", { name: "Registro de auditoría" }).click();
  await page.getByLabel("Acción").selectOption({ label: "Inicio de sesión" });
  await page.getByRole("button", { name: "Filtrar" }).click();
  await expect(page.getByRole("cell", { name: "Inicio de sesión" }).first()).toBeVisible();
  await expect(page.locator("main")).not.toContainText("LOGIN");
  await logout(page);

  await login(page, "MENTOR", /\/app\/metricas$/);
  await expect(page.getByText("Vista anonimizada", { exact: false })).toBeVisible();
  await expect(page.getByRole("link", { name: "Registro de auditoría" })).toHaveCount(0);
});
