import { expect, test } from "@playwright/test";

import { login } from "./support";

test("the administrator reviews the published checklist with pending references", async ({
  page,
}) => {
  await login(page, "ADMIN");
  await page.goto("/app/admin/checklist");
  await expect(page.getByText("30 de 30 criterios activos").first()).toBeVisible();
  await page.getByRole("link", { name: /Ver criterios Versión 1/ }).click();

  await expect(page.getByText("ISO-07 · Gestión de activos")).toBeVisible();
  await expect(page.getByText("ISO-30 · Mejora continua y acciones correctivas")).toBeVisible();
  await expect(page.getByText("referencia por confirmar").first()).toBeVisible();
  await expect(page.getByText("CIS Controls v8.1:").first()).toBeVisible();
  await expect(
    page.getByText("Esta versión está publicada y no se puede modificar."),
  ).toBeVisible();
  await expect(page.getByText(/CIS-\d/)).toHaveCount(0);
});
