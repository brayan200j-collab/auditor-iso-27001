import { randomUUID } from "node:crypto";
import { resolve } from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { login, logout } from "./support";

const FIXTURES = resolve(__dirname, "fixtures");

async function analysedEvaluation(page: Page): Promise<string> {
  const title = `Revisión E2E ${randomUUID().slice(0, 6)}`;
  await login(page, "SME");
  await page.goto("/app/evaluaciones/nueva");
  await page.getByLabel("Nombre de la evaluación").fill(title);
  await page.getByRole("button", { name: "Crear evaluación" }).click();
  await page.getByLabel("He leído y acepto las condiciones anteriores.").check();
  await page.getByRole("button", { name: "Aceptar y continuar" }).click();
  await page
    .getByLabel("Seleccionar PDF")
    .setInputFiles(resolve(FIXTURES, "politica_seguridad_sintetica.pdf"));
  await expect(page.getByRole("status").filter({ hasText: "PDF válido" })).toBeVisible();
  await page.getByRole("button", { name: "Iniciar análisis" }).click();
  await expect(page.getByText("Pendiente de revisión", { exact: true })).toBeVisible({
    timeout: 90_000,
  });
  await logout(page);

  await login(page, "ADMIN");
  await page.goto("/app/admin/evaluaciones?status=PENDING_REVIEW");
  const row = page.getByRole("row").filter({ hasText: title });
  await row.getByLabel(`Revisor para ${title}`).selectOption({ label: "Revisor" });
  await row.getByRole("button", { name: "Asignar" }).click();
  await expect(row.getByText("Revisor asignado.")).toBeVisible();
  await logout(page);
  return title;
}

test("a reviewer edits a finding, approves the rest and approves the evaluation", async ({
  page,
}) => {
  test.setTimeout(300_000);
  const title = await analysedEvaluation(page);

  await login(page, "REVIEWER");
  await page.goto("/app/revision");
  await page.getByRole("row").filter({ hasText: title }).getByRole("link").click();
  await expect(page.getByText("30 criterios evaluados", { exact: false })).toBeVisible();
  await expect(page.getByText("Revisados 0 de 30")).toBeVisible();
  await expect(page.getByRole("button", { name: "Aprobar evaluación" })).toBeDisabled();
  await expect(page.locator("main")).not.toContainText("%");
  const queueUrl = page.url();

  // Edit the first finding in the queue: the reviewer changes its priority and comments.
  await page
    .getByRole("link", { name: /^Revisar ISO-/ })
    .first()
    .click();
  await expect(
    page.getByText("Nivel de confianza estimado", { exact: false }).first(),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Evidencia", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Editar y aprobar" }).first().click();
  await page.getByLabel("Prioridad").selectOption({ label: "Alta" });
  await page.getByLabel("Comentario").fill("Prioridad ajustada por el revisor.");
  await page.getByRole("button", { name: "Editar y aprobar" }).last().click();
  await expect(page).toHaveURL(queueUrl);
  await expect(page.getByText("Revisados 1 de 30")).toBeVisible();
  await expect(page.getByText("Editado y aprobado").first()).toBeVisible();

  // Approve every remaining finding as proposed.
  const pendingRows = page
    .getByRole("row")
    .filter({ has: page.getByText("Pendiente", { exact: true }) });
  for (let reviewed = 1; reviewed < 30; reviewed += 1) {
    await pendingRows
      .first()
      .getByRole("link", { name: /^Revisar ISO-/ })
      .click();
    await page.getByRole("button", { name: "Aprobar", exact: true }).last().click();
    await expect(page).toHaveURL(queueUrl);
    await expect(page.getByText(`Revisados ${reviewed + 1} de 30`)).toBeVisible();
  }

  await page.getByRole("button", { name: "Aprobar evaluación" }).click();
  await expect(page.getByText("Evaluación aprobada.")).toBeVisible();
  await page.reload();
  await expect(page.getByText("Aprobado", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Aprobar evaluación" })).toHaveCount(0);
  await logout(page);

  // Only now does the company see the reviewed results.
  await login(page, "SME");
  await page.goto("/app/evaluaciones");
  await page.getByRole("row").filter({ hasText: title }).getByRole("link").click();
  await page.getByRole("link", { name: "Ver resultados aprobados" }).click();
  await expect(page.getByText("Cobertura documental preliminar")).toBeVisible();
  await expect(page.getByText(/de 30 criterios con evidencia documental/)).toBeVisible();
  await expect(page.getByText("Plan inicial de mejora")).toBeVisible();
  await expect(page.locator("main")).not.toContainText("%");
  await expect(page.locator("main")).not.toContainText("Nivel de confianza");
  await page
    .getByRole("link", { name: /^Ver detalle de ISO-/ })
    .first()
    .click();
  await expect(page.getByRole("link", { name: "Volver a los resultados" })).toBeVisible();
  await expect(page.getByText(/no constituye una certificación/)).toBeVisible();
});
