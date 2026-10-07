import { randomUUID } from "node:crypto";

import { expect, test } from "@playwright/test";

import { login, logout } from "./support";

test("an SME creates an evaluation and gives consent; an admin assigns a reviewer", async ({
  page,
}) => {
  const title = `Autoevaluación E2E ${randomUUID().slice(0, 6)}`;

  await login(page, "SME");
  await page.getByRole("link", { name: "Nueva evaluación" }).click();
  await page.getByLabel("Nombre de la evaluación").fill(title);
  await page.getByRole("button", { name: "Crear evaluación" }).click();

  await expect(page.getByRole("heading", { name: title })).toBeVisible();
  await expect(page.getByText("Borrador")).toBeVisible();
  const timeline = page.getByRole("list", { name: "Progreso" });
  await expect(timeline.getByRole("listitem")).toHaveCount(5);
  await expect(timeline).toContainText("Revisión humana");

  await page.getByRole("button", { name: "Aceptar y continuar" }).click();
  await expect(page.getByText("Debes aceptar las condiciones para continuar.")).toBeVisible();
  await page.getByLabel("He leído y acepto las condiciones anteriores.").check();
  await page.getByRole("button", { name: "Aceptar y continuar" }).click();
  // Once consent is stored the page re-renders without the consent card and offers the upload.
  await expect(page.getByRole("button", { name: "Seleccionar PDF" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "Aceptar y continuar" })).toHaveCount(0);
  await logout(page);

  await login(page, "ADMIN");
  await page.goto("/app/admin/evaluaciones?status=DRAFT");
  const row = page.getByRole("row").filter({ hasText: title });
  await row.getByLabel(`Revisor para ${title}`).selectOption({ label: "Revisor" });
  await row.getByRole("button", { name: "Asignar" }).click();
  await expect(row.getByText("Revisor asignado.")).toBeVisible();
  await logout(page);

  await login(page, "REVIEWER");
  await page.goto("/app/revision");
  await expect(page.getByRole("cell", { name: title, exact: true })).toBeVisible();
});

test("an SME cannot open another company's evaluation", async ({ page }) => {
  const title = `Evaluación privada ${randomUUID().slice(0, 6)}`;
  await login(page, "SME_B");
  await page.goto("/app/evaluaciones/nueva");
  await page.getByLabel("Nombre de la evaluación").fill(title);
  await page.getByRole("button", { name: "Crear evaluación" }).click();
  await expect(page.getByRole("heading", { name: title })).toBeVisible();
  const foreignUrl = page.url();
  await logout(page);

  await login(page, "SME");
  const response = await page.goto(foreignUrl);
  expect(response?.status()).toBe(404);
  await expect(page.getByText(title)).toHaveCount(0);
});
