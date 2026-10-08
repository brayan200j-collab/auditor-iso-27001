import { randomUUID } from "node:crypto";
import { resolve } from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { login } from "./support";

const FIXTURES = resolve(__dirname, "fixtures");

async function newEvaluationWithConsent(page: Page): Promise<string> {
  const title = `Carga E2E ${randomUUID().slice(0, 6)}`;
  await page.goto("/app/evaluaciones/nueva");
  await page.getByLabel("Nombre de la evaluación").fill(title);
  await page.getByRole("button", { name: "Crear evaluación" }).click();
  await expect(page.getByRole("heading", { name: title })).toBeVisible();
  await page.getByLabel("He leído y acepto las condiciones anteriores.").check();
  await page.getByRole("button", { name: "Aceptar y continuar" }).click();
  // Once consent is stored the page re-renders without the consent card and offers the upload.
  await expect(page.getByRole("button", { name: "Seleccionar PDF" })).toBeVisible();
  return title;
}

test("an SME uploads a valid PDF, sees the checks and can delete it", async ({ page }) => {
  await login(page, "SME");
  await newEvaluationWithConsent(page);

  await page
    .getByLabel("Seleccionar PDF")
    .setInputFiles(resolve(FIXTURES, "politica_seguridad_sintetica.pdf"));
  const confirmation = page.getByRole("status").filter({ hasText: "PDF válido" });
  await expect(confirmation).toContainText("PDF válido");
  await expect(confirmation).toContainText("5 páginas");
  await expect(confirmation).toContainText("Texto detectado");
  await expect(page.getByText("Recibido", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("politica_seguridad_sintetica.pdf").first()).toBeVisible();

  await page.getByRole("button", { name: "Eliminar politica_seguridad_sintetica.pdf" }).click();
  await expect(page.getByText("Documento eliminado.")).toBeVisible();
  await expect(page.getByText("Aún no has cargado documentos.")).toBeVisible();
  await expect(page.getByText("Borrador").first()).toBeVisible();
});

test("a scanned PDF is rejected with a clear message", async ({ page }) => {
  await login(page, "SME");
  await newEvaluationWithConsent(page);
  await page
    .getByLabel("Seleccionar PDF")
    .setInputFiles(resolve(FIXTURES, "documento_escaneado_sintetico.pdf"));
  await expect(page.getByRole("alert").filter({ hasText: "OCR" })).toContainText(
    "parece un documento escaneado",
  );
});

test("starting the analysis runs extraction and AI analysis up to human review", async ({
  page,
}) => {
  await login(page, "SME");
  await newEvaluationWithConsent(page);
  await page
    .getByLabel("Seleccionar PDF")
    .setInputFiles(resolve(FIXTURES, "politica_seguridad_sintetica.pdf"));
  await expect(page.getByRole("status").filter({ hasText: "PDF válido" })).toBeVisible();

  await page.getByRole("button", { name: "Iniciar análisis" }).click();
  const timeline = page.getByRole("list", { name: "Progreso" });
  await expect(timeline.getByRole("listitem").nth(2)).toContainText("completado", {
    timeout: 60_000,
  });
  await expect(timeline.getByRole("listitem").nth(3)).toContainText("en curso");
  await expect(page.getByText("Pendiente de revisión", { exact: true })).toBeVisible();
  await expect(page.getByText(/Una persona revisará los resultados/)).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Eliminar politica_seguridad_sintetica.pdf" }),
  ).toHaveCount(0);
});
