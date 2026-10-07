import { randomInt, randomUUID } from "node:crypto";

import { expect, test } from "@playwright/test";

import { waitForLink } from "./mailbox";
import { login, logout } from "./support";

test("an administrator registers a company, invites an SME user and can deactivate it", async ({
  page,
  browser,
}) => {
  const suffix = randomUUID().slice(0, 8);
  const companyName = `Empresa sintética E2E ${suffix}`;
  const email = `pyme-${suffix}@example.test`;
  const password = `Clave${suffix}Segura1A`;

  await login(page, "ADMIN");

  await page.goto("/app/admin/empresas");
  await page.getByLabel("Razón social", { exact: true }).fill(companyName);
  await page
    .getByLabel("NIT", { exact: true })
    .fill(`900.${randomInt(100, 999)}.${randomInt(100, 999)}-${randomInt(0, 9)}`);
  await page.getByRole("button", { name: "Crear empresa" }).click();
  await expect(page.getByText("La empresa se creó correctamente.")).toBeVisible();
  await expect(page.getByRole("cell", { name: companyName, exact: true })).toBeVisible();

  await page.goto("/app/admin/usuarios");
  await page.getByLabel("Correo electrónico", { exact: true }).fill(email);
  await page.getByLabel("Nombre completo", { exact: true }).fill("Persona sintética E2E");
  await page.getByLabel("Rol", { exact: true }).selectOption("SME");
  await page.getByLabel("Empresa", { exact: true }).selectOption({ label: companyName });
  await page.getByRole("button", { name: "Enviar invitación" }).click();
  await expect(page.getByText("El usuario se creó y se envió la invitación.")).toBeVisible();

  // The invited person follows the link from the email and defines a password.
  const invitation = await waitForLink(email, "/auth/confirm");
  const invitedContext = await browser.newContext();
  const invited = await invitedContext.newPage();
  await invited.goto(invitation);
  await expect(invited).toHaveURL(/\/restablecer$/);
  await invited.getByLabel("Nueva contraseña").fill(password);
  await invited.getByLabel("Confirmar contraseña").fill(password);
  await invited.getByRole("button", { name: "Guardar contraseña" }).click();
  await expect(invited.getByText("Tu contraseña se actualizó.")).toBeVisible();

  await invited.goto("/login");
  await invited.getByLabel("Correo electrónico", { exact: true }).fill(email);
  await invited.getByLabel("Contraseña").fill(password);
  await invited.getByRole("button", { name: "Ingresar" }).click();
  await expect(invited).toHaveURL(/\/app$/);
  await expect(invited.getByText(companyName)).toBeVisible();
  await logout(invited);

  // Deactivation blocks the account.
  await page.goto("/app/admin/usuarios?search=" + encodeURIComponent(email));
  await page.getByRole("link", { name: /Editar Persona sintética E2E/ }).click();
  await page.getByRole("button", { name: "Desactivar" }).click();
  await expect(page.getByText("Los cambios se guardaron.")).toBeVisible();

  await invited.goto("/login");
  await invited.getByLabel("Correo electrónico", { exact: true }).fill(email);
  await invited.getByLabel("Contraseña").fill(password);
  await invited.getByRole("button", { name: "Ingresar" }).click();
  await expect(invited.getByText("Correo o contraseña incorrectos.")).toBeVisible();
  await invitedContext.close();
});

test("non-administrators cannot open administration screens", async ({ page }) => {
  await login(page, "SME");
  for (const path of ["/app/admin/empresas", "/app/admin/usuarios"]) {
    const response = await page.goto(path);
    expect(response?.status()).toBe(404);
  }
});
